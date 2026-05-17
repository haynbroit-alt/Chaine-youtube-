from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import typer

from productivity_kit import __version__
from productivity_kit.csv_tools import summarize_csv
from productivity_kit.jobs import run_digest
from productivity_kit.organize import organize_folder
from productivity_kit.settings import get_settings

app = typer.Typer(
    help="Outils en ligne de commande du kit productivité (CSV, e-mails, lancement du serveur).",
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command("version", help="Affiche le numéro de version installé.")
def version_cmd() -> None:
    typer.echo(__version__)


@app.command("serve", help="Démarre le serveur web documenté (FastAPI avec Uvicorn).")
def serve_cmd(
    host: str | None = typer.Option(None, help="Remplace la valeur de la variable API_HOST"),
    port: int | None = typer.Option(None, help="Remplace la valeur de la variable API_PORT"),
) -> None:
    s = get_settings()
    h = host or s.api_host
    p = port or s.api_port
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "productivity_kit.api:app",
        "--host",
        h,
        "--port",
        str(p),
    ]
    raise typer.Exit(subprocess.call(cmd))


@app.command("csv-summary", help="Affiche le résumé JSON d’un fichier CSV (UTF-8).")
def csv_summary_cmd(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True, help="Chemin du fichier .csv"),
    rows: int = typer.Option(8, help="Nombre de lignes d’aperçu dans le résultat"),
) -> None:
    data = summarize_csv(path, preview_rows=rows)
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@app.command("organize", help="Range les fichiers d’un dossier dans des sous-dossiers par extension.")
def organize_cmd(
    folder: Path = typer.Argument(..., help="Dossier à traiter"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simule les déplacements sans rien modifier"),
) -> None:
    for line in organize_folder(folder, dry_run=dry_run):
        typer.echo(line)


@app.command("mail-list", help="Liste les derniers messages IMAP (nécessite la configuration IMAP).")
def mail_list_cmd(
    limit: int | None = typer.Option(None, help="Nombre maximum de messages (remplace IMAP_LIMIT)"),
) -> None:
    from productivity_kit.mail_imap import fetch_mail_summaries

    s = get_settings()
    if not s.imap_configured:
        typer.secho(
            "La messagerie n’est pas configurée : renseignez IMAP_HOST, IMAP_USER et IMAP_PASSWORD.",
            err=True,
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    lim = limit if limit is not None else s.imap_limit
    items = fetch_mail_summaries(
        host=s.imap_host,
        user=s.imap_user,
        password=s.imap_password,
        folder=s.imap_folder,
        ssl=s.imap_ssl,
        limit=lim,
        unseen_only=s.imap_unseen_only,
    )
    typer.echo(json.dumps([m.__dict__ for m in items], ensure_ascii=False, indent=2))


@app.command("digest", help="Exécute le digest (messagerie, webhook, rangement selon la configuration).")
def digest_cmd() -> None:
    s = get_settings()
    result = run_digest(s)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
