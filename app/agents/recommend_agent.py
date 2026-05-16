"""Task 2 — recommendation agent.

Pipeline per PRD v4 §6.7:
  1. Load persona.
  2. Multi-source candidate retrieval (Chroma semantic; falls back to sample products).
  3. Pre-ranking with external knowledge injection (popularity + register match).
  4. LLM re-rank top-30 with per-item rationale.
  5. MMR diversity re-rank on the LLM scores.
  6. Optional: negative recommendations.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from app.api.schemas.persona import Persona
from app.api.schemas.product import Product
from app.config import get_settings
from app.llm import get_llm_client
from app.llm.client import LLMError
from app.rag.retriever import retrieve_candidates

logger = logging.getLogger(__name__)
settings = get_settings()


async def recommend_products(
    persona: Persona,
    candidate_set: list[str] | None,
    domain: str,
    k: int,
    include_negatives: bool = False,
    include_reasoning: bool = False,
) -> dict[str, Any]:
    """Generate top-k product recommendations for the persona."""
    trace: list[dict[str, Any]] = []

    # Step 1 — Candidate retrieval
    t0 = time.perf_counter()
    candidates = await retrieve_candidates(
        persona=persona,
        domain=domain,
        candidate_set=candidate_set,
        top_k=30,
    )
    trace.append(
        {
            "node": "candidate_retrieval",
            "n_candidates": len(candidates),
            "domain": domain,
            "duration_ms": int((time.perf_counter() - t0) * 1000),
        }
    )

    if not candidates:
        return {"recommendations": [], "negatives": None, "reasoning_trace": trace}

    # Step 2 — Pre-rank with external knowledge (popularity, register match)
    candidates = _prerank(candidates, persona)
    trace.append({"node": "pre_ranking", "method": "popularity+register_match"})

    # Step 3 — LLM re-rank top-30 → top-K
    t1 = time.perf_counter()
    ranked = await _llm_rerank(persona, candidates[:30], k=k)
    trace.append(
        {
            "node": "llm_rerank",
            "reranker": settings.task2_reranker,
            "duration_ms": int((time.perf_counter() - t1) * 1000),
        }
    )

    # Step 4 — MMR diversity re-rank (FR-T2.7)
    ranked = _mmr_rerank(ranked, lambda_param=0.7)
    trace.append({"node": "mmr_diversity", "lambda": 0.7})

    # Attach rank numbers
    recommendations = [{**item, "rank": i + 1} for i, item in enumerate(ranked[:k])]

    # Step 5 — Optional negative recommendations (FR-T2.11)
    negatives: list[dict[str, Any]] | None = None
    if include_negatives and len(candidates) > k:
        negatives = [
            {
                **{
                    "product_id": c["product_id"],
                    "title": c.get("title"),
                    "score": -c.get("score", 0.0),
                    "rationale": "Mismatch with persona's primary aspects.",
                    "rank": i + 1,
                }
            }
            for i, c in enumerate(candidates[-3:])
        ]
        trace.append({"node": "negative_recommendations", "n": len(negatives)})

    return {
        "recommendations": recommendations,
        "negatives": negatives,
        "reasoning_trace": trace if include_reasoning else None,
    }


# --------------------------------------------------------------------------- #
# Pre-ranking                                                                  #
# --------------------------------------------------------------------------- #


def _prerank(candidates: list[dict[str, Any]], persona: Persona) -> list[dict[str, Any]]:
    """Re-order candidates by a simple composite score before LLM re-rank.

    Score = retrieval_similarity * 0.7 + popularity_score * 0.2 + register_match * 0.1
    """
    primary = persona.primary_aspects(top_k=3)
    for c in candidates:
        sim = float(c.get("similarity", 0.5))
        pop = float(c.get("popularity", 0.5))  # 0-1 normalised
        desc = (c.get("description") or "").lower()
        title = (c.get("title") or "").lower()
        text = f"{title} {desc}"
        match = sum(1.0 for a in primary if a.lower() in text) / max(len(primary), 1)
        c["prerank_score"] = sim * 0.7 + pop * 0.2 + match * 0.1
    return sorted(candidates, key=lambda c: c["prerank_score"], reverse=True)


# --------------------------------------------------------------------------- #
# LLM re-rank                                                                  #
# --------------------------------------------------------------------------- #


async def _llm_rerank(
    persona: Persona, candidates: list[dict[str, Any]], k: int
) -> list[dict[str, Any]]:
    """Use the configured re-ranker LLM to score and rationalise each candidate."""
    client = get_llm_client(settings.task2_reranker)

    candidate_lines = "\n".join(
        f"{i}. id={c['product_id']} | title={c.get('title','')[:80]} | "
        f"category={c.get('category','')} | price=₦{c.get('price_naira','?')}"
        for i, c in enumerate(candidates)
    )

    system = (
        "You are recommending products to a Nigerian user. You are given the user's "
        "persona (cognitive dimensions + register + aspect priorities) and a candidate "
        "list. Score each candidate 0.0–1.0 for fit. Be sensitive to register, "
        "communal vs individual framing, hedonic vs utilitarian disposition, and the "
        "aspects the user emphasises. Return STRICT JSON."
    )

    prompt = f"""
Persona:
- register_tier: {persona.register_tier.value}
- register_markers: {persona.register_markers}
- hedonic_utilitarian: {persona.hedonic_utilitarian:.2f}  (0=utility, 1=hedonic)
- communal_individual: {persona.communal_individual:.2f}  (0=individual, 1=communal)
- aspect_priority top 3: {persona.primary_aspects(top_k=3)}
- history_count: {persona.history_count}

Candidates:
{candidate_lines}

Return JSON of the form:
{{
  "ranked": [
    {{"product_id": "...", "score": 0.92, "rationale": "one short sentence"}},
    ...
  ]
}}

Rank from BEST fit to WORST. Include ALL candidates. Score must be in [0.0, 1.0].
Rationale: one short sentence naming WHICH persona feature drove the score.
""".strip()

    try:
        result = await client.complete_json(
            prompt=prompt, system=system, max_tokens=2000, temperature=0.4
        )
        ranked_raw = result.get("ranked", [])
    except LLMError as exc:
        logger.warning("LLM re-rank failed (%s); falling back to prerank order", exc)
        return [
            {
                "product_id": c["product_id"],
                "title": c.get("title"),
                "score": c["prerank_score"],
                "rationale": "Pre-rank score (LLM re-rank unavailable).",
                "serendipity_score": None,
            }
            for c in candidates[:k]
        ]

    # Hydrate with title from candidates
    by_id = {c["product_id"]: c for c in candidates}
    hydrated: list[dict[str, Any]] = []
    for item in ranked_raw:
        c = by_id.get(item.get("product_id"))
        if not c:
            continue
        hydrated.append(
            {
                "product_id": item["product_id"],
                "title": c.get("title"),
                "score": float(item.get("score", 0.0)),
                "rationale": item.get("rationale", ""),
                "serendipity_score": _serendipity(c, persona),
            }
        )
    return hydrated


def _serendipity(candidate: dict[str, Any], persona: Persona) -> float:
    """Surprise score: candidate's distance from persona's primary aspect centroid.

    Day-1 stub: 1.0 if candidate's category isn't in the user's primary aspects.
    """
    primary = set(a.lower() for a in persona.primary_aspects(top_k=3))
    cat = (candidate.get("category") or "").lower()
    return 1.0 if cat and cat not in primary else 0.3


# --------------------------------------------------------------------------- #
# MMR diversity                                                                #
# --------------------------------------------------------------------------- #


def _mmr_rerank(
    items: list[dict[str, Any]], lambda_param: float = 0.7
) -> list[dict[str, Any]]:
    """Maximal Marginal Relevance re-rank.

    score_mmr(i) = λ * score(i) − (1-λ) * max_sim(i, already_selected)

    Day-1 stub: similarity uses category overlap (1.0 if same category as a selected
    item, 0.0 otherwise). Replace with embedding cosine when embeddings are wired.
    """
    if not items:
        return items
    remaining = items.copy()
    selected: list[dict[str, Any]] = []

    while remaining:
        if not selected:
            selected.append(remaining.pop(0))
            continue
        best_idx = 0
        best_score = -float("inf")
        for i, cand in enumerate(remaining):
            cand_cat = (cand.get("category") or "").lower()
            max_sim = max(
                (1.0 if cand_cat and cand_cat == (s.get("category") or "").lower() else 0.0)
                for s in selected
            )
            mmr = lambda_param * cand.get("score", 0.0) - (1 - lambda_param) * max_sim
            if mmr > best_score:
                best_score = mmr
                best_idx = i
        selected.append(remaining.pop(best_idx))

    return selected
