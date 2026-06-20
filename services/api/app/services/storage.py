from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import quote, urlparse


DEFAULT_IMAGE_UPLOAD_MAX_BYTES = 8_000_000
DEFAULT_UPLOAD_SOFT_LIMIT_BYTES = 8_000_000_000
DEFAULT_IMAGE_TTL_DAYS = 30
DEFAULT_PRESIGN_EXPIRES_SECONDS = 900


class StorageConfigurationError(RuntimeError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class PresignedUpload:
    upload_url: str
    headers: dict[str, str]
    expires_at: str


@dataclass(frozen=True)
class StorageReadiness:
    status: str
    provider: str
    message: str | None = None


class StorageAdapter(Protocol):
    provider: str

    def presign_put(self, *, object_key: str, content_type: str, expires_seconds: int) -> PresignedUpload: ...

    def image_reference(self, *, object_key: str) -> str: ...


def get_image_upload_max_bytes(environ: dict[str, str] | None = None) -> int:
    return _read_positive_int("IMAGE_UPLOAD_MAX_BYTES", DEFAULT_IMAGE_UPLOAD_MAX_BYTES, environ)


def get_upload_soft_limit_bytes(environ: dict[str, str] | None = None) -> int:
    return _read_positive_int("UPLOAD_SOFT_LIMIT_BYTES", DEFAULT_UPLOAD_SOFT_LIMIT_BYTES, environ)


def get_image_ttl_days(environ: dict[str, str] | None = None) -> int:
    return _read_positive_int("IMAGE_TTL_DAYS", DEFAULT_IMAGE_TTL_DAYS, environ)


def get_storage_adapter(environ: dict[str, str] | None = None) -> StorageAdapter:
    env = environ if environ is not None else os.environ
    provider = env.get("STORAGE_PROVIDER", "local").strip().lower()
    if provider in {"", "local", "mock"}:
        return LocalStorageAdapter()
    if provider == "r2":
        return R2StorageAdapter.from_env(env)
    raise StorageConfigurationError(f"unsupported storage provider: {provider}")


def get_storage_readiness(environ: dict[str, str] | None = None) -> StorageReadiness:
    env = environ if environ is not None else os.environ
    provider = env.get("STORAGE_PROVIDER", "local").strip().lower() or "local"
    if provider in {"local", "mock"}:
        return StorageReadiness(status="ok", provider=provider, message="local storage fallback enabled")
    if provider != "r2":
        return StorageReadiness(status="misconfigured", provider=provider, message="unsupported storage provider")

    missing = [name for name in R2StorageAdapter.required_env_names() if not env.get(name)]
    if missing:
        return StorageReadiness(status="misconfigured", provider="r2", message=f"missing env vars: {', '.join(missing)}")
    return StorageReadiness(status="ok", provider="r2", message="r2 presigned upload configured")


class LocalStorageAdapter:
    provider = "local"

    def presign_put(self, *, object_key: str, content_type: str, expires_seconds: int) -> PresignedUpload:
        expires_at = _future_iso(expires_seconds)
        return PresignedUpload(
            upload_url=f"local-upload://{object_key}",
            headers={"Content-Type": content_type},
            expires_at=expires_at,
        )

    def image_reference(self, *, object_key: str) -> str:
        return f"local-image://{object_key}"


@dataclass(frozen=True)
class R2StorageAdapter:
    bucket_name: str
    account_id: str
    access_key_id: str
    secret_access_key: str
    endpoint: str
    region: str

    provider = "r2"

    @classmethod
    def required_env_names(cls) -> tuple[str, ...]:
        return (
            "R2_BUCKET_NAME",
            "R2_ACCOUNT_ID",
            "R2_ACCESS_KEY_ID",
            "R2_SECRET_ACCESS_KEY",
            "R2_ENDPOINT",
            "R2_REGION",
        )

    @classmethod
    def from_env(cls, env: dict[str, str]) -> "R2StorageAdapter":
        missing = [name for name in cls.required_env_names() if not env.get(name)]
        if missing:
            raise StorageConfigurationError(f"missing R2 env vars: {', '.join(missing)}")
        return cls(
            bucket_name=env["R2_BUCKET_NAME"],
            account_id=env["R2_ACCOUNT_ID"],
            access_key_id=env["R2_ACCESS_KEY_ID"],
            secret_access_key=env["R2_SECRET_ACCESS_KEY"],
            endpoint=env["R2_ENDPOINT"].rstrip("/"),
            region=env.get("R2_REGION") or "auto",
        )

    def presign_put(self, *, object_key: str, content_type: str, expires_seconds: int) -> PresignedUpload:
        now = datetime.now(UTC)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        parsed = urlparse(self.endpoint)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise StorageConfigurationError("R2_ENDPOINT must be an absolute URL")

        canonical_uri = _canonical_object_path(parsed.path, self.bucket_name, object_key)
        credential_scope = f"{date_stamp}/{self.region}/s3/aws4_request"
        credential = f"{self.access_key_id}/{credential_scope}"
        signed_headers = "content-type;host"
        query_params = {
            "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
            "X-Amz-Credential": credential,
            "X-Amz-Date": amz_date,
            "X-Amz-Expires": str(expires_seconds),
            "X-Amz-SignedHeaders": signed_headers,
        }
        canonical_query = _canonical_query(query_params)
        canonical_headers = f"content-type:{content_type}\nhost:{parsed.netloc}\n"
        canonical_request = "\n".join(
            [
                "PUT",
                canonical_uri,
                canonical_query,
                canonical_headers,
                signed_headers,
                "UNSIGNED-PAYLOAD",
            ]
        )
        string_to_sign = "\n".join(
            [
                "AWS4-HMAC-SHA256",
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )
        signing_key = _signature_key(self.secret_access_key, date_stamp, self.region, "s3")
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        upload_url = f"{parsed.scheme}://{parsed.netloc}{canonical_uri}?{canonical_query}&X-Amz-Signature={signature}"
        return PresignedUpload(
            upload_url=upload_url,
            headers={"Content-Type": content_type},
            expires_at=_future_iso(expires_seconds, now=now),
        )

    def image_reference(self, *, object_key: str) -> str:
        return f"r2://{self.bucket_name}/{object_key}"


def _canonical_object_path(endpoint_path: str, bucket_name: str, object_key: str) -> str:
    prefix = endpoint_path.rstrip("/")
    encoded_bucket = quote(bucket_name, safe="-_.~")
    encoded_key = "/".join(quote(part, safe="-_.~") for part in object_key.split("/"))
    return f"{prefix}/{encoded_bucket}/{encoded_key}" if prefix else f"/{encoded_bucket}/{encoded_key}"


def _canonical_query(params: dict[str, str]) -> str:
    return "&".join(f"{quote(key, safe='-_.~')}={quote(value, safe='-_.~')}" for key, value in sorted(params.items()))


def _signature_key(secret_access_key: str, date_stamp: str, region: str, service: str) -> bytes:
    date_key = _sign(f"AWS4{secret_access_key}".encode("utf-8"), date_stamp)
    region_key = _sign(date_key, region)
    service_key = _sign(region_key, service)
    return _sign(service_key, "aws4_request")


def _sign(key: bytes, message: str) -> bytes:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()


def _future_iso(seconds: int, *, now: datetime | None = None) -> str:
    base = now or datetime.now(UTC)
    return (base + timedelta(seconds=seconds)).isoformat(timespec="seconds")


def _read_positive_int(name: str, default: int, environ: dict[str, str] | None = None) -> int:
    env = environ if environ is not None else os.environ
    raw_value = env.get(name)
    if raw_value is None or raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise StorageConfigurationError(f"{name} must be an integer") from exc
    if value <= 0:
        raise StorageConfigurationError(f"{name} must be positive")
    return value
