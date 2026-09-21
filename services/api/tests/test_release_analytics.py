from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from app import main
from app.admin_schemas import AnalyticsEventRequest, AnalyticsHeartbeatRequest
from app.services.analytics_repository import (
    AnalyticsOwnershipError,
    AnalyticsProfileOwnershipError,
    get_analytics_repository,
)
from app.services.auth import AuthenticatedUser
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError


@pytest.fixture
def client(monkeypatch):
    def verified_user(authorization):
        if not authorization:
            return None
        return AuthenticatedUser(user_id=authorization.removeprefix("Bearer "))
    monkeypatch.setattr(main, "authenticate_bearer_token", verified_user)
    with TestClient(main.app) as test_client:
        yield test_client


def headers(owner):
    return {"Authorization": f"Bearer {owner}"} if owner else {}


def test_empty_funnel_does_not_report_complete_abandonment():
    funnel = get_analytics_repository().overview().funnel
    assert funnel
    assert all(stage.users == 0 and stage.dropoff_from_previous == 0 for stage in funnel)


def create_profile(client, owner):
    response = client.post("/v1/onboarding", headers=headers(owner), json={
        "age": 29, "sex": "male", "height_cm": 176, "current_weight_kg": 82,
        "target_weight_kg": 76, "goal_type": "recomp", "activity_level": "moderate",
        "training_frequency": "3-4",
    })
    assert response.status_code == 200
    return response.json()["profile_id"]


def send(client, endpoint, owner, session="release_session", profile=None):
    payload = {"session_id": session, "screen": "today", "profile_id": profile}
    if endpoint == "events":
        payload["event_name"] = "app_opened"
    return client.post(f"/v1/analytics/{endpoint}", headers=headers(owner), json=payload)


def snapshot():
    repo = get_analytics_repository()
    with repo._connection() as conn:
        return {table: [dict(row) for row in conn.execute(f"select * from {table}").fetchall()]
                for table in ("app_users", "app_sessions", "product_events")}


@pytest.mark.parametrize("endpoint", ["events", "heartbeat"])
def test_profile_ownership_and_initial_profileless_events(client, endpoint):
    owner_profile = create_profile(client, "owner-a")
    for profile in (None, owner_profile):
        assert send(client, endpoint, "owner-a", profile=profile).status_code == 200
    before = snapshot()
    for profile in (owner_profile, "missing-profile"):
        response = send(client, endpoint, "owner-b", profile=profile)
        assert response.status_code == 404
        assert response.json()["detail"] == "profile_not_found"
        assert snapshot() == before
    assert send(client, endpoint, None, profile=owner_profile).status_code == 404
    assert snapshot() == before


@pytest.mark.parametrize("endpoint", ["events", "heartbeat"])
@pytest.mark.parametrize("initial,attacker", [
    ("owner-a", "owner-b"), ("owner-a", None), (None, "owner-b"),
])
def test_session_owner_is_immutable_and_rejection_rolls_back(client, endpoint, initial, attacker):
    assert send(client, "events", initial).status_code == 200
    before = snapshot()
    response = send(client, endpoint, attacker)
    assert response.status_code == 409
    assert response.json()["detail"] == "analytics_session_conflict"
    assert snapshot() == before
    assert send(client, endpoint, initial).status_code == 200


@pytest.mark.parametrize("endpoint", ["events", "heartbeat"])
def test_repository_rechecks_profile_inside_write_transaction(client, endpoint):
    profile = create_profile(client, "owner-a")
    assert send(client, "events", "owner-a", profile=profile).status_code == 200
    assert send(client, "events", "owner-b", session="existing_attacker").status_code == 200
    before = snapshot()
    repo = get_analytics_repository()
    payload = {"session_id": "attacker_session", "screen": "today", "profile_id": profile}
    with pytest.raises(AnalyticsProfileOwnershipError):
        if endpoint == "events":
            repo.record_event(AnalyticsEventRequest(event_name="app_opened", **payload),
                              AuthenticatedUser(user_id="owner-b"))
        else:
            repo.heartbeat(AnalyticsHeartbeatRequest(**payload), AuthenticatedUser(user_id="owner-b"))
    assert snapshot() == before


def test_concurrent_session_claim_has_only_one_owner():
    repo = get_analytics_repository()
    barrier = Barrier(2)

    def claim(owner):
        barrier.wait(timeout=5)
        try:
            repo.record_event(AnalyticsEventRequest(
                event_name="app_opened", session_id="contested_session", screen="today",
            ), AuthenticatedUser(user_id=owner))
            return owner
        except AnalyticsOwnershipError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        winners = list(pool.map(claim, ("owner-a", "owner-b")))
    winner = next(owner for owner in winners if owner is not None)
    assert winners.count(None) == 1
    rows = snapshot()
    for table in rows:
        assert len(rows[table]) == 1
        assert rows[table][0]["user_id"] == winner


@pytest.mark.parametrize("owner", ["owner-a", None])
def test_profile_deletion_cleans_analytics_and_preserves_other_owners(client, owner):
    profile = create_profile(client, owner)
    other_profile = create_profile(client, "owner-b")
    assert send(client, "events", owner, "deleted_session", profile).status_code == 200
    assert send(client, "events", owner, "initial_session").status_code == 200
    assert send(client, "events", "owner-b", "survivor_session", other_profile).status_code == 200
    repo = get_analytics_repository()
    assert repo.consume_admin_login_attempt()
    # A pre-fix anonymous event can be identifiable through its session alone.
    with repo._connection() as conn:
        conn.execute("update product_events set user_id = null, profile_id = null "
                     "where session_id = 'deleted_session'")
        # Preserve an explicit other owner even when legacy references were polluted.
        conn.execute("update product_events set profile_id = ? where user_id = 'owner-b'", (profile,))
    before = snapshot()
    denied = client.delete(f"/v1/profiles/{profile}", headers=headers("owner-b"))
    assert denied.status_code == 404
    assert snapshot() == before
    deleted = client.delete(f"/v1/profiles/{profile}", headers=headers(owner))
    assert deleted.status_code == 200
    after = snapshot()
    for table, rows in after.items():
        expected = [row for row in before[table] if row.get("user_id") == "owner-b"
                    or (owner is None and row.get("session_id") == "initial_session")]
        assert rows == expected
    assert get_coach_repository().get_profile(profile) is None
    assert get_coach_repository().get_profile(other_profile) is not None
    assert repo.user_detail("owner-b") is not None
    if owner:
        assert repo.user_detail(owner) is None
    with repo._connection() as conn:
        assert conn.execute("select attempts from admin_login_budget").fetchone()["attempts"] == 1


def test_failed_analytics_deletion_keeps_profile_for_retry(client, monkeypatch):
    profile = create_profile(client, "owner-a")
    assert send(client, "events", "owner-a", profile=profile).status_code == 200
    repo = get_analytics_repository()
    original = repo.delete_profile_data

    def fail(*args, **kwargs):
        raise PersistenceError("synthetic_failure")

    monkeypatch.setattr(repo, "delete_profile_data", fail)
    assert client.delete(f"/v1/profiles/{profile}", headers=headers("owner-a")).status_code == 503
    assert get_coach_repository().get_profile(profile) is not None
    monkeypatch.setattr(repo, "delete_profile_data", original)
    assert client.delete(f"/v1/profiles/{profile}", headers=headers("owner-a")).status_code == 200


def test_analytics_cleanup_rolls_back_as_one_transaction(client):
    profile = create_profile(client, "owner-a")
    assert send(client, "events", "owner-a", profile=profile).status_code == 200
    before = snapshot()
    repo = get_analytics_repository()
    with repo._connection() as conn:
        conn.execute("create trigger fail_user_delete before delete on app_users "
                     "begin select raise(abort, 'synthetic failure'); end")
    with pytest.raises(PersistenceError):
        repo.delete_profile_data(profile, owner_id="owner-a")
    assert snapshot() == before
