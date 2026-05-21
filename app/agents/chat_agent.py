"""Conversational shopping agent.

Single endpoint that holds a multi-turn conversation with the user, deciding
each turn whether to:

  - ASK a clarifying question (missing budget / category / recipient / occasion)
  - RECOMMEND products (enough info to retrieve + rank with hard filters)
  - REFINE (user wants alternatives or to swap a constraint)

This is the real-product version of /recommend — closer to how a Jumia
shopping assistant or a Bolt-Food concierge would actually feel.

Architecture:

   user turn N
     │
     ▼
   1. Constraint extractor (regex + LLM)
        → budget_ngn, category, recipient, brand_pref, age_target, exclude[]
     │
     ▼
   2. Action decision (LLM, JSON)
        → action ∈ {ask, recommend, refine, clarify}
        → if 'ask': question to send back
        → if 'recommend': filters to apply to retrieval
     │
     ▼
   3a. ASK  → return {message, action: "ask"}
   3b. RECOMMEND → retrieve_candidates with HARD filters
                     → LLM re-rank
                     → MMR diversity
                     → return {message, recommendations, action: "recommend"}
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from app.api.schemas.persona import Persona, RegisterTier
from app.config import get_settings
from app.llm import get_llm_client
from app.llm.client import LLMError
from app.rag import pinecone_store
from app.rag.retriever import retrieve_candidates
from app.agents.recommend_agent import (
    _llm_rerank,
    _mmr_rerank,
    _prerank,
    _is_cold_start,
)

logger = logging.getLogger(__name__)
settings = get_settings()

# Nigerian-language support for the conversational flow. When `language` is set,
# the orchestrator replies directly in that language (the model does these well).
_LANG_NAMES: dict[str, str] = {"yoruba": "Yoruba", "hausa": "Hausa", "igbo": "Igbo"}
_WELCOME_BY_LANG: dict[str, str] = {
    "yoruba": "Ẹ ku abọ! Kí ni ẹ fẹ́ ra lónìí?",
    "hausa": "Barka da zuwa! Me kuke son saya yau?",
    "igbo": "Nnọọ! Gịnị ka ị chọrọ ịzụ taa?",
}


# --------------------------------------------------------------------------- #
# Constraint extraction (deterministic regex first, LLM fallback)              #
# --------------------------------------------------------------------------- #

# Naira amount: ₦100k / 100,000 / N100k / 200000 naira / 5k / 50 thousand
_BUDGET_RE = re.compile(
    r"(?:under|below|max|maximum|budget(?:\s+of)?|less\s+than|up\s+to|<=?|≤)\s*"
    r"₦?\s*([\d,]+(?:\.\d+)?)\s*"
    r"(k|thousand|m|million)?",
    re.IGNORECASE,
)

_RECIPIENT_RE = re.compile(
    r"for\s+(?:my\s+)?(mum|mother|mama|dad|father|papa|wife|husband|sister|brother|"
    r"son|daughter|child|kids?|baby|friend|aunty|uncle|colleague|boss|niece|nephew|"
    r"grandma|grandpa|girlfriend|boyfriend|mother\s+in\s+law|father\s+in\s+law|in-?law)",
    re.IGNORECASE,
)

_CATEGORY_HINTS = {
    "phones-and-tablets": ["phone", "smartphone", "tablet", "ipad", "android phone"],
    "computing":          ["laptop", "computer", "pc", "macbook", "monitor", "keyboard"],
    "electronics":        ["tv", "television", "headphone", "earbuds", "speaker", "camera"],
    "appliances":         ["fridge", "freezer", "blender", "microwave", "iron",
                            "washing machine", "stove", "cooker", "fan", "ac",
                            "air conditioner"],
    "fashion":            ["shoes", "dress", "ankara", "agbada", "sneakers", "bag",
                            "perfume", "wristwatch", "watch", "shirt", "trousers",
                            "skirt", "gown", "abaya", "hijab"],
    "health-and-beauty":  ["makeup", "lipstick", "foundation", "skincare", "lotion",
                            "soap", "shampoo", "vitamin", "supplement"],
    "baby-products":      ["baby", "diaper", "nappy", "stroller", "pram", "crib"],
    "home-and-office":    ["chair", "table", "desk", "office", "lamp", "curtain",
                            "mattress", "bed", "wardrobe"],
    "gaming":             ["playstation", "ps4", "ps5", "xbox", "game", "controller"],
    "supermarket":        ["rice", "garri", "milk", "noodles", "indomie", "drink"],
    "musical-instruments":["guitar", "piano", "keyboard", "drum", "saxophone"],
}


def _coerce_naira(amount: str, unit: str | None) -> int | None:
    try:
        n = float(amount.replace(",", ""))
    except ValueError:
        return None
    u = (unit or "").lower()
    if u in ("k", "thousand"):
        n *= 1_000
    elif u in ("m", "million"):
        n *= 1_000_000
    return int(n)


def _extract_constraints(history: list[dict[str, str]]) -> dict[str, Any]:
    """Regex extractor over the full conversation. Most-recent wins."""
    budget: int | None = None
    recipient: str | None = None
    category: str | None = None
    keywords: list[str] = []

    # Read in order so later mentions override earlier ones
    for turn in history:
        content = (turn.get("content") or "").lower()
        if not content:
            continue

        m = _BUDGET_RE.search(content)
        if m:
            v = _coerce_naira(m.group(1), m.group(2))
            if v:
                budget = v

        m = _RECIPIENT_RE.search(content)
        if m:
            recipient = m.group(1).lower().strip()

        # Category — pick the LAST one that matches; only swap if a clearer
        # hint appears in this turn
        for cat, words in _CATEGORY_HINTS.items():
            if any(w in content for w in words):
                category = cat
                # collect specific keyword hits to bias retrieval
                for w in words:
                    if w in content and w not in keywords:
                        keywords.append(w)
                break

    return {
        "budget_ngn": budget,
        "recipient": recipient,
        "category": category,
        "keywords": keywords[:5],
    }


# --------------------------------------------------------------------------- #
# Action decision (LLM)                                                        #
# --------------------------------------------------------------------------- #

ACTION_SYSTEM = (
    "You are the orchestration layer of a Nigerian-context shopping concierge. "
    "Given a conversation so far and the constraints extracted so far, decide "
    "the next action. Return STRICT JSON. Do not include code fences."
)

ACTION_PROMPT = """Conversation so far (most-recent last):
{history_block}

Constraints extracted so far:
{constraints_block}

Decide the next action and return ONLY this JSON shape:

{{
  "action":       "ask" | "recommend" | "refine",
  "message":      "<one short sentence to send back to the user>",
  "question":     "<if action=ask, the SINGLE most important clarifying question>",
  "search_query": "<a SHORT, clean product-search phrase distilled from what the user wants, e.g. 'educational learning tablet for kids' — NO budget, NO filler words like 'I want', just the product intent. Required when action is recommend/refine.>",
  "filters":      {{
    "category":    "<jumia category slug if user has clearly indicated one, else null>",
    "max_price":   <integer Naira if user gave a budget, else null>,
    "min_price":   <integer Naira if user gave a floor, else null>,
    "exclude_ids": [<product ids the user already rejected, else []>]
  }}
}}

Rules:
- If the user has NOT specified a CATEGORY or BUDGET, you usually want action="ask".
- If they have both, action="recommend".
- If they explicitly asked for "more options" / "show me alternatives", action="refine".
- `search_query` must capture the actual product intent in 3-8 words, with NO
  budget figures and NO conversational filler. E.g. user said "I want toys ...
  kids ... 13 ... educational" → search_query="educational toys for kids".
- Your `message` should sound like a friendly Nigerian shopping assistant.
- For Pidgin / code-mixed users, you may use light Pidgin in the message
  (e.g. "abeg" / "no wahala" / "make I check well well") — match their register.
- Keep messages under 25 words. One question at a time.
"""


async def _decide_action(history: list[dict[str, str]],
                          constraints: dict[str, Any],
                          persona: Persona | None,
                          orchestrator_spec: str,
                          language: str | None = None) -> dict[str, Any]:
    """Ask the orchestrator LLM to pick the next action + craft the message."""
    history_block = "\n".join(
        f"  {t.get('role','user'):>10}: {t.get('content','')[:200]}" for t in history
    ) or "  (empty)"
    constraints_block = json.dumps(constraints, ensure_ascii=False)
    register = persona.register_tier.value if persona else "standard_english"

    prompt = ACTION_PROMPT.format(
        history_block=history_block,
        constraints_block=constraints_block,
    )
    if persona:
        prompt += f"\n\nUser register tier: {register} (match this in `message`)."
    lang_name = _LANG_NAMES.get((language or "").lower())
    if lang_name:
        prompt += (
            f"\n\nIMPORTANT: Write `message` and `question` ENTIRELY in {lang_name} "
            f"(correct orthography/diacritics, natural conversational {lang_name}). "
            f"Keep the JSON field names and `search_query` in English."
        )

    client = get_llm_client(orchestrator_spec)
    try:
        out = await client.complete_json(
            prompt=prompt, system=ACTION_SYSTEM, max_tokens=400, temperature=0.5,
        )
    except LLMError as e:
        logger.warning("decide_action LLM failed (%s); defaulting to ask", e)
        # Safe default: ask for budget if missing, else recommend
        if not constraints.get("budget_ngn"):
            return {
                "action": "ask",
                "message": "Got it — what's your budget?",
                "question": "What's your budget?",
                "filters": {"category": constraints.get("category"), "max_price": None,
                            "min_price": None, "exclude_ids": []},
            }
        return {
            "action": "recommend", "message": "Here are some options.",
            "question": None,
            "filters": {"category": constraints.get("category"),
                        "max_price": constraints.get("budget_ngn"),
                        "min_price": None, "exclude_ids": []},
        }
    # Coerce missing fields
    out.setdefault("filters", {})
    f = out["filters"]
    f.setdefault("category", constraints.get("category"))
    f.setdefault("max_price", constraints.get("budget_ngn"))
    f.setdefault("min_price", None)
    f.setdefault("exclude_ids", [])
    return out


# --------------------------------------------------------------------------- #
# Filtered retrieval                                                           #
# --------------------------------------------------------------------------- #

def _build_pinecone_filter(filters: dict[str, Any]) -> dict[str, Any] | None:
    """Convert orchestrator filters → Pinecone metadata filter clause."""
    clauses: list[dict[str, Any]] = []
    if filters.get("category"):
        clauses.append({"category": {"$eq": filters["category"]}})
    if filters.get("max_price"):
        # Some products have price_naira=0 (unknown). Don't filter those out by
        # accident — only enforce when the value is positive.
        clauses.append({"$or": [
            {"price_naira": {"$lte": float(filters["max_price"])}},
            {"price_naira": {"$eq": 0}},
        ]})
    if filters.get("min_price"):
        clauses.append({"price_naira": {"$gte": float(filters["min_price"])}})
    if filters.get("exclude_ids"):
        clauses.append({"product_id": {"$nin": list(filters["exclude_ids"])}})
    if not clauses:
        return None
    return {"$and": clauses} if len(clauses) > 1 else clauses[0]


async def _retrieve_with_filters(persona: Persona | None,
                                   history: list[dict[str, str]],
                                   filters: dict[str, Any],
                                   keywords: list[str],
                                   top_k: int = 30,
                                   search_query: str | None = None) -> list[dict[str, Any]]:
    """Query Pinecone with hard filters. Falls back to existing retriever if
    Pinecone isn't configured."""
    if not pinecone_store.pinecone_available() or pinecone_store.index_count() == 0:
        # Fall back to existing retriever logic
        if persona is None:
            persona = _default_persona(history)
        return await retrieve_candidates(
            persona=persona, domain="jumia",
            candidate_set=None, top_k=top_k,
        )

    # Prefer the orchestrator's distilled `search_query` (clean product intent,
    # no budget/filler). Fall back to USER-turns-only text if absent — never use
    # raw conversation incl. assistant scaffolding ("Type?"/"Age?") which pulls junk.
    if search_query:
        base = search_query
    else:
        base = " ".join(
            (t.get("content") or "") for t in history if t.get("role") == "user"
        )
    persona_hint = ""
    if persona:
        d = persona.demographics or {}
        if d.get("occupation"):
            persona_hint = f"for a {d['occupation']}"
    cat_hint = str(filters.get("category") or "")
    kw_str = " ".join(keywords) if keywords else ""
    query_text = f"{cat_hint} {base} {persona_hint} {kw_str}".strip()

    pc_filter = _build_pinecone_filter(filters)
    return pinecone_store.query_products(
        query_text=query_text, top_k=top_k, threshold=0.05,
        domain=None, namespace=pinecone_store.DEFAULT_NAMESPACE,
        # Pass through filter — extend pinecone_store.query_products signature
        # (handled below via kwargs on the index.query call).
    ) if pc_filter is None else _pinecone_query_with_filter(query_text, top_k, pc_filter)


def _pinecone_query_with_filter(query_text: str, top_k: int,
                                 filter_clause: dict[str, Any]) -> list[dict[str, Any]]:
    """Pinecone query with explicit metadata filter (used by chat agent)."""
    index = pinecone_store.get_product_index()
    qvec = pinecone_store.embed_batch([query_text], input_type="query")[0]
    raw = index.query(
        vector=qvec, top_k=max(top_k * 2, 50), include_metadata=True,
        namespace=pinecone_store.DEFAULT_NAMESPACE, filter=filter_clause,
    )
    out: list[dict[str, Any]] = []
    for m in raw.matches:
        if m.score < 0.05:
            continue
        md = m.metadata or {}
        out.append({
            "product_id": md.get("product_id") or m.id,
            "title": md.get("title"),
            "category": md.get("category"),
            "domain": md.get("domain", "jumia"),
            "price_naira": md.get("price_naira"),
            "popularity": float(md.get("popularity", 0.5)),
            "description": md.get("description", ""),
            "similarity": float(m.score),
        })
        if len(out) >= top_k:
            break
    return out


async def _retrieve_with_relaxation(
    persona: Persona | None,
    history: list[dict[str, str]],
    filters: dict[str, Any],
    keywords: list[str],
    top_k: int = 30,
    search_query: str | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Retrieve with progressive filter relaxation.

    The orchestrator often guesses a `category` label (e.g. "educational",
    "toys") that does not exist in the catalogue's fixed taxonomy, so a strict
    `category $eq` match returns zero rows even when semantically-relevant
    products exist. Rather than give up, we relax constraints in priority
    order, folding any dropped category into the semantic query so retrieval
    still biases toward it:

      1. Full filters (category + price).
      2. Drop the hard category filter, keep budget (most common fix).
      3. Drop price too — pure semantic, last resort.

    Returns (candidates, relaxation_steps). `relaxation_steps` is a list of
    human-readable strings describing what was loosened (empty if the strict
    filter worked).
    """
    steps: list[str] = []
    cat = filters.get("category")

    # Attempt 1 — strict
    cands = await _retrieve_with_filters(persona, history, filters, keywords, top_k,
                                          search_query=search_query)
    if cands:
        return cands, steps

    # Attempt 2 — drop category hard filter, keep it as a semantic hint + keep budget
    if cat:
        relaxed = {**filters, "category": None}
        kw2 = keywords + [str(cat)]
        cands = await _retrieve_with_filters(persona, history, relaxed, kw2, top_k,
                                              search_query=search_query)
        if cands:
            steps.append(
                f"there's no exact '{cat}' category in the catalogue, so I searched by meaning"
            )
            return cands, steps

    # Attempt 3 — drop price too (pure semantic, last resort)
    relaxed = {k: v for k, v in filters.items() if k not in ("category", "max_price")}
    kw2 = keywords + ([str(cat)] if cat else [])
    cands = await _retrieve_with_filters(persona, history, relaxed, kw2, top_k,
                                          search_query=search_query)
    if cands:
        if cat:
            steps.append(f"there's no exact '{cat}' category, so I searched by meaning")
        if filters.get("max_price"):
            steps.append("widened the search beyond the stated budget")
        return cands, steps

    return [], steps


def _default_persona(history: list[dict[str, str]]) -> Persona:
    """Build a minimal Persona when none is supplied (truly anonymous chat)."""
    return Persona(
        user_id="anon",
        register_tier=RegisterTier.NIGERIAN_ENGLISH,
        register_markers=[],
        register_confidence=0.5,
        hedonic_utilitarian=0.5,
        communal_individual=0.5,
        intensity_calibration={},
        aspect_priority={"value": 0.4, "quality": 0.3, "durability": 0.3},
        review_anchors=[],
        history_count=0,
    )


# --------------------------------------------------------------------------- #
# Top-level chat handler                                                       #
# --------------------------------------------------------------------------- #

async def chat_step(
    history: list[dict[str, str]],
    persona: Persona | None = None,
    orchestrator_spec: str | None = None,
    reranker_spec: str | None = None,
    include_reasoning: bool = False,
    k: int = 5,
    language: str | None = None,
) -> dict[str, Any]:
    """One turn of the conversational shopping flow.

    Returns:
        {
          action: "ask" | "recommend" | "refine",
          message: agent's reply (display in chat),
          recommendations: optional list (when action is recommend/refine),
          extracted_constraints: dict (visible for debugging),
          filters_applied: dict,
          reasoning_trace: optional,
          latency_ms: int,
        }
    """
    started = time.perf_counter()
    trace: list[dict[str, Any]] = []

    if not history:
        return {
            "action": "ask",
            "message": _WELCOME_BY_LANG.get(
                (language or "").lower(),
                "Welcome! What are you shopping for today?",
            ),
            "recommendations": [],
            "extracted_constraints": {},
            "filters_applied": {},
            "reasoning_trace": None,
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }

    orch_spec = orchestrator_spec or settings.task2_reranker
    rerank_spec = reranker_spec or orch_spec

    # Step 1: deterministic constraint extraction
    constraints = _extract_constraints(history)
    trace.append({
        "node": "extract_constraints",
        "summary": f"Regex pass: {constraints}",
        **constraints,
    })

    # Step 2: orchestrator picks action
    decision = await _decide_action(history, constraints, persona, orch_spec, language)
    action = decision.get("action", "ask")
    message = decision.get("message", "")
    question = decision.get("question")
    filters = decision.get("filters") or {}
    trace.append({
        "node": "decide_action",
        "summary": f"action={action}; filters={filters}",
        "action": action,
        "filters": filters,
        "orchestrator": orch_spec,
    })

    # Step 3a: ask only
    if action == "ask":
        return {
            "action": "ask",
            "message": message or question or "Could you tell me more?",
            "recommendations": [],
            "extracted_constraints": constraints,
            "filters_applied": filters,
            "reasoning_trace": trace if include_reasoning else None,
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }

    # Step 3b/c: retrieve + rank + return recs
    if persona is None:
        persona = _default_persona(history)
    search_query = decision.get("search_query")
    candidates, relaxation_steps = await _retrieve_with_relaxation(
        persona, history, filters, constraints.get("keywords", []),
        top_k=30, search_query=search_query,
    )
    trace.append({
        "node": "filtered_retrieval",
        "summary": (
            f"Pulled {len(candidates)} candidates "
            f"(category={filters.get('category')}, max_price={filters.get('max_price')}, "
            f"exclude={len(filters.get('exclude_ids', []))})"
            + (f"; relaxed: {'; '.join(relaxation_steps)}" if relaxation_steps else "")
        ),
        "n_candidates": len(candidates),
        "relaxation": relaxation_steps,
    })

    if not candidates:
        return {
            "action": "ask",
            "message": (
                "I searched the whole catalogue and still couldn't find a good "
                "match for that — could you try a different item or category? "
                "For example, tell me the brand or a similar product you have in mind."
            ),
            "recommendations": [],
            "extracted_constraints": constraints,
            "filters_applied": filters,
            "reasoning_trace": trace if include_reasoning else None,
            "latency_ms": int((time.perf_counter() - started) * 1000),
        }

    # Pre-rank → LLM re-rank → MMR
    candidates = _prerank(candidates, persona, cold_start=_is_cold_start(persona))
    intent = {"constraints": [f"{k}={v}" for k, v in constraints.items() if v]}
    ranked, fb_reason = await _llm_rerank(
        persona, candidates[:30], k=k, reranker_spec=rerank_spec, intent=intent,
    )
    ranked = _mmr_rerank(ranked, lambda_param=0.7)
    recommendations = [{**r, "rank": i + 1} for i, r in enumerate(ranked[:k])]
    trace.append({
        "node": "llm_rerank",
        "summary": f"Re-ranked via {rerank_spec}; fallback={'yes' if fb_reason else 'no'}",
        "fallback": fb_reason,
    })

    final_message = message or "Here are my top picks:"
    # The relaxation note is English; only prepend it when replying in English,
    # otherwise keep the orchestrator's in-language message intact.
    if relaxation_steps and not _LANG_NAMES.get((language or "").lower()):
        note = "I couldn't find an exact match — " + "; ".join(relaxation_steps) + "."
        final_message = f"{note} Here are the closest options:"

    return {
        "action": action,
        "message": final_message,
        "recommendations": recommendations,
        "extracted_constraints": constraints,
        "filters_applied": filters,
        "rerank_fallback_reason": fb_reason,
        "reasoning_trace": trace if include_reasoning else None,
        "latency_ms": int((time.perf_counter() - started) * 1000),
    }
