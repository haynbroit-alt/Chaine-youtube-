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
        description="Si vrai : résumé par intelligence artificielle (clé OPENAI_API_KEY requise). Sinon : résumé automatique gratuit à partir du texte",
    )


class YoutubeBatchRequest(BaseModel):
    urls: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Liste d’adresses YouTube à traiter l’une après l’autre",
    )
    template: TemplateId = Field(default="court", description="Modèle de résumé pour toutes les vidéos")
    use_llm: bool = Field(default=False, description="Utiliser l’IA OpenAI pour chaque vidéo")
