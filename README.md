# Kit productivité

Ensemble **installable et documenté** : **API FastAPI** (CSV, YouTube, digest), **interface Streamlit** (sans curl), **CLI**, **Docker**, **Vercel**, **tests**. **Interface et messages orientés français** (documentation OpenAPI, erreurs, page d’accueil). Pensé pour une chaîne / veille / admin — sans promesse de revenus.

## Fonctionnalités

| Zone | Détail |
|------|--------|
| Interface | **Streamlit** (`streamlit_app.py`) : déposer un CSV, coller une URL YouTube → résumé |
| API | **FastAPI** : santé, version, page d’accueil HTML, digest, CSV simple / **lot**, **YouTube** (sous-titres) |
| YouTube | Résumé **extractif** (gratuit) ou **OpenAI** (`OPENAI_API_KEY`, modèles `OPENAI_MODEL`) |
| CLI | `python -m productivity_kit` : `serve`, `csv-summary`, `organize`, `mail-list`, `digest`, `version` |
| Fichiers | Classement par extension (module + script) |
| E-mail | Lecture IMAP (en-têtes, `BODY.PEEK[HEADER]`) |
| Notifications | POST JSON vers `WEBHOOK_URL` |
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
# éditez .env (IMAP, webhook, OpenAI : optionnels selon usage)
```

## Interface Streamlit (priorité « grand public »)

Lancez l’UI locale (même dépôt, même `.env` que l’API si vous partagez les clés) :

```bash
cd /chemin/vers/le/repo
python3 -m streamlit run streamlit_app.py
```

Onglets **CSV** et **YouTube**. Pour les résumés IA, renseignez `OPENAI_API_KEY` dans `.env`.

Pour afficher un lien vers Streamlit sur la page d’accueil de l’API (HTML à `/`), renseignez `STREAMLIT_PUBLIC_URL` (ex. URL Streamlit Cloud).

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
| GET | `/` | Page d’accueil HTML (liens `/docs`, Streamlit si `STREAMLIT_PUBLIC_URL`) |
| GET | `/health` | Disponibilité : `{"statut": "disponible"}` |
| GET | `/version` | `version`, `nom` |
| GET | `/ready` | Indicateurs en français (`messagerie_imap_configuree`, `cle_openai_configuree`, …) |
| POST | `/youtube/summarize` | JSON `{ "url", "template": "court"\|"detaille"\|"decision", "use_llm" }` — champ `mode` du résumé : `automatique` ou `ia` |
| POST | `/youtube/batch-summarize` | JSON `urls` — réponse : `nombre`, `resultats[]` avec `reussi`, `donnees` ou `erreur` |
| POST | `/jobs/digest` | Digest (IMAP + webhook + rangement optionnels) |
| POST | `/csv/summary` | Un CSV : `multipart/form-data`, champ `file` |
| POST | `/csv/batch-summary` | Plusieurs CSV : champs répétés `files` — réponse : `nombre`, `fichiers[]` avec `reussi`, `resume` ou `erreur` |

La documentation interactive **/docs** (Swagger) est rédigée en **français** (titres des groupes, résumés des opérations). URL locale : `http://127.0.0.1:8000/docs`.

### Codes d’erreur (API)

- **400** : paramètre invalide (URL, encodage CSV, clé OpenAI manquante si `use_llm`) — message en français dans `detail`.
- **404** : fichier introuvable (rare côté upload).
- **502** : erreur réseau / fournisseur (ex. YouTube ou OpenAI).

## Variables d’environnement

Voir `.env.example` : `API_*`, `CORS_ORIGINS`, `IMAP_*`, `WEBHOOK_*`, `ORGANIZE_*`, **`OPENAI_*`**, **`STREAMLIT_PUBLIC_URL`**.

- **`ORGANIZE_ON_DIGEST=true`** : lors d’un digest, range aussi `ORGANIZE_FOLDER` (à utiliser avec prudence).
- **`IMAP_UNSEEN_ONLY=true`** : ne liste que les non lus.

## Docker

```bash
cp .env.example .env
docker compose up --build
```

L’API écoute sur le port **8000** du conteneur.

## Vercel

Le fichier `pyproject.toml` contient une section `[project]` (dépendances pour `uv lock`) et `[tool.vercel] entrypoint = "productivity_kit.api:app"`. Le fichier `api/index.py` réexporte aussi `app`. **Streamlit** n’est pas exécuté sur Vercel par ce dépôt : déployez-le sur [Streamlit Community Cloud](https://streamlit.io/cloud) ou en local, puis renseignez `STREAMLIT_PUBLIC_URL` sur Vercel.

## Feuille de route (par rapport aux pistes produit)

| Idée | Statut |
|------|--------|
| Interface visuelle simple | **Fait** : Streamlit + page `/` en HTML |
| Lots CSV / lots YouTube (réponse unique) | **Fait** : `/csv/batch-summary`, `/youtube/batch-summarize` |
| Jobs async + `job_id` + file d’attente | **Pas fait** (Redis/Celery ou Upstash recommandé pour la prod) |
| Export PDF / e-mail / Drive | **Pas fait** |
| Bot Telegram / Discord | **Pas fait** |
| Cache résultats YouTube | **Pas fait** |
| Statistiques d’usage | **Pas fait** |

## Tests

```bash
python3 -m pytest
```

## Scripts (compatibilité)

Les scripts sous `scripts/` restent utilisables ; la CLI les remplace pour un flux unique.

## Sécurité

Ne commitez pas `.env`. Les mots de passe et clés API ne sont pas journalisés par ce kit ; limitez les droits du fichier `.env` sur votre machine.
