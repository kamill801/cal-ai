from __future__ import annotations

from dataclasses import replace
from datetime import datetime, date

import pytest
from fastapi.testclient import TestClient

from app import main
from app.coach_schemas import CoachProfile, WeightLogResponse
from app.services import coach as coach_service
from app.services.auth import AuthenticatedUser
from app.services.coach_repository import get_coach_repository
from app.services.persistence import get_persistence_repository


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


def _create_meal_job(headers: dict[str, str] | None = None) -> str:
    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": _upload_body_photo(headers), "meal_type": "lunch"},
        headers=headers,
    )
    assert response.status_code == 200
    job_id = response.json()["analysis_job_id"]
    assert client.get(f"/v1/analysis-jobs/{job_id}", headers=headers).status_code == 200
    assert client.post(
        f"/v1/analysis-jobs/{job_id}/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
        headers=headers,
    ).status_code == 200
    return job_id


def _log_meal(profile_id: str, job_id: str, logged_on: str, headers: dict[str, str] | None = None) -> None:
    response = client.post(
        "/v1/meal-logs",
        json={
            "profile_id": profile_id,
            "analysis_job_id": job_id,
            "result_id": "analysis-lunch-001",
            "clarification_value": "one_bowl",
            "logged_on": logged_on,
        },
        headers=headers,
    )
    assert response.status_code == 200


def _freeze_service_now(monkeypatch: pytest.MonkeyPatch, now: datetime) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz=None) -> datetime:
            return now.astimezone(tz) if tz else now

    monkeypatch.setattr(coach_service, "datetime", FrozenDateTime)


def _install_auth(monkeypatch: pytest.MonkeyPatch, owner_id: str = "weekly-owner") -> dict[str, str]:
    monkeypatch.setattr(main, "authenticate_bearer_token", lambda authorization: AuthenticatedUser(user_id=owner_id) if authorization else None)
    return {"Authorization": f"Bearer {owner_id}"}


def _log_completed_workout(
    profile_id: str,
    plan: dict,
    performed_on: str,
    headers: dict[str, str] | None = None,
) -> None:
    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": plan["days"][0]["id"],
            "performed_on": performed_on,
            "duration_minutes": 45,
            "completed_exercise_ids": [exercise["id"] for exercise in plan["days"][0]["exercises"]],
            "session_rpe": 7,
        },
        headers=headers,
    )
    assert response.status_code == 200


def _log_body_check_in(
    profile_id: str,
    captured_on: str,
    headers: dict[str, str],
) -> None:
    response = client.post(
        f"/v1/profiles/{profile_id}/body-check-ins",
        json={
            "captured_on": captured_on,
            "image_upload_id": _upload_body_photo(headers),
            "view": "front",
            "consent_to_ai_analysis": True,
        },
        headers=headers,
    )
    assert response.status_code == 200


class _MalformedDateCoachRepository:
    def __init__(self, profile: CoachProfile) -> None:
        self.profile = profile

    def get_profile(self, profile_id: str) -> CoachProfile | None:
        return self.profile if profile_id == self.profile.profile_id else None

    def list_weight_logs(self, profile_id: str) -> list[WeightLogResponse]:
        return [
            WeightLogResponse.model_construct(
                id="legacy-weight-bad-date",
                profile_id=profile_id,
                logged_on="not-a-date",
                weight_kg=82.0,
                created_at="2026-10-14T00:00:00+09:00",
            )
        ]

    def list_wellness(self, profile_id: str) -> list[object]:
        return []

    def list_body_check_ins(self, profile_id: str) -> list[object]:
        return []

    def list_workout_sessions(self, profile_id: str) -> list[object]:
        return []

    def get_workout_plan(self, profile_id: str) -> None:
        return None


class _EmptyMealRepository:
    def list_meal_logs(self) -> list[object]:
        return []


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


def test_weekly_coach_uses_neutral_baseline_language_for_sparse_evidence(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-08-19T12:00:00+09:00"))
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


def test_weekly_coach_acknowledges_partial_workout_without_counting_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-14T12:00:00+09:00"))
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]
    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-10-14",
            "duration_minutes": 30,
            "completed_exercise_ids": [day["exercises"][0]["id"]],
            "session_rpe": 7,
        },
    )
    assert response.status_code == 200
    assert response.json()["completed"] is False

    body = client.get(f"/v1/profiles/{profile_id}/weekly-coach").json()
    assert body["evidence"]["workouts_completed"] == 0
    assert body["score"] == 0
    assert "기록이 없" not in body["headline"]
    assert "부분 운동 기록 1회를 확인했어요." in body["wins"]
    assert not any("운동 수행 기록이 없어" in item for item in body["focus_items"])


def test_weekly_coach_uses_korea_calendar_week_for_recorded_activity_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-11T15:00:00+00:00"))
    headers = _install_auth(monkeypatch)
    profile_id = _create_profile(headers=headers)
    meal_job_id = _create_meal_job(headers)
    for logged_on in ("2026-10-05", "2026-10-12", "2026-10-18", "2026-10-19"):
        _log_meal(profile_id, meal_job_id, logged_on, headers)
    for logged_on, weight in (
        ("2026-10-05", 82.2),
        ("2026-10-12", 82.0),
        ("2026-10-18", 81.8),
        ("2026-10-19", 81.7),
    ):
        assert client.post(f"/v1/profiles/{profile_id}/weight-logs", json={"logged_on": logged_on, "weight_kg": weight}, headers=headers).status_code == 200
        assert client.post(
            f"/v1/profiles/{profile_id}/wellness-check-ins",
            json={"logged_on": logged_on, "energy": 3, "sleep_quality": 3, "soreness": 2},
            headers=headers,
        ).status_code == 200

    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate", headers=headers).json()
    for created_at, performed_on in (
        ("2026-10-14T12:00:00+09:00", "2026-10-05"),
        ("2026-10-19T00:00:00+09:00", "2026-10-12"),
        ("2026-10-20T00:00:00+09:00", "2026-10-18"),
    ):
        monkeypatch.setattr(coach_service, "now_iso", lambda created_at=created_at: created_at)
        _log_completed_workout(profile_id, plan, performed_on, headers)

    for created_at, captured_on in (
        ("2026-10-14T12:00:00+09:00", "2026-10-05"),
        ("2026-10-19T00:00:00+09:00", "2026-10-12"),
        ("2026-10-20T00:00:00+09:00", "2026-10-18"),
    ):
        monkeypatch.setattr(coach_service, "now_iso", lambda created_at=created_at: created_at)
        _log_body_check_in(profile_id, captured_on, headers)

    body = client.get(f"/v1/profiles/{profile_id}/weekly-coach", headers=headers).json()

    assert body["evidence"] == {
        "meals_logged": 2,
        "workouts_completed": 2,
        "weight_logs": 2,
        "wellness_check_ins": 2,
        "body_check_ins": 2,
    }
    assert body["score"] == 61


def test_weekly_coach_excludes_previous_week_partial_workout(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-14T12:00:00+09:00"))
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]
    monkeypatch.setattr(coach_service, "now_iso", lambda: "2026-10-14T12:00:00+09:00")
    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-10-05",
            "duration_minutes": 30,
            "completed_exercise_ids": [day["exercises"][0]["id"]],
            "session_rpe": 7,
        },
    )
    assert response.status_code == 200
    assert response.json()["completed"] is False

    body = client.get(f"/v1/profiles/{profile_id}/weekly-coach").json()

    assert body["evidence"]["workouts_completed"] == 0
    assert body["score"] == 0
    assert "기록이 없" in body["headline"]
    assert "부분 운동 기록 1회를 확인했어요." not in body["wins"]


def test_weekly_coach_uses_next_sunday_as_current_week_cutoff(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-18T14:59:59+00:00"))
    profile_id = _create_profile()
    for logged_on, weight in (("2026-10-18", 81.8), ("2026-10-19", 81.7)):
        assert client.post(f"/v1/profiles/{profile_id}/weight-logs", json={"logged_on": logged_on, "weight_kg": weight}).status_code == 200

    body = client.get(f"/v1/profiles/{profile_id}/weekly-coach").json()

    assert body["evidence"]["weight_logs"] == 1
    assert body["wins"] == ["체중 기록 1회를 확인했어요."]


def test_current_calendar_week_window_uses_korea_clock_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-18T14:59:59+00:00"))
    assert coach_service._current_calendar_week_window() == (date(2026, 10, 12), date(2026, 10, 19))

    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-18T15:00:00+00:00"))
    assert coach_service._current_calendar_week_window() == (date(2026, 10, 19), date(2026, 10, 26))


def test_weekly_coach_skips_malformed_legacy_recorded_date(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-14T12:00:00+09:00"))
    profile_id = _create_profile()
    profile = coach_service.require_profile(profile_id, get_coach_repository())

    body = coach_service.weekly_coach(
        profile_id,
        repository=_MalformedDateCoachRepository(profile),
        meal_repository=_EmptyMealRepository(),
    )

    assert body.evidence.weight_logs == 0
    assert body.score == 0
    assert "기록이 없" in body.headline


def test_weekly_coach_skips_malformed_legacy_meal_date(monkeypatch: pytest.MonkeyPatch) -> None:
    _freeze_service_now(monkeypatch, datetime.fromisoformat("2026-10-14T12:00:00+09:00"))
    profile_id = _create_profile()
    _log_meal(profile_id, _create_meal_job(), "2026-10-14")
    repository = get_persistence_repository()
    record = repository.list_meal_logs()[0]
    legacy_dashboard = record.response.dashboard.model_copy(update={"date": "not-a-date"})
    legacy_record = replace(
        record,
        request=record.request.model_copy(update={"logged_on": None}),
        response=record.response.model_copy(update={"dashboard": legacy_dashboard}),
    )
    monkeypatch.setattr(repository, "list_meal_logs", lambda: [legacy_record])

    response = client.get(f"/v1/profiles/{profile_id}/weekly-coach")

    assert response.status_code == 200
    assert response.json()["evidence"]["meals_logged"] == 0
    assert response.json()["score"] == 0


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
