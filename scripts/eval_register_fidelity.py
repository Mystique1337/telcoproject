"""No-ground-truth register-fidelity eval.

Runs every (persona, product) combination in data/sample/ through each backbone
and measures the metrics that DON'T need a ground-truth review:

  - register_match_pct: detected register of output == persona's declared tier
  - tier_appropriate_pct: for Pidgin/code-mixed personas, output uses >= 1 marker
  - cultural_marker_count_mean: avg # Pidgin/Nigerian markers per output
  - length_chars_mean
  - latency_ms_mean
  - rating_distribution (1-5 histogram)

This is the eval we can run BEFORE the held-out test set arrives from Drive.
It directly evidences the rubric's "register fidelity" and "Nigerian-context
bonus" lines, which are the strongest claim in our paper anyway.

Outputs:
  paper/results_register_fidelity.json
  paper/results.md   (replaces the placeholder TBD section)

Usage:
  python scripts/eval_register_fidelity.py
  python scripts/eval_register_fidelity.py --concurrency 4
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

logger = logging.getLogger("eval_register")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")

API_URL = "http://localhost:8765"

BACKBONES = {
    "naija_reviewer_8b":           "lmstudio:naija-reviewer-8b",
    "claude_sonnet_4_with_prompt": "anthropic:claude-sonnet-4-20250514",
    # Special pseudo-backbone: bypasses our /simulate-review pipeline and calls
    # Anthropic directly with a minimal prompt. Apples-to-apples baseline that
    # isolates the value of our register-aware scaffolding from the fine-tune.
    "claude_sonnet_4_raw":         "RAW:anthropic:claude-sonnet-4-20250514",
}

# True Pidgin lexicon — words/phrases that signal a Pidgin register specifically.
PIDGIN_MARKERS = {
    "abeg", "wahala", "no cap", "nna", "scatter", "shey", "sef",
    "haba", "omo", "naija", "ahn ahn", "na fire", "chop", "gbam",
    "yawa", "shege", "comot", "epp", "shakara",
    "dem", "wetin", "e clear", "e too much", "e dey", "e shock", "owambe",
}
# Nigerian English specifically — markers that signal NE register without Pidgin.
NIGERIAN_ENGLISH_MARKERS = {
    "well done", "thank god", "by god's grace", "by god grace",
    "no shaking", "sharp sharp", "as for me", "see ehn",
}
# Register-neutral Nigerian/religious markers — used across Pidgin, code-mixed,
# Nigerian English, and even standard Nigerian writing. They signal "this is a
# Nigerian voice" but NOT which tier — so we must NOT use them to classify a
# review as Pidgin (that was the detector bug).
NIGERIAN_NEUTRAL_MARKERS = {
    "alhamdulillah", "mashallah", "wallahi",          # Hausa/Muslim Nigerian
    "biko",                                            # Igbo "please" — used widely
    "by god's grace", "by god grace", "thank god",    # Christian Nigerian
}


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


def count_markers(text: str) -> int:
    """Total Nigerian-voice marker count (Pidgin + NE + neutral — for marker density)."""
    t = (text or "").lower()
    all_markers = PIDGIN_MARKERS | NIGERIAN_ENGLISH_MARKERS | NIGERIAN_NEUTRAL_MARKERS
    return sum(1 for m in all_markers if m in t)


def tier_is_nigerian(tier: str) -> bool:
    return tier in ("nigerian_pidgin", "code_mixed", "nigerian_english")


def load_personas() -> list[dict[str, Any]]:
    out = []
    for p in sorted((PROJECT_ROOT / "data" / "sample" / "personas").glob("*.json")):
        out.append(json.loads(p.read_text()))
    return out


def load_products() -> list[dict[str, Any]]:
    out = []
    for p in sorted((PROJECT_ROOT / "data" / "sample" / "products").glob("*.json")):
        out.append(json.loads(p.read_text()))
    return out


async def call_one(client: httpx.AsyncClient, persona: dict, product: dict,
                    backbone: str) -> dict[str, Any]:
    """Dispatch one (persona, product) → review/rating call.

    If backbone starts with "RAW:", bypass our FastAPI pipeline and call the
    provider directly with a minimal prompt — no register awareness, no
    persona scaffolding. This is the apples-to-apples baseline that
    isolates the value of our pipeline from raw frontier-model capability.
    """
    if backbone.startswith("RAW:"):
        return await _call_raw(client, persona, product, backbone[4:])

    payload = {
        "persona": persona,
        "product": product,
        "backbone_override": backbone,
    }
    t0 = time.perf_counter()
    try:
        r = await client.post(f"{API_URL}/simulate-review", json=payload, timeout=180)
        r.raise_for_status()
        result = r.json()
        result["_latency_ms"] = int((time.perf_counter() - t0) * 1000)
        return result
    except Exception as e:
        return {"error": str(e)[:200], "_latency_ms": int((time.perf_counter() - t0) * 1000)}


async def _call_raw(client: httpx.AsyncClient, persona: dict, product: dict,
                    spec: str) -> dict[str, Any]:
    """Direct LLM call with a minimal prompt — no NPA pipeline."""
    import os
    provider, model = spec.split(":", 1)
    t0 = time.perf_counter()

    prompt = (
        f"You are a user described by this profile:\n{json.dumps(persona)}\n\n"
        f"Write a product review and a star rating (1-5) for this product:\n"
        f"{json.dumps(product)}\n\n"
        f"Respond exactly as:\nstars: <number>\nreview: <one paragraph>"
    )

    if provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not set", "_latency_ms": 0}
        try:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 400,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=180,
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"]
        except Exception as e:
            return {"error": str(e)[:200], "_latency_ms": int((time.perf_counter() - t0) * 1000)}
    else:
        return {"error": f"raw mode unsupported for provider {provider}", "_latency_ms": 0}

    stars, review = _parse_stars_review(text)
    return {
        "rating": stars or 3,
        "review": review or text,
        "register_tier": "unknown",
        "_latency_ms": int((time.perf_counter() - t0) * 1000),
    }


def _parse_stars_review(text: str) -> tuple[int | None, str | None]:
    import re as _re
    stars: int | None = None
    review_lines: list[str] = []
    in_review = False
    for raw in (text or "").splitlines():
        low = raw.strip().lower()
        if low.startswith("stars:") or low.startswith("rating:"):
            m = _re.search(r"(\d+(?:\.\d+)?)", raw)
            if m:
                stars = int(round(float(m.group(1))))
        elif low.startswith("review:"):
            in_review = True
            tail = raw.split(":", 1)[1].strip()
            if tail:
                review_lines.append(tail)
        elif in_review:
            review_lines.append(raw.strip())
    review = " ".join(review_lines).strip() or None
    if not review:
        review = " ".join(l.strip() for l in (text or "").splitlines() if l.strip()) or None
    return stars, review


async def eval_backbone(label: str, backbone: str, personas: list, products: list,
                        concurrency: int) -> dict[str, Any]:
    logger.info("→ %s (%s) on %d × %d = %d combos",
                label, backbone, len(personas), len(products), len(personas) * len(products))

    sem = asyncio.Semaphore(concurrency)
    rows: list[dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        async def _one(persona, product):
            async with sem:
                return persona, product, await call_one(client, persona, product, backbone)

        tasks = [_one(p, pr) for p in personas for pr in products]
        for fut in asyncio.as_completed(tasks):
            persona, product, res = await fut
            if "error" in res:
                logger.warning("  err for %s × %s: %s",
                               persona.get("user_id", "?"), product.get("product_id", "?"),
                               res["error"][:80])
                continue
            rows.append({
                "persona_id": persona.get("user_id"),
                "declared_tier": persona.get("register_tier"),
                "product_id": product.get("product_id"),
                "review": res.get("review", ""),
                "rating": int(res.get("rating", 3)),
                "detected_tier": detect_register(res.get("review", "")),
                "marker_count": count_markers(res.get("review", "")),
                "length_chars": len(res.get("review", "")),
                "latency_ms": res["_latency_ms"],
            })

    n = len(rows)
    if n == 0:
        return {"backbone": backbone, "n": 0, "_rows": []}

    n_register_match = sum(1 for r in rows if r["detected_tier"] == r["declared_tier"])
    n_nigerian_personas = sum(1 for r in rows if tier_is_nigerian(r["declared_tier"]))
    n_nigerian_appropriate = sum(
        1 for r in rows
        if tier_is_nigerian(r["declared_tier"]) and r["marker_count"] >= 1
    )

    rating_hist = Counter(r["rating"] for r in rows)
    summary = {
        "backbone": backbone,
        "n": n,
        "register_match_pct": round(100 * n_register_match / n, 1),
        "tier_appropriate_pct_nigerian_only": (
            round(100 * n_nigerian_appropriate / n_nigerian_personas, 1)
            if n_nigerian_personas else None
        ),
        "cultural_marker_count_mean": round(
            statistics.mean(r["marker_count"] for r in rows), 2
        ),
        "cultural_marker_count_median": statistics.median(r["marker_count"] for r in rows),
        "length_chars_mean": round(statistics.mean(r["length_chars"] for r in rows), 0),
        "latency_ms_mean": round(statistics.mean(r["latency_ms"] for r in rows), 0),
        "latency_ms_median": int(statistics.median(r["latency_ms"] for r in rows)),
        "rating_histogram": {str(k): rating_hist.get(k, 0) for k in (1, 2, 3, 4, 5)},
        "_rows": rows,
    }
    logger.info(
        "  %s: n=%d  reg_match=%.1f%%  marker_mean=%.2f  lat_med=%dms",
        label, n, summary["register_match_pct"],
        summary["cultural_marker_count_mean"], summary["latency_ms_median"],
    )
    return summary


def write_report(results: dict[str, dict], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "results_register_fidelity.json"
    json_path.write_text(json.dumps(results, indent=2, default=str))
    logger.info("💾 %s", json_path)

    md_lines = [
        "# Naija Persona Agent — Register Fidelity Eval (no ground truth needed)",
        "",
        "_Eval ran across 5 personas × 6 products = 30 combos per backbone, served via the FastAPI service on port 8765._",
        "",
        "| Model | n | **Register match ↑** | Tier-appropriate (Naija personas) ↑ | Markers/review ↑ | Length (chars) | Latency (median ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, r in results.items():
        if r.get("n", 0) == 0:
            md_lines.append(f"| **{label}** | 0 | — | — | — | — | — |")
            continue
        ta = r.get("tier_appropriate_pct_nigerian_only")
        md_lines.append(
            f"| **{label}** | {r['n']} | "
            f"**{r['register_match_pct']:.1f}%** | "
            f"{ta:.1f}% |" if ta is not None else "— |"
        )
    # Rebuild with proper formatting
    md_lines = [
        "# Naija Persona Agent — Register Fidelity Eval (no ground truth needed)",
        "",
        "_Eval ran across 5 personas × 6 products = 30 combos per backbone, served via the FastAPI service on port 8765._",
        "",
        "| Model | n | **Register match ↑** | Tier-appropriate (Naija personas) ↑ | Markers/review ↑ | Length (chars) | Latency (median ms) |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, r in results.items():
        if r.get("n", 0) == 0:
            md_lines.append(f"| **{label}** | 0 | — | — | — | — | — |")
            continue
        ta_val = r.get("tier_appropriate_pct_nigerian_only")
        ta_str = f"{ta_val:.1f}%" if ta_val is not None else "—"
        md_lines.append(
            f"| **{label}** | {r['n']} | "
            f"**{r['register_match_pct']:.1f}%** | "
            f"{ta_str} | "
            f"{r['cultural_marker_count_mean']:.2f} | "
            f"{int(r['length_chars_mean'])} | "
            f"{r['latency_ms_median']} |"
        )
    md_lines += [
        "",
        "## Rating distribution",
        "",
        "| Model | 1★ | 2★ | 3★ | 4★ | 5★ |",
        "|---|---|---|---|---|---|",
    ]
    for label, r in results.items():
        if r.get("n", 0) == 0:
            continue
        h = r["rating_histogram"]
        md_lines.append(f"| **{label}** | {h['1']} | {h['2']} | {h['3']} | {h['4']} | {h['5']} |")
    md_lines.append("")
    md_lines.append("## Sample outputs (one per persona)")
    md_lines.append("")
    seen: dict[tuple[str, str], bool] = {}
    for label, r in results.items():
        if r.get("n", 0) == 0:
            continue
        md_lines.append(f"### {label}")
        md_lines.append("")
        for row in r["_rows"]:
            key = (label, row["persona_id"])
            if key in seen:
                continue
            seen[key] = True
            md_lines.append(
                f"- **{row['persona_id']}** ({row['declared_tier']}) → ★{row['rating']} · "
                f"detected={row['detected_tier']} · {row['marker_count']} markers"
            )
            md_lines.append(f"  > {row['review'][:280]}{'…' if len(row['review']) > 280 else ''}")
        md_lines.append("")

    md_path = out_dir / "results.md"
    md_path.write_text("\n".join(md_lines))
    logger.info("💾 %s", md_path)

    print("\n" + "=" * 80)
    print(md_path.read_text())
    print("=" * 80)


async def main_async(args) -> int:
    personas = load_personas()
    products = load_products()
    logger.info("Loaded %d personas, %d products", len(personas), len(products))

    results: dict[str, dict] = {}
    for label, backbone in BACKBONES.items():
        results[label] = await eval_backbone(label, backbone, personas, products, args.concurrency)

    write_report(results, PROJECT_ROOT / "paper")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=3)
    args = parser.parse_args()
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
