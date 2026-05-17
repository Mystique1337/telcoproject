# Evaluation Results — Naija Persona Agent

## Task A — User Modeling (Review Generation)

### Our metrics (rubric-aligned)

| Model | n | RMSE ↓ | BERTScore F1 ↑ | ROUGE-L ↑ | Register match ↑ | Marker recall ↑ |
|---|---|---|---|---|---|---|
| **naija_reviewer_8b** | 40 | 1.449 | 0.862 | 0.219 | 70.0% | 35.8% |
| **claude_sonnet_4** | 40 | 1.549 | 0.856 | 0.183 | 70.0% | 21.5% |

### Official AgentSociety metrics (run by the upstream simulator)

| Model | preference_estimation ↑ | sentiment_err ↓ | emotion_err ↓ | topic_err ↓ | review_generation ↑ | **overall_quality ↑** |
|---|---|---|---|---|---|---|
| **naija_reviewer_8b** | 0.750 | 0.357 | 0.265 | 0.155 | 0.767 | **0.758** |
| **claude_sonnet_4** | 0.750 | 0.276 | 0.240 | 0.182 | 0.780 | **0.765** |


## Task B — Recommendation

| Model (re-ranker) | n | NDCG@10 ↑ | HR@1 ↑ | HR@3 ↑ | HR@5 ↑ |
|---|---|---|---|---|---|
| **claude_sonnet_4** | 4 | 0.000 | 0.000 | 0.000 | 0.000 |
| **naija_reviewer_8b** | 4 | 0.000 | 0.000 | 0.000 | 0.000 |
