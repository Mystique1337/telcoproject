# Naija Persona Agent (NPA)

> A Nigerian-context LLM agent system for review simulation and personalised product recommendation. Submission to the Nigerian AI Agents Hackathon, May 2026.

Vanilla LLM agents carry an implicit Western cultural prior. On Nigerian users this shows up as compressed rating intensity, flattened Pidgin / Nigerian-English register, individualised framing, and misread religious markers. **NPA** makes the cultural prior visible and recovers it with a structured cognitive persona representation + register-aware prompting + a fine-tuned open-weight Llama 3.1 8B model (**NaijaReviewer-8B**), and ships it as two production-ready API endpoints.

| Asset | Link |
|---|---|
| 📄 **Paper** | `paper/paper.tex` (compiles to `paper/paper.pdf`) |
| 🤗 **Model (GGUF)** | <https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF> |
| 💻 **AgentSociety-compatible drop-in** | `submission/naija_agent.py` |
| 🎬 **Judge demo (Streamlit)** | `demo/streamlit_app.py` |
| 📊 **Eval harness** | `scripts/eval_all.py` + `scripts/eval_register_fidelity.py` |

## Two submission paths

NPA ships two equivalent ways to drive it, so judges can use whichever fits their harness:

1. **REST API mode** (FastAPI) — `POST /simulate-review` and `POST /recommend` on `http://localhost:8765`. Per-request `backbone_override` / `reranker_override` fields let judges A/B between the fine-tune and frontier models.
2. **AgentSociety simulator mode** — drop `submission/naija_agent.py` into the upstream `websocietysimulator` from [`AGI-FBHC/AgentsChallenge`](https://github.com/AGI-FBHC/AgentsChallenge). It subclasses `SimulationAgent` and `RecommendationAgent` and implements `workflow()` per the reference contract. No persona JSON is assumed — every input comes from `self.interaction_tool`.

See [`JUDGES.md`](JUDGES.md) for end-to-end instructions on both paths.

## Two endpoints (per hackathon brief)

| Endpoint | Input | Output |
|---|---|---|
| `POST /simulate-review` | `{persona, product, backbone_override?}` | `{rating, review, register_tier, rationale}` |
| `POST /recommend` | `{persona, candidate_set?, k, reranker_override?}` | `{recommendations: [{product_id, score, rationale, rank}, ...]}` |

Both share a structured `Persona` (4 cognitive dimensions + Nigerian register tier + aspect priorities + history anchors).

## Quick start (no Docker, no Poetry)

```bash
git clone https://github.com/Mystique1337/telcoproject
cd telcoproject

# 1. Install deps
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY and/or OPENAI_API_KEY

# 3. (Optional) Run NaijaReviewer-8B locally via LM Studio:
#    a) Download the GGUF model from
#       https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF
#    b) Load it in LM Studio → start the local server on port 1234
#    c) .env already sets TASK1_BACKBONE=lmstudio:naija-reviewer-8b
#    If you skip this, /simulate-review will use Claude as the backbone instead.

# 4. Run the API
make serve
# or: uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8765
```

API live at `http://localhost:8765/docs` (interactive Swagger UI) in ~10 seconds.

## Curl examples

### Task 1 — generate a review

```bash
curl -X POST http://localhost:8765/simulate-review \
  -H "Content-Type: application/json" \
  -d '{
    "persona": {
      "user_id": "chinwe_owerri_genz",
      "hedonic_utilitarian": 0.8,
      "intensity_calibration": {"amazing": 4.8, "okay": 3.0},
      "communal_individual": 0.7,
      "aspect_priority": {"quality": 0.4, "value": 0.3, "delivery": 0.2, "seller": 0.1},
      "register_tier": "code_mixed",
      "register_markers": ["abeg", "wahala", "no cap"],
      "register_confidence": 0.85,
      "review_anchors": [],
      "history_count": 0,
      "extraction_source": "manual"
    },
    "product": {
      "product_id": "TECNO-SPARK-10",
      "title": "Tecno Spark 10 — 128GB",
      "category": "Phone & Tablet",
      "description": "6.6 inch display, 5000mAh battery, dual SIM",
      "domain": "jumia"
    }
  }'
```

Pass `"backbone_override": "anthropic:claude-sonnet-4-20250514"` to compare against vanilla Claude on the same request.

### Task 2 — recommend products

```bash
curl -X POST http://localhost:8765/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "persona": {... same as above ...},
    "k": 5,
    "domain": "jumia"
  }'
```

Full schemas at `http://localhost:8765/docs`.

## Streamlit judge demo

```bash
make demo
# or: NPA_API_URL=http://localhost:8765 streamlit run demo/streamlit_app.py
```

Opens at `http://localhost:8501`. Tab 1 — side-by-side compare (NaijaReviewer vs vanilla Claude / GPT-4o). Tab 2 — single-model recommendation panel.

## Train the model (Colab, Drive-persisted, resume-safe)

**The fastest path to a working NaijaReviewer-8B is the end-to-end Colab notebook:** build the ~20k Nigerian corpus, QLoRA fine-tune Llama 3.1 8B, eval head-to-head against Claude + Nemotron baselines, and push everything to HuggingFace — in one notebook, ~3-4 hours on an A100.

1. **Open in Colab**: `File → Open notebook → GitHub → Mystique1337/telcoproject → notebooks/02_finetune.ipynb`
2. **Runtime → Change runtime type → A100** (auto-tunes batch size for H100 / A100 / L4 / T4)
3. **Add three secrets** to Colab Secrets: `NVIDIA_API_KEY`, `ANTHROPIC_API_KEY`, `HF_TOKEN`
4. **Runtime → Run all** — walk away

Everything writes to `Drive/MyDrive/naija-persona-agent/`. If Colab disconnects mid-run, **just re-open the notebook and Run all again** — corpus stages skip if their JSONL exists, training resumes from the last `checkpoint-XXXX`, the merged model skips if already present.

## Switch the backbone — 11 supported models

| Provider class | Spec format | Models | Auth |
|---|---|---|---|
| 🇳🇬 NaijaReviewer-8B (Task A) | `lmstudio:naija-reviewer-8b` | our fine-tune via LM Studio | none (local) |
| Anthropic | `anthropic:claude-sonnet-4-20250514` | Claude Sonnet 4 | `ANTHROPIC_API_KEY` |
| OpenAI | `openai:gpt-4o`, `openai:gpt-4o-mini` | GPT-4o family | `OPENAI_API_KEY` |
| **Ollama Cloud** (open-source) | `ollama-cloud:gpt-oss:120b`, `ollama-cloud:qwen3-coder:480b` | GPT-OSS 120B, Qwen3-Coder | `OLLAMA_API_KEY` |
| **HF Inference** (open-source) | `hf:meta-llama/Llama-3.3-70B-Instruct`, `hf:Qwen/Qwen2.5-72B-Instruct`, `hf:mistralai/Mixtral-8x7B-Instruct-v0.1` | Llama 3.3 70B, Qwen 2.5 72B, Mixtral | `HF_TOKEN` |
| NVIDIA NIM (free tier) | `nvidia:meta/llama-3.3-70b-instruct` | Llama 3.3 70B | `NVIDIA_API_KEY` |
| Ollama (local) | `ollama:llama3.1:8b-instruct` | any local Ollama model | none |

Set the default in `.env`:

```bash
TASK1_BACKBONE=lmstudio:naija-reviewer-8b      # review generation (Task A)
TASK2_RERANKER=anthropic:claude-sonnet-4-20250514  # ranking (Task B — frontier recommended)
```

Restart `make serve`. Per-request `backbone_override` / `reranker_override` fields in the request body override the defaults — judges can A/B between any two models on the same persona × product without restart.

## Vector retrieval — Pinecone (recommended) or Chroma (local)

The recommend agent uses **Pinecone serverless with `llama-text-embed-v2`** (1024-dim, asymmetric `passage`/`query` retrieval) when `PINECONE_API_KEY` is set in `.env` and the index is populated. Otherwise falls back to local Chroma, then to persona-aware disk sampling.

## Stage-2.5 cross-encoder pre-rerank — Cohere (optional)

Between the prerank step and the LLM rerank step, the agent optionally runs a **Cohere `rerank-v3.5`** cross-encoder pass to narrow 30 → 15 candidates by persona-flavored query. Adds ~200–600ms and tightens the LLM rerank's input pool. Auto-skips if `COHERE_API_KEY` is not set in `.env`. Reasoning trace exposes the stage with its model, top-N, duration, and any fallback reason.

```bash
# Populate Pinecone (one-time, ~7 min for 6,657 products)
python scripts/build_pinecone_index.py

# Or, local-only flow with Chroma
python scripts/build_product_index.py --provider local
```

## Evaluation

```bash
# No-GT register-fidelity eval — runs in ~3 min on the 5 sample personas × 6 products
make eval-fidelity

# Full eval with held-out test set (drop v1_test_full.parquet into data/finetune/)
make eval
```

Both write to `paper/results.json` + `paper/results.md`. The full eval computes both our rubric-aligned metrics (RMSE / BERTScore F1 / ROUGE-L / register-match / cultural-marker recall) **and** the official AgentSociety metrics (`preference_estimation`, `sentiment_error`, `emotion_error`, `topic_error`, `review_generation`, `overall_quality`).

## Architecture in 60 seconds

```
┌───────────────────────────────────────────┐
│  SHARED PERSONA REPRESENTATION            │
│  (4 cog dims + register + aspects + anchors) │
└───────┬─────────────────────┬─────────────┘
        │                     │
        ▼                     ▼
┌────────────────┐    ┌────────────────┐
│ Task 1 Agent   │    │ Task 2 Agent   │
│ /simulate-     │    │ /recommend     │
│ review         │    │                │
│                │    │ semantic       │
│ NaijaReviewer- │    │ retrieval +    │
│ 8B (LM Studio) │    │ Claude         │
│ + Claude       │    │ re-rank + MMR  │
│ fallback       │    │                │
└────────────────┘    └────────────────┘
        │                     │
        └─────────┬───────────┘
                  ▼
         ┌──────────────────┐
         │ Chroma + sample  │
         │ Nigerian fixtures │
         └──────────────────┘
```

## Repository structure

```
telcoproject/
├── app/                  FastAPI application
│   ├── api/              routers, schemas, main
│   ├── agents/           persona extractor, review agent, recommend agent
│   ├── llm/              LM Studio + Claude + OpenAI + Ollama client abstraction
│   ├── rag/              Chroma vector store wrapper
│   ├── data/             loaders, persona cache
│   └── prompts/          Jinja templates per domain × register tier
├── data/                 datasets (gitignored at scale; samples committed)
│   ├── sample/           5 personas + 6 products (judge fixtures)
│   └── finetune/         held-out test parquet (gitignored)
├── finetuning/           NaijaReviewer-8B QLoRA training scripts
├── demo/                 Streamlit judge demo (entry point)
├── paper/                LaTeX paper + figures + eval results
├── scripts/              build_finetune_corpus, build_product_index, eval_all, eval_register_fidelity
├── submission/           naija_agent.py — single-file drop-in for the AgentSociety simulator
├── tests/                pytest suite
└── notebooks/            01_build_corpus, 01b_build_corpus_openai, 02_finetune (Colab)
```

## Documentation

| Doc | Purpose |
|---|---|
| [`JUDGES.md`](JUDGES.md) | Two-mode submission paths + reading order for the panel |
| [`finetuning/README.md`](finetuning/README.md) | Reproduce NaijaReviewer-8B from scratch |
| [`paper/README.md`](paper/README.md) | Paper drafting notes |

## Team

- **Ashinze** — system & fine-tuning (`ashinze@bluebulb.co.uk`)
- **Franca** — product & frontend
- **[3rd]** — paper & evaluation

## License

- **Code** — MIT
- **NaijaReviewer-8B weights** — Llama 3.1 Community License
- **Released datasets** — CC-BY-4.0

## Citation

```bibtex
@misc{npa2026,
  title={Naija Persona Agent: A Cultural-Prior-Aware LLM Agent for
         Nigerian Review Simulation and Recommendation},
  author={Ashinze and Franca and team},
  year={2026},
  url={https://github.com/Mystique1337/telcoproject}
}
```

## Acknowledgments

AfriSenti, NaijaSenti, SentiLeye, Masakhane, the AgentSociety Challenge organisers, and the Nigerian AI Agents Hackathon panel.
