import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Moon, Sun, ChevronDown, ArrowRight, FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";

function applyTheme(theme: "light" | "dark") {
  document.documentElement.classList.toggle("light", theme === "light");
  document.documentElement.classList.toggle("dark", theme === "dark");
}

const PRODUCTS = [
  {
    id: "insidenaija",
    href: "/products/insidenaija",
    name: "InsideNaija",
    tagline: "Synthetic Nigerian consumer research panel",
    desc: "Run any product through 24 culturally-grounded Nigerian personas and get structured feedback in minutes.",
    badge: "B2B",
    color: "text-naija-400",
    bg: "bg-naija-900/40",
  },
  {
    id: "shopeasy",
    href: "/products/shopeasy",
    name: "ShopEasy",
    tagline: "Persona-aware Nigerian storefront",
    desc: "AI-powered product recommendations tuned to Nigerian shopping behaviour, language, and culture.",
    badge: "B2C",
    color: "text-amber-400",
    bg: "bg-amber-900/30",
  },
];

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const session = useAuthStore((s) => s.session);
  const signOut = useAuthStore((s) => s.signOut);

  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") || "dark",
  );
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Close on route change
  useEffect(() => { setDropdownOpen(false); }, [location.pathname]);

  return (
    <nav className="border-b border-ink-800 px-6 py-3 flex items-center justify-between sticky top-0 z-50 bg-ink-950/95 backdrop-blur">
      {/* Logo */}
      <button
        onClick={() => navigate("/")}
        className="flex items-center gap-2 group"
      >
        <span className="w-8 h-8 rounded-lg bg-naija-600 flex items-center justify-center text-white text-sm font-bold group-hover:bg-naija-500 transition-colors">
          NP
        </span>
        <span className="font-bold text-ink-50 hidden sm:block">Naija Persona</span>
      </button>

      {/* Centre nav */}
      <div className="flex items-center gap-1">
        {/* Products dropdown */}
        <div ref={dropdownRef} className="relative">
          <button
            onMouseEnter={() => setDropdownOpen(true)}
            onClick={() => setDropdownOpen((o) => !o)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              dropdownOpen ? "bg-ink-800 text-ink-50" : "text-ink-300 hover:text-ink-50 hover:bg-ink-800/50"
            }`}
          >
            Products
            <ChevronDown
              size={14}
              className={`transition-transform duration-200 ${dropdownOpen ? "rotate-180" : ""}`}
            />
          </button>

          {dropdownOpen && (
            <div
              onMouseLeave={() => setDropdownOpen(false)}
              className="absolute top-full left-0 mt-2 w-[480px] bg-ink-900 border border-ink-700 rounded-2xl shadow-2xl p-2 animate-in fade-in slide-in-from-top-2 duration-150"
            >
              {PRODUCTS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => navigate(p.href)}
                  className="w-full text-left p-4 rounded-xl hover:bg-ink-800 transition-colors group flex items-start gap-4"
                >
                  <div className={`w-10 h-10 rounded-lg ${p.bg} flex items-center justify-center shrink-0 mt-0.5`}>
                    <span className={`text-xs font-bold ${p.color}`}>{p.badge}</span>
                  </div>
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-ink-50 group-hover:text-naija-300 transition-colors">
                        {p.name}
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${p.color} border-current opacity-60`}>
                        {p.badge}
                      </span>
                    </div>
                    <p className="text-xs text-ink-400 font-medium">{p.tagline}</p>
                    <p className="text-xs text-ink-500 leading-relaxed">{p.desc}</p>
                  </div>
                </button>
              ))}

              <div className="border-t border-ink-800 mt-1 pt-1 px-2 pb-1">
                <button
                  onClick={() => navigate("/business")}
                  className="w-full text-left px-3 py-2.5 rounded-lg text-sm text-ink-400 hover:text-ink-100 hover:bg-ink-800 transition-colors flex items-center justify-between"
                >
                  <span>For Business — integrations, API, white-label</span>
                  <ArrowRight size={14} />
                </button>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={() => navigate("/business")}
          className="px-4 py-2 rounded-lg text-sm font-medium text-ink-300 hover:text-ink-50 hover:bg-ink-800/50 transition-colors"
        >
          For Business
        </button>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="w-9 h-9 rounded-full border border-ink-700 text-ink-400 hover:text-ink-100 flex items-center justify-center transition-colors"
        >
          {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        {/* Labz — ash tint, always visible */}
        <Button
          size="sm"
          variant="outline"
          className="border-ink-600 bg-ink-800/50 text-ink-400 hover:bg-ink-700 hover:text-ink-200 hover:border-ink-500"
          onClick={() => navigate("/lab")}
        >
          <FlaskConical size={13} className="mr-1" /> Labz
        </Button>

        {session ? (
          <>
            <Button size="sm" className="bg-naija-600 hover:bg-naija-700 text-white"
              onClick={() => navigate("/dashboard")}>
              Dashboard
            </Button>
            <Button size="sm" variant="ghost" className="text-ink-400 hover:text-ink-100"
              onClick={signOut}>
              Sign out
            </Button>
          </>
        ) : (
          <>
            <Button size="sm" variant="ghost" className="text-ink-300 hover:text-ink-50"
              onClick={() => navigate("/login")}>
              Sign in
            </Button>
            <Button size="sm" className="bg-naija-600 hover:bg-naija-700 text-white"
              onClick={() => navigate("/signup")}>
              Get started <ArrowRight size={13} className="ml-1" />
            </Button>
          </>
        )}
      </div>
    </nav>
  );
}
