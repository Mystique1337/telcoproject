// API types — must stay in sync with app/api/schemas/

export interface Persona {
  user_id: string;
  demographics?: {
    age_range?: string;
    location?: string;
    occupation?: string;
  };
  hedonic_utilitarian: number;
  intensity_calibration: Record<string, number>;
  communal_individual: number;
  aspect_priority: Record<string, number>;
  register_tier: "standard_english" | "nigerian_english" | "nigerian_pidgin" | "code_mixed";
  register_markers: string[];
  register_confidence: number;
  review_anchors: ReviewAnchor[];
  history_count: number;
  extraction_source: string;
  schema_version?: string;
}

export interface ReviewAnchor {
  review_id: string;
  product_id: string;
  rating: number;
  text: string;
}

export interface Product {
  product_id: string;
  title: string;
  category?: string;
  brand?: string;
  price_naira?: number | null;
  description?: string;
  seller?: string;
  domain?: string;
}

export interface TraceNode {
  node: string;
  summary?: string;
  [key: string]: unknown;
}

export interface SimulateReviewResponse {
  rating: number;
  review: string;
  register_tier: string;
  rationale: string;
  fallback_reason?: string | null;
  reasoning_trace?: TraceNode[] | null;
  latency_ms: number;
  language?: string | null;
  original_review?: string | null;
}

export type NaijaLanguage = "yoruba" | "hausa" | "igbo";

// ── InsideNaija panel ──────────────────────────────────────────────────────
export interface PanelReaction {
  persona_id: string;
  location?: string | null;
  zone: string;
  age_range?: string | null;
  occupation?: string | null;
  register_tier: string;
  rating: number;
  review: string;
  language?: string | null;
  original_review?: string | null;
  sentiment: "positive" | "neutral" | "negative";
}

export interface CohortStat {
  n: number;
  avg_rating: number;
  buy_likelihood: number;
}

export interface PanelAggregate {
  n_personas: number;
  avg_rating: number;
  rating_distribution: Record<string, number>;
  buy_likelihood: number;
  sentiment_split: { positive: number; neutral: number; negative: number };
  by_register: Record<string, CohortStat>;
  by_zone: Record<string, CohortStat>;
  by_age: Record<string, CohortStat>;
  themes: { praised: string[]; complaints: string[] };
}

export interface PanelResponse {
  product_title: string;
  reactions: PanelReaction[];
  aggregate: PanelAggregate;
  backbone?: { primary: string; fallback: string; fallback_used: number };
  rmse_band?: number;
  latency_ms: number;
}

// ── ShopEasy ───────────────────────────────────────────────────────────────
export interface ShopProduct {
  product_id: string;
  title: string;
  category?: string | null;
  price_naira?: number | null;
  description?: string;
  score?: number;
  rationale?: string | null;
}

export interface ShopPersonaInfo {
  user_id: string;
  register_tier: string;
  demographics: { age_range?: string; location?: string; occupation?: string };
}

export interface ShopSearchResponse {
  query: string;
  detected?: string;
  persona?: ShopPersonaInfo | null;
  products: ShopProduct[];
}

export interface RecommendItem {
  product_id: string;
  title?: string;
  price_naira?: number | null;
  category?: string | null;
  score: number;
  rationale: string;
  serendipity_score?: number | null;
  rank: number;
}

export interface RecommendResponse {
  recommendations: RecommendItem[];
  negatives?: RecommendItem[] | null;
  cold_start?: boolean | null;
  cross_domain?: boolean | null;
  multi_turn?: boolean | null;
  extracted_constraints?: string[] | null;
  rerank_fallback_reason?: string | null;
  reasoning_trace?: TraceNode[] | null;
  latency_ms: number;
}

export interface ProductSearchResponse {
  total: number;
  limit: number;
  products: Product[];
}

export interface PersonasResponse {
  count: number;
  personas: Persona[];
}

export interface ConversationTurn {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  action: "ask" | "recommend" | "refine";
  message: string;
  recommendations: RecommendItem[];
  extracted_constraints: Record<string, unknown>;
  filters_applied: Record<string, unknown>;
  rerank_fallback_reason?: string | null;
  reasoning_trace?: TraceNode[] | null;
  latency_ms: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  app_name: string;
  components: Record<string, string>;
}

export interface EvalSummary {
  task1?: {
    naija_rmse?: number;
    claude_rmse?: number;
    naija_bert?: number;
    claude_bert?: number;
    naija_ndcg10?: number;
    claude_ndcg10?: number;
    naija_overall?: number;
    claude_overall?: number;
    n_task1?: number;
    n_task2?: number;
  };
}
