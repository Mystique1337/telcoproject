"""Text-to-speech endpoint — Nigerian voices via YarnGPT.

POST /tts → returns raw audio (mp3/wav/opus/flac) of the input text
spoken in one of 16 Nigerian voices (Idera, Emma, Zainab, Osagie,
Wura, Jude, Chinenye, Tayo, Regina, Femi, Adaora, Umar, Mary,
Nonso, Remi, Adam).

Auth: requires YARNGPT_API_KEY in the environment.
"""

from __future__ import annotations

import logging
import os
from typing import Literal

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tts", tags=["tts"])

YARNGPT_BASE = os.getenv("YARNGPT_BASE_URL", "https://yarngpt.ai/api/v1").rstrip("/")
YARNGPT_VOICES = [
    "Idera", "Emma", "Zainab", "Osagie", "Wura", "Jude",
    "Chinenye", "Tayo", "Regina", "Femi", "Adaora", "Umar",
    "Mary", "Nonso", "Remi", "Adam",
]


class TTSRequest(BaseModel):
    text: str = Field(..., max_length=2000, description="Text to synthesise (max 2000 chars)")
    voice: str = Field(default="Idera", description=f"One of: {', '.join(YARNGPT_VOICES)}")
    response_format: Literal["mp3", "wav", "opus", "flac"] = Field(default="mp3")


_AUDIO_MIME = {
    "mp3":  "audio/mpeg",
    "wav":  "audio/wav",
    "opus": "audio/opus",
    "flac": "audio/flac",
}


@router.post("")
async def tts(req: TTSRequest) -> Response:
    """Proxy YarnGPT TTS — returns raw audio body."""
    key = os.getenv("YARNGPT_API_KEY")
    if not key:
        raise HTTPException(
            status_code=503,
            detail="YARNGPT_API_KEY not set in .env — add it to enable Nigerian TTS",
        )
    if req.voice not in YARNGPT_VOICES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown voice '{req.voice}'. Available: {YARNGPT_VOICES}",
        )
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(
                f"{YARNGPT_BASE}/tts",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": req.text,
                    "voice": req.voice,
                    "response_format": req.response_format,
                },
            )
        if r.status_code != 200:
            logger.warning("yarngpt %d: %s", r.status_code, r.text[:200])
            raise HTTPException(
                status_code=502,
                detail=f"YarnGPT upstream {r.status_code}: {r.text[:200]}",
            )
        return Response(
            content=r.content,
            media_type=_AUDIO_MIME[req.response_format],
            headers={
                "Content-Disposition": f'inline; filename="speech.{req.response_format}"',
                "Cache-Control": "no-store",
            },
        )
    except httpx.RequestError as e:
        logger.exception("yarngpt request failed")
        raise HTTPException(status_code=502, detail=f"YarnGPT network error: {e}") from e


@router.get("/voices")
async def list_voices() -> dict:
    """List available Nigerian voices (for the UI dropdown)."""
    return {
        "voices": YARNGPT_VOICES,
        "default": "Idera",
        "formats": ["mp3", "wav", "opus", "flac"],
        "configured": bool(os.getenv("YARNGPT_API_KEY")),
    }
