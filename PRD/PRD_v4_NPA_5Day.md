# PRODUCT REQUIREMENTS DOCUMENT
## Naija Persona Agent (NPA) — 5-Day Sprint Edition
### Containerised Nigerian-Context LLM Agent for Review Simulation & Recommendation

| | |
|---|---|
| **Project ID** | Project B v4.0 |
| **Version** | 4.0 (5-Day Sprint Edition) |
| **Date** | May 2026 |
| **Team** | 3 people — Franca, Ashinze, + 1 |
| **Submission Target** | Nigerian AI Agents Hackathon (Tasks 1 + 2 + Paper + Repo) |
| **Build Window** | 5 days |
| **Status** | Approved for build — supersedes v3.1 (8-week vision document, preserved for post-hackathon roadmap) |

> **Why v4 over v3.1.** v3.1 sized the build for 8 weeks and 4 artifacts (system + fine-tune + benchmark + arXiv). With a 5-day window and 3 people, we cut to **2 artifacts** — the agent system + the open-weight fine-tuned model — and ship a tight 4–6 page paper around them. NPA-Bench public release, arXiv preprint, human evaluation, cross-domain bridge, and the 22-feature v3.1 audit additions move to post-hackathon roadmap. The architecture's intellectual core (cultural prior thesis + persona representation + fine-tuned recovery) stays intact.

---

## Table of Contents

1. Executive Summary
2. Problem Statement (condensed)
3. Required Deliverables
4. System Architecture
5. Persona Representation (simplified for 5 days)
6. Functional Requirements
7. Technical Architecture
8. Dataset Strategy
9. Fine-Tuning Recipe — NaijaReviewer-8B
10. Evaluation Framework
11. Solution Paper Plan (4–6 pages)
12. Container & Deployment
13. Reproducibility & Submission
14. Non-Functional Requirements
15. Out of Scope (vs v3.1)
16. Risks & Mitigations
17. Business Applications (paper Section 6)
18. Comparison: NPA vs Median Submission
19. Appendix — What We Cut & Why

---

## 1. Executive Summary

The Naija Persona Agent (NPA) is a Nigerian-context LLM agent system for review/rating generation and personalised product recommendation. It is the team's 5-day submission to the Nigerian AI Agents Hackathon and ships in two coordinated artifacts:

1. **NPA system** — containerised app exposing two endpoints (`/simulate-review`, `/recommend`) plus `/health`, `/docs`, and a Streamlit demo at `/demo`. FastAPI + Docker; backed by NaijaReviewer-8B (local Ollama) for Task 1 generation; Claude Sonnet 4 (API) for persona extraction + Task 2 re-ranking; Chroma vector store + SQLite persona cache; deployable to Fly.io or Render free tier.
2. **NaijaReviewer-8B** — Llama 3.1 8B Instruct QLoRA fine-tuned on ~10–15k Nigerian-marker examples from the Iwendi et al. 2020 Jumia/Konga corpus. Open weights on HuggingFace under the Llama 3.1 Community License. Served locally via Ollama as the Task 1 backbone.

The team also produces a **4–6 page solution paper** (Overleaf, ACM-style) defending the cultural prior thesis with concrete numbers and qualitative case studies, and a **clean MIT-licensed GitHub repository** with Docker reproducibility tested on a fresh machine.

**The headline claim.** A small fine-tuned open-weight model combined with structured persona representation and register-aware prompting recovers a measurable portion of the cultural prior gap on Nigerian users — without requiring frontier-scale models. We quantify the recovery on a curated Nigerian-marker subset and release the open-weight model so the community can verify and build on it.

**The 5-day scope.** Two artifacts, one paper, one repo. No NPA-Bench public release. No arXiv preprint (optional within Week 1 post-submission). No human evaluation. No cross-domain bridge. Single domain (Jumia/Konga). Real Iwendi data anchors validity. Streamlit demo (not Next.js). Plain Python async functions (not LangGraph state graphs). Clean cuts, defensible deliverable.

---

## 2. Problem Statement (Cultural Prior, Condensed)

Frontier LLMs are pre-trained on corpora dominated by U.S./EU English. When deployed on Nigerian users they produce systematic miscalibration:

- **Rating intensity is compressed** — Nigerian reviewers use 1-star and 5-star more frequently; vanilla models smooth toward the middle, under-shooting extreme reviews by 0.3–0.7 stars on average.
- **Register is flattened** — Pidgin markers ("e shock me", "no cap"), Nigerian English forms ("the food sweet die"), and code-mixing with Yorùbá/Hausa/Igbo are smoothed into standard English. Grammatically correct, culturally hollow.
- **Framing is individualised** — communal "we enjoyed" / "my family loved" replaced by individualist "I" framing.
- **Religious markers misread** — "by God's grace", "Alhamdulillah" misclassified as neutral or off-topic.
- **Aspect priorities are wrong** — party-jollof texture, Nollywood production-value cues, Afrobeats sub-genre awareness absent from the vanilla prior.

These are not cosmetic. They have structural consequences for any downstream Nigerian deployment (recommendation, churn intervention, credit scoring, marketplace personalisation). We make the cultural prior visible, recover it on the Task 1 + Task 2 pair, and ship the recovery as an open-weight model.

**Quantified backdrop (anchors the Business Applications section of the paper):** 171.6M Nigerian telecom subscribers, $3.60 MTN ARPU, 25–35% annual churn; 64% adult financial inclusion (EFInA 2023); ₦130T MSME credit gap (CBN April 2026); ~17M Nigerian diaspora globally.

---

## 3. Required Deliverables (per hackathon brief)

| # | Brief requirement | What we ship |
|---|---|---|
| 1 | Containerised app for review + rating generation | `/simulate-review` endpoint inside Docker container; takes `{persona, product}` JSON, returns `{rating, review, register_tier, rationale}` |
| 2 | Containerised app for personalised recommendation | `/recommend` endpoint inside the same Docker container; takes `{persona, candidate_set?, k}`, returns ranked list with per-item rationale |
| 3 | Solution paper (4–8 pages) | 4–6 page Overleaf-built PDF in ACM template; 4 named contributions; 1-row ablation; 4 baselines |
| 4 | Code repository | MIT-licensed GitHub repo with Dockerfile, README, JUDGES.md, < 10-minute fresh-clone reproducibility |
| **Bonus** | Open-weight artifact | NaijaReviewer-8B on HuggingFace under Llama 3.1 Community License |

---

## 4. System Architecture

### 4.1 Two-task architecture

```
                   ┌────────────────────────────────────┐
                   │     SHARED PERSONA REPRESENTATION  │
                   │  (4 cognitive dims + register tier │
                   │   + aspect priorities + anchors)   │
                   └────────────────┬─────────┬─────────┘
                                    │         │
                                    ▼         ▼
                ┌─────────────────────┐  ┌──────────────────────┐
                │   TASK 1 AGENT      │  │  TASK 2 AGENT        │
                │   /simulate-review  │  │  /recommend          │
                │                     │  │                      │
                │  Backbone:          │  │  Pipeline:           │
                │   NaijaReviewer-8B  │  │   semantic retrieval │
                │   (local Ollama)    │  │   + MMR diversity    │
                │                     │  │   + Claude re-rank   │
                │  Fallback:          │  │                      │
                │   Claude Sonnet 4   │  │  Backbone:           │
                │                     │  │   Claude Sonnet 4    │
                │  Input:             │  │                      │
                │   • persona         │  │  Input:              │
                │   • product detail  │  │   • persona          │
                │                     │  │   • candidates       │
                │  Output:            │  │                      │
                │   • rating (1-5)    │  │  Output:             │
                │   • review text     │  │   • ranked top-K     │
                │   • register tier   │  │   • rationale/item   │
                │   • rationale       │  │                      │
                └─────────────────────┘  └──────────────────────┘
                              │                 │
                              └─────────┬───────┘
                                        ▼
                       ┌──────────────────────────┐
                       │   CHROMA + SQLITE STORE  │
                       │  (product index +        │
                       │   persona cache)         │
                       └──────────────────────────┘
```

Both endpoints share the persona representation, the vector store, and the LLM clients. **Task 1 generation is NaijaReviewer-8B** (your fine-tune, served locally via Ollama). **Task 2 re-ranking is Claude Sonnet 4** (API; reasoning quality matters more than register for ranking).

### 4.2 Why this shape (5-day rationale)

- **One container, two routes**: cleaner deploy, same Docker compose, judges see one URL.
- **Plain Python async functions, no LangGraph**: state graphs are overkill for linear pipelines this size; we save ~1 person-day.
- **Single domain (Jumia/Konga)**: Iwendi et al. data is already cleaned and labelled. Adding Nollywood as a separate domain adds scrape time + persona migration we don't have.
- **No trained register classifier**: Claude detects register natively from the persona's `register_markers` field; we prompt-condition rather than train a separate classifier (saves ~1 person-day).
- **Streamlit demo over Next.js**: 1 day to ship vs 3+; same demonstrative power on a 5-day budget.

---

## 5. Persona Representation (Simplified)

```python
@dataclass
class Persona:
    user_id: str | None
    demographics: dict | None       # age range, location, gender — never PII

    # Cognitive dimensions (4 — trimmed from v3.1's 6 for speed)
    hedonic_utilitarian: float      # 0.0 utilitarian → 1.0 hedonic
    intensity_calibration: dict     # {"amazing": 4.7, "okay": 3.1, ...}
    communal_individual: float      # 0.0 individualist → 1.0 communal
    aspect_priority: dict[str, float]

    # Cultural register
    register_tier: Literal[
        "standard_english",
        "nigerian_english",
        "nigerian_pidgin",
        "code_mixed",
    ]
    register_markers: list[str]

    # History anchors for retrieval
    review_anchors: list[ReviewAnchor]

    # Provenance
    extraction_source: Literal["history", "elicitation", "synthetic"]
    extraction_timestamp: datetime
```

**v4 cuts from v3.1:** age cohort, religious framing tier, dimension confidence, code-switch intensity dial, punctuation profile, diaspora flag. These were valuable v3.1 features that exceed the 5-day cost-benefit.

**Persona extraction** uses Claude Sonnet 4 with a structured prompt (one-shot offline pass over Iwendi users → cached to SQLite). For cold-start in the demo, a 3-question elicitation flow seeds the persona.

---

## 6. Functional Requirements

### 6.1 Persona

- **FR-P1**. Extract persona from a user's review history (≥3 reviews) via Claude Sonnet 4 structured-output pipeline; cache to SQLite (~30-day TTL).
- **FR-P2**. Cold-start: 3-question elicitation flow at `/elicit` returning a seeded persona.
- **FR-P3**. Schema versioned (`schema_version: "1.0"`); JSON-schema validator at the API boundary.

### 6.2 Task 1 — Review & Rating

- **FR-T1.1**. `POST /simulate-review` accepts `{persona, product}`; returns `{rating, review, register_tier, rationale}`.
- **FR-T1.2**. Rating predicted by a separate Stage-A regressor (XGBoost) before text generation — Renmin-team insight, never joint.
- **FR-T1.3**. Text generation via NaijaReviewer-8B (local Ollama); Claude Sonnet 4 fallback if Ollama unreachable.
- **FR-T1.4**. Self-consistency style check: embedding similarity (generated vs. persona's review corpus); single regen if below τ.
- **FR-T1.5**. Every response carries a `rationale` string identifying which 2 persona dimensions + 1 register marker drove the output.
- **FR-T1.6**. OpenAPI / Swagger published at `/docs`.

### 6.3 Task 2 — Recommendation

- **FR-T2.1**. `POST /recommend` accepts `{persona, candidate_set?, k}` (default `k=5`); returns `{recommendations: [{product_id, score, rationale}, ...]}`.
- **FR-T2.2**. If `candidate_set` omitted: semantic retrieval via Chroma over the product index (top-30 retrieved).
- **FR-T2.3**. Pre-ranking with external knowledge injection — combine item quality, popularity, register-tier match — before LLM re-rank.
- **FR-T2.4**. Claude Sonnet 4 re-ranks top-30 → top-K with per-item rationale.
- **FR-T2.5**. **MMR diversity re-rank** (λ=0.7) on top of LLM scores; prevents top-K all-same-category.
- **FR-T2.6**. Cold-start branch activates when `persona.history_count < 3`.

### 6.4 Container & misc

- **FR-C1**. Healthcheck `GET /health` returns `200`.
- **FR-C2**. Streamlit demo at `/demo` with 3–4 Nigerian persona archetypes + side-by-side compare vs vanilla Claude.
- **FR-C3**. Pydantic schemas → OpenAPI JSON; Swagger UI at `/docs`.

---

## 7. Technical Architecture

| Layer | Choice | Notes |
|---|---|---|
| API | FastAPI + uvicorn | Standard |
| LLM (Task 1 gen) | NaijaReviewer-8B via Ollama | Local, your fine-tune |
| LLM (persona extraction, Task 2 re-rank, fallback) | Claude Sonnet 4 (Anthropic API) | $30–50 expected total spend |
| Baseline comparators | GPT-4o, Claude Sonnet 4 zero-shot, base Llama 3.1 8B | For paper Table 1 |
| Persona store | SQLite (file-backed) | Lightest possible |
| Vector store | Chroma (embedded) | No separate service |
| Embeddings | `text-embedding-3-small` (OpenAI) | Cheap + reasonable |
| Rating regressor | XGBoost | Standard tabular ML |
| Orchestration | Plain Python `async def` functions | No LangGraph |
| Demo UI | Streamlit | 1 day to ship |
| Container | Single Dockerfile + docker-compose | App + Ollama + Chroma in compose |
| Deploy | Fly.io free tier (or Render) | Public URL for judges |
| Experiment tracking | Weights & Biases (free hosted) | Required for paper rigor |
| Paper | Overleaf — ACM proceedings template | Standard |
| Repo | GitHub, MIT, branch-protected `main` | PR-based workflow |

---

## 8. Dataset Strategy

### 8.1 Primary corpus

**Iwendi et al. 2020** — 30,382 cleaned Nigerian e-commerce reviews across Jumia / Jiji / Konga / Takealot. Already academic-grade clean. Cited as the primary anchor.

Schema after our normalisation:
- `review_id`, `user_pseudonym` (hashed), `product_id`, `product_title`, `category`, `rating`, `review_text`, `timestamp`.

### 8.2 Nigerian-marker subset

Tag ~5–8k reviews as "high-confidence Nigerian-marker" using:
- Claude-based register classification (no separate trained classifier in v4)
- Marker lexicon match (from SentiLeye Pidgin lexicon)
- Combined confidence ≥ 0.8

This is the headline cultural-gap evaluation subset.

### 8.3 Fine-tuning corpus

Built specifically for NaijaReviewer-8B QLoRA training. **Target ~10–15k examples** (smaller than v3.1's 35k for time):

- ~80% from Iwendi Nigerian-marker reviews
- ~20% register-balanced synthetic generated by Claude Sonnet 4 (declared `synthetic: True`)
- Format: instruction-tuning `{persona_json, product_json, register_tier} → {rating, review_text}`
- Split: 90 / 5 / 5 (train / val / test)
- Test split: never seen during training; the source of the paper's headline numbers

Released alongside NaijaReviewer-8B on HuggingFace Datasets (small companion dataset, not the full NPA-Bench v3.1 dream).

### 8.4 Synthetic data policy

Per the brief — "Where there's no data at all, we use synthetic." Synthetic is used only for:

1. Register-tier balance in the fine-tune corpus (Pidgin under-represented in raw data).
2. Cold-start persona elicitation seeds.

All synthetic tagged. Eval splits exclude synthetic by default.

### 8.5 What we cut (vs v3.1)

- Nollywood corpus (no scrape time; Jumia/Konga is sufficient for one paper)
- Cross-domain user pairs
- Full 35k fine-tune corpus (shrunk to 10–15k)
- NPA-Bench public release (kept private as internal eval)

---

## 9. Fine-Tuning Recipe — NaijaReviewer-8B

### 9.1 Base & method

| | |
|---|---|
| Base model | **Llama 3.1 8B Instruct** (Community License; Ollama-native) |
| Method | **QLoRA** (4-bit NF4 via bitsandbytes) |
| LoRA config | `r=16, α=32, dropout=0.1`, target attention (q,k,v,o) + MLP (gate, up, down) |
| Trainable params | ~80M (~1% of base) |
| Max seq length | 4,096 tokens |
| Precision | bfloat16 |

### 9.2 Training data format

```json
{
  "instruction": "Simulate the review behaviour of the following Nigerian user reviewing the described product. Generate the rating (1-5) and review text exactly as this user would write it. Match the user's register tier and cultural framing.",
  "input": {
    "persona": { ... full Persona JSON ... },
    "product": { ... product details ... },
    "register_tier": "nigerian_pidgin"
  },
  "output": {
    "rating": 4,
    "review": "Abeg, this phone good die. Battery dey last for 2 days straight..."
  }
}
```

### 9.3 Hyperparameters

| | |
|---|---|
| Optimiser | AdamW 8-bit |
| Learning rate | 2e-4, cosine schedule, 100 warmup steps |
| Batch size | 4 per device, gradient accumulation 8 → effective 32 |
| Epochs | 2 (early-stop on val loss) |
| Random seed | 42 (set everywhere) |

### 9.4 Compute & time

- Your GPU (8B QLoRA fits comfortably on A100 40GB / 80GB).
- Single training run target: **6–10 hours**.
- Plan: kick off Day 2 evening, complete Day 3 morning, integrate Day 3 afternoon.

### 9.5 Release

- HuggingFace repo: `<team>/naija-reviewer-8b`
- Model card with intended use, training recipe, eval table, bias acknowledgments, carbon estimate, citation block.
- GGUF Q4_K_M variant for Ollama compatibility.

---

## 10. Evaluation Framework

### 10.1 Task 1 metrics

| Metric | Target |
|---|---|
| **RMSE (rating)** | < 0.75 on Nigerian-marker subset |
| **BERTScore F1** | ≥ 0.80 |
| **Register-tier match** | ≥ 80% on Nigerian-marker subset |
| **Cultural-marker recall** | ≥ 55% on Pidgin/code-mixed subset |

### 10.2 Task 2 metrics

| Metric | Target |
|---|---|
| **HR@5** | ≥ 0.65 on internal eval |
| **NDCG@5** | ≥ 0.55 |

### 10.3 Baselines (4)

1. **Vanilla Claude Sonnet 4** zero-shot + concat history (the median submission)
2. **Vanilla GPT-4o** zero-shot + concat history
3. **Base Llama 3.1 8B Instruct** (no fine-tune) — isolates the fine-tune's contribution
4. **NaijaReviewer-8B + concat history** (no persona structure) — isolates the persona representation

### 10.4 Ablations (1 row + headline)

| Configuration | RMSE ↓ | RGM ↑ | HR@5 ↑ |
|---|---|---|---|
| **Full NPA + NaijaReviewer-8B** | | | |
| − No persona structure (concat history only) | | | |
| − No register conditioning | | | |
| **Headline: Vanilla Claude Sonnet 4** | | | |

3 rows + the headline. Run with 3 seeds.

### 10.5 Cultural-gap recovery experiment (paper headline)

1. Vanilla Claude Sonnet 4 on Nigerian-marker subset → record errors.
2. NPA full + NaijaReviewer-8B → record errors.
3. **Gap recovery = baseline error − NPA error**.

Targets: ≥ 15% RMSE reduction; ≥ 25 percentage points register-tier match lift.

### 10.6 Qualitative case studies

Two Nigerian personas walked through end-to-end in the paper's appendix — full persona JSON, retrieved anchors, generated output, comparison to vanilla Claude, commentary on what each component contributed.

---

## 11. Solution Paper Plan (4–6 pages)

### 11.1 Target

- **Length**: 4–6 pages, ACM proceedings template.
- **Title (working)**: "The Cultural Prior in LLM Agents: A Five-Day Open-Source Recovery for Nigerian User Modelling and Recommendation."
- **Authors**: Franca, Ashinze, + 3rd teammate.

### 11.2 Section structure

1. **Abstract** (~150 words) — cultural prior + 2 contributions (NPA system + NaijaReviewer-8B) + headline number.
2. **Introduction** (½ page) — motivate cultural prior; preview contributions.
3. **Related Work** (½ page, 4 paragraphs) — LLM user simulation; AgentSociety winners (USHB, Tsinghua AKF); Nigerian NLP (AfriSenti, NaijaSenti, SentiLeye, Lin 2024); existing Nigerian/African AI work (Masakhane, AfriBERTa, LELAPA AI).
4. **Method** (1 page) —
   - 4.1 Cognitive persona decomposition (formal definitions).
   - 4.2 Register-aware prompting + few-shot conditioning.
   - 4.3 NaijaReviewer-8B fine-tuning recipe.
   - 4.4 Task 2 retrieval + Claude re-rank + MMR diversity.
5. **Experiments** (1½ pages) — dataset (Iwendi Nigerian-marker subset); baselines (4); main results table; 1-row ablation; cultural-gap recovery table; 2 qualitative case studies.
6. **Discussion & Business Implications** (½ page) — Nigerian deployments (telco churn intervention, MSME credit scoring, marketplace personalisation) with quantified backdrop.
7. **Limitations** (¼ page) — cite "Lost in Simulation"; 5-day scope; single-domain focus; small eval set; no human evaluation.
8. **Conclusion** (¼ page) — one paragraph.

### 11.3 Required tables and figures

| # | Type | Content |
|---|---|---|
| Table 1 | Dataset composition | Iwendi total, Nigerian-marker subset, fine-tune split |
| Table 2 | Main results | NPA + NaijaReviewer-8B vs 4 baselines on Task 1 + Task 2 |
| Table 3 | Ablation + cultural gap | 3 rows showing component contributions + recovery |
| Figure 1 | Architecture | Section 4.1 schematic, polished |
| Figure 2 | Persona schema | annotated example |
| Figure 3 | Qualitative compare | 2 side-by-side (vanilla vs NaijaReviewer-8B) showing Nigerian markers |

### 11.4 Headline claim (single sentence, repeat across abstract / intro / conclusion)

> *We define the cultural register as a missing architectural primitive for LLM agents and show that a small QLoRA fine-tune (NaijaReviewer-8B, 8B parameters) combined with a four-dimension cognitive persona representation reduces rating-prediction RMSE by XX% and improves register-tier fidelity by YY percentage points against vanilla Claude Sonnet 4 on the Iwendi Nigerian-marker subset. All code, model weights, and fine-tuning corpus released under open licenses.*

*(Placeholders. Replace with Day-5 numbers.)*

---

## 12. Container & Deployment

### 12.1 Stack

- **Dockerfile** (multi-stage): `python:3.11-slim` base → poetry install → app code → models pre-pulled.
- **docker-compose.yml**: `app` + `ollama` (with `naija-reviewer-8b` GGUF mounted) + `chroma` (volume-mounted).
- **`make demo`**: brings everything up, seeds sample data, runs a smoke curl.
- **Image size**: target < 1.5 GB compressed (excl. Ollama model weights).

### 12.2 Endpoints

```
POST   /simulate-review          Task 1 (judged)
POST   /recommend                Task 2 (judged)
POST   /elicit                   cold-start elicitation
POST   /feedback                 outcome logging (optional)
GET    /health                   liveness/readiness
GET    /docs                     Swagger UI
GET    /demo                     Streamlit demo (3-4 personas, compare panel)
```

### 12.3 Deployment

- **Public URL** on Fly.io free tier (or Render): `https://npa.fly.dev` or similar.
- Single container, Ollama bundled in compose.
- Healthcheck at `/health` for orchestrator liveness probe.
- Hackathon judges hit the URL directly; no auth required.

---

## 13. Reproducibility & Submission

### 13.1 Repository structure

```
naija-persona-agent/
├── README.md
├── JUDGES.md
├── LICENSE                    (MIT)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── poetry.lock
├── Makefile
├── .env.example
├── app/
│   ├── api/main.py             FastAPI app
│   ├── api/routers/            simulate_review.py, recommend.py, elicit.py
│   ├── api/schemas/            Pydantic models
│   ├── agents/                 persona_extractor.py, review_agent.py, recommend_agent.py
│   ├── llm/client.py           Ollama + Claude + OpenAI abstraction
│   ├── rag/                    vector_store.py, retriever.py
│   ├── data/                   loaders.py, personas.py
│   └── prompts/                jumia_v1.jinja, recommend_v1.jinja
├── data/
│   ├── README.md
│   ├── jumia_reviews/          Iwendi + normalised
│   ├── personas/               extracted, cached
│   ├── sample/                 bundled in container
│   └── finetune/               training corpus
├── finetuning/
│   ├── train_naija_reviewer.py
│   ├── configs/naija_reviewer_qlora.yaml
│   └── eval_naija_reviewer.py
├── notebooks/
│   ├── 01_dataset_prep.ipynb
│   ├── 02_persona_extraction.ipynb
│   ├── 03_finetune_kickoff.ipynb     Colab-ready
│   ├── 04_eval_task1.ipynb
│   ├── 05_eval_task2.ipynb
│   └── 06_qualitative_cases.ipynb
├── demo/streamlit_app.py
├── paper/paper.tex paper.pdf figures/ references.bib
├── scripts/
│   ├── build_dataset.sh
│   ├── train_all.sh
│   ├── eval_all.sh
│   └── make_demo.sh
└── tests/
```

### 13.2 README

- One-paragraph what-this-is + screenshot of demo.
- Quick-start: `cp .env.example .env` → fill 3 keys (Anthropic, OpenAI, optional HF) → `make demo` → curl example.
- Architecture diagram (paper Figure 1).
- Every env var documented.
- Curl examples for both endpoints with realistic Nigerian persona JSON.
- Reproduction note: seeds, model versions, data revision, GPU requirements (for re-running the fine-tune).
- Links: deployed demo URL, paper PDF, HuggingFace model.
- Citation block.

### 13.3 JUDGES.md

- Team intro.
- 30-minute response SLA during evaluation week.
- Direct contact (email + Slack/Discord).
- Three tested curl commands judges can paste directly.

### 13.4 Reproducibility test (Day 4 gate)

- Fresh-clone on a fresh machine by someone outside the daily codebase.
- Clone → `make demo` → first successful API call must complete in **< 10 minutes**.
- Anything that breaks triggers a README update before submission.

### 13.5 Submission package

| Submission | Form |
|---|---|
| Link to agent built | `https://npa.fly.dev` + Docker image on GHCR |
| Solution paper | `paper/paper.pdf` |
| Code repository | `github.com/<team>/naija-persona-agent` (MIT) |
| **Bonus**: model | `huggingface.co/<team>/naija-reviewer-8b` |

---

## 14. Non-Functional Requirements

| Requirement | Spec |
|---|---|
| Latency | p95 < 3 s per request; cold start < 30 s |
| Throughput | ≥ 5 concurrent requests on free-tier container |
| Privacy | No PII beyond hashed pseudonyms |
| Explainability | Every response carries `rationale` |
| Reliability | Claude fallback if Ollama unavailable; static initial corpus if Chroma down |
| Cost ceiling | < $50 total API spend (Anthropic + OpenAI combined) |
| Security | Env-var secrets; no auth required for hackathon container |
| Logging | Structured JSON; one log line per agent step |

---

## 15. Out of Scope (vs v3.1)

Cut for the 5-day window — flagged in paper as "future work" or carried in the v3.1 vision document for post-hackathon roadmap:

- **NPA-Bench public release** — internal eval set kept; HF Datasets release deferred.
- **arXiv preprint** — submit within 1 week post-hackathon if time permits.
- **Human evaluation study** — recruitment requires 5+ days; cut entirely.
- **Cross-domain bridge** — single-domain (Jumia/Konga) only.
- **Nollywood corpus** — paper acknowledges single-domain limitation.
- **Trained register classifier** — Claude detects register at request time; no separate XLM-R training.
- **v3.1's 22 feature additions** — most cut; we keep MMR diversity + self-consistency + rationale field.
- **Polished Next.js demo** — Streamlit instead.
- **LangGraph orchestration** — plain Python async functions.
- **NocoDB + n8n + Postgres + Qdrant** — SQLite + Chroma in-process.
- **Bias audit / robustness probes / LLM-as-judge / calibration plots / pre-registration** — paper mentions in Limitations only.
- **Interactive persona builder** — Streamlit demo uses 3–4 pre-built archetypes.
- **Educational Colab notebook** — flag for post-hackathon community work.

The v3.1 vision document at `/PRD/PRD_v3_Naija_Persona_Agent_AllOut.md` remains the post-hackathon roadmap.

---

## 16. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **Fine-tune doesn't beat Claude baseline** | Medium | High | Paper backup framing: "narrow the gap from X to Y, demonstrate the recovery method"; the architecture + persona + register claim stands independently of the headline beat |
| **GPU access intermittent** | Low | High | Train v0.1 Day 2 evening on a single overnight run; do not iterate unless time allows |
| **Container fails fresh-clone** | Medium | Critical | Day 4 fresh-clone reproducibility test (non-negotiable); CI builds container on every commit |
| **API budget overrun** | Medium | Low | Cache aggressively; use base Llama 3.1 8B (free local) for ablation inner loops; reserve Claude for headline runs |
| **Day-5 last-mile bugs** | High | Medium | Day 4 is integration day; Day 5 is polish + submit only; no new features on Day 5 |
| **Eval set too small** | Medium | Medium | Be honest in paper Limitations; small N is disclosed; future-work flag for larger eval |
| **Team capacity uneven** | Medium | High | Day 1 sync confirms role split + skill match; rebalance Day 2 if needed |
| **Paper not finished** | High | Critical | Start drafting Day 1 (outline + abstract); first complete draft Day 4; Day 5 is polish only |
| **3rd teammate ramp-up time** | Medium | Medium | Pair on Day 1 with whoever knows the project best; clear scoped task by Day 2 |

---

## 17. Business Applications (Paper Section 6, ½ page)

Short half-page in the paper grounding the persona work in concrete Nigerian deployments. Each is *what we could build with this representation*, not what we build in 5 days.

1. **Telco churn intervention recommender** — persona feeds an intervention ranker; 25–35% churn × $3.60 ARPU at MTN/Airtel/Glo scale. (The v1 PRD work, preserved.)
2. **Thin-file MSME credit scoring** — cognitive dimensions + register signals as behavioural features; ₦130T credit gap.
3. **Cross-cultural marketplace personalisation** — Nigerian diaspora ~17M; mis-served by U.S.-trained recommenders.
4. **Behavioural cohort modelling for fintechs** — Opay, Palmpay, Moniepoint, Kuda.

Half a page in the paper, three sentences each. No demo endpoint in the 5-day container (cut to save time).

---

## 18. Comparison: NPA vs Median Submission

| Dimension | Median | NPA v4 |
|---|---|---|
| Persona representation | Concatenated history in prompt | Structured 4-dim cognitive + register tier + aspect priorities |
| LLM backbone | Frontier closed API only | Fine-tuned open-weight Llama 3.1 8B + Claude where it matters |
| Cultural register | None | Register-aware prompting with marker conditioning |
| Dataset | Yelp / Amazon / Goodreads | Iwendi Nigerian-marker subset |
| Two-stage rating | Single-prompt joint | Stage-A regressor → Stage-B text gen |
| Self-consistency | None | One regen on style-check fail |
| MMR diversity (Task 2) | None | λ=0.7 re-rank |
| Baselines | 0–1 | 4 (Vanilla Claude, Vanilla GPT-4o, base Llama 3.1 8B, NaijaReviewer-no-persona) |
| Ablations | 0 | 3-row + headline |
| Open weights | None | NaijaReviewer-8B on HuggingFace |
| Business framing | Generic | 4 Nigerian deployments with quantified backdrop |
| Reproducibility | Often broken | Day 4 fresh-clone test |
| Paper | Last-minute | Drafted Day 1; polished Day 4–5 |

---

## 19. Appendix — What We Cut & Why

The v3.1 PRD was sized for 8 weeks + 2 people (5,000 person-hours) and 4 artifacts. v4 sizes for 5 days + 3 people (~120 person-hours). Direct cuts:

| Cut | v3.1 had | v4 reason |
|---|---|---|
| NPA-Bench public release | 1,000 personas + 5,000 + 1,000 triples on HF Datasets | Curation + QA = 2 days; private eval set sufficient |
| arXiv preprint | Co-submitted within 7 days | Post-hackathon if time allows |
| Human evaluation | 30–50 raters, 600+ judgments, ₦5k honorarium each | Recruitment = 5+ days |
| Cross-domain bridge | Jumia → Nollywood transfer experiment | Adds 2 days of scrape + alignment |
| Nollywood corpus | ~10k reviews | Single-domain focus for clarity |
| Trained register classifier | XLM-R fine-tune, calibrated | Claude does it natively at request time |
| 22 v3.1 feature additions | Persona uncertainty, age cohort, religion, code-switch dial, diaspora flag, punctuation profile, MMR, serendipity, negative recs, time-aware, long-tail, streaming, batch, reasoning trace toggle, LLM-as-judge, statistical tests, calibration plots, robustness probes, bias audit, pre-registration, failure analysis, case studies, carbon footprint, African AI compare, interactive persona builder, reasoning trace viewer, educational Colab | Most cut; keep MMR diversity + self-consistency + rationale field + 2 case studies |
| Polished Next.js demo | 5 archetypes + side-by-side + reasoning trace viewer + persona builder | Streamlit demo with 3-4 archetypes + compare panel |
| LangGraph | Stateful workflows with checkpointer | Plain Python async functions |
| Heavy infra (NocoDB + n8n + Postgres + Qdrant) | Production-shaped stack | SQLite + Chroma in-process |

What is preserved from v3.1 in v4:
- Cultural prior thesis + headline claim shape
- Persona representation (simplified to 4 dims + register tier)
- NaijaReviewer-8B QLoRA fine-tune
- Open-source commitment (MIT code, Llama Community License model)
- Container with two endpoints
- Solution paper with named contributions, ablations, baselines, qualitative cases
- Reproducibility discipline (fresh-clone gate)
- Business Applications half-page

---

*This document is the operational PRD for the 5-day build. The v3.1 PRD (`PRD_v3_Naija_Persona_Agent_AllOut.md`) is preserved as the post-hackathon vision document. Detailed day-by-day execution is in `BUILD_PLAN_5DAY.md`.*
