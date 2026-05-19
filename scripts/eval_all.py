"""Full evaluation suite — closes the metrics gap on both tasks.

Task A (User Modeling) metrics:
  - RMSE on rating (25 pts in rubric)
  - BERTScore F1 + ROUGE on review text (30 pts in rubric)
  - Register-tier match (Nigerian-context bonus)
  - Cultural-marker recall on Pidgin/Nigerian markers

Task B (Recommendation) metrics:
  - NDCG@10 (30 pts in rubric)
  - HR@1 / HR@3 / HR@5 (30 pts in rubric — alternate ranking metric)

Runs each metric against multiple backbones for head-to-head comparison:
  - NaijaReviewer-8B (local fine-tune via LM Studio)
  - Vanilla Claude Sonnet 4
  - Vanilla GPT-4o
  - Base Llama 3.1 8B Instruct (Ollama, if available)

Outputs:
  paper/results.json   — raw metric numbers (paper Section 5 reads this)
  paper/results.md     — pretty markdown table for the paper

Usage:
  python scripts/eval_all.py                  # default: 50 rows per backbone
  python scripts/eval_all.py --n 100          # bump to 100 rows
  python scripts/eval_all.py --backbone naija_only  # only the fine-tune
  python scripts/eval_all.py --task1-only     # skip recommendation eval
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger("eval")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")


# --------------------------------------------------------------------------- #
# Config                                                                       #
# --------------------------------------------------------------------------- #

API_URL = os.getenv("NPA_API_URL", "http://localhost:8765")

# Backbones to evaluate. Format: "label" → "provider:model"
BACKBONES_TASK1 = {
    "naija_reviewer_8b":  "lmstudio:naija-reviewer-8b",
    "claude_sonnet_4":    "anthropic:claude-sonnet-4-20250514",
    # Uncomment if you have these set up:
    # "gpt_4o":           "openai:gpt-4o",
    # "base_llama_3_1":   "ollama:llama3.1:8b-instruct",
}
BACKBONES_TASK2 = {
    # Frontier (closed-source)
    "claude_sonnet_4":     "anthropic:claude-sonnet-4-20250514",
    # Our fine-tune (Task A model — included to demonstrate the fallback path)
    "naija_reviewer_8b":   "lmstudio:naija-reviewer-8b",
    # Open-source heavyweights via Ollama Cloud + HF Inference
    "llama_3_3_70b_hf":    "hf:meta-llama/Llama-3.3-70B-Instruct",
    "qwen_2_5_72b_hf":     "hf:Qwen/Qwen2.5-72B-Instruct",
    "gpt_oss_120b_ocloud": "ollama-cloud:gpt-oss:120b",
}

# Concurrency on API calls
CONCURRENCY = 4

# Pidgin lexicon (specific to Pidgin register).
PIDGIN_MARKERS = {
    "abeg", "wahala", "no cap", "nna", "scatter", "shey", "sef",
    "haba", "omo", "naija", "ahn ahn", "na fire",
    "dem", "wetin", "e clear", "e too much", "e dey", "e shock", "owambe",
}
# Nigerian English specifically.
NIGERIAN_ENGLISH_MARKERS = {
    "well done", "well done sir", "no shaking", "sharp sharp", "as for me", "see ehn",
}
# Register-neutral / religious markers (across all Nigerian tiers).
NIGERIAN_NEUTRAL_MARKERS = {
    "alhamdulillah", "mashallah", "wallahi", "biko",
    "thank god", "by god's grace", "by god grace",
}
# Used for cultural-marker recall metric — any Nigerian-voice marker counts.
ALL_NIGERIAN_MARKERS = PIDGIN_MARKERS | NIGERIAN_ENGLISH_MARKERS | NIGERIAN_NEUTRAL_MARKERS


# --------------------------------------------------------------------------- #
# Test-data loading                                                            #
# --------------------------------------------------------------------------- #

def load_test_set(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the test split, preferring the richer parquet, falling back to alpaca jsonl."""
    if path is not None and path.exists():
        return _load_jsonl(path) if path.suffix == ".jsonl" else _load_parquet(path)

    candidates = [
        Path("/content/drive/MyDrive/naija_persona_corpus_openai/processed/v1_test_full.parquet"),
        Path("/content/drive/MyDrive/naija_persona_corpus/processed/v1_test_full.parquet"),
        PROJECT_ROOT / "data" / "finetune" / "v1_test_full.parquet",
        Path("/content/drive/MyDrive/naija_persona_corpus_openai/processed/v1_test_alpaca.jsonl"),
        Path("/content/drive/MyDrive/naija_persona_corpus/processed/v1_test_alpaca.jsonl"),
        PROJECT_ROOT / "data" / "finetune" / "v1_test_alpaca.jsonl",
    ]
    for p in candidates:
        if p.exists():
            logger.info("loading test set from %s", p)
            return _load_parquet(p) if p.suffix == ".parquet" else _load_jsonl(p)

    raise FileNotFoundError(
        "Test set not found. Looked for v1_test_full.parquet and v1_test_alpaca.jsonl in:\n  "
        + "\n  ".join(str(c) for c in candidates)
        + "\n\nIf your corpus is somewhere else, pass --test-set <path>"
    )


def _load_parquet(p: Path) -> list[dict[str, Any]]:
    """Load the parquet test split, normalising column names + filtering rows
    that lack product info (seed_grounded pipeline rows don't have a product).

    The corpus builder writes a richer schema than the eval needs; we coerce
    it into the {persona_id, register_tier, product_title, product_category,
    rating, review} shape expected downstream.
    """
    import pandas as pd
    df = pd.read_parquet(p)

    # Prefer product_title; fall back to title column if present.
    if "title" in df.columns and "product_title" in df.columns:
        df["product_title"] = df["product_title"].fillna("").astype(str)
        empty = df["product_title"].str.len() == 0
        df.loc[empty, "product_title"] = df.loc[empty, "title"].fillna("").astype(str)

    # Same for category.
    if "category" in df.columns and "product_category" in df.columns:
        df["product_category"] = df["product_category"].fillna("").astype(str)
        empty = df["product_category"].str.len() == 0
        df.loc[empty, "product_category"] = df.loc[empty, "category"].fillna("").astype(str)

    # Prefer the rich `persona_review` column when present (corpus-builder's
    # final synthesised review). Fall back to `review`.
    if "persona_review" in df.columns:
        df["review"] = df["persona_review"].fillna(df.get("review", "")).astype(str)

    # target_rating is the corpus-builder's GT rating (1-5 string). The plain
    # `rating` column is a constant 3 placeholder in our corpus build, so we
    # prefer target_rating when present.
    if "target_rating" in df.columns:
        def _coerce_rating(row):
            tr = row.get("target_rating")
            if tr is not None and str(tr).strip() not in ("", "None", "nan"):
                try:
                    return int(round(float(tr)))
                except Exception:
                    return None
            r = row.get("rating")
            try:
                return int(round(float(r))) if r is not None else None
            except Exception:
                return None
        df["rating"] = df.apply(_coerce_rating, axis=1)
        df = df[df["rating"].notna()].copy()
        df["rating"] = df["rating"].astype(int)

    # Drop rows without product_title — they're seed_grounded pipeline rows
    # whose "review" is about an underspecified item; product-grounded eval
    # would be apples-to-oranges.
    n_before = len(df)
    df = df[df["product_title"].fillna("").astype(str).str.len() > 0].reset_index(drop=True)
    n_after = len(df)
    if n_after < n_before:
        logger.info("filtered %d/%d rows missing product_title (likely seed_grounded)",
                    n_before - n_after, n_before)

    return df.to_dict("records")


def _load_jsonl(p: Path) -> list[dict[str, Any]]:
    """Load alpaca-format JSONL — extract persona, product, rating, review from input/output."""
    rows: list[dict[str, Any]] = []
    with p.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            # Parse persona from "### Persona\n{...}" block in input
            input_text = r.get("input", "")
            persona_match = re.search(r"### Persona\s*\n(\{.*?\})", input_text, re.DOTALL)
            product_match = re.search(r"### Product\s*\n(\{.*?\})", input_text, re.DOTALL)
            try:
                persona = json.loads(persona_match.group(1)) if persona_match else {}
            except Exception:
                persona = {}
            try:
                product = json.loads(product_match.group(1)) if product_match else {}
            except Exception:
                product = {}
            # Parse output JSON for rating + review
            try:
                output = json.loads(r.get("output", "{}"))
            except Exception:
                output = {}
            rows.append({
                "persona_id": persona.get("persona_id", "unknown"),
                "register_tier": persona.get("register_tier", "nigerian_english"),
                "product_title": product.get("title", ""),
                "product_category": product.get("category", ""),
                "rating": int(output.get("rating", 3)),
                "review": output.get("review", ""),
            })
    return rows


# --------------------------------------------------------------------------- #
# Metric helpers                                                               #
# --------------------------------------------------------------------------- #

def rmse(predictions: list[int], targets: list[int]) -> float:
    if not predictions:
        return float("nan")
    sq = [(p - t) ** 2 for p, t in zip(predictions, targets)]
    return statistics.mean(sq) ** 0.5


def bootstrap_ci(
    values: list[float],
    n_resamples: int = 1000,
    confidence: float = 0.95,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap mean + (lo, hi) percentile CI for a per-sample metric.

    Returns: (point_estimate, ci_low, ci_high). Returns (mean, NaN, NaN) if
    fewer than 2 samples (CI undefined).
    """
    import random as _random
    if not values:
        return (float("nan"), float("nan"), float("nan"))
    point = statistics.mean(values)
    if len(values) < 2:
        return (point, float("nan"), float("nan"))
    rng = _random.Random(seed)
    n = len(values)
    means: list[float] = []
    for _ in range(n_resamples):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(n_resamples * (1 - confidence) / 2)]
    hi = means[int(n_resamples * (1 - (1 - confidence) / 2))]
    return (point, lo, hi)


def bootstrap_rmse(
    pred: list[int], gt: list[int],
    n_resamples: int = 1000, confidence: float = 0.95, seed: int = 42,
) -> tuple[float, float, float]:
    """Bootstrap CI for RMSE specifically (re-computes RMSE on each resample).

    RMSE isn't a simple per-sample mean, so we resample (pred, gt) pairs.
    """
    import random as _random
    if not pred:
        return (float("nan"), float("nan"), float("nan"))
    point = rmse(pred, gt)
    if len(pred) < 2:
        return (point, float("nan"), float("nan"))
    rng = _random.Random(seed)
    n = len(pred)
    rmses: list[float] = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        rmses.append(rmse([pred[i] for i in idx], [gt[i] for i in idx]))
    rmses.sort()
    lo = rmses[int(n_resamples * (1 - confidence) / 2)]
    hi = rmses[int(n_resamples * (1 - (1 - confidence) / 2))]
    return (point, lo, hi)


def detect_register(text: str) -> str:
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


def cultural_marker_recall(predicted: str, ground_truth: str) -> float | None:
    """Of the markers in ground_truth, fraction that appear in predicted."""
    gt = (ground_truth or "").lower()
    pred = (predicted or "").lower()
    gt_markers = {m for m in ALL_NIGERIAN_MARKERS if m in gt}
    if not gt_markers:
        return None
    return sum(1 for m in gt_markers if m in pred) / len(gt_markers)


def length_ratio(predicted: str, ground_truth: str) -> float:
    if not ground_truth:
        return 0.0
    return len(predicted) / max(len(ground_truth), 1)


def _ndcg(predicted_ranks: list[str], relevant: set[str], k: int = 10) -> float:
    """NDCG@k. Binary relevance — item is in the relevant set or not."""
    import math
    relevant_items = list(relevant)
    if not relevant_items:
        return 0.0
    dcg = 0.0
    for i, item in enumerate(predicted_ranks[:k]):
        if item in relevant:
            dcg += 1.0 / math.log2(i + 2)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant_items), k)))
    return dcg / idcg if idcg > 0 else 0.0


def _hr_at_k(predicted_ranks: list[str], relevant: set[str], k: int) -> float:
    """Fraction of relevant items appearing in top-k predictions."""
    if not relevant:
        return 0.0
    return sum(1 for item in predicted_ranks[:k] if item in relevant) / min(len(relevant), k)


def bertscore_batch(predictions: list[str], targets: list[str]) -> dict[str, float]:
    """Run BERTScore on pred-vs-target pairs. Returns mean P/R/F1."""
    try:
        from bert_score import score as bert_score
    except ImportError:
        logger.warning("bert-score not installed (`pip install bert-score`) — skipping BERTScore")
        return {"P": float("nan"), "R": float("nan"), "F1": float("nan")}
    if not predictions or not targets:
        return {"P": float("nan"), "R": float("nan"), "F1": float("nan")}
    try:
        P, R, F1 = bert_score(predictions, targets, lang="en", verbose=False, device="cpu")
        return {
            "P":  float(P.mean()),
            "R":  float(R.mean()),
            "F1": float(F1.mean()),
        }
    except Exception as e:
        logger.warning("BERTScore failed: %s", e)
        return {"P": float("nan"), "R": float("nan"), "F1": float("nan")}


def agentsociety_metrics(predictions: list[str], targets: list[str],
                         pred_stars: list[float], gt_stars: list[float]) -> dict[str, float]:
    """Replicate the official AgentSociety EvaluationTool numbers.

    Their three components, normalised so higher is better:
      - preference_estimation = 1 - mean(|sim - real| / 5)
      - review_generation     = 1 - (0.25*sentiment_err + 0.25*emotion_err + 0.5*topic_err)
      - overall_quality       = mean of the two

    Implementation mirrors websocietysimulator/tools/evaluation_tool.py.
    sentence-transformers + transformers + nltk are heavyweight; if absent we
    return NaN for that sub-metric and a warning, so the script never crashes
    on a fresh clone.
    """
    out: dict[str, float] = {}

    # ── Preference estimation (always available — pure arithmetic) ────────
    if pred_stars and gt_stars:
        errs = [abs(min(5, max(0, p)) - t) / 5.0 for p, t in zip(pred_stars, gt_stars)]
        out["preference_estimation"] = float(1 - sum(errs) / len(errs))
    else:
        out["preference_estimation"] = float("nan")

    # ── Sentiment error via NLTK VADER ────────────────────────────────────
    try:
        import nltk
        try:
            nltk.data.find("sentiment/vader_lexicon.zip")
        except LookupError:
            nltk.download("vader_lexicon", quiet=True)
        from nltk.sentiment import SentimentIntensityAnalyzer
        sia = SentimentIntensityAnalyzer()
        sent_errs = []
        for p, t in zip(predictions, targets):
            if not p or not t:
                continue
            s1 = sia.polarity_scores(p)["compound"]
            s2 = sia.polarity_scores(t)["compound"]
            sent_errs.append(abs(s1 - s2) / 2.0)
        sentiment_error = float(sum(sent_errs) / len(sent_errs)) if sent_errs else float("nan")
    except Exception as e:
        logger.warning("AgentSociety sentiment metric skipped: %s", e)
        sentiment_error = float("nan")
    out["sentiment_error"] = sentiment_error

    # ── Topic error via sentence-transformers cosine distance ─────────────
    try:
        from sentence_transformers import SentenceTransformer
        from scipy.spatial import distance
        model = SentenceTransformer("paraphrase-MiniLM-L6-v2", device="cpu")
        topic_errs = []
        for p, t in zip(predictions, targets):
            if not p or not t:
                continue
            emb = model.encode([p, t], show_progress_bar=False)
            topic_errs.append(float(distance.cosine(emb[0], emb[1])) / 2.0)
        topic_error = float(sum(topic_errs) / len(topic_errs)) if topic_errs else float("nan")
    except Exception as e:
        logger.warning("AgentSociety topic metric skipped: %s", e)
        topic_error = float("nan")
    out["topic_error"] = topic_error

    # ── Emotion error via cardiffnlp/twitter-roberta-base-emotion ─────────
    try:
        from transformers import pipeline
        clf = pipeline(
            "text-classification",
            model="cardiffnlp/twitter-roberta-base-emotion",
            top_k=5, device=-1,
        )
        # Cap each text at 300 chars per their reference implementation
        preds_c = [(p or "")[:300] for p in predictions if p]
        tgts_c  = [(t or "")[:300] for t in targets    if t]
        n = min(len(preds_c), len(tgts_c))
        if n == 0:
            raise RuntimeError("no overlapping pred/target pairs")
        sim_em = clf(preds_c[:n])
        real_em = clf(tgts_c[:n])
        emotion_errs = []
        for se, re_ in zip(sim_em, real_em):
            d1 = {e["label"]: e["score"] for e in se}
            d2 = {e["label"]: e["score"] for e in re_}
            keys = set(d1) | set(d2)
            v1 = [d1.get(k, 0) for k in keys]
            v2 = [d2.get(k, 0) for k in keys]
            emotion_errs.append(sum(abs(a - b) for a, b in zip(v1, v2)) / len(keys))
        emotion_error = float(sum(emotion_errs) / len(emotion_errs))
    except Exception as e:
        logger.warning("AgentSociety emotion metric skipped: %s", e)
        emotion_error = float("nan")
    out["emotion_error"] = emotion_error

    # ── Composite review_generation + overall_quality ─────────────────────
    import math as _math
    if not any(_math.isnan(x) for x in (sentiment_error, topic_error, emotion_error)):
        out["review_generation"] = float(
            1 - (0.25 * sentiment_error + 0.25 * emotion_error + 0.5 * topic_error)
        )
        out["overall_quality"] = float(
            (out["preference_estimation"] + out["review_generation"]) / 2
        )
    else:
        out["review_generation"] = float("nan")
        out["overall_quality"] = float("nan")
    return out


def rouge_batch(predictions: list[str], targets: list[str]) -> dict[str, float]:
    """Run ROUGE-1/2/L. Returns mean F1."""
    try:
        from rouge_score import rouge_scorer
    except ImportError:
        logger.warning("rouge-score not installed (`pip install rouge-score`) — skipping ROUGE")
        return {"rouge1": float("nan"), "rouge2": float("nan"), "rougeL": float("nan")}
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    sums = {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
    n = 0
    for pred, tgt in zip(predictions, targets):
        if not pred or not tgt:
            continue
        scores = scorer.score(tgt, pred)
        for k in sums:
            sums[k] += scores[k].fmeasure
        n += 1
    return {k: v / n if n else float("nan") for k, v in sums.items()}


# --------------------------------------------------------------------------- #
# API call helpers                                                             #
# --------------------------------------------------------------------------- #

async def call_simulate_review(client: httpx.AsyncClient, persona: dict, product: dict,
                                backbone: str) -> dict[str, Any]:
    payload = {"persona": persona, "product": product, "backbone_override": backbone}
    try:
        r = await client.post(f"{API_URL}/simulate-review", json=payload, timeout=180)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)[:200]}


async def call_recommend(client: httpx.AsyncClient, persona: dict, candidate_set: list[str],
                          reranker: str, k: int = 10) -> dict[str, Any]:
    payload = {
        "persona": persona, "candidate_set": candidate_set,
        "k": k, "reranker_override": reranker,
    }
    try:
        r = await client.post(f"{API_URL}/recommend", json=payload, timeout=180)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)[:200]}


# --------------------------------------------------------------------------- #
# Task A — User Modeling eval                                                  #
# --------------------------------------------------------------------------- #

def _row_to_persona(row: dict) -> dict[str, Any]:
    """Construct a Persona-shaped dict from a test row."""
    return {
        "user_id": row.get("persona_id", "test"),
        "register_tier": row.get("register_tier", "nigerian_english"),
        "register_markers": [],
        "register_confidence": 0.85,
        "hedonic_utilitarian": 0.6,
        "communal_individual": 0.55,
        "intensity_calibration": {},
        "aspect_priority": {"quality": 0.4, "value": 0.3, "delivery": 0.2, "packaging": 0.1},
        "review_anchors": [],
        "history_count": 5,
        "extraction_source": "manual",
    }


def _row_to_product(row: dict) -> dict[str, Any]:
    title = row.get("product_title") or row.get("title") or "Test Product"
    category = row.get("product_category") or row.get("category") or "general"
    description = (row.get("description") or "")[:800]
    price = row.get("price_naira")
    return {
        "product_id": str(row.get("product_id") or title)[:60],
        "title": title,
        "category": category,
        "description": description,
        "price_naira": float(price) if price and not (isinstance(price, float) and price != price) else None,
        "domain": "jumia",
    }


async def eval_task1(test_set: list[dict], n: int, backbones: dict[str, str]) -> dict[str, Any]:
    """Run Task A eval across the chosen backbones."""
    subset = test_set[:n]
    logger.info("Task A — evaluating on %d test rows × %d backbones", len(subset), len(backbones))

    results: dict[str, dict[str, Any]] = {}
    async with httpx.AsyncClient() as client:
        for label, backbone in backbones.items():
            logger.info("  → %s (%s)", label, backbone)
            sem = asyncio.Semaphore(CONCURRENCY)

            async def _one(row):
                async with sem:
                    return row, await call_simulate_review(
                        client, _row_to_persona(row), _row_to_product(row), backbone
                    )

            tasks = [_one(row) for row in subset]
            preds_rating, gt_rating = [], []
            preds_review, gt_review = [], []
            register_match, marker_recall_scores = 0, []
            n_valid, n_errors = 0, 0

            for fut in asyncio.as_completed(tasks):
                row, res = await fut
                if "error" in res:
                    n_errors += 1
                    continue
                n_valid += 1
                preds_rating.append(int(res.get("rating", 3)))
                gt_rating.append(int(row["rating"]))
                preds_review.append(res.get("review", ""))
                gt_review.append(row["review"])

                if detect_register(res.get("review", "")) == row.get("register_tier", ""):
                    register_match += 1
                cmr = cultural_marker_recall(res.get("review", ""), row["review"])
                if cmr is not None:
                    marker_recall_scores.append(cmr)

            results[label] = {
                "backbone": backbone,
                "n_valid": n_valid,
                "n_errors": n_errors,
                "RMSE": rmse(preds_rating, gt_rating),
                "register_match_pct": 100 * register_match / max(n_valid, 1),
                "cultural_marker_recall": (
                    statistics.mean(marker_recall_scores) if marker_recall_scores else None
                ),
                "length_ratio_mean": (
                    statistics.mean(length_ratio(p, t) for p, t in zip(preds_review, gt_review))
                    if preds_review else None
                ),
                "_preds_review": preds_review,
                "_gt_review": gt_review,
                "_pred_stars": [float(s) for s in preds_rating],
                "_gt_stars": [float(s) for s in gt_rating],
            }
            logger.info(
                "    n=%d errors=%d RMSE=%.3f register_match=%.1f%%",
                n_valid, n_errors, results[label]["RMSE"], results[label]["register_match_pct"],
            )

    # BERTScore + ROUGE + official AgentSociety metrics (slow, batched)
    logger.info("Computing BERTScore + ROUGE + AgentSociety metrics (may take a few min)...")
    for label, r in results.items():
        if r["n_valid"] == 0:
            continue
        r["BERTScore"] = bertscore_batch(r["_preds_review"], r["_gt_review"])
        r["ROUGE"] = rouge_batch(r["_preds_review"], r["_gt_review"])
        r["AgentSociety"] = agentsociety_metrics(
            r["_preds_review"], r["_gt_review"],
            r["_pred_stars"], r["_gt_stars"],
        )
        # Strip the raw text fields from JSON output (keep summary numbers only)
        for k in ("_preds_review", "_gt_review", "_pred_stars", "_gt_stars"):
            r.pop(k, None)
        logger.info(
            "    %s BERTScore F1=%.3f ROUGE-L=%.3f AS-overall=%.3f",
            label, r["BERTScore"]["F1"], r["ROUGE"]["rougeL"],
            r["AgentSociety"].get("overall_quality", float("nan")),
        )

    return results


# --------------------------------------------------------------------------- #
# Task B — Recommendation eval                                                 #
# --------------------------------------------------------------------------- #

def _build_task2_scenarios(test_set: list[dict], n_scenarios: int) -> list[dict[str, Any]]:
    """
    Build recommendation test scenarios with synthetic ground-truth ranks.

    For each persona:
    - Group their reviews by rating (4-5 = relevant, 1-2 = irrelevant)
    - Sample a candidate set: 3 relevant products + 7 irrelevant products
    - Ground truth: the 3 relevant products should rank in top of the K=10 output
    """
    by_persona = defaultdict(list)
    for row in test_set:
        by_persona[row.get("persona_id", "unknown")].append(row)

    scenarios = []
    for persona_id, rows in by_persona.items():
        relevant = [r["product_title"] for r in rows if r.get("rating", 3) >= 4 and r.get("product_title")]
        irrelevant = [r["product_title"] for r in rows if r.get("rating", 3) <= 2 and r.get("product_title")]
        # Need at least some relevant + irrelevant
        if len(relevant) < 2 or len(irrelevant) < 2:
            continue

        # Sample candidate set of 10
        n_rel = min(3, len(relevant))
        n_irr = 10 - n_rel
        candidate_titles = (
            random.sample(relevant, n_rel)
            + random.sample(irrelevant, min(n_irr, len(irrelevant)))
        )
        # Pad with global random if still short
        all_titles = list({r.get("product_title", "") for r in test_set if r.get("product_title")})
        while len(candidate_titles) < 10 and all_titles:
            cand = random.choice(all_titles)
            if cand not in candidate_titles:
                candidate_titles.append(cand)

        if len(candidate_titles) >= 5:
            scenarios.append({
                "persona": _row_to_persona(rows[0]),
                "candidate_titles": candidate_titles,
                "relevant_titles": set(random.sample(relevant, n_rel)),
            })
        if len(scenarios) >= n_scenarios:
            break

    return scenarios


async def eval_task2(test_set: list[dict], n_scenarios: int,
                      backbones: dict[str, str]) -> dict[str, Any]:
    """Run Task B eval — synthesize ground-truth ranks from persona × rating history."""
    scenarios = _build_task2_scenarios(test_set, n_scenarios)
    if not scenarios:
        logger.warning("Task B: no scenarios could be built — need personas with ≥2 4+ star and ≥2 1-2 star reviews")
        return {}

    logger.info("Task B — %d scenarios × %d backbones", len(scenarios), len(backbones))
    results: dict[str, dict[str, Any]] = {}

    async with httpx.AsyncClient() as client:
        for label, backbone in backbones.items():
            logger.info("  → %s (%s)", label, backbone)
            sem = asyncio.Semaphore(CONCURRENCY)

            async def _one(scenario):
                async with sem:
                    res = await call_recommend(
                        client, scenario["persona"], scenario["candidate_titles"], backbone, k=10
                    )
                return scenario, res

            tasks = [_one(s) for s in scenarios]
            ndcg_at_10, hr_at_1, hr_at_3, hr_at_5 = [], [], [], []
            n_valid, n_errors = 0, 0

            for fut in asyncio.as_completed(tasks):
                scenario, res = await fut
                if "error" in res or not res.get("recommendations"):
                    n_errors += 1
                    continue
                n_valid += 1
                pred_ranks = [r.get("title", r.get("product_id", "")) for r in res["recommendations"]]
                relevant = scenario["relevant_titles"]
                ndcg_at_10.append(_ndcg(pred_ranks, relevant, k=10))
                hr_at_1.append(_hr_at_k(pred_ranks, relevant, k=1))
                hr_at_3.append(_hr_at_k(pred_ranks, relevant, k=3))
                hr_at_5.append(_hr_at_k(pred_ranks, relevant, k=5))

            results[label] = {
                "reranker": backbone,
                "n_valid": n_valid,
                "n_errors": n_errors,
                "NDCG_at_10": statistics.mean(ndcg_at_10) if ndcg_at_10 else float("nan"),
                "HR_at_1":    statistics.mean(hr_at_1) if hr_at_1 else float("nan"),
                "HR_at_3":    statistics.mean(hr_at_3) if hr_at_3 else float("nan"),
                "HR_at_5":    statistics.mean(hr_at_5) if hr_at_5 else float("nan"),
            }
            logger.info(
                "    n=%d errors=%d NDCG@10=%.3f HR@5=%.3f",
                n_valid, n_errors, results[label]["NDCG_at_10"], results[label]["HR_at_5"],
            )

    return results


# --------------------------------------------------------------------------- #
# Reporting                                                                    #
# --------------------------------------------------------------------------- #

def write_results(task1: dict, task2: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    combined = {"task1_user_modeling": task1, "task2_recommendation": task2}

    json_path = out_dir / "results.json"
    json_path.write_text(json.dumps(combined, indent=2, default=str))
    logger.info("💾 results.json → %s", json_path)

    # Pretty markdown table
    md_lines = ["# Evaluation Results — Naija Persona Agent\n"]
    if task1:
        md_lines.append("## Task A — User Modeling (Review Generation)\n")
        md_lines.append("### Our metrics (rubric-aligned)\n")
        md_lines.append("| Model | n | RMSE ↓ | BERTScore F1 ↑ | ROUGE-L ↑ | Register match ↑ | Marker recall ↑ |")
        md_lines.append("|---|---|---|---|---|---|---|")
        for label, r in task1.items():
            bs = r.get("BERTScore", {})
            ro = r.get("ROUGE", {})
            md_lines.append(
                f"| **{label}** | {r['n_valid']} | "
                f"{r.get('RMSE', float('nan')):.3f} | "
                f"{bs.get('F1', float('nan')):.3f} | "
                f"{ro.get('rougeL', float('nan')):.3f} | "
                f"{r.get('register_match_pct', 0):.1f}% | "
                f"{(r.get('cultural_marker_recall') or 0)*100:.1f}% |"
            )
        md_lines.append("")
        md_lines.append("### Official AgentSociety metrics (run by the upstream simulator)\n")
        md_lines.append("| Model | preference_estimation ↑ | sentiment_err ↓ | emotion_err ↓ | topic_err ↓ | review_generation ↑ | **overall_quality ↑** |")
        md_lines.append("|---|---|---|---|---|---|---|")
        for label, r in task1.items():
            ag = r.get("AgentSociety", {}) or {}
            md_lines.append(
                f"| **{label}** | "
                f"{ag.get('preference_estimation', float('nan')):.3f} | "
                f"{ag.get('sentiment_error', float('nan')):.3f} | "
                f"{ag.get('emotion_error', float('nan')):.3f} | "
                f"{ag.get('topic_error', float('nan')):.3f} | "
                f"{ag.get('review_generation', float('nan')):.3f} | "
                f"**{ag.get('overall_quality', float('nan')):.3f}** |"
            )
        md_lines.append("")
    if task2:
        md_lines.append("\n## Task B — Recommendation\n")
        md_lines.append("| Model (re-ranker) | n | NDCG@10 ↑ | HR@1 ↑ | HR@3 ↑ | HR@5 ↑ |")
        md_lines.append("|---|---|---|---|---|---|")
        for label, r in task2.items():
            md_lines.append(
                f"| **{label}** | {r['n_valid']} | "
                f"{r.get('NDCG_at_10', 0):.3f} | "
                f"{r.get('HR_at_1', 0):.3f} | "
                f"{r.get('HR_at_3', 0):.3f} | "
                f"{r.get('HR_at_5', 0):.3f} |"
            )
        md_lines.append("")

    md_path = out_dir / "results.md"
    md_path.write_text("\n".join(md_lines))
    logger.info("💾 results.md → %s", md_path)

    # Print to stdout
    print("\n" + "=" * 80)
    print(md_path.read_text())
    print("=" * 80)


# --------------------------------------------------------------------------- #
# Main                                                                         #
# --------------------------------------------------------------------------- #

async def main_async(args) -> int:
    test_set = load_test_set(args.test_set)
    random.seed(args.seed)
    random.shuffle(test_set)

    task1_results, task2_results = {}, {}

    if not args.task2_only:
        backbones = BACKBONES_TASK1
        if args.backbone == "naija_only":
            backbones = {"naija_reviewer_8b": BACKBONES_TASK1["naija_reviewer_8b"]}
        task1_results = await eval_task1(test_set, args.n, backbones)

    if not args.task1_only:
        backbones = BACKBONES_TASK2
        if args.backbone == "naija_only":
            backbones = {"naija_reviewer_8b": BACKBONES_TASK2["naija_reviewer_8b"]}
        task2_results = await eval_task2(test_set, args.n_scenarios, backbones)

    write_results(task1_results, task2_results, PROJECT_ROOT / "paper")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=50, help="Task A: rows per backbone")
    parser.add_argument("--n-scenarios", type=int, default=30, help="Task B: persona scenarios")
    parser.add_argument("--test-set", type=Path, default=None, help="Path to test set (jsonl/parquet)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--task1-only", action="store_true")
    parser.add_argument("--task2-only", action="store_true")
    parser.add_argument("--backbone", choices=["all", "naija_only"], default="all")
    args = parser.parse_args()

    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
