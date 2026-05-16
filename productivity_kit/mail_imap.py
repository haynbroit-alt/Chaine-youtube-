from __future__ import annotations

import imaplib
from dataclasses import dataclass
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import Message


def _decode_mime_header(value: str | None) -> str:
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


@dataclass(frozen=True)
class MailSummary:
    uid: str
    subject: str
    sender: str
    date: str


def _parse_envelope(msg: Message) -> tuple[str, str, str]:
    subject = _decode_mime_header(msg.get("Subject"))
    sender = _decode_mime_header(msg.get("From") or msg.get("Sender"))
    date = (msg.get("Date") or "").strip()
    return subject, sender, date


def fetch_mail_summaries(
    *,
    host: str,
    user: str,
    password: str,
    folder: str = "INBOX",
    ssl: bool = True,
    limit: int = 25,
    unseen_only: bool = False,
) -> list[MailSummary]:
    """Récupère les derniers messages (en-têtes seulement)."""
    if ssl:
        client = imaplib.IMAP4_SSL(host)
    else:
        client = imaplib.IMAP4(host)
    try:
        client.login(user, password)
        typ, _ = client.select(folder, readonly=True)
        if typ != "OK":
            raise RuntimeError(f"Dossier IMAP inaccessible: {folder}")

        criterion = "UNSEEN" if unseen_only else "ALL"
        typ, data = client.search(None, criterion)
        if typ != "OK" or not data or not data[0]:
            return []

        uids = data[0].split()
        uids = uids[-limit:] if len(uids) > limit else uids

        out: list[MailSummary] = []
        for uid in reversed(uids):
            uid_s = uid.decode() if isinstance(uid, bytes) else str(uid)
            typ, msg_data = client.fetch(uid, "(BODY.PEEK[HEADER])")
            if typ != "OK" or not msg_data:
                continue
            raw: bytes | None = None
            for part in msg_data:
                if isinstance(part, tuple) and len(part) >= 2 and isinstance(part[1], bytes):
                    raw = part[1]
                    break
            if raw is None:
                continue
            msg = message_from_bytes(raw)
            subject, sender, date = _parse_envelope(msg)
            out.append(MailSummary(uid=uid_s, subject=subject, sender=sender, date=date))
        return out
    finally:
        try:
            client.logout()
        except Exception:
            pass
