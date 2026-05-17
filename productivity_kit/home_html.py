from __future__ import annotations

import html


def landing_page_html(*, streamlit_url: str | None) -> str:
    """Page d’accueil HTML minimaliste (UTF-8)."""
    extra = ""
    if streamlit_url and streamlit_url.startswith(("http://", "https://")):
        safe = html.escape(streamlit_url, quote=True)
        extra = (
            f'<p class="links"><a href="{safe}">Interface graphique (Streamlit)</a></p>'
        )
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Kit productivité</title>
  <style>
    body {{
      font-family: system-ui, sans-serif;
      max-width: 40rem;
      margin: 2rem auto;
      padding: 0 1rem;
      line-height: 1.5;
      color: #111;
      background: #fafafa;
    }}
    .card {{
      background: #fff;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 1px 3px rgba(0,0,0,.08);
    }}
    a {{ color: #2563eb; }}
    .links a {{ margin-right: 1rem; }}
    code {{ background: #eee; padding: .1rem .35rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Kit productivité</h1>
    <p>
      API pour <strong>résumer des vidéos YouTube</strong> (sous-titres) et
      <strong>analyser des CSV</strong>, plus digest e-mail / webhooks.
      Démarrez par la documentation interactive ou lancez Streamlit en local.
    </p>
    {extra}
    <p class="links">
      <a href="/docs">Documentation API (Swagger)</a>
      <a href="/redoc">ReDoc</a>
      <a href="/health">Santé</a>
    </p>
    <p><small>Endpoints utiles : <code>POST /youtube/summarize</code>,
    <code>POST /csv/batch-summary</code>, <code>POST /csv/summary</code></small></p>
  </div>
</body>
</html>
"""
