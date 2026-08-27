from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import main
from app.services.auth import AuthenticatedUser


client = TestClient(main.app)


def _create_profile(
    *,
    training_frequency: str = "3-4",
    experience_level: str = "beginner",
    available_equipment: list[str] | None = None,
    session_minutes: int = 60,
    headers: dict[str, str] | None = None,
) -> str:
    response = client.post(
        "/v1/onboarding",
        json={
            "age": 29,
            "sex": "male",
            "height_cm": 176,
            "current_weight_kg": 82,
            "target_weight_kg": 76,
            "goal_type": "recomp",
            "activity_level": "moderate",
            "training_frequency": training_frequency,
            "experience_level": experience_level,
            "available_equipment": available_equipment or ["gym"],
            "session_minutes": session_minutes,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["profile_id"]


def _upload_body_photo(headers: dict[str, str] | None = None) -> str:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "coach-quality-body-photo",
            "file_name": "body-front.png",
            "content_type": "image/png",
            "byte_size": 420_000,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response.json()["image_upload_id"]


def test_weekly_coach_is_zero_and_explicitly_no_data_without_records() -> None:
    profile_id = _create_profile()

    response = client.get(f"/v1/profiles/{profile_id}/weekly-coach")

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 0
    assert "기록이 없" in body["headline"]
    assert body["wins"] == []
    assert set(body["evidence"].values()) == {0}
    assert any("식사" in action for action in body["next_week_actions"])


def test_weekly_coach_uses_neutral_baseline_language_for_sparse_evidence() -> None:
    profile_id = _create_profile()
    response = client.post(
        f"/v1/profiles/{profile_id}/wellness-check-ins",
        json={
            "logged_on": "2026-08-18",
            "energy": 3,
            "sleep_quality": 3,
            "soreness": 2,
        },
    )
    assert response.status_code == 200

    body = client.get(f"/v1/profiles/{profile_id}/weekly-coach").json()

    assert body["score"] == 5
    assert "기준선" in body["headline"]
    assert body["evidence"]["wellness_check_ins"] == 1
    assert body["wins"] == ["회복 상태 기록 1회를 확인했어요."]
    combined_copy = " ".join([body["headline"], *body["wins"], *body["focus_items"]])
    assert all(term not in combined_copy for term in ("잘했", "훌륭", "성공", "충분히"))


def test_short_beginner_bodyweight_plan_is_compact_and_conservative() -> None:
    profile_id = _create_profile(
        training_frequency="1-2",
        experience_level="beginner",
        available_equipment=["bodyweight"],
        session_minutes=30,
    )

    response = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate")

    assert response.status_code == 200
    plan = response.json()
    assert plan["days_per_week"] == 2
    assert len(plan["days"]) == 2
    assert all(len(day["exercises"]) == 3 for day in plan["days"])
    assert all(exercise["sets"] == 2 for day in plan["days"] for exercise in day["exercises"])
    assert all(exercise["target_rir"] >= 3 for day in plan["days"] for exercise in day["exercises"])
    exercise_names = " ".join(exercise["name"] for day in plan["days"] for exercise in day["exercises"])
    assert all(term not in exercise_names for term in ("바벨", "케이블", "머신", "랫풀다운", "레그프레스"))
    assert "운동 경력: 입문" in plan["personalization_basis"]
    assert "사용 장비: 맨몸" in plan["personalization_basis"]
    assert "세션 시간: 30분" in plan["personalization_basis"]


def test_long_advanced_gym_plan_uses_frequency_volume_and_skill_level() -> None:
    profile_id = _create_profile(
        training_frequency="5+",
        experience_level="advanced",
        available_equipment=["gym"],
        session_minutes=90,
    )

    response = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate")

    assert response.status_code == 200
    plan = response.json()
    assert plan["days_per_week"] == 5
    assert len(plan["days"]) == 5
    assert all(len(day["exercises"]) == 5 for day in plan["days"])
    assert all(exercise["sets"] >= 4 for day in plan["days"] for exercise in day["exercises"])
    assert all(exercise["target_rir"] == 1 for day in plan["days"] for exercise in day["exercises"])
    assert "운동 경력: 숙련" in plan["personalization_basis"]
    assert "사용 장비: 헬스장" in plan["personalization_basis"]
    assert "세션 시간: 90분" in plan["personalization_basis"]


def test_latest_recovery_and_body_focus_reduce_load_and_change_program_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "authenticate_bearer_token", lambda authorization: AuthenticatedUser(user_id="quality-owner") if authorization else None)
    headers = {"Authorization": "Bearer quality-owner"}
    profile_id = _create_profile(
        training_frequency="3-4",
        experience_level="intermediate",
        available_equipment=["gym"],
        session_minutes=60,
        headers=headers,
    )
    wellness_response = client.post(
        f"/v1/profiles/{profile_id}/wellness-check-ins",
        json={
            "logged_on": "2026-08-18",
            "energy": 2,
            "sleep_quality": 2,
            "soreness": 4,
        },
        headers=headers,
    )
    assert wellness_response.status_code == 200
    body_response = client.post(
        f"/v1/profiles/{profile_id}/body-check-ins",
        json={
            "captured_on": "2026-08-18",
            "image_upload_id": _upload_body_photo(headers),
            "view": "front",
            "consent_to_ai_analysis": True,
        },
        headers=headers,
    )
    assert body_response.status_code == 200

    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate", headers=headers).json()

    assert all(len(day["exercises"]) == 3 for day in plan["days"])
    assert all(exercise["target_rir"] >= 3 for day in plan["days"] for exercise in day["exercises"])
    assert any("최근 몸 체크인" in exercise["rationale"] for day in plan["days"] for exercise in day["exercises"])
    assert any("회복 조절" in basis for basis in plan["personalization_basis"])
    assert any("몸 체크인 초점" in basis for basis in plan["personalization_basis"])
