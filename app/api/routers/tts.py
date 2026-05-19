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


# --------------------------------------------------------------------------- #
# Voice → cultural profile (for persona auto-matching)                         #
# --------------------------------------------------------------------------- #
#
# Inferred from voice name etymology + the character descriptions in YarnGPT's
# docs. Gender is the most reliable signal (16/16 names are gendered in Nigerian
# usage). Ethnicity is inferred from name origin (Yoruba names start Femi/Tayo/
# Wura/Remi/Idera; Igbo names with Ada-/Chi-/-onso/-uche; Hausa/Muslim Zainab/
# Umar). Religion can be inferred from clearly-religious names (Mary, Regina,
# Jude → Christian; Zainab, Umar → Muslim). Age "mature" hint is from voice
# descriptions calling out "mature" or "authoritative".
#
VOICE_PROFILES: dict[str, dict[str, str | None]] = {
    "Idera":    {"gender": "F", "ethnicity": "yoruba", "religion": None,        "age": "any"},
    "Emma":     {"gender": "M", "ethnicity": "any",    "religion": None,        "age": "mature"},
    "Zainab":   {"gender": "F", "ethnicity": "hausa",  "religion": "muslim",    "age": "any"},
    "Osagie":   {"gender": "M", "ethnicity": "edo",    "religion": None,        "age": "any"},
    "Wura":     {"gender": "F", "ethnicity": "yoruba", "religion": None,        "age": "young"},
    "Jude":     {"gender": "M", "ethnicity": "igbo",   "religion": "christian", "age": "any"},
    "Chinenye": {"gender": "F", "ethnicity": "igbo",   "religion": "christian", "age": "any"},
    "Tayo":     {"gender": "F", "ethnicity": "yoruba", "religion": None,        "age": "young"},
    "Regina":   {"gender": "F", "ethnicity": "any",    "religion": "christian", "age": "mature"},
    "Femi":     {"gender": "M", "ethnicity": "yoruba", "religion": None,        "age": "any"},
    "Adaora":   {"gender": "F", "ethnicity": "igbo",   "religion": None,        "age": "any"},
    "Umar":     {"gender": "M", "ethnicity": "hausa",  "religion": "muslim",    "age": "any"},
    "Mary":     {"gender": "F", "ethnicity": "any",    "religion": "christian", "age": "young"},
    "Nonso":    {"gender": "M", "ethnicity": "igbo",   "religion": None,        "age": "any"},
    "Remi":     {"gender": "F", "ethnicity": "yoruba", "religion": None,        "age": "any"},
    "Adam":     {"gender": "M", "ethnicity": "any",    "religion": None,        "age": "mature"},
}


# Persona-name → gender inference. We vote over EVERY token in the persona_id
# (so compound ids like 'mama_grace_benue' or 'chief_okonkwo' get classified
# correctly even when the leading token is a title rather than a personal name).
_FEMALE_NAMES = {
    # Personal names (Nigerian + biblical/Christian + Hausa-Muslim feminine)
    "aisha", "chinwe", "ifeoma", "amaka", "fatima", "deborah", "ngozi",
    "blessing", "ada", "halima", "yemisi", "mary", "grace", "wura",
    "idera", "zainab", "regina", "chinenye", "tayo", "adaora", "remi",
    "esther", "ruth", "rebecca", "favour", "joy", "peace",
    # Titles / kinship terms that mark a female persona
    "mama", "iya", "ma", "madam", "mrs", "auntie", "aunty",
    "sister", "ada",
}
_MALE_NAMES = {
    "tunde", "femi", "kelechi", "musa", "tobi", "tomide", "ibrahim", "olumide",
    "emeka", "garba", "okonkwo", "yusuf", "jude", "umar", "nonso", "osagie",
    "adam", "emma", "ade", "ola", "samuel", "david", "daniel",
    # Titles
    "alhaji", "chief", "oga", "mr", "papa", "baba",
}

# Region → likely ethnicity (loose mapping; many Lagos personas are non-Yoruba etc.)
_REGION_ETHNICITY = {
    "lagos": "yoruba", "ibadan": "yoruba", "ogun": "yoruba", "oyo": "yoruba",
    "abeokuta": "yoruba", "ife": "yoruba",
    "kano": "hausa", "sokoto": "hausa", "kaduna": "hausa", "katsina": "hausa",
    "borno": "hausa", "maiduguri": "hausa", "jos": "hausa",
    "anambra": "igbo", "imo": "igbo", "enugu": "igbo", "abia": "igbo",
    "owerri": "igbo", "onitsha": "igbo", "aba": "igbo", "nnewi": "igbo",
    "rivers": "igbo", "port harcourt": "igbo",
    "delta": "edo", "warri": "edo", "edo": "edo", "benin city": "edo",
    "calabar": "any", "cross river": "any", "benue": "any",
}


def _infer_persona_traits(persona_id: str | None,
                            demographics: dict | None,
                            register_tier: str | None,
                            register_markers: list[str] | None) -> dict[str, str | None]:
    """Best-effort inference: gender, ethnicity, religion, age band."""
    persona_id = (persona_id or "").lower()
    demographics = demographics or {}
    register_markers = register_markers or []
    markers = " ".join(register_markers).lower()

    # Gender — vote over all id tokens (handles 'mama_grace_benue' or
    # 'chief_okonkwo' where the LEADING token is a title not a name).
    tokens = persona_id.replace("-", "_").split("_")
    f_votes = sum(1 for t in tokens if t in _FEMALE_NAMES)
    m_votes = sum(1 for t in tokens if t in _MALE_NAMES)
    first_token = tokens[0] if tokens else ""
    gender: str | None = None
    if f_votes > m_votes:
        gender = "F"
    elif m_votes > f_votes:
        gender = "M"

    # Ethnicity from location — WORD-BOUNDARY match to avoid false positives
    # (e.g. "aba" ⊂ "calabar" would otherwise mis-assign Calabar as Igbo).
    import re as _re
    location = (demographics.get("location") or "").lower()
    ethnicity: str | None = None
    # Also infer from persona_id tokens (Yoruba/Igbo/Hausa name origin)
    name_ethnicity_hints = {
        "yoruba": {"tunde", "femi", "tobi", "tomide", "olumide", "ade", "yemisi",
                    "wura", "remi", "idera", "tayo", "ola", "ife", "kunle"},
        "igbo":   {"chinwe", "ifeoma", "amaka", "ngozi", "ada", "chinenye",
                    "adaora", "kelechi", "emeka", "okonkwo", "ifeoma", "nonso",
                    "chukwu", "uche"},
        "hausa":  {"musa", "ibrahim", "fatima", "aisha", "halima", "umar",
                    "yusuf", "garba", "zainab", "alhaji"},
    }
    for tok in tokens:
        for ethn, names in name_ethnicity_hints.items():
            if tok in names:
                ethnicity = ethn
                break
        if ethnicity:
            break
    if ethnicity is None:
        for key, ethn in _REGION_ETHNICITY.items():
            if _re.search(r"\b" + _re.escape(key) + r"\b", location):
                ethnicity = ethn
                break

    # Religion from markers + name
    religion: str | None = None
    if "alhamdulillah" in markers or "mashallah" in markers or "wallahi" in markers:
        religion = "muslim"
    elif "alhaji" in persona_id or first_token in ("fatima", "aisha", "halima", "ibrahim",
                                                     "musa", "umar", "yusuf", "garba", "zainab"):
        religion = "muslim"
    elif "by god's grace" in markers or "thank god" in markers:
        religion = "christian"
    elif first_token in ("mary", "regina", "jude", "chief", "deborah", "blessing", "grace"):
        religion = "christian"

    # Age band
    age_range = (demographics.get("age_range") or "").lower()
    age_band: str | None = None
    if any(x in age_range for x in ("18", "19", "20", "22", "24", "z")):
        age_band = "young"
    elif any(x in age_range for x in ("50", "55", "60", "62", "66", "boomer", "x")):
        age_band = "mature"
    elif "chief" in persona_id or "alhaji" in persona_id or "mama" in persona_id:
        age_band = "mature"

    return {
        "gender": gender,
        "ethnicity": ethnicity,
        "religion": religion,
        "age_band": age_band,
    }


def _score_voice(voice_name: str, traits: dict) -> int:
    """Score how well a voice matches inferred persona traits (higher = better)."""
    p = VOICE_PROFILES.get(voice_name, {})
    score = 0
    # Gender match is the strongest signal — penalise heavily on mismatch
    if traits.get("gender") and p.get("gender") and p["gender"] != "any":
        if p["gender"] == traits["gender"]:
            score += 100
        else:
            score -= 200
    # Ethnicity bonus
    if traits.get("ethnicity") and p.get("ethnicity") and p["ethnicity"] != "any":
        if p["ethnicity"] == traits["ethnicity"]:
            score += 50
    # Religion bonus
    if traits.get("religion") and p.get("religion"):
        if p["religion"] == traits["religion"]:
            score += 40
    elif traits.get("religion") == "muslim" and p.get("religion") == "christian":
        score -= 20
    elif traits.get("religion") == "christian" and p.get("religion") == "muslim":
        score -= 20
    # Age band bonus
    if traits.get("age_band") and p.get("age") and p["age"] != "any":
        if p["age"] == traits["age_band"]:
            score += 20
    return score


def pick_voice_for_persona(persona_id: str | None,
                              demographics: dict | None,
                              register_tier: str | None = None,
                              register_markers: list[str] | None = None) -> dict[str, str]:
    """Return the best-fit Nigerian voice for this persona + the runner-up."""
    traits = _infer_persona_traits(persona_id, demographics, register_tier, register_markers)
    ranked = sorted(
        [(_score_voice(v, traits), v) for v in YARNGPT_VOICES],
        key=lambda x: -x[0],
    )
    return {
        "voice": ranked[0][1],
        "score": str(ranked[0][0]),
        "runner_up": ranked[1][1] if len(ranked) > 1 else ranked[0][1],
        "inferred_traits": traits,
    }


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


@router.post("/voice-for-persona")
async def voice_for_persona(req: dict) -> dict:
    """Suggest a Nigerian voice that best matches a given persona.

    Body: {persona_id, demographics?, register_tier?, register_markers?}
    Returns: {voice, runner_up, inferred_traits, score}.
    """
    return pick_voice_for_persona(
        persona_id=req.get("persona_id"),
        demographics=req.get("demographics"),
        register_tier=req.get("register_tier"),
        register_markers=req.get("register_markers"),
    )


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
