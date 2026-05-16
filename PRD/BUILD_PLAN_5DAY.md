# BUILD PLAN — Naija Persona Agent (NPA), 5-Day Sprint

**Companion to**: `PRD_v4_NPA_5Day.md`
**Window**: 5 consecutive working days
**Team**: 3 people (Franca, Ashinze, +1)
**Submission**: hackathon URL + paper PDF + GitHub repo (+ bonus HuggingFace model)

---

## STATUS (live)

| Day | Owner | Status |
|---|---|---|
| **Day 1** | Ashinze | ✅ **Complete** — repo scaffolded, FastAPI + Docker stack, corpus pipeline, end-to-end Colab notebook, sample personas + products, paper LaTeX skeleton, both initial commits pushed |
| **Day 2** | Ashinze (training) + Franca (frontend) + Writer (paper §1-2) | 🟢 In progress — fine-tune kicks off via `notebooks/naija_reviewer_8b_end_to_end.ipynb` |
| Day 3 | — | Pending — integrate trained model into FastAPI container; head-to-head eval; Streamlit demo polish |
| Day 4 | — | Pending — deploy public URL; reproducibility test; paper sections 3-7 drafted |
| Day 5 | — | Pending — paper polish; final submission |

**Critical-path entry point Day 2**: open `notebooks/naija_reviewer_8b_end_to_end.ipynb` in Colab. The notebook runs the full corpus → fine-tune → eval → HF push pipeline unattended, ~3–4 hours on an A100.

---

## Day-0 Setup Checklist (do this BEFORE Day 1)

Allocate 2–3 hours together. Don't start Day 1 without these green.

### Accounts (everyone)
- [ ] **GitHub org** (`naija-persona-agent` or similar); both/all members as owners; private until Day 5
- [ ] **HuggingFace org** for `naija-reviewer-8b` + companion dataset
- [ ] **Anthropic API key** — $50 budget cap
- [ ] **OpenAI API key** — $30 budget cap (for embeddings + GPT-4o baselines)
- [ ] **Fly.io** OR **Render** account (deployment target)
- [ ] **Weights & Biases** (free hosted) — experiment tracking
- [ ] **Overleaf** project for the paper, ACM proceedings template
- [ ] **Streamlit Cloud** OR **HuggingFace Spaces** account (demo hosting)

### Local tooling (each)
- [ ] Python 3.11, Poetry, Docker, Docker Compose, Ollama
- [ ] `ollama pull llama3.1:8b-instruct` (~5GB; pre-cache before Day 1)
- [ ] `gh` CLI authenticated
- [ ] VS Code (or Cursor) + Copilot

### GPU for fine-tuning
- [ ] Confirm GPU is reachable & has bf16 support (A100 / H100 / 4090 / etc.)
- [ ] Test: `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"`
- [ ] Install transformers + peft + bitsandbytes + datasets + trl from a clean conda env
- [ ] Smoke-test: load Llama 3.1 8B in 4-bit, run one forward pass

### Communication
- [ ] Slack / Discord / WhatsApp channel for the team
- [ ] Pin: PRD link, this build plan, repo link, GPU access details, API key vault
- [ ] **Daily 15-min standup** at end of each day (async-OK; post in channel)
- [ ] **Day-5 morning emergency sync** at 9 AM (60 min, sync)

### Day-0 kickoff sync (60 min)
Lock these decisions:
1. **Role split** — confirm assignments (see "Roles" below); flex by skill
2. **Branch policy** — `main` protected; feature branches; squash-merge; CI must pass
3. **Coding standards** — `ruff` + `black` + pre-commit hooks
4. **Tie-breaker** — who arbitrates technical disputes
5. **Day-5 deadline** — exact hour for submission (work backward from this)

---

## Roles (default — confirm or swap at Day-0 sync)

| Person | Primary owner | Secondary |
|---|---|---|
| **A** (Ashinze?) | Repo / Container / FastAPI / Deployment / Streamlit demo | Day 5 submission ops |
| **B** (Franca?) | Dataset / Fine-tuning / Register handling / NaijaReviewer-8B release | Eval scripts |
| **C** (3rd) | Paper drafting / Evaluation runs / Baselines / Figures | README + JUDGES.md |

If C is engineering-heavy: swap with A; B's scope stays. If C is data-leaning: pair on Day 1 with B; take over baselines + paper Day 2 onwards.

---

## Day 1 — Foundation, Data, Schema (Monday)

**EOD goal**: Docker container responds to `curl /health`; Iwendi data loaded; persona schema in code; fine-tuning corpus prep started; paper outline + Section 1 drafted.

### Person A — Engineering setup
| Task | Hours |
|---|---|
| `gh repo create` org/naija-persona-agent; branch protection; CI skeleton (`.github/workflows/ci.yml` lint + tests stub) | 1 |
| Scaffold app directory tree (see PRD §13.1); `poetry init`; install langchain, fastapi, uvicorn, pydantic, chromadb, openai, anthropic | 1 |
| `Dockerfile` (multi-stage); `docker-compose.yml` with `app` + `ollama` + `chroma` services; `make demo` brings everything up; `/health` returns 200 inside container | 3 |
| Implement Pydantic schemas: `Persona`, `Product`, `SimulateReviewRequest`, `SimulateReviewResponse`, `RecommendRequest`, `RecommendResponse` | 2 |
| README + JUDGES.md skeletons | 1 |

### Person B — Data + persona schema + fine-tune prep
| Task | Hours |
|---|---|
| Download Iwendi et al. 2020 dataset; verify integrity; document license in `data/README.md` | 1 |
| Normalise to standard schema (review_id, user_pseudonym, product_id, rating, text, category, timestamp); commit as `data/jumia_reviews/iwendi_2020_cleaned.parquet`; build loader in `app/data/loaders.py` | 3 |
| Hand-write 5 Nigerian persona archetypes (Chinwe / Tunde / Aisha / Femi / Ifeoma per PRD §16.2) as JSON in `data/sample/personas/` | 1 |
| Start fine-tuning corpus prep: filter Nigerian-marker subset via Claude classification + SentiLeye lexicon; aim for ~6–8k high-confidence examples by EOD | 3 |

### Person C — Paper + architecture diagram
| Task | Hours |
|---|---|
| Overleaf project; ACM template; commit paper.tex skeleton with placeholder section headers + abstract stub | 1 |
| Draft Introduction (½ page) — cultural prior thesis + 2 contributions + headline-number placeholder | 2 |
| Architecture diagram in Excalidraw or draw.io (PRD §4.1); export PNG to `paper/figures/architecture.png` | 2 |
| Survey related work — pull 4 paragraphs of references: LLM user simulation (AgentCF, AgentCF++), AgentSociety winners (USHB, Tsinghua AKF), Nigerian NLP (AfriSenti, NaijaSenti, SentiLeye), African AI (Masakhane, AfriBERTa, LELAPA) | 2 |
| Set up `references.bib` with all citations from PRD §11.2 | 1 |

### EOD standup (15 min, async-OK)
- A: container live? schema valid?
- B: how many Nigerian-marker examples filtered?
- C: paper outline committed?
- Any blockers?

### Day-1 gate criteria
- ✅ Repo scaffolded; CI green; Dockerfile builds; `make demo` brings up `app + ollama + chroma`; `/health` returns 200
- ✅ Iwendi data loaded; schema documented; ~6–8k Nigerian-marker examples filtered
- ✅ Persona schema implemented; 5 archetypes committed
- ✅ Paper Overleaf project alive; architecture diagram done; Section 1 draft

**If any red flag**: fix tomorrow morning before starting Day-2 tasks.

---

## Day 2 — Both endpoints working (rough) + fine-tune kickoff (Tuesday)

**EOD goal**: `/simulate-review` and `/recommend` return *something* end-to-end (quality polish is Day 3). NaijaReviewer-8B training kicked off overnight.

### Person A — Task 1 + Task 2 wired up
| Task | Hours |
|---|---|
| `/simulate-review` route: call persona extractor (Claude API) if persona has `extraction_source: "history"`, else use as-is; call Stage-A rating regressor stub (returns avg rating for now); call Task 1 LLM via Ollama (NaijaReviewer-8B not ready yet, so use Claude as backbone for Day 2) | 3 |
| Prompt template `app/prompts/jumia_v1.jinja` — register-aware, few-shot Nigerian examples (2 Pidgin + 2 Nigerian English + 1 code-mixed) | 2 |
| `/recommend` route: persona → Chroma semantic retrieval over product index → Claude API re-rank top-30 → top-5 with rationale | 3 |

### Person B — Fine-tune corpus + kickoff
| Task | Hours |
|---|---|
| Complete fine-tuning corpus to ~10–12k examples: 80% Iwendi Nigerian-marker, 20% Claude-generated register-balanced synthetic (PRD §8.3); commit to `data/finetune/v1_train.jsonl` + `v1_val.jsonl` + `v1_test.jsonl` (90/5/5 split, seed 42) | 4 |
| QLoRA training script `finetuning/train_naija_reviewer.py` with config `configs/naija_reviewer_qlora.yaml`; smoke-test on 100 examples (verify it runs end-to-end before launching real run) | 3 |
| **Kick off real training overnight** — ~6–10 hours; logs to W&B | 1 |

### Person C — Baselines + Method section draft
| Task | Hours |
|---|---|
| Build product index in Chroma — embed Iwendi product titles + descriptions with `text-embedding-3-small`; commit `data/jumia_reviews/product_index.chroma/` | 2 |
| Eval script `finetuning/eval_baselines.py` — runs Vanilla Claude Sonnet 4 + Vanilla GPT-4o + Base Llama 3.1 8B (via Ollama) on the Nigerian-marker test split; logs RMSE, BERTScore, register-tier match to W&B | 3 |
| Paper Method section draft (1 page) — persona decomposition + register-aware prompting + fine-tune recipe outline | 3 |

### EOD standup
- A: both endpoints return valid JSON?
- B: training running? estimated completion time?
- C: baseline numbers in W&B?

### Day-2 gate criteria
- ✅ `/simulate-review` returns `{rating, review, register_tier, rationale}` (even if Claude is backbone for now)
- ✅ `/recommend` returns `{recommendations: [...]}`  with top-5 + per-item rationale
- ✅ Fine-tune training kicked off; W&B run live
- ✅ Vanilla baselines measured; numbers in W&B
- ✅ Paper Sections 1–2 draft; Method outline

---

## Day 3 — Integrate fine-tune, polish quality, register handling (Wednesday)

**EOD goal**: NaijaReviewer-8B integrated as Task 1 backbone; outputs feel authentically Nigerian; we have *numbers vs vanilla baseline* for the paper headline.

### Person A — Integrate fine-tune + Streamlit demo
| Task | Hours |
|---|---|
| Wait for fine-tune to complete (likely overnight ran ~6–10h, ready Wed morning); B converts to GGUF Q4_K_M for Ollama | 0 (B's task) |
| Configure Ollama with NaijaReviewer-8B Q4_K_M; verify it loads + responds | 1 |
| Swap Task 1 backbone in `/simulate-review` from Claude to NaijaReviewer-8B; keep Claude as fallback (`fallback_to_claude` env flag); commit | 2 |
| Self-consistency style check (FR-T1.4): generated review embedding vs persona corpus; single regen if below τ | 2 |
| MMR diversity re-rank in `/recommend` (FR-T2.5); λ=0.7 | 2 |
| Build Streamlit demo `demo/streamlit_app.py`: 3 persona archetypes (dropdown) + product picker + "Generate Review" button + side-by-side compare panel (NaijaReviewer-8B vs Vanilla Claude); deploy to Streamlit Cloud or HF Spaces | 3 |

### Person B — Fine-tune eval + iteration + GGUF
| Task | Hours |
|---|---|
| Convert NaijaReviewer-8B LoRA → merged weights → GGUF Q4_K_M for Ollama; upload to HF (private for now); test load via Ollama | 2 |
| Run head-to-head eval: NaijaReviewer-8B vs 4 baselines on test split (PRD §10.3) — RMSE, BERTScore, register-tier match, cultural-marker recall | 3 |
| If v0.1 weak on register match: iterate corpus (add more Pidgin examples, drop noisy ones); kick off v0.2 training **only if time allows** | 3 |
| Update model card draft (HuggingFace template): intended use, training recipe, eval table, bias notes, citation block | 1 |

### Person C — Run main results + ablations + qualitative cases
| Task | Hours |
|---|---|
| Run full evaluation: NPA-full + NaijaReviewer-8B on test split; log to W&B; produce Table 2 (main results) | 2 |
| Run ablation rows (PRD §10.4): − no persona structure; − no register conditioning; commit numbers to `paper/results.json` | 2 |
| Pick 2 personas for qualitative case studies (PRD §10.6); generate end-to-end outputs from NaijaReviewer-8B + Vanilla Claude; commit annotated comparison to `paper/figures/qualitative_cases.md` | 2 |
| Paper Experiments section draft (1.5 pages) — dataset, baselines, main results table, ablation, cultural-gap recovery, 2 case studies | 3 |

### EOD standup
- A: NaijaReviewer-8B serving in container? Streamlit demo working?
- B: head-to-head numbers in W&B? Does v0.1 beat baselines anywhere?
- C: paper Experiments draft committed?

### Day-3 gate criteria (the most important)
- ✅ NaijaReviewer-8B integrated as Task 1 backbone
- ✅ Streamlit demo running locally with compare panel
- ✅ Head-to-head eval complete; **at least one metric where NaijaReviewer-8B beats a baseline meaningfully**
- ✅ Ablation table data committed
- ✅ Paper Experiments section drafted

**If NaijaReviewer-8B doesn't beat baselines anywhere**: don't panic. Paper backup framing is "we narrow the gap from X to Y"; the system architecture + persona claim still holds. Iterate v0.2 corpus Day 4 only if absolutely necessary.

---

## Day 4 — Deploy + reproducibility + paper polish (Thursday)

**EOD goal**: Container live at public URL; fresh-clone reproducibility test passes; paper drafted to ~85%.

### Person A — Deploy + reproducibility
| Task | Hours |
|---|---|
| Build production Docker image; push to GHCR | 1 |
| Deploy to Fly.io / Render at public URL (`npa.fly.dev` or similar); configure secrets via Fly secrets; verify `/health` + `/docs` + `/simulate-review` + `/recommend` all respond live | 3 |
| **Reproducibility test** — recruit a non-team friend OR use a fresh VM; clone repo, follow README, must reach first successful API call in < 10 minutes. Fix anything that breaks. | 3 |
| README polish: quick-start, curl examples with realistic Nigerian persona JSON, architecture diagram, links to demo URL + paper + HF model | 2 |

### Person B — Model release + carbon footprint + ablation re-run
| Task | Hours |
|---|---|
| Publish NaijaReviewer-8B to HuggingFace under Llama 3.1 Community License (public Day 5 morning); model card with training recipe, eval table, biases, citation, carbon estimate | 3 |
| Carbon footprint calc: GPU hours × ~400 W × regional gCO₂/kWh; commit `paper/carbon.md`; reference in model card | 1 |
| Re-run ablation with 3 seeds; produce final results table with mean ± std for paper Table 3 | 3 |
| Edge-case testing: empty persona, malformed product JSON, Pidgin-only history, code-mixed product description; verify graceful degradation | 2 |

### Person C — Paper polish
| Task | Hours |
|---|---|
| Paper Sections 5–7 polished: Experiments (with final numbers), Discussion & Business Implications (½ page), Limitations (¼ page) | 4 |
| Figures finalised: architecture (Fig 1), persona schema with annotated example (Fig 2), qualitative compare (Fig 3) — consistent matplotlib styling | 3 |
| Compile paper.pdf; check page count (target 4–6); read it cold once for flow | 2 |

### EOD standup + Day-5 plan sync (30 min)
- A: deployed URL working? fresh-clone test passed?
- B: model published? carbon disclosed?
- C: paper at 4–6 pages, readable cold?
- Lock Day-5 timeline: morning polish, afternoon submit, **submit by [agreed hour]**

### Day-4 gate criteria
- ✅ Public deployment URL works
- ✅ Fresh-clone reproducibility test passes < 10 min
- ✅ NaijaReviewer-8B published on HF (can stay private until Day 5 morning)
- ✅ Paper at ~85%; readable cold; figures in
- ✅ All baselines reproduced + ablation 3-seed run complete

---

## Day 5 — Polish + submit (Friday)

**Strict rule: no new features. Only fixes + polish + submission.**

### Morning (9 AM – 1 PM)

#### Person A
- [ ] Final smoke test on deployed container — both endpoints respond with realistic personas
- [ ] Tag `v1.0` release on GitHub; commit final README + JUDGES.md
- [ ] Flip GitHub repo to **public**
- [ ] Verify all submission URLs in an incognito browser

#### Person B
- [ ] Flip HuggingFace model to **public**; verify model card is clean; verify downloads work
- [ ] Final eval re-run (sanity check on results table)
- [ ] Polish demo UI; ensure all 3 personas render cleanly

#### Person C
- [ ] Final paper polish — read aloud once; eyeball typography; verify all citations resolve; compile clean PDF
- [ ] Verify paper is 4–6 pages
- [ ] Record 60-second screen-capture walkthrough video (loom.com or QuickTime) — paste link in JUDGES.md

### Afternoon (1 PM – 5 PM)

#### All hands
- [ ] **Submission package check** — confirm three required deliverables work:
  1. Live agent URL — visit, hit `/simulate-review` with sample JSON
  2. Paper PDF — open in browser, verify formatting
  3. GitHub repo URL — visit in incognito, verify public + README renders
- [ ] **Bonus check** — HuggingFace model URL works, downloads + GGUF + license visible
- [ ] **Submit on hackathon portal** by [agreed deadline hour]
- [ ] Verify each link works post-submission

#### After submission (celebration)
- [ ] Drop a screenshot in the team channel
- [ ] Tweet thread / LinkedIn post / HN Show / Reddit posts (optional Day-5 evening or weekend amplification)
- [ ] Sleep

---

## Daily Rituals

### EOD standup (15 min, async-OK in Slack/Discord)

Each person posts in a single daily thread:
1. **Done today** — links to commits / W&B runs / notebooks
2. **Doing tomorrow** — single most important task
3. **Blockers** — anything waiting on the other people or external

### Weekly review — N/A (we're 5 days, not weeks)

Daily reviews substitute. The Day-4 EOD sync (30 min, synchronous if possible) doubles as the Day-5 planning meeting.

---

## Critical Path Watchlist

| Critical path item | Day | If it slips |
|---|---|---|
| Iwendi data loaded | 1 | Everything downstream blocked; fix Day-1 morning before standup |
| Fine-tune corpus ready | 2 | Training delayed; eval pushed to Day 4; cut iteration v0.2 |
| Training completed | 3 | Use Claude as Task 1 backbone in container; paper headline shifts to "architecture + persona recovers gap" without the fine-tune contribution; honest in paper |
| Eval numbers in W&B | 3 | Paper Experiments section delayed; Day 4 absorbs |
| Container deployed | 4 | Hard deadline — judges need a URL; if Fly.io down, fall back to local container + ngrok |
| Reproducibility test pass | 4 | Lose ~10 reproducibility points but submission still valid; fix README in real-time |
| Paper compiled | 5 morning | Submission risk — pre-compile draft Day 4 evening as backup |

---

## What to Do TODAY (Saturday May 16)

1. **Send PRD v4 + this build plan to Franca + 3rd teammate**. Ask them to skim before Day-0 sync.
2. **Schedule Day-0 sync** for tomorrow (Sunday) or Monday morning — 2 hours.
3. **Day-0 setup checklist** — start the accounts/keys provisioning now; some take time to verify.
4. **Pull Llama 3.1 8B locally**: `ollama pull llama3.1:8b-instruct` (~5 GB).
5. **Verify GPU access** for Person B: `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"`.
6. **Identify the 3rd teammate's strength** — confirm role assignments above.

---

## If This Goes Wrong

| Worst-case at end of Day | What to do |
|---|---|
| **Day 1**: container won't build | Drop docker-compose features; ship FastAPI + Ollama only; fix during Day 2 |
| **Day 2**: corpus < 5k examples | Train on what you have; smaller corpus is fine; document in paper |
| **Day 3**: NaijaReviewer-8B is worse than baseline | Use Claude as Task 1 backbone; paper claim shifts to architecture + persona (the fine-tune becomes "future work narrows the gap"); still publishable |
| **Day 4**: container won't deploy publicly | Ship a Docker image on GHCR + local run instructions in README; judges run locally |
| **Day 5 morning**: paper not done | Submit a 3-page version; cut Discussion/Limitations to one paragraph each; don't miss deadline |
| **Day 5 hour 1**: submission portal down | Email organisers with all artifacts attached; capture screenshots; document outage |

The hackathon is won by **shipping**, not by perfection. A working URL + readable paper + public repo on time beats a partial submission with perfect components.

---

*Companion document to `PRD_v4_NPA_5Day.md`. Vision-document context in `PRD_v3_Naija_Persona_Agent_AllOut.md`. v1 churn intervention work preserved in `PRD_Project_B_Churn_Intervention_Recommender.docx`.*
