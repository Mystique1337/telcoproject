// Thin API client for the FastAPI service.
//
// In dev, Vite proxies /health, /simulate-review, /recommend to localhost:8765
// (see vite.config.ts). In prod we serve dist/ directly off FastAPI on :8765
// so the relative paths work without proxy config.

import type {
  ConversationTurn,
  HealthResponse,
  PanelResponse,
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

  simulateReview: (opts: {
    persona: Persona;
    product: Product;
    backbone_override?: string;
    include_reasoning?: boolean;
    target_rating?: number | null;
    aspect_focus?: string;
    length_hint?: "short" | "medium" | "long";
    tone_modifier?: string;
    refinement_instructions?: string;
    target_language?: "yoruba" | "hausa" | "igbo" | null;
  }) =>
    postJson<SimulateReviewResponse>("/simulate-review", {
      persona: opts.persona,
      product: opts.product,
      include_reasoning: opts.include_reasoning ?? true,
      backbone_override: opts.backbone_override,
      target_rating: opts.target_rating ?? null,
      aspect_focus: opts.aspect_focus || undefined,
      length_hint: opts.length_hint || undefined,
      tone_modifier: opts.tone_modifier || undefined,
      refinement_instructions: opts.refinement_instructions || undefined,
      target_language: opts.target_language || undefined,
    }),

  chat: async (opts: {
    history: ConversationTurn[];
    persona?: Persona | null;
    orchestrator_override?: string;
    reranker_override?: string;
    k?: number;
    include_reasoning?: boolean;
    language?: "yoruba" | "hausa" | "igbo" | null;
  }) => {
    const r = await fetch(`${BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        history: opts.history,
        persona: opts.persona ?? null,
        orchestrator_override: opts.orchestrator_override,
        reranker_override: opts.reranker_override,
        k: opts.k ?? 5,
        include_reasoning: opts.include_reasoning ?? false,
        language: opts.language || undefined,
      }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}: ${(await r.text()).slice(0, 200)}`);
    return r.json() as Promise<import("./types").ChatResponse>;
  },

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

  /** InsideNaija — run a product across the persona panel. */
  panel: (opts: {
    product: Product;
    persona_ids?: string[];
    backbone_override?: string;
    target_language?: "yoruba" | "hausa" | "igbo" | null;
  }) =>
    postJson<PanelResponse>("/panel", {
      product: opts.product,
      persona_ids: opts.persona_ids,
      backbone_override: opts.backbone_override,
      target_language: opts.target_language || undefined,
    }),

  // ── ShopEasy ──────────────────────────────────────────────────────────
  shopSearch: (query: string, k = 12, persona_id?: string | null, profile_id?: string | null) =>
    postJson<import("./types").ShopSearchResponse>("/shop/search", { query, k, persona_id: persona_id || undefined, profile_id: profile_id || undefined }),

  shopVisualSearch: (image_base64: string, mime: string, k = 12, persona_id?: string | null, profile_id?: string | null) =>
    postJson<import("./types").ShopSearchResponse>("/shop/visual-search", { image_base64, mime, k, persona_id: persona_id || undefined, profile_id: profile_id || undefined }),

  personas: async () => {
    const r = await fetch(`${BASE}/catalog/personas`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<{ count: number; personas: Persona[] }>;
  },

  shopProduct: async (id: string) => {
    const r = await fetch(`${BASE}/shop/product/${encodeURIComponent(id)}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<import("./types").ShopProduct>;
  },

  // ── Accounts (passwordless) ───────────────────────────────────────────
  register: (body: {
    name: string; location: string; age_range?: string;
    gender?: string; occupation?: string; interests?: string[]; language?: string;
  }) =>
    postJson<{ profile_id: string; profile: Record<string, unknown>; persona: Persona; zone: string }>(
      "/auth/register", body),

  getProfile: async (id: string) => {
    const r = await fetch(`${BASE}/auth/profile/${encodeURIComponent(id)}`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.json() as Promise<{ profile_id: string; name: string; profile: Record<string, unknown>; persona: Persona }>;
  },
};
