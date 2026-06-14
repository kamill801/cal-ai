from fastapi.testclient import TestClient

from app import main as api_main
from app.main import app
from app.services.analysis_provider import StructuredOutputMalformedError


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cal-ai-api"}


def test_onboarding_returns_initial_target() -> None:
    response = client.post(
        "/v1/onboarding",
        json={
            "age": 29,
            "sex": "male",
            "height_cm": 176,
            "current_weight_kg": 82,
            "target_weight_kg": 75,
            "goal_type": "lose",
            "activity_level": "moderate",
            "training_frequency": "3-4",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["profile_id"]
    assert body["target"]["calories_kcal"] > 0
    assert body["target"]["protein_g"] > 0


def test_dashboard_today_mock_contract() -> None:
    response = client.get("/v1/dashboard/today")

    assert response.status_code == 200
    body = response.json()
    assert body["target"]["calories_kcal"] == 1850
    assert body["next_meal_guidance"]["menu_type_recommendations"]


def test_analysis_job_serialized_contract_shape() -> None:
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": "local-demo-image", "meal_type": "lunch", "optional_note": "밥은 거의 다 먹었어요"},
    )
    assert create_response.status_code == 200
    assert create_response.json() == {"analysis_job_id": "mock-lunch-001", "status": "queued"}

    response = client.get("/v1/analysis-jobs/mock-lunch-001")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_clarification"
    assert set(body["result"]) >= {
        "id",
        "meal_name",
        "meal_type",
        "stage_text",
        "summary",
        "detected_foods",
        "uncertainty_reasons",
        "primary_explanation",
        "clarification_question",
    }
    assert set(body["result"]["summary"]) == {
        "calories_kcal",
        "calorie_range",
        "protein_g",
        "carbs_g",
        "fat_g",
        "confidence",
        "confidence_label",
        "confidence_group",
    }
    assert set(body["result"]["summary"]["calorie_range"]) == {"low", "midpoint", "high"}
    assert body["result"]["clarification_question"]["question_key"] == "rice_amount"
    assert body["result"]["clarification_question"]["options"][0]["helper_text"]


def test_mock_jobs_preserve_requested_meal_type() -> None:
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": "local-demo-image", "meal_type": "breakfast"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["analysis_job_id"] == "mock-breakfast-001"

    job_response = client.get("/v1/analysis-jobs/mock-breakfast-001")
    assert job_response.status_code == 200
    assert job_response.json()["result"]["meal_type"] == "breakfast"
    assert job_response.json()["result"]["id"] == "analysis-breakfast-001"

    clarify_response = client.post(
        "/v1/analysis-jobs/mock-dinner-001/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "large_bowl"}]},
    )
    assert clarify_response.status_code == 200
    assert clarify_response.json()["result"]["meal_type"] == "dinner"

    save_response = client.post(
        "/v1/meal-logs",
        json={"analysis_job_id": "mock-breakfast-001", "result_id": "analysis-breakfast-001", "clarification_value": "half_bowl"},
    )
    assert save_response.status_code == 200
    assert save_response.json()["dashboard"]["meals"][0]["meal_type"] == "breakfast"


def test_clarification_and_save_contracts() -> None:
    clarify_response = client.post(
        "/v1/analysis-jobs/mock-lunch-001/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
    )
    assert clarify_response.status_code == 200
    clarify_body = clarify_response.json()
    assert clarify_body["status"] == "completed"
    assert clarify_body["result"]["summary"]["calorie_range"] == {"low": 640, "midpoint": 675, "high": 710}
    assert clarify_body["range_narrowing"]["before"]["high"] - clarify_body["range_narrowing"]["before"]["low"] == 160
    assert clarify_body["range_narrowing"]["after"]["high"] - clarify_body["range_narrowing"]["after"]["low"] == 70

    save_response = client.post("/v1/meal-logs", json={"analysis_job_id": "mock-lunch-001", "result_id": "analysis-lunch-001", "clarification_value": "one_bowl"})
    assert save_response.status_code == 200
    save_body = save_response.json()
    assert save_body["confirmation"] == "기록했어요"
    assert save_body["remaining_calories_kcal"] == 505
    assert save_body["dashboard"]["meals"][0]["name"] == "닭고기 덮밥"


def test_clarification_answers_drive_distinct_mock_results() -> None:
    expected = {
        "half_bowl": ({"low": 560, "midpoint": 595, "high": 630}, 595),
        "one_bowl": ({"low": 640, "midpoint": 675, "high": 710}, 675),
        "large_bowl": ({"low": 720, "midpoint": 765, "high": 810}, 765),
    }

    for value, (expected_range, expected_calories) in expected.items():
        response = client.post(
            "/v1/analysis-jobs/mock-lunch-001/clarifications",
            json={"answers": [{"question_key": "rice_amount", "value": value}]},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["result"]["summary"]["calories_kcal"] == expected_calories
        assert body["result"]["summary"]["calorie_range"] == expected_range
        assert body["range_narrowing"]["after"] == expected_range

    unknown_response = client.post(
        "/v1/analysis-jobs/mock-lunch-001/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "unknown"}]},
    )
    assert unknown_response.status_code == 200
    unknown_body = unknown_response.json()
    assert unknown_body["result"]["summary"]["calories_kcal"] == 700
    assert unknown_body["range_narrowing"] is None


def test_save_contract_uses_clarification_value() -> None:
    expected = {
        "half_bowl": 585,
        "one_bowl": 505,
        "large_bowl": 415,
        "unknown": 480,
    }

    for value, expected_remaining in expected.items():
        response = client.post(
            "/v1/meal-logs",
            json={"analysis_job_id": "mock-lunch-001", "result_id": "analysis-lunch-001", "clarification_value": value},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["remaining_calories_kcal"] == expected_remaining
        assert body["dashboard"]["meals"][0]["calories_kcal"] == 1850 - 670 - expected_remaining


def test_save_contract_requires_clarification_value() -> None:
    response = client.post(
        "/v1/meal-logs",
        json={"analysis_job_id": "mock-lunch-001", "result_id": "analysis-lunch-001"},
    )

    assert response.status_code == 422


def test_malformed_provider_output_returns_safe_503(monkeypatch) -> None:
    class MalformedProvider:
        def create_job(self, payload):
            raise StructuredOutputMalformedError("openai_output_malformed")

    monkeypatch.setattr(api_main, "get_analysis_provider", lambda: MalformedProvider())

    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": "local-demo-image", "meal_type": "lunch"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "analysis_provider_unavailable"
    assert "openai_output_malformed" not in response.text
