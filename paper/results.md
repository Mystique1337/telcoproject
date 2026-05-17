# Evaluation Results — Naija Persona Agent

## Task A — User Modeling (Review Generation)

### Our metrics (rubric-aligned)

| Model | n | RMSE ↓ | BERTScore F1 ↑ | ROUGE-L ↑ | Register match ↑ | Marker recall ↑ |
|---|---|---|---|---|---|---|
| **naija_reviewer_8b** | 40 | 1.432 | 0.863 | 0.222 | 62.5% | 40.9% |
| **claude_sonnet_4** | 40 | 1.500 | 0.857 | 0.187 | 70.0% | 20.6% |

### Official AgentSociety metrics (run by the upstream simulator)

| Model | preference_estimation ↑ | sentiment_err ↓ | emotion_err ↓ | topic_err ↓ | review_generation ↑ | **overall_quality ↑** |
|---|---|---|---|---|---|---|
| **naija_reviewer_8b** | 0.760 | 0.376 | 0.249 | 0.165 | 0.761 | **0.761** |
| **claude_sonnet_4** | 0.750 | 0.288 | 0.245 | 0.174 | 0.780 | **0.765** |


## Task B — Recommendation

| Model (re-ranker) | n | NDCG@10 ↑ | HR@1 ↑ | HR@3 ↑ | HR@5 ↑ |
|---|---|---|---|---|---|
| **claude_sonnet_4** | 2 | 0.422 | 0.000 | 0.333 | 0.333 |
| **naija_reviewer_8b** | 4 | 0.801 | 0.750 | 0.750 | 0.833 |
