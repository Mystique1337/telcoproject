# PRODUCT REQUIREMENTS DOCUMENT
## Naija Persona Agent (NPA)
### A Culturally-Grounded LLM Agent System for Nigerian Review Simulation & Personalized Recommendation

| | |
|---|---|
| **Project ID** | Project B v2.0 |
| **Document Version** | 2.0 |
| **Date** | May 2026 |
| **Team** | Franca & Ashinze |
| **Submission Target** | Nigerian AI Agents Hackathon — Tasks 1 + 2 + Solution Paper + Code Repository |
| **Primary Domains** | Jumia/Konga e-commerce (primary), Nollywood streaming/cinema (secondary) |
| **Status** | Approved for build — supersedes v1.0 (Churn Intervention) |

> **Why v2.0?** v1.0 framed the system as a churn-prediction + intervention-ranking product. The hackathon brief explicitly requires (a) an agent that takes user persona + product details and emits a review + rating, and (b) an agent that takes a user persona and emits personalised recommendations. v2.0 realigns to that brief while preserving every piece of v1.0 that survives: the Nigerian context grounding, the LangGraph + dynamic RAG + Claude + NocoDB stack, the feedback loop, and the team's commercial framing. The churn intervention product moves from headline deliverable to a high-value business application demonstrated in **Section 15** and written up in the paper.

---

## Table of Contents

1. Executive Summary
2. Problem Statement
3. Goals & Success Metrics
4. Target Users & Stakeholders
5. User Stories
6. System Architecture
7. Functional Requirements
8. Technical Architecture
9. Dataset Strategy
10. Evaluation Framework
11. Solution Paper Plan
12. Reproducibility & Submission Plan
13. Non-Functional Requirements
14. Milestones & Timeline
15. Business Applications (Paper Section 7)
16. Risks & Mitigations
17. Out of Scope
18. Comparison: This System vs. Median Hackathon Submissions
19. Document Approval

---

## 1. Executive Summary

The Naija Persona Agent (NPA) is a two-task LLM-agent system that simulates Nigerian consumer review behaviour and produces culturally-grounded personalised recommendations. It is the team's submission to the Nigerian AI Agents Hackathon, satisfying all three required deliverables:

1. **Task 1 — Review & Rating Simulator** (containerised API): given a structured Nigerian user persona and a product description, generate the review text + 1–5 star rating that user would write.
2. **Task 2 — Recommendation Agent** (containerised API): given a structured Nigerian user persona, return a ranked list of products the user is most likely to engage with positively.
3. **Solution Paper (4–8 pages)** + **Code Repository** with reproducible Docker container and clean modular agentic workflow.

**The headline research claim** the paper defends:

> *Vanilla LLM agents — including the kind 200+ WWW'25 AgentSociety teams submitted — systematically under-represent Nigerian reviewers. They smooth out Pidgin and Nigerian-English register, miscalibrate rating intensity, and miss communal framing. We introduce a five-dimension cognitive persona decomposition, a cultural register module trained on AfriSenti / NaijaSenti / SentiLeye, and a cross-domain bridge that transfers persona representation from Nigerian e-commerce reviews (Jumia/Konga) to Nigerian film reviews (Nollywood). The system recovers the cultural gap quantifiably while improving global metrics, demonstrating that culturally-grounded persona representation is a generalisable architectural contribution.*

**The architectural backbone** is Proposal A from the team's strategy guide — cognitive persona decomposition — extended with a cultural register module and a cross-domain bridge. Orchestrated in **LangGraph** (preserved from v1), retrieval via a **dynamic RAG** layer in **Chroma/Qdrant**, persistence and outcome logging in **NocoDB**, generation via **Claude Sonnet 4** with **Qwen2.5-72B-Instruct** as a cost-controlled local alternative for ablations. Containerised in **FastAPI + Docker**, exposing two judged endpoints plus a Section-15 demo endpoint that uses the persona representation to drive telco churn intervention ranking — preserving the v1 commercial vision as a "with more time" payoff.

**The business framing** that v1.0 invested in is not lost. It becomes the paper's Section 7 *Business Implications* — three Nigerian deployments grounded in real numbers (171.6M telco subscribers, $3.60 ARPU, ₦130 trillion MSME credit gap, 25–35% annual churn) that the global hackathon winners cannot make because they never built for the Nigerian context.

---

## 2. Problem Statement

### 2.1 The cultural gap in LLM agent systems

The WWW'25 AgentSociety Challenge attracted 295 teams. Every winning architecture — USHB (Jiangnan University), Renmin Collaborative Optimization, Tsinghua Adaptive Knowledge Fusion, the CAS Knowledge-Driven Framework — was trained, tuned, and evaluated on Yelp, Amazon, and Goodreads. These are U.S./global-distribution datasets. The winners are excellent at what they do; none of them speak Nigerian.

Concretely, Nigerian reviews exhibit features that vanilla LLM simulators handle poorly:

- **Register and code-switching.** Pidgin English markers ("e shock me", "e too much", "no cap", "scatter scatter"), Nigerian English forms ("the food sweet die", "well done sir"), code-mixing with Yorùbá, Hausa, Igbo phrases ("ahn ahn", "wahala", "abeg").
- **Rating-intensity variance.** Anecdotal and partially empirical evidence: Nigerian reviewers use 1-star and 5-star more frequently than U.S. baselines, with thinner middle-ground reviewing.
- **Communal framing.** "We enjoyed", "my family loved", "even my mama was vibing" — versus the individualist "I" framing of U.S./EU reviews.
- **Religious markers.** "By God's grace", "Thank God", "Praise the Lord" — that vanilla sentiment classifiers often misread.
- **Domain-specific aspect priorities.** Party-jollof texture vs. generic "food quality"; Nollywood production-value cues (Africa Magic Epic level, juju vs. modern setting, big-budget cinematography) vs. Hollywood-trained vocabularies.

A median submission to the hackathon — "paste the user history into a prompt and ask the LLM to write a review" — produces output that is technically grammatical but culturally hollow. The judges (Nigerian-based panel) will spot it on read.

### 2.2 Why this matters beyond cosmetic register

This is not a "sprinkle abeg into the output" cosmetic problem. It has two structural consequences:

- **User simulation downstream tasks fail.** If you cannot simulate a Nigerian user faithfully, you cannot build any product that depends on simulated user behaviour: thin-file credit scoring, telco churn intervention modelling, marketplace personalization, survey augmentation, social-media policy testing. Every downstream Nigerian use case inherits the cultural gap.
- **Recommendation systems mis-recommend.** A recommender that does not understand Nigerian aspect priorities will not understand why a user who loved "Anikulapo" also loved "King of Boys" — it sees them as unrelated dramas; a Nigerian persona sees them as the same epic-historical aesthetic.

### 2.3 Quantified backdrop (for the paper's business section)

- **Nigerian telecom market.** 171.6M subscribers as of August 2025 (NCC). MTN: ~52.3% share, ~89.6M subscribers. Airtel: ~33.9%, ~58M. Globacom: ~12.2%, ~20.9M. ARPU at MTN Nigeria ~$3.60 in 2025. Annual churn 25–35%.
- **Financial inclusion.** 64% of Nigerian adults financially included (EFInA 2023), up from 54% in 2020. Consumer credit at ₦4.12 trillion, ~3% of GDP.
- **MSME credit gap.** ₦130 trillion (CBN, April 2026) / ~$236 billion (Stears). Only ~4% of Nigeria's 40M MSMEs have formal bank loans. Maximum lending rates frequently >30% per annum.
- **Diaspora.** ~17 million Nigerian-diaspora globally — systematically mis-served by recommenders trained on U.S./EU patterns.

The PRD does not ask the agent to solve these problems directly. They are the business consequence of solving the underlying persona-representation problem well.

---

## 3. Goals & Success Metrics

| Goal | Metric | Target |
|---|---|---|
| **Task 1 — Rating accuracy** | RMSE on held-out Jumia/Konga + Nollywood Nigerian-marker subset | < 0.75 RMSE; beat vanilla-LLM baseline by ≥ 0.15 |
| **Task 1 — Review text quality** | RGM = 1 − (0.25 ETE + 0.25 SAE + 0.5 TRE); BERTScore vs. ground truth | RGM ≥ 0.85; BERTScore F1 ≥ 0.82 |
| **Task 1 — Cultural register fidelity** | NaijaSenti-classifier confidence on generated text matches ground-truth register tier | ≥ 80% tier match |
| **Task 2 — Ranking quality** | HR@1, HR@3, HR@5 averaged on Jumia/Konga; HR@5 on Nollywood | Average HR ≥ 0.65 on Jumia; HR@5 ≥ 0.55 on Nollywood |
| **Cross-domain transfer** | HR@5 on Nollywood using *Jumia-only* persona vs. Nollywood-only persona | Cross-domain HR@5 ≥ 80% of in-domain HR@5 |
| **Cold-start** | HR@5 on users with < 3 reviews | Beat zero-shot LLM by ≥ 10 percentage points |
| **Reproducibility** | Time from `git clone` to first successful API call on a fresh machine | < 10 minutes |
| **Container performance** | p95 latency per request; cold start | < 3s per request; < 30s cold start |
| **Solution Paper** | Section coverage, ablation count, baseline count, page count | 8 sections, ≥ 7 ablations, ≥ 4 baselines, 6–8 pages |
| **Nigerian-context bonus** | Quantified gap recovery on Nigerian-marker subset | ≥ 0.3-star rating intensity recovery; ≥ 25% review-quality lift over vanilla baseline on Nigerian-marker subset |

---

## 4. Target Users & Stakeholders

### 4.1 Primary audience: hackathon judges

The judges are a Nigerian-based panel evaluating against the brief's three deliverables. Their reading order, per the brief: **paper first, then code, then live container**. The paper has to be the strongest artefact. Architecture decisions in this PRD are made to give the paper claimable, ablated, defensible contributions — not to maximise raw metrics at the expense of the story.

### 4.2 Secondary audience: downstream business buyers

Once the hackathon is over, the same architecture serves real commercial pilots:

- **Telcos** — MTN Nigeria (89.6M subscribers), Airtel Nigeria (58M), Globacom (20.9M) — for churn intervention recommendation (the v1 product, repositioned).
- **Fintechs** — Opay, Palmpay, Moniepoint, Kuda, FairMoney — for thin-file credit scoring, dormancy prediction, behavioural cohorting.
- **Commerce platforms** — Jumia, Konga, Selar, Bumpa — for review augmentation and cross-cultural personalisation.
- **Media platforms** — Showmax, IROKO TV, Boomplay, Mdundo — for Nigerian-context content recommendation.

### 4.3 Tertiary audience: research community

- **AgentSociety / Tsinghua FIBLAB** — the lab whose 2025 challenge framework this submission extends.
- **Masakhane / AfriSenti community** — Nigerian NLP work the register module builds on; the paper cites them explicitly.
- **WWW / NeurIPS 2026 cycle** — the post-hackathon target for paper expansion.

---

## 5. User Stories

### 5.1 As a hackathon judge

- I want to clone the repo, run `make demo`, and see Task 1 and Task 2 endpoints serving requests within 10 minutes — so I do not waste my evaluation slot on setup.
- I want the README to tell me exactly which curl command exercises each task — so I can sanity-check the system without reading source.
- I want the paper to have a clear headline claim, a clean ablation table, and at least three baselines I recognise — so I can place this submission against the median.
- I want the Nigerian-context contribution to be quantified, not flagged — so I can score the cultural bonus honestly.

### 5.2 As a downstream business user (telco / fintech CX team)

- I want the persona representation to be exportable as JSON so my CRM team can ingest it without custom engineering.
- I want every output (review, recommendation, intervention) to ship with a human-readable rationale — "this user is a high-intensity, communal-framing, Pidgin-leaning reviewer who prioritises delivery speed" — so I can defend campaign decisions to my CFO.
- I want the system to keep getting smarter as we feed back outcome data, so my recommendations improve quarter-over-quarter.

### 5.3 As an internal data engineer / researcher

- I want each architectural component to be ablatable independently so I can measure its contribution before deciding to keep it.
- I want all dependencies pinned and all seeds set so I can rerun any experiment exactly.
- I want the LangGraph state to be inspectable and checkpointed so I can debug failed runs without losing intermediate work.

---

## 6. System Architecture

### 6.1 Two-task architecture aligned to the brief

```
              ┌─────────────────────────────────────────────────┐
              │           SHARED PERSONA REPRESENTATION         │
              │ (5 cognitive dimensions + register tier +       │
              │  aspect priority + history anchors)             │
              └────────────────┬─────────────────┬──────────────┘
                               │                 │
                               ▼                 ▼
              ┌────────────────────────┐  ┌────────────────────────┐
              │   TASK 1 AGENT         │  │   TASK 2 AGENT         │
              │   Review & Rating      │  │   Recommendation       │
              │   Simulator            │  │   Agent                │
              │                        │  │                        │
              │ Input:                 │  │ Input:                 │
              │   • persona            │  │   • persona            │
              │   • product details    │  │   • candidate set      │
              │                        │  │     (or universe)      │
              │ Output:                │  │                        │
              │   • star rating (1-5)  │  │ Output:                │
              │   • review text        │  │   • ranked top-K       │
              │   • register tier      │  │     products with      │
              │   • rationale          │  │     reasons            │
              └────────────────────────┘  └────────────────────────┘
                               │                 │
                               └─────────┬───────┘
                                         ▼
                  ┌──────────────────────────────────────┐
                  │      DYNAMIC RAG + NOCODB STORE      │
                  │   (post-query writeback, outcome     │
                  │    reinforcement, register corpus)   │
                  └──────────────────────────────────────┘
```

Two independent LangGraph workflows share the persona representation layer, the RAG store, and the LLM backbone. The brief requires two independent containers/endpoints; the implementation is one container exposing two routes plus shared services.

### 6.2 Shared persona representation

The persona is the system's central abstraction. Every component reads it; the agents are conditioned on it; the cross-domain bridge transfers it; the paper's headline claim lives or dies by it.

```python
@dataclass
class Persona:
    # Identity (optional; can be anonymous)
    user_id: str | None
    demographics: dict | None  # age range, location, gender — never PII

    # Cognitive dimensions (5)
    hedonic_utilitarian: float          # 0.0 utilitarian → 1.0 hedonic
    intensity_calibration: dict          # mapping {"amazing": 4.7, "okay": 3.1, ...}
    communal_individual: float           # 0.0 individualist → 1.0 communal
    aspect_priority: dict[str, float]    # per-domain weighted vocabulary
    context_sensitivity: float           # variance under time/season/weekend

    # Cultural register (1)
    register_tier: Literal[
        "standard_english",
        "nigerian_english",
        "nigerian_pidgin",
        "code_mixed",
    ]
    register_markers: list[str]          # observed markers from history

    # Domain-specific aspect priors (loaded lazily)
    domain_priors: dict[str, dict]       # {"jumia": {...}, "nollywood": {...}}

    # History anchors for retrieval
    review_anchors: list[ReviewAnchor]   # 3-5 similar past reviews
```

The five cognitive dimensions are extracted **offline** for known users from review history via a structured LLM-pipeline. For unknown users (cold-start), they are inferred from a 3-question elicitation flow at first interaction.

### 6.3 Cultural register module

A dedicated classifier trained on AfriSenti-SemEval (Hausa, Igbo, Nigerian-Pidgin, Yorùbá) + NaijaSenti (30k tweets per language) + SentiLeye (300 Pidgin sentiment tokens + 14k gold-standard reviews) classifies any text into one of four register tiers. The classifier outputs both a tier and a confidence; the persona stores the tier; the agent conditions style generation on it.

**Why it matters**: the headline ablation — "no register module" — is the experiment whose result anchors the paper's Nigerian-context claim. If the register module recovers ≥ 25% of the cultural gap on the Nigerian-marker subset, the paper has its thesis.

### 6.4 Cross-domain bridge

The same persona can produce both a Jumia electronics review and a Nollywood film review. The bridge is the LLM-mediated aspect-mapping function:

```
persona × jumia_aspects → persona × nollywood_aspects
```

A user who scores high on hedonic-utilitarian + communal framing + Pidgin register in their Jumia reviews of bridal makeup is hypothesised to score similarly when reviewing Nollywood romance dramas. The bridge experiment **measures the strength of this transfer**: how much of the in-domain HR@5 on Nollywood can a Jumia-only persona recover?

This is the paper's novel cross-domain claim. No WWW'25 winner attempted it.

### 6.5 Dynamic RAG layer (preserved and extended from v1)

The retrieval index is live, not static. After every Task 1 or Task 2 query, the LangGraph workflow writes three documents back to the vector store:

1. The resolved persona snapshot (timestamped, tagged with sector/domain/register tier).
2. The generated review or recommendation list.
3. (When available) the campaign outcome / feedback signal.

Outcome-reinforced embeddings boost successful recommendations and decay failed ones — the retrieval-layer companion to the standard feedback loop in v1.

**Vector store**: Chroma in development, Qdrant in production deployment.
**Embeddings**: BGE-large (`BAAI/bge-large-en-v1.5`) for cost-quality balance; `text-embedding-3-small` for the cost-optimal path.
**Initial corpus**: Jumia/Konga reviews, Nollywood reviews, NCC quarterly reports (for business-section grounding), AfriSenti/NaijaSenti reference samples, intervention library entries (for Section-15 demo), behavioural signal taxonomy.

### 6.6 Data flow (Task 1)

```
Input: persona + product description
   │
   ▼
[1] LangGraph entry — load persona; resolve domain
   │
   ▼
[2] Retrieve — RAG node pulls top-K anchors:
       • user's own most-similar prior reviews
       • this product's most representative reviews
       • register-tier exemplars
   │
   ▼
[3] Style retrieval — pull user's most-extreme positive
       and negative reviews of same category
   │
   ▼
[4] Stage A — Rating prediction (XGBoost / LightGBM)
       Features: [persona dimensions, product embedding,
                  aspect match score, user mean rating,
                  similar-user ratings for this product,
                  register marker, context]
       Output: predicted rating ∈ {1..5}
   │
   ▼
[5] Stage B — Text generation (Claude Sonnet 4)
       Prompt template selected by:
         • domain (jumia | nollywood)
         • register tier
       Conditioning:
         • predicted rating
         • persona dimensions
         • retrieved anchors
         • product description
       Output: review text
   │
   ▼
[6] Self-consistency check
       Embedding similarity (generated, user's corpus)
       If < τ_self_consistency: regenerate with stronger
       style anchoring (one retry only)
   │
   ▼
[7] Writeback — index the new (persona, product, review,
       rating) tuple to the RAG store
   │
   ▼
Output: { rating, review_text, register_tier, rationale }
```

### 6.7 Data flow (Task 2)

```
Input: persona [+ optional candidate set]
   │
   ▼
[1] LangGraph entry — load persona; resolve domain
   │
   ▼
[2] Multi-source parallel candidate retrieval (if no
       candidate set given):
       • LightGCN candidates (collaborative)
       • Content-similarity candidates (product embedding)
       • Semantic candidates (LLM zero-shot from textual
         persona priors)
       • Aspect-match candidates (top items matching the
         persona's aspect-priority vector)
   │
   ▼
[3] Reciprocal Rank Fusion → unified candidate pool (K=50)
   │
   ▼
[4] Pre-ranking with external knowledge injection (per
       Tsinghua Adaptive Knowledge Fusion):
         Prerank(persona, I) =
           Rank( K(persona, i_1), ..., K(persona, i_n) )
       where K combines item quality, popularity, average
       rating, register-tier match
   │
   ▼
[5] MACF-style multi-agent re-ranker
       Instantiate similar-user agents and relevant-item
       agents; they deliberate; aggregate via soft self-
       consistency (5 traces, summarised, not majority-voted)
   │
   ▼
[6] Cold-start handler (if persona.history_count < 3)
       3-question elicitation flow seeded by register
       inference; reseed candidates
   │
   ▼
[7] Cross-domain bridge (if source_domain ≠ target_domain)
       LLM-mediated aspect mapping; re-score top-N with
       transferred persona representation
   │
   ▼
[8] Writeback — index the recommendation list with
       persona context to the RAG store
   │
   ▼
Output: ranked list of top-K products with rationale
        per item
```

---

## 7. Functional Requirements

### 7.1 Persona Extraction Layer

- **FR-P1.** Given a user's review history (≥ 3 reviews), extract the five cognitive dimensions via a structured LLM pipeline. Output: serialisable `Persona` JSON.
- **FR-P2.** Given < 3 reviews, run a 3-question elicitation flow seeded by register inference of any available text.
- **FR-P3.** Extracted personas are cached in NocoDB with TTL = 30 days; re-extraction triggered on cache miss or explicit refresh.
- **FR-P4.** Persona JSON includes every field shown in Section 6.2. No additional or optional fields not in the schema.
- **FR-P5.** Personas are versioned (`schema_version: "1.0"`). Schema migrations live in `app/data/persona_migrations.py`.

### 7.2 Cultural Register Module

- **FR-R1.** A trained classifier (`app/agents/register_classifier.py`) maps any text → register tier ∈ `{standard_english, nigerian_english, nigerian_pidgin, code_mixed}` with confidence ∈ [0, 1].
- **FR-R2.** The classifier is trained on a corpus combining AfriSenti, NaijaSenti, SentiLeye gold-standard, and 10–20% LLM-augmented synthetic data using orthographic variation per Lin et al. (2024).
- **FR-R3.** Inference latency < 100ms per text on CPU.
- **FR-R4.** Register markers extracted at classification time are stored on the persona for downstream conditioning.
- **FR-R5.** Classifier outputs are calibrated (Platt scaling or isotonic) and reported in the paper.

### 7.3 Task 1: Review & Rating Agent

- **FR-T1.1.** Accepts `{ persona: Persona, product: ProductDetail }` and returns `{ rating: int, review: str, register_tier: str, rationale: str }`.
- **FR-T1.2.** Rating is predicted by a separate Stage-A regressor before text generation (Renmin-team insight — never joint).
- **FR-T1.3.** Text generation uses a domain-specific prompt template (`jumia_v1.jinja`, `nollywood_v1.jinja`) chosen at runtime.
- **FR-T1.4.** Output text is style-checked against persona's review-corpus embedding; regeneration triggered once if similarity < τ.
- **FR-T1.5.** Every response includes a `rationale` string identifying which two persona dimensions and which one register marker most influenced the output.
- **FR-T1.6.** API contract documented in `app/api/routers/simulate_review.py` and exposed via FastAPI Swagger at `/docs`.

### 7.4 Task 2: Recommendation Agent

- **FR-T2.1.** Accepts `{ persona: Persona, candidate_set?: list[str], domain?: "jumia" | "nollywood", k: int = 5 }` and returns `{ recommendations: list[RecItem] }` where each `RecItem = { product_id, score, rationale }`.
- **FR-T2.2.** If `candidate_set` is omitted, runs full multi-source retrieval (Section 6.7 step 2).
- **FR-T2.3.** Pre-ranking with external knowledge injection (Tsinghua-style) runs before the LLM re-ranker.
- **FR-T2.4.** Multi-agent re-ranker (MACF-style) samples 5 traces, aggregates via soft self-consistency.
- **FR-T2.5.** Cold-start branch activates automatically when persona's `history_count < 3`; cold-start elicitation is a separate endpoint `/elicit` returning a 3-question flow.
- **FR-T2.6.** Cross-domain bridge activates when `persona.history_domain ≠ domain`; bridge logic is in `app/agents/cross_domain_bridge.py`.

### 7.5 Cross-Domain Bridge

- **FR-CB1.** Function signature: `bridge(persona: Persona, source_domain: str, target_domain: str) -> Persona` — returns a persona with `domain_priors[target_domain]` populated from `domain_priors[source_domain]`.
- **FR-CB2.** Bridge uses LLM-mediated aspect mapping with a fixed prompt template (`bridge_jumia_to_nollywood.jinja` and reverse).
- **FR-CB3.** Bridged personas are tagged `bridged: True` in the rationale so downstream consumers know the persona's target-domain priors are inferred, not observed.
- **FR-CB4.** Bridge effectiveness is the headline cross-domain experiment in the paper (Section 11).

### 7.6 Dynamic RAG layer

- **FR-RAG1.** Embeds and writes back every persona snapshot, generated review, and recommendation list after every query.
- **FR-RAG2.** Outcome reinforcement: when an outcome signal is logged (campaign retention, click-through, purchase, rating-back), the corresponding document's embedding is reweighted (+ on success, − on failure).
- **FR-RAG3.** Stale documents (no reinforcement, > 18 months) demoted via nightly maintenance job.
- **FR-RAG4.** Retrieval respects metadata filters: `domain`, `register_tier`, `recency`, `operator` (for the business-section demo).

### 7.7 Self-Consistency

- **FR-SC1.** Task 1 uses single-shot generation + one regeneration on style-check failure.
- **FR-SC2.** Task 2 uses 5-sample self-consistency with soft summarisation aggregation (Wu et al. WWW '25 finding — soft beats majority).
- **FR-SC3.** Sample temperature: 0.7 for Task 1 (creative), 0.4 for Task 2 (precision).

### 7.8 Feedback Loop (carried forward from v1, repositioned)

- **FR-FB1.** Outcome logging endpoint: `POST /feedback` accepts `{ query_id, outcome }` where outcome is task-specific (e.g., true rating, true rank, purchase).
- **FR-FB2.** Weekly reweighting cycle (n8n cron) recomputes recommendation effectiveness weights.
- **FR-FB3.** Effectiveness changelog persisted in NocoDB, retained 24 months.

### 7.9 Business-Application Demo (Section 15)

- **FR-BD1.** Optional endpoint `POST /business/churn-intervention` accepts a Nigerian-telco subscriber persona and returns a ranked intervention list using the same persona representation.
- **FR-BD2.** This endpoint is **not** part of the scored hackathon tasks; it exists to demonstrate that the persona representation transfers to the business case the paper claims.
- **FR-BD3.** Demonstration only; uses synthetic Nigerian telco profiles calibrated to NCC.

---

## 8. Technical Architecture

### 8.1 Framework decision: LangGraph (preserved from v1)

The system uses **LangGraph** as the primary Python framework, with **LangChain** components used selectively for utilities. The five reasons from v1 are preserved verbatim because they remain correct for the review/recommendation framing:

- Stateful, cyclical workflows (classify → explain → recommend → log → reweight → re-retrieve).
- Persistent state across runs via the built-in checkpointer (SQLite in dev, Postgres in production).
- Human-in-the-loop gates (interrupt-and-resume at any node) — used for the cold-start elicitation flow and for the business-section demo.
- Observability and auditability via per-node traces (LangSmith-compatible).
- Reuses the LangChain ecosystem for loaders, embeddings, vector stores.

### 8.2 Container & API design

- **Single Dockerfile** builds the production image.
- **docker-compose.yml** orchestrates: app + Chroma + NocoDB + Postgres (for LangGraph checkpointer).
- **FastAPI** as the API framework. **uvicorn** as the ASGI server. Lazy LLM-client loading on first request to keep cold-start under 30s.
- **Endpoints**:
  - `POST /simulate-review` — Task 1
  - `POST /recommend` — Task 2
  - `POST /elicit` — cold-start elicitation
  - `POST /feedback` — outcome logging
  - `GET /health` — liveness/readiness probe
  - `GET /docs` — Swagger UI
  - `POST /business/churn-intervention` — Section 15 demo (optional, behind `--with-business-demo` flag)
- **API request/response schemas** are declared with Pydantic and exported as OpenAPI JSON.

### 8.3 LLM backbone

- **Primary**: Claude Sonnet 4 (`claude-sonnet-4-20250514`) via Anthropic API. Reasoning quality + cultural breadth.
- **Cost-controlled benchmarking**: Qwen2.5-72B-Instruct served via vLLM on a local A100, for ablation runs.
- **Embedding model**: BGE-large-en-v1.5 primary; `text-embedding-3-small` (OpenAI) for the cost-optimal path.
- **No fine-tuning of the base LLM** for hackathon submission — keep dependencies API-shaped for judge reproducibility. The register classifier is the only trained model in the system.

### 8.4 Storage

- **NocoDB** — persona profiles, intervention library, outcome log, model weights, paper-figure data.
- **Postgres** — LangGraph checkpointer backing store.
- **Chroma (dev) / Qdrant (production)** — vector index for the dynamic RAG layer.
- **Local disk** — dataset shards, register classifier weights, prompt templates.

### 8.5 Orchestration

- **n8n** (self-hosted) — data ingestion pipelines, weekly reweighting cron, outcome-logging workflow. Same role as v1.
- **LangGraph** — agent reasoning workflows. Same role as v1.

### 8.6 Observability

- LangSmith traces for every agent run.
- MLflow / Weights & Biases for experiment tracking (mandatory if you want the paper's ablation table to be reproducible).
- Loki + Grafana lightweight stack in docker-compose for production-style log inspection.

### 8.7 Deployment notes

- Cloud-hosted on Render / Railway / Fly.io for hackathon judge access (free-tier ok).
- Nigeria data residency is preferred but not blocking for hackathon submission — flagged for the pilot deployment in Section 15.
- NDPR-compliant architecture: no PII stored; only hashed identifiers; right-to-be-forgotten endpoint planned (out of scope for hackathon container).

---

## 9. Dataset Strategy

### 9.1 Primary domain: Jumia/Konga e-commerce

- **Source A — Iwendi et al. 2020.** Existing academic dataset, 30,382 cleaned reviews across Jumia/Jiji/Konga/Takealot. Anchor for the validity story. Cite explicitly.
- **Source B — Fresh scrape.** Curated scrape of current Jumia and Konga listings across 10 category trees (Electronics, Fashion, Beauty, Home & Office, Phone & Tablet, Health, Baby Products, Computing, Sports, Automobile). Rate-limited, respectful, robots.txt-compliant. Target +20k fresh reviews.
- **Total target**: ~50k Jumia/Konga reviews.
- **Per review**: text, star rating, product metadata (category, price band, brand), reviewer pseudonym (hashed), timestamp.

### 9.2 Secondary domain: Nollywood

- **Source A — Letterboxd Nigerian-user reviews.** Filter Letterboxd's public review corpus for Nigerian user locale markers + Nollywood film tags. Target 3–5k reviews.
- **Source B — Twitter / Reddit / Instagram Nollywood discourse.** Scrape #Nollywood, r/Nollywood, Instagram comments on Nollywood film promo posts. Target 5–10k items.
- **Source C — Nigerian blog reviews.** Hand-curated list of 10–15 Nollywood-focused blogs (Mira Mason-Reader, What Kept Me Up, NollywoodTV, Bella Naija film section). Target ~1k long-form reviews.
- **Source D — Showmax / IROKO TV catalogue metadata.** Films, casts, directors, plot summaries. Not reviews — corpus for product detail.
- **Total target**: ~10k Nollywood reviews + ~5k catalogue items.

### 9.3 Cross-domain user subset

- Users with reviews in *both* domains are rare in raw data. We construct them via **persona-linked synthetic generation**: for ~500 real users with rich Jumia history, generate plausible Nollywood reviews conditioned on their extracted persona; have a held-out human-evaluation set verify plausibility on a 100-sample subset.
- This is the cross-domain experiment dataset. The paper section reports the persona-linked synthetic generation explicitly — it is the experimental method, not concealed data augmentation.

### 9.4 Nigerian-marker construction

A subset of the corpus is tagged "high-confidence Nigerian" for the headline cultural-gap experiment:

- AfriSenti + NaijaSenti classifier → register tier
- SentiLeye lexicon → Pidgin marker count
- Geographic markers from author profile (where available)
- Name markers from username analysis
- Combined confidence ≥ 0.8 → "Nigerian-marker" tag

Target Nigerian-marker subset: ~15k Jumia + ~7k Nollywood reviews. This is what the headline cultural gap is measured on.

### 9.5 Synthetic data policy

Per the hackathon brief: "I can use data if available online or internationally available data but custom to this use case, where there's no data at all, we use synthetic data."

The policy:

- **Real data primary** wherever it exists (Jumia/Konga, Letterboxd, Nigerian blogs, social media).
- **Synthetic augmentation only** for: cross-domain user pairs (Section 9.3), register-tier balancing (under-represented Pidgin-heavy reviews), and the Section-15 churn demo (synthetic subscriber profiles).
- **All synthetic data tagged** with `synthetic: True` in the corpus. Train/eval splits respect this — main evaluation runs on real-only subsets; cross-domain experiments allow synthetic but report the result separately.
- **Generation grounding**: synthetic reviews are generated by Claude Sonnet 4 conditioned on real-distribution priors (rating intensity histogram, register marker frequency, aspect priority by category). No "free-form synthesise a Nigerian review" prompts.

### 9.6 Dataset deliverables for the repo

- `data/jumia_reviews/` — schema documented in `data/README.md`.
- `data/nollywood_reviews/` — same.
- `data/personas/` — extracted personas (cached).
- `data/synthetic/` — synthetic augmentations, tagged.
- `data/sample/` — small representative subset bundled in the container for judges who do not want to download the full corpus.
- `scripts/build_dataset.sh` — reproducible build script from raw sources to clean splits.

---

## 10. Evaluation Framework

### 10.1 Task 1 metrics

| Metric | Definition | Target |
|---|---|---|
| **RMSE** (rating) | √( Σ (predicted − actual)² / N ) | < 0.75 |
| **MAE** (rating) | Σ |predicted − actual| / N | < 0.58 |
| **BERTScore F1** (review text) | precision/recall F1 over BERT token embeddings against ground-truth review | ≥ 0.82 |
| **RGM** | 1 − (0.25 × ETE + 0.25 × SAE + 0.5 × TRE) per USHB | ≥ 0.85 |
| ETE | TweetEval emotion classifier embedding distance | minimised |
| SAE | NLTK / VADER sentiment-score distance | minimised |
| TRE | Sentence-BERT topic-cosine distance | minimised |
| **Register-tier match** | predicted_register == ground_truth_register | ≥ 80% |
| **Cultural-marker recall** | fraction of ground-truth Pidgin/Nigerian markers that appear in generated text | ≥ 60% on Nigerian-marker subset |

### 10.2 Task 2 metrics

| Metric | Definition | Target |
|---|---|---|
| **HR@1** | fraction of test cases where ground truth is rank 1 | ≥ 0.30 |
| **HR@3** | fraction where ground truth is in top 3 of 20 | ≥ 0.60 |
| **HR@5** | fraction where ground truth is in top 5 of 20 | ≥ 0.75 |
| **Average HR** | mean of HR@1, HR@3, HR@5 | ≥ 0.55 (Jumia) |
| **NDCG@5** | discounted cumulative gain at 5 | ≥ 0.65 |
| **Cross-domain HR@5** | HR@5 on Nollywood using Jumia-only persona | ≥ 0.80 × in-domain HR@5 |
| **Cold-start HR@5** | HR@5 for users with < 3 reviews | beat zero-shot LLM by ≥ 10pp |

### 10.3 Ablation table (mandatory for paper)

Each row reports Task-1 RMSE + Task-1 RGM + Task-2 HR@5, on the Nigerian-marker subset, averaged across 3 seeds:

| Configuration | RMSE ↓ | RGM ↑ | HR@5 ↑ |
|---|---|---|---|
| **Full system** | | | |
| − No cognitive dimensions (Persona = history-paste baseline) | | | |
| − No register module | | | |
| − No two-stage rating (single-prompt) | | | |
| − No domain-specific templates | | | |
| − No self-consistency | | | |
| − No cross-domain bridge | | | |
| − No external-knowledge pre-ranking | | | |
| − No outcome-reinforced RAG | | | |
| − **Headline:** Vanilla LLM (Claude zero-shot + history paste) | | | |

Each ablation removes exactly one component to isolate contribution. Run with 3 seeds, report mean and standard deviation.

### 10.4 Baselines (mandatory for paper)

| Baseline | Description | Source |
|---|---|---|
| **Vanilla LLM** | Claude Sonnet 4 zero-shot with concatenated user history in prompt | This work |
| **USHB-style** | Re-implementation of USHB (User-and-Item Relationship Graph + IF-THEN style rules) on Jumia/Konga | github.com/jnuaipr/AgentsChallenge, ported |
| **Tsinghua AKF** | Adaptive Knowledge Fusion (pre-ranking + ensemble) on Jumia/Konga | DOI 10.1145/3701716.3719230, re-implemented |
| **LightGCN** | Pure collaborative filtering (rec only) | RecBole or PyTorch implementation |
| **AgentCF++** | Dual-agent user-and-item memory baseline | arXiv:2502.13843, lightweight port |

All baselines are run on the same Jumia/Konga + Nollywood Nigerian-marker subset. The paper compares head-to-head.

### 10.5 Cross-domain experiment

- Train persona extractor on Jumia reviews only.
- Apply cross-domain bridge to produce Nollywood-domain persona priors.
- Run Task 2 Nollywood recommendation; compare HR@5 to in-domain Nollywood persona.
- Report the transfer ratio in the paper.

### 10.6 Cultural-gap recovery experiment (paper headline)

The paper's central claim is the cultural-gap recovery number. Protocol:

1. Run Vanilla LLM baseline on Nigerian-marker subset. Record rating intensity bias (mean predicted − mean actual), RGM, register-tier match.
2. Run NPA full system on the same subset. Record same metrics.
3. **Gap = baseline error − NPA error**. Report as the headline number.

Target: ≥ 0.3-star rating intensity recovery, ≥ 25% RGM lift, ≥ 30pp register-tier match lift.

---

## 11. Solution Paper Plan

### 11.1 Target

- **Length**: 6 pages, expandable to 8 with appendix. Two-column ACM/IEEE style.
- **Venue framing**: drafted to hackathon brief; structured so it is one revision away from arXiv-ready and two revisions away from a WWW / NeurIPS workshop submission.
- **Title (working)**: "Naija Persona Agent: Cognitive Decomposition and Cultural Register for LLM-Based User Simulation and Recommendation in Nigerian Markets."

### 11.2 Section structure

1. **Abstract** (150 words) — state the gap (vanilla LLM agents miss Nigerian register and miscalibrate intensity), the contribution (cognitive persona + register + cross-domain bridge), the result (X% gap recovery, Y% global metric improvement).
2. **Introduction** (¾ page) — motivate user modelling and recommendation as more than profile aggregation; state the cultural gap; preview the contributions; commit to the headline number.
3. **Related Work** (¾ page, 5 paragraphs) — LLM user simulation (AgentCF, AgentCF++, RecAgent, Agent4Rec), LLM recommendation (P5, TALLRec, RecMind, MACF), AgentSociety winners (USHB, Renmin, Tsinghua AKF), Cold-start LLM reasoning (Netflix WWW '26), Nigerian NLP (AfriSenti, NaijaSenti, SentiLeye, Lin et al. 2024 Pidgin orthographic augmentation).
4. **Method** (2 pages) —
   - 4.1 Cognitive dimension extraction with formal definitions.
   - 4.2 Cultural register module: training data, classifier architecture, calibration.
   - 4.3 Task 1 two-stage rating-text pipeline.
   - 4.4 Task 2 multi-source candidate retrieval + MACF re-ranker + cold-start branch.
   - 4.5 Cross-domain bridge.
5. **Nigerian Context Case Study** (¾ page) — *distinctive section*. Data construction (Jumia/Konga, Nollywood, marker filter, synthetic augmentation policy). Baseline gap analysis. Recovery analysis with register module. This is where the headline number lives.
6. **Experiments** (1¼ pages) — datasets and protocol; baselines; main results (Tables 1–2); ablation study (Table 3); cross-domain transfer (Table 4); cold-start (Table 5); register fidelity (Table 6); qualitative examples (Figure 4).
7. **Business Implications** (½ page) — three Nigerian deployments grounded in the v1 PRD work: telco churn intervention (with the v1 quantification), MSME credit scoring layer, cross-cultural marketplace personalisation. Quantified backdrop (₦130T MSME gap, 25–35% telco churn, ARPU $3.60, ~17M diaspora).
8. **Limitations** (¼ page) — cite "Lost in Simulation" (arXiv:2601.17087) explicitly; acknowledge LLM-simulated users diverge from real users on action sequences; note correlative not causal evaluation; sample-size constraints; synthetic-data caveats.
9. **Conclusion** (¼ page) — one paragraph.

### 11.3 Required tables and figures

| # | Type | Content |
|---|---|---|
| Table 1 | Dataset composition | Sources, sizes, Nigerian-marker subset, synthetic share |
| Table 2 | Main results | NPA vs. 5 baselines on Task 1 + Task 2, both domains |
| Table 3 | Ablation | 9 rows from Section 10.3 |
| Table 4 | Cross-domain transfer | In-domain vs. cross-domain HR@5 |
| Table 5 | Cold-start | Cold-start HR@5 by elicitation strategy |
| Table 6 | Register fidelity | Tier-match accuracy and marker-recall by configuration |
| Figure 1 | Architecture diagram | Section 6.1 schematic, polished |
| Figure 2 | Persona schema | Section 6.2 fields with example |
| Figure 3 | Cross-domain bridge mechanism | Section 6.4 mapping illustration |
| Figure 4 | Qualitative examples | 4 side-by-side generations (vanilla vs. NPA) showing Nigerian-marker differences |

### 11.4 Headline claim (one sentence to repeat across abstract + intro + conclusion)

> *On the Nigerian-marker subset of Jumia/Konga and Nollywood reviews, cognitive persona decomposition combined with a cultural register module reduces rating-prediction RMSE by 23.4%, improves review-generation BERTScore by 5.2 points, and recovers 31.7 percentage points of register-tier fidelity over a vanilla LLM baseline — while a Jumia-only persona, transferred through our cross-domain bridge, retains 84% of in-domain HR@5 performance on Nollywood recommendation.*

*(Numbers are placeholders. Replace with actual results after Week 5 ablation runs.)*

### 11.5 Authorship and acknowledgments

- **Authors**: Franca and Ashinze.
- **Acknowledgments**: AgentSociety Challenge organisers, Masakhane / AfriSenti community, SentiLeye authors, Iwendi et al. for the Jumia/Konga dataset.

---

## 12. Reproducibility & Submission Plan

### 12.1 Repository structure

```
naija-persona-agent/
├── README.md                      # judge-facing quick start
├── LICENSE                        # MIT
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml                 # pinned dependencies
├── poetry.lock                    # exact resolutions
├── Makefile                       # one-command demos
├── .env.example                   # required env vars
├── .github/workflows/             # CI: lint + tests + container build
│   └── ci.yml
├── app/
│   ├── api/
│   │   ├── main.py                # FastAPI app
│   │   ├── routers/
│   │   │   ├── simulate_review.py # Task 1
│   │   │   ├── recommend.py       # Task 2
│   │   │   ├── elicit.py          # cold-start elicitation
│   │   │   ├── feedback.py        # outcome logging
│   │   │   └── business_demo.py   # Section 15 (optional flag)
│   │   └── schemas/               # Pydantic models
│   ├── agents/
│   │   ├── persona_extractor.py
│   │   ├── register_classifier.py
│   │   ├── review_agent.py
│   │   ├── recommendation_agent.py
│   │   ├── cross_domain_bridge.py
│   │   └── macf_reranker.py
│   ├── graphs/                    # LangGraph workflows
│   │   ├── task1_review_graph.py
│   │   └── task2_recommend_graph.py
│   ├── rag/
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   └── writeback.py
│   ├── data/
│   │   ├── loaders.py
│   │   ├── personas.py
│   │   └── persona_migrations.py
│   ├── llm/
│   │   └── client.py              # Claude + Qwen2.5 abstraction
│   └── prompts/
│       ├── jumia_v1.jinja
│       ├── nollywood_v1.jinja
│       └── bridge_jumia_to_nollywood.jinja
├── data/
│   ├── README.md                  # data schema + sources
│   ├── jumia_reviews/
│   ├── nollywood_reviews/
│   ├── personas/
│   ├── synthetic/
│   └── sample/                    # bundled for judge demo
├── notebooks/
│   ├── 01_dataset_construction.ipynb
│   ├── 02_persona_extraction.ipynb
│   ├── 03_register_classifier_training.ipynb
│   ├── 04_task1_evaluation.ipynb
│   ├── 05_task2_evaluation.ipynb
│   ├── 06_ablations.ipynb
│   └── 07_cross_domain_experiment.ipynb
├── scripts/
│   ├── build_dataset.sh
│   ├── train_register_classifier.py
│   ├── build_personas.py
│   ├── run_ablations.py
│   └── make_demo.sh
├── paper/
│   ├── paper.tex                  # camera-ready LaTeX
│   ├── paper.pdf                  # compiled
│   ├── figures/
│   └── references.bib
└── tests/
    ├── test_persona_extractor.py
    ├── test_register_classifier.py
    ├── test_task1_pipeline.py
    ├── test_task2_pipeline.py
    └── test_cross_domain_bridge.py
```

### 12.2 README requirements

The README is the artefact judges read second (after the paper). It must:

- Open with a one-paragraph "what this is" + a single GIF or screenshot of the working API.
- Show the **quick-start path**: `cp .env.example .env` → fill three keys → `make demo` → `curl localhost:8000/simulate-review -d @sample/persona_request.json`.
- Include an **architecture diagram** (same as paper Figure 1).
- Document **every environment variable** required (Anthropic API key, embedding key, NocoDB token, vector store URL).
- Show **API examples** as curl one-liners for both endpoints, with realistic Nigerian persona JSON.
- Provide a **reproduction note**: random seeds set in `app/config.py`; model versions pinned; data revision documented; GPU requirements stated explicitly.
- Cite the academic acknowledgments cleanly (AgentSociety, AfriSenti, NaijaSenti, SentiLeye, Iwendi et al.).
- End with **judge contact**: a `JUDGES.md` file with our team email and a 30-minute response SLA during evaluation week.

### 12.3 Container architecture

- **Image base**: `python:3.11-slim`.
- **Layered build**: deps → code → models. Cache-friendly.
- **Image size target**: < 1.5 GB compressed.
- **Healthcheck**: `GET /health` returns `200` when all dependencies reachable.
- **Compose stack**: app, Chroma, NocoDB, Postgres, optional n8n.
- **Make targets**:
  - `make demo` — bring up the stack, seed sample data, run a smoke test.
  - `make eval` — run the full evaluation suite (long).
  - `make ablations` — run ablation table.
  - `make paper` — compile the paper from `paper/paper.tex`.
  - `make clean` — tear down.

### 12.4 Submission package

The hackathon brief requires three submissions:

| Submission | Form | This project's artefact |
|---|---|---|
| **Link to the Agent built** | Live URL or container | `https://<deployment-url>` + Docker image on GHCR; container ZIP fallback |
| **Solution Paper (4–8 pages)** | PDF | `paper/paper.pdf`; arXiv-ready source |
| **Code Repository** | GitHub link | `github.com/<team>/naija-persona-agent`, MIT-licensed, judge-readable |

### 12.5 Reproducibility test (Week 5 gate)

In Week 5, one team member who has not been touching the codebase clones the repo on a fresh laptop. The clone-to-first-API-call walkthrough must complete in < 10 minutes with no manual fix-ups. Any deviation triggers a README update before submission. This is non-negotiable — the brief says "judges will attempt to run it."

---

## 13. Non-Functional Requirements

| Requirement | Specification |
|---|---|
| **Latency** | p95 < 3s per request; cold start < 30s |
| **Throughput** | ≥ 10 concurrent requests on a single container |
| **Privacy** | No PII stored beyond hashed identifiers; NDPR-aware data architecture; right-to-be-forgotten in roadmap |
| **Explainability** | Every output ships a `rationale` field identifying ≥ 2 persona dimensions and ≥ 1 register marker that drove it |
| **Reliability** | Graceful degradation: if dynamic-RAG vector store is unavailable, fall back to static initial corpus; if LLM API rate-limits, queue and retry with backoff |
| **Scalability** | Architecture supports 10× data growth without replatforming (Qdrant scales horizontally; LangGraph state externalised to Postgres) |
| **Auditability** | Full input-output logs and reweighting changelog retained 24 months |
| **Cost ceiling** | Hackathon evaluation budget: < $100 in API spend across full ablation suite. Achieved via aggressive caching + Qwen2.5 for ablation inner loops |
| **Security** | API keys via env vars only, never in code; rate-limiting on public endpoints; CORS scoped to known origins |
| **Logging** | Structured JSON logs; LangSmith traces; one log line per agent node decision |

---

## 14. Milestones & Timeline (6 weeks)

| Week | Owner focus | Deliverables |
|---|---|---|
| **Week 1** | Foundation | Repo skeleton + Dockerfile + FastAPI stub. Dataset scrape kickoff: Iwendi et al. download, fresh Jumia/Konga scrape running. Persona schema finalised. LangGraph state schema drafted. AfriSenti / NaijaSenti / SentiLeye corpora downloaded and inspected. Memory: project + reference + user updated. |
| **Week 2** | Task 1 + register module | Persona extractor v1 (offline pipeline). Register classifier trained, calibrated, evaluated. Task 1 pipeline end-to-end on Jumia. Stage-A rating regressor trained. Vanilla baseline measured. First numbers in MLflow. |
| **Week 3** | Task 2 + Nigerian-marker subset | Multi-source candidate retrieval (LightGCN trained on Jumia, content-similarity index, semantic, aspect-match). MACF-style multi-agent re-ranker. Cold-start elicitation. Nigerian-marker subset constructed and tagged. First cultural-gap measurement. |
| **Week 4** | Nollywood generalisation + cross-domain bridge | Nollywood corpus assembled (Letterboxd + social + blogs). Task 1 + Task 2 ported to Nollywood. Cross-domain bridge implemented and ablation-tested. Persona-linked synthetic generation for cross-domain user subset. |
| **Week 5** | Container + ablations + baselines | USHB and Tsinghua AKF baselines re-implemented and run on Jumia/Konga + Nollywood. Full ablation suite executed (9 rows × 3 seeds × 2 domains). Container hardened. Fresh-clone reproducibility test passes. Paper Sections 1–4 drafted. |
| **Week 6** | Paper + polish + submit | Paper Sections 5–9 drafted; figures rendered. README finalised with judge-facing quick start. JUDGES.md written. Deployment URL stood up. Submission package assembled. Submit. |

**Slack week (optional Week 7)**: if the team has it, polish + reviewer-style critique pass on the paper + record a 5-minute demo video.

---

## 15. Business Applications (paper Section 7)

The persona representation built for the hackathon tasks is the foundation for a portfolio of Nigerian commercial products. The paper devotes half a page to this — quantified, specific, and tied directly to the v1 PRD work.

### 15.1 Telco churn intervention recommender (preserves v1 PRD)

**Problem.** Nigerian telcos face 25–35% annual churn. ARPU is ~$3.60. Generic blanket promotions waste budget. A churn-prone subscriber whose review behaviour reveals price-sensitivity-not-brand-loyalty needs a different intervention than one whose behaviour shows service-quality-prioritisation.

**Application.** The NPA persona — five cognitive dimensions + register tier + aspect priorities — is exactly what a churn intervention recommender needs as input. The v1 PRD's full architecture (LangGraph orchestration, intervention library, feedback loop, ranked recommendations with cost-to-serve) plugs in directly with the NPA persona as its upstream feed.

**Demonstration.** The optional `/business/churn-intervention` endpoint in the container shows this working on synthetic Nigerian-telco subscriber profiles calibrated to NCC distributions. The paper reports it as a working demonstration, not a fully-evaluated product.

**Buyer.** MTN Nigeria (89.6M subscribers), Airtel Nigeria (58M), Globacom (20.9M).

**ROI math (preserved from v1).** Reducing churn by 7% for 10,000 active users at $500 LTV protects $350,000 in revenue. At MTN scale: a 1% churn improvement is a 9-figure naira annual figure.

### 15.2 Thin-file MSME credit scoring layer

**Problem.** Nigerian banks cannot underwrite the 96% of MSMEs with no formal financial records. Maximum lending rates frequently exceed 30% per annum. CBN MSME funding gap: ₦130 trillion (April 2026).

**Application.** Cognitive dimensions + aspect priorities + register signals derived from consumer review behaviour serve as a behavioural feature layer for credit scoring. Specifically: consistency of purchase categories, variance in aspect emphasis, spending category breadth, review tone stability.

**Buyer.** Commercial banks (Access, GTBank, UBA, Zenith), microfinance banks, the National Credit Guarantee Company (NCGC ₦100B scheme), and digital lenders (FairMoney, Carbon, Renmoney).

**Paper claim.** Not "we built a credit model" — "the persona representation we built correlates with publicly available sector default-rate data from CBN reports." Demonstrable; defensible.

### 15.3 Cross-cultural marketplace personalisation

**Problem.** Nigerian-diaspora consumers (~17M globally) are mis-served by recommenders trained on U.S./EU patterns. Showing a Nigerian-diaspora user the same recommendations as a Boston-resident user misses the point.

**Application.** The cross-domain bridge generalises to cross-cultural personalisation. A user's Jumia-review register predicts their Amazon-US review register; the bridge re-projects U.S.-based recommendations through a Nigerian persona representation.

**Buyer.** Jumia, Konga, Selar, Bumpa, Spar Nigeria, plus diaspora-facing platforms (African Food Box, Tappi, JJC Online).

### 15.4 Nollywood / Afrobeats content recommendation

Cross-domain bridge plus persona representation enable culturally-aware streaming recommendation. Buyer: Showmax, IROKO TV, Boomplay, Mdundo.

### 15.5 Behavioural cohort modelling for fintech

Cognitive dimensions provide an interpretable cohort framework. Hedonic-utilitarian × Communal-individual × Register tier creates explainable segments. Buyer: Opay, Palmpay, Moniepoint, Kuda, FairMoney.

### 15.6 Survey augmentation / synthetic respondents

Per "Lost in Simulation" caveats, can produce synthetic Nigerian respondents for exploratory market research at much lower cost than live surveys. Validate periodically with live data.

---

## 16. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **Nollywood review data is thinner than expected** | Medium | High | Combine 4+ sources (Letterboxd, social, blogs, scraped catalogues); allow persona-linked synthetic augmentation (tagged); fall back to fewer Nollywood examples if needed, with clear paper disclosure |
| **Cross-domain bridge transfer score is weak** | Medium | High | Have single-domain backup numbers ready; even a weak bridge is publishable if quantified honestly; in the worst case, the bridge becomes a negative result the paper still reports |
| **Register classifier underperforms** | Low | Medium | Multiple training corpora (AfriSenti + NaijaSenti + SentiLeye); fallback to pretrained AfriBERTa or NaijaBERT (no retraining); explicit calibration step |
| **API cost overrun** | Medium | Medium | Aggressive caching at every layer; use Qwen2.5-72B via vLLM for ablation inner loops; reserve Claude API for headline runs only; budget ceiling of $100, monitored daily |
| **Container does not reproduce on fresh machine** | Medium | Critical | Week 5 fresh-clone test (non-negotiable); CI pipeline that builds the container from scratch on every commit; pinned deps including OS packages |
| **Hackathon judges expect specific dataset** | Low | Medium | Choice of Jumia/Konga (the Amazon-analog) is the safest read of the "movies, food, drinks" examples; Nollywood adds Nigerian flavour without straying from "products" |
| **Paper does not land headline number** | Medium | Critical | Headline number is the **gap recovery** vs. vanilla baseline, not absolute SOTA — even a modest recovery is a defensible contribution; back-up framing: "even where we under-perform absolute SOTA, we recover the Nigerian-context gap" |
| **Two-person team capacity** | Medium | Critical | Triage ruthlessly: drop the optional business-demo endpoint, drop Week 7 polish, drop one secondary baseline if needed — never drop the ablations or the paper |
| **Cross-domain users are too sparse** | High | Medium | Persona-linked synthetic generation policy (Section 9.3) is explicit; sample size disclosed in paper |
| **NDPR or scraping concerns** | Low | High | Use existing academic dataset (Iwendi et al.) as primary; scraping respectful (rate-limited, robots.txt); no PII stored beyond hashed identifiers |
| **Judges find a baseline implementation bug** | Medium | High | Code review week 5; ablation re-run before submission; baseline numbers disclosed transparently with confidence intervals |

---

## 17. Out of Scope

- Real-time data ingestion from operator partners.
- Production-grade authentication on the public hackathon API (judges receive an open endpoint).
- Multi-tenant SaaS hosting.
- Mobile app.
- Real Nigerian operator subscriber data (the v1 risk — unavailable for hackathon).
- Fine-tuning the base LLM (register classifier is the only trained model).
- Automated campaign execution / autonomous customer outreach (the v1 churn product's deployment side — explicitly out of scope per v1 too).
- Individual-level (vs. persona-level) prediction beyond the persona structure.
- Real-time network quality monitoring.
- Legal or regulatory compliance certification.

---

## 18. Comparison: This System vs. Median Hackathon Submissions

| Dimension | Median submission | Naija Persona Agent |
|---|---|---|
| **Persona representation** | Concatenated past reviews in prompt | Five structured cognitive dimensions + register tier + aspect priorities |
| **Cultural register handling** | None (vanilla LLM smooths it out) | Dedicated classifier trained on AfriSenti + NaijaSenti + SentiLeye; explicit conditioning |
| **Dataset** | Yelp / Amazon / Goodreads (already saturated) | Jumia/Konga + Nollywood (Nigerian-marker subset) |
| **Cross-domain claim** | None — single dataset | Jumia → Nollywood bridge with quantified transfer |
| **Two-stage rating** | Single-prompt rating + text | Stage-A regressor → Stage-B text generator |
| **Self-consistency** | Single LLM call | 5-sample soft self-consistency on Task 2; one-retry style check on Task 1 |
| **External-knowledge pre-ranking** | None | Tsinghua AKF-style pre-ranking before LLM re-rank |
| **Ablations** | 0–2 | 9, with seeds and confidence intervals |
| **Baselines** | 0–1 (vanilla LLM) | 5 (Vanilla, USHB, Tsinghua AKF, LightGCN, AgentCF++) |
| **Business framing** | Generic | Three Nigerian deployments with quantified backdrop |
| **Container** | Often broken on clone | Fresh-clone tested in Week 5 |
| **Paper** | Last-minute write-up | Outline locked Week 1; sections drafted Weeks 5–6 |
| **Reproducibility** | Often missing | Make targets, CI, pinned deps, fresh-clone test, seeds set |

---

## 19. Document Approval

| Role | Name | Signature / Date |
|---|---|---|
| Product Lead | | |
| Technical Lead | | |
| Paper Lead | | |
| Business Sponsor | | |

---

## Appendix A — Glossary

- **NPA**: Naija Persona Agent (this system).
- **Persona**: the structured representation of a user (cognitive dimensions + register + history anchors).
- **Register tier**: one of {standard_english, nigerian_english, nigerian_pidgin, code_mixed}.
- **RGM**: Review Generation Metric, USHB's combined review-quality score.
- **HR@k**: Hit Rate at k, fraction of test cases where the ground-truth item appears in the top-k recommendations.
- **MACF**: Multi-Agent Collaborative Filtering (arXiv:2511.18413).
- **Tsinghua AKF**: Adaptive Knowledge Fusion (Yu et al., WWW '25, DOI 10.1145/3701716.3719230).
- **USHB**: Unified Framework for Simulating Human Behaviors (Zhao et al., WWW '25, 3rd-place User Modeling).
- **Cross-domain bridge**: the LLM-mediated function transferring persona representation from source domain (Jumia) to target domain (Nollywood).
- **NCC**: Nigerian Communications Commission.
- **NDPR**: Nigeria Data Protection Regulation.

## Appendix B — References (for the paper)

(Trimmed; full BibTeX in `paper/references.bib`.)

- Yan et al., *AgentSociety Challenge: Designing LLM Agents for User Modeling and Recommendation on Web Platforms.* arXiv:2502.18754.
- Zhao, Yang et al., *USHB.* WWW '25 Companion, DOI 10.1145/3701716.3719227.
- Zhang et al. (Renmin), *Collaborative Optimization for Workflow Agents.* DOI 10.1145/3701716.3719228.
- Yu et al. (Tsinghua), *Adaptive Knowledge Fusion.* DOI 10.1145/3701716.3719230.
- Wu et al., *Self-Consistency Recommendations.* DOI 10.1145/3701716.3719229.
- Shang et al., *AgentRecBench.* arXiv:2505.19623.
- Zhang et al., *AgentCF++.* arXiv:2502.13843.
- Muhammad et al., *AfriSenti.* ACL Anthology.
- Muhammad et al., *NaijaSenti.* LREC 2022.
- Oyewusi, Adekanmbi, Akinsande, *SentiLeye.* IJCAI 2021 AI4SG.
- Lin et al., *Pidgin orthographic augmentation.* arXiv:2404.18264.
- Iwendi et al., *Sentiment analysis on African e-commerce reviews.* IEEE 2020.
- *Lost in Simulation: LLM-Simulated Users are Unreliable Proxies.* arXiv:2601.17087.
- MACF: *Multi-Agent Collaborative Filtering.* arXiv:2511.18413.
- Cold-Start LLM Reasoning (Netflix), WWW '26. arXiv:2511.18261.

---

*This document supersedes PRD v1.0 (Churn Intervention Recommender). All v1 work is preserved as Section 15 of the paper and as the optional `/business/churn-intervention` demonstration endpoint in the container.*
