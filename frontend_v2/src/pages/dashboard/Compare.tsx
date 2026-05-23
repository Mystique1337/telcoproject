/**
 * Run comparison page — /compare?a={runId}&b={runId}
 */
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Loader2, TrendingUp, TrendingDown, Minus, ArrowLeft } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { compareRuns, type RunCompareSide } from "@/lib/apiClient";

function RatingBar({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-ink-500 w-4 shrink-0">{label}★</span>
      <div className="flex-1 h-1.5 bg-ink-800 rounded-full overflow-hidden">
        <div className="h-full bg-naija-600 rounded-full" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-ink-600 w-4 text-right">{count}</span>
    </div>
  );
}

function SentBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2">
      <span className={`text-xs w-16 shrink-0 ${color}`}>{label}</span>
      <div className="flex-1 h-1.5 bg-ink-800 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color.includes("naija") ? "bg-naija-600" : color.includes("red") ? "bg-red-600" : "bg-ink-600"}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-ink-600 w-8 text-right">{pct}%</span>
    </div>
  );
}

type StatProps = {
  label: string;
  aVal: number | string | null | undefined;
  bVal: number | string | null | undefined;
  higher?: "a" | "b" | null;
  format?: (v: number) => string;
};

function StatRow({ label, aVal, bVal, format }: StatProps) {
  const aNum = typeof aVal === "number" ? aVal : null;
  const bNum = typeof bVal === "number" ? bVal : null;
  const aWins = aNum != null && bNum != null && aNum > bNum;
  const bWins = aNum != null && bNum != null && bNum > aNum;

  function display(v: number | string | null | undefined) {
    if (v == null) return "—";
    if (typeof v === "number" && format) return format(v);
    return String(v);
  }

  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-2 py-2.5 border-b border-ink-800 last:border-0">
      <div className={`text-sm font-semibold text-right ${aWins ? "text-naija-400" : "text-ink-200"}`}>
        {display(aVal)}
        {aWins && <TrendingUp size={12} className="inline ml-1 text-naija-400" />}
      </div>
      <span className="text-xs text-ink-600 text-center whitespace-nowrap px-2">{label}</span>
      <div className={`text-sm font-semibold ${bWins ? "text-naija-400" : "text-ink-200"}`}>
        {display(bVal)}
        {bWins && <TrendingUp size={12} className="inline ml-1 text-naija-400" />}
      </div>
    </div>
  );
}

function RunColumn({ side, label }: { side: RunCompareSide; label: string }) {
  const agg = side.aggregate;
  return (
    <div className="flex-1 space-y-1">
      <p className="text-xs font-semibold uppercase tracking-wider text-ink-500">{label}</p>
      <h2 className="font-bold text-ink-50 text-base leading-snug">{side.project_name}</h2>
      <p className="text-xs text-ink-500 capitalize">{side.project_category}</p>
      <p className="text-xs text-ink-600">
        {new Date(side.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
      </p>
      {agg && (
        <div className="mt-4 space-y-3">
          <div className="bg-ink-900 border border-ink-800 rounded-xl p-4 space-y-2">
            <p className="text-xs font-medium text-ink-500 uppercase tracking-wider">Rating distribution</p>
            {[5, 4, 3, 2, 1].map((s) => (
              <RatingBar key={s} label={String(s)} count={agg.rating_distribution?.[String(s)] ?? 0} total={agg.n_personas} />
            ))}
          </div>
          <div className="bg-ink-900 border border-ink-800 rounded-xl p-4 space-y-2">
            <p className="text-xs font-medium text-ink-500 uppercase tracking-wider">Sentiment</p>
            {[
              { key: "positive", label: "Positive", color: "text-naija-400" },
              { key: "neutral", label: "Neutral", color: "text-ink-400" },
              { key: "negative", label: "Negative", color: "text-red-400" },
            ].map(({ key, label, color }) => (
              <SentBar
                key={key}
                label={label}
                count={(agg.sentiment_split as Record<string, number>)?.[key] ?? 0}
                total={agg.n_personas}
                color={color}
              />
            ))}
          </div>
          {agg.themes?.praised && (
            <div className="bg-ink-900 border border-ink-800 rounded-xl p-4 space-y-2">
              <p className="text-xs font-medium text-ink-500 uppercase tracking-wider">Praised themes</p>
              <div className="flex flex-wrap gap-1.5">
                {agg.themes.praised.slice(0, 5).map((t) => (
                  <span key={t} className="text-xs px-2 py-0.5 rounded-full border bg-naija-900/40 border-naija-700/40 text-naija-300">{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Compare() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const runA = params.get("a") ?? "";
  const runB = params.get("b") ?? "";

  const { data, isLoading, error } = useQuery({
    queryKey: ["compare", runA, runB],
    queryFn: () => compareRuns(runA, runB),
    enabled: !!runA && !!runB,
    staleTime: 60000,
  });

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink-50">Compare runs</h1>
            <p className="text-sm text-ink-400 mt-0.5">Side-by-side panel comparison</p>
          </div>
          <button
            onClick={() => navigate("/history")}
            className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-100 transition-colors"
          >
            <ArrowLeft size={15} /> Back to history
          </button>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="text-naija-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-center">
            <p className="text-red-400 text-sm">Failed to load comparison.</p>
          </div>
        )}

        {data && (
          <>
            {/* Key stats comparison */}
            <div className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
              <div className="grid grid-cols-[1fr_auto_1fr] px-5 py-3 border-b border-ink-800 bg-ink-950/40">
                <span className="text-xs font-semibold text-naija-400 text-right">Run A</span>
                <span className="px-4" />
                <span className="text-xs font-semibold text-naija-400">Run B</span>
              </div>
              <div className="px-5 py-2">
                <StatRow
                  label="Project"
                  aVal={data.run_a.project_name}
                  bVal={data.run_b.project_name}
                />
                <StatRow
                  label="Avg rating"
                  aVal={data.run_a.aggregate?.avg_rating}
                  bVal={data.run_b.aggregate?.avg_rating}
                  format={(v) => `${v.toFixed(1)} / 5`}
                />
                <StatRow
                  label="Buy likelihood"
                  aVal={data.run_a.aggregate?.buy_likelihood}
                  bVal={data.run_b.aggregate?.buy_likelihood}
                  format={(v) => `${v}%`}
                />
                <StatRow
                  label="Personas"
                  aVal={data.run_a.aggregate?.n_personas}
                  bVal={data.run_b.aggregate?.n_personas}
                />
                <StatRow
                  label="Positive"
                  aVal={data.run_a.aggregate?.sentiment_split?.positive}
                  bVal={data.run_b.aggregate?.sentiment_split?.positive}
                />
              </div>
            </div>

            {/* Side-by-side detail */}
            <div className="flex gap-6">
              <RunColumn side={data.run_a} label="Run A" />
              <div className="w-px bg-ink-800 shrink-0 my-2" />
              <RunColumn side={data.run_b} label="Run B" />
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
