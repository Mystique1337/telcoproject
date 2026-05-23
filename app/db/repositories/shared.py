from __future__ import annotations

import uuid

from app.db.base_repository import BaseRepository
from app.db.models import User


class UserRepository(BaseRepository[User]):
    model_class = User

    def get_or_create(self, supabase_id: str, email: str) -> User:
        uid = uuid.UUID(supabase_id)
        with self.db.session() as session:
            user = session.get(User, uid)
            if user is None:
                user = User(id=uid, email=email)
                session.add(user)
                session.flush()
                session.refresh(user)
            return user
