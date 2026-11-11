import json
from html.parser import HTMLParser
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


PUBLIC_PAGES = [
    ("/privacy", "개인정보처리방침"),
    ("/terms", "서비스 이용약관"),
    ("/support", "문의"),
    ("/account-deletion", "계정 삭제"),
]


class PublicDocument(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


@pytest.fixture(autouse=True)
def default_public_metadata(monkeypatch):
    monkeypatch.delenv("PUBLIC_POLICY_EFFECTIVE_DATE", raising=False)
    monkeypatch.delenv("PUBLIC_POLICY_VERSION", raising=False)


@pytest.mark.parametrize("path,title", PUBLIC_PAGES)
def test_public_notices_are_real_html_without_auth(path, title, monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_PROVIDER", "supabase")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    response = TestClient(app).get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert response.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert "default-src 'none'" in response.headers["content-security-policy"]
    assert "form-action 'none'" in response.headers["content-security-policy"]
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert title in response.text
    assert "Trust First Nutrition" in response.text
    assert "아르케" in response.text
    assert "areche.ai.kr@gmail.com" in response.text
    assert "최종 법률 검토나 준법 확인을 마쳤다는 뜻이 아닙니다" in response.text


@pytest.mark.parametrize("path,_title", PUBLIC_PAGES)
def test_public_documents_have_accessible_structure_and_no_active_content(path, _title):
    document = PublicDocument(TestClient(app).get(path).text)
    tags = [tag for tag, _ in document.elements]
    assert ("html", {"lang": "ko"}) in document.elements
    assert tags.count("main") == tags.count("h1") == 1
    assert not {"script", "iframe", "form", "input", "object"}.intersection(tags)
    ids = [attrs["id"] for _, attrs in document.elements if "id" in attrs]
    assert len(ids) == len(set(ids))
    for tag, attrs in document.elements:
        if tag == "nav":
            assert attrs.get("aria-label")
        if tag == "a":
            href = attrs["href"]
            assert href.startswith(("/", "#", "mailto:"))
            assert not href.startswith("//")
            if href.startswith("#"):
                assert href[1:] in ids


@pytest.mark.parametrize("path,_title", PUBLIC_PAGES)
def test_public_pages_do_not_expose_credentials_or_reflect_request(path, _title, monkeypatch):
    secret_names = (
        "DATABASE_URL", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "AI_PROVIDER_API_KEY",
        "SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY", "CRON_SECRET",
        "ADMIN_LOGIN_USERNAME", "ADMIN_LOGIN_EMAIL", "GROBLE_WEBHOOK_SECRET",
        "PLAY_REVIEWER_EMAIL", "PLAY_REVIEWER_PASSWORD", "SENTRY_DSN", "POSTHOG_KEY",
    )
    secrets = [f"sentinel-private-{index}" for index in range(len(secret_names))]
    for name, value in zip(secret_names, secrets):
        monkeypatch.setenv(name, value)
    response = TestClient(app).get(
        path,
        params={"email": "request-private-email", "password": "request-private-password"},
        headers={"Authorization": "Bearer request-private-token"},
    )
    assert response.status_code == 200
    public_output = response.text + str(response.headers)
    for secret in (*secrets, "request-private-email", "request-private-password", "request-private-token"):
        assert secret not in public_output


@pytest.mark.parametrize("path,_title", PUBLIC_PAGES)
def test_get_pages_never_authenticate_or_operate_on_accounts(path, _title, monkeypatch):
    def unexpected_operation(*args, **kwargs):
        pytest.fail("Public documentation must not authenticate, persist, or delete")

    for target in (
        "app.main.authenticate_bearer_token", "app.main.account_deletion_gate",
        "app.main.get_persistence_repository", "app.main.get_analytics_repository",
        "app.main.get_storage_adapter", "app.account_routes.delete_account",
        "app.account_routes.run_account_deletion_jobs",
    ):
        monkeypatch.setattr(target, unexpected_operation)
    assert TestClient(app).get(path).status_code == 200


@pytest.mark.parametrize("path,_title", PUBLIC_PAGES)
def test_policy_effective_date_and_version_are_public_and_configurable(path, _title, monkeypatch):
    client = TestClient(app)
    default = client.get(path).text
    assert '<time datetime="2026-11-10">2026-11-10</time>' in default
    assert "정책 문서 버전: 2026-11-10.1" in default
    monkeypatch.setenv("PUBLIC_POLICY_EFFECTIVE_DATE", "2026-12-01")
    monkeypatch.setenv("PUBLIC_POLICY_VERSION", "2026-12-01.2")
    configured = client.get(path).text
    assert '<time datetime="2026-12-01">2026-12-01</time>' in configured
    assert "정책 문서 버전: 2026-12-01.2" in configured


@pytest.mark.parametrize("setting,value", [
    ("PUBLIC_POLICY_EFFECTIVE_DATE", ""),
    ("PUBLIC_POLICY_EFFECTIVE_DATE", "2026-02-30"),
    ("PUBLIC_POLICY_EFFECTIVE_DATE", "20261110"),
    ("PUBLIC_POLICY_EFFECTIVE_DATE", '\"><script>alert(1)</script>'),
    ("PUBLIC_POLICY_EFFECTIVE_DATE", "sentinel-private-key"),
    ("PUBLIC_POLICY_VERSION", ""),
    ("PUBLIC_POLICY_VERSION", "x" * 1000),
    ("PUBLIC_POLICY_VERSION", '\"><script>alert(1)</script>'),
    ("PUBLIC_POLICY_VERSION", "sentinel-private-key"),
    ("PUBLIC_POLICY_VERSION", "sb_secret_synthetic_not_a_real_key"),
    ("PUBLIC_POLICY_VERSION", "2026-11-10.1\nprivate"),
])
def test_invalid_public_metadata_falls_back_without_leaking_values(setting, value, monkeypatch):
    monkeypatch.setenv(setting, value)
    html = TestClient(app).get("/privacy").text
    assert '<time datetime="2026-11-10">2026-11-10</time>' in html
    assert "정책 문서 버전: 2026-11-10.1" in html
    if value:
        assert value not in html


def test_privacy_covers_sensitive_data_and_actual_conditional_processing():
    html = TestClient(app).get("/privacy").text
    for fact in (
        "건강 상태를 드러낼 수 있는 민감한 정보", "사진을 제공하지 않아도",
        "권한 철회만으로 이미 업로드한 사진이 삭제되지는 않습니다", "별도의 AI 분석 동의",
        "동의 시각·제공자·모델·동의 정책 버전", "보정 답변", "회복 메모",
        "이용 기록이 항상 익명인 것은 아닙니다", "SecureStore", "SQLite", "Neon",
        "Vercel", "Supabase", "카카오", "Cloudflare R2", "OpenAI",
        "실제 AI 제공자로 활성화된 경우", "이전 사진 자체는 이 요청에 포함하지 않습니다",
        "모든 로그·보관이 없거나 즉시 삭제된다고 보장하지 않습니다", "PostHog·Sentry",
        "처리 국가", "법적 근거", "미확인 사항", "처리 정지", "동의 철회",
        "이메일 발신 주소만으로 소유권을 확정하지 않으며", "18~100세",
        "실제 나이 확인이나 보호자 동의 확인이 아닙니다", "별도 설정",
    ):
        assert fact in html


@pytest.mark.parametrize("path", ["/privacy", "/terms"])
def test_public_age_policy_is_18_plus_without_claiming_verification(path):
    html = TestClient(app).get(path).text
    assert "이용 대상은 만 18세 이상입니다" in html
    assert "18~100세" in html
    assert "자기 입력값 검사" in html
    assert "실제 나이 확인이나 보호자 동의 확인이 아닙니다" in html
    assert "이미 저장된 프로필의 접근까지 차단하는 것은 아닙니다" in html
    assert "14~100세" not in html
    assert "최종 이용 대상 연령" not in html
    assert "최종 이용 연령" not in html


@pytest.mark.parametrize("path", ["/privacy", "/account-deletion"])
def test_deletion_disclosures_do_not_promote_pending_to_completed(path):
    html = TestClient(app).get(path).text
    for fact in (
        "처리 중", "기본적으로 비활성화", "실제 저장소 검증이 필요합니다",
        "사진 내용이 없는 0바이트 객체", "안전한 정리 조건을 검증하기 전까지", "계정 식별자",
        "사진 객체 키", "보관 기한", "별도", "백업", "특정 완료 기한",
        "삭제 완료 응답이 있는 경우에도 계정 식별자와 삭제 상태는 남습니다",
        "현재 코드에는 이 정보의 자동 만료가 없습니다",
        "해당 계정의 이용 분석 이벤트·세션·분석용 사용자 정보도 함께 삭제합니다",
        "분석 정보의 삭제 범위는 현재 프로필에만 한정되지 않습니다",
    ):
        assert fact in html
    assert "사진은 서버에 설정된 만료일과 정기 정리 작업을 통해 삭제하며" not in html
    assert "완료되면 로그인 계정" not in html


def test_retention_example_is_not_a_deployed_ttl_promise():
    html = TestClient(app).get("/privacy").text
    assert "설정 예시의 사진 만료값은 30일" in html
    assert "실제 운영 보관 기한이 확인된 값은 아닙니다" in html
    assert "정기 작업의 배포·실행·성공 여부는 확인되지 않았으므로" in html
    assert "30일 이내 자동 삭제를 보장하지 않습니다" in html
    assert "모든 기록에 적용되는 자동 보관 기한은 코드에서 확인되지 않았습니다" in html
    assert "법정 보존 항목·기간" in html


def test_support_describes_reviewer_access_without_publishing_or_attesting_credentials():
    html = TestClient(app).get("/support").text
    assert "이메일로 로그인" in html
    assert "이미 발급된 계정" in html
    assert "Play Console의 비공개 앱 액세스" in html
    assert "이메일·비밀번호는 이 페이지에 게시하지 않습니다" in html
    assert "이메일 소유권 검증 기능을 제공하지 않습니다" in html
    assert "수신 가능 여부·담당자·응답 기한은 별도 운영 확인 대상" in html
    assert "추가 인증 면제를 이 문서만으로 보장하지 않습니다" in html


def test_policy_facts_do_not_attest_play_account_or_operational_approval():
    root = Path(__file__).resolve().parents[3]
    facts = (root / "docs/google-play/POLICY-FACTS-2026-11-10.md").read_text(encoding="utf-8")
    for gate in (
        "UNRESOLVED, NOT APPROVED", "PERSONAL", "Organization",
        "nutrition, fitness", "revocation/drain/lifecycle",
        "support mailbox ownership/delivery", "No account was provisioned in this task",
    ):
        assert gate in facts
    for official_page in ("13996367", "14738291", "10788890", "13634885"):
        assert f"https://support.google.com/googleplay/android-developer/answer/{official_page}" in facts


def test_account_deletion_page_has_authenticated_flow_and_no_get_side_effect():
    response = TestClient(app).get("/account-deletion")
    assert 'href="/?action=delete-account"' in response.text
    assert "로그인" in response.text
    assert "최종 확인" in response.text
    assert "복구" in response.text
    assert "이 링크를 열거나 로그인하는 것만으로 삭제되지 않습니다" in response.text
    assert "비활성화" in response.text
    assert "이메일 요청만으로 자동 접수·삭제되는 것은 아닙니다" in response.text
    assert "<form" not in response.text


def test_vercel_routes_public_notices_before_spa_fallback():
    root = Path(__file__).resolve().parents[3]
    routes = json.loads((root / "vercel.json").read_text())["routes"]
    public_route = next(index for index, value in enumerate(routes) if value.get("src") == "/(privacy|terms|support|account-deletion)/?")
    filesystem = next(index for index, value in enumerate(routes) if value.get("handle") == "filesystem")
    assert public_route < filesystem
    assert routes[public_route]["dest"] == "api/index.py"
