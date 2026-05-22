from __future__ import annotations

from contextlib import contextmanager
from typing import Generator
from urllib.parse import urlparse, quote, urlunparse

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings


def _safe_url(url: str) -> str:
    """URL-encode the password in a connection string.

    Passwords with special characters like '@' break URL parsing.
    This encodes just the password component, leaving everything else intact.
    """
    parsed = urlparse(url)
    if parsed.password and any(c in parsed.password for c in "@/:?#[]!$&'()*+,;="):
        safe_pass = quote(parsed.password, safe="")
        netloc = f"{parsed.username}:{safe_pass}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"
        return urlunparse(parsed._replace(netloc=netloc))
    return url


class DBStorage:
    """Singleton database connection manager.

    All repositories obtain their session through this class — the
    engine and session factory are created once and reused.
    """

    _instance: "DBStorage | None" = None

    def __init__(self) -> None:
        settings = get_settings()
        # Use DIRECT_URL for SQLAlchemy (bypasses pgbouncer which psycopg2 doesn't support)
        url = settings.direct_url or settings.database_url
        if not url:
            raise RuntimeError("DATABASE_URL or DIRECT_URL must be set")
        # Strip pgbouncer param if present
        if "pgbouncer" in url:
            url = url.split("?")[0]
        url = _safe_url(url)
        self.engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
        self._SessionLocal = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )

    @classmethod
    def get_instance(cls) -> "DBStorage":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        db: Session = self._SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
