import hashlib
from dataclasses import replace
from email.message import Message
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit

import pytest

from app.services import storage
from app.services import image_uploads
from app.services.image_uploads import create_image_object_key
from app.schemas import ImageUploadCompleteRequest, ImageUploadPresignRequest
from app.services.persistence import get_persistence_repository


KEY = "uploads/image-upload-11111111-1111-4111-8111-111111111111/sealed-v1/image.jpg"
LEGACY = "uploads/image-upload-11111111-1111-4111-8111-111111111111/meal.jpg"


@pytest.fixture
def adapter():
    return storage.R2StorageAdapter(
        "fixture-bucket", "fixture-account", "disposable-access-fixture", "disposable-secret-fixture",
        "https://fixture-account.r2.cloudflarestorage.com", "auto",
    )


def test_write_once_key_requires_signed_conditional_header(adapter):
    result = adapter.presign_put(object_key=KEY, content_type="image/jpeg", expires_seconds=60)
    assert result.headers == {"Content-Type": "image/jpeg", "If-None-Match": "*"}
    assert parse_qs(urlsplit(result.upload_url).query)["X-Amz-SignedHeaders"] == [
        "content-type;host;if-none-match"
    ]
    assert "If-None-Match" not in adapter.presign_put(
        object_key=LEGACY, content_type="image/jpeg", expires_seconds=60,
    ).headers


def test_sealed_keys_do_not_include_user_file_names():
    assert create_image_object_key(
        image_upload_id="image-upload-11111111-1111-4111-8111-111111111111",
        file_name="private-user-name.jpg", write_once=True, content_type="image/jpeg",
    ) == KEY


def test_r2_credentials_are_not_in_repr(adapter):
    assert "disposable-access-fixture" not in repr(adapter)
    assert "disposable-secret-fixture" not in repr(adapter)


def test_namespace_identifies_original_storage_not_rotating_credentials(adapter):
    namespace = adapter.storage_namespace()
    assert namespace.startswith("r2-v1:")
    assert replace(adapter, secret_access_key="rotated-fixture").storage_namespace() == namespace
    assert replace(adapter, bucket_name="different-bucket").storage_namespace() != namespace
    assert replace(adapter, account_id="different-account").storage_namespace() != namespace
    assert replace(adapter, endpoint="https://other.example.com").storage_namespace() != namespace
    assert "fixture-account" not in namespace


def test_guard_signs_empty_payload_and_content_type_not_a_bearer_url(adapter):
    request = adapter._erasure_guard_request(object_key=KEY)
    assert urlsplit(request.full_url).query == ""
    assert request.get_header("X-amz-content-sha256") == hashlib.sha256(b"").hexdigest()
    assert "content-type;host;x-amz-content-sha256;x-amz-date" in request.get_header("Authorization")
    assert "disposable-secret-fixture" not in request.get_header("Authorization")


def test_presign_records_original_namespace_and_default_flag_preserves_legacy(adapter, monkeypatch):
    monkeypatch.setattr(image_uploads, "get_storage_adapter", lambda: adapter)
    monkeypatch.delenv("R2_WRITE_ONCE_UPLOADS_ENABLED", raising=False)
    payload = ImageUploadPresignRequest(
        local_asset_id="fixture-asset", file_name="private-user-name.jpg", content_type="image/jpeg", byte_size=1024,
    )
    legacy = image_uploads.create_presigned_image_upload(payload)
    assert not storage.is_write_once_object_key(legacy.object_key)
    monkeypatch.setenv("R2_WRITE_ONCE_UPLOADS_ENABLED", "true")
    sealed = image_uploads.create_presigned_image_upload(payload)
    assert storage.is_write_once_object_key(sealed.object_key)
    assert sealed.headers["If-None-Match"] == "*"
    record = get_persistence_repository().get_image_upload(sealed.image_upload_id)
    assert record.storage_namespace == adapter.storage_namespace()
    assert sealed.upload_url not in repr(record)


def test_complete_and_analysis_reject_changed_namespace_before_network(adapter, monkeypatch):
    monkeypatch.setattr(image_uploads, "get_storage_adapter", lambda: adapter)
    payload = ImageUploadPresignRequest(
        local_asset_id="fixture-asset", file_name="fixture.jpg", content_type="image/jpeg", byte_size=1024,
    )
    presign = image_uploads.create_presigned_image_upload(payload)
    changed = replace(adapter, endpoint="https://changed.example.com")
    monkeypatch.setattr(image_uploads, "get_storage_adapter", lambda: changed)
    monkeypatch.setattr(storage, "urlopen", lambda *a, **k: pytest.fail("wrong namespace network access"))
    complete = ImageUploadCompleteRequest(**payload.model_dump(), image_upload_id=presign.image_upload_id,
                                          object_key=presign.object_key)
    with pytest.raises(image_uploads.ImageUploadError, match="image_upload_storage_mismatch"):
        image_uploads.complete_presigned_image_upload(complete)
    monkeypatch.setattr(image_uploads, "get_storage_adapter", lambda: adapter)
    monkeypatch.setattr(storage.R2StorageAdapter, "stat_object", lambda *a, **k: storage.StorageObjectMetadata(1024, "image/jpeg"))
    image_uploads.complete_presigned_image_upload(complete)
    monkeypatch.setattr(image_uploads, "get_storage_adapter", lambda: changed)
    with pytest.raises(image_uploads.ImageUploadError, match="image_upload_storage_mismatch"):
        image_uploads.resolve_analysis_image_reference(presign.image_upload_id)


def test_erasure_guard_replaces_content_and_requires_readback(adapter, monkeypatch):
    calls = []

    class Response:
        headers = Message()
        headers["Content-Length"] = "0"
        headers["Content-Type"] = storage.ERASURE_GUARD_CONTENT_TYPE

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    def request(req, **kwargs):
        calls.append(req)
        assert kwargs["timeout"] <= 8
        return Response()

    monkeypatch.setattr(storage, "urlopen", request)
    assert adapter.erase_account_object(object_key=KEY) is True
    assert [req.method for req in calls] == ["PUT", "HEAD"]
    assert calls[0].data == b""
    assert calls[0].get_header("Content-type") == storage.ERASURE_GUARD_CONTENT_TYPE
    assert calls[0].get_header("If-none-match") is None
    assert all(req.method != "DELETE" for req in calls)


def test_legacy_delete_does_not_claim_drain_barrier(adapter, monkeypatch):
    calls = []
    monkeypatch.setattr(storage.R2StorageAdapter, "delete_object", lambda self, **kw: calls.append(kw))
    assert adapter.erase_account_object(object_key=LEGACY) is False
    assert calls == [{"object_key": LEGACY}]


def test_profile_and_retention_delete_preserve_sealed_guard(adapter, monkeypatch):
    calls = []
    monkeypatch.setattr(storage.R2StorageAdapter, "erase_account_object", lambda self, **kw: calls.append(kw))
    adapter.delete_object(object_key=KEY)
    assert calls == [{"object_key": KEY}]


@pytest.mark.parametrize("readback", [None, storage.StorageObjectMetadata(9, "image/jpeg")])
def test_guard_missing_or_replaced_readback_fails_closed(adapter, monkeypatch, readback):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(storage, "urlopen", lambda *a, **kw: Response())
    monkeypatch.setattr(storage.R2StorageAdapter, "stat_object", lambda *a, **kw: readback)
    with pytest.raises(storage.StorageConfigurationError, match="erasure_guard_unverified"):
        adapter.erase_account_object(object_key=KEY)


def test_guard_http_failure_does_not_expose_signed_url_or_secret(adapter, monkeypatch):
    def fail(req, **kwargs):
        raise HTTPError(req.full_url, 503, "upstream fixture", {}, None)

    monkeypatch.setattr(storage, "urlopen", fail)
    with pytest.raises(storage.StorageConfigurationError) as caught:
        adapter.erase_account_object(object_key=KEY)
    assert "X-Amz" not in str(caught.value)
    assert "disposable" not in str(caught.value)
    assert caught.value.__suppress_context__
