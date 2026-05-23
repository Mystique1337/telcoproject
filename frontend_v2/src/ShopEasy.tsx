// ShopEasy - Task B shopper-facing storefront.
// Language gate -> search (text or image) -> recommendations with thumbnails
// -> order page (mock checkout).

import { useEffect, useRef, useState } from "react";
import {
  ArrowLeft, Baby, Camera, Check, Gamepad2, Headphones, Heart, Heart as HeartOutline,
  History, Home as HomeIcon, ImageIcon, Laptop, Loader2, MessageSquare, Music,
  Package, Search, Shirt, ShoppingBasket, ShoppingCart, Smartphone, Sparkles,
  Send, Star, Users, X,
} from "lucide-react";

import { api } from "./api";
import { LanguageGate, type AppLang } from "./LanguageGate";
import { Onboarding, loadProfile, type ShopProfile } from "./Onboarding";
import ShopLayout from "@/components/ShopLayout";
import { type ShopView } from "@/components/ShopSidebar";

type View = ShopView;

// Alias so the rest of the file works unchanged
const ShopLayoutWrapper = ShopLayout;
import { ArrowRight, LogIn, Mic, Sparkles as SparklesIcon } from "lucide-react";
import type { ConversationTurn, PanelReaction, Persona, ShopProduct } from "./types";
import {
  getShopPersona,
  setupShopPersona,
  placeShopOrder,
  listShopOrders,
  getWishlist,
  addToWishlist,
  removeFromWishlist,
  type ShopPersona,
  type ShopOrder,
  type ShopWishlistItem,
} from "./lib/apiClient";

// Compact switcher presenting the two products as separate, linkable apps.
function ProductSwitcher({ current }: { current: "panel" | "shop" }) {
  return (
    <div className="inline-flex items-center bg-ink-900 border border-ink-700 rounded-lg p-0.5 text-xs">
      <a href="#"
         className={`px-2.5 py-1 rounded-md transition-colors ${current === "panel" ? "bg-ink-700 text-ink-50" : "text-ink-400 hover:text-ink-200"}`}>
        InsideNaija
      </a>
      <a href="#shopeasy"
         className={`px-2.5 py-1 rounded-md transition-colors ${current === "shop" ? "bg-amber-600 text-white" : "text-ink-400 hover:text-ink-200"}`}>
        ShopEasy
      </a>
    </div>
  );
}

function personaName(id: string): string {
  return id.split("_")[0].replace(/\b\w/g, (c) => c.toUpperCase());
}
function personaAvatar(seed: string): string {
  return `https://api.dicebear.com/9.x/personas/svg?seed=${encodeURIComponent(seed)}&backgroundType=gradientLinear`;
}

// ── Localised UI strings ────────────────────────────────────────────────────
const T: Record<AppLang, Record<string, string>> = {
  english: { tagline: "Shop smarter. Search by word or photo.", ph: "What are you looking for?", search: "Search", photo: "Search with a photo", results: "Recommended for you", view: "View", order: "Order now", place: "Place order", placed: "Order placed!", deliver: "Pay on delivery · arrives in 2–3 days", empty: "Search or drop a photo to see recommendations", qty: "Quantity" },
  pidgin: { tagline: "Shop sharp-sharp. Find am with word or photo.", ph: "Wetin you dey find?", search: "Find am", photo: "Use photo find am", results: "Wetin go fit you", view: "Check am", order: "Order am", place: "Place order", placed: "Order don enter!", deliver: "Pay when e land · e go reach in 2–3 days", empty: "Search abeg, or drop photo make we show you wetin dey", qty: "How many" },
  yoruba: { tagline: "Ra ọjà pẹ̀lú ọ̀rọ̀ tàbí àwòrán.", ph: "Kí ni o ń wá?", search: "Wá", photo: "Fi àwòrán wá", results: "Tí a gbà fún ọ", view: "Wò ó", order: "Ṣe ọ̀dẹ̀rẹ̀", place: "Fi ọ̀dẹ̀rẹ̀ sí lẹ̀", placed: "A ti gba ọ̀dẹ̀rẹ̀!", deliver: "San nígbà tí ó dé · ọjọ́ 2–3", empty: "Wá tàbí fi àwòrán sí láti rí àbá", qty: "Iye" },
  hausa: { tagline: "Yi sayayya da kalma ko hoto.", ph: "Me kake nema?", search: "Nema", photo: "Nema da hoto", results: "Shawarwari a gare ka", view: "Duba", order: "Yi oda", place: "Aika oda", placed: "An karɓi oda!", deliver: "Biya idan ya iso · kwana 2–3", empty: "Nema ko saka hoto don ganin shawarwari", qty: "Adadi" },
  igbo: { tagline: "Zụọ ahịa site na okwu ma ọ bụ foto.", ph: "Gịnị ka ị na-achọ?", search: "Chọọ", photo: "Jiri foto chọọ", results: "Atụmatụ maka gị", view: "Lee ya", order: "Tụọ iwu", place: "Zipu iwu", placed: "Anataala iwu!", deliver: "Kwụọ mgbe o rutere · ụbọchị 2–3", empty: "Chọọ ma ọ bụ tinye foto ka ị hụ atụmatụ", qty: "Ọnụọgụ" },
};

// ── Thumbnails ──────────────────────────────────────────────────────────────
function hashNum(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 100000;
  return h;
}
function naira(n?: number | null): string {
  return n ? "₦" + Number(n).toLocaleString() : " - ";
}

const CAT_ICON: { match: string[]; Icon: typeof Package }[] = [
  { match: ["phone", "tablet"], Icon: Smartphone },
  { match: ["comput", "laptop"], Icon: Laptop },
  { match: ["electron", "audio", "headphone", "sound"], Icon: Headphones },
  { match: ["appliance", "home", "office", "kitchen"], Icon: HomeIcon },
  { match: ["fashion", "cloth", "wear", "shoe", "bag"], Icon: Shirt },
  { match: ["beauty", "health", "cosmet", "skin"], Icon: Sparkles },
  { match: ["baby", "kid", "child", "toy"], Icon: Baby },
  { match: ["gaming", "game"], Icon: Gamepad2 },
  { match: ["supermarket", "grocer", "food"], Icon: ShoppingBasket },
  { match: ["music", "instrument"], Icon: Music },
];
const TILE_GRADIENTS = [
  "from-emerald-600/30 to-emerald-900/30",
  "from-sky-600/30 to-sky-900/30",
  "from-violet-600/30 to-violet-900/30",
  "from-amber-600/30 to-amber-900/30",
  "from-rose-600/30 to-rose-900/30",
  "from-cyan-600/30 to-cyan-900/30",
];
function iconFor(p: ShopProduct): typeof Package {
  const hay = `${p.category || ""} ${p.title || ""}`.toLowerCase();
  return (CAT_ICON.find((c) => c.match.some((m) => hay.includes(m)))?.Icon) || Package;
}

const _imgCache = new Map<string, string | null>();

function IconTile({ p, className, iconSize }: { p: ShopProduct; className: string; iconSize: number }) {
  const Icon = iconFor(p);
  const grad = TILE_GRADIENTS[hashNum(p.product_id) % TILE_GRADIENTS.length];
  return (
    <div className={`bg-gradient-to-br ${grad} flex items-center justify-center relative ${className}`}>
      <Icon size={iconSize} className="text-white/70" strokeWidth={1.4} />
    </div>
  );
}

function Thumb({ p, className = "", iconSize = 40 }:
  { p: ShopProduct; className?: string; iconSize?: number }) {
  const [url, setUrl] = useState<string | null | undefined>(() => _imgCache.get(p.product_id));
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (_imgCache.has(p.product_id)) { setUrl(_imgCache.get(p.product_id)); return; }
    let cancelled = false;
    const q = `${p.title || ""} ${(p.category || "").replace(/-/g, " ")}`.trim().slice(0, 100);
    fetch(`/shop/image?q=${encodeURIComponent(q)}`)
      .then((r) => r.json())
      .then((d) => { if (!cancelled) { _imgCache.set(p.product_id, d.url ?? null); setUrl(d.url ?? null); } })
      .catch(() => { if (!cancelled) { _imgCache.set(p.product_id, null); setUrl(null); } });
    return () => { cancelled = true; };
  }, [p.product_id]);

  if (url && !failed) {
    return (
      <img src={url} alt={p.title} loading="lazy" onError={() => setFailed(true)}
           className={`object-cover bg-ink-800 ${className}`} />
    );
  }
  return <IconTile p={p} className={className} iconSize={iconSize} />;
}

function StarsRow({ n }: { n: number }) {
  return (
    <span className="inline-flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star key={i} size={13} className={i <= n ? "fill-amber-400 text-amber-400" : "text-ink-700"} />
      ))}
    </span>
  );
}

function toSpecs(desc?: string): string[] {
  if (!desc) return [];
  return desc.split(/[•·,;\n]|\s-\s/).map((s) => s.trim()).filter((s) => s.length > 2).slice(0, 8);
}

// ── Bar component (for profile page) ────────────────────────────────────────
function Bar({ label, value, leftLabel, rightLabel, color = "bg-amber-500" }:
  { label: string; value: number; leftLabel?: string; rightLabel?: string; color?: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-ink-400">
        <span>{leftLabel || label}</span>
        {rightLabel && <span>{rightLabel}</span>}
      </div>
      <div className="h-2 bg-ink-800 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Product detail page ───────────────────────────────────────────────────────
function OrderPage({ p, t, onClose, hasSession }:
  { p: ShopProduct; t: Record<string, string>; onClose: () => void; hasSession: boolean }) {
  const [qty, setQty] = useState(1);
  const [placed, setPlaced] = useState(false);
  const [tab, setTab] = useState<"specs" | "reviews">("specs");
  const [reviews, setReviews] = useState<PanelReaction[] | null>(null);
  const [avg, setAvg] = useState<number | null>(null);
  const [loadingR, setLoadingR] = useState(true);
  const specs = toSpecs(p.description);

  useEffect(() => {
    let cancelled = false;
    const ids = ["chinwe_owerri", "tunde_lagos", "aisha_kano", "blessing_warri", "kelechi_lagos"];
    api.panel({
      product: { product_id: p.product_id, title: p.title, category: p.category || undefined,
                 price_naira: p.price_naira ?? undefined, description: p.description, domain: "jumia" },
      persona_ids: ids,
      backbone_override: "anthropic:claude-sonnet-4-20250514",
    }).then((r) => {
      if (cancelled) return;
      setReviews(r.reactions); setAvg(r.aggregate?.avg_rating ?? null); setLoadingR(false);
    }).catch(() => { if (!cancelled) setLoadingR(false); });
    return () => { cancelled = true; };
  }, [p.product_id]);

  async function handlePlaceOrder() {
    setPlaced(true);
    if (hasSession) {
      try {
        await placeShopOrder({
          items: [{
            product_id: p.product_id,
            product_title: p.title,
            quantity: qty,
            unit_price_naira: p.price_naira || 0,
          }],
          total_naira: (p.price_naira || 0) * qty,
        });
      } catch {
        // order save is best-effort; don't block the UX
      }
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center p-4 overflow-y-auto" onClick={onClose}>
      <div className="bg-ink-900 border border-ink-700 rounded-2xl max-w-3xl w-full overflow-hidden shadow-2xl my-8"
           onClick={(e) => e.stopPropagation()}>
        {placed ? (
          <div className="flex flex-col items-center justify-center text-center py-16 px-6">
            <div className="w-14 h-14 rounded-full bg-amber-600/20 border border-amber-500 flex items-center justify-center mb-4">
              <Check size={28} className="text-amber-300" />
            </div>
            <div className="text-lg font-bold text-ink-50">{t.placed}</div>
            <div className="text-sm text-ink-300 mt-1">{qty}× {p.title}</div>
            <div className="text-xs text-ink-400 mt-3">{t.deliver}</div>
            <button onClick={onClose} className="mt-6 text-sm text-amber-300 hover:text-amber-200">Done</button>
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-2">
              <Thumb p={p} className="w-full h-72 md:h-full min-h-[18rem]" iconSize={64} />
              <div className="p-6 relative">
                <button onClick={onClose} className="absolute top-4 right-4 text-ink-400 hover:text-ink-50"><X size={18} /></button>
                <div className="text-[10px] uppercase tracking-wide text-ink-400">{(p.category || "").replace(/-/g, " ")}</div>
                <h2 className="text-lg font-bold text-ink-50 mt-1 leading-snug">{p.title}</h2>
                <div className="flex items-center gap-2 mt-2">
                  {avg != null ? <><StarsRow n={Math.round(avg)} /><span className="text-xs text-ink-400">{avg.toFixed(1)} · {reviews?.length ?? 0} reviews</span></>
                    : <span className="text-xs text-ink-500">Loading reviews…</span>}
                </div>
                <div className="text-[11px] text-ink-400 mt-1.5 flex items-center gap-1.5">
                  <Check size={11} className="text-amber-400" /> Sold by <span className="text-ink-200">{p.seller || "Verified ShopEasy Seller"}</span>
                </div>
                <div className="text-2xl font-bold text-amber-300 mt-3">{naira(p.price_naira)}</div>
                {p.rationale && (
                  <div className="text-xs text-amber-300/90 mt-2 bg-amber-900/20 border border-amber-700/30 rounded-md px-2 py-1">
                    ✓ {p.rationale}
                  </div>
                )}
                <div className="flex items-center gap-3 mt-5">
                  <span className="text-xs text-ink-400">{t.qty}</span>
                  <div className="flex items-center border border-ink-700 rounded-lg">
                    <button onClick={() => setQty(Math.max(1, qty - 1))} className="px-3 py-1 text-ink-300 hover:text-ink-50">−</button>
                    <span className="px-3 text-ink-100 tabular-nums">{qty}</span>
                    <button onClick={() => setQty(qty + 1)} className="px-3 py-1 text-ink-300 hover:text-ink-50">+</button>
                  </div>
                </div>
                <button onClick={handlePlaceOrder}
                        className="w-full mt-5 inline-flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-lg py-3 transition-colors">
                  <ShoppingCart size={17} /> {t.place} · {naira((p.price_naira || 0) * qty)}
                </button>
              </div>
            </div>

            <div className="border-t border-ink-800 px-6 pt-4 pb-6">
              <div className="flex gap-4 border-b border-ink-800 mb-4">
                <button onClick={() => setTab("specs")}
                        className={`pb-2 text-sm font-medium ${tab === "specs" ? "text-amber-300 border-b-2 border-amber-500" : "text-ink-400 hover:text-ink-200"}`}>Specifications</button>
                <button onClick={() => setTab("reviews")}
                        className={`pb-2 text-sm font-medium ${tab === "reviews" ? "text-amber-300 border-b-2 border-amber-500" : "text-ink-400 hover:text-ink-200"}`}>
                  Reviews {reviews ? `(${reviews.length})` : ""}
                </button>
              </div>

              {tab === "specs" && (
                specs.length ? (
                  <ul className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5">
                    {specs.map((s, i) => (
                      <li key={i} className="text-sm text-ink-300 flex items-start gap-2">
                        <Check size={13} className="text-amber-400 mt-0.5 flex-shrink-0" /> {s}
                      </li>
                    ))}
                  </ul>
                ) : <p className="text-sm text-ink-400">{p.description || "No specifications listed."}</p>
              )}

              {tab === "reviews" && (
                loadingR ? (
                  <div className="flex items-center gap-2 text-sm text-ink-400 py-4"><Loader2 size={15} className="animate-spin" /> Gathering Nigerian shopper reviews…</div>
                ) : reviews && reviews.length ? (
                  <div className="space-y-3">
                    <div className="text-[11px] text-ink-500 mb-1">Simulated by a panel of Nigerian personas (InsideNaija engine).</div>
                    {reviews.map((r) => (
                      <div key={r.persona_id} className="bg-ink-800/40 rounded-lg p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-ink-100">{personaName(r.persona_id)} <span className="text-[10px] text-ink-400 font-normal">· {r.zone}</span></span>
                          <StarsRow n={r.rating} />
                        </div>
                        <p className="text-sm text-ink-300 mt-1.5 leading-relaxed">"{r.review}"</p>
                      </div>
                    ))}
                  </div>
                ) : <p className="text-sm text-ink-400">Reviews unavailable right now.</p>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Product card ──────────────────────────────────────────────────────────
function Card({ p, t, onOpen, wishlisted, onToggleWishlist }:
  { p: ShopProduct; t: Record<string, string>; onOpen: () => void; wishlisted: boolean; onToggleWishlist: () => void }) {
  return (
    <div className="group text-left bg-ink-900/50 border border-ink-800 hover:border-amber-600/60 rounded-xl overflow-hidden transition-all hover:-translate-y-0.5 relative">
      {/* Wishlist heart button */}
      <button
        onClick={(e) => { e.stopPropagation(); onToggleWishlist(); }}
        className="absolute top-2 right-2 z-10 w-7 h-7 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center transition-colors hover:bg-black/70"
        title={wishlisted ? "Remove from wishlist" : "Add to wishlist"}
      >
        <Heart
          size={14}
          className={wishlisted ? "fill-amber-400 text-amber-400" : "text-white/70"}
        />
      </button>
      <button onClick={onOpen} className="w-full text-left">
        <div className="relative aspect-square overflow-hidden">
          <Thumb p={p} className="w-full h-full group-hover:scale-105 transition-transform duration-300" />
          {p.category && (
            <span className="absolute top-2 left-2 text-[10px] bg-black/60 text-ink-100 rounded px-1.5 py-0.5 capitalize">
              {p.category.replace(/-/g, " ")}
            </span>
          )}
        </div>
        <div className="p-3">
          <div className="text-sm text-ink-100 leading-snug line-clamp-2 min-h-[2.5rem]">{p.title}</div>
          {p.rationale && (
            <div className="text-xs text-amber-300/90 leading-snug mt-1.5 line-clamp-2 bg-amber-900/20 border border-amber-700/30 rounded-md px-2 py-1">
              ✓ {p.rationale}
            </div>
          )}
          <div className="flex items-center justify-between mt-2">
            <span className="text-base font-bold text-amber-300">{naira(p.price_naira)}</span>
            <span className="text-xs text-amber-400 group-hover:text-amber-300 inline-flex items-center gap-1">{t.order} →</span>
          </div>
        </div>
      </button>
    </div>
  );
}

// ── Conversational assistant ────────────────────────────────────────────────
const CT: Record<AppLang, { greet: string; ph: string; tab: string; stab: string }> = {
  english: { greet: "Hi! What are you shopping for today? Tell me what you need, who it's for, and your budget.", ph: "Type what you need…", tab: "Assistant", stab: "Search" },
  pidgin: { greet: "How far! Wetin you wan buy today? Tell me wetin you need, for who, and your budget.", ph: "Tell me wetin you need…", tab: "Assistant", stab: "Find am" },
  yoruba: { greet: "Báwo! Kí ni o fẹ́ rà lónìí? Sọ ohun tí o nílò, fún ta, àti ìnáwó rẹ.", ph: "Sọ ohun tí o nílò…", tab: "Olùrànlọ́wọ́", stab: "Wá" },
  hausa: { greet: "Sannu! Me kake son saya yau? Faɗa min abin da kake bukata, da kuɗin da kake da shi.", ph: "Faɗa min abin da kake bukata…", tab: "Mataimaki", stab: "Nema" },
  igbo: { greet: "Ndewo! Gịnị ka ị chọrọ ịzụ taa? Kwuo ihe ị chọrọ, onye ọ bụ maka ya, na ego i nwere.", ph: "Kwuo ihe ị chọrọ…", tab: "Onye enyemaka", stab: "Chọọ" },
};

interface ChatMsg { id: string; role: "user" | "assistant"; content: string; recs?: ShopProduct[]; }

function ChatPanel({ lang, persona, onOpen }:
  { lang: AppLang; persona?: Persona | null; onOpen: (p: ShopProduct) => void }) {
  const ct = CT[lang] ?? CT.english;
  const chatLang = (lang === "yoruba" || lang === "hausa" || lang === "igbo") ? lang : undefined;
  const [msgs, setMsgs] = useState<ChatMsg[]>([{ id: "w", role: "assistant", content: ct.greet }]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [msgs, sending]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    const um: ChatMsg = { id: "u" + Date.now(), role: "user", content: text };
    setMsgs((m) => [...m, um]);
    setInput(""); setSending(true);
    try {
      const history: ConversationTurn[] = [...msgs, um]
        .filter((m) => m.id !== "w")
        .map((m) => ({ role: m.role, content: m.content }));
      const r = await api.chat({
        history,
        persona: persona ?? null,
        language: chatLang ?? null,
        k: 6,
        reranker_override: "anthropic:claude-sonnet-4-20250514",
        orchestrator_override: "anthropic:claude-sonnet-4-20250514",
      });
      const recs: ShopProduct[] = (r.recommendations || []).map((x) => ({
        product_id: x.product_id, title: x.title || x.product_id,
        category: x.category, price_naira: x.price_naira,
      }));
      setMsgs((m) => [...m, { id: "a" + Date.now(), role: "assistant", content: r.message, recs }]);
    } catch (e) {
      setMsgs((m) => [...m, { id: "e" + Date.now(), role: "assistant", content: "⚠ " + String(e) }]);
    }
    setSending(false);
  }

  async function sendImage(file: File) {
    if (sending) return;
    const note = input.trim();
    setInput("");
    setSending(true);
    setMsgs((m) => [...m, { id: "u" + Date.now(), role: "user", content: note ? `📷 Photo + "${note}"` : "📷 Sent a photo" }]);
    try {
      const b64 = await new Promise<string>((res, rej) => {
        const fr = new FileReader();
        fr.onload = () => res(String(fr.result).split(",")[1]);
        fr.onerror = rej;
        fr.readAsDataURL(file);
      });
      const r = await api.shopVisualSearch(b64, file.type || "image/jpeg", 6, persona?.user_id ?? null, null, note || null);
      const recs: ShopProduct[] = (r.products || []).map((x) => ({
        product_id: x.product_id, title: x.title || x.product_id,
        category: x.category, price_naira: x.price_naira, rationale: x.rationale,
      }));
      const msg = r.detected
        ? `Looks like you're after "${r.detected}". Here's what I found${persona ? " for " + persona.user_id.split("_")[0] : ""}:`
        : "Here's what I found from your photo:";
      setMsgs((m) => [...m, { id: "a" + Date.now(), role: "assistant", content: msg, recs }]);
    } catch (e) {
      setMsgs((m) => [...m, { id: "e" + Date.now(), role: "assistant", content: "⚠ Couldn't read that photo: " + String(e) }]);
    }
    setSending(false);
  }

  return (
    <div className="max-w-3xl mx-auto px-6 pb-16">
      <div className="bg-ink-900/40 border border-ink-800 rounded-2xl overflow-hidden">
        <div ref={scrollRef} className="h-[55vh] overflow-y-auto p-4 space-y-4">
          {msgs.map((m) => (
            <div key={m.id} className={m.role === "user" ? "flex justify-end" : ""}>
              <div className={m.role === "user"
                ? "bg-amber-600 text-white rounded-2xl rounded-br-sm px-4 py-2 max-w-[80%] text-sm"
                : "bg-ink-800 text-ink-100 rounded-2xl rounded-bl-sm px-4 py-2 max-w-[85%] text-sm"}>
                {m.content}
              </div>
              {m.role === "assistant" && m.recs && m.recs.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 mt-3">
                  {m.recs.map((p) => (
                    <button key={p.product_id} onClick={() => onOpen(p)}
                            className="group text-left bg-ink-900/60 border border-ink-800 hover:border-amber-600/60 rounded-lg overflow-hidden transition-all">
                      <Thumb p={p} className="w-full aspect-square" iconSize={28} />
                      <div className="p-2">
                        <div className="text-[11px] text-ink-200 line-clamp-2 leading-snug min-h-[2rem]">{p.title}</div>
                        <div className="text-sm font-bold text-amber-300 mt-0.5">{naira(p.price_naira)}</div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          {sending && (
            <div className="flex items-center gap-2 text-ink-400 text-sm">
              <Loader2 size={14} className="animate-spin" /> …
            </div>
          )}
        </div>
        <div className="border-t border-ink-800 p-3 flex items-center gap-2">
          <label className="cursor-pointer text-ink-400 hover:text-amber-300 p-2" title="Send a photo">
            <Camera size={18} />
            <input type="file" accept="image/*" className="hidden" disabled={sending}
                   onChange={(e) => e.target.files?.[0] && sendImage(e.target.files[0])} />
          </label>
          <input value={input} onChange={(e) => setInput(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && send()}
                 placeholder={ct.ph} disabled={sending}
                 className="flex-1 bg-ink-950 border border-ink-700 focus:border-amber-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" />
          <button onClick={send} disabled={sending || !input.trim()}
                  className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white rounded-lg p-2.5 transition-colors">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Voice input ──────────────────────────────────────────────────────────────
function useVoice(onResult: (text: string) => void) {
  const [listening, setListening] = useState(false);
  const recRef = useRef<any>(null);
  const supported = typeof window !== "undefined" &&
    ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition);
  function toggle() {
    if (!supported) return;
    if (listening) { recRef.current?.stop(); return; }
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = "en-NG"; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onresult = (e: any) => { onResult(e.results[0][0].transcript); };
    rec.onend = () => setListening(false);
    rec.onerror = () => setListening(false);
    recRef.current = rec; setListening(true); rec.start();
  }
  return { listening, toggle, supported };
}

// ── Order History ─────────────────────────────────────────────────────────────
function OrderHistory({ onBack }: { onBack: () => void }) {
  const [orders, setOrders] = useState<ShopOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    listShopOrders()
      .then(setOrders)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-ink-950 text-ink-100">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 size={24} className="animate-spin text-amber-400" />
          </div>
        ) : orders.length === 0 ? (
          <div className="flex flex-col items-center py-20 text-ink-500">
            <ShoppingCart size={40} className="mb-4 text-ink-700" />
            <p className="text-sm">No orders yet. Start shopping!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {orders.map((order) => (
              <div key={order.id} className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
                <button
                  onClick={() => setExpanded(expanded === order.id ? null : order.id)}
                  className="w-full px-4 py-3 flex items-center justify-between text-left"
                >
                  <div>
                    <div className="text-sm font-medium text-ink-100">
                      {new Date(order.created_at).toLocaleDateString("en-NG", { day: "numeric", month: "short", year: "numeric" })}
                    </div>
                    <div className="text-xs text-ink-400 mt-0.5">
                      {order.items.length} item{order.items.length !== 1 ? "s" : ""} · {naira(order.total_naira)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-900/40 border border-amber-700/50 text-amber-300 capitalize">
                      {order.status}
                    </span>
                    <span className="text-ink-500 text-xs">{expanded === order.id ? "▲" : "▼"}</span>
                  </div>
                </button>
                {expanded === order.id && (
                  <div className="border-t border-ink-800 px-4 pb-4 pt-3 space-y-2">
                    {order.items.map((item, i) => (
                      <div key={i} className="flex items-center justify-between text-sm">
                        <span className="text-ink-200 line-clamp-1">{item.product_title}</span>
                        <span className="text-ink-400 text-xs ml-2 whitespace-nowrap">×{item.quantity} · {naira(item.unit_price_naira)}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Wishlist Page ─────────────────────────────────────────────────────────────
function WishlistPage({ onBack, onSignIn, onWishlistChange }: { onBack: () => void; onSignIn: () => void; onWishlistChange?: (n: number) => void }) {
  const hasSession = !!localStorage.getItem("shop_profile_id");
  const [items, setItems] = useState<ShopWishlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hasSession) { setLoading(false); return; }
    getWishlist()
      .then((data) => { setItems(data); onWishlistChange?.(data.length); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function remove(productId: string) {
    const next = items.filter((i) => i.product_id !== productId);
    setItems(next);
    onWishlistChange?.(next.length);
    try { await removeFromWishlist(productId); } catch { /* best-effort */ }
  }

  return (
    <div className="bg-ink-950 text-ink-100">
      <div className="max-w-3xl mx-auto px-6 py-8">
        {!hasSession ? (
          <div className="flex flex-col items-center py-20 text-ink-500">
            <Heart size={40} className="mb-4 text-ink-700" />
            <p className="text-sm mb-4">Sign in to save products to your wishlist.</p>
            <button onClick={onSignIn} className="bg-amber-600 hover:bg-amber-500 text-white px-5 py-2 rounded-lg text-sm font-medium">
              Sign in
            </button>
          </div>
        ) : loading ? (
          <div className="flex justify-center py-16">
            <Loader2 size={24} className="animate-spin text-amber-400" />
          </div>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center py-20 text-ink-500">
            <Heart size={40} className="mb-4 text-ink-700" />
            <p className="text-sm">Your wishlist is empty. Heart a product to save it!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div key={item.id} className="bg-ink-900 border border-ink-800 rounded-xl px-4 py-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm text-ink-100 line-clamp-1 font-medium">{item.product_title}</div>
                  <div className="flex items-center gap-2 mt-0.5">
                    {item.product_category && (
                      <span className="text-[10px] text-ink-500 capitalize">{item.product_category.replace(/-/g, " ")}</span>
                    )}
                    {item.product_price && (
                      <span className="text-xs font-bold text-amber-300">{naira(item.product_price)}</span>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => remove(item.product_id)}
                  className="flex-shrink-0 text-ink-500 hover:text-red-400 transition-colors p-1"
                  title="Remove"
                >
                  <X size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Profile Page ─────────────────────────────────────────────────────────────
function ProfilePage({ profile, persona, onBack, onSignOut }:
  { profile: ShopProfile | null; persona: ShopPersona | null; onBack: () => void; onSignOut: () => void }) {
  const [editLang, setEditLang] = useState(persona?.language || "english");
  const [editLoc, setEditLoc] = useState(persona?.location || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const aspectEntries = Object.entries(persona?.aspect_priority || {})
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5);

  async function handleSave() {
    if (!profile) return;
    setSaving(true);
    try {
      await setupShopPersona({
        display_name: profile.name,
        language: editLang,
        location: editLoc,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch { /* best-effort */ }
    setSaving(false);
  }

  return (
    <div className="bg-ink-950 text-ink-100">
      <div className="max-w-2xl mx-auto px-6 py-8 space-y-6">
        {/* Avatar + basics */}
        {profile && (
          <div className="bg-ink-900 border border-ink-800 rounded-2xl p-5 flex items-center gap-4">
            <img src={personaAvatar(profile.id)} alt="" className="w-16 h-16 rounded-full border-2 border-amber-600/50" />
            <div>
              <div className="text-lg font-bold text-ink-50">{profile.name}</div>
              {persona && (
                <>
                  <div className="text-sm text-ink-300 mt-0.5">{persona.location} · {persona.language}</div>
                  <div className="text-xs text-ink-500 mt-0.5 capitalize">{persona.register_tier?.replace(/_/g, " ")}</div>
                </>
              )}
            </div>
          </div>
        )}

        {/* Cognitive dimensions */}
        {persona && (
          <div className="bg-ink-900 border border-ink-800 rounded-2xl p-5 space-y-4">
            <div className="text-sm font-semibold text-ink-200 mb-3">Shopping style</div>
            <Bar
              label="Hedonic / Utilitarian"
              leftLabel="Hedonic (emotional)"
              rightLabel="Utilitarian (practical)"
              value={persona.hedonic_utilitarian}
              color="bg-amber-500"
            />
            <Bar
              label="Individual / Communal"
              leftLabel="Individual"
              rightLabel="Communal"
              value={1 - persona.communal_individual}
              color="bg-sky-500"
            />
          </div>
        )}

        {/* Aspect priorities */}
        {aspectEntries.length > 0 && (
          <div className="bg-ink-900 border border-ink-800 rounded-2xl p-5 space-y-3">
            <div className="text-sm font-semibold text-ink-200 mb-3">What you care about</div>
            {aspectEntries.map(([key, val]) => (
              <Bar
                key={key}
                label={key.replace(/_/g, " ")}
                leftLabel={key.replace(/_/g, " ")}
                value={val as number}
                color="bg-emerald-500"
              />
            ))}
          </div>
        )}

        {/* Edit section */}
        <div className="bg-ink-900 border border-ink-800 rounded-2xl p-5 space-y-4">
          <div className="text-sm font-semibold text-ink-200">Edit preferences</div>
          <div>
            <label className="text-xs text-ink-400 block mb-1">Language</label>
            <select
              value={editLang}
              onChange={(e) => setEditLang(e.target.value)}
              className="w-full bg-ink-950 border border-ink-700 focus:border-amber-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none"
            >
              {["english", "pidgin", "yoruba", "hausa", "igbo"].map((l) => (
                <option key={l} value={l} className="capitalize">{l.charAt(0).toUpperCase() + l.slice(1)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-ink-400 block mb-1">Location</label>
            <input
              value={editLoc}
              onChange={(e) => setEditLoc(e.target.value)}
              placeholder="e.g. Lagos, Kano, Enugu…"
              className="w-full bg-ink-950 border border-ink-700 focus:border-amber-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none"
            />
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="w-full bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-semibold rounded-lg py-2.5 text-sm transition-colors inline-flex items-center justify-center gap-2"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : saved ? <Check size={14} /> : null}
            {saved ? "Saved!" : "Save changes"}
          </button>
        </div>

        {/* Sign out */}
        <button
          onClick={onSignOut}
          className="w-full bg-ink-900 border border-ink-800 hover:border-red-700/50 text-ink-400 hover:text-red-400 font-medium rounded-xl py-3 text-sm transition-colors"
        >
          Sign out
        </button>
      </div>
    </div>
  );
}

// ── Store ─────────────────────────────────────────────────────────────────────
function Store({ lang, profile, shopPersona, onHome, onSignIn, onProfile, onOrders, onWishlist, initialCategory, onWishlistCountChange }:
  {
    lang: AppLang; profile: ShopProfile | null; shopPersona: ShopPersona | null;
    onHome: () => void; onSignIn: () => void; onProfile: () => void;
    onOrders: () => void; onWishlist: () => void; initialCategory?: string;
    onWishlistCountChange?: (n: number) => void;
  }) {
  const t = T[lang] ?? T.english;
  const ct = CT[lang] ?? CT.english;
  const [mode, setMode] = useState<"search" | "chat">("search");
  const [query, setQuery] = useState(initialCategory || "");
  const [loading, setLoading] = useState(false);
  const [detected, setDetected] = useState<string | null>(null);
  const [products, setProducts] = useState<ShopProduct[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<ShopProduct | null>(null);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [personaId, setPersonaId] = useState<string | null>(null);
  const [wishlistIds, setWishlistIds] = useState<Set<string>>(new Set());
  const profileId = profile?.id ?? null;
  const hasSession = !!localStorage.getItem("shop_profile_id");

  useEffect(() => {
    api.personas().then((r) => setPersonas(r.personas)).catch(() => {});
  }, []);

  // Load wishlist if signed in
  useEffect(() => {
    if (!hasSession) return;
    getWishlist()
      .then((items) => setWishlistIds(new Set(items.map((i) => i.product_id))))
      .catch(() => {});
  }, [hasSession]);

  // Auto-search if initial category was provided
  useEffect(() => {
    if (initialCategory) {
      runText(initialCategory);
    }
  }, []);

  const persona = profile?.persona ?? (personas.find((p) => p.user_id === personaId) || null);
  const voice = useVoice((text) => { setQuery(text); setTimeout(() => runText(text), 50); });

  async function runText(q?: string) {
    const term = (q ?? query).trim();
    if (!term || loading) return;
    setLoading(true); setErr(null); setDetected(null);
    try {
      const r = await api.shopSearch(term, 12, personaId, profileId);
      setProducts(r.products);
    } catch (e) { setErr(String(e)); }
    setLoading(false);
  }

  async function runImage(file: File) {
    if (loading) return;
    setLoading(true); setErr(null); setDetected(null);
    try {
      const b64 = await new Promise<string>((res, rej) => {
        const fr = new FileReader();
        fr.onload = () => res(String(fr.result).split(",")[1]);
        fr.onerror = rej;
        fr.readAsDataURL(file);
      });
      const r = await api.shopVisualSearch(b64, file.type || "image/jpeg", 12, personaId, profileId);
      setDetected(r.detected || null);
      setQuery(r.detected || "");
      setProducts(r.products);
    } catch (e) { setErr(String(e)); }
    setLoading(false);
  }

  async function toggleWishlist(p: ShopProduct) {
    if (!hasSession) { onSignIn(); return; }
    const wasWishlisted = wishlistIds.has(p.product_id);
    setWishlistIds((prev) => {
      const next = new Set(prev);
      if (wasWishlisted) next.delete(p.product_id);
      else next.add(p.product_id);
      onWishlistCountChange?.(next.size);
      return next;
    });
    try {
      if (wasWishlisted) {
        await removeFromWishlist(p.product_id);
      } else {
        await addToWishlist({
          product_id: p.product_id,
          product_title: p.title,
          product_price: p.price_naira,
          product_category: p.category,
        });
      }
    } catch {
      // Revert on failure
      setWishlistIds((prev) => {
        const next = new Set(prev);
        if (wasWishlisted) next.add(p.product_id);
        else next.delete(p.product_id);
        return next;
      });
    }
  }

  const wishlistCount = wishlistIds.size;

  return (
    <div className="min-h-screen bg-ink-950 text-ink-100">

      {/* Persona pill (Feature 1a) */}
      {shopPersona && (
        <div className="max-w-6xl mx-auto px-6 pt-3 flex justify-end">
          <span className="inline-flex items-center gap-1.5 bg-amber-900/30 border border-amber-700/40 rounded-full px-3 py-1 text-xs text-amber-300">
            <SparklesIcon size={11} className="text-amber-400" />
            Shopping as: {shopPersona.location} · {shopPersona.language.charAt(0).toUpperCase() + shopPersona.language.slice(1)}
          </span>
        </div>
      )}

      {/* Mode toggle */}
      <div className="max-w-3xl mx-auto px-6 pt-6 flex justify-center">
        <div className="inline-flex bg-ink-900 border border-ink-700 rounded-lg p-1">
          <button onClick={() => setMode("search")}
                  className={`text-sm font-medium rounded-md px-4 py-1.5 inline-flex items-center gap-1.5 transition-colors ${mode === "search" ? "bg-amber-600 text-white" : "text-ink-300 hover:text-ink-50"}`}>
            <Search size={14} /> {ct.stab}
          </button>
          <button onClick={() => setMode("chat")}
                  className={`text-sm font-medium rounded-md px-4 py-1.5 inline-flex items-center gap-1.5 transition-colors ${mode === "chat" ? "bg-amber-600 text-white" : "text-ink-300 hover:text-ink-50"}`}>
            <MessageSquare size={14} /> {ct.tab}
          </button>
        </div>
      </div>

      {/* Personalization context */}
      <div className="max-w-4xl mx-auto px-6 pt-5">
        {profile ? (
          <div className="text-center text-xs text-ink-300">
            <span className="inline-flex items-center gap-1.5 bg-amber-900/30 border border-amber-700/40 rounded-full px-3 py-1">
              <SparklesIcon size={12} className="text-amber-300" />
              Personalised for <span className="text-amber-300 font-medium">{profile.name}</span>
              {profile.persona.demographics?.location ? ` · ${profile.persona.demographics.location}` : ""}
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-2 flex-wrap justify-center">
            <span className="text-xs text-ink-400 inline-flex items-center gap-1 mr-1"><Users size={12} /> Preview as:</span>
            <button onClick={() => setPersonaId(null)}
                    className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${!personaId ? "bg-amber-600 text-white border-amber-600" : "bg-ink-900 text-ink-300 border-ink-700 hover:border-ink-600"}`}>
              Anyone
            </button>
            {personas.slice(0, 6).map((p) => (
              <button key={p.user_id} onClick={() => setPersonaId(p.user_id)}
                      title={`${p.demographics?.location || ""} · ${p.demographics?.occupation || ""}`}
                      className={`text-xs px-2.5 py-1 rounded-full border inline-flex items-center gap-1.5 transition-colors ${personaId === p.user_id ? "bg-amber-600 text-white border-amber-600" : "bg-ink-900 text-ink-300 border-ink-700 hover:border-ink-600"}`}>
                <span className="w-4 h-4 rounded-full bg-ink-700 overflow-hidden flex items-center justify-center">
                  <img src={personaAvatar(p.user_id)} alt="" className="w-full h-full object-cover"
                       onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }} />
                </span>
                {personaName(p.user_id)}
              </button>
            ))}
            <button onClick={onSignIn} className="text-xs text-amber-300 hover:text-amber-200 ml-1">
              + Personalise for me
            </button>
          </div>
        )}
      </div>

      {mode === "chat" && <div className="pt-6"><ChatPanel lang={lang} persona={persona} onOpen={(p) => setOpen(p)} /></div>}

      {/* Search hero */}
      {mode === "search" && (
      <section className="max-w-3xl mx-auto px-6 pt-8 pb-6 text-center">
        <div className="inline-flex items-center gap-2 text-xs font-medium text-amber-300 bg-amber-900/40 border border-amber-700/40 rounded-full px-3 py-1 mb-4">
          <Sparkles size={13} /> AI-powered Nigerian shopping
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-ink-50 tracking-tight">{t.tagline}</h1>
        <div className="mt-7 flex items-center gap-2 bg-ink-900 border border-ink-700 focus-within:border-amber-600 rounded-xl p-1.5 transition-colors">
          <Search size={18} className="text-ink-400 ml-2" />
          <input value={query} onChange={(e) => setQuery(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && runText()}
                 placeholder={t.ph}
                 className="flex-1 bg-transparent text-ink-100 text-sm outline-none px-1" />
          {voice.supported && (
            <button onClick={voice.toggle} title="Speak your search"
                    className={`px-2 py-2 transition-colors ${voice.listening ? "text-red-400 animate-pulse" : "text-ink-400 hover:text-amber-300"}`}>
              <Mic size={18} />
            </button>
          )}
          <label className="cursor-pointer text-ink-400 hover:text-amber-300 px-2 py-2" title={t.photo}>
            <Camera size={18} />
            <input type="file" accept="image/*" className="hidden"
                   onChange={(e) => e.target.files?.[0] && runImage(e.target.files[0])} />
          </label>
          <button onClick={() => runText()} disabled={loading}
                  className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-sm font-semibold rounded-lg px-5 py-2 transition-colors">
            {loading ? <Loader2 size={16} className="animate-spin" /> : t.search}
          </button>
        </div>
        <div className="mt-2 text-xs text-ink-500 flex items-center justify-center gap-3">
          <span className="inline-flex items-center gap-1.5"><ImageIcon size={12} /> photo</span>
          {voice.supported && <span className="inline-flex items-center gap-1.5"><Mic size={12} /> {voice.listening ? "listening…" : "voice"}</span>}
        </div>
        {detected && (
          <div className="mt-3 text-xs text-ink-300">
            <span className="text-ink-500">AI saw:</span> "{detected}"
          </div>
        )}
        {/* Feature 1c: empty state with location/language hint */}
        {!loading && products.length === 0 && !err && shopPersona && (
          <div className="mt-4 text-xs text-ink-400">
            Your recommendations are tuned to <span className="text-amber-300">{shopPersona.location}</span> · <span className="text-amber-300">{shopPersona.language}</span>
          </div>
        )}
      </section>
      )}

      {/* Results */}
      {mode === "search" && (
      <section className="max-w-6xl mx-auto px-6 pb-16">
        {err && <div className="text-sm text-red-300 bg-red-900/20 border border-red-700/40 rounded-lg p-3 mb-4">{err}</div>}
        {loading && (
          <div className="flex flex-col items-center gap-3 py-16 text-ink-400">
            <Loader2 size={26} className="animate-spin text-amber-400" />
            <span className="text-sm">Finding the best products for you…</span>
          </div>
        )}
        {!loading && products.length === 0 && !err && !shopPersona && (
          <div className="text-center py-16 text-ink-500 text-sm">{t.empty}</div>
        )}
        {!loading && products.length > 0 && (
          <>
            <h2 className="text-sm font-semibold text-ink-200 mb-4">{t.results} · {products.length}</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {products.map((p) => (
                <Card
                  key={p.product_id}
                  p={p}
                  t={t}
                  onOpen={() => setOpen(p)}
                  wishlisted={wishlistIds.has(p.product_id)}
                  onToggleWishlist={() => toggleWishlist(p)}
                />
              ))}
            </div>
          </>
        )}
      </section>
      )}

      {open && (
        <OrderPage
          p={open}
          t={t}
          onClose={() => setOpen(null)}
          hasSession={hasSession}
        />
      )}
    </div>
  );
}

// ── Home landing ─────────────────────────────────────────────────────────────
const HOME_CATEGORIES = [
  { label: "All", Icon: ShoppingCart, color: "text-amber-400", query: "trending" },
  { label: "Phones", Icon: Smartphone, color: "text-sky-400", query: "phones" },
  { label: "Fashion", Icon: Shirt, color: "text-pink-400", query: "fashion clothing" },
  { label: "Beauty", Icon: Sparkles, color: "text-purple-400", query: "beauty cosmetics" },
  { label: "Electronics", Icon: Headphones, color: "text-blue-400", query: "electronics" },
  { label: "Food", Icon: ShoppingBasket, color: "text-lime-400", query: "food groceries" },
  { label: "Home", Icon: HomeIcon, color: "text-orange-400", query: "home appliances" },
  { label: "Gaming", Icon: Gamepad2, color: "text-violet-400", query: "gaming" },
];

const FEATURED = [
  { label: "Latest Smartphones", gradient: "from-sky-600/30 to-sky-900/30", Icon: Smartphone },
  { label: "Fashion Drops", gradient: "from-rose-600/30 to-rose-900/30", Icon: Shirt },
  { label: "Best in Gaming", gradient: "from-violet-600/30 to-violet-900/30", Icon: Gamepad2 },
];

function Home({ profile, onStart, onSignIn }:
  { profile: ShopProfile | null; onStart: (category?: string) => void; onSignIn: () => void }) {
  return (
    <div className="min-h-screen bg-ink-950 text-ink-100">

      <div className="max-w-4xl mx-auto px-6">
        {/* Hero */}
        <div className="pt-14 pb-10 text-center">
          {profile ? (
            <>
              <div className="text-amber-300 text-sm font-medium mb-2">Welcome back, {profile.name}!</div>
              <h1 className="text-4xl font-extrabold text-ink-50 tracking-tight">Ready to shop today?</h1>
            </>
          ) : (
            <>
              <h1 className="text-4xl font-extrabold text-ink-50 tracking-tight leading-tight">
                Shop smarter,<br />
                <span className="text-amber-400">the Naija way.</span>
              </h1>
              <p className="text-ink-400 mt-3 text-sm">AI recommendations tuned for Nigerian shoppers.</p>
            </>
          )}
          <div className="mt-8 flex items-center justify-center gap-3 flex-wrap">
            <button
              onClick={() => onStart()}
              className="inline-flex items-center gap-2 bg-amber-600 hover:bg-amber-500 text-white font-semibold rounded-xl px-7 py-3 transition-colors"
            >
              <ShoppingCart size={17} /> Start shopping <ArrowRight size={15} />
            </button>
            {!profile && (
              <button
                onClick={onSignIn}
                className="inline-flex items-center gap-2 bg-ink-900 border border-ink-700 hover:border-amber-600/60 text-ink-200 font-medium rounded-xl px-6 py-3 transition-colors"
              >
                Set up your profile
              </button>
            )}
          </div>
        </div>

        {/* Category tiles */}
        <div className="pb-8">
          <div className="text-xs font-semibold text-ink-400 uppercase tracking-widest mb-4">Shop by category</div>
          <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide">
            {HOME_CATEGORIES.map(({ label, Icon, color, query }) => (
              <button
                key={label}
                onClick={() => onStart(query)}
                className="flex-shrink-0 flex flex-col items-center justify-center gap-2 w-20 h-20 rounded-xl bg-ink-900 border border-ink-800 hover:border-amber-600/50 transition-all hover:-translate-y-0.5"
              >
                <Icon size={22} className={color} />
                <span className="text-[11px] text-ink-300 font-medium">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Featured section */}
        <div className="pb-10">
          <div className="flex items-center justify-between mb-4">
            <div className="text-sm font-semibold text-ink-200">Trending in Nigeria</div>
            <button onClick={() => onStart()} className="text-xs text-amber-400 hover:text-amber-300">Browse all →</button>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {FEATURED.map(({ label, gradient, Icon }) => (
              <button
                key={label}
                onClick={() => onStart(label)}
                className={`bg-gradient-to-br ${gradient} rounded-xl p-4 border border-ink-800 hover:border-amber-600/40 transition-all hover:-translate-y-0.5 text-left`}
              >
                <Icon size={22} className="text-white/70 mb-3" strokeWidth={1.4} />
                <div className="text-xs font-semibold text-ink-100 leading-snug">{label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Quick stats */}
        <div className="pb-12 flex items-center justify-center gap-4 flex-wrap">
          {[
            { label: "5 languages", desc: "Shop in your language" },
            { label: "Persona-aware AI", desc: "Tailored to you" },
            { label: "Pay on delivery", desc: "No upfront risk" },
          ].map(({ label, desc }) => (
            <div key={label} className="inline-flex items-center gap-2 bg-ink-900 border border-ink-800 rounded-full px-4 py-2">
              <Check size={12} className="text-amber-400" />
              <div>
                <div className="text-xs font-semibold text-ink-100">{label}</div>
                <div className="text-[10px] text-ink-500">{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── ShopApp state machine ─────────────────────────────────────────────────────

function ShopApp({ lang }: { lang: AppLang }) {
  const [view, setView] = useState<View>("store");
  const [profile, setProfile] = useState<ShopProfile | null>(null);
  const [shopPersona, setShopPersona] = useState<ShopPersona | null>(null);
  const [onboarding, setOnboarding] = useState(false);
  const [storeCategory, setStoreCategory] = useState<string | undefined>(undefined);
  const [wishlistCount, setWishlistCount] = useState(0);

  useEffect(() => {
    const p = loadProfile();
    if (p) {
      api.getProfile(p.id)
        .then((r) => setProfile({ id: p.id, name: r.name, persona: r.persona }))
        .catch(() => {});
    }
    const hasSession = !!localStorage.getItem("shop_profile_id");
    if (hasSession) {
      getShopPersona().then(setShopPersona).catch(() => {});
      getWishlist().then((items) => setWishlistCount(items.length)).catch(() => {});
    }
  }, []);

  function goStore(category?: string) {
    setStoreCategory(category);
    setView("store");
  }

  function handleSignOut() {
    localStorage.removeItem("shop_profile_id");
    localStorage.removeItem("shop_profile_name");
    setProfile(null);
    setShopPersona(null);
    setWishlistCount(0);
    setView("store");
  }

  const layoutProps = {
    view,
    onNav: (v: View) => { if (v === "store") goStore(); else setView(v); },
    onCategorySelect: goStore,
    profile,
    shopPersona,
    wishlistCount,
    onSignIn: () => setOnboarding(true),
    onSignOut: handleSignOut,
  };

  return (
    <ShopLayoutWrapper {...layoutProps}>
      {view === "home" && (
        <Home profile={profile} onStart={goStore} onSignIn={() => setOnboarding(true)} />
      )}
      {view === "profile" && (
        <ProfilePage
          profile={profile}
          persona={shopPersona}
          onBack={() => setView("store")}
          onSignOut={handleSignOut}
        />
      )}
      {view === "orders" && (
        <OrderHistory onBack={() => setView("store")} />
      )}
      {view === "wishlist" && (
        <WishlistPage
          onBack={() => setView("store")}
          onSignIn={() => setOnboarding(true)}
          onWishlistChange={setWishlistCount}
        />
      )}
      {(view === "store" || !["home","profile","orders","wishlist"].includes(view)) && (
        <Store
          lang={lang}
          profile={profile}
          shopPersona={shopPersona}
          onHome={() => setView("home")}
          onSignIn={() => setOnboarding(true)}
          onProfile={() => setView("profile")}
          onOrders={() => setView("orders")}
          onWishlist={() => setView("wishlist")}
          initialCategory={storeCategory}
          onWishlistCountChange={setWishlistCount}
        />
      )}
      {onboarding && (
        <Onboarding
          onClose={() => setOnboarding(false)}
          onDone={(p) => { setProfile(p); setOnboarding(false); setView("store"); }}
        />
      )}
    </ShopLayoutWrapper>
  );
}

export default function ShopEasy() {
  return (
    <LanguageGate storageKey="shopeasy_lang"
                  title="Welcome to ShopEasy"
                  subtitle="Choose your language to start shopping.">
      {(lang) => <ShopApp lang={lang} />}
    </LanguageGate>
  );
}
