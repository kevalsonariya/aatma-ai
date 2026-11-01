"""
app/api/routes/grammar.py — POST /api/grammar

Accepts a block of text, sends it to the local Ollama instance (Qwen3 4B)
with a few-shot grammar correction prompt (temperature 0.0), returning the
grammar-corrected text.

All inference is 100% local — no cloud API is used.
"""

from __future__ import annotations

import json
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
    "You are an English grammar correction assistant. "
    "Correct all grammar, spelling, capitalization, and punctuation errors while preserving the original meaning. "
    "Return ONLY a valid JSON object with exactly two keys: 'corrected_text' and 'explanation'. "
    "In 'explanation', briefly describe the changes made. "
    "If the text is already grammatically correct, return the original text as 'corrected_text' and 'No corrections needed.' as 'explanation'."
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

def _parse_grammar_response(raw: str, original_text: str) -> tuple[str, str]:
    """
    Parse the model's response into (corrected_text, explanation).
    Handles reasoning blocks, markdown fences, and JSON payloads with graceful fallbacks.
    """
    text = raw.strip()

    # Extract text after </think> tag if present
    if "</think>" in text:
        text = text.split("</think>")[-1].strip()
    else:
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code blocks (e.g. ```json ... ```)
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            if lines[-1].strip() == "```":
                text = "\n".join(lines[1:-1]).strip()
            else:
                text = "\n".join(lines[1:]).strip()

    # Try parsing direct JSON
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "corrected_text" in data:
            corrected = str(data["corrected_text"]).strip()
            explanation = str(data.get("explanation", "")).strip()
            if not explanation:
                explanation = (
                    "No corrections needed."
                    if corrected.lower() == original_text.strip().lower()
                    else "Corrected grammar, spelling, and punctuation."
                )
            return corrected, explanation
    except Exception:
        pass

    # Regex extraction fallback for JSON fields
    match_corr = re.search(r'"corrected_text"\s*:\s*"([^"]+)"', text)
    match_exp = re.search(r'"explanation"\s*:\s*"([^"]+)"', text)
    if match_corr:
        corrected = match_corr.group(1).strip()
        explanation = (
            match_exp.group(1).strip()
            if match_exp
            else ("No corrections needed." if corrected.lower() == original_text.strip().lower() else "Corrected grammar, spelling, and punctuation.")
        )
        return corrected, explanation

    # Fallback to plain text if JSON parsing fails
    if text:
        cleaned = text.strip().strip('"\'')
        explanation = (
            "No corrections needed."
            if cleaned.lower() == original_text.strip().lower()
            else "Corrected grammar, spelling, and punctuation."
        )
        return cleaned, explanation

    return original_text, "No corrections needed."


# ── Dependency ────────────────────────────────────────────────────────────────

def get_ollama_client() -> OllamaClient:
    return ollama_client


# ── Route ─────────────────────────────────────────────────────────────────────

@router.post(
    "/grammar",
    response_model=GrammarResponse,
    summary="Correct text grammar using local Ollama model",
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
    Send text to local Ollama model for grammar correction.
    Uses JSON instruction prompting with temperature=0.0.
    """
    messages = [
        {"role": "system", "content": GRAMMAR_SYSTEM_PROMPT},
        {"role": "user", "content": body.text},
    ]

    logger.info("grammar request — chars=%d", len(body.text))

    try:
        data = await client.chat(
            messages,
            temperature=0.0,
            options={"num_predict": 1024},
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
    corrected, explanation = _parse_grammar_response(raw, body.text)

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
