# Paper Drafting Notes

> 4–6 pages, ACM proceedings template, Overleaf-built.

## What we're writing

**Working title**: *The Cultural Prior in LLM Agents: An Open-Source Recovery for Nigerian Review Simulation and Recommendation.*

**Headline claim (single sentence, repeat across abstract / intro / conclusion)**:

> *We define the cultural register as a missing architectural primitive for LLM agents and show that a small QLoRA fine-tune (NaijaReviewer-8B, 8B parameters) combined with a four-dimension cognitive persona representation reduces rating-prediction RMSE by **XX%** and improves register-tier fidelity by **YY percentage points** against vanilla Claude Sonnet 4 on the Nigerian-marker subset. All code, model weights, and fine-tuning corpus released under open licenses.*

Fill in `XX` and `YY` after Day 3 evaluation runs.

## Section structure (target ~6 pages)

1. **Abstract** (~150 words) — cultural prior + 2 contributions (NPA system + NaijaReviewer-8B) + headline number.
2. **Introduction** (½ page) — motivate cultural prior; preview contributions.
3. **Related Work** (½ page, 4 paragraphs) — see citation list below.
4. **Method** (1 page) — persona decomposition + register-aware prompting + fine-tune recipe + Task 2 pipeline.
5. **Experiments** (1½ pages) — dataset, baselines, main results table, ablation, cultural-gap recovery, 2 qualitative case studies.
6. **Discussion + Business Implications** (½ page) — Nigerian deployments with quantified backdrop.
7. **Limitations** (¼ page) — cite "Lost in Simulation"; 5-day scope; small eval set; no human eval.
8. **Conclusion** (¼ page).

## Required tables and figures

| # | Type | Status |
|---|---|---|
| Table 1 | Dataset composition | After Day 1 data is loaded |
| Table 2 | Main results vs 4 baselines | After Day 3 eval runs |
| Table 3 | Ablation + cultural gap | After Day 3 ablation |
| Figure 1 | Architecture diagram | Day 1 (already in repo at `paper/figures/architecture.png` placeholder) |
| Figure 2 | Persona schema (annotated example) | Day 2 |
| Figure 3 | Qualitative compare (vanilla vs NaijaReviewer) | Day 3 |

## Citation list (12+ to start)

These are all in `references.bib` — drop and import directly.

- **Yan et al. 2025** — *AgentSociety Challenge*. arXiv:2502.18754.
- **Zhao, Yang et al. 2025** — *USHB* (WWW '25 3rd-place User Modeling). DOI 10.1145/3701716.3719227.
- **Zhang et al. 2025 (Renmin)** — *Collaborative Optimization for Workflow Agents*. DOI 10.1145/3701716.3719228.
- **Yu et al. 2025 (Tsinghua)** — *Adaptive Knowledge Fusion*. DOI 10.1145/3701716.3719230.
- **Zhang et al. 2025** — *AgentCF++*. arXiv:2502.13843.
- **MACF 2026** — *Multi-Agent Collaborative Filtering*. arXiv:2511.18413.
- **Lost in Simulation 2026** — arXiv:2601.17087.
- **Muhammad et al.** — *AfriSenti*. ACL Anthology.
- **Muhammad et al. 2022** — *NaijaSenti*. LREC 2022.
- **Oyewusi et al. 2021** — *SentiLeye*. IJCAI 2021 AI4SG.
- **Lin et al. 2024** — *Pidgin orthographic augmentation*. arXiv:2404.18264.
- **Dettmers et al. 2023** — *QLoRA*. arXiv:2305.14314.
- **Ogueji et al. 2021** — *AfriBERTa*.

## Where to write

- **Overleaf** project (template: `ACM-Reference-Format` → "ACM Master Template" → "Master article-author + 2-col"); invite all 3 collaborators.
- Local LaTeX source committed to `paper/paper.tex` after each Overleaf save.
- Final PDF: `paper/paper.pdf`.

## Voice tips

- Honest first, glossy second. Hackathon judges trust honest > polished.
- Foreground the cultural prior thesis — that's the intellectual contribution.
- Don't oversell. If the fine-tune wins on only 1 metric, say so and explain why.
- Use specific Nigerian examples (Tunde the Lagos trader, etc.) — the judges will recognise the personas.
- Cite the AgentSociety winners explicitly — shows you did your reading.
- Limitations section is a feature, not a bug. Cite "Lost in Simulation" and "we only had 5 days" — judges respect this.

## Day-by-day paper progress targets

| Day | Target |
|---|---|
| Day 1 | Overleaf live; abstract + intro draft; architecture figure; refs.bib populated |
| Day 2 | Method section draft (1 page); Related Work paragraphs |
| Day 3 | Experiments section with real numbers; ablation table |
| Day 4 | Discussion + Limitations + Conclusion; figures polished |
| Day 5 | Final read-aloud polish; compile clean PDF; submit |
