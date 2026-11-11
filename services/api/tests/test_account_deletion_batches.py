from contextlib import contextmanager

import pytest

from app.services import account_deletion as deletion
from app.services.analytics_repository import get_analytics_repository
from app.services.coach_repository import get_coach_repository
from app.services.persistence import PersistenceError, get_persistence_repository
from app.schemas import ImageUploadRequest
from test_account_deletion import OWNER, FOREIGN, admin, client, delete, job, profile, rows, upload


def prepared():
    repo = get_persistence_repository()
    get_coach_repository()
    get_analytics_repository()
    repo.prepare_account_deletion()
    return repo


def test_acceptance_requires_explicit_guard_migration(client):
    repo = get_persistence_repository()
    with pytest.raises(PersistenceError, match="account_deletion_schema_unavailable"):
        repo.begin_account_deletion(OWNER)
    assert repo.get_account_deletion_stage(OWNER) is None


def test_acceptance_is_small_and_does_not_reinstall_guards(client, monkeypatch):
    own = profile(client)
    upload("source", object_key="fixture/source")
    repo = prepared()
    monkeypatch.setattr(repo, "_install_account_write_guards", lambda *a: pytest.fail("runtime DDL"))
    monkeypatch.setattr(repo, "_save_account_deletion_objects", lambda *a: pytest.fail("acceptance inventory"))
    assert repo.begin_account_deletion(OWNER) == 0
    assert rows("account_deletion_objects") == []
    assert repo.get_image_upload("source") is not None
    assert get_coach_repository().get_profile(own) is not None
    assert repo.begin_account_deletion(OWNER) == 0


def test_inflight_source_delete_cannot_discard_uninventoried_rows(client):
    own = profile(client)
    upload("source", object_key="fixture/source")
    repo = prepared()
    repo.begin_account_deletion(OWNER)
    for table, column, key in [("image_uploads", "image_upload_id", "source"),
                               ("coach_profiles", "profile_id", own)]:
        with pytest.raises(PersistenceError):
            with repo._connection() as conn:
                conn.execute(f"delete from {table} where {column} = ?", (key,))
    assert repo.get_image_upload("source") is not None


@pytest.mark.parametrize("operation", ["stage", "identity", "object", "batch"])
def test_every_worker_mutation_requires_current_lease(client, operation):
    repo = prepared()
    repo.begin_account_deletion(OWNER)
    assert repo.claim_account_deletion(OWNER, "old")
    with repo._connection() as conn:
        conn.execute("update account_deletion_work set lease_token = 'new'")
    calls = {
        "stage": lambda: repo.advance_account_deletion(OWNER, 1, lease_token="old"),
        "identity": lambda: repo.mark_account_identity_deleted(OWNER, lease_token="old"),
        "object": lambda: repo.mark_account_deletion_object_swept(OWNER, "source", lease_token="old"),
        "batch": lambda: repo.process_account_deletion_batch(OWNER, "old", batch_size=2),
    }
    with pytest.raises(PersistenceError, match="account_deletion_lease_lost"):
        calls[operation]()
    assert repo.get_account_deletion_stage(OWNER) == 0
    assert not repo.account_identity_deleted(OWNER)


def test_inventory_failure_rolls_back_source_deletion_not_acceptance(client, monkeypatch):
    upload("source", object_key="fixture/source")
    repo = prepared()
    repo.begin_account_deletion(OWNER)
    assert repo.claim_account_deletion(OWNER, "worker")
    original = repo._save_account_deletion_objects
    monkeypatch.setattr(repo, "_save_account_deletion_objects", lambda *a: (_ for _ in ()).throw(PersistenceError("fixture")))
    with pytest.raises(PersistenceError, match="fixture"):
        for _ in range(10):
            repo.process_account_deletion_batch(OWNER, "worker", batch_size=2)
    assert repo.get_account_deletion_stage(OWNER) == 0
    assert repo.get_image_upload("source") is not None
    assert rows("account_deletion_objects") == []
    monkeypatch.setattr(repo, "_save_account_deletion_objects", original)


def test_small_batches_capture_keys_before_removal_and_prune_temporary_refs(client):
    own = profile(client)
    foreign = profile(client, FOREIGN)
    for index in range(9):
        upload(str(index), object_key=f"fixture/{index}")
        job(f"job-{index}", str(index), profile_id=own)
    upload("foreign", FOREIGN, object_key="fixture/foreign")
    job("foreign-job", "foreign", FOREIGN, foreign)
    repo = prepared()
    repo.begin_account_deletion(OWNER)
    assert repo.claim_account_deletion(OWNER, "worker")
    done = False
    for _ in range(100):
        before = {r["image_upload_id"] for r in rows("image_uploads")}
        done = repo.process_account_deletion_batch(OWNER, "worker", batch_size=2)
        after = {r["image_upload_id"] for r in rows("image_uploads")}
        assert len(before - after) <= 2
        manifest = {r["image_upload_id"] for r in rows("account_deletion_objects")}
        assert before - after <= manifest
        if done:
            break
    assert done
    assert repo.get_account_deletion_stage(OWNER) == 1
    assert rows("account_deletion_refs") == []
    assert {r["image_upload_id"] for r in rows("image_uploads")} == {"foreign"}
    assert {r["analysis_job_id"] for r in rows("analysis_jobs")} == {"foreign-job"}
    assert get_coach_repository().get_profile(foreign) is not None


def test_fence_is_revalidated_before_batch_commit(client, monkeypatch):
    upload("source", object_key="fixture/source")
    repo = prepared()
    repo.begin_account_deletion(OWNER)
    assert repo.claim_account_deletion(OWNER, "worker")
    original = repo._connection

    @contextmanager
    def connection():
        with original() as conn:
            class Connection:
                def execute(self, statement, parameters=()):
                    result = conn.execute(statement, parameters)
                    if statement.startswith("update account_deletion_work set phase = ?, cursor = ?") and parameters[:2] == ("uploads", "source"):
                        conn.execute("update account_deletion_work set lease_token = 'replacement'")
                    return result
            yield Connection()

    monkeypatch.setattr(repo, "_connection", connection)
    with pytest.raises(PersistenceError, match="account_deletion_lease_lost"):
        for _ in range(10):
            repo.process_account_deletion_batch(OWNER, "worker", batch_size=2)
    assert repo.get_image_upload("source") is not None
    assert rows("account_deletion_objects") == []
    assert repo.account_deletion_lease_current(OWNER, "worker")


def test_initial_cleanup_precedes_old_reconciliation_without_starving_it(client):
    repo = prepared()
    for owner in (OWNER, FOREIGN):
        repo.begin_account_deletion(owner)
    with repo._connection() as conn:
        conn.execute("update account_deletions set stage = 2 where owner_id = ?", (OWNER,))
        conn.execute("update account_deletion_work set identity_deleted = 1, phase = 'done' where owner_id = ?", (OWNER,))
    assert repo.list_pending_account_deletions(2)[0] == FOREIGN
    assert OWNER in repo.list_pending_account_deletions(2)


def test_aged_reconciliation_cannot_starve_behind_new_initial_jobs(client):
    repo = prepared()
    for owner in (OWNER, FOREIGN):
        repo.begin_account_deletion(owner)
    with repo._connection() as conn:
        conn.execute("update account_deletions set stage = 2, updated_at = '2000-01-01T00:00:00+00:00' where owner_id = ?", (OWNER,))
        conn.execute("update account_deletion_work set identity_deleted = 1, phase = 'done' where owner_id = ?", (OWNER,))
    assert repo.list_pending_account_deletions(1) == [OWNER]


def test_retention_claim_after_acceptance_skips_without_losing_key(client):
    upload("source", object_key="fixture/source")
    repo = prepared()
    repo.begin_account_deletion(OWNER)
    assert repo.mark_image_upload_deleting("source") is False
    assert repo.mark_image_upload_deleted("source") is False
    assert repo.get_image_upload("source").object_key == "fixture/source"


@pytest.mark.parametrize("verified", [False, True])
def test_remote_terminal_checkpoint_requires_verified_erase_hook(client, monkeypatch, verified):
    from types import SimpleNamespace

    upload("remote", object_key="fixture/remote")
    repo = get_persistence_repository()
    with repo._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', storage_namespace = 'fixture-namespace'")
    calls = []

    def erase(**kwargs):
        calls.append(kwargs["object_key"])
        return verified

    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: SimpleNamespace(
        provider="r2", storage_namespace=lambda: "fixture-namespace", erase_account_object=erase,
    ))
    assert delete(client).status_code == 202
    result = deletion.run_account_deletion_jobs()
    assert calls == ["fixture/remote"]
    assert result["deleted" if verified else "pending"] == 1
    assert repo.get_account_deletion_stage(OWNER) == (3 if verified else 2)
    assert rows("account_deletion_objects")[0]["erase_verified"] == int(verified)
    assert repo.list_account_deletion_objects(OWNER, 5) == ([] if verified else rows("account_deletion_objects"))


def test_unknown_remote_key_is_not_overridden_by_other_verified_objects(client, monkeypatch):
    from types import SimpleNamespace

    upload("known", object_key="fixture/known")
    upload("lost")
    repo = get_persistence_repository()
    with repo._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', storage_namespace = 'fixture-namespace'")
    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: SimpleNamespace(
        provider="r2", storage_namespace=lambda: "fixture-namespace", erase_account_object=lambda **kw: True,
    ))
    assert delete(client).status_code == 202
    assert deletion.run_account_deletion_jobs()["pending"] == 1
    assert repo.account_storage_uncertain(OWNER)
    assert repo.get_account_deletion_stage(OWNER) == 2


@pytest.mark.parametrize("namespace", [None, "original-bucket"])
def test_remote_namespace_missing_or_changed_never_calls_storage(client, monkeypatch, namespace):
    from types import SimpleNamespace

    upload("remote", object_key="fixture/remote")
    repo = get_persistence_repository()
    with repo._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2', storage_namespace = ?", (namespace,))
    monkeypatch.setattr(deletion, "get_storage_adapter", lambda: SimpleNamespace(
        provider="r2", storage_namespace=lambda: "different-bucket",
        erase_account_object=lambda **kw: pytest.fail("wrong namespace erasure"),
        delete_object=lambda **kw: pytest.fail("wrong namespace deletion"),
    ))
    assert delete(client).status_code == 202
    assert deletion.run_account_deletion_jobs()["failed"] == 1
    assert repo.get_account_deletion_stage(OWNER) == 2
    manifest = rows("account_deletion_objects")[0]
    assert manifest["storage_namespace"] == namespace
    assert manifest["erase_verified"] == manifest["sweep_count"] == 0


@pytest.mark.parametrize("namespace", [None, "original-bucket"])
def test_upload_namespace_cannot_be_rebound_even_when_original_unknown(client, namespace):
    repo = get_persistence_repository()
    payload = ImageUploadRequest(local_asset_id="fixture", file_name="image.jpg", content_type="image/jpeg", byte_size=1)
    arguments = dict(payload=payload, image_upload_id="remote", image_reference="r2://fixture/remote",
                     storage_provider="r2", object_key="fixture/remote", owner_id=OWNER)
    repo.save_image_upload(**arguments, storage_namespace=namespace)
    assert repo.save_image_upload(**arguments).storage_namespace == namespace
    with pytest.raises(PersistenceError, match="image_upload_storage_namespace_immutable"):
        repo.save_image_upload(**arguments, storage_namespace="different-bucket")
    assert repo.get_image_upload("remote").storage_namespace == namespace


def test_conflicting_manifest_preserves_source_metadata(client):
    upload("source", object_key="fixture/source")
    repo = prepared()
    repo.begin_account_deletion(OWNER)
    assert repo.claim_account_deletion(OWNER, "worker")
    with repo._connection() as conn:
        conn.execute("insert into account_deletion_objects "
                     "(owner_id, image_upload_id, storage_provider, object_key) values (?, 'source', 'local', 'wrong-key')", (OWNER,))
    with pytest.raises(PersistenceError, match="account_deletion_manifest_conflict"):
        for _ in range(10):
            repo.process_account_deletion_batch(OWNER, "worker", batch_size=2)
    assert repo.get_image_upload("source").object_key == "fixture/source"


def test_ownerless_remote_source_delete_requires_inventoried_worker(client):
    upload("legacy", None, object_key="fixture/legacy")
    repo = prepared()
    with repo._connection() as conn:
        conn.execute("update image_uploads set storage_provider = 'r2'")
    with pytest.raises(PersistenceError):
        with repo._connection() as conn:
            conn.execute("delete from image_uploads where image_upload_id = 'legacy'")
    assert repo.get_image_upload("legacy") is not None
