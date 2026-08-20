"""
app/core/config.py — Application Settings

Uses pydantic-settings to load configuration from environment variables
(and optionally a .env file). All defaults are safe for local development.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Aatma AI"
    """Human-readable name of the assistant."""

    # ── Ollama ────────────────────────────────────────────────────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    """Base URL of the locally running Ollama server."""

    MODEL_NAME: str = "qwen3:8b"
    """Ollama model tag to use for inference."""

    # ── Server ────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    """Allowed origins for CORS. Add your production domain here when ready."""

    API_PREFIX: str = "/api"
    """Global prefix for all API routes."""


# Singleton instance — import this throughout the app
settings = Settings()

