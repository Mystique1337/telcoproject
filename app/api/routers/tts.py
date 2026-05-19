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

# 16 Nigerian voices from YarnGPT with their character descriptions
# (per official docs at https://yarngpt.ai/api-docs)
YARNGPT_VOICE_DETAILS: list[dict[str, str]] = [
    {"name": "Idera",    "description": "Melodic, gentle"},
    {"name": "Emma",     "description": "Authoritative, deep"},
    {"name": "Zainab",   "description": "Soothing, gentle"},
    {"name": "Osagie",   "description": "Smooth, calm"},
    {"name": "Wura",     "description": "Young, sweet"},
    {"name": "Jude",     "description": "Warm, confident"},
    {"name": "Chinenye", "description": "Engaging, warm"},
    {"name": "Tayo",     "description": "Upbeat, energetic"},
    {"name": "Regina",   "description": "Mature, warm"},
    {"name": "Femi",     "description": "Rich, reassuring"},
    {"name": "Adaora",   "description": "Warm, engaging"},
    {"name": "Umar",     "description": "Calm, smooth"},
    {"name": "Mary",     "description": "Energetic, youthful"},
    {"name": "Nonso",    "description": "Bold, resonant"},
    {"name": "Remi",     "description": "Melodious, warm"},
    {"name": "Adam",     "description": "Deep, clear"},
]
YARNGPT_VOICES = [v["name"] for v in YARNGPT_VOICE_DETAILS]


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
    """List available Nigerian voices (for the UI dropdown).

    Each voice has a `name` and a one-line character description from the
    YarnGPT docs (gentle / authoritative / soothing / etc.).
    """
    return {
        "voices": YARNGPT_VOICES,             # backward-compat: list of names
        "voice_details": YARNGPT_VOICE_DETAILS,  # name + description pairs
        "default": "Idera",
        "formats": ["mp3", "wav", "opus", "flac"],
        "configured": bool(os.getenv("YARNGPT_API_KEY")),
    }
