from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Mapping

import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError, PyJWTError


class AuthConfigurationError(RuntimeError):
    pass


class AuthenticationError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    provider: str | None = None
    email: str | None = None
    display_name: str | None = None


@lru_cache(maxsize=8)
def _jwk_client(issuer: str) -> PyJWKClient:
    return PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_jwk_set=True, lifespan=600)


def authentication_required(environ: Mapping[str, str] | None = None) -> bool:
    env = environ if environ is not None else os.environ
    return (
        env.get("APP_ENV", "").strip().lower() == "production"
        or env.get("VERCEL_ENV", "").strip().lower() in {"production", "preview"}
    )


def authenticate_bearer_token(
    authorization: str | None,
    environ: Mapping[str, str] | None = None,
) -> AuthenticatedUser | None:
    env = environ if environ is not None else os.environ
    provider = env.get("AUTH_PROVIDER", "disabled").strip().lower() or "disabled"
    if provider == "disabled":
        if authentication_required(env):
            raise AuthConfigurationError("production_auth_required")
        return None
    if provider != "supabase":
        raise AuthConfigurationError("auth_provider_unknown")
    supabase_url = (env.get("SUPABASE_URL") or "").rstrip("/")
    if not supabase_url.startswith("https://"):
        raise AuthConfigurationError("supabase_url_missing")
    algorithm = (env.get("SUPABASE_JWT_ALGORITHM") or "").strip().upper()
    if algorithm not in {"RS256", "ES256"}:
        raise AuthConfigurationError("supabase_asymmetric_jwt_required")
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("bearer_token_missing")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("bearer_token_missing")

    return _authenticate_supabase_bearer_token(
        authorization,
        supabase_url=supabase_url,
        algorithm=algorithm,
    )


def authenticate_admin_bearer_token(
    authorization: str | None,
    environ: Mapping[str, str] | None = None,
) -> AuthenticatedUser:
    env = environ if environ is not None else os.environ
    if env.get("ADMIN_DASHBOARD_ENABLED", "false").strip().lower() != "true":
        raise AuthConfigurationError("admin_dashboard_disabled")
    supabase_url = (env.get("ADMIN_SUPABASE_URL") or "").rstrip("/")
    if not supabase_url.startswith("https://"):
        raise AuthConfigurationError("admin_supabase_url_missing")
    algorithm = (env.get("ADMIN_SUPABASE_JWT_ALGORITHM") or "").strip().upper()
    if algorithm not in {"RS256", "ES256"}:
        raise AuthConfigurationError("admin_supabase_asymmetric_jwt_required")
    user = _authenticate_supabase_bearer_token(
        authorization,
        supabase_url=supabase_url,
        algorithm=algorithm,
    )
    allowed_user_ids = {
        value.strip()
        for value in (env.get("ADMIN_USER_IDS") or "").split(",")
        if value.strip()
    }
    if not allowed_user_ids:
        raise AuthConfigurationError("admin_user_ids_missing")
    if user.user_id not in allowed_user_ids:
        raise AuthenticationError("admin_forbidden")
    return user


def _authenticate_supabase_bearer_token(
    authorization: str | None,
    *,
    supabase_url: str,
    algorithm: str,
) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("bearer_token_missing")
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("bearer_token_missing")

    issuer = f"{supabase_url}/auth/v1"
    try:
        signing_key = _jwk_client(issuer).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=issuer,
            options={"require": ["exp", "iss", "sub"]},
        )
    except (PyJWTError, PyJWKClientError, ValueError) as exc:
        raise AuthenticationError("bearer_token_invalid") from exc
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AuthenticationError("bearer_token_subject_missing")
    app_metadata = claims.get("app_metadata") if isinstance(claims.get("app_metadata"), dict) else {}
    user_metadata = claims.get("user_metadata") if isinstance(claims.get("user_metadata"), dict) else {}
    provider = app_metadata.get("provider")
    email = claims.get("email")
    display_name = user_metadata.get("full_name") or user_metadata.get("name") or user_metadata.get("nickname")
    return AuthenticatedUser(
        user_id=subject,
        provider=provider if isinstance(provider, str) else None,
        email=email if isinstance(email, str) else None,
        display_name=display_name if isinstance(display_name, str) else None,
    )
