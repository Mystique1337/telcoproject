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

import httpx

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
    reranker_override: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Generate top-k product recommendations for the persona.

    Handles four scoring-rubric scenarios explicitly:
      - Normal: history-grounded ranking via persona aspects + anchors.
      - Cold-start: persona.history_count < 3 → fall back to demographic +
        aspect_priority + popularity (no history-based filtering).
      - Cross-domain: domain="all" or comma-separated list → pull candidates
        from multiple categories, surface diversity per category in output.
      - Multi-turn: conversation_history present → fold prior constraints
        ("I want a phone", "for my mum", "under ₦100k") into the prompt.
    """
    trace: list[dict[str, Any]] = []
    is_cold_start = _is_cold_start(persona)
    is_cross_domain = _is_cross_domain(domain)
    multi_turn = bool(conversation_history)

    # Step 0 — Agentic intent analysis (the model reasons about the user)
    intent = _build_intent(persona, conversation_history)
    trace.append({
        "node": "intent_analysis",
        "summary": (
            f"Persona is {'cold-start (no history)' if is_cold_start else 'history-grounded'}, "
            f"hedonic-utilitarian={persona.hedonic_utilitarian:.2f}, "
            f"communal-individual={persona.communal_individual:.2f}, "
            f"top aspects={persona.primary_aspects(top_k=3)}. "
            f"Cross-domain={'yes' if is_cross_domain else 'no'}. "
            f"Multi-turn={'yes (' + str(len(conversation_history or [])) + ' prior turns)' if multi_turn else 'no'}. "
            f"Constraints extracted from conversation: {intent.get('constraints') or 'none'}."
        ),
        "cold_start": is_cold_start,
        "cross_domain": is_cross_domain,
        "multi_turn": multi_turn,
        "extracted_constraints": intent.get("constraints", []),
    })

    # Step 1 — Candidate retrieval (cross-domain aware)
    t0 = time.perf_counter()
    domains = _resolve_domains(domain)
    all_candidates: list[dict[str, Any]] = []
    for d in domains:
        chunk = await retrieve_candidates(
            persona=persona, domain=d, candidate_set=candidate_set,
            top_k=max(30, 30 // max(len(domains), 1)),
        )
        all_candidates.extend(chunk)
    # De-dupe by product_id, preserve order
    seen_ids: set[str] = set()
    candidates = []
    for c in all_candidates:
        cid = str(c.get("product_id", ""))
        if cid and cid not in seen_ids:
            seen_ids.add(cid); candidates.append(c)
    trace.append({
        "node": "candidate_retrieval",
        "summary": (
            f"Pulled {len(candidates)} unique candidates"
            + (f" across {len(domains)} domains: {domains}" if is_cross_domain else f" from {domains[0]}")
            + (" via explicit candidate_set" if candidate_set else "")
        ),
        "n_candidates": len(candidates),
        "domains_searched": domains,
        "duration_ms": int((time.perf_counter() - t0) * 1000),
    })

    if not candidates:
        return {
            "recommendations": [], "negatives": None,
            "cold_start": is_cold_start, "cross_domain": is_cross_domain,
            "reasoning_trace": trace if include_reasoning else None,
        }

    # Step 2 — Pre-rank (cold-start branches into a different weighting)
    candidates = _prerank(candidates, persona, cold_start=is_cold_start)
    trace.append({
        "node": "pre_ranking",
        "summary": (
            "Cold-start path: popularity (50%) + aspect-match (30%) + similarity (20%)"
            if is_cold_start
            else "Standard: similarity (70%) + popularity (20%) + aspect-match (10%)"
        ),
        "strategy": "cold_start" if is_cold_start else "history_grounded",
    })

    # Step 2.5 — Cohere cross-encoder pre-rerank (fast, multilingual,
    # cheaper than LLM rerank). Narrows top-30 → top-N (default 15) so the
    # LLM rerank stage works on a tighter, already-relevance-filtered pool.
    # Skipped automatically if COHERE_API_KEY not set or if there are too
    # few candidates to narrow.
    t_cohere = time.perf_counter()
    pool_for_llm = candidates[:30]
    cohere_top_n = settings.cohere_rerank_top_n
    pool_for_llm, cohere_fallback = await _cohere_pre_rerank(
        pool_for_llm, persona, top_n=cohere_top_n,
    )
    trace.append({
        "node": "cohere_pre_rerank",
        "summary": (
            (f"Cohere pre-rerank skipped: {cohere_fallback}"
             if cohere_fallback else
             f"Cohere ({settings.cohere_rerank_model}) narrowed "
             f"{min(30, len(candidates))} → {len(pool_for_llm)} by persona-flavored query")
        ),
        "model": settings.cohere_rerank_model,
        "top_n": cohere_top_n,
        "fallback": cohere_fallback,
        "duration_ms": int((time.perf_counter() - t_cohere) * 1000),
    })

    # Step 3 — LLM re-rank with intent context (multi-turn aware)
    t1 = time.perf_counter()
    reranker_spec = reranker_override or settings.task2_reranker
    ranked, rerank_fallback = await _llm_rerank(
        persona, pool_for_llm, k=k, reranker_spec=reranker_spec,
        intent=intent,
    )
    trace.append({
        "node": "llm_rerank",
        "summary": (
            (f"LLM re-rank FELL BACK to pre-rank: {rerank_fallback}"
             if rerank_fallback else
             "LLM re-ranked top-30 candidates by predicted fit with persona "
             + ("+ conversation constraints" if multi_turn else "")
             + f"; reranker={reranker_spec}")
        ),
        "reranker": reranker_spec,
        "fallback": rerank_fallback,
        "duration_ms": int((time.perf_counter() - t1) * 1000),
    })

    # Step 4 — MMR diversity re-rank
    # Cross-domain mode uses stronger diversity weight to spread categories
    lambda_param = 0.55 if is_cross_domain else 0.7
    ranked = _mmr_rerank(ranked, lambda_param=lambda_param)
    trace.append({
        "node": "mmr_diversity",
        "summary": (
            f"Applied MMR diversity (λ={lambda_param}) — "
            + ("biased toward category diversity for cross-domain" if is_cross_domain
               else "standard relevance-leaning")
        ),
        "lambda": lambda_param,
    })

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
                    "price_naira": c.get("price_naira"),
                    "category": c.get("category"),
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
        "cold_start": is_cold_start,
        "cross_domain": is_cross_domain,
        "multi_turn": multi_turn,
        "extracted_constraints": intent.get("constraints", []),
        "rerank_fallback_reason": rerank_fallback,
        "reasoning_trace": trace if include_reasoning else None,
    }


# --------------------------------------------------------------------------- #
# Scenario detection                                                           #
# --------------------------------------------------------------------------- #


def _is_cold_start(persona: Persona) -> bool:
    """Persona is cold-start if it has < 3 history items / anchors."""
    return (persona.history_count < 3) and (len(persona.review_anchors) < 2)


def _is_cross_domain(domain: str) -> bool:
    if not domain:
        return False
    d = domain.lower().strip()
    return d in ("all", "*", "any") or "," in d


def _resolve_domains(domain: str) -> list[str]:
    """Map the domain field to a concrete list of domains to retrieve from."""
    if not domain:
        return ["jumia"]
    d = domain.lower().strip()
    if d in ("all", "*", "any"):
        # Default cross-domain set
        return ["jumia", "konga", "nollywood"]
    if "," in d:
        return [x.strip() for x in d.split(",") if x.strip()]
    return [d]


def _build_intent(persona: Persona,
                  conversation_history: list[dict[str, str]] | None) -> dict[str, Any]:
    """Extract intent / constraints from the conversation history (multi-turn).

    Cheap regex-based extractor — enough for budget, brand, recipient, category
    constraints commonly mentioned in Nigerian e-commerce chat.
    """
    constraints: list[str] = []
    summary_lines: list[str] = []
    if not conversation_history:
        return {"constraints": constraints, "summary": ""}
    import re as _re
    for turn in conversation_history:
        content = (turn.get("content") or "").lower()
        if not content:
            continue
        # Budget: ₦XXk or XXk naira
        m = _re.search(r"(?:under|below|max|maximum|budget(?:\s+of)?)\s*₦?\s*([\d,]+)\s*(k|thousand)?",
                       content)
        if m:
            val = m.group(1).replace(",", "")
            mult = 1000 if m.group(2) in ("k", "thousand") else 1
            try:
                budget = int(val) * mult
                constraints.append(f"budget≤₦{budget:,}")
            except ValueError:
                pass
        # Recipient: "for my X"
        m = _re.search(r"for (?:my )?(mum|mother|dad|father|wife|husband|sister|brother|son|daughter|child|kids|friend|aunty|uncle)",
                       content)
        if m:
            constraints.append(f"recipient={m.group(1)}")
        # Category hints
        for cat in ("phone", "tablet", "laptop", "tv", "fridge", "inverter", "shoes",
                    "ankara", "perfume", "makeup", "iron", "bag", "baby"):
            if cat in content:
                constraints.append(f"category={cat}")
                break
        summary_lines.append(turn.get("content", "")[:120])

    # De-dupe constraints while preserving order
    seen: set[str] = set()
    dedup = []
    for c in constraints:
        if c not in seen:
            seen.add(c); dedup.append(c)
    return {
        "constraints": dedup,
        "summary": " | ".join(summary_lines)[:500],
    }


# --------------------------------------------------------------------------- #
# Pre-ranking                                                                  #
# --------------------------------------------------------------------------- #


def _prerank(candidates: list[dict[str, Any]], persona: Persona,
             cold_start: bool = False) -> list[dict[str, Any]]:
    """Re-order candidates by a composite score before LLM re-rank.

    Standard weighting:  similarity 70%, popularity 20%, aspect-match 10%
    Cold-start weighting: popularity 50%, aspect-match 30%, similarity 20%
      (no review history → can't rely on similarity-to-past-purchases as much)
    """
    primary = persona.primary_aspects(top_k=3)
    for c in candidates:
        sim = float(c.get("similarity", 0.5))
        pop = float(c.get("popularity", 0.5))  # 0-1 normalised
        desc = (c.get("description") or "").lower()
        title = (c.get("title") or "").lower()
        text = f"{title} {desc}"
        match = sum(1.0 for a in primary if a.lower() in text) / max(len(primary), 1)
        if cold_start:
            c["prerank_score"] = pop * 0.5 + match * 0.3 + sim * 0.2
        else:
            c["prerank_score"] = sim * 0.7 + pop * 0.2 + match * 0.1
    return sorted(candidates, key=lambda c: c["prerank_score"], reverse=True)


# --------------------------------------------------------------------------- #
# Stage 2.5 — Cohere cross-encoder pre-rerank                                  #
# --------------------------------------------------------------------------- #


def _build_cohere_query(persona: Persona) -> str:
    """Flatten persona into a query string Cohere's cross-encoder can score
    documents against. Mirrors the retrieval-stage query construction but
    weighted toward the signals Cohere can actually use (text), not the
    structured numerics."""
    parts: list[str] = []
    if getattr(persona, "occupation", None):
        parts.append(str(persona.occupation))
    if getattr(persona, "location", None):
        parts.append(str(persona.location))
    aspects = persona.primary_aspects(top_k=3)
    if aspects:
        parts.append("looking for: " + ", ".join(aspects))
    if persona.hedonic_utilitarian > 0.6:
        parts.append("hedonic / pleasure-driven purchase")
    elif persona.hedonic_utilitarian < 0.4:
        parts.append("utility / practical purchase")
    if persona.communal_individual > 0.6:
        parts.append("for family or community use")
    elif persona.communal_individual < 0.4:
        parts.append("for personal use")
    return " | ".join(parts) or "Nigerian shopper"


async def _cohere_pre_rerank(
    candidates: list[dict[str, Any]], persona: Persona, top_n: int
) -> tuple[list[dict[str, Any]], str | None]:
    """Cross-encoder pre-rerank using Cohere rerank-v3.5. Narrows the
    candidate pool from len(candidates) → top_n before the LLM rerank.

    Returns (narrowed_candidates, fallback_reason).
    On any failure, returns the original candidates and a fallback string.
    """
    if not settings.cohere_api_key:
        return candidates, "no COHERE_API_KEY set"
    if len(candidates) <= top_n:
        return candidates, None  # nothing to narrow

    query = _build_cohere_query(persona)
    # Cohere wants document strings — use title + truncated description
    docs = []
    for c in candidates:
        title = c.get("title", "") or ""
        desc = c.get("description", "") or ""
        docs.append(f"{title}. {desc[:400]}".strip())

    payload = {
        "model": settings.cohere_rerank_model,
        "query": query,
        "documents": docs,
        "top_n": min(top_n, len(docs)),
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.cohere.com/v2/rerank",
                headers={
                    "Authorization": f"Bearer {settings.cohere_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            if resp.status_code != 200:
                return candidates, f"cohere {resp.status_code}: {resp.text[:150]}"
            data = resp.json()
            results = data.get("results", [])
            if not results:
                return candidates, "cohere returned empty results"
            # Build narrowed list in cohere's ranked order, attach score
            narrowed: list[dict[str, Any]] = []
            for r in results:
                idx = r.get("index")
                score = r.get("relevance_score")
                if idx is None or idx >= len(candidates):
                    continue
                c = dict(candidates[idx])
                c["cohere_score"] = float(score) if score is not None else 0.0
                narrowed.append(c)
            return narrowed, None
    except Exception as e:  # noqa: BLE001
        return candidates, f"cohere call failed: {type(e).__name__}: {str(e)[:120]}"


# --------------------------------------------------------------------------- #
# LLM re-rank                                                                  #
# --------------------------------------------------------------------------- #


async def _llm_rerank(
    persona: Persona,
    candidates: list[dict[str, Any]],
    k: int,
    reranker_spec: str | None = None,
    intent: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Use the configured re-ranker LLM to score and rationalise each candidate.

    If ``intent`` carries multi-turn constraints (budget, recipient, category),
    we fold them explicitly into the prompt so the re-ranker honours them.

    Returns: (ranked_items, fallback_reason).
        fallback_reason is None on full LLM rerank, or a short string when we
        had to degrade to pre-rank order (e.g. NaijaReviewer-8B is a Task A
        fine-tune and emits prose instead of strict JSON for ranking).
    """
    spec = reranker_spec or settings.task2_reranker
    client = get_llm_client(spec)

    # NaijaReviewer-8B is a review-generation fine-tune; the rerank JSON
    # contract is out-of-distribution for it. Emit a clear caveat instead of
    # silently producing degraded output.
    is_naija_reviewer = "naija-reviewer" in spec.lower()

    # Reference candidates by 1-based index, NOT by echoing the product_id.
    # Long Jumia slug IDs get mangled or hallucinated by the LLM; an integer
    # index is impossible to mangle and forces the model to pick from the
    # actual candidate set (no inventing plausible-but-absent products).
    candidate_lines = "\n".join(
        f"[{i + 1}] title={c.get('title','')[:90]} | "
        f"category={c.get('category','')} | price=₦{c.get('price_naira','?')}"
        for i, c in enumerate(candidates)
    )

    system = (
        "You are recommending products to a Nigerian user. You are given the user's "
        "persona (cognitive dimensions + register + aspect priorities), optional "
        "conversation constraints from prior turns, and a numbered candidate list. "
        "Score each candidate 0.0–1.0 for fit. Be sensitive to register, communal vs "
        "individual framing, hedonic vs utilitarian disposition, the aspects the user "
        "emphasises, AND any explicit budget / recipient / category constraints from "
        "prior turns. You MUST only choose from the numbered candidates given — never "
        "invent a product that is not in the list. Return STRICT JSON."
    )

    constraints_block = ""
    convo_summary = (intent or {}).get("summary", "") if intent else ""
    constraints = (intent or {}).get("constraints", []) if intent else []
    if constraints:
        constraints_block = (
            f"\nExplicit constraints extracted from conversation:\n  - "
            + "\n  - ".join(constraints)
            + "\nCandidates that violate a HARD constraint (e.g. price > budget) "
              "must be scored ≤ 0.30. Mention the constraint in the rationale."
        )
    if convo_summary:
        constraints_block += f"\nConversation history (most-recent last):\n{convo_summary}"

    prompt = f"""
Persona:
- register_tier: {persona.register_tier.value}
- register_markers: {persona.register_markers}
- hedonic_utilitarian: {persona.hedonic_utilitarian:.2f}  (0=utility, 1=hedonic)
- communal_individual: {persona.communal_individual:.2f}  (0=individual, 1=communal)
- aspect_priority top 3: {persona.primary_aspects(top_k=3)}
- history_count: {persona.history_count} {"(cold-start)" if persona.history_count < 3 else ""}
{constraints_block}

Candidates:
{candidate_lines}

Return ONLY this JSON (no markdown fences, no prose before or after):
{{"ranked":[{{"index":3,"score":0.92,"rationale":"6-15 word reason"}}]}}

"index" is the [N] number of the candidate above. Use ONLY indices that appear
in the list. Rank from BEST fit to WORST. Include the top {min(k * 2, 15)}
candidates only (not all {len(candidates)}). Score in [0.0, 1.0]. Keep each
rationale ≤ 15 words.
""".strip()

    fallback_reason: str | None = None
    try:
        result = await client.complete_json(
            prompt=prompt, system=system, max_tokens=3500, temperature=0.4
        )
        ranked_raw = result.get("ranked", [])
        if not isinstance(ranked_raw, list) or len(ranked_raw) == 0:
            raise LLMError(f"reranker returned empty/invalid 'ranked' field")
    except LLMError as exc:
        fallback_reason = (
            f"Re-ranker '{spec}' did not return parseable JSON ({str(exc)[:80]}). "
            + (
                "NaijaReviewer-8B is a Task A (review-generation) fine-tune and "
                "emits prose, not the strict JSON contract this Task B "
                "re-ranker expects. Pre-rank score used instead. For best Task B "
                "results pick Claude or GPT-4o as re-ranker."
                if is_naija_reviewer
                else "Pre-rank score (similarity + popularity + aspect-match) used instead."
            )
        )
        logger.warning("LLM re-rank fallback fired: %s", fallback_reason)
        fallback_items = [
            {
                "product_id": c["product_id"],
                "title": c.get("title"),
                "price_naira": c.get("price_naira"),
                "category": c.get("category"),
                "score": float(c["prerank_score"]),
                "rationale": (
                    f"Pre-rank: similarity={c.get('similarity',0):.2f}, "
                    f"popularity={c.get('popularity',0):.2f}, "
                    f"aspect-match score-contribution. LLM re-rank fell back."
                ),
                "serendipity_score": _serendipity(c, persona),
            }
            for c in candidates[:k]
        ]
        return fallback_items, fallback_reason

    # Hydrate by the 1-based index the model returned. Index is robust to
    # ID-mangling and forces selection from the actual candidate set. We keep
    # a product_id path for backwards-compat in case a model still echoes ids.
    def _norm(pid: str) -> str:
        return "".join(ch for ch in str(pid).lower() if ch.isalnum())

    by_id = {c["product_id"]: c for c in candidates}
    by_norm = {_norm(c["product_id"]): c for c in candidates}
    seen: set[str] = set()
    hydrated: list[dict[str, Any]] = []
    for item in ranked_raw:
        c = None
        idx = item.get("index")
        if isinstance(idx, (int, float)) and 1 <= int(idx) <= len(candidates):
            c = candidates[int(idx) - 1]
        elif item.get("product_id") is not None:  # backwards-compat
            pid = item["product_id"]
            c = by_id.get(pid) or by_norm.get(_norm(pid))
        if not c or c["product_id"] in seen:
            continue
        seen.add(c["product_id"])
        hydrated.append(
            {
                "product_id": c["product_id"],
                "title": c.get("title"),
                "price_naira": c.get("price_naira"),
                "category": c.get("category"),
                "score": float(item.get("score", 0.0)),
                "rationale": item.get("rationale", ""),
                "serendipity_score": _serendipity(c, persona),
            }
        )

    # Safety net: reranker returned a non-empty list but nothing hydrated.
    # With index-based referencing this should be rare; keep the net so we
    # never return an empty recommendation set.
    if not hydrated:
        fallback_reason = (
            "reranker returned no valid candidate indices; fell back to pre-rank order"
        )
        logger.warning("LLM re-rank hydration empty: %s", fallback_reason)
        hydrated = [
            {
                "product_id": c["product_id"],
                "title": c.get("title"),
                "price_naira": c.get("price_naira"),
                "category": c.get("category"),
                "score": float(c.get("prerank_score", 0.0)),
                "rationale": "Closest match by similarity + popularity + aspect fit.",
                "serendipity_score": _serendipity(c, persona),
            }
            for c in candidates[:k]
        ]

    return hydrated, fallback_reason


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
