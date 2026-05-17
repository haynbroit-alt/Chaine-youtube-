# Kit productivité

Ensemble **installable et documenté** pour automatiser en local : **API HTTP**, **CLI**, **CSV**, **rangement de fichiers**, **messagerie IMAP**, **webhooks**, **digest planifiable**, **Docker** et **tests**. À brancher sur une activité réelle (veille, chaîne, admin) — sans promesse de revenus.

## Fonctionnalités

| Zone | Détail |
|------|--------|
| API | `FastAPI` : santé, version, état de config, digest, résumé CSV uploadé |
| CLI | `python -m productivity_kit` : `serve`, `csv-summary`, `organize`, `mail-list`, `digest`, `version` |
| Fichiers | Classement par extension (module + script) |
| E-mail | Lecture IMAP (en-têtes uniquement, `BODY.PEEK[HEADER]`) |
| Notifications | POST JSON vers `WEBHOOK_URL` (Slack, Discord incoming, n8n, etc.) |
| Planification | Exemple `schedules/crontab.example` |
| Conteneur | `Dockerfile` + `docker-compose.yml` |

## Installation

```bash
python3 -m pip install -r requirements.txt
# développement / CI
python3 -m pip install -r requirements-dev.txt
```

Copiez la configuration :

```bash
cp .env.example .env
# éditez .env (IMAP et webhook sont optionnels)
```

## CLI

```bash
python3 -m productivity_kit --help
python3 -m productivity_kit serve --help
python3 -m productivity_kit csv-summary examples/sample.csv
python3 -m productivity_kit organize ~/Downloads --dry-run
python3 -m productivity_kit mail-list          # nécessite IMAP dans .env
python3 -m productivity_kit digest               # IMAP + webhook + rangement optionnels
```

## API

```bash
python3 -m productivity_kit serve
# ou
python3 -m uvicorn productivity_kit.api:app --host 127.0.0.1 --port 8000
```

| Méthode | Chemin | Rôle |
|---------|--------|------|
| GET | `/` | Redirection vers `/docs` (interface Swagger) |
| GET | `/health` | Statut |
| GET | `/version` | Version + nom d’app |
| GET | `/ready` | Indicateurs de config (sans secrets) |
| POST | `/jobs/digest` | Lance le digest (effets de bord possibles : webhook, rangement) |
| POST | `/csv/summary` | `multipart/form-data`, champ `file` = `.csv` UTF-8 |

Documentation interactive : `http://127.0.0.1:8000/docs`

## Variables d’environnement

Voir `.env.example` : `API_*`, `CORS_ORIGINS`, `IMAP_*`, `WEBHOOK_*`, `ORGANIZE_*`.

- **`ORGANIZE_ON_DIGEST=true`** : lors d’un digest, range aussi `ORGANIZE_FOLDER` (à utiliser avec prudence).
- **`IMAP_UNSEEN_ONLY=true`** : ne liste que les non lus.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

L’API écoute sur le port **8000** du conteneur.

## Vercel

Le fichier `pyproject.toml` contient une section `[project]` (dépendances runtime pour `uv lock` sur Vercel) et `[tool.vercel] entrypoint = "productivity_kit.api:app"`, comme décrit pour le [déploiement FastAPI sur Vercel](https://vercel.com/docs/frameworks/backend/fastapi). Le fichier `api/index.py` réexporte aussi `app` pour les builds qui ne lisent que les chemins conventionnels. Définissez les variables d’environnement dans le projet Vercel (équivalent de `.env`).

## Tests

```bash
python3 -m pytest
```

## Scripts (compatibilité)

Les scripts sous `scripts/` restent utilisables ; la CLI les remplace pour un flux unique.

## Sécurité

Ne commitez pas `.env`. Les mots de passe IMAP ne sont jamais journalisés par ce kit ; limitez les droits du fichier `.env` sur votre machine.
