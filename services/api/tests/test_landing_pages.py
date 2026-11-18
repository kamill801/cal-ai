import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.main import app
import app.main as main
import app.landing_routes as landing
from app.recruitment_schemas import POLICY_VERSION
from app.services import recruitment
from app.services.recruitment_repository import RecruitmentPersistenceError, RecruitmentRepository
from app.services.storage import StorageConfigurationError

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[3]


def test_landing_and_security_headers():
    for route in ("/", "/beta", "/beta/"):
        response = client.get(route)
        assert response.status_code == 200
        assert '<html lang="ko">' in response.text
        assert 'id="beta-form"' in response.text
        assert 'href="/app"' not in response.text
        assert 'href="/privacy"' in response.text
        assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["referrer-policy"] == "no-referrer"
        assert "<script>" not in response.text


def test_deletion_intent_preserved_without_reflecting_other_query_values():
    response = client.get("/?action=delete-account&secret=not-to-reflect", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/account-deletion"
    assert "not-to-reflect" not in response.text
    assert "not-to-reflect" not in client.get("/?secret=not-to-reflect").text


def test_assets_resolve_without_provider_credentials():
    for name in ("landing.css", "landing.js", "mascot-welcome.png", "mascot-meal.png", "meal-preview.png", "favicon.png"):
        response = client.get(f"/beta-assets/{name}")
        assert response.status_code == 200
        assert len(response.content) > 100
    assert client.get("/beta-assets/../main.py").status_code == 404


def test_vercel_routes_preserve_app_auth_and_public_api():
    config = json.loads((ROOT / "vercel.json").read_text())
    routes = config["routes"]
    assert routes[0] == {"src": "/(beta/?)?", "dest": "api/index.py"}
    assert any(route.get("src") == "/recruitment/(.*)" for route in routes)
    assert routes[-1] == {"src": "/(.*)", "dest": "api/index.py"}
    assert config["crons"] == [{"path": "/internal/cleanup-images", "schedule": "0 18 * * *"}]
    guard = {"src": "/(app(/.*)?|index.html|auth/callback/?)", "dest": "api/index.py"}
    assert routes.index(guard) < routes.index({"handle": "filesystem"})
    assert config["functions"]["api/index.py"]["includeFiles"] == "services/api/app/web/**"


def test_hidden_web_entries_do_not_serve_the_spa_or_reflect_tokens(monkeypatch):
    monkeypatch.delenv("WEB_APP_ENABLED", raising=False)
    for route in ("/app", "/app/", "/app/nested", "/index.html", "/auth/callback", "/auth/callback/"):
        for method in (client.get, client.head):
            response = method(route + "?code=not-to-reflect", follow_redirects=False)
            assert response.status_code == 307
            assert response.headers["location"] == "/"
            assert response.headers["cache-control"] == "no-store"
            assert "not-to-reflect" not in response.text
    deletion = client.get("/account-deletion").text
    assert 'href="/?action=delete-account"' not in deletion
    assert "mailto:areche.ai.kr@gmail.com" in deletion


def test_original_app_can_be_restored_with_one_flag(monkeypatch, tmp_path):
    shell = tmp_path / "index.html"
    shell.write_text("<html>preserved Expo shell</html>")
    monkeypatch.setattr(landing, "PRESERVED_APP", shell)
    monkeypatch.setenv("WEB_APP_ENABLED", "true")
    for route in ("/", "/app", "/app/nested", "/index.html", "/auth/callback"):
        response = client.get(route)
        assert response.status_code == 200
        assert response.text == shell.read_text()
        assert response.headers["cache-control"] == "no-store"
    assert 'id="beta-form"' in client.get("/beta").text
    assert client.get("/?action=delete-account", follow_redirects=False).headers["location"] == "/app?action=delete-account"
    assert 'href="/?action=delete-account"' in client.get("/account-deletion").text


def test_web_restore_fails_closed_if_build_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(landing, "PRESERVED_APP", tmp_path / "missing")
    monkeypatch.setenv("WEB_APP_ENABLED", "true")
    assert client.get("/app").status_code == 503
    monkeypatch.setenv("WEB_APP_ENABLED", "yes")
    assert client.get("/app", follow_redirects=False).status_code == 307


def test_no_prechecked_consent_or_external_tracker():
    html = client.get("/").text
    for field in ("beta-adult", "beta-android", "beta-privacy"):
        tag = html.split(f'id="{field}"')[1].split(">")[0]
        assert "required" in tag
        assert "checked" not in tag
    assert "gtag" not in html
    assert "facebook.net" not in html


def test_beta_retention_uses_existing_authenticated_schedule_and_only_beta_records(monkeypatch, tmp_path):
    path = str(tmp_path / "retention.db")
    start = datetime(2026, 11, 18, tzinfo=UTC)
    RecruitmentRepository(path, clock=lambda: start).save_application("fixture@example.invalid", POLICY_VERSION, 30, retention_enabled=True)
    with sqlite3.connect(path) as conn:
        conn.execute("create table preserved_user_records(id text)")
        conn.execute("insert into preserved_user_records values('untouched')")
    repository = RecruitmentRepository(path, clock=lambda: start + timedelta(days=31))
    monkeypatch.setattr(recruitment, "get_recruitment_repository", lambda *a: repository)
    monkeypatch.setenv("CRON_SECRET", "synthetic-local-cron-only")
    monkeypatch.setenv("BETA_RECRUITMENT_RETENTION_ENABLED", "true")
    monkeypatch.setenv("IMAGE_RETENTION_ENABLED", "false")
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")
    assert client.get("/internal/cleanup-images").status_code == 401
    with sqlite3.connect(path) as conn:
        assert conn.execute("select count(*) from beta_recruitment_applications").fetchone()[0] == 1
    result = client.get("/internal/cleanup-images", headers={"Authorization": "Bearer synthetic-local-cron-only"})
    assert result.status_code == 200
    with sqlite3.connect(path) as conn:
        assert conn.execute("select count(*) from beta_recruitment_applications").fetchone()[0] == 0
        assert conn.execute("select id from preserved_user_records").fetchone()[0] == "untouched"


def test_beta_cleanup_failure_is_sanitized_and_reported(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "synthetic-local-cron-only")
    monkeypatch.setenv("IMAGE_RETENTION_ENABLED", "false")
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")
    def fail():
        raise RecruitmentPersistenceError("postgres://secret@example.invalid")
    monkeypatch.setattr(main, "cleanup_expired_recruitment", fail)
    result = client.get("/internal/cleanup-images", headers={"Authorization": "Bearer synthetic-local-cron-only"})
    assert result.status_code == 503
    assert result.json()["detail"]["code"] == "recruitment_cleanup_unavailable"
    assert "secret@example" not in result.text


def test_image_cleanup_failure_cannot_starve_beta_retention(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "synthetic-local-cron-only")
    monkeypatch.setenv("IMAGE_RETENTION_ENABLED", "true")
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")
    beta = Mock(return_value=1)
    monkeypatch.setattr(main, "cleanup_expired_recruitment", beta)
    monkeypatch.setattr(main, "get_persistence_repository", lambda: object())
    photo = Mock(side_effect=StorageConfigurationError("private storage error"))
    monkeypatch.setattr(main, "cleanup_expired_image_uploads", photo)
    result = client.get("/internal/cleanup-images", headers={"Authorization": "Bearer synthetic-local-cron-only"})
    assert result.status_code == 503
    assert result.json()["detail"]["code"] == "storage_cleanup_unavailable"
    beta.assert_called_once()


def test_beta_failure_does_not_prevent_image_cleanup(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "synthetic-local-cron-only")
    monkeypatch.setenv("IMAGE_RETENTION_ENABLED", "true")
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")
    monkeypatch.setattr(main, "cleanup_expired_recruitment", Mock(side_effect=RecruitmentPersistenceError("unavailable")))
    monkeypatch.setattr(main, "get_persistence_repository", lambda: object())
    photo = Mock(return_value=1)
    monkeypatch.setattr(main, "cleanup_expired_image_uploads", photo)
    result = client.get("/internal/cleanup-images", headers={"Authorization": "Bearer synthetic-local-cron-only"})
    assert result.status_code == 503
    assert result.json()["detail"]["code"] == "recruitment_cleanup_unavailable"
    photo.assert_called_once()
