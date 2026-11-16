from __future__ import annotations

from collections.abc import Callable

from app.services.persistence import PersistenceError
from app.services.storage import StorageConfigurationError


def cleanup_expired_image_uploads(
    repository, *, storage_factory: Callable, now_iso: str, deadline: float, clock: Callable[[], float],
) -> int:
    """Bounded retention work shared by the production cron and isolated verification."""
    def check_budget(*, reserve_seconds: float = 0) -> None:
        remaining = deadline - clock()
        if remaining <= 0 or remaining < reserve_seconds:
            raise StorageConfigurationError("cleanup_budget_exhausted")

    deleted_images = 0
    failure: Exception | None = None
    try:
        check_budget()
        storage = storage_factory()
        erase = getattr(storage, "erase_account_object", None)
        reserve = 18 if callable(erase) else 10
        check_budget()
        expired = repository.list_expired_image_uploads(now_iso, limit=100)
        check_budget()
        for index, record in enumerate(expired):
            check_budget()
            if index >= 100:
                raise StorageConfigurationError("cleanup_batch_incomplete")
            try:
                check_budget(reserve_seconds=reserve)
                # Persist selection before slow/failing storage work so retries rotate
                # across serverless invocations, including budget-limited batches.
                if not repository.record_image_retention_attempt(record.image_upload_id):
                    continue
                check_budget()
                if record.storage_provider != "local":
                    namespace_method = getattr(storage, "storage_namespace", None)
                    namespace = namespace_method() if callable(namespace_method) else None
                    if not isinstance(namespace, str) or not namespace.strip() or record.storage_namespace != namespace:
                        raise StorageConfigurationError("storage_namespace_mismatch")
                if record.object_key:
                    if record.storage_provider != storage.provider:
                        raise StorageConfigurationError("storage_provider_mismatch")
                    if record.storage_provider != "local" and not callable(erase):
                        raise StorageConfigurationError("erasure_proof_unavailable")
                    check_budget(reserve_seconds=reserve)
                    if not repository.mark_image_upload_deleting(record.image_upload_id):
                        continue
                    check_budget(reserve_seconds=reserve)
                    if callable(erase):
                        # A false/ambiguous result leaves the row retryable. DELETE/404
                        # alone cannot prevent a previously issued remote PUT committing.
                        if erase(object_key=record.object_key) is not True:
                            raise StorageConfigurationError("erasure_guard_unverified")
                    else:
                        storage.delete_object(object_key=record.object_key)
                elif record.storage_provider != "local":
                    raise StorageConfigurationError("remote_object_key_missing")
                check_budget()
                if repository.mark_image_upload_deleted(record.image_upload_id):
                    deleted_images += 1
            except (StorageConfigurationError, PersistenceError, OSError, ValueError) as exc:
                # Tombstone races and one failed object must not starve independent work.
                failure = failure or exc
    except (StorageConfigurationError, PersistenceError, OSError, ValueError) as exc:
        failure = failure or exc
    if failure is not None:
        raise failure
    return deleted_images
