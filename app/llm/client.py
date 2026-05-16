"""Unified LLM client.

One interface — `LLMClient.complete(...)` — that dispatches to Anthropic, OpenAI,
or Ollama based on a `"provider:model"` spec string. This lets us swap backbones
via env var (e.g. `TASK1_BACKBONE=ollama:naija-reviewer-8b`) without code changes.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Raised when an LLM call fails after retries / fallbacks."""


class LLMClient:
    """Provider-agnostic completion client.

    Spec format: `"provider:model-id"` — e.g.:
        anthropic:claude-sonnet-4-20250514
        openai:gpt-4o
        ollama:llama3.1:8b-instruct
        ollama:naija-reviewer-8b
    """

    def __init__(self, spec: str) -> None:
        self.spec = spec
        self.provider, self.model = spec.split(":", 1)
        self.settings = get_settings()

    # ----------------------------- public ------------------------------ #

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        stop: list[str] | None = None,
    ) -> str:
        """Return the LLM's completion as a single string."""
        if self.provider == "anthropic":
            return await self._anthropic(prompt, system, max_tokens, temperature, stop)
        if self.provider == "openai":
            return await self._openai(prompt, system, max_tokens, temperature, stop)
        if self.provider == "ollama":
            return await self._ollama(prompt, system, max_tokens, temperature, stop)
        if self.provider == "nvidia":
            return await self._nvidia(prompt, system, max_tokens, temperature, stop)
        raise LLMError(f"Unknown provider: {self.provider}")

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        """Like `complete`, but parses the response as JSON. Strips code fences."""
        raw = await self.complete(prompt, system, max_tokens, temperature)
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[len("json") :]
            text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise LLMError(f"Model returned non-JSON: {raw[:200]}") from exc

    # ----------------------------- private ----------------------------- #

    async def _anthropic(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        if not self.settings.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY not set")

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            payload["system"] = system
        if stop:
            payload["stop_sequences"] = stop

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.settings.anthropic_api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                raise LLMError(f"Anthropic API {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            return data["content"][0]["text"]

    async def _openai(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        if not self.settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY not set")

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                raise LLMError(f"OpenAI API {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _ollama(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }
        if system:
            payload["system"] = system
        if stop:
            payload["options"]["stop"] = stop

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.settings.ollama_url}/api/generate",
                json=payload,
            )
            if resp.status_code != 200:
                raise LLMError(f"Ollama {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            return data["response"]

    async def _nvidia(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        """NVIDIA NIM / NeMo Data Designer endpoint (OpenAI-compatible).

        Default endpoint: integrate.api.nvidia.com (build.nvidia.com hosted models).
        Override via `NVIDIA_BASE_URL` env var for self-hosted NIM or
        NeMo Microservices deployments.
        """
        if not self.settings.nvidia_api_key:
            raise LLMError("NVIDIA_API_KEY not set")

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.settings.nvidia_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.nvidia_api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                raise LLMError(f"NVIDIA NIM {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ----------------------------- embeddings -------------------------- #

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed `texts`. Only supported on OpenAI (text-embedding-3-small)."""
        if self.provider != "openai":
            raise LLMError("embed() only supported on openai provider for now")
        if not self.settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY not set")

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.settings.openai_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": self.model, "input": texts},
            )
            if resp.status_code != 200:
                raise LLMError(f"OpenAI embed {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            return [item["embedding"] for item in data["data"]]


# --------------------------------------------------------------------------- #
# Convenience accessor                                                         #
# --------------------------------------------------------------------------- #


_cache: dict[str, LLMClient] = {}


def get_llm_client(spec: str | None = None) -> LLMClient:
    """Return a cached LLMClient for the given `provider:model` spec.

    If `spec` is None, defaults to the Task-1 backbone from settings.
    """
    if spec is None:
        spec = get_settings().task1_backbone
    if spec not in _cache:
        _cache[spec] = LLMClient(spec)
    return _cache[spec]
