"""Task 1 — review + rating generation.

POST /simulate-review
Input:  { persona, product }
Output: { rating, review, register_tier, rationale }
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException

from app.agents.review_agent import generate_review
from app.api.schemas import SimulateReviewRequest, SimulateReviewResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["task-1"])


@router.post("/simulate-review", response_model=SimulateReviewResponse)
async def simulate_review(req: SimulateReviewRequest) -> SimulateReviewResponse:
    """Generate a review + rating in the persona's voice for the given product."""
    started = time.perf_counter()
    logger.info(
        "simulate-review user=%s product=%s register=%s",
        req.persona.user_id,
        req.product.product_id,
        req.persona.register_tier.value,
    )
    try:
        result = await generate_review(
            persona=req.persona,
            product=req.product,
            include_reasoning=req.include_reasoning,
            backbone_override=req.backbone_override,
            target_rating=req.target_rating,
            aspect_focus=req.aspect_focus,
            length_hint=req.length_hint,
            tone_modifier=req.tone_modifier,
            refinement_instructions=req.refinement_instructions,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("simulate-review failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return SimulateReviewResponse(
        rating=result["rating"],
        review=result["review"],
        register_tier=result["register_tier"],
        rationale=result["rationale"],
        fallback_reason=result.get("fallback_reason"),
        reasoning_trace=result.get("reasoning_trace"),
        latency_ms=elapsed_ms,
    )
