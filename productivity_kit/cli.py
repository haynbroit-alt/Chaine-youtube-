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

app = typer.Typer(help="Kit productivité : CSV, fichiers, IMAP, webhooks, API.")


@app.command("version")
def version_cmd() -> None:
    typer.echo(__version__)


@app.command("serve")
def serve_cmd(
    host: str | None = typer.Option(None, help="Surcharge API_HOST"),
    port: int | None = typer.Option(None, help="Surcharge API_PORT"),
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


@app.command("csv-summary")
def csv_summary_cmd(
    path: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True),
    rows: int = typer.Option(8, help="Lignes d’aperçu"),
) -> None:
    data = summarize_csv(path, preview_rows=rows)
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@app.command("organize")
def organize_cmd(
    folder: Path = typer.Argument(..., help="Dossier à organiser"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simule sans déplacer"),
) -> None:
    for line in organize_folder(folder, dry_run=dry_run):
        typer.echo(line)


@app.command("mail-list")
def mail_list_cmd(
    limit: int | None = typer.Option(None, help="Surcharge IMAP_LIMIT"),
) -> None:
    from productivity_kit.mail_imap import fetch_mail_summaries

    s = get_settings()
    if not s.imap_configured:
        typer.secho("Configurez IMAP_HOST, IMAP_USER, IMAP_PASSWORD.", err=True, fg=typer.colors.RED)
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


@app.command("digest")
def digest_cmd() -> None:
    s = get_settings()
    result = run_digest(s)
    typer.echo(json.dumps(result, ensure_ascii=False, indent=2))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
