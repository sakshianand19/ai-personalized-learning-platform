import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEV_SECRET_KEY = "dev-only-insecure-secret-change-me"


def _default_database_url() -> str:
    # Vercel's filesystem is read-only except for /tmp.
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/learning.db"
    return "sqlite:///./learning.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AI-Powered Personalized Learning Platform"
    database_url: str = Field(default_factory=_default_database_url)
    seed_demo_data: bool = True

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_api_version: str = "2024-10-21"
    azure_openai_deployment: str | None = None
    llm_temperature: float = 0.2
    llm_timeout_seconds: float = 30.0

    # Signs session tokens. Set a long random value in production; every instance must share it.
    secret_key: str = DEV_SECRET_KEY
    session_hours: int = 8

    # A topic whose mastery is below this threshold is reported as a learning gap.
    mastery_threshold: float = 0.6
    # Minimum answered questions on a topic before it can be judged a gap.
    min_attempts_for_gap: int = 2

    @property
    def azure_openai_configured(self) -> bool:
        return all(
            [self.azure_openai_endpoint, self.azure_openai_api_key, self.azure_openai_deployment]
        )

    @property
    def sqlalchemy_url(self) -> str:
        # Hosted Postgres providers (Neon, Supabase, Vercel Postgres) hand out postgres:// URLs.
        url = self.database_url
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix) :]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
