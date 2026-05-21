"""B2B — businesses connect to the platform and embed a recommendations widget.

A business registers (name, website, brand colour, default category) and gets a
`business_id`. They drop an <iframe> embed snippet on their site; the widget
calls /b2b/recommend to serve persona-aware product recommendations from our
engine, branded for them. B2C users get the same engine via ShopEasy.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import PROJECT_ROOT
from app.rag import pinecone_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/b2b", tags=["b2b"])

_DB = PROJECT_ROOT / "data" / "profiles.db"  # shared db, separate table


def _conn() -> sqlite3.Connection:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(_DB)
    c.execute(
        """CREATE TABLE IF NOT EXISTS businesses (
            id TEXT PRIMARY KEY, name TEXT, config TEXT, created_at REAL
        )"""
    )
    return c


class BusinessRegister(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    website: str | None = None
    brand_color: str = Field(default="#008751")  # Nigerian green default
    default_category: str | None = None


class B2BRecommendRequest(BaseModel):
    business_id: str
    query: str = Field(default="", max_length=200)
    k: int = Field(default=8, ge=1, le=24)


@router.post("/register")
async def register_business(req: BusinessRegister) -> dict[str, Any]:
    bid = "biz_" + uuid.uuid4().hex[:12]
    config = req.model_dump()
    with _conn() as c:
        c.execute("INSERT INTO businesses (id, name, config, created_at) VALUES (?,?,?,?)",
                  (bid, req.name, json.dumps(config), time.time()))
        c.commit()
    return {"business_id": bid, "config": config}


@router.get("/{business_id}")
async def get_business(business_id: str) -> dict[str, Any]:
    with _conn() as c:
        row = c.execute("SELECT name, config FROM businesses WHERE id=?", (business_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="business not found")
    return {"business_id": business_id, "name": row[0], "config": json.loads(row[1])}


@router.post("/recommend")
async def b2b_recommend(req: B2BRecommendRequest) -> dict[str, Any]:
    """Serve recommendations for a business's embedded widget. If no query is
    given, fall back to the business's default category (a 'popular picks' feed)."""
    with _conn() as c:
        row = c.execute("SELECT config FROM businesses WHERE id=?", (req.business_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="business not found")
    config = json.loads(row[0])
    if not pinecone_store.pinecone_available() or pinecone_store.index_count() == 0:
        raise HTTPException(status_code=503, detail="product index unavailable")
    query = req.query.strip() or config.get("default_category") or "popular products"
    products = pinecone_store.query_products(query, top_k=req.k, threshold=0.05)
    return {
        "query": query,
        "products": [
            {
                "product_id": p.get("product_id"), "title": p.get("title"),
                "category": p.get("category"), "price_naira": p.get("price_naira"),
            }
            for p in products
        ],
    }
