from fastapi.testclient import TestClient

from productivity_kit.api import app


def test_pwa_index_served() -> None:
    c = TestClient(app)
    r = c.get("/pwa/")
    assert r.status_code == 200
    assert "youtube/summarize" in r.text
    assert "csv/summary" in r.text
    assert "/manifest.json" in r.text


def test_web_manifest_root() -> None:
    c = TestClient(app)
    r = c.get("/manifest.json")
    assert r.status_code == 200
    assert "Kit Productivité" in r.text
    assert '"start_url": "/"' in r.text
    assert "icon-192.png" in r.text


def test_pwa_icons() -> None:
    c = TestClient(app)
    assert c.get("/icon-192.png").status_code == 200
    assert c.get("/icon-512.png").status_code == 200
