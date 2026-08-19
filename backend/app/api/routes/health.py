"""
app/api/routes/health.py — GET /api/health

Reports the operational status of both the FastAPI backend and the
locally running Ollama instance (Qwen3 4B).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.services.ollama_client import OllamaClient, ollama_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Health"])


# ── Response schema ────────────────────────────────────────────────────────────

OllamaStatus = Literal["ok", "unavailable"]


class OllamaInfo(BaseModel):
    status: OllamaStatus
    url: str
    message: str


class HealthResponse(BaseModel):
    backend: Literal["ok"] = "ok"
    ollama: OllamaInfo
    model: str
    timestamp: str


# ── Dependency ────────────────────────────────────────────────────────────────

def get_ollama_client() -> OllamaClient:
    return ollama_client


# ── Route ─────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Backend and Ollama liveness check",
    responses={
        200: {"description": "Health status (backend is always ok if this endpoint responds; check ollama.status for Ollama)."},
    },
)
async def get_health(
    client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> HealthResponse:
    """
    Returns the operational status of the backend and Ollama.

    The `backend` field is always `"ok"` (the server is running if you can
    reach this endpoint). The `ollama` field reflects whether the local
    Ollama daemon is reachable and the configured model is available.
    """
    ollama_reachable, ollama_message = await client.ping()

    return HealthResponse(
        ollama=OllamaInfo(
            status="ok" if ollama_reachable else "unavailable",
            url=settings.OLLAMA_BASE_URL,
            message=ollama_message,
        ),
        model=settings.MODEL_NAME,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get(
    "/model-status",
    response_model=HealthResponse,
    summary="Model status check",
    include_in_schema=True,
)
async def get_model_status(
    client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> HealthResponse:
    """Alias for /api/health returning Ollama and model status."""
    return await get_health(client)

