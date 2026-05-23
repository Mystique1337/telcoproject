"""Temporary auth diagnostics — remove before production."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt as jose_jwt

router = APIRouter(prefix="/api/debug", tags=["debug"])
_bearer = HTTPBearer(auto_error=False)


@router.get("/token-info")
async def token_info(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Decode the JWT WITHOUT verifying signature — shows what's in the token."""
    if not credentials:
        return {"error": "No Authorization header"}
    token = credentials.credentials
    try:
        header = jose_jwt.get_unverified_header(token)
        claims = jose_jwt.get_unverified_claims(token)
        return {
            "algorithm": header.get("alg"),
            "sub": claims.get("sub"),
            "email": claims.get("email"),
            "aud": claims.get("aud"),
            "iss": claims.get("iss"),
            "exp": claims.get("exp"),
            "role": claims.get("role"),
        }
    except Exception as exc:
        return {"error": str(exc)}
