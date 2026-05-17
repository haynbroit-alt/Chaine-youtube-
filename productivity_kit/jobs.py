from __future__ import annotations

from pathlib import Path

from productivity_kit.mail_imap import MailSummary, fetch_mail_summaries
from productivity_kit.notify import post_json_webhook
from productivity_kit.organize import organize_folder
from productivity_kit.settings import Settings


def format_digest_lines(summaries: list[MailSummary]) -> list[str]:
    lines: list[str] = []
    if not summaries:
        lines.append("Aucun message à afficher (ou boîte vide selon critères).")
        return lines
    lines.append(f"Messages : {len(summaries)}")
    for m in summaries:
        subj = m.subject or "(sans objet)"
        lines.append(f"- [{m.uid}] {subj} — {m.sender} ({m.date})")
    return lines


def run_digest(settings: Settings) -> dict[str, object]:
    """
    Optionnel: lit IMAP, envoie un webhook, peut organiser un dossier.
    Retourne un résumé sérialisable (logs, pas de secrets).
    """
    log: list[str] = []
    summaries: list[MailSummary] = []

    if settings.imap_configured:
        summaries = fetch_mail_summaries(
            host=settings.imap_host,
            user=settings.imap_user,
            password=settings.imap_password,
            folder=settings.imap_folder,
            ssl=settings.imap_ssl,
            limit=settings.imap_limit,
            unseen_only=settings.imap_unseen_only,
        )
        log.extend(format_digest_lines(summaries))
    else:
        log.append("IMAP non configuré (IMAP_HOST / IMAP_USER / IMAP_PASSWORD).")

    body = "\n".join(log)
    webhook_status: int | None = None
    if settings.webhook_url:
        try:
            code, _text = post_json_webhook(
                settings.webhook_url,
                {"source": "productivity_kit", "kind": "digest", "text": body},
                timeout_s=settings.webhook_timeout_s,
            )
            webhook_status = code
            log.append(f"Notification webhook envoyée, code HTTP {code}")
        except Exception as e:
            log.append(f"Erreur lors de l’envoi au webhook : {e!s}")

    organize_lines: list[str] = []
    if settings.organize_on_digest and settings.organize_folder:
        root = Path(settings.organize_folder).expanduser()
        try:
            organize_lines = organize_folder(root, dry_run=False)
            log.extend(organize_lines)
        except OSError as e:
            log.append(f"Erreur lors du rangement des fichiers : {e!s}")

    return {
        "lines": log,
        "mail_count": len(summaries),
        "webhook_status": webhook_status,
        "organized_moves": len(organize_lines),
    }
