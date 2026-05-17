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
         Each item is tried first as a Chroma id, then matched by title in
         Chroma metadata, then synthesised as a minimal {product_id, title}
         dict so the LLM re-ranker still has something to rank. Sample
         products are NEVER used to replace an explicit candidate set.
      2. Otherwise: semantic retrieval from Chroma if populated.
      3. Otherwise: fall back to the sample-products bundle.
    """
    collection = get_product_collection()
    n_in_index = collection.count()

    # Path 1: explicit candidate set — always honoured
    if candidate_set:
        return _resolve_candidate_set(candidate_set, collection if n_in_index > 0 else None)

    # Path 2: empty Chroma + no candidate set → sample fallback
    if n_in_index == 0:
        logger.info("chroma empty + no candidate_set — loading sample products bundle")
        return _load_sample_products(domain=domain, limit=top_k)

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


def _load_sample_products(domain: str, limit: int) -> list[dict[str, Any]]:
    """Day-1 fallback: read products from `data/sample/products/*.json`."""
    sample_dir = settings.sample_products_dir
    if not sample_dir.exists():
        logger.warning("sample products dir missing: %s", sample_dir)
        return []
    products: list[dict[str, Any]] = []
    for json_file in sorted(sample_dir.glob("*.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            logger.warning("could not parse %s", json_file)
            continue
        if domain and data.get("domain", "jumia") != domain:
            continue
        # Synthesise a tiny similarity score so the pre-ranker has something to work with
        data["similarity"] = 0.6
        data["popularity"] = data.get("popularity", 0.5)
        products.append(data)
        if len(products) >= limit:
            break
    return products
