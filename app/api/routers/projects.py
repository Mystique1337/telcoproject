"""InsideNaija projects — create + list research projects."""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel


def _strip_html(html: str) -> str:
    """Remove HTML tags so the LLM receives clean plain text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return re.sub(r"\s+", " ", text).strip()

from app.api.schemas.product import Product as ProductSchema
from app.db.repositories.shared import UserRepository
from app.middleware.auth import get_current_user
from app.services.insidenaija import PanelRunService, ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def _ensure_user(user_data: dict = Depends(get_current_user)) -> dict:
    """Upsert the Supabase user into our users table on every authenticated call."""
    UserRepository().get_or_create(user_data["user_id"], user_data["email"])
    return user_data


class CreateProjectRequest(BaseModel):
    name: str
    description: str
    category: str = "general"
    image_url: str | None = None
    target_rating: float | None = None


@router.post("")
async def create_project(
    req: CreateProjectRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    project_svc = ProjectService()
    run_svc = PanelRunService()

    project = project_svc.create(
        user_id=user["user_id"],
        name=req.name,
        description=req.description,
        category=req.category,
        image_url=req.image_url,
        target_rating=req.target_rating,
    )

    run = run_svc.create_run(str(project.id))

    product = ProductSchema(
        product_id=str(uuid.uuid4()),
        title=req.name,
        description=_strip_html(req.description),  # LLM gets plain text
        category=req.category,
        metadata={"image_url": req.image_url} if req.image_url else {},
    )

    background_tasks.add_task(run_svc.execute_run, str(run.id), product, user["email"])

    return {
        "project_id": str(project.id),
        "run_id": str(run.id),
        "status": "running",
    }


@router.get("")
async def list_projects(
    user: dict = Depends(_ensure_user),
) -> list[dict[str, Any]]:
    project_svc = ProjectService()
    run_svc = PanelRunService()

    projects = project_svc.list_for_user(user["user_id"])

    result = []
    for p in projects:
        latest = run_svc.get_latest_for_project(str(p.id))
        result.append(
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "target_rating": p.target_rating,
                "created_at": p.created_at.isoformat(),
                "latest_run": {
                    "id": str(latest.id),
                    "status": latest.status,
                    "created_at": latest.created_at.isoformat(),
                }
                if latest
                else None,
            }
        )

    return result


class BulkProjectItem(BaseModel):
    name: str
    description: str
    category: str = "general"
    image_url: str | None = None


@router.post("/bulk")
async def create_projects_bulk(
    items: list[BulkProjectItem],
    background_tasks: BackgroundTasks,
    user: dict = Depends(_ensure_user),
) -> list[dict[str, Any]]:
    if not items:
        return []
    if len(items) > 25:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Max 25 projects per bulk import")

    project_svc = ProjectService()
    run_svc = PanelRunService()
    results = []

    for item in items:
        project = project_svc.create(
            user_id=user["user_id"],
            name=item.name,
            description=item.description,
            category=item.category,
            image_url=item.image_url,
        )
        run = run_svc.create_run(str(project.id))
        product = ProductSchema(
            product_id=str(uuid.uuid4()),
            title=item.name,
            description=_strip_html(item.description),
            category=item.category,
            metadata={"image_url": item.image_url} if item.image_url else {},
        )
        background_tasks.add_task(run_svc.execute_run, str(run.id), product, user["email"])
        results.append({
            "project_id": str(project.id),
            "run_id": str(run.id),
            "name": item.name,
            "status": "running",
        })

    return results


@router.get("/stats")
async def get_stats(
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    from app.db.repositories.insidenaija import PanelRunRepository as _RunRepo
    projects = ProjectService().list_for_user(user["user_id"])
    run_repo = _RunRepo()

    completed = running = total_personas = rated_runs = 0
    total_rating = 0.0

    for p in projects:
        for run in run_repo.find_all_for_project(str(p.id)):
            if run.status == "completed":
                completed += 1
                agg = (run.meta or {}).get("aggregate") or {}
                n = agg.get("n_personas", 0)
                r = agg.get("avg_rating")
                total_personas += n
                if r:
                    total_rating += r
                    rated_runs += 1
            elif run.status == "running":
                running += 1

    return {
        "total_projects": len(projects),
        "completed_runs": completed,
        "running_runs": running,
        "avg_rating": round(total_rating / rated_runs, 2) if rated_runs else None,
        "total_personas_evaluated": total_personas,
    }


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    project = ProjectService().get(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if str(project.user_id) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": str(project.id),
        "name": project.name,
        "description": project.description,
        "category": project.category,
        "created_at": project.created_at.isoformat(),
    }


@router.post("/{project_id}/rerun")
async def rerun_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(_ensure_user),
) -> dict[str, Any]:
    """Create a new panel run for an existing project."""
    project_svc = ProjectService()
    run_svc = PanelRunService()

    project = project_svc.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if str(project.user_id) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    run = run_svc.create_run(project_id)
    product = ProductSchema(
        product_id=str(uuid.uuid4()),
        title=project.name,
        description=_strip_html(project.description),
        category=project.category,
        metadata={},
    )
    background_tasks.add_task(run_svc.execute_run, str(run.id), product, user["email"])

    return {
        "run_id": str(run.id),
        "status": "running",
    }
