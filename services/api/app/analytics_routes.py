from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request

from app.admin_schemas import (
    AnalyticsAcceptedResponse,
    AnalyticsEventRequest,
    AnalyticsHeartbeatRequest,
    BillingStatusResponse,
)
from app.services.analytics_repository import (
    AnalyticsOwnershipError,
    AnalyticsProfileOwnershipError,
    get_analytics_repository,
)
from app.services.auth import AuthenticatedUser
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError


router = APIRouter(prefix="/v1/analytics", tags=["analytics"])
billing_router = APIRouter(prefix="/v1/billing", tags=["billing"])


def analytics_user(request: Request, profile_id: str | None) -> AuthenticatedUser | None:
    user = getattr(request.state, "auth_user", None)
    if profile_id is not None:
        profile = get_coach_repository().get_profile(profile_id)
        owner_id = user.user_id if user else None
        if profile is None or profile.owner_id != owner_id:
            raise HTTPException(status_code=404, detail="profile_not_found")
    return user


@router.post("/events", response_model=AnalyticsAcceptedResponse)
def record_analytics_event(
    payload: AnalyticsEventRequest,
    request: Request,
) -> AnalyticsAcceptedResponse:
    try:
        user = analytics_user(request, payload.profile_id)
        accepted_at = get_analytics_repository().record_event(
            payload,
            user,
        )
    except AnalyticsProfileOwnershipError as exc:
        raise HTTPException(status_code=404, detail="profile_not_found") from exc
    except AnalyticsOwnershipError as exc:
        raise HTTPException(status_code=409, detail="analytics_session_conflict") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="analytics_unavailable") from exc
    return AnalyticsAcceptedResponse(accepted_at=accepted_at)


@router.post("/heartbeat", response_model=AnalyticsAcceptedResponse)
def record_analytics_heartbeat(
    payload: AnalyticsHeartbeatRequest,
    request: Request,
) -> AnalyticsAcceptedResponse:
    try:
        user = analytics_user(request, payload.profile_id)
        accepted_at = get_analytics_repository().heartbeat(
            payload,
            user,
        )
    except AnalyticsProfileOwnershipError as exc:
        raise HTTPException(status_code=404, detail="profile_not_found") from exc
    except AnalyticsOwnershipError as exc:
        raise HTTPException(status_code=409, detail="analytics_session_conflict") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="analytics_unavailable") from exc
    return AnalyticsAcceptedResponse(accepted_at=accepted_at)


@billing_router.get("/status", response_model=BillingStatusResponse)
def billing_status(request: Request) -> BillingStatusResponse:
    try:
        plan, status = get_analytics_repository().billing_status(
            getattr(request.state, "user_id", None)
        )
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="billing_unavailable") from exc
    provider = (os.environ.get("PAYMENT_PROVIDER") or "").strip().lower() or None
    groble_configured = provider == "groble" and bool(
        (os.environ.get("GROBLE_PRODUCT_ID") or "").strip()
        and (os.environ.get("GROBLE_WEBHOOK_SECRET") or "").strip()
    )
    # The checkout stays closed until the signed order and webhook endpoints exist.
    checkout_available = False
    return BillingStatusResponse(
        plan=plan,
        status=status,
        checkout_available=checkout_available,
        provider=provider,
        message=(
            "Groble 설정은 확인됐고, 안전한 결제·웹훅 연결을 준비 중이에요."
            if groble_configured
            else "베타 기간에는 무료로 이용할 수 있어요. 결제 연결 후 Pro를 열 예정이에요."
        ),
    )
