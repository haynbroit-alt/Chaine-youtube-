from __future__ import annotations

import asyncio
import re
from typing import Literal

import httpx
from youtube_transcript_api import (
    CouldNotRetrieveTranscript,
    RequestBlocked,
    YouTubeTranscriptApi,
)
from youtube_transcript_api.proxies import GenericProxyConfig

from productivity_kit.settings import get_settings

YOUTUBE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})",
    re.IGNORECASE,
)

TemplateId = Literal["court", "detaille", "decision"]

_LLM_PROMPTS: dict[TemplateId, str] = {
    "court": (
        "Résume la transcription en exactement 3 puces courtes, en français, "
        "sans introduction inutile."
    ),
    "detaille": (
        "Produis un résumé structuré en français : contexte, points clés par "
        "thème, et conclusion. Utilise des sous-titres Markdown (##)."
    ),
    "decision": (
        "À partir de la transcription, rédige en français : avantages, "
        "inconvénients / risques, et une recommandation claire (1 phrase). "
        "Format Markdown avec listes."
    ),
}


def _transcript_error_message(exc: CouldNotRetrieveTranscript) -> str:
    if isinstance(exc, RequestBlocked):
        return (
            "YouTube refuse l’accès aux sous-titres depuis l’IP de ce serveur "
            "(cas fréquent sur Vercel, AWS, Google Cloud, Azure, etc.). "
            "Configurez YOUTUBE_PROXY_URL (proxy HTTP ou HTTPS, de préférence résidentiel) "
            "dans les variables d’environnement, ou exécutez l’API depuis une connexion résidentielle."
        )
    return "Impossible d’obtenir les sous-titres pour cette vidéo."


def _youtube_api() -> YouTubeTranscriptApi:
    s = get_settings()
    url = (s.youtube_proxy_url or "").strip()
    if url:
        cfg = GenericProxyConfig(http_url=url, https_url=url)
        return YouTubeTranscriptApi(proxy_config=cfg)
    return YouTubeTranscriptApi()


def extract_video_id(url: str) -> str | None:
    u = url.strip()
    m = YOUTUBE_RE.search(u)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", u):
        return u
    return None


def fetch_transcript_text(video_id: str) -> str:
    api = _youtube_api()
    try:
        tlist = api.list(video_id)
        langs = ["fr", "fr-FR", "en", "en-US"]
        try:
            tr = tlist.find_transcript(langs)
        except Exception:
            try:
                tr = next(iter(tlist))
            except StopIteration as e:
                raise ValueError("Aucune piste de sous-titres pour cette vidéo.") from e
        try:
            data = tr.fetch()
        except Exception as e:
            raise ValueError(
                "Impossible de récupérer les sous-titres (vidéo privée, réseau, ou erreur YouTube)."
            ) from e
        parts: list[str] = []
        for part in data:
            t = part.get("text", "") if isinstance(part, dict) else ""
            parts.append(t.replace("\n", " "))
        return " ".join(parts).strip()
    except CouldNotRetrieveTranscript as e:
        raise ValueError(_transcript_error_message(e)) from e


def summarize_extractive(text: str, template: TemplateId) -> str:
    text = text.strip()
    if not text:
        return "(Transcription vide)"
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text) if s]
    if template == "court":
        n = 3
    elif template == "detaille":
        n = 22
    else:
        n = 14
    out = " ".join(sentences[:n])
    if len(out) > 4500:
        out = out[:4497] + "…"
    if template == "decision":
        out = (
            "Aperçu factuel (résumé automatique à partir du texte) :\n\n"
            + out
            + "\n\nPour une synthèse « décision » structurée (avantages, limites, "
            "recommandation), activez l’option d’intelligence artificielle et configurez "
            "soit OPENAI_API_KEY (service distant), soit un serveur **Ollama** local "
            "(variable OLLAMA_BASE_URL, par ex. http://127.0.0.1:11434)."
        )
    return out


def summarize_with_openai(
    transcript: str,
    template: TemplateId,
    *,
    api_key: str,
    model: str,
) -> str:
    from openai import OpenAI

    t = transcript[:14_000]
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Tu aides à résumer des vidéos YouTube pour un utilisateur francophone.",
            },
            {
                "role": "user",
                "content": f"{_LLM_PROMPTS[template]}\n\n---\nTranscription :\n{t}",
            },
        ],
        temperature=0.3,
        max_tokens=1200,
    )
    choice = r.choices[0].message.content
    return (choice or "").strip() or "(Réponse vide du modèle)"


def summarize_with_ollama(
    transcript: str,
    template: TemplateId,
    *,
    base_url: str,
    model: str,
    timeout_s: float = 120.0,
) -> str:
    """Appelle un serveur Ollama (LAN ou machine locale) — aucune clé nuagique requise."""
    base = base_url.strip().rstrip("/")
    t = transcript[:14_000]
    user_content = f"{_LLM_PROMPTS[template]}\n\n---\nTranscription :\n{t}"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Tu résumes des transcriptions de vidéos en français, de façon factuelle.",
            },
            {"role": "user", "content": user_content},
        ],
        "stream": False,
    }
    r = httpx.post(f"{base}/api/chat", json=payload, timeout=timeout_s)
    r.raise_for_status()
    data = r.json()
    msg = data.get("message") or {}
    content = (msg.get("content") or "").strip()
    return content or "(Réponse vide du modèle)"


def summarize_youtube(
    url: str,
    template: TemplateId,
    *,
    use_llm: bool,
    openai_api_key: str | None,
    openai_model: str,
    ollama_base_url: str | None,
    ollama_model: str,
    ollama_timeout_s: float = 120.0,
) -> dict[str, str | int | None]:
    vid = extract_video_id(url)
    if not vid:
        raise ValueError("URL ou identifiant YouTube invalide (11 caractères attendus).")
    transcript = fetch_transcript_text(vid)
    fournisseur: str | None = None
    if use_llm:
        if openai_api_key:
            summary = summarize_with_openai(
                transcript, template, api_key=openai_api_key, model=openai_model
            )
            fournisseur = "openai"
        elif ollama_base_url and ollama_base_url.strip():
            summary = summarize_with_ollama(
                transcript,
                template,
                base_url=ollama_base_url,
                model=ollama_model,
                timeout_s=ollama_timeout_s,
            )
            fournisseur = "ollama"
        else:
            raise ValueError(
                "Résumé par IA demandé : renseignez OPENAI_API_KEY (service distant) "
                "ou OLLAMA_BASE_URL (serveur Ollama sur cette machine ou sur votre réseau local, "
                "par exemple http://127.0.0.1:11434)."
            )
        mode = "ia"
    else:
        summary = summarize_extractive(transcript, template)
        mode = "automatique"
    preview = transcript[:500] + ("…" if len(transcript) > 500 else "")
    return {
        "video_id": vid,
        "transcript_preview": preview,
        "transcript_char_count": len(transcript),
        "template": template,
        "summary": summary,
        "mode": mode,
        "fournisseur_ia": fournisseur,
    }


async def summarize_youtube_async(
    url: str,
    template: TemplateId,
    *,
    use_llm: bool,
    openai_api_key: str | None,
    openai_model: str,
    ollama_base_url: str | None,
    ollama_model: str,
    ollama_timeout_s: float = 120.0,
) -> dict[str, str | int | None]:
    """Évite de bloquer l’event loop (transcription + éventuel appel IA)."""

    return await asyncio.to_thread(
        summarize_youtube,
        url,
        template,
        use_llm=use_llm,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_timeout_s=ollama_timeout_s,
    )
