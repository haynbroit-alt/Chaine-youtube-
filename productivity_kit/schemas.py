from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TemplateId = Literal["court", "detaille", "decision"]


class YoutubeSummarizeRequest(BaseModel):
    url: str = Field(..., description="URL ou identifiant (11 caractères) YouTube")
    template: TemplateId = Field(
        default="court",
        description="court, detaille ou decision (decision + IA recommandé)",
    )
    use_llm: bool = Field(
        default=False,
        description="Si true : OpenAI (OPENAI_API_KEY). Sinon résumé extractif gratuit.",
    )


class YoutubeBatchRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=50)
    template: TemplateId = "court"
    use_llm: bool = False
