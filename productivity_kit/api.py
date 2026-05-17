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

_TAGS: list[dict[str, str]] = [
    {
        "name": "Utilitaires",
        "description": "État du service et informations générales.",
    },
    {
        "name": "YouTube",
        "description": "Résumés à partir des sous-titres disponibles sur la vidéo.",
    },
    {
        "name": "Fichiers CSV",
        "description": "Analyse et statistiques sur des tableurs exportés en CSV.",
    },
    {
        "name": "Automatisation",
        "description": "Digest e-mail, notifications webhooks et rangement de fichiers.",
    },
]

app = FastAPI(
    title=_bootstrap.app_name,
    description=(
        "Application en français : résumé de vidéos YouTube (sous-titres), analyse de CSV "
        "(fichier unique ou lot), digest e-mail et webhooks. L’IA peut passer par **OpenAI** (nuage) "
        "ou **Ollama** (machine locale ou réseau privé). Commencez par la page d’accueil `/` "
        "ou la documentation interactive ci-dessous."
    ),
    version=__version__,
    openapi_tags=_TAGS,
)

if _bootstrap.cors_origins_list:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_bootstrap.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def root() -> str:
    """Page d’accueil en français avec liens utiles."""
    s = get_settings()
    url = (s.streamlit_public_url or "").strip() or None
    return landing_page_html(streamlit_url=url)


@app.get(
    "/health",
    tags=["Utilitaires"],
    summary="Disponibilité du service",
)
def health() -> dict[str, str]:
    return {"statut": "disponible"}


@app.get(
    "/version",
    tags=["Utilitaires"],
    summary="Version installée",
)
def version() -> dict[str, str]:
    s = get_settings()
    return {"version": __version__, "nom": s.app_name}


@app.get(
    "/ready",
    tags=["Utilitaires"],
    summary="Configuration détectée (sans secrets)",
)
def ready() -> dict[str, bool | int | str]:
    s = get_settings()
    return {
        "messagerie_imap_configuree": s.imap_configured,
        "webhook_configure": bool(s.webhook_url),
        "rangement_lors_du_digest": s.organize_on_digest,
        "dossier_de_rangement_defini": bool(s.organize_folder),
        "nombre_maximum_de_messages_imap": s.imap_limit,
        "cle_openai_configuree": bool(s.openai_api_key),
        "serveur_ollama_defini": s.ollama_est_configure,
    }


@app.post(
    "/jobs/digest",
    tags=["Automatisation"],
    summary="Lancer le digest",
    description="Lit la messagerie si elle est configurée, envoie éventuellement un webhook et peut ranger un dossier.",
)
def jobs_digest() -> dict[str, object]:
    return run_digest(get_settings())


@app.post(
    "/youtube/summarize",
    tags=["YouTube"],
    summary="Résumer une vidéo",
    description=(
        "Utilise les sous-titres publics. Résumé automatique gratuit, ou résumé par IA : "
        "OpenAI (OPENAI_API_KEY) ou **Ollama** sur la machine / le réseau local (OLLAMA_BASE_URL)."
    ),
)
async def youtube_summarize(body: YoutubeSummarizeRequest) -> dict[str, str | int | None]:
    s = get_settings()
    try:
        return await summarize_youtube_async(
            body.url,
            body.template,
            use_llm=body.use_llm,
            openai_api_key=s.openai_api_key or None,
            openai_model=s.openai_model,
            ollama_base_url=s.ollama_base_url or None,
            ollama_model=s.ollama_model,
            ollama_timeout_s=s.ollama_timeout_s,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Impossible de terminer le résumé (réseau ou service externe) : {e!s}",
        ) from e


@app.post(
    "/youtube/batch-summarize",
    tags=["YouTube"],
    summary="Résumer plusieurs vidéos",
    description="Traite chaque adresse l’une après l’autre ; la réponse arrive quand tout est terminé.",
)
async def youtube_batch_summarize(body: YoutubeBatchRequest) -> dict[str, object]:
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
                ollama_base_url=s.ollama_base_url or None,
                ollama_model=s.ollama_model,
                ollama_timeout_s=s.ollama_timeout_s,
            )
            results.append({"url": url, "reussi": True, "donnees": data})
        except ValueError as e:
            results.append({"url": url, "reussi": False, "erreur": str(e)})
    return {"nombre": len(results), "resultats": results}


async def _summarize_uploaded_csv(file: UploadFile) -> dict:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Seuls les fichiers dont le nom se termine par .csv sont acceptés.",
        )

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
            raise HTTPException(
                status_code=500,
                detail="Impossible de créer un fichier temporaire sur le serveur.",
            )
        return summarize_csv(tmp_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail="Le fichier n’est pas en UTF-8. Enregistrez-le au format UTF-8 puis réessayez.",
        ) from e
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


@app.post(
    "/csv/summary",
    tags=["Fichiers CSV"],
    summary="Analyser un fichier CSV",
    description="Renvoie statistiques, aperçu des lignes et indices sur le type des colonnes.",
)
async def csv_summary(
    file: UploadFile = File(..., description="Fichier .csv encodé en UTF-8"),
) -> dict:
    return await _summarize_uploaded_csv(file)


@app.post(
    "/csv/batch-summary",
    tags=["Fichiers CSV"],
    summary="Analyser plusieurs fichiers CSV",
    description="Envoyez plusieurs pièces jointes avec le même nom de champ « files ».",
)
async def csv_batch_summary(
    files: list[UploadFile] = File(
        ...,
        description="Un ou plusieurs fichiers .csv (UTF-8), champ du formulaire « files »",
    ),
) -> dict[str, object]:
    if not files:
        raise HTTPException(
            status_code=400,
            detail="Veuillez joindre au moins un fichier CSV.",
        )
    elements: list[dict[str, object]] = []
    for i, f in enumerate(files):
        entree: dict[str, object] = {"indice": i, "nom_fichier": f.filename}
        try:
            entree["resume"] = await _summarize_uploaded_csv(f)
            entree["reussi"] = True
        except HTTPException as e:
            entree["reussi"] = False
            entree["erreur"] = e.detail
            entree["code_http"] = e.status_code
        elements.append(entree)
    return {"nombre": len(elements), "fichiers": elements}
