"""InsideNaija panel runs — fetch status + results."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.db.repositories.shared import UserRepository
from app.middleware.auth import get_current_user
from app.services.insidenaija import PanelRunService, ProjectService

router = APIRouter(prefix="/api/runs", tags=["runs"])


async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    run_svc = PanelRunService()
    project_svc = ProjectService()

    run = run_svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    project = project_svc.get(str(run.project_id))
    if not project or str(project.user_id) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    results = run_svc.get_results(run_id) if run.status == "completed" else []
    meta = run.meta or {}

    return {
        "id": str(run.id),
        "project_id": str(run.project_id),
        "project_name": project.name,
        "status": run.status,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "aggregate": meta.get("aggregate"),
        "backbone": meta.get("backbone"),
        "latency_ms": meta.get("latency_ms"),
        "results": [
            {
                "id": str(r.id),
                "persona_id": r.persona_id,
                "persona_name": r.persona_name,
                "review_text": r.review_text,
                "rating": r.rating,
                "register_tier": r.register_tier,
                "sentiment": r.sentiment,
            }
            for r in results
        ],
    }
