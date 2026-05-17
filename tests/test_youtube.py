from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from productivity_kit.api import app
from productivity_kit.youtube import extract_video_id


def test_extract_video_id_variants() -> None:
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ?t=12") == "dQw4w9WgXcQ"
    assert extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("not-a-url") is None


def test_youtube_summarize_mocked(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(_video_id: str) -> str:
        return "Première phrase. Deuxième phrase. Troisième."

    monkeypatch.setattr("productivity_kit.youtube.fetch_transcript_text", fake_fetch)
    c = TestClient(app)
    r = c.post(
        "/youtube/summarize",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "template": "court",
            "use_llm": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["video_id"] == "dQw4w9WgXcQ"
    assert data["mode"] == "automatique"
    assert data.get("fournisseur_ia") is None
    assert "summary" in data


def test_youtube_summarize_use_llm_sans_fournisseur(monkeypatch: pytest.MonkeyPatch) -> None:
    from productivity_kit.settings import get_settings

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    get_settings.cache_clear()
    c = TestClient(app)
    r = c.post(
        "/youtube/summarize",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "template": "court",
            "use_llm": True,
        },
    )
    assert r.status_code == 400
    get_settings.cache_clear()


def test_youtube_summarize_ollama_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from productivity_kit.settings import get_settings

    def fake_fetch(_video_id: str) -> str:
        return "Phrase une. Phrase deux."

    def fake_post(_url: str, json: dict | None = None, **_kwargs: object) -> object:
        class Resp:
            def raise_for_status(self) -> None:
                return None

            def json(self) -> dict[str, object]:
                return {"message": {"content": "Résumé via Ollama (test)."}}

        return Resp()

    monkeypatch.setattr("productivity_kit.youtube.fetch_transcript_text", fake_fetch)
    monkeypatch.setattr("productivity_kit.youtube.httpx.post", fake_post)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    get_settings.cache_clear()
    c = TestClient(app)
    r = c.post(
        "/youtube/summarize",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "template": "court",
            "use_llm": True,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["fournisseur_ia"] == "ollama"
    assert "Ollama" in data["summary"]
    get_settings.cache_clear()


def test_youtube_summarize_invalid_url() -> None:
    c = TestClient(app)
    r = c.post("/youtube/summarize", json={"url": "https://example.com", "template": "court"})
    assert r.status_code == 400


def test_youtube_batch_mixed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_fetch(video_id: str) -> str:
        if video_id == "dQw4w9WgXcQ":
            return "Une phrase. Deux phrases."
        raise ValueError("invalide")

    monkeypatch.setattr("productivity_kit.youtube.fetch_transcript_text", fake_fetch)
    c = TestClient(app)
    r = c.post(
        "/youtube/batch-summarize",
        json={
            "urls": ["https://youtu.be/dQw4w9WgXcQ", "not-valid"],
            "template": "court",
            "use_llm": False,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["nombre"] == 2
    assert data["resultats"][0]["reussi"] is True
    assert data["resultats"][1]["reussi"] is False
