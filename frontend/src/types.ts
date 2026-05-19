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
}

export interface RecommendItem {
  product_id: string;
  title?: string;
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
  reasoning_trace?: TraceNode[] | null;
  latency_ms: number;
}

export interface ConversationTurn {
  role: "user" | "assistant";
  content: string;
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
