from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from productivity_kit.csv_tools import summarize_csv
from productivity_kit.settings import get_settings
from productivity_kit.youtube import summarize_youtube

_LIBELLE_MODE: dict[str, str] = {
    "ia": "intelligence artificielle (OpenAI)",
    "automatique": "résumé automatique (texte seul)",
}

st.set_page_config(
    page_title="Kit productivité",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.title("Kit productivité")
st.caption(
    "Application en français : analysez un fichier CSV ou résumez une vidéo YouTube grâce aux sous-titres publics."
)

csv_tab, yt_tab = st.tabs(["Fichier CSV", "Vidéo YouTube"])

with csv_tab:
    st.markdown(
        "Déposez un fichier **.csv** enregistré en **UTF-8**. Vous verrez des statistiques, un aperçu des lignes "
        "et une estimation du type de chaque colonne."
    )
    up = st.file_uploader("Choisir un fichier CSV", type=["csv"])
    if up is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(up.getvalue())
            path = Path(tmp.name)
        try:
            try:
                data = summarize_csv(path)
            except UnicodeDecodeError:
                st.error(
                    "Encodage non reconnu comme UTF-8. Ouvrez le fichier dans un tableur et exportez-le au format UTF-8."
                )
            except Exception as e:
                st.error(f"Une erreur s’est produite : {e}")
            else:
                st.subheader("Résumé de l’analyse")
                c1, c2, c3 = st.columns(3)
                c1.metric("Lignes de données", data["row_count"])
                c2.metric("Nombre de colonnes", data["column_count"])
                c3.metric("Nom du fichier", up.name[:40] + ("…" if len(up.name) > 40 else ""))
                if data.get("headers"):
                    st.markdown("**Noms des colonnes** : " + ", ".join(f"`{h}`" for h in data["headers"]))
                if data.get("column_types_hint"):
                    st.markdown("**Types détectés (indicatif)**")
                    st.json(data["column_types_hint"])
                if data.get("preview"):
                    st.markdown("**Aperçu des premières lignes**")
                    st.dataframe(data["preview"], use_container_width=True)
                with st.expander("Voir toutes les données brutes (JSON)"):
                    st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")
        finally:
            path.unlink(missing_ok=True)

with yt_tab:
    st.markdown(
        "Collez l’**adresse complète** d’une vidéo YouTube. Il faut que des **sous-titres** "
        "(automatiques ou rédigés à la main) soient disponibles."
    )
    url = st.text_input("Adresse de la vidéo", placeholder="https://www.youtube.com/watch?v=…")
    tpl = st.selectbox(
        "Modèle de résumé",
        options=["court", "detaille", "decision"],
        format_func=lambda x: {
            "court": "Court — quelques idées principales",
            "detaille": "Détaillé — plus de phrases et de contexte",
            "decision": "Décision — structuré (mieux avec l’intelligence artificielle)",
        }[x],
    )
    settings = get_settings()
    use_llm = st.checkbox(
        "Utiliser l’intelligence artificielle (OpenAI)",
        value=False,
        help="Nécessite la variable d’environnement OPENAI_API_KEY (fichier .env à côté du lancement).",
    )
    if use_llm and not settings.openai_api_key:
        st.warning(
            "La clé OPENAI_API_KEY est absente : le résumé par intelligence artificielle ne pourra pas fonctionner. "
            "Copiez le fichier `.env.example` vers `.env` et renseignez votre clé."
        )
    if st.button("Lancer le résumé", type="primary"):
        if not url.strip():
            st.warning("Veuillez d’abord coller une adresse YouTube.")
        else:
            with st.spinner("Lecture des sous-titres en cours…"):
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
                    st.error(f"Une erreur s’est produite : {e}")
                else:
                    st.success("Résumé terminé.")
                    st.subheader("Texte du résumé")
                    st.markdown(out["summary"])
                    libelle = _LIBELLE_MODE.get(str(out["mode"]), str(out["mode"]))
                    st.caption(
                        f"Méthode utilisée : **{libelle}** — longueur de la transcription : "
                        f"**{out['transcript_char_count']}** caractères"
                    )
                    with st.expander("Aperçu du texte transcrit"):
                        st.text(out["transcript_preview"])
