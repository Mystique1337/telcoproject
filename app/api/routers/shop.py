"""ShopEasy — Task B shopper-facing storefront endpoints.

POST /shop/search          { query, k }              -> ranked products
POST /shop/visual-search   { image_base64, mime, k } -> detected phrase + products
GET  /shop/product/{id}    -> single product detail (for the order page)
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.agents.panel_agent import load_panel_personas
from app.agents.recommend_agent import _llm_rerank, _mmr_rerank, _prerank
from app.agents.visual_search import describe_product_image
from app.api.schemas.persona import Persona
from app.rag import pinecone_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/shop", tags=["shopeasy"])


def _to_card(p: dict[str, Any]) -> dict[str, Any]:
    return {
        "product_id": p.get("product_id"),
        "title": p.get("title"),
        "category": p.get("category"),
        "price_naira": p.get("price_naira"),
        "description": (p.get("description") or "")[:400],
        "seller": p.get("seller") or p.get("brand") or None,
        "score": round(float(p.get("score", p.get("similarity", 0.0))), 3),
        "rationale": p.get("rationale"),
    }


async def _personalize(
    products: list[dict[str, Any]], persona_id: str | None,
    profile_id: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Re-rank retrieved products for the active persona — either a logged-in
    user's stored profile persona (profile_id) or a catalog persona (persona_id).
    Returns (products, persona_info). Falls back to retrieval order on failure."""
    if not products:
        return products, None
    persona = None
    if profile_id:
        from app.api.routers.auth import persona_for_profile
        pd = persona_for_profile(profile_id)
        if pd:
            try:
                persona = Persona(**pd)
            except Exception:  # noqa: BLE001
                persona = None
    if persona is None and persona_id:
        personas = load_panel_personas([persona_id])
        persona = personas[0] if personas else None
    if persona is None:
        return products, None
    info = {
        "user_id": persona.user_id,
        "register_tier": persona.register_tier.value,
        "demographics": persona.demographics or {},
    }
    try:
        ranked = _prerank(list(products), persona, cold_start=persona.history_count < 3)
        out, _fb = await _llm_rerank(persona, ranked[:20], k=20, reranker_spec=None)
        out = _mmr_rerank(out, lambda_param=0.7)
        return out, info
    except Exception as e:  # noqa: BLE001
        logger.warning("persona rerank failed (%s); using retrieval order", e)
        return products, info


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    k: int = Field(default=12, ge=1, le=40)
    persona_id: str | None = None
    profile_id: str | None = None


class VisualSearchRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 (no data: prefix) of the image")
    mime: str = Field(default="image/jpeg")
    k: int = Field(default=12, ge=1, le=40)
    persona_id: str | None = None
    profile_id: str | None = None
    note: str | None = Field(default=None, max_length=200,
                             description="Optional text typed alongside the image, e.g. 'but in red, cheaper'.")


@router.post("/search")
async def search(req: SearchRequest) -> dict[str, Any]:
    if not pinecone_store.pinecone_available() or pinecone_store.index_count() == 0:
        raise HTTPException(status_code=503, detail="product index unavailable")
    products = pinecone_store.query_products(req.query, top_k=max(req.k, 20), threshold=0.05)
    products, persona = await _personalize(products, req.persona_id, req.profile_id)
    return {"query": req.query, "persona": persona,
            "products": [_to_card(p) for p in products[:req.k]]}


@router.post("/visual-search")
async def visual_search(req: VisualSearchRequest) -> dict[str, Any]:
    if not pinecone_store.pinecone_available() or pinecone_store.index_count() == 0:
        raise HTTPException(status_code=503, detail="product index unavailable")
    try:
        detected = await describe_product_image(req.image_base64, req.mime)
    except Exception as exc:  # noqa: BLE001
        logger.exception("visual search vision step failed")
        raise HTTPException(status_code=502, detail=f"image understanding failed: {exc}") from exc
    if not detected:
        raise HTTPException(status_code=422, detail="could not interpret the image")
    # Fold in any text the shopper typed with the photo ("…but cheaper / in red").
    query = f"{detected}. {req.note.strip()}" if req.note and req.note.strip() else detected
    products = pinecone_store.query_products(query, top_k=max(req.k, 20), threshold=0.05)
    products, persona = await _personalize(products, req.persona_id, req.profile_id)
    return {"detected": detected, "query": query, "persona": persona,
            "products": [_to_card(p) for p in products[:req.k]]}


# In-memory thumbnail cache: normalized query -> image url (or "" if none found).
_IMG_CACHE: dict[str, str] = {}


@router.get("/image")
async def product_image(q: str = Query(..., min_length=1)) -> dict[str, Any]:
    """Resolve a relevant product thumbnail for a query via Openverse (keyless
    Creative-Commons image search). Cached in-memory so repeat lookups are
    instant. Returns {url} (url may be null if nothing relevant was found —
    the client then shows a category-icon tile)."""
    key = q.lower().strip()[:120]
    if key in _IMG_CACHE:
        return {"url": _IMG_CACHE[key] or None}

    # Meaningful query tokens (drop hyphen-joins, units, pure numbers, stopwords).
    _STOP = {"and", "the", "for", "with", "set", "pcs", "pack", "size", "new",
             "quality", "original", "product", "ladies", "men", "women"}
    raw = q.lower().replace("-", " ").replace(",", " ")
    qtokens = {
        w for w in raw.split()
        if len(w) > 2 and not w.isdigit() and w not in _STOP
        and not any(ch.isdigit() for ch in w)  # drop "256gb", "5000mah" etc.
    }
    # Search a clean phrase; over-fetch and pick the result whose title/tags
    # actually overlap the product words — so we never show an unrelated image.
    search_q = " ".join(list(qtokens)[:6]) or q
    url: str | None = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.openverse.org/v1/images/",
                params={"q": search_q, "page_size": 8},
                headers={"User-Agent": "InsideNaija-ShopEasy/1.0"},
            )
            if r.status_code == 200:
                best_score = 0
                for res in r.json().get("results", []):
                    hay = (res.get("title") or "").lower()
                    hay += " " + " ".join(
                        (t.get("name") or "") for t in (res.get("tags") or []) if isinstance(t, dict)
                    ).lower()
                    haytok = set(hay.replace("-", " ").replace(",", " ").split())
                    score = len(qtokens & haytok)
                    if score > best_score:
                        best_score = score
                        url = res.get("thumbnail") or res.get("url")
                # Require at least one real keyword overlap — else fall back to
                # the category-icon tile on the client (no irrelevant photos).
                if best_score < 1:
                    url = None
    except Exception as e:  # noqa: BLE001
        logger.warning("openverse image lookup failed for %r: %s", q, e)
    _IMG_CACHE[key] = url or ""
    return {"url": url}


@router.get("/photo")
async def lifestyle_photo(q: str = Query(..., min_length=1)) -> dict[str, Any]:
    """Full-size lifestyle/section photo for the marketing site (Openverse).
    Cached. Returns {url} (full image, not thumbnail)."""
    key = "photo:" + q.lower().strip()[:120]
    if key in _IMG_CACHE:
        return {"url": _IMG_CACHE[key] or None}
    url: str | None = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.openverse.org/v1/images/",
                params={"q": q, "page_size": 1, "aspect_ratio": "wide"},
                headers={"User-Agent": "InsideNaija/1.0"},
            )
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    url = results[0].get("url") or results[0].get("thumbnail")
    except Exception as e:  # noqa: BLE001
        logger.warning("openverse photo lookup failed for %r: %s", q, e)
    _IMG_CACHE[key] = url or ""
    return {"url": url}


@router.get("/product/{product_id}")
async def product_detail(product_id: str) -> dict[str, Any]:
    """Fetch one product by id (for the order page). Resolves via a title-ish
    query against the index, then exact-id match."""
    if not pinecone_store.pinecone_available():
        raise HTTPException(status_code=503, detail="product index unavailable")
    # The id is a slug of the title — turn it back into a query to find it.
    q = product_id.replace("-", " ").lower()
    products = pinecone_store.query_products(q, top_k=20, threshold=0.0)
    exact = next((p for p in products if p.get("product_id") == product_id), None)
    chosen = exact or (products[0] if products else None)
    if not chosen:
        raise HTTPException(status_code=404, detail="product not found")
    return _to_card(chosen)
