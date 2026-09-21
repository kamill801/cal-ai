from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.admin_schemas import AdminOverviewResponse, AdminUserDetailResponse, AdminUserId
from app.services.analytics_repository import get_analytics_repository
from app.services.auth import (
    AuthConfigurationError,
    AuthenticatedUser,
    AuthenticationError,
    authenticate_admin_bearer_token,
)
from app.services.persistence import PersistenceError
from app.services.admin_login import AdminLoginRequest, AdminLoginFailure, login_owner


router = APIRouter(prefix="/internal/admin", tags=["admin"])


@router.post("/login", include_in_schema=False)
def admin_login(payload: AdminLoginRequest, response: Response) -> dict[str, str]:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    try:
        return login_owner(payload)
    except AdminLoginFailure as exc:
        headers = {"Cache-Control": "no-store, max-age=0"}
        if exc.status == 429:
            headers["Retry-After"] = "900"
        raise HTTPException(status_code=exc.status, detail="admin_login_failed", headers=headers) from None
    except (AuthConfigurationError, PersistenceError):
        raise HTTPException(status_code=503, detail="admin_login_unavailable", headers={"Cache-Control": "no-store"}) from None


def require_admin(
    authorization: str | None = Header(default=None),
) -> AuthenticatedUser:
    try:
        return authenticate_admin_bearer_token(authorization)
    except AuthConfigurationError as exc:
        if str(exc) == "admin_dashboard_disabled":
            raise HTTPException(status_code=404, detail="not_found") from exc
        raise HTTPException(status_code=503, detail="admin_auth_unavailable") from exc
    except AuthenticationError as exc:
        status_code = 403 if str(exc) == "admin_forbidden" else 401
        raise HTTPException(status_code=status_code, detail="admin_access_denied") from exc


@router.get("/overview", response_model=AdminOverviewResponse)
def admin_overview(
    response: Response,
    admin: AuthenticatedUser = Depends(require_admin),
) -> AdminOverviewResponse:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    try:
        repository = get_analytics_repository()
        overview = repository.overview()
        repository.record_admin_audit(
            admin_user_id=admin.user_id,
            action="read",
            resource_type="overview",
        )
        return overview
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="admin_data_unavailable") from exc


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
def admin_user_detail(
    user_id: AdminUserId,
    response: Response,
    admin: AuthenticatedUser = Depends(require_admin),
) -> AdminUserDetailResponse:
    response.headers["Cache-Control"] = "no-store, max-age=0"
    try:
        repository = get_analytics_repository()
        detail = repository.user_detail(user_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="user_not_found")
        repository.record_admin_audit(
            admin_user_id=admin.user_id,
            action="read",
            resource_type="user",
            resource_id=user_id,
        )
        return detail
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="admin_data_unavailable") from exc
