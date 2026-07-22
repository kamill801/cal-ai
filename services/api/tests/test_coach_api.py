from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_profile(goal_type: str = "recomp") -> str:
    response = client.post(
        "/v1/onboarding",
        json={
            "age": 29,
            "sex": "male",
            "height_cm": 176,
            "current_weight_kg": 82,
            "target_weight_kg": 76,
            "goal_type": goal_type,
            "activity_level": "moderate",
            "training_frequency": "3-4",
            "experience_level": "beginner",
            "available_equipment": ["gym"],
            "session_minutes": 60,
        },
    )
    assert response.status_code == 200
    return response.json()["profile_id"]


def upload_body_photo() -> str:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "body-front-demo",
            "file_name": "body-front.png",
            "content_type": "image/png",
            "byte_size": 420_000,
        },
    )
    assert response.status_code == 200
    return response.json()["image_upload_id"]


def test_today_coach_dashboard_uses_persisted_profile_target() -> None:
    profile_id = create_profile()

    response = client.get(f"/v1/profiles/{profile_id}/dashboard/today")

    assert response.status_code == 200
    body = response.json()
    assert body["profile_id"] == profile_id
    assert body["nutrition"]["target"]["protein_g"] > 0
    assert body["nutrition"]["remaining"]["protein_g"] == body["nutrition"]["target"]["protein_g"]
    assert body["training"]["completed_sessions"] == 0
    assert body["next_action"]["type"] == "log_meal"


def test_profile_meals_accumulate_into_real_nutrition_dashboard() -> None:
    profile_id = create_profile()
    image_upload_id = upload_body_photo()
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": image_upload_id, "meal_type": "lunch"},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["analysis_job_id"]
    assert client.get(f"/v1/analysis-jobs/{job_id}").status_code == 200
    assert client.post(
        f"/v1/analysis-jobs/{job_id}/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
    ).status_code == 200

    for _ in range(2):
        save_response = client.post(
            "/v1/meal-logs",
            json={
                "profile_id": profile_id,
                "analysis_job_id": job_id,
                "result_id": "analysis-lunch-001",
                "clarification_value": "one_bowl",
            },
        )
        assert save_response.status_code == 200

    dashboard = client.get(f"/v1/profiles/{profile_id}/dashboard/today").json()
    assert dashboard["nutrition"]["consumed"]["calories_kcal"] == 1_350
    assert dashboard["nutrition"]["consumed"]["protein_g"] == 68
    assert dashboard["nutrition"]["remaining"]["protein_g"] == dashboard["nutrition"]["target"]["protein_g"] - 68


def test_today_dashboard_excludes_meals_logged_on_other_days() -> None:
    profile_id = create_profile()
    image_upload_id = upload_body_photo()
    create_response = client.post("/v1/analysis-jobs", json={"image_upload_id": image_upload_id, "meal_type": "lunch"})
    job_id = create_response.json()["analysis_job_id"]
    client.get(f"/v1/analysis-jobs/{job_id}")
    client.post(
        f"/v1/analysis-jobs/{job_id}/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
    )

    for logged_on in ("2026-07-19", "2026-07-20"):
        response = client.post(
            "/v1/meal-logs",
            json={
                "profile_id": profile_id,
                "analysis_job_id": job_id,
                "result_id": "analysis-lunch-001",
                "clarification_value": "one_bowl",
                "logged_on": logged_on,
            },
        )
        assert response.status_code == 200

    dashboard = client.get(f"/v1/profiles/{profile_id}/dashboard/today?logged_on=2026-07-20").json()
    assert dashboard["date"] == "2026-07-20"
    assert dashboard["nutrition"]["consumed"]["calories_kcal"] == 675
    assert dashboard["nutrition"]["consumed"]["protein_g"] == 34


def test_meal_log_rejects_unknown_profile_with_structured_not_found() -> None:
    image_upload_id = upload_body_photo()
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": image_upload_id, "meal_type": "lunch"},
    )
    job_id = create_response.json()["analysis_job_id"]
    client.get(f"/v1/analysis-jobs/{job_id}")
    client.post(
        f"/v1/analysis-jobs/{job_id}/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
    )

    response = client.post(
        "/v1/meal-logs",
        json={
            "profile_id": "missing-profile",
            "analysis_job_id": job_id,
            "result_id": "analysis-lunch-001",
            "clarification_value": "one_bowl",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "profile_not_found"


def test_weight_and_wellness_logs_are_reflected_in_progress() -> None:
    profile_id = create_profile()

    weight_response = client.post(
        f"/v1/profiles/{profile_id}/weight-logs",
        json={"logged_on": "2026-07-20", "weight_kg": 81.4},
    )
    wellness_response = client.post(
        f"/v1/profiles/{profile_id}/wellness-check-ins",
        json={"logged_on": "2026-07-20", "energy": 4, "sleep_quality": 3, "soreness": 2, "note": "하체가 조금 뻐근해요"},
    )
    progress_response = client.get(f"/v1/profiles/{profile_id}/progress")

    assert weight_response.status_code == 200
    assert wellness_response.status_code == 200
    assert progress_response.status_code == 200
    body = progress_response.json()
    assert body["latest_weight_kg"] == 81.4
    assert body["latest_wellness"]["energy"] == 4
    assert body["latest_wellness"]["soreness"] == 2


def test_body_check_in_uses_ready_private_upload_and_safe_mock_observations() -> None:
    profile_id = create_profile()
    image_upload_id = upload_body_photo()

    response = client.post(
        f"/v1/profiles/{profile_id}/body-check-ins",
        json={
            "captured_on": "2026-07-20",
            "image_upload_id": image_upload_id,
            "view": "front",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_upload_id"] == image_upload_id
    assert body["analysis"]["provider"] == "mock"
    assert body["analysis"]["confidence"] == "limited"
    assert body["analysis"]["training_focus"]
    assert "body_fat" not in response.text
    assert "diagnosis" not in response.text

    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    for focus in body["analysis"]["training_focus"]:
        assert focus in plan["personalization_basis"]


def test_body_check_in_rejects_unknown_upload() -> None:
    profile_id = create_profile()

    response = client.post(
        f"/v1/profiles/{profile_id}/body-check-ins",
        json={
            "captured_on": "2026-07-20",
            "image_upload_id": "missing-upload",
            "view": "front",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "image_upload_not_found"


def test_workout_plan_and_session_logging_form_a_complete_loop() -> None:
    profile_id = create_profile()

    plan_response = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate")
    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert plan["days_per_week"] == 3
    assert len(plan["days"]) == 3
    assert all(day["exercises"] for day in plan["days"])
    assert all(exercise["sets"] >= 2 for day in plan["days"] for exercise in day["exercises"])

    session_response = client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": plan["days"][0]["id"],
            "performed_on": "2026-07-20",
            "duration_minutes": 58,
            "completed_exercise_ids": [exercise["id"] for exercise in plan["days"][0]["exercises"]],
            "session_rpe": 7,
        },
    )
    dashboard_response = client.get(f"/v1/profiles/{profile_id}/dashboard/today")

    assert session_response.status_code == 200
    assert session_response.json()["completed"] is True
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["training"]["completed_sessions"] == 1


def test_weekly_coach_combines_nutrition_training_recovery_and_body_context() -> None:
    profile_id = create_profile()
    plan = client.post(f"/v1/profiles/{profile_id}/workout-plans/generate").json()
    client.post(
        f"/v1/profiles/{profile_id}/weight-logs",
        json={"logged_on": "2026-07-20", "weight_kg": 81.4},
    )
    client.post(
        f"/v1/profiles/{profile_id}/wellness-check-ins",
        json={"logged_on": "2026-07-20", "energy": 3, "sleep_quality": 3, "soreness": 4},
    )
    client.post(
        f"/v1/profiles/{profile_id}/workout-sessions",
        json={
            "plan_id": plan["id"],
            "workout_day_id": plan["days"][0]["id"],
            "performed_on": "2026-07-20",
            "duration_minutes": 55,
            "completed_exercise_ids": [exercise["id"] for exercise in plan["days"][0]["exercises"]],
            "session_rpe": 8,
        },
    )

    response = client.get(f"/v1/profiles/{profile_id}/weekly-coach")

    assert response.status_code == 200
    body = response.json()
    assert body["profile_id"] == profile_id
    assert body["score"] >= 0
    assert body["wins"]
    assert body["focus_items"]
    assert body["next_week_actions"]
    assert body["evidence"]["workouts_completed"] == 1
    assert body["safety_note"]


def test_target_adjustment_waits_for_evidence_and_requires_confirmation() -> None:
    profile_id = create_profile("lose")
    initial = client.get(f"/v1/profiles/{profile_id}/progress").json()["target_adjustment"]
    assert initial["status"] == "insufficient_data"

    image_upload_id = upload_body_photo()
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": image_upload_id, "meal_type": "lunch"},
    )
    job_id = create_response.json()["analysis_job_id"]
    client.get(f"/v1/analysis-jobs/{job_id}")
    client.post(
        f"/v1/analysis-jobs/{job_id}/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
    )
    for _ in range(5):
        response = client.post(
            "/v1/meal-logs",
            json={
                "profile_id": profile_id,
                "analysis_job_id": job_id,
                "result_id": "analysis-lunch-001",
                "clarification_value": "one_bowl",
            },
        )
        assert response.status_code == 200
    for logged_on, weight_kg in (("2026-07-13", 82.0), ("2026-07-20", 82.1)):
        response = client.post(
            f"/v1/profiles/{profile_id}/weight-logs",
            json={"logged_on": logged_on, "weight_kg": weight_kg},
        )
        assert response.status_code == 200

    suggestion = client.get(f"/v1/profiles/{profile_id}/progress").json()["target_adjustment"]
    assert suggestion["status"] == "suggested"
    assert suggestion["calorie_delta"] == -100
    assert suggestion["requires_confirmation"] is True
