from __future__ import annotations

import hmac
import os
from urllib.parse import urlsplit

import httpx
from pydantic import BaseModel, Field, SecretStr

from app.services.analytics_repository import get_analytics_repository
from app.services.auth import authenticate_admin_bearer_token, AuthenticationError


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: SecretStr = Field(min_length=1, max_length=1024)


class AdminLoginFailure(Exception):
    def __init__(self, status: int) -> None:
        self.status = status
        super().__init__("admin_login_failed")


def login_owner(payload: AdminLoginRequest) -> dict[str, str]:
    if os.getenv("ADMIN_DASHBOARD_ENABLED", "false").strip().lower() != "true":
        raise AdminLoginFailure(404)
    url = os.getenv("ADMIN_SUPABASE_URL", "").rstrip("/")
    username = os.getenv("ADMIN_LOGIN_USERNAME", "").strip()
    email = os.getenv("ADMIN_LOGIN_EMAIL", "").strip()
    key = os.getenv("ADMIN_SUPABASE_PUBLISHABLE_KEY", "").strip()
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path or not username or not email
            or not key or not os.getenv("ADMIN_USER_IDS", "").strip()):
        raise AdminLoginFailure(503)
    if not hmac.compare_digest(payload.username.strip().encode(), username.encode()):
        raise AdminLoginFailure(401)
    # Unknown aliases do not consume the owner's shared credential-attempt budget.
    if not get_analytics_repository().consume_admin_login_attempt():
        raise AdminLoginFailure(429)
    try:
        response = httpx.post(
            f"{url}/auth/v1/token?grant_type=password",
            headers={"apikey": key},
            json={"email": email, "password": payload.password.get_secret_value()},
            timeout=10,
            follow_redirects=False,
        )
        if response.status_code == 429:
            raise AdminLoginFailure(429)
        if response.status_code in {400, 401, 403, 422}:
            raise AdminLoginFailure(401)
        if response.status_code != 200:
            raise AdminLoginFailure(503)
        data = response.json()
        access_token, refresh_token = data.get("access_token"), data.get("refresh_token")
        if not isinstance(access_token, str) or not access_token or not isinstance(refresh_token, str) or not refresh_token:
            raise AdminLoginFailure(503)
        authenticate_admin_bearer_token(f"Bearer {access_token}")
    except AuthenticationError:
        raise AdminLoginFailure(401) from None
    except (httpx.HTTPError, ValueError, AttributeError):
        raise AdminLoginFailure(503) from None
    # Do not forward provider response metadata, identity fields, or error bodies.
    return {"access_token": access_token, "refresh_token": refresh_token}
