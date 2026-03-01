"""Settings / health API routes."""

from fastapi import APIRouter
from services.searxng import searxng_service
from config import settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("/health")
async def health_check():
    searxng_ok = await searxng_service.health_check()
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "services": {
            "searxng": searxng_ok,
            "ollama": settings.OLLAMA_BASE_URL,
            "database": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgres",
        },
    }


@router.get("/config")
async def get_config():
    """Return non-sensitive config."""
    return {
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "ollama_model": settings.OLLAMA_MODEL,
        "auto_approve_safe": settings.AUTO_APPROVE_SAFE_ACTIONS,
        "market_intel_cron": settings.MARKET_INTEL_CRON,
        "email_check_interval": settings.EMAIL_CHECK_INTERVAL_SECONDS,
    }
