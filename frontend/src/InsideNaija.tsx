// InsideNaija — pre-launch synthetic customer panel for the Nigerian market.
// Landing hero (live persona reactions) + the panel dashboard.

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowRight, BarChart3, Check, ChevronDown, Clock, Globe2, Loader2,
  Package, Play, Quote, Sparkles, Star, ThumbsDown, ThumbsUp, Users, Volume2, Zap,
} from "lucide-react";

import { api } from "./api";
import type { PanelReaction, PanelResponse, Product } from "./types";

// ─────────────────────────────────────────────────────────────────────────
// Shared bits
// ─────────────────────────────────────────────────────────────────────────

const ZONE_COLOR: Record<string, string> = {
  "South-West": "bg-emerald-500",
  "South-East": "bg-sky-500",
  "South-South": "bg-cyan-500",
  "North-West": "bg-amber-500",
  "North-East": "bg-orange-500",
  "North-Central": "bg-violet-500",
  Unknown: "bg-ink-500",
};

const LANG_VOICE: Record<string, string> = { yoruba: "Femi", hausa: "Zainab", igbo: "Chinenye" };

function initials(id: string): string {
  const parts = id.replace(/_/g, " ").split(" ");
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase();
}

function prettyName(id: string): string {
  return id.split("_")[0].replace(/\b\w/g, (c) => c.toUpperCase());
}

// Consistent illustrated avatar per persona (DiceBear, keyless, reliable).
function avatarUrl(seed: string): string {
  return `https://api.dicebear.com/9.x/personas/svg?seed=${encodeURIComponent(seed)}&backgroundType=gradientLinear`;
}

function Stars({ n, size = 14 }: { n: number; size?: number }) {
  return (
    <span className="inline-flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star key={i} size={size}
              className={i <= n ? "fill-amber-400 text-amber-400" : "text-ink-700"} />
      ))}
    </span>
  );
}

function Avatar({ id, zone, size = 40, speaking = false }:
  { id: string; zone: string; size?: number; speaking?: boolean }) {
  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      {/* pulsing rings while speaking */}
      {speaking && (
        <>
          <span className="absolute inset-0 rounded-full bg-naija-500/40 animate-ping" />
          <span className="absolute -inset-1 rounded-full ring-2 ring-naija-400/60 animate-pulse" />
        </>
      )}
      <div
        className={`${ZONE_COLOR[zone] ?? "bg-ink-600"} relative rounded-full flex items-center justify-center font-bold text-white transition-transform overflow-hidden ${speaking ? "scale-105" : ""}`}
        style={{ width: size, height: size, fontSize: size * 0.36 }}
        title={`${prettyName(id)} · ${zone}`}
      >
        <span className="absolute inset-0 flex items-center justify-center">{initials(id)}</span>
        <img src={avatarUrl(id)} alt={prettyName(id)} loading="lazy"
             className="absolute inset-0 w-full h-full object-cover"
             onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }} />
        {/* "talking" sound bars overlaid at the chin */}
        {speaking && (
          <span className="absolute -bottom-1 left-1/2 -translate-x-1/2 flex items-end gap-[2px] h-2.5">
            {[0, 1, 2].map((i) => (
              <span key={i} className="w-[2px] bg-naija-300 rounded-full animate-[talkbar_0.5s_ease-in-out_infinite]"
                    style={{ height: "100%", animationDelay: `${i * 0.12}s` }} />
            ))}
          </span>
        )}
      </div>
    </div>
  );
}

// Hook: synthesise + play TTS, exposing loading + speaking state for the avatar.
function useSpeech(text: string, language?: string | null) {
  const [loading, setLoading] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const urlRef = useRef<string | null>(null);

  async function play() {
    if (loading) return;
    if (audioRef.current && urlRef.current) {  // replay cached
      audioRef.current.currentTime = 0;
      audioRef.current.play().catch(() => {});
      return;
    }
    setLoading(true);
    try {
      const voice = (language && LANG_VOICE[language]) || "Idera";
      const r = await fetch("/tts", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text.slice(0, 500), voice }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const url = URL.createObjectURL(await r.blob());
      urlRef.current = url;
      const a = new Audio(url);
      a.playbackRate = 1.08;
      a.onplay = () => setSpeaking(true);
      a.onended = () => setSpeaking(false);
      a.onpause = () => setSpeaking(false);
      audioRef.current = a;
      a.play().catch(() => {});
    } catch { /* ignore */ }
    setLoading(false);
  }
  return { play, loading, speaking };
}

function ListenButton({ play, loading, speaking }:
  { play: () => void; loading: boolean; speaking: boolean }) {
  return (
    <button onClick={play} disabled={loading}
            className={`text-[11px] inline-flex items-center gap-1 transition-colors ${speaking ? "text-naija-300" : "text-ink-400 hover:text-naija-300"}`}
            title="Hear it in a Nigerian voice">
      {loading ? <Loader2 size={11} className="animate-spin" />
        : speaking ? <Volume2 size={11} className="animate-pulse" />
        : <Volume2 size={11} />}
      {loading ? "…" : speaking ? "Speaking" : "Listen"}
    </button>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Hero — live persona reaction amplifier
// ─────────────────────────────────────────────────────────────────────────

const HERO_PRODUCT: Product = {
  product_id: "demo",
  title: "Samsung Galaxy A05s",
  category: "phones-and-tablets",
  price_naira: 92000,
  description:
    "6.7-inch display, 50MP camera, 5000mAh battery, 128GB storage. Budget Android phone.",
  domain: "jumia",
};

function Hero({ onTryItOwn }: { onTryItOwn: () => void }) {
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const [shown, setShown] = useState<PanelReaction[]>([]);
  const [agg, setAgg] = useState<PanelResponse["aggregate"] | null>(null);

  async function react() {
    if (running) return;
    setRunning(true); setDone(false); setShown([]); setAgg(null);
    try {
      // Six personas spanning all six geopolitical zones for the hero demo.
      const ids = ["chinwe_owerri", "tunde_lagos", "aisha_kano",
                   "blessing_warri", "halima_jos", "ibrahim_maiduguri"];
      // Teaser uses the fast frontier backbone so the hero feels instant; the
      // real panel below defaults to NaijaReviewer-8B (+ frontier fallback).
      const res = await api.panel({
        product: HERO_PRODUCT, persona_ids: ids,
        backbone_override: "anthropic:claude-sonnet-4-20250514",
      });
      // Reveal reactions one by one for the "watch Nigeria react" effect
      for (let i = 0; i < res.reactions.length; i++) {
        await new Promise((r) => setTimeout(r, 420));
        setShown(res.reactions.slice(0, i + 1));
      }
      setAgg(res.aggregate);
      setDone(true);
    } catch {
      /* network hiccup — leave hero idle */
    }
    setRunning(false);
  }

  return (
    <section className="relative overflow-hidden">
      {/* glow */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-naija-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="relative max-w-6xl mx-auto px-6 pt-20 pb-12 grid lg:grid-cols-2 gap-12 items-center">
        {/* Left — pitch */}
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-medium text-naija-300 bg-naija-900/40 border border-naija-700/40 rounded-full px-3 py-1 mb-6">
            <Sparkles size={13} /> Pre-launch consumer intelligence
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-ink-50 leading-[1.1] tracking-tight">
            See how <span className="text-naija-400">Nigeria</span> will react —
            <br /> before you launch.
          </h1>
          <p className="mt-5 text-lg text-ink-300 leading-relaxed max-w-lg">
            Drop in any product and a calibrated panel of 24 Nigerian personas
            reacts with real ratings and reviews — across every region, register
            and religion. A ₦5M panel study, in 90 seconds.
          </p>
          <div className="mt-8 flex items-center gap-3">
            <button onClick={react} disabled={running}
                    className="inline-flex items-center gap-2 bg-naija-600 hover:bg-naija-500 disabled:opacity-60 text-white font-semibold rounded-lg px-5 py-3 transition-colors">
              {running ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
              {running ? "Nigeria is reacting…" : "Watch Nigeria react"}
            </button>
            <button onClick={onTryItOwn}
                    className="inline-flex items-center gap-2 text-ink-200 hover:text-white font-medium px-4 py-3 transition-colors">
              Try your product <ArrowRight size={16} />
            </button>
          </div>
          <div className="mt-8 flex items-center gap-6 text-xs text-ink-400">
            <span className="inline-flex items-center gap-1.5"><Clock size={13} /> ~90s per study</span>
            <span className="inline-flex items-center gap-1.5"><Users size={13} /> 24 personas</span>
            <span className="inline-flex items-center gap-1.5"><Globe2 size={13} /> 4 languages</span>
          </div>
        </div>

        {/* Right — live reaction panel */}
        <div className="bg-ink-900/60 border border-ink-700 rounded-2xl p-5 shadow-2xl backdrop-blur">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="text-sm font-semibold text-ink-100">{HERO_PRODUCT.title}</div>
              <div className="text-xs text-ink-400">
                ₦{HERO_PRODUCT.price_naira?.toLocaleString()} · phones-and-tablets
              </div>
            </div>
            {agg && (
              <div className="text-right">
                <div className="text-2xl font-bold text-naija-300 tabular-nums">{agg.avg_rating}★</div>
                <div className="text-[10px] text-ink-400 uppercase tracking-wide">panel avg</div>
              </div>
            )}
          </div>

          <div className="space-y-2 min-h-[260px]">
            {shown.length === 0 && !running && (
              <div className="h-[260px] flex flex-col items-center justify-center text-ink-500 text-sm gap-2">
                <Users size={28} className="opacity-40" />
                Hit “Watch Nigeria react” to see the panel light up
              </div>
            )}
            {running && shown.length === 0 && (
              <div className="h-[260px] flex items-center justify-center">
                <Loader2 size={24} className="animate-spin text-naija-400" />
              </div>
            )}
            {shown.map((r, i) => (
              <div key={r.persona_id}
                   className="flex items-start gap-3 bg-ink-800/40 rounded-lg p-2.5 animate-[fadeIn_0.35s_ease]"
                   style={{ animationDelay: `${i * 30}ms` }}>
                <Avatar id={r.persona_id} zone={r.zone} size={34} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold text-ink-100">{prettyName(r.persona_id)}</span>
                    <Stars n={r.rating} size={11} />
                  </div>
                  <div className="text-[11px] text-ink-300 leading-snug mt-0.5 line-clamp-2">"{r.review}"</div>
                </div>
              </div>
            ))}
          </div>

          {agg && (
            <div className="mt-4 pt-4 border-t border-ink-700 flex items-center justify-between">
              <div>
                <div className="text-lg font-bold text-naija-300 tabular-nums">{agg.buy_likelihood}%</div>
                <div className="text-[10px] text-ink-400 uppercase tracking-wide">buy-likelihood</div>
              </div>
              <div className="flex items-center gap-1 text-xs">
                <span className="text-emerald-400">{agg.sentiment_split.positive}+</span>
                <span className="text-ink-500">·</span>
                <span className="text-ink-300">{agg.sentiment_split.neutral}=</span>
                <span className="text-ink-500">·</span>
                <span className="text-red-400">{agg.sentiment_split.negative}−</span>
              </div>
              <button onClick={onTryItOwn}
                      className="text-xs text-naija-300 hover:text-naija-200 inline-flex items-center gap-1">
                Run your own <ArrowRight size={13} />
              </button>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Value strip + how it works
// ─────────────────────────────────────────────────────────────────────────

function ValueStrip() {
  const items = [
    { icon: <Zap size={18} />, k: "₦5M → ₦0", v: "vs a traditional panel study" },
    { icon: <Clock size={18} />, k: "6 weeks → 90s", v: "from question to verdict" },
    { icon: <Users size={18} />, k: "24 personas", v: "6 zones × registers × religions" },
    { icon: <Globe2 size={18} />, k: "4 languages", v: "English, Pidgin, Yorùbá, Hausa, Igbo" },
  ];
  return (
    <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-2 lg:grid-cols-4 gap-4">
      {items.map((it) => (
        <div key={it.k} className="bg-ink-900/40 border border-ink-800 rounded-xl p-4">
          <div className="text-naija-400 mb-2">{it.icon}</div>
          <div className="text-lg font-bold text-ink-50">{it.k}</div>
          <div className="text-xs text-ink-400 mt-0.5">{it.v}</div>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// How it works + Why sections (real imagery)
// ─────────────────────────────────────────────────────────────────────────

function SectionPhoto({ q, className = "" }: { q: string; className?: string }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    let c = false;
    fetch(`/shop/photo?q=${encodeURIComponent(q)}`).then((r) => r.json())
      .then((d) => { if (!c) setUrl(d.url || null); }).catch(() => {});
    return () => { c = true; };
  }, [q]);
  return (
    <div className={`relative overflow-hidden bg-ink-800 ${className}`}>
      {url && <img src={url} alt="" className="absolute inset-0 w-full h-full object-cover" loading="lazy" />}
      <div className="absolute inset-0 bg-gradient-to-tr from-ink-950/80 via-ink-950/30 to-transparent" />
    </div>
  );
}

function HowItWorks({ onTry }: { onTry: () => void }) {
  const steps = [
    { n: 1, icon: <Package size={20} />, t: "Describe your product", d: "Title, price, a line of detail — or drop a photo. Takes 20 seconds." },
    { n: 2, icon: <Users size={20} />, t: "The panel reacts", d: "24 Nigerian personas across 6 zones rate it and write a real review in their own register." },
    { n: 3, icon: <BarChart3 size={20} />, t: "Read the verdict", d: "Predicted rating, buy-likelihood, who's warm/cold, and the recurring praise & concerns." },
  ];
  return (
    <section className="max-w-6xl mx-auto px-6 py-16">
      <div className="text-center max-w-2xl mx-auto mb-12">
        <h2 className="text-3xl font-bold text-ink-50 tracking-tight">From product to verdict in 90 seconds</h2>
        <p className="text-ink-400 mt-3">A traditional Nigerian panel study costs ₦5M and takes 6 weeks. InsideNaija simulates one instantly so you can kill bad ideas before they cost you.</p>
      </div>
      <div className="grid md:grid-cols-3 gap-6">
        {steps.map((s) => (
          <div key={s.n} className="bg-ink-900/40 border border-ink-800 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-naija-600/20 border border-naija-700/40 text-naija-300 flex items-center justify-center">{s.icon}</div>
              <span className="text-xs text-ink-500 font-mono">STEP {s.n}</span>
            </div>
            <h3 className="text-lg font-semibold text-ink-50">{s.t}</h3>
            <p className="text-sm text-ink-400 mt-2 leading-relaxed">{s.d}</p>
          </div>
        ))}
      </div>
      <div className="mt-10 text-center">
        <button onClick={onTry}
                className="inline-flex items-center gap-2 bg-naija-600 hover:bg-naija-500 text-white font-semibold rounded-lg px-6 py-3 transition-colors">
          Run a free study <ArrowRight size={16} />
        </button>
      </div>
    </section>
  );
}

function WhySection() {
  return (
    <section className="max-w-6xl mx-auto px-6 py-12">
      <div className="grid lg:grid-cols-2 gap-8 items-stretch">
        <SectionPhoto q="nigeria lagos market shopping" className="rounded-2xl min-h-[300px] border border-ink-800" />
        <div className="flex flex-col justify-center">
          <h2 className="text-2xl md:text-3xl font-bold text-ink-50 tracking-tight">
            Built for how Nigerians actually shop & speak
          </h2>
          <p className="text-ink-300 mt-4 leading-relaxed">
            Vanilla AI flattens "e too much abeg" into bland English and reads
            "Alhamdulillah" as a complaint. InsideNaija is powered by
            <span className="text-naija-300"> NaijaReviewer-8B</span>, fine-tuned on Nigerian
            reviews, so reactions land in the right register — Pidgin, Yorùbá,
            Hausa, Igbo — for every region, age and faith.
          </p>
          <ul className="mt-5 space-y-2.5">
            {["Calibrated to 6 geopolitical zones", "Predicts ratings within ±1.1★ on unseen products", "Hear every reaction in a Nigerian voice"].map((x) => (
              <li key={x} className="flex items-center gap-2.5 text-sm text-ink-200">
                <Check size={16} className="text-naija-400 flex-shrink-0" /> {x}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// The panel app — input + dashboard
// ─────────────────────────────────────────────────────────────────────────

function Bar({ label, value, max, suffix = "", tone = "naija" }:
  { label: string; value: number; max: number; suffix?: string; tone?: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  const color = tone === "amber" ? "bg-amber-500" : tone === "sky" ? "bg-sky-500" : "bg-naija-500";
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-ink-300 w-32 truncate text-right">{label}</span>
      <div className="flex-1 bg-ink-800 rounded-full h-2.5 overflow-hidden">
        <div className={`${color} h-full rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-ink-200 tabular-nums w-12">{value}{suffix}</span>
    </div>
  );
}

function ReactionCard({ r }: { r: PanelReaction }) {
  const speech = useSpeech(r.review, r.language);
  const tone = r.sentiment === "positive" ? "border-l-emerald-500"
    : r.sentiment === "negative" ? "border-l-red-500" : "border-l-ink-600";
  return (
    <div className={`bg-ink-900/40 border border-ink-800 border-l-2 ${tone} rounded-lg p-3.5 ${speech.speaking ? "ring-1 ring-naija-600/40" : ""}`}>
      <div className="flex items-start gap-3">
        <Avatar id={r.persona_id} zone={r.zone} size={38} speaking={speech.speaking} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-semibold text-ink-100">{prettyName(r.persona_id)}</span>
            <Stars n={r.rating} />
          </div>
          <div className="text-[10px] text-ink-400 mt-0.5">
            {r.zone} · {r.register_tier.replace(/_/g, " ")}{r.occupation ? ` · ${r.occupation}` : ""}
          </div>
        </div>
      </div>
      <p className="text-sm text-ink-200 leading-relaxed mt-2.5">"{r.review}"</p>
      <div className="mt-2"><ListenButton {...speech} /></div>
    </div>
  );
}

function Dashboard({ data }: { data: PanelResponse }) {
  const a = data.aggregate;
  const maxDist = Math.max(...Object.values(a.rating_distribution), 1);
  const verdict = a.avg_rating >= 4 ? { t: "Strong fit", c: "text-emerald-400" }
    : a.avg_rating >= 3 ? { t: "Mixed — needs work", c: "text-amber-400" }
    : { t: "Weak fit", c: "text-red-400" };

  return (
    <div className="space-y-6">
      {/* Verdict header */}
      <div className="grid md:grid-cols-4 gap-4">
        <div className="bg-ink-900/60 border border-ink-700 rounded-xl p-5">
          <div className="text-xs text-ink-400 uppercase tracking-wide">Panel verdict</div>
          <div className={`text-xl font-bold mt-1 ${verdict.c}`}>{verdict.t}</div>
          <div className="text-xs text-ink-400 mt-1">{a.n_personas} personas</div>
        </div>
        <div className="bg-ink-900/60 border border-ink-700 rounded-xl p-5">
          <div className="text-xs text-ink-400 uppercase tracking-wide">Predicted rating</div>
          <div className="text-3xl font-bold text-naija-300 tabular-nums mt-1">{a.avg_rating}★</div>
          {data.rmse_band != null && (
            <div className="text-[10px] text-ink-400 mt-1" title="Held-out rating-prediction error (RMSE) on products the model never saw in training.">
              ± {data.rmse_band}★ predicted band
            </div>
          )}
        </div>
        <div className="bg-ink-900/60 border border-ink-700 rounded-xl p-5">
          <div className="text-xs text-ink-400 uppercase tracking-wide">Buy-likelihood</div>
          <div className="text-3xl font-bold text-naija-300 tabular-nums mt-1">{a.buy_likelihood}%</div>
        </div>
        <div className="bg-ink-900/60 border border-ink-700 rounded-xl p-5">
          <div className="text-xs text-ink-400 uppercase tracking-wide">Sentiment</div>
          <div className="flex items-center gap-2 mt-2 text-sm">
            <span className="inline-flex items-center gap-1 text-emerald-400"><ThumbsUp size={13} />{a.sentiment_split.positive}</span>
            <span className="text-ink-400">{a.sentiment_split.neutral}</span>
            <span className="inline-flex items-center gap-1 text-red-400"><ThumbsDown size={13} />{a.sentiment_split.negative}</span>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Rating distribution */}
        <div className="bg-ink-900/40 border border-ink-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-ink-100 flex items-center gap-2 mb-4"><BarChart3 size={15} /> Rating distribution</h3>
          <div className="space-y-2">
            {[5, 4, 3, 2, 1].map((s) => (
              <Bar key={s} label={`${s} star`} value={a.rating_distribution[String(s)] ?? 0} max={maxDist} />
            ))}
          </div>
        </div>

        {/* Themes */}
        <div className="bg-ink-900/40 border border-ink-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-ink-100 flex items-center gap-2 mb-4"><Quote size={15} /> What the panel said</h3>
          <div className="text-xs text-emerald-400 font-medium mb-1">Praised</div>
          <div className="flex flex-wrap gap-1.5 mb-4">
            {a.themes.praised.length ? a.themes.praised.map((t) => (
              <span key={t} className="text-xs bg-emerald-900/30 text-emerald-300 border border-emerald-700/30 rounded-full px-2.5 py-1">
                <Check size={10} className="inline mr-1" />{t}
              </span>
            )) : <span className="text-xs text-ink-500">—</span>}
          </div>
          <div className="text-xs text-amber-400 font-medium mb-1">Concerns</div>
          <div className="flex flex-wrap gap-1.5">
            {a.themes.complaints.length ? a.themes.complaints.map((t) => (
              <span key={t} className="text-xs bg-amber-900/30 text-amber-200 border border-amber-700/30 rounded-full px-2.5 py-1">{t}</span>
            )) : <span className="text-xs text-ink-500">—</span>}
          </div>
        </div>
      </div>

      {/* Cohorts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-ink-900/40 border border-ink-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-ink-100 mb-4">By geopolitical zone</h3>
          <div className="space-y-2">
            {Object.entries(a.by_zone).map(([z, s]) => (
              <Bar key={z} label={`${z} (${s.n})`} value={s.avg_rating} max={5} suffix="★" tone="sky" />
            ))}
          </div>
        </div>
        <div className="bg-ink-900/40 border border-ink-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-ink-100 mb-4">By register tier</h3>
          <div className="space-y-2">
            {Object.entries(a.by_register).map(([z, s]) => (
              <Bar key={z} label={`${z.replace(/_/g, " ")} (${s.n})`} value={s.avg_rating} max={5} suffix="★" />
            ))}
          </div>
        </div>
      </div>

      {/* Reactions */}
      <div>
        <h3 className="text-sm font-semibold text-ink-100 mb-3">All {data.reactions.length} reactions</h3>
        <div className="grid md:grid-cols-2 gap-3">
          {data.reactions.map((r) => <ReactionCard key={r.persona_id} r={r} />)}
        </div>
      </div>

      {/* Methodology / honesty footnote */}
      <div className="text-[11px] text-ink-500 leading-relaxed border-t border-ink-800 pt-4">
        These are <strong className="text-ink-300">predicted</strong> reactions, not measured ones —
        the panel simulates how each persona would rate a product it has never seen, calibrated to a
        held-out rating error of <strong className="text-ink-300">±{data.rmse_band ?? 1.1}★</strong>.
        Read the cohort signal (which groups react warmer/cooler, recurring concerns) as the durable
        output; treat any single number as a directional estimate.
        {data.backbone && (
          <>
            {" "}Model:{" "}
            <span className="text-ink-400">{data.backbone.primary.split(":").pop()}</span>
            {data.backbone.fallback_used > 0 && (
              <> · {data.backbone.fallback_used} persona(s) fell back to {data.backbone.fallback.split(":").pop()}</>
            )}.
          </>
        )}
      </div>
    </div>
  );
}

function PanelApp() {
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [category, setCategory] = useState("");
  const [price, setPrice] = useState("");
  const [language, setLanguage] = useState<"yoruba" | "hausa" | "igbo" | "">("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [data, setData] = useState<PanelResponse | null>(null);

  async function run() {
    if (!title.trim() || loading) return;
    setLoading(true); setErr(null); setData(null);
    try {
      const res = await api.panel({
        product: {
          product_id: "user",
          title: title.trim(),
          description: desc.trim() || undefined,
          category: category.trim() || undefined,
          price_naira: price ? Number(price) : undefined,
          domain: "jumia",
        },
        target_language: language || undefined,
      });
      setData(res);
    } catch (e) { setErr(String(e)); }
    setLoading(false);
  }

  return (
    <div id="panel" className="max-w-6xl mx-auto px-6 py-12">
      <h2 className="text-2xl font-bold text-ink-50 mb-1">Run a panel study</h2>
      <p className="text-ink-400 text-sm mb-6">Describe your product. The 24-persona panel will react in seconds.</p>

      <div className="bg-ink-900/50 border border-ink-700 rounded-2xl p-5 grid md:grid-cols-2 gap-4">
        <div className="md:col-span-2">
          <label className="text-xs text-ink-400">Product title *</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)}
                 placeholder="e.g. Oraimo FreePods 4 Wireless Earbuds"
                 className="w-full mt-1 bg-ink-950 border border-ink-700 rounded-lg px-3 py-2 text-sm text-ink-100 focus:border-naija-600 outline-none" />
        </div>
        <div className="md:col-span-2">
          <label className="text-xs text-ink-400">Description</label>
          <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={2}
                    placeholder="Key features, specs, what it does…"
                    className="w-full mt-1 bg-ink-950 border border-ink-700 rounded-lg px-3 py-2 text-sm text-ink-100 focus:border-naija-600 outline-none resize-none" />
        </div>
        <div>
          <label className="text-xs text-ink-400">Category</label>
          <input value={category} onChange={(e) => setCategory(e.target.value)}
                 placeholder="electronics"
                 className="w-full mt-1 bg-ink-950 border border-ink-700 rounded-lg px-3 py-2 text-sm text-ink-100 focus:border-naija-600 outline-none" />
        </div>
        <div>
          <label className="text-xs text-ink-400">Price (₦)</label>
          <input value={price} onChange={(e) => setPrice(e.target.value.replace(/[^\d]/g, ""))}
                 placeholder="18500" inputMode="numeric"
                 className="w-full mt-1 bg-ink-950 border border-ink-700 rounded-lg px-3 py-2 text-sm text-ink-100 focus:border-naija-600 outline-none" />
        </div>
        <div className="md:col-span-2 flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs text-ink-400">Reviews in:</span>
            {([["", "EN/Pidgin"], ["yoruba", "Yorùbá"], ["hausa", "Hausa"], ["igbo", "Igbo"]] as const).map(([v, l]) => (
              <button key={v} onClick={() => setLanguage(v as typeof language)}
                      className={`text-xs px-2.5 py-1 rounded-md border ${language === v
                        ? "bg-naija-600 text-white border-naija-600"
                        : "bg-ink-800 text-ink-300 border-ink-700 hover:bg-ink-700"}`}>{l}</button>
            ))}
          </div>
          <button onClick={run} disabled={loading || !title.trim()}
                  className="inline-flex items-center gap-2 bg-naija-600 hover:bg-naija-500 disabled:opacity-50 text-white font-semibold rounded-lg px-5 py-2.5 transition-colors">
            {loading ? <><Loader2 size={16} className="animate-spin" /> Panel reacting…</> : <><Play size={16} /> Run panel</>}
          </button>
        </div>
      </div>

      {err && <div className="mt-4 text-sm text-red-300 bg-red-900/20 border border-red-700/40 rounded-lg p-3">{err}</div>}

      {loading && !data && (
        <div className="mt-10 flex flex-col items-center gap-3 text-ink-400">
          <Loader2 size={28} className="animate-spin text-naija-400" />
          <span className="text-sm">24 Nigerian personas are trying your product…</span>
        </div>
      )}

      {data && <div className="mt-8"><Dashboard data={data} /></div>}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
// Page shell
// ─────────────────────────────────────────────────────────────────────────

export default function InsideNaija() {
  const panelRef = useRef<HTMLDivElement>(null);
  const scrollToPanel = () =>
    document.getElementById("panel")?.scrollIntoView({ behavior: "smooth" });

  return (
    <div className="min-h-screen bg-ink-950 text-ink-100">
      <header className="sticky top-0 z-30 border-b border-ink-800 bg-ink-950/80 backdrop-blur-md">
        <div className="max-w-6xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-naija-500 to-naija-800 flex items-center justify-center text-lg">🇳🇬</div>
              <span className="font-bold text-ink-50 tracking-tight">Inside<span className="text-naija-400">Naija</span></span>
            </div>
            {/* product switcher — two separate products */}
            <div className="inline-flex items-center bg-ink-900 border border-ink-700 rounded-lg p-0.5 text-xs">
              <a href="#" className="px-2.5 py-1 rounded-md bg-naija-600 text-white">InsideNaija</a>
              <a href="#shopeasy" className="px-2.5 py-1 rounded-md text-ink-400 hover:text-ink-200 transition-colors">ShopEasy</a>
            </div>
          </div>
          <nav className="flex items-center gap-4 text-sm">
            <button onClick={scrollToPanel} className="text-ink-300 hover:text-white transition-colors">Run a study</button>
            <a href="#b2b" className="text-ink-300 hover:text-white transition-colors">For Business</a>
            <a href="#lab" className="text-ink-400 hover:text-ink-200 transition-colors text-xs">Lab ↗</a>
            <button onClick={scrollToPanel}
                    className="bg-naija-600 hover:bg-naija-500 text-white text-sm font-medium rounded-lg px-4 py-1.5 transition-colors">
              Try free
            </button>
          </nav>
        </div>
      </header>

      <Hero onTryItOwn={scrollToPanel} />
      <ValueStrip />
      <HowItWorks onTry={scrollToPanel} />
      <WhySection />
      <div ref={panelRef}><PanelApp /></div>

      <footer className="border-t border-ink-800 mt-12">
        <div className="max-w-6xl mx-auto px-6 py-8 text-xs text-ink-500 flex items-center justify-between flex-wrap gap-3">
          <span>InsideNaija — synthetic Nigerian customer panel. Powered by NaijaReviewer-8B.</span>
          <span>Predicts reactions; complements human research, doesn't replace it.</span>
        </div>
      </footer>
    </div>
  );
}
