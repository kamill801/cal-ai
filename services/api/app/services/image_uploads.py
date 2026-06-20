from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.schemas import ImageUploadCompleteRequest, ImageUploadPresignRequest, ImageUploadPresignResponse, ImageUploadRequest, ImageUploadResponse
from app.services.persistence import PersistenceRepository, get_persistence_repository
from app.services.storage import (
    DEFAULT_PRESIGN_EXPIRES_SECONDS,
    StorageConfigurationError,
    get_image_ttl_days,
    get_image_upload_max_bytes,
    get_storage_adapter,
    get_upload_soft_limit_bytes,
)

SUPPORTED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageUploadError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.message = message
        self.retryable = retryable


def create_mock_image_upload(
    payload: ImageUploadRequest,
    repository: PersistenceRepository | None = None,
) -> ImageUploadResponse:
    if payload.simulate_failure:
        raise ImageUploadError("image_upload_failed", "이미지를 업로드하지 못했어요. 다시 시도해 주세요.", retryable=True)
    _validate_image_metadata(content_type=payload.content_type, byte_size=payload.byte_size)

    safe_asset_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", payload.local_asset_id).strip("-") or "local-image"
    image_upload_id = f"local-upload-{safe_asset_id}"
    image_reference = f"local-image://{image_upload_id}"
    (repository or get_persistence_repository()).save_image_upload(
        payload=payload,
        image_upload_id=image_upload_id,
        image_reference=image_reference,
    )
    return ImageUploadResponse(image_upload_id=image_upload_id, image_reference=image_reference, status="ready")


def create_presigned_image_upload(payload: ImageUploadPresignRequest) -> ImageUploadPresignResponse:
    _validate_image_metadata(content_type=payload.content_type, byte_size=payload.byte_size)
    try:
        repository = get_persistence_repository()
        adapter = get_storage_adapter()
        soft_limit_bytes = get_upload_soft_limit_bytes()
        projected_bytes = repository.sum_image_upload_bytes() + payload.byte_size
        if projected_bytes > soft_limit_bytes:
            raise ImageUploadError(
                "upload_soft_limit_exceeded",
                "이미지 저장소 사용량이 설정된 한도에 가까워졌어요. 오래된 이미지를 정리한 뒤 다시 시도해 주세요.",
                retryable=False,
            )

        image_upload_id = f"image-upload-{uuid4()}"
        object_key = create_image_object_key(image_upload_id=image_upload_id, file_name=payload.file_name)
        presigned = adapter.presign_put(
            object_key=object_key,
            content_type=payload.content_type,
            expires_seconds=DEFAULT_PRESIGN_EXPIRES_SECONDS,
        )
        image_reference = adapter.image_reference(object_key=object_key)
        repository.save_image_upload(
            payload=ImageUploadRequest(
                local_asset_id=payload.local_asset_id,
                file_name=payload.file_name,
                content_type=payload.content_type,
                byte_size=payload.byte_size,
            ),
            image_upload_id=image_upload_id,
            image_reference=image_reference,
            storage_provider=adapter.provider,
            object_key=object_key,
            upload_status="pending",
            upload_expires_at=presigned.expires_at,
        )
        return ImageUploadPresignResponse(
            image_upload_id=image_upload_id,
            object_key=object_key,
            upload_url=presigned.upload_url,
            headers=presigned.headers,
            expires_at=presigned.expires_at,
            max_bytes=get_image_upload_max_bytes(),
            soft_limit_bytes=soft_limit_bytes,
            soft_limit_exceeded=False,
            ttl_days=get_image_ttl_days(),
        )
    except StorageConfigurationError as exc:
        raise ImageUploadError("storage_unavailable", "이미지 저장소 설정을 확인해 주세요.", retryable=True) from exc


def complete_presigned_image_upload(
    payload: ImageUploadCompleteRequest,
    repository: PersistenceRepository | None = None,
) -> ImageUploadResponse:
    _validate_image_metadata(content_type=payload.content_type, byte_size=payload.byte_size)
    _validate_object_key(payload.object_key)
    if not payload.object_key.startswith(f"uploads/{payload.image_upload_id}/"):
        raise ImageUploadError("image_upload_key_mismatch", "업로드 주소와 이미지 정보가 일치하지 않아요.", retryable=False)

    try:
        persistence = repository or get_persistence_repository()
        existing = persistence.get_image_upload(payload.image_upload_id)
        if not existing:
            raise ImageUploadError("image_upload_not_found", "업로드된 이미지를 찾을 수 없어요. 다시 업로드해 주세요.", retryable=False)
        _validate_presigned_upload_record(existing, payload)

        adapter = get_storage_adapter()
        image_reference = adapter.image_reference(object_key=payload.object_key)
        cleanup_after = _cleanup_after_iso(get_image_ttl_days())
        record = persistence.save_image_upload(
            payload=ImageUploadRequest(
                local_asset_id=payload.local_asset_id,
                file_name=payload.file_name,
                content_type=payload.content_type,
                byte_size=payload.byte_size,
            ),
            image_upload_id=payload.image_upload_id,
            image_reference=image_reference,
            storage_provider=adapter.provider,
            object_key=payload.object_key,
            upload_status="ready",
            cleanup_after=cleanup_after,
            upload_expires_at=existing.upload_expires_at,
        )
        return ImageUploadResponse(image_upload_id=record.image_upload_id, image_reference=record.image_reference, status="ready")
    except StorageConfigurationError as exc:
        raise ImageUploadError("storage_unavailable", "이미지 저장소 설정을 확인해 주세요.", retryable=True) from exc


def resolve_image_reference(
    image_upload_id: str,
    repository: PersistenceRepository | None = None,
) -> str:
    upload = (repository or get_persistence_repository()).get_image_upload(image_upload_id)
    if not upload:
        raise ImageUploadError("image_upload_not_found", "업로드된 이미지를 찾을 수 없어요. 다시 업로드해 주세요.", retryable=False)
    if upload.upload_status != "ready":
        raise ImageUploadError("image_upload_not_ready", "이미지 업로드가 아직 완료되지 않았어요.", retryable=False)
    return upload.image_reference


def create_image_object_key(*, image_upload_id: str, file_name: str) -> str:
    safe_file_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", file_name).strip(".-") or "meal-image"
    return f"uploads/{image_upload_id}/{safe_file_name}"


def _validate_image_metadata(*, content_type: str, byte_size: int) -> None:
    if content_type not in SUPPORTED_IMAGE_CONTENT_TYPES:
        raise ImageUploadError("unsupported_image_type", "JPG, PNG, WebP 이미지만 업로드할 수 있어요.", retryable=False)
    try:
        max_bytes = get_image_upload_max_bytes()
    except StorageConfigurationError as exc:
        raise ImageUploadError("storage_unavailable", "이미지 저장소 설정을 확인해 주세요.", retryable=True) from exc
    if byte_size > max_bytes:
        max_mb = max(1, max_bytes // 1_000_000)
        raise ImageUploadError("image_too_large", f"이미지 용량은 {max_mb}MB 이하로 줄여 주세요.", retryable=False)


def _validate_object_key(object_key: str) -> None:
    if ".." in object_key or object_key.startswith("/") or "//" in object_key:
        raise ImageUploadError("invalid_image_object_key", "이미지 업로드 키가 올바르지 않아요.", retryable=False)


def _validate_presigned_upload_record(existing: object, payload: ImageUploadCompleteRequest) -> None:
    if existing.upload_status == "ready":
        if (
            existing.object_key == payload.object_key
            and existing.file_name == payload.file_name
            and existing.content_type == payload.content_type
            and existing.byte_size == payload.byte_size
        ):
            return
        raise ImageUploadError("image_upload_already_completed", "이미 완료된 업로드 정보와 요청이 일치하지 않아요.", retryable=False)
    if existing.upload_status != "pending":
        raise ImageUploadError("image_upload_not_ready", "이미지 업로드 상태를 확인할 수 없어요.", retryable=False)
    if existing.object_key != payload.object_key:
        raise ImageUploadError("image_upload_key_mismatch", "업로드 주소와 이미지 정보가 일치하지 않아요.", retryable=False)
    if existing.content_type != payload.content_type or existing.byte_size != payload.byte_size or existing.file_name != payload.file_name:
        raise ImageUploadError("image_upload_metadata_mismatch", "업로드된 이미지 정보가 처음 요청과 일치하지 않아요.", retryable=False)
    if existing.upload_expires_at and datetime.fromisoformat(existing.upload_expires_at) < datetime.now(UTC):
        raise ImageUploadError("image_upload_expired", "업로드 시간이 만료됐어요. 다시 업로드해 주세요.", retryable=False)


def _cleanup_after_iso(ttl_days: int) -> str:
    return (datetime.now(UTC) + timedelta(days=ttl_days)).isoformat(timespec="seconds")
