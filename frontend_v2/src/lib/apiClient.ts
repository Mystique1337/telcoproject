import { supabase } from "./supabase";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function authHeaders(): Promise<Record<string, string>> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session) throw new Error("Not authenticated");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${session.access_token}`,
  };
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  const headers = await authHeaders();
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

// ── Projects ────────────────────────────────────────────────────────────────

export interface ProjectSummary {
  id: string;
  name: string;
  description: string;
  category: string;
  created_at: string;
  latest_run: {
    id: string;
    status: "running" | "completed" | "failed";
    created_at: string;
  } | null;
}

export interface CreateProjectPayload {
  name: string;
  description: string;
  category: string;
  image_url?: string;
}

export interface CreateProjectResponse {
  project_id: string;
  run_id: string;
  status: string;
}

export const listProjects = () =>
  request<ProjectSummary[]>("GET", "/api/projects");

export const createProject = (payload: CreateProjectPayload) =>
  request<CreateProjectResponse>("POST", "/api/projects", payload);

// ── Runs ────────────────────────────────────────────────────────────────────

export interface PersonaResult {
  id: string;
  persona_id: string;
  persona_name: string;
  review_text: string;
  rating: number;
  register_tier: string;
  sentiment: "positive" | "neutral" | "negative";
}

export interface RunDetail {
  id: string;
  project_id: string;
  project_name: string;
  status: "running" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
  progress: { completed: number; total: number };
  aggregate: {
    n_personas: number;
    avg_rating: number;
    buy_likelihood: number;
    rating_distribution: Record<string, number>;
    sentiment_split: Record<string, number>;
    by_register: Record<string, { n: number; avg_rating: number; buy_likelihood: number }>;
    by_zone: Record<string, { n: number; avg_rating: number; buy_likelihood: number }>;
    by_age: Record<string, { n: number; avg_rating: number; buy_likelihood: number }>;
    themes: { praised: string[]; complaints: string[] };
  } | null;
  backbone: { primary: string; fallback: string; fallback_used: number } | null;
  latency_ms: number | null;
  results: PersonaResult[];
}

export const getRun = (runId: string) =>
  request<RunDetail>("GET", `/api/runs/${runId}`);

export interface DashboardStats {
  total_projects: number;
  completed_runs: number;
  running_runs: number;
  avg_rating: number | null;
  total_personas_evaluated: number;
}

export const getDashboardStats = () =>
  request<DashboardStats>("GET", "/api/projects/stats");

export interface RunSummary {
  id: string;
  project_id: string;
  project_name: string;
  status: "running" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
  n_personas: number | null;
  avg_rating: number | null;
  buy_likelihood: number | null;
}

export const listRuns = () => request<RunSummary[]>("GET", "/api/runs");

// ── Panel personas ───────────────────────────────────────────────────────────

export interface PanelPersona {
  user_id: string;
  demographics: {
    age_range?: string;
    location?: string;
    occupation?: string;
  };
  hedonic_utilitarian: number;
  communal_individual: number;
  aspect_priority: Record<string, number>;
  register_tier: string;
  register_markers: string[];
  register_confidence: number;
  history_count: number;
}

export const getPanelPersonas = () =>
  fetch("/api/panel-personas").then((r) => r.json()) as Promise<PanelPersona[]>;

export interface PersonaReview {
  run_id: string;
  project_name: string;
  project_category: string;
  created_at: string;
  rating: number;
  sentiment: "positive" | "neutral" | "negative";
  review_text: string;
  register_tier: string;
}

export const getPersonaReviews = (personaId: string) =>
  request<PersonaReview[]>("GET", `/api/panel-personas/${personaId}/reviews`);

// ── Analytics ────────────────────────────────────────────────────────────────

export interface AnalyticsData {
  top_products: {
    project_name: string;
    category: string;
    avg_rating: number;
    buy_likelihood: number;
    n_personas: number;
    run_id: string;
  }[];
  top_personas: {
    persona_id: string;
    persona_name: string;
    positive_count: number;
    total_reviews: number;
    positive_rate: number;
    avg_rating: number;
  }[];
  sentiment_distribution: Record<string, number>;
  rating_distribution: Record<string, number>;
  category_performance: {
    category: string;
    avg_rating: number;
    avg_buy_likelihood: number;
    n_runs: number;
  }[];
  register_performance: {
    register: string;
    avg_rating: number;
    avg_buy_likelihood: number;
  }[];
  total_reviews: number;
  total_completed_runs: number;
}

export const getAnalytics = () =>
  request<AnalyticsData>("GET", "/api/analytics");
