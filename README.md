# Naija Persona Agent

**A Nigerian-context LLM agent system for review simulation and personalised product recommendation.**

Submission to the **DSN X BCT LLM Agent Challenge**.

- **Live app:** <https://switteefranca2-0--naijapersona-web.modal.run/>
- **Paper, Task A (User Modelling):** `paper/USER_MODELLING_TASK.pdf`
- **Paper, Task B (Recommendation):** `paper/RECOMMENDATION_PAPER.pdf`
- **Model weights (GGUF):** <https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF>
- **Training corpus:** <https://huggingface.co/datasets/Shinzmann/npa-corpus-v1>

---

## The thesis

General-purpose LLM agents trained on predominantly Western web data carry an implicit **cultural prior**. When prompted to simulate a Nigerian shopper, frontier models compress rating intensity, flatten Pidgin and Nigerian-English register into a sanitised international voice, default to individualistic framing, and routinely misread cultural and religious markers. This project measures that gap and recovers it for the Nigerian context through three coordinated mechanisms:

1. A structured **cognitive persona** representation (four behavioural dimensions plus a Nigerian register tier).
2. Register-aware prompting grounded in that persona.
3. **NaijaReviewer-8B**, an open-weight Llama 3.1 8B model QLoRA-fine-tuned on Nigerian product reviews, served as the review-generation and re-ranking backbone.

The system ships as a FastAPI service plus a React frontend that exposes two products.

## Headline results

**Task A (review generation), 100-row held-out test split.**

| Metric | NaijaReviewer-8B | Claude Sonnet 4 |
|---|---|---|
| RMSE (lower is better) | **1.114** | 1.319 |
| BERTScore F1 | 0.858 | 0.857 |
| AgentSociety `preference_estimation` | **0.792** | 0.784 |
| Human-rater win-rate (5 raters, 50 pairs) | **48.5%** (CI 40.2 to 56.9) | 51.5% |

A 15.5% RMSE reduction over Claude at roughly 17 times fewer parameters; Nigerian human raters judge the two systems at parity on prose authenticity.

**Task B (recommendation), held-out persona scenarios.**

| Re-ranker | Params | NDCG@10 | HR@5 |
|---|---|---|---|
| **NaijaReviewer-8B** | **8B** | **0.588** | **0.648** |
| GPT-OSS-120B | 120B | 0.441 | 0.370 |
| Claude Sonnet 4 | n/d | 0.433 | 0.392 |
| Llama-3.3-70B | 70B | 0.425 | 0.354 |
| Qwen-2.5-72B | 72B | 0.404 | 0.324 |

NaijaReviewer-8B leads NDCG@10 against four heavyweight baselines at 9 to 15 times fewer parameters and zero per-call API cost.

## The two products

The same FastAPI service powers four end-user surfaces.

| Surface | Audience | What it does |
|---|---|---|
| **InsideNaija** | Analysts, brand teams | Synthetic 24-persona panel that returns ratings, register-correct reviews, and aggregates for any product description. |
| **ShopEasy** | Nigerian shoppers | Storefront with text, image, voice, and conversational search powered by persona-aware recommendation. |
| **NaijaPersona Lab** | Developers | Console for driving the raw endpoints, A/B-ing across eleven LLM backbones, and inspecting the agent's reasoning trace. Experiment history is persisted in Supabase. |
| **B2B widget** | External sites | iframe-embeddable persona-aware recommendation widget. |

## Navigating the live app

Open <https://switteefranca2-0--naijapersona-web.modal.run/>. The Modal endpoint scales to zero, so the first request may take ten to fifteen seconds to warm; subsequent requests are fast. From the landing page:

| Click | Where it takes you | What to try |
|---|---|---|
| **InsideNaija** (default home) | The synthetic-panel interface. | Type a product description (for example *"Tecno Spark 10 mobile phone, 4 GB RAM, 64 GB storage, 5,000 mAh battery, NGN 145,000"*) and run the panel. You will see a 24-persona reaction stream with star ratings, register-tagged reviews, and aggregates by zone, age band, and register. Click any reaction to expand the persona detail and the reasoning. |
| **ShopEasy** (top nav) | The Nigerian-shopper storefront. | Try the text search (for example *"affordable phone under 100k"*), the voice search (microphone icon), and the image search (upload any product photo). Click into a product to see specs, simulated reviews from the panel, and a "why this for you" rationale. The chat icon opens the conversational assistant; try refining the budget mid-conversation. |
| **NaijaPersona Lab** (top nav, after sign-in) | The developer console. | Run a side-by-side A/B between any two of the eleven supported LLM backbones on the same persona and product. Inspect the structured reasoning trace each one returns. Every run is saved to your experiment history; click any past run to re-open or share. |
| **B2B widget** | Demonstration of the embeddable iframe. | Register a business, copy the generated iframe snippet, and confirm the recommendation surface renders inside the snippet. |
| **Sign in** (top right) | Supabase magic link. | Sign in with any email; you will receive a magic link. After login an onboarding wizard builds your personal persona which is used to personalise both panel and storefront responses from that session onwards. |

If the live link is asleep when you click it, the first request triggers the warm-up. No action is required.

## How judges should evaluate this

### Fastest path: try the live app
Visit <https://switteefranca2-0--naijapersona-web.modal.run/>. The Modal endpoint scales to zero, so the first request may take a few seconds to warm. Both InsideNaija and ShopEasy work out of the box.

### Read the papers
Both PDFs are checked in:
- `paper/USER_MODELLING_TASK.pdf` covers user modelling and review generation.
- `paper/RECOMMENDATION_PAPER.pdf` covers persona-aware recommendation.

The `.tex` sources, `references.bib`, and figures are alongside them.

### Run it locally
Prerequisites: Python 3.11, an Anthropic or OpenAI API key, and (optionally) Node.js 20+ if you want to rebuild the frontend.

```bash
git clone https://github.com/Mystique1337/telcoproject
cd telcoproject

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Configure (only ANTHROPIC_API_KEY or OPENAI_API_KEY is strictly required)
cp .env.example .env
# Open .env and fill in your API key.
# MODAL_BASE_URL is already wired to the hosted NaijaReviewer-8B endpoint,
# so no local GPU is needed.

# 3. Run the API and the bundled frontend
make serve
```

Open `http://localhost:8765` for the products and `http://localhost:8765/docs` for the interactive API.

To rebuild the frontend yourself:

```bash
cd frontend_v2
npm install
npm run build
```

### Reproduce the evaluations
With the service running:

```bash
make eval-fidelity     # quick: register-fidelity, no ground truth needed
make eval              # full: RMSE, BERTScore, ROUGE-L, NDCG@10, HR@k
```

Results write to `paper/results.json` and `paper/results.md`. The Task B human relevance eval and the Task A blind A/B human eval are reproducible through the scripts in `scripts/` (see "Human evaluation" below).

### Reproduce the model
End-to-end, on Colab with a single A100:

1. `notebooks/01_build_corpus.ipynb` (or `01b_build_corpus_openai.ipynb`) builds the training corpus from the public Jumia review dump and product catalogue.
2. `notebooks/02_finetune.ipynb` runs the QLoRA fine-tune, merges the adapter, converts to GGUF, and pushes to HuggingFace.
3. `notebooks/03_training_results.ipynb` pulls the training run history from Weights and Biases.

The whole pipeline takes about 2.5 hours end-to-end on an A100.

### Inspect the inference deployment
`deploy/modal_naija.py` is the Modal app that hosts NaijaReviewer-8B as an OpenAI-compatible endpoint. `deploy/test_modal.py` is a small client that smoke-tests it:

```bash
python deploy/test_modal.py https://chidi-ashinze--naija-reviewer-serve.modal.run
```

`modal_deploy.py` is the full web-app Modal deployment (FastAPI + the built React frontend), which is what runs at the live URL above.

## Architecture

```
        Client tier      InsideNaija  /  ShopEasy  /  Lab  /  B2B widget   +   Supabase auth
                                              |
        API tier                        FastAPI service
                                              |
              -----------------------------------------------------
              |                          |                        |
   Pinecone retrieval        Cohere cross-encoder        LLM provider gateway
   (llama-text-embed-v2)     (rerank-v3.5, Stage 2.5)    (Modal, Anthropic, OpenAI,
                                                          HuggingFace, Ollama Cloud)
              |                          |                        |
              -----------------------------------------------------
                                              |
                            Modal serverless L4 GPU
                            NaijaReviewer-8B (Q4_K_M GGUF, llama.cpp)
                                              |
                            HuggingFace (model + corpus)  +  GitHub (code)
```

Both Task A and Task B papers include a higher-fidelity rendering of this diagram (TikZ, in the `.tex`).

## Agentic workflow: where to read the code

The "agentic" surface is concentrated in five files. Each is heavily commented to explain the *why* (architectural decision) as well as the *what* (code mechanics), so a judge reading them top to bottom can follow the reasoning.

| File | Agent | What its workflow does |
|---|---|---|
| `app/agents/review_agent.py` | **Review generator** (Task A) | Picks the register-aware prompt template by persona tier, renders the Jinja template against the persona JSON, dispatches to the configured backbone, parses the rating and review out of the response, optionally runs a second-pass refinement loop, and returns the structured rationale. |
| `app/agents/panel_agent.py` | **Multi-persona panel** (Task A) | Fans out review generation across the 24 persona library in parallel, aggregates star ratings, sentiment, register-tagged themes, and buy-likelihood by zone, age band, and register, and returns the aggregate object the InsideNaija UI consumes. |
| `app/agents/recommend_agent.py` | **Recommendation re-ranker** (Task B) | Six explicit stages: scenario detection (cold-start / cross-domain / multi-turn), constraint extraction from the persona and conversation, Pinecone dense retrieval, optional Cohere Stage-2.5 pre-rerank, persona-aware LLM re-rank with index-based scoring, and an MMR diversity pass. Each stage writes into the reasoning trace. |
| `app/agents/chat_agent.py` | **Conversational shopper** (Task B) | Handles multi-turn refinement: detects budget changes mid-chat, parses category and constraint updates from natural language, re-issues a recommendation call with the refined persona view, and stitches the dialog state into a coherent reply. |
| `app/agents/visual_search.py` | **Image-to-recommendation** | Pulls product features out of a user-uploaded image, projects into the same embedding space as the catalogue, and hands off to the recommendation re-ranker so the same persona-aware pipeline handles visual queries. |

Two further pieces sit underneath the agents:

- `app/llm/client.py` is the unified LLM provider gateway. One `complete(...)` interface dispatches to eleven backbones (Anthropic, OpenAI, NVIDIA NIM, HuggingFace Inference, Ollama Cloud, LM Studio, freemodel.dev, our Modal endpoint, etc.); the comments at the top explain the dispatch contract, the JSON-following parser, and the 429 backoff strategy that lets the multi-backbone re-ranker comparison run without silent fallbacks.
- `app/rag/` contains the Pinecone retrieval wrappers and the Chroma local fallback. The asymmetric query / passage encoding rationale is documented in the module header.

Every recommendation and chat response carries a `reasoning_trace` field that lets you read each stage's input, decision, and output without diving into the code; it is the agent's narrative of its own work. The Lab UI renders this trace alongside the response.

## API reference

The service exposes the following routes (full schemas at `/docs`):

| Endpoint | Purpose |
|---|---|
| `POST /simulate-review` | Generate one persona-grounded review for a product. |
| `POST /panel` | InsideNaija multi-persona synthetic panel with aggregates. |
| `POST /recommend` | Persona-aware ranked recommendations. |
| `POST /chat` | Conversational shopping assistant with budget and follow-up handling. |
| `POST /elicit` | Build a persona from a short interview. |
| `GET/POST /shop/*` | Text, image, and voice search for ShopEasy. |
| `POST /auth/*` | Passwordless accounts and stored personas. |
| `POST /b2b/*` | Business registration and embeddable recommendations. |
| `GET /tts/*` | Nigerian text-to-speech voices (YarnGPT). |
| `GET /catalog/*` | Products, personas, categories, evaluation summary. |

Every request supports `backbone_override` or `reranker_override`, so two backbones can be compared on the exact same input without restarting the server.

## The model: NaijaReviewer-8B

- Base: `meta-llama/Meta-Llama-3.1-8B-Instruct`.
- Adapter: LoRA r=16, alpha=32, dropout 0.1; targets q/k/v/o/up/gate/down (0.52% trainable parameters).
- Quantisation: 4-bit NF4 weights, paged AdamW 8-bit optimiser, gradient checkpointing.
- Framework: Unsloth on a single A100-40GB.
- Loss: response-only loss with EOS-terminated training (so the model learns to stop cleanly in production).
- Distribution: merged FP16 plus GGUF (Q4_K_M, Q5_K_M, Q8_0).
- Inference host: **Modal** serverless L4 GPU (open OpenAI-compatible endpoint, scales to zero).

The unified `LLMClient` in `app/llm/client.py` dispatches between Anthropic, OpenAI, NVIDIA NIM, HuggingFace Inference, Ollama Cloud, LM Studio, freemodel.dev, and the Modal endpoint, swappable per request through the `backbone_override` field.

## Human evaluation

Two blind A/B instruments are released alongside the system.

```bash
# Task A: review quality / behavioural fidelity (5 raters, 50 pairs, collected)
python scripts/build_human_eval_xlsx.py
python scripts/aggregate_human_eval_xlsx.py
#   -> paper/human_eval_summary.md

# Task B: recommendation contextual relevance (3 raters, 24 scenarios, collected)
python scripts/build_task_b_human_eval_xlsx.py
python scripts/aggregate_task_b_human_eval_xlsx.py
#   -> paper/task_b_human_eval_summary.md
```

Each builder produces a shareable workbook with no model labels (sides randomised) plus a local answer key; raters fill it in, returned copies drop into `paper/*_returned/`, and the aggregator reports win-rate (Wilson 95% CI), mean per-system relevance, and Krippendorff alpha.

## Data sources

- **Real Jumia reviews (~76k)** from the public `aymane-maghouti/Sentiment-Analysis-for-Jumia-Reviews-and-Smartphone-Price-Prediction-System` repository on GitHub, used as Pipeline 1 seed.
- **Real Jumia product catalogue (~18k)** from the `Idowenst/jumia_dataset` HuggingFace dataset, filtered to 6,657 products and used as Pipeline 2 seed plus the Pinecone retrieval index.
- **Synthetic expansion to ~20k Alpaca-style instruction/response pairs** via NVIDIA Nemotron and OpenAI gpt-5.5, stratified 90/5/5 by register tier.

The final corpus is released as `Shinzmann/npa-corpus-v1` on HuggingFace.

## Repository layout

```
telcoproject/
  app/                 FastAPI service: routers, agents, LLM client, RAG, prompts
  frontend_v2/         React + Vite + TypeScript + Tailwind frontend
  deploy/              Modal deployment of NaijaReviewer-8B + test client
  modal_deploy.py      Modal deployment of the full FastAPI + frontend stack
  notebooks/           Colab notebooks: corpus build, fine-tune, training results
  scripts/             Corpus build, Pinecone index, eval harness, human-eval tooling
  paper/               Final papers (Task A + Task B), figures, references, eval outputs
  data/                Sample personas and products; large datasets are pulled at build time
  tests/               pytest suite
```

## Configuration

Set in `.env` (see `.env.example`):

| Variable | Purpose | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` | Frontier LLM for re-ranking and persona extraction | At least one |
| `MODAL_BASE_URL` | Hosted NaijaReviewer-8B endpoint (pre-filled) | No |
| `PINECONE_API_KEY` | Vector retrieval over 6,657 Jumia products | Optional (Chroma fallback) |
| `COHERE_API_KEY` | Stage 2.5 cross-encoder pre-rerank | Optional (auto-skips) |
| `HF_TOKEN` | Required only to rerun the corpus / fine-tune notebooks | Optional |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | Passwordless auth and experiment history in the V2 frontend | Optional |

`TASK1_BACKBONE=modal:naija-reviewer-8b` is the default review backbone; any of the supported providers can be swapped in.

## Team

- **Ashinze Emmanuel**, International University of Applied Sciences, Germany. System, fine-tuning, and infrastructure.
- **Franca Uvere**, University of Lagos, Nigeria. Product and frontend.
- **Esther Oyenekan**, MIVA Open University, Nigeria. Paper and evaluation.

Contact: chidi.ashinze@gmail.com

## License

- Code: MIT (see `LICENSE`).
- NaijaReviewer-8B weights: Llama 3.1 Community License.
- Released datasets: CC-BY-4.0.

## Citation

```bibtex
@misc{naijapersonaagent2026,
  title  = {Naija Persona Agent: Cultural-Prior-Aware Review Simulation
            and Recommendation for Nigerian Consumers},
  author = {Ashinze, Emmanuel and Uvere, Franca and Oyenekan, Esther},
  year   = {2026},
  url    = {https://github.com/Mystique1337/telcoproject}
}
```

## Acknowledgement of generative-AI use

Generative AI was used during the development of this submission. Concretely:

- **Coding assistant.** An LLM assistant supported parts of the implementation work (FastAPI endpoints, evaluation harness, frontend scaffolding, paper LaTeX). All code was reviewed, tested, and adapted by the authors; we take full responsibility for correctness.
- **Synthetic data generation.** The training corpus for NaijaReviewer-8B is partly synthesised by NVIDIA Nemotron and OpenAI GPT-class models, anchored on a public seed of real Jumia reviews and a real Jumia product catalogue. The two pipelines, the seed sources, and the final dataset are fully documented above and released openly.
- **LLM-as-Judge evaluation.** Three frontier LLMs (GPT-5.5, Claude Sonnet 4, Llama-3.3-70B) acted as automated arbiters in the behavioural-fidelity study. Their verdicts are reported alongside the authoritative five-rater Nigerian human-eval, with the disagreement between the two arbiters discussed as a finding in its own right.
- **Frontier baselines.** Claude Sonnet 4, GPT-OSS-120B, Llama-3.3-70B, and Qwen-2.5-72B are evaluated as comparison backbones; their use is purely for benchmarking, with no fine-tuning or distillation from them.

The system's headline contribution, the cognitive persona schema, the QLoRA fine-tune, the multi-stage agentic pipeline, the evaluation methodology, and the product surfaces, was designed and validated by the team.
