# Naija Persona Agent

**A Nigerian-context AI system for review simulation and product recommendation, built on a purpose fine-tuned open-weight model.**

Submission to the Nigerian AI Agents Hackathon, 2026.

---

## The problem

General-purpose LLM agents carry an implicit Western cultural prior. On Nigerian users that prior shows up as compressed rating intensity, flattened Pidgin and Nigerian-English register, individualised framing where the user is communal, and misread religious or cultural markers. The result is review and recommendation behaviour that does not sound or score like a real Nigerian shopper.

Naija Persona Agent makes that prior visible and recovers it with three things working together:

1. A structured **cognitive persona** representation (four behavioural dimensions, a Nigerian register tier, aspect priorities, and review history anchors).
2. Register-aware prompting grounded in that persona.
3. **NaijaReviewer-8B**, an open-weight Llama 3.1 8B model QLoRA fine-tuned on a Nigerian review corpus, served as the review and ranking backbone.

The system ships as a FastAPI service plus a React frontend that exposes two products built on the same persona core.

## What is in the box

| Asset | Where |
|---|---|
| NaijaReviewer-8B (GGUF) | <https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF> |
| Hosted inference endpoint (serverless GPU) | `deploy/modal_naija.py` (Modal, OpenAI-compatible) |
| Paper (Task A, review generation) | `paper/paper_task_a.tex` |
| Paper (Task B, recommendation) | `paper/paper_task_b.tex` |
| Frontend (two products + dev lab) | `frontend/` (React, Vite, Tailwind) |
| Evaluation harness | `scripts/eval_all.py`, `scripts/eval_register_fidelity.py`, `scripts/eval_ablation.py` |
| Simulator drop-in | `submission/naija_agent.py` |

## The two products

Both run from the same FastAPI service. The frontend is hash-routed, so one running server serves all of them.

### InsideNaija (Task A, review generation) - default route `/`
A synthetic consumer-research panel. Describe a product and a panel of 24 Nigerian personas reacts with ratings and authentic, register-correct reviews, aggregated into sentiment, themes, and buy-likelihood by zone, age, and register. Useful for testing a product before launch, including products with no existing reviews. The 24 personas span Nigeria's geopolitical zones, age bands, occupations, and register tiers (standard English, Nigerian English, Pidgin, and code-mixed).

### ShopEasy (Task B, recommendation) - route `#shopeasy`
A Nigerian storefront experience: text search, image search ("find me something like this photo"), voice search, and a conversational shopping assistant that handles budgets, follow-ups, and mid-chat budget changes. Recommendations are persona-aware, show price and vendor, and link to a product page with specs, photos, and simulated reviews. Supports passwordless accounts with an onboarding wizard that builds and stores a persona.

### NaijaPersona Lab - route `#lab`
A developer console for driving the raw endpoints and A/B-ing backbones side by side.

### B2B widget - route `#b2b` and `?widget`
A business can register, get an embeddable snippet, and drop persona-aware recommendations into its own site via an iframe.

Language support across the products: English, Nigerian Pidgin, plus Yoruba, Hausa, and Igbo, with Nigerian text-to-speech (YarnGPT) reading reviews and chat aloud.

## Headline results

**Task B (recommendation), held-out test set.** NaijaReviewer-8B is the strongest re-ranker measured, ahead of Claude Sonnet 4 and the open-weight 70B+ baselines.

| Re-ranker | NDCG@10 | HR@5 |
|---|---|---|
| **NaijaReviewer-8B** | **0.572** | **0.588** |
| Llama 3.3 70B | 0.477 | 0.298 |
| Qwen 2.5 72B | 0.461 | 0.324 |
| Claude Sonnet 4 | 0.430 | 0.353 |
| GPT-OSS 120B | 0.366 | 0.323 |

A blind human relevance eval tells a different and honest story: on a 2-rater panel over the 24 personas, raters preferred Claude's recommendation lists (NaijaReviewer-8B win-rate 27.3%, mean relevance 2.60 vs 3.40). The fine-tune wins on recovering held-out relevant products (NDCG@10) but Claude composes lists humans find more coherent. See `paper/task_b_human_eval_summary.md`.

**Task A (review generation), blind human A/B.** Across 5 Nigerian raters and 50 review pairs, NaijaReviewer-8B reaches a **48.5%** win-rate against Claude Sonnet 4 (95% CI [40.2%, 56.9%]) - statistical parity with a frontier model many times its size. Notably, an LLM-judge over the same pairs preferred the frontier model far more often than the human raters did, which is itself evidence of the Western prior the system is designed to correct.

Full numbers: `paper/results.md`, `paper/human_eval_summary.md`, `paper/llm_judge_summary.md`, `paper/task_b_human_eval_summary.md`.

## How this maps to the judging criteria

The submission is built to address every line of the scoring rubric for both tasks, on a shared 100-point scale.

| Weight | Task A: User Modeling | Task B: Recommendation |
|---|---|---|
| 30 | Review text quality (ROUGE / BERTScore) | Ranking quality (NDCG@10 / Hit Rate) |
| 25 | Rating accuracy (RMSE) | Cold-start and cross-domain |
| 20 | Behavioural fidelity (human eval) | Contextual relevance (human eval) |
| 15 | Solution paper | Solution paper |
| 10 | Code reproducibility | Code reproducibility |

Where each criterion is satisfied:

**Task A**
- *Review text quality:* BERTScore F1 0.858 and ROUGE-L 0.205 on the held-out v2 split, reported in `paper/paper_task_a.tex` and `paper/results.md`, computed by `scripts/eval_all.py`.
- *Rating accuracy:* RMSE 1.114 versus Claude Sonnet 4 at 1.319, a 15.5% reduction, on the same split.
- *Behavioural fidelity:* a blind 5-rater human A/B over 50 pairs (48.5% win-rate against Claude), in `paper/human_eval_summary.md`, with an LLM-judge contrast in `paper/llm_judge_summary.md`.
- *Solution paper:* `paper/paper_task_a.tex`.
- *Code reproducibility:* one-command `make serve`, plus the full Colab build pipeline (`notebooks/02_finetune.ipynb`) and the hosted endpoint.

**Task B**
- *Ranking quality:* NDCG@10 0.572 and HR@5 0.588, the best of five re-rankers measured, in `paper/paper_task_b.tex` and `paper/results.md`.
- *Cold-start and cross-domain:* explicit handlers in `app/agents/recommend_agent.py` (demographic fallback when a persona has little history; multi-domain candidate pulls), surfaced in the API response and reasoning trace.
- *Contextual relevance:* every recommendation carries a persona-grounded rationale, demonstrated in the Task B qualitative case study and observable live in the ShopEasy storefront. A blind A/B relevance human-eval (`scripts/build_task_b_human_eval_xlsx.py` / `scripts/aggregate_task_b_human_eval_xlsx.py`, summary in `paper/task_b_human_eval_summary.md`) compares NaijaReviewer-8B and Claude lists across the 24 personas. On the current 2-rater panel, raters preferred Claude's lists (NaijaReviewer-8B win-rate 27.3%, mean relevance 2.60 vs 3.40), the reverse of the automatic NDCG@10 result. We report this divergence openly: the fine-tune is better at recovering held-out relevant products, while Claude composes lists humans find more coherent at a glance.
- *Solution paper:* `paper/paper_task_b.tex`.
- *Code reproducibility:* same one-command run; the recommendation stack is reproducible with `scripts/build_pinecone_index.py`.

**Nigerian contextualisation (bonus).** The system is designed from the ground up to behave and sound Nigerian: a four-tier register model (standard English, Nigerian English, Pidgin, code-mixed), cultural-marker handling, the NaijaReviewer-8B fine-tune trained on Nigerian review data, multilingual output in Yoruba, Hausa, and Igbo, and Nigerian text-to-speech. This is the core thesis of both papers, not an afterthought.

## Architecture

```
                    Shared cognitive persona
        (4 behavioural dims + register tier + aspects + anchors)
                               |
            +------------------+------------------+
            |                                     |
            v                                     v
   Task A: review generation            Task B: recommendation
   POST /simulate-review                POST /recommend, /chat
   POST /panel (InsideNaija)
            |                                     |
   NaijaReviewer-8B                      Pinecone retrieval
   (hosted on Modal)                     -> Cohere cross-encoder
   + frontier fallback                   -> persona-aware LLM rerank
            |                                     |
            +------------------+------------------+
                               |
                React frontend (InsideNaija, ShopEasy, Lab, B2B)
```

## Quick start

Requires Python 3.11+ and an `ANTHROPIC_API_KEY` and/or `OPENAI_API_KEY`. The hosted NaijaReviewer-8B endpoint needs no local GPU.

```bash
git clone https://github.com/Mystique1337/telcoproject
cd telcoproject

# 1. Backend deps
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env: add your API keys. MODAL_BASE_URL is already wired to the
# hosted NaijaReviewer-8B endpoint; no local model runtime is required.

# 3. Run the API + frontend (the built frontend is served by FastAPI)
make serve
# or: uvicorn app.api.main:app --host 0.0.0.0 --port 8765
```

Open `http://localhost:8765` for the products and `http://localhost:8765/docs` for the interactive API.

To rebuild the frontend after changes:

```bash
cd frontend && npm install && npm run build
```

## API reference

| Endpoint | Purpose |
|---|---|
| `POST /simulate-review` | Generate one persona-grounded review for a product |
| `POST /panel` | InsideNaija: a multi-persona synthetic review panel with aggregates |
| `POST /recommend` | Persona-aware ranked recommendations |
| `POST /chat` | Conversational shopping assistant (budgets, follow-ups, refinement) |
| `POST /elicit` | Build a persona from a short interview |
| `GET/POST /shop/*` | ShopEasy text, image, and voice search |
| `POST /auth/register`, `GET /auth/profile/{id}` | Passwordless accounts and stored personas |
| `POST /b2b/*` | Business registration and embeddable recommendations |
| `GET /tts/*` | Nigerian text-to-speech voices |
| `GET /catalog/*` | Products, personas, categories, eval summary |

Per-request `backbone_override` and `reranker_override` fields let you A/B any two models on the same input without a restart. Full schemas are at `/docs`.

## The model: NaijaReviewer-8B, end to end

NaijaReviewer-8B is the heart of the system: a Llama 3.1 8B Instruct model QLoRA fine-tuned on Nigerian review data, then quantised and hosted so it can drive both products at low cost. The full pipeline lives in the Colab notebooks and reproduces from scratch.

### 1. Corpus construction (`notebooks/01_build_corpus.ipynb`, `01b_build_corpus_openai.ipynb`)
A Nigerian review corpus is generated through two independent synthetic-data pipelines, one driven by NVIDIA Nemotron and one by OpenAI, then deduplicated and formatted as Alpaca instruction/input/response triples and split into train and validation sets. Generating from two pipelines reduces single-model stylistic bias in the training data.

### 2. Fine-tuning (`notebooks/02_finetune.ipynb`)
QLoRA fine-tune of `Meta-Llama-3.1-8B-Instruct` using Unsloth on a single GPU (autotuned for A100, L4, or T4):

- LoRA rank 16, alpha 32, dropout 0.1, applied to all attention and MLP projections (`q,k,v,o,gate,up,down`).
- 4-bit base load; `paged_adamw_8bit`; learning rate 2e-4 with cosine schedule and 100 warmup steps; 2 epochs; bf16 where supported.
- **Response-only loss**: the trainer masks everything before `### Response`, so gradient is computed only on the answer tokens, not the instruction scaffolding.
- **EOS-terminated training**: an explicit end-of-sequence token is appended to every example so the model learns to stop cleanly in production instead of rambling.
- A pre-training truncation diagnostic and a masking-verification step catch silent length and tokenisation issues before any GPU hours are spent.
- The run is tracked in Weights and Biases (`notebooks/03_training_results.ipynb` pulls the loss and learning-rate history back from the W&B run).

### 3. Merge, quantise, and package (same notebook)
The LoRA adapter is merged into the 16-bit base, smoke-tested on validation examples, then converted with llama.cpp to f16 GGUF and quantised to `Q4_K_M`, `Q5_K_M`, and `Q8_0`. The notebook also auto-generates an Ollama `Modelfile` (encoding the exact Alpaca template used in training, with proper stop tokens) and a HuggingFace model card.

### 4. HuggingFace artifacts
The pipeline pushes every artifact to HuggingFace under the `Shinzmann` namespace:

| Artifact | Repo |
|---|---|
| Merged model (HF format) + GGUF builds | `Shinzmann/naija-reviewer-8b-v2` |
| Quantised GGUF served in production | <https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF> |
| LoRA adapter (small, for re-merging) | `Shinzmann/naija-reviewer-8b-v2-lora` |
| Training corpus snapshot | `Shinzmann/npa-corpus-v1` (dataset) |

### 5. Serving on Modal (`deploy/modal_naija.py`)
The `Q4_K_M` GGUF is hosted on **Modal** as a serverless, OpenAI-compatible inference endpoint:

- CUDA 12.4 runtime image with a prebuilt `llama-cpp-python` CUDA wheel; the GGUF is pulled from HuggingFace once and cached in a Modal Volume so cold starts do not re-download it.
- Runs on a single L4 GPU and scales to zero after idle, so there is no idle cost.
- A minimal FastAPI wrapper exposes `/v1/models` and `/v1/chat/completions` directly over `llama_cpp.Llama`, which is what the app calls.

```bash
modal deploy deploy/modal_naija.py            # deploy (prints the public URL)
python deploy/test_modal.py <url>             # smoke-test the live endpoint
```

### 6. Wiring into the backend
The FastAPI service reaches the hosted model through a dedicated `modal:` provider in `app/llm/client.py`, configured by `MODAL_BASE_URL` in `.env`. This keeps it isolated from the real OpenAI base URL, so `modal:naija-reviewer-8b` can be the Task-1 backbone while OpenAI and Anthropic remain available for ranking, persona extraction, and A/B comparison.

### Switching the backbone

Set the default in `.env`, or override per request.

| Provider | Spec format | Auth |
|---|---|---|
| NaijaReviewer-8B (hosted) | `modal:naija-reviewer-8b` | none (open endpoint) |
| NaijaReviewer-8B (local) | `lmstudio:naija-reviewer-8b` | none (LM Studio on :1234) |
| Anthropic | `anthropic:claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai:gpt-4o`, `openai:gpt-4o-mini` | `OPENAI_API_KEY` |
| HuggingFace Inference | `hf:meta-llama/Llama-3.3-70B-Instruct` | `HF_TOKEN` |
| Ollama Cloud | `ollama-cloud:gpt-oss:120b` | `OLLAMA_API_KEY` |
| NVIDIA NIM | `nvidia:meta/llama-3.3-70b-instruct` | `NVIDIA_API_KEY` |

```bash
TASK1_BACKBONE=modal:naija-reviewer-8b              # review generation (Task A)
TASK2_RERANKER=anthropic:claude-sonnet-4-20250514   # ranking (Task B)
```

## Retrieval and reranking

ShopEasy and `/recommend` retrieve from **Pinecone serverless** with `llama-text-embed-v2` (1024-dim, asymmetric query/passage) over roughly 6,657 Jumia products when `PINECONE_API_KEY` is set, falling back to local Chroma and then to persona-aware disk sampling. An optional **Cohere `rerank-v3.5`** cross-encoder runs as a Stage-2.5 pre-rerank to narrow candidates before the persona-aware LLM rerank; it auto-skips when `COHERE_API_KEY` is absent.

```bash
python scripts/build_pinecone_index.py        # populate Pinecone (one-time)
python scripts/build_product_index.py --provider local   # or local Chroma
```

## Evaluation

```bash
make eval-fidelity     # no-ground-truth register-fidelity eval (fast)
make eval              # full eval with held-out test set
```

Results write to `paper/results.json` and `paper/results.md`. The harness reports both the project's rubric metrics (RMSE, BERTScore F1, ROUGE-L, register match, cultural-marker recall) and the AgentSociety challenge metrics.

**Human evaluation.** Two blind A/B human-eval instruments back the human-judged criteria:

```bash
# Task A - review quality / behavioural fidelity (5 raters, 50 pairs, already collected)
python scripts/build_human_eval_xlsx.py
python scripts/aggregate_human_eval_xlsx.py            # -> paper/human_eval_summary.md

# Task B - recommendation contextual relevance (needs `make serve` running)
python scripts/build_task_b_human_eval_xlsx.py         # -> paper/task_b_human_eval_template.xlsx
python scripts/aggregate_task_b_human_eval_xlsx.py     # -> paper/task_b_human_eval_summary.md
```

Each builder produces a shareable workbook with no model labels (sides are randomised) plus a local answer key; raters fill it in, drop copies in the matching `paper/*_returned/` folder, and the aggregator reports win-rate with Wilson 95% CIs and inter-rater agreement.

## For judges

The two solution papers are the place to start: `paper/paper_task_a.tex` (user modeling and review generation) and `paper/paper_task_b.tex` (recommendation). The "How this maps to the judging criteria" section above points each rubric line to its evidence. To run the system:

1. `pip install -r requirements.txt`, then `cp .env.example .env` and add an API key.
2. `make serve` and open `http://localhost:8765` to use InsideNaija and ShopEasy directly, or `http://localhost:8765/docs` to call the API.
3. To compare NaijaReviewer-8B against a frontier model on the same input, pass `backbone_override` / `reranker_override` in any `/simulate-review` or `/recommend` request.
4. `submission/naija_agent.py` is a single-file agent that conforms to the AgentSociety simulator contract for harness-based review.
5. Reproduce the model end to end with `notebooks/02_finetune.ipynb` (Colab, A100).

## Reproduce the model yourself

1. Open `notebooks/02_finetune.ipynb` in Colab and select an A100, L4, or T4 runtime.
2. Add `HF_TOKEN` (write access) and, optionally, `ANTHROPIC_API_KEY` to Colab Secrets, and accept the Llama 3.1 license on HuggingFace.
3. Run all. The notebook fine-tunes, merges, quantises, and pushes every artifact to HuggingFace in one pass (roughly 2.5 hours on an A100).

Stages are resume-safe: corpus steps skip if their output exists, training resumes from the last checkpoint, and conversion skips files already produced. `notebooks/01_build_corpus.ipynb` and `01b_build_corpus_openai.ipynb` regenerate the corpus from scratch if you want to start before the fine-tune.

## Repository structure

```
telcoproject/
  app/            FastAPI service: routers, agents, LLM client, RAG, prompts
  frontend/       React frontend: InsideNaija, ShopEasy, B2B, Lab, widget
  deploy/         Modal hosting for NaijaReviewer-8B + test client
  finetuning/     QLoRA training scripts
  notebooks/      Colab notebooks: corpus build, fine-tune, GGUF, training results
  scripts/        corpus build, index build, eval harness, human-eval tooling
  paper/          Task A and Task B papers, results, figures
  submission/     naija_agent.py simulator drop-in
  data/           sample personas + products (committed); large data gitignored
  tests/          pytest suite
```

## Team

- **Ashinze** - system, fine-tuning, model hosting, and infrastructure
- **Franca** - product and frontend
- **Esther Oyenekan** - paper and evaluation

Contact: chidi.ashinze@gmail.com

## License

- Code: MIT (see `LICENSE`)
- NaijaReviewer-8B weights: Llama 3.1 Community License
- Released datasets: CC-BY-4.0

## Citation

```bibtex
@misc{naijapersonaagent2026,
  title  = {Naija Persona Agent: Cultural-Prior-Aware Review Simulation
            and Recommendation for Nigerian Consumers},
  author = {Ashinze and Franca and Oyenekan, Esther},
  year   = {2026},
  url    = {https://github.com/Mystique1337/telcoproject}
}
```
