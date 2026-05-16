# NaijaReviewer-8B — Fine-Tuning

> Llama 3.1 8B Instruct → QLoRA → Nigerian-context review-generation model.

## TL;DR

```bash
# 1. Build the training corpus (Day 2)
poetry run python scripts/build_finetune_corpus.py \
    --out data/finetune/v1.jsonl --target_size 12000

# 2. Train (Day 2 evening — runs 6-10 hours)
poetry run python finetuning/train_naija_reviewer.py \
    --config finetuning/configs/naija_reviewer_qlora.yaml

# 3. Convert to GGUF for Ollama (Day 3 morning)
poetry run python finetuning/export_to_gguf.py \
    --checkpoint finetuning/checkpoints/naija-reviewer-v1 \
    --out naija-reviewer-8b.gguf

# 4. Pull into Ollama
ollama create naija-reviewer-8b -f finetuning/Modelfile

# 5. Flip the env flag and restart
echo "TASK1_BACKBONE=ollama:naija-reviewer-8b" >> .env
make demo
```

## Training corpus format

Each example in the JSONL is:

```json
{
  "instruction": "Simulate the review behaviour of the following Nigerian user reviewing the described product. Generate the rating (1-5) and review text exactly as this user would write it.",
  "input": {
    "persona": { ... full Persona JSON ... },
    "product": { ... product details ... },
    "register_tier": "nigerian_pidgin"
  },
  "output": {
    "rating": 4,
    "review": "Abeg, this phone good die..."
  }
}
```

## Data sources

Compose ~10-15k training examples from:

| Source | Target | Notes |
|---|---|---|
| `Idowenst/jumia_dataset` (HuggingFace) | 0 (product metadata only — no review text) | Used only for product index, not training |
| Direct Jumia scrape (Day 1) | ~3-5k | 1 req/sec; product pages with reviews |
| Letterboxd Nollywood reviews | ~2-3k | Public; Nigerian-locale filter |
| Synthetic register-balanced | ~5-7k | Claude-generated; declared `synthetic: True` |

**Synthetic policy**: real data primary. Synthetic only where coverage is missing — specifically Pidgin and code-mixed registers. All synthetic tagged.

## Hyperparameters (locked)

| | |
|---|---|
| Base | `meta-llama/Meta-Llama-3.1-8B-Instruct` |
| Method | QLoRA (4-bit NF4 via bitsandbytes) |
| LoRA `r`, `alpha`, `dropout` | 16, 32, 0.1 |
| LoRA target modules | `q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj` |
| Max seq length | 4096 |
| Precision | bf16 |
| Optimiser | AdamW 8-bit |
| Learning rate | 2e-4, cosine schedule, 100 warmup steps |
| Batch size | 4 per device × grad_accum 8 = effective 32 |
| Epochs | 2 (early-stop on val loss) |
| Random seed | 42 |

## Compute and time

- 1× A100 40GB (your access) — confirmed
- Single run: ~6-10 hours
- VRAM: ~22GB for 8B QLoRA at seq=4096, batch=4

## Evaluation (Day 3)

Head-to-head on the held-out test split:

| Model | RMSE ↓ | BERTScore ↑ | Register match ↑ | Cultural marker recall ↑ |
|---|---|---|---|---|
| Vanilla Claude Sonnet 4 | TBD | TBD | TBD | TBD |
| Vanilla GPT-4o | TBD | TBD | TBD | TBD |
| Base Llama 3.1 8B Instruct | TBD | TBD | TBD | TBD |
| **NaijaReviewer-8B (ours)** | TBD | TBD | TBD | TBD |

Run with 3 seeds; report mean ± std.

## Release artifacts (Day 5)

- HuggingFace repo: `<team>/naija-reviewer-8b` — full LoRA adapter + merged weights + GGUF Q4_K_M
- Model card: intended use, training recipe, bias acknowledgments, carbon footprint estimate, citation block
- License: Llama 3.1 Community License

## Carbon footprint estimate

| Item | Value |
|---|---|
| GPU type | A100 40GB |
| Wattage (active) | ~400W |
| Training time | ~8 hours |
| Total energy | ~3.2 kWh |
| Regional g CO₂/kWh | ~400 g/kWh |
| **Carbon** | **~1.3 kg CO₂eq** |

Report this in the model card and paper Section 7 (Limitations / Ethics).

## Fallback if training underperforms

If NaijaReviewer-8B v1 does not beat vanilla Claude on any axis, the paper claim shifts to:
**"we narrow the open-weight gap from X to Y"** — the architectural contribution (persona + register-aware prompting) stands independently of the fine-tune.
