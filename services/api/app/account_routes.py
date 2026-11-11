from __future__ import annotations

import secrets
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StrictBool, field_validator

from app.schemas import ApiErrorDetail
from app.services.account_deletion import (
    AccountDeletionError,
    account_access_blocked,
    account_deletion_worker_secret,
    delete_account,
    run_account_deletion_jobs,
)
from app.services.persistence import PersistenceError


router = APIRouter(prefix="/v1/account", tags=["account"])
worker_router = APIRouter(prefix="/internal/account-deletions", tags=["internal"])


class AccountDeletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: StrictBool

    @field_validator("confirm")
    @classmethod
    def confirmed(cls, value: bool) -> bool:
        if not value:
            raise ValueError("explicit_confirmation_required")
        return value


class AccountDeletionResponse(BaseModel):
    status: Literal["pending", "deleted"]


def _detail(code: str, *, retryable: bool = True) -> dict:
    return ApiErrorDetail(
        code=code,
        message=(
            "로그인이 필요해요." if code == "authentication_required"
            else "계정 삭제를 완료하지 못했어요. 잠시 후 계정 삭제를 다시 시도해 주세요."
            if retryable else "계정 삭제가 요청되어 다른 기능을 사용할 수 없어요. 계정 삭제만 다시 시도할 수 있어요."
        ),
        retryable=retryable,
        kind="server" if retryable else "validation",
    ).model_dump()


def account_deletion_gate(request: Request) -> JSONResponse | None:
    """Call immediately AFTER verified authentication, BEFORE any data/analytics writes."""
    owner_id = getattr(request.state, "user_id", None)
    if not owner_id or (request.method == "DELETE" and request.url.path == "/v1/account"):
        return None
    try:
        blocked = account_access_blocked(owner_id)
    except PersistenceError:
        return JSONResponse(status_code=503, content={"detail": _detail("account_state_unavailable")})
    if blocked:
        return JSONResponse(
            status_code=403,
            content={"detail": _detail("account_deletion_in_progress", retryable=False)},
        )
    return None


@router.delete("", response_model=AccountDeletionResponse)
def delete_current_account(payload: AccountDeletionRequest, request: Request) -> JSONResponse:
    user = getattr(request.state, "auth_user", None)
    owner_id = getattr(request.state, "user_id", None)
    authorization = request.headers.get("Authorization", "")
    if not user or not owner_id or user.user_id != owner_id or not authorization.startswith("Bearer "):
        raise HTTPException(401, detail=_detail("authentication_required", retryable=False))
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, detail=_detail("authentication_required", retryable=False))
    if request.query_params:
        raise HTTPException(422, detail=_detail("account_deletion_invalid_request", retryable=False))
    try:
        status = delete_account(owner_id)
    except AccountDeletionError as exc:
        raise HTTPException(503, detail=_detail(exc.code), headers={"Retry-After": "30"}) from None
    except PersistenceError:
        raise HTTPException(
            503, detail=_detail("account_deletion_persistence_unavailable"), headers={"Retry-After": "30"}
        ) from None
    return JSONResponse(
        status_code=200 if status == "deleted" else 202,
        content=AccountDeletionResponse(status=status).model_dump(),
        headers={} if status == "deleted" else {"Retry-After": "30"},
    )


@worker_router.api_route("/run", methods=["GET", "POST"])
def run_account_deletion_worker(request: Request) -> dict[str, int]:
    try:
        secret = account_deletion_worker_secret()
    except AccountDeletionError:
        raise HTTPException(503, detail=_detail("account_deletion_unavailable")) from None
    authorization = request.headers.get("Authorization", "")
    if not secrets.compare_digest(authorization.encode(), f"Bearer {secret}".encode()):
        raise HTTPException(401, detail=_detail("authentication_required", retryable=False))
    if request.query_params:
        raise HTTPException(422, detail=_detail("account_deletion_invalid_request", retryable=False))
    try:
        return run_account_deletion_jobs()
    except AccountDeletionError as exc:
        raise HTTPException(503, detail=_detail(exc.code)) from None
    except PersistenceError:
        raise HTTPException(503, detail=_detail("account_deletion_persistence_unavailable")) from None
