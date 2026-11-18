from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.recruitment_schemas import (
    POLICY_RETENTION_DAYS, POLICY_VERSION, RecruitmentApplication, RecruitmentConfigResponse,
)
from app.services.recruitment_repository import get_recruitment_repository

DEFAULT_INSTALL_URL = (
    "https://expo.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/"
    "builds/0ed6f218-7210-4ecf-9238-c522fa669bed"
)
DEFAULT_PUBLIC_ORIGIN = "https://cal-ai-api.vercel.app"
INSTALL_URL_PATTERN = re.compile(
    r"https://expo\.dev/accounts/arche-trustfirstnutrition/projects/trust-first-nutrition/builds/"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)


@dataclass(frozen=True)
class RecruitmentSettings:
    config: RecruitmentConfigResponse
    install_url: str | None
    public_origin: str | None


def _production_environment(env: Mapping[str, str]) -> bool:
    return env.get("VERCEL") == "1" or any(
        env.get(key, "").strip().lower() in {"production", "prod"}
        for key in ("APP_ENV", "VERCEL_ENV", "ENVIRONMENT")
    )


def _public_origin(raw: str, env: Mapping[str, str]) -> str | None:
    try:
        url = urlsplit(raw)
        _ = url.port
        if (url.username or url.password or url.query or url.fragment or url.path not in ("", "/")
                or not url.hostname or any(c.isspace() or ord(c) < 33 for c in raw)
                or "?" in raw or "#" in raw or "\\" in raw):
            return None
        local = url.hostname in {"localhost", "127.0.0.1", "::1"}
        production = _production_environment(env)
        if local and production or url.scheme != "https" and not (local and url.scheme == "http" and not production):
            return None
        return f"{url.scheme}://{url.netloc}"
    except ValueError:
        return None


def load_recruitment_settings(environ: Mapping[str, str] | None = None) -> RecruitmentSettings:
    env = os.environ if environ is None else environ
    raw_url = env.get("BETA_ANDROID_INSTALL_URL", DEFAULT_INSTALL_URL)
    install_url = raw_url if INSTALL_URL_PATTERN.fullmatch(raw_url) else None
    origin = _public_origin(env.get("BETA_RECRUITMENT_PUBLIC_ORIGIN", DEFAULT_PUBLIC_ORIGIN), env)
    try:
        days = int(env.get("BETA_RECRUITMENT_RETENTION_DAYS", str(POLICY_RETENTION_DAYS)))
        # Changing retention requires a new consent policy, not an environment override.
        valid_days = days == POLICY_RETENTION_DAYS
    except ValueError:
        valid_days = False
    durable_database = (not _production_environment(env)
                        or env.get("DATABASE_URL", "").startswith(("postgres://", "postgresql://")))
    accepting = bool(env.get("BETA_RECRUITMENT_ENABLED") == "true"
                     and env.get("BETA_RECRUITMENT_RETENTION_ENABLED") == "true"
                     and env.get("BETA_RECRUITMENT_POLICY_APPROVED_VERSION") == POLICY_VERSION
                     and install_url and origin and valid_days and durable_database)
    return RecruitmentSettings(RecruitmentConfigResponse(accepting=accepting), install_url, origin)


def accept_application(payload: RecruitmentApplication, settings: RecruitmentSettings) -> dict:
    get_recruitment_repository().save_application(payload.email, payload.policy_version, settings.config.retention_days,
                                                 retention_enabled=settings.config.accepting)
    return {"accepted": True, "delivery": "on_page", "install_url": settings.install_url, "app_version": "0.1.2"}


def cleanup_expired_recruitment(environ: Mapping[str, str] | None = None) -> int:
    """Explicit beta-only cleanup; this function does not install a scheduler."""
    env = os.environ if environ is None else environ
    if env.get("BETA_RECRUITMENT_RETENTION_ENABLED") != "true":
        return 0
    return get_recruitment_repository(env).purge_expired(retention_enabled=True)
