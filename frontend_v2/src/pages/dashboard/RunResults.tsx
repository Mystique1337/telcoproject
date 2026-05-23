import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft, CheckCircle, CheckCircle2, Copy, Download, Loader2, Star, XCircle, Clock, Share2, RefreshCw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import DashboardLayout from "@/components/DashboardLayout";
import { getRun, getPanelPersonas, shareRun, rerunProject, type PersonaResult, type RunDetail } from "@/lib/apiClient";

// ── Helpers ───────────────────────────────────────────────────────────────────

function sentimentColor(s: string) {
  if (s === "positive") return "text-naija-400 bg-naija-900/30 border-naija-700/50";
  if (s === "negative") return "text-red-400 bg-red-900/20 border-red-700/40";
  return "text-ink-400 bg-ink-800 border-ink-700";
}

function StarRating({ rating, size = 12 }: { rating: number; size?: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star key={i} size={size} className={i <= rating ? "text-amber-400 fill-amber-400" : "text-ink-700"} />
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

function exportCSV(run: RunDetail) {
  const rows = [
    ["Persona", "Rating", "Sentiment", "Register", "Review"],
    ...run.results.map((r) => [
      r.persona_name, r.rating, r.sentiment, r.register_tier,
      `"${r.review_text.replace(/"/g, '""')}"`,
    ]),
  ];
  const blob = new Blob([rows.map((r) => r.join(",")).join("\n")], { type: "text/csv" });
  const a = Object.assign(document.createElement("a"), { href: URL.createObjectURL(blob), download: `${run.project_name}-results.csv` });
  a.click();
}

// ── Live persona grid card ────────────────────────────────────────────────────

function PersonaCard({
  personaId, personaName, result, onClick,
}: {
  personaId: string;
  personaName: string;
  result?: PersonaResult;
  onClick?: () => void;
}) {
  if (!result) {
    return (
      <div className="bg-ink-900/60 border border-ink-800 rounded-xl p-4 space-y-2 animate-pulse">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-ink-800 shrink-0" />
          <div className="space-y-1 flex-1">
            <div className="h-3 bg-ink-800 rounded w-24" />
            <div className="h-2 bg-ink-800/60 rounded w-16" />
          </div>
          <Clock size={13} className="text-ink-700 shrink-0" />
        </div>
        <p className="text-xs text-ink-700">Waiting…</p>
      </div>
    );
  }

  return (
    <div
      className="bg-ink-900 border border-ink-800 hover:border-naija-700/50 rounded-xl p-4 space-y-2.5 cursor-pointer transition-all group"
      onClick={onClick}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-naija-900/50 border border-naija-700/30 flex items-center justify-center text-naija-400 text-xs font-bold shrink-0">
            {personaName.charAt(0)}
          </div>
          <span className="text-sm font-medium text-ink-100 truncate group-hover:text-naija-300 transition-colors">
            {personaName}
          </span>
        </div>
        <span className={`shrink-0 text-xs px-1.5 py-0.5 rounded-full border font-medium ${sentimentColor(result.sentiment)}`}>
          {result.sentiment}
        </span>
      </div>
      <StarRating rating={result.rating} />
      <p className="text-xs text-ink-500 leading-relaxed line-clamp-2">{result.review_text}</p>
    </div>
  );
}

// ── Progress bar ──────────────────────────────────────────────────────────────

function LiveProgress({ completed, total, projectName }: { completed: number; total: number; projectName: string }) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  return (
    <div className="bg-ink-900 border border-naija-700/30 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative">
            <Loader2 size={20} className="text-naija-400 animate-spin" />
          </div>
          <div>
            <p className="font-semibold text-ink-50">{projectName}</p>
            <p className="text-xs text-naija-400">Panel running live</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-2xl font-bold text-naija-400">{completed}<span className="text-ink-600 text-base font-normal">/{total}</span></p>
          <p className="text-xs text-ink-500">personas done</p>
        </div>
      </div>
      <div className="space-y-1.5">
        <div className="h-2.5 bg-ink-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-naija-600 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${pct}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-ink-600">
          <span>{pct}% complete</span>
          <span>{total - completed} remaining</span>
        </div>
      </div>
    </div>
  );
}

// ── Failed state ──────────────────────────────────────────────────────────────

function FailedState() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-20 space-y-4 text-center">
      <XCircle size={36} className="text-red-400" />
      <h2 className="text-lg font-semibold text-ink-100">Panel run failed</h2>
      <p className="text-sm text-ink-500">Something went wrong during the evaluation.</p>
      <Button variant="outline" className="border-ink-700 text-ink-200" onClick={() => navigate("/dashboard")}>
        Back to dashboard
      </Button>
    </div>
  );
}

// ── Review detail modal ───────────────────────────────────────────────────────

function ReviewModal({ result, onClose }: { result: PersonaResult; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-ink-900 border border-ink-700 rounded-2xl p-6 max-w-lg w-full space-y-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div className="space-y-1.5">
            <h3 className="font-semibold text-ink-50">{result.persona_name}</h3>
            <div className="flex items-center gap-2">
              <StarRating rating={result.rating} />
              <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${sentimentColor(result.sentiment)}`}>
                {result.sentiment}
              </span>
            </div>
          </div>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-100 text-xl">×</button>
        </div>
        <p className="text-sm text-ink-300 leading-relaxed whitespace-pre-wrap">{result.review_text}</p>
        <p className="text-xs text-ink-600">Register: {result.register_tier?.replace(/_/g, " ")}</p>
      </div>
    </div>
  );
}

// ── CohortTable + RatingDist (reused from before) ─────────────────────────────

function CohortTable({ data }: { data: Record<string, { n: number; avg_rating: number; buy_likelihood: number }> }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-ink-800">
          {["Segment", "n", "Avg rating", "Buy %"].map((h) => (
            <th key={h} className={`py-2 px-3 text-xs font-medium text-ink-500 ${h === "Segment" ? "text-left" : "text-right"}`}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {Object.entries(data).map(([key, val]) => (
          <tr key={key} className="border-b border-ink-800/50 hover:bg-ink-800/20">
            <td className="py-2.5 px-3 text-ink-200">{key}</td>
            <td className="py-2.5 px-3 text-right text-ink-400">{val.n}</td>
            <td className="py-2.5 px-3 text-right text-amber-400 font-medium">{val.avg_rating.toFixed(1)}</td>
            <td className="py-2.5 px-3 text-right text-naija-400">{val.buy_likelihood}%</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

function copyToClipboard(text: string): Promise<void> {
  // Modern clipboard API (requires HTTPS or localhost with secure context)
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }
  // Fallback for HTTP: create a temporary input, select all, execCommand
  return new Promise((resolve, reject) => {
    const el = document.createElement("input");
    el.value = text;
    el.style.cssText = "position:fixed;left:-9999px;top:-9999px;opacity:0";
    document.body.appendChild(el);
    el.focus();
    el.select();
    try {
      const ok = document.execCommand("copy");
      document.body.removeChild(el);
      ok ? resolve() : reject(new Error("execCommand failed"));
    } catch (err) {
      document.body.removeChild(el);
      reject(err);
    }
  });
}

function ShareModal({ shareUrl, onClose }: { shareUrl: string; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  const fullUrl = `${window.location.origin}${shareUrl}`;

  function copy() {
    copyToClipboard(fullUrl)
      .then(() => {
        setCopied(true);
        setCopyFailed(false);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch(() => {
        setCopyFailed(true);
        setTimeout(() => setCopyFailed(false), 3000);
      });
  }
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-ink-900 border border-ink-700 rounded-2xl p-6 max-w-md w-full space-y-4 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <h3 className="font-semibold text-ink-50">Share results</h3>
          <button onClick={onClose} className="text-ink-500 hover:text-ink-100 text-xl">×</button>
        </div>
        <p className="text-sm text-ink-400">Anyone with this link can view the panel results (no login required).</p>
        <div className="flex items-center gap-2 bg-ink-800 border border-ink-700 rounded-lg px-3 py-2">
          <input
            readOnly
            value={fullUrl}
            onFocus={(e) => e.target.select()}
            className="text-xs text-ink-300 flex-1 min-w-0 bg-transparent outline-none font-mono cursor-text"
          />
          <button
            onClick={copy}
            className={`shrink-0 flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded-lg transition-all whitespace-nowrap ${
              copied
                ? "bg-naija-700/60 text-naija-300 border border-naija-600/50"
                : copyFailed
                ? "bg-red-900/30 text-red-400 border border-red-700/40"
                : "bg-ink-700 hover:bg-ink-600 text-ink-200 border border-ink-600"
            }`}
          >
            {copied
              ? <><CheckCircle2 size={13} className="text-naija-400" /> Copied!</>
              : copyFailed
              ? <>Failed — select &amp; copy</>
              : <><Copy size={13} /> Copy</>}
          </button>
        </div>
        {copyFailed && (
          <p className="text-xs text-ink-600">
            Click the URL to select it, then press Ctrl+C / ⌘C.
          </p>
        )}
      </div>
    </div>
  );
}

export default function RunResults() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [expandedPersona, setExpandedPersona] = useState<PersonaResult | null>(null);
  const [cohortTab, setCohortTab] = useState<"by_zone" | "by_register" | "by_age">("by_zone");
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [sharingLoading, setSharingLoading] = useState(false);
  const [rerunLoading, setRerunLoading] = useState(false);

  const { data: run, error } = useQuery({
    queryKey: ["run", runId],
    queryFn: () => getRun(runId!),
    // Poll every 2s while running for live updates, stop when done
    refetchInterval: (query) => query.state.data?.status === "running" ? 2000 : false,
    enabled: !!runId,
  });

  // Load all 24 panel personas for the grid (public endpoint, no auth)
  const { data: panelPersonas } = useQuery({
    queryKey: ["panel-personas"],
    queryFn: getPanelPersonas,
    staleTime: Infinity,
  });

  async function handleShare() {
    if (!runId) return;
    setSharingLoading(true);
    try {
      const res = await shareRun(runId);
      setShareUrl(res.url);
    } catch (e) {
      console.error(e);
    } finally {
      setSharingLoading(false);
    }
  }

  async function handleRerun() {
    if (!run) return;
    setRerunLoading(true);
    try {
      const res = await rerunProject(run.project_id);
      navigate(`/runs/${res.run_id}`);
    } catch (e) {
      console.error(e);
    } finally {
      setRerunLoading(false);
    }
  }

  if (!run && !error) {
    return (
      <div className="min-h-screen bg-ink-950 flex items-center justify-center">
        <Loader2 size={32} className="text-naija-400 animate-spin" />
      </div>
    );
  }

  if (error || !run) {
    return <DashboardLayout><FailedState /></DashboardLayout>;
  }

  const isRunning = run.status === "running";
  const isFailed = run.status === "failed";
  const isDone = run.status === "completed";
  const agg = run.aggregate;
  const { completed, total } = run.progress ?? { completed: run.results.length, total: 24 };

  // Index results by persona_id for the grid
  const resultByPersonaId = Object.fromEntries(run.results.map((r) => [r.persona_id, r]));

  // Ordered list of all 24 slots — completed ones first, then pending
  const allSlots = panelPersonas ?? [];
  const completedIds = new Set(run.results.map((r) => r.persona_id));
  const orderedSlots = [
    ...allSlots.filter((p) => completedIds.has(p.user_id)),
    ...allSlots.filter((p) => !completedIds.has(p.user_id)),
  ];

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate("/dashboard")} className="text-ink-400 hover:text-ink-100 transition-colors">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-xl font-bold text-ink-50">{run.project_name}</h1>
              <p className="text-xs text-ink-500">
                {new Date(run.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {isDone && (
              <>
                <span className="flex items-center gap-1.5 text-sm text-naija-400">
                  <CheckCircle size={15} /> Complete
                </span>
                <Button size="sm" variant="outline" className="border-ink-700 text-ink-300 hover:border-naija-600" onClick={() => exportCSV(run)}>
                  <Download size={13} className="mr-1.5" /> CSV
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-ink-700 text-ink-300 hover:border-naija-600"
                  onClick={handleShare}
                  disabled={sharingLoading}
                >
                  {sharingLoading ? <Loader2 size={13} className="animate-spin mr-1.5" /> : <Share2 size={13} className="mr-1.5" />}
                  Share
                </Button>
              </>
            )}
            {(isDone || isFailed) && (
              <Button
                size="sm"
                variant="outline"
                className="border-ink-700 text-ink-300 hover:border-naija-600"
                onClick={handleRerun}
                disabled={rerunLoading}
              >
                {rerunLoading ? <Loader2 size={13} className="animate-spin mr-1.5" /> : <RefreshCw size={13} className="mr-1.5" />}
                Run again
              </Button>
            )}
          </div>
        </div>

        {/* Project description card */}
        {run.project_description && (
          <div className="bg-ink-900 border border-ink-800 rounded-xl px-5 py-4 space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              <p className="text-sm font-semibold text-ink-100">{run.project_name}</p>
              {run.project_category && (
                <span className="text-xs px-2 py-0.5 rounded-md bg-ink-800 border border-ink-700 text-ink-400">
                  {run.project_category}
                </span>
              )}
            </div>
            <p className="text-sm text-ink-400 leading-relaxed">{run.project_description}</p>
          </div>
        )}

        {/* Live progress bar (shown while running) */}
        {isRunning && <LiveProgress completed={completed} total={total} projectName={run.project_name} />}

        {/* Failed */}
        {isFailed && <FailedState />}

        {/* Live persona grid — shown while running AND when done */}
        {(isRunning || isDone) && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-ink-400 uppercase tracking-wider">
                {isRunning ? "Live results" : `All ${run.results.length} personas`}
              </h2>
              {isRunning && (
                <span className="text-xs text-ink-500">
                  {completed} done · {total - completed} pending
                </span>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {orderedSlots.length > 0
                ? orderedSlots.map((p) => (
                    <PersonaCard
                      key={p.user_id}
                      personaId={p.user_id}
                      personaName={p.user_id.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      result={resultByPersonaId[p.user_id]}
                      onClick={resultByPersonaId[p.user_id] ? () => setExpandedPersona(resultByPersonaId[p.user_id]) : undefined}
                    />
                  ))
                : // Fallback if panel personas haven't loaded yet
                  run.results.map((r) => (
                    <PersonaCard
                      key={r.id}
                      personaId={r.persona_id}
                      personaName={r.persona_name}
                      result={r}
                      onClick={() => setExpandedPersona(r)}
                    />
                  ))}
            </div>
          </div>
        )}

        {/* Aggregate analytics — only shown when complete */}
        {isDone && agg && (
          <>
            {/* Stat cards */}
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

            {/* Rating dist + Themes */}
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

            {/* Cohort breakdown */}
            <div className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
              <div className="flex border-b border-ink-800">
                {([["by_zone", "By zone"], ["by_register", "By register"], ["by_age", "By age"]] as const).map(([key, label]) => (
                  <button
                    key={key}
                    onClick={() => setCohortTab(key)}
                    className={`px-5 py-3 text-sm font-medium transition-colors ${cohortTab === key ? "text-naija-400 border-b-2 border-naija-500" : "text-ink-400 hover:text-ink-200"}`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="p-4">
                {agg[cohortTab] && Object.keys(agg[cohortTab]).length > 0
                  ? <CohortTable data={agg[cohortTab]} />
                  : <p className="text-sm text-ink-500 py-4 text-center">No data</p>}
              </div>
            </div>
          </>
        )}
      </div>

      {expandedPersona && <ReviewModal result={expandedPersona} onClose={() => setExpandedPersona(null)} />}
      {shareUrl && <ShareModal shareUrl={shareUrl} onClose={() => setShareUrl(null)} />}
    </DashboardLayout>
  );
}
