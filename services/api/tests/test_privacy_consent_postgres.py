"""Consent races on the isolated Unix-socket PostgreSQL fixture only."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import monotonic, sleep

import pytest

from app.admin_schemas import AnalyticsEventRequest, AnalyticsHeartbeatRequest
from app.services.analytics_repository import (
    AnalyticsConsentError, PRIVACY_CONSENT_VERSION, get_analytics_repository,
)
from app.services.auth import AuthenticatedUser
from test_account_deletion import admin
from test_account_deletion_postgres import postgres


def test_real_postgres_current_policy_consent_is_owner_scoped(postgres, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    repo = get_analytics_repository()
    repo.save_privacy_consent("consent-owner", policy_version=PRIVACY_CONSENT_VERSION,
                              health_data_consent=True, analytics_consent=False)
    assert repo.privacy_consent("other-owner") is None
    assert repo.privacy_consent("consent-owner")["health_data_consent"] == 1
    with pytest.raises(AnalyticsConsentError):
        repo.heartbeat(AnalyticsHeartbeatRequest(session_id="pg-consent-session", screen="today"),
                       AuthenticatedUser(user_id="consent-owner"))
    with repo._connection() as conn:
        assert conn.execute("select count(*) as count from app_sessions").fetchone()["count"] == 0


def test_real_postgres_optout_serializes_with_event_transaction(postgres, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    repo = get_analytics_repository()
    user = AuthenticatedUser(user_id="consent-race-owner")
    repo.save_privacy_consent(user.user_id, policy_version=PRIVACY_CONSENT_VERSION,
                              health_data_consent=True, analytics_consent=True)
    checked, release, opting_out = Event(), Event(), Event()
    original = repo._upsert_user

    def pause_after_consent_check(conn, user, received_at):
        checked.set()
        assert release.wait(10), "test did not release the event transaction"
        return original(conn, user, received_at)

    def revoke():
        opting_out.set()
        return repo.save_privacy_consent(user.user_id, policy_version=PRIVACY_CONSENT_VERSION,
                                         health_data_consent=True, analytics_consent=False)

    monkeypatch.setattr(repo, "_upsert_user", pause_after_consent_check)
    event = AnalyticsEventRequest(event_name="app_opened", session_id="pg-consent-race", screen="today")
    with ThreadPoolExecutor(max_workers=2) as pool:
        recorded = pool.submit(repo.record_event, event, user)
        try:
            assert checked.wait(10)
            revoked = pool.submit(revoke)
            assert opting_out.wait(10)
            assert not revoked.done()
        finally:
            release.set()
        recorded.result(timeout=15)
        assert revoked.result(timeout=15)["analytics_consent"] is False
    with pytest.raises(AnalyticsConsentError):
        repo.record_event(event, user)
    with repo._connection() as conn:
        assert conn.execute("select count(*) as count from product_events").fetchone()["count"] == 1


def test_real_postgres_revoke_owner_lock_precedes_event_consent_read(postgres, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    repo = get_analytics_repository()
    user = AuthenticatedUser(user_id="consent-revoke-first")
    repo.save_privacy_consent(user.user_id, policy_version=PRIVACY_CONSENT_VERSION,
                              health_data_consent=True, analytics_consent=True)
    owner_locked, release, event_started = Event(), Event(), Event()
    waiter_ready = Event()
    backends = {}
    original = repo._lock_consent_owner

    def owner_lock(conn, owner_id):
        if owner_locked.is_set():
            backends["waiter"] = conn.info.backend_pid
            waiter_ready.set()
        original(conn, owner_id)
        if not owner_locked.is_set():
            backends["holder"] = conn.info.backend_pid
            owner_locked.set()
            assert release.wait(10)

    def record():
        event_started.set()
        return repo.record_event(AnalyticsEventRequest(
            event_name="app_opened", session_id="pg-revoke-first", screen="today",
        ), user)

    monkeypatch.setattr(repo, "_lock_consent_owner", owner_lock)
    with ThreadPoolExecutor(max_workers=2) as pool:
        revoked = pool.submit(repo.save_privacy_consent, user.user_id,
                              policy_version=PRIVACY_CONSENT_VERSION,
                              health_data_consent=True, analytics_consent=False)
        try:
            assert owner_locked.wait(10)
            recorded = pool.submit(record)
            assert event_started.wait(10)
            assert waiter_ready.wait(10)
            deadline = monotonic() + 5
            blocked = False
            while monotonic() < deadline:
                with repo._connection() as conn:
                    blockers = conn.execute("select pg_blocking_pids(%s) as blockers",
                                            (backends["waiter"],)).fetchone()["blockers"]
                if backends["holder"] in blockers:
                    blocked = True
                    break
                sleep(0.01)
            assert blocked, "PostgreSQL must report the event waiting on the revocation owner lock"
        finally:
            release.set()
        assert revoked.result(timeout=15)["analytics_consent"] is False
        with pytest.raises(AnalyticsConsentError):
            recorded.result(timeout=15)
    with repo._connection() as conn:
        assert conn.execute("select count(*) as count from product_events").fetchone()["count"] == 0
