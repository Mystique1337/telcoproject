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
    """Return candidate products as dicts of metadata."""
    collection = get_product_collection()
    n_in_index = collection.count()

    if n_in_index == 0:
        logger.info("chroma empty — loading sample products bundle")
        return _load_sample_products(domain=domain, limit=top_k)

    # Path 1: explicit candidate set
    if candidate_set:
        result = collection.get(ids=candidate_set, include=["metadatas", "documents"])
        return [_meta_to_candidate(m) for m in (result.get("metadatas") or [])]

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
