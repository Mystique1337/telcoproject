import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ShoppingBag, Heart, Package, User, Smartphone, Shirt,
  Sparkles, ShoppingBasket, HomeIcon, Gamepad2, LogIn,
  LogOut, Menu, X, ChevronRight, FlaskConical,
} from "lucide-react";

export type ShopView = "home" | "store" | "orders" | "wishlist" | "profile";

interface ShopPersonaInfo {
  display_name?: string;
  language?: string;
  location?: string;
}

interface Profile {
  id: string;
  name: string;
}

interface Props {
  view: ShopView;
  onNav: (v: ShopView) => void;
  onCategorySelect: (query: string) => void;
  profile: Profile | null;
  shopPersona: ShopPersonaInfo | null;
  wishlistCount: number;
  onSignIn: () => void;
  onSignOut: () => void;
  onClose?: () => void;
}

function personaAvatar(seed: string) {
  return `https://api.dicebear.com/9.x/personas/svg?seed=${encodeURIComponent(seed)}&backgroundType=gradientLinear`;
}

const CATEGORIES = [
  { label: "Phones",    icon: Smartphone,     query: "phones smartphones" },
  { label: "Fashion",   icon: Shirt,          query: "fashion clothing" },
  { label: "Beauty",    icon: Sparkles,       query: "beauty cosmetics" },
  { label: "Food",      icon: ShoppingBasket, query: "food groceries supermarket" },
  { label: "Home",      icon: HomeIcon,       query: "home appliances" },
  { label: "Gaming",    icon: Gamepad2,       query: "gaming" },
];

function NavItem({ label, icon: Icon, active, badge, onClick }: {
  label: string; icon: React.ElementType; active: boolean;
  badge?: number; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
        active
          ? "bg-amber-900/40 border border-amber-700/50 text-amber-300"
          : "text-ink-400 hover:text-ink-100 hover:bg-ink-800/60"
      }`}
    >
      <Icon size={16} className="shrink-0" />
      {label}
      {badge != null && badge > 0 && (
        <span className="ml-auto bg-amber-600 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center shrink-0">
          {badge > 9 ? "9+" : badge}
        </span>
      )}
      {active && !badge && <ChevronRight size={12} className="ml-auto text-ink-600" />}
    </button>
  );
}

function SidebarContent({ view, onNav, onCategorySelect, profile, shopPersona, wishlistCount, onSignIn, onSignOut, onClose }: Props) {
  const navigate = useNavigate();
  function go(v: ShopView) { onNav(v); onClose?.(); }
  function cat(q: string) { onCategorySelect(q); onClose?.(); }

  const displayName = shopPersona?.display_name || profile?.name || "Guest";
  const location = shopPersona?.location;
  const language = shopPersona?.language;

  return (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5">
        <div className="w-8 h-8 rounded-lg bg-amber-600 flex items-center justify-center shrink-0">
          <ShoppingBag size={15} className="text-white" />
        </div>
        <span className="font-bold text-ink-50 text-sm">ShopEasy</span>
      </div>

      <div className="border-t border-ink-800 mx-3" />

      {/* User card */}
      {(profile || shopPersona) ? (
        <div className="mx-3 mt-3 mb-1 bg-ink-900 border border-ink-800 rounded-xl p-3 space-y-1.5">
          <div className="flex items-center gap-2.5">
            <img
              src={personaAvatar(profile?.id || displayName)}
              alt=""
              className="w-8 h-8 rounded-full shrink-0"
            />
            <div className="min-w-0">
              <p className="text-sm font-medium text-ink-100 truncate">{displayName}</p>
              {(location || language) && (
                <p className="text-xs text-ink-500 truncate">
                  {[location, language].filter(Boolean).join(" · ")}
                </p>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="mx-3 mt-3 mb-1">
          <button
            onClick={() => { onSignIn(); onClose?.(); }}
            className="w-full flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium rounded-xl py-2.5 transition-colors"
          >
            <LogIn size={14} /> Sign in
          </button>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
        <NavItem label="Browse"     icon={ShoppingBag} active={view === "store"}   onClick={() => go("store")} />
        <NavItem label="Wishlist"   icon={Heart}       active={view === "wishlist"} onClick={() => go("wishlist")} badge={wishlistCount} />
        {profile || shopPersona ? (
          <NavItem label="Orders"   icon={Package}     active={view === "orders"}  onClick={() => go("orders")} />
        ) : null}
        {profile || shopPersona ? (
          <NavItem label="My Profile" icon={User}      active={view === "profile"} onClick={() => go("profile")} />
        ) : null}

        {/* Categories */}
        <div className="pt-3">
          <p className="text-xs font-semibold text-ink-600 uppercase tracking-wider px-3 mb-2">Categories</p>
          {CATEGORIES.map(({ label, icon: Icon, query }) => (
            <button
              key={label}
              onClick={() => cat(query)}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-ink-400 hover:text-ink-100 hover:bg-ink-800/60 transition-colors"
            >
              <Icon size={14} className="shrink-0 text-amber-600/70" />
              {label}
            </button>
          ))}
        </div>
      </nav>

      {/* Labz */}
      <div className="px-3 pb-2">
        <button
          onClick={() => { onClose?.(); navigate("/lab"); }}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium border border-ink-600 bg-ink-800/40 text-ink-400 hover:text-ink-200 hover:bg-ink-700/60 hover:border-ink-500 transition-all"
        >
          <FlaskConical size={15} className="shrink-0" />
          Labz
        </button>
      </div>

      {/* Footer */}
      <div className="border-t border-ink-800 mx-3 mb-1" />
      <div className="px-3 py-3">
        {profile || shopPersona ? (
          <button
            onClick={() => { onSignOut(); onClose?.(); }}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-ink-500 hover:text-red-400 hover:bg-red-900/10 transition-all"
          >
            <LogOut size={15} className="shrink-0" />
            Sign out
          </button>
        ) : null}
      </div>
    </div>
  );
}

// ── Desktop sidebar ───────────────────────────────────────────────────────────
export function ShopSidebar(props: Props) {
  return (
    <aside className="hidden md:flex flex-col w-[220px] shrink-0 bg-ink-950 border-r border-ink-800 min-h-screen sticky top-0 h-screen">
      <SidebarContent {...props} />
    </aside>
  );
}

// ── Mobile: top bar + drawer ──────────────────────────────────────────────────
export function ShopMobileNav(props: Props) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className="md:hidden flex items-center justify-between px-4 py-3 border-b border-ink-800 bg-ink-950 sticky top-0 z-40">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-amber-600 flex items-center justify-center">
            <ShoppingBag size={13} className="text-white" />
          </div>
          <span className="font-bold text-ink-50 text-sm">ShopEasy</span>
        </div>
        <button
          onClick={() => setOpen(true)}
          className="w-9 h-9 flex items-center justify-center rounded-lg text-ink-400 hover:text-ink-100 hover:bg-ink-800 transition-colors"
        >
          <Menu size={20} />
        </button>
      </div>

      {open && (
        <div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setOpen(false)}
        >
          <div
            className="absolute left-0 top-0 bottom-0 w-64 bg-ink-950 border-r border-ink-800"
            onClick={(e) => e.stopPropagation()}
          >
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
