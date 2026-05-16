# PRODUCT REQUIREMENTS DOCUMENT
## Naija Persona Agent (NPA) — All-Out Edition
### A Four-Artifact Submission: Agent System + Fine-Tuned Open Model + Public Benchmark + Research Preprint

| | |
|---|---|
| **Project ID** | Project B v3.1 |
| **Document Version** | 3.1 (post-feature-audit, 2026-05-16) |
| **Date** | May 2026 |
| **Team** | Franca & Ashinze |
| **Submission Target** | Nigerian AI Agents Hackathon (Tasks 1 + 2 + Paper + Repo) |
| **Concurrent Release** | arXiv preprint (cs.CL) + HuggingFace model + HuggingFace dataset |
| **Primary Domains** | Jumia/Konga e-commerce + Nollywood film |
| **Open-Source Commitment** | All code MIT; model Llama-3.1 Community License; dataset CC-BY-4.0 |
| **Status** | Approved for build — v3.1 supersedes v3.0 (pre-feature-audit), v2.0 (single-artifact), and v1.0 (Churn Intervention) |
| **v3.1 Additions** | 22 features added across 7 categories from a comprehensive feature audit on 2026-05-16. See **Appendix C — v3.1 Feature Audit & Additions** at end of document. |

> **Why v3.0 over v2.0.** v2.0 satisfied the hackathon brief but treated the submission as a single artifact. v3.0 commits to **four citable artifacts** — the agent system, an open-weight fine-tuned model, a public benchmark dataset, and an arXiv preprint — because we have the compute (Colab Pro+ + local Ollama), the open-source commitment, and the time to build them. The strategic move is to convert a hackathon submission into a research contribution that lives beyond the hackathon. The team's structural advantage — authentic Nigerian curation — compounds once attached to durable open artifacts that other teams structurally cannot replicate inside the build window.

---

## Table of Contents

1. Executive Summary
2. The Cultural Prior Thesis (problem statement, expanded)
3. Goals & Success Metrics
4. Target Users & Stakeholders
5. User Stories
6. System Architecture
7. Functional Requirements
8. Technical Architecture
9. Dataset Strategy
10. Fine-Tuning Recipe — *NaijaReviewer-8B*
11. NPA-Bench Release Plan
12. Evaluation Framework
13. Human Evaluation Protocol
14. Solution Paper Plan
15. arXiv Preprint Plan
16. Judge Demo UX
17. Reproducibility & Submission Plan
18. Non-Functional Requirements
19. Milestones & Timeline (8 weeks)
20. Business Applications (paper Section 7)
21. Risks & Mitigations
22. Out of Scope
23. Comparison: This System vs. Median Submissions
24. Document Approval
25. Appendix A — Glossary
26. Appendix B — Selected References
27. Appendix C — v3.1 Feature Audit & Additions

---

## 1. Executive Summary

The Naija Persona Agent (NPA) is a four-artifact submission to the Nigerian AI Agents Hackathon, designed to be the most defensible, most citable, and most Nigerian entry in the field. It satisfies all three required deliverables — Task 1 (review + rating generation), Task 2 (personalised recommendation), and the 4–8 page solution paper with reproducible code repository — and adds three publicly-released artifacts that make the contribution durable beyond hackathon week.

**Artifacts.**

1. **NPA system** — containerised application exposing two endpoints (`/simulate-review`, `/recommend`) plus supporting routes (`/elicit`, `/feedback`, `/health`, `/docs`, optional `/business/churn-intervention`). LangGraph orchestration; dynamic RAG; cognitive persona representation; cultural register module; cross-domain bridge between Jumia/Konga and Nollywood.
2. **NaijaReviewer-8B** — Llama 3.1 8B Instruct QLoRA fine-tuned on ~35k Nigerian-marker examples for persona-conditioned review generation. Released as open weights on HuggingFace under the Llama 3.1 Community License. Served locally via Ollama as the Task 1 backbone.
3. **NPA-Bench** — public benchmark of ~1,000 personas, ~5,000 (persona, product, target-rating, target-review) triples for Task 1 evaluation, and ~1,000 (persona, candidate-set, ground-truth) triples for Task 2 evaluation, across Jumia/Konga and Nollywood. Released on HuggingFace Datasets under CC-BY-4.0. First public benchmark for Nigerian-context agent evaluation.
4. **arXiv preprint** — co-submitted to arXiv (cs.CL) within one week of the hackathon paper. Same headline claim, slightly expanded methods and discussion sections. Citation-ready.

**The intellectual core.** We position cultural register as a missing architectural primitive for LLM agents. Vanilla agents — including frontier closed models — carry an implicit Western cultural prior that produces systematic miscalibration when deployed for non-Western users. We quantify this gap on Nigerian users, recover it with a small open-weight fine-tuned model and an explicit cultural register module, and release the benchmark instrument that lets the community measure it. The recovery generalises across two Nigerian domains via a cross-domain persona bridge — the novel architectural contribution.

**The strategic centrepiece.** NaijaReviewer-8B. A small fine-tuned open model that beats frontier closed models on Nigerian register fidelity and rating intensity is the kind of finding hackathon judges and academic reviewers both recognise — it is a clean, hard-to-replicate, citable artifact that takes weeks to produce from scratch and minutes to download once released. We frame the entire paper around it.

**What survives from v1 and v2.** All the Nigerian context work, the LangGraph + dynamic RAG + Claude + NocoDB stack, the cross-domain bridge, the cognitive persona decomposition, and the paper's Nigerian Case Study + Business Implications sections survive intact. v3 is additive — it adds fine-tuning, the benchmark, the arXiv preprint, and the human evaluation study on top of v2's architecture. The original v1 churn intervention work continues to live as Section 20 (Business Applications) and as the optional `/business/churn-intervention` demo endpoint.

---

## 2. The Cultural Prior Thesis (Problem Statement, Expanded)

### 2.1 The hidden assumption in agent training data

Frontier LLMs (GPT-4o, Claude Sonnet 4, Llama 3.1, Qwen 2.5) are pre-trained on corpora dominated by U.S./EU English. The agent frameworks built on top of them — AgentSociety, AgentCF, RecMind, MACF — inherit this distribution. The downstream consequence is that "vanilla LLM agent" really means "Western LLM agent." This is rarely stated explicitly because the systems are evaluated on Yelp / Amazon / Goodreads, which are also U.S.-dominant. The training distribution and the evaluation distribution agree, and the cultural prior stays invisible.

The 295 teams in WWW'25 AgentSociety Challenge optimised on this overlapping prior. The winners — USHB (Jiangnan), Renmin Collaborative Optimization, Tsinghua Adaptive Knowledge Fusion, the CAS Knowledge-Driven Framework — produced excellent systems for the data they were given. None of them addressed the cultural prior; they had no incentive to.

### 2.2 What the prior actually does

When you deploy a vanilla LLM agent on Nigerian users, the cultural prior produces measurable, systematic miscalibration:

- **Rating intensity is compressed.** Nigerian reviewers use 1-star and 5-star more frequently than U.S. baselines; the LLM smooths toward the middle, producing predicted ratings that under-shoot extreme reviews by 0.3–0.7 stars on average.
- **Register is flattened.** Pidgin English markers ("e shock me", "e too much", "no cap", "scatter scatter"), Nigerian English forms ("the food sweet die", "well done sir"), and code-mixing with Yorùbá/Hausa/Igbo ("ahn ahn", "wahala", "abeg") are smoothed into standard English. The output is grammatically correct and culturally hollow.
- **Framing is individualised.** Nigerian reviews carry communal framing ("we enjoyed", "my family loved", "even my mama was vibing"); vanilla agents produce individualist "I" framing.
- **Religious markers are misread.** "By God's grace", "Thank God", "Praise the Lord" are misclassified by vanilla sentiment classifiers as either neutral or off-topic.
- **Aspect priorities are wrong.** Party-jollof texture, Nollywood production-value cues, Afrobeats sub-genre awareness — none of these aspect vocabularies are in the vanilla agent's prior.

These are not cosmetic failures. They have structural downstream consequences:

- A persona representation derived from a vanilla agent is biased; every downstream task that consumes it inherits the bias.
- A recommendation system built on the biased persona will mis-recommend; users notice and disengage.
- A churn-prediction system trained on the biased persona will mis-segment users; retention budget is wasted on wrong targets.
- A credit-scoring system that uses persona features will systematically under-score Nigerian applicants; financial exclusion compounds.

The cultural prior is invisible until you build for the non-Western context. We make it visible, measure it, and recover it.

### 2.3 Why this matters beyond Nigeria

The Nigerian context is the empirical case study. The structural claim is broader: any LLM agent deployed for a market under-represented in the pre-training corpus inherits a cultural prior that requires explicit recovery. The framework we build — cognitive persona decomposition + cultural register module + cross-domain bridge + small fine-tuned model + public benchmark — is portable to any such market. Brazilian Portuguese reviewers, Indonesian Bahasa reviewers, Egyptian Arabic reviewers all face structurally analogous gaps. We do not solve those gaps in this work; we demonstrate the recovery method that generalises.

### 2.4 Quantified Nigerian backdrop

- **Nigerian telecom market**. 171.6M subscribers (NCC, August 2025). MTN ~52.3% / ~89.6M; Airtel ~33.9% / ~58M; Globacom ~12.2% / ~20.9M. ARPU ~$3.60. Annual churn 25–35%. Tariff hike of 50% in 2024 stabilised ARPU but did not solve churn.
- **Financial inclusion**. 64% of Nigerian adults financially included (EFInA 2023). Consumer credit ₦4.12T, ~3% of GDP.
- **MSME credit gap**. ₦130T (CBN, April 2026) / ~$236B (Stears). ~4% of Nigeria's 40M MSMEs have formal bank loans. Maximum lending rates frequently >30%.
- **Diaspora**. ~17M Nigerian-diaspora globally.
- **Digital review platforms**. Jumia (Pan-African e-commerce, founded Lagos 2012, ~3M active customers in Nigeria); Konga (Lagos-based, acquired by Zinox 2018); Showmax (multi-tier streaming, strong Nollywood catalogue); IROKO TV (Nollywood-first streaming, ~25M registered users globally).

These figures anchor the Business Applications section of the paper. They are not the task — they are what the task makes possible.

---

## 3. Goals & Success Metrics

### 3.1 Required hackathon deliverables

| Deliverable | Form | Target |
|---|---|---|
| Task 1 endpoint | Containerised API | RMSE < 0.65 on Nigerian-marker subset; RGM ≥ 0.88; BERTScore F1 ≥ 0.82; register-tier match ≥ 85% |
| Task 2 endpoint | Containerised API | Average HR ≥ 0.55 on Jumia/Konga; HR@5 ≥ 0.55 on Nollywood; cross-domain HR@5 ≥ 80% of in-domain |
| Solution paper | PDF | 6 pages (expandable to 8); 4 contributions named; 9-row ablation; 6 baselines |
| Code repository | GitHub link, MIT | Fresh-clone reproducibility test passes in < 10 min |

### 3.2 v3 artifact goals

| Artifact | Target |
|---|---|
| NaijaReviewer-8B | Beats GPT-4o on register-tier fidelity (Nigerian-marker subset) by ≥ 30 percentage points; beats GPT-4o on rating-intensity RMSE by ≥ 0.15; matches GPT-4o on BERTScore F1 within 0.02 |
| NPA-Bench | 1,000 personas, 5,000 Task-1 triples, 1,000 Task-2 triples, four-tier register distribution, two-domain coverage; HuggingFace download count ≥ 100 in first month |
| arXiv preprint | Submitted within 7 days of hackathon submission; format-clean; cited URL in paper |
| Judge demo URL | Public; loads in < 3s; 5 sample personas; side-by-side compare panel |
| Human evaluation | ≥ 30 raters, ≥ 600 paired-sample judgments, Fleiss-κ ≥ 0.4 (moderate agreement) |

### 3.3 The headline number (paper claim)

> *On the NPA-Bench Nigerian-marker subset, NaijaReviewer-8B (8B parameters, QLoRA-fine-tuned) outperforms GPT-4o (frontier closed model) on rating-intensity RMSE by 22.7% (0.61 vs 0.79), on register-tier fidelity by 38.4pp (89.2% vs 50.8%), and matches it on BERTScore F1 within 0.018 (0.831 vs 0.849). Combined with our cognitive persona decomposition and cross-domain bridge, this yields the first open-weight Nigerian agent system whose persona representation transfers from Jumia/Konga e-commerce to Nollywood recommendation with 87% retention of in-domain HR@5.*

*(Numbers are placeholders. Replace with actual results after Week 6 ablation runs.)*

---

## 4. Target Users & Stakeholders

### 4.1 Primary: hackathon judges (Nigerian panel)

The judges read the paper first, then attempt the code, then visit the demo URL. The artifact priority is set by their reading order:

1. **Paper**. The single strongest signal. 4 named contributions; ablation table; 6 baselines; honest limitations; quantified Nigerian-context bonus.
2. **Code repository**. README quick-start gets them to a working API in < 10 minutes. Make targets. Pinned deps. Fresh-clone tested.
3. **Demo URL**. Polished, Nigerian-vibed, side-by-side compare panel that lets them *feel* the cultural difference without reading code.
4. **Public artifacts** (model, dataset, arXiv). Discovered when they search the team's name — confirms the work is serious.

### 4.2 Secondary: open-source / research community

NaijaReviewer-8B and NPA-Bench are designed for community consumption. HuggingFace download counts and citation counts are the long-tail success signal. AfriSenti, NaijaSenti, SentiLeye, and Masakhane communities are direct stakeholders.

### 4.3 Tertiary: commercial buyers

The Business Applications section of the paper is read by potential funders, partners, and pilot clients:

- **Telcos**: MTN Nigeria, Airtel Nigeria, Globacom, 9mobile.
- **Fintechs**: Opay, Palmpay, Moniepoint, Kuda, FairMoney, Carbon, Renmoney.
- **Commerce**: Jumia, Konga, Selar, Bumpa.
- **Media**: Showmax, IROKO TV, Boomplay, Mdundo.
- **Banks**: Access, GTBank, UBA, Zenith.

The paper does not pitch them directly. It demonstrates the persona representation is real and the recovery is quantified. They self-route.

### 4.4 Quaternary: the team's own future

This submission is also a portfolio anchor for Franca and Ashinze. arXiv preprint + open-weight model + open benchmark create a citable record that compounds value over years.

---

## 5. User Stories

### 5.1 As a hackathon judge

- I clone the repo, run `make demo`, and a working API responds to `curl localhost:8000/simulate-review` within 10 minutes.
- I read the paper's abstract and the headline number is specific, quantified, and surprising.
- I open the demo URL and the five sample Nigerian personas feel authentic, not stereotyped.
- I click "compare with vanilla GPT-4" and see the difference in register and rating intensity side-by-side.
- I visit the HuggingFace model card and find a clean training recipe I can verify.

### 5.2 As a Nigerian researcher reading the arXiv preprint

- I find a benchmark I can use for my own work.
- I find a fine-tuned model I can download and run locally.
- I find a methodology section that is honest about limitations and reproducible.
- I find a citation block I can paste into BibTeX.

### 5.3 As a commercial buyer reading the Business Applications section

- I see specific Nigerian numbers (₦130T MSME gap, 25–35% telco churn, $3.60 ARPU) tied to specific use cases.
- I see how the persona representation maps to my problem (credit scoring, churn intervention, marketplace personalisation).
- I see the team's contact information and a clear next-step path.

### 5.4 As a contributor wanting to build on NPA-Bench

- I find a HuggingFace Datasets release with a clear schema.
- I find evaluation scripts in the repo I can run against my own model.
- I find a leaderboard template (HuggingFace Space) where I can submit results.

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
              │ Backbone:              │  │ Backbone:              │
              │  NaijaReviewer-8B      │  │  multi-source retrieval│
              │  (local, Ollama)       │  │  + MACF re-ranker      │
              │                        │  │  (Claude Sonnet 4 for  │
              │ Fallback:              │  │   re-ranker reasoning) │
              │  Claude Sonnet 4       │  │                        │
              │  (non-Nigerian path)   │  │ Fallback:              │
              │                        │  │  pure LightGCN if LLM  │
              │ Input:                 │  │  budget exhausted      │
              │   • persona            │  │                        │
              │   • product details    │  │ Input:                 │
              │                        │  │   • persona            │
              │ Output:                │  │   • candidate_set      │
              │   • star rating (1-5)  │  │   • domain             │
              │   • review text        │  │                        │
              │   • register tier      │  │ Output:                │
              │   • rationale          │  │   • ranked top-K       │
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

Two LangGraph workflows share the persona representation, the RAG store, the register classifier, and (some of) the LLM backbone. **The Task 1 generation backbone is NaijaReviewer-8B served locally via Ollama** — this is the v3 architectural change. Task 2 uses NaijaReviewer-8B for its self-consistency text generation and Claude Sonnet 4 for the MACF re-ranker reasoning (which benefits from frontier reasoning quality more than from cultural register fidelity).

### 6.2 Shared persona representation

The persona is the system's central abstraction. Schema:

```python
@dataclass
class Persona:
    # Identity (optional; can be anonymous)
    user_id: str | None
    demographics: dict | None       # age range, location, gender — never PII

    # Cognitive dimensions (6 — v3.1 added age_cohort)
    hedonic_utilitarian: float                # 0.0 utilitarian → 1.0 hedonic
    intensity_calibration: dict               # {"amazing": 4.7, "okay": 3.1, ...}
    communal_individual: float                # 0.0 individualist → 1.0 communal
    aspect_priority: dict[str, float]         # per-domain weighted vocabulary
    context_sensitivity: float                # variance under time/season/weekend
    age_cohort: Literal[                      # v3.1 added
        "gen_z",        # ~1997-2012; heavy code-mix, slang-dense
        "millennial",   # ~1981-1996; bilingual fluency, brand-aware
        "gen_x",        # ~1965-1980; measured Nigerian English
        "boomer",       # pre-1965; formal Nigerian English, low slang
    ]

    # v3.1 — Per-dimension uncertainty quantification
    dimension_confidence: dict[str, float]    # {"hedonic_utilitarian": 0.87, ...}

    # Cultural register
    register_tier: Literal[
        "standard_english",
        "nigerian_english",
        "nigerian_pidgin",
        "code_mixed",  # English + Yorùbá / Hausa / Igbo
    ]
    register_markers: list[str]
    register_confidence: float

    # v3.1 — Religious framing (parallel tier)
    religious_framing: Literal[
        "none",
        "christian",      # "by God's grace", "Praise the Lord", "Glory to God"
        "muslim",         # "Alhamdulillah", "Mashallah", "Inshallah", "Subhanallah"
        "traditional",    # "by my ancestors", regional traditional markers
    ]
    religious_marker_density: float           # 0.0 secular → 1.0 dense markers

    # v3.1 — Code-switching intensity (controllable at generation time)
    code_switch_intensity: float              # 0.0 none → 1.0 maximum

    # v3.1 — Diaspora vs. in-country
    diaspora: bool
    diaspora_region: Literal["uk", "us", "canada", "europe", "gulf", "other"] | None

    # v3.1 — Punctuation/emoji style profile
    punctuation_style: dict                   # {
                                              #   "exclamation_density": 0.12,
                                              #   "ellipsis_use": 0.04,
                                              #   "all_caps_emphasis": 0.08,
                                              #   "emoji_density": 0.03,
                                              #   "emoji_preferences": ["🔥", "💯", "🙏🏾"],
                                              # }

    # Domain-specific aspect priors
    domain_priors: dict[str, dict]

    # History anchors
    review_anchors: list[ReviewAnchor]

    # Provenance
    extraction_source: Literal["history", "elicitation", "synthetic"]
    extraction_timestamp: datetime
```

**v3.1 note**: the persona schema is the data backbone for nearly every claim in the paper. Adding six new fields (`age_cohort`, `dimension_confidence`, `religious_framing`, `religious_marker_density`, `code_switch_intensity`, `diaspora`, `diaspora_region`, `punctuation_style`) deepens the representation without breaking earlier code — all v3.0 consumers continue to work; the new fields are optional in extraction and surfaced when present.

Personas are extracted offline by a structured LLM pipeline for users with history (≥ 3 reviews). For cold-start users, a 3-question elicitation flow infers an initial persona seeded by any available text signal.

### 6.3 Cultural register module

A small fine-tuned classifier (XLM-RoBERTa-base + classification head; ~280M params; ~110MB) maps any text → register tier ∈ {standard_english, nigerian_english, nigerian_pidgin, code_mixed} with confidence ∈ [0, 1]. Trained on AfriSenti + NaijaSenti + SentiLeye + ~5k LLM-augmented synthetic examples using Lin et al. (2024) orthographic variation for Pidgin coverage. Calibrated via temperature scaling.

The module both **classifies** (for persona) and **detects markers** (for downstream conditioning). Marker examples per tier:

| Tier | Lexical markers | Syntactic markers |
|---|---|---|
| Standard English | "however", "I would recommend", "overall" | full conjugation, no copula drop |
| Nigerian English | "well done sir", "sharp sharp", "no shaking" | "sef", "now" sentence-final, "shey" |
| Nigerian Pidgin | "abeg", "no cap", "wahala", "e shock me", "scatter scatter" | "go", "dey", "be like say" |
| Code-mixed | "ahn ahn", "haba", "ah ah", "owambe", "japa" (Yoruba); "kai", "wallahi" (Hausa); "nna", "biko" (Igbo) | code-switch tag insertions |

### 6.4 Cross-domain bridge

The same persona produces both a Jumia electronics review and a Nollywood film review. The bridge is the function:

```
persona × jumia_aspects → persona × nollywood_aspects
```

Implementation: LLM-mediated aspect-vocabulary mapping with a fixed prompt template, run through Claude Sonnet 4 (reasoning matters more than cultural fidelity here, and the bridge is run once per persona, not per query — caching cost is amortised).

The bridge experiment is the paper's novel claim: how much of in-domain HR@5 on Nollywood does a Jumia-only persona recover, transferred through the bridge?

### 6.5 Dynamic RAG layer

Chroma in dev / Qdrant in production. Embeddings: BGE-M3 (multilingual, handles Pidgin/Yorùbá/Hausa/Igbo tokens reasonably). After every Task-1 or Task-2 query, the LangGraph workflow writes three documents back:

1. Resolved persona snapshot (timestamped, register-tagged).
2. Generated review or recommendation list.
3. Outcome signal (when feedback received).

Outcome-reinforced embeddings boost successful generations and decay failed ones.

### 6.6 Data flow (Task 1, v3)

```
Input: { persona: Persona, product: ProductDetail }
   │
   ▼
[1] LangGraph entry — load persona; resolve domain (jumia | nollywood)
   │
   ▼
[2] Retrieve via RAG — pull anchors:
       • user's most-similar prior reviews
       • product's representative reviews
       • register-tier exemplars from the corpus
   │
   ▼
[3] Style retrieval — user's most-extreme +/- past reviews in same category
   │
   ▼
[4] Stage A — Rating prediction (XGBoost regressor)
       Features: [5 cognitive dimensions, product embedding,
                  aspect-match score, user mean, similar-user
                  ratings, register marker, context]
       Output: predicted rating ∈ {1..5}
   │
   ▼
[5] Stage B — Text generation
       Backbone: NaijaReviewer-8B (local, Ollama)
       Prompt template selected by domain + register tier
       Conditioning:
         • predicted rating
         • full persona JSON
         • retrieved anchors (top-3)
         • product description
       Output: review text
   │
   ▼
[6] Self-consistency check
       Embedding similarity (generated, user corpus)
       If < τ: regenerate with stronger style anchoring
   │
   ▼
[7] Writeback — index (persona, product, review, rating) to RAG
   │
   ▼
Output: { rating, review_text, register_tier, rationale }
```

### 6.7 Data flow (Task 2, v3)

```
Input: { persona: Persona, candidate_set?: list[str], domain: str, k: int }
   │
   ▼
[1] LangGraph entry — load persona; resolve domain
   │
   ▼
[2] Multi-source parallel candidate retrieval (if candidate_set not given):
       • LightGCN (collaborative)
       • Content-similarity (product embedding)
       • Semantic (LLM zero-shot from textual persona priors)
       • Aspect-match (top-N items matching aspect-priority vector)
   │
   ▼
[3] Reciprocal Rank Fusion → unified candidate pool (K=50)
   │
   ▼
[4] Pre-ranking with external knowledge injection (Tsinghua AKF style)
       K(persona, item) combines item quality, popularity, average
       rating, and register-tier match
   │
   ▼
[5] MACF-style multi-agent re-ranker
       Instantiate similar-user agents and relevant-item agents
       (LLM: Claude Sonnet 4 for reasoning quality)
       Soft self-consistency aggregation across 5 traces
   │
   ▼
[6] Cold-start handler if persona.history_count < 3
       3-question elicitation flow, seeded by register inference
   │
   ▼
[7] Cross-domain bridge if persona.source_domain ≠ target_domain
       LLM-mediated aspect mapping; re-score top-N
   │
   ▼
[8] Writeback to RAG
   │
   ▼
Output: ranked list of top-K with rationale per item
```

### 6.8 Why the v3 backbone choice

| Component | Backbone | Rationale |
|---|---|---|
| Task 1 generation | NaijaReviewer-8B (local) | Register fidelity matters most; small fine-tuned model wins on register; cost is essentially zero (local Ollama) |
| Task 2 MACF re-ranker | Claude Sonnet 4 (API) | Reasoning quality matters most; cultural register fidelity less critical for ranking decisions; frontier model amortises cost across 5 traces |
| Cross-domain bridge | Claude Sonnet 4 (API) | Run once per persona; reasoning-heavy; amortised |
| Register classifier | XLM-R fine-tuned (local) | Fast, deterministic, calibrated |
| Persona extraction | Claude Sonnet 4 (API) | Run once per user offline; reasoning-heavy; one-time cost |
| Cold-start elicitation | NaijaReviewer-8B (local) | Quick interactive; cost-controlled |
| Embeddings | BGE-M3 (local) | Multilingual; covers Pidgin/Yorùbá/Hausa/Igbo |

This is the "right tool for each job" principle. The paper makes this explicit as a deployment-cost finding.

---

## 7. Functional Requirements

### 7.1 Persona Extraction Layer

- **FR-P1.** Given a user's review history (≥ 3 reviews), extract five cognitive dimensions + register tier + aspect priorities via a structured Claude Sonnet 4 pipeline. Output: serialisable `Persona` JSON.
- **FR-P2.** Given < 3 reviews, run a 3-question elicitation flow seeded by register inference from any available text.
- **FR-P3.** Extracted personas cached in NocoDB with 30-day TTL. Re-extraction on cache miss or explicit refresh.
- **FR-P4.** Persona schema versioned (`schema_version: "1.0"`). Migrations live in `app/data/persona_migrations.py`.

### 7.2 Cultural Register Module

- **FR-R1.** Trained classifier (`app/agents/register_classifier.py`) maps text → register tier ∈ {standard_english, nigerian_english, nigerian_pidgin, code_mixed} with calibrated confidence.
- **FR-R2.** Inference latency < 100ms per text on CPU.
- **FR-R3.** Marker extraction returns the specific tokens or phrases that triggered the tier classification, for downstream prompt conditioning.
- **FR-R4.** Model weights published to HuggingFace as `<team>/naija-register-classifier-xlmr-base`.

### 7.3 Task 1: Review & Rating Agent

- **FR-T1.1.** Accepts `{ persona: Persona, product: ProductDetail }`; returns `{ rating: int, review: str, register_tier: str, rationale: str }`.
- **FR-T1.2.** Rating predicted by separate Stage-A regressor before text generation (never joint).
- **FR-T1.3.** Text generation calls NaijaReviewer-8B via local Ollama. If Ollama unavailable, falls back to Claude Sonnet 4 with `fallback_reason` populated in rationale.
- **FR-T1.4.** Domain-specific prompt template selected at runtime (`jumia_v1.jinja`, `nollywood_v1.jinja`).
- **FR-T1.5.** Self-consistency check: regenerate once if embedding similarity to user corpus < τ.
- **FR-T1.6.** Every response ships a `rationale` field identifying ≥ 2 persona dimensions and ≥ 1 register marker that drove the output.
- **FR-T1.7.** OpenAPI / Swagger schema published at `/docs`.

### 7.4 Task 2: Recommendation Agent

- **FR-T2.1.** Accepts `{ persona: Persona, candidate_set?: list[str], domain?: "jumia" | "nollywood", k: int = 5 }`; returns `{ recommendations: list[RecItem] }`.
- **FR-T2.2.** If `candidate_set` omitted, runs full multi-source retrieval.
- **FR-T2.3.** Pre-ranking with external knowledge injection before LLM re-rank.
- **FR-T2.4.** MACF-style multi-agent re-ranker; 5-sample soft self-consistency.
- **FR-T2.5.** Cold-start branch when `persona.history_count < 3`; `/elicit` endpoint returns the 3-question flow.
- **FR-T2.6.** Cross-domain bridge auto-activates when `persona.source_domain ≠ domain`.
- **FR-T2.7.** *(v3.1)* **MMR diversity re-rank** after MACF re-ranker with λ=0.7; prevents top-K from being all-same-category.
- **FR-T2.8.** *(v3.1)* **Serendipity score** computed and surfaced per recommendation (cosine distance from user's primary interest centroid); items above τ flagged `serendipitous: True`.
- **FR-T2.9.** *(v3.1)* **Long-tail item floor** — at least 1 of top-5 must be from the bottom-60% popularity tier; combats popularity bias.
- **FR-T2.10.** *(v3.1)* **Time-aware conditioning** — when `persona.context_sensitivity > τ`, recommendations are conditioned on time-of-day, day-of-week, season, and post-paycheck cycle (Nigerian end-of-month effect).
- **FR-T2.11.** *(v3.1)* **Negative recommendations** — `include_negatives: bool` flag returns a ranked list of items the user would actively dislike, each with a per-item rationale.

### 7.5 Cross-Domain Bridge

- **FR-CB1.** `bridge(persona, source_domain, target_domain) -> Persona` — returns persona with `domain_priors[target_domain]` populated.
- **FR-CB2.** Uses LLM-mediated aspect mapping; fixed prompt template (`bridge_<src>_to_<tgt>.jinja`).
- **FR-CB3.** Bridged personas tagged `bridged: True` in rationale.

### 7.6 Dynamic RAG layer

- **FR-RAG1.** Embeds and writes back every persona snapshot, generated review, and recommendation after every query.
- **FR-RAG2.** Outcome reinforcement: feedback boosts/decays document embeddings.
- **FR-RAG3.** Stale documents (no reinforcement, > 18 months) demoted nightly.
- **FR-RAG4.** Metadata filters: domain, register tier, recency, demographic cluster.

### 7.7 Self-Consistency

- **FR-SC1.** Task 1: single-shot generation + one regeneration on style-check failure. Temperature 0.7.
- **FR-SC2.** Task 2: 5-sample soft self-consistency with summarisation aggregation. Temperature 0.4.

### 7.8 Feedback Loop

- **FR-FB1.** `POST /feedback` accepts `{ query_id, outcome }`.
- **FR-FB2.** Weekly n8n cron recomputes effectiveness weights.
- **FR-FB3.** Effectiveness changelog persisted, 24-month retention.

### 7.9 Business-Application Demo

- **FR-BD1.** Optional `POST /business/churn-intervention` accepts a Nigerian-telco subscriber persona; returns ranked intervention list using the same persona representation.
- **FR-BD2.** Behind feature flag (`--with-business-demo`). Not part of scored tasks.

---

## 8. Technical Architecture

### 8.1 Framework: LangGraph

Preserved from v1/v2. State graph with checkpointer (Postgres in production, SQLite in dev). Five reasons unchanged: stateful cyclical workflows; persistent state across runs; human-in-the-loop gates; observability via per-node traces; reuses LangChain ecosystem for utilities.

### 8.2 LLM Stack (v3 specific)

| Use case | Model | Serving | Cost |
|---|---|---|---|
| Task 1 review generation | NaijaReviewer-8B | Local Ollama (your access) | ~$0 marginal |
| Task 1 fallback | Claude Sonnet 4 | Anthropic API | ~$3/1M tokens |
| Task 2 MACF re-ranker | Claude Sonnet 4 | Anthropic API | ~$3/1M tokens |
| Cross-domain bridge | Claude Sonnet 4 | Anthropic API | one-off per persona |
| Persona extraction | Claude Sonnet 4 | Anthropic API | one-off per user |
| Register classifier | XLM-R fine-tuned (~280M) | Local CPU | ~$0 |
| Embeddings | BGE-M3 (~570M) | Local CPU/GPU | ~$0 |
| LightGCN | trained from scratch | Local | ~$0 |
| Benchmarking baselines | GPT-4o, GPT-4o-mini, Claude Haiku 4.5, base Llama 3.1 8B | API / local | Budget-capped |

**Total expected API budget for hackathon evaluation + paper experiments**: ~$100–150.

### 8.3 Container & API design

- **Single Dockerfile** + **docker-compose.yml** orchestrating: app + Ollama + Chroma/Qdrant + NocoDB + Postgres.
- **FastAPI** + **uvicorn**. Lazy LLM-client loading. Cold start < 30s.
- **Endpoints**: `/simulate-review`, `/recommend`, `/elicit`, `/feedback`, `/health`, `/docs`, optional `/business/churn-intervention`.
- **Pydantic** schemas → OpenAPI JSON.
- *(v3.1)* **Streaming**: both `/simulate-review` and `/recommend` accept `stream: bool` flag. Streaming responses use Server-Sent Events (SSE), token-by-token where possible, supports the judge demo's live render.
- *(v3.1)* **Per-request reasoning trace**: `include_reasoning: bool` flag returns the full LangGraph node-by-node execution trace as a structured `reasoning_trace` field. Each node entry includes `node_name`, `inputs`, `outputs`, `duration_ms`, `model_used`.
- *(v3.1)* **Batch endpoints**: `/simulate-reviews/batch` and `/recommend/batch` accept up to 100 requests per call; async with job ID + status polling endpoint `/jobs/{id}`.

### 8.4 Storage

- **NocoDB**: persona profiles, intervention library (v1 carry-forward), outcome log, model weights metadata.
- **Postgres**: LangGraph checkpointer.
- **Chroma (dev) / Qdrant (prod)**: vector index for dynamic RAG.
- **Local disk**: dataset shards, fine-tuned model weights, prompt templates.

### 8.5 Orchestration

- **n8n** (self-hosted): data ingestion, weekly reweighting cron.
- **LangGraph**: agent reasoning.

### 8.6 Observability

- LangSmith traces.
- MLflow for experiment tracking (mandatory).
- Loki + Grafana for production-style log inspection.

### 8.7 Frontend (judge demo)

- **Next.js 15** + **Tailwind CSS** + **shadcn/ui** + **Vercel AI SDK** for streaming responses.
- Hosted on Vercel free tier; sub-3s cold start.
- 5 Nigerian persona archetypes pre-loaded; side-by-side compare panel; streaming response render.

### 8.8 Deployment

- **Hackathon submission**: cloud-hosted on Render / Railway / Fly.io (free tier acceptable).
- **Production roadmap**: Nigeria data residency preferred; NDPR-compliant architecture; right-to-be-forgotten endpoint.

---

## 9. Dataset Strategy

### 9.1 Primary domain: Jumia/Konga

- **Source A — Iwendi et al. 2020.** Existing academic dataset, 30,382 cleaned reviews across Jumia/Jiji/Konga/Takealot. Cite. Anchor.
- **Source B — Fresh Jumia/Konga scrape.** ~20k additional reviews across 10 category trees (Electronics, Fashion, Beauty, Home & Office, Phone & Tablet, Health, Baby Products, Computing, Sports, Automobile). Rate-limited, respectful.
- **Total**: ~50k Jumia/Konga reviews.

### 9.2 Secondary domain: Nollywood

- **Source A — Letterboxd.** Filter for Nigerian user locale + Nollywood tag. ~3–5k reviews.
- **Source B — Twitter / Reddit / Instagram.** #Nollywood, r/Nollywood, IG comments on Nollywood promo posts. ~5–10k items.
- **Source C — Blog reviews.** Mira Mason-Reader, What Kept Me Up, NollywoodTV, Bella Naija film. ~1k long-form.
- **Source D — Showmax / IROKO TV catalogue.** Metadata only (films, casts, directors, summaries).
- **Total**: ~10k Nollywood reviews + ~5k catalogue items.

### 9.3 Cross-domain user subset

- Real cross-domain users are rare. Constructed via **persona-linked synthetic generation**:
  - Take ~500 real users with rich Jumia history.
  - Extract their persona.
  - Generate plausible Nollywood reviews conditioned on the persona.
  - Hand-validate a 100-sample subset against persona consistency.
- Persona-linked synthetic generation explicitly declared in paper. Not concealed augmentation.

### 9.4 Nigerian-marker construction

- AfriSenti + NaijaSenti classifier → register tier.
- SentiLeye lexicon → Pidgin marker count.
- Geographic + name markers (where available).
- Combined confidence ≥ 0.8 → tagged "Nigerian-marker".
- **Target**: ~15k Jumia + ~7k Nollywood reviews.

### 9.5 Synthetic data policy

- **Real data primary** wherever it exists.
- **Synthetic augmentation only** for: cross-domain user pairs, register-tier balancing (under-represented code-mixed), Section-20 churn demo (synthetic subscriber profiles).
- **All synthetic tagged** `synthetic: True`. Train/eval splits respect this — main evaluation runs on real-only subsets.
- **Generation grounding**: synthetic conditioned on real-distribution priors (rating histogram, register frequency, aspect priority).

### 9.6 Fine-tuning corpus construction (NaijaReviewer-8B)

Built specifically for QLoRA training (see Section 10):

- ~35,000 examples in instruction-tuning format.
- Each example: `{ instruction, input (persona + product), output (rating + review) }`.
- Composition: 80% real Nigerian-marker reviews, 20% register-balanced synthetic.
- Train / val / test split: 90 / 5 / 5.
- Held-out test set never seen during training; used for the headline paper number.
- Released as `<team>/naija-reviewer-train` on HuggingFace Datasets.

### 9.7 Repository artefacts

- `data/jumia_reviews/` + `data/nollywood_reviews/` + `data/personas/` + `data/synthetic/` (tagged) + `data/sample/` (judge-bundled small subset) + `data/finetune/` (NaijaReviewer training set).
- `data/README.md` documents every schema, source, and split.
- `scripts/build_dataset.sh` reproducible from raw sources to clean splits.

---

## 10. Fine-Tuning Recipe — NaijaReviewer-8B

### 10.1 Base model selection

**Llama 3.1 8B Instruct** as primary base.

| | |
|---|---|
| Why Llama 3.1 8B | Permissive Community License; Ollama-native; well-supported in HuggingFace ecosystem; widely cited; 8B is the sweet spot for register-fidelity tasks per recent research |
| Backup | Qwen 2.5 7B Instruct (Apache 2.0; sometimes stronger on multilingual register) |
| Considered and rejected | Mistral 7B (less Pidgin coverage in pre-training); Llama 3.1 70B (compute too steep for ablation iteration); Llama 3.1 8B *Base* (instruct gives better adherence to persona-conditioning) |

### 10.2 Method: QLoRA

- Quantisation: **4-bit NF4** via bitsandbytes.
- LoRA configuration: `r=16, α=32, dropout=0.1`.
- Target modules: attention (q, k, v, o) + MLP (gate, up, down).
- Trainable parameters: ~80M (~1% of base).
- Maximum context: 4,096 tokens (sufficient for persona JSON + product + retrieved anchors + target review).

### 10.3 Training data format

Each training example:

```json
{
  "instruction": "You are simulating the review behaviour of the following Nigerian user reviewing the described product. Generate the review text and a 1-5 star rating exactly as this user would write it. Match the user's register tier and cultural framing.",
  "input": {
    "persona": { ... full Persona JSON ... },
    "product": { ... product details ... },
    "register_tier": "nigerian_pidgin"
  },
  "output": {
    "rating": 4,
    "review": "Abeg, this phone good die. Battery dey last for 2 days straight, even with all my WhatsApp wahala. ..."
  }
}
```

### 10.4 Training hyperparameters

| | |
|---|---|
| Optimiser | AdamW 8-bit |
| Learning rate | 2e-4, cosine schedule, 100 warmup steps |
| Batch size | 4 per device, gradient accumulation 8 → effective 32 |
| Epochs | 3 (early stopping on val loss plateau) |
| Max seq length | 4,096 |
| Mixed precision | bfloat16 |
| Random seed | 42 (set everywhere) |

### 10.5 Compute plan

- **Hardware**: Colab Pro+ A100 40GB (your access) + HuggingFace AutoTrain fallback.
- **Time**: ~10–15 hours per full training run; ~30–50 hours total across v1 + v2 + final.
- **Cost**: $0 marginal on Colab Pro+ subscription.
- **Memory**: 4-bit QLoRA fits 8B comfortably on 40GB.

### 10.6 Auxiliary multi-task head (optional, Week 4–5 stretch)

- Add a regression head on the rating prediction.
- Joint loss: `L = L_LM(review) + λ × L_MSE(rating)` with λ ≈ 0.3.
- Goal: tighten rating accuracy without sacrificing review quality.

### 10.7 Iteration plan

- **NaijaReviewer-8B v0.1** (Week 3): trained on Jumia/Konga only. Establishes baseline.
- **NaijaReviewer-8B v0.2** (Week 4): adds Nollywood data. Tests cross-domain transfer.
- **NaijaReviewer-8B v1.0** (Week 5): full corpus, multi-task head, calibrated. Release candidate.

### 10.8 Evaluation (head-to-head)

On the NPA-Bench Nigerian-marker held-out test set:

| Model | RMSE ↓ | BERTScore ↑ | RGM ↑ | Register match ↑ | Cultural-marker recall ↑ |
|---|---|---|---|---|---|
| Vanilla concat-history (Claude Sonnet 4) | | | | | |
| GPT-4o zero-shot | | | | | |
| GPT-4o-mini zero-shot | | | | | |
| Claude Sonnet 4 zero-shot | | | | | |
| Claude Haiku 4.5 zero-shot | | | | | |
| Base Llama 3.1 8B Instruct (no fine-tune) | | | | | |
| **NaijaReviewer-8B (ours)** | | | | | |

Run 3 seeds per row. Report mean ± std. This table is paper Figure / Table headline.

### 10.9 Open-source release

- **Model card** following HuggingFace template.
  - Intended use.
  - Out-of-scope use.
  - Bias and limitations (with explicit acknowledgment of "Lost in Simulation" caveats).
  - Training data documented (links to NPA-Bench).
  - Carbon footprint estimate.
  - License: Llama 3.1 Community License.
- **Citation block** ready for BibTeX.
- **Reproducibility**: training script + config + dataset version pin published.
- **Quantised variants**: GGUF Q4_K_M + Q5_K_M + Q8 for Ollama compatibility.

### 10.10 Naming

- Repo: `<team>/naija-reviewer-8b`
- Variants: `naija-reviewer-8b-instruct`, `naija-reviewer-8b-instruct-gguf`

---

## 11. NPA-Bench Release Plan

### 11.1 Motivation

There is no public benchmark for measuring cultural fidelity of LLM agents on Nigerian users. Without one, the gap recovery claim cannot be replicated. NPA-Bench fills this gap and becomes the citation point for future Nigerian-context agent work.

### 11.2 Composition

| Component | Size | Source |
|---|---|---|
| Personas | 1,000 | Extracted from real Jumia/Konga + Nollywood users with rich review history; demographic + register tier balanced |
| Task-1 triples (review + rating) | 5,000 | (persona, product, target rating, target review). Held-out from training data |
| Task-2 triples (recommendation) | 1,000 | (persona, candidate set of 20, ground-truth positive). 1 positive + 19 negatives per item |
| Cross-domain triples | 200 | Personas with reviews in both Jumia and Nollywood; persona-linked synthetic, tagged |
| Cold-start triples | 300 | Personas with < 3 reviews; for cold-start evaluation |
| Nigerian-marker subset | 1,500 | High-confidence Nigerian register; the headline cultural-gap subset |

### 11.3 Splits

| Split | Use |
|---|---|
| `train` | Available for fine-tuning baselines (not used for our NaijaReviewer training — that uses a separate corpus) |
| `validation` | Hyperparameter tuning, ablation iteration |
| `test` | Headline reported numbers; never seen during training |
| `nigerian_marker_test` | Subset of test split; cultural-gap headline experiment |

Splits stratified by domain, register tier, and product category.

### 11.4 Schema (HuggingFace Datasets format)

```python
features = {
    "id": Value("string"),
    "split": ClassLabel(["train", "validation", "test", "nigerian_marker_test"]),
    "domain": ClassLabel(["jumia", "nollywood"]),
    "task": ClassLabel(["review_generation", "recommendation"]),
    "persona": {
        "user_id": Value("string"),
        "demographics": {...},
        "cognitive_dimensions": {...},
        "register_tier": ClassLabel([...]),
        "register_markers": Sequence(Value("string")),
        "aspect_priority": {...},
        "history_anchors": Sequence({...}),
        "extraction_source": ClassLabel([...]),
    },
    "product": {
        "product_id": Value("string"),
        "title": Value("string"),
        "category": Value("string"),
        "description": Value("string"),
        "metadata": {...},
    },
    "target": {
        # For review_generation:
        "rating": Value("int32"),
        "review_text": Value("string"),
        # For recommendation:
        "candidate_set": Sequence(Value("string")),
        "ground_truth_id": Value("string"),
    },
    "synthetic": Value("bool"),
    "provenance": Value("string"),
}
```

### 11.5 Quality assurance

- **Inter-annotator agreement** on register tier (subset of 200 items) — Fleiss-κ reported.
- **Synthetic items flagged** with `synthetic: True`; main eval excludes them; ablation experiments include them with explicit toggle.
- **Nigerian-marker confidence** documented per item.

### 11.6 Release format

- HuggingFace Datasets repo: `<team>/npa-bench`
- License: **CC-BY-4.0** (attribution required; commercial use permitted)
- Dataset card with:
  - Motivation, composition, recommended uses, social impact, biases, limitations.
  - Citation block.
- Companion HuggingFace Space hosting a starter notebook and a leaderboard scaffold.

### 11.7 Leaderboard (optional Week 8 stretch)

- Simple HuggingFace Space + Streamlit / Gradio.
- Submission via PR with model card pointing at HuggingFace model + JSON results.
- Auto-eval pipeline (community can submit; we run scripts; results posted).
- Initial entries: NaijaReviewer-8B + GPT-4o + Claude Sonnet 4 + Base Llama 3.1 8B + Vanilla baseline.

### 11.8 Naming and identifiers

- `<team>/npa-bench` on HuggingFace.
- DOI via Zenodo for archival citation.

---

## 12. Evaluation Framework

### 12.1 Task 1 metrics

| Metric | Definition | Target |
|---|---|---|
| **RMSE (rating)** | √( Σ (predicted − actual)² / N ) | < 0.65 |
| **MAE (rating)** | Σ |predicted − actual| / N | < 0.50 |
| **BERTScore F1** | precision/recall over BERT embeddings | ≥ 0.82 |
| **RGM** | USHB formula: 1 − (0.25 ETE + 0.25 SAE + 0.5 TRE) | ≥ 0.88 |
| **Register-tier match** | predicted == ground truth | ≥ 85% |
| **Cultural-marker recall** | fraction of ground-truth Pidgin/Nigerian markers in generated text | ≥ 65% on Nigerian-marker subset |

### 12.2 Task 2 metrics

| Metric | Definition | Target |
|---|---|---|
| **HR@1, HR@3, HR@5** | fraction where ground truth at rank ≤ k | HR@5 ≥ 0.75 |
| **Average HR** | mean of HR@1/3/5 | ≥ 0.55 |
| **NDCG@5** | discounted cumulative gain | ≥ 0.65 |
| **Cross-domain HR@5** | Nollywood HR@5 using Jumia-only persona | ≥ 0.80 × in-domain |
| **Cold-start HR@5** | persona with < 3 reviews | beat zero-shot LLM by ≥ 10pp |

### 12.3 Mandatory ablation table

All on Nigerian-marker subset, 3 seeds, mean ± std:

| Configuration | RMSE ↓ | RGM ↑ | HR@5 ↑ |
|---|---|---|---|
| **Full NPA + NaijaReviewer-8B** | | | |
| − NaijaReviewer-8B (use Claude Sonnet 4 backbone instead) | | | |
| − No cognitive dimensions (history-paste only) | | | |
| − No register module | | | |
| − No two-stage rating | | | |
| − No domain-specific templates | | | |
| − No self-consistency | | | |
| − No cross-domain bridge | | | |
| − No external-knowledge pre-ranking | | | |
| − No outcome-reinforced RAG | | | |
| − **Headline:** Vanilla LLM (Claude zero-shot + history paste) | | | |

### 12.4 Mandatory baselines

| Baseline | Description |
|---|---|
| Vanilla GPT-4o | zero-shot + concat history |
| Vanilla GPT-4o-mini | zero-shot + concat history |
| Vanilla Claude Sonnet 4 | zero-shot + concat history |
| Vanilla Claude Haiku 4.5 | zero-shot + concat history |
| Base Llama 3.1 8B Instruct | no fine-tune |
| USHB-style | reimplementation of WWW '25 USHB on Jumia/Konga |
| Tsinghua Adaptive Knowledge Fusion | reimplementation on Jumia/Konga |
| LightGCN | pure CF for Task 2 |
| AgentCF++ | lightweight port |

### 12.5 Cross-domain transfer experiment

- Train persona extractor on Jumia only.
- Apply cross-domain bridge → Nollywood persona priors.
- Run Task 2 Nollywood recommendation.
- Compare HR@5 to in-domain Nollywood persona.
- Report the transfer ratio.

### 12.6 Cultural-gap recovery experiment (paper headline)

1. Vanilla baseline on Nigerian-marker subset → record errors.
2. NPA full + NaijaReviewer-8B → record errors.
3. **Gap recovery = baseline error − NPA error**.

Targets: ≥ 0.20-star rating-intensity recovery; ≥ 30% RGM lift; ≥ 35pp register-tier match lift.

### 12.7 *(v3.1)* LLM-as-judge cultural authenticity grading

GPT-4o is used as a blind judge scoring every Task-1 output on a 1–5 Likert scale against the prompt *"Does this read as if a real Nigerian wrote it?"* The judge is blind to whether the output came from a baseline or NPA. Run on the full Nigerian-marker test split.

- Compared to the human-evaluation Likert scores from Section 13 — Pearson correlation reported.
- Automated; scales to the full test set; serves as the high-N companion to the lower-N human eval.
- Implemented in `benchmark/llm_judge.py` with a fixed rubric prompt logged in `paper/prompts/`.

### 12.8 *(v3.1)* Statistical significance testing

All baseline comparisons report:

- **Paired bootstrap 95% CI** (10,000 resamples) for each metric.
- **Paired t-test** p-values, Bonferroni-corrected for multiple comparisons across the baseline grid.
- **Cliff's δ** as a non-parametric effect-size measure.

Tables in the paper carry `*`/`**`/`***` significance markers per cell. Numbers without statistical significance footnoted explicitly.

### 12.9 *(v3.1)* Calibration plots

For every model in the head-to-head comparison:

- **Predicted-rating histogram** overlaid on ground-truth-rating histogram on the Nigerian-marker subset (Figure 6).
- **Reliability diagram** binning by predicted rating, plotting actual rating means with 95% CI per bin (Figure 7).

These visualise the *rating intensity* recovery claim directly — vanilla baselines collapse to the middle; NaijaReviewer-8B should bimodal-track the Nigerian distribution.

### 12.10 *(v3.1)* Robustness probes

Adversarial input perturbations evaluated on a 1,000-sample subset:

| Probe | Perturbation | Expected behaviour |
|---|---|---|
| Typos | inject character-level typos at 5% rate | < 10% metric degradation |
| Word-order | shuffle 3-word windows in product description | < 15% degradation |
| Register mixing | mix Pidgin + standard in persona history | classifier still picks dominant register |
| Marker drop | strip register markers from persona | tier defaults to `nigerian_english`; outputs degrade gracefully |
| Cross-domain leakage | Jumia persona + Nollywood product | bridge activates; rationale notes `bridged: True` |

Results reported in paper as a robustness column in Table 4.

### 12.11 *(v3.1)* Bias audit

Single paper section measuring potential demographic biases in NPA outputs:

- **Gender bias**: do reviews for female-coded products (cosmetics, baby) vs. male-coded (consoles, tools) differ in rating intensity or register beyond what personas justify?
- **Region/tribe bias**: do recommendations differ systematically between Yoruba-marker, Hausa-marker, Igbo-marker personas after controlling for cognitive dimensions?
- **Religious bias**: are Muslim-coded personas treated equally to Christian-coded personas on identical products?
- **Diaspora vs. in-country**: do diaspora personas receive systematically different recommendations from in-country personas with otherwise identical profiles?

Implementation: counterfactual probing on a held-out 500-persona subset where one demographic field is swapped while everything else is held constant. Statistical tests reported.

---

## 13. Human Evaluation Protocol

### 13.1 Why

LLM-based automatic metrics (BERTScore, RGM) are correlative, not absolute. Human judgment is the gold standard for cultural fidelity. The "Lost in Simulation" critique (arXiv:2601.17087) is the explicit motivation: we cite it and run human eval to address it.

### 13.2 Recruitment

- **Target**: 30–50 Nigerian raters.
- **Channels**: Twitter call, university communities (UNILAG, UI, ABU, OAU), Slack/Discord Nigerian tech groups, diaspora Slack channels, family / friends network.
- **Inclusion**: native or near-native Nigerian English; lived in Nigeria ≥ 5 years; ≥ 18 years old.
- **Honorarium**: ₦5,000 (~$3) per rater via Paystack or direct bank transfer. Total budget: ~₦250,000 (~$165).

### 13.3 Protocol

- **Paired samples**: each rater sees 20 paired samples. Pair = (vanilla GPT-4o output, NaijaReviewer-8B output) on same persona + product, blinded order.
- **Three judgments per pair** on 5-point Likert:
  1. *"Does this sound like a Nigerian wrote it?"*
  2. *"Is the rating reasonable given the review text?"*
  3. *"Is the cultural register appropriate for the product context?"*
- **Implementation**: Streamlit / Gradio web form, sent via SurveyMonkey or Tally.so.
- **Estimated time per rater**: 20–30 minutes.
- **Total judgments**: 30 raters × 20 pairs × 3 questions = 1,800 judgments.

### 13.4 Analysis

- **Mean Likert per condition** with bootstrap 95% CI.
- **Fleiss-κ** for inter-rater agreement on the "sounds Nigerian" question (target ≥ 0.4 — moderate agreement).
- **Win rate**: fraction of pairs where NaijaReviewer-8B beats vanilla GPT-4o on each axis.
- **Qualitative themes**: open-ended comments coded for recurring critiques.

### 13.5 Ethics

- **Informed consent** at form intro. No PII collected beyond email for honorarium payout.
- **Anonymisation** of all rater identifiers in published data.
- **Opt-out** at any time.
- **Data retention**: 12 months, then purged.

### 13.6 Result reporting

- Paper Table 7: human-eval headline win-rates.
- Paper Figure 5: qualitative themes from open-ended comments.
- Appendix: full rater protocol + form template + ethics statement.

---

## 14. Solution Paper Plan

### 14.1 Target

- **Length**: 6 pages (extensible to 8 with appendix). Two-column ACM/IEEE style.
- **Title (working)**: "The Cultural Prior in LLM Agents: A Case Study and Open-Source Recovery for Nigerian User Modelling and Recommendation."
- **Authors**: Franca and Ashinze.

### 14.2 Section structure (6 pages)

1. **Abstract** (150 words) — cultural prior + 4 contributions + headline number.
2. **Introduction** (¾ page) — motivate cultural prior; preview contributions; commit to headline.
3. **Related Work** (¾ page, 5 paragraphs) — LLM user simulation (AgentCF, AgentCF++, RecAgent, Agent4Rec); LLM recommendation (P5, TALLRec, RecMind, MACF); AgentSociety winners; Cold-Start LLM (Netflix WWW '26); Nigerian NLP (AfriSenti, NaijaSenti, SentiLeye, Lin 2024).
4. **Method** (1¾ pages) —
   - 4.1 Cognitive dimensions (formal definitions).
   - 4.2 Cultural register module (training data, architecture, calibration).
   - 4.3 NaijaReviewer-8B fine-tuning recipe.
   - 4.4 Task 1 two-stage rating-text pipeline.
   - 4.5 Task 2 multi-source retrieval + MACF re-ranker.
   - 4.6 Cross-domain bridge.
5. **NPA-Bench** (½ page) — *distinctive*. Construction, schema, release.
6. **Experiments** (1¼ pages) — datasets, baselines, main results (Tables 2–3); ablation (Table 4); cross-domain transfer (Table 5); cold-start; register fidelity; human evaluation (Table 7); qualitative examples (Figure 4).
7. **Business Implications** (½ page) — telco churn intervention, MSME credit scoring, marketplace personalisation. Quantified Nigerian backdrop.
8. **Limitations** (¼ page) — cite "Lost in Simulation"; acknowledge LLM-simulated divergence; sample size; synthetic-data caveats; English/Pidgin focus (no Yoruba/Igbo/Hausa generation).
9. **Conclusion** (¼ page).

### 14.3 Required tables and figures

| # | Type | Content |
|---|---|---|
| Table 1 | Dataset composition | Sources, sizes, register distribution |
| Table 2 | Task 1 main results | NPA+NaijaReviewer vs. 7 baselines |
| Table 3 | Task 2 main results | NPA vs. 5 baselines |
| Table 4 | Ablation | 10 rows |
| Table 5 | Cross-domain transfer | in-domain vs. cross-domain HR@5 |
| Table 6 | Register fidelity | tier-match by configuration |
| Table 7 | Human evaluation | Likert means + win rates |
| Figure 1 | Architecture | Section 6.1 schematic |
| Figure 2 | Persona schema | with annotated example |
| Figure 3 | Cross-domain bridge mechanism | aspect-mapping diagram |
| Figure 4 | Qualitative comparison | 4 side-by-side (vanilla vs. NaijaReviewer) |
| Figure 5 | Human eval themes | bar plot |

### 14.4 *(v3.1)* Pre-registration of hypotheses

Before running the final ablation suite (Week 6), we publicly commit to:

- **H1**: NaijaReviewer-8B reduces Nigerian rating-intensity RMSE by ≥ 15% vs GPT-4o.
- **H2**: NaijaReviewer-8B improves register-tier fidelity by ≥ 20pp vs GPT-4o.
- **H3**: Cross-domain persona bridge retains ≥ 75% of in-domain HR@5 on Nollywood from Jumia-only personas.
- **H4**: Per-dimension cognitive persona representation outperforms history-paste on RMSE and RGM jointly.
- **H5**: The register module is the single largest contributor (by ablation Δ) to RGM on the Nigerian-marker subset.

Pre-registration is timestamped in a public Gist or in the paper's GitHub repo before final eval runs. Whether H1–H5 hold or not is reported honestly — failed hypotheses still earn paper credit for transparency.

### 14.5 *(v3.1)* Failure analysis section (Section 7 of paper)

Explicit subsection in Experiments documenting where NPA breaks. Target three failure modes:

- **Persona × product mismatch**: e.g., conservative Boomer Hausa persona reviewing party-jollof or club-wear → register defaults oddly.
- **Register interference**: persona registered as Pidgin but generating about technical electronics → output collapses to standard English.
- **Cold-start with sparse signal**: < 3 reviews + ambiguous demographic → cognitive dimensions noisy → recommendations regress to popularity baseline.

Each failure mode illustrated with 1–2 example outputs, root-cause analysed, and proposed fix flagged for future work. Self-aware research signals depth to judges.

### 14.6 *(v3.1)* Case study deep-dives (Appendix in paper)

Four personas walked through end-to-end with annotated outputs:

1. **Chinwe (Owerri Gen-Z, code-mixed Igbo+English, communal-hedonic, Afrobeats fan)** — reviewing Tecno phone + recommending Nollywood films.
2. **Tunde (Lagos market trader, Pidgin-heavy, utilitarian, high-intensity)** — reviewing cosmetics he sells + recommending wholesale products.
3. **Aisha (Kano teacher, measured Nigerian English, Muslim framing, mid-intensity)** — reviewing household goods + recommending educational books.
4. **Femi (Abuja banker, standard Nigerian English, low-intensity, hedonic-individualist)** — reviewing premium electronics + recommending Nollywood epic-historical films.

Each deep-dive shows: the persona JSON; the model's reasoning trace; the generated output; comparison to vanilla GPT-4o; commentary on what the cognitive dimensions and register module contributed.

### 14.7 *(v3.1)* Carbon footprint disclosure

Per HuggingFace model-card requirements + good practice:

- Training compute: A100 40GB × ~40 hours total across v0.1 → v1.0 = ~960 GPU-watt-hours = ~0.96 kWh.
- Region: Colab data centre (Iowa / Singapore — to be confirmed).
- gCO₂ per kWh (regional average): ~400 g/kWh.
- **Total estimated carbon**: ~0.4 kg CO₂eq for fine-tuning.
- Inference: per-request ~50 mJ on local Ollama (negligible at hackathon scale).

Reported in paper Section 8 (Limitations / Ethics) and in the model card.

### 14.8 *(v3.1)* Comparison to existing African / Nigerian AI work

Related Work paragraph specifically positions NPA against:

- **AfriBERTa** (Ogueji et al.) — multilingual African language model. NPA differs: focused on English+Pidgin register and persona-conditioned generation, not language modelling.
- **Masakhane** — community-driven African NLP. NPA differs: agent system over CLI/library; explicit cultural register primitive.
- **LELAPA AI** — South-African foundation-model lab; Vulavula API for African languages. NPA differs: open weights for a Nigerian-context user simulator, not a general-purpose African model.
- **AfroLLM / NaijaBERT / NaijaGPT** — Nigerian-context attempts; NPA differs: focuses on persona representation + cultural register module as architectural primitives, not just a Nigerian-data-finetuned base model.
- **AI4D Africa** — research network. NPA differs: hackathon-paced concrete artifact release.

This positioning gives Nigerian/African research community context and forestalls the "did you check existing work?" reviewer critique.

### 14.9 Headline claim (single sentence to repeat across abstract / intro / conclusion)

> *We define the cultural register as a missing architectural primitive for LLM agents and demonstrate that a small fine-tuned model (NaijaReviewer-8B, 8B parameters, QLoRA) recovers 38pp of register fidelity and 23% of rating-intensity error against GPT-4o on Nigerian users, while a cross-domain persona bridge transfers 87% of in-domain HR@5 from Jumia/Konga e-commerce to Nollywood film recommendation. All artifacts — model, benchmark (NPA-Bench), and code — released under open licenses.*

---

## 15. arXiv Preprint Plan

### 15.1 Scope

The arXiv preprint **is the hackathon paper** with three additions:

- Extended Related Work (1 paragraph longer per sub-area).
- Appendix with full prompt templates, training hyperparameters, dataset card.
- Acknowledgments (hackathon, AfriSenti / NaijaSenti / Masakhane / SentiLeye communities).

### 15.2 Submission

- **Track**: cs.CL (Computation and Language). Cross-list: cs.IR (Information Retrieval), cs.HC (Human-Computer Interaction).
- **License**: CC-BY-4.0.
- **Submission window**: within 7 days of hackathon submission. Earlier preferred — arXiv stamp predates hackathon results, signals seriousness.

### 15.3 Pre-announcement amplification

- **Tweet thread** (10 tweets): problem, contributions, headline number, links to model + benchmark + paper + repo.
- **LinkedIn post**: Nigerian / African AI community framing; team intro; call for collaboration.
- **Hacker News submission**: ShowHN. Tone: "we built a Nigerian-context agent and open-sourced the model + benchmark".
- **Mailing lists**: AfriCAI, Masakhane, Africa Deep Learning Indaba mailing list.
- **Reddit**: r/MachineLearning, r/Nigeria, r/Nollywood.

### 15.4 Citation block (ready for community)

```bibtex
@article{<team>2026npa,
  title={The Cultural Prior in LLM Agents: A Case Study and Open-Source Recovery for Nigerian User Modelling and Recommendation},
  author={Ifeanyi, Ashinze and ... and ...},
  journal={arXiv preprint arXiv:2606.XXXXX},
  year={2026}
}
```

### 15.5 Long-tail goals

- 100+ arXiv downloads in first month.
- 100+ HuggingFace model downloads in first month.
- 1+ external citation within 6 months (industry blog, academic paper, or Twitter mention from a notable researcher).
- Invited talk at one of: Deep Learning Indaba 2026, Lagos AI Summit, EkoExcel, MTN HQ AI Forum.

---

## 16. Judge Demo UX

### 16.1 Architecture

- **Frontend**: Next.js 15 (App Router) + Tailwind CSS + shadcn/ui.
- **Hosting**: Vercel free tier; subdomain `npa.<team>.dev` or similar.
- **Backend**: hits the same FastAPI container deployed on Render / Fly.io.
- **Streaming**: Vercel AI SDK for token-by-token rendering.

### 16.2 Pages

1. **Landing** — one-paragraph what-this-is; the headline claim; CTA "Try a persona".
2. **Persona Gallery** — five archetypes:
   - *Chinwe* — Owerri university student, Igbo + English code-mixing, hedonic, communal, Afrobeats + Nollywood superfan.
   - *Tunde* — Lagos market trader, Pidgin-heavy, high-intensity calibration, utilitarian, mobile electronics + cosmetics.
   - *Aisha* — Kano teacher, measured Nigerian English, mid-intensity, family-budget-aware household goods.
   - *Femi* — Abuja banker, standard Nigerian English, low-intensity calibration, premium electronics + business books.
   - *Ifeoma* — Port Harcourt Nollywood superfan, Nigerian English with film vocabulary, communal framing, Nollywood ratings.
   Each archetype: portrait illustration (Nigerian artist commission — small budget), bio, sample reviews.
3. **Try-It-Live** — pick persona → pick product (Jumia or Nollywood) → click "Generate Review". Streaming token-by-token render. Below, the same input rendered by vanilla GPT-4o for compare. Highlights register markers + cognitive dimensions used.
4. **Recommend** — pick persona → click "Recommend products" → ranked list with rationale per item.
5. **Architecture** — diagram + brief explanation. Links to paper + repo + HuggingFace.
6. **Contact** — team intro; ask-us-anything.

### 16.2a *(v3.1)* Additional interactive features

- **Interactive persona builder**. Page where judges construct their own Nigerian persona via dropdowns (age cohort, region, religion, register tier, code-switching intensity slider, aspect priority sliders, history-length toggle). Click "generate" → run both Task 1 and Task 2 on that custom persona. The output reveals how the persona structure drives the agent — *judges feel the architecture* by playing with it.
- **"Watch the agent think" reasoning trace viewer**. For any generation, judges can toggle the trace panel and see the LangGraph nodes execute one by one with intermediate outputs (persona resolution → retrieval → rating prediction → text generation → self-consistency check → writeback). Streamed live. Demonstrates transparency and technical depth that vanilla-LLM submissions cannot show.
- **Stress test mode**. A toggle that lets judges try adversarial inputs (typos, register-conflicting personas, edge-case products) and see how gracefully the system degrades.
- **Press kit / one-pager PDF** downloadable from the demo footer — headline claim, architecture diagram, links to all four artifacts. For judges who want to share the work.

### 16.3 Vibe

- Nigerian, not generic. Subtle use of green / white / green palette accents. Naija-themed example products. Real Nigerian Pidgin in sample outputs. No emojis (per house style); rich typography.
- Loads under 3 seconds. Generates token-by-token. The compare panel reveals the cultural gap visually — the visceral moment.

### 16.4 Why this matters for judges

The paper proves the cultural gap statistically. The demo lets judges *feel* it in real time. Two of the three judging artifacts (paper, repo, demo) are intellectual; this one is emotional. We need the emotional moment.

---

## 17. Reproducibility & Submission Plan

### 17.1 Repository structure

```
naija-persona-agent/
├── README.md                       # judge-facing quick start
├── LICENSE                         # MIT
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml                  # pinned deps
├── poetry.lock
├── Makefile
├── .env.example
├── .github/workflows/
│   └── ci.yml                      # lint + tests + container build
├── app/
│   ├── api/
│   │   ├── main.py
│   │   ├── routers/
│   │   │   ├── simulate_review.py
│   │   │   ├── recommend.py
│   │   │   ├── elicit.py
│   │   │   ├── feedback.py
│   │   │   └── business_demo.py    # optional flag
│   │   └── schemas/
│   ├── agents/
│   │   ├── persona_extractor.py
│   │   ├── register_classifier.py
│   │   ├── review_agent.py
│   │   ├── recommendation_agent.py
│   │   ├── cross_domain_bridge.py
│   │   └── macf_reranker.py
│   ├── graphs/
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
│   │   └── client.py               # Ollama + Claude + OpenAI abstraction
│   └── prompts/
│       ├── jumia_v1.jinja
│       ├── nollywood_v1.jinja
│       ├── bridge_jumia_to_nollywood.jinja
│       └── bridge_nollywood_to_jumia.jinja
├── data/
│   ├── README.md
│   ├── jumia_reviews/
│   ├── nollywood_reviews/
│   ├── personas/
│   ├── synthetic/
│   ├── finetune/                   # NaijaReviewer training corpus
│   └── sample/                     # judge-bundled small subset
├── finetuning/
│   ├── train_naija_reviewer.py
│   ├── train_register_classifier.py
│   ├── configs/
│   │   ├── naija_reviewer_qlora.yaml
│   │   └── register_xlmr.yaml
│   ├── eval_naija_reviewer.py
│   └── README.md                   # reproduce the fine-tune from scratch
├── benchmark/
│   ├── build_npa_bench.py
│   ├── eval_runner.py
│   ├── leaderboard/                # HF Space template
│   └── README.md
├── frontend/                       # Next.js judge demo
│   ├── app/
│   ├── components/
│   ├── public/personas/            # archetype portraits
│   └── package.json
├── notebooks/
│   ├── 01_dataset_construction.ipynb
│   ├── 02_persona_extraction.ipynb
│   ├── 03_register_classifier_training.ipynb
│   ├── 04_naija_reviewer_finetune.ipynb     # Colab Pro+ ready
│   ├── 05_task1_evaluation.ipynb
│   ├── 06_task2_evaluation.ipynb
│   ├── 07_ablations.ipynb
│   ├── 08_cross_domain_experiment.ipynb
│   └── 09_human_eval_analysis.ipynb
├── scripts/
│   ├── build_dataset.sh
│   ├── build_npa_bench.sh
│   ├── train_all.sh
│   ├── eval_all.sh
│   └── make_demo.sh
├── human_eval/
│   ├── protocol.md
│   ├── form_template.html
│   └── analysis/
├── paper/
│   ├── paper.tex
│   ├── paper.pdf
│   ├── figures/
│   └── references.bib
└── tests/
    ├── test_persona_extractor.py
    ├── test_register_classifier.py
    ├── test_task1_pipeline.py
    ├── test_task2_pipeline.py
    └── test_cross_domain_bridge.py
```

### 17.2 README requirements

- One-paragraph what-this-is + GIF of working demo.
- Quick-start: `cp .env.example .env` → fill keys → `make demo` → curl example.
- Architecture diagram (same as paper Figure 1).
- Every env var documented.
- API examples as curl one-liners with Nigerian persona JSON.
- Reproduction note: seeds, model versions, data revision, GPU requirements.
- Links to all four artifacts: paper PDF, HuggingFace model, HuggingFace dataset, demo URL.
- Citation block.
- `JUDGES.md` with team email + 30-min response SLA during evaluation week.

### 17.3 Container architecture

- Image base: `python:3.11-slim`.
- Layered build: deps → models → code (cache-friendly).
- Image size: < 1.5GB compressed (without Ollama models; those mount as volume).
- Healthcheck: `GET /health`.
- Compose stack: app + Ollama + Chroma + NocoDB + Postgres + optional n8n.

### 17.4 Make targets

- `make demo` — bring up stack, seed sample data, smoke test.
- `make eval` — full evaluation suite (long).
- `make ablations` — ablation table run.
- `make finetune` — kicks off NaijaReviewer-8B training (Colab notebook variant for non-local).
- `make paper` — compile paper.tex.
- `make bench` — build NPA-Bench from raw data.
- `make clean` — tear down.

### 17.5 Reproducibility test (Week 7 gate)

- Fresh clone on a fresh machine by someone outside the daily codebase.
- Clone-to-first-API-call walkthrough must complete in < 10 minutes.
- Any deviation triggers README update.
- Non-negotiable per the brief.

### 17.6 Submission package

| Submission | Artefact |
|---|---|
| Link to agent built | `https://<deployment-url>` (Render/Fly.io) + Docker image on GHCR |
| Solution paper | `paper/paper.pdf` |
| Code repository | `github.com/<team>/naija-persona-agent`, MIT |
| **Bonus**: HuggingFace model | `huggingface.co/<team>/naija-reviewer-8b` |
| **Bonus**: HuggingFace dataset | `huggingface.co/datasets/<team>/npa-bench` |
| **Bonus**: arXiv preprint | `arxiv.org/abs/2606.XXXXX` |
| **Bonus**: Demo URL | `npa.<team>.dev` |

---

## 18. Non-Functional Requirements

| Requirement | Specification |
|---|---|
| Latency | p95 < 3s per request; cold start < 30s (Ollama warm); model load < 60s |
| Throughput | ≥ 10 concurrent requests on single container |
| Privacy | No PII; hashed identifiers only; NDPR-aware |
| Explainability | Every output ships rationale: ≥ 2 dimensions, ≥ 1 register marker |
| Reliability | Graceful degradation: fall back to static initial corpus if RAG unavailable; queue + backoff on API rate limits |
| Scalability | 10× data growth without replatforming (Qdrant scales, LangGraph state externalised to Postgres) |
| Auditability | Full I/O logs + reweighting changelog, 24-month retention |
| Cost ceiling | < $150 API spend across full eval + ablation suite |
| Security | Env-var secrets; rate-limited public endpoints; CORS scoped |
| Logging | Structured JSON; LangSmith traces; one log per agent node |

---

## 19. Milestones & Timeline (8 weeks)

Starting **2026-05-16**, targeting **2026-07-11** submission.

| Week | Dates | Theme | Key deliverables |
|---|---|---|---|
| **Week 1** | May 16 – May 22 | Foundation | Repo skeleton + Dockerfile + FastAPI stub. Iwendi et al. corpus downloaded + cleaned. Fresh Jumia/Konga scrape kickoff. Persona schema finalised. AfriSenti/NaijaSenti/SentiLeye corpora downloaded + inspected. Memory + project tracking updated. |
| **Week 2** | May 23 – May 29 | Register module + persona | Register classifier trained, calibrated, evaluated. Persona extractor v1 (offline pipeline). Vanilla baseline (Claude Sonnet 4 + concat history) measured end-to-end. First MLflow experiments. |
| **Week 3** | May 30 – June 5 | Fine-tune v0.1 + Task 1 | NaijaReviewer-8B v0.1 trained (Jumia-only). Task 1 pipeline end-to-end on Jumia. Stage-A rating regressor trained. First head-to-head measurements vs. Claude/GPT-4o. |
| **Week 4** | June 6 – June 12 | Task 2 + Nollywood data | Multi-source candidate retrieval. LightGCN trained. MACF re-ranker. Cold-start elicitation. Nollywood corpus assembled. NaijaReviewer-8B v0.2 (with Nollywood) trained. |
| **Week 5** | June 13 – June 19 | Cross-domain + NPA-Bench build | Cross-domain bridge implemented + ablation-tested. Persona-linked synthetic generation for cross-domain users. NPA-Bench v0.9 assembled. Nigerian-marker subset finalised. First cultural-gap measurement. |
| **Week 6** | June 20 – June 26 | NaijaReviewer-8B v1.0 + container hardening + ablations | NaijaReviewer-8B v1.0 (release candidate). Full ablation suite executed (10 rows × 3 seeds × 2 domains). USHB + Tsinghua AKF baselines reimplemented + run. Container hardened. Frontend judge demo built. |
| **Week 7** | June 27 – July 3 | Human eval + paper draft | Human evaluation form launched; ≥ 30 raters recruited; ≥ 600 judgments collected. Paper Sections 1–6 drafted. Fresh-clone reproducibility test passes. HuggingFace model + dataset cards drafted. |
| **Week 8** | July 4 – July 10 | Paper polish + open-source release + submit | Paper Sections 7–9 + figures finalised. NaijaReviewer-8B + NPA-Bench published to HuggingFace. arXiv preprint submitted. JUDGES.md written. Demo URL public. Submission package assembled. Submit. |
| **Optional Week 9** | July 11 – July 17 | Post-submission amplification | Twitter thread + LinkedIn post + Hacker News + community mailings. Respond to early feedback. |

**Triage path if a week slips:**

1. First to cut: NaijaReviewer-8B v0.1 (Jumia-only). Skip directly to v0.2 with Nollywood data.
2. Second to cut: optional `/business/churn-intervention` endpoint. Keep as paper Section 7 only.
3. Third to cut: HuggingFace Space leaderboard scaffold.
4. Fourth to cut: cross-domain experiment (single-domain backup numbers ready).
5. Hard floor: cannot cut. Two endpoints, paper, repo, NaijaReviewer-8B model release.

---

## 20. Business Applications (Paper Section 7)

The persona representation built for the hackathon tasks is the foundation for a portfolio of Nigerian commercial deployments. The paper's Section 7 is half a page; each application here gets one paragraph in the paper.

### 20.1 Telco churn intervention recommender (v1 PRD preserved)

- **Problem.** 25–35% annual churn; $3.60 ARPU; blanket promotions waste budget.
- **Application.** Persona feeds the v1 intervention recommender; outputs ranked retention interventions per subscriber segment.
- **Demonstration.** Optional `/business/churn-intervention` endpoint in container; uses synthetic NCC-calibrated subscriber profiles.
- **Buyer.** MTN Nigeria (89.6M), Airtel Nigeria (58M), Globacom (20.9M), 9mobile.
- **ROI math.** 7% churn reduction × 10k users × $500 LTV = $350k protected. At MTN scale: 1% improvement = 9-figure naira annual figure.

### 20.2 Thin-file MSME credit scoring layer

- **Problem.** 96% of 40M Nigerian MSMEs lack formal financial records. ₦130T CBN credit gap.
- **Application.** Cognitive dimensions + aspect priorities + register signals from consumer review behaviour serve as a behavioural feature layer for credit scoring.
- **Buyer.** Access, GTBank, UBA, Zenith; microfinance banks; NCGC ₦100B scheme; FairMoney, Carbon, Renmoney.
- **Paper claim.** Persona representation correlates with publicly available sector default-rate data from CBN reports.

### 20.3 Cross-cultural marketplace personalisation

- **Problem.** ~17M Nigerian-diaspora mis-served by recommenders trained on U.S./EU patterns.
- **Application.** Cross-domain bridge generalises to cross-cultural; Nigerian persona priors re-project recommendations.
- **Buyer.** Jumia, Konga, Selar, Bumpa, Spar Nigeria; diaspora platforms (African Food Box, Tappi, JJC Online).

### 20.4 Nollywood / Afrobeats content recommendation

- **Application.** Cross-domain bridge + cultural-register-aware recommendation for African content platforms.
- **Buyer.** Showmax, IROKO TV, Boomplay, Mdundo.

### 20.5 Behavioural cohort modelling for fintech

- **Application.** Interpretable cohort framework via cognitive dimensions × register tier.
- **Buyer.** Opay, Palmpay, Moniepoint, Kuda, FairMoney.

### 20.6 Survey augmentation / synthetic respondents

- **Application.** Synthetic Nigerian respondents for exploratory market research, with "Lost in Simulation" caveats explicit.

---

## 21. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Nollywood review data thinner than expected | Medium | High | Combine 4+ sources; allow persona-linked synthetic (tagged); minimum viable Nollywood subset for ablation |
| Cross-domain bridge transfer weak | Medium | High | Single-domain backup numbers ready; negative results still publishable if quantified |
| Register classifier underperforms | Low | Medium | Multiple corpora (AfriSenti + NaijaSenti + SentiLeye); pretrained AfriBERTa / NaijaBERT fallback; explicit calibration |
| NaijaReviewer-8B does not beat GPT-4o on headline metrics | Medium | Critical | Pre-mitigation: extensive iteration on training data quality + register-balanced augmentation; even partial wins on subset of metrics are publishable; backup framing: "we narrow the gap from Xpp to Ypp" |
| Colab Pro+ A100 access intermittent | Medium | Medium | Fall back to HuggingFace AutoTrain or RunPod $1.50/hr A100; budget ~$50 for paid alternatives |
| Human eval recruitment slow | Medium | Medium | Cast wider net early (Week 5 call out); honorarium covers cost; family/friends network as floor |
| Container fails reproducibility | Medium | Critical | Fresh-clone test Week 7; CI pipeline builds container on every commit; pinned deps |
| Paper does not land headline number | Medium | Critical | Backup framing: gap recovery + cross-domain transfer + open-source artifact release each support claim independently |
| Two-person team capacity overrun | High | Critical | Ruthless triage path in Section 19; never cut paper or fine-tune |
| Cross-domain users sparse | High | Medium | Persona-linked synthetic generation policy explicit (Section 9.3); sample size disclosed |
| NDPR / scraping concerns | Low | High | Iwendi et al. as primary; scraping respectful (rate-limit, robots.txt); no PII beyond hashed IDs |
| Judges find baseline implementation bug | Medium | High | Code review Week 7; baseline numbers disclosed with CI; ablation re-run before submission |
| Ollama deployment fails for judges | Medium | Medium | Container ships with pre-downloaded model weights (GGUF Q4_K_M, ~5GB); judges do not pull |
| Model card / dataset card review concerns | Low | Low | Use HuggingFace templates; disclose biases + limitations explicitly |
| arXiv submission timing slips | Low | Medium | Format-clean from Week 7; submit any time within 7 days post-hackathon |

---

## 22. Out of Scope

- Real-time data ingestion from operator partners.
- Production-grade auth (judges receive open endpoint).
- Multi-tenant SaaS hosting.
- Mobile app.
- Real Nigerian operator subscriber data (unavailable for hackathon window).
- Fine-tuning beyond NaijaReviewer-8B (no 70B variant for this submission; future work).
- Generation in Yoruba / Igbo / Hausa (detection only — generation is future work).
- Automated campaign execution / autonomous customer outreach.
- Individual-level (vs. persona-level) prediction beyond the persona structure.
- Real-time network quality monitoring.
- Legal / regulatory compliance certification.

---

## 23. Comparison: This System vs. Median Submissions

| Dimension | Median submission | NPA v3.0 |
|---|---|---|
| Persona representation | Concatenated past reviews in prompt | 5 structured cognitive dimensions + register tier + aspect priorities + 4-tier register classifier |
| Cultural register | None | Dedicated trained classifier + explicit conditioning |
| LLM backbone | Frontier closed API (GPT-4 / Claude) | Fine-tuned open-weight Llama 3.1 8B (NaijaReviewer-8B) + Claude where reasoning matters |
| Dataset | Yelp / Amazon / Goodreads (saturated) | Jumia/Konga + Nollywood with explicit Nigerian-marker subset |
| Cross-domain | None | Bridge with quantified transfer |
| Two-stage rating | Single-prompt | Stage-A regressor → Stage-B text |
| Self-consistency | Single LLM call | 5-sample soft self-consistency (Task 2) + style-check retry (Task 1) |
| External-knowledge pre-ranking | None | Tsinghua AKF-style |
| Ablations | 0–2 | 10 with 3 seeds and confidence intervals |
| Baselines | 0–1 | 9 (including 4 frontier zero-shot, 3 reimplemented winning architectures, 1 CF, 1 base Llama) |
| Human evaluation | None | 30+ Nigerian raters, 600+ judgments, Fleiss-κ reported |
| Public benchmark | None | NPA-Bench released CC-BY-4.0 |
| Open weights | None | NaijaReviewer-8B + register classifier released |
| arXiv preprint | None | Co-submitted within 7 days |
| Judge demo | API only | Polished Next.js with 5 archetypes + side-by-side compare |
| Business framing | Generic | 6 Nigerian deployments with quantified backdrop |
| Container | Often broken on clone | Fresh-clone tested Week 7 |
| Paper | Last-minute write-up | Outline locked Week 1; sections drafted Weeks 6–8 |
| Reproducibility | Often missing | Make targets, CI, pinned deps, fresh-clone test, seeds set |

---

## 24. Document Approval

| Role | Name | Signature / Date |
|---|---|---|
| Product Lead | | |
| Technical Lead | | |
| Fine-Tuning Lead | | |
| Paper Lead | | |
| Open-Source Release Lead | | |

---

## Appendix A — Glossary

- **NPA**: Naija Persona Agent (this system).
- **NaijaReviewer-8B**: Llama 3.1 8B Instruct QLoRA fine-tune released as the headline open-weight artifact.
- **NPA-Bench**: Public benchmark of Nigerian personas + review-generation triples + recommendation triples.
- **Persona**: Structured user representation (5 cognitive dimensions + register tier + aspect priorities + history anchors).
- **Register tier**: ∈ {standard_english, nigerian_english, nigerian_pidgin, code_mixed}.
- **Cultural prior**: Implicit Western distribution baked into vanilla LLM agent training.
- **Cross-domain bridge**: LLM-mediated function transferring persona representation from source domain (Jumia) to target domain (Nollywood).
- **RGM**: Review Generation Metric, USHB's combined review-quality score.
- **HR@k**: Hit Rate at k.
- **QLoRA**: Quantised Low-Rank Adaptation — 4-bit fine-tuning method.
- **MACF**: Multi-Agent Collaborative Filtering (arXiv:2511.18413).
- **Tsinghua AKF**: Adaptive Knowledge Fusion (Yu et al., WWW '25).
- **USHB**: Unified Framework for Simulating Human Behaviors (Zhao et al., WWW '25, 3rd-place User Modeling).
- **NCC**: Nigerian Communications Commission.
- **NDPR**: Nigeria Data Protection Regulation.
- **AfriSenti / NaijaSenti / SentiLeye**: Nigerian / African NLP datasets used in register classifier training.
- **Ollama**: Local-LLM serving runtime; the user has access.
- **Colab Pro+**: Google Colab paid tier with A100 access; used for QLoRA training.

---

## Appendix B — Selected References

(Full BibTeX in `paper/references.bib`.)

- Yan et al., *AgentSociety Challenge*. arXiv:2502.18754.
- Zhao, Yang et al., *USHB*. WWW '25 Companion, DOI 10.1145/3701716.3719227.
- Zhang et al. (Renmin), *Collaborative Optimization for Workflow Agents*. DOI 10.1145/3701716.3719228.
- Yu et al. (Tsinghua), *Adaptive Knowledge Fusion*. DOI 10.1145/3701716.3719230.
- Wu et al., *Self-Consistency Recommendations*. DOI 10.1145/3701716.3719229.
- Shang et al., *AgentRecBench*. arXiv:2505.19623.
- Zhang et al., *AgentCF++*. arXiv:2502.13843.
- MACF: *Multi-Agent Collaborative Filtering*. arXiv:2511.18413.
- Cold-Start LLM Reasoning (Netflix), WWW '26. arXiv:2511.18261.
- *Lost in Simulation*. arXiv:2601.17087.
- Muhammad et al., *AfriSenti*. ACL Anthology.
- Muhammad et al., *NaijaSenti*. LREC 2022.
- Oyewusi et al., *SentiLeye*. IJCAI 2021 AI4SG.
- Lin et al., *Pidgin orthographic augmentation*. arXiv:2404.18264.
- Iwendi et al., *Sentiment analysis on African e-commerce reviews*. IEEE 2020.
- Dettmers et al., *QLoRA*. arXiv:2305.14314.
- Touvron et al., *Llama 3*. Meta AI technical report.
- *NaijaBERT / AfriBERTa*. Masakhane research.

---

*This document supersedes PRD v3.0 (pre-feature-audit), v2.0 (Naija Persona Agent, single-artifact), and v1.0 (Churn Intervention Recommender). All v1 and v2 work is preserved as Section 20 of the paper and as the optional `/business/churn-intervention` demonstration endpoint in the container. The Open-Source Commitment of v3.x is non-negotiable: all four artifacts (NPA system code, NaijaReviewer-8B weights, NPA-Bench dataset, arXiv preprint) released under their respective open licenses.*

---

## Appendix C — v3.1 Feature Audit & Additions

This appendix documents the 22 features added to v3.0 after a comprehensive feature audit conducted on **2026-05-16** before fine-tuning began. The goal of the audit: ensure NPA has every high-leverage feature a winning Nigerian-hackathon submission needs, before committing the longest-pole work (fine-tuning).

### Method

Brainstormed candidate features across 7 dimensions: persona representation, recommendation engineering, generation quality, infrastructure, evaluation rigor, paper craft, judge experience, and open-source community engagement. Each candidate was triaged by impact × engineering cost × differentiation against the hackathon median. Tier-1 features (high impact, manageable cost, low risk) are integrated into v3.1. Tier-2 features (medium impact, medium cost) were considered but rejected with rationale. The full audit reasoning is preserved in conversation history with the architect.

### Feature catalog (22 additions)

#### A. Persona representation (Section 6.2)

| # | Feature | Where integrated | Marginal cost |
|---|---|---|---|
| A1 | Per-dimension uncertainty quantification (`dimension_confidence`) | Section 6.2 Persona schema | 1 day |
| A2 | Age cohort dimension (`age_cohort`: gen_z / millennial / gen_x / boomer) | Section 6.2 (6th cognitive dim) | 1 day |
| A3 | Diaspora vs. in-country flag (`diaspora`, `diaspora_region`) | Section 6.2 | 1 day |
| A4 | Religious framing tier (`religious_framing`, `religious_marker_density`) | Section 6.2, parallel to register | 1.5 days |
| A5 | Punctuation / emoji style profile (`punctuation_style` dict) | Section 6.2 + Task 1 prompt template injection | 1 day |
| A6 | Code-switching intensity control (`code_switch_intensity` ∈ [0,1]) | Section 6.2 + Task 1 generation | 0.5 day |

#### B. Recommendation engineering (Section 7.4)

| # | Feature | Where integrated | Marginal cost |
|---|---|---|---|
| B1 | MMR diversity re-ranking (λ=0.7) | FR-T2.7 | 0.5 day |
| B2 | Serendipity scoring per recommendation | FR-T2.8 | 0.5 day |
| B3 | Negative recommendations capability (`include_negatives` flag) | FR-T2.11 | 1 day |
| B4 | Time-aware conditioning (paycheck cycle, season, day-of-week) | FR-T2.10 | 1 day |
| B5 | Long-tail item floor constraint | FR-T2.9 | 0.5 day |

#### C. API & infrastructure (Section 8.3)

| # | Feature | Where integrated | Marginal cost |
|---|---|---|---|
| C1 | Streaming responses (SSE) on both endpoints | Section 8.3 | 1 day |
| C2 | Per-request reasoning trace toggle (`include_reasoning` flag) | Section 8.3 | 1 day |
| C3 | Batch endpoints + async job ID polling | Section 8.3 | 1 day |

#### D. Evaluation rigor (Sections 12.7–12.11)

| # | Feature | Where integrated | Marginal cost |
|---|---|---|---|
| D1 | LLM-as-judge cultural authenticity grading (GPT-4o blind) | Section 12.7 | 2 days |
| D2 | Statistical significance testing (paired bootstrap + t-test + Cliff's δ) | Section 12.8 | 1 day |
| D3 | Calibration plots (Figs 6–7) | Section 12.9 | 0.5 day |
| D4 | Robustness probes (typos, word swaps, register mixing) | Section 12.10 | 1 day |
| D5 | Bias audit (gender / region / tribe / religion / diaspora) | Section 12.11 + paper Section 7a | 2 days |

#### E. Paper craft (Sections 14.4–14.8)

| # | Feature | Where integrated | Marginal cost |
|---|---|---|---|
| E1 | Pre-registration of hypotheses H1–H5 | Section 14.4 | 0.5 day |
| E2 | Failure analysis section (3 documented modes) | Section 14.5 | 1 day |
| E3 | Case study deep-dives (4 personas, paper appendix) | Section 14.6 | 1 day |
| E4 | Carbon footprint disclosure (~0.4 kg CO₂eq for fine-tuning) | Section 14.7 | 0.5 day |
| E5 | Comparison to existing African / Nigerian AI work | Section 14.8 | 1 day |

#### F. Judge demo (Section 16.2a)

| # | Feature | Where integrated | Marginal cost |
|---|---|---|---|
| F1 | Interactive persona builder (judges construct + run) | Section 16.2a | 1.5 days |
| F2 | "Watch the agent think" reasoning trace viewer | Section 16.2a | 1.5 days |

#### G. Open-source community

| # | Feature | Where integrated | Marginal cost |
|---|---|---|---|
| G1 | Educational Colab notebook for Nigerian students | Section 17.1 (`notebooks/10_naija_student_intro.ipynb`) | 1 day |

### Total marginal cost

**~22 days across 8 weeks = ~2.75 days/week** in addition to the baseline v3.0 build. This fits within the team's capacity given the timeline and the optional Week 9 amplification week absorbing any spill.

### Triage path if v3.1 features slip

In order of cuttability:

1. **G1 Educational Colab notebook** — community goodwill, no judging impact. Cut first.
2. **B5 Long-tail floor + B3 Negative recommendations** — production-grade but not paper-headline.
3. **C3 Batch endpoints** — production feature; judges don't need it.
4. **F1 Interactive persona builder** — wow factor but F2 reasoning trace viewer covers most of the engagement.
5. **D5 Bias audit (full)** — keep statistical tests on gender + region; cut religion/tribe if time-pressed.
6. **A5 Punctuation style profile** — subtle; degrades gracefully if cut.

**Never cut** (these are the v3.1 contribution backbone):

- A1, A2, A4 (persona richness justifies the cognitive-dimensions claim)
- B1 MMR diversity (production-grade differentiator)
- C1 Streaming, C2 reasoning trace (judge demo demands them)
- D1 LLM-as-judge, D2 statistical tests, D3 calibration plots (paper rigor non-negotiable)
- E1 pre-registration, E2 failure analysis, E3 case studies, E5 African AI comparison (paper substance)
- F2 reasoning trace viewer (demo moment of truth)

### Features audited and rejected (with rationale)

| Feature | Why rejected |
|---|---|
| Tool use / external API access | Brief doesn't require; adds complexity; out of scope. |
| Multi-agent debate frameworks (theatrical N-agent debate) | MACF 5-trace self-consistency is sufficient; debate is risk without proportional gain. |
| Watermarking | Research-level; not hackathon-relevant. |
| 70B fine-tune | Compute steep; 8B sufficient for register tasks; future work. |
| Yorùbá / Igbo / Hausa native generation | Native validation hard at hackathon scale; detection only (in register classifier) captures the signal. |
| Cultural prior gradient experiment | Interesting but expensive; future work. |
| Synthetic Nigerian Turing test (full study) | Multi-week effort; subset captured in human eval. |
| LoRA composition | Research stretch. |
| Diaspora-only sub-corpus | Likely too sparse for separate sub-claim; diaspora flag in persona is the lighter alternative. |
| Webhook callbacks / Prometheus metrics / API key auth | Production features; not judged. |
| Watermarking generated content | Research-level; not differentiating. |
| Multi-task scaling laws (1B / 3B / 8B comparison) | Compute-heavy; future work. |

---

*End of Appendix C — v3.1 Feature Audit & Additions.*
