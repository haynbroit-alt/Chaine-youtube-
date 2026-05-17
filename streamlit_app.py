from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from productivity_kit.csv_tools import summarize_csv
from productivity_kit.settings import get_settings
from productivity_kit.youtube import summarize_youtube

st.set_page_config(page_title="Kit productivité", layout="centered")

st.title("Kit productivité")
st.caption(
    "Interface simple : analysez un CSV ou résumez une vidéo YouTube à partir des sous-titres publics."
)

csv_tab, yt_tab = st.tabs(["Fichier CSV", "Vidéo YouTube"])

with csv_tab:
    st.markdown(
        "Déposez un fichier **.csv** encodé en **UTF-8**. Vous obtenez statistiques, aperçu et types de colonnes."
    )
    up = st.file_uploader("Fichier CSV", type=["csv"])
    if up is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(up.getvalue())
            path = Path(tmp.name)
        try:
            try:
                data = summarize_csv(path)
            except UnicodeDecodeError:
                st.error("Encodage non UTF-8 : ouvrez le fichier dans un tableur et exportez en UTF-8.")
            except Exception as e:
                st.error(f"Erreur : {e}")
            else:
                st.subheader("Résumé")
                c1, c2, c3 = st.columns(3)
                c1.metric("Lignes de données", data["row_count"])
                c2.metric("Colonnes", data["column_count"])
                c3.metric("Fichier", up.name[:40] + ("…" if len(up.name) > 40 else ""))
                if data.get("headers"):
                    st.markdown("**Colonnes** : " + ", ".join(f"`{h}`" for h in data["headers"]))
                if data.get("column_types_hint"):
                    st.json(data["column_types_hint"])
                if data.get("preview"):
                    st.dataframe(data["preview"], use_container_width=True)
                with st.expander("JSON complet"):
                    st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
        finally:
            path.unlink(missing_ok=True)

with yt_tab:
    st.markdown(
        "Collez une **URL YouTube**. Il faut des **sous-titres** (automatiques ou manuels) accessibles."
    )
    url = st.text_input("URL", placeholder="https://www.youtube.com/watch?v=…")
    tpl = st.selectbox(
        "Modèle de résumé",
        options=["court", "detaille", "decision"],
        format_func=lambda x: {
            "court": "Court (extraire les premières idées)",
            "detaille": "Détaillé (plus de phrases)",
            "decision": "Décision (structure conseillée avec IA)",
        }[x],
    )
    settings = get_settings()
    use_llm = st.checkbox(
        "Résumé avec OpenAI",
        value=False,
        help="Nécessite OPENAI_API_KEY dans l’environnement (fichier .env à côté du lancement).",
    )
    if use_llm and not settings.openai_api_key:
        st.warning(
            "OPENAI_API_KEY absente : le résumé IA ne fonctionnera pas. "
            "Copiez `.env.example` vers `.env` et renseignez la clé."
        )
    if st.button("Résumer", type="primary"):
        if not url.strip():
            st.warning("Collez d’abord une URL.")
        else:
            with st.spinner("Récupération des sous-titres…"):
                try:
                    out = summarize_youtube(
                        url.strip(),
                        tpl,
                        use_llm=use_llm,
                        openai_api_key=settings.openai_api_key or None,
                        openai_model=settings.openai_model,
                    )
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Erreur : {e}")
                else:
                    st.success("Terminé")
                    st.subheader("Résumé")
                    st.markdown(out["summary"])
                    st.caption(
                        f"Mode : **{out['mode']}** · transcription : **{out['transcript_char_count']}** caractères"
                    )
                    with st.expander("Aperçu de la transcription"):
                        st.text(out["transcript_preview"])
