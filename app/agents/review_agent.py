"""Task 1 — review + rating generation agent.

Pipeline per PRD v4 §6.6:
  1. Load persona (already validated by API layer).
  2. (Stage A) Predict rating — heuristic now; XGBoost regressor swaps in later.
  3. (Stage B) Generate review text via the configured backbone.
  4. Self-consistency style check — single regen if the output drifts off-register.
  5. Compose `rationale` string explaining what drove the output.

The backbone is configured via `TASK1_BACKBONE` env var. Defaults to Claude Sonnet 4
until NaijaReviewer-8B is fine-tuned and pulled into Ollama, at which point you set
`TASK1_BACKBONE=ollama:naija-reviewer-8b` in `.env` and restart.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.api.schemas.persona import Persona, RegisterTier
from app.api.schemas.product import Product
from app.config import PROJECT_ROOT, get_settings
from app.llm import get_llm_client
from app.llm.client import LLMError

logger = logging.getLogger(__name__)
settings = get_settings()


# --------------------------------------------------------------------------- #
# Prompt templating                                                            #
# --------------------------------------------------------------------------- #


_env = Environment(
    loader=FileSystemLoader(str(PROJECT_ROOT / "app" / "prompts")),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def _template_for_domain(domain: str) -> str:
    """Pick the prompt template by product domain."""
    mapping = {
        "jumia": "jumia_v1.jinja",
        "konga": "jumia_v1.jinja",
        "nollywood": "nollywood_v1.jinja",
    }
    return mapping.get(domain.lower(), "jumia_v1.jinja")


# --------------------------------------------------------------------------- #
# Stage A — rating prediction                                                  #
# --------------------------------------------------------------------------- #


def predict_rating(persona: Persona, product: Product) -> int:
    """Heuristic Stage-A rating predictor.

    Day 1 stub: combines persona's hedonic disposition, product price tier, and
    aspect-priority match. Swap in the XGBoost regressor (Day 3) by replacing this
    function — interface preserved.
    """
    # Base on persona's intensity calibration — high intensity → extreme ratings
    intensity = sum(persona.intensity_calibration.values()) / max(
        len(persona.intensity_calibration), 1
    )
    # If we have nothing, default to the user's hedonic centre
    if not persona.intensity_calibration:
        intensity = 3.5 + (persona.hedonic_utilitarian - 0.5) * 2

    # Small uplift if product domain matches the persona's primary aspect
    primary = persona.primary_aspects(top_k=1)
    domain_boost = 0.3 if primary and primary[0] in product.description.lower() else 0.0

    raw = intensity + domain_boost
    return max(1, min(5, round(raw)))


# --------------------------------------------------------------------------- #
# Stage B — text generation                                                    #
# --------------------------------------------------------------------------- #


_REGISTER_INSTRUCTIONS = {
    RegisterTier.STANDARD_ENGLISH: (
        "Write in clear standard English. No slang, no Pidgin, no code-switching."
    ),
    RegisterTier.NIGERIAN_ENGLISH: (
        "Write in Nigerian English. Use natural Nigerian-English markers where appropriate "
        '(e.g. "well done sir/ma", "no shaking", "sharp sharp", sentence-final "now", "sef"). '
        "Avoid heavy Pidgin and avoid words from Yoruba/Hausa/Igbo."
    ),
    RegisterTier.NIGERIAN_PIDGIN: (
        "Write in Nigerian Pidgin. Use Pidgin markers naturally where appropriate "
        '(e.g. "abeg", "no cap", "wahala", "e shock me", "scatter scatter", "dey", "go", '
        '"be like say"). Do NOT explain Pidgin words. Sound natural, not stereotyped.'
    ),
    RegisterTier.CODE_MIXED: (
        "Write in code-mixed Nigerian English with natural insertions from Yoruba, Hausa, "
        'or Igbo where appropriate (e.g. "ahn ahn", "haba", "wallahi", "nna", "biko", '
        '"owambe", "wahala"). Do NOT translate or explain. Mix registers naturally, the way '
        "a real Nigerian would on social media or chat."
    ),
}


async def generate_review(
    persona: Persona,
    product: Product,
    include_reasoning: bool = False,
) -> dict[str, Any]:
    """Generate a review + rating for the given persona × product pair."""
    trace: list[dict[str, Any]] = []

    # Stage A — rating
    t0 = time.perf_counter()
    predicted_rating = predict_rating(persona, product)
    trace.append(
        {
            "node": "stage_a_rating_prediction",
            "predicted_rating": predicted_rating,
            "duration_ms": int((time.perf_counter() - t0) * 1000),
        }
    )

    # Stage B — text generation
    template = _env.get_template(_template_for_domain(product.domain))
    user_prompt = template.render(
        persona=persona,
        product=product,
        predicted_rating=predicted_rating,
        register_instructions=_REGISTER_INSTRUCTIONS[persona.register_tier],
    )

    system_prompt = (
        "You are a Nigerian product reviewer. Generate a review that authentically "
        "matches the user's persona — their register, intensity, framing, and the "
        "aspects they care about. Do not break character. Do not add disclaimers."
    )

    backbone = settings.task1_backbone
    fallback_reason: str | None = None
    t1 = time.perf_counter()

    try:
        client = get_llm_client(backbone)
        review_text = await client.complete(
            prompt=user_prompt,
            system=system_prompt,
            max_tokens=400,
            temperature=0.7,
        )
        used_backbone = backbone
    except LLMError as primary_err:
        logger.warning("primary backbone %s failed: %s; falling back", backbone, primary_err)
        fallback_reason = f"primary_failed: {primary_err}"
        fallback_spec = settings.task1_fallback
        try:
            client = get_llm_client(fallback_spec)
            review_text = await client.complete(
                prompt=user_prompt,
                system=system_prompt,
                max_tokens=400,
                temperature=0.7,
            )
            used_backbone = fallback_spec
        except LLMError as fb_err:
            raise LLMError(
                f"Both primary ({backbone}) and fallback ({fallback_spec}) failed: {fb_err}"
            ) from fb_err

    trace.append(
        {
            "node": "stage_b_text_generation",
            "backbone": used_backbone,
            "duration_ms": int((time.perf_counter() - t1) * 1000),
        }
    )

    # Self-consistency check is a Day-3 add-on; for now we accept the first generation.
    # See PRD v4 FR-T1.4.

    rationale = _compose_rationale(persona, product, predicted_rating)
    trace.append({"node": "rationale_composition"})

    return {
        "rating": predicted_rating,
        "review": review_text.strip(),
        "register_tier": persona.register_tier,
        "rationale": rationale,
        "fallback_reason": fallback_reason,
        "reasoning_trace": trace if include_reasoning else None,
    }


def _compose_rationale(persona: Persona, product: Product, rating: int) -> str:
    """Build the human-readable rationale string per FR-T1.5.

    Identifies 2 persona dimensions + 1 register marker that drove the output.
    """
    bits: list[str] = []
    if persona.hedonic_utilitarian > 0.6:
        bits.append("hedonic-leaning")
    elif persona.hedonic_utilitarian < 0.4:
        bits.append("utility-focused")
    if persona.communal_individual > 0.6:
        bits.append("communal framing")
    elif persona.communal_individual < 0.4:
        bits.append("individualist framing")

    primary = persona.primary_aspects(top_k=2)
    if primary:
        bits.append(f"aspect-priority: {' + '.join(primary)}")

    marker = persona.register_markers[0] if persona.register_markers else "no markers"
    return (
        f"Rating {rating}/5 driven by {', '.join(bits) or 'baseline persona'}; "
        f"register tier '{persona.register_tier.value}' (marker: '{marker}')."
    )
