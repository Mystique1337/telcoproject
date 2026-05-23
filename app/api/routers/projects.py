"""InsideNaija projects — create + list research projects."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

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
    )

    run = run_svc.create_run(str(project.id))

    product = ProductSchema(
        product_id=str(uuid.uuid4()),
        title=req.name,
        description=req.description,
        category=req.category,
        metadata={"image_url": req.image_url} if req.image_url else {},
    )

    background_tasks.add_task(run_svc.execute_run, str(run.id), product)

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
