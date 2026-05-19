"""Chroma vector-store wrapper.

Single source of truth for the product index. Use `get_product_collection()` to
access; the collection is lazily created on first call.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logger = logging.getLogger(__name__)

_PRODUCT_COLLECTION = "products_v1"


@lru_cache(maxsize=1)
def get_chroma_client() -> chromadb.ClientAPI:
    """Return a singleton Chroma client.

    Uses an in-process PersistentClient pointing at `settings.chroma_path`.
    For docker-compose deployments where chroma runs as a separate service,
    switch to `HttpClient(host=..., port=...)` — env-flag controlled.
    """
    settings = get_settings()
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(settings.chroma_path),
        settings=ChromaSettings(anonymized_telemetry=False),
    )


def get_product_collection() -> chromadb.Collection:
    """Get or create the product collection."""
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=_PRODUCT_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )


def _coerce(v, default, kind):
    """Chroma metadata values must be str/int/float/bool (no None). Coerce."""
    if v is None:
        return default
    if kind is float:
        try:
            return float(v)
        except (ValueError, TypeError):
            return default
    if kind is int:
        try:
            return int(v)
        except (ValueError, TypeError):
            return default
    return str(v) if v is not None else default


def add_products(
    products: list[dict[str, str]],
    embeddings: list[list[float]],
) -> None:
    """Bulk-insert products into the index. Sanitises None values which
    Chroma rejects with `validate_metadata` errors."""
    if not products:
        return
    collection = get_product_collection()
    collection.add(
        ids=[str(p["product_id"]) for p in products],
        embeddings=embeddings,
        documents=[f"{p.get('title','')} — {p.get('description','')}" for p in products],
        metadatas=[
            {
                "product_id": _coerce(p.get("product_id"), "", str),
                "title": _coerce(p.get("title"), "", str),
                "category": _coerce(p.get("category"), "", str),
                "domain": _coerce(p.get("domain"), "jumia", str),
                "price_naira": _coerce(p.get("price_naira"), 0.0, float),
                "popularity": _coerce(p.get("popularity"), 0.5, float),
            }
            for p in products
        ],
    )
    logger.info("indexed %d products", len(products))
