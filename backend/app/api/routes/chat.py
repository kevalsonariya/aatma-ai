"""
app/api/routes/chat.py — POST /api/chat

Accepts a user message (and optional conversation history), forwards it to
the local Ollama instance running Qwen3 4B, and returns the model's reply.

No cloud API is involved — all inference runs on-device.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.services.ollama_client import (
    OllamaClient,
    OllamaInferenceError,
    OllamaUnavailableError,
    ollama_client,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Chat"])


# ── Request / Response schemas ─────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """A single turn in the conversation history."""
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    """Payload for POST /api/chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=8192,
        description="The user's question or prompt.",
        examples=["What is the capital of France?"],
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        description="Previous turns to include as conversation context.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (0 = deterministic, 1 = creative).",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=2048,
        description="Optional system prompt to prepend to the conversation.",
    )


class ChatResponse(BaseModel):
    """Response from POST /api/chat."""
    response: str = Field(..., description="The model's reply text.")
    model: str = Field(..., description="Ollama model tag that generated the reply.")
    prompt_tokens: int | None = Field(None, description="Tokens in the prompt (if reported).")
    completion_tokens: int | None = Field(None, description="Tokens in the completion (if reported).")
    done: bool = Field(True, description="Whether generation completed successfully.")


# ── Dependency ────────────────────────────────────────────────────────────────

def get_ollama_client() -> OllamaClient:
    """FastAPI dependency that yields the shared OllamaClient instance."""
    return ollama_client


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the local Aatma AI assistant",
    responses={
        200: {"description": "Model reply returned successfully."},
        503: {"description": "Ollama is not running or unreachable."},
        502: {"description": "Ollama returned an unexpected error."},
    },
)
async def post_chat(
    body: ChatRequest,
    client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> ChatResponse:
    """
    Forward a user message to the local Ollama instance (Qwen3 4B) and return
    the assistant's reply.

    - **message**: The user's natural-language question or instruction.
    - **history**: Optional prior turns for multi-turn conversations.
    - **temperature**: Controls response creativity (default 0.7).
    - **system_prompt**: Optional override of the system prompt.
    """

    # Build the messages list Ollama expects
    messages: list[dict[str, str]] = []

    if body.system_prompt:
        messages.append({"role": "system", "content": body.system_prompt})
    elif not body.history:
        # Default system prompt when starting a fresh conversation
        messages.append({
            "role": "system",
            "content": (
                "You are Aatma AI, a helpful offline AI assistant. "
                "Answer clearly and concisely. "
                "You run entirely on the user's device — no internet is used."
            ),
        })

    for turn in body.history:
        messages.append({"role": turn.role, "content": turn.content})

    messages.append({"role": "user", "content": body.message})

    logger.info(
        "chat request — turns=%d user_chars=%d temperature=%.2f",
        len(messages),
        len(body.message),
        body.temperature,
    )

    try:
        data = await client.chat(messages, temperature=body.temperature)
    except OllamaUnavailableError as exc:
        logger.warning("Ollama unavailable: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ollama_unavailable",
                "message": str(exc),
                "hint": "Ensure Ollama is running: `ollama serve`",
            },
        ) from exc
    except OllamaInferenceError as exc:
        logger.error("Ollama inference error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "ollama_inference_error",
                "message": str(exc),
            },
        ) from exc

    assistant_message = data.get("message", {})
    reply_text: str = assistant_message.get("content", "").strip()

    if not reply_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "empty_response",
                "message": "Ollama returned an empty reply. The model may still be loading.",
            },
        )

    return ChatResponse(
        response=reply_text,
        model=data.get("model", "unknown"),
        prompt_tokens=data.get("prompt_eval_count"),
        completion_tokens=data.get("eval_count"),
        done=data.get("done", True),
    )
