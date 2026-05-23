/**
 * Public share page — /share/:token
 * No auth, no DashboardLayout.
 */
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Star, CheckCircle, XCircle } from "lucide-react";
import { getSharedRun, type PersonaResult } from "@/lib/apiClient";

function StarRating({ rating }: { rating: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star key={i} size={12} className={i <= rating ? "text-amber-400 fill-amber-400" : "text-ink-700"} />
      ))}
    </span>
  );
}

function RatingBar({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-3">
      <span className="text-xs text-ink-400 w-4 shrink-0">{label}★</span>
      <div className="flex-1 h-2 bg-ink-800 rounded-full overflow-hidden">
        <div className="h-full bg-naija-600 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-ink-500 w-6 text-right">{count}</span>
    </div>
  );
}

function sentimentColor(s: string) {
  if (s === "positive") return "text-naija-400 bg-naija-900/30 border-naija-700/50";
  if (s === "negative") return "text-red-400 bg-red-900/20 border-red-700/40";
  return "text-ink-400 bg-ink-800 border-ink-700";
}

export default function ShareView() {
  const { token } = useParams<{ token: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ["shared-run", token],
    queryFn: () => getSharedRun(token!),
    enabled: !!token,
    staleTime: 60000,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-ink-950 flex items-center justify-center">
        <Loader2 size={32} className="text-naija-400 animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-ink-950 flex flex-col items-center justify-center gap-4 text-center p-6">
        <XCircle size={36} className="text-red-400" />
        <h2 className="text-lg font-semibold text-ink-100">Panel not found</h2>
        <p className="text-sm text-ink-500">This share link may be invalid or expired.</p>
        <Link to="/signup" className="text-sm text-naija-400 hover:text-naija-300 transition-colors">
          Run your own panel →
        </Link>
      </div>
    );
  }

  const agg = data.aggregate;

  return (
    <div className="min-h-screen bg-ink-950 text-ink-100">
      {/* Header bar */}
      <div className="border-b border-ink-800 bg-ink-950 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 group">
            <span className="w-8 h-8 rounded-lg bg-naija-600 flex items-center justify-center text-white text-sm font-bold group-hover:bg-naija-500 transition-colors shrink-0">
              NP
            </span>
            <span className="font-bold text-ink-50 text-sm">Naija Persona</span>
          </Link>
          <Link
            to="/signup"
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-naija-600 hover:bg-naija-500 text-white text-sm font-medium transition-colors"
          >
            Run your own panel →
          </Link>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* Title */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs px-2.5 py-1 rounded-full border border-naija-700/50 bg-naija-900/30 text-naija-400 font-medium capitalize">
              {data.project_category}
            </span>
            <span className="flex items-center gap-1 text-xs text-naija-400">
              <CheckCircle size={12} /> Completed
            </span>
          </div>
          <h1 className="text-2xl font-bold text-ink-50">{data.project_name}</h1>
          <p className="text-sm text-ink-500">
            {data.completed_at
              ? new Date(data.completed_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })
              : new Date(data.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}
          </p>
        </div>

        {/* Stat cards */}
        {agg && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {[
              { label: "Avg rating", value: `${agg.avg_rating.toFixed(1)} / 5`, color: "text-amber-400" },
              { label: "Buy likelihood", value: `${agg.buy_likelihood}%`, color: "text-naija-400" },
              { label: "Personas", value: agg.n_personas, color: "text-blue-400" },
              { label: "Positive", value: agg.sentiment_split?.positive ?? 0, color: "text-naija-400" },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-1">
                <p className={`text-2xl font-bold ${color}`}>{value}</p>
                <p className="text-xs font-medium text-ink-200">{label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Rating distribution + Themes */}
        {agg && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-4">
              <h2 className="font-semibold text-ink-100">Rating distribution</h2>
              <div className="space-y-2">
                {[5, 4, 3, 2, 1].map((star) => (
                  <RatingBar key={star} label={String(star)} count={agg.rating_distribution?.[String(star)] ?? 0} total={agg.n_personas} />
                ))}
              </div>
            </div>
            <div className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-4">
              <h2 className="font-semibold text-ink-100">Top themes</h2>
              {agg.themes ? (
                <div className="space-y-4">
                  {[
                    { label: "Praised", items: agg.themes.praised, cls: "bg-naija-900/40 border-naija-700/40 text-naija-300" },
                    { label: "Concerns", items: agg.themes.complaints, cls: "bg-red-900/20 border-red-700/30 text-red-300" },
                  ].map(({ label, items, cls }) => (
                    <div key={label} className="space-y-2">
                      <p className="text-xs font-medium text-ink-500 uppercase tracking-wider">{label}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {items.map((t) => <span key={t} className={`text-xs px-2.5 py-1 rounded-full border ${cls}`}>{t}</span>)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : <p className="text-sm text-ink-500">No theme data.</p>}
            </div>
          </div>
        )}

        {/* Persona results table */}
        {data.results.length > 0 && (
          <div className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
            <div className="px-5 py-3 border-b border-ink-800 bg-ink-950/40">
              <h2 className="font-semibold text-ink-100 text-sm">Persona results</h2>
            </div>
            <div className="divide-y divide-ink-800 max-h-[480px] overflow-y-auto">
              {data.results.map((r: PersonaResult) => (
                <div key={r.id} className="flex items-center gap-4 px-5 py-3">
                  <div className="w-7 h-7 rounded-lg bg-naija-900/50 border border-naija-700/30 flex items-center justify-center text-naija-400 text-xs font-bold shrink-0">
                    {r.persona_name.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-ink-100">{r.persona_name}</p>
                    <p className="text-xs text-ink-500 truncate mt-0.5">{r.review_text}</p>
                  </div>
                  <StarRating rating={r.rating} />
                  <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full border font-medium ${sentimentColor(r.sentiment)}`}>
                    {r.sentiment}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div className="bg-ink-900 border border-naija-800/50 rounded-xl p-8 text-center space-y-4">
          <h3 className="text-lg font-bold text-ink-50">Test your product with 24 Nigerian personas</h3>
          <p className="text-sm text-ink-400">Get authentic consumer insights from diverse Nigerian voices in minutes.</p>
          <Link
            to="/signup"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-naija-600 hover:bg-naija-500 text-white font-semibold text-sm transition-colors"
          >
            Run your own panel →
          </Link>
        </div>
      </div>
    </div>
  );
}
