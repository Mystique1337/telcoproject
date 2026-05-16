# For the Hackathon Judges

Welcome, and thank you for evaluating **Naija Persona Agent (NPA)** — our submission to the Nigerian AI Agents Hackathon.

## Team

- **Ashinze** — system architect & fine-tuning lead — `ashinze@bluebulb.co.uk`
- **Franca** — product & frontend
- **[3rd teammate]** — paper & evaluation

We respond within 30 minutes during evaluation week.

## Submission package

| Required deliverable | URL / path |
|---|---|
| **1. Live agent (containerised API)** | `[deployed URL]` — populated Day 4 |
| **2. Solution paper (4–6 pages)** | `paper/paper.pdf` |
| **3. Code repository** | `https://github.com/Mystique1337/telcoproject` (MIT) |
| **Bonus — open-weight model** | `huggingface.co/<team>/naija-reviewer-8b` — populated Day 5 |

## Three curl commands to test the live agent

```bash
# 1) Health
curl https://[deployed-url]/health

# 2) Task 1 — Review simulation
curl -X POST https://[deployed-url]/simulate-review \
  -H "Content-Type: application/json" \
  -d @data/sample/requests/simulate_review_chinwe.json

# 3) Task 2 — Recommendation
curl -X POST https://[deployed-url]/recommend \
  -H "Content-Type: application/json" \
  -d @data/sample/requests/recommend_tunde.json
```

Sample request payloads live in `data/sample/requests/`.

## Local reproducibility

```bash
git clone https://github.com/Mystique1337/telcoproject
cd telcoproject
cp .env.example .env  # fill in ANTHROPIC_API_KEY and OPENAI_API_KEY
make demo
```

Expected: working API at `http://localhost:8000/docs` in under 10 minutes from clone.

## Reading order (most efficient evaluation)

1. **Abstract + Section 1 of `paper/paper.pdf`** — the headline claim and contributions (2 minutes).
2. **`README.md` Quick-start** — three curl commands you can run live (3 minutes).
3. **`PRD/PRD_v4_NPA_5Day.md` Section 4 (Architecture)** — what we built and why (5 minutes).
4. **Live demo URL** — three pre-built Nigerian personas with side-by-side compare vs vanilla GPT-4o.
5. **Paper Sections 4–5 (Method + Experiments)** — full architecture + results.
6. **`finetuning/README.md`** — how to reproduce NaijaReviewer-8B from scratch.

## What makes this submission distinctive

- A **structured cognitive persona representation** (not concatenated history) with 4 dimensions + cultural register tier.
- A **fine-tuned open-weight Llama 3.1 8B** (NaijaReviewer-8B) released alongside the system.
- **Real Nigerian data** anchors validity (Iwendi et al. 2020 + Jumia direct + Letterboxd Nollywood) with declared synthetic only where coverage is missing.
- A **paper-first deliverable** with named contributions, an ablation table, 4 baselines, and quantified Nigerian-context gap recovery.

We had 5 days, 3 people, and a single goal: ship a system that *sounds Nigerian* on review generation and *thinks Nigerian* on recommendation. We hope it does.
