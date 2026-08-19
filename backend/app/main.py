"""
Aatma AI Backend — FastAPI Entry Point

Creates the FastAPI application, manages the OllamaClient lifecycle via
a lifespan context manager, registers CORS middleware, and mounts all routers.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.services.ollama_client import ollama_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the Ollama HTTP client on startup and cleanly close it on shutdown."""
    logger.info("Aatma AI backend starting up…")
    await ollama_client.start()

    reachable, msg = await ollama_client.ping()
    if reachable:
        logger.info("Ollama is reachable — %s (model: %s)", msg, settings.MODEL_NAME)
    else:
        logger.warning(
            "Ollama is NOT reachable at startup (%s). "
            "Chat endpoints will return 503 until Ollama is available.",
            msg,
        )

    yield  # app runs here

    logger.info("Aatma AI backend shutting down…")
    await ollama_client.stop()


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="Aatma AI API",
    description=(
        "Offline AI assistant backend — 100%% on-device inference "
        "via Ollama + Qwen3 4B. No cloud API is used."
    ),
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.routes import chat, health, grammar  # noqa: E402 — imported after app is created

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(grammar.router)


# ── Backward-compatible bare /health ─────────────────────────────────────────
# The original scaffold exposed GET /health (no /api prefix).
# This route is kept so existing clients don't break while /api/health
# continues to serve the richer structured response.
@app.get("/health", tags=["System"], include_in_schema=True)
async def health_simple() -> dict:
    """Simple liveness probe — always returns 200 {"status": "ok"} if the server is up."""
    return {"status": "ok"}


logger.info("Routes registered: /health, /api/health, /api/chat, /api/grammar")


