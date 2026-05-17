from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from productivity_kit.api import app


def test_root_redirects_to_docs() -> None:
    c = TestClient(app)
    r = c.get("/", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers.get("location") == "/docs"


def test_health_and_version() -> None:
    c = TestClient(app)
    assert c.get("/health").json() == {"status": "ok"}
    r = c.get("/version")
    assert r.status_code == 200
    assert "version" in r.json()


def test_ready_shape() -> None:
    c = TestClient(app)
    j = c.get("/ready").json()
    assert "imap_configured" in j


def test_csv_summary_upload(tmp_path: Path) -> None:
    p = tmp_path / "t.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    c = TestClient(app)
    r = c.post("/csv/summary", files={"file": ("t.csv", p.read_bytes(), "text/csv")})
    assert r.status_code == 200
    body = r.json()
    assert body["row_count"] == 1
    assert body["headers"] == ["a", "b"]


def test_jobs_digest_no_config(monkeypatch: pytest.MonkeyPatch) -> None:
    from productivity_kit.settings import get_settings

    for key in (
        "IMAP_HOST",
        "IMAP_USER",
        "IMAP_PASSWORD",
        "WEBHOOK_URL",
        "ORGANIZE_FOLDER",
    ):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ORGANIZE_ON_DIGEST", "false")
    get_settings.cache_clear()
    c = TestClient(app)
    r = c.post("/jobs/digest")
    assert r.status_code == 200
    data = r.json()
    assert "lines" in data
    assert any("IMAP non configuré" in line for line in data["lines"])
    get_settings.cache_clear()
