"""Run comparison endpoint."""

from __future__ import annotations

import uuid as _uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.db.repositories.shared import UserRepository
from app.middleware.auth import get_current_user
from app.services.insidenaija import PanelRunService, ProjectService

router = APIRouter(prefix="/api/compare", tags=["compare"])


async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


def _run_summary(run: Any, project: Any, result_count: int) -> dict[str, Any]:
    agg = (run.meta or {}).get("aggregate") or {}
    return {
        "id": str(run.id),
        "project_name": project.name,
        "project_category": project.category,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "aggregate": agg,
        "results_count": result_count,
    }


@router.get("")
async def compare_runs(
    run_a: str = Query(...),
    run_b: str = Query(...),
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    """Side-by-side comparison of two runs belonging to the current user."""
    from app.db.repositories.insidenaija import ResultRepository as _ResultRepo

    run_svc = PanelRunService()
    project_svc = ProjectService()
    result_repo = _ResultRepo()

    summaries = {}
    for key, run_id in (("run_a", run_a), ("run_b", run_b)):
        run = run_svc.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail=f"{key} not found")
        project = project_svc.get(str(run.project_id))
        if not project or str(project.user_id) != user["user_id"]:
            raise HTTPException(status_code=403, detail=f"Access denied for {key}")
        results = result_repo.find_by_run(run_id)
        summaries[key] = _run_summary(run, project, len(results))

    return summaries
