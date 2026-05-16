# Naija Persona Agent (NPA)

> A Nigerian-context LLM agent system for review simulation and personalised product recommendation. Submission to the Nigerian AI Agents Hackathon, May 2026.

Vanilla LLM agents carry an implicit Western cultural prior. On Nigerian users this shows up as compressed rating intensity, flattened Pidgin/Nigerian-English register, individualised framing, and misread religious markers. **NPA** makes the cultural prior visible, recovers it with a structured cognitive persona representation + register-aware prompting + a fine-tuned open-weight Llama 3.1 8B model (**NaijaReviewer-8B**), and ships it as two production-ready API endpoints.

> 📄 **Paper**: `paper/paper.pdf` *(drafted Day 4–5)*
> 🤗 **Model**: `huggingface.co/<org>/naija-reviewer-8b` *(released Day 4)*
> 📊 **Corpus**: `huggingface.co/datasets/<org>/npa-corpus-v1` *(~20k Nigerian reviews, released Day 4)*
> 🌐 **Demo**: `[deployment URL]` *(deployed Day 4)*

## Two endpoints (per hackathon brief)

| Endpoint | Input | Output |
|---|---|---|
| `POST /simulate-review` | `{persona, product}` | `{rating, review, register_tier, rationale}` |
| `POST /recommend` | `{persona, candidate_set?, k}` | `{recommendations: [{product_id, score, rationale}, ...]}` |

Both share a structured `Persona` representation (4 cognitive dimensions + register tier + aspect priorities + history anchors).

## Train the model (Colab, Drive-persisted, resume-safe)

**The fastest path to a working NaijaReviewer-8B is the end-to-end Colab notebook**: build the ~20k corpus, QLoRA fine-tune Llama 3.1 8B, eval head-to-head against Claude + Nemotron baselines, and push everything to HuggingFace — in one notebook, ~3–4 hours on an A100.

1. **Open in Colab**: `File → Open notebook → GitHub → Mystique1337/telcoproject → notebooks/naija_reviewer_8b_end_to_end.ipynb`
2. **Runtime → Change runtime type → A100** (or whatever GPU you have — the notebook auto-tunes batch size for H100/A100/L4/T4)
3. **Add three secrets** to Colab Secrets (sidebar key icon): `NVIDIA_API_KEY`, `ANTHROPIC_API_KEY`, `HF_TOKEN`
4. **Runtime → Run all** — walk away

Everything writes to `Drive/MyDrive/naija-persona-agent/`. If Colab disconnects mid-run, **just re-open the notebook and Run all again** — corpus stages skip if their JSONL exists, training resumes from the last `checkpoint-XXXX`, the merged model skips if already present.

Full notebook docs in `notebooks/naija_reviewer_8b_end_to_end.ipynb`.

## Serve the API locally (after the model trains)

```bash
# 1. Clone
git clone https://github.com/Mystique1337/telcoproject
cd telcoproject

# 2. Configure
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY, OPENAI_API_KEY, (optional) HF_TOKEN

# 3. Bring up the stack
make demo
# Expected: ✅ Demo up — visit http://localhost:8000/docs
```

If `make demo` exits clean within ~30 seconds, the API is live at `http://localhost:8000/docs` (interactive Swagger UI). Until NaijaReviewer-8B is trained and pulled into Ollama, the Task 1 backbone defaults to Claude Sonnet 4 via API — see Section "Switch to local NaijaReviewer-8B" below.

## Curl examples

### Task 1 — Generate a review

```bash
curl -X POST http://localhost:8000/simulate-review \
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
      "review_anchors": [],
      "extraction_source": "synthetic"
    },
    "product": {
      "product_id": "TECNO-SPARK-10",
      "title": "Tecno Spark 10 — 128GB",
      "category": "Phone & Tablet",
      "description": "6.6 inch display, 5000mAh battery, dual SIM"
    }
  }'
```

### Task 2 — Recommend products

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "persona": {... same as above ...},
    "k": 5,
    "domain": "jumia"
  }'
```

Full request/response schemas at `http://localhost:8000/docs`.

## Switch to local NaijaReviewer-8B (after training)

Once the notebook finishes training and you have the merged model on HuggingFace:

```bash
# On your local machine (you'll need llama.cpp built)
git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp && make

# Download merged model from HF
huggingface-cli download <org>/naija-reviewer-8b --local-dir ./naija-reviewer-merged

# Convert + quantize to GGUF for Ollama
python3 convert_hf_to_gguf.py ./naija-reviewer-merged --outfile naija-reviewer-8b-f16.gguf --outtype f16
./llama-quantize naija-reviewer-8b-f16.gguf naija-reviewer-8b-Q4_K_M.gguf Q4_K_M

# Register with Ollama
cp naija-reviewer-8b-Q4_K_M.gguf <repo>/finetuning/
cd <repo> && ollama create naija-reviewer-8b -f finetuning/Modelfile

# Flip the backbone in .env, restart the container
echo "TASK1_BACKBONE=ollama:naija-reviewer-8b" >> .env
make down && make demo
```

Now `/simulate-review` is served by your local fine-tuned model — zero API cost.

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
│ 8B (Ollama) +  │    │ Claude         │
│ Claude fallback│    │ re-rank + MMR  │
└────────────────┘    └────────────────┘
        │                     │
        └─────────┬───────────┘
                  ▼
         ┌──────────────────┐
         │ Chroma + SQLite  │
         └──────────────────┘
```

See PRD at `PRD/PRD_v4_NPA_5Day.md` for the full architecture rationale.

## Repository structure

```
telcoproject/
├── app/                  FastAPI application
│   ├── api/              routers, schemas, main
│   ├── agents/           persona extractor, review agent, recommend agent
│   ├── llm/              Ollama + Claude + OpenAI client abstraction
│   ├── rag/              Chroma vector store wrapper
│   ├── data/             loaders, persona cache
│   └── prompts/          Jinja templates per domain / register tier
├── data/                 datasets (gitignored at scale; samples committed)
├── finetuning/           NaijaReviewer-8B QLoRA training scripts
├── frontend/             Streamlit (or Next.js) judge demo
├── demo/                 Streamlit app (entry point)
├── paper/                LaTeX paper sources + figures
├── scripts/              build / eval / deploy scripts
├── tests/                pytest test suite
├── notebooks/            exploratory notebooks
└── PRD/                  product requirements + build plan + vision docs
```

## Documentation

| Doc | Purpose |
|---|---|
| `PRD/PRD_v4_NPA_5Day.md` | Operational PRD for the 5-day build |
| `PRD/BUILD_PLAN_5DAY.md` | Day-by-day execution plan |
| `PRD/PRD_v3_Naija_Persona_Agent_AllOut.md` | Vision document (post-hackathon roadmap) |
| `JUDGES.md` | For the hackathon panel |
| `finetuning/README.md` | Reproduce NaijaReviewer-8B from scratch |
| `frontend/README.md` | Frontend setup notes for Franca |
| `paper/README.md` | Paper drafting notes for the writer |

## Team

- **Ashinze** — system & fine-tuning (`ashinze@bluebulb.co.uk`)
- **Franca** — product & frontend
- **[3rd]** — paper & evaluation

## License

- **Code**: MIT
- **NaijaReviewer-8B weights**: Llama 3.1 Community License (when released)
- **Datasets we release**: CC-BY-4.0

## Citation

```bibtex
@misc{npa2026,
  title={Naija Persona Agent: A Cultural-Prior-Aware LLM Agent for Nigerian Review Simulation and Recommendation},
  author={Ashinze, Franca, and team},
  year={2026},
  url={https://github.com/Mystique1337/telcoproject}
}
```

## Acknowledgments

AfriSenti, NaijaSenti, SentiLeye, Masakhane community, AgentSociety Challenge organisers, and the Nigerian AI Agents Hackathon panel.
