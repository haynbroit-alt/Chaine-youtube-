from __future__ import annotations

from typing import Any

import httpx


def post_json_webhook(
    url: str,
    payload: dict[str, Any],
    *,
    timeout_s: float = 15.0,
) -> tuple[int, str]:
    """Envoie un POST JSON ; renvoie (code_http, corps_texte_court)."""
    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, json=payload)
        text = (r.text or "")[:2000]
        return r.status_code, text
