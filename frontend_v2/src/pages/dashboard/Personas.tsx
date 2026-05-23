import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2, MapPin, Briefcase, Users } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { getPanelPersonas, type PanelPersona } from "@/lib/apiClient";

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

function PersonaCard({ persona }: { persona: PanelPersona }) {
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
        <span className={`shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${reg.color}`}>
          {reg.label}
        </span>
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
        <DimensionBar
          label="hedonic"
          value={persona.hedonic_utilitarian}
          leftLabel="Utilitarian"
          rightLabel="Hedonic"
          color="bg-purple-500"
        />
        <DimensionBar
          label="communal"
          value={persona.communal_individual}
          leftLabel="Individual"
          rightLabel="Communal"
          color="bg-naija-500"
        />
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
                <PersonaCard key={p.user_id} persona={p} />
              ))}
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
