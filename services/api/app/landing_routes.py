from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from app.services.web_surface import web_app_enabled

WEB_DIRECTORY = Path(__file__).parent / "web" / "beta"
PRESERVED_APP = Path(__file__).parent / "web" / "preserved-app" / "index.html"
SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "Content-Security-Policy": (
        "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; "
        "connect-src 'self'; font-src 'self'; base-uri 'none'; frame-ancestors 'none'; "
        "form-action 'self'; object-src 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
router = APIRouter(include_in_schema=False)


@router.api_route("/", methods=["GET", "HEAD"])
@router.api_route("/beta", methods=["GET", "HEAD"])
@router.api_route("/beta/", methods=["GET", "HEAD"])
def landing_page(request: Request):
    if request.query_params.get("action") == "delete-account":
        target = "/app?action=delete-account" if web_app_enabled() else "/account-deletion"
        return RedirectResponse(target, status_code=307, headers=SECURITY_HEADERS)
    if request.url.path == "/" and web_app_enabled():
        return preserved_app()
    return FileResponse(WEB_DIRECTORY / "index.html", media_type="text/html", headers=SECURITY_HEADERS)


def preserved_app():
    headers = {"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer"}
    if not PRESERVED_APP.is_file():
        return JSONResponse({"detail": {"code": "web_app_build_unavailable"}}, status_code=503, headers=headers)
    return FileResponse(PRESERVED_APP, media_type="text/html", headers=headers)


@router.api_route("/app", methods=["GET", "HEAD"])
@router.api_route("/app/{path:path}", methods=["GET", "HEAD"])
@router.api_route("/index.html", methods=["GET", "HEAD"])
@router.api_route("/auth/callback", methods=["GET", "HEAD"])
@router.api_route("/auth/callback/", methods=["GET", "HEAD"])
def web_app_entry(path: str = ""):
    if web_app_enabled():
        return preserved_app()
    return RedirectResponse("/", status_code=307, headers=SECURITY_HEADERS)
