from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, StrictBool, model_validator

from app.schemas import ApiErrorDetail
from app.services.analytics_repository import PRIVACY_CONSENT_VERSION, get_analytics_repository
from app.services.auth import authentication_required
from app.services.persistence import PersistenceError


router = APIRouter(prefix="/v1/privacy-consent", tags=["privacy"])


class PrivacyConsentResponse(BaseModel):
    policy_version: str
    health_data_consent: bool
    analytics_consent: bool
    consented_at: str | None


class PrivacyConsentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy_version: str
    health_data_consent: StrictBool
    analytics_consent: StrictBool

    @model_validator(mode="after")
    def separate_optional_consent(self):
        if self.analytics_consent and not self.health_data_consent:
            raise ValueError("health_consent_required_before_analytics")
        return self


def consent_error(code: str, *, unavailable: bool = False) -> dict:
    return ApiErrorDetail(
        code=code,
        message=("개인정보 동의 설정을 확인하지 못했어요. 잠시 후 다시 시도해 주세요." if unavailable
                 else "건강정보 처리 안내를 확인하고 동의 여부를 선택해 주세요."),
        retryable=unavailable, kind="server" if unavailable else "validation",
    ).model_dump()


def current_consent(owner_id: str) -> PrivacyConsentResponse:
    saved = get_analytics_repository().privacy_consent(owner_id)
    accepted = bool(saved and saved["policy_version"] == PRIVACY_CONSENT_VERSION)
    return PrivacyConsentResponse(
        policy_version=PRIVACY_CONSENT_VERSION,
        health_data_consent=bool(accepted and saved["health_data_consent"]),
        analytics_consent=bool(accepted and saved["health_data_consent"] and saved["analytics_consent"]),
        consented_at=saved["consented_at"] if accepted else None,
    )


def consent_owner(request: Request) -> str:
    owner_id = getattr(request.state, "user_id", None)
    if owner_id:
        return owner_id
    if authentication_required():
        raise HTTPException(401, detail=consent_error("authentication_required"))
    return "local-development"


@router.get("", response_model=PrivacyConsentResponse)
def get_current_consent(request: Request) -> PrivacyConsentResponse:
    try:
        return current_consent(consent_owner(request))
    except PersistenceError:
        raise HTTPException(503, detail=consent_error("privacy_consent_unavailable", unavailable=True)) from None


@router.put("", response_model=PrivacyConsentResponse)
def update_consent(payload: PrivacyConsentRequest, request: Request) -> PrivacyConsentResponse:
    if payload.policy_version != PRIVACY_CONSENT_VERSION:
        raise HTTPException(409, detail=consent_error("privacy_policy_version_changed"))
    try:
        record = get_analytics_repository().save_privacy_consent(
            consent_owner(request), policy_version=PRIVACY_CONSENT_VERSION,
            health_data_consent=payload.health_data_consent, analytics_consent=payload.analytics_consent,
        )
        return PrivacyConsentResponse(**record)
    except PersistenceError:
        raise HTTPException(503, detail=consent_error("privacy_consent_unavailable", unavailable=True)) from None
