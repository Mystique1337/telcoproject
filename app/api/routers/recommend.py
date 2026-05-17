"""Task 2 — personalised recommendation.

POST /recommend
Input:  { persona, candidate_set?, domain, k }
Output: { recommendations: [{product_id, score, rationale}, ...] }
"""

from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException

from app.agents.recommend_agent import recommend_products
from app.api.schemas import RecommendItem, RecommendRequest, RecommendResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["task-2"])


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest) -> RecommendResponse:
    """Rank products for the persona; return top-k with per-item rationale."""
    started = time.perf_counter()
    logger.info(
        "recommend user=%s domain=%s k=%d candidate_set=%s",
        req.persona.user_id,
        req.domain,
        req.k,
        len(req.candidate_set) if req.candidate_set else "auto-retrieve",
    )
    try:
        result = await recommend_products(
            persona=req.persona,
            candidate_set=req.candidate_set,
            domain=req.domain,
            k=req.k,
            include_negatives=req.include_negatives,
            include_reasoning=req.include_reasoning,
            reranker_override=req.reranker_override,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("recommend failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return RecommendResponse(
        recommendations=[RecommendItem(**item) for item in result["recommendations"]],
        negatives=(
            [RecommendItem(**item) for item in result["negatives"]]
            if result.get("negatives")
            else None
        ),
        reasoning_trace=result.get("reasoning_trace"),
        latency_ms=elapsed_ms,
    )
