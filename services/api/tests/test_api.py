from fastapi.testclient import TestClient

from app.main import app


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
