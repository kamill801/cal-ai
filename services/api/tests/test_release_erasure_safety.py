from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app import coach_routes
from app.coach_schemas import CoachProfile
from app.schemas import AnalysisJobCreateResponse, AnalysisJobRequest, ImageUploadRequest
from app.services import account_deletion
from app.services.analytics_repository import get_analytics_repository
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError, get_persistence_repository
from app.services.storage import (
    ERASURE_GUARD_CONTENT_TYPE,
    StorageConfigurationError,
    StorageObjectMetadata,
)


OWNER = "11111111-1111-4111-8111-111111111111"
FOREIGN = "22222222-2222-4222-8222-222222222222"
NAMESPACE = "r2-v1:" + "a" * 64


@pytest.fixture
def erasure(monkeypatch):
    meals = get_persistence_repository()
    coach = get_coach_repository()
    get_analytics_repository()
    meals.prepare_account_deletion()
    storage = SimpleNamespace(
        provider="r2", storage_namespace=Mock(return_value=NAMESPACE),
        erase_account_object=Mock(return_value=True), delete_object=Mock(), stat_object=Mock(),
    )
    monkeypatch.setattr(coach_routes, "get_storage_adapter", lambda: storage)
    for flag in (
        "ACCOUNT_DELETION_ENABLED", "ACCOUNT_DELETION_WORKER_ENABLED",
        "R2_WRITE_ONCE_UPLOADS_ENABLED",
    ):
        monkeypatch.setenv(flag, "false")
    app = FastAPI()
    app.include_router(coach_routes.router)

    @app.middleware("http")
    async def fixture_owner(request: Request, call_next):
        request.state.user_id = OWNER
        return await call_next(request)

    def profile(label):
        coach.save_profile(CoachProfile(
            profile_id=label, owner_id=OWNER, created_at="2026-11-15T00:00:00+00:00",
            onboarding={
                "age": 29, "sex": "male", "height_cm": 176, "current_weight_kg": 82,
                "target_weight_kg": 76, "goal_type": "recomp", "activity_level": "moderate",
                "training_frequency": "3-4",
            },
            target={"calories_kcal": 2000, "protein_g": 100, "carbs_g": 250, "fat_g": 60},
        ))
        return label

    def upload(profile_id, *, provider="r2", owner=OWNER, key="sealed"):
        identifier = "image-upload-" + str(uuid4())
        object_key = f"uploads/{identifier}/sealed-v1/image.jpg" if key == "sealed" else key
        record = meals.save_image_upload(
            payload=ImageUploadRequest(
                local_asset_id=identifier, file_name="fixture.jpg",
                content_type="image/jpeg", byte_size=12,
            ),
            image_upload_id=identifier, image_reference="fixture://" + identifier,
            storage_provider=provider, storage_namespace=NAMESPACE if provider != "local" else None,
            object_key=object_key, owner_id=owner,
        )
        meals.save_analysis_job(
            payload=AnalysisJobRequest(image_upload_id=identifier, profile_id=profile_id),
            image_reference=record.image_reference, owner_id=owner,
            create_response=AnalysisJobCreateResponse(
                analysis_job_id="job-" + identifier, status="queued",
            ),
        )
        return record

    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client, meals=meals, coach=coach, storage=storage,
            profile=profile, upload=upload,
        )


@pytest.mark.parametrize("unsafe_first", [True, False])
@pytest.mark.parametrize("failure", [
    "legacy", "key_binding", "provider", "ownerless", "foreign_owner", "missing_key",
    "missing_namespace", "blank_namespace", "namespace_mismatch", "missing_erase",
])
def test_profile_preflights_every_remote_record_before_any_side_effect(
    erasure, monkeypatch, failure, unsafe_first,
):
    own = erasure.profile("selected")
    valid, unsafe = erasure.upload(own), erasure.upload(own)
    if failure == "legacy":
        unsafe = replace(unsafe, object_key=f"uploads/{unsafe.image_upload_id}/legacy.jpg")
    elif failure == "key_binding":
        unsafe = replace(unsafe, object_key=valid.object_key)
    elif failure == "provider":
        erasure.storage.provider = "unsupported-remote"
        valid = replace(valid, storage_provider=erasure.storage.provider)
        unsafe = replace(unsafe, storage_provider=erasure.storage.provider)
    elif failure in {"ownerless", "foreign_owner"}:
        unsafe = replace(unsafe, owner_id=None if failure == "ownerless" else FOREIGN)
    elif failure == "missing_key":
        unsafe = replace(unsafe, object_key=None)
    elif failure.endswith("namespace") or failure == "namespace_mismatch":
        unsafe = replace(unsafe, storage_namespace={
            "missing_namespace": None, "blank_namespace": " ",
            "namespace_mismatch": "other-namespace",
        }[failure])
    else:
        erasure.storage.erase_account_object = None
    selected = [unsafe, valid] if unsafe_first else [valid, unsafe]
    monkeypatch.setattr(erasure.meals, "list_profile_image_uploads", lambda *a, **kw: selected)
    mark = Mock(wraps=erasure.meals.mark_image_upload_deleting)
    monkeypatch.setattr(erasure.meals, "mark_image_upload_deleting", mark)
    before = [erasure.meals.get_image_upload(item.image_upload_id) for item in selected]

    response = erasure.client.delete(f"/v1/profiles/{own}")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "profile_image_verification_required"
    mark.assert_not_called()
    erasure.storage.delete_object.assert_not_called()
    erasure.storage.stat_object.assert_not_called()
    if callable(erasure.storage.erase_account_object):
        erasure.storage.erase_account_object.assert_not_called()
    assert [erasure.meals.get_image_upload(item.image_upload_id) for item in selected] == before
    assert erasure.coach.get_profile(own) is not None


@pytest.mark.parametrize("proof", [False, None, 1, "verified"])
def test_profile_retains_inventory_until_remote_erasure_is_exactly_true(erasure, proof):
    own = erasure.profile("selected")
    record = erasure.upload(own)
    erasure.storage.erase_account_object.return_value = proof

    response = erasure.client.delete(f"/v1/profiles/{own}")

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_delete_unavailable"
    pending = erasure.meals.get_image_upload(record.image_upload_id)
    assert pending is not None and pending.upload_status == "deleting"
    assert pending.object_key == record.object_key
    assert erasure.meals.get_analysis_job("job-" + record.image_upload_id) is not None
    assert erasure.coach.get_profile(own) is not None
    erasure.storage.delete_object.assert_not_called()
    erasure.storage.stat_object.assert_not_called()

    erasure.storage.erase_account_object.return_value = True
    assert erasure.client.delete(f"/v1/profiles/{own}").status_code == 200
    assert erasure.meals.get_image_upload(record.image_upload_id) is None


@pytest.mark.parametrize("error", [StorageConfigurationError, OSError, ValueError])
def test_profile_storage_failure_preserves_all_records_for_retry(erasure, error):
    own = erasure.profile("selected")
    records = [erasure.upload(own), erasure.upload(own)]
    erasure.storage.erase_account_object.side_effect = [True, error("private-fixture")]

    response = erasure.client.delete(f"/v1/profiles/{own}")
    assert response.status_code == 503
    assert "private-fixture" not in response.text
    assert all(
        erasure.meals.get_image_upload(record.image_upload_id) is not None for record in records
    )
    assert erasure.coach.get_profile(own) is not None
    erasure.storage.delete_object.assert_not_called()


def test_profile_does_not_infer_legacy_lock_from_empty_object_metadata(erasure):
    own = erasure.profile("selected")
    record = erasure.upload(own, key="uploads/legacy-fixture/image.jpg")
    erasure.storage.stat_object.return_value = StorageObjectMetadata(0, ERASURE_GUARD_CONTENT_TYPE)

    response = erasure.client.delete(f"/v1/profiles/{own}")

    assert response.status_code == 503
    assert erasure.meals.get_image_upload(record.image_upload_id) == record
    erasure.storage.erase_account_object.assert_not_called()
    erasure.storage.delete_object.assert_not_called()
    erasure.storage.stat_object.assert_not_called()


def test_profile_requires_verified_sealed_erasure_and_preserves_other_profile(erasure):
    own, other = erasure.profile("selected"), erasure.profile("retained")
    selected, retained = erasure.upload(own), erasure.upload(other)

    response = erasure.client.delete(f"/v1/profiles/{own}")

    assert response.status_code == 200
    erasure.storage.erase_account_object.assert_called_once_with(object_key=selected.object_key)
    erasure.storage.delete_object.assert_not_called()
    assert erasure.meals.get_image_upload(selected.image_upload_id) is None
    assert erasure.meals.get_image_upload(retained.image_upload_id) == retained
    assert erasure.coach.get_profile(other) is not None


def test_profile_failed_deletion_claim_does_not_erase_or_discard_inventory(erasure, monkeypatch):
    own = erasure.profile("selected")
    record = erasure.upload(own)
    def unavailable(*args, **kwargs):
        raise PersistenceError("image_upload_deletion_unavailable")

    monkeypatch.setattr(erasure.meals, "claim_profile_erasure", unavailable)

    assert erasure.client.delete(f"/v1/profiles/{own}").status_code == 503
    erasure.storage.erase_account_object.assert_not_called()
    assert erasure.meals.get_image_upload(record.image_upload_id) == record
    assert erasure.coach.get_profile(own) is not None


def test_profile_can_remove_retention_deleted_metadata_only_after_verified_remote_erase(erasure):
    own = erasure.profile("selected")
    record = erasure.upload(own)
    assert erasure.meals.mark_image_upload_deleted(record.image_upload_id)

    assert erasure.client.delete(f"/v1/profiles/{own}").status_code == 200
    erasure.storage.erase_account_object.assert_called_once_with(object_key=record.object_key)
    assert erasure.meals.get_image_upload(record.image_upload_id) is None


@pytest.mark.parametrize("key", [None, "fixture/local"])
def test_profile_preserves_local_ownerless_deletion(erasure, key):
    own = erasure.profile("selected")
    record = erasure.upload(own, provider="local", owner=None, key=key)
    erasure.storage.provider = "local"

    assert erasure.client.delete(f"/v1/profiles/{own}").status_code == 200
    assert erasure.meals.get_image_upload(record.image_upload_id) is None
    erasure.storage.erase_account_object.assert_not_called()
    assert erasure.storage.delete_object.call_count == int(key is not None)


@pytest.mark.parametrize("stage,status", [
    (0, "pending"), (1, "pending"), (2, "pending"), (3, "deleted"),
])
def test_existing_accepted_account_jobs_keep_their_persisted_status(monkeypatch, stage, status):
    repository = SimpleNamespace(get_account_deletion_stage=Mock(return_value=stage))
    monkeypatch.setattr(account_deletion, "get_persistence_repository", lambda: repository)
    storage = Mock(side_effect=AssertionError("accepted retries must not manufacture completion"))
    monkeypatch.setattr(account_deletion, "get_storage_adapter", storage)
    monkeypatch.setenv("ACCOUNT_DELETION_ENABLED", "false")
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")

    assert account_deletion.delete_account(OWNER) == status
    storage.assert_not_called()
