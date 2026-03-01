"""NerveOS Configuration — all settings from environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────
    APP_NAME: str = "NerveOS"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    SECRET_KEY: str = "nerveos-secret-change-me-in-prod"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ─────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./nerveos.db"

    # ── LLM / OpenRouter (Grok) ─────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "x-ai/grok-3-mini-beta"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # ── SearXNG ──────────────────────────────────────────
    SEARXNG_URL: str = "http://localhost:8888"

    # ── Email (IMAP / SMTP) ──────────────────────────────
    IMAP_HOST: str = ""
    IMAP_PORT: int = 993
    IMAP_USER: str = ""
    IMAP_PASSWORD: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # ── Redis (for Celery / caching) ─────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Guardrails ───────────────────────────────────────
    AUTO_APPROVE_SAFE_ACTIONS: bool = False
    MAX_DEAL_VALUE_AUTO_APPROVE: float = 10000.0

    # ── Scheduler ────────────────────────────────────────
    MARKET_INTEL_CRON: str = "0 8 * * *"   # daily 8am
    EMAIL_CHECK_INTERVAL_SECONDS: int = 300  # 5 min
    DASHBOARD_REFRESH_SECONDS: int = 900     # 15 min

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
