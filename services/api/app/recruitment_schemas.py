from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

POLICY_VERSION = "2026-11-18.1"
POLICY_RETENTION_DAYS = 30


class RecruitmentConfigResponse(BaseModel):
    accepting: bool
    policy_version: Literal["2026-11-18.1"] = POLICY_VERSION
    retention_days: Literal[30] = POLICY_RETENTION_DAYS
    delivery: Literal["on_page"] = "on_page"
    min_age: int = 18
    platform: Literal["android"] = "android"
    support_email: str = "areche.ai.kr@gmail.com"


class RecruitmentApplication(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    email: str = Field(min_length=3, max_length=254)
    platform: Literal["android"]
    adult_confirmed: Literal[True]
    privacy_consent: Literal[True]
    policy_version: Literal["2026-11-18.1"]
    website: str = Field(max_length=200)

    @field_validator("adult_confirmed", "privacy_consent", mode="before")
    @classmethod
    def affirmative_boolean(cls, value):
        if value is not True:
            raise ValueError("affirmative_consent_required")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        local, separator, domain = value.partition("@")
        if (not value.isascii() or not separator or len(local) > 64
                or local.startswith(".") or local.endswith(".") or ".." in local
                or not re.fullmatch(r"[a-z0-9.!#$%&'*+/=?^_`{|}~-]+", local)
                or len(domain) > 253 or "." not in domain
                or any(not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                       for label in domain.split("."))):
            raise ValueError("invalid_email")
        return value
