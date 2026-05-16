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


def add_products(
    products: list[dict[str, str]],
    embeddings: list[list[float]],
) -> None:
    """Bulk-insert products into the index."""
    if not products:
        return
    collection = get_product_collection()
    collection.add(
        ids=[p["product_id"] for p in products],
        embeddings=embeddings,
        documents=[f"{p.get('title','')} — {p.get('description','')}" for p in products],
        metadatas=[
            {
                "product_id": p["product_id"],
                "title": p.get("title", ""),
                "category": p.get("category", ""),
                "domain": p.get("domain", "jumia"),
                "price_naira": p.get("price_naira", 0.0),
                "popularity": p.get("popularity", 0.5),
            }
            for p in products
        ],
    )
    logger.info("indexed %d products", len(products))
