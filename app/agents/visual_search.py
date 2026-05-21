"""Visual search for ShopEasy — image -> product description -> retrieval.

We have no CLIP/image-embedding model wired, so we use a vision-capable LLM
(GPT-4o by default, via the OpenAI-compatible endpoint) to turn an uploaded
photo into a concise shopping search phrase, then run that phrase through the
existing Pinecone retrieval. This is the pragmatic "image search" MVP.
"""

from __future__ import annotations

import logging
import os

import httpx

from app.config import get_settings
from app.llm.client import LLMError

logger = logging.getLogger(__name__)
settings = get_settings()

_VISION_PROMPT = (
    "You are a shopping assistant looking at a product photo. Describe the item "
    "as a concise search phrase a Nigerian shopper would type to find it on an "
    "e-commerce site: product type/category, key visual attributes (colour, "
    "style, material), and obvious use. 6-15 words. No preamble, no quotes — "
    "just the search phrase."
)


async def describe_product_image(
    image_b64: str,
    mime: str = "image/jpeg",
    model: str | None = None,
) -> str:
    """Caption an uploaded product image into a search phrase via a vision LLM.

    Uses OpenAI gpt-4o by default (the configured OPENAI key). Honours
    OPENAI_BASE_URL so it also works through freemodel.dev if set.
    """
    if not settings.openai_api_key:
        raise LLMError("OPENAI_API_KEY not set — needed for image search")
    model = model or "gpt-4o"
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": _VISION_PROMPT},
                {"type": "image_url",
                 "image_url": {"url": f"data:{mime};base64,{image_b64}"}},
            ],
        }],
        "max_tokens": 80,
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        if resp.status_code != 200:
            raise LLMError(f"vision API {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        return (data["choices"][0]["message"]["content"] or "").strip()
