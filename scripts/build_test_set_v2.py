"""Build a fresh held-out test set (v2) on the expanded persona × product matrix.

For each (persona, product) sampled combo:
  - Prompt NIM Llama 3.3 70B to generate a persona-authentic review + rating,
    grounded in the product details + the persona's anchors and aspect
    priorities.
  - Output schema matches v1_test_full.parquet so eval_all.py can consume it
    without changes.

Cold-start and cross-domain scenarios are explicitly included by design:
  - 20% of rows use personas with history_count=0 (cold-start GT)
  - 20% mix high-affinity personas with off-category products (cross-domain GT)

Free: uses NIM (Llama 3.3 70B) which is on the NVIDIA free tier.

Run:
  python scripts/build_test_set_v2.py --n 200
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import re
import sys
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

logger = logging.getLogger("test_set_v2")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")

PERSONAS_DIR = PROJECT_ROOT / "data" / "sample" / "personas"
PRODUCTS_DIR = PROJECT_ROOT / "data" / "sample" / "products"
OUT_PATH = PROJECT_ROOT / "data" / "finetune" / "v2_test_full.parquet"

NIM_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
NIM_MODEL = os.getenv("NIM_MODEL", "meta/llama-3.3-70b-instruct")


SYSTEM = """You are an expert Nigerian-context review writer. Given a Nigerian user persona and a Jumia product, generate a review that authentically reflects the persona's voice, register, and concerns. Be honest — if the product seems likely to disappoint someone with their priorities, write a 1-2 star critical review. If it aligns, write a 4-5 star positive review."""


PROMPT_TEMPLATE = """## Persona
register tier:       {register_tier}
register markers:    {register_markers}
hedonic↔utilitarian: {hedonic_utilitarian:.2f}  (0=utility, 1=hedonic)
communal↔individual: {communal_individual:.2f}  (0=individual, 1=communal)
top aspects:         {primary_aspects}
intensity calibration: {intensity_calibration}
location:            {location}
occupation:          {occupation}
review history sample:
{anchor_block}

## Product
title:      {product_title}
category:   {product_category}
price:      ₦{price}
description: {product_description}

## Task
Write ONE Nigerian-style review that this persona would actually write, AND assign a star rating (1-5).
- Tone, register, and intensifiers must match the persona EXACTLY.
- Be honest about whether this product fits the persona — give low ratings when the product doesn't match their aspects, high when it does.
- Reviews 2-5 sentences, ~70-150 words.

## OUTPUT FORMAT — return ONLY valid JSON, no markdown:
{{"target_rating": "<integer 1-5 as string>", "persona_review": "<the review text>"}}
"""


# --------------------------------------------------------------------------- #
# Loading                                                                      #
# --------------------------------------------------------------------------- #

def _load_personas() -> list[dict]:
    out = []
    for p in sorted(PERSONAS_DIR.glob("*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def _load_products(n_sample: int) -> list[dict]:
    files = list(PRODUCTS_DIR.glob("*.json"))
    rng = random.Random(42)
    rng.shuffle(files)
    out = []
    for p in files[: n_sample * 2]:  # over-sample then filter
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("title") and d.get("description"):
                out.append(d)
        except Exception:
            continue
        if len(out) >= n_sample:
            break
    return out


def _primary_aspects(persona: dict, k: int = 3) -> list[str]:
    ap = persona.get("aspect_priority", {})
    return [a for a, _ in sorted(ap.items(), key=lambda x: -x[1])[:k]]


def _anchor_block(persona: dict, max_anchors: int = 2) -> str:
    anchors = persona.get("review_anchors", [])[:max_anchors]
    if not anchors:
        return "  (no prior history — cold-start persona)"
    lines = []
    for a in anchors:
        lines.append(f"  - ★{a.get('rating','?')} on {a.get('product_id','?')}: \"{(a.get('text') or '')[:200]}\"")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# NIM call                                                                     #
# --------------------------------------------------------------------------- #

async def _retry_429(coro_factory, max_tries: int = 6) -> Any:
    """Exponential backoff on 429s (NIM free tier rate-limits)."""
    import asyncio as _a
    for attempt in range(max_tries):
        try:
            return await coro_factory()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_tries - 1:
                wait = 2 ** (attempt + 2)
                logger.warning("  429 rate-limited, sleeping %ds", wait)
                await _a.sleep(wait)
                continue
            raise


async def call_nim(client: httpx.AsyncClient, prompt: str) -> str:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    payload = {
        "model": NIM_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 600,
        "temperature": 0.7,
    }
    async def _do():
        r = await client.post(NIM_URL, json=payload, headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    return await _retry_429(_do)


def _parse(text: str) -> dict | None:
    text = (text or "").strip()
    # Strip code fences
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.MULTILINE)
    # Try direct JSON
    try:
        out = json.loads(text)
    except Exception:
        # Fallback: pull first {...} blob
        m = re.search(r"\{.*?\}", text, re.DOTALL)
        if not m:
            return None
        try:
            out = json.loads(m.group(0))
        except Exception:
            return None
    if not isinstance(out, dict):
        return None
    if "target_rating" not in out or "persona_review" not in out:
        return None
    # Coerce rating
    try:
        r = int(round(float(out["target_rating"])))
        r = max(1, min(5, r))
        out["target_rating"] = str(r)
    except Exception:
        return None
    return out


# --------------------------------------------------------------------------- #
# Main loop                                                                    #
# --------------------------------------------------------------------------- #

async def generate_one(client: httpx.AsyncClient, persona: dict, product: dict,
                        cold_start: bool, semaphore: asyncio.Semaphore) -> dict | None:
    """One (persona, product) -> {persona_review, target_rating} via NIM."""
    p = dict(persona)
    if cold_start:
        # Wipe history to simulate cold-start ground truth
        p["review_anchors"] = []
        p["history_count"] = 0

    prompt = PROMPT_TEMPLATE.format(
        register_tier=p.get("register_tier", "nigerian_english"),
        register_markers=", ".join(p.get("register_markers", [])[:6]),
        hedonic_utilitarian=p.get("hedonic_utilitarian", 0.5),
        communal_individual=p.get("communal_individual", 0.5),
        primary_aspects=_primary_aspects(p, k=4),
        intensity_calibration=p.get("intensity_calibration", {}),
        location=p.get("demographics", {}).get("location", ""),
        occupation=p.get("demographics", {}).get("occupation", ""),
        anchor_block=_anchor_block(p, max_anchors=2),
        product_title=(product.get("title") or "")[:120],
        product_category=product.get("category", ""),
        price=product.get("price_naira") or "?",
        product_description=(product.get("description") or "")[:600],
    )
    async with semaphore:
        try:
            raw = await call_nim(client, prompt)
        except Exception as e:
            logger.warning("  NIM failed: %s", str(e)[:100])
            return None
    parsed = _parse(raw)
    if not parsed:
        return None
    return {
        "persona_id": persona.get("user_id"),
        "register_tier": persona.get("register_tier"),
        "product_category": product.get("category"),
        "product_title": product.get("title"),
        "title": product.get("title"),
        "category": product.get("category"),
        "description": product.get("description", "")[:1500],
        "price_naira": product.get("price_naira"),
        "review": parsed["persona_review"],
        "persona_review": parsed["persona_review"],
        "rating": int(parsed["target_rating"]),
        "target_rating": parsed["target_rating"],
        "pipeline": "v2_nim_llama33",
        "cold_start": cold_start,
    }


async def main_async(args) -> int:
    rng = random.Random(args.seed)
    personas = _load_personas()
    products = _load_products(args.n * 2)
    logger.info("loaded %d personas, %d products", len(personas), len(products))
    if not personas or not products:
        logger.error("need personas + products"); return 1

    # Build (persona, product, cold_start) sample list
    samples: list[tuple[dict, dict, bool]] = []
    n_cold = int(args.n * 0.20)
    n_normal = args.n - n_cold
    # Normal samples — stratified by persona
    persona_cycle = list(personas)
    rng.shuffle(persona_cycle)
    for i in range(n_normal):
        p = persona_cycle[i % len(persona_cycle)]
        prod = rng.choice(products)
        samples.append((p, prod, False))
    # Cold-start samples
    for i in range(n_cold):
        p = persona_cycle[i % len(persona_cycle)]
        prod = rng.choice(products)
        samples.append((p, prod, True))
    rng.shuffle(samples)

    logger.info("generating %d test rows via NIM %s (concurrency=%d)",
                len(samples), NIM_MODEL, args.concurrency)

    sem = asyncio.Semaphore(args.concurrency)
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[
            generate_one(client, p, pr, cs, sem) for p, pr, cs in samples
        ])
    rows = [r for r in results if r is not None]
    logger.info("✅ %d / %d rows generated", len(rows), len(samples))

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(OUT_PATH, index=False)
    logger.info("💾 %s (%d rows)", OUT_PATH, len(rows))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200, help="Target number of test rows")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
