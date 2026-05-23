import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, RadialBarChart, RadialBar, Legend,
} from "recharts";
import {
  Plus, Star, TrendingUp, Users, BarChart3,
  CheckCircle, Loader2, ArrowRight, Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import DashboardLayout from "@/components/DashboardLayout";
import { getDashboardStats, getAnalytics } from "@/lib/apiClient";

// ── Colour palette ────────────────────────────────────────────────────────────

const C = {
  naija:   "#22c55e",
  amber:   "#f59e0b",
  blue:    "#3b82f6",
  purple:  "#a855f7",
  red:     "#ef4444",
  ink700:  "#374151",
  ink600:  "#4b5563",
  ink400:  "#9ca3af",
};

const SENTIMENT_COLORS: Record<string, string> = {
  positive: C.naija,
  neutral:  C.amber,
  negative: C.red,
};

const RATING_COLORS = ["#ef4444", "#f97316", "#f59e0b", "#84cc16", "#22c55e"];

// ── Custom tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-ink-900 border border-ink-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      {label && <p className="text-ink-400 mb-1">{label}</p>}
      {payload.map((p: any) => (
        <p key={p.name} style={{ color: p.color ?? C.naija }}>
          {p.name}: <span className="font-semibold">{
            typeof p.value === "number" ? p.value.toFixed(p.value % 1 === 0 ? 0 : 1) : p.value
          }</span>
        </p>
      ))}
    </div>
  );
}

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({ label, value, icon: Icon, color, sub }: {
  label: string; value: string | number; icon: React.ElementType;
  color: string; sub?: string;
}) {
  return (
    <div className="bg-ink-900 border border-ink-800 rounded-xl px-5 py-4 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-ink-500 font-medium">{label}</p>
        <Icon size={15} className={color} />
      </div>
      <p className="text-2xl font-bold text-ink-50">{value}</p>
      {sub && <p className="text-xs text-ink-600">{sub}</p>}
    </div>
  );
}

// ── Section header ────────────────────────────────────────────────────────────

function SectionHeader({ title, sub }: { title: string; sub?: string }) {
  return (
    <div className="space-y-0.5">
      <h2 className="font-semibold text-ink-100">{title}</h2>
      {sub && <p className="text-xs text-ink-500">{sub}</p>}
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function EmptyAnalytics() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-28 space-y-5 text-center">
      <div className="w-16 h-16 rounded-2xl bg-naija-900/30 border border-naija-700/30 flex items-center justify-center">
        <BarChart3 size={28} className="text-naija-400" />
      </div>
      <div className="space-y-2">
        <h3 className="text-xl font-semibold text-ink-100">No data yet</h3>
        <p className="text-sm text-ink-400 max-w-sm">
          Run your first panel and this dashboard will fill with ratings, sentiment, persona performance, and more.
        </p>
      </div>
      <Button className="bg-naija-600 hover:bg-naija-700 text-white" onClick={() => navigate("/projects/new")}>
        <Plus size={16} className="mr-2" /> Run first panel
      </Button>
    </div>
  );
}

// ── Personas table ────────────────────────────────────────────────────────────

type TopPersona = {
  persona_id: string; persona_name: string; positive_count: number;
  total_reviews: number; positive_rate: number; avg_rating: number;
};

function PersonasTable({ data }: { data: TopPersona[] }) {
  return (
    <div className="divide-y divide-ink-800">
      {data.map((p, i) => (
        <div key={p.persona_id} className="flex items-center gap-3 py-3 px-1">
          <span className="text-xs text-ink-700 w-4 shrink-0">{i + 1}</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-ink-100 truncate">{p.persona_name}</p>
            <p className="text-xs text-ink-600">{p.total_reviews} review{p.total_reviews !== 1 ? "s" : ""}</p>
          </div>
          {/* Positive rate bar */}
          <div className="w-24 hidden sm:block">
            <div className="h-1.5 bg-ink-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-naija-500 rounded-full"
                style={{ width: `${p.positive_rate}%` }}
              />
            </div>
          </div>
          <span className="text-sm font-bold text-naija-400 w-12 text-right shrink-0">
            {p.positive_rate}%
          </span>
          <div className="flex items-center gap-0.5 w-16 justify-end shrink-0">
            <Star size={11} className="text-amber-400 fill-amber-400" />
            <span className="text-xs text-ink-300">{p.avg_rating.toFixed(1)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main dashboard ────────────────────────────────────────────────────────────

export default function Dashboard() {
  const navigate = useNavigate();

  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    refetchInterval: 15000,
  });

  const { data: analytics, isLoading } = useQuery({
    queryKey: ["analytics"],
    queryFn: getAnalytics,
    refetchInterval: 20000,
  });

  const sentimentData = analytics
    ? Object.entries(analytics.sentiment_distribution)
        .filter(([, v]) => v > 0)
        .map(([name, value]) => ({ name, value }))
    : [];

  const ratingData = analytics
    ? [5, 4, 3, 2, 1].map((star) => ({
        star: `${star}★`,
        count: analytics.rating_distribution[String(star)] ?? 0,
      }))
    : [];

  const topProductsData = (analytics?.top_products ?? []).slice(0, 7).map((p) => ({
    name: p.project_name.length > 18 ? p.project_name.slice(0, 16) + "…" : p.project_name,
    rating: p.avg_rating,
    buy: p.buy_likelihood,
  }));

  const categoryData = (analytics?.category_performance ?? []).map((c) => ({
    name: c.category.length > 12 ? c.category.slice(0, 10) + "…" : c.category,
    rating: c.avg_rating,
    buy: c.avg_buy_likelihood,
  }));

  const registerData = (analytics?.register_performance ?? []).map((r) => ({
    name: r.register,
    rating: r.avg_rating,
    buy: r.avg_buy_likelihood,
  }));

  const hasData = (analytics?.total_completed_runs ?? 0) > 0;

  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink-50">Analytics</h1>
            <p className="text-sm text-ink-400 mt-0.5">InsideNaija panel performance</p>
          </div>
          <Button className="bg-naija-600 hover:bg-naija-700 text-white" onClick={() => navigate("/projects/new")}>
            <Plus size={16} className="mr-2" /> New project
          </Button>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          <StatCard label="Projects" value={stats?.total_projects ?? "—"} icon={Users} color="text-naija-400" />
          <StatCard label="Completed runs" value={stats?.completed_runs ?? "—"} icon={CheckCircle} color="text-naija-400" />
          <StatCard label="Running" value={stats?.running_runs ?? "—"} icon={Activity} color="text-amber-400" />
          <StatCard
            label="Avg rating"
            value={stats?.avg_rating != null ? `${stats.avg_rating}/5` : "—"}
            icon={Star}
            color="text-amber-400"
          />
          <StatCard
            label="Personas evaluated"
            value={stats?.total_personas_evaluated != null ? stats.total_personas_evaluated.toLocaleString() : "—"}
            icon={BarChart3}
            color="text-blue-400"
          />
        </div>

        {/* Loading */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="text-naija-400 animate-spin" />
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !hasData && <EmptyAnalytics />}

        {/* Charts */}
        {!isLoading && hasData && analytics && (
          <>
            {/* Row 1: Sentiment + Rating distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Sentiment donut */}
              <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-4">
                <SectionHeader title="Sentiment split" sub={`${analytics.total_reviews} total reviews`} />
                <div className="flex items-center justify-center">
                  <PieChart width={220} height={180}>
                    <Pie
                      data={sentimentData}
                      cx={105}
                      cy={85}
                      innerRadius={52}
                      outerRadius={80}
                      paddingAngle={3}
                      dataKey="value"
                    >
                      {sentimentData.map((entry) => (
                        <Cell key={entry.name} fill={SENTIMENT_COLORS[entry.name] ?? C.ink600} />
                      ))}
                    </Pie>
                    <Tooltip content={<ChartTooltip />} />
                  </PieChart>
                </div>
                <div className="flex justify-center gap-5">
                  {sentimentData.map((s) => (
                    <div key={s.name} className="flex items-center gap-1.5 text-xs">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: SENTIMENT_COLORS[s.name] }} />
                      <span className="text-ink-400 capitalize">{s.name}</span>
                      <span className="font-semibold text-ink-200">{s.value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Rating distribution */}
              <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-4">
                <SectionHeader title="Rating distribution" sub="Across all completed runs" />
                <ResponsiveContainer width="100%" height={175}>
                  <BarChart data={ratingData} barSize={28}>
                    <XAxis dataKey="star" tick={{ fill: C.ink400, fontSize: 12 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: C.ink400, fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar dataKey="count" name="Reviews" radius={[4, 4, 0, 0]}>
                      {ratingData.map((_, i) => (
                        <Cell key={i} fill={RATING_COLORS[i]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Row 2: Top products (full width horizontal bar) */}
            {topProductsData.length > 0 && (
              <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <SectionHeader title="Top rated products" sub="Avg rating per panel run" />
                  <button
                    onClick={() => navigate("/history")}
                    className="flex items-center gap-1 text-xs text-ink-500 hover:text-naija-400 transition-colors"
                  >
                    View all <ArrowRight size={12} />
                  </button>
                </div>
                <ResponsiveContainer width="100%" height={Math.max(topProductsData.length * 44, 140)}>
                  <BarChart data={topProductsData} layout="vertical" barSize={14} barGap={4}>
                    <XAxis type="number" domain={[0, 5]} tick={{ fill: C.ink400, fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis type="category" dataKey="name" width={140} tick={{ fill: C.ink400, fontSize: 12 }} axisLine={false} tickLine={false} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar dataKey="rating" name="Avg rating" fill={C.naija} radius={[0, 4, 4, 0]} />
                    <Bar dataKey="buy" name="Buy %" fill={C.amber} radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex gap-4 justify-end">
                  {[{ color: C.naija, label: "Avg rating (0–5)" }, { color: C.amber, label: "Buy likelihood (%)" }].map(({ color, label }) => (
                    <span key={label} className="flex items-center gap-1.5 text-xs text-ink-500">
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ background: color }} />
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Row 3: Personas + Category performance */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

              {/* Top personas by positive rate */}
              {analytics.top_personas.length > 0 && (
                <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <SectionHeader title="Top personas" sub="By positive review rate" />
                    <button
                      onClick={() => navigate("/personas")}
                      className="flex items-center gap-1 text-xs text-ink-500 hover:text-naija-400 transition-colors"
                    >
                      All personas <ArrowRight size={12} />
                    </button>
                  </div>
                            <PersonasTable data={analytics.top_personas.slice(0, 8)} />
                </div>
              )}

              {/* Category performance */}
              {categoryData.length > 0 && (
                <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-4">
                  <SectionHeader title="Performance by category" sub="Avg rating and buy likelihood" />
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={categoryData} barSize={14} barGap={3}>
                      <XAxis dataKey="name" tick={{ fill: C.ink400, fontSize: 11 }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fill: C.ink400, fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
                      <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                      <Bar dataKey="rating" name="Avg rating" fill={C.naija} radius={[4, 4, 0, 0]} />
                      <Bar dataKey="buy" name="Buy %" fill={C.blue} radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Row 4: Register tier performance */}
            {registerData.length > 0 && (
              <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-4">
                <SectionHeader
                  title="Performance by language register"
                  sub="How ratings and purchase intent vary across Nigerian English, Pidgin, and code-mixed speakers"
                />
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={registerData} barSize={20} barGap={4}>
                    <XAxis dataKey="name" tick={{ fill: C.ink400, fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: C.ink400, fontSize: 11 }} axisLine={false} tickLine={false} width={28} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
                    <Bar dataKey="rating" name="Avg rating" fill={C.purple} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="buy" name="Buy %" fill={C.amber} radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex gap-4 justify-end">
                  {[{ color: C.purple, label: "Avg rating" }, { color: C.amber, label: "Buy %" }].map(({ color, label }) => (
                    <span key={label} className="flex items-center gap-1.5 text-xs text-ink-500">
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ background: color }} />
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
