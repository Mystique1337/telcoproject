"""InsideNaija panel runs — fetch status + results."""

from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.db.repositories.shared import UserRepository
from app.middleware.auth import get_current_user
from app.services.insidenaija import PanelRunService, ProjectService

router = APIRouter(prefix="/api/runs", tags=["runs"])


async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


@router.post("/{run_id}/share")
async def share_run(
    run_id: str,
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    """Generate (or return existing) a shareable token for a completed run."""
    from app.db.repositories.insidenaija import PanelRunRepository as _RunRepo
    run_repo = _RunRepo()
    run_svc = PanelRunService()
    project_svc = ProjectService()

    run = run_svc.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    project = project_svc.get(str(run.project_id))
    if not project or str(project.user_id) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    token = run.share_token or secrets.token_urlsafe(16)
    if not run.share_token:
        run_repo.update(run, share_token=token)

    return {"token": token, "url": f"/share/{token}"}


@router.get("/active")
async def list_active_runs(
    user: dict = Depends(_ensure_user),
) -> list[dict[str, Any]]:
    """Running panel runs with live progress — for the dashboard live strip."""
    from app.db.repositories.insidenaija import PanelRunRepository as _RunRepo
    from app.db.repositories.insidenaija import ResultRepository as _ResultRepo
    project_svc = ProjectService()
    run_repo = _RunRepo()
    result_repo = _ResultRepo()

    projects = project_svc.list_for_user(user["user_id"])
    project_map = {str(p.id): p for p in projects}

    active = []
    for p in projects:
        for run in run_repo.find_all_for_project(str(p.id)):
            if run.status != "running":
                continue
            completed = len(result_repo.find_by_run(str(run.id)))
            active.append({
                "run_id": str(run.id),
                "project_id": str(run.project_id),
                "project_name": p.name,
                "project_category": p.category,
                "created_at": run.created_at.isoformat(),
                "completed": completed,
                "total": 24,
            })

    active.sort(key=lambda r: r["created_at"])
    return active


@router.get("")
async def list_runs(
    user: dict = Depends(_ensure_user),
) -> list[dict[str, Any]]:
    """All runs for the current user across all projects, newest first."""
    from app.db.repositories.insidenaija import PanelRunRepository as _RunRepo
    project_svc = ProjectService()
    run_repo = _RunRepo()

    projects = project_svc.list_for_user(user["user_id"])
    project_map = {str(p.id): p.name for p in projects}

    all_runs = []
    for p in projects:
        for run in run_repo.find_all_for_project(str(p.id)):
            agg = (run.meta or {}).get("aggregate") or {}
            all_runs.append({
                "id": str(run.id),
                "project_id": str(run.project_id),
                "project_name": project_map.get(str(run.project_id), "—"),
                "status": run.status,
                "created_at": run.created_at.isoformat(),
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "n_personas": agg.get("n_personas"),
                "avg_rating": agg.get("avg_rating"),
                "buy_likelihood": agg.get("buy_likelihood"),
            })

    all_runs.sort(key=lambda r: r["created_at"], reverse=True)
    return all_runs


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

    # Always return results — even mid-run so the UI can show live progress
    results = run_svc.get_results(run_id)
    meta = run.meta or {}
    total_personas = len(run.personas_used) if run.personas_used else 24

    return {
        "id": str(run.id),
        "project_id": str(run.project_id),
        "project_name": project.name,
        "status": run.status,
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "progress": {
            "completed": len(results),
            "total": total_personas,
        },
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
