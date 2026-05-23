from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

from app.config import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer()


@lru_cache(maxsize=1)
def _supabase_client() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict[str, Any]:
    try:
        response = _supabase_client().auth.get_user(credentials.credentials)
        user = response.user
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid token")
        return {"user_id": str(user.id), "email": user.email or ""}
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Auth failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")
