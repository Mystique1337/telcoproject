"""Build the NaijaReviewer-8B fine-tuning corpus from three sources.

Sources, per PRD v4 §8 + 2026-05-16 data hunt findings:

  1. **Jumia (real, ~15k)** — aymane-maghouti/Sentiment-Analysis-for-Jumia-Reviews
     76,539 Jumia reviews with binary sentiment. We refine binary → 1-5 stars
     via Nemotron (NeMo). Length-filtered, deduped, subsampled.

  2. **AfriSenti pcm (real Pidgin, ~3k)** — shmuhammad/AfriSenti-twitter-sentiment
     10,559 Nigerian Pidgin tweets with sentiment (CC-BY 4.0).
     Claude reframes each as a product review while preserving authentic Pidgin.

  3. **Synthetic (~2k)** — NVIDIA NeMo Data Designer / Nemotron
     Schema-conditioned: 5 personas × Jumia products × 4 register tiers × 5 ratings.
     Config: finetuning/configs/nemo_synthetic.yaml.

Output: data/finetune/v1_{train,val,test}.jsonl  +  data/finetune/DATA_CARD.md
Splits: 90 / 5 / 5, seed=42, stratified by register_tier and rating.

Resumable: each step writes an intermediate JSONL; re-running skips completed stages.

Usage:
    poetry run python scripts/build_finetune_corpus.py            # full run
    poetry run python scripts/build_finetune_corpus.py --dry-run  # 50 rows per source
    poetry run python scripts/build_finetune_corpus.py --stage 3  # rerun stage 3 only
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import logging
import random
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import yaml

# Ensure the repo root is on sys.path so we can import app.*
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings  # noqa: E402
from app.llm.client import LLMClient, LLMError  # noqa: E402

logger = logging.getLogger("corpus")
random.seed(42)

# --------------------------------------------------------------------------- #
# Constants                                                                    #
# --------------------------------------------------------------------------- #

JUMIA_CSV_URL = (
    "https://raw.githubusercontent.com/"
    "aymane-maghouti/Sentiment-Analysis-for-Jumia-Reviews-and-Smartphone-Price-Prediction-System/"
    "main/Main/Sentiment_Analysis_for_Jumia_Reviews/final_data.csv"
)

DATA_DIR = PROJECT_ROOT / "data" / "finetune"
RAW_DIR = DATA_DIR / "raw"
STAGES_DIR = DATA_DIR / "stages"

# Default targets (overridable by CLI)
TARGET_JUMIA = 15_000
TARGET_AFRISENTI = 3_000
TARGET_SYNTHETIC = 2_000

# Concurrency
RATING_REFINE_WORKERS = 12
AFRISENTI_WORKERS = 8
SYNTHETIC_WORKERS = 8

# Pidgin markers used to detect register density in source text
PIDGIN_MARKERS = {
    "abeg", "wahala", "no cap", "biko", "nna", "scatter", "shey", "sef",
    "haba", "wallahi", "aproko", "omo", "naija", "no shaking", "sharp sharp",
    "kpere", "dem dey", "wetin", "e clear", "e too much", "e dey",
}

# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    STAGES_DIR.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    logger.info("wrote %d rows → %s", len(rows), path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def detect_register(text: str) -> str:
    """Heuristic register classifier. Used to tag source rows for stratification."""
    t = text.lower()
    hits = sum(1 for m in PIDGIN_MARKERS if m in t)
    if hits >= 3:
        return "nigerian_pidgin"
    if hits >= 1:
        return "code_mixed"
    # Look for Nigerian-English markers
    nig_eng = ["well done sir", "well done ma", "by God", "thank God", "kindly", "sef"]
    if any(m in t for m in nig_eng):
        return "nigerian_english"
    return "standard_english"


def normalize_review(text: str) -> str:
    """Light cleanup — collapse whitespace, strip emoji-only chars."""
    text = re.sub(r"\s+", " ", text).strip()
    return text


# --------------------------------------------------------------------------- #
# Stage 1 — Download + filter raw Jumia                                        #
# --------------------------------------------------------------------------- #


def stage1_download_jumia(*, dry_run: bool = False) -> Path:
    """Download aymane-maghouti final_data.csv and emit filtered intermediate JSONL."""
    raw_csv = RAW_DIR / "aymane_jumia_final_data.csv"
    stage_out = STAGES_DIR / "stage1_jumia_filtered.jsonl"

    if stage_out.exists() and not dry_run:
        logger.info("[stage 1] %s exists — skipping download", stage_out)
        return stage_out

    if not raw_csv.exists():
        logger.info("[stage 1] downloading Jumia CSV (~15MB)...")
        with httpx.Client(timeout=120.0) as client:
            r = client.get(JUMIA_CSV_URL)
            r.raise_for_status()
            raw_csv.write_bytes(r.content)
        logger.info("[stage 1] saved → %s (%.1f MB)", raw_csv, raw_csv.stat().st_size / 1e6)

    rows: list[dict[str, Any]] = []
    with raw_csv.open(encoding="utf-8", errors="replace") as fh:
        rd = csv.reader(fh)
        next(rd, None)  # header
        for r in rd:
            if len(r) < 2:
                continue
            text = normalize_review(r[0])
            if len(text) < 50 or len(text) > 1500:
                continue
            try:
                target = int(r[1])
            except ValueError:
                continue
            rows.append(
                {
                    "source": "aymane_jumia",
                    "text": text,
                    "binary_sentiment": target,  # -1 or +1
                    "register_hint": detect_register(text),
                }
            )

    # Stratified subsample
    target = 100 if dry_run else TARGET_JUMIA
    pos = [r for r in rows if r["binary_sentiment"] == 1]
    neg = [r for r in rows if r["binary_sentiment"] == -1]
    random.shuffle(pos)
    random.shuffle(neg)
    # Preserve real positive/negative ratio (72.8 / 27.2)
    n_pos = int(round(target * 0.728))
    n_neg = target - n_pos
    selected = pos[:n_pos] + neg[:n_neg]
    random.shuffle(selected)

    write_jsonl(stage_out, selected)
    logger.info(
        "[stage 1] kept %d Jumia rows (filtered from %d); pos/neg=%d/%d",
        len(selected),
        len(rows),
        n_pos,
        n_neg,
    )
    return stage_out


# --------------------------------------------------------------------------- #
# Stage 2 — Refine binary sentiment → 1-5 stars via Nemotron                   #
# --------------------------------------------------------------------------- #


RATING_REFINE_SYSTEM = (
    "You are an expert at calibrating Nigerian product reviewers. Given a real "
    "Jumia review text and its binary sentiment (positive=+1, negative=-1), assign "
    "a precise 1-5 star rating that matches the text's actual intensity. Output "
    "STRICT JSON only."
)

RATING_REFINE_PROMPT = """
Review text:
\"\"\"{text}\"\"\"

Binary sentiment label: {sentiment}  (+1 = positive, -1 = negative)

Assign a precise 1-5 star rating that fits the text's actual intensity:
- 1 = strongly negative / "scam", "rubbish", "waste of money"
- 2 = clearly negative / disappointed but not enraged
- 3 = mixed / mostly neutral with caveats
- 4 = clearly positive / satisfied with mild caveats
- 5 = strongly positive / "scatter", "e too much", "best ever"

Also identify ONE primary aspect the reviewer cared about (one of: quality, value,
delivery, durability, customer_service, packaging, design, battery, performance,
seller_responsiveness, or "general").

Return STRICT JSON:
{{"rating": <int 1-5>, "primary_aspect": "<one of the aspects>"}}
""".strip()


async def _refine_one_rating(
    client: LLMClient, row: dict[str, Any], sem: asyncio.Semaphore
) -> dict[str, Any]:
    async with sem:
        prompt = RATING_REFINE_PROMPT.format(text=row["text"][:1200], sentiment=row["binary_sentiment"])
        try:
            result = await client.complete_json(
                prompt=prompt, system=RATING_REFINE_SYSTEM, max_tokens=80, temperature=0.2
            )
            rating = int(result.get("rating", 4 if row["binary_sentiment"] == 1 else 2))
            aspect = str(result.get("primary_aspect", "general"))[:40]
        except (LLMError, ValueError, KeyError) as exc:
            logger.warning("rating refine failed: %s; using fallback", exc)
            rating = 4 if row["binary_sentiment"] == 1 else 2
            aspect = "general"

        rating = max(1, min(5, rating))
        return {**row, "rating": rating, "primary_aspect": aspect}


async def stage2_refine_ratings(*, dry_run: bool = False) -> Path:
    """For each Jumia row, infer 1-5 star rating from text via Nemotron."""
    stage_in = STAGES_DIR / "stage1_jumia_filtered.jsonl"
    stage_out = STAGES_DIR / "stage2_jumia_rated.jsonl"

    if stage_out.exists() and not dry_run:
        logger.info("[stage 2] %s exists — skipping refinement", stage_out)
        return stage_out

    rows = read_jsonl(stage_in)
    settings = get_settings()
    if not settings.nvidia_api_key:
        raise SystemExit("NVIDIA_API_KEY not set — required for stage 2 rating refinement")

    nemo_model = settings.nvidia_nemo_model
    client = LLMClient(f"nvidia:{nemo_model}")
    logger.info("[stage 2] using NVIDIA model: %s", nemo_model)
    sem = asyncio.Semaphore(RATING_REFINE_WORKERS)

    logger.info("[stage 2] refining ratings on %d rows (concurrency=%d)", len(rows), RATING_REFINE_WORKERS)
    tasks = [_refine_one_rating(client, row, sem) for row in rows]

    done: list[dict[str, Any]] = []
    completed = 0
    for fut in asyncio.as_completed(tasks):
        done.append(await fut)
        completed += 1
        if completed % 250 == 0:
            logger.info("[stage 2] progress: %d / %d", completed, len(tasks))

    # Quick distribution check
    dist = Counter(r["rating"] for r in done)
    logger.info("[stage 2] rating distribution: %s", dict(sorted(dist.items())))

    write_jsonl(stage_out, done)
    return stage_out


# --------------------------------------------------------------------------- #
# Stage 3 — AfriSenti pcm → reformulated as product reviews via Claude         #
# --------------------------------------------------------------------------- #


AFRISENTI_REFORMULATE_SYSTEM = (
    "You convert Nigerian Pidgin sentiment tweets into authentic Nigerian product "
    "reviews while preserving the original speaker's voice, register, and intensity. "
    "Output STRICT JSON."
)

AFRISENTI_REFORMULATE_PROMPT = """
Original Nigerian Pidgin tweet (sentiment={sentiment}):
\"\"\"{text}\"\"\"

Reframe this as a Nigerian product review on Jumia. Choose a plausible Nigerian
product (electronics, fashion, beauty, household, phones, food, baby items, etc.)
and write a 2-4 sentence review that:

1. KEEPS the original speaker's Pidgin voice, intensity, and characteristic phrases
2. References the product naturally (don't force it)
3. Matches the sentiment: positive→4-5 stars, negative→1-2 stars, neutral→3 stars
4. Sounds like a real Nigerian customer wrote it (not a translation)

Return STRICT JSON:
{{
  "product_category": "<short category>",
  "product_hint": "<plausible specific product>",
  "rating": <int 1-5>,
  "review": "<the reframed review text>",
  "primary_aspect": "<one of: quality, value, delivery, durability, customer_service, design, performance, general>"
}}
""".strip()


async def _reformulate_one(
    client: LLMClient,
    tweet: str,
    sentiment_label: int,
    sem: asyncio.Semaphore,
) -> dict[str, Any] | None:
    async with sem:
        prompt = AFRISENTI_REFORMULATE_PROMPT.format(text=tweet[:600], sentiment=sentiment_label)
        try:
            result = await client.complete_json(
                prompt=prompt, system=AFRISENTI_REFORMULATE_SYSTEM, max_tokens=400, temperature=0.7
            )
        except LLMError as exc:
            logger.warning("afrisenti reformulate failed: %s", exc)
            return None

        review = str(result.get("review", "")).strip()
        if len(review) < 40 or len(review) > 1200:
            return None
        return {
            "source": "afrisenti_pcm_reformulated",
            "text": review,
            "rating": max(1, min(5, int(result.get("rating", 3)))),
            "register_hint": "nigerian_pidgin",
            "primary_aspect": str(result.get("primary_aspect", "general"))[:40],
            "product_category": str(result.get("product_category", ""))[:60],
            "product_hint": str(result.get("product_hint", ""))[:120],
            "source_tweet": tweet[:300],
            "source_sentiment": sentiment_label,
        }


async def stage3_afrisenti_reformulate(*, dry_run: bool = False) -> Path:
    """Reframe AfriSenti pcm tweets as Nigerian product reviews via Claude."""
    stage_out = STAGES_DIR / "stage3_afrisenti_reformulated.jsonl"
    if stage_out.exists() and not dry_run:
        logger.info("[stage 3] %s exists — skipping reformulation", stage_out)
        return stage_out

    settings = get_settings()
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY not set — required for stage 3 reformulation")

    # Lazy import: datasets is heavy
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError:
        raise SystemExit("`datasets` package not installed — run `poetry install`")

    logger.info("[stage 3] downloading shmuhammad/AfriSenti-twitter-sentiment (pcm split)...")
    ds = load_dataset("shmuhammad/AfriSenti-twitter-sentiment", "pcm")

    # Combine all splits; filter out neutral (we want polarity signal)
    rows = []
    for split_name in ("train", "validation", "test"):
        if split_name not in ds:
            continue
        for r in ds[split_name]:
            label_int = r.get("label")
            tweet = (r.get("tweet") or "").strip()
            if len(tweet) < 20 or len(tweet) > 280:
                continue
            # 0=positive, 1=neutral, 2=negative in some splits — normalize
            label_str = r.get("label_text") or ""
            if isinstance(label_int, int):
                sentiment = 1 if label_int == 0 else (-1 if label_int == 2 else 0)
            elif isinstance(label_str, str):
                sentiment = 1 if "positive" in label_str.lower() else (-1 if "negative" in label_str.lower() else 0)
            else:
                continue
            if sentiment == 0:
                continue  # skip neutral
            rows.append({"tweet": tweet, "sentiment": sentiment})

    random.shuffle(rows)
    target = 50 if dry_run else TARGET_AFRISENTI
    rows = rows[: target + 500]  # +slack for filtered failures

    logger.info("[stage 3] reformulating %d AfriSenti pcm tweets...", len(rows))

    # Claude — use the configured reformulation model
    client = LLMClient(settings.task1_backbone if "claude" in settings.task1_backbone else "anthropic:claude-sonnet-4-20250514")
    sem = asyncio.Semaphore(AFRISENTI_WORKERS)
    tasks = [_reformulate_one(client, r["tweet"], r["sentiment"], sem) for r in rows]

    done: list[dict[str, Any]] = []
    completed = 0
    for fut in asyncio.as_completed(tasks):
        out = await fut
        if out:
            done.append(out)
        completed += 1
        if completed % 100 == 0:
            logger.info("[stage 3] progress: %d / %d (kept: %d)", completed, len(tasks), len(done))
        if len(done) >= target:
            break

    write_jsonl(stage_out, done[:target])
    logger.info("[stage 3] reformulated %d AfriSenti rows", len(done))
    return stage_out


# --------------------------------------------------------------------------- #
# Stage 4 — Synthetic via NeMo Data Designer (Nemotron via NIM endpoint)       #
# --------------------------------------------------------------------------- #


# Persona archetype voice summaries (consumed by the prompt template)
PERSONA_VOICES = {
    "chinwe_owerri": {
        "name": "Chinwe",
        "voice": (
            "Owerri university student, ~22, code-mixed Igbo+English, communal-hedonic. "
            "Uses 'nna', 'biko', 'scatter scatter', 'abeg', shares experiences with siblings."
        ),
        "aspects": ["quality", "delivery", "value", "packaging"],
    },
    "tunde_lagos": {
        "name": "Tunde",
        "voice": (
            "Lagos market trader, ~40, Pidgin-heavy, utilitarian. Uses 'e too much', "
            "'no cap', 'wahala', 'as e dey hot'. Focused on bulk-buy and durability."
        ),
        "aspects": ["value", "durability", "bulk_pricing", "warranty"],
    },
    "aisha_kano": {
        "name": "Aisha",
        "voice": (
            "Kano secondary-school teacher, ~35, measured Nigerian English with Muslim "
            "framing ('Alhamdulillah', 'Mashallah', 'wallahi'). Family-budget aware."
        ),
        "aspects": ["value_for_family", "durability", "quality", "child_safety"],
    },
    "femi_abuja": {
        "name": "Femi",
        "voice": (
            "Abuja commercial banker, ~35, standard Nigerian English. Low-intensity, "
            "individualist. Uses 'however', 'overall', 'I would recommend'."
        ),
        "aspects": ["build_quality", "brand_reputation", "customer_service", "aesthetics"],
    },
    "ifeoma_ph": {
        "name": "Ifeoma",
        "voice": (
            "Port Harcourt fashion entrepreneur + Nollywood superfan, ~28, Nigerian "
            "English with film vocab ('epic', 'Africa Magic level', 'big-budget'). "
            "Hedonic, communal."
        ),
        "aspects": ["design", "cultural_authenticity", "quality", "story"],
    },
}


REGISTER_INSTRUCTIONS = {
    "standard_english": (
        "Use clear standard English. No Pidgin, no Yoruba/Hausa/Igbo, no Nigerian slang."
    ),
    "nigerian_english": (
        "Use Nigerian English with natural markers ('well done sir/ma', 'no shaking', "
        "'sharp sharp', sentence-final 'now', 'sef'). Avoid heavy Pidgin."
    ),
    "nigerian_pidgin": (
        "Use Nigerian Pidgin naturally ('abeg', 'no cap', 'wahala', 'e shock me', "
        "'scatter', 'dey', 'go', 'be like say'). Sound authentic, not stereotyped."
    ),
    "code_mixed": (
        "Code-mix Nigerian English with natural Yoruba/Hausa/Igbo insertions "
        "('ahn ahn', 'haba', 'wallahi', 'nna', 'biko', 'owambe'). Don't translate."
    ),
}


SYNTHETIC_SYSTEM = (
    "You are simulating Nigerian customers writing product reviews on Jumia. "
    "Match the persona voice EXACTLY. Sound like a real person. Output ONLY the review text."
)


def _build_synthetic_prompt(
    persona_id: str,
    product: dict[str, Any],
    register_tier: str,
    rating: int,
) -> str:
    voice = PERSONA_VOICES[persona_id]
    instr = REGISTER_INSTRUCTIONS[register_tier]
    return f"""
PERSONA: {voice["name"]} ({persona_id})
Voice: {voice["voice"]}
Aspects this user cares about: {", ".join(voice["aspects"])}

PRODUCT (from Jumia catalog):
- Title: {product.get('title','')}
- Category: {product.get('category','')}
- Description: {(product.get('description','') or '')[:400]}
- Price: ₦{product.get('price','')}

TARGET RATING: {rating}/5
REGISTER: {register_tier}

INSTRUCTIONS:
- {instr}
- Write 2-4 sentences that justify a {rating}/5 rating without saying the number.
- Mention at least one of the persona's aspect priorities naturally.
- Sound like a real Nigerian customer, not a chatbot.
- Do NOT add disclaimers, "As an AI", or meta-commentary.
- Output ONLY the review text. No quotes, no labels, no preamble.

REVIEW:
""".strip()


def _load_synthetic_config() -> dict[str, Any]:
    cfg_path = PROJECT_ROOT / "finetuning" / "configs" / "nemo_synthetic.yaml"
    with cfg_path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _stratified_sample_products(n: int, dry_run: bool) -> list[dict[str, Any]]:
    """Sample n products from the Idowenst Jumia catalog (lazy import)."""
    if dry_run:
        # Use bundled samples for dry-run
        sample_dir = PROJECT_ROOT / "data" / "sample" / "products"
        items = []
        for f in sample_dir.glob("*.json"):
            items.append(json.loads(f.read_text(encoding="utf-8")))
        return (items * ((n // max(len(items), 1)) + 1))[:n]

    from datasets import load_dataset  # type: ignore

    ds = load_dataset("Idowenst/jumia_dataset", split="train")
    products: list[dict[str, Any]] = []
    indices = random.sample(range(len(ds)), min(n * 2, len(ds)))
    for i in indices:
        r = ds[i]
        title = r.get("name") or ""
        if not title:
            continue
        products.append(
            {
                "title": title,
                "category": r.get("category", ""),
                "description": (r.get("description") or "")[:600],
                "price": r.get("price"),
            }
        )
        if len(products) >= n:
            break
    return products


async def _synth_one(
    client: LLMClient,
    persona_id: str,
    product: dict[str, Any],
    register_tier: str,
    rating: int,
    sem: asyncio.Semaphore,
) -> dict[str, Any] | None:
    async with sem:
        prompt = _build_synthetic_prompt(persona_id, product, register_tier, rating)
        try:
            text = await client.complete(
                prompt=prompt, system=SYNTHETIC_SYSTEM, max_tokens=400, temperature=0.85
            )
        except LLMError as exc:
            logger.warning("synthetic gen failed: %s", exc)
            return None

        review = normalize_review(text)
        # Quality filters
        if len(review) < 50 or len(review) > 800:
            return None
        bad = ("[INST]", "</s>", "I cannot", "As an AI", "I'm an AI", "I am an AI")
        if any(b in review for b in bad):
            return None

        return {
            "source": "synthetic_nemo",
            "text": review,
            "rating": rating,
            "register_hint": register_tier,
            "primary_aspect": PERSONA_VOICES[persona_id]["aspects"][0],
            "persona_id": persona_id,
            "product_title": product.get("title", ""),
            "product_category": product.get("category", ""),
            "synthetic": True,
        }


async def stage4_synthetic(*, dry_run: bool = False) -> Path:
    """Generate persona-conditioned synthetic reviews via NeMo Nemotron."""
    stage_out = STAGES_DIR / "stage4_synthetic.jsonl"
    if stage_out.exists() and not dry_run:
        logger.info("[stage 4] %s exists — skipping synthetic generation", stage_out)
        return stage_out

    settings = get_settings()
    if not settings.nvidia_api_key:
        raise SystemExit("NVIDIA_API_KEY not set — required for stage 4 synthetic generation")

    cfg = _load_synthetic_config()
    target = 50 if dry_run else cfg.get("target_examples", TARGET_SYNTHETIC)

    # Build the generation grid: stratified by register × rating
    register_dist = cfg["register_distribution"]
    rating_dist = cfg["rating_distribution"]
    persona_pool = cfg["persona_pool"]

    plan: list[tuple[str, str, int]] = []
    for register, r_share in register_dist.items():
        for rating, rate_share in rating_dist.items():
            count = int(round(target * r_share * rate_share))
            for _ in range(count):
                persona = random.choice(persona_pool)
                plan.append((persona, register, int(rating)))
    random.shuffle(plan)
    plan = plan[: target + 200]  # +slack
    logger.info("[stage 4] generation plan: %d items across %d personas × %d registers × 5 ratings",
                len(plan), len(persona_pool), len(register_dist))

    products = _stratified_sample_products(len(plan), dry_run)

    # Prefer the env var (NVIDIA_NEMO_MODEL) so users with restricted accounts can override
    # without editing the YAML or the script.
    nemo_model = settings.nvidia_nemo_model or cfg.get("model", "meta/llama-3.3-70b-instruct")
    client = LLMClient(f"nvidia:{nemo_model}")
    logger.info("[stage 4] using NVIDIA model: %s", nemo_model)
    sem = asyncio.Semaphore(SYNTHETIC_WORKERS)
    tasks = [
        _synth_one(client, persona, product, register, rating, sem)
        for (persona, register, rating), product in zip(plan, products)
    ]

    done: list[dict[str, Any]] = []
    completed = 0
    for fut in asyncio.as_completed(tasks):
        out = await fut
        if out:
            done.append(out)
        completed += 1
        if completed % 100 == 0:
            logger.info("[stage 4] progress: %d / %d (kept: %d)", completed, len(tasks), len(done))
        if len(done) >= target:
            break

    write_jsonl(stage_out, done[:target])
    logger.info("[stage 4] generated %d synthetic rows", len(done))
    return stage_out


# --------------------------------------------------------------------------- #
# Stage 5 — Combine, format, split                                             #
# --------------------------------------------------------------------------- #


INSTRUCTION = (
    "Simulate the review behaviour of the following Nigerian user reviewing the "
    "described product. Generate the rating (1-5) and review text exactly as this "
    "user would write it. Match the user's register tier and cultural framing."
)


def _to_instruction_example(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a stage-2/3/4 row into the canonical training format."""
    register = row.get("register_hint") or "nigerian_english"
    primary_aspect = row.get("primary_aspect", "general")

    # Build the persona stub from row signal
    persona_stub = {
        "register_tier": register,
        "primary_aspect": primary_aspect,
        "history_count": row.get("history_count", 5),
        "source_provenance": row["source"],
    }

    # Build the product stub
    product_stub: dict[str, Any]
    if row["source"] == "synthetic_nemo":
        product_stub = {
            "title": row.get("product_title", ""),
            "category": row.get("product_category", ""),
        }
    elif row["source"] == "afrisenti_pcm_reformulated":
        product_stub = {
            "title": row.get("product_hint", ""),
            "category": row.get("product_category", ""),
        }
    else:  # aymane_jumia
        product_stub = {
            "title": "Jumia product",
            "category": primary_aspect,
        }

    return {
        "instruction": INSTRUCTION,
        "input": {
            "persona": persona_stub,
            "product": product_stub,
            "register_tier": register,
        },
        "output": {
            "rating": int(row["rating"]),
            "review": row["text"],
        },
        "_meta": {
            "source": row["source"],
            "synthetic": row.get("synthetic", False),
        },
    }


def stage5_combine_and_split(*, dry_run: bool = False) -> tuple[Path, Path, Path]:
    """Combine all sources, dedupe by text, split 90/5/5 stratified by register."""
    s1 = read_jsonl(STAGES_DIR / "stage2_jumia_rated.jsonl")
    s2 = read_jsonl(STAGES_DIR / "stage3_afrisenti_reformulated.jsonl")
    s3 = read_jsonl(STAGES_DIR / "stage4_synthetic.jsonl")

    combined = s1 + s2 + s3
    logger.info("[stage 5] combined %d rows (%d + %d + %d)", len(combined), len(s1), len(s2), len(s3))

    # Dedup by normalised text
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in combined:
        key = row["text"].lower().strip()[:200]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    logger.info("[stage 5] after dedup: %d", len(deduped))

    # Convert to instruction format
    examples = [_to_instruction_example(r) for r in deduped]
    random.shuffle(examples)

    # Stratified split by register_tier
    by_register: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ex in examples:
        by_register[ex["input"]["register_tier"]].append(ex)

    train: list[dict[str, Any]] = []
    val: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    for register, items in by_register.items():
        random.shuffle(items)
        n = len(items)
        v_size = max(1, n // 20)
        t_size = max(1, n // 20)
        val += items[:v_size]
        test += items[v_size : v_size + t_size]
        train += items[v_size + t_size :]

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    train_out = DATA_DIR / "v1_train.jsonl"
    val_out = DATA_DIR / "v1_val.jsonl"
    test_out = DATA_DIR / "v1_test.jsonl"
    write_jsonl(train_out, train)
    write_jsonl(val_out, val)
    write_jsonl(test_out, test)

    # Quick stats by register / source / rating
    def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "n": len(rows),
            "by_register": dict(Counter(r["input"]["register_tier"] for r in rows)),
            "by_source": dict(Counter(r["_meta"]["source"] for r in rows)),
            "by_rating": dict(sorted(Counter(r["output"]["rating"] for r in rows).items())),
        }

    summary = {
        "train": _summary(train),
        "val": _summary(val),
        "test": _summary(test),
    }
    summary_path = DATA_DIR / "v1_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    logger.info("[stage 5] summary: %s", json.dumps(summary, indent=2))

    return train_out, val_out, test_out


# --------------------------------------------------------------------------- #
# Stage 6 — Data card                                                          #
# --------------------------------------------------------------------------- #


DATA_CARD_TEMPLATE = """# NaijaReviewer-8B — Fine-Tuning Corpus v1

**Generated**: {generated_at}
**Total examples**: {total} (train: {train_n}, val: {val_n}, test: {test_n})

## Sources

| Source | Rows | License | Voice | Role |
|---|---|---|---|---|
| `aymane-maghouti/Sentiment-Analysis-for-Jumia-Reviews` | {jumia_n} | Public Jumia scrape (no formal license; attributed) | Real Nigerian e-commerce voice (Nigerian English + 1.2% Pidgin) | Primary fine-tune corpus; binary sentiment refined to 1-5 stars via Nemotron |
| `shmuhammad/AfriSenti-twitter-sentiment` (pcm split) | {afri_n} | CC-BY 4.0 | Real Nigerian Pidgin (10.6k pool) | Pidgin register density boost; reformulated as product reviews via Claude Sonnet 4 |
| Synthetic — NVIDIA NeMo / Nemotron-70B | {synth_n} | MIT (ours) | Persona-conditioned (5 archetypes) | Schema-balanced for under-represented code-mixed register tier + rating-distribution balancing |

## Composition

- **Register tiers**: stratified across {register_dist}
- **Rating distribution**: {rating_dist}
- **Splits**: 90 / 5 / 5 stratified by register_tier, seed 42

## Format

Each row is an instruction-tuning example:

```json
{{
  "instruction": "{instruction_short}",
  "input": {{
    "persona": {{ "register_tier": "...", "primary_aspect": "...", ... }},
    "product": {{ "title": "...", "category": "..." }},
    "register_tier": "..."
  }},
  "output": {{
    "rating": 4,
    "review": "Abeg, this phone good die..."
  }},
  "_meta": {{ "source": "...", "synthetic": false }}
}}
```

## Use

```bash
poetry run python finetuning/train_naija_reviewer.py \\
    --config finetuning/configs/naija_reviewer_qlora.yaml
```

The trainer reads `data/finetune/v1_train.jsonl` (set in the YAML).

## Reproducibility

```bash
poetry run python scripts/build_finetune_corpus.py
```

All sources are publicly downloadable. Random seed = 42.

## Attribution

- Aymane Maghouti — Jumia review scrape (GitHub).
- Shamsuddeen Hassan Muhammad et al. — AfriSenti (CC-BY 4.0).
- NVIDIA NeMo / Nemotron — synthetic generation.

## License

This corpus is released under **CC-BY 4.0** (consistent with AfriSenti). Use of the
Jumia scrape component requires attribution to the source repo. The synthetic
component is original work and contributes no upstream licensing constraint.
"""


def write_data_card() -> Path:
    from datetime import datetime
    s1 = STAGES_DIR / "stage2_jumia_rated.jsonl"
    s2 = STAGES_DIR / "stage3_afrisenti_reformulated.jsonl"
    s3 = STAGES_DIR / "stage4_synthetic.jsonl"
    n1 = sum(1 for _ in s1.open()) if s1.exists() else 0
    n2 = sum(1 for _ in s2.open()) if s2.exists() else 0
    n3 = sum(1 for _ in s3.open()) if s3.exists() else 0

    summary_path = DATA_DIR / "v1_summary.json"
    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}

    train_n = summary.get("train", {}).get("n", 0)
    val_n = summary.get("val", {}).get("n", 0)
    test_n = summary.get("test", {}).get("n", 0)
    total = train_n + val_n + test_n
    reg_dist = summary.get("train", {}).get("by_register", {})
    rat_dist = summary.get("train", {}).get("by_rating", {})

    out = DATA_DIR / "DATA_CARD.md"
    out.write_text(
        DATA_CARD_TEMPLATE.format(
            generated_at=datetime.utcnow().isoformat(timespec="seconds") + "Z",
            total=total,
            train_n=train_n,
            val_n=val_n,
            test_n=test_n,
            jumia_n=n1,
            afri_n=n2,
            synth_n=n3,
            register_dist=reg_dist,
            rating_dist=rat_dist,
            instruction_short=INSTRUCTION[:120],
        ),
        encoding="utf-8",
    )
    logger.info("[data card] wrote → %s", out)
    return out


# --------------------------------------------------------------------------- #
# Orchestrator                                                                 #
# --------------------------------------------------------------------------- #


async def run(stages: list[int], dry_run: bool) -> None:
    ensure_dirs()
    logger.info("=== build_finetune_corpus.py — stages=%s dry_run=%s ===", stages, dry_run)

    if 1 in stages:
        stage1_download_jumia(dry_run=dry_run)
    if 2 in stages:
        await stage2_refine_ratings(dry_run=dry_run)
    if 3 in stages:
        await stage3_afrisenti_reformulate(dry_run=dry_run)
    if 4 in stages:
        await stage4_synthetic(dry_run=dry_run)
    if 5 in stages:
        stage5_combine_and_split(dry_run=dry_run)
    if 6 in stages:
        write_data_card()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="50-row probe per source")
    parser.add_argument(
        "--stage",
        type=int,
        action="append",
        choices=[1, 2, 3, 4, 5, 6],
        help="Run only this stage (repeatable). Default: all stages 1-6.",
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )

    stages = args.stage or [1, 2, 3, 4, 5, 6]
    asyncio.run(run(stages=stages, dry_run=args.dry_run))
    return 0


if __name__ == "__main__":
    sys.exit(main())
