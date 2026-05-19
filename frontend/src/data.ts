// Static config — model registry + eval headline numbers.
//
// Personas and products are NOT bundled here; they're served as JSON from the
// FastAPI static-files mount or loaded via separate fetches once we wire that.
// For now we ship a tiny built-in fallback set so the UI is usable without
// the backend mount.

export interface ModelOption {
  label: string;
  spec: string;
  badge?: string;
  /** Which task this model is good at. Used to surface guidance in the UI. */
  bestFor: "review" | "rank" | "both";
}

export const MODELS: ModelOption[] = [
  // ── Our fine-tune ────────────────────────────────────────────────────
  {
    label: "NaijaReviewer-8B",
    spec: "lmstudio:naija-reviewer-8b",
    badge: "🇳🇬 fine-tune · local",
    bestFor: "review",   // Task A only — emits prose, not JSON
  },

  // ── Frontier (closed-source) ────────────────────────────────────────
  {
    label: "Claude Sonnet 4",
    spec: "anthropic:claude-sonnet-4-20250514",
    badge: "Anthropic · frontier",
    bestFor: "both",
  },
  {
    label: "GPT-4o",
    spec: "openai:gpt-4o",
    badge: "OpenAI · frontier",
    bestFor: "both",
  },
  {
    label: "GPT-4o mini",
    spec: "openai:gpt-4o-mini",
    badge: "OpenAI · cheap",
    bestFor: "both",
  },

  // ── Open-source via Ollama Cloud (hosted) ────────────────────────────
  {
    label: "GPT-OSS 120B",
    spec: "ollama-cloud:gpt-oss:120b",
    badge: "Ollama Cloud · open",
    bestFor: "both",
  },
  {
    label: "Qwen3 Coder 480B",
    spec: "ollama-cloud:qwen3-coder:480b",
    badge: "Ollama Cloud · open",
    bestFor: "both",
  },
  {
    label: "DeepSeek V3.1 671B",
    spec: "ollama-cloud:deepseek-v3.1:671b",
    badge: "Ollama Cloud · paid sub",
    bestFor: "both",
  },

  // ── Open-source via HuggingFace Inference ───────────────────────────
  {
    label: "Llama 3.3 70B (HF)",
    spec: "hf:meta-llama/Llama-3.3-70B-Instruct",
    badge: "HF Inference · open",
    bestFor: "both",
  },
  {
    label: "Qwen 2.5 72B (HF)",
    spec: "hf:Qwen/Qwen2.5-72B-Instruct",
    badge: "HF Inference · open",
    bestFor: "both",
  },
  {
    label: "Mixtral 8x7B (HF)",
    spec: "hf:mistralai/Mixtral-8x7B-Instruct-v0.1",
    badge: "HF Inference · open",
    bestFor: "both",
  },

  // ── Open-source via NVIDIA NIM (free tier) ──────────────────────────
  {
    label: "Llama 3.3 70B (NIM)",
    spec: "nvidia:meta/llama-3.3-70b-instruct",
    badge: "NIM · free tier",
    bestFor: "both",
  },

  // ── Local Ollama / base ────────────────────────────────────────────
  {
    label: "Llama 3.1 8B base",
    spec: "ollama:llama3.1:8b-instruct",
    badge: "local Ollama · base",
    bestFor: "both",
  },
];

export function modelLabel(spec: string): string {
  return MODELS.find((m) => m.spec === spec)?.label ?? spec;
}

export function modelBestFor(spec: string): "review" | "rank" | "both" | undefined {
  return MODELS.find((m) => m.spec === spec)?.bestFor;
}

// Live eval numbers — read from paper/results.json. Falls back to a tiny
// known-good baseline if the file isn't reachable (so the UI is never broken
// in early environments).
export const EVAL_FALLBACK = {
  naija_rmse: 1.114,
  claude_rmse: 1.319,
  naija_bert: 0.858,
  claude_bert: 0.857,
  naija_ndcg10: 0.623,
  claude_ndcg10: 0.485,
  naija_overall: 0.787,
  claude_overall: 0.795,
  n_task1: 100,
  n_task2: 17,
};
