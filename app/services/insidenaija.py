from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from app.api.schemas.product import Product as ProductSchema
from app.db.models import PanelRun, Project, Result
from app.db.repositories.insidenaija import (
    PanelRunRepository,
    ProjectRepository,
    ResultRepository,
)

logger = logging.getLogger(__name__)


class ProjectService:
    def __init__(self) -> None:
        self.repo = ProjectRepository()

    def create(
        self,
        user_id: str,
        name: str,
        description: str,
        category: str,
        image_url: str | None = None,
    ) -> Project:
        project = Project(
            user_id=uuid.UUID(user_id),
            name=name,
            description=description,
            category=category,
            image_url=image_url,
        )
        return self.repo.save(project)

    def list_for_user(self, user_id: str) -> list[Project]:
        return self.repo.find_by_user(user_id)

    def get(self, project_id: str) -> Project | None:
        return self.repo.find(uuid.UUID(project_id))


class PanelRunService:
    def __init__(self) -> None:
        self.run_repo = PanelRunRepository()
        self.result_repo = ResultRepository()

    def create_run(self, project_id: str) -> PanelRun:
        run = PanelRun(project_id=uuid.UUID(project_id), status="running")
        return self.run_repo.save(run)

    async def execute_run(
        self, run_id: str, product: ProductSchema, user_email: str = ""
    ) -> None:
        """Background task: runs the persona panel, saving each result as it arrives."""
        from app.agents.panel_agent import run_panel

        run_repo = PanelRunRepository()
        result_repo = ResultRepository()
        rid = uuid.UUID(run_id)

        async def _save_on_result(reaction: dict[str, Any]) -> None:
            """Called by run_panel as each persona finishes — persists immediately."""
            result = Result(
                run_id=rid,
                persona_id=reaction["persona_id"],
                persona_name=reaction["persona_id"].replace("_", " ").title(),
                review_text=reaction.get("review", ""),
                rating=int(reaction["rating"]),
                register_tier=reaction.get("register_tier"),
                sentiment=reaction.get("sentiment"),
            )
            result_repo.save(result)

        try:
            panel_result = await run_panel(product=product, on_result=_save_on_result)

            if panel_result.get("error"):
                run = run_repo.find(rid)
                if run:
                    run_repo.update(
                        run,
                        status="failed",
                        meta={"error": panel_result["error"]},
                        completed_at=datetime.utcnow(),
                    )
                return

            reactions: list[dict[str, Any]] = panel_result.get("reactions", [])
            run = run_repo.find(rid)
            if run:
                run_repo.update(
                    run,
                    status="completed",
                    completed_at=datetime.utcnow(),
                    model_used=panel_result.get("backbone", {}).get("primary"),
                    personas_used=[r["persona_id"] for r in reactions],
                    meta={
                        "aggregate": panel_result.get("aggregate"),
                        "backbone": panel_result.get("backbone"),
                        "latency_ms": panel_result.get("latency_ms"),
                    },
                )

            # Send completion email (best-effort — never raises)
            try:
                from app.services.email import send_run_complete_email
                agg = panel_result.get("aggregate") or {}
                send_run_complete_email(
                    to_email=user_email,
                    project_name=product.title,
                    run_id=run_id,
                    avg_rating=agg.get("avg_rating"),
                    buy_likelihood=agg.get("buy_likelihood"),
                    n_personas=agg.get("n_personas", len(reactions)),
                    themes_praised=(agg.get("themes") or {}).get("praised", []),
                )
            except Exception:
                logger.warning("send_run_complete_email raised unexpectedly for run %s", run_id)

        except Exception:
            logger.exception("panel run %s failed", run_id)
            run = run_repo.find(rid)
            if run:
                run_repo.update(
                    run,
                    status="failed",
                    completed_at=datetime.utcnow(),
                    meta={"error": "Internal error — see server logs"},
                )

    def get_run(self, run_id: str) -> PanelRun | None:
        return self.run_repo.find(uuid.UUID(run_id))

    def get_results(self, run_id: str) -> list[Result]:
        return self.result_repo.find_by_run(run_id)

    def get_latest_for_project(self, project_id: str) -> PanelRun | None:
        return self.run_repo.find_latest_for_project(project_id)
