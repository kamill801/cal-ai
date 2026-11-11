from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

import app.main as main
from app.schemas import ImageUploadRequest
from app.services.account_deletion import AccountDeletionError
from app.services.analytics_repository import get_analytics_repository
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError, get_persistence_repository
from app.services.storage import StorageConfigurationError


HEADERS = {"Authorization": "Bearer fixture-cron-secret"}
STORAGE_NAMESPACE = "r2://fixture-account/fixture-bucket"


@pytest.fixture
def cron(monkeypatch):
    monkeypatch.setenv("CRON_SECRET", "fixture-cron-secret")
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "true")
    repository = SimpleNamespace(
        list_expired_image_uploads=Mock(return_value=[]),
        mark_image_upload_deleting=Mock(return_value=True),
        mark_image_upload_deleted=Mock(return_value=True),
    )
    storage = SimpleNamespace(
        provider="local", delete_object=Mock(),
        storage_namespace=Mock(return_value=STORAGE_NAMESPACE),
    )
    worker = Mock(return_value={"failed": 0})
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(main, "get_persistence_repository", lambda: repository)
    monkeypatch.setattr(main, "get_storage_adapter", Mock(return_value=storage))
    monkeypatch.setattr(main, "run_account_deletion_jobs", worker)
    monkeypatch.setattr(main, "monotonic", lambda: clock.now)
    return SimpleNamespace(repository=repository, storage=storage, worker=worker, clock=clock)


def _expired(image_upload_id, *, object_key=True, storage_provider="local", storage_namespace=None):
    return SimpleNamespace(
        image_upload_id=image_upload_id,
        storage_provider=storage_provider,
        storage_namespace=storage_namespace,
        object_key=f"uploads/{image_upload_id}" if object_key else None,
    )


def _cleanup():
    return TestClient(main.app).get("/internal/cleanup-images", headers=HEADERS)


def test_existing_cron_runs_bounded_account_jobs_without_a_second_schedule(cron):
    client = TestClient(main.app)
    assert client.get("/internal/cleanup-images").status_code == 401
    cron.worker.assert_not_called()
    cron.repository.list_expired_image_uploads.assert_not_called()
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 0}
    cron.worker.assert_called_once_with(max_jobs=3, max_objects=5, budget_seconds=25)
    assert cron.repository.list_expired_image_uploads.call_args.kwargs == {"limit": 100}


@pytest.mark.parametrize("error_type", [AccountDeletionError, PersistenceError])
def test_account_worker_failure_is_sanitized_and_retention_still_runs(cron, error_type):
    cron.worker.side_effect = error_type("private account failure fixture-cron-secret")
    cron.repository.list_expired_image_uploads.return_value = [_expired("expired")]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "account_deletion_cleanup_unavailable"
    assert "fixture-cron-secret" not in response.text
    assert "private account failure" not in response.text
    cron.repository.mark_image_upload_deleted.assert_called_once_with("expired")


def test_account_worker_reported_failure_does_not_claim_success(cron):
    cron.worker.return_value = {"failed": 1}
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "account_deletion_cleanup_unavailable"
    cron.repository.list_expired_image_uploads.assert_called_once()


def test_disabled_worker_preserves_existing_retention_cron(cron, monkeypatch):
    monkeypatch.setenv("ACCOUNT_DELETION_WORKER_ENABLED", "false")
    cron.repository.list_expired_image_uploads.return_value = [_expired("expired", object_key=False)]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.worker.assert_not_called()
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_called_once_with("expired")


def test_account_worker_runs_before_retention_with_a_reserved_budget(cron):
    events = []
    cron.worker.side_effect = lambda **_kwargs: events.append("account") or {"failed": 0}

    def expired(_now, *, limit):
        assert limit == 100
        events.append("retention")
        return []

    cron.repository.list_expired_image_uploads.side_effect = expired
    assert _cleanup().status_code == 200
    assert events == ["account", "retention"]


@pytest.mark.parametrize("operation", [
    "list_expired_image_uploads", "mark_image_upload_deleting", "mark_image_upload_deleted",
])
def test_retention_persistence_failure_cannot_starve_account_worker(cron, operation):
    cron.repository.list_expired_image_uploads.return_value = [_expired("tombstoned")]
    getattr(cron.repository, operation).side_effect = PersistenceError(
        "account_deleted private subject fixture-cron-secret"
    )
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "persistence_unavailable"
    assert "private subject" not in response.text
    assert "fixture-cron-secret" not in response.text
    cron.worker.assert_called_once()
    if operation == "mark_image_upload_deleting":
        cron.storage.delete_object.assert_not_called()
        cron.repository.mark_image_upload_deleted.assert_not_called()


@pytest.mark.parametrize("error_type", [StorageConfigurationError, OSError, ValueError])
def test_storage_setup_failure_cannot_starve_account_worker(cron, monkeypatch, error_type):
    monkeypatch.setattr(main, "get_storage_adapter", Mock(side_effect=error_type("private storage")))
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    assert "private storage" not in response.text
    cron.worker.assert_called_once()


@pytest.mark.parametrize("failure_stage", ["deleting", "storage", "deleted"])
def test_retention_race_or_object_failure_does_not_block_other_images(cron, failure_stage):
    cron.repository.list_expired_image_uploads.return_value = [
        _expired("raced"), _expired("independent"),
    ]
    failure = (
        StorageConfigurationError("private storage failure")
        if failure_stage == "storage" else PersistenceError("account_deleted private subject")
    )
    operation = {
        "deleting": cron.repository.mark_image_upload_deleting,
        "storage": cron.storage.delete_object,
        "deleted": cron.repository.mark_image_upload_deleted,
    }[failure_stage]
    operation.side_effect = [failure, True]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["retryable"] is True
    assert "private" not in response.text
    cron.worker.assert_called_once()
    assert cron.repository.mark_image_upload_deleted.call_args.args == ("independent",)


def test_provider_mismatch_is_sanitized_but_other_retention_work_continues(cron):
    mismatched = _expired("foreign-provider")
    mismatched.storage_provider = "r2"
    cron.repository.list_expired_image_uploads.return_value = [mismatched, _expired("local")]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    cron.worker.assert_called_once()
    cron.storage.delete_object.assert_called_once_with(object_key="uploads/local")
    cron.repository.mark_image_upload_deleted.assert_called_once_with("local")


def test_deadline_after_account_work_does_not_start_retention_or_claim_success(cron):
    def account_work(**_kwargs):
        cron.clock.now = 45.0
        return {"failed": 0}

    cron.worker.side_effect = account_work
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    cron.worker.assert_called_once()
    cron.repository.list_expired_image_uploads.assert_not_called()


@pytest.mark.parametrize("slow_stage", ["listing", "deleting", "storage", "deleted"])
def test_retention_loop_obeys_deadline_between_operations(cron, slow_stage):
    records = [_expired("first"), _expired("second")]
    cron.repository.list_expired_image_uploads.return_value = records

    def expire(*_args, **_kwargs):
        cron.clock.now = 45.0
        return records if slow_stage == "listing" else True

    operation = {
        "listing": cron.repository.list_expired_image_uploads,
        "deleting": cron.repository.mark_image_upload_deleting,
        "storage": cron.storage.delete_object,
        "deleted": cron.repository.mark_image_upload_deleted,
    }[slow_stage]
    operation.side_effect = expire
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    cron.worker.assert_called_once()
    assert cron.repository.mark_image_upload_deleting.call_count <= 1
    assert cron.storage.delete_object.call_count == (1 if slow_stage in {"storage", "deleted"} else 0)
    assert cron.repository.mark_image_upload_deleted.call_count == (1 if slow_stage == "deleted" else 0)


def test_retention_batch_is_bounded_even_when_clock_does_not_advance(cron):
    cron.repository.list_expired_image_uploads.return_value = [_expired(str(i)) for i in range(101)]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    assert cron.storage.delete_object.call_count == 100
    assert cron.repository.mark_image_upload_deleted.call_count == 100
    cron.worker.assert_called_once()


def test_success_counts_completed_retention_images_only(cron):
    cron.repository.list_expired_image_uploads.return_value = [_expired("first"), _expired("second")]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 2}
    assert cron.repository.mark_image_upload_deleted.call_count == 2


def test_tombstoned_claim_is_skipped_without_deleting_storage(cron):
    cron.repository.list_expired_image_uploads.return_value = [
        _expired("tombstoned"), _expired("independent"),
    ]
    cron.repository.mark_image_upload_deleting.side_effect = [False, True]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.storage.delete_object.assert_called_once_with(object_key="uploads/independent")
    cron.repository.mark_image_upload_deleted.assert_called_once_with("independent")
    cron.worker.assert_called_once()


def test_tombstone_race_after_storage_delete_is_not_counted_as_retention_deletion(cron):
    cron.repository.list_expired_image_uploads.return_value = [
        _expired("tombstoned"), _expired("independent"),
    ]
    cron.repository.mark_image_upload_deleted.side_effect = [False, True]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.worker.assert_called_once()


def test_tombstoned_upload_without_object_key_is_not_counted(cron):
    cron.repository.list_expired_image_uploads.return_value = [_expired("tombstoned", object_key=False)]
    cron.repository.mark_image_upload_deleted.return_value = False
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 0}
    cron.storage.delete_object.assert_not_called()


def test_account_budget_leaves_retention_headroom(cron):
    def account_work(**kwargs):
        cron.clock.now += kwargs["budget_seconds"]
        return {"failed": 0}

    cron.worker.side_effect = account_work
    cron.repository.list_expired_image_uploads.return_value = [_expired("expired")]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.worker.assert_called_once_with(max_jobs=3, max_objects=5, budget_seconds=25)


@pytest.mark.parametrize("slow_stage", ["listing", "deleting"])
def test_retention_delete_reserves_network_timeout_and_checkpoint_headroom(cron, slow_stage):
    records = [_expired("expired")]
    cron.repository.list_expired_image_uploads.return_value = records

    def use_headroom(*_args, **_kwargs):
        cron.clock.now = 35.1
        return records if slow_stage == "listing" else True

    operation = (
        cron.repository.list_expired_image_uploads
        if slow_stage == "listing" else cron.repository.mark_image_upload_deleting
    )
    operation.side_effect = use_headroom
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    cron.worker.assert_called_once()
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_not_called()


def test_retention_delete_is_admitted_with_ten_seconds_remaining(cron):
    records = [_expired("expired")]

    def listing(*_args, **_kwargs):
        cron.clock.now = 35.0
        return records

    def delete_object(**_kwargs):
        cron.clock.now += 8.0

    cron.repository.list_expired_image_uploads.side_effect = listing
    cron.storage.delete_object.side_effect = delete_object
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.storage.delete_object.assert_called_once()


@pytest.mark.parametrize("elapsed, account_budget", [(0, 25), (2, 23), (5, 20), (5.1, None)])
def test_account_admission_preserves_retention_time_and_minimum_worker_budget(
    cron, monkeypatch, elapsed, account_budget,
):
    initial = iter([0.0])
    monkeypatch.setattr(main, "monotonic", lambda: next(initial, elapsed))
    cron.repository.list_expired_image_uploads.return_value = [_expired("expired")]
    response = _cleanup()
    if account_budget is None:
        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "account_deletion_cleanup_unavailable"
        cron.worker.assert_not_called()
    else:
        assert response.status_code == 200
        cron.worker.assert_called_once_with(
            max_jobs=3, max_objects=5, budget_seconds=account_budget,
        )
    cron.repository.mark_image_upload_deleted.assert_called_once_with("expired")


@pytest.mark.parametrize("verified", [True, False])
def test_retention_prefers_erasure_hook_without_requiring_worker_completion_proof(cron, verified):
    cron.storage.erase_account_object = Mock(return_value=verified)
    cron.repository.list_expired_image_uploads.return_value = [_expired("expired")]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.storage.erase_account_object.assert_called_once_with(object_key="uploads/expired")
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_called_once_with("expired")


@pytest.mark.parametrize("hook", [None, False])
def test_retention_uses_legacy_delete_when_erasure_hook_is_not_callable(cron, hook):
    cron.storage.erase_account_object = hook
    cron.repository.list_expired_image_uploads.return_value = [_expired("expired")]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.storage.delete_object.assert_called_once_with(object_key="uploads/expired")


def test_retention_does_not_call_erasure_hook_after_rejected_atomic_claim(cron):
    cron.storage.erase_account_object = Mock(return_value=True)
    cron.repository.list_expired_image_uploads.return_value = [_expired("tombstoned")]
    cron.repository.mark_image_upload_deleting.return_value = False
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 0}
    cron.storage.erase_account_object.assert_not_called()
    cron.storage.delete_object.assert_not_called()


@pytest.mark.parametrize("error_type", [StorageConfigurationError, OSError, ValueError])
def test_retention_erasure_hook_failure_is_sanitized_without_delete_fallback(cron, error_type):
    cron.storage.erase_account_object = Mock(side_effect=[
        error_type("private erasure failure fixture-cron-secret"), False,
    ])
    cron.repository.list_expired_image_uploads.return_value = [
        _expired("failed"), _expired("independent"),
    ]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    assert response.json()["detail"]["retryable"] is True
    assert "private erasure" not in response.text
    assert "fixture-cron-secret" not in response.text
    assert cron.storage.erase_account_object.call_count == 2
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_called_once_with("independent")
    cron.worker.assert_called_once()


@pytest.mark.parametrize("slow_stage", ["listing", "deleting"])
def test_retention_erasure_hook_requires_eighteen_seconds_before_and_after_claim(cron, slow_stage):
    cron.storage.erase_account_object = Mock(return_value=True)
    records = [_expired("expired")]
    cron.repository.list_expired_image_uploads.return_value = records

    def use_headroom(*_args, **_kwargs):
        cron.clock.now = 27.1
        return records if slow_stage == "listing" else True

    operation = (
        cron.repository.list_expired_image_uploads
        if slow_stage == "listing" else cron.repository.mark_image_upload_deleting
    )
    operation.side_effect = use_headroom
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    cron.storage.erase_account_object.assert_not_called()
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_not_called()
    if slow_stage == "listing":
        cron.repository.mark_image_upload_deleting.assert_not_called()


def test_retention_erasure_hook_is_admitted_with_eighteen_seconds_remaining(cron):
    records = [_expired("expired")]

    def listing(*_args, **_kwargs):
        cron.clock.now = 27.0
        return records

    def erase(**_kwargs):
        cron.clock.now += 16.0
        return True

    cron.repository.list_expired_image_uploads.side_effect = listing
    cron.storage.erase_account_object = Mock(side_effect=erase)
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.storage.erase_account_object.assert_called_once()
    cron.storage.delete_object.assert_not_called()


def test_full_account_budget_still_leaves_time_for_retention_erasure_hook(cron):
    def account_work(**kwargs):
        cron.clock.now += kwargs["budget_seconds"]
        return {"failed": 0}

    def erase(**_kwargs):
        cron.clock.now += 16.0
        return False

    cron.worker.side_effect = account_work
    cron.repository.list_expired_image_uploads.return_value = [_expired("expired")]
    cron.storage.erase_account_object = Mock(side_effect=erase)
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.worker.assert_called_once_with(max_jobs=3, max_objects=5, budget_seconds=25)
    cron.storage.erase_account_object.assert_called_once()
    cron.storage.delete_object.assert_not_called()


@pytest.fixture
def persisted_cron(cron, monkeypatch):
    repository = get_persistence_repository()
    get_coach_repository()
    get_analytics_repository()
    repository.prepare_account_deletion()
    monkeypatch.setattr(main, "get_persistence_repository", lambda: repository)
    cron.repository = repository
    return cron


@pytest.mark.parametrize("tombstone_stage", ["before_listing", "after_snapshot", "after_claim"])
def test_sqlite_tombstone_races_preserve_account_job_and_independent_retention(
    persisted_cron, monkeypatch, tombstone_stage,
):
    cron = persisted_cron
    repository = cron.repository
    owner = "11111111-1111-4111-8111-111111111111"
    independent = "22222222-2222-4222-8222-222222222222"
    tombstoned_upload = "a-tombstoned"
    independent_upload = "z-independent"
    for image_upload_id, owner_id in [(tombstoned_upload, owner), (independent_upload, independent)]:
        repository.save_image_upload(
            payload=ImageUploadRequest(
                local_asset_id=image_upload_id,
                file_name=f"{image_upload_id}.jpg",
                content_type="image/jpeg",
                byte_size=128,
            ),
            image_upload_id=image_upload_id,
            image_reference=f"local-image://uploads/{image_upload_id}",
            storage_provider="local",
            object_key=f"uploads/{image_upload_id}",
            cleanup_after="2020-01-01T00:00:00+00:00",
            owner_id=owner_id,
        )

    if tombstone_stage == "before_listing":
        repository.begin_account_deletion(owner)
    elif tombstone_stage == "after_snapshot":
        real_list = repository.list_expired_image_uploads

        def snapshot_then_tombstone(*args, **kwargs):
            records = real_list(*args, **kwargs)
            repository.begin_account_deletion(owner)
            return records

        monkeypatch.setattr(repository, "list_expired_image_uploads", snapshot_then_tombstone)

    def erase(*, object_key):
        if tombstone_stage == "after_claim" and object_key == f"uploads/{tombstoned_upload}":
            repository.begin_account_deletion(owner)
        return False

    cron.storage.erase_account_object = Mock(side_effect=erase)
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.worker.assert_called_once()
    cron.storage.delete_object.assert_not_called()
    erased = [call.kwargs["object_key"] for call in cron.storage.erase_account_object.call_args_list]
    expected = [f"uploads/{tombstoned_upload}"] if tombstone_stage == "after_claim" else []
    assert erased == expected + [f"uploads/{independent_upload}"]
    source = repository.get_image_upload(tombstoned_upload)
    assert source is not None
    assert source.object_key == f"uploads/{tombstoned_upload}"
    assert source.upload_status == ("deleting" if tombstone_stage == "after_claim" else "ready")
    assert repository.get_account_deletion_stage(owner) == 0
    assert repository.list_pending_account_deletions(3) == [owner]
    assert repository.get_image_upload(independent_upload).upload_status == "deleted"


@pytest.mark.parametrize("use_hook", [False, True])
@pytest.mark.parametrize("namespace", [None, "", "r2://other-account/fixture-bucket"])
@pytest.mark.parametrize("has_key", [False, True])
def test_remote_retention_rejects_missing_or_mismatched_namespace(
    cron, use_hook, namespace, has_key,
):
    cron.storage.provider = "r2"
    if use_hook:
        cron.storage.erase_account_object = Mock(return_value=True)
    cron.repository.list_expired_image_uploads.return_value = [_expired(
        "remote", object_key=has_key, storage_provider="r2", storage_namespace=namespace,
    )]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    assert response.json()["detail"]["retryable"] is True
    assert "fixture-account" not in response.text
    assert "other-account" not in response.text
    cron.repository.mark_image_upload_deleting.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_not_called()
    cron.storage.delete_object.assert_not_called()
    if use_hook:
        cron.storage.erase_account_object.assert_not_called()
    cron.worker.assert_called_once()


@pytest.mark.parametrize("use_hook", [False, True])
def test_remote_retention_accepts_exact_nonempty_namespace(cron, use_hook):
    cron.storage.provider = "r2"
    if use_hook:
        cron.storage.erase_account_object = Mock(return_value=False)
    cron.repository.list_expired_image_uploads.return_value = [_expired(
        "remote", storage_provider="r2", storage_namespace=STORAGE_NAMESPACE,
    )]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.storage.storage_namespace.assert_called_once_with()
    if use_hook:
        cron.storage.erase_account_object.assert_called_once_with(object_key="uploads/remote")
        cron.storage.delete_object.assert_not_called()
    else:
        cron.storage.delete_object.assert_called_once_with(object_key="uploads/remote")
    cron.repository.mark_image_upload_deleted.assert_called_once_with("remote")


@pytest.mark.parametrize("adapter_namespace", [None, "", "   ", 123])
def test_remote_retention_rejects_invalid_active_namespace(cron, adapter_namespace):
    cron.storage.provider = "r2"
    cron.storage.storage_namespace.return_value = adapter_namespace
    cron.storage.erase_account_object = Mock(return_value=True)
    cron.repository.list_expired_image_uploads.return_value = [_expired(
        "remote", storage_provider="r2", storage_namespace=adapter_namespace,
    )]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    cron.storage.erase_account_object.assert_not_called()
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleting.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_not_called()


@pytest.mark.parametrize("namespace_method", [None, False])
def test_remote_retention_requires_callable_namespace_provenance(cron, namespace_method):
    cron.storage.provider = "r2"
    cron.storage.storage_namespace = namespace_method
    cron.repository.list_expired_image_uploads.return_value = [_expired(
        "remote", storage_provider="r2", storage_namespace=STORAGE_NAMESPACE,
    )]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_not_called()


def test_local_retention_does_not_require_namespace_method(cron):
    del cron.storage.storage_namespace
    cron.repository.list_expired_image_uploads.return_value = [_expired("local")]
    response = _cleanup()
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "deleted_images": 1}
    cron.storage.delete_object.assert_called_once_with(object_key="uploads/local")


def test_namespace_resolution_failure_is_sanitized_and_other_retention_continues(cron):
    cron.storage.provider = "r2"
    cron.storage.storage_namespace.side_effect = [
        StorageConfigurationError("private namespace fixture-cron-secret"), STORAGE_NAMESPACE,
    ]
    cron.storage.erase_account_object = Mock(return_value=True)
    cron.repository.list_expired_image_uploads.return_value = [
        _expired(name, storage_provider="r2", storage_namespace=STORAGE_NAMESPACE)
        for name in ("failed", "independent")
    ]
    response = _cleanup()
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "storage_cleanup_unavailable"
    assert "private namespace" not in response.text
    assert "fixture-cron-secret" not in response.text
    cron.storage.erase_account_object.assert_called_once_with(object_key="uploads/independent")
    cron.storage.delete_object.assert_not_called()
    cron.repository.mark_image_upload_deleted.assert_called_once_with("independent")
    cron.worker.assert_called_once()
