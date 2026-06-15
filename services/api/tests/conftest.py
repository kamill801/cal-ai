from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_api_data_path(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("CAL_AI_API_DATA_PATH", str(tmp_path / "cal-ai-api.db"))
