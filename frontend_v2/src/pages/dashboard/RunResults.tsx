import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  CheckCircle,
  Download,
  Loader2,
  Star,
  XCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import { getRun, type PersonaResult, type RunDetail } from "@/lib/apiClient";

// ── Helpers ──────────────────────────────────────────────────────────────────

function sentimentColor(s: string) {
  if (s === "positive") return "text-naija-400 bg-naija-900/30 border-naija-700/50";
  if (s === "negative") return "text-red-400 bg-red-900/20 border-red-700/40";
  return "text-ink-400 bg-ink-800 border-ink-700";
}

function StarRating({ rating }: { rating: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          size={12}
          className={i <= rating ? "text-amber-400 fill-amber-400" : "text-ink-700"}
        />
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
        <div
          className="h-full bg-naija-600 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-ink-500 w-8 text-right">{count}</span>
    </div>
  );
}

// ── CSV export ────────────────────────────────────────────────────────────────

function exportCSV(run: RunDetail) {
  const rows = [
    ["Persona", "Rating", "Sentiment", "Register", "Review"],
    ...run.results.map((r) => [
      r.persona_name,
      r.rating,
      r.sentiment,
      r.register_tier,
      `"${r.review_text.replace(/"/g, '""')}"`,
    ]),
  ];
  const csv = rows.map((r) => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${run.project_name}-results.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ── Sub-components ────────────────────────────────────────────────────────────

function RunningState({ projectName }: { projectName: string }) {
  const [dots, setDots] = useState(".");
  useEffect(() => {
    const id = setInterval(
      () => setDots((d) => (d.length >= 3 ? "." : d + ".")),
      600,
    );
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center py-24 space-y-6 text-center">
      <div className="relative">
        <div className="w-20 h-20 rounded-full border-2 border-naija-700/30 flex items-center justify-center">
          <Loader2 size={32} className="text-naija-400 animate-spin" />
        </div>
        <div className="absolute inset-0 rounded-full border-2 border-naija-500/20 animate-ping" />
      </div>
      <div className="space-y-2">
        <h2 className="text-xl font-semibold text-ink-100">{projectName}</h2>
        <p className="text-naija-400 font-medium">Panel running{dots}</p>
        <p className="text-sm text-ink-400 max-w-sm">
          24 Nigerian personas are evaluating your product. This takes about 90 seconds.
        </p>
      </div>
      <div className="grid grid-cols-3 gap-4 mt-4">
        {["24 personas", "6 zones", "<2 min"].map((s) => (
          <div key={s} className="bg-ink-900 border border-ink-800 rounded-xl px-4 py-3 text-center">
            <p className="text-sm font-semibold text-naija-400">{s}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function FailedState({ error }: { error?: string }) {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-24 space-y-4 text-center">
      <XCircle size={40} className="text-red-400" />
      <h2 className="text-xl font-semibold text-ink-100">Panel run failed</h2>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <Button variant="outline" className="border-ink-700 text-ink-200" onClick={() => navigate("/dashboard")}>
        Back to dashboard
      </Button>
    </div>
  );
}

function CohortTable({ data }: { data: Record<string, { n: number; avg_rating: number; buy_likelihood: number }> }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-ink-800">
            <th className="text-left py-2 px-3 text-xs font-medium text-ink-500">Segment</th>
            <th className="text-right py-2 px-3 text-xs font-medium text-ink-500">n</th>
            <th className="text-right py-2 px-3 text-xs font-medium text-ink-500">Avg rating</th>
            <th className="text-right py-2 px-3 text-xs font-medium text-ink-500">Buy likelihood</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data).map(([key, val]) => (
            <tr key={key} className="border-b border-ink-800/50 hover:bg-ink-800/30 transition-colors">
              <td className="py-2.5 px-3 text-ink-200">{key}</td>
              <td className="py-2.5 px-3 text-right text-ink-400">{val.n}</td>
              <td className="py-2.5 px-3 text-right text-amber-400 font-medium">
                {val.avg_rating.toFixed(1)}
              </td>
              <td className="py-2.5 px-3 text-right text-naija-400">{val.buy_likelihood}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PersonaRow({ result, onClick }: { result: PersonaResult; onClick: () => void }) {
  return (
    <tr
      className="border-b border-ink-800/50 hover:bg-ink-800/30 transition-colors cursor-pointer"
      onClick={onClick}
    >
      <td className="py-3 px-4">
        <span className="font-medium text-ink-200">{result.persona_name}</span>
      </td>
      <td className="py-3 px-4">
        <StarRating rating={result.rating} />
      </td>
      <td className="py-3 px-4">
        <span
          className={`text-xs px-2 py-0.5 rounded-full border font-medium ${sentimentColor(result.sentiment)}`}
        >
          {result.sentiment}
        </span>
      </td>
      <td className="py-3 px-4 text-xs text-ink-500">{result.register_tier?.replace(/_/g, " ")}</td>
      <td className="py-3 px-4 max-w-xs">
        <p className="text-xs text-ink-400 truncate">{result.review_text}</p>
      </td>
    </tr>
  );
}

// ── Results page ──────────────────────────────────────────────────────────────

export default function RunResults() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [expandedPersona, setExpandedPersona] = useState<PersonaResult | null>(null);
  const [cohortTab, setCohortTab] = useState<"by_zone" | "by_register" | "by_age">("by_zone");

  const { data: run, error } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => getRun(runId!),
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 4000 : false,
    enabled: !!runId,
  });

  if (!run && !error) {
    return (
      <div className="min-h-screen bg-ink-950 flex items-center justify-center">
        <Loader2 size={32} className="text-naija-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-ink-950 text-ink-50">
        <Navbar />
        <FailedState error={(error as Error).message} />
      </div>
    );
  }

  const agg = run!.aggregate;

  return (
    <div className="min-h-screen bg-ink-950 text-ink-50">
      <Navbar />

      <div className="max-w-5xl mx-auto px-6 py-10 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate("/dashboard")}
              className="text-ink-400 hover:text-ink-100 transition-colors"
            >
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-xl font-bold text-ink-50">{run!.project_name}</h1>
              <p className="text-xs text-ink-500">
                {new Date(run!.created_at).toLocaleDateString("en-GB", {
                  day: "numeric", month: "long", year: "numeric",
                })}
              </p>
            </div>
          </div>

          {run!.status === "completed" && (
            <div className="flex items-center gap-2">
              <span className="flex items-center gap-1.5 text-sm text-naija-400">
                <CheckCircle size={16} />
                Complete
              </span>
              <Button
                size="sm"
                variant="outline"
                className="border-ink-700 text-ink-300 hover:border-naija-600"
                onClick={() => exportCSV(run!)}
              >
                <Download size={14} className="mr-1.5" />
                Export CSV
              </Button>
            </div>
          )}
        </div>

        {/* Content by status */}
        {run!.status === "running" && <RunningState projectName={run!.project_name} />}

        {run!.status === "failed" && (
          <FailedState error={agg ? undefined : "Panel run could not complete."} />
        )}

        {run!.status === "completed" && agg && (
          <>
            {/* Stat cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                {
                  label: "Avg rating",
                  value: agg.avg_rating.toFixed(1),
                  sub: "out of 5",
                  color: "text-amber-400",
                },
                {
                  label: "Buy likelihood",
                  value: `${agg.buy_likelihood}%`,
                  sub: "rated ≥4 stars",
                  color: "text-naija-400",
                },
                {
                  label: "Personas",
                  value: agg.n_personas,
                  sub: "evaluated",
                  color: "text-blue-400",
                },
                {
                  label: "Positive",
                  value: agg.sentiment_split?.positive ?? 0,
                  sub: "of personas",
                  color: "text-naija-400",
                },
              ].map(({ label, value, sub, color }) => (
                <div
                  key={label}
                  className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-1"
                >
                  <p className={`text-2xl font-bold ${color}`}>{value}</p>
                  <p className="text-xs font-medium text-ink-200">{label}</p>
                  <p className="text-xs text-ink-600">{sub}</p>
                </div>
              ))}
            </div>

            {/* Rating distribution + Themes */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              {/* Rating distribution */}
              <div className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-4">
                <h2 className="font-semibold text-ink-100">Rating distribution</h2>
                <div className="space-y-2">
                  {[5, 4, 3, 2, 1].map((star) => (
                    <RatingBar
                      key={star}
                      label={String(star)}
                      count={agg.rating_distribution?.[String(star)] ?? 0}
                      total={agg.n_personas}
                    />
                  ))}
                </div>
              </div>

              {/* Themes */}
              <div className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-4">
                <h2 className="font-semibold text-ink-100">Top themes</h2>
                {agg.themes ? (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-naija-400 uppercase tracking-wider">
                        Praised
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {agg.themes.praised.map((t) => (
                          <span
                            key={t}
                            className="text-xs px-2.5 py-1 rounded-full bg-naija-900/40 border border-naija-700/40 text-naija-300"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs font-medium text-red-400 uppercase tracking-wider">
                        Concerns
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {agg.themes.complaints.map((t) => (
                          <span
                            key={t}
                            className="text-xs px-2.5 py-1 rounded-full bg-red-900/20 border border-red-700/30 text-red-300"
                          >
                            {t}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-ink-500">Theme extraction not available.</p>
                )}
              </div>
            </div>

            {/* Cohort breakdown */}
            <div className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
              <div className="flex border-b border-ink-800">
                {(
                  [
                    ["by_zone", "By zone"],
                    ["by_register", "By register"],
                    ["by_age", "By age"],
                  ] as const
                ).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setCohortTab(key)}
                    className={`px-5 py-3 text-sm font-medium transition-colors ${
                      cohortTab === key
                        ? "text-naija-400 border-b-2 border-naija-500"
                        : "text-ink-400 hover:text-ink-200"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="p-4">
                {agg[cohortTab] && Object.keys(agg[cohortTab]).length > 0 ? (
                  <CohortTable data={agg[cohortTab]} />
                ) : (
                  <p className="text-sm text-ink-500 py-4 text-center">No data</p>
                )}
              </div>
            </div>

            {/* Per-persona results */}
            <div className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
              <div className="px-6 py-4 border-b border-ink-800 flex items-center justify-between">
                <h2 className="font-semibold text-ink-100">
                  Persona reviews{" "}
                  <span className="text-sm font-normal text-ink-500">
                    ({run!.results.length})
                  </span>
                </h2>
                <p className="text-xs text-ink-500">Click a row to read the full review</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-ink-950/50">
                    <tr>
                      {["Persona", "Rating", "Sentiment", "Register", "Review"].map((h) => (
                        <th
                          key={h}
                          className="text-left py-2.5 px-4 text-xs font-medium text-ink-500 border-b border-ink-800"
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {run!.results.map((r) => (
                      <PersonaRow
                        key={r.id}
                        result={r}
                        onClick={() => setExpandedPersona(r)}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Review modal */}
      {expandedPersona && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          onClick={() => setExpandedPersona(null)}
        >
          <div
            className="bg-ink-900 border border-ink-700 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <h3 className="font-semibold text-ink-50">{expandedPersona.persona_name}</h3>
                <div className="flex items-center gap-2">
                  <StarRating rating={expandedPersona.rating} />
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full border font-medium ${sentimentColor(expandedPersona.sentiment)}`}
                  >
                    {expandedPersona.sentiment}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setExpandedPersona(null)}
                className="text-ink-500 hover:text-ink-100 text-xl leading-none"
              >
                ×
              </button>
            </div>
            <p className="text-sm text-ink-300 leading-relaxed whitespace-pre-wrap">
              {expandedPersona.review_text}
            </p>
            <p className="text-xs text-ink-600">
              Register: {expandedPersona.register_tier?.replace(/_/g, " ")}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
