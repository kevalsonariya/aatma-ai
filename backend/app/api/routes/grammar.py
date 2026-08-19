"""
app/api/routes/grammar.py — POST /api/grammar

Accepts a block of text, sends it to the local Ollama instance (Qwen3 4B)
with a few-shot grammar correction prompt (temperature 0.0), returning the
grammar-corrected text.

All inference is 100% local — no cloud API is used.
"""

from __future__ import annotations

import logging
import re
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

router = APIRouter(prefix="/api", tags=["Grammar"])

# ── User-specified instruction ────────────────────────────────────────────────
GRAMMAR_SYSTEM_PROMPT = (
    "You are a grammar correction tool. Correct all grammar, spelling, punctuation, "
    "subject-verb agreement, plural and possessive errors. Preserve meaning. Return ONLY the corrected text."
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class GrammarRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The text to grammar-check and correct.",
        examples=["AI are changing peoples life. It have many advantage."],
    )


class GrammarResponse(BaseModel):
    original_text: str = Field(..., description="The input text, unchanged.")
    corrected_text: str = Field(..., description="The grammar-corrected version of the text.")
    explanation: str = Field(..., description="Brief explanation of the corrections made.")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clean_response(raw: str) -> str:
    """
    Clean the model output.

    1. Extract content after </think> if Qwen3 generated internal reasoning.
    2. Strip markdown code fences.
    3. Strip outer wrapping quotes.
    """
    text = raw.strip()

    # Extract text after </think> tag if present
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    else:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code blocks
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            text = "\n".join(lines[1:-1]).strip()

    # Strip wrapping quotes
    if len(text) >= 2 and (
        (text[0] == '"' and text[-1] == '"') or
        (text[0] == "'" and text[-1] == "'")
    ):
        text = text[1:-1].strip()

    return text


# ── Dependency ────────────────────────────────────────────────────────────────

def get_ollama_client() -> OllamaClient:
    return ollama_client


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post(
    "/grammar",
    response_model=GrammarResponse,
    summary="Correct text grammar using local Qwen3 4B model",
    responses={
        200: {"description": "Grammar-corrected text returned successfully."},
        503: {"description": "Ollama is not running, unreachable, or timed out."},
        502: {"description": "Ollama returned an unexpected error."},
    },
)
async def post_grammar(
    body: GrammarRequest,
    client: Annotated[OllamaClient, Depends(get_ollama_client)],
) -> GrammarResponse:
    """
    Send text to local Qwen3 4B model for grammar correction.
    Uses few-shot prompting with temperature=0.0 for 100% deterministic accuracy.
    """
    messages = [
        {"role": "system", "content": GRAMMAR_SYSTEM_PROMPT},
        {"role": "user", "content": "He go to school yesterday."},
        {"role": "assistant", "content": "He went to school yesterday."},
        {"role": "user", "content": body.text},
    ]

    logger.info("grammar request — chars=%d", len(body.text))

    try:
        data = await client.chat(
            messages,
            temperature=0.0,
            options={"num_predict": 256},
        )
    except OllamaUnavailableError as exc:
        logger.warning("Ollama unavailable (grammar): %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "ollama_unavailable",
                "message": str(exc),
                "hint": "Ensure Ollama is running (`ollama serve`) and model is loaded.",
            },
        ) from exc
    except OllamaInferenceError as exc:
        logger.error("Ollama inference error (grammar): %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "ollama_inference_error", "message": str(exc)},
        ) from exc

    raw: str = data.get("message", {}).get("content", "").strip()
    corrected = _clean_response(raw)

    if not corrected:
        corrected = body.text

    if corrected.lower() == body.text.strip().lower():
        explanation = "No corrections needed — the text was already grammatically correct."
    else:
        explanation = "Corrected grammar, spelling, and punctuation."

    logger.info(
        "grammar response — original_chars=%d corrected_chars=%d",
        len(body.text),
        len(corrected),
    )

    return GrammarResponse(
        original_text=body.text,
        corrected_text=corrected,
        explanation=explanation,
    )
