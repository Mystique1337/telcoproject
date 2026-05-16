"""Persona extractor — convert a user's review history into a structured Persona.

Runs OFFLINE in batch (`scripts/build_personas.py`); the API caches results in SQLite
and serves cached personas to the endpoints.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from app.api.schemas.persona import (
    ExtractionSource,
    Persona,
    RegisterTier,
    ReviewAnchor,
)
from app.config import get_settings
from app.llm import get_llm_client
from app.llm.client import LLMError

logger = logging.getLogger(__name__)
settings = get_settings()


_EXTRACTOR_SYSTEM = (
    "You are a persona analyst for Nigerian users. Given a list of past reviews, you "
    "infer a structured persona JSON. Always return STRICT JSON matching the schema. "
    "Detect register tier honestly — do not over-classify as Pidgin. Identify aspect "
    "priorities specific to what the user actually talks about."
)


_EXTRACTOR_PROMPT_TEMPLATE = """
You are given {n_reviews} past reviews from a single Nigerian user.

Reviews:
{reviews_block}

Infer the user's persona and return STRICT JSON with these keys:

{{
  "hedonic_utilitarian": 0.0 to 1.0  (0=utility focus, 1=hedonic/experiential),
  "intensity_calibration": {{"<word>": <rating 1-5>, ...}}  (3-5 entries from this user's vocabulary),
  "communal_individual": 0.0 to 1.0  (0=individualist "I", 1=communal "we/family"),
  "aspect_priority": {{"<aspect>": <weight>, ...}}  (4-6 aspects, weights sum to ~1.0),
  "register_tier": "standard_english" | "nigerian_english" | "nigerian_pidgin" | "code_mixed",
  "register_markers": ["<marker>", ...]  (3-8 actual phrases from the reviews),
  "register_confidence": 0.0 to 1.0
}}

Be specific and honest. Do not invent markers.
""".strip()


async def extract_persona(
    user_id: str,
    review_history: list[dict[str, Any]],
) -> Persona:
    """Run the offline persona extraction pipeline.

    `review_history` items must contain: `review_id`, `product_id`, `rating`, `text`.
    """
    if len(review_history) < 1:
        raise ValueError("review_history must contain ≥1 review")

    reviews_block = "\n\n".join(
        f"[{i+1}] rating={r['rating']}/5: {r['text']}" for i, r in enumerate(review_history[:20])
    )
    prompt = _EXTRACTOR_PROMPT_TEMPLATE.format(
        n_reviews=len(review_history), reviews_block=reviews_block
    )

    client = get_llm_client(settings.persona_extractor)
    try:
        result = await client.complete_json(
            prompt=prompt, system=_EXTRACTOR_SYSTEM, max_tokens=1200, temperature=0.3
        )
    except LLMError as exc:
        logger.exception("persona extraction failed for user=%s", user_id)
        raise

    register_str = result.get("register_tier", "nigerian_english")
    try:
        register = RegisterTier(register_str)
    except ValueError:
        logger.warning("unknown register %s; defaulting to nigerian_english", register_str)
        register = RegisterTier.NIGERIAN_ENGLISH

    anchors = [
        ReviewAnchor(
            review_id=str(r["review_id"]),
            product_id=str(r["product_id"]),
            rating=int(r["rating"]),
            text=r["text"][:500],
        )
        for r in review_history[:5]
    ]

    return Persona(
        user_id=user_id,
        hedonic_utilitarian=float(result.get("hedonic_utilitarian", 0.5)),
        intensity_calibration={k: float(v) for k, v in result.get("intensity_calibration", {}).items()},
        communal_individual=float(result.get("communal_individual", 0.5)),
        aspect_priority={k: float(v) for k, v in result.get("aspect_priority", {}).items()},
        register_tier=register,
        register_markers=list(result.get("register_markers", []))[:10],
        register_confidence=float(result.get("register_confidence", 0.7)),
        review_anchors=anchors,
        history_count=len(review_history),
        extraction_source=ExtractionSource.HISTORY,
    )
