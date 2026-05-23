from __future__ import annotations

import uuid

from sqlalchemy import desc

from app.db.base_repository import BaseRepository
from app.db.models import PanelRun, Project, Result


class ProjectRepository(BaseRepository[Project]):
    model_class = Project

    def find_by_user(self, user_id: str) -> list[Project]:
        uid = uuid.UUID(user_id)
        with self.db.session() as session:
            rows = (
                session.query(Project)
                .filter(Project.user_id == uid)
                .order_by(desc(Project.created_at))
                .all()
            )
            # Detach cleanly — simple columns still accessible after close
            for r in rows:
                session.expunge(r)
            return rows


class PanelRunRepository(BaseRepository[PanelRun]):
    model_class = PanelRun

    def find_by_share_token(self, token: str) -> PanelRun | None:
        with self.db.session() as session:
            row = (
                session.query(PanelRun)
                .filter(PanelRun.share_token == token)
                .first()
            )
            if row:
                session.expunge(row)
            return row

    def find_latest_for_project(self, project_id: str) -> PanelRun | None:
        pid = uuid.UUID(project_id)
        with self.db.session() as session:
            row = (
                session.query(PanelRun)
                .filter(PanelRun.project_id == pid)
                .order_by(desc(PanelRun.created_at))
                .first()
            )
            if row:
                session.expunge(row)
            return row

    def find_all_for_project(self, project_id: str) -> list[PanelRun]:
        pid = uuid.UUID(project_id)
        with self.db.session() as session:
            rows = (
                session.query(PanelRun)
                .filter(PanelRun.project_id == pid)
                .order_by(desc(PanelRun.created_at))
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows


class ResultRepository(BaseRepository[Result]):
    model_class = Result

    def find_by_run(self, run_id: str) -> list[Result]:
        rid = uuid.UUID(run_id)
        with self.db.session() as session:
            rows = (
                session.query(Result)
                .filter(Result.run_id == rid)
                .order_by(Result.created_at)
                .all()
            )
            for r in rows:
                session.expunge(r)
            return rows
