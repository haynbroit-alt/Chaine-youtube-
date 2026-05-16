# Kit productivité (local)

Base légère pour **automatiser un peu** le travail du quotidien : petite API, résumé de CSV, rangement de fichiers. Aucun revenu n’est garanti ; à adapter à votre activité.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## API (FastAPI)

```bash
uvicorn productivity_kit.api:app --reload --host 127.0.0.1 --port 8000
```

- `GET http://127.0.0.1:8000/health` — statut
- `POST http://127.0.0.1:8000/csv/summary` — corps `multipart/form-data`, champ `file` = fichier `.csv` UTF-8

## Scripts

Résumé JSON d’un CSV :

```bash
python scripts/csv_summary.py examples/sample.csv
```

Organiser les fichiers d’un dossier par extension (sous-dossiers `pdf`, `jpg`, etc.) :

```bash
python scripts/organize_folder.py ~/Downloads --dry-run
python scripts/organize_folder.py ~/Downloads
```

## Suite possible

Brancher la messagerie (IMAP), des webhooks, ou un planning (cron) autour de ces briques selon vos besoins réels.
