from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.schemas import ApiErrorDetail, ImageUploadPresignRequest, ImageUploadPresignResponse
from app.services.analysis_provider import AnalysisProviderConfigurationError, AnalysisProviderUnavailableError, StructuredOutputMalformedError
from app.services.coach_repository import CoachRepository, EquipmentUsageLimitError, get_coach_repository
from app.services.equipment_guide import (
    CATALOG, EQUIPMENT_BY_ID, Equipment, EquipmentGuide, EquipmentIdentification,
    EquipmentProviderDisabledError, get_equipment_guide, get_equipment_provider,
)
from app.services.image_uploads import ImageUploadError, create_presigned_image_upload, resolve_analysis_image_reference
from app.services.persistence import ImageUploadRecord, PersistenceError, PersistenceRepository, get_persistence_repository
from app.services.storage import StorageConfigurationError, get_storage_adapter

router = APIRouter(prefix="/v1", tags=["equipment"])


class EquipmentCatalog(BaseModel):
    items: list[Equipment]
    photo_identification_available: bool


class EquipmentUploadRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    byte_size: int = Field(gt=0)


class EquipmentIdentifyRequest(BaseModel):
    image_upload_id: str = Field(min_length=1, max_length=180)


def _error(status: int, code: str, message: str, *, retryable: bool = False, kind: str = "validation") -> HTTPException:
    return HTTPException(status, detail=ApiErrorDetail(code=code, message=message, retryable=retryable, kind=kind).model_dump())


def _require_profile_owner(profile_id: str, request: Request) -> str:
    owner_id = getattr(request.state, "user_id", None)
    if not owner_id:
        raise _error(401, "authentication_required", "기구 사진을 분석하려면 로그인이 필요해요.")
    profile = get_coach_repository().get_profile(profile_id)
    if profile is None or profile.owner_id != owner_id:
        raise _error(404, "profile_not_found", "프로필을 찾을 수 없어요.", kind="not_found")
    return owner_id


def _remove_transient_image(upload: ImageUploadRecord, repository: PersistenceRepository) -> None:
    reconcile_at = datetime.fromisoformat(upload.upload_expires_at) + timedelta(hours=1) if upload.upload_expires_at else datetime.now(UTC)
    retain_key = upload.storage_provider == "r2" and reconcile_at > datetime.now(UTC)
    if retain_key:
        repository.retain_transient_image_cleanup(upload.image_upload_id, reconcile_at.isoformat(timespec="seconds"))
    if upload.object_key:
        storage = get_storage_adapter()
        if storage.provider != upload.storage_provider:
            raise StorageConfigurationError("equipment_storage_provider_mismatch")
        storage.delete_object(object_key=upload.object_key)
    if not retain_key:
        repository.mark_image_upload_deleted(upload.image_upload_id)


def _cleanup_without_losing_result(upload: ImageUploadRecord, repository: PersistenceRepository, result: EquipmentIdentification | None) -> None:
    try:
        _remove_transient_image(upload, repository)
    except (StorageConfigurationError, PersistenceError):
        if result is not None:
            result.cleanup_pending = True


def _finish_equipment_receipt(
    coach: CoachRepository,
    profile_id: str,
    upload_id: str,
    result: EquipmentIdentification | None,
) -> EquipmentIdentification | None:
    # Retry the receipt write, never the paid provider; read back ambiguous commits.
    payload = result.model_dump() if result is not None else None
    for _ in range(2):
        try:
            coach.finish_equipment_analysis(profile_id, upload_id, payload)
        except PersistenceError:
            pass
        try:
            receipt = coach.get_equipment_receipt(profile_id, upload_id)
        except PersistenceError:
            continue
        if receipt is not None:
            if receipt["status"] == "complete":
                return EquipmentIdentification.model_validate(receipt["result"])
            if receipt["status"] == "failed":
                if result is None:
                    return None
                raise _error(409, "equipment_image_already_used", "이미 사용한 사진이에요. 사진을 다시 선택해 주세요.")
    raise _error(503, "equipment_result_unconfirmed", "분석 결과 저장을 확인하지 못했어요. 새 사진을 선택하거나 기구 이름을 직접 선택해 주세요.", kind="server")


def _daily_limit(name: str, default: int, maximum: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
        if not 1 <= value <= maximum:
            raise ValueError("invalid_limit")
        return value
    except ValueError as exc:
        raise AnalysisProviderConfigurationError("equipment_limit_invalid") from exc


@router.get("/equipment-guides/catalog", response_model=EquipmentCatalog)
def equipment_catalog() -> EquipmentCatalog:
    try:
        get_equipment_provider()
        available = True
    except (EquipmentProviderDisabledError, AnalysisProviderConfigurationError):
        available = False
    return EquipmentCatalog(items=list(CATALOG), photo_identification_available=available)


@router.get("/equipment-guides/{equipment_id}", response_model=EquipmentGuide)
def equipment_guide(equipment_id: str) -> EquipmentGuide:
    if equipment_id not in EQUIPMENT_BY_ID:
        raise _error(404, "equipment_not_found", "등록된 기구를 선택해 주세요.", kind="not_found")
    return get_equipment_guide(equipment_id)


@router.post("/profiles/{profile_id}/equipment-image-uploads/presign", response_model=ImageUploadPresignResponse)
def presign_equipment_image(profile_id: str, payload: EquipmentUploadRequest, request: Request) -> ImageUploadPresignResponse:
    try:
        owner_id = _require_profile_owner(profile_id, request)
        get_equipment_provider()
        extension = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[payload.content_type]
        return create_presigned_image_upload(
            ImageUploadPresignRequest(local_asset_id=f"equipment-{uuid4()}", file_name=f"equipment-guide.{extension}", content_type=payload.content_type, byte_size=payload.byte_size),
            owner_id=owner_id,
            expires_seconds=120,
        )
    except EquipmentProviderDisabledError as exc:
        raise _error(503, "equipment_provider_disabled", "사진 찾기는 준비 중이에요. 기구 이름을 선택하면 사용법을 볼 수 있어요.", kind="provider") from exc
    except AnalysisProviderConfigurationError as exc:
        raise _error(503, "equipment_provider_unavailable", "사진 분석을 사용할 수 없어요. 기구 이름을 직접 선택해 주세요.", kind="provider") from exc
    except ImageUploadError as exc:
        raise _error(400, exc.code, exc.message, retryable=exc.retryable) from exc
    except PersistenceError as exc:
        raise _error(503, "persistence_unavailable", "이미지 업로드를 준비하지 못했어요.", retryable=True, kind="server") from exc


@router.post("/profiles/{profile_id}/equipment-identifications", response_model=EquipmentIdentification)
def identify_equipment(profile_id: str, payload: EquipmentIdentifyRequest, request: Request) -> EquipmentIdentification:
    try:
        owner_id = _require_profile_owner(profile_id, request)
        repository = get_persistence_repository()
        upload = repository.get_image_upload(payload.image_upload_id)
        if upload is None or upload.owner_id != owner_id or upload.file_name not in {"equipment-guide.jpg", "equipment-guide.png", "equipment-guide.webp"}:
            raise _error(404, "image_upload_not_found", "기구 사진을 새로 선택해 주세요.", kind="not_found")
        coach = get_coach_repository()
        receipt = coach.get_equipment_receipt(profile_id, payload.image_upload_id)
        if receipt is not None:
            if receipt["status"] == "complete":
                result = EquipmentIdentification.model_validate(receipt["result"])
                _cleanup_without_losing_result(upload, repository, result)
                return result
            # Cleanup's tombstone proves provider work has ended, even if finalization failed.
            if receipt["status"] == "running" and upload.image_reference.startswith("deleted://"):
                result = _finish_equipment_receipt(coach, profile_id, payload.image_upload_id, None)
                if result is not None:
                    _cleanup_without_losing_result(upload, repository, result)
                    return result
            raise _error(409, "equipment_image_already_used", "이미 분석 중이거나 사용한 사진이에요. 사진을 다시 선택해 주세요.")
        provider = get_equipment_provider()
        if upload.cleanup_after and datetime.fromisoformat(upload.cleanup_after) <= datetime.now(UTC):
            raise _error(400, "equipment_image_expired", "사진의 보관 시간이 지났어요. 새 사진을 선택해 주세요.")
        image_reference = resolve_analysis_image_reference(payload.image_upload_id, repository, owner_id=owner_id)
        state = coach.reserve_equipment_analysis(profile_id, owner_id, payload.image_upload_id, _daily_limit("EQUIPMENT_DAILY_LIMIT", 10, 100), _daily_limit("EQUIPMENT_GLOBAL_DAILY_LIMIT", 100, 1000))
        if state != "reserved":
            raise _error(409, "equipment_scan_in_progress", "분석 중인 사진이 있어요. 잠시 기다려 주세요.", retryable=True)
        result = None
        try:
            if not repository.claim_transient_image_upload(payload.image_upload_id, owner_id):
                raise _error(409, "equipment_image_already_used", "이미 분석 중이거나 사용한 사진이에요. 사진을 다시 선택해 주세요.")
            result = provider.identify(image_reference)
        except Exception:
            _finish_equipment_receipt(coach, profile_id, payload.image_upload_id, None)
            raise
        else:
            result = _finish_equipment_receipt(coach, profile_id, payload.image_upload_id, result)
            return result
        finally:
            _cleanup_without_losing_result(upload, repository, result)
    except EquipmentUsageLimitError as exc:
        raise _error(429, exc.code, "사진 분석 한도에 도달했거나 다른 사진을 분석 중이에요. 기구 이름을 직접 선택해 주세요.") from exc
    except EquipmentProviderDisabledError as exc:
        raise _error(503, "equipment_provider_disabled", "사진 찾기는 준비 중이에요. 기구 이름을 직접 선택해 주세요.", kind="provider") from exc
    except AnalysisProviderConfigurationError as exc:
        raise _error(503, "equipment_provider_unavailable", "사진 분석 설정을 확인하고 있어요. 기구 이름을 직접 선택해 주세요.", kind="provider") from exc
    except StructuredOutputMalformedError as exc:
        raise _error(503, "equipment_output_malformed", "기구를 확실히 구분하지 못했어요. 다시 촬영하거나 이름을 선택해 주세요.", retryable=True, kind="provider") from exc
    except AnalysisProviderUnavailableError as exc:
        raise _error(503, "equipment_provider_unavailable", "사진 분석이 잠시 지연되고 있어요. 다시 촬영하거나 이름을 선택해 주세요.", retryable=True, kind="provider") from exc
    except ImageUploadError as exc:
        raise _error(400, exc.code, exc.message, retryable=exc.retryable) from exc
    except StorageConfigurationError as exc:
        raise _error(503, "equipment_storage_unavailable", "사진 처리를 완료하지 못했어요. 잠시 뒤 다시 시도해 주세요.", retryable=True, kind="server") from exc
    except PersistenceError as exc:
        raise _error(503, "persistence_unavailable", "사진 처리를 완료하지 못했어요. 잠시 뒤 다시 시도해 주세요.", retryable=True, kind="server") from exc


@router.delete("/profiles/{profile_id}/equipment-image-uploads/{image_upload_id}")
def discard_equipment_image(profile_id: str, image_upload_id: str, request: Request) -> dict[str, str]:
    try:
        owner_id = _require_profile_owner(profile_id, request)
        repository = get_persistence_repository()
        upload = repository.get_image_upload(image_upload_id)
        if upload is None or upload.owner_id != owner_id or upload.file_name not in {"equipment-guide.jpg", "equipment-guide.png", "equipment-guide.webp"}:
            raise _error(404, "image_upload_not_found", "기구 사진을 찾을 수 없어요.", kind="not_found")
        if upload.upload_status == "deleted":
            return {"status": "deleted"}
        if not repository.cancel_transient_image_upload(image_upload_id, owner_id):
            upload = repository.get_image_upload(image_upload_id)
            if upload is None or upload.owner_id != owner_id:
                raise _error(404, "image_upload_not_found", "기구 사진을 찾을 수 없어요.", kind="not_found")
            if upload.upload_status == "deleted":
                return {"status": "deleted"}
            # A deleting upload cannot be claimed again. Check all of this owner's profiles.
            if not upload.image_reference.startswith("deleted://") and get_coach_repository().is_equipment_analysis_running(image_upload_id):
                return {"status": "cleanup_after_analysis"}
        _remove_transient_image(upload, repository)
        return {"status": "deleted"}
    except (StorageConfigurationError, PersistenceError) as exc:
        raise _error(503, "equipment_cleanup_pending", "사진 정리를 다시 시도하고 있어요.", retryable=True, kind="server") from exc
