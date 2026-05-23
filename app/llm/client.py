"""Unified LLM client.

One interface — `LLMClient.complete(...)` — that dispatches to Anthropic, OpenAI,
or Ollama based on a `"provider:model"` spec string. This lets us swap backbones
via env var (e.g. `TASK1_BACKBONE=ollama:naija-reviewer-8b`) without code changes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Raised when an LLM call fails after retries / fallbacks."""


# --------------------------------------------------------------------------- #
# JSON parsing helpers — used by complete_json()                                #
# --------------------------------------------------------------------------- #

import re as _re


def _extract_json(text: str) -> dict | None:
    """Try to extract a JSON object from messy LLM output.

    Strategy:
      1. Strip leading prose like "Here is the JSON:" or "Output:"
      2. Strip any ```json … ``` or ``` … ``` code fences
      3. Find the outermost {...} block via balanced-brace scan
      4. json.loads
    Returns None if no JSON found (caller tries repair next).
    """
    if not text:
        return None
    # Remove fenced blocks first (most common case): pull the LARGEST inner span
    fence_re = _re.compile(r"```(?:json|JSON)?\s*(.*?)\s*```", _re.DOTALL)
    m = fence_re.search(text)
    if m:
        candidate = m.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    # Find the outermost { ... } by balanced-brace scan
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _repair_truncated_json(text: str) -> dict | None:
    """Best-effort repair when the model ran out of tokens mid-JSON.

    Strategy: walk forward, track bracket/quote state, then close any
    unclosed strings/arrays/objects to make valid JSON.
    """
    if not text:
        return None
    # Find the start of JSON
    src = text
    # Strip leading fence/prose
    m = _re.search(r"```(?:json|JSON)?\s*", src)
    if m:
        src = src[m.end():]
    start = src.find("{")
    if start == -1:
        return None
    src = src[start:]
    # Strip trailing fence if present
    if "```" in src:
        src = src.split("```", 1)[0]

    # Walk forward to figure out close-state at end of input
    depth_obj = 0
    depth_arr = 0
    in_string = False
    escape = False
    last_complete_pos = 0  # position after the last complete top-level item
    for i, ch in enumerate(src):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth_obj += 1
        elif ch == "}":
            depth_obj -= 1
        elif ch == "[":
            depth_arr += 1
        elif ch == "]":
            depth_arr -= 1
        elif ch == "," and depth_obj == 1 and depth_arr <= 1:
            last_complete_pos = i

    # If we have at least one complete top-level entry, truncate to it + close.
    # `last_complete_pos` points at a comma between complete array entries,
    # so by construction we are NOT inside a string at that point. We close
    # whatever brackets remain net-open.
    if last_complete_pos > 0:
        candidate = src[:last_complete_pos]
        depth_obj = candidate.count("{") - candidate.count("}")
        depth_arr = candidate.count("[") - candidate.count("]")
        # Close arrays before objects (inner-most first)
        candidate += "]" * max(0, depth_arr) + "}" * max(0, depth_obj)
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None


# 429 rate-limit handling: retry up to N times with exponential backoff + jitter
_RETRY_MAX = 6
_RETRY_BASE = 4.0  # seconds


async def _retry_on_429(do_request, *, attempt_label: str = "request") -> httpx.Response:
    """Call do_request() async until it returns non-429 or retries exhausted."""
    for attempt in range(_RETRY_MAX):
        resp = await do_request()
        if resp.status_code != 429:
            return resp
        if attempt < _RETRY_MAX - 1:
            sleep_for = _RETRY_BASE * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(
                "%s rate-limited (429); backing off %.1fs (attempt %d/%d)",
                attempt_label, sleep_for, attempt + 1, _RETRY_MAX,
            )
            await asyncio.sleep(sleep_for)
    return resp  # last 429, caller decides what to do


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
        try:
            if self.provider == "anthropic":
                return await self._anthropic(prompt, system, max_tokens, temperature, stop)
            if self.provider == "openai":
                return await self._openai(prompt, system, max_tokens, temperature, stop)
            if self.provider == "freemodel":
                return await self._freemodel(prompt, system, max_tokens, temperature, stop)
            if self.provider == "modal":
                return await self._modal(prompt, system, max_tokens, temperature, stop)
            if self.provider == "ollama":
                return await self._ollama(prompt, system, max_tokens, temperature, stop)
            if self.provider == "nvidia":
                return await self._nvidia(prompt, system, max_tokens, temperature, stop)
            if self.provider == "lmstudio":
                return await self._lmstudio(prompt, system, max_tokens, temperature, stop)
            if self.provider in ("ollama-cloud", "ollamacloud", "ocloud"):
                return await self._ollama_cloud(prompt, system, max_tokens, temperature, stop)
            if self.provider in ("hf", "huggingface", "hf-inference"):
                return await self._hf_inference(prompt, system, max_tokens, temperature, stop)
            raise LLMError(f"Unknown provider: {self.provider}")
        except httpx.ConnectError as exc:
            raise LLMError(
                f"{self.provider}:{self.model} unreachable — {exc}"
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMError(
                f"{self.provider}:{self.model} timed out — {exc}"
            ) from exc

    async def complete_json(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.4,
    ) -> dict[str, Any]:
        """Like `complete`, but parses the response as JSON.

        Bulletproofed against:
          - markdown code fences (```json ... ``` or ``` ... ```) anywhere in output
          - leading/trailing prose ("Here is the JSON: { ... }")
          - truncated outputs (hit max_tokens mid-JSON) → best-effort repair
        """
        raw = await self.complete(prompt, system, max_tokens, temperature)
        text = (raw or "").strip()

        parsed = _extract_json(text)
        if parsed is not None:
            return parsed

        # Last-ditch: try to repair a truncated JSON tail by closing brackets
        repaired = _repair_truncated_json(text)
        if repaired is not None:
            logger.warning("complete_json: had to repair truncated JSON (output was likely hit by max_tokens limit)")
            return repaired

        raise LLMError(f"Model returned non-JSON: {raw[:300]}")

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
            async def _do():
                return await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.settings.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json=payload,
                )
            resp = await _retry_on_429(_do, attempt_label=f"anthropic:{self.model}")
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

        # GPT-5 / o1 / o3 series use `max_completion_tokens` and do not accept
        # `temperature`. Detect by model name prefix and adapt.
        is_reasoning_model = (
            self.model.startswith("gpt-5")
            or self.model.startswith("o1")
            or self.model.startswith("o3")
        )
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if is_reasoning_model:
            payload["max_completion_tokens"] = max_tokens
            # temperature defaults to 1.0 on these and is non-tunable
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature
        if stop:
            payload["stop"] = stop

        # Honour OPENAI_BASE_URL for freemodel.dev / Azure-OpenAI / etc.
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
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

    async def _freemodel(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        """freemodel.dev — OpenAI-compatible gateway. Uses its own API key
        (FREE_MODEL_API_KEY) and base URL. Same chat/completions wire format
        as OpenAI, including the GPT-5/reasoning-model token-budget split."""
        if not self.settings.freemodel_api_key:
            raise LLMError("FREE_MODEL_API_KEY not set")
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        is_reasoning_model = (
            self.model.startswith("gpt-5")
            or self.model.startswith("o1")
            or self.model.startswith("o3")
        )
        payload: dict[str, Any] = {"model": self.model, "messages": messages}
        if is_reasoning_model:
            payload["max_completion_tokens"] = max_tokens
        else:
            payload["max_tokens"] = max_tokens
            payload["temperature"] = temperature
        if stop:
            payload["stop"] = stop

        base_url = self.settings.freemodel_base_url.rstrip("/")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.freemodel_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                raise LLMError(f"freemodel.dev {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def _modal(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        """Modal-hosted NaijaReviewer-8B (GGUF on a serverless L4).

        OpenAI-compatible /v1/chat/completions, open endpoint (no real auth).
        Set MODAL_BASE_URL in .env (must end in /v1). First call after idle
        includes a cold start (model load), so the timeout is generous.
        """
        if not self.settings.modal_base_url:
            raise LLMError("MODAL_BASE_URL not set")
        base_url = self.settings.modal_base_url.rstrip("/")

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if stop:
            payload["stop"] = stop

        # Generous timeout: cold start downloads/loads the model on first hit.
        async with httpx.AsyncClient(timeout=300.0) as client:
            async def _do():
                return await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.modal_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            resp = await _retry_on_429(_do, attempt_label=f"modal:{self.model}")
            if resp.status_code != 200:
                raise LLMError(f"Modal {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise LLMError(f"Modal response shape unexpected: {str(data)[:200]}")

    async def _lmstudio(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        """LM Studio's OpenAI-compatible local server (default localhost:1234)."""
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

        async with httpx.AsyncClient(timeout=300.0) as client:
            async def _do():
                return await client.post(
                    f"{self.settings.lm_studio_url}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
            resp = await _retry_on_429(_do, attempt_label=f"lmstudio:{self.model}")
            if resp.status_code != 200:
                raise LLMError(f"LM Studio {resp.status_code}: {resp.text[:300]}")
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
            async def _do():
                return await client.post(
                    f"{self.settings.nvidia_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.nvidia_api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=payload,
                )
            resp = await _retry_on_429(_do, attempt_label=f"nvidia:{self.model}")
            if resp.status_code != 200:
                raise LLMError(f"NVIDIA NIM {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ----------------------------- embeddings -------------------------- #

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed `texts`. Supports openai and local sentence-transformers.

        Spec formats:
          - "openai:text-embedding-3-small"           → 1536-dim, requires OPENAI_API_KEY
          - "local:paraphrase-MiniLM-L6-v2"           → 384-dim, free, runs on CPU
          - "sentence-transformers:<any HF model>"    → same as local:
        """
        if self.provider in ("local", "sentence-transformers", "st"):
            return await self._embed_local(texts)
        if self.provider == "openai":
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
        raise LLMError(f"embed() not supported for provider '{self.provider}'")

    # Sentence-transformers model is cached at the module level to avoid
    # reloading the 80MB checkpoint for every query.
    _ST_CACHE: dict[str, Any] = {}

    async def _ollama_cloud(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        """Ollama Cloud — hosted open-weight models (Llama 3.3 70B, Qwen 2.5 72B,
        DeepSeek-V3, etc.) via OpenAI-compatible API.

        Endpoint defaults to https://ollama.com/v1 ; override via
        OLLAMA_CLOUD_BASE_URL env var. Requires OLLAMA_API_KEY.

        Spec examples:
            ollama-cloud:llama3.3:70b
            ollama-cloud:qwen2.5:72b-instruct
            ollama-cloud:deepseek-v3.1:671b
        """
        api_key = os.getenv("OLLAMA_API_KEY") or os.getenv("OLLAMA_CLOUD_API_KEY")
        if not api_key:
            raise LLMError("OLLAMA_API_KEY not set (Ollama Cloud)")
        base_url = os.getenv("OLLAMA_CLOUD_BASE_URL", "https://ollama.com/v1").rstrip("/")

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient(timeout=180.0) as client:
            async def _do():
                return await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            resp = await _retry_on_429(_do, attempt_label=f"ollama-cloud:{self.model}")
            if resp.status_code != 200:
                raise LLMError(f"Ollama Cloud {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise LLMError(f"Ollama Cloud response shape unexpected: {str(data)[:200]}")

    async def _hf_inference(
        self,
        prompt: str,
        system: str | None,
        max_tokens: int,
        temperature: float,
        stop: list[str] | None,
    ) -> str:
        """HuggingFace Inference (router) — open-weight models hosted by HF.

        Endpoint: https://router.huggingface.co/v1/chat/completions
                  (OpenAI-compatible router, auto-routes to whichever provider
                  serves the model).

        Spec examples:
            hf:meta-llama/Llama-3.3-70B-Instruct
            hf:Qwen/Qwen2.5-72B-Instruct
            hf:mistralai/Mixtral-8x7B-Instruct-v0.1
            hf:HuggingFaceH4/zephyr-7b-beta
        """
        hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            raise LLMError("HF_TOKEN not set")
        base_url = os.getenv("HF_INFERENCE_BASE_URL",
                             "https://router.huggingface.co/v1").rstrip("/")

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if stop:
            payload["stop"] = stop

        async with httpx.AsyncClient(timeout=180.0) as client:
            async def _do():
                return await client.post(
                    f"{base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {hf_token}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            resp = await _retry_on_429(_do, attempt_label=f"hf:{self.model}")
            if resp.status_code != 200:
                raise LLMError(f"HF Inference {resp.status_code}: {resp.text[:300]}")
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError):
                raise LLMError(f"HF Inference response shape unexpected: {str(data)[:200]}")

    async def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """Run sentence-transformers in a worker thread (synchronous library)."""
        model_id = self.model or "paraphrase-MiniLM-L6-v2"
        if model_id not in self._ST_CACHE:
            from sentence_transformers import SentenceTransformer
            logger.info("loading sentence-transformers model %s (one-time)", model_id)
            self._ST_CACHE[model_id] = SentenceTransformer(model_id, device="cpu")
        model = self._ST_CACHE[model_id]
        # Run the synchronous encode in a thread so we don't block the event loop
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: model.encode(texts, show_progress_bar=False,
                                  convert_to_numpy=True).tolist(),
        )
        return embeddings


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
