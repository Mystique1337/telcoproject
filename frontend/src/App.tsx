import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  Bot,
  CheckCircle2,
  ChevronDown,
  Github,
  Info,
  Loader2,
  MessageSquare,
  Package,
  Pause,
  Play,
  Plus,
  RefreshCcw,
  Search,
  Sparkles,
  Star,
  Tag,
  Target,
  Trash2,
  TrendingUp,
  Users,
  Volume2,
  Wand2,
} from "lucide-react";

import { api } from "./api";
import { EVAL_FALLBACK, MODELS, modelBestFor, modelLabel } from "./data";
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
  children, tone = "default",
}: {
  children: React.ReactNode;
  tone?: "default" | "success" | "warn" | "info" | "naija" | "danger";
}) {
  const tones: Record<string, string> = {
    default: "bg-ink-800 text-ink-200 border border-ink-700",
    success: "bg-naija-900/40 text-naija-300 border border-naija-700/50",
    warn:    "bg-amber-900/40 text-amber-200 border border-amber-700/40",
    info:    "bg-sky-900/40 text-sky-200 border border-sky-700/40",
    naija:   "bg-naija-600 text-white",
    danger:  "bg-red-900/40 text-red-300 border border-red-700/40",
  };
  return <span className={`badge ${tones[tone]}`}>{children}</span>;
}

function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-ink-200">
      <Loader2 size={16} className="animate-spin" />
      <span className="text-sm">{label ?? "Working..."}</span>
    </div>
  );
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((n) => (
        <Star key={n} size={16}
              className={n <= rating ? "fill-amber-400 text-amber-400" : "text-ink-700"} />
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
      <button onClick={() => setOpen(!open)}
              className="flex items-center gap-2 text-sm text-ink-300 hover:text-ink-100 transition-colors">
        <ChevronDown size={16} className={`transition-transform ${open ? "rotate-180" : ""}`} />
        <Bot size={14} /> Agentic reasoning trace · {trace.length} steps
      </button>
      {open && (
        <ol className="mt-3 space-y-3 text-sm">
          {trace.map((node, i) => (
            <li key={i} className="border-l-2 border-naija-700/60 pl-3">
              <div className="text-ink-200 font-medium">{i + 1}. {node.node ?? "step"}</div>
              {node.summary
                ? <div className="text-ink-300 text-xs mt-1 leading-relaxed">{String(node.summary)}</div>
                : <div className="text-ink-400 text-xs mt-1 font-mono">
                    {Object.entries(node).filter(([k]) => k !== "node")
                      .map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(" · ")}
                  </div>}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

function ResponseFlags({ cold, cross, multi }:
  { cold?: boolean | null; cross?: boolean | null; multi?: boolean | null }) {
  if (!cold && !cross && !multi) return null;
  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {cold && <Badge tone="info">🧊 Cold-start path</Badge>}
      {cross && <Badge tone="warn">🌍 Cross-domain</Badge>}
      {multi && <Badge tone="naija">💬 Multi-turn</Badge>}
    </div>
  );
}

function FallbackBanner({ reason }: { reason: string | null | undefined }) {
  if (!reason) return null;
  return (
    <div className="border border-amber-700/40 bg-amber-900/20 rounded-lg p-3 flex gap-3 text-sm">
      <AlertTriangle size={18} className="text-amber-400 flex-shrink-0 mt-0.5" />
      <div className="text-amber-100">
        <div className="font-medium mb-1">Re-rank fell back to pre-rank</div>
        <div className="text-xs text-amber-200/90 leading-relaxed">{reason}</div>
      </div>
    </div>
  );
}

function useDebounced<T>(value: T, ms = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return debounced;
}


// =========================================================================
// Header + Hero stats
// =========================================================================

function Header({ health }: { health: HealthResponse | null }) {
  return (
    <header className="border-b border-ink-800 bg-ink-950/80 backdrop-blur-md sticky top-0 z-30">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-naija-600 to-naija-800 flex items-center justify-center text-2xl">🇳🇬</div>
          <div>
            <h1 className="text-lg font-bold text-ink-50 tracking-tight">Naija Persona Agent</h1>
            <p className="text-xs text-ink-400">Nigerian-context LLM agent · review simulation + recommendation</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {health
            ? <Badge tone="success"><CheckCircle2 size={12}/> API connected</Badge>
            : <Badge tone="warn"><AlertCircle size={12}/> API offline</Badge>}
          <a href="https://github.com/Mystique1337/telcoproject" target="_blank" rel="noreferrer"
             className="btn-ghost flex items-center gap-2 text-sm"><Github size={14}/> Code</a>
          <a href="https://huggingface.co/Shinzmann/naija-reviewer-8b-v2-Q4_K_M-GGUF"
             target="_blank" rel="noreferrer" className="btn-ghost flex items-center gap-2 text-sm">🤗 Model</a>
        </div>
      </div>
    </header>
  );
}

function StatTile({ icon, label, value, sub, positive }:
  { icon: React.ReactNode; label: string; value: string; sub?: string; positive?: boolean }) {
  return (
    <div className="card flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-ink-400 uppercase tracking-wider">{label}</span>
        <span className="text-ink-500">{icon}</span>
      </div>
      <div className="text-2xl font-bold text-ink-50 tabular-nums">{value}</div>
      {sub && <div className={`text-xs ${positive ? "text-naija-300" : "text-ink-400"}`}>{sub}</div>}
    </div>
  );
}

function HeroStats({ personasCount, productsCount, evalData }:
  { personasCount: number; productsCount: number; evalData: typeof EVAL_FALLBACK }) {
  const rmseDelta = evalData.naija_rmse && evalData.claude_rmse
    ? (((evalData.claude_rmse - evalData.naija_rmse) / evalData.claude_rmse) * 100).toFixed(1) : "?";
  const ndcgDelta = evalData.naija_ndcg10 && evalData.claude_ndcg10
    ? (((evalData.naija_ndcg10 - evalData.claude_ndcg10) / evalData.claude_ndcg10) * 100).toFixed(0) : "?";
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatTile icon={<Users size={16}/>} label="Personas"
                value={String(personasCount)} sub="6 zones × 4 register tiers"/>
      <StatTile icon={<Package size={16}/>} label="Products"
                value={productsCount.toLocaleString()} sub="real Jumia catalogue"/>
      <StatTile icon={<Target size={16}/>} label="Rating RMSE ↓"
                value={evalData.naija_rmse?.toFixed(3) ?? "—"}
                sub={`vs Claude ${evalData.claude_rmse?.toFixed(3)} · −${rmseDelta}%`} positive/>
      <StatTile icon={<TrendingUp size={16}/>} label="NDCG@10 ↑"
                value={evalData.naija_ndcg10?.toFixed(3) ?? "—"}
                sub={`vs Claude ${evalData.claude_ndcg10?.toFixed(3)} · +${ndcgDelta}%`} positive/>
    </div>
  );
}


// =========================================================================
// Persona picker (uses local personas array — already loaded once)
// =========================================================================

function PersonaPicker({ personas, selected, onChange }:
  { personas: Persona[]; selected: Persona | null; onChange: (p: Persona) => void }) {
  const [tier, setTier] = useState("all");
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
        <select className="input" value={tier} onChange={(e) => setTier(e.target.value)}>
          <option value="all">All register tiers</option>
          <option value="nigerian_pidgin">Nigerian Pidgin</option>
          <option value="code_mixed">Code-mixed</option>
          <option value="nigerian_english">Nigerian English</option>
          <option value="standard_english">Standard English</option>
        </select>
        <div className="relative md:col-span-2">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500"/>
          <input className="input pl-9" placeholder="Search persona — lagos, kano, fintech, trader..."
                 value={search} onChange={(e) => setSearch(e.target.value)}/>
        </div>
      </div>
      <div className="text-xs text-ink-400">{filtered.length} / {personas.length} match</div>
      <div className="max-h-72 overflow-y-auto border border-ink-700 rounded-lg divide-y divide-ink-800">
        {filtered.map((p) => {
          const active = selected?.user_id === p.user_id;
          return (
            <button key={p.user_id} onClick={() => onChange(p)}
                    className={`w-full text-left px-4 py-3 hover:bg-ink-800 transition-colors ${
                      active ? "bg-naija-900/30 border-l-2 border-naija-500" : ""}`}>
              <div className="flex items-center justify-between">
                <span className="font-medium text-ink-100">{p.user_id}</span>
                <Badge tone={active ? "naija" : "default"}>{p.register_tier.replace("_", " ")}</Badge>
              </div>
              <div className="text-xs text-ink-400 mt-1">
                {p.demographics?.location} · {p.demographics?.occupation}
              </div>
            </button>
          );
        })}
        {filtered.length === 0 && <div className="text-sm text-ink-400 p-4 text-center">No personas match</div>}
      </div>
    </div>
  );
}


// =========================================================================
// Product picker — SERVER-SIDE search (no 300-cap)
// =========================================================================

function ProductPicker({ selected, onChange }:
  { selected: Product | null; onChange: (p: Product) => void }) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const debouncedSearch = useDebounced(search, 250);
  const [items, setItems] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [categories, setCategories] = useState<{ name: string; n: number }[]>([]);

  useEffect(() => {
    api.categories().then((d) => setCategories(d.categories ?? [])).catch(() => {});
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.searchProducts({ search: debouncedSearch, category, limit: 80 })
      .then((d) => {
        if (cancelled) return;
        setItems((d.products as Product[]) ?? []);
        setTotal(d.total ?? 0);
      })
      .catch(() => { if (!cancelled) { setItems([]); setTotal(0); } })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [debouncedSearch, category]);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="label !mb-0">Product</span>
        <span className="text-xs text-ink-400 flex items-center gap-1.5">
          {loading && <Loader2 size={11} className="animate-spin"/>}
          {total > 0
            ? `showing ${Math.min(items.length, 80)} of ${total.toLocaleString()}`
            : "no matches"}
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <select className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="all">All categories ({categories.reduce((a, c) => a + c.n, 0).toLocaleString()})</option>
          {categories.map((c) => (
            <option key={c.name} value={c.name}>{c.name} ({c.n})</option>
          ))}
        </select>
        <div className="relative md:col-span-2">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-500"/>
          <input className="input pl-9" placeholder="Search 6,657 products — tecno, blender, ankara..."
                 value={search} onChange={(e) => setSearch(e.target.value)} autoFocus={false}/>
        </div>
      </div>
      <div className="max-h-80 overflow-y-auto border border-ink-700 rounded-lg divide-y divide-ink-800">
        {items.map((p) => {
          const active = selected?.product_id === p.product_id;
          return (
            <button key={p.product_id} onClick={() => onChange(p)}
                    className={`w-full text-left px-4 py-3 hover:bg-ink-800 transition-colors ${
                      active ? "bg-naija-900/30 border-l-2 border-naija-500" : ""}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-ink-100 text-sm line-clamp-2 leading-snug">{p.title}</div>
                  <div className="text-xs text-ink-400 mt-1 flex items-center gap-2">
                    <Tag size={10}/> {p.category}
                  </div>
                </div>
                {p.price_naira != null && (
                  <span className="text-xs text-naija-300 whitespace-nowrap font-mono">
                    ₦{Number(p.price_naira).toLocaleString()}
                  </span>
                )}
              </div>
            </button>
          );
        })}
        {!loading && items.length === 0 && (
          <div className="text-sm text-ink-400 p-4 text-center">No products match — try a different search</div>
        )}
      </div>
    </div>
  );
}


// =========================================================================
// Model select with task-fit guidance
// =========================================================================

function ModelSelect({ value, onChange, label, taskKind }:
  { value: string; onChange: (v: string) => void; label: string;
    taskKind: "review" | "rank" }) {
  const best = modelBestFor(value);
  const mismatch =
    (taskKind === "rank" && best === "review") ||
    (taskKind === "review" && best === "rank");

  return (
    <div className="space-y-2">
      <span className="label">{label}</span>
      <select className="input" value={value} onChange={(e) => onChange(e.target.value)}>
        {MODELS.map((m) => {
          const rec = m.bestFor === taskKind || m.bestFor === "both";
          return (
            <option key={m.spec} value={m.spec}>
              {m.label} — {m.badge}{rec ? "" : " · ⚠ best for " + m.bestFor}
            </option>
          );
        })}
      </select>
      {mismatch && (
        <div className="text-xs flex items-start gap-2 px-3 py-2 rounded-md bg-amber-900/20 border border-amber-700/30 text-amber-200">
          <Info size={14} className="flex-shrink-0 mt-0.5"/>
          <span>
            <strong>{modelLabel(value)}</strong> is best at {best}. If output isn't
            parseable for the {taskKind} contract, the agent falls back to pre-rank
            (similarity + popularity + aspect-match) — still high quality given
            Pinecone llama-text-embed-v2 retrieval, but you lose LLM-side semantic
            ranking.
          </span>
        </div>
      )}
    </div>
  );
}


// =========================================================================
// Tab: Simulate Review (Task A)
// =========================================================================

// 16 Nigerian voices from YarnGPT with character descriptions
// (per https://yarngpt.ai/api-docs)
const NAIJA_VOICES: { name: string; description: string }[] = [
  { name: "Idera",    description: "Melodic, gentle"      },
  { name: "Emma",     description: "Authoritative, deep"  },
  { name: "Zainab",   description: "Soothing, gentle"     },
  { name: "Osagie",   description: "Smooth, calm"         },
  { name: "Wura",     description: "Young, sweet"         },
  { name: "Jude",     description: "Warm, confident"      },
  { name: "Chinenye", description: "Engaging, warm"       },
  { name: "Tayo",     description: "Upbeat, energetic"    },
  { name: "Regina",   description: "Mature, warm"         },
  { name: "Femi",     description: "Rich, reassuring"     },
  { name: "Adaora",   description: "Warm, engaging"       },
  { name: "Umar",     description: "Calm, smooth"         },
  { name: "Mary",     description: "Energetic, youthful"  },
  { name: "Nonso",    description: "Bold, resonant"       },
  { name: "Remi",     description: "Melodious, warm"      },
  { name: "Adam",     description: "Deep, clear"          },
];


function ListenButton({ text, persona }: { text: string; persona?: Persona | null }) {
  const [voice, setVoice] = useState("Idera");
  const [autoMatched, setAutoMatched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Auto-match the voice to the persona on mount / persona change
  useEffect(() => {
    if (!persona) return;
    let cancelled = false;
    fetch("/tts/voice-for-persona", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        persona_id: persona.user_id,
        demographics: persona.demographics,
        register_tier: persona.register_tier,
        register_markers: persona.register_markers,
      }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        if (d.voice) {
          setVoice(d.voice);
          setAutoMatched(true);
          setAudioUrl(null);   // invalidate any prior audio
        }
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [persona?.user_id]);

  async function generate() {
    if (loading) return;
    setLoading(true); setError(null);
    try {
      const r = await fetch("/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, voice, response_format: "mp3" }),
      });
      if (!r.ok) {
        const detail = await r.text();
        throw new Error(`HTTP ${r.status}: ${detail.slice(0, 120)}`);
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      setAudioUrl(url);
      // Auto-play
      setTimeout(() => audioRef.current?.play().catch(() => {}), 50);
    } catch (e) {
      setError(String(e));
    }
    setLoading(false);
  }

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <select
        className="bg-ink-900 border border-ink-700 rounded text-xs px-2 py-1 text-ink-200"
        value={voice}
        onChange={(e) => { setVoice(e.target.value); setAutoMatched(false); setAudioUrl(null); }}
        disabled={loading}
        title="Pick a Nigerian voice character (auto-matched to persona by default)"
      >
        {NAIJA_VOICES.map((v) => (
          <option key={v.name} value={v.name}>
            {v.name} — {v.description}
          </option>
        ))}
      </select>
      {autoMatched && persona && (
        <span className="text-[10px] text-naija-300/80 px-1" title={`Auto-matched to ${persona.user_id}`}>
          ✨ matched
        </span>
      )}
      <button
        onClick={generate}
        disabled={loading || !text}
        className="text-xs flex items-center gap-1.5 px-3 py-1 rounded-md bg-naija-700/40 hover:bg-naija-700/60 border border-naija-700/40 text-naija-100 disabled:opacity-50"
        title="Hear this in a Nigerian voice (YarnGPT)"
      >
        {loading
          ? <><Loader2 size={12} className="animate-spin"/> Synthesising…</>
          : <><Volume2 size={12}/> Listen</>}
      </button>
      {audioUrl && (
        <audio
          ref={audioRef}
          src={audioUrl}
          controls
          className="h-8 max-w-full flex-1 min-w-[180px]"
        />
      )}
      {error && (
        <span className="text-[10px] text-amber-300/90 italic">
          {error.includes("503") || error.includes("YARNGPT_API_KEY")
            ? "Set YARNGPT_API_KEY in .env"
            : error}
        </span>
      )}
    </div>
  );
}


function ReviewCard({ data, modelLabel, persona }:
  { data: SimulateReviewResponse; modelLabel: string; persona?: Persona | null }) {
  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between gap-3">
        <Badge tone="naija">{modelLabel}</Badge>
        <div className="flex items-center gap-3 text-xs text-ink-400">
          <Badge>{data.register_tier.replace("_", " ")}</Badge>
          <span>{data.latency_ms} ms</span>
        </div>
      </div>
      <StarRating rating={data.rating}/>
      <p className="text-ink-100 leading-relaxed">{data.review}</p>
      <ListenButton text={data.review} persona={persona}/>
      <p className="text-xs text-ink-400 italic">💡 {data.rationale}</p>
      <ReasoningTrace trace={data.reasoning_trace}/>
    </div>
  );
}

function TabReview({ personas }: { personas: Persona[] }) {
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

  useEffect(() => { if (!persona && personas.length) setPersona(personas[0]); }, [personas]);

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

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card"><PersonaPicker personas={personas} selected={persona} onChange={setPersona}/></div>
        <div className="card"><ProductPicker selected={product} onChange={setProduct}/></div>
      </div>

      <div className="card space-y-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)}
                 className="w-4 h-4 accent-naija-500"/>
          <span className="text-sm text-ink-200">
            Compare side-by-side <span className="text-ink-400">— pit two backbones on the same input</span>
          </span>
        </label>
        <div className={`grid gap-4 ${compare ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
          <ModelSelect label={compare ? "Model A (left)" : "Model"} value={modelA} onChange={setModelA} taskKind="review"/>
          {compare && <ModelSelect label="Model B (right)" value={modelB} onChange={setModelB} taskKind="review"/>}
        </div>
        <button className="btn-primary flex items-center gap-2 w-full md:w-auto"
                onClick={run} disabled={loading || !persona || !product}>
          {loading ? <Spinner label="Generating review..."/> : (<><Sparkles size={16}/> Generate Review</>)}
        </button>
      </div>

      {(dataA || errA || dataB || errB) && (
        <div className={`grid gap-4 ${compare ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
          <div>
            {errA && <div className="card border-red-700 text-red-300 text-sm">{errA}</div>}
            {dataA && <ReviewCard data={dataA} modelLabel={modelLabel(modelA)} persona={persona}/>}
          </div>
          {compare && (
            <div>
              {errB && <div className="card border-red-700 text-red-300 text-sm">{errB}</div>}
              {dataB && <ReviewCard data={dataB} modelLabel={modelLabel(modelB)} persona={persona}/>}
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// =========================================================================
// Product result card (used in Recommend + Multi-turn)
// =========================================================================

function RecCard({ item }: { item: RecommendResponse["recommendations"][number] }) {
  return (
    <div className="border border-ink-700 hover:border-naija-600/50 transition-colors rounded-lg p-4 flex items-start gap-4 bg-ink-900/30">
      <div className="w-10 h-10 rounded-lg bg-naija-900/40 text-naija-300 flex items-center justify-center font-bold flex-shrink-0">
        #{item.rank}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-ink-100 leading-snug">
          {item.title ?? item.product_id}
        </div>
        <div className="text-xs text-ink-300 mt-1.5 italic leading-relaxed">💡 {item.rationale}</div>
      </div>
      <div className="text-right flex-shrink-0 ml-2">
        <div className="text-base font-mono text-naija-300 font-semibold">{item.score.toFixed(2)}</div>
        <div className="text-[10px] text-ink-500 uppercase tracking-wider">score</div>
      </div>
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
  // Default to Claude — the right model for Task B re-ranking
  const [model, setModel] = useState(MODELS[1].spec);
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { if (!persona && personas.length) setPersona(personas[0]); }, [personas]);

  async function run() {
    if (!persona) return;
    setLoading(true); setErr(null); setData(null);
    const active: Persona = coldStart
      ? { ...persona, history_count: 0, review_anchors: [] } : persona;
    try {
      const resp = await api.recommend({
        persona: active, domain, k, reranker_override: model,
      });
      setData(resp);
    } catch (e) {
      setErr(String(e));
    }
    setLoading(false);
  }

  return (
    <div className="space-y-6">
      <div className="card"><PersonaPicker personas={personas} selected={persona} onChange={setPersona}/></div>

      <div className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <label className="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" checked={coldStart} onChange={(e) => setColdStart(e.target.checked)}
                   className="w-4 h-4 mt-1 accent-naija-500"/>
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
            <input type="number" min={1} max={10} value={k}
                   onChange={(e) => setK(Number(e.target.value))} className="input"/>
          </div>
          <ModelSelect label="Re-ranker" value={model} onChange={setModel} taskKind="rank"/>
        </div>
        <button className="btn-primary flex items-center gap-2" onClick={run} disabled={loading || !persona}>
          {loading ? <Spinner label="Ranking..."/> : (<><Target size={16}/> Generate Recommendations</>)}
        </button>
      </div>

      {err && <div className="card border-red-700 text-red-300 text-sm">{err}</div>}

      {data && (
        <div className="card space-y-4">
          <FallbackBanner reason={data.rerank_fallback_reason}/>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Wand2 size={18}/> {data.recommendations.length} recommendations
            </h3>
            <span className="text-xs text-ink-400">{data.latency_ms} ms</span>
          </div>
          <ResponseFlags cold={data.cold_start} cross={data.cross_domain} multi={data.multi_turn}/>
          <div className="space-y-2">
            {data.recommendations.map((item) => <RecCard key={item.product_id} item={item}/>)}
          </div>
          <ReasoningTrace trace={data.reasoning_trace}/>
        </div>
      )}
    </div>
  );
}


// =========================================================================
// Tab: Conversational Chat (real shopping concierge)
// =========================================================================

interface ChatMessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendations?: RecommendResponse["recommendations"];
  constraints?: Record<string, unknown>;
  filters?: Record<string, unknown>;
  fallback?: string | null;
  latency_ms?: number;
}

function TabChat({ personas }: { personas: Persona[] }) {
  const [persona, setPersona] = useState<Persona | null>(null);
  const [model, setModel] = useState(MODELS[1].spec);  // default Claude
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessageItem[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Welcome! What are you shopping for today? Tell me what you need, who it's for, and your budget.",
    },
  ]);
  const [sending, setSending] = useState(false);
  const [showPersonaPicker, setShowPersonaPicker] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new message
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    const userMsg: ChatMessageItem = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setSending(true);

    // Build history payload — strip welcome message if it's the only assistant turn
    const history = [...messages, userMsg]
      .filter((m, i) => !(i === 0 && m.id === "welcome"))
      .map((m) => ({ role: m.role, content: m.content }));
    // Ensure welcome is included only if user-engaged
    const payload = messages.length === 1 && messages[0].id === "welcome"
      ? [{ role: "user" as const, content: text }]
      : history;

    try {
      const resp = await api.chat({
        history: payload,
        persona: persona ?? undefined,
        reranker_override: model,
        orchestrator_override: model,
        k: 4,
      });
      setMessages((m) => [...m, {
        id: `a-${Date.now()}`,
        role: "assistant",
        content: resp.message,
        recommendations: resp.recommendations,
        constraints: resp.extracted_constraints,
        filters: resp.filters_applied,
        fallback: resp.rerank_fallback_reason,
        latency_ms: resp.latency_ms,
      }]);
    } catch (e) {
      setMessages((m) => [...m, {
        id: `e-${Date.now()}`,
        role: "assistant",
        content: `⚠ ${String(e)}`,
      }]);
    }
    setSending(false);
  }

  function reset() {
    setMessages([{
      id: "welcome",
      role: "assistant",
      content: "Welcome! What are you shopping for today? Tell me what you need, who it's for, and your budget.",
    }]);
    setInput("");
  }

  return (
    <div className="space-y-4">
      {/* ── Compact controls strip ────────────────────────────────────── */}
      <div className="card flex flex-wrap items-center gap-3 py-3">
        <button
          onClick={() => setShowPersonaPicker(!showPersonaPicker)}
          className="btn-ghost flex items-center gap-2 text-sm"
        >
          <Users size={14}/>
          {persona ? persona.user_id : "Anonymous"}
          <ChevronDown size={12} className={showPersonaPicker ? "rotate-180 transition-transform" : "transition-transform"}/>
        </button>
        <div className="flex-1 min-w-[200px]">
          <ModelSelect label="" value={model} onChange={setModel} taskKind="rank"/>
        </div>
        <button onClick={reset} className="btn-ghost text-xs flex items-center gap-1">
          <RefreshCcw size={12}/> New chat
        </button>
      </div>
      {showPersonaPicker && (
        <div className="card">
          <PersonaPicker personas={personas} selected={persona} onChange={(p) => {
            setPersona(p); setShowPersonaPicker(false);
          }}/>
        </div>
      )}

      {/* ── Chat window ───────────────────────────────────────────────── */}
      <div ref={scrollRef}
           className="card h-[60vh] overflow-y-auto flex flex-col gap-4">
        {messages.map((m) => (
          <ChatBubble key={m.id} msg={m}/>
        ))}
        {sending && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-naija-700 flex items-center justify-center flex-shrink-0 text-sm">🇳🇬</div>
            <div className="bg-ink-800 px-4 py-3 rounded-2xl rounded-tl-sm max-w-[80%]">
              <Spinner label="thinking..."/>
            </div>
          </div>
        )}
      </div>

      {/* ── Input bar ─────────────────────────────────────────────────── */}
      <div className="card flex items-end gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          rows={2}
          placeholder='Type a message... e.g. "I want a phone for my mum, under ₦100k, easy to use"'
          className="input flex-1 resize-none"
          disabled={sending}
        />
        <button onClick={send} disabled={!input.trim() || sending}
                className="btn-primary flex items-center gap-2 self-stretch">
          <Wand2 size={16}/> Send
        </button>
      </div>
      <div className="text-xs text-ink-500 px-2">
        ⏎ to send · ⇧⏎ for new line · constraints (budget, recipient, category) are extracted automatically and used as hard filters on retrieval
      </div>
    </div>
  );
}


function ChatBubble({ msg }: { msg: ChatMessageItem }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 text-sm ${
        isUser ? "bg-ink-700" : "bg-naija-700"
      }`}>
        {isUser ? "👤" : "🇳🇬"}
      </div>
      <div className={`max-w-[80%] flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
        <div className={`px-4 py-3 rounded-2xl ${
          isUser
            ? "bg-naija-600 text-white rounded-tr-sm"
            : "bg-ink-800 text-ink-100 rounded-tl-sm"
        }`}>
          <p className="whitespace-pre-wrap leading-relaxed text-sm">{msg.content}</p>
        </div>

        {/* Extracted constraints + filters under agent messages with recs */}
        {!isUser && msg.constraints && Object.values(msg.constraints).some(Boolean) && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {Object.entries(msg.constraints).map(([k, v]) => {
              if (!v || (Array.isArray(v) && v.length === 0)) return null;
              const display = Array.isArray(v) ? v.join(", ") : String(v);
              return (
                <code key={k} className="text-[10px] px-2 py-0.5 bg-ink-900 text-naija-300 rounded-full font-mono">
                  {k}={display}
                </code>
              );
            })}
          </div>
        )}

        {/* Inline recommendation cards */}
        {!isUser && msg.recommendations && msg.recommendations.length > 0 && (
          <div className="w-full space-y-2 mt-1">
            {msg.recommendations.map((item) => <RecCard key={item.product_id} item={item}/>)}
            {msg.fallback && (
              <div className="text-[10px] text-amber-300/80 px-1 italic">
                ⚠ rerank fell back to pre-rank · {msg.fallback.slice(0, 100)}
              </div>
            )}
          </div>
        )}

        {!isUser && msg.latency_ms != null && (
          <span className="text-[10px] text-ink-500 px-1">{msg.latency_ms} ms</span>
        )}
      </div>
    </div>
  );
}


// =========================================================================
// Root App
// =========================================================================

type TabKey = "review" | "recommend" | "multiturn";
const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: "review",    label: "Simulate Review", icon: <Sparkles size={14}/> },
  { key: "recommend", label: "Recommend",        icon: <Target size={14}/> },
  { key: "multiturn", label: "Chat",             icon: <MessageSquare size={14}/> },
];

export default function App() {
  const [tab, setTab] = useState<TabKey>("review");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [productsTotal, setProductsTotal] = useState(0);
  const [evalData, setEvalData] = useState(EVAL_FALLBACK);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth(null));

    fetch("/catalog/personas").then((r) => r.json())
      .then((d) => setPersonas(d.personas ?? []))
      .catch(() => setPersonas([]));

    // Just need the total count for the hero stat — server search drives the picker.
    api.searchProducts({ limit: 1 })
      .then((d) => setProductsTotal(d.total ?? 0))
      .catch(() => setProductsTotal(0));

    fetch("/catalog/eval-summary").then((r) => r.json())
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
      }).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-ink-950">
      <Header health={health}/>
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <section>
          <HeroStats personasCount={personas.length}
                     productsCount={productsTotal || 6657}
                     evalData={evalData}/>
        </section>
        <nav className="flex items-center gap-1 border-b border-ink-800">
          {TABS.map((t) => {
            const active = tab === t.key;
            return (
              <button key={t.key} onClick={() => setTab(t.key)}
                      className={`flex items-center gap-2 px-4 py-3 text-sm transition-colors border-b-2 -mb-px ${
                        active ? "border-naija-500 text-ink-50"
                               : "border-transparent text-ink-400 hover:text-ink-200"}`}>
                {t.icon} {t.label}
              </button>
            );
          })}
          <div className="ml-auto text-xs text-ink-500 flex items-center gap-2 pb-3">
            <Activity size={12}/>
            {personas.length} personas · {(productsTotal || 6657).toLocaleString()} products
          </div>
        </nav>
        {tab === "review"    && <TabReview     personas={personas}/>}
        {tab === "recommend" && <TabRecommend  personas={personas}/>}
        {tab === "multiturn" && <TabChat       personas={personas}/>}
      </main>
      <footer className="border-t border-ink-800 mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 flex flex-col md:flex-row items-center justify-between text-xs text-ink-500">
          <span>Open-source · Bluechip Tech Hackathon submission · Team Ashinze · Franca</span>
          <span className="font-mono">naija-persona-agent · v0.2</span>
        </div>
      </footer>
    </div>
  );
}
