"""Catalog endpoints — list the personas and products bundled with the repo.

Used by the React frontend to populate its persona / product pickers without
having to bundle JSON into the build. Cached at process start.
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/catalog", tags=["catalog"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PERSONAS_DIR = PROJECT_ROOT / "data" / "sample" / "personas"
PRODUCTS_DIR = PROJECT_ROOT / "data" / "sample" / "products"


@lru_cache(maxsize=1)
def _load_personas() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not PERSONAS_DIR.exists():
        logger.warning("personas dir missing: %s", PERSONAS_DIR)
        return out
    for f in sorted(PERSONAS_DIR.glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:  # noqa: BLE001
            logger.warning("skip persona %s: %s", f.name, e)
    return out


@lru_cache(maxsize=1)
def _load_products() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not PRODUCTS_DIR.exists():
        logger.warning("products dir missing: %s", PRODUCTS_DIR)
        return out
    for f in sorted(PRODUCTS_DIR.glob("*.json")):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception as e:  # noqa: BLE001
            logger.warning("skip product %s: %s", f.name, e)
    return out


@router.get("/personas")
async def list_personas() -> dict[str, Any]:
    personas = _load_personas()
    return {"count": len(personas), "personas": personas}


@router.get("/products")
async def list_products(limit: int = 1000, category: str | None = None,
                         search: str | None = None) -> dict[str, Any]:
    """Paginated product list. Default cap of 1000 to keep the wire payload sane;
    React side does its own client-side filtering on the page.
    """
    products = _load_products()
    if category:
        products = [p for p in products if (p.get("category") or "").lower() == category.lower()]
    if search:
        s = search.lower()
        products = [p for p in products if s in (p.get("title") or "").lower()]
    return {
        "total": len(products),
        "limit": limit,
        "products": products[:limit],
    }


@router.get("/categories")
async def list_categories() -> dict[str, Any]:
    products = _load_products()
    from collections import Counter
    cats = Counter((p.get("category") or "uncategorised") for p in products)
    return {
        "count": len(cats),
        "categories": [{"name": k, "n": v} for k, v in cats.most_common()],
    }


@router.get("/eval-summary")
async def eval_summary() -> dict[str, Any]:
    """Read paper/results.json + paper/results_ablation.json for the frontend
    sidebar / hero stats. Returns a flat shape friendly to the React UI."""
    results_path = PROJECT_ROOT / "paper" / "results.json"
    if not results_path.exists():
        return {"available": False}
    try:
        d = json.loads(results_path.read_text())
    except Exception:
        return {"available": False}
    t1 = d.get("task1_user_modeling", {})
    t2 = d.get("task2_recommendation", {})
    naija_t1 = t1.get("naija_reviewer_8b", {}) or {}
    claude_t1 = t1.get("claude_sonnet_4", {}) or {}
    naija_t2 = t2.get("naija_reviewer_8b", {}) or {}
    claude_t2 = t2.get("claude_sonnet_4", {}) or {}
    return {
        "available": True,
        "task1": {
            "n": naija_t1.get("n_valid"),
            "naija": {
                "RMSE": naija_t1.get("RMSE"),
                "BERTScore_F1": (naija_t1.get("BERTScore") or {}).get("F1"),
                "ROUGE_L": (naija_t1.get("ROUGE") or {}).get("rougeL"),
                "register_match": naija_t1.get("register_match_pct"),
                "marker_recall": naija_t1.get("cultural_marker_recall"),
                "AS_overall": (naija_t1.get("AgentSociety") or {}).get("overall_quality"),
            },
            "claude": {
                "RMSE": claude_t1.get("RMSE"),
                "BERTScore_F1": (claude_t1.get("BERTScore") or {}).get("F1"),
                "ROUGE_L": (claude_t1.get("ROUGE") or {}).get("rougeL"),
                "register_match": claude_t1.get("register_match_pct"),
                "marker_recall": claude_t1.get("cultural_marker_recall"),
                "AS_overall": (claude_t1.get("AgentSociety") or {}).get("overall_quality"),
            },
        },
        "task2": {
            "n": naija_t2.get("n_valid"),
            "naija": {
                "NDCG_at_10": naija_t2.get("NDCG_at_10"),
                "HR_at_1": naija_t2.get("HR_at_1"),
                "HR_at_5": naija_t2.get("HR_at_5"),
            },
            "claude": {
                "NDCG_at_10": claude_t2.get("NDCG_at_10"),
                "HR_at_1": claude_t2.get("HR_at_1"),
                "HR_at_5": claude_t2.get("HR_at_5"),
            },
        },
    }
