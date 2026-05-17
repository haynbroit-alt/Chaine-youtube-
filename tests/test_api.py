from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from productivity_kit.api import app


def test_root_landing_html() -> None:
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert "text/html" in (r.headers.get("content-type") or "")
    assert "Kit productivité" in r.text
    assert "/docs" in r.text
    assert "documentation interactive" in r.text.lower()


def test_health_and_version() -> None:
    c = TestClient(app)
    assert c.get("/health").json() == {"statut": "disponible"}
    r = c.get("/version")
    assert r.status_code == 200
    j = r.json()
    assert "version" in j
    assert "nom" in j


def test_ready_shape() -> None:
    c = TestClient(app)
    j = c.get("/ready").json()
    assert "messagerie_imap_configuree" in j
    assert "cle_openai_configuree" in j
    assert "serveur_ollama_defini" in j


def test_csv_batch_summary() -> None:
    c = TestClient(app)
    files = [
        ("files", ("a.csv", b"x,y\n1,2\n", "text/csv")),
        ("files", ("b.csv", b"a\nb\n", "text/csv")),
    ]
    r = c.post("/csv/batch-summary", files=files)
    assert r.status_code == 200
    body = r.json()
    assert body["nombre"] == 2
    assert all(f["reussi"] for f in body["fichiers"])


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
