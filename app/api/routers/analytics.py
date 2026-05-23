"""InsideNaija analytics — aggregated stats across all runs and results."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.db.repositories.insidenaija import PanelRunRepository, ResultRepository
from app.db.repositories.shared import UserRepository
from app.middleware.auth import get_current_user
from app.services.insidenaija import ProjectService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


@router.get("")
async def get_analytics(user: dict = Depends(_ensure_user)) -> dict[str, Any]:
    project_svc = ProjectService()
    run_repo = PanelRunRepository()
    result_repo = ResultRepository()

    projects = project_svc.list_for_user(user["user_id"])
    project_map = {str(p.id): p for p in projects}

    top_products: list[dict] = []
    all_results: list[Any] = []
    rating_dist: dict[str, int] = {str(i): 0 for i in range(1, 6)}
    sentiment_totals: dict[str, int] = {"positive": 0, "neutral": 0, "negative": 0}
    category_data: dict[str, dict] = {}
    register_data: dict[str, dict] = {}

    for p in projects:
        for run in run_repo.find_all_for_project(str(p.id)):
            if run.status != "completed":
                continue
            agg = (run.meta or {}).get("aggregate") or {}
            if not agg:
                continue

            # Top products list
            top_products.append({
                "project_name": p.name,
                "category": p.category,
                "avg_rating": agg.get("avg_rating"),
                "buy_likelihood": agg.get("buy_likelihood"),
                "n_personas": agg.get("n_personas"),
                "run_id": str(run.id),
            })

            # Global rating distribution
            for star, count in (agg.get("rating_distribution") or {}).items():
                rating_dist[star] = rating_dist.get(star, 0) + (count or 0)

            # Global sentiment
            for s, count in (agg.get("sentiment_split") or {}).items():
                sentiment_totals[s] = sentiment_totals.get(s, 0) + (count or 0)

            # Category performance
            cat = p.category
            if cat not in category_data:
                category_data[cat] = {"ratings": [], "buy_likelihoods": []}
            if agg.get("avg_rating"):
                category_data[cat]["ratings"].append(agg["avg_rating"])
            if agg.get("buy_likelihood") is not None:
                category_data[cat]["buy_likelihoods"].append(agg["buy_likelihood"])

            # Register performance from aggregate by_register
            for reg, data in (agg.get("by_register") or {}).items():
                if reg not in register_data:
                    register_data[reg] = {"totals": [], "buy_likelihoods": []}
                register_data[reg]["totals"].append(data.get("avg_rating", 0))
                register_data[reg]["buy_likelihoods"].append(data.get("buy_likelihood", 0))

            # Collect results for persona analysis
            for result in result_repo.find_by_run(str(run.id)):
                all_results.append(result)

    # ── Top products (by avg_rating desc) ────────────────────────────────────
    top_products.sort(key=lambda x: x.get("avg_rating") or 0, reverse=True)

    # ── Persona analysis ─────────────────────────────────────────────────────
    persona_stats: dict[str, dict] = {}
    for r in all_results:
        pid = r.persona_id
        if pid not in persona_stats:
            persona_stats[pid] = {
                "name": r.persona_name,
                "positive": 0,
                "total": 0,
                "ratings": [],
            }
        persona_stats[pid]["total"] += 1
        if r.sentiment == "positive":
            persona_stats[pid]["positive"] += 1
        if r.rating:
            persona_stats[pid]["ratings"].append(r.rating)

    top_personas = sorted(
        [
            {
                "persona_id": pid,
                "persona_name": d["name"],
                "positive_count": d["positive"],
                "total_reviews": d["total"],
                "positive_rate": round(d["positive"] / d["total"] * 100, 1) if d["total"] else 0,
                "avg_rating": round(sum(d["ratings"]) / len(d["ratings"]), 2) if d["ratings"] else 0,
            }
            for pid, d in persona_stats.items()
        ],
        key=lambda x: x["positive_rate"],
        reverse=True,
    )

    # ── Category performance ──────────────────────────────────────────────────
    category_performance = sorted(
        [
            {
                "category": cat,
                "avg_rating": round(sum(d["ratings"]) / len(d["ratings"]), 2) if d["ratings"] else 0,
                "avg_buy_likelihood": round(sum(d["buy_likelihoods"]) / len(d["buy_likelihoods"]), 1) if d["buy_likelihoods"] else 0,
                "n_runs": len(d["ratings"]),
            }
            for cat, d in category_data.items()
        ],
        key=lambda x: x["avg_rating"],
        reverse=True,
    )

    # ── Register performance ──────────────────────────────────────────────────
    register_performance = sorted(
        [
            {
                "register": reg.replace("_", " ").title(),
                "avg_rating": round(sum(d["totals"]) / len(d["totals"]), 2) if d["totals"] else 0,
                "avg_buy_likelihood": round(sum(d["buy_likelihoods"]) / len(d["buy_likelihoods"]), 1) if d["buy_likelihoods"] else 0,
            }
            for reg, d in register_data.items()
        ],
        key=lambda x: x["avg_rating"],
        reverse=True,
    )

    return {
        "top_products": top_products[:10],
        "top_personas": top_personas[:10],
        "sentiment_distribution": sentiment_totals,
        "rating_distribution": rating_dist,
        "category_performance": category_performance,
        "register_performance": register_performance,
        "total_reviews": len(all_results),
        "total_completed_runs": len(top_products),
    }
