import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FlaskConical, Sparkles, Target, MessageSquare, History,
  ArrowLeft, Menu, X, ChevronRight, CheckCircle2, AlertCircle,
} from "lucide-react";
import { supabase } from "@/lib/supabase";
import { useEffect } from "react";

type TabKey = "review" | "recommend" | "multiturn" | "experiments";

interface Props {
  tab: TabKey;
  onTabChange: (t: TabKey) => void;
  apiOnline: boolean;
  onClose?: () => void;
}

const TABS: { key: TabKey; label: string; icon: React.ElementType }[] = [
  { key: "review",      label: "Simulate Review",  icon: Sparkles },
  { key: "recommend",   label: "Recommend",         icon: Target },
  { key: "multiturn",   label: "Chat",              icon: MessageSquare },
  { key: "experiments", label: "My Experiments",    icon: History },
];

function SidebarContent({ tab, onTabChange, apiOnline, onClose }: Props) {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUserEmail(session?.user?.email ?? null);
    });
  }, []);

  function go(t: TabKey) { onTabChange(t); onClose?.(); }
  function goBack() { navigate(-1); onClose?.(); }

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5">
        <div className="w-8 h-8 rounded-lg bg-violet-700 flex items-center justify-center shrink-0">
          <FlaskConical size={15} className="text-white" />
        </div>
        <div className="min-w-0">
          <p className="font-bold text-ink-50 text-sm leading-none">Labz</p>
          <p className="text-[10px] text-ink-600 mt-0.5">developer console</p>
        </div>
        {/* API status dot */}
        <div className="ml-auto shrink-0">
          <span title={apiOnline ? "API connected" : "API offline"}>
            {apiOnline
              ? <CheckCircle2 size={13} className="text-naija-400" />
              : <AlertCircle size={13} className="text-amber-400" />}
          </span>
        </div>
      </div>

      <div className="border-t border-ink-800 mx-3" />

      {/* Tab nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        <p className="text-xs font-semibold text-ink-600 uppercase tracking-wider px-3 mb-3">
          Console
        </p>
        {TABS.map(({ key, label, icon: Icon }) => {
          const active = tab === key;
          return (
            <button
              key={key}
              onClick={() => go(key)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                active
                  ? "bg-violet-900/40 border border-violet-700/50 text-violet-300"
                  : "text-ink-400 hover:text-ink-100 hover:bg-ink-800/60"
              }`}
            >
              <Icon size={15} className="shrink-0" />
              {label}
              {active && <ChevronRight size={12} className="ml-auto text-ink-600" />}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-ink-800 mx-3 mb-1" />
      <div className="px-3 py-3 space-y-1">
        {userEmail && (
          <p className="text-xs text-ink-600 px-3 truncate mb-2">{userEmail}</p>
        )}
        <button
          onClick={goBack}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-ink-500 hover:text-ink-200 hover:bg-ink-800/50 transition-all"
        >
          <ArrowLeft size={15} className="shrink-0" />
          Back
        </button>
      </div>
    </div>
  );
}

// Desktop (fixed 220px)
export function LabSidebar(props: Props) {
  return (
    <aside className="hidden md:flex flex-col w-[220px] shrink-0 bg-ink-950 border-r border-ink-800 min-h-screen sticky top-0 h-screen">
      <SidebarContent {...props} />
    </aside>
  );
}

// Mobile: top bar + slide-in drawer
export function LabMobileNav(props: Props) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-ink-800 bg-ink-950 sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-violet-700 flex items-center justify-center">
            <FlaskConical size={13} className="text-white" />
          </div>
          <span className="font-bold text-ink-50 text-sm">Labz</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-ink-400 hover:text-ink-100 hover:bg-ink-800 transition-colors"
        >
          <Menu size={20} />
        </button>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm md:hidden" onClick={() => setOpen(false)}>
          <div className="absolute left-0 top-0 bottom-0 w-64 bg-ink-950 border-r border-ink-800" onClick={(e) => e.stopPropagation()}>
            <button onClick={() => setOpen(false)} className="absolute top-4 right-4 text-ink-400 hover:text-ink-100">
              <X size={20} />
            </button>
            <SidebarContent {...props} onClose={() => setOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
