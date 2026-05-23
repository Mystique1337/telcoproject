import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LabSidebar, LabMobileNav } from "@/components/LabSidebar";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Bot,
  CheckCircle2,
  ChevronDown,
  Github,
  History,
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
import { useAuthStore } from "@/store/auth";
import {
  saveLabExperiment,
  listLabExperiments,
  deleteLabExperiment,
  type LabExperiment,
} from "@/lib/apiClient";


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
                value={evalData.naija_rmse?.toFixed(3) ?? " - "}
                sub={`vs Claude ${evalData.claude_rmse?.toFixed(3)} · −${rmseDelta}%`} positive/>
      <StatTile icon={<TrendingUp size={16}/>} label="NDCG@10 ↑"
                value={evalData.naija_ndcg10?.toFixed(3) ?? " - "}
                sub={`vs Claude ${evalData.claude_ndcg10?.toFixed(3)} · +${ndcgDelta}%`} positive/>
    </div>
  );
}


// =========================================================================
// Persona picker (uses local personas array - already loaded once)
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
          <input className="input pl-9" placeholder="Search persona - lagos, kano, fintech, trader..."
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
// Product picker - SERVER-SIDE search (no 300-cap)
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
          <input className="input pl-9" placeholder="Search 6,657 products - tecno, blender, ankara..."
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
          <div className="text-sm text-ink-400 p-4 text-center">No products match - try a different search</div>
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
              {m.label} - {m.badge}{rec ? "" : " · ⚠ best for " + m.bestFor}
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
            (similarity + popularity + aspect-match) - still high quality given
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


// YarnGPT renders a touch slow; ~1.08x reads as natural conversational pace
// without audible pitch shift. Tweak here if it sounds off.
const NATURAL_TTS_RATE = 1.08;

// Default YarnGPT voice per Nigerian language (names whose etymology matches
// the language, so the accent reads correctly).
const LANG_VOICE: Record<string, string> = {
  yoruba: "Femi",
  hausa: "Zainab",
  igbo: "Chinenye",
};

function ListenButton({
  text, persona, language,
}: { text: string; persona?: Persona | null; language?: string | null }) {
  const [voice, setVoice] = useState("Idera");
  const [autoMatched, setAutoMatched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // If a Nigerian language is selected, the voice must match the LANGUAGE
  // (overrides persona auto-match) so the accent is correct.
  useEffect(() => {
    if (language && LANG_VOICE[language]) {
      setVoice(LANG_VOICE[language]);
      setAutoMatched(true);
      setAudioUrl(null);
    }
  }, [language]);

  // Auto-match the voice to the persona on mount / persona change
  useEffect(() => {
    if (language && LANG_VOICE[language]) return;  // language wins over persona
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
  }, [persona?.user_id, language]);

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
      // Auto-play at a natural pace. YarnGPT renders slightly slow, so a small
      // tempo nudge reads as natural without audible pitch artifacts.
      setTimeout(() => {
        if (audioRef.current) {
          audioRef.current.playbackRate = NATURAL_TTS_RATE;
          audioRef.current.play().catch(() => {});
        }
      }, 50);
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
            {v.name} - {v.description}
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
          onLoadedMetadata={(e) => { e.currentTarget.playbackRate = NATURAL_TTS_RATE; }}
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


interface ReviewIteration {
  data: SimulateReviewResponse;
  refinement?: string; // the instruction that produced THIS iteration (None for v1)
}

function ReviewCard({ iterations, modelLabel, persona, product, modelSpec, generationKnobs,
                       onRefine }:
  {
    iterations: ReviewIteration[];
    modelLabel: string;
    persona?: Persona | null;
    product?: Product | null;
    modelSpec: string;
    generationKnobs: GenerationKnobs;
    onRefine: (refinement: string, newData: SimulateReviewResponse) => void;
  }) {
  const latest = iterations[iterations.length - 1];
  const [showHistory, setShowHistory] = useState(false);
  const [refineInput, setRefineInput] = useState("");
  const [refining, setRefining] = useState(false);
  const [refineErr, setRefineErr] = useState<string | null>(null);
  const refineRef = useRef<HTMLTextAreaElement>(null);

  if (!latest) return null;
  const data = latest.data;

  const quickRefines = [
    "make it shorter",
    "make it longer",
    "use heavier Pidgin",
    "tone it down",
    "more communal framing",
    "mention price/value more",
    "regenerate",
  ];

  async function runRefine(instr: string) {
    if (!instr.trim() || refining || !persona || !product) return;
    setRefining(true); setRefineErr(null);
    try {
      const resp = await api.simulateReview({
        persona,
        product,
        backbone_override: modelSpec,
        include_reasoning: true,
        target_rating: generationKnobs.target_rating ?? undefined,
        aspect_focus: generationKnobs.aspect_focus,
        length_hint: generationKnobs.length_hint,
        tone_modifier: generationKnobs.tone_modifier,
        target_language: generationKnobs.target_language ?? undefined,
        refinement_instructions: instr,
      });
      onRefine(instr, resp);
      setRefineInput("");
    } catch (e) {
      setRefineErr(String(e));
    }
    setRefining(false);
  }

  return (
    <div className="card space-y-3">
      <div className="flex items-center justify-between gap-3">
        <Badge tone="naija">{modelLabel}</Badge>
        <div className="flex items-center gap-3 text-xs text-ink-400">
          {iterations.length > 1 && (
            <button onClick={() => setShowHistory(!showHistory)}
                    className="text-naija-300 hover:text-naija-200 text-xs flex items-center gap-1"
                    title="View prior iterations">
              <RefreshCcw size={11}/> v{iterations.length}
            </button>
          )}
          <Badge>{data.register_tier.replace("_", " ")}</Badge>
          <span>{data.latency_ms} ms</span>
        </div>
      </div>

      {latest.refinement && (
        <div className="text-[11px] px-2 py-1 rounded-md bg-naija-900/30 border border-naija-700/30 text-naija-200 italic">
          ↺ Refined with: "{latest.refinement}"
        </div>
      )}

      <StarRating rating={data.rating}/>
      {data.language && (
        <Badge tone="info">🗣 {data.language.charAt(0).toUpperCase() + data.language.slice(1)}</Badge>
      )}
      <p className="text-ink-100 leading-relaxed">{data.review}</p>
      {data.original_review && (
        <details className="text-xs text-ink-400">
          <summary className="cursor-pointer hover:text-ink-200">Show original (English)</summary>
          <p className="mt-1 italic leading-relaxed">{data.original_review}</p>
        </details>
      )}
      <ListenButton text={data.review} persona={persona} language={data.language}/>
      <p className="text-xs text-ink-400 italic">💡 {data.rationale}</p>

      {/* Iteration history */}
      {showHistory && iterations.length > 1 && (
        <div className="border-t border-ink-700/60 pt-3 space-y-3">
          <div className="text-xs text-ink-400 uppercase tracking-wider">prior iterations</div>
          {iterations.slice(0, -1).map((it, i) => (
            <div key={i} className="border-l-2 border-ink-700 pl-3 text-sm">
              <div className="text-[10px] text-ink-500 mb-1">
                v{i + 1} {it.refinement ? ` - refined with "${it.refinement}"` : "(initial)"} · ★{it.data.rating}
              </div>
              <p className="text-ink-300 text-xs leading-relaxed">{it.data.review}</p>
            </div>
          ))}
        </div>
      )}

      {/* Refinement chat */}
      <div className="border-t border-ink-700/60 pt-3 space-y-2">
        <div className="text-xs text-ink-400 uppercase tracking-wider flex items-center gap-2">
          <MessageSquare size={12}/> Refine via chat
        </div>
        <div className="flex flex-wrap gap-1.5">
          {quickRefines.map((q) => (
            <button key={q} onClick={() => runRefine(q)} disabled={refining}
                    className="text-[11px] px-2 py-1 rounded-full bg-ink-800 hover:bg-ink-700 border border-ink-700 text-ink-200 disabled:opacity-40">
              {q}
            </button>
          ))}
        </div>
        <div className="flex gap-2 items-end">
          <textarea
            ref={refineRef}
            value={refineInput}
            onChange={(e) => setRefineInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); runRefine(refineInput); }
            }}
            rows={1}
            placeholder='e.g. "use the word \"owambe\"" or "rewrite as 4 stars"'
            className="input flex-1 resize-none text-sm"
            disabled={refining}
          />
          <button onClick={() => runRefine(refineInput)} disabled={refining || !refineInput.trim()}
                  className="btn-primary text-sm">
            {refining ? <Loader2 size={14} className="animate-spin"/> : <>Apply ↵</>}
          </button>
        </div>
        {refineErr && <div className="text-xs text-amber-300/90">{refineErr}</div>}
      </div>

      <ReasoningTrace trace={data.reasoning_trace}/>
    </div>
  );
}

interface GenerationKnobs {
  target_rating: number | null;        // null = let LLM decide
  aspect_focus: string;
  length_hint: "short" | "medium" | "long";
  tone_modifier: string;
  target_language: "yoruba" | "hausa" | "igbo" | null;  // null = English/Pidgin
}

function TabReview({ personas }: { personas: Persona[] }) {
  const [persona, setPersona] = useState<Persona | null>(null);
  const [product, setProduct] = useState<Product | null>(null);
  const [modelA, setModelA] = useState(MODELS[0].spec);
  const [modelB, setModelB] = useState(MODELS[1].spec);
  const [compare, setCompare] = useState(true);
  const [iterA, setIterA] = useState<ReviewIteration[]>([]);
  const [iterB, setIterB] = useState<ReviewIteration[]>([]);
  const [errA, setErrA] = useState<string | null>(null);
  const [errB, setErrB] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const session = useAuthStore((s) => s.session);

  // Generation knobs (target rating + aspect + length + tone)
  const [knobs, setKnobs] = useState<GenerationKnobs>({
    target_rating: null,
    aspect_focus: "",
    length_hint: "medium",
    tone_modifier: "",
    target_language: null,
  });
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => { if (!persona && personas.length) setPersona(personas[0]); }, [personas]);

  async function run() {
    if (!persona || !product) return;
    setLoading(true);
    setIterA([]); setIterB([]); setErrA(null); setErrB(null);
    const baseOpts = {
      persona, product,
      include_reasoning: true,
      target_rating: knobs.target_rating ?? undefined,
      aspect_focus: knobs.aspect_focus || undefined,
      length_hint: knobs.length_hint,
      tone_modifier: knobs.tone_modifier || undefined,
      target_language: knobs.target_language ?? undefined,
    };
    const callA = api.simulateReview({ ...baseOpts, backbone_override: modelA })
                       .then((d) => {
                         setIterA([{ data: d }]);
                         if (session) {
                           saveLabExperiment({
                             experiment_type: "review",
                             product_title: product.title ?? product.product_id,
                             persona_id: persona.user_id,
                             rating: d.rating ?? undefined,
                             result: d,
                           }).catch(() => {});
                         }
                       })
                       .catch((e) => setErrA(String(e)));
    const callB = compare
      ? api.simulateReview({ ...baseOpts, backbone_override: modelB })
            .then((d) => {
              setIterB([{ data: d }]);
              if (session) {
                saveLabExperiment({
                  experiment_type: "review",
                  product_title: product.title ?? product.product_id,
                  persona_id: persona.user_id,
                  rating: d.rating ?? undefined,
                  result: d,
                }).catch(() => {});
              }
            })
            .catch((e) => setErrB(String(e)))
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
            Compare side-by-side <span className="text-ink-400"> - pit two backbones on the same input</span>
          </span>
        </label>
        <div className={`grid gap-4 ${compare ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
          <ModelSelect label={compare ? "Model A (left)" : "Model"} value={modelA} onChange={setModelA} taskKind="review"/>
          {compare && <ModelSelect label="Model B (right)" value={modelB} onChange={setModelB} taskKind="review"/>}
        </div>

        {/* ── Generation knobs ──────────────────────────────────────── */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
          <div>
            <span className="label">Target rating</span>
            <div className="flex items-center gap-1.5 flex-wrap">
              <button
                onClick={() => setKnobs({...knobs, target_rating: null})}
                className={`text-xs px-2.5 py-1 rounded-md border ${knobs.target_rating === null
                  ? "bg-naija-600 text-white border-naija-600"
                  : "bg-ink-800 text-ink-300 border-ink-700 hover:bg-ink-700"}`}
                title="Let the model decide based on persona × product fit">
                ✨ any
              </button>
              {[1, 2, 3, 4, 5].map((n) => (
                <button key={n}
                        onClick={() => setKnobs({...knobs, target_rating: n})}
                        className={`text-xs px-2.5 py-1 rounded-md border flex items-center gap-0.5 ${knobs.target_rating === n
                          ? "bg-amber-600 text-white border-amber-600"
                          : "bg-ink-800 text-ink-300 border-ink-700 hover:bg-ink-700"}`}
                        title={`Force a ${n}-star review`}>
                  {Array.from({length: n}).map((_, i) => <Star key={i} size={10} className="fill-current"/>)}
                </button>
              ))}
            </div>
          </div>

          <div>
            <span className="label">Length</span>
            <div className="flex items-center gap-1.5">
              {(["short", "medium", "long"] as const).map((l) => (
                <button key={l}
                        onClick={() => setKnobs({...knobs, length_hint: l})}
                        className={`text-xs px-3 py-1 rounded-md border ${knobs.length_hint === l
                          ? "bg-naija-600 text-white border-naija-600"
                          : "bg-ink-800 text-ink-300 border-ink-700 hover:bg-ink-700"}`}>
                  {l}
                </button>
              ))}
            </div>
          </div>

          <div>
            <span className="label">Language</span>
            <div className="flex items-center gap-1.5 flex-wrap">
              {([
                { v: null, label: "EN / Pidgin" },
                { v: "yoruba", label: "Yorùbá" },
                { v: "hausa", label: "Hausa" },
                { v: "igbo", label: "Igbo" },
              ] as const).map((opt) => (
                <button key={String(opt.v)}
                        onClick={() => setKnobs({...knobs, target_language: opt.v})}
                        className={`text-xs px-2.5 py-1 rounded-md border ${knobs.target_language === opt.v
                          ? "bg-naija-600 text-white border-naija-600"
                          : "bg-ink-800 text-ink-300 border-ink-700 hover:bg-ink-700"}`}
                        title={opt.v ? `Generate, then translate the review into ${opt.label}` : "English / Nigerian Pidgin (no translation)"}>
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-xs text-ink-400 hover:text-ink-200 flex items-center gap-1"
        >
          <ChevronDown size={12} className={showAdvanced ? "rotate-180 transition-transform" : "transition-transform"}/>
          {showAdvanced ? "Hide" : "Show"} advanced (aspect focus, tone)
        </button>
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <span className="label">Aspect focus <span className="text-ink-500">(optional)</span></span>
              <input
                type="text"
                value={knobs.aspect_focus}
                onChange={(e) => setKnobs({...knobs, aspect_focus: e.target.value})}
                placeholder="e.g. battery life, value for money, Owambe use"
                className="input text-sm"
                maxLength={120}
              />
            </div>
            <div>
              <span className="label">Tone <span className="text-ink-500">(optional)</span></span>
              <input
                type="text"
                value={knobs.tone_modifier}
                onChange={(e) => setKnobs({...knobs, tone_modifier: e.target.value})}
                placeholder="e.g. enthusiastic, skeptical, frustrated"
                className="input text-sm"
                maxLength={80}
              />
            </div>
          </div>
        )}

        <button className="btn-primary flex items-center gap-2 w-full md:w-auto"
                onClick={run} disabled={loading || !persona || !product}>
          {loading ? <Spinner label="Generating review..."/> : (<><Sparkles size={16}/> Generate Review</>)}
        </button>
      </div>

      {(iterA.length || errA || iterB.length || errB) ? (
        <div className={`grid gap-4 ${compare ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"}`}>
          <div>
            {errA && <div className="card border-red-700 text-red-300 text-sm">{errA}</div>}
            {iterA.length > 0 && (
              <ReviewCard
                iterations={iterA}
                modelLabel={modelLabel(modelA)}
                persona={persona}
                product={product}
                modelSpec={modelA}
                generationKnobs={knobs}
                onRefine={(r, d) => setIterA([...iterA, { data: d, refinement: r }])}
              />
            )}
          </div>
          {compare && (
            <div>
              {errB && <div className="card border-red-700 text-red-300 text-sm">{errB}</div>}
              {iterB.length > 0 && (
                <ReviewCard
                  iterations={iterB}
                  modelLabel={modelLabel(modelB)}
                  persona={persona}
                  product={product}
                  modelSpec={modelB}
                  generationKnobs={knobs}
                  onRefine={(r, d) => setIterB([...iterB, { data: d, refinement: r }])}
                />
              )}
            </div>
          )}
        </div>
      ) : null}
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
        <div className="flex flex-wrap items-center gap-2 mt-1.5">
          {item.price_naira != null && (
            <span className="text-sm font-mono font-semibold text-emerald-300 tabular-nums">
              ₦{Number(item.price_naira).toLocaleString()}
            </span>
          )}
          {item.category && (
            <span className="text-[10px] uppercase tracking-wider text-ink-400 border border-ink-700 rounded px-1.5 py-0.5">
              {item.category}
            </span>
          )}
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
  // Default to Claude - the right model for Task B re-ranking
  const [model, setModel] = useState(MODELS[2].spec);  // default Claude Sonnet
  const [data, setData] = useState<RecommendResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const session = useAuthStore((s) => s.session);

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
      if (session) {
        const topTitle = resp.recommendations?.[0]?.title
          ?? resp.recommendations?.[0]?.product_id
          ?? domain;
        saveLabExperiment({
          experiment_type: "recommend",
          product_title: topTitle,
          persona_id: persona.user_id,
          result: resp,
        }).catch(() => {});
      }
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
  const [model, setModel] = useState(MODELS[2].spec);  // default Claude Sonnet
  const [chatLang, setChatLang] = useState<"yoruba" | "hausa" | "igbo" | null>(null);
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

    // Build history payload - strip welcome message if it's the only assistant turn
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
        language: chatLang,
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
        <select
          className="bg-ink-900 border border-ink-700 rounded text-xs px-2 py-1.5 text-ink-200"
          value={chatLang ?? ""}
          onChange={(e) => setChatLang((e.target.value || null) as typeof chatLang)}
          title="Reply language - the assistant responds directly in this language"
        >
          <option value="">English / Pidgin</option>
          <option value="yoruba">Yorùbá</option>
          <option value="hausa">Hausa</option>
          <option value="igbo">Igbo</option>
        </select>
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
// Tab: Experiment History
// =========================================================================

function TabExperiments() {
  const session = useAuthStore((s) => s.session);
  const [experiments, setExperiments] = useState<LabExperiment[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!session) return;
    setLoading(true);
    setError(null);
    listLabExperiments()
      .then((data) => setExperiments(data))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [session]);

  function toggleExpand(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  async function handleDelete(id: string) {
    if (!window.confirm("Delete this experiment?")) return;
    setDeleting((prev) => new Set(prev).add(id));
    try {
      await deleteLabExperiment(id);
      setExperiments((prev) => prev.filter((e) => e.id !== id));
    } catch {
      // silently ignore
    }
    setDeleting((prev) => {
      const next = new Set(prev);
      next.delete(id);
      return next;
    });
  }

  if (!session) {
    return (
      <div className="card flex flex-col items-center gap-4 py-16 text-center">
        <History size={40} className="text-ink-600"/>
        <div className="text-ink-300 text-lg font-medium">Sign in to save and view your experiment history</div>
        <div className="text-ink-500 text-sm">Your review and recommendation runs will be saved automatically once you're signed in.</div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="card flex items-center justify-center py-16">
        <Spinner label="Loading experiment history..."/>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card border-red-700 text-red-300 text-sm py-6 text-center">
        Failed to load experiments: {error}
      </div>
    );
  }

  if (experiments.length === 0) {
    return (
      <div className="card flex flex-col items-center gap-4 py-16 text-center">
        <History size={40} className="text-ink-600"/>
        <div className="text-ink-300 text-lg font-medium">No experiments yet</div>
        <div className="text-ink-500 text-sm">Run an experiment to see it saved here.</div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-ink-300 uppercase tracking-wider flex items-center gap-2">
          <History size={14}/> {experiments.length} saved experiment{experiments.length !== 1 ? "s" : ""}
        </h3>
      </div>
      {experiments.map((exp) => {
        const isExpanded = expanded.has(exp.id);
        const isDeleting = deleting.has(exp.id);
        const date = new Date(exp.created_at).toLocaleString("en-GB", {
          day: "2-digit", month: "short", year: "numeric",
          hour: "2-digit", minute: "2-digit",
        });
        return (
          <div key={exp.id} className="card border border-ink-800 bg-ink-900/40 space-y-3">
            {/* Row header */}
            <div className="flex items-start gap-3">
              {/* Type badge */}
              <span className={`flex-shrink-0 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                exp.experiment_type === "review"
                  ? "bg-naija-900/40 text-naija-300 border-naija-700/50"
                  : "bg-sky-900/40 text-sky-300 border-sky-700/50"
              }`}>
                {exp.experiment_type}
              </span>

              {/* Product name — click to expand */}
              <button
                className="flex-1 text-left text-sm font-medium text-ink-100 hover:text-naija-300 transition-colors leading-snug"
                onClick={() => toggleExpand(exp.id)}
                title="Click to expand result"
              >
                {exp.product_title}
              </button>

              {/* Meta: persona, rating, date */}
              <div className="flex items-center gap-3 flex-shrink-0 ml-auto">
                {exp.persona_id && (
                  <span className="text-xs text-ink-400 hidden sm:inline">{exp.persona_id}</span>
                )}
                {exp.rating != null && (
                  <div className="flex items-center gap-0.5">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <Star key={n} size={11}
                            className={n <= exp.rating! ? "fill-amber-400 text-amber-400" : "text-ink-700"}/>
                    ))}
                  </div>
                )}
                <span className="text-[10px] text-ink-500 whitespace-nowrap">{date}</span>
                <button
                  onClick={() => handleDelete(exp.id)}
                  disabled={isDeleting}
                  className="text-ink-500 hover:text-red-400 transition-colors disabled:opacity-40 flex-shrink-0"
                  title="Delete experiment"
                >
                  {isDeleting ? <Loader2 size={13} className="animate-spin"/> : <Trash2 size={13}/>}
                </button>
              </div>
            </div>

            {/* Persona sub-row on mobile */}
            {exp.persona_id && (
              <div className="text-xs text-ink-500 sm:hidden">persona: {exp.persona_id}</div>
            )}

            {/* Expanded JSON result */}
            {isExpanded && (
              <div className="mt-1">
                <div className="text-[10px] text-ink-500 uppercase tracking-wider mb-1.5">Full result</div>
                <pre className="bg-ink-950 border border-ink-800 rounded-lg p-3 text-xs text-ink-300 overflow-x-scroll leading-relaxed max-h-80 overflow-y-auto">
                  {JSON.stringify(exp.result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}


// =========================================================================
// Root App
// =========================================================================

type TabKey = "review" | "recommend" | "multiturn" | "experiments";
const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: "review",      label: "Simulate Review",  icon: <Sparkles size={14}/> },
  { key: "recommend",   label: "Recommend",         icon: <Target size={14}/> },
  { key: "multiturn",   label: "Chat",              icon: <MessageSquare size={14}/> },
  { key: "experiments", label: "My Experiments",    icon: <History size={15}/> },
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

    // Just need the total count for the hero stat - server search drives the picker.
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

  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen bg-ink-950 text-ink-50">
      {/* Sidebar */}
      <LabSidebar tab={tab} onTabChange={setTab} apiOnline={!!health} />

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        <LabMobileNav tab={tab} onTabChange={setTab} apiOnline={!!health} />

        <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8 space-y-8">
          <section>
            <HeroStats personasCount={personas.length}
                       productsCount={productsTotal || 6657}
                       evalData={evalData}/>
          </section>
          {/* Tab content — sidebar controls which tab is active */}
          {tab === "review"      && <TabReview      personas={personas}/>}
          {tab === "recommend"   && <TabRecommend   personas={personas}/>}
          {tab === "multiturn"   && <TabChat         personas={personas}/>}
          {tab === "experiments" && <TabExperiments/>}
        </main>

        <footer className="border-t border-ink-800 mt-8">
          <div className="px-6 py-4 flex items-center justify-between text-xs text-ink-600">
            <span>NaijaPersona Labz · developer console</span>
            <span className="font-mono text-ink-700">v0.2</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
