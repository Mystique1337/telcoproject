import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, Users, Clock, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import DashboardLayout from "@/components/DashboardLayout";
import { listProjects, type ProjectSummary } from "@/lib/apiClient";

const CATEGORY_COLORS: Record<string, string> = {
  fmcg: "text-naija-400 border-naija-700/50 bg-naija-900/20",
  "fashion & beauty": "text-pink-400 border-pink-700/50 bg-pink-900/20",
  fintech: "text-blue-400 border-blue-700/50 bg-blue-900/20",
  "media & entertainment": "text-purple-400 border-purple-700/50 bg-purple-900/20",
  agriculture: "text-lime-400 border-lime-700/50 bg-lime-900/20",
};

function statusIcon(status: string) {
  if (status === "running") return <Loader2 size={14} className="text-amber-400 animate-spin" />;
  if (status === "completed") return <CheckCircle size={14} className="text-naija-400" />;
  return <XCircle size={14} className="text-red-400" />;
}

function statusLabel(status: string) {
  if (status === "running") return "Running…";
  if (status === "completed") return "Complete";
  return "Failed";
}

function categoryColor(cat: string) {
  return CATEGORY_COLORS[cat.toLowerCase()] ?? "text-ink-400 border-ink-700/50 bg-ink-900/20";
}

function ProjectCard({ project }: { project: ProjectSummary }) {
  const navigate = useNavigate();
  const run = project.latest_run;

  return (
    <div
      className="bg-ink-900 border border-ink-800 hover:border-naija-700/50 rounded-xl p-6 space-y-4 cursor-pointer transition-all group"
      onClick={() =>
        run ? navigate(`/runs/${run.id}`) : navigate(`/projects/${project.id}`)
      }
    >
      <div className="flex items-start justify-between">
        <div className="space-y-1 flex-1 min-w-0">
          <h3 className="font-semibold text-ink-50 group-hover:text-naija-300 transition-colors truncate">
            {project.name}
          </h3>
          <p className="text-xs text-ink-500 line-clamp-2">{project.description}</p>
        </div>
        <span
          className={`ml-3 shrink-0 text-xs font-medium px-2 py-0.5 rounded-full border ${categoryColor(project.category)}`}
        >
          {project.category}
        </span>
      </div>

      <div className="flex items-center justify-between pt-2 border-t border-ink-800">
        {run ? (
          <span className="flex items-center gap-1.5 text-xs text-ink-400">
            {statusIcon(run.status)}
            {statusLabel(run.status)}
          </span>
        ) : (
          <span className="text-xs text-ink-600">No runs yet</span>
        )}
        <span className="text-xs text-ink-600">
          {new Date(project.created_at).toLocaleDateString("en-GB", {
            day: "numeric",
            month: "short",
            year: "numeric",
          })}
        </span>
      </div>
    </div>
  );
}

function EmptyState() {
  const navigate = useNavigate();
  return (
    <div className="flex flex-col items-center justify-center py-24 space-y-5 text-center">
      <div className="w-16 h-16 rounded-2xl bg-naija-900/30 border border-naija-700/30 flex items-center justify-center">
        <Users size={28} className="text-naija-400" />
      </div>
      <div className="space-y-2">
        <h3 className="text-xl font-semibold text-ink-100">No projects yet</h3>
        <p className="text-sm text-ink-400 max-w-sm">
          Create your first research project and run it through 24 Nigerian consumer personas in under 2 minutes.
        </p>
      </div>
      <Button
        className="bg-naija-600 hover:bg-naija-700 text-white"
        onClick={() => navigate("/projects/new")}
      >
        <Plus size={16} className="mr-2" />
        Run your first panel
      </Button>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: projects, isLoading, error } = useQuery({
    queryKey: ["projects"],
    queryFn: listProjects,
    refetchInterval: 8000, // refresh so running panels update
  });

  return (
    <DashboardLayout>
      <div className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink-50">InsideNaija</h1>
            <p className="text-sm text-ink-400 mt-0.5">Your research projects</p>
          </div>
          <Button
            className="bg-naija-600 hover:bg-naija-700 text-white"
            onClick={() => navigate("/projects/new")}
          >
            <Plus size={16} className="mr-2" />
            New project
          </Button>
        </div>

        {/* Stats bar */}
        {projects && projects.length > 0 && (
          <div className="grid grid-cols-3 gap-4">
            {[
              {
                label: "Total projects",
                value: projects.length,
                icon: Users,
              },
              {
                label: "Completed runs",
                value: projects.filter((p) => p.latest_run?.status === "completed").length,
                icon: CheckCircle,
              },
              {
                label: "Running now",
                value: projects.filter((p) => p.latest_run?.status === "running").length,
                icon: Clock,
              },
            ].map(({ label, value, icon: Icon }) => (
              <div
                key={label}
                className="bg-ink-900 border border-ink-800 rounded-xl px-5 py-4 flex items-center gap-3"
              >
                <Icon size={18} className="text-naija-400 shrink-0" />
                <div>
                  <p className="text-xl font-bold text-ink-50">{value}</p>
                  <p className="text-xs text-ink-500">{label}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Content */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={28} className="text-naija-400 animate-spin" />
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-center">
            <p className="text-red-400 text-sm">Failed to load projects. Try refreshing.</p>
          </div>
        )}

        {!isLoading && !error && projects?.length === 0 && <EmptyState />}

        {!isLoading && !error && projects && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {projects.map((p) => (
              <ProjectCard key={p.id} project={p} />
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
