"""Health / readiness endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.schemas import HealthResponse
from app.config import get_settings

router = APIRouter(tags=["meta"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Always returns 200 if the app is reachable."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        app_name=settings.app_name,
        components={
            "ollama_url": settings.ollama_url,
            "task1_backbone": settings.task1_backbone,
            "task2_reranker": settings.task2_reranker,
            "embedding_model": settings.embedding_model,
        },
    )
