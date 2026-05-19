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
  {
    label: "NaijaReviewer-8B",
    spec: "lmstudio:naija-reviewer-8b",
    badge: "🇳🇬 fine-tune · local",
    bestFor: "review",   // Task A only — emits prose, not JSON
  },
  {
    label: "Claude Sonnet 4",
    spec: "anthropic:claude-sonnet-4-20250514",
    badge: "Anthropic · API",
    bestFor: "both",
  },
  {
    label: "GPT-4o",
    spec: "openai:gpt-4o",
    badge: "OpenAI · API",
    bestFor: "both",
  },
  {
    label: "GPT-4o mini",
    spec: "openai:gpt-4o-mini",
    badge: "OpenAI · cheap",
    bestFor: "both",
  },
  {
    label: "Llama 3.3 70B",
    spec: "nvidia:meta/llama-3.3-70b-instruct",
    badge: "NIM · free tier",
    bestFor: "both",
  },
  {
    label: "Llama 3.1 8B base",
    spec: "ollama:llama3.1:8b-instruct",
    badge: "Ollama · base",
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
