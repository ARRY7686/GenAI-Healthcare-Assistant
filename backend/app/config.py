"""Runtime configuration.

Everything is overridable via env vars prefixed TRIAGE_ or a .env file. The app defaults to
the offline mock provider, so it runs with zero secrets.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRIAGE_", env_file=".env", extra="ignore")

    # --- LLM provider ---
    # "mock" -> deterministic offline provider (default; runs with zero secrets).
    # Real providers (anthropic/openai/gemini) are an optional follow-up.
    llm_provider: str = "mock"

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None

    # Pinned model per provider (no floating aliases). `model_id` overrides them all when set.
    model_id: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"
    openai_model: str = "gpt-4o"
    gemini_model: str = "gemini-2.0-flash"

    prompt_version: str = "v1"
    llm_timeout_seconds: float = 20.0
    llm_max_retries: int = 2

    # --- Adaptive questioning (feature #2) ---
    max_clarifying_turns: int = 6  # hard ceiling on clarifying questions per session

    # --- API ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    def resolve_model(self) -> str:
        """The model id for the active provider (explicit override wins)."""
        if self.model_id:
            return self.model_id
        return {
            "anthropic": self.anthropic_model,
            "openai": self.openai_model,
            "gemini": self.gemini_model,
        }.get(self.llm_provider, self.llm_provider)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
