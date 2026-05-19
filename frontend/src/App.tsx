import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  BookOpen,
  Bot,
  CheckCircle2,
  ChevronDown,
  Github,
  MessageSquare,
  Plus,
  RefreshCcw,
  Search,
  Sparkles,
  Star,
  Target,
  Trash2,
  TrendingUp,
  Users,
} from "lucide-react";

import { api } from "./api";
import { EVAL_FALLBACK, MODELS } from "./data";
import type {
  ConversationTurn,
  HealthResponse,
  Persona,
  Product,
  RecommendResponse,
  SimulateReviewResponse,
  TraceNode,
} from "./types";


// =========================================================================
// Shared UI bits
// =========================================================================

function Badge({
  children,
  tone = "default",
}: {
  children: React.ReactNode;
  tone?: "default" | "success" | "warn" | "info" | "naija";
}) {
  const tones: Record<string, string> = {
    default: "bg-ink-800 text-ink-200 border border-ink-700",
    success: "bg-naija-900/40 text-naija-300 border border-naija-700/50",
    warn: "bg-amber-900/40 text-amber-200 border border-amber-700/40",
    info: "bg-sky-900/40 text-sky-200 border border-sky-700/40",
    naija: "bg-naija-600 text-white",
  };
  return <span className={`badge ${tones[tone]}`}>{children}</span>;
}

function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-ink-300">
      <div className="w-4 h-4 border-2 border-naija-500/60 border-t-naija-300 rounded-full animate-spin" />
      <span className="text-sm">{label ?? "Working..."}</span>
    </div>
  );
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <Star
          key={n}
          size={16}
          className={n <= rating ? "fill-amber-400 text-amber-400" : "text-ink-700"}
        />
      ))}
      <span className="ml-2 text-sm text-ink-300">{rating}/5</span>
    </div>
  );
}

function ReasoningTrace({ trace }: { trace: TraceNode[] | null | undefined }) {
  const [open, setOpen] = useState(false);
  if (!trace || trace.length === 0) return null;
  return (
    <div className="mt-4 border-t border-ink-700/60 pt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-sm text-ink-300 hover:text-ink-100 transition-colors"
      >
        <ChevronDown
          size={16}
          className={`transition-transform ${open ? "rotate-180" : ""}`}
        />
        <Bot size={14} /> Agentic reasoning trace · {trace.length} steps
      </button>
      {open && (
        <ol className="mt-3 space-y-3 text-sm">
          {trace.map((node, i) => (
            <li key={i} className="border-l-2 border-naija-700/60 pl-3">
              <div className="text-ink-200 font-medium">
                {i + 1}. {node.node ?? "step"}
              </div>
              {node.summary ? (
                <div className="text-ink-300 text-xs mt-1 leading-relaxed">
                  {String(node.summary)}
                </div>
              ) : (
                <div className="text-ink-400 text-xs mt-1 font-mono">
                  {Object.entries(node)
                    .filter(([k]) => k !== "node")
                    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
                    .join(" · ")}
                </div>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function ResponseFlags({
  cold,
  cross,
  multi,
}: {
  cold?: boolean | null;
  cross?: boolean | null;
  multi?: boolean | null;
}) {
  if (!cold && !cross && !multi) return null;
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {cold && <Badge tone="info">🧊 Cold-start path</Badge>}
      {cross && <Badge tone="warn">🌍 Cross-domain</Badge>}
      {multi && <Badge tone="naija">💬 Multi-turn</Badge>}
    </div>
  );
}


// =========================================================================
// Header + sidebar bits
// =========================================================================

function Header({ health }: { health: HealthResponse | null }) {
  return (
    <header className="border-b border-ink-800 bg-ink-950/80 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-naija-600 to-naija-800 flex items-center justify-center text-2xl">
            🇳🇬
          </div>
          <div>
            <h1 className="text-lg font-bold text-ink-50 tracking-tight">
              Naija Persona Agent
            </h1>
            <p className="text-xs text-ink-400">
              Nigerian-context LLM agent · review simulation + recommendation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {health ? (
            <Badge tone="success">
              <CheckCircle2 size={12} /> API connected
            </Badge>
          ) : (
            <Badge tone="warn">
              <AlertCircle size={12} /> API offline
            </Badge>
          )}
          <a
            href="https://github.com/Mystique1337/telcoproject"
            target="_blank"
            rel="noreferrer"
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            <Github size={14} /> Code
          </a>
          <a
            href="https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF"
            target="_blank"
            rel="noreferrer"
            className="btn-ghost flex items-center gap-2 text-sm"
          >
            🤗 Model
          </a>
        </div>
      </div>
    </header>
  );
}


function StatTile({
  icon,
  label,
  value,
  sub,
  positive,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub?: string;
  positive?: boolean;
}) {
  return (
    <div className="card flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-ink-400 uppercase tracking-wider">{label}</span>
        <span className="text-ink-500">{icon}</span>
      </div>
      <div className="text-2xl font-bold text-ink-50 tabular-nums">{value}</div>
      {sub && (
        <div className={`text-xs ${positive ? "text-naija-300" : "text-ink-400"}`}>
          {sub}
        </div>
      )}
    </div>
  );
}


function HeroStats({
  personasCount,
  productsCount,
  evalData,
}: {
  personasCount: number;
  productsCount: number;
  evalData: typeof EVAL_FALLBACK;
}) {
  const rmseDelta = evalData.naija_rmse && evalData.claude_rmse
    ? (((evalData.claude_rmse - evalData.naija_rmse) / evalData.claude_rmse) * 100).toFixed(1)
    : "?";
  const ndcgDelta = evalData.naija_ndcg10 && evalData.claude_ndcg10
    ? (((evalData.naija_ndcg10 - evalData.claude_ndcg10) / evalData.claude_ndcg10) * 100).toFixed(0)
    : "?";

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatTile
        icon={<Users size={16} />}
        label="Personas"
        value={String(personasCount)}
        sub="6 zones × 4 register tiers"
      />
      <StatTile
        icon={<BookOpen size={16} />}
        label="Products"
        value={productsCount.toLocaleString()}
        sub="real Jumia catalogue"
      />
      <StatTile
        icon={<Target size={16} />}
        label="Rating RMSE"
        value={evalData.naija_rmse?.toFixed(3) ?? "—"}
        sub={`vs Claude ${evalData.claude_rmse?.toFixed(3)} · −${rmseDelta}%`}
        positive
      />
      <StatTile
        icon={<TrendingUp size={16} />}
        label="NDCG@10"
        value={evalData.naija_ndcg10?.toFixed(3) ?? "—"}
        sub={`vs Claude ${evalData.claude_ndcg10?.toFixed(3)} · +${ndcgDelta}%`}
        positive
      />
    </div>
  );
}


// =========================================================================
// Persona + Product pickers
// =========================================================================

function PersonaPicker({
  personas,
  selected,
  onChange,
}: {
  personas: Persona[];
  selected: Persona | null;
  onChange: (p: Persona) => void;
}) {
  const [tier, setTier] = useState<string>("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const s = search.toLowerCase();
    return personas.filter((p) => {
      if (tier !== "all" && p.register_tier !== tier) return false;
      if (!s) return true;
      const blob = `${p.user_id} ${p.demographics?.location ?? ""} ${p.demographics?.occupation ?? ""}`.toLowerCase();
      return blob.includes(s);
    });
  }, [personas, tier, search]);

  return (
    <div className="space-y-3">
      <span className="label">Persona</span>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <select
          className="input"
          value={tier}
          onChange={(e) => setTier(e.target.value)}
        >
          <option value="all">All register tiers</option>
          <option value="nigerian_pidgin">Nigerian Pidgin</option>
          <option value="code_mixed">Code-mixed</option>
          <option value="nigerian_english">Nigerian English</option>
          <option value="standard_english">Standard English</option>
        </select>
        <div className="relative md:col-span-2">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500" />
          <input
            className="input pl-9"
            placeholder="Search persona — lagos, kano, fintech, trader..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="text-xs text-ink-400">
        {filtered.length} / {personas.length} match
      </div>

      <div className="max-h-72 overflow-y-auto border border-ink-700 rounded-lg divide-y divide-ink-800">
        {filtered.map((p) => {
          const active = selected?.user_id === p.user_id;
          return (
            <button
              key={p.user_id}
              onClick={() => onChange(p)}
              className={`w-full text-left px-4 py-3 hover:bg-ink-800 transition-colors ${
                active ? "bg-naija-900/30 border-l-2 border-naija-500" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-ink-100">{p.user_id}</span>
                <Badge tone={active ? "naija" : "default"}>
                  {p.register_tier.replace("_", " ")}
                </Badge>
              </div>
              <div className="text-xs text-ink-400 mt-1">
                {p.demographics?.location} · {p.demographics?.occupation}
              </div>
            </button>
          );
        })}
        {filtered.length === 0 && (
          <div className="text-sm text-ink-400 p-4 text-center">No personas match</div>
        )}
      </div>
    </div>
  );
}


function ProductPicker({
  products,
  selected,
  onChange,
}: {
  products: Product[];
  selected: Product | null;
  onChange: (p: Product) => void;
}) {
  const [category, setCategory] = useState<string>("all");
  const [search, setSearch] = useState("");

  const categories = useMemo(() => {
    const c = new Set<string>();
    products.forEach((p) => p.category && c.add(p.category));
    return Array.from(c).sort();
  }, [products]);

  const filtered = useMemo(() => {
    const s = search.toLowerCase();
    return products
      .filter((p) => {
        if (category !== "all" && p.category !== category) return false;
        if (!s) return true;
        return (p.title ?? "").toLowerCase().includes(s);
      })
      .slice(0, 200);
  }, [products, category, search]);

  return (
    <div className="space-y-3">
      <span className="label">Product</span>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <select
          className="input"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="all">All categories</option>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <div className="relative md:col-span-2">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500" />
          <input
            className="input pl-9"
            placeholder="Search by title — tecno, blender, anikulapo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="text-xs text-ink-400">
        showing {filtered.length} of {products.length}
      </div>

      <div className="max-h-72 overflow-y-auto border border-ink-700 rounded-lg divide-y divide-ink-800">
        {filtered.map((p) => {
          const active = selected?.product_id === p.product_id;
          return (
            <button
              key={p.product_id}
              onClick={() => onChange(p)}
              className={`w-full text-left px-4 py-3 hover:bg-ink-800 transition-colors ${
                active ? "bg-naija-900/30 border-l-2 border-naija-500" : ""
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-ink-100 text-sm line-clamp-1">
                  {p.title}
                </span>
                {p.price_naira != null && (
                  <span className="text-xs text-naija-300 whitespace-nowrap">
                    ₦{Number(p.price_naira).toLocaleString()}
                  </span>
                )}
              </div>
              <div className="text-xs text-ink-400 mt-1">{p.category}</div>
            </button>
          );
        })}
        {filtered.length === 0 && (
          <div className="text-sm text-ink-400 p-4 text-center">No products match</div>
        )}
      </div>
    </div>
  );
}


function ModelSelect({
  value,
  onChange,
  label,
}: {
  value: string;
  onChange: (v: string) => void;
  label: string;
}) {
  return (
    <div>
      <span className="label">{label}</span>
      <select
        className="input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        {MODELS.map((m) => (
          <option key={m.spec} value={m.spec}>
            {m.label} {m.badge ? `— ${m.badge}` : ""}
          </option>
        ))}
      </select>
    </div>
  );
}


// =========================================================================
// Tab: Simulate Review (Task A)
// =========================================================================

function ReviewCard({
  data,
  modelLabel,
}: {
  data: SimulateReviewResponse;
  modelLabel: string;
}) {
  return (
    <div className="card space-y-3 relative">
      <div className="flex items-center justify-between gap-3">
        <Badge tone="naija">{modelLabel}</Badge>
        <div className="flex items-center gap-3 text-xs text-ink-400">
          <Badge>{data.register_tier.replace("_", " ")}</Badge>
          <span>{data.latency_ms} ms</span>
        </div>
      </div>
      <StarRating rating={data.rating} />
      <p className="text-ink-100 leading-relaxed">{data.review}</p>
      <p className="text-xs text-ink-400 italic">💡 {data.rationale}</p>
      <ReasoningTrace trace={data.reasoning_trace} />
    </div>
  );
}


function TabReview({
  personas,
  products,
}: {
  personas: Persona[];
  products: Product[];
}) {
  const [persona, setPersona] = useState<Persona | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [modelA, setModelA] = useState(MODELS[0].spec);
  const [modelB, setModelB] = useState(MODELS[1].spec);
  const [compare, setCompare] = useState(true);
  const [dataA, setDataA] = useState<SimulateReviewResponse | null>(null);
  const [dataB, setDataB] = useState<SimulateReviewResponse | null>(null);
  const [errA, setErrA] = useState<string | null>(null);
  const [errB, setErrB] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Auto-select first persona + product on mount
  useEffect(() => {
    if (!persona && personas.length) setPersona(personas[0]);
    if (!product && products.length) setProduct(products[0]);
  }, [personas, products]);

  async function run() {
    if (!persona || !product) return;
    setLoading(true);
    setDataA(null); setDataB(null); setErrA(null); setErrB(null);
    const callA = api.simulateReview(persona, product, modelA).then(setDataA).catch((e) => setErrA(String(e)));
    const callB = compare
      ? api.simulateReview(persona, product, modelB).then(setDataB).catch((e) => setErrB(String(e)))
      : Promise.resolve();
    await Promise.all([callA, callB]);
    setLoading(false);
  }

  const labelA = MODELS.find((m) => m.spec === modelA)?.label ?? modelA;
  const labelB = MODELS.find((m) => m.spec === modelB)?.label ?? modelB;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card"><PersonaPicker personas={personas} selected={persona} onChange={setPersona} /></div>
        <div className="card"><ProductPicker products={products} selected={product} onChange={setProduct} /></div>
      </div>

      <div className="card space-y-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={compare}
            onChange={(e) => setCompare(e.target.checked)}
            className="w-4 h-4 accent-naija-500"
          />
          <span className="text-sm text-ink-200">
            Compare side-by-side <span className="text-ink-400">— pit two backbones on the same input</span>
          </span>
        </label>

        <div className={`grid gap-4 ${compare ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
          <ModelSelect label={compare ? "Model A (left)" : "Model"} value={modelA} onChange={setModelA} />
          {compare && <ModelSelect label="Model B (right)" value={modelB} onChange={setModelB} />}
        </div>

        <button
          className="btn-primary flex items-center gap-2 w-full md:w-auto"
          onClick={run}
          disabled={loading || !persona || !product}
        >
          {loading ? <Spinner label="Generating review..." /> : (<><Sparkles size={16} /> Generate Review</>)}
        </button>
      </div>

      {(dataA || errA || dataB || errB) && (
        <div className={`grid gap-4 ${compare ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
          <div>
            {errA && <div className="card border-red-700 text-red-300 text-sm">{errA}</div>}
            {dataA && <ReviewCard data={dataA} modelLabel={labelA} />}
          </div>
          {compare && (
            <div>
              {errB && <div className="card border-red-700 text-red-300 text-sm">{errB}</div>}
              {dataB && <ReviewCard data={dataB} modelLabel={labelB} />}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// =========================================================================
// Tab: Recommend (Task B, single-shot)
// =========================================================================

function TabRecommend({ personas }: { personas: Persona[] }) {
  const [persona, setPersona] = useState<Persona | null>(null);
  const [coldStart, setColdStart] = useState(false);
  const [domain, setDomain] = useState("jumia");
  const [k, setK] = useState(5);
  const [model, setModel] = useState(MODELS[0].spec);
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!persona && personas.length) setPersona(personas[0]);
  }, [personas]);

  async function run() {
    if (!persona) return;
    setLoading(true); setErr(null); setData(null);
    const active: Persona = coldStart
      ? { ...persona, history_count: 0, review_anchors: [] }
      : persona;
    try {
      const resp = await api.recommend({
        persona: active,
        domain,
        k,
        reranker_override: model,
      });
      setData(resp);
    } catch (e) {
      setErr(String(e));
    }
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      <div className="card"><PersonaPicker personas={personas} selected={persona} onChange={setPersona} /></div>

      <div className="card grid grid-cols-1 md:grid-cols-4 gap-4">
        <label className="flex items-start gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={coldStart}
            onChange={(e) => setColdStart(e.target.checked)}
            className="w-4 h-4 mt-1 accent-naija-500"
          />
          <div>
            <div className="text-sm text-ink-200">🧊 Force cold-start</div>
            <div className="text-xs text-ink-400">wipe history + anchors</div>
          </div>
        </label>
        <div>
          <span className="label">Domain</span>
          <select className="input" value={domain} onChange={(e) => setDomain(e.target.value)}>
            <option value="jumia">jumia</option>
            <option value="konga">konga</option>
            <option value="nollywood">nollywood</option>
            <option value="all">all (cross-domain)</option>
          </select>
        </div>
        <div>
          <span className="label">Top-K</span>
          <input
            type="number"
            min={1}
            max={10}
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="input"
          />
        </div>
        <ModelSelect label="Re-ranker" value={model} onChange={setModel} />
      </div>

      <button
        className="btn-primary flex items-center gap-2"
        onClick={run}
        disabled={loading || !persona}
      >
        {loading ? <Spinner label="Ranking..." /> : (<><Target size={16} /> Generate Recommendations</>)}
      </button>

      {err && <div className="card border-red-700 text-red-300 text-sm">{err}</div>}

      {data && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">{data.recommendations.length} recommendations</h3>
            <span className="text-xs text-ink-400">{data.latency_ms} ms</span>
          </div>
          <ResponseFlags cold={data.cold_start} cross={data.cross_domain} multi={data.multi_turn} />
          <div className="space-y-2">
            {data.recommendations.map((item) => (
              <div
                key={item.product_id}
                className="border border-ink-700 rounded-lg p-3 flex items-start gap-3"
              >
                <div className="w-10 h-10 rounded-lg bg-naija-900/40 text-naija-300 flex items-center justify-center font-bold flex-shrink-0">
                  #{item.rank}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-ink-100 line-clamp-1">
                    {item.title ?? item.product_id}
                  </div>
                  <div className="text-xs text-ink-400 mt-0.5">💡 {item.rationale}</div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-sm font-mono text-naija-300">{item.score.toFixed(2)}</div>
                  <div className="text-[10px] text-ink-500 uppercase">score</div>
                </div>
              </div>
            ))}
          </div>
          <ReasoningTrace trace={data.reasoning_trace} />
        </div>
      )}
    </div>
  );
}


// =========================================================================
// Tab: Multi-turn (Task B with conversation history)
// =========================================================================

function TabMultiTurn({ personas }: { personas: Persona[] }) {
  const [persona, setPersona] = useState<Persona | null>(null);
  const [domain, setDomain] = useState("jumia");
  const [k, setK] = useState(5);
  const [model, setModel] = useState(MODELS[0].spec);
  const [turns, setTurns] = useState<ConversationTurn[]>([
    { role: "user", content: "I want a phone for my mum" },
    { role: "assistant", content: "Got it — any budget or features she cares about?" },
    { role: "user", content: "Under ₦100k, durable, big buttons preferred" },
  ]);
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!persona && personas.length) setPersona(personas[0]);
  }, [personas]);

  function updateTurn(i: number, patch: Partial<ConversationTurn>) {
    setTurns(turns.map((t, idx) => (idx === i ? { ...t, ...patch } : t)));
  }

  async function run() {
    if (!persona) return;
    setLoading(true); setErr(null); setData(null);
    try {
      const resp = await api.recommend({
        persona,
        domain,
        k,
        reranker_override: model,
        conversation_history: turns.filter((t) => t.content.trim()),
      });
      setData(resp);
    } catch (e) {
      setErr(String(e));
    }
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      <div className="card"><PersonaPicker personas={personas} selected={persona} onChange={setPersona} /></div>

      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold flex items-center gap-2">
            <MessageSquare size={18} /> Conversation history
          </h3>
          <button
            className="btn-ghost text-xs flex items-center gap-1"
            onClick={() => setTurns([
              { role: "user", content: "I want a phone for my mum" },
              { role: "assistant", content: "Got it — any budget or features she cares about?" },
              { role: "user", content: "Under ₦100k, durable, big buttons preferred" },
            ])}
          >
            <RefreshCcw size={12} /> Reset demo
          </button>
        </div>
        <div className="space-y-2">
          {turns.map((t, i) => (
            <div key={i} className="flex items-stretch gap-2">
              <select
                className="input w-32 flex-shrink-0"
                value={t.role}
                onChange={(e) => updateTurn(i, { role: e.target.value as "user" | "assistant" })}
              >
                <option value="user">user</option>
                <option value="assistant">assistant</option>
              </select>
              <input
                className="input flex-1"
                value={t.content}
                onChange={(e) => updateTurn(i, { content: e.target.value })}
                placeholder="Type a turn…"
              />
              <button
                className="btn-ghost px-3"
                onClick={() => setTurns(turns.filter((_, idx) => idx !== i))}
                title="Remove turn"
              >
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <button
            className="btn-ghost text-xs flex items-center gap-1"
            onClick={() => setTurns([...turns, { role: "user", content: "" }])}
          >
            <Plus size={12} /> Add user turn
          </button>
          <button
            className="btn-ghost text-xs flex items-center gap-1"
            onClick={() => setTurns([...turns, { role: "assistant", content: "" }])}
          >
            <Plus size={12} /> Add assistant turn
          </button>
        </div>
      </div>

      <div className="card grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <span className="label">Domain</span>
          <select className="input" value={domain} onChange={(e) => setDomain(e.target.value)}>
            <option value="jumia">jumia</option>
            <option value="konga">konga</option>
            <option value="all">all (cross-domain)</option>
          </select>
        </div>
        <div>
          <span className="label">Top-K</span>
          <input type="number" min={1} max={10} value={k}
                 onChange={(e) => setK(Number(e.target.value))} className="input" />
        </div>
        <ModelSelect label="Re-ranker" value={model} onChange={setModel} />
      </div>

      <button
        className="btn-primary flex items-center gap-2"
        onClick={run}
        disabled={loading || !persona}
      >
        {loading ? <Spinner label="Reasoning + ranking..." /> : (<><MessageSquare size={16} /> Generate</>)}
      </button>

      {err && <div className="card border-red-700 text-red-300 text-sm">{err}</div>}

      {data && (
        <div className="card space-y-4">
          <ResponseFlags cold={data.cold_start} cross={data.cross_domain} multi={data.multi_turn} />
          {data.extracted_constraints && data.extracted_constraints.length > 0 && (
            <div>
              <span className="label">Extracted constraints</span>
              <div className="flex flex-wrap gap-2">
                {data.extracted_constraints.map((c) => (
                  <code key={c} className="px-2 py-1 bg-ink-800 rounded text-xs text-naija-300 font-mono">
                    {c}
                  </code>
                ))}
              </div>
            </div>
          )}
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">{data.recommendations.length} recommendations</h3>
            <span className="text-xs text-ink-400">{data.latency_ms} ms</span>
          </div>
          <div className="space-y-2">
            {data.recommendations.map((item) => (
              <div
                key={item.product_id}
                className="border border-ink-700 rounded-lg p-3 flex items-start gap-3"
              >
                <div className="w-10 h-10 rounded-lg bg-naija-900/40 text-naija-300 flex items-center justify-center font-bold flex-shrink-0">
                  #{item.rank}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-ink-100 line-clamp-1">
                    {item.title ?? item.product_id}
                  </div>
                  <div className="text-xs text-ink-400 mt-0.5">💡 {item.rationale}</div>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className="text-sm font-mono text-naija-300">{item.score.toFixed(2)}</div>
                  <div className="text-[10px] text-ink-500 uppercase">score</div>
                </div>
              </div>
            ))}
          </div>
          <ReasoningTrace trace={data.reasoning_trace} />
        </div>
      )}
    </div>
  );
}


// =========================================================================
// Root App
// =========================================================================

type TabKey = "review" | "recommend" | "multiturn";

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: "review",     label: "Simulate Review",       icon: <Sparkles size={14} /> },
  { key: "recommend",  label: "Recommend",             icon: <Target size={14} /> },
  { key: "multiturn",  label: "Multi-turn",            icon: <MessageSquare size={14} /> },
];


export default function App() {
  const [tab, setTab] = useState<TabKey>("review");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [evalData, setEvalData] = useState(EVAL_FALLBACK);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));

    fetch("/catalog/personas")
      .then((r) => r.json())
      .then((d) => setPersonas(d.personas ?? []))
      .catch(() => setPersonas([]));

    fetch("/catalog/products?limit=300")
      .then((r) => r.json())
      .then((d) => setProducts(d.products ?? []))
      .catch(() => setProducts([]));

    fetch("/catalog/eval-summary")
      .then((r) => r.json())
      .then((d) => {
        if (d.available && d.task1?.naija) {
          setEvalData({
            naija_rmse: d.task1.naija.RMSE,
            claude_rmse: d.task1.claude.RMSE,
            naija_bert: d.task1.naija.BERTScore_F1,
            claude_bert: d.task1.claude.BERTScore_F1,
            naija_ndcg10: d.task2?.naija?.NDCG_at_10,
            claude_ndcg10: d.task2?.claude?.NDCG_at_10,
            naija_overall: d.task1.naija.AS_overall,
            claude_overall: d.task1.claude.AS_overall,
            n_task1: d.task1.n,
            n_task2: d.task2?.n,
          });
        }
      })
      .catch(() => { /* keep fallback */ });
  }, []);

  return (
    <div className="min-h-screen bg-ink-950">
      <Header health={health} />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Hero stats */}
        <section>
          <HeroStats
            personasCount={personas.length}
            productsCount={products.length || 6657}
            evalData={evalData}
          />
        </section>

        {/* Tab bar */}
        <nav className="flex items-center gap-1 border-b border-ink-800">
          {TABS.map((t) => {
            const active = tab === t.key;
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={`flex items-center gap-2 px-4 py-3 text-sm transition-colors border-b-2 -mb-px ${
                  active
                    ? "border-naija-500 text-ink-50"
                    : "border-transparent text-ink-400 hover:text-ink-200"
                }`}
              >
                {t.icon} {t.label}
              </button>
            );
          })}
          <div className="ml-auto text-xs text-ink-500 flex items-center gap-2 pb-3">
            <Activity size={12} />
            {personas.length} personas · {(products.length || 6657).toLocaleString()} products
          </div>
        </nav>

        {/* Tab content */}
        {tab === "review"    && <TabReview     personas={personas} products={products} />}
        {tab === "recommend" && <TabRecommend  personas={personas} />}
        {tab === "multiturn" && <TabMultiTurn  personas={personas} />}
      </main>

      <footer className="border-t border-ink-800 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col md:flex-row items-center justify-between text-xs text-ink-500">
          <span>Open-source · Bluechip Tech Hackathon submission · Team Ashinze · Franca</span>
          <span className="font-mono">naija-persona-agent · v0.1</span>
        </div>
      </footer>
    </div>
  );
}
