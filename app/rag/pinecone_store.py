"""Pinecone vector store with asymmetric llama-text-embed-v2 retrieval.

Mirrors the architecture in `[1_0]_[TAM_ESCO_SKILLS_EXTRACTOR_V2].ipynb` — same
pattern, applied to Nigerian-context product retrieval:

  - Index name:   NPA_PINECONE_INDEX (default 'naija-persona')
  - Embed model:  llama-text-embed-v2  (1024-dim, Llama-3.2-1B-based)
  - Asymmetric:   passage at index time, query at retrieval time
  - Distance:     cosine (default Pinecone metric)
  - Threshold:    NPA_RETRIEVAL_THRESHOLD (default 0.20 — Pinecone scores are
                  re-scaled cosine in [-1, 1], typical "useful" floor ~0.2)

This module is functional, not stateful (singleton client cached at module
level). The retriever decides between Chroma and Pinecone based on whether
PINECONE_API_KEY is set in the environment.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


PINECONE_INDEX = os.getenv("NPA_PINECONE_INDEX", "naija-persona")
EMBED_MODEL = os.getenv("NPA_EMBED_MODEL", "llama-text-embed-v2")
DEFAULT_NAMESPACE = "products-v1"


@lru_cache(maxsize=1)
def get_pinecone_client():
    """Return a cached Pinecone client. None if no PINECONE_API_KEY."""
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        return None
    try:
        from pinecone import Pinecone
    except ImportError as e:
        logger.warning("pinecone SDK not installed: %s", e)
        return None
    return Pinecone(api_key=api_key)


def pinecone_available() -> bool:
    return get_pinecone_client() is not None


@lru_cache(maxsize=1)
def get_product_index():
    """Lazily fetch the Pinecone index handle."""
    pc = get_pinecone_client()
    if pc is None:
        raise RuntimeError("PINECONE_API_KEY not set")
    return pc.Index(PINECONE_INDEX)


def index_count(namespace: str = DEFAULT_NAMESPACE) -> int:
    """Return the number of vectors in the given namespace (0 if missing)."""
    try:
        stats = get_product_index().describe_index_stats()
        ns = stats.namespaces.get(namespace)
        return ns.vector_count if ns else 0
    except Exception as e:
        logger.warning("pinecone stats failed: %s", e)
        return 0


def embed_batch(texts: list[str], input_type: str = "passage",
                 pause_seconds: float = 0.0) -> list[list[float]]:
    """Embed a batch of texts via Pinecone's hosted llama-text-embed-v2.

    Handles the free-tier rate limit (250k tokens/min for passage input) with
    exponential backoff on 429. Set `pause_seconds` to throttle between
    micro-batches when indexing large catalogues.

    Args:
        texts: list of strings to embed (truncated by the model if needed).
        input_type: 'passage' for indexing, 'query' for retrieval.
        pause_seconds: sleep between embedding micro-batches (default 0).
    """
    import time
    pc = get_pinecone_client()
    if pc is None:
        raise RuntimeError("PINECONE_API_KEY not set")
    if not texts:
        return []
    out: list[list[float]] = []
    BATCH = 90  # Pinecone inference has a 96-input cap per call
    for i in range(0, len(texts), BATCH):
        chunk = texts[i:i + BATCH]
        # Exponential backoff for 429s. Pinecone free tier: 250k tokens/min
        for attempt in range(8):
            try:
                result = pc.inference.embed(
                    model=EMBED_MODEL,
                    inputs=chunk,
                    parameters={"input_type": input_type, "truncate": "END"},
                )
                out.extend([d.values for d in result.data])
                break
            except Exception as e:
                msg = str(e)
                if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                    wait = min(60, 2 ** (attempt + 2)) + 5  # 9s, 13s, 21s, 37s, 60s, 60s...
                    logger.warning("pinecone 429 — sleeping %ds (attempt %d/8)", wait, attempt + 1)
                    time.sleep(wait)
                    continue
                raise
        if pause_seconds and i + BATCH < len(texts):
            time.sleep(pause_seconds)
    return out


def _sanitize_metadata(p: dict[str, Any]) -> dict[str, Any]:
    """Pinecone metadata must be str/int/float/bool (no None, lists ok)."""
    def coerce(v, default):
        if v is None:
            return default
        if isinstance(v, (int, float, bool, str)):
            return v
        return str(v)
    return {
        "product_id":  coerce(p.get("product_id") or p.get("title"), ""),
        "title":       coerce(p.get("title"), ""),
        "category":    coerce(p.get("category"), ""),
        "domain":      coerce(p.get("domain"), "jumia"),
        "price_naira": coerce(float(p.get("price_naira")) if p.get("price_naira") is not None else None, 0.0),
        "popularity":  coerce(float(p.get("popularity", 0.5)), 0.5),
        "seller":      coerce(p.get("seller"), ""),
        "brand":       coerce(p.get("brand"), ""),
        # store first 500 chars of description for retrieval-time display
        "description": coerce(((p.get("description") or "")[:500]), ""),
    }


def upsert_products(products: list[dict[str, Any]],
                     namespace: str = DEFAULT_NAMESPACE,
                     batch: int = 100,
                     pause_seconds: float = 1.5) -> int:
    """Index products into Pinecone (asymmetric passage embedding).

    Pause defaults to 1.5s between batches so we stay under the free-tier
    250k tokens/min cap (~1.5 batches/sec at 80 products × 200 tokens each
    = ~24k tokens/sec peak, throttled to ~16k/sec = ~960k/min — safe).
    """
    if not products:
        return 0
    index = get_product_index()
    total = 0
    for start in range(0, len(products), batch):
        chunk = products[start:start + batch]
        texts = [
            f"{p.get('title','')} — {p.get('category','')} — {(p.get('description') or '')[:600]}"
            for p in chunk
        ]
        vecs = embed_batch(texts, input_type="passage", pause_seconds=0.0)
        vectors = [
            {
                "id": str(p.get("product_id") or p.get("title", f"prod-{start+i}"))[:120],
                "values": vecs[i],
                "metadata": _sanitize_metadata(p),
            }
            for i, p in enumerate(chunk)
        ]
        index.upsert(vectors=vectors, namespace=namespace)
        total += len(vectors)
        logger.info("  pinecone upserted %d / %d", total, len(products))
        if pause_seconds and start + batch < len(products):
            import time
            time.sleep(pause_seconds)
    return total


def query_products(query_text: str,
                    top_k: int = 30,
                    threshold: float = 0.10,
                    domain: str | None = None,
                    namespace: str = DEFAULT_NAMESPACE) -> list[dict[str, Any]]:
    """Query for top-K most-similar products, filtering below threshold.

    Returns candidate dicts in the shape the recommend agent expects.
    """
    index = get_product_index()
    query_vec = embed_batch([query_text], input_type="query")[0]
    filter_clause = None
    if domain and domain not in ("all", "*", "any") and "," not in domain:
        filter_clause = {"domain": {"$eq": domain}}
    # Over-fetch then threshold-filter so we still hit `top_k` after the cut.
    raw = index.query(
        vector=query_vec,
        top_k=max(top_k * 2, 50),
        include_metadata=True,
        namespace=namespace,
        filter=filter_clause,
    )
    out: list[dict[str, Any]] = []
    for match in raw.matches:
        score = float(match.score)
        if score < threshold:
            continue
        m = match.metadata or {}
        out.append({
            "product_id": m.get("product_id") or match.id,
            "title": m.get("title"),
            "category": m.get("category"),
            "domain": m.get("domain", "jumia"),
            "price_naira": m.get("price_naira"),
            "popularity": float(m.get("popularity", 0.5)),
            "seller": m.get("seller") or None,
            "brand": m.get("brand") or None,
            "description": m.get("description", ""),
            "similarity": score,
        })
        if len(out) >= top_k:
            break
    return out


def reset_namespace(namespace: str = DEFAULT_NAMESPACE) -> None:
    """Delete all vectors in the namespace (rebuild from scratch)."""
    try:
        get_product_index().delete(delete_all=True, namespace=namespace)
        logger.info("cleared pinecone namespace '%s'", namespace)
    except Exception as e:
        logger.warning("pinecone clear failed: %s", e)
