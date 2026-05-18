# Evaluation Results — Naija Persona Agent

## Task A — User Modeling (Review Generation)

### Our metrics (rubric-aligned)

| Model | n | RMSE ↓ | BERTScore F1 ↑ | ROUGE-L ↑ | Register match ↑ | Marker recall ↑ |
|---|---|---|---|---|---|---|
| **naija_reviewer_8b** | 100 | 1.114 | 0.858 | 0.205 | 53.0% | 13.0% |
| **claude_sonnet_4** | 100 | 1.319 | 0.857 | 0.192 | 35.0% | 7.1% |

### Official AgentSociety metrics (run by the upstream simulator)

| Model | preference_estimation ↑ | sentiment_err ↓ | emotion_err ↓ | topic_err ↓ | review_generation ↑ | **overall_quality ↑** |
|---|---|---|---|---|---|---|
| **naija_reviewer_8b** | 0.792 | 0.285 | 0.253 | 0.167 | 0.782 | **0.787** |
| **claude_sonnet_4** | 0.784 | 0.228 | 0.213 | 0.169 | 0.805 | **0.795** |


## Task B — Recommendation

| Model (re-ranker) | n | NDCG@10 ↑ | HR@1 ↑ | HR@3 ↑ | HR@5 ↑ |
|---|---|---|---|---|---|
| **claude_sonnet_4** | 17 | 0.485 | 0.353 | 0.333 | 0.431 |
| **naija_reviewer_8b** | 17 | 0.623 | 0.588 | 0.588 | 0.647 |
