# For the Hackathon Judges

Welcome, and thank you for evaluating **Naija Persona Agent (NPA)** — our submission to the Nigerian AI Agents Hackathon (May 2026).

> ⚡ TL;DR — the agent runs in **two interchangeable modes**. Pick whichever your harness supports:
> 1. **AgentSociety simulator mode** (upstream `websocietysimulator` from `AGI-FBHC/AgentsChallenge`): drop in `submission/naija_agent.py` — it subclasses `SimulationAgent` + `RecommendationAgent` and implements `workflow()` per the reference contract.
> 2. **REST API mode** (FastAPI service): `POST /simulate-review` for Track A, `POST /recommend` for Track B — see curl commands below.
>
> Both modes share the same Nigerian-context logic (register induction → register-aware prompt → NaijaReviewer-8B LLM call). Nothing is hard-coded to specific personas, products, or test sets.

## Team

- **Ashinze** — system architect & fine-tuning lead — `ashinze@bluebulb.co.uk`
- **Franca** — product & frontend
- **[3rd teammate]** — paper & evaluation

We respond within 30 minutes during evaluation week.

## Submission package

| Deliverable | Path / URL |
|---|---|
| **1. Single-file agent** (AgentSociety-compatible) | `submission/naija_agent.py` |
| **2. REST API service** (FastAPI) | `app/api/main.py` → `http://[host]:8765` |
| **3. Solution paper** | `paper/paper.tex` (compiles to `paper/paper.pdf`) |
| **4. Code repository** (MIT) | <https://github.com/Mystique1337/telcoproject> |
| **5. Open-weight model** | <https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF> |
| **6. Judge demo** (Streamlit) | `demo/streamlit_app.py` (5 personas, side-by-side compare) |
| **7. Eval harness** | `scripts/eval_all.py` (rubric metrics **and** official AgentSociety metrics) |

## Mode 1 — AgentSociety simulator (recommended if judges use the official harness)

```bash
# 1. Install the upstream simulator
git clone https://github.com/AGI-FBHC/AgentsChallenge && cd AgentsChallenge
pip install -r requirements.txt && pip install .

# 2. Drop in our agent
cp /path/to/telcoproject/submission/naija_agent.py .

# 3. Run their evaluation harness with our agent
python - <<'PY'
from websocietysimulator import Simulator
from websocietysimulator.llm import InfinigenceLLM       # or any LLMBase subclass
from naija_agent import MySimulationAgent                # ← OUR AGENT
sim = Simulator(data_dir="<your data dir>", device="auto", cache=True)
sim.set_task_and_groundtruth(task_dir="<tasks>", groundtruth_dir="<gt>")
sim.set_agent(MySimulationAgent)
sim.set_llm(InfinigenceLLM(api_key="<your key>"))         # or our local LM Studio
out = sim.run_simulation(number_of_tasks=40, enable_threading=True, max_workers=2)
print(sim.evaluate())
PY
```

Pointing `set_llm(...)` at our local NaijaReviewer-8B served by LM Studio
(`http://localhost:1234/v1`, OpenAI-compatible) is a one-line change — anything
that subclasses `LLMBase` works.

For Track B, swap `MySimulationAgent` for `MyRecommendationAgent` from the same
file. Both classes live side by side; the harness picks the right one.

### Why this is genuinely aligned

- **Same base classes**: subclasses upstream `SimulationAgent` and `RecommendationAgent` verbatim.
- **Same return shape**: `{"stars": float, "review": str}` for Track A; ranked id list for Track B.
- **Same data-access pattern**: every input comes from `self.interaction_tool.get_user/get_item/get_reviews`. No assumption about our structured persona schema.
- **Same LLM contract**: uses the harness-injected `self.llm` (any `LLMBase`).
- **Robust fallbacks**: malformed LLM output → centred default (3 stars, generic review) — the harness never crashes.

## Mode 2 — REST API (recommended if judges want a live URL)

### Local install (no Docker needed)

```bash
git clone https://github.com/Mystique1337/telcoproject
cd telcoproject
pip install -r requirements.txt
cp .env.example .env       # fill in ANTHROPIC_API_KEY and/or OPENAI_API_KEY

# Optional: serve NaijaReviewer-8B locally via LM Studio at http://localhost:1234/v1
# (the .env.example sets TASK1_BACKBONE=lmstudio:naija-reviewer-8b by default)

uvicorn app.api.main:app --host 0.0.0.0 --port 8765
```

Expected: `http://localhost:8765/docs` (Swagger UI) in ~30 seconds from clone.

### Three curl commands to test

```bash
# 1) Health
curl http://localhost:8765/health

# 2) Track A — Review simulation
curl -X POST http://localhost:8765/simulate-review \
  -H "Content-Type: application/json" \
  -d @data/sample/requests/simulate_review_chinwe.json

# 3) Track B — Recommendation
curl -X POST http://localhost:8765/recommend \
  -H "Content-Type: application/json" \
  -d @data/sample/requests/recommend_tunde.json
```

Each endpoint accepts a `backbone_override` / `reranker_override` field so judges can A/B between NaijaReviewer-8B, Claude, GPT-4o, or any other registered model on the same request — no redeploy needed.

### Streamlit demo (visual compare)

```bash
streamlit run demo/streamlit_app.py
# Tab 1: side-by-side compare (NaijaReviewer vs vanilla Claude / GPT-4o)
# Tab 2: single-model recommendation panel
```

## What we evaluate against (matches whatever judges run)

`scripts/eval_all.py` outputs **two tables** to `paper/results.json` + `paper/results.md`:

1. **Our rubric-aligned metrics**: RMSE (rating accuracy), BERTScore F1 + ROUGE-L (review text quality), register-match %, cultural-marker recall.
2. **Official AgentSociety metrics** (replicated from `websocietysimulator/tools/evaluation_tool.py`): `preference_estimation`, `sentiment_error` (VADER), `emotion_error` (cardiffnlp/twitter-roberta-base-emotion), `topic_error` (sentence-transformers cosine), `review_generation`, **`overall_quality`**.

```bash
# Reproduce the eval (assumes API is running on :8765 and LM Studio on :1234)
python scripts/eval_all.py --n 50 --n-scenarios 30
# → paper/results.json + paper/results.md
```

The eval gracefully skips heavy metrics (BERTScore, emotion classifier) if optional deps are missing — it never fails on a fresh clone.

## Reading order (most efficient evaluation)

1. **`paper/paper.tex` abstract + Section 1** — headline claim & contributions (2 min).
2. **This file** — three curl commands you can run live (3 min).
3. **`submission/naija_agent.py`** — single-file agent, drop-in for the upstream simulator (5 min).
4. **Live demo** — five Nigerian personas with side-by-side vs vanilla GPT-4o.
5. **Paper §3–§5** — method, experiments, results.
6. **`finetuning/README.md`** — how to reproduce NaijaReviewer-8B from scratch (Colab, ~3-4h on A100).

## What makes this submission distinctive

- A **fine-tuned open-weight 8B model** (`Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF`) that actually sounds Nigerian — not a wrapper around a frontier API.
- A **structured cognitive persona representation** (4 dimensions + Nigerian register tier) shared verbatim across both tracks.
- A **dual submission path**: AgentSociety-harness-compatible single file *and* a containerless FastAPI service.
- A **paper-first evaluation** that runs both our rubric metrics **and** the official AgentSociety metrics on the same test split, so judges can spot-check either way.

We had 5 days, 3 people, and a single goal: ship a system that *sounds Nigerian* on review generation and *thinks Nigerian* on recommendation. We hope it does.
