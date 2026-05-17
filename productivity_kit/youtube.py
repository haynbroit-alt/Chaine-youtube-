from __future__ import annotations

import asyncio
import re
from typing import Literal

from youtube_transcript_api import YouTubeTranscriptApi

TemplateId = Literal["court", "detaille", "decision"]

YOUTUBE_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})",
    re.IGNORECASE,
)


def extract_video_id(url: str) -> str | None:
    u = url.strip()
    m = YOUTUBE_RE.search(u)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", u):
        return u
    return None


def fetch_transcript_text(video_id: str) -> str:
    api = YouTubeTranscriptApi()
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
            "Aperçu factuel (mode extractif) :\n\n"
            + out
            + "\n\nPour une synthèse « décision » structurée (avantages / limites / "
            "recommandation), utilisez `use_llm: true` avec `OPENAI_API_KEY` configurée."
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
    prompts: dict[TemplateId, str] = {
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
                "content": f"{prompts[template]}\n\n---\nTRANSCRIPTION :\n{t}",
            },
        ],
        temperature=0.3,
        max_tokens=1200,
    )
    choice = r.choices[0].message.content
    return (choice or "").strip() or "(Réponse vide du modèle)"


def summarize_youtube(
    url: str,
    template: TemplateId,
    *,
    use_llm: bool,
    openai_api_key: str | None,
    openai_model: str,
) -> dict[str, str | int]:
    vid = extract_video_id(url)
    if not vid:
        raise ValueError("URL ou identifiant YouTube invalide (11 caractères attendus).")
    transcript = fetch_transcript_text(vid)
    if use_llm:
        if not openai_api_key:
            raise ValueError(
                "Résumé IA demandé mais OPENAI_API_KEY n'est pas configurée "
                "(variable d'environnement)."
            )
        summary = summarize_with_openai(
            transcript, template, api_key=openai_api_key, model=openai_model
        )
        mode = "llm"
    else:
        summary = summarize_extractive(transcript, template)
        mode = "extractif"
    preview = transcript[:500] + ("…" if len(transcript) > 500 else "")
    return {
        "video_id": vid,
        "transcript_preview": preview,
        "transcript_char_count": len(transcript),
        "template": template,
        "summary": summary,
        "mode": mode,
    }


async def summarize_youtube_async(
    url: str,
    template: TemplateId,
    *,
    use_llm: bool,
    openai_api_key: str | None,
    openai_model: str,
) -> dict[str, str | int]:
    """Évite de bloquer l’event loop (transcription + éventuel appel OpenAI)."""

    return await asyncio.to_thread(
        summarize_youtube,
        url,
        template,
        use_llm=use_llm,
        openai_api_key=openai_api_key,
        openai_model=openai_model,
    )
