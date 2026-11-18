from __future__ import annotations

import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import MutableHeaders
from starlette.requests import ClientDisconnect

from app.recruitment_schemas import RecruitmentApplication
from app.services.recruitment import accept_application, load_recruitment_settings
from app.services.recruitment_repository import RecruitmentLimitError, RecruitmentPersistenceError

MAX_BODY_BYTES = 4096


class RecruitmentRoute(APIRoute):
    async def handle(self, scope, receive, send):
        async def secure_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Cache-Control"] = "no-store"
                headers["X-Content-Type-Options"] = "nosniff"
            await send(message)
        if scope["type"] == "http" and scope["method"] not in self.methods:
            response = JSONResponse(status_code=405, headers={"Allow": ", ".join(sorted(self.methods))},
                                    content={"detail": {"code": "method_not_allowed", "message": "Method not allowed.",
                                                        "retryable": False, "kind": "validation"}})
            await response(scope, receive, secure_send)
            return
        await super().handle(scope, receive, secure_send)


router = APIRouter(prefix="/recruitment", tags=["recruitment"], route_class=RecruitmentRoute)


def error(status: int, code: str) -> JSONResponse:
    messages = {
        "recruitment_closed": "Applications are not currently available.",
        "origin_not_allowed": "Please submit from the application page.",
        "body_too_large": "The request is too large.",
        "validation_error": "Please check the application fields.",
        "recruitment_policy_changed": "Please reload and review the current privacy notice.",
        "recruitment_rate_limited": "Please try again after one hour.",
        "recruitment_capacity_reached": "Applications are temporarily unavailable.",
        "recruitment_unavailable": "The application could not be saved. Please try again later.",
    }
    return JSONResponse(status_code=status, content={"detail": {
        "code": code, "message": messages[code], "retryable": status in (429, 503),
        "kind": "server" if status == 503 else "validation",
    }})


@router.get("/config")
def recruitment_config():
    return load_recruitment_settings().config


@router.post("/applications", status_code=202)
async def recruitment_application(request: Request):
    settings = load_recruitment_settings()
    if not settings.config.accepting:
        return error(503, "recruitment_closed")
    if (request.headers.get("origin") != settings.public_origin
            or request.headers.get("sec-fetch-site") not in (None, "same-origin", "same-site")):
        return error(403, "origin_not_allowed")
    if (request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json"
            or request.headers.get("content-encoding", "identity").lower() != "identity"):
        return error(422, "validation_error")
    length = request.headers.get("content-length")
    if length is not None:
        if not length.isascii() or not length.isdecimal() or len(length) > 10:
            return error(413, "body_too_large")
        if int(length) > MAX_BODY_BYTES:
            return error(413, "body_too_large")
    data = bytearray()
    try:
        async for chunk in request.stream():
            if len(data) + len(chunk) > MAX_BODY_BYTES:
                return error(413, "body_too_large")
            data.extend(chunk)
        payload = RecruitmentApplication.model_validate(json.loads(data))
    except ValidationError as exc:
        stale = any(item["loc"] == ("policy_version",) and item["type"] == "literal_error"
                    for item in exc.errors(include_input=False))
        return error(409 if stale else 422, "recruitment_policy_changed" if stale else "validation_error")
    except (ValueError, UnicodeError, RecursionError, ClientDisconnect):
        return error(422, "validation_error")
    if payload.website:
        return JSONResponse(status_code=202, content={"accepted": True, "delivery": "on_page"})
    try:
        result = await run_in_threadpool(accept_application, payload, settings)
    except RecruitmentLimitError as exc:
        return error(429 if exc.code == "recruitment_rate_limited" else 503, exc.code)
    except RecruitmentPersistenceError:
        return error(503, "recruitment_unavailable")
    return JSONResponse(status_code=202, content=result)
