import os

from fastapi.testclient import TestClient

from app import main as api_main
from app.main import app
from app.services.analysis_provider import (
    AnalysisProviderConfigurationError,
    AnalysisProviderDryRunError,
    StructuredOutputMalformedError,
)
from app.services import persistence as persistence_module
from app.services.persistence import PostgresPersistenceRepository, SQLitePersistenceRepository


client = TestClient(app)


def upload_demo_image(local_asset_id: str = "local-demo-image") -> str:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": local_asset_id,
            "file_name": "meal-preview.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )
    assert response.status_code == 200
    return response.json()["image_upload_id"]


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "cal-ai-api"}


def test_onboarding_returns_initial_target() -> None:
    response = client.post(
        "/v1/onboarding",
        json={
            "age": 29,
            "sex": "male",
            "height_cm": 176,
            "current_weight_kg": 82,
            "target_weight_kg": 75,
            "goal_type": "lose",
            "activity_level": "moderate",
            "training_frequency": "3-4",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["profile_id"]
    assert body["target"]["calories_kcal"] > 0
    assert body["target"]["protein_g"] > 0


def test_dashboard_today_mock_contract() -> None:
    response = client.get("/v1/dashboard/today")

    assert response.status_code == 200
    body = response.json()
    assert body["target"]["calories_kcal"] == 1850
    assert body["next_meal_guidance"]["menu_type_recommendations"]


def test_image_upload_returns_local_reference_for_analysis() -> None:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "local-demo-meal-preview",
            "file_name": "meal-preview.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "image_upload_id": "local-upload-local-demo-meal-preview",
        "image_reference": "local-image://local-upload-local-demo-meal-preview",
        "status": "ready",
    }


def test_image_upload_presign_returns_local_fallback_contract() -> None:
    response = client.post(
        "/image-uploads/presign",
        json={
            "local_asset_id": "local-demo-meal-preview",
            "file_name": "meal-preview.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["image_upload_id"].startswith("image-upload-")
    assert body["object_key"] == f"uploads/{body['image_upload_id']}/meal-preview.png"
    assert body["upload_url"] == f"local-upload://{body['object_key']}"
    assert body["headers"] == {"Content-Type": "image/png"}
    assert body["max_bytes"] == 8_000_000
    assert body["soft_limit_bytes"] == 8_000_000_000
    assert body["soft_limit_exceeded"] is False
    assert body["ttl_days"] == 30


def test_r2_image_upload_presign_does_not_expose_secret(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_PROVIDER", "r2")
    monkeypatch.setenv("R2_BUCKET_NAME", "cal-ai-meal-images")
    monkeypatch.setenv("R2_ACCOUNT_ID", "example-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("R2_ENDPOINT", "https://example-account.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_REGION", "auto")

    response = client.post(
        "/image-uploads/presign",
        json={
            "local_asset_id": "camera-roll-demo",
            "file_name": "meal photo.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["object_key"] == f"uploads/{body['image_upload_id']}/meal-photo.png"
    assert body["upload_url"].startswith("https://example-account.r2.cloudflarestorage.com/cal-ai-meal-images/uploads/")
    assert "X-Amz-Signature=" in body["upload_url"]
    assert "test-access-key" in body["upload_url"]
    assert "test-secret-key" not in body["upload_url"]
    assert body["headers"] == {"Content-Type": "image/png"}
    assert body["soft_limit_exceeded"] is False


def test_image_upload_presign_blocks_when_total_soft_limit_would_be_exceeded(monkeypatch) -> None:
    monkeypatch.setenv("UPLOAD_SOFT_LIMIT_BYTES", "500000")

    first_response = client.post(
        "/image-uploads/presign",
        json={
            "local_asset_id": "first-soft-limit-demo",
            "file_name": "first.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/image-uploads/presign",
        json={
            "local_asset_id": "second-soft-limit-demo",
            "file_name": "second.png",
            "content_type": "image/png",
            "byte_size": 100000,
        },
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == {
        "code": "upload_soft_limit_exceeded",
        "message": "이미지 저장소 사용량이 설정된 한도에 가까워졌어요. 오래된 이미지를 정리한 뒤 다시 시도해 주세요.",
        "retryable": False,
        "kind": "validation",
    }


def test_r2_image_upload_complete_persists_ready_metadata(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_PROVIDER", "r2")
    monkeypatch.setenv("R2_BUCKET_NAME", "cal-ai-meal-images")
    monkeypatch.setenv("R2_ACCOUNT_ID", "example-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("R2_ENDPOINT", "https://example-account.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_REGION", "auto")
    monkeypatch.setenv("IMAGE_TTL_DAYS", "7")

    presign_response = client.post(
        "/image-uploads/presign",
        json={
            "local_asset_id": "camera-roll-demo",
            "file_name": "meal.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )
    assert presign_response.status_code == 200
    presign_body = presign_response.json()
    pending_upload = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"]).get_image_upload(presign_body["image_upload_id"])
    assert pending_upload is not None
    assert pending_upload.upload_status == "pending"
    assert pending_upload.upload_expires_at == presign_body["expires_at"]

    complete_response = client.post(
        "/image-uploads/complete",
        json={
            "image_upload_id": presign_body["image_upload_id"],
            "object_key": presign_body["object_key"],
            "local_asset_id": "camera-roll-demo",
            "file_name": "meal.png",
            "content_type": "image/png",
            "byte_size": 420000,
            "etag": "fake-etag",
        },
    )

    assert complete_response.status_code == 200
    complete_body = complete_response.json()
    assert complete_body == {
        "image_upload_id": presign_body["image_upload_id"],
        "image_reference": f"r2://cal-ai-meal-images/{presign_body['object_key']}",
        "status": "ready",
    }

    repository = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"])
    upload = repository.get_image_upload(presign_body["image_upload_id"])
    assert upload is not None
    assert upload.storage_provider == "r2"
    assert upload.object_key == presign_body["object_key"]
    assert upload.upload_status == "ready"
    assert upload.cleanup_after is not None
    assert upload.soft_limit_exceeded is False


def test_r2_upload_complete_rejects_key_mismatch(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_PROVIDER", "r2")
    monkeypatch.setenv("R2_BUCKET_NAME", "cal-ai-meal-images")
    monkeypatch.setenv("R2_ACCOUNT_ID", "example-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("R2_ENDPOINT", "https://example-account.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_REGION", "auto")

    response = client.post(
        "/image-uploads/complete",
        json={
            "image_upload_id": "image-upload-123",
            "object_key": "uploads/image-upload-other/meal.png",
            "file_name": "meal.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "image_upload_key_mismatch"


def test_upload_complete_rejects_unpresigned_object_key(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_PROVIDER", "r2")
    monkeypatch.setenv("R2_BUCKET_NAME", "cal-ai-meal-images")
    monkeypatch.setenv("R2_ACCOUNT_ID", "example-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "test-access-key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "test-secret-key")
    monkeypatch.setenv("R2_ENDPOINT", "https://example-account.r2.cloudflarestorage.com")
    monkeypatch.setenv("R2_REGION", "auto")

    response = client.post(
        "/image-uploads/complete",
        json={
            "image_upload_id": "image-upload-never-presigned",
            "object_key": "uploads/image-upload-never-presigned/meal.png",
            "file_name": "meal.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "image_upload_not_found"


def test_analysis_job_rejects_pending_presigned_upload() -> None:
    presign_response = client.post(
        "/image-uploads/presign",
        json={
            "local_asset_id": "pending-analysis-demo",
            "file_name": "meal.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )
    assert presign_response.status_code == 200

    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": presign_response.json()["image_upload_id"], "meal_type": "lunch"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "image_upload_not_ready"


def test_ready_reports_database_and_local_storage() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"]["status"] == "ok"
    assert response.json()["storage"]["status"] == "ok"


def test_ready_reports_misconfigured_r2(monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_PROVIDER", "r2")
    monkeypatch.delenv("R2_SECRET_ACCESS_KEY", raising=False)

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["storage"]["status"] == "misconfigured"
    assert "R2_SECRET_ACCESS_KEY" in response.json()["storage"]["message"]


def test_recreating_deterministic_mock_job_clears_stale_persisted_response() -> None:
    first_upload_id = upload_demo_image("first-dinner-demo")
    first_create = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": first_upload_id, "meal_type": "dinner", "optional_note": "first"},
    )
    assert first_create.status_code == 200
    job_id = first_create.json()["analysis_job_id"]

    first_fetch = client.get(f"/v1/analysis-jobs/{job_id}")
    assert first_fetch.status_code == 200

    repository = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"])
    first_record = repository.get_analysis_job(job_id)
    assert first_record is not None
    assert first_record.response is not None

    second_upload_id = upload_demo_image("second-dinner-demo")
    second_create = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": second_upload_id, "meal_type": "dinner", "optional_note": "second"},
    )
    assert second_create.status_code == 200
    assert second_create.json()["analysis_job_id"] == job_id

    second_record = repository.get_analysis_job(job_id)
    assert second_record is not None
    assert second_record.image_upload_id == second_upload_id
    assert second_record.request.optional_note == "second"
    assert second_record.status == "queued"
    assert second_record.response is None


def test_scan_to_save_metadata_persists_across_repository_instances() -> None:
    upload_id = upload_demo_image("persisted-demo")
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": upload_id, "meal_type": "dinner", "optional_note": "소스는 조금만"},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["analysis_job_id"]

    job_response = client.get(f"/v1/analysis-jobs/{job_id}")
    assert job_response.status_code == 200

    clarify_response = client.post(
        f"/v1/analysis-jobs/{job_id}/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "large_bowl"}]},
    )
    assert clarify_response.status_code == 200

    save_response = client.post(
        "/v1/meal-logs",
        json={"analysis_job_id": job_id, "result_id": "analysis-dinner-001", "clarification_value": "large_bowl"},
    )
    assert save_response.status_code == 200

    restarted_repository = SQLitePersistenceRepository(os.environ["CAL_AI_API_DATA_PATH"])
    upload = restarted_repository.get_image_upload(upload_id)
    job = restarted_repository.get_analysis_job(job_id)
    clarifications = restarted_repository.list_clarifications(job_id)
    meal_logs = restarted_repository.list_meal_logs(job_id)

    assert upload is not None
    assert upload.file_name == "meal-preview.png"
    assert upload.image_reference == f"local-image://{upload_id}"
    assert job is not None
    assert job.image_upload_id == upload_id
    assert job.image_reference == upload.image_reference
    assert job.request.optional_note == "소스는 조금만"
    assert job.response is not None
    assert job.response.status == "completed"
    assert clarifications[0].request.answers[0].value == "large_bowl"
    assert clarifications[0].response.result.meal_type == "dinner"
    assert meal_logs[0].request.clarification_value == "large_bowl"
    assert meal_logs[0].response.confirmation == "기록했어요"


def test_persistence_repository_falls_back_to_sqlite_without_database_url(tmp_path) -> None:
    repository = persistence_module.get_persistence_repository(
        {
            "CAL_AI_API_DATA_PATH": str(tmp_path / "fallback.db"),
        }
    )

    assert isinstance(repository, SQLitePersistenceRepository)


def test_persistence_repository_uses_postgres_when_database_url_is_present(monkeypatch) -> None:
    created_urls: list[str] = []

    class FakePostgresRepository:
        def __init__(self, database_url: str) -> None:
            created_urls.append(database_url)

    monkeypatch.setattr(persistence_module, "PostgresPersistenceRepository", FakePostgresRepository)

    repository = persistence_module.get_persistence_repository(
        {
            "DATABASE_URL": "postgresql://example.invalid/neondb",
            "CAL_AI_API_DATA_PATH": "/tmp/ignored.db",
        }
    )

    assert isinstance(repository, FakePostgresRepository)
    assert created_urls == ["postgresql://example.invalid/neondb"]


def test_postgres_repository_wraps_missing_driver_as_persistence_error(monkeypatch) -> None:
    real_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "psycopg":
            raise ImportError("no module named psycopg")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)

    try:
        PostgresPersistenceRepository("postgresql://example.invalid/neondb")
    except persistence_module.PersistenceError as exc:
        assert str(exc) == "postgres_driver_unavailable"
    else:
        raise AssertionError("expected PersistenceError")


def test_image_upload_rejects_too_large_image() -> None:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "large-demo",
            "file_name": "large.png",
            "content_type": "image/png",
            "byte_size": 8_000_001,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "image_too_large",
        "message": "이미지 용량은 8MB 이하로 줄여 주세요.",
        "retryable": False,
        "kind": "validation",
    }


def test_image_upload_rejects_unsupported_image_type() -> None:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "heic-demo",
            "file_name": "meal.heic",
            "content_type": "image/heic",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "code": "unsupported_image_type",
        "message": "JPG, PNG, WebP 이미지만 업로드할 수 있어요.",
        "retryable": False,
        "kind": "validation",
    }


def test_image_upload_rejects_overlong_content_type_metadata() -> None:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "metadata-demo",
            "file_name": "meal.png",
            "content_type": f"image/{'x' * 80}",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_image_upload_failed_simulation_is_retryable() -> None:
    response = client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "temporary-failure",
            "file_name": "meal.png",
            "content_type": "image/png",
            "byte_size": 420000,
            "simulate_failure": True,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "image_upload_failed",
        "message": "이미지를 업로드하지 못했어요. 다시 시도해 주세요.",
        "retryable": True,
        "kind": "server",
    }


def test_analysis_job_requires_image_reference() -> None:
    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": "", "meal_type": "lunch"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "validation_error"


def test_analysis_job_serialized_contract_shape() -> None:
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": upload_demo_image(), "meal_type": "lunch", "optional_note": "밥은 거의 다 먹었어요"},
    )
    assert create_response.status_code == 200
    assert create_response.json() == {"analysis_job_id": "mock-lunch-001", "status": "queued"}

    response = client.get("/v1/analysis-jobs/mock-lunch-001")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_clarification"
    assert set(body["result"]) >= {
        "id",
        "meal_name",
        "meal_type",
        "stage_text",
        "summary",
        "detected_foods",
        "uncertainty_reasons",
        "primary_explanation",
        "clarification_question",
    }
    assert set(body["result"]["summary"]) == {
        "calories_kcal",
        "calorie_range",
        "protein_g",
        "carbs_g",
        "fat_g",
        "confidence",
        "confidence_label",
        "confidence_group",
    }
    assert set(body["result"]["summary"]["calorie_range"]) == {"low", "midpoint", "high"}
    assert body["result"]["clarification_question"]["question_key"] == "rice_amount"
    assert body["result"]["clarification_question"]["options"][0]["helper_text"]


def test_mock_jobs_preserve_requested_meal_type() -> None:
    create_response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": upload_demo_image("breakfast-demo"), "meal_type": "breakfast"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["analysis_job_id"] == "mock-breakfast-001"

    job_response = client.get("/v1/analysis-jobs/mock-breakfast-001")
    assert job_response.status_code == 200
    assert job_response.json()["result"]["meal_type"] == "breakfast"
    assert job_response.json()["result"]["id"] == "analysis-breakfast-001"

    clarify_response = client.post(
        "/v1/analysis-jobs/mock-dinner-001/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "large_bowl"}]},
    )
    assert clarify_response.status_code == 200
    assert clarify_response.json()["result"]["meal_type"] == "dinner"

    save_response = client.post(
        "/v1/meal-logs",
        json={
            "analysis_job_id": "mock-breakfast-001",
            "result_id": "analysis-breakfast-001",
            "clarification_value": "half_bowl",
        },
    )
    assert save_response.status_code == 200
    assert save_response.json()["dashboard"]["meals"][0]["meal_type"] == "breakfast"


def test_clarification_and_save_contracts() -> None:
    clarify_response = client.post(
        "/v1/analysis-jobs/mock-lunch-001/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "one_bowl"}]},
    )
    assert clarify_response.status_code == 200
    clarify_body = clarify_response.json()
    assert clarify_body["status"] == "completed"
    assert clarify_body["result"]["summary"]["calorie_range"] == {"low": 640, "midpoint": 675, "high": 710}
    assert clarify_body["range_narrowing"]["before"]["high"] - clarify_body["range_narrowing"]["before"]["low"] == 160
    assert clarify_body["range_narrowing"]["after"]["high"] - clarify_body["range_narrowing"]["after"]["low"] == 70

    save_response = client.post(
        "/v1/meal-logs",
        json={
            "analysis_job_id": "mock-lunch-001",
            "result_id": "analysis-lunch-001",
            "clarification_value": "one_bowl",
        },
    )
    assert save_response.status_code == 200
    save_body = save_response.json()
    assert save_body["confirmation"] == "기록했어요"
    assert save_body["remaining_calories_kcal"] == 505
    assert save_body["dashboard"]["meals"][0]["name"] == "닭고기 덮밥"


def test_clarification_answers_drive_distinct_mock_results() -> None:
    expected = {
        "half_bowl": ({"low": 560, "midpoint": 595, "high": 630}, 595),
        "one_bowl": ({"low": 640, "midpoint": 675, "high": 710}, 675),
        "large_bowl": ({"low": 720, "midpoint": 765, "high": 810}, 765),
    }

    for value, (expected_range, expected_calories) in expected.items():
        response = client.post(
            "/v1/analysis-jobs/mock-lunch-001/clarifications",
            json={"answers": [{"question_key": "rice_amount", "value": value}]},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["result"]["summary"]["calories_kcal"] == expected_calories
        assert body["result"]["summary"]["calorie_range"] == expected_range
        assert body["range_narrowing"]["after"] == expected_range

    unknown_response = client.post(
        "/v1/analysis-jobs/mock-lunch-001/clarifications",
        json={"answers": [{"question_key": "rice_amount", "value": "unknown"}]},
    )
    assert unknown_response.status_code == 200
    unknown_body = unknown_response.json()
    assert unknown_body["result"]["summary"]["calories_kcal"] == 700
    assert unknown_body["range_narrowing"] is None


def test_save_contract_uses_clarification_value() -> None:
    expected = {
        "half_bowl": 585,
        "one_bowl": 505,
        "large_bowl": 415,
        "unknown": 480,
    }

    for value, expected_remaining in expected.items():
        response = client.post(
            "/v1/meal-logs",
            json={"analysis_job_id": "mock-lunch-001", "result_id": "analysis-lunch-001", "clarification_value": value},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["remaining_calories_kcal"] == expected_remaining
        assert body["dashboard"]["meals"][0]["calories_kcal"] == 1850 - 670 - expected_remaining


def test_save_contract_requires_clarification_value() -> None:
    response = client.post(
        "/v1/meal-logs",
        json={"analysis_job_id": "mock-lunch-001", "result_id": "analysis-lunch-001"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == {
        "code": "validation_error",
        "message": "요청 형식이 올바르지 않아요. 입력값을 확인해 주세요.",
        "retryable": False,
        "kind": "validation",
    }


def test_malformed_provider_output_returns_safe_503(monkeypatch) -> None:
    class MalformedProvider:
        def create_job(self, payload):
            raise StructuredOutputMalformedError("openai_output_malformed")

    monkeypatch.setattr(api_main, "get_analysis_provider", lambda: MalformedProvider())

    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": upload_demo_image("malformed-demo"), "meal_type": "lunch"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "analysis_output_malformed",
        "message": "분석 결과 형식이 올바르지 않아 다시 시도해야 해요.",
        "retryable": True,
        "kind": "provider",
    }
    assert "openai_output_malformed" not in response.text


def test_provider_dry_run_returns_distinct_safe_503(monkeypatch) -> None:
    class DryRunProvider:
        def create_job(self, payload):
            raise AnalysisProviderDryRunError("openai_provider_dry_run_only")

    monkeypatch.setattr(api_main, "get_analysis_provider", lambda: DryRunProvider())

    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": upload_demo_image("dry-run-demo"), "meal_type": "lunch"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "analysis_provider_dry_run",
        "message": "실제 AI 분석 호출은 아직 비활성화되어 있어요. 로컬 mock 설정을 확인해 주세요.",
        "retryable": False,
        "kind": "provider",
    }
    assert "openai_provider_dry_run_only" not in response.text


def test_provider_configuration_returns_distinct_safe_503(monkeypatch) -> None:
    class MisconfiguredProvider:
        def create_job(self, payload):
            raise AnalysisProviderConfigurationError("ai_provider_api_key_missing")

    monkeypatch.setattr(api_main, "get_analysis_provider", lambda: MisconfiguredProvider())

    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": upload_demo_image("misconfigured-demo"), "meal_type": "lunch"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "code": "analysis_provider_unavailable",
        "message": "분석 제공자를 사용할 수 없어요. 로컬 mock 설정을 확인해 주세요.",
        "retryable": False,
        "kind": "provider",
    }
    assert "ai_provider_api_key_missing" not in response.text


def test_persistence_failure_returns_structured_api_error(monkeypatch) -> None:
    monkeypatch.setenv("CAL_AI_API_DATA_PATH", "/tmp")
    failing_client = TestClient(app, raise_server_exceptions=False)

    response = failing_client.post(
        "/v1/image-uploads",
        json={
            "local_asset_id": "persistence-failure-demo",
            "file_name": "meal.png",
            "content_type": "image/png",
            "byte_size": 420000,
        },
    )

    assert response.status_code == 503
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["detail"] == {
        "code": "persistence_unavailable",
        "message": "로컬 저장소를 사용할 수 없어요. API 설정을 확인한 뒤 다시 시도해 주세요.",
        "retryable": True,
        "kind": "server",
    }


def test_analysis_job_rejects_unknown_image_upload_id() -> None:
    response = client.post(
        "/v1/analysis-jobs",
        json={"image_upload_id": "local-upload-not-created", "meal_type": "lunch"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "code": "image_upload_not_found",
        "message": "업로드된 이미지를 찾을 수 없어요. 다시 업로드해 주세요.",
        "retryable": False,
        "kind": "not_found",
    }
