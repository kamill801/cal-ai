from __future__ import annotations

import io
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app import coach_routes, equipment_routes, main
from app.services.auth import AuthenticatedUser
from app.services.analysis_provider import AnalysisProviderConfigurationError, AnalysisProviderUnavailableError, StructuredOutputMalformedError
from app.services.equipment_guide import EquipmentIdentification, EquipmentProviderDisabledError, OpenAIEquipmentProvider, get_equipment_guide, get_equipment_provider
from app.services.persistence import PersistenceError, get_persistence_repository
from app.services.coach_repository import EquipmentUsageLimitError, get_coach_repository
from app.services.image_uploads import ImageUploadError, complete_presigned_image_upload
from app.schemas import ImageUploadCompleteRequest, ImageUploadRequest
from app.services.storage import StorageConfigurationError


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "authenticate_bearer_token", lambda value: AuthenticatedUser(value.removeprefix("Bearer ")) if value else None)
    monkeypatch.setenv("STORAGE_PROVIDER", "local")
    monkeypatch.setenv("AI_PROVIDER", "mock")
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    monkeypatch.setenv("EQUIPMENT_AI_PROVIDER", "disabled")
    return TestClient(main.app)


def profile(client, owner="owner-a"):
    response = client.post("/v1/onboarding", headers={"Authorization": f"Bearer {owner}"}, json={"age": 29, "sex": "male", "height_cm": 176, "current_weight_kg": 82, "goal_type": "recomp", "activity_level": "moderate"})
    assert response.status_code == 200
    return response.json()["profile_id"]


def ready_image(client, profile_id, monkeypatch, *, owner="owner-a"):
    class Provider:
        def identify(self, image):
            return EquipmentIdentification(equipment_id="lat_pulldown", confidence="medium", visible_evidence=["위쪽에 도르래가 보여요"])
    monkeypatch.setattr(equipment_routes, "get_equipment_provider", lambda: Provider())
    headers = {"Authorization": f"Bearer {owner}"}
    response = client.post(f"/v1/profiles/{profile_id}/equipment-image-uploads/presign", headers=headers, json={"content_type": "image/jpeg", "byte_size": 1200})
    assert response.status_code == 200
    upload = response.json()
    response = client.post("/image-uploads/complete", headers=headers, json={"image_upload_id": upload["image_upload_id"], "object_key": upload["object_key"], "file_name": "equipment-guide.jpg", "content_type": "image/jpeg", "byte_size": 1200})
    assert response.status_code == 200
    return upload["image_upload_id"]


def test_catalog_and_manual_guide_work_without_ai_or_youtube_keys(client):
    catalog = client.get("/v1/equipment-guides/catalog").json()
    assert not catalog["photo_identification_available"]
    assert len(catalog["items"]) >= 10
    response = client.get("/v1/equipment-guides/lat_pulldown")
    assert response.status_code == 200
    guide = response.json()
    assert guide["source"] == "search_link" and guide["videos"] == []
    assert urlparse(guide["search_url"]).hostname == "www.youtube.com"
    assert "랫풀다운" in parse_qs(urlparse(guide["search_url"]).query)["search_query"][0]
    assert client.get("/v1/equipment-guides/unknown").status_code == 404


def test_scan_requires_authenticated_profile_before_upload(client):
    pid = profile(client)
    assert client.post(f"/v1/profiles/{pid}/equipment-identifications", json={"image_upload_id": "anything"}).status_code == 401
    assert client.post(f"/v1/profiles/{pid}/equipment-image-uploads/presign", json={"content_type": "image/jpeg", "byte_size": 100}).status_code == 401


def test_disabled_photo_provider_does_not_reserve_storage(client):
    pid = profile(client)
    response = client.post(f"/v1/profiles/{pid}/equipment-image-uploads/presign", headers={"Authorization": "Bearer owner-a"}, json={"content_type": "image/jpeg", "byte_size": 100})
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "equipment_provider_disabled"
    assert get_persistence_repository().sum_image_upload_bytes() == 0


def test_equipment_upload_rejects_other_owner_and_unsupported_type(client):
    pid = profile(client)
    assert client.post(f"/v1/profiles/{pid}/equipment-image-uploads/presign", headers={"Authorization": "Bearer owner-b"}, json={"content_type": "image/jpeg", "byte_size": 100}).status_code == 404
    assert client.post(f"/v1/profiles/{pid}/equipment-image-uploads/presign", headers={"Authorization": "Bearer owner-a"}, json={"content_type": "image/svg+xml", "byte_size": 100}).status_code == 422


def test_identification_deletes_photo_and_cannot_be_reused(client, monkeypatch):
    pid = profile(client)
    upload_id = ready_image(client, pid, monkeypatch)
    response = client.post(f"/v1/profiles/{pid}/equipment-identifications", headers={"Authorization": "Bearer owner-a"}, json={"image_upload_id": upload_id})
    assert response.status_code == 200
    assert response.json()["equipment_id"] == "lat_pulldown"
    assert response.json()["needs_confirmation"] is True
    record = get_persistence_repository().get_image_upload(upload_id)
    assert record.upload_status == "deleted" and record.object_key is None
    assert get_persistence_repository().sum_image_upload_bytes() == 0
    assert client.post(f"/v1/profiles/{pid}/equipment-identifications", headers={"Authorization": "Bearer owner-a"}, json={"image_upload_id": upload_id}).json() == response.json()


def test_other_owner_cannot_read_or_delete_equipment_upload(client, monkeypatch):
    pid_a = profile(client)
    pid_b = profile(client, "owner-b")
    upload_id = ready_image(client, pid_a, monkeypatch)
    response = client.post(f"/v1/profiles/{pid_b}/equipment-identifications", headers={"Authorization": "Bearer owner-b"}, json={"image_upload_id": upload_id})
    assert response.status_code == 404
    assert get_persistence_repository().get_image_upload(upload_id).upload_status == "ready"


def test_meal_photo_cannot_be_consumed_as_equipment(client):
    pid = profile(client)
    response = client.post("/v1/image-uploads", headers={"Authorization": "Bearer owner-a"}, json={"local_asset_id": "meal", "file_name": "meal.jpg", "content_type": "image/jpeg", "byte_size": 100})
    upload_id = response.json()["image_upload_id"]
    assert client.post(f"/v1/profiles/{pid}/equipment-identifications", headers={"Authorization": "Bearer owner-a"}, json={"image_upload_id": upload_id}).status_code == 404
    assert get_persistence_repository().get_image_upload(upload_id).upload_status == "ready"


def test_provider_failure_still_deletes_photo_without_leaking_error(client, monkeypatch):
    pid = profile(client)
    upload_id = ready_image(client, pid, monkeypatch)
    class FailingProvider:
        def identify(self, image):
            raise AnalysisProviderUnavailableError("fixture-secret-in-transport")
    monkeypatch.setattr(equipment_routes, "get_equipment_provider", lambda: FailingProvider())
    response = client.post(f"/v1/profiles/{pid}/equipment-identifications", headers={"Authorization": "Bearer owner-a"}, json={"image_upload_id": upload_id})
    assert response.status_code == 503
    assert "fixture-secret" not in response.text
    assert get_persistence_repository().get_image_upload(upload_id).upload_status == "deleted"


def test_claim_is_atomic_and_owner_scoped(client, monkeypatch):
    pid = profile(client)
    upload_id = ready_image(client, pid, monkeypatch)
    repo = get_persistence_repository()
    assert not repo.claim_transient_image_upload(upload_id, "owner-b")
    assert repo.claim_transient_image_upload(upload_id, "owner-a")
    assert not repo.claim_transient_image_upload(upload_id, "owner-a")


def test_incomplete_upload_is_available_for_retention_cleanup(client):
    repo = get_persistence_repository()
    repo.save_image_upload(payload=ImageUploadRequest(local_asset_id="equipment-test", file_name="equipment-guide.jpg", content_type="image/jpeg", byte_size=100), image_upload_id="pending-equipment", image_reference="local://pending", object_key="uploads/pending/equipment-guide.jpg", upload_status="pending", cleanup_after="2026-01-01T00:00:00Z")
    assert "pending-equipment" in [item.image_upload_id for item in repo.list_expired_image_uploads("2026-10-05T00:00:00Z")]


def test_cleanup_failure_keeps_auditable_retryable_record(client, monkeypatch):
    pid = profile(client)
    upload_id = ready_image(client, pid, monkeypatch)
    def fail(*args): raise StorageConfigurationError("fixture-storage-secret")
    monkeypatch.setattr(equipment_routes, "_remove_transient_image", fail)
    response = client.post(f"/v1/profiles/{pid}/equipment-identifications", headers={"Authorization": "Bearer owner-a"}, json={"image_upload_id": upload_id})
    assert response.status_code == 200 and "fixture-storage-secret" not in response.text
    assert response.json()["cleanup_pending"] is True
    upload = get_persistence_repository().get_image_upload(upload_id)
    assert upload.upload_status == "deleting" and upload.cleanup_after is not None
    assert client.post(f"/v1/profiles/{pid}/equipment-identifications", headers={"Authorization": "Bearer owner-a"}, json={"image_upload_id": upload_id}).status_code == 200


def test_openai_payload_is_bounded_and_requires_confirmation():
    calls = []
    def call(payload, key):
        calls.append(payload)
        assert key == "fixture-key"
        return json.dumps({"equipment_id": "lat_pulldown", "confidence": "high", "visible_evidence": ["위쪽 도르래와 허벅지 패드가 보여요"]})
    result = OpenAIEquipmentProvider(api_key="fixture-key", model="vision-model", responses_call=call).identify("https://storage.example/temporary")
    assert result.equipment_id == "lat_pulldown" and result.needs_confirmation
    assert calls[0]["store"] is False
    assert "fixture-key" not in json.dumps(calls)
    assert len(calls) == 1


@pytest.mark.parametrize("output", ["invalid", '{"equipment_id":"invented","confidence":"high","visible_evidence":[]}', '{"equipment_id":"leg_press","confidence":"certain","visible_evidence":[]}', '{"equipment_id":"leg_press","confidence":"low","visible_evidence":"not-a-list"}'])
def test_malformed_equipment_output_fails_closed(output):
    provider = OpenAIEquipmentProvider(api_key="fixture-key", model="vision-model", responses_call=lambda payload, key: output)
    with pytest.raises(StructuredOutputMalformedError):
        provider.identify("https://storage.example/temporary")


def test_unknown_equipment_never_becomes_a_confident_match():
    result = OpenAIEquipmentProvider(api_key="fixture-key", model="vision-model", responses_call=lambda payload, key: '{"equipment_id":"unknown","confidence":"high","visible_evidence":[]}').identify("https://storage.example/temporary")
    assert result.equipment_id is None and result.confidence == "none"


def test_provider_requires_explicit_activation_and_key():
    with pytest.raises(EquipmentProviderDisabledError): get_equipment_provider({})
    with pytest.raises(AnalysisProviderConfigurationError): get_equipment_provider({"EQUIPMENT_AI_PROVIDER": "openai"})


def test_youtube_no_key_makes_no_http_call():
    def forbidden(*args, **kwargs): raise AssertionError("network should not be called")
    assert get_equipment_guide("leg_press", environ={}, opener=forbidden).source == "search_link"


def test_youtube_only_returns_valid_video_links_without_key_exposure():
    payload = {"items": [{"id": {"videoId": "abc123XYZ_-"}, "snippet": {"title": "A &amp; B", "channelTitle": "Coach"}}, {"id": {"videoId": "https://evil.example"}, "snippet": {}}]}
    def opener(url, timeout):
        query = parse_qs(urlparse(url).query)
        assert query["type"] == ["video"] and query["safeSearch"] == ["strict"]
        return io.StringIO(json.dumps(payload))
    result = get_equipment_guide("leg_press", environ={"YOUTUBE_API_KEY": "fixture-secret"}, opener=opener)
    assert len(result.videos) == 1 and result.videos[0].title == "A & B"
    assert "fixture-secret" not in result.model_dump_json()
    assert result.videos[0].url == "https://www.youtube.com/watch?v=abc123XYZ_-"


@pytest.mark.parametrize("payload", [[], {"items": None}, {"items": [None, {"id": "invalid"}]}])
def test_youtube_malformed_results_fall_back_to_search(payload):
    result = get_equipment_guide("leg_press", environ={"YOUTUBE_API_KEY": "fixture-key"}, opener=lambda *args, **kwargs: io.StringIO(json.dumps(payload)))
    assert result.source == "search_link" and not result.videos


def test_youtube_transport_failure_does_not_expose_key():
    def opener(*args, **kwargs): raise URLError("fixture-secret")
    result = get_equipment_guide("leg_press", environ={"YOUTUBE_API_KEY": "fixture-secret"}, opener=opener)
    assert result.source == "search_link"
    assert "fixture-secret" not in result.model_dump_json()


def test_retention_gate_blocks_activation_even_with_existing_key():
    env = {"EQUIPMENT_AI_PROVIDER": "openai", "AI_PROVIDER_API_KEY": "fixture-key"}
    with pytest.raises(AnalysisProviderConfigurationError, match="equipment_retention_not_verified"):
        get_equipment_provider(env)
    assert isinstance(get_equipment_provider({**env, "EQUIPMENT_RETENTION_VERIFIED": "true"}), OpenAIEquipmentProvider)


def test_stale_completion_cannot_restore_consumed_upload(client, monkeypatch):
    pid = profile(client)
    upload_id = ready_image(client, pid, monkeypatch)
    repo = get_persistence_repository()
    ready = repo.get_image_upload(upload_id)
    repo.save_image_upload(payload=ImageUploadRequest(local_asset_id=ready.local_asset_id, file_name=ready.file_name, content_type=ready.content_type, byte_size=ready.byte_size), image_upload_id=upload_id, image_reference=ready.image_reference, object_key=ready.object_key, owner_id=ready.owner_id, upload_status="pending", cleanup_after=ready.cleanup_after, upload_expires_at=ready.upload_expires_at)
    original = repo.get_image_upload
    stale = original(upload_id)
    repo.mark_image_upload_deleting(upload_id)
    calls = 0
    def stale_first(upload_id):
        nonlocal calls
        calls += 1
        return stale if calls == 1 else original(upload_id)
    monkeypatch.setattr(repo, "get_image_upload", stale_first)
    payload = ImageUploadCompleteRequest(image_upload_id=upload_id, object_key=ready.object_key, file_name=ready.file_name, content_type=ready.content_type, byte_size=ready.byte_size)
    with pytest.raises(ImageUploadError, match="image_upload_state_changed"):
        complete_presigned_image_upload(payload, repo, owner_id="owner-a")
    assert original(upload_id).upload_status == "deleting"


def test_r2_delete_keeps_replay_cleanup_tombstone(client, monkeypatch):
    repo = get_persistence_repository()
    expires = datetime.now(UTC) + timedelta(minutes=2)
    record = repo.save_image_upload(payload=ImageUploadRequest(local_asset_id="equipment-tombstone", file_name="equipment-guide.jpg", content_type="image/jpeg", byte_size=100), image_upload_id="equipment-tombstone", image_reference="r2://private/equipment", storage_provider="r2", object_key="uploads/equipment-tombstone/equipment-guide.jpg", owner_id="owner-a", upload_expires_at=expires.isoformat())
    deletes = []
    class Storage:
        provider = "r2"
        def delete_object(self, *, object_key): deletes.append(object_key)
    monkeypatch.setattr(equipment_routes, "get_storage_adapter", lambda: Storage())
    equipment_routes._remove_transient_image(record, repo)
    tombstone = repo.get_image_upload(record.image_upload_id)
    assert deletes == [record.object_key]
    assert tombstone.upload_status == "deleting" and tombstone.object_key == record.object_key
    assert tombstone.image_reference.startswith("deleted://")
    assert not repo.list_expired_image_uploads(expires.isoformat())
    assert record.image_upload_id in [item.image_upload_id for item in repo.list_expired_image_uploads((expires + timedelta(hours=2)).isoformat())]


def test_account_daily_budget_counts_attempts_and_exempts_receipt_retry(client, monkeypatch):
    monkeypatch.setenv("EQUIPMENT_DAILY_LIMIT", "1")
    pid = profile(client)
    first = ready_image(client, pid, monkeypatch)
    calls = []
    class Provider:
        def identify(self, reference):
            calls.append(reference)
            return EquipmentIdentification(equipment_id="lat_pulldown", confidence="medium", visible_evidence=[])
    monkeypatch.setattr(equipment_routes, "get_equipment_provider", lambda: Provider())
    url = f"/v1/profiles/{pid}/equipment-identifications"
    headers = {"Authorization": "Bearer owner-a"}
    assert client.post(url, headers=headers, json={"image_upload_id": first}).status_code == 200
    assert client.post(url, headers=headers, json={"image_upload_id": first}).status_code == 200
    second = ready_image(client, pid, monkeypatch)
    monkeypatch.setattr(equipment_routes, "get_equipment_provider", lambda: Provider())
    assert client.post(url, headers=headers, json={"image_upload_id": second}).status_code == 429
    assert len(calls) == 1


def test_global_budget_and_owner_concurrency_are_atomic(client):
    repo = get_coach_repository()
    pid = profile(client)
    def reserve(index):
        try:
            return repo.reserve_equipment_analysis(pid, "owner-a", f"parallel-{index}", 10, 100)
        except EquipmentUsageLimitError as exc:
            return exc.code
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(reserve, range(4)))
    assert results.count("reserved") == 1 and results.count("equipment_scan_in_progress") == 3
    pid_b = profile(client, "owner-b")
    with pytest.raises(EquipmentUsageLimitError, match="equipment_daily_limit"):
        repo.reserve_equipment_analysis(pid_b, "owner-b", "global-over-budget", 10, 1)


def test_discard_is_owner_scoped_and_blocks_late_completion(client, monkeypatch):
    pid = profile(client)
    other_pid = profile(client, "owner-b")
    upload_id = ready_image(client, pid, monkeypatch)
    assert client.delete(f"/v1/profiles/{other_pid}/equipment-image-uploads/{upload_id}", headers={"Authorization": "Bearer owner-b"}).status_code == 404
    assert client.delete(f"/v1/profiles/{pid}/equipment-image-uploads/{upload_id}", headers={"Authorization": "Bearer owner-a"}).status_code == 200
    assert get_persistence_repository().get_image_upload(upload_id).upload_status == "deleted"


def test_youtube_negative_cache_avoids_repeated_failure_calls(monkeypatch):
    from app.services import equipment_guide as service
    service._VIDEO_CACHE.clear()
    monkeypatch.setattr(service, "_VIDEO_COOLDOWN_UNTIL", 0)
    calls = []
    def fail(*args, **kwargs):
        calls.append(args)
        raise URLError("fixture-secret")
    monkeypatch.setattr(service, "urlopen", fail)
    env = {"YOUTUBE_API_KEY": "fixture-secret"}
    assert service.get_equipment_guide("leg_press", environ=env).source == "search_link"
    assert service.get_equipment_guide("leg_press", environ=env).source == "search_link"
    assert len(calls) == 1
    service._VIDEO_CACHE.clear()


def test_profile_deletion_does_not_reset_owner_or_global_paid_budget(client):
    repo = get_coach_repository()
    pid = profile(client)
    assert repo.reserve_equipment_analysis(pid, "owner-a", "spent-before-delete", 1, 1) == "reserved"
    repo.finish_equipment_analysis(pid, "spent-before-delete", None)
    assert repo.delete_profile(pid)
    replacement = profile(client)
    with pytest.raises(EquipmentUsageLimitError, match="equipment_daily_limit"):
        repo.reserve_equipment_analysis(replacement, "owner-a", "new-owner-attempt", 1, 100)
    other = profile(client, "owner-b")
    with pytest.raises(EquipmentUsageLimitError, match="equipment_daily_limit"):
        repo.reserve_equipment_analysis(other, "owner-b", "new-global-attempt", 10, 1)


def test_profile_deletion_preserves_only_unexpired_replay_cleanup(client, monkeypatch):
    pid = profile(client)
    repo = get_persistence_repository()
    expires = datetime.now(UTC) + timedelta(minutes=2)
    record = repo.save_image_upload(payload=ImageUploadRequest(local_asset_id="equipment-delete-profile", file_name="equipment-guide.jpg", content_type="image/jpeg", byte_size=100), image_upload_id="equipment-delete-profile", image_reference="r2://private/equipment", storage_provider="r2", object_key="uploads/equipment-delete-profile/equipment-guide.jpg", owner_id="owner-a", upload_expires_at=expires.isoformat())
    deletes = []
    class Storage:
        provider = "r2"
        def delete_object(self, *, object_key): deletes.append(object_key)
    monkeypatch.setattr(coach_routes, "get_storage_adapter", lambda: Storage())
    response = client.delete(f"/v1/profiles/{pid}", headers={"Authorization": "Bearer owner-a"})
    assert response.status_code == 200
    assert get_coach_repository().get_profile(pid) is None
    tombstone = repo.get_image_upload(record.image_upload_id)
    assert tombstone.owner_id is None and tombstone.local_asset_id == "deleted" and tombstone.file_name == "deleted"
    assert tombstone.upload_status == "deleting" and tombstone.object_key == record.object_key
    assert tombstone.image_reference.startswith("deleted://") and deletes == [record.object_key]
    assert record.image_upload_id in [item.image_upload_id for item in repo.list_expired_image_uploads((expires + timedelta(hours=2)).isoformat())]


def test_cancellation_and_analysis_claim_compete_atomically(client, monkeypatch):
    pid = profile(client)
    repo = get_persistence_repository()
    first = ready_image(client, pid, monkeypatch)
    assert repo.cancel_transient_image_upload(first, "owner-a")
    assert not repo.claim_transient_image_upload(first, "owner-a")
    second = ready_image(client, pid, monkeypatch)
    cancel = repo.cancel_transient_image_upload
    def claim_before_cancel(upload_id, owner):
        assert repo.claim_transient_image_upload(upload_id, owner)
        return cancel(upload_id, owner)
    monkeypatch.setattr(repo, "cancel_transient_image_upload", claim_before_cancel)
    monkeypatch.setattr(equipment_routes, "_remove_transient_image", lambda *args: pytest.fail("active analysis image must not be deleted by cancellation"))
    response = client.delete(f"/v1/profiles/{pid}/equipment-image-uploads/{second}", headers={"Authorization": "Bearer owner-a"})
    assert response.status_code == 200 and response.json()["status"] == "cleanup_after_analysis"


def test_committed_result_survives_failed_persistence_acknowledgment(client, monkeypatch):
    pid = profile(client)
    upload_id = ready_image(client, pid, monkeypatch)
    repo = get_coach_repository()
    finish = repo.finish_equipment_analysis
    calls = []
    class Provider:
        def identify(self, reference):
            calls.append(reference)
            return EquipmentIdentification(equipment_id="leg_press", confidence="medium", visible_evidence=[])
    monkeypatch.setattr(equipment_routes, "get_equipment_provider", lambda: Provider())
    def commit_then_fail_ack(profile_id, image_id, result):
        finish(profile_id, image_id, result)
        if result is not None:
            raise PersistenceError("fixture-commit-ack-failure")
    monkeypatch.setattr(repo, "finish_equipment_analysis", commit_then_fail_ack)
    url = f"/v1/profiles/{pid}/equipment-identifications"
    headers = {"Authorization": "Bearer owner-a"}
    first = client.post(url, headers=headers, json={"image_upload_id": upload_id})
    assert first.status_code == 200 and first.json()["equipment_id"] == "leg_press"
    assert client.post(url, headers=headers, json={"image_upload_id": upload_id}).json() == first.json()
    assert len(calls) == 1 and repo.get_equipment_receipt(pid, upload_id)["status"] == "complete"


def test_terminal_receipt_is_monotonic(client):
    repo = get_coach_repository()
    pid = profile(client)
    assert repo.reserve_equipment_analysis(pid, "owner-a", "monotonic-complete", 10, 100) == "reserved"
    result = {"equipment_id": "lat_pulldown"}
    repo.finish_equipment_analysis(pid, "monotonic-complete", result)
    repo.finish_equipment_analysis(pid, "monotonic-complete", None)
    assert repo.get_equipment_receipt(pid, "monotonic-complete")["result"] == result
    assert repo.reserve_equipment_analysis(pid, "owner-a", "monotonic-failed", 10, 100) == "reserved"
    repo.finish_equipment_analysis(pid, "monotonic-failed", None)
    repo.finish_equipment_analysis(pid, "monotonic-failed", result)
    assert repo.get_equipment_receipt(pid, "monotonic-failed")["status"] == "failed"
