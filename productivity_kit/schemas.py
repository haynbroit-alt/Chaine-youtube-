from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TemplateId = Literal["court", "detaille", "decision"]


class YoutubeSummarizeRequest(BaseModel):
    url: str = Field(..., description="Adresse complète ou identifiant (11 caractères) de la vidéo YouTube")
    template: TemplateId = Field(
        default="court",
        description="Modèle : « court », « detaille » ou « decision » (ce dernier est meilleur avec l’IA)",
    )
    use_llm: bool = Field(
        default=False,
        description=(
            "Si vrai : résumé par modèle de langage. Priorité : OPENAI_API_KEY si présente, "
            "sinon serveur **Ollama** (OLLAMA_BASE_URL, ex. http://127.0.0.1:11434). Sinon : résumé automatique gratuit."
        ),
    )


class YoutubeBatchRequest(BaseModel):
    urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Liste d’adresses YouTube à traiter l’une après l’autre",
    )
    template: TemplateId = Field(default="court", description="Modèle de résumé pour toutes les vidéos")
    use_llm: bool = Field(
        default=False,
        description="Même logique que pour une seule vidéo : OpenAI en priorité, sinon Ollama si configuré.",
    )
