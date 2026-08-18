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


@lru_cache(maxsize=8)
def _jwk_client(issuer: str) -> PyJWKClient:
    return PyJWKClient(f"{issuer}/.well-known/jwks.json", cache_jwk_set=True, lifespan=600)


def authenticate_bearer_token(
    authorization: str | None,
    environ: Mapping[str, str] | None = None,
) -> AuthenticatedUser | None:
    env = environ if environ is not None else os.environ
    provider = env.get("AUTH_PROVIDER", "disabled").strip().lower() or "disabled"
    if provider == "disabled":
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
    return AuthenticatedUser(user_id=subject)
