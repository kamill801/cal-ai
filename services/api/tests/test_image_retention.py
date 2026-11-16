from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.schemas import ImageUploadRequest
from app.services.persistence import get_persistence_repository
from app.services.image_retention import cleanup_expired_image_uploads
from app.services.storage import StorageConfigurationError


NOW = "2026-11-13T12:00:00+00:00"
NAMESPACE = "r2-v1:" + "a" * 64


@pytest.fixture
def persisted():
    repository = get_persistence_repository()
    for identifier, due in (("due", "2026-11-13T11:59:59+00:00"),
                            ("future", "2026-11-14T12:00:00+00:00")):
        repository.save_image_upload(
            payload=ImageUploadRequest(local_asset_id=identifier, file_name="fixture.png",
                                       content_type="image/png", byte_size=351),
            image_upload_id=identifier, image_reference="r2://fixture/" + identifier,
            storage_provider="r2", object_key="uploads/" + identifier,
            storage_namespace=NAMESPACE, cleanup_after=due,
        )
    storage = SimpleNamespace(provider="r2", storage_namespace=lambda: NAMESPACE,
                              erase_account_object=Mock(return_value=True), delete_object=Mock())
    return repository, storage


def run(repository, storage):
    return cleanup_expired_image_uploads(repository, storage_factory=lambda: storage,
                                        now_iso=NOW, deadline=45, clock=lambda: 0)


def test_persisted_retention_deletes_only_due_row_and_duplicate_run_is_noop(persisted):
    repository, storage = persisted
    future = repository.get_image_upload("future")
    assert run(repository, storage) == 1
    deleted = repository.get_image_upload("due")
    assert deleted.upload_status == "deleted" and deleted.image_reference == "deleted://due"
    assert repository.get_image_upload("future") == future
    storage.erase_account_object.assert_called_once_with(object_key="uploads/due")
    assert run(repository, storage) == 0
    assert storage.erase_account_object.call_count == 1
    storage.delete_object.assert_not_called()


def test_persisted_unverified_legacy_stays_discoverable_until_verified_retry(persisted):
    repository, storage = persisted
    storage.erase_account_object.side_effect = [False, True]
    with pytest.raises(StorageConfigurationError, match="erasure_guard_unverified"):
        run(repository, storage)
    pending = repository.get_image_upload("due")
    assert pending.upload_status == "deleting" and pending.object_key == "uploads/due"
    assert [row.image_upload_id for row in repository.list_expired_image_uploads(NOW)] == ["due"]
    assert run(repository, storage) == 1
    assert repository.get_image_upload("due").upload_status == "deleted"
    assert repository.get_image_upload("future").upload_status == "ready"


def test_persisted_remote_without_key_is_not_claimed_deleted(persisted):
    repository, storage = persisted
    with repository._connection() as conn:
        conn.execute("update image_uploads set object_key = null where image_upload_id = 'due'")
    with pytest.raises(StorageConfigurationError, match="remote_object_key_missing"):
        run(repository, storage)
    assert repository.get_image_upload("due").upload_status == "ready"
    storage.erase_account_object.assert_not_called()


def test_failed_batch_rotates_persistently_without_changing_retention_deadline(persisted):
    repository, storage = persisted
    with repository._connection() as conn:
        conn.execute("delete from image_uploads")
    for index in range(101):
        repository.save_image_upload(
            payload=ImageUploadRequest(local_asset_id=str(index), file_name="fixture.png",
                                       content_type="image/png", byte_size=351),
            image_upload_id=f"due-{index:03}", image_reference=f"r2://fixture/{index}",
            storage_provider="r2", object_key=f"uploads/due-{index:03}",
            storage_namespace=NAMESPACE, cleanup_after="2026-11-13T11:59:59+00:00",
        )
    storage.erase_account_object.side_effect = lambda *, object_key: object_key.endswith("100")
    with pytest.raises(StorageConfigurationError, match="erasure_guard_unverified"):
        run(repository, storage)
    assert storage.erase_account_object.call_count == 100
    # Reconstruct the repository to prove rotation survives a serverless restart.
    restarted = type(repository)(repository.db_path)
    with pytest.raises(StorageConfigurationError, match="erasure_guard_unverified"):
        run(restarted, storage)
    assert storage.erase_account_object.call_args_list[100].kwargs["object_key"] == "uploads/due-100"
    assert restarted.get_image_upload("due-100").upload_status == "deleted"
    assert restarted.get_image_upload("due-000").upload_status == "deleting"
    assert restarted.get_image_upload("due-000").cleanup_after == "2026-11-13T11:59:59+00:00"


def test_slow_failure_rotates_before_budget_exhaustion(persisted):
    repository, storage = persisted
    with repository._connection() as conn:
        conn.execute("update image_uploads set cleanup_after = ?", (NOW,))
    clock = SimpleNamespace(now=0)

    def slow_failure(*, object_key):
        clock.now = 40
        return False

    storage.erase_account_object.side_effect = slow_failure
    with pytest.raises(StorageConfigurationError, match="erasure_guard_unverified"):
        cleanup_expired_image_uploads(repository, storage_factory=lambda: storage,
                                      now_iso=NOW, deadline=45, clock=lambda: clock.now)
    assert storage.erase_account_object.call_count == 1
    assert repository.list_expired_image_uploads(NOW)[0].image_upload_id == "future"


def test_invalid_namespace_attempt_rotates_without_touching_storage(persisted):
    repository, storage = persisted
    with repository._connection() as conn:
        conn.execute("update image_uploads set cleanup_after = ?", (NOW,))
        conn.execute("update image_uploads set storage_namespace = 'wrong' where image_upload_id = 'due'")
    with pytest.raises(StorageConfigurationError, match="storage_namespace_mismatch"):
        run(repository, storage)
    assert repository.get_image_upload("due").upload_status == "ready"
    assert repository.get_image_upload("future").upload_status == "deleted"
    storage.erase_account_object.assert_called_once_with(object_key="uploads/future")
    with repository._connection() as conn:
        row = conn.execute("select retention_attempted_at from image_uploads where image_upload_id = 'due'").fetchone()
    assert row["retention_attempted_at"] is not None


@pytest.mark.parametrize("cleanup_after", [None, "2026-11-13T11:59:59+00:00"])
def test_abandoned_pending_upload_is_counted_until_verified_erasure(persisted, cleanup_after):
    repository, storage = persisted
    repository.save_image_upload(
        payload=ImageUploadRequest(local_asset_id="abandoned", file_name="fixture.png",
                                   content_type="image/png", byte_size=70),
        image_upload_id="abandoned", image_reference="r2://fixture/abandoned",
        storage_provider="r2", object_key="uploads/abandoned", storage_namespace=NAMESPACE,
        upload_status="pending", upload_expires_at="2020-01-01T00:00:00+00:00",
        cleanup_after=cleanup_after,
    )
    assert repository.sum_image_upload_bytes() == 772
    assert "abandoned" in {row.image_upload_id for row in repository.list_expired_image_uploads(NOW)}
    assert repository.record_image_retention_attempt("abandoned") is True
    storage.erase_account_object.side_effect = lambda *, object_key: object_key != "uploads/abandoned"
    with pytest.raises(StorageConfigurationError, match="erasure_guard_unverified"):
        run(repository, storage)
    assert repository.get_image_upload("abandoned").upload_status == "deleting"
    assert repository.sum_image_upload_bytes() == 421
    storage.erase_account_object.side_effect = None
    assert run(repository, storage) == 1
    assert repository.get_image_upload("abandoned").upload_status == "deleted"
    assert repository.sum_image_upload_bytes() == 351


@pytest.mark.parametrize("expiry,cleanup_after", [
    ("2026-11-14T12:00:00+00:00", "2026-11-13T11:59:59+00:00"),
    ("2020-01-01T00:00:00+00:00", "2026-11-14T12:00:00+00:00"),
    (None, None),
])
def test_pending_upload_without_both_expired_deadlines_is_not_selected(persisted, expiry, cleanup_after):
    repository, _ = persisted
    repository.save_image_upload(
        payload=ImageUploadRequest(local_asset_id="pending", file_name="fixture.png",
                                   content_type="image/png", byte_size=70),
        image_upload_id="pending", image_reference="r2://fixture/pending",
        storage_provider="r2", object_key="uploads/pending", storage_namespace=NAMESPACE,
        upload_status="pending", upload_expires_at=expiry, cleanup_after=cleanup_after,
    )
    assert "pending" not in {row.image_upload_id for row in repository.list_expired_image_uploads(NOW)}
