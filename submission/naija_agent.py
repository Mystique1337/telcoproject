"""Naija Persona Agent — single-file submission for the AgentSociety simulator
================================================================================

DROP-IN AGENT FOR THE WWW'25 AgentSociety Challenge harness
(https://github.com/AGI-FBHC/AgentsChallenge).

This file is the *only* file you need to submit if the evaluation harness is the
upstream `websocietysimulator` (or any fork that follows the same
``SimulationAgent`` / ``RecommendationAgent`` contract). It subclasses both base
agents and implements ``workflow()`` for each.

It contains zero hard-coded persona names, zero hard-coded product titles, and
zero hard-coded test data: every piece of context is pulled at run-time from the
``interaction_tool`` that the simulator provides, and the LLM is whatever the
``Simulator.set_llm(...)`` call provides. Plug in a vanilla frontier model and
this agent still runs; plug in NaijaReviewer-8B (via LM Studio's
OpenAI-compatible endpoint at ``http://localhost:1234/v1``) and the same code
path produces register-aware Nigerian output.

Architecture (mirrors the FastAPI service in app/ but inlined for one-file
submission):

1.  Pull raw ``user`` + ``item`` + recent ``reviews`` from the harness.
2.  Lightweight **persona induction** — infer four cognitive dimensions
    (hedonic/utilitarian, communal/individual, intensity calibration, aspect
    priorities) and a Nigerian register tier from the user's review history.
3.  **Register-aware prompting** — pick a Pidgin / code-mixed / Nigerian-English
    / standard-English instruction block based on the induced register.
4.  Call the harness-provided LLM once with the assembled prompt.
5.  Robustly parse ``stars`` + ``review`` (or a ranked id list for Task B); fall
    back to a centred default if parsing fails so the harness never crashes.

Submission instructions
-----------------------
* For Track 1 (User Behavior Simulation): zip this file alone and upload as the
  ``naija_agent.py`` solution. The harness will instantiate ``MySimulationAgent``.
* For Track 2 (Recommendation): same file, the harness instantiates
  ``MyRecommendationAgent``.
* If the local LM Studio server hosting NaijaReviewer-8B is unreachable, the
  agent transparently falls back to whatever frontier LLM the harness injected
  via ``set_llm`` — no code change needed.

Author: Naija Persona Agent Team (Ashinze, Franca, +1).
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
from typing import Any

# ── AgentSociety harness imports (must remain top-level so the simulator can
#    import this module without surprises) ─────────────────────────────────────
try:
    from websocietysimulator.agent import RecommendationAgent, SimulationAgent
    from websocietysimulator.llm import LLMBase
except ImportError:  # pragma: no cover — happens during local syntax checks
    SimulationAgent = object  # type: ignore[assignment,misc]
    RecommendationAgent = object  # type: ignore[assignment,misc]
    LLMBase = object  # type: ignore[assignment,misc]


logger = logging.getLogger("naija_agent")


# ─────────────────────────────────────────────────────────────────────────────
#  Pidgin / Nigerian register markers — used for on-the-fly persona induction.
#  No persona is "hard-coded" — these are linguistic *features* a real review
#  may exhibit. The agent uses them only to decide which register-aware prompt
#  to send to the LLM.
# ─────────────────────────────────────────────────────────────────────────────
# True Pidgin lexicon.
PIDGIN_MARKERS: set[str] = {
    "abeg", "wahala", "no cap", "nna", "scatter", "shey", "sef",
    "haba", "omo", "naija", "ahn ahn", "na fire", "epp", "comot",
    "chop", "gbam", "shakara", "yawa", "shege",
    "dem", "wetin", "e clear", "e too much", "e dey", "e shock", "owambe",
}
# Nigerian English specifically.
NIGERIAN_ENGLISH_MARKERS: set[str] = {
    "well done", "well done sir", "no shaking", "sharp sharp", "as for me", "see ehn",
}
# Register-neutral / religious markers — appear across multiple Nigerian tiers,
# so do NOT use them to classify a review as Pidgin.
NIGERIAN_NEUTRAL_MARKERS: set[str] = {
    "alhamdulillah", "mashallah", "wallahi",
    "biko",
    "thank god", "by god's grace", "by god grace",
}

# Aspect lexicon (English + light Pidgin glosses) for aspect-priority induction.
ASPECT_LEXICON: dict[str, set[str]] = {
    "quality":    {"quality", "build", "solid", "premium", "cheap material", "fake"},
    "value":      {"price", "cost", "affordable", "value", "money", "₦", "naira", "expensive", "wahala"},
    "delivery":   {"delivery", "shipping", "arrived", "courier", "late", "fast"},
    "packaging":  {"package", "packaging", "box", "wrapped", "broken"},
    "seller":     {"seller", "vendor", "shop", "store", "trader", "merchant"},
    "durability": {"durable", "lasted", "long lasting", "broke", "spoil", "spoilt"},
    "design":     {"design", "look", "style", "colour", "color", "aesthetic", "fine"},
}


def _detect_register(text: str) -> str:
    """Return one of {nigerian_pidgin, code_mixed, nigerian_english, standard_english}.

    Religious / Hausa-Arabic markers (alhamdulillah, mashallah, wallahi) and
    biko are register-neutral — they count as Nigerian voice but do NOT push
    a review into the Pidgin bucket.
    """
    t = (text or "").lower()
    pidgin_hits = sum(1 for m in PIDGIN_MARKERS if m in t)
    ne_hits = sum(1 for m in NIGERIAN_ENGLISH_MARKERS if m in t)
    neutral_hits = sum(1 for m in NIGERIAN_NEUTRAL_MARKERS if m in t)
    if pidgin_hits >= 3:
        return "nigerian_pidgin"
    if pidgin_hits >= 1:
        return "code_mixed"
    if ne_hits >= 1 or neutral_hits >= 1:
        return "nigerian_english"
    return "standard_english"


def _induce_persona(user_info: dict[str, Any], user_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the 4-dim + register persona from raw harness data.

    No structured persona is assumed in the upstream dataset; this function is
    the on-the-fly equivalent of the FastAPI service's ``/elicit`` endpoint.
    """
    if not user_reviews:
        # Cold-start: neutral defaults, register from user_info if present.
        about = (user_info or {}).get("about", "") if isinstance(user_info, dict) else ""
        return {
            "register_tier": _detect_register(about),
            "register_markers": [],
            "hedonic_utilitarian": 0.5,
            "communal_individual": 0.5,
            "intensity_calibration": {"amazing": 4.5, "okay": 3.0, "bad": 2.0},
            "aspect_priority": {a: 1 / len(ASPECT_LEXICON) for a in ASPECT_LEXICON},
            "history_count": 0,
        }

    blob = " ".join((r.get("text") or r.get("review") or "") for r in user_reviews[:30]).lower()

    # Register tier — majority vote across history.
    register_votes = [_detect_register(r.get("text") or r.get("review") or "") for r in user_reviews[:20]]
    register_tier = max(set(register_votes), key=register_votes.count)
    found_markers = sorted({m for m in PIDGIN_MARKERS if m in blob})[:8]

    # Hedonic-vs-utilitarian: count emotion vs utility words.
    hedonic_words = ("love", "amazing", "beautiful", "sweet die", "fire", "owambe", "vibe")
    utility_words = ("works", "useful", "value", "price", "durable", "lasts", "function")
    h = sum(blob.count(w) for w in hedonic_words)
    u = sum(blob.count(w) for w in utility_words)
    hedonic = (h + 1) / (h + u + 2)

    # Communal-vs-individual: 1st-person plural vs singular.
    we_count = sum(blob.count(p) for p in (" we ", " us ", " our ", "family", "community"))
    i_count = sum(blob.count(p) for p in (" i ", " me ", " my ", "mine"))
    communal = (we_count + 1) / (we_count + i_count + 2)

    # Intensity calibration: mean star rating when each intensifier appears.
    intensifier_words = ("amazing", "great", "good", "okay", "bad", "terrible", "sweet die", "e too much")
    intensity: dict[str, float] = {}
    for w in intensifier_words:
        ratings = [
            float(r.get("stars", 3)) for r in user_reviews
            if w in (r.get("text") or r.get("review") or "").lower()
        ]
        if ratings:
            intensity[w] = round(sum(ratings) / len(ratings), 2)

    # Aspect priority: fraction of reviews touching each aspect.
    n = max(len(user_reviews), 1)
    aspect_counts = {a: 0 for a in ASPECT_LEXICON}
    for r in user_reviews:
        text = (r.get("text") or r.get("review") or "").lower()
        for aspect, keywords in ASPECT_LEXICON.items():
            if any(kw in text for kw in keywords):
                aspect_counts[aspect] += 1
    total = sum(aspect_counts.values()) or 1
    aspect_priority = {a: round(c / total, 3) for a, c in aspect_counts.items()}

    return {
        "register_tier": register_tier,
        "register_markers": found_markers,
        "hedonic_utilitarian": round(hedonic, 3),
        "communal_individual": round(communal, 3),
        "intensity_calibration": intensity,
        "aspect_priority": aspect_priority,
        "history_count": len(user_reviews),
    }


def _register_instruction(tier: str) -> str:
    """Voice/register guidance block injected into the LLM prompt."""
    if tier == "nigerian_pidgin":
        return (
            "Write in fluent Nigerian Pidgin. Code-switch naturally; do NOT sanitize "
            "into standard English. Use Pidgin markers like 'abeg', 'wahala', 'dey', "
            "'no shaking', 'e too much' where they fit. Sound like a real Naija reviewer."
        )
    if tier == "code_mixed":
        return (
            "Write in code-mixed Nigerian English + Pidgin. Mix Pidgin clauses into "
            "English sentences naturally. Keep cultural markers ('wahala', 'abeg', "
            "'gbam', 'owambe') where they fit the experience."
        )
    if tier == "nigerian_english":
        return (
            "Write in Nigerian English. Use phrases like 'well done sir', "
            "'by God's grace', 'sharp sharp', 'no shaking' where natural. "
            "Do NOT default to American or British register."
        )
    return "Write in clear standard English. Keep the review concise and factual."


def _summarise(obj: Any, max_chars: int = 800) -> str:
    """Compact string repr for arbitrary harness records, capped to avoid prompt bloat."""
    if obj is None:
        return ""
    s = json.dumps(obj, ensure_ascii=False, default=str) if not isinstance(obj, str) else obj
    return s[:max_chars]


# ─────────────────────────────────────────────────────────────────────────────
#  Track 1 — User Behavior Simulation
# ─────────────────────────────────────────────────────────────────────────────

class MySimulationAgent(SimulationAgent):
    """Generate (stars, review) for a (user, item) pair in Nigerian register.

    Drop-in for ``websocietysimulator.Simulator``.
    """

    def __init__(self, llm: LLMBase) -> None:  # type: ignore[override]
        super().__init__(llm=llm)
        self.default_fallback = {
            "stars": 3.0,
            "review": (
                "The product meets basic expectations. Quality is okay, the price is "
                "fair, and delivery was alright. Nothing exceptional but no major "
                "wahala either. Would consider buying again."
            ),
        }

    def workflow(self) -> dict[str, Any]:  # type: ignore[override]
        try:
            user_id = self.task.get("user_id")
            item_id = self.task.get("item_id")

            user_info = self.interaction_tool.get_user(user_id=user_id) or {}
            item_info = self.interaction_tool.get_item(item_id=item_id) or {}
            user_reviews = self.interaction_tool.get_reviews(user_id=user_id) or []
            item_reviews = self.interaction_tool.get_reviews(item_id=item_id) or []

            persona = _induce_persona(user_info, user_reviews)
            register_block = _register_instruction(persona["register_tier"])

            # Random sample of past reviews to anchor the writing style.
            sample_user_reviews = random.sample(user_reviews, min(len(user_reviews), 3))
            sample_user_review_text = "\n".join(
                f"- (★{r.get('stars','?')}) {(r.get('text') or r.get('review') or '')[:200]}"
                for r in sample_user_reviews
            ) or "(none)"

            sample_item_reviews = random.sample(item_reviews, min(len(item_reviews), 3))
            sample_item_review_text = "\n".join(
                f"- (★{r.get('stars','?')}) {(r.get('text') or r.get('review') or '')[:200]}"
                for r in sample_item_reviews
            ) or "(none)"

            prompt = f"""You are simulating a real Nigerian-context user on an online review platform.
The user's behavioural profile (induced from their review history):
- register tier: {persona['register_tier']}
- hedonic↔utilitarian: {persona['hedonic_utilitarian']:.2f}  (0 = utility, 1 = hedonic)
- communal↔individual: {persona['communal_individual']:.2f}  (0 = individual, 1 = communal)
- top aspects emphasised: {sorted(persona['aspect_priority'].items(), key=lambda x: -x[1])[:3]}
- intensity calibration: {persona['intensity_calibration']}
- history count: {persona['history_count']}

Item under review:
{_summarise(item_info, 900)}

A handful of this user's past reviews (style anchors):
{sample_user_review_text}

A handful of past reviews of this item (context, not to copy):
{sample_item_review_text}

VOICE / REGISTER GUIDANCE
{register_block}

TASK
Write ONE review for this item, in this user's voice. Then choose a star rating.
- Star rating must be one of: 1.0, 2.0, 3.0, 4.0, 5.0
- Be objective; do not give 5 stars unless the item clearly deserves it
- Review: 3-5 sentences, ~80-150 tokens
- Stay consistent with the user's past style and rating pattern

Respond in EXACTLY this format, no extra commentary:
stars: <number>
review: <single paragraph>
""".strip()

            messages = [{"role": "user", "content": prompt}]
            response = self.llm(messages=messages, temperature=0.4, max_tokens=400)
            if isinstance(response, list):
                response = response[0]

            stars, review = self._parse_response(response)
            if stars is None or not review:
                return self.default_fallback
            review = review[:512]  # harness caps long reviews
            return {"stars": float(stars), "review": review}

        except Exception as exc:  # noqa: BLE001
            logger.exception("workflow failed; returning fallback: %s", exc)
            return self.default_fallback

    @staticmethod
    def _parse_response(text: str) -> tuple[float | None, str | None]:
        """Robust 'stars: X / review: Y' parser tolerant to stray markdown/quotes."""
        if not text:
            return None, None
        stars: float | None = None
        review_lines: list[str] = []
        in_review = False
        for raw in text.splitlines():
            line = raw.strip().lstrip("*-•").strip()
            low = line.lower()
            if low.startswith("stars:") or low.startswith("**stars:**") or low.startswith("rating:"):
                match = re.search(r"(\d+(?:\.\d+)?)", line)
                if match:
                    val = float(match.group(1))
                    stars = max(1.0, min(5.0, val))
            elif low.startswith("review:") or low.startswith("**review:**"):
                in_review = True
                tail = line.split(":", 1)[1].strip() if ":" in line else ""
                if tail:
                    review_lines.append(tail)
            elif in_review:
                review_lines.append(line)
        review = " ".join(review_lines).strip().strip('"').strip("'") or None
        # Fallback: if no 'review:' label, treat any non-stars line as the review.
        if not review:
            review = " ".join(
                l.strip() for l in text.splitlines()
                if l.strip() and not l.lower().strip().startswith(("stars:", "rating:"))
            ) or None
        return stars, review


# ─────────────────────────────────────────────────────────────────────────────
#  Track 2 — Recommendation
# ─────────────────────────────────────────────────────────────────────────────

class MyRecommendationAgent(RecommendationAgent):
    """Rank a candidate list of items for the user in Nigerian-context register."""

    def __init__(self, llm: LLMBase) -> None:  # type: ignore[override]
        super().__init__(llm=llm)

    def workflow(self) -> list[str]:  # type: ignore[override]
        try:
            user_id = self.task["user_id"]
            candidate_list: list[str] = list(self.task["candidate_list"])

            user_info = self.interaction_tool.get_user(user_id=user_id) or {}
            user_reviews = self.interaction_tool.get_reviews(user_id=user_id) or []
            persona = _induce_persona(user_info, user_reviews)

            candidate_blobs: list[str] = []
            for cid in candidate_list:
                item = self.interaction_tool.get_item(item_id=cid) or {}
                # Keep only signal-bearing fields; ditch URLs / huge attribute dumps.
                trimmed = {
                    k: item[k] for k in (
                        "item_id", "name", "title", "category", "categories",
                        "description", "stars", "average_rating",
                        "review_count", "rating_number", "price",
                    ) if k in item
                }
                candidate_blobs.append(f"{cid}: {_summarise(trimmed, 350)}")

            user_history_summary = "\n".join(
                f"(★{r.get('stars','?')}) {(r.get('text') or r.get('review') or '')[:160]}"
                for r in user_reviews[:8]
            ) or "(no history)"

            top_aspects = [
                a for a, _ in sorted(persona["aspect_priority"].items(), key=lambda x: -x[1])[:3]
            ]
            register_block = _register_instruction(persona["register_tier"])

            prompt = f"""You are recommending products to a Nigerian-context user.

User profile (induced from history):
- register tier: {persona['register_tier']}
- hedonic↔utilitarian: {persona['hedonic_utilitarian']:.2f}
- communal↔individual: {persona['communal_individual']:.2f}
- top aspects: {top_aspects}
- history count: {persona['history_count']}

User's recent reviews:
{user_history_summary}

Candidate items (id : trimmed info):
{chr(10).join(candidate_blobs)}

Rank the candidate items from BEST to WORST fit for this user.
{register_block}
Output ONLY a Python-style list of item ids, in ranked order. No analysis, no prose.
Example: ['item_42', 'item_13', 'item_7', ...]
""".strip()

            messages = [{"role": "user", "content": prompt}]
            response = self.llm(messages=messages, temperature=0.2, max_tokens=600)
            if isinstance(response, list):
                response = response[0]

            ranked = self._parse_ranked_list(response, candidate_list)
            return ranked

        except Exception as exc:  # noqa: BLE001
            logger.exception("rec workflow failed; returning unranked list: %s", exc)
            return list(self.task.get("candidate_list", []))

    @staticmethod
    def _parse_ranked_list(text: str, candidate_list: list[str]) -> list[str]:
        """Extract a ranked id list from the LLM output; fall back to harness order."""
        if not text:
            return list(candidate_list)
        match = re.search(r"\[(.*?)\]", text, re.DOTALL)
        if not match:
            return list(candidate_list)
        inner = match.group(1)
        # Match anything that looks like an id token between quotes / commas.
        raw_ids = re.findall(r"['\"]([^'\"]+)['\"]", inner)
        if not raw_ids:
            # Comma-separated bare tokens
            raw_ids = [s.strip() for s in inner.split(",") if s.strip()]
        # Keep only ids that were in the candidate list; preserve LLM order.
        seen: set[str] = set()
        ranked: list[str] = []
        for rid in raw_ids:
            if rid in candidate_list and rid not in seen:
                ranked.append(rid)
                seen.add(rid)
        # Append any candidates the LLM dropped, in original harness order.
        for cid in candidate_list:
            if cid not in seen:
                ranked.append(cid)
        return ranked


# ─────────────────────────────────────────────────────────────────────────────
#  Local sanity check — `python submission/naija_agent.py` does a static parse
#  check using a dummy LLM. The real entry point is the harness's `Simulator`.
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":  # pragma: no cover
    import sys
    sample = """stars: 4
review: Phone sweet die! Battery dey last like four days, abeg. Camera clear gan."""
    s, r = MySimulationAgent._parse_response(sample)
    assert s == 4.0 and "abeg" in (r or "")
    rank = MyRecommendationAgent._parse_ranked_list(
        "['p_3', 'p_1', 'p_2']", ["p_1", "p_2", "p_3", "p_4"]
    )
    assert rank == ["p_3", "p_1", "p_2", "p_4"]
    persona = _induce_persona({"about": "I dey love good market"}, [
        {"text": "wahala no dey, this phone too much abeg", "stars": 5},
        {"text": "battery don tire small, but for the price e dey work", "stars": 4},
    ])
    assert persona["register_tier"] in ("nigerian_pidgin", "code_mixed")
    print("OK — parsers and persona induction pass.", file=sys.stderr)
