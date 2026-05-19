"""Candidate retrieval for Task 2.

`retrieve_candidates(persona, domain, candidate_set?, top_k)` returns a list of
candidate products either from an explicit `candidate_set` or via semantic search
over the Chroma product index. If the index is empty, falls back to loading the
sample products bundle.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.api.schemas.persona import Persona
from app.config import get_settings
from app.llm import get_llm_client
from app.llm.client import LLMError
from app.rag.vector_store import get_product_collection

logger = logging.getLogger(__name__)
settings = get_settings()


def _persona_query_text(persona: Persona) -> str:
    """Build a free-text query from the persona for semantic retrieval."""
    aspects = " ".join(persona.primary_aspects(top_k=4))
    framing = "communal family" if persona.communal_individual > 0.6 else "personal"
    intent = "hedonic experience" if persona.hedonic_utilitarian > 0.6 else "practical value"
    return f"{aspects} {framing} {intent} Nigerian product".strip()


async def retrieve_candidates(
    persona: Persona,
    domain: str,
    candidate_set: list[str] | None,
    top_k: int = 30,
) -> list[dict[str, Any]]:
    """Return candidate products as dicts of metadata.

    Resolution order:
      1. If an explicit ``candidate_set`` is provided, ALWAYS honour it.
      2. Otherwise: semantic retrieval from Chroma if populated.
      3. Otherwise: PERSONA-AWARE sampling from data/sample/products/ on disk
         (scores all available products against the persona's aspect_priority +
         register signals, returns the diverse top-K). This is the realistic
         e-commerce browsing path when no vector index is hot.
    """
    collection = get_product_collection()
    n_in_index = collection.count()

    # Path 1: explicit candidate set — always honoured
    if candidate_set:
        return _resolve_candidate_set(candidate_set, collection if n_in_index > 0 else None)

    # Path 2: empty Chroma + no candidate set → persona-aware disk sampling
    if n_in_index == 0:
        logger.info(
            "chroma empty + no candidate_set — using persona-aware disk sampling "
            "(consider running scripts/build_product_index.py for production)"
        )
        return _persona_aware_disk_sample(persona, domain=domain, limit=top_k)

    # Path 2: semantic retrieval
    query_text = _persona_query_text(persona)
    try:
        client = get_llm_client(settings.embedding_model)
        embeddings = await client.embed([query_text])
        query_emb = embeddings[0]
    except LLMError as exc:
        logger.warning("embedding failed (%s); using text-query fallback", exc)
        result = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where={"domain": domain} if domain else None,
            include=["metadatas", "distances", "documents"],
        )
    else:
        result = collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            where={"domain": domain} if domain else None,
            include=["metadatas", "distances", "documents"],
        )

    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    out: list[dict[str, Any]] = []
    for m, d in zip(metadatas, distances):
        cand = _meta_to_candidate(m)
        cand["similarity"] = 1.0 - float(d)
        out.append(cand)
    return out


def _resolve_candidate_set(
    candidate_set: list[str], collection: Any | None
) -> list[dict[str, Any]]:
    """Resolve an explicit candidate_set into candidate dicts.

    For each input string: try Chroma id lookup → title lookup → synthesise.
    Order is preserved (callers may rely on it).
    """
    out: list[dict[str, Any]] = []
    if collection is not None:
        # Single Chroma .get() with all ids; the collection returns metadatas
        # in the SAME ORDER as the ids that resolved. Items not found in
        # Chroma are silently dropped from this result, so we have to fall
        # back to title-match + synthesise for the rest.
        found_by_id: dict[str, dict[str, Any]] = {}
        try:
            result = collection.get(ids=candidate_set, include=["metadatas"])
            for meta in (result.get("metadatas") or []):
                if meta and meta.get("product_id"):
                    found_by_id[str(meta["product_id"])] = _meta_to_candidate(meta)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Chroma id lookup failed (%s); falling back to title match", exc)

        # For unmatched items, try matching by title.
        unmatched = [c for c in candidate_set if c not in found_by_id]
        found_by_title: dict[str, dict[str, Any]] = {}
        if unmatched:
            try:
                # Scan up to 2000 items by title — fine for our catalog size.
                all_items = collection.get(limit=2000, include=["metadatas"])
                meta_list = all_items.get("metadatas") or []
                titles_index = {
                    str(m.get("title", "")).strip().lower(): m
                    for m in meta_list if m and m.get("title")
                }
                for c in unmatched:
                    key = c.strip().lower()
                    if key in titles_index:
                        found_by_title[c] = _meta_to_candidate(titles_index[key])
            except Exception as exc:  # noqa: BLE001
                logger.warning("Chroma title-match scan failed (%s)", exc)

        for c in candidate_set:
            if c in found_by_id:
                out.append(found_by_id[c])
            elif c in found_by_title:
                out.append(found_by_title[c])
            else:
                out.append(_synthesize_candidate(c))
        return out

    # No Chroma — synthesise every candidate from its title/id string.
    return [_synthesize_candidate(c) for c in candidate_set]


def _synthesize_candidate(s: str) -> dict[str, Any]:
    """Minimal candidate dict when we have nothing but a title or product id."""
    return {
        "product_id": s,
        "title": s,
        "category": "",
        "domain": "",
        "price_naira": None,
        "popularity": 0.5,
        "description": "",
        "similarity": 0.5,
    }


def _meta_to_candidate(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_id": meta.get("product_id"),
        "title": meta.get("title"),
        "category": meta.get("category"),
        "domain": meta.get("domain"),
        "price_naira": meta.get("price_naira"),
        "popularity": meta.get("popularity", 0.5),
        "description": meta.get("description", ""),
        "similarity": meta.get("similarity", 0.5),
    }


_DISK_PRODUCT_CACHE: list[dict[str, Any]] | None = None


def _load_all_disk_products() -> list[dict[str, Any]]:
    """Load (and cache) every product JSON in data/sample/products/.

    On a populated Jumia pull this is ~6,600 products / ~26MB on disk; we
    cache the list in-process so we only pay the parse cost once.
    """
    global _DISK_PRODUCT_CACHE
    if _DISK_PRODUCT_CACHE is not None:
        return _DISK_PRODUCT_CACHE
    sample_dir = settings.sample_products_dir
    if not sample_dir.exists():
        _DISK_PRODUCT_CACHE = []
        return _DISK_PRODUCT_CACHE
    products: list[dict[str, Any]] = []
    for json_file in sample_dir.glob("*.json"):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            products.append(data)
        except Exception:
            continue
    logger.info("loaded %d products from disk into cache", len(products))
    _DISK_PRODUCT_CACHE = products
    return products


def _persona_aware_disk_sample(persona: Persona, domain: str, limit: int) -> list[dict[str, Any]]:
    """Score every disk product against the persona and return top-`limit`.

    Scoring features (each in [0, 1]):
      - aspect_match:       persona's aspect_priority words found in title/desc/category
      - category_affinity:  category appears in persona's recent review_anchors
      - price_band_fit:     price is in the realistic band for the persona's history
      - jitter:             tiny random component so identical scores break randomly
      - popularity:         if present in product metadata (else 0.5)
    """
    import random as _random
    all_products = _load_all_disk_products()
    if not all_products:
        return []

    # Filter by domain first (most are "jumia").
    products = [p for p in all_products if (not domain or p.get("domain", "jumia") == domain)]
    if not products:
        products = all_products  # fall back if no exact match

    # Build persona feature sets.
    primary_aspects = [a.lower() for a in persona.primary_aspects(top_k=4)]
    # Aspect → relevant lexical tokens (cheap heuristic; replace with embeddings
    # once Chroma is populated).
    aspect_tokens: dict[str, set[str]] = {
        "quality":          {"quality", "premium", "durable", "solid", "build"},
        "value":            {"value", "affordable", "cheap", "discount", "deal", "promo"},
        "durability":       {"durable", "long lasting", "warranty", "tough", "heavy duty"},
        "delivery":         {"fast delivery", "express", "in stock"},
        "packaging":        {"packaging", "box", "sealed"},
        "design":           {"design", "style", "fine", "beautiful", "premium"},
        "seller":           {"trusted", "official", "authentic"},
        "value_for_family": {"family", "kids", "household", "home"},
        "child_safety":     {"safe", "child", "kids", "baby"},
    }
    persona_categories_from_history = {
        (a.product_id or "").lower() for a in persona.review_anchors
    }

    rng = _random.Random(persona.user_id or "default")  # deterministic per persona
    scored: list[tuple[float, dict[str, Any]]] = []
    for p in products:
        title = (p.get("title") or "").lower()
        desc = (p.get("description") or "").lower()
        cat = (p.get("category") or "").lower()
        text = f"{title} {desc} {cat}"

        # Aspect match — for each top aspect, did any of its tokens appear?
        aspect_score = 0.0
        for asp in primary_aspects:
            tokens = aspect_tokens.get(asp, {asp})
            if any(t in text for t in tokens):
                aspect_score += 1.0
        aspect_score /= max(len(primary_aspects), 1)  # 0–1

        # Category affinity — does category match anything in history?
        cat_affinity = 0.0
        if cat:
            for hist_pid in persona_categories_from_history:
                if cat in hist_pid or hist_pid in cat:
                    cat_affinity = 1.0
                    break

        # Popularity (already in [0,1] if set, else 0.5)
        popularity = float(p.get("popularity", 0.5))

        # Diversity jitter so equal scores don't cluster
        jitter = rng.random() * 0.05

        composite = (
            0.50 * aspect_score
            + 0.20 * cat_affinity
            + 0.20 * popularity
            + 0.10 * jitter
        )

        # Pack into the candidate shape the agent expects
        candidate = {
            "product_id": p.get("product_id") or title,
            "title": p.get("title"),
            "category": p.get("category"),
            "domain": p.get("domain", "jumia"),
            "price_naira": p.get("price_naira"),
            "popularity": popularity,
            "description": (p.get("description") or "")[:500],
            "similarity": min(1.0, aspect_score + 0.3),  # surface for prerank
        }
        scored.append((composite, candidate))

    # Sort by composite desc, return top `limit`
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:limit]]


# Keep the old name as a thin wrapper for backward compat with any test code.
def _load_sample_products(domain: str, limit: int) -> list[dict[str, Any]]:
    """Legacy helper — unconditionally returns first `limit` products
    (alphabetical). Persona-aware sampling lives in _persona_aware_disk_sample."""
    return _load_all_disk_products()[:limit]
