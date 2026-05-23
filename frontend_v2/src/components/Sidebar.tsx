import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Plus,
  ShoppingBag,
  LogOut,
  History,
  Users,
  Menu,
  X,
  ChevronRight,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import { getDashboardStats } from "@/lib/apiClient";

const NAV_ITEMS = [
  {
    section: "InsideNaija",
    color: "text-naija-400",
    items: [
      { label: "Dashboard", icon: LayoutDashboard, href: "/dashboard" },
      { label: "New project", icon: Plus, href: "/projects/new", accent: true },
      { label: "History", icon: History, href: "/history" },
      { label: "Personas", icon: Users, href: "/personas" },
    ],
  },
  {
    section: "ShopEasy",
    color: "text-amber-400",
    items: [
      { label: "Store", icon: ShoppingBag, href: "/shop" },
    ],
  },
];

function NavItem({
  label,
  icon: Icon,
  href,
  accent,
  active,
  onClick,
}: {
  label: string;
  icon: React.ElementType;
  href: string;
  accent?: boolean;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
        accent
          ? "bg-naija-600 hover:bg-naija-500 text-white"
          : active
          ? "bg-ink-800 text-ink-50"
          : "text-ink-400 hover:text-ink-100 hover:bg-ink-800/60"
      }`}
    >
      <Icon size={16} className="shrink-0" />
      {label}
      {active && !accent && (
        <ChevronRight size={12} className="ml-auto text-ink-600" />
      )}
    </button>
  );
}

function QuotaBar() {
  const session = useAuthStore((s) => s.session);
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
    staleTime: 30000,
    enabled: !!session,
  });

  const quota = stats?.quota;
  if (!quota) return null;

  const pct = quota.limit > 0 ? Math.round((quota.used / quota.limit) * 100) : 0;
  const barColor =
    quota.used >= quota.limit
      ? "bg-red-500"
      : quota.used >= 7
      ? "bg-amber-400"
      : "bg-naija-500";

  return (
    <div className="px-3 pb-1 space-y-1.5">
      <div className="flex items-center justify-between">
        <span className="text-xs text-ink-600">{quota.used} / {quota.limit} runs used</span>
        {quota.remaining === 0 && (
          <span className="text-xs text-red-400 font-medium">Limit reached</span>
        )}
      </div>
      <div className="h-1.5 bg-ink-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const navigate = useNavigate();
  const location = useLocation();
  const session = useAuthStore((s) => s.session);
  const signOut = useAuthStore((s) => s.signOut);

  function go(href: string) {
    navigate(href);
    onNavigate?.();
  }

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <button
        onClick={() => go("/")}
        className="flex items-center gap-2.5 px-4 py-5 group"
      >
        <span className="w-8 h-8 rounded-lg bg-naija-600 flex items-center justify-center text-white text-sm font-bold group-hover:bg-naija-500 transition-colors shrink-0">
          NP
        </span>
        <span className="font-bold text-ink-50 text-sm">Naija Persona</span>
      </button>

      <div className="border-t border-ink-800 mx-3" />

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-5 overflow-y-auto">
        {NAV_ITEMS.map(({ section, color, items }) => (
          <div key={section} className="space-y-1">
            <p className={`text-xs font-semibold uppercase tracking-wider px-3 mb-2 ${color}`}>
              {section}
            </p>
            {items.map((item) => (
              <NavItem
                key={item.href}
                {...item}
                active={location.pathname === item.href}
                onClick={() => go(item.href)}
              />
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-ink-800 mx-3 mb-1" />
      <div className="px-3 py-4 space-y-1">
        {session?.user?.email && (
          <p className="text-xs text-ink-600 px-3 truncate mb-2">
            {session.user.email}
          </p>
        )}
        <QuotaBar />
        <button
          onClick={signOut}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-ink-500 hover:text-red-400 hover:bg-red-900/10 transition-all"
        >
          <LogOut size={15} className="shrink-0" />
          Sign out
        </button>
      </div>
    </div>
  );
}

// Desktop sidebar (fixed, 220px)
export function Sidebar() {
  return (
    <aside className="hidden md:flex flex-col w-[220px] shrink-0 bg-ink-950 border-r border-ink-800 min-h-screen sticky top-0 h-screen">
      <SidebarContent />
    </aside>
  );
}

// Mobile: top bar with slide-in drawer
export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-ink-800 bg-ink-950 sticky top-0 z-40">
        <span className="font-bold text-ink-50 text-sm">Naija Persona</span>
        <button
          onClick={() => setOpen(true)}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-ink-400 hover:text-ink-100 hover:bg-ink-800 transition-colors"
        >
          <Menu size={20} />
        </button>
      </div>

      {/* Drawer overlay */}
      {open && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setOpen(false)}
        >
          <div
            className="absolute left-0 top-0 bottom-0 w-64 bg-ink-950 border-r border-ink-800"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setOpen(false)}
              className="absolute top-4 right-4 text-ink-400 hover:text-ink-100"
            >
              <X size={20} />
            </button>
            <SidebarContent onNavigate={() => setOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
