"""Ablation eval — what does each component contribute?

Runs four conditions on the held-out test split and reports the delta on every
metric eval_all.py reports.

  A. FULL          — NaijaReviewer-8B + structured persona + register-aware prompt
  B. NO_REGISTER   — NaijaReviewer-8B + structured persona, generic prompt (no register block)
  C. NO_PERSONA    — NaijaReviewer-8B with raw "write a review for this product" (no persona schema)
  D. NO_FINETUNE   — Base Llama 3.1 70B (via NIM) + full pipeline

The first three isolate which parts of OUR system matter. The fourth shows
what the fine-tune buys you over a much bigger off-the-shelf model.

Output:
  paper/results_ablation.json     — raw numbers per condition
  paper/results_ablation.md       — pretty markdown table for the paper §5.3

Usage:
  python scripts/eval_ablation.py --n 40
  python scripts/eval_ablation.py --conditions A,C    # subset
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import statistics
import sys
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

from scripts.eval_all import (  # type: ignore
    BACKBONES_TASK1, _row_to_persona, _row_to_product, bootstrap_ci,
    bootstrap_rmse, count_markers, detect_register, length_ratio,
    load_test_set, logger as eval_logger, rmse, rouge_batch, bertscore_batch,
)

logger = logging.getLogger("ablation")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")

API_URL = "http://localhost:8765"


# --------------------------------------------------------------------------- #
# Condition definitions                                                        #
# --------------------------------------------------------------------------- #

NAIJA_BACKBONE = "lmstudio:naija-reviewer-8b"
BASE_LARGE_BACKBONE = "nvidia/llama-3.1-nemotron-70b-instruct"  # via NIM


CONDITIONS: dict[str, dict[str, Any]] = {
    "A_full": {
        "label": "A. Full pipeline (NaijaReviewer-8B)",
        "backbone": NAIJA_BACKBONE,
        "via_api": True,
        "strip_persona": False,
        "strip_register": False,
    },
    "B_no_register": {
        "label": "B. − register-aware prompt",
        "backbone": NAIJA_BACKBONE,
        "via_api": True,
        "strip_persona": False,
        "strip_register": True,
    },
    "C_no_persona": {
        "label": "C. − structured persona",
        "backbone": NAIJA_BACKBONE,
        "via_api": False,  # bare LLM call
        "strip_persona": True,
        "strip_register": True,
    },
    "D_no_finetune": {
        "label": "D. − fine-tune (base Llama-3.1 70B via NIM)",
        "backbone": BASE_LARGE_BACKBONE,
        "via_api": True,
        "strip_persona": False,
        "strip_register": False,
    },
}


# --------------------------------------------------------------------------- #
# Per-condition call paths                                                     #
# --------------------------------------------------------------------------- #

async def _api_call(client: httpx.AsyncClient, persona: dict, product: dict,
                     backbone: str, strip_register: bool) -> dict[str, Any]:
    """Standard /simulate-review call. strip_register patches the persona's
    register_tier to standard_english so the template's register instruction
    becomes the bland one."""
    if strip_register:
        persona = {**persona, "register_tier": "standard_english", "register_markers": []}
    payload = {"persona": persona, "product": product, "backbone_override": backbone}
    try:
        r = await client.post(f"{API_URL}/simulate-review", json=payload, timeout=180)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)[:200]}


async def _bare_lmstudio_call(client: httpx.AsyncClient, product: dict) -> dict[str, Any]:
    """Direct LM Studio call with NO persona context — just product."""
    import os as _os
    lm_url = _os.getenv("LM_STUDIO_URL", "http://localhost:1234/v1")
    prompt = (
        f"Write a product review and a star rating (1-5) for this product:\n"
        f"{json.dumps(product, ensure_ascii=False)}\n\n"
        f"Output exactly:\nRATING: <number>\nREVIEW: <one paragraph>"
    )
    try:
        r = await client.post(
            f"{lm_url}/chat/completions",
            headers={"Content-Type": "application/json"},
            json={
                "model": "naija-reviewer-8b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
                "temperature": 0.7,
            },
            timeout=180,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"] or ""
    except Exception as e:
        return {"error": str(e)[:200]}
    # Parse RATING / REVIEW
    import re as _re
    stars: int | None = None
    review_lines: list[str] = []
    in_review = False
    for raw in text.splitlines():
        low = raw.strip().lower()
        if low.startswith("rating:") or low.startswith("stars:"):
            m = _re.search(r"(\d+(?:\.\d+)?)", raw)
            if m:
                stars = max(1, min(5, int(round(float(m.group(1))))))
        elif low.startswith("review:"):
            in_review = True
            tail = raw.split(":", 1)[1].strip()
            if tail:
                review_lines.append(tail)
        elif in_review:
            review_lines.append(raw.strip())
    return {
        "rating": stars or 3,
        "review": " ".join(review_lines).strip() or text.strip(),
        "register_tier": "unknown",
    }


# --------------------------------------------------------------------------- #
# Eval loop                                                                    #
# --------------------------------------------------------------------------- #

async def run_condition(label: str, cfg: dict, test_set: list[dict], n: int,
                         concurrency: int) -> dict[str, Any]:
    subset = test_set[:n]
    logger.info("→ %s (%s)  n=%d", label, cfg["backbone"], len(subset))
    sem = asyncio.Semaphore(concurrency)
    preds_rating, gt_rating = [], []
    preds_review, gt_review = [], []
    register_match = 0
    marker_counts: list[int] = []
    n_valid, n_errors = 0, 0

    async with httpx.AsyncClient() as client:
        async def _one(row):
            async with sem:
                persona = _row_to_persona(row)
                product = _row_to_product(row)
                if cfg["via_api"]:
                    res = await _api_call(
                        client, persona, product,
                        cfg["backbone"], cfg["strip_register"],
                    )
                else:
                    res = await _bare_lmstudio_call(client, product)
                return row, res

        tasks = [_one(r) for r in subset]
        for fut in asyncio.as_completed(tasks):
            row, res = await fut
            if "error" in res:
                n_errors += 1
                continue
            n_valid += 1
            preds_rating.append(int(res.get("rating", 3)))
            gt_rating.append(int(row["rating"]))
            preds_review.append(res.get("review", ""))
            gt_review.append(row.get("review", ""))
            if detect_register(res.get("review", "")) == row.get("register_tier", ""):
                register_match += 1
            marker_counts.append(count_markers(res.get("review", "")))

    # Metrics with bootstrap CIs
    rmse_point, rmse_lo, rmse_hi = bootstrap_rmse(preds_rating, gt_rating)
    bs = bertscore_batch(preds_review, gt_review) if preds_review else {"F1": float("nan")}
    ro = rouge_batch(preds_review, gt_review) if preds_review else {"rougeL": float("nan")}
    reg_match_pct = 100 * register_match / max(n_valid, 1)
    reg_ci = bootstrap_ci(
        [100.0 if i < register_match else 0.0 for i in range(n_valid)] if n_valid else []
    )
    marker_ci = bootstrap_ci([float(m) for m in marker_counts])

    return {
        "label": cfg["label"],
        "backbone": cfg["backbone"],
        "via_api": cfg["via_api"],
        "strip_persona": cfg["strip_persona"],
        "strip_register": cfg["strip_register"],
        "n_valid": n_valid,
        "n_errors": n_errors,
        "RMSE": {"point": rmse_point, "ci95": [rmse_lo, rmse_hi]},
        "BERTScore_F1": bs.get("F1", float("nan")),
        "ROUGE_L": ro.get("rougeL", float("nan")),
        "register_match_pct": {"point": reg_match_pct, "ci95": list(reg_ci[1:])},
        "markers_per_review": {"point": marker_ci[0], "ci95": list(marker_ci[1:])},
    }


# --------------------------------------------------------------------------- #
# Reporting                                                                    #
# --------------------------------------------------------------------------- #

def _fmt(x: float, fmt: str = "{:.3f}") -> str:
    return fmt.format(x) if x == x else "nan"  # NaN-safe


def _fmt_ci(point: float, lo: float, hi: float, fmt: str = "{:.3f}") -> str:
    p = _fmt(point, fmt)
    if lo != lo or hi != hi:
        return p
    return f"{p} [{_fmt(lo, fmt)}, {_fmt(hi, fmt)}]"


def write_report(results: dict[str, dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results_ablation.json").write_text(
        json.dumps(results, indent=2, default=str)
    )

    md = [
        "# Ablation Study — what contributes the wins?",
        "",
        "Each condition is evaluated on the same held-out test split. The full "
        "system (A) is the baseline; each subsequent row removes one component. "
        "Numbers are point estimates with bootstrap 95% CI in brackets.",
        "",
        "| Condition | n | RMSE ↓ | BERTScore F1 ↑ | ROUGE-L ↑ | Register match ↑ | Markers/review |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, r in results.items():
        rmse_v = r["RMSE"]
        reg_v = r["register_match_pct"]
        mark_v = r["markers_per_review"]
        md.append(
            f"| **{r['label']}** | {r['n_valid']} | "
            f"{_fmt_ci(rmse_v['point'], *rmse_v['ci95'])} | "
            f"{_fmt(r['BERTScore_F1'])} | "
            f"{_fmt(r['ROUGE_L'])} | "
            f"{_fmt_ci(reg_v['point'], *reg_v['ci95'], fmt='{:.1f}%')} | "
            f"{_fmt_ci(mark_v['point'], *mark_v['ci95'], fmt='{:.2f}')} |"
        )
    md.append("")
    (out_dir / "results_ablation.md").write_text("\n".join(md))
    logger.info("💾 %s", out_dir / "results_ablation.json")
    logger.info("💾 %s", out_dir / "results_ablation.md")
    print("\n" + "=" * 80)
    print((out_dir / "results_ablation.md").read_text())


async def main_async(args) -> int:
    test_set = load_test_set(args.test_set)
    import random as _random
    _random.seed(args.seed)
    _random.shuffle(test_set)

    conditions_to_run = args.conditions.split(",") if args.conditions else list(CONDITIONS)
    results: dict[str, dict] = {}
    for key in conditions_to_run:
        full_key = next((k for k in CONDITIONS if k.startswith(key)), None)
        if not full_key:
            logger.warning("unknown condition: %s", key)
            continue
        results[full_key] = await run_condition(
            full_key, CONDITIONS[full_key], test_set, args.n, args.concurrency
        )

    write_report(results, PROJECT_ROOT / "paper")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--concurrency", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--test-set", type=Path, default=None)
    ap.add_argument("--conditions", type=str, default=None,
                    help="Comma-separated prefixes: A,B,C,D")
    args = ap.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
