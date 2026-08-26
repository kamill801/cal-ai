from __future__ import annotations

import json
import os
import sqlite3

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ImageUploadRequest
from app.services.coach_repository import get_coach_repository
from app.services.persistence import get_persistence_repository


client = TestClient(app)


def test_default_repositories_are_reused_for_concurrent_screen_loads() -> None:
    assert get_coach_repository() is get_coach_repository()
    assert get_persistence_repository() is get_persistence_repository()


def test_legacy_body_check_in_without_consent_remains_readable() -> None:
    profile_id = _create_profile()
    repository = get_coach_repository()
    legacy_payload = {
        "id": "legacy-body-check-in",
        "profile_id": profile_id,
        "captured_on": "2026-08-01",
        "image_upload_id": "legacy-upload",
        "view": "front",
        "analysis": {
            "provider": "mock",
            "confidence": "limited",
            "capture_quality": "good",
            "observations": [{"title": "기록 조건", "detail": "비교 가능한 사진이에요."}],
            "training_focus": ["기본 동작을 유지해요."],
            "comparison_note": "첫 기록이에요.",
            "safety_note": "의료 판단에 사용하지 않아요.",
        },
        "created_at": "2026-08-01T00:00:00+00:00",
    }
    with sqlite3.connect(os.environ["CAL_AI_API_DATA_PATH"]) as connection:
        connection.execute(
            "insert into coach_events (event_id, profile_id, event_type, payload_json, created_at) values (?, ?, ?, ?, ?)",
            (
                legacy_payload["id"],
                profile_id,
                "body",
                json.dumps(legacy_payload, ensure_ascii=False),
                legacy_payload["created_at"],
            ),
        )

    loaded = repository.list_body_check_ins(profile_id)

    assert loaded[0].id == "legacy-body-check-in"
    assert loaded[0].consent is None


def _create_profile() -> str:
    response = client.post(
        "/v1/onboarding",
        json={
            "age": 30,
            "sex": "other",
            "height_cm": 170,
            "current_weight_kg": 70,
            "target_weight_kg": 68,
            "goal_type": "recomp",
            "activity_level": "moderate",
            "training_frequency": "3-4",
            "experience_level": "intermediate",
            "available_equipment": ["dumbbells"],
            "session_minutes": 45,
        },
    )
    assert response.status_code == 200
    return response.json()["profile_id"]


def _create_analysis(profile_id: str | None = None) -> tuple[str, str, str]:
    upload_response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "quality-meal",
            "file_name": "quality-meal.jpg",
            "content_type": "image/jpeg",
            "byte_size": 320_000,
        },
    )
    assert upload_response.status_code == 200
    upload_id = upload_response.json()["image_upload_id"]
    job_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": upload_id, "profile_id": profile_id, "meal_type": "dinner"},
    )
    assert job_response.status_code == 200
    job_id = job_response.json()["analysis_job_id"]
    loaded = client.get(f"/v1/analysis-jobs/{job_id}")
    assert loaded.status_code == 200
    result_id = loaded.json()["result"]["id"]
    return upload_id, job_id, result_id


def test_manual_nutrition_override_is_saved_and_accumulated() -> None:
    profile_id = _create_profile()
    _, job_id, result_id = _create_analysis()

    response = client.post(
        "/v1/meal-logs",
        json={
            "profile_id": profile_id,
            "analysis_job_id": job_id,
            "result_id": result_id,
            "clarification_value": "unknown",
            "nutrition_override": {
                "meal_name": "직접 수정한 닭가슴살 덮밥",
                "calories_kcal": 510,
                "protein_g": 42,
                "carbs_g": 55,
                "fat_g": 12,
            },
        },
    )

    assert response.status_code == 200
    dashboard = response.json()["dashboard"]
    assert dashboard["consumed"] == {
        "calories_kcal": 510,
        "protein_g": 42,
        "carbs_g": 55,
        "fat_g": 12,
    }
    assert dashboard["meals"][0]["name"] == "직접 수정한 닭가슴살 덮밥"
    assert dashboard["meals"][0]["confidence_label"] == "manual"

    live_dashboard = client.get(f"/v1/profiles/{profile_id}/dashboard/today")
    assert live_dashboard.status_code == 200
    assert live_dashboard.json()["nutrition"]["consumed"]["protein_g"] == 42
    assert live_dashboard.json()["meals"][0]["name"] == "직접 수정한 닭가슴살 덮밥"


def test_profile_deletion_removes_profile_meals_and_images() -> None:
    profile_id = _create_profile()
    upload_id, job_id, result_id = _create_analysis()
    save_response = client.post(
        "/v1/meal-logs",
        json={
            "profile_id": profile_id,
            "analysis_job_id": job_id,
            "result_id": result_id,
            "clarification_value": "unknown",
        },
    )
    assert save_response.status_code == 200

    response = client.delete(f"/v1/profiles/{profile_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "deleted"
    assert response.json()["deleted_images"] == 1
    assert response.json()["deleted_meal_logs"] == 1
    assert get_coach_repository().get_profile(profile_id) is None
    assert get_persistence_repository().get_image_upload(upload_id) is None
    assert get_persistence_repository().get_analysis_job(job_id) is None
    assert get_persistence_repository().list_meal_logs(job_id) == []
    assert client.get(f"/v1/profiles/{profile_id}/dashboard/today").status_code == 404


def test_profile_deletion_rejects_unknown_profile() -> None:
    response = client.delete("/v1/profiles/missing-profile")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "profile_not_found"


def test_profile_deletion_removes_unsaved_analysis_and_image() -> None:
    profile_id = _create_profile()
    upload_id, job_id, _ = _create_analysis(profile_id)

    response = client.delete(f"/v1/profiles/{profile_id}")

    assert response.status_code == 200
    assert response.json()["deleted_images"] == 1
    assert response.json()["deleted_meal_logs"] == 0
    assert get_persistence_repository().get_image_upload(upload_id) is None
    assert get_persistence_repository().get_analysis_job(job_id) is None


def test_retention_cleanup_requires_secret_and_marks_expired_upload_deleted(monkeypatch) -> None:
    repository = get_persistence_repository()
    repository.save_image_upload(
        payload=ImageUploadRequest(
            local_asset_id="expired-photo",
            file_name="expired.jpg",
            content_type="image/jpeg",
            byte_size=123_000,
        ),
        image_upload_id="upload-expired",
        image_reference="local-image://uploads/expired.jpg",
        storage_provider="local",
        cleanup_after="2020-01-01T00:00:00+00:00",
    )
    monkeypatch.setenv("CRON_SECRET", "test-cleanup-secret")

    unauthorized = client.get("/internal/cleanup-images")
    response = client.get(
        "/internal/cleanup-images",
        headers={"Authorization": "Bearer test-cleanup-secret"},
    )

    assert unauthorized.status_code == 401
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    deleted = repository.get_image_upload("upload-expired")
    assert deleted is not None
    assert deleted.upload_status == "deleted"
    assert deleted.object_key is None
    assert deleted.image_reference == "deleted://upload-expired"


def test_deleting_image_state_keeps_object_key_for_retry() -> None:
    repository = get_persistence_repository()
    repository.save_image_upload(
        payload=ImageUploadRequest(
            local_asset_id="retry-photo",
            file_name="retry.jpg",
            content_type="image/jpeg",
            byte_size=100_000,
        ),
        image_upload_id="upload-retry",
        image_reference="r2://bucket/retry.jpg",
        storage_provider="r2",
        object_key="uploads/retry.jpg",
        cleanup_after="2020-01-01T00:00:00+00:00",
    )

    repository.mark_image_upload_deleting("upload-retry")

    deleting = repository.get_image_upload("upload-retry")
    assert deleting is not None
    assert deleting.upload_status == "deleting"
    assert deleting.object_key == "uploads/retry.jpg"
    assert [item.image_upload_id for item in repository.list_expired_image_uploads("2026-08-19T00:00:00+00:00")] == ["upload-retry"]


def test_workout_session_persists_real_performance_instead_of_assuming_completion() -> None:
    profile_id = _create_profile()
    plan_response = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate")
    assert plan_response.status_code == 200
    plan = plan_response.json()
    day = plan["days"][0]
    exercise = day["exercises"][0]

    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-08-19",
            "duration_minutes": 42,
            "completed_exercise_ids": [exercise["id"]],
            "exercise_performance": [
                {
                    "exercise_id": exercise["id"],
                    "sets_completed": 3,
                    "reps_completed": 8,
                    "load_kg": 22.5,
                }
            ],
            "session_rpe": 8,
        },
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False
    assert response.json()["duration_minutes"] == 42
    assert response.json()["session_rpe"] == 8
    assert response.json()["exercise_performance"][0]["load_kg"] == 22.5


def test_workout_session_rejects_performance_for_unknown_exercise() -> None:
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]

    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-08-19",
            "duration_minutes": 30,
            "completed_exercise_ids": [],
            "exercise_performance": [{"exercise_id": "unknown-exercise", "sets_completed": 1}],
            "session_rpe": 6,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "workout_exercise_not_found"


def test_workout_session_rejects_unknown_completed_exercise() -> None:
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]

    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-08-19",
            "duration_minutes": 30,
            "completed_exercise_ids": ["unknown-exercise"],
            "exercise_performance": [],
            "session_rpe": 6,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "workout_exercise_not_found"


def test_workout_session_rejects_performance_for_unchecked_exercise() -> None:
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]
    exercise = day["exercises"][0]

    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-08-19",
            "duration_minutes": 30,
            "completed_exercise_ids": [],
            "exercise_performance": [
                {
                    "exercise_id": exercise["id"],
                    "sets_completed": exercise["sets"],
                    "reps_completed": 10,
                    "load_kg": 20,
                    "effort": "easy",
                }
            ],
            "session_rpe": 7,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "workout_performance_not_completed"
    current_plan = client.get(f"/v1/profiles/{profile_id}/workout-plan").json()
    assert current_plan["days"][0]["exercises"][0]["progression_action"] == "collect_baseline"
    assert client.get(f"/v1/profiles/{profile_id}/workout-history").json()["total_sessions"] == 0


def test_partial_workout_does_not_advance_next_workout() -> None:
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]
    exercise = day["exercises"][0]

    response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-08-19",
            "duration_minutes": 30,
            "completed_exercise_ids": [exercise["id"]],
            "exercise_performance": [
                {
                    "exercise_id": exercise["id"],
                    "sets_completed": exercise["sets"],
                    "reps_completed": 8,
                    "load_kg": 20,
                    "effort": "on_target",
                }
            ],
            "session_rpe": 7,
        },
    )
    dashboard = client.get(f"/v1/profiles/{profile_id}/dashboard/today").json()

    assert response.status_code == 200
    assert response.json()["completed"] is False
    assert dashboard["training"]["completed_sessions"] == 0
    assert dashboard["training"]["next_workout_title"] == day["title"]


def test_confirmed_clarification_nutrition_is_the_saved_snapshot() -> None:
    profile_id = _create_profile()
    _, job_id, result_id = _create_analysis(profile_id)

    save_response = client.post(
        "/v1/meal-logs",
        json={
            "profile_id": profile_id,
            "analysis_job_id": job_id,
            "result_id": result_id,
            "clarification_value": "large_bowl",
            "logged_on": "2026-08-26",
        },
    )
    assert save_response.status_code == 200
    meal_id = save_response.json()["dashboard"]["meals"][0]["id"]

    repeat_response = client.post(
        f"/v1/profiles/{profile_id}/meal-logs/{meal_id}/repeat",
        json={"logged_on": "2026-08-26"},
    )

    assert save_response.json()["dashboard"]["consumed"] == {
        "calories_kcal": 765,
        "protein_g": 34,
        "carbs_g": 101,
        "fat_g": 22,
    }
    assert repeat_response.status_code == 200
    assert repeat_response.json()["dashboard"]["consumed"] == {
        "calories_kcal": 1530,
        "protein_g": 68,
        "carbs_g": 202,
        "fat_g": 44,
    }


def test_repeat_meal_rejects_invalid_calendar_date() -> None:
    profile_id = _create_profile()
    _, job_id, result_id = _create_analysis(profile_id)
    save_response = client.post(
        "/v1/meal-logs",
        json={
            "profile_id": profile_id,
            "analysis_job_id": job_id,
            "result_id": result_id,
            "clarification_value": "one_bowl",
            "logged_on": "2026-08-26",
        },
    )
    meal_id = save_response.json()["dashboard"]["meals"][0]["id"]

    response = client.post(
        f"/v1/profiles/{profile_id}/meal-logs/{meal_id}/repeat",
        json={"logged_on": "2026-99-99"},
    )

    assert response.status_code == 422


def test_confirmed_meal_can_repeat_without_new_analysis_and_delete_recalculates_totals() -> None:
    profile_id = _create_profile()
    _, job_id, result_id = _create_analysis(profile_id)
    save_response = client.post(
        "/v1/meal-logs",
        json={
            "profile_id": profile_id,
            "analysis_job_id": job_id,
            "result_id": result_id,
            "clarification_value": "unknown",
            "logged_on": "2026-08-26",
            "nutrition_override": {
                "meal_name": "닭가슴살 현미밥",
                "calories_kcal": 510,
                "protein_g": 42,
                "carbs_g": 55,
                "fat_g": 12,
            },
        },
    )
    original_id = save_response.json()["dashboard"]["meals"][0]["id"]
    jobs_before = len(get_persistence_repository().list_analysis_jobs())

    repeat_response = client.post(
        f"/v1/profiles/{profile_id}/meal-logs/{original_id}/repeat",
        json={"logged_on": "2026-08-26"},
    )

    assert repeat_response.status_code == 200
    repeated_dashboard = repeat_response.json()["dashboard"]
    assert repeated_dashboard["consumed"] == {
        "calories_kcal": 1020,
        "protein_g": 84,
        "carbs_g": 110,
        "fat_g": 24,
    }
    assert repeated_dashboard["meals"][0]["id"] != original_id
    assert len(get_persistence_repository().list_analysis_jobs()) == jobs_before

    history = client.get(f"/v1/profiles/{profile_id}/meal-logs").json()
    assert [meal["name"] for meal in history["meals"]] == ["닭가슴살 현미밥", "닭가슴살 현미밥"]

    delete_response = client.delete(f"/v1/profiles/{profile_id}/meal-logs/{original_id}")
    dashboard = client.get(f"/v1/profiles/{profile_id}/dashboard/today?logged_on=2026-08-26").json()
    assert delete_response.status_code == 200
    assert dashboard["nutrition"]["consumed"]["calories_kcal"] == 510
    assert dashboard["nutrition"]["consumed"]["protein_g"] == 42
    assert len(dashboard["meals"]) == 1


def test_workout_performance_updates_next_target_and_history() -> None:
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]
    exercise = day["exercises"][0]

    first_session = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-08-25",
            "duration_minutes": 42,
            "completed_exercise_ids": [exercise["id"]],
            "exercise_performance": [
                {
                    "exercise_id": exercise["id"],
                    "sets_completed": exercise["sets"],
                    "reps_completed": 12,
                    "load_kg": 20,
                    "effort": "easy",
                }
            ],
            "session_rpe": 7,
        },
    )
    assert first_session.status_code == 200

    updated_plan = client.get(f"/v1/profiles/{profile_id}/workout-plan").json()
    updated_exercise = updated_plan["days"][0]["exercises"][0]
    assert updated_exercise["last_performance"]["load_kg"] == 20
    assert updated_exercise["progression_action"] == "increase"
    assert updated_exercise["recommended_load_kg"] == 22.5
    assert "증량" in updated_exercise["recommendation_reason"]

    history = client.get(f"/v1/profiles/{profile_id}/workout-history").json()
    assert history["total_sessions"] == 1
    assert history["sessions"][0]["workout_title"] == day["title"]
    assert history["sessions"][0]["total_volume_kg"] == exercise["sets"] * 12 * 20


def test_low_recovery_blocks_workout_load_increase() -> None:
    profile_id = _create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    day = plan["days"][0]
    exercise = day["exercises"][0]
    client.post(
        f"/v1/profiles/{profile_id}/wellness-check-ins",
        json={"logged_on": "2026-08-26", "energy": 2, "sleep_quality": 2, "soreness": 4},
    )

    client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": day["id"],
            "performed_on": "2026-08-26",
            "duration_minutes": 40,
            "completed_exercise_ids": [exercise["id"]],
            "exercise_performance": [
                {
                    "exercise_id": exercise["id"],
                    "sets_completed": exercise["sets"],
                    "reps_completed": 12,
                    "load_kg": 20,
                    "effort": "easy",
                }
            ],
            "session_rpe": 7,
        },
    )

    updated = client.get(f"/v1/profiles/{profile_id}/workout-plan").json()["days"][0]["exercises"][0]
    assert updated["progression_action"] == "hold"
    assert updated["recommended_load_kg"] == 20
    assert "회복" in updated["recommendation_reason"]
