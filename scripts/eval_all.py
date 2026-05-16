"""Run the full evaluation suite for the paper.

Day-1 stub. Wires together baselines, ablations, and the main results table.
"""

from __future__ import annotations

import sys


def main() -> int:
    print("Day-1 stub. On Day 3, implement:")
    print("  - read test split")
    print("  - call /simulate-review with our full system (NaijaReviewer-8B + persona)")
    print("  - call same for ablation rows")
    print("  - call vanilla baselines (Claude, GPT-4o, base Llama)")
    print("  - compute RMSE, BERTScore F1, RGM, register-tier match")
    print("  - call /recommend for Task 2 (HR@1, HR@3, HR@5, NDCG@5)")
    print("  - aggregate to paper/results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
