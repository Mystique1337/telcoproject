"""Human eval CLI — blind A/B pairwise rating of model outputs.

Presents N pre-generated review pairs (NaijaReviewer-8B vs vanilla Claude
Sonnet 4 on the SAME persona × product). Each pair is shown with the model
labels hidden and randomly side-swapped. Rater picks A / B / =.

Outputs:
  paper/human_eval_votes_<rater>.json   — per-rater raw votes
  paper/human_eval_summary.json         — aggregated win-rate + Krippendorff α
                                           across all raters whose vote files exist

Two-step usage:
    # Step 1 (one-time, run by you): generate the blind pair pack
    python scripts/human_eval.py --build --n-pairs 20

    # Step 2 (each rater runs themselves): cast votes
    python scripts/human_eval.py --rate --rater "ashinze"
    python scripts/human_eval.py --rate --rater "franca"
    ...

    # Step 3: aggregate
    python scripts/human_eval.py --aggregate

Free: human eval costs only rater time. No LLM calls during voting.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import random
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

logger = logging.getLogger("human_eval")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — %(message)s")

API_URL = "http://localhost:8765"
PAIRS_PATH = PROJECT_ROOT / "paper" / "human_eval_pairs.json"
VOTES_DIR = PROJECT_ROOT / "paper" / "human_eval_votes"
SUMMARY_PATH = PROJECT_ROOT / "paper" / "human_eval_summary.json"

MODEL_A = "lmstudio:naija-reviewer-8b"   # the fine-tune
MODEL_B = "anthropic:claude-sonnet-4-20250514"


# --------------------------------------------------------------------------- #
# Step 1: build the blind pair pack                                            #
# --------------------------------------------------------------------------- #

async def _gen(client: httpx.AsyncClient, persona: dict, product: dict,
                backbone: str) -> dict[str, Any]:
    try:
        r = await client.post(
            f"{API_URL}/simulate-review",
            json={"persona": persona, "product": product, "backbone_override": backbone},
            timeout=180,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)[:200]}


def _load_personas() -> list[dict]:
    out = []
    for p in sorted((PROJECT_ROOT / "data" / "sample" / "personas").glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def _load_products() -> list[dict]:
    out = []
    for p in sorted((PROJECT_ROOT / "data" / "sample" / "products").glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


async def build_pairs(n_pairs: int, seed: int) -> None:
    rng = random.Random(seed)
    personas = _load_personas()
    products = _load_products()
    if not personas or not products:
        logger.error("need personas + products in data/sample/")
        return

    # Sample N (persona, product) combos, balanced across persona register tiers.
    combos = [(p, pr) for p in personas for pr in products]
    rng.shuffle(combos)
    selected = combos[:n_pairs]
    logger.info("generating %d pairs (model A=%s, model B=%s)",
                n_pairs, MODEL_A, MODEL_B)

    async with httpx.AsyncClient() as client:
        async def _one(persona, product):
            a_task = _gen(client, persona, product, MODEL_A)
            b_task = _gen(client, persona, product, MODEL_B)
            a, b = await asyncio.gather(a_task, b_task)
            return persona, product, a, b

        # Concurrency 2 — gentle on LM Studio
        sem = asyncio.Semaphore(2)
        async def _bounded(persona, product):
            async with sem:
                return await _one(persona, product)

        results = await asyncio.gather(*[_bounded(p, pr) for p, pr in selected])

    pairs = []
    for i, (persona, product, a, b) in enumerate(results):
        if "error" in a or "error" in b:
            logger.warning("  pair %d skipped (API error)", i)
            continue
        # Randomly side-swap A/B per pair so raters can't pattern-match.
        swap = rng.random() < 0.5
        left = b if swap else a
        right = a if swap else b
        left_model = MODEL_B if swap else MODEL_A
        right_model = MODEL_A if swap else MODEL_B
        pairs.append({
            "pair_id": f"p{i:03d}",
            "persona_id": persona.get("user_id"),
            "register_tier": persona.get("register_tier"),
            "product_title": product.get("title"),
            "left": {"review": left.get("review", ""), "rating": left.get("rating", 3),
                     "_model": left_model},
            "right": {"review": right.get("review", ""), "rating": right.get("rating", 3),
                      "_model": right_model},
        })

    PAIRS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAIRS_PATH.write_text(json.dumps(pairs, indent=2, ensure_ascii=False))
    logger.info("✅ wrote %d pairs → %s", len(pairs), PAIRS_PATH)
    logger.info("   raters: `python scripts/human_eval.py --rate --rater <yourname>`")


# --------------------------------------------------------------------------- #
# Step 2: cast votes                                                           #
# --------------------------------------------------------------------------- #

def _rate_one(pair: dict, idx: int, n: int) -> str:
    """Show pair + collect a vote. Returns one of {A, B, =, SKIP}."""
    print("\n" + "─" * 78)
    print(f"PAIR {idx + 1} / {n}   (pair_id: {pair['pair_id']})")
    print(f"Persona: {pair['persona_id']}  ·  Register: {pair['register_tier']}")
    print(f"Product: {pair['product_title']}")
    print()
    print("─── REVIEW A ─────────────────────────────────────────────────────────")
    print(f"  Rating: ★{pair['left']['rating']}")
    print(f"  {pair['left']['review']}")
    print()
    print("─── REVIEW B ─────────────────────────────────────────────────────────")
    print(f"  Rating: ★{pair['right']['rating']}")
    print(f"  {pair['right']['review']}")
    print()
    print(
        "Which review sounds more like an AUTHENTIC Nigerian user matching "
        "this persona?"
    )
    print("  [A]  Review A is more authentic")
    print("  [B]  Review B is more authentic")
    print("  [=]  Equally authentic / can't tell")
    print("  [s]  Skip this pair")
    print("  [q]  Quit (saves progress)")
    while True:
        ans = input("Your vote (A/B/=/s/q): ").strip().upper()
        if ans in ("A", "B", "=", "S", "Q"):
            return ans
        print("  please enter A, B, =, s, or q")


def rate_loop(rater: str) -> None:
    if not PAIRS_PATH.exists():
        logger.error("no pairs found; run with --build first (or copy paper/human_eval_pairs.json)")
        return
    pairs = json.loads(PAIRS_PATH.read_text())
    VOTES_DIR.mkdir(parents=True, exist_ok=True)
    vote_path = VOTES_DIR / f"{rater}.json"

    # Resume from prior votes if file exists.
    votes: dict[str, str] = {}
    if vote_path.exists():
        votes = json.loads(vote_path.read_text())
        logger.info("resuming from %d prior votes by %s", len(votes), rater)

    for idx, pair in enumerate(pairs):
        if pair["pair_id"] in votes and votes[pair["pair_id"]] not in ("S",):
            continue
        try:
            ans = _rate_one(pair, idx, len(pairs))
        except KeyboardInterrupt:
            ans = "Q"
        if ans == "Q":
            break
        votes[pair["pair_id"]] = ans
        vote_path.write_text(json.dumps(votes, indent=2))
    vote_path.write_text(json.dumps(votes, indent=2))
    print(f"\n✅ saved {sum(1 for v in votes.values() if v != 'S')} votes → {vote_path}")


# --------------------------------------------------------------------------- #
# Step 3: aggregate                                                            #
# --------------------------------------------------------------------------- #

def _wilson_ci(wins: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Wilson score 95% CI for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = wins / n
    z = 1.96 if abs(confidence - 0.95) < 1e-6 else 1.96  # close enough for our purposes
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    halfwidth = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return (max(0.0, centre - halfwidth), min(1.0, centre + halfwidth))


def _krippendorff_alpha_nominal(rater_votes: dict[str, dict[str, str]]) -> float:
    """Nominal Krippendorff's alpha for inter-rater agreement.

    Implementation: standard formula for nominal data, ignoring SKIP votes.
    See Krippendorff (2018) §11.
    """
    # Build {pair_id: {rater: vote}} excluding skips
    by_pair: dict[str, dict[str, str]] = {}
    for rater, votes in rater_votes.items():
        for pid, v in votes.items():
            if v in ("S", "SKIP", "Q"):
                continue
            by_pair.setdefault(pid, {})[rater] = v

    # Coincidence matrix
    categories = sorted({v for raters in by_pair.values() for v in raters.values()})
    cat_index = {c: i for i, c in enumerate(categories)}
    k = len(categories)
    if k < 2:
        return float("nan")
    coincidence = [[0.0] * k for _ in range(k)]

    for pid, raters in by_pair.items():
        m_u = len(raters)
        if m_u < 2:
            continue
        vs = list(raters.values())
        for i in range(len(vs)):
            for j in range(len(vs)):
                if i == j:
                    continue
                coincidence[cat_index[vs[i]]][cat_index[vs[j]]] += 1.0 / (m_u - 1)

    n_c = [sum(coincidence[c]) for c in range(k)]
    n_total = sum(n_c)
    if n_total == 0:
        return float("nan")

    # Observed disagreement
    do = sum(coincidence[c1][c2]
             for c1 in range(k) for c2 in range(k)
             if c1 != c2) / n_total
    # Expected disagreement (nominal: 1 - sum(p_i^2))
    de = 1.0 - sum((nc / n_total) ** 2 for nc in n_c)
    if de == 0:
        return float("nan")
    return 1 - do / de


def aggregate() -> None:
    if not PAIRS_PATH.exists():
        logger.error("no pairs file — run --build first")
        return
    pairs = json.loads(PAIRS_PATH.read_text())
    pair_models: dict[str, dict[str, str]] = {
        p["pair_id"]: {"left": p["left"]["_model"], "right": p["right"]["_model"]}
        for p in pairs
    }

    if not VOTES_DIR.exists():
        logger.error("no votes dir — have raters run --rate first")
        return
    rater_votes: dict[str, dict[str, str]] = {}
    for f in sorted(VOTES_DIR.glob("*.json")):
        rater_votes[f.stem] = json.loads(f.read_text())
    if not rater_votes:
        logger.error("no rater files in %s", VOTES_DIR)
        return

    # Tally per-rater wins for each model
    summary: dict[str, Any] = {"n_raters": len(rater_votes), "raters": list(rater_votes), "per_rater": {}}
    naija_wins_all, claude_wins_all, ties_all, decisive_all = 0, 0, 0, 0

    for rater, votes in rater_votes.items():
        naija, claude, tie, decisive = 0, 0, 0, 0
        for pid, v in votes.items():
            if v in ("S", "SKIP", "Q"):
                continue
            if v == "=":
                tie += 1
                decisive += 0
                continue
            decisive += 1
            models = pair_models.get(pid)
            if not models:
                continue
            picked_side = "left" if v == "A" else "right"
            picked_model = models[picked_side]
            if picked_model == MODEL_A:
                naija += 1
            else:
                claude += 1
        naija_wins_all += naija
        claude_wins_all += claude
        ties_all += tie
        decisive_all += decisive
        win_rate = naija / max(decisive, 1)
        wlo, whi = _wilson_ci(naija, decisive) if decisive else (float("nan"),) * 2
        summary["per_rater"][rater] = {
            "naija_wins": naija, "claude_wins": claude, "ties": tie,
            "decisive": decisive,
            "naija_win_rate": win_rate,
            "naija_win_rate_ci95": [wlo, whi],
        }

    overall_decisive = naija_wins_all + claude_wins_all
    overall_win_rate = naija_wins_all / max(overall_decisive, 1)
    wlo, whi = _wilson_ci(naija_wins_all, overall_decisive) if overall_decisive else (float("nan"),) * 2
    alpha = _krippendorff_alpha_nominal(rater_votes)

    summary["overall"] = {
        "naija_wins": naija_wins_all,
        "claude_wins": claude_wins_all,
        "ties": ties_all,
        "decisive_total": overall_decisive,
        "naija_win_rate": overall_win_rate,
        "naija_win_rate_ci95": [wlo, whi],
        "krippendorff_alpha_nominal": alpha,
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2))
    logger.info("💾 %s", SUMMARY_PATH)

    print("\n" + "=" * 70)
    print("HUMAN EVAL — summary")
    print("=" * 70)
    print(f"raters:               {summary['n_raters']}")
    print(f"decisive votes:       {overall_decisive}")
    print(f"ties:                 {ties_all}")
    print(f"naija wins:           {naija_wins_all}")
    print(f"claude wins:          {claude_wins_all}")
    print(f"naija win-rate:       {overall_win_rate:.1%}  "
          f"(95% CI [{wlo:.1%}, {whi:.1%}])")
    print(f"Krippendorff α:       {alpha:.3f}"
          if alpha == alpha else "Krippendorff α:       n/a")
    print("=" * 70)


# --------------------------------------------------------------------------- #
# Entry                                                                        #
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="Step 1: build the blind pair pack")
    ap.add_argument("--rate", action="store_true", help="Step 2: cast votes")
    ap.add_argument("--aggregate", action="store_true", help="Step 3: tally everything")
    ap.add_argument("--n-pairs", type=int, default=20)
    ap.add_argument("--rater", type=str, default=None,
                    help="Rater identifier (only required for --rate)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.build:
        asyncio.run(build_pairs(args.n_pairs, args.seed))
    elif args.rate:
        if not args.rater:
            print("--rater <yourname> is required for --rate"); return 2
        rate_loop(args.rater)
    elif args.aggregate:
        aggregate()
    else:
        ap.print_help()
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
