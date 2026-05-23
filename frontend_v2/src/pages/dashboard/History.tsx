import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { CheckCircle, XCircle, Loader2, Star, ArrowRight, Clock, RefreshCw, GitCompare } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { listRuns, rerunProject, type RunSummary } from "@/lib/apiClient";

function StatusBadge({ status }: { status: RunSummary["status"] }) {
  if (status === "running")
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-amber-400 bg-amber-900/20 border border-amber-700/40 px-2.5 py-1 rounded-full">
        <Loader2 size={11} className="animate-spin" /> Running
      </span>
    );
  if (status === "completed")
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-medium text-naija-400 bg-naija-900/20 border border-naija-700/40 px-2.5 py-1 rounded-full">
        <CheckCircle size={11} /> Complete
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-red-400 bg-red-900/20 border border-red-700/40 px-2.5 py-1 rounded-full">
      <XCircle size={11} /> Failed
    </span>
  );
}

function MiniStars({ rating }: { rating: number }) {
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star key={i} size={11} className={i <= Math.round(rating) ? "text-amber-400 fill-amber-400" : "text-ink-700"} />
      ))}
      <span className="ml-1 text-xs text-ink-400">{rating.toFixed(1)}</span>
    </span>
  );
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function EmptyHistory() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-24 space-y-4 text-center">
      <div className="w-14 h-14 rounded-2xl bg-ink-900 border border-ink-800 flex items-center justify-center">
        <Clock size={24} className="text-ink-500" />
      </div>
      <div className="space-y-1">
        <h3 className="font-semibold text-ink-200">No runs yet</h3>
        <p className="text-sm text-ink-500">Create a project and run your first panel to see results here.</p>
      </div>
      <button
        onClick={() => navigate("/projects/new")}
        className="text-sm text-naija-400 hover:text-naija-300 flex items-center gap-1 transition-colors"
      >
        Start a panel run <ArrowRight size={14} />
      </button>
    </div>
  );
}

export default function History() {
  const navigate = useNavigate();
  const [compareMode, setCompareMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [rerunningId, setRerunningId] = useState<string | null>(null);

  const { data: runs, isLoading, error } = useQuery({
    queryKey: ["runs-history"],
    queryFn: listRuns,
    refetchInterval: 10000,
  });

  function toggleSelect(id: string) {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : prev.length < 2 ? [...prev, id] : prev
    );
  }

  async function handleRerun(e: React.MouseEvent, projectId: string) {
    e.stopPropagation();
    setRerunningId(projectId);
    try {
      const res = await rerunProject(projectId);
      navigate(`/runs/${res.run_id}`);
    } catch (err) {
      console.error(err);
    } finally {
      setRerunningId(null);
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink-50">History</h1>
            <p className="text-sm text-ink-400 mt-0.5">All panel runs across your projects</p>
          </div>
          <div className="flex items-center gap-2">
            {compareMode && selectedIds.length === 2 && (
              <button
                onClick={() => navigate(`/compare?a=${selectedIds[0]}&b=${selectedIds[1]}`)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-naija-600 hover:bg-naija-500 text-white text-sm font-medium transition-colors"
              >
                <GitCompare size={14} /> Compare
              </button>
            )}
            <button
              onClick={() => { setCompareMode((m) => !m); setSelectedIds([]); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
                compareMode
                  ? "bg-ink-800 border-naija-600 text-naija-300"
                  : "border-ink-700 text-ink-400 hover:text-ink-200 hover:border-ink-600"
              }`}
            >
              <GitCompare size={14} /> {compareMode ? "Cancel" : "Compare"}
            </button>
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="text-naija-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-center">
            <p className="text-red-400 text-sm">Failed to load history.</p>
          </div>
        )}

        {!isLoading && !error && runs?.length === 0 && <EmptyHistory />}

        {!isLoading && !error && runs && runs.length > 0 && (
          <div className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
            {/* Table header */}
            <div className="grid grid-cols-[auto_1fr_auto_auto_auto_auto_auto_auto] items-center gap-4 px-5 py-3 border-b border-ink-800 bg-ink-950/40">
              {(compareMode ? ["", "Project", "Date", "Status", "Avg rating", "Buy %", "", ""] : ["Project", "Date", "Status", "Avg rating", "Buy %", "", ""]).map((h, i) => (
                <span key={i} className="text-xs font-medium text-ink-500 uppercase tracking-wider">
                  {h}
                </span>
              ))}
            </div>

            {/* Rows */}
            <div className="divide-y divide-ink-800">
              {runs.map((run) => (
                <div
                  key={run.id}
                  className={`grid items-center gap-4 px-5 py-4 transition-colors cursor-pointer group ${
                    compareMode
                      ? "grid-cols-[auto_1fr_auto_auto_auto_auto_auto_auto]"
                      : "grid-cols-[1fr_auto_auto_auto_auto_auto_auto]"
                  } ${
                    compareMode && selectedIds.includes(run.id)
                      ? "bg-naija-900/20 hover:bg-naija-900/30"
                      : "hover:bg-ink-800/30"
                  }`}
                  onClick={() => compareMode ? toggleSelect(run.id) : navigate(`/runs/${run.id}`)}
                >
                  {/* Compare checkbox */}
                  {compareMode && (
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(run.id)}
                      onChange={() => toggleSelect(run.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="w-4 h-4 accent-naija-500 cursor-pointer"
                    />
                  )}

                  {/* Project name */}
                  <div className="min-w-0">
                    <p className="font-medium text-ink-100 truncate group-hover:text-naija-300 transition-colors">
                      {run.project_name}
                    </p>
                    <p className="text-xs text-ink-600 mt-0.5">{formatTime(run.created_at)}</p>
                  </div>

                  {/* Date */}
                  <span className="text-sm text-ink-400 whitespace-nowrap">
                    {formatDate(run.created_at)}
                  </span>

                  {/* Status */}
                  <StatusBadge status={run.status} />

                  {/* Avg rating */}
                  <div className="w-28 flex justify-center">
                    {run.avg_rating != null ? (
                      <MiniStars rating={run.avg_rating} />
                    ) : (
                      <span className="text-xs text-ink-700">—</span>
                    )}
                  </div>

                  {/* Buy likelihood */}
                  <div className="w-16 text-center">
                    {run.buy_likelihood != null ? (
                      <span className="text-sm font-semibold text-naija-400">
                        {run.buy_likelihood}%
                      </span>
                    ) : (
                      <span className="text-xs text-ink-700">—</span>
                    )}
                  </div>

                  {/* Rerun icon */}
                  <button
                    onClick={(e) => handleRerun(e, run.project_id)}
                    className="text-ink-600 hover:text-naija-400 transition-colors p-1 rounded"
                    title="Run again"
                    disabled={rerunningId === run.project_id}
                  >
                    {rerunningId === run.project_id
                      ? <Loader2 size={14} className="animate-spin" />
                      : <RefreshCw size={14} />
                    }
                  </button>

                  {/* Arrow */}
                  <ArrowRight size={15} className="text-ink-700 group-hover:text-naija-400 transition-colors" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
