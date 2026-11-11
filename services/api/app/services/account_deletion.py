from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from time import monotonic
from urllib.parse import quote, urlsplit
from uuid import uuid4

import httpx
import jwt

from app.services.analytics_repository import get_analytics_repository
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError, get_persistence_repository
from app.services.storage import StorageConfigurationError, get_storage_adapter


class AccountDeletionError(RuntimeError):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def account_deletion_worker_secret(environ: Mapping[str, str] | None = None) -> str:
    env = os.environ if environ is None else environ
    secret = env.get("CRON_SECRET", "").strip()
    if (
        env.get("ACCOUNT_DELETION_WORKER_ENABLED", "false").strip().lower() != "true"
        or len(secret) < 32
        or any(char.isspace() for char in secret)
    ):
        raise AccountDeletionError("account_deletion_unavailable")
    return secret


@dataclass(frozen=True)
class SupabaseAccountAdmin:
    base_url: str
    secret_key: str = field(repr=False)

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None):
        env = os.environ if environ is None else environ
        url = (env.get("SUPABASE_URL") or "").strip().rstrip("/")
        secret = (env.get("SUPABASE_SECRET_KEY") or env.get("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
        try:
            parsed = urlsplit(url)
            parsed.port
        except ValueError:
            raise AccountDeletionError("account_deletion_unavailable") from None
        valid_key = secret.startswith("sb_secret_") and len(secret) > len("sb_secret_")
        if not valid_key and secret.count(".") == 2:
            try:
                # Type-check a server-configured legacy key, never authenticate users with it.
                valid_key = jwt.decode(secret, options={"verify_signature": False}).get("role") == "service_role"
            except (jwt.PyJWTError, ValueError):
                valid_key = False
        if (
            env.get("ACCOUNT_DELETION_ENABLED", "false").strip().lower() != "true"
            or env.get("AUTH_PROVIDER", "").strip().lower() != "supabase"
            or parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or not valid_key
            or any(char.isspace() for char in secret)
        ):
            raise AccountDeletionError("account_deletion_unavailable")
        return cls(base_url=url, secret_key=secret)

    def delete_identity(self, owner_id: str) -> None:
        self._request(
            "DELETE",
            f"/auth/v1/admin/users/{quote(owner_id, safe='')}",
            payload={"should_soft_delete": False},
            allow_missing_user=True,
        )

    def _request(
        self, method, path, *, payload=None, allow_missing_user=False,
    ):
        headers = {"apikey": self.secret_key}
        if not self.secret_key.startswith("sb_secret_"):
            headers["Authorization"] = f"Bearer {self.secret_key}"
        try:
            with httpx.Client(timeout=httpx.Timeout(8.0, connect=3.0), follow_redirects=False) as client:
                response = client.request(method, self.base_url + path, headers=headers, json=payload)
            if 200 <= response.status_code < 300:
                return
            if allow_missing_user and response.status_code == 404:
                try:
                    body = response.json()
                except ValueError:
                    body = None
                if isinstance(body, dict) and body.get("code") == "user_not_found":
                    return
        except (httpx.HTTPError, OSError, ValueError):
            pass
        # No upstream body, URL, token, exception chain, or key reaches the API response.
        raise AccountDeletionError("account_deletion_provider_unavailable") from None


def delete_account(owner_id: str) -> str:
    """Accept a durable job, without retaining or depending on a client credential."""
    repository = get_persistence_repository()
    stage = repository.get_account_deletion_stage(owner_id)
    if stage is not None:
        return "deleted" if stage == 3 else "pending"
    # Reject before tombstoning when the server-owned retry path is not configured.
    SupabaseAccountAdmin.from_environment()
    account_deletion_worker_secret()
    get_coach_repository()
    get_analytics_repository()
    stage = repository.begin_account_deletion(owner_id)
    return "deleted" if stage == 3 else "pending"


def _resume_account_deletion(
    owner_id: str, admin: SupabaseAccountAdmin, *, max_objects: int, deadline: float, lease_token: str,
) -> str:
    repository = get_persistence_repository()

    def checkpoint_allowed() -> bool:
        if not repository.account_deletion_lease_current(owner_id, lease_token):
            raise PersistenceError("account_deletion_lease_lost")
        return monotonic() < deadline

    if not checkpoint_allowed():
        return "pending"
    stage = repository.get_account_deletion_stage(owner_id)
    if stage is None or stage == 3:
        return "deleted" if stage == 3 else "pending"
    if stage == 0:
        for _ in range(32):
            if not checkpoint_allowed():
                return "pending"
            remaining = deadline - monotonic()
            if remaining < 0.1:
                return "pending"
            if repository.process_account_deletion_batch(
                owner_id, lease_token, batch_size=100, timeout_seconds=min(2, remaining),
            ):
                stage = 1
                break
        if stage == 0:
            return "pending"
    if not checkpoint_allowed():
        return "pending"
    # Legacy stage 2 meant logout succeeded, NOT identity deletion. Its new marker
    # defaults false, so old interrupted jobs still perform admin identity cleanup.
    if stage in {1, 2} and not repository.account_identity_deleted(owner_id):
        # Eight-second network timeout plus a fenced SQL checkpoint; not a hard HTTP deadline.
        if deadline - monotonic() < 10:
            return "pending"
        admin.delete_identity(owner_id)
        if not checkpoint_allowed():
            return "pending"
        repository.mark_account_identity_deleted(owner_id, lease_token=lease_token)
    objects = repository.list_account_deletion_objects(owner_id, max_objects)
    if not objects and checkpoint_allowed() and repository.account_storage_cleanup_complete(owner_id):
        repository.advance_account_deletion(owner_id, 3, lease_token=lease_token)
        return "deleted"
    try:
        storage = None
        for item in objects:
            if not checkpoint_allowed():
                break
            storage = storage or get_storage_adapter()
            if item["storage_provider"] != storage.provider:
                raise StorageConfigurationError("storage_provider_mismatch")
            namespace_method = getattr(storage, "storage_namespace", None)
            namespace = namespace_method() if callable(namespace_method) else None
            if storage.provider != "local" and (
                not namespace or item.get("storage_namespace") != namespace
            ):
                raise StorageConfigurationError("storage_namespace_mismatch")
            erase = getattr(storage, "erase_account_object", None)
            if deadline - monotonic() < (18 if callable(erase) else 10):
                break
            if callable(erase):
                erase_verified = erase(object_key=item["object_key"]) is True
            else:
                storage.delete_object(object_key=item["object_key"])
                erase_verified = False
            if not checkpoint_allowed():
                return "pending"
            repository.mark_account_deletion_object_swept(
                owner_id, item["image_upload_id"], lease_token=lease_token, erase_verified=erase_verified,
                storage_namespace=namespace,
            )
    except (StorageConfigurationError, OSError, ValueError):
        raise AccountDeletionError("account_deletion_storage_unavailable") from None
    if checkpoint_allowed() and repository.account_storage_cleanup_complete(owner_id):
        repository.advance_account_deletion(owner_id, 3, lease_token=lease_token)
        return "deleted"
    # Legacy PUTs cannot be drained by expiry/HEAD. Only a verified permanent guard
    # can terminalize sealed keys; those guard objects are deliberately retained.
    return "pending"


def run_account_deletion_jobs(
    *, max_jobs: int = 1, max_objects: int = 5, budget_seconds: float = 45,
) -> dict[str, int]:
    """Server-owned cron entry point. The caller must authorize its scheduler."""
    if (
        type(max_jobs) is not int or not 1 <= max_jobs <= 5
        or type(max_objects) is not int or not 1 <= max_objects <= 25
        or type(budget_seconds) not in {int, float} or not 1 <= budget_seconds <= 45
    ):
        raise ValueError("invalid_account_deletion_batch")
    account_deletion_worker_secret()
    admin = SupabaseAccountAdmin.from_environment()
    repository = get_persistence_repository()
    result = {"processed": 0, "deleted": 0, "pending": 0, "failed": 0}
    deadline = monotonic() + budget_seconds
    for owner_id in repository.list_pending_account_deletions(min(100, max_jobs * 4)):
        if monotonic() >= deadline:
            break
        lease_token = str(uuid4())
        if not repository.claim_account_deletion(owner_id, lease_token):
            continue
        result["processed"] += 1
        status = "failed"
        try:
            status = _resume_account_deletion(
                owner_id, admin, max_objects=max_objects, deadline=deadline, lease_token=lease_token,
            )
        except (AccountDeletionError, PersistenceError):
            status = "failed"
        finally:
            try:
                repository.release_account_deletion(owner_id, lease_token)
            except PersistenceError:
                status = "failed"
        result[status] += 1
        if result["processed"] >= max_jobs:
            break
    return result


def account_access_blocked(owner_id: str) -> bool:
    """No cache: restart/outage/retry must never resurrect a tombstoned subject."""
    return get_persistence_repository().get_account_deletion_stage(owner_id) is not None
