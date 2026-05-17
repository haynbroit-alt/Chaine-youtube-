from fastapi.testclient import TestClient

from productivity_kit.api import app


def test_pwa_index_served() -> None:
    c = TestClient(app)
    r = c.get("/pwa/")
    assert r.status_code == 200
    assert "youtube/summarize" in r.text
    assert "csv/summary" in r.text


def test_pwa_manifest() -> None:
    c = TestClient(app)
    r = c.get("/pwa/manifest.json")
    assert r.status_code == 200
    assert "Kit productivité" in r.text or "Kit productivit" in r.text
