from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables d’environnement (fichier `.env` optionnel)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Kit productivité"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: str = Field(
        default="",
        description="Origines CORS séparées par des virgules ; vide = désactivé",
    )

    imap_host: str = ""
    imap_user: str = ""
    imap_password: str = ""
    imap_folder: str = "INBOX"
    imap_ssl: bool = True
    imap_limit: int = 25
    imap_unseen_only: bool = False

    webhook_url: str = ""
    webhook_timeout_s: float = 15.0

    organize_folder: str = ""
    organize_on_digest: bool = False

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    streamlit_public_url: str = ""

    ollama_base_url: str = ""
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_s: float = 120.0

    @property
    def cors_origins_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if not raw:
            return []
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def imap_configured(self) -> bool:
        return bool(self.imap_host and self.imap_user and self.imap_password)

    @property
    def ollama_est_configure(self) -> bool:
        return bool(self.ollama_base_url.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
