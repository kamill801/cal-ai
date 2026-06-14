from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas import ImageUploadRequest, ImageUploadResponse

MAX_IMAGE_UPLOAD_BYTES = 8_000_000
MAX_MOCK_UPLOADS = 128
SUPPORTED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


class ImageUploadError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.message = message
        self.retryable = retryable


@dataclass(frozen=True)
class StoredImageUpload:
    image_upload_id: str
    image_reference: str
    content_type: str
    byte_size: int


_uploads: dict[str, StoredImageUpload] = {}


def create_mock_image_upload(payload: ImageUploadRequest) -> ImageUploadResponse:
    if payload.simulate_failure:
        raise ImageUploadError("image_upload_failed", "이미지를 업로드하지 못했어요. 다시 시도해 주세요.", retryable=True)
    if payload.content_type not in SUPPORTED_IMAGE_CONTENT_TYPES:
        raise ImageUploadError("unsupported_image_type", "JPG, PNG, WebP 이미지만 업로드할 수 있어요.", retryable=False)
    if payload.byte_size > MAX_IMAGE_UPLOAD_BYTES:
        raise ImageUploadError("image_too_large", "이미지 용량은 8MB 이하로 줄여 주세요.", retryable=False)

    safe_asset_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", payload.local_asset_id).strip("-") or "local-image"
    image_upload_id = f"local-upload-{safe_asset_id}"
    image_reference = f"local-image://{image_upload_id}"
    _uploads[image_upload_id] = StoredImageUpload(
        image_upload_id=image_upload_id,
        image_reference=image_reference,
        content_type=payload.content_type,
        byte_size=payload.byte_size,
    )
    while len(_uploads) > MAX_MOCK_UPLOADS:
        oldest_id = next(iter(_uploads))
        del _uploads[oldest_id]
    return ImageUploadResponse(image_upload_id=image_upload_id, image_reference=image_reference, status="ready")


def resolve_image_reference(image_upload_id: str) -> str:
    upload = _uploads.get(image_upload_id)
    if not upload:
        raise ImageUploadError("image_upload_not_found", "업로드된 이미지를 찾을 수 없어요. 다시 업로드해 주세요.", retryable=False)
    return upload.image_reference
