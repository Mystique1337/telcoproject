"""InsideNaija — synthetic customer panel.

Fan a single product out across the 24-persona Nigerian panel, collect each
persona's simulated rating + review, and aggregate into pre-launch consumer
insight: predicted rating distribution, buy-likelihood, sentiment split, and
cohort breakdowns (by register, geopolitical zone, age band).

This is the product surface for Task A (User Modeling): instead of one
persona × one product, we run the whole panel and summarise.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

from app.agents.review_agent import generate_review
from app.api.schemas.persona import Persona
from app.api.schemas.product import Product
from app.config import PROJECT_ROOT, get_settings
from app.llm import get_llm_client
from app.llm.client import LLMError

logger = logging.getLogger(__name__)
settings = get_settings()

PERSONAS_DIR = PROJECT_ROOT / "data" / "sample" / "personas"

# Nigerian state → geopolitical zone (for cohort breakdown). Matched by
# substring against the persona's free-text location.
_ZONE_BY_STATE: dict[str, str] = {
    # North-Central
    "benue": "North-Central", "makurdi": "North-Central", "kogi": "North-Central",
    "kwara": "North-Central", "nasarawa": "North-Central", "niger": "North-Central",
    "plateau": "North-Central", "jos": "North-Central", "abuja": "North-Central",
    "fct": "North-Central",
    # North-East
    "adamawa": "North-East", "bauchi": "North-East", "borno": "North-East",
    "maiduguri": "North-East", "gombe": "North-East", "taraba": "North-East",
    "yobe": "North-East",
    # North-West
    "kaduna": "North-West", "kano": "North-West", "katsina": "North-West",
    "kebbi": "North-West", "sokoto": "North-West", "jigawa": "North-West",
    "zamfara": "North-West", "sabon gari": "North-West",
    # South-East
    "abia": "South-East", "aba": "South-East", "anambra": "South-East",
    "nnewi": "South-East", "onitsha": "South-East", "ebonyi": "South-East",
    "enugu": "South-East", "imo": "South-East", "owerri": "South-East",
    # South-South
    "akwa ibom": "South-South", "bayelsa": "South-South", "cross river": "South-South",
    "calabar": "South-South", "delta": "South-South", "warri": "South-South",
    "edo": "South-South", "rivers": "South-South", "port harcourt": "South-South",
    # South-West
    "ekiti": "South-West", "lagos": "South-West", "ikeja": "South-West",
    "victoria island": "South-West", "ogun": "South-West", "abeokuta": "South-West",
    "ondo": "South-West", "osun": "South-West", "oyo": "South-West", "ibadan": "South-West",
}


def _zone_for(location: str | None) -> str:
    loc = (location or "").lower()
    for key, zone in _ZONE_BY_STATE.items():
        if key in loc:
            return zone
    return "Unknown"


def load_panel_personas(persona_ids: list[str] | None = None) -> list[Persona]:
    """Load the bundled persona panel, optionally filtered to specific ids."""
    personas: list[Persona] = []
    for fp in sorted(PERSONAS_DIR.glob("*.json")):
        data = json.loads(fp.read_text())
        if persona_ids and data.get("user_id") not in persona_ids:
            continue
        try:
            personas.append(Persona(**data))
        except Exception as e:  # noqa: BLE001
            logger.warning("skipping persona %s: %s", fp.name, e)
    return personas


def _sentiment_of(rating: int) -> str:
    if rating >= 4:
        return "positive"
    if rating == 3:
        return "neutral"
    return "negative"


async def _summarise_themes(reviews: list[str], backbone: str) -> dict[str, list[str]]:
    """One aggregation pass: pull the recurring praise + complaint themes
    across all panel reviews. Best-effort — returns empty lists on failure."""
    if not reviews:
        return {"praised": [], "complaints": []}
    client = get_llm_client(backbone)
    joined = "\n".join(f"- {r[:300]}" for r in reviews[:30])
    prompt = (
        "Below are simulated product reviews from a Nigerian customer panel. "
        "Identify the recurring themes. Return STRICT JSON:\n"
        '{"praised": ["short theme", ...], "complaints": ["short theme", ...]}\n'
        "Max 5 items each, 2-5 words per theme. No prose.\n\n"
        f"Reviews:\n{joined}"
    )
    try:
        out = await client.complete_json(prompt, max_tokens=400, temperature=0.2)
        return {
            "praised": [str(x) for x in (out.get("praised") or [])][:5],
            "complaints": [str(x) for x in (out.get("complaints") or [])][:5],
        }
    except LLMError as e:  # noqa: BLE001
        logger.warning("theme summary failed: %s", e)
        return {"praised": [], "complaints": []}


def _cohort_breakdown(reactions: list[dict[str, Any]], key_fn) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[int]] = {}
    for r in reactions:
        k = key_fn(r)
        buckets.setdefault(k, []).append(r["rating"])
    out: dict[str, dict[str, Any]] = {}
    for k, ratings in buckets.items():
        n = len(ratings)
        out[k] = {
            "n": n,
            "avg_rating": round(sum(ratings) / n, 2) if n else 0.0,
            "buy_likelihood": round(100 * sum(1 for x in ratings if x >= 4) / n, 0) if n else 0.0,
        }
    return dict(sorted(out.items(), key=lambda kv: -kv[1]["avg_rating"]))


async def run_panel(
    product: Product,
    persona_ids: list[str] | None = None,
    backbone_override: str | None = None,
    target_language: str | None = None,
    concurrency: int = 6,
    include_reasoning: bool = False,
    on_result=None,  # Optional[Callable[[dict], Awaitable[None]]] — called per persona as it finishes
) -> dict[str, Any]:
    """Run the full panel against one product and aggregate insights."""
    started = time.perf_counter()
    personas = load_panel_personas(persona_ids)
    if not personas:
        return {"error": "no personas loaded", "reactions": [], "aggregate": {}}

    primary = backbone_override or settings.task1_backbone
    fallback = settings.task1_fallback
    used_fallback = {"n": 0}

    sem = asyncio.Semaphore(concurrency)

    async def _one(persona: Persona) -> dict[str, Any] | None:
        async with sem:
            res = None
            try:
                res = await generate_review(
                    persona=persona,
                    product=product,
                    include_reasoning=False,
                    backbone_override=primary,
                    target_language=target_language,
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("panel primary (%s) failed for %s: %s; falling back to %s",
                               primary, persona.user_id, e, fallback)
            if res is None and fallback and fallback != primary:
                try:
                    res = await generate_review(
                        persona=persona,
                        product=product,
                        include_reasoning=False,
                        backbone_override=fallback,
                        target_language=target_language,
                    )
                    used_fallback["n"] += 1
                except Exception as e:  # noqa: BLE001
                    logger.warning("panel fallback also failed for %s: %s", persona.user_id, e)
                    return None
            if res is None:
                return None
            demo = persona.demographics or {}
            rating = int(res["rating"])
            reaction = {
                "persona_id": persona.user_id,
                "location": demo.get("location"),
                "zone": _zone_for(demo.get("location")),
                "age_range": demo.get("age_range"),
                "occupation": demo.get("occupation"),
                "register_tier": persona.register_tier.value,
                "rating": rating,
                "review": res["review"],
                "language": res.get("language"),
                "original_review": res.get("original_review"),
                "sentiment": _sentiment_of(rating),
            }
            # Fire the per-result callback immediately so callers can persist/stream
            if on_result is not None:
                try:
                    await on_result(reaction)
                except Exception as e:  # noqa: BLE001
                    logger.warning("on_result callback failed for %s: %s", persona.user_id, e)
            return reaction

    results = await asyncio.gather(*[_one(p) for p in personas])
    reactions = [r for r in results if r]

    n = len(reactions)
    ratings = [r["rating"] for r in reactions]
    dist = {str(s): sum(1 for x in ratings if x == s) for s in range(1, 6)}
    avg = round(sum(ratings) / n, 2) if n else 0.0
    buy = round(100 * sum(1 for x in ratings if x >= 4) / n, 0) if n else 0.0
    sentiment_split = {
        s: sum(1 for r in reactions if r["sentiment"] == s)
        for s in ("positive", "neutral", "negative")
    }

    themes = await _summarise_themes(
        [r["original_review"] or r["review"] for r in reactions],
        backbone_override or settings.task1_fallback,
    )

    aggregate = {
        "n_personas": n,
        "avg_rating": avg,
        "rating_distribution": dist,
        "buy_likelihood": buy,
        "sentiment_split": sentiment_split,
        "by_register": _cohort_breakdown(reactions, lambda r: r["register_tier"]),
        "by_zone": _cohort_breakdown(reactions, lambda r: r["zone"]),
        "by_age": _cohort_breakdown(reactions, lambda r: r.get("age_range") or "Unknown"),
        "themes": themes,
    }

    return {
        "product_title": product.title,
        "reactions": sorted(reactions, key=lambda r: -r["rating"]),
        "aggregate": aggregate,
        "backbone": {
            "primary": primary,
            "fallback": fallback,
            "fallback_used": used_fallback["n"],
        },
        "rmse_band": 1.1,  # held-out rating-prediction RMSE (paper §5)
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }
