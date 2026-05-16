from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from productivity_kit.csv_tools import summarize_csv

app = FastAPI(
    title="Kit productivité",
    description="API locale : santé, résumé de CSV uploadé.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
