// Thin API client for the FastAPI service.
//
// In dev, Vite proxies /health, /simulate-review, /recommend to localhost:8765
// (see vite.config.ts). In prod we serve dist/ directly off FastAPI on :8765
// so the relative paths work without proxy config.

import type {
  ConversationTurn,
  HealthResponse,
  Persona,
  Product,
  RecommendResponse,
  SimulateReviewResponse,
} from "./types";

const BASE = ""; // same-origin in prod; proxied in dev

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new Error(`HTTP ${r.status}: ${text.slice(0, 200)}`);
  }
  return r.json();
}

async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export const api = {
  health: () => getJson<HealthResponse>("/health"),

  /** Server-side product search (no arbitrary cap on the client side). */
  searchProducts: async (
    opts: { search?: string; category?: string; limit?: number } = {},
  ) => {
    const params = new URLSearchParams();
    if (opts.search) params.set("search", opts.search);
    if (opts.category && opts.category !== "all") params.set("category", opts.category);
    params.set("limit", String(opts.limit ?? 80));
    const r = await fetch(`${BASE}/catalog/products?${params}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<{ total: number; limit: number; products: any[] }>;
  },

  /** Categories with counts. */
  categories: async () => {
    const r = await fetch(`${BASE}/catalog/categories`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<{ count: number; categories: { name: string; n: number }[] }>;
  },

  simulateReview: (
    persona: Persona,
    product: Product,
    backboneOverride?: string,
    includeReasoning = true,
  ) =>
    postJson<SimulateReviewResponse>("/simulate-review", {
      persona,
      product,
      include_reasoning: includeReasoning,
      backbone_override: backboneOverride,
    }),

  recommend: (opts: {
    persona: Persona;
    candidate_set?: string[];
    domain?: string;
    k?: number;
    include_reasoning?: boolean;
    reranker_override?: string;
    conversation_history?: ConversationTurn[];
  }) =>
    postJson<RecommendResponse>("/recommend", {
      persona: opts.persona,
      candidate_set: opts.candidate_set,
      domain: opts.domain ?? "jumia",
      k: opts.k ?? 5,
      include_reasoning: opts.include_reasoning ?? true,
      reranker_override: opts.reranker_override,
      conversation_history: opts.conversation_history,
    }),
};
