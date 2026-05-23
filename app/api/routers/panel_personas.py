"""Panel personas — expose the 24 bundled Nigerian personas."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends

from app.config import PROJECT_ROOT
from app.db.repositories.insidenaija import PanelRunRepository, ResultRepository
from app.db.repositories.shared import UserRepository
from app.middleware.auth import get_current_user
from app.services.insidenaija import ProjectService

router = APIRouter(prefix="/api/panel-personas", tags=["panel-personas"])

_PERSONAS_DIR = PROJECT_ROOT / "data" / "sample" / "personas"


def _load_all() -> list[dict[str, Any]]:
    personas = []
    for fp in sorted(_PERSONAS_DIR.glob("*.json")):
        try:
            personas.append(json.loads(fp.read_text()))
        except Exception:
            pass
    return personas


async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


@router.get("")
async def list_panel_personas() -> list[dict[str, Any]]:
    """Return all 24 panel personas (read from bundled JSON files)."""
    return _load_all()


@router.get("/{persona_id}/reviews")
async def get_persona_reviews(
    persona_id: str,
    user: dict = Depends(_ensure_user),
) -> list[dict[str, Any]]:
    """All reviews this persona has given across the user's completed panel runs."""
    run_repo = PanelRunRepository()
    result_repo = ResultRepository()
    projects = ProjectService().list_for_user(user["user_id"])
    project_map = {str(p.id): p for p in projects}

    reviews: list[dict[str, Any]] = []
    for p in projects:
        for run in run_repo.find_all_for_project(str(p.id)):
            if run.status != "completed":
                continue
            for r in result_repo.find_by_run(str(run.id)):
                if r.persona_id != persona_id:
                    continue
                reviews.append({
                    "run_id": str(run.id),
                    "project_name": p.name,
                    "project_category": p.category,
                    "created_at": run.created_at.isoformat(),
                    "rating": r.rating,
                    "sentiment": r.sentiment,
                    "review_text": r.review_text,
                    "register_tier": r.register_tier,
                })

    reviews.sort(key=lambda x: x["created_at"], reverse=True)
    return reviews
