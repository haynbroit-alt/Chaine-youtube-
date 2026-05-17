from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from productivity_kit import __version__
from productivity_kit.csv_tools import summarize_csv
from productivity_kit.jobs import run_digest
from productivity_kit.settings import get_settings

_bootstrap = get_settings()

app = FastAPI(
    title=_bootstrap.app_name,
    description="API locale : santé, version, digest, résumé CSV.",
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


@app.get("/")
def root() -> RedirectResponse:
    """Racine : renvoie vers la doc interactive (évite une page « Not Found » vide)."""
    return RedirectResponse(url="/docs", status_code=307)


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
    }


@app.post("/jobs/digest")
def jobs_digest() -> dict[str, object]:
    """Exécute le digest (IMAP + webhook optionnel + rangement optionnel)."""
    return run_digest(get_settings())


@app.post("/csv/summary")
async def csv_summary(file: UploadFile = File(...)) -> dict:
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
