import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, MapPin, Briefcase, Users, MoreVertical, Star, X, BarChart2 } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { getPanelPersonas, getPersonaReviews, type PanelPersona, type PersonaReview } from "@/lib/apiClient";

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatName(id: string) {
  return id.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
}

const REGISTER_META: Record<string, { label: string; color: string; dot: string }> = {
  nigerian_english: { label: "Nigerian English", color: "text-blue-400 border-blue-700/50 bg-blue-900/20", dot: "bg-blue-400" },
  nigerian_pidgin:  { label: "Pidgin",           color: "text-amber-400 border-amber-700/50 bg-amber-900/20", dot: "bg-amber-400" },
  code_mixed:       { label: "Code-mixed",        color: "text-naija-400 border-naija-700/50 bg-naija-900/20", dot: "bg-naija-500" },
  formal_english:   { label: "Formal English",    color: "text-ink-300 border-ink-600/50 bg-ink-800/30", dot: "bg-ink-400" },
};

const ZONE_COLORS: Record<string, string> = {
  "South-West":   "bg-emerald-600",
  "South-East":   "bg-naija-600",
  "South-South":  "bg-teal-600",
  "North-West":   "bg-blue-600",
  "North-East":   "bg-purple-600",
  "North-Central":"bg-orange-600",
};

const ZONE_BY_STATE: Record<string, string> = {
  lagos: "South-West", ibadan: "South-West", ogun: "South-West", ekiti: "South-West", osun: "South-West", ondo: "South-West", oyo: "South-West",
  owerri: "South-East", aba: "South-East", enugu: "South-East", anambra: "South-East", onitsha: "South-East", nnewi: "South-East", imo: "South-East", abia: "South-East",
  "port harcourt": "South-South", warri: "South-South", calabar: "South-South", delta: "South-South", rivers: "South-South", bayelsa: "South-South",
  kano: "North-West", kaduna: "North-West", sokoto: "North-West", katsina: "North-West", zamfara: "North-West", kebbi: "North-West", jigawa: "North-West",
  maiduguri: "North-East", bauchi: "North-East", gombe: "North-East", adamawa: "North-East", yola: "North-East",
  abuja: "North-Central", jos: "North-Central", makurdi: "North-Central", ilorin: "North-Central", lokoja: "North-Central",
};

function zoneFor(location: string) {
  const loc = location.toLowerCase();
  for (const [key, zone] of Object.entries(ZONE_BY_STATE)) {
    if (loc.includes(key)) return zone;
  }
  return "Unknown";
}

function avatarColor(zone: string) {
  return ZONE_COLORS[zone] ?? "bg-ink-700";
}

const ALL_REGISTERS = ["all", "nigerian_english", "nigerian_pidgin", "code_mixed", "formal_english"];

function DimensionBar({ label, value, leftLabel, rightLabel, color }: {
  label: string; value: number; leftLabel: string; rightLabel: string; color: string;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-ink-600">
        <span>{leftLabel}</span>
        <span>{rightLabel}</span>
      </div>
      <div className="h-1.5 bg-ink-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Three-dot menu ────────────────────────────────────────────────────────────

function ThreeDotMenu({ onViewRatings }: { onViewRatings: () => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative shrink-0">
      <button
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o); }}
        className="w-7 h-7 flex items-center justify-center rounded-lg text-ink-600 hover:text-ink-200 hover:bg-ink-800 transition-colors"
      >
        <MoreVertical size={15} />
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 z-20 w-52 bg-ink-900 border border-ink-700 rounded-xl shadow-2xl py-1 overflow-hidden">
          <button
            onClick={(e) => { e.stopPropagation(); setOpen(false); onViewRatings(); }}
            className="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-ink-200 hover:bg-ink-800 hover:text-naija-300 transition-colors"
          >
            <BarChart2 size={14} className="text-naija-400 shrink-0" />
            View ratings in projects
          </button>
        </div>
      )}
    </div>
  );
}

// ── Reviews modal ─────────────────────────────────────────────────────────────

function sentimentStyle(s: string) {
  if (s === "positive") return "text-naija-400 bg-naija-900/30 border-naija-700/40";
  if (s === "negative") return "text-red-400 bg-red-900/20 border-red-700/30";
  return "text-ink-400 bg-ink-800 border-ink-700";
}

function ReviewsModal({
  persona,
  onClose,
}: {
  persona: PanelPersona;
  onClose: () => void;
}) {
  const navigate = useNavigate();
  const name = formatName(persona.user_id);

  const { data: reviews, isLoading } = useQuery({
    queryKey: ["persona-reviews", persona.user_id],
    queryFn: () => getPersonaReviews(persona.user_id),
  });

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-ink-950 border border-ink-700 rounded-2xl w-full max-w-xl max-h-[80vh] flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-ink-800 shrink-0">
          <div className="flex items-center gap-3">
            <div className={`w-9 h-9 rounded-xl ${avatarColor(zoneFor(persona.demographics?.location ?? ""))} flex items-center justify-center text-white text-sm font-bold`}>
              {name.charAt(0)}
            </div>
            <div>
              <p className="font-semibold text-ink-50">{name}</p>
              <p className="text-xs text-ink-500">Ratings across your projects</p>
            </div>
          </div>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-100 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="flex items-center justify-center py-16">
              <Loader2 size={24} className="text-naija-400 animate-spin" />
            </div>
          )}

          {!isLoading && reviews?.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 space-y-2 text-center px-6">
              <BarChart2 size={28} className="text-ink-700" />
              <p className="text-sm text-ink-400">No reviews yet</p>
              <p className="text-xs text-ink-600">
                Run a panel to see how {name} rates your products.
              </p>
            </div>
          )}

          {!isLoading && reviews && reviews.length > 0 && (
            <div className="divide-y divide-ink-800">
              {reviews.map((r, i) => (
                <div
                  key={`${r.run_id}-${i}`}
                  className="px-6 py-4 hover:bg-ink-900/40 transition-colors cursor-pointer group"
                  onClick={() => { onClose(); navigate(`/runs/${r.run_id}`); }}
                >
                  {/* Project + date */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-ink-100 group-hover:text-naija-300 transition-colors truncate">
                        {r.project_name}
                      </p>
                      <p className="text-xs text-ink-600 mt-0.5">
                        {new Date(r.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
                        {r.project_category && (
                          <span className="ml-2 text-ink-700">· {r.project_category}</span>
                        )}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      {/* Star rating */}
                      <span className="flex items-center gap-0.5">
                        {[1, 2, 3, 4, 5].map((s) => (
                          <Star
                            key={s}
                            size={12}
                            className={s <= r.rating ? "text-amber-400 fill-amber-400" : "text-ink-700"}
                          />
                        ))}
                      </span>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full border font-medium ${sentimentStyle(r.sentiment)}`}>
                        {r.sentiment}
                      </span>
                    </div>
                  </div>
                  {/* Review snippet */}
                  <p className="text-xs text-ink-400 leading-relaxed line-clamp-3">{r.review_text}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {reviews && reviews.length > 0 && (
          <div className="border-t border-ink-800 px-6 py-3 shrink-0">
            <p className="text-xs text-ink-600 text-center">
              {reviews.length} review{reviews.length !== 1 ? "s" : ""} · click any row to open the full run
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Persona card ──────────────────────────────────────────────────────────────

function PersonaCard({
  persona,
  onViewRatings,
}: {
  persona: PanelPersona;
  onViewRatings: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const name = formatName(persona.user_id);
  const dem = persona.demographics || {};
  const zone = zoneFor(dem.location ?? "");
  const reg = REGISTER_META[persona.register_tier] ?? {
    label: persona.register_tier, color: "text-ink-400 border-ink-700 bg-ink-800", dot: "bg-ink-500",
  };
  const topAspects = Object.entries(persona.aspect_priority)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  return (
    <div className="bg-ink-900 border border-ink-800 hover:border-ink-700 rounded-xl p-5 space-y-4 transition-colors">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className={`w-10 h-10 rounded-xl ${avatarColor(zone)} flex items-center justify-center text-white text-sm font-bold shrink-0`}>
          {name.charAt(0)}
        </div>
        <div className="flex-1 min-w-0 space-y-0.5">
          <p className="font-semibold text-ink-50 truncate">{name}</p>
          {dem.location && (
            <p className="flex items-center gap-1 text-xs text-ink-500 truncate">
              <MapPin size={10} className="shrink-0" />
              {dem.location}
            </p>
          )}
        </div>
        {/* Register badge + three-dot menu */}
        <div className="flex items-center gap-1 shrink-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full border ${reg.color}`}>
            {reg.label}
          </span>
          <ThreeDotMenu onViewRatings={onViewRatings} />
        </div>
      </div>

      {/* Occupation + age */}
      <div className="flex items-center gap-3 text-xs text-ink-500">
        {dem.occupation && (
          <span className="flex items-center gap-1 truncate">
            <Briefcase size={10} className="shrink-0" />
            {dem.occupation}
          </span>
        )}
        {dem.age_range && (
          <span className="shrink-0 px-2 py-0.5 rounded-md bg-ink-800 text-ink-400">
            {dem.age_range}
          </span>
        )}
      </div>

      {/* Cognitive dimensions */}
      <div className="space-y-2">
        <DimensionBar label="hedonic" value={persona.hedonic_utilitarian} leftLabel="Utilitarian" rightLabel="Hedonic" color="bg-purple-500" />
        <DimensionBar label="communal" value={persona.communal_individual} leftLabel="Individual" rightLabel="Communal" color="bg-naija-500" />
      </div>

      {/* Top aspects */}
      <div className="space-y-1.5">
        <p className="text-xs text-ink-600 uppercase tracking-wider font-medium">Aspect priorities</p>
        <div className="flex flex-wrap gap-1.5">
          {topAspects.map(([asp, w]) => (
            <span key={asp} className="text-xs px-2 py-0.5 rounded-md bg-ink-800 text-ink-300">
              {asp.replace(/_/g, " ")}
              <span className="text-ink-600 ml-1">{Math.round(w * 100)}%</span>
            </span>
          ))}
        </div>
      </div>

      {/* Register markers — toggle */}
      {persona.register_markers?.length > 0 && (
        <div>
          <button
            onClick={() => setExpanded((e) => !e)}
            className="text-xs text-ink-500 hover:text-ink-300 transition-colors"
          >
            {expanded ? "Hide markers ↑" : `${persona.register_markers.length} register markers ↓`}
          </button>
          {expanded && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {persona.register_markers.map((m) => (
                <span key={m} className="text-xs px-2 py-0.5 rounded-md bg-naija-900/30 border border-naija-700/30 text-naija-300 italic">
                  "{m}"
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Zone chip */}
      <div className="flex items-center justify-between pt-1 border-t border-ink-800">
        <span className="text-xs text-ink-600">{zone}</span>
        <span className="text-xs text-ink-700">{persona.history_count} anchors</span>
      </div>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function Personas() {
  const [filter, setFilter] = useState("all");
  const [reviewPersona, setReviewPersona] = useState<PanelPersona | null>(null);

  const { data: personas, isLoading, error } = useQuery({
    queryKey: ["panel-personas"],
    queryFn: getPanelPersonas,
    staleTime: Infinity, // static data — never refetch
  });

  const filtered = filter === "all"
    ? (personas ?? [])
    : (personas ?? []).filter((p) => p.register_tier === filter);

  const counts = personas ? {
    total: personas.length,
    zones: new Set(personas.map((p) => zoneFor(p.demographics?.location ?? "")).filter((z) => z !== "Unknown")).size,
  } : null;

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold text-ink-50">The Panel</h1>
          <p className="text-sm text-ink-400">
            24 culturally-grounded Nigerian consumer personas used in every InsideNaija run
          </p>
        </div>

        {/* Stats row */}
        {counts && (
          <div className="flex items-center gap-6">
            {[
              { value: counts.total, label: "Personas" },
              { value: counts.zones, label: "Geopolitical zones" },
              { value: 4, label: "Languages" },
              { value: "8B", label: "Model backbone" },
            ].map(({ value, label }) => (
              <div key={label} className="text-center">
                <p className="text-xl font-bold text-naija-400">{value}</p>
                <p className="text-xs text-ink-500">{label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filter chips */}
        <div className="flex flex-wrap gap-2">
          {ALL_REGISTERS.map((r) => {
            const meta = r === "all" ? null : REGISTER_META[r];
            const count = r === "all"
              ? (personas?.length ?? 0)
              : (personas?.filter((p) => p.register_tier === r).length ?? 0);
            return (
              <button
                key={r}
                onClick={() => setFilter(r)}
                className={`text-xs font-medium px-3 py-1.5 rounded-full border transition-all ${
                  filter === r
                    ? "bg-naija-600 border-naija-500 text-white"
                    : "border-ink-700 text-ink-400 hover:text-ink-100 hover:border-ink-600"
                }`}
              >
                {r === "all" ? "All" : (meta?.label ?? r)}{" "}
                <span className="opacity-60">({count})</span>
              </button>
            );
          })}
        </div>

        {/* Grid */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="text-naija-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-center">
            <p className="text-red-400 text-sm">Failed to load personas.</p>
          </div>
        )}

        {!isLoading && !error && (
          <>
            <p className="text-xs text-ink-600">
              {filtered.length} persona{filtered.length !== 1 ? "s" : ""}
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((p) => (
                <PersonaCard
                  key={p.user_id}
                  persona={p}
                  onViewRatings={() => setReviewPersona(p)}
                />
              ))}
            </div>
          </>
        )}
      </div>

      {/* Reviews modal */}
      {reviewPersona && (
        <ReviewsModal
          persona={reviewPersona}
          onClose={() => setReviewPersona(null)}
        />
      )}
    </DashboardLayout>
  );
}
