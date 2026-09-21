from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app import main
from app.services import auth, coach


ONBOARDING_PAYLOAD = {
    "age": 29,
    "sex": "male",
    "height_cm": 176,
    "current_weight_kg": 82,
    "target_weight_kg": 76,
    "goal_type": "recomp",
    "activity_level": "moderate",
    "training_frequency": "3-4",
    "experience_level": "beginner",
    "available_equipment": ["gym"],
    "session_minutes": 60,
}


def _headers(owner_id: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {owner_id}"} if owner_id else {}


def _install_verified_owner_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_authentication(authorization: str | None) -> auth.AuthenticatedUser | None:
        if not authorization:
            return None
        return auth.AuthenticatedUser(user_id=authorization.removeprefix("Bearer "))

    monkeypatch.setattr(main, "authenticate_bearer_token", fake_authentication)


def _install_created_at_sequence(monkeypatch: pytest.MonkeyPatch, values: list[str]) -> None:
    sequence: Iterator[str] = iter(values)
    monkeypatch.setattr(coach, "now_iso", lambda: next(sequence))


def _create_profile(client: TestClient, owner_id: str | None = None) -> str:
    response = client.post("/v1/onboarding", headers=_headers(owner_id), json=ONBOARDING_PAYLOAD)
    assert response.status_code == 200
    return response.json()["profile_id"]


def test_current_profile_uses_authenticated_owner_and_newest_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_verified_owner_auth(monkeypatch)
    _install_created_at_sequence(
        monkeypatch,
        [
            "2026-09-07T00:00:00.000001+00:00",
            "2026-09-07T00:00:00.000002+00:00",
            "2026-09-07T00:00:00.000003+00:00",
        ],
    )

    with TestClient(main.app) as client:
        _create_profile(client, "owner-a")
        owner_b_profile_id = _create_profile(client, "owner-b")
        owner_a_newest_profile_id = _create_profile(client, "owner-a")

        owner_a_response = client.get(
            "/v1/profiles/me?owner_id=owner-b&profile_id=forged",
            headers=_headers("owner-a"),
        )
        owner_b_response = client.get("/v1/profiles/me", headers=_headers("owner-b"))

    assert owner_a_response.status_code == 200
    assert owner_a_response.json() == {"profile_id": owner_a_newest_profile_id}
    assert owner_b_response.status_code == 200
    assert owner_b_response.json() == {"profile_id": owner_b_profile_id}


def test_current_profile_returns_null_for_authenticated_owner_without_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_verified_owner_auth(monkeypatch)

    with TestClient(main.app) as client:
        _create_profile(client, "owner-a")
        response = client.get("/v1/profiles/me", headers=_headers("owner-without-profile"))

    assert response.status_code == 200
    assert response.json() == {"profile_id": None}


def test_current_profile_does_not_deserialize_other_owner_invalid_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_verified_owner_auth(monkeypatch)

    with TestClient(main.app) as client:
        owner_a_profile_id = _create_profile(client, "owner-a")
        with sqlite3.connect(os.environ["CAL_AI_API_DATA_PATH"]) as connection:
            connection.execute(
                "insert into coach_profiles (profile_id, payload_json, created_at, updated_at) values (?, ?, ?, ?)",
                (
                    "invalid-owner-b-profile",
                    json.dumps({"profile_id": "invalid-owner-b-profile", "owner_id": "owner-b"}),
                    "2026-09-07T00:00:00.000004+00:00",
                    "2026-09-07T00:00:00.000004+00:00",
                ),
            )
        response = client.get("/v1/profiles/me", headers=_headers("owner-a"))

    assert response.status_code == 200
    assert response.json() == {"profile_id": owner_a_profile_id}


def test_current_profile_returns_null_for_anonymous_request(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_verified_owner_auth(monkeypatch)

    with TestClient(main.app) as client:
        _create_profile(client, "owner-a")
        response = client.get("/v1/profiles/me")

    assert response.status_code == 200
    assert response.json() == {"profile_id": None}


def test_current_profile_auth_disabled_local_does_not_expose_profiles() -> None:
    with TestClient(main.app) as client:
        _create_profile(client)
        response = client.get("/v1/profiles/me", headers=_headers("owner-a"))

    assert response.status_code == 200
    assert response.json() == {"profile_id": None}
