from __future__ import annotations

from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from app.db.storage import DBStorage

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Generic repository — all domain repositories inherit from this.

    The DB connection is owned by DBStorage. Repositories never
    instantiate the engine or session directly.
    """

    model_class: Type[T]

    def __init__(self) -> None:
        self.db = DBStorage.get_instance()

    def find(self, id: Any) -> Optional[T]:
        with self.db.session() as session:
            obj = session.get(self.model_class, id)
            if obj is not None:
                session.expunge(obj)
            return obj

    def find_all(self, **filters: Any) -> list[T]:
        with self.db.session() as session:
            q = session.query(self.model_class)
            for attr, value in filters.items():
                q = q.filter(getattr(self.model_class, attr) == value)
            rows = q.all()
            for r in rows:
                session.expunge(r)
            return rows

    def save(self, instance: T) -> T:
        with self.db.session() as session:
            session.add(instance)
            session.flush()
            session.refresh(instance)
            session.expunge(instance)
            return instance

    def update(self, instance: T, **fields: Any) -> T:
        with self.db.session() as session:
            session.add(instance)
            for key, value in fields.items():
                setattr(instance, key, value)
            session.flush()
            session.refresh(instance)
            session.expunge(instance)
            return instance

    def delete(self, instance: T) -> None:
        with self.db.session() as session:
            session.delete(instance)
