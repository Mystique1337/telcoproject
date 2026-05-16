"""Evaluate NaijaReviewer-8B head-to-head against baselines on the test split.

Day-1 stub — implement the evaluation harness on Day 3.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="ollama:naija-reviewer-8b")
    parser.add_argument("--baselines", nargs="+", default=[
        "anthropic:claude-sonnet-4-20250514",
        "openai:gpt-4o",
        "ollama:llama3.1:8b-instruct",
    ])
    parser.add_argument("--test_file", default="data/finetune/v1_test.jsonl")
    parser.add_argument("--out", default="paper/results.json")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 7])
    args = parser.parse_args()

    print("Day-1 stub. On Day 3, implement:")
    print("  - load test JSONL")
    print("  - for each model in [our model + baselines]:")
    print("      - for each seed:")
    print("          - generate (rating, review) per test example")
    print("          - compute RMSE, BERTScore, RGM, register-tier match, cultural-marker recall")
    print("  - aggregate mean ± std across seeds")
    print("  - save to", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
