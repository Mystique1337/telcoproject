"""Translation into the three major Nigerian languages.

Used by:
  - the review agent (Task A): generate the review normally, then translate
    it into the target language for display + TTS read-out.
  - the chat agent: for the conversational flow we ask the model to respond
    directly in the language instead (see chat_agent), so this is review-only.

We route translation through a frontier backbone (Claude/GPT) by default, since
the local NaijaReviewer-8B fine-tune was trained on Pidgin/English reviews and
is not reliable at full Yoruba/Hausa/Igbo orthography.
"""

from __future__ import annotations

import logging

from app.config import get_settings
from app.llm import get_llm_client
from app.llm.client import LLMError

logger = logging.getLogger(__name__)
settings = get_settings()

# Canonical language codes → display names. These are the only supported targets.
NIGERIAN_LANGUAGES: dict[str, str] = {
    "yoruba": "Yoruba",
    "hausa": "Hausa",
    "igbo": "Igbo",
}


def is_supported_language(code: str | None) -> bool:
    return bool(code) and code.lower() in NIGERIAN_LANGUAGES


async def translate_text(
    text: str,
    target_language: str,
    backbone_spec: str | None = None,
) -> str:
    """Translate `text` into the target Nigerian language.

    Preserves rating sentiment, intensity, and cultural framing. Returns the
    original text unchanged if the language is unsupported or translation fails
    (fail-open: better to show the English review than nothing).
    """
    code = (target_language or "").lower()
    lang = NIGERIAN_LANGUAGES.get(code)
    if not lang or not text.strip():
        return text

    # Frontier backbone for quality; fall back to the configured Task-1 fallback
    # (Claude by default), NOT the local fine-tune which can't do these well.
    spec = backbone_spec or settings.task1_fallback
    client = get_llm_client(spec)

    system = (
        f"You are an expert {lang} translator and native speaker. You translate "
        f"Nigerian product reviews into natural, conversational {lang} as a real "
        f"Nigerian {lang} speaker would write them — correct orthography and "
        f"diacritics, idiomatic phrasing, not stiff textbook language."
    )
    prompt = (
        f"Translate this product review into natural {lang}. Preserve the "
        f"writer's rating sentiment, enthusiasm/frustration level, and any "
        f"cultural framing. Keep product names and numbers as-is. Return ONLY "
        f"the {lang} translation — no preamble, no quotes, no explanation.\n\n"
        f"Review:\n{text}"
    )
    try:
        out = await client.complete(prompt, system=system, max_tokens=900, temperature=0.3)
        translated = (out or "").strip()
        return translated or text
    except LLMError as e:  # noqa: BLE001
        logger.warning("translation to %s failed (%s); returning original text", lang, e)
        return text
