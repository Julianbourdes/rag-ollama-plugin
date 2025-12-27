"""Health check endpoints."""

from fastapi import APIRouter
from app.services.ollama_service import get_ollama_service
from app.services.qdrant_service import get_qdrant_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health():
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/ready")
async def ready():
    """Readiness check - verifies all services are available."""
    ollama = get_ollama_service()
    qdrant = get_qdrant_service()

    ollama_ok = await ollama.health_check()
    qdrant_ok = await qdrant.health_check()

    status = "ready" if (ollama_ok and qdrant_ok) else "degraded"

    return {
        "status": status,
        "services": {
            "ollama": "up" if ollama_ok else "down",
            "qdrant": "up" if qdrant_ok else "down"
        }
    }


@router.get("/live")
async def live():
    """Liveness check - just confirms the app is running."""
    return {"status": "alive"}
