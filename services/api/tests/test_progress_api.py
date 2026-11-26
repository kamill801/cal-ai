from datetime import UTC, datetime, timedelta

from test_coach_api import client, create_profile


def log_weight(profile_id: str, day: str, weight: float) -> None:
    response = client.post(
        f"/v1/profiles/{profile_id}/weight-logs",
        json={"logged_on": day, "weight_kg": weight},
    )
    assert response.status_code == 200


def read_progress(profile_id: str) -> dict:
    response = client.get(f"/v1/profiles/{profile_id}/progress")
    assert response.status_code == 200
    return response.json()


def test_progress_history_contains_only_persisted_points_for_the_profile() -> None:
    profile_id = create_profile()
    another_profile_id = create_profile()
    log_weight(another_profile_id, "2026-02-19", 85)

    assert read_progress(profile_id)["weight_history"] == []

    log_weight(profile_id, "2026-02-20", 73.2)
    log_weight(profile_id, "2026-02-18", 74.4)
    log_weight(profile_id, "2026-02-20", 72.4)
    log_weight(profile_id, "2026-02-30", 80)

    progress = read_progress(profile_id)
    assert progress["weight_history"] == [
        {"logged_on": "2026-02-18", "weight_kg": 74.4},
        {"logged_on": "2026-02-20", "weight_kg": 72.4},
    ]
    assert progress["latest_weight_kg"] == 80


def test_progress_history_is_bounded_by_measurement_date_not_insertion_order() -> None:
    profile_id = create_profile()
    today = datetime.now(UTC).date()
    log_weight(profile_id, (today + timedelta(days=7)).isoformat(), 70)

    for days_ago in range(91):
        log_weight(profile_id, (today - timedelta(days=days_ago)).isoformat(), 72.5)
    log_weight(profile_id, today.isoformat(), 72.4)

    history = read_progress(profile_id)["weight_history"]
    assert len(history) == 90
    assert history[0] == {"logged_on": (today - timedelta(days=89)).isoformat(), "weight_kg": 72.5}
    assert history[-1] == {"logged_on": today.isoformat(), "weight_kg": 72.4}
