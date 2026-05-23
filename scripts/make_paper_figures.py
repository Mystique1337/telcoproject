"""Generate the figures used in the Task A and Task B papers.

Outputs vector PDFs into paper/figures/:
  - fig_training_loss.pdf   training + validation loss for NaijaReviewer-8B
  - fig_task_a_rmse.pdf     Task A rating-prediction RMSE (lower is better)
  - fig_task_b_ndcg.pdf     Task B NDCG@10 by re-ranker vs model size

Data is the real captured run / eval numbers (see notebooks/03_training_results
and paper/results.md). Re-run any time: python scripts/make_paper_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent.parent / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# Brand-ish palette
NAIJA = "#1f9d55"   # green
GREY = "#9aa0a6"
DARK = "#202124"
EVAL = "#d9480f"    # orange

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.bbox": "tight",
    "figure.dpi": 150,
})


# --------------------------------------------------------------------------- #
# 1. Training + validation loss (real W&B history, run xc3z506e)
# --------------------------------------------------------------------------- #
# (global_step, train/loss) - NaN eval-only rows dropped
TRAIN = [
    (25, 2.525048), (50, 2.099057), (75, 1.902666), (100, 1.871259),
    (125, 1.842007), (150, 1.792507), (175, 1.792452), (200, 1.737915),
    (225, 1.706180), (250, 1.691716), (275, 1.710263), (300, 1.638439),
    (325, 1.691411), (350, 1.645309), (375, 1.671726), (400, 1.652696),
    (425, 1.623813), (450, 1.625577), (475, 1.628035), (500, 1.660273),
    (525, 1.590833), (550, 1.438684), (575, 1.391153), (600, 1.395020),
    (625, 1.375086), (650, 1.416431), (675, 1.408078), (700, 1.393151),
    (725, 1.370936), (750, 1.366918), (775, 1.337886), (800, 1.331477),
    (825, 1.371972), (850, 1.344892), (875, 1.342461), (900, 1.336900),
    (925, 1.349253), (950, 1.349691), (975, 1.324670), (1000, 1.374743),
    (1025, 1.333345), (1050, 1.339043),
]
# (global_step, eval/loss)
EVALPTS = [
    (200, 1.732761), (400, 1.638570), (600, 1.615273),
    (800, 1.593879), (1000, 1.577564), (1066, 1.577269),
]


def fig_training_loss():
    xs = [s for s, _ in TRAIN]
    ys = [l for _, l in TRAIN]
    ex = [s for s, _ in EVALPTS]
    ey = [l for _, l in EVALPTS]
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.plot(xs, ys, color=NAIJA, lw=1.8, label="Training loss")
    ax.plot(ex, ey, color=EVAL, lw=1.8, marker="o", ms=5, label="Validation loss")
    # epoch boundary (2 epochs over 1066 steps -> epoch 1 ~ step 533)
    ax.axvline(533, color=GREY, ls="--", lw=1)
    ax.text(533, ax.get_ylim()[1], " epoch 1 / 2", color=GREY, va="top", fontsize=9)
    ax.set_xlabel("Training step")
    ax.set_ylabel("Cross-entropy loss")
    ax.set_title("NaijaReviewer-8B QLoRA fine-tuning loss", fontsize=12, color=DARK)
    ax.legend(frameon=False)
    ax.grid(axis="y", color="#eeeeee")
    fig.savefig(OUT / "fig_training_loss.pdf")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 2. Task A RMSE (lower is better) - v2 held-out split
# --------------------------------------------------------------------------- #
def fig_task_a_rmse():
    models = ["NaijaReviewer-8B", "Claude Sonnet 4"]
    rmse = [1.114, 1.319]
    colors = [NAIJA, GREY]
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    bars = ax.bar(models, rmse, color=colors, width=0.55)
    for b, v in zip(bars, rmse):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.3f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.set_ylabel("RMSE (lower is better)")
    ax.set_ylim(0, 1.5)
    ax.set_title("Task A: rating-prediction RMSE", fontsize=12, color=DARK)
    ax.annotate("-15.5%", xy=(0, 1.114), xytext=(0.0, 0.7),
                ha="center", color=NAIJA, fontweight="bold")
    ax.grid(axis="y", color="#eeeeee")
    fig.savefig(OUT / "fig_task_a_rmse.pdf")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 3. Task B NDCG@10 by re-ranker (Cohere-OFF) vs model size
# --------------------------------------------------------------------------- #
def fig_task_b_ndcg():
    # (label, params-string, ndcg)
    rows = [
        ("NaijaReviewer-8B", "8B", 0.588),
        ("GPT-OSS-120B", "120B", 0.441),
        ("Claude Sonnet 4", "n/d", 0.433),
        ("Llama-3.3-70B", "70B", 0.425),
        ("Qwen-2.5-72B", "72B", 0.404),
    ]
    labels = [r[0] for r in rows]
    params = [r[1] for r in rows]
    ndcg = [r[2] for r in rows]
    colors = [NAIJA] + [GREY] * 4
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    bars = ax.bar(range(len(rows)), ndcg, color=colors, width=0.62)
    for i, (b, v, p) in enumerate(zip(bars, ndcg, params)):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.3f}",
                ha="center", va="bottom", fontsize=10, fontweight="bold")
        ax.text(b.get_x() + b.get_width() / 2, 0.012, p,
                ha="center", va="bottom", fontsize=9, color="white")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=18, ha="right", fontsize=9)
    ax.set_ylabel("NDCG@10 (higher is better)")
    ax.set_ylim(0, 0.66)
    ax.set_title("Task B: re-ranker NDCG@10 vs model size (params on bars)",
                 fontsize=11.5, color=DARK)
    ax.grid(axis="y", color="#eeeeee")
    fig.savefig(OUT / "fig_task_b_ndcg.pdf")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 4. Task A ablation - register match and markers across conditions
# --------------------------------------------------------------------------- #
def fig_task_a_ablation():
    conds = ["A. Full", "B. -prompt", "C. -persona", "D. 70B base"]
    reg = [48.0, 6.0, 4.0, 53.1]       # register-match %
    markers = [3.22, 0.16, 0.00, 4.65]  # markers / review
    bar_colors = [NAIJA, GREY, GREY, "#5b8def"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.8, 3.2))
    b1 = ax1.bar(conds, reg, color=bar_colors, width=0.6)
    ax1.set_ylabel("Register-tier match (%)")
    ax1.set_ylim(0, 60)
    ax1.set_title("Register fidelity", fontsize=11, color=DARK)
    for b, v in zip(b1, reg):
        ax1.text(b.get_x()+b.get_width()/2, v+0.8, f"{v:.0f}", ha="center", fontsize=9)
    ax1.tick_params(axis="x", labelrotation=20, labelsize=8)
    b2 = ax2.bar(conds, markers, color=bar_colors, width=0.6)
    ax2.set_ylabel("Cultural markers / review")
    ax2.set_ylim(0, 5)
    ax2.set_title("Marker emission", fontsize=11, color=DARK)
    for b, v in zip(b2, markers):
        ax2.text(b.get_x()+b.get_width()/2, v+0.07, f"{v:.2f}", ha="center", fontsize=9)
    ax2.tick_params(axis="x", labelrotation=20, labelsize=8)
    for ax in (ax1, ax2):
        ax.grid(axis="y", color="#eeeeee")
    fig.suptitle("Removing the register-aware prompt collapses Nigerian voice",
                 fontsize=11.5, color=DARK)
    fig.savefig(OUT / "fig_task_a_ablation.pdf")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 5. Task A - LLM judges vs human raters (the cultural-prior twist)
# --------------------------------------------------------------------------- #
def fig_task_a_judge_human():
    arbiters = ["LLM judges\n(majority)", "Nigerian humans\n(pooled)"]
    winrate = [32.0, 48.5]
    fig, ax = plt.subplots(figsize=(4.6, 3.3))
    bars = ax.bar(arbiters, winrate, color=[GREY, NAIJA], width=0.55)
    ax.axhline(50, color=EVAL, ls="--", lw=1)
    ax.text(1.45, 50, "parity", color=EVAL, va="center", fontsize=9)
    for b, v in zip(bars, winrate):
        ax.text(b.get_x()+b.get_width()/2, v+0.8, f"{v:.1f}%", ha="center",
                fontweight="bold", fontsize=11)
    ax.set_ylabel("NaijaReviewer-8B win-rate vs Claude")
    ax.set_ylim(0, 60)
    ax.set_title("Who judges authenticity?", fontsize=12, color=DARK)
    ax.grid(axis="y", color="#eeeeee")
    fig.savefig(OUT / "fig_task_a_judge_human.pdf")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 6. Task B - Cohere pre-rerank ablation (NDCG@10 OFF vs ON)
# --------------------------------------------------------------------------- #
def fig_task_b_cohere():
    models = ["NaijaReviewer-8B", "Llama-3.3-70B", "Qwen-2.5-72B",
              "Claude Sonnet 4", "GPT-OSS-120B"]
    off = [0.588, 0.425, 0.404, 0.433, 0.441]
    on = [0.572, 0.477, 0.461, 0.430, 0.366]
    import numpy as np
    x = np.arange(len(models)); w = 0.38
    fig, ax = plt.subplots(figsize=(7.0, 3.5))
    ax.bar(x - w/2, off, w, label="Pre-rerank OFF", color=GREY)
    ax.bar(x + w/2, on, w, label="Pre-rerank ON", color=NAIJA)
    ax.set_xticks(x); ax.set_xticklabels(models, rotation=18, ha="right", fontsize=9)
    ax.set_ylabel("NDCG@10")
    ax.set_ylim(0, 0.66)
    ax.set_title("Stage-2.5 pre-rerank ablation: a non-uniform effect",
                 fontsize=11.5, color=DARK)
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", color="#eeeeee")
    fig.savefig(OUT / "fig_task_b_cohere.pdf")
    plt.close(fig)


# --------------------------------------------------------------------------- #
# 7. Task B - human contextual-relevance (mean relevance + win-rate)
# --------------------------------------------------------------------------- #
def fig_task_b_relevance():
    # 3-rater pooled (Christianah, Uvere_Amarachi, ashinze): n=59 decisive,
    # mean relevance NaijaReviewer 3.00 vs Claude 3.68 over 72 paired ratings.
    models = ["NaijaReviewer-8B", "Claude Sonnet 4"]
    rel = [3.00, 3.68]
    fig, ax = plt.subplots(figsize=(4.7, 3.3))
    bars = ax.bar(models, rel, color=[NAIJA, GREY], width=0.55)
    for b, v in zip(bars, rel):
        ax.text(b.get_x()+b.get_width()/2, v+0.05, f"{v:.2f}", ha="center",
                fontweight="bold", fontsize=11)
    ax.set_ylabel("Mean relevance (1-5)")
    ax.set_ylim(0, 5)
    ax.set_title("Human relevance, 3-rater panel\n"
                 "(NaijaReviewer-8B win-rate 25.4%)", fontsize=10.5, color=DARK)
    ax.grid(axis="y", color="#eeeeee")
    fig.savefig(OUT / "fig_task_b_relevance.pdf")
    plt.close(fig)


if __name__ == "__main__":
    fig_training_loss()
    fig_task_a_rmse()
    fig_task_b_ndcg()
    fig_task_a_ablation()
    fig_task_a_judge_human()
    fig_task_b_cohere()
    fig_task_b_relevance()
    print(f"wrote figures to {OUT}")
    for p in sorted(OUT.glob("*.pdf")):
        print("  ", p.name, f"{p.stat().st_size/1024:.1f} KB")
