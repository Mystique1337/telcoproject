# LLM-as-Judge: NaijaReviewer-8B vs Claude Sonnet 4

_Same 50 blind A/B pairs used for human evaluation. Each judge votes on each pair TWICE (sides swapped) for position-bias control._

- **Pairs evaluated**: 50
- **Judges**: gpt5_5, claude, llama_70b
- **Inter-judge Fleiss κ** (nominal): **0.317**

## Per-judge breakdown

| Judge | NaijaReviewer wins | Claude wins | Ties | Decisive | NaijaReviewer win-rate | 95% CI |
|---|---|---|---|---|---|---|
| gpt5_5 | 23 | 77 | 0 | 100 | **23.0%** | [15.8%, 32.2%] |
| claude | 30 | 70 | 0 | 100 | **30.0%** | [21.9%, 39.6%] |
| llama_70b | 45 | 55 | 0 | 100 | **45.0%** | [35.6%, 54.8%] |

## Majority vote across all judges (per pair × orientation)

- NaijaReviewer wins: **32**
- Claude wins:        **68**
- Ties / no majority: **0**
- NaijaReviewer **win-rate 32.0% (95% CI [23.7%, 41.7%])**

## Interpretation

Following Zheng et al. 2023 (MT-Bench / LLM-as-Judge methodology), we run each pair twice with sides swapped to control for position bias, and aggregate across multiple independent judges to control for any single judge's idiosyncrasies. The Fleiss κ above measures inter-judge agreement (>0.4 = moderate agreement; >0.6 = substantial; >0.8 = near-perfect).

**This methodology supplements but does not replace human evaluation. Human rater XLSX template at `paper/human_eval_template.xlsx` is still the ground-truth measurement; LLM-judge is reported as a high-throughput screening pass for behavioural fidelity.**