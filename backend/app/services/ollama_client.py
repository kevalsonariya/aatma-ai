"""
app/services/ollama_client.py — Ollama HTTP Client

Async HTTP client that communicates with the locally running Ollama server.
All inference stays 100% on-device; no cloud API is used.

Public Interface:
    client = OllamaClient()
    await client.start()                   # call once at startup
    result = await client.chat(messages)   # blocking (non-streaming) inference
    ok, info = await client.ping()         # liveness check
    models = await client.list_models()    # list locally pulled models
    await client.stop()                    # call once at shutdown
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Exceptions ────────────────────────────────────────────────────────────────

class OllamaUnavailableError(RuntimeError):
    """Raised when the Ollama server cannot be reached."""


class OllamaInferenceError(RuntimeError):
    """Raised when Ollama returns an unexpected or error response."""


# ── Client ────────────────────────────────────────────────────────────────────

class OllamaClient:
    """
    Async HTTP client for the Ollama REST API.

    Lifecycle:
        - Call `start()` once at application startup (e.g. FastAPI lifespan).
        - Call `stop()` once at application shutdown.
        - All other methods require the client to be started.

    Reference: https://github.com/ollama/ollama/blob/main/docs/api.md
    """

    def __init__(self) -> None:
        self._base_url: str = settings.OLLAMA_BASE_URL
        self._model: str = settings.MODEL_NAME
        self._client: httpx.AsyncClient | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Initialise the underlying HTTP client. Call once at app startup."""
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(
                connect=5.0,   # fail fast if Ollama is not running
                read=120.0,    # Qwen3 4B can be slow on first token
                write=10.0,
                pool=5.0,
            ),
        )
        logger.info("OllamaClient started — base_url=%s model=%s", self._base_url, self._model)

    async def stop(self) -> None:
        """Close the HTTP client. Call once at app shutdown."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("OllamaClient stopped.")

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("OllamaClient.start() has not been called.")
        return self._client

    # ── Public API ─────────────────────────────────────────────────────────────

    async def chat(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.7,
        options: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        """
        Send a chat completion request to Ollama.

        Args:
            messages:    List of {"role": "user"|"assistant"|"system", "content": str}.
            temperature: Sampling temperature (0.0 – 1.0).
            options:     Additional Ollama options (e.g. {"num_predict": 512}).
            stream:      If True, Ollama streams chunks — not yet supported here.

        Returns:
            Parsed Ollama /api/chat JSON response dict.

        Raises:
            OllamaUnavailableError: If the Ollama server is unreachable.
            OllamaInferenceError:   If Ollama returns a non-200 status or error body.
        """
        client = self._require_client()
        opts: dict[str, Any] = {"temperature": temperature}
        if options:
            opts.update(options)

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": stream,
            "options": opts,
        }

        try:
            response = await client.post("/api/chat", json=payload)
        except httpx.ConnectError as exc:
            raise OllamaUnavailableError(
                f"Cannot connect to Ollama at {self._base_url}. "
                "Make sure Ollama is installed and running (`ollama serve`)."
            ) from exc
        except httpx.TimeoutException as exc:
            raise OllamaUnavailableError(
                f"Ollama request timed out after 120 s. "
                "The model may still be loading — try again shortly."
            ) from exc

        if response.status_code != 200:
            raise OllamaInferenceError(
                f"Ollama returned HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()

        if "error" in data:
            raise OllamaInferenceError(f"Ollama error: {data['error']}")

        logger.debug(
            "chat completed — model=%s prompt_tokens=%s eval_tokens=%s",
            data.get("model"),
            data.get("prompt_eval_count"),
            data.get("eval_count"),
        )
        return data

    async def ping(self) -> tuple[bool, str]:
        """Check whether the Ollama server is reachable."""
        client = self._require_client()
        try:
            resp = await client.get("/", timeout=4.0)
            if resp.status_code == 200:
                return True, resp.text.strip()
            return False, f"unexpected status {resp.status_code}"
        except httpx.ConnectError:
            return False, f"cannot connect to {self._base_url}"
        except httpx.TimeoutException:
            return False, "connection timed out"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    async def list_models(self) -> list[str]:
        """Return tag names of all models pulled locally in Ollama."""
        client = self._require_client()
        try:
            resp = await client.get("/api/tags", timeout=8.0)
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise OllamaUnavailableError(str(exc)) from exc

        if resp.status_code != 200:
            raise OllamaInferenceError(f"Ollama /api/tags returned {resp.status_code}")

        data = resp.json()
        return [m["name"] for m in data.get("models", [])]


# ── Module-level singleton (initialised during FastAPI lifespan) ──────────────
ollama_client = OllamaClient()
