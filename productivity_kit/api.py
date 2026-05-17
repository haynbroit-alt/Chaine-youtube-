from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from productivity_kit import __version__
from productivity_kit.csv_tools import summarize_csv
from productivity_kit.home_html import landing_page_html
from productivity_kit.jobs import run_digest
from productivity_kit.schemas import YoutubeBatchRequest, YoutubeSummarizeRequest
from productivity_kit.settings import get_settings
from productivity_kit.youtube import summarize_youtube_async

_bootstrap = get_settings()

app = FastAPI(
    title=_bootstrap.app_name,
    description=(
        "API : résumé YouTube (sous-titres), analyse CSV (simple ou lot), digest e-mail / webhooks. "
        "Voir la page d'accueil `/` pour démarrer."
    ),
    version=__version__,
)

if _bootstrap.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_bootstrap.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root() -> str:
    """Une phrase d’accueil + liens (plus convivial qu’une API nue)."""
    s = get_settings()
    url = (s.streamlit_public_url or "").strip() or None
    return landing_page_html(streamlit_url=url)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/version")
def version() -> dict[str, str]:
    s = get_settings()
    return {"version": __version__, "app": s.app_name}


@app.get("/ready")
def ready() -> dict[str, bool | int | str]:
    s = get_settings()
    return {
        "imap_configured": s.imap_configured,
        "webhook_configured": bool(s.webhook_url),
        "organize_on_digest": s.organize_on_digest,
        "organize_folder_set": bool(s.organize_folder),
        "imap_limit": s.imap_limit,
        "openai_configured": bool(s.openai_api_key),
    }


@app.post("/jobs/digest")
def jobs_digest() -> dict[str, object]:
    """Exécute le digest (IMAP + webhook optionnel + rangement optionnel)."""
    return run_digest(get_settings())


@app.post("/youtube/summarize")
async def youtube_summarize(body: YoutubeSummarizeRequest) -> dict[str, str | int]:
    """Résume une vidéo à partir des sous-titres publics (résumé extractif ou OpenAI)."""
    s = get_settings()
    try:
        return await summarize_youtube_async(
            body.url,
            body.template,
            use_llm=body.use_llm,
            openai_api_key=s.openai_api_key or None,
            openai_model=s.openai_model,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur lors du résumé (réseau ou fournisseur) : {e!s}",
        ) from e


@app.post("/youtube/batch-summarize")
async def youtube_batch_summarize(body: YoutubeBatchRequest) -> dict[str, object]:
    """Traite plusieurs URLs à la suite (synchrone côté client : la réponse attend la fin)."""
    s = get_settings()
    results: list[dict[str, object]] = []
    for url in body.urls:
        try:
            data = await summarize_youtube_async(
                url,
                body.template,
                use_llm=body.use_llm,
                openai_api_key=s.openai_api_key or None,
                openai_model=s.openai_model,
            )
            results.append({"url": url, "ok": True, "result": data})
        except ValueError as e:
            results.append({"url": url, "ok": False, "error": str(e)})
    return {"count": len(results), "results": results}


async def _summarize_uploaded_csv(file: UploadFile) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Fichier .csv attendu.")

    suffix = Path(file.filename).suffix or ".csv"
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    try:
        if tmp_path is None:
            raise HTTPException(status_code=500, detail="Fichier temporaire indisponible.")
        return summarize_csv(tmp_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail="Encodage non UTF-8 ; convertissez le fichier en UTF-8.",
        ) from e
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


@app.post("/csv/summary")
async def csv_summary(file: UploadFile = File(...)) -> dict:
    return await _summarize_uploaded_csv(file)


@app.post("/csv/batch-summary")
async def csv_batch_summary(files: list[UploadFile] = File(...)) -> dict[str, object]:
    """Plusieurs CSV en un envoi (multipart, champ répété `files`)."""
    if not files:
        raise HTTPException(status_code=400, detail="Au moins un fichier CSV requis.")
    items: list[dict[str, object]] = []
    for i, f in enumerate(files):
        entry: dict[str, object] = {"index": i, "filename": f.filename}
        try:
            entry["summary"] = await _summarize_uploaded_csv(f)
            entry["ok"] = True
        except HTTPException as e:
            entry["ok"] = False
            entry["error"] = e.detail
            entry["status_code"] = e.status_code
        items.append(entry)
    return {"count": len(items), "items": items}
