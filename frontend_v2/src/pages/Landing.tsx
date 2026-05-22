import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";

import InsideNaija from "@/InsideNaija";
import ShopEasy from "@/ShopEasy";
import B2B from "@/B2B";
import { LanguageGate } from "@/LanguageGate";
import App from "@/App";

type Tab = "insidenaija" | "shopeasy" | "b2b" | "lab";

const TABS: { id: Tab; label: string }[] = [
  { id: "insidenaija", label: "InsideNaija" },
  { id: "shopeasy", label: "ShopEasy" },
  { id: "b2b", label: "B2B" },
  { id: "lab", label: "Lab" },
];

function applyTheme(theme: "light" | "dark") {
  document.documentElement.classList.toggle("light", theme === "light");
  document.documentElement.classList.toggle("dark", theme === "dark");
}

export default function Landing() {
  const navigate = useNavigate();
  const session = useAuthStore((s) => s.session);
  const signOut = useAuthStore((s) => s.signOut);

  const [tab, setTab] = useState<Tab>("insidenaija");
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") || "dark",
  );

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <div className="min-h-screen bg-ink-950 text-ink-50 flex flex-col">

      {/* Nav */}
      <nav className="border-b border-ink-800 px-6 py-3 flex items-center justify-between sticky top-0 z-50 bg-ink-950/95 backdrop-blur">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-md bg-naija-600 flex items-center justify-center text-white text-xs font-bold">
            NP
          </span>
          <span className="font-bold text-ink-50">Naija Persona</span>
        </div>

        {/* Tab switcher */}
        <div className="hidden sm:flex items-center gap-1 bg-ink-900 border border-ink-800 rounded-lg p-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                tab === t.id
                  ? "bg-naija-600 text-white"
                  : "text-ink-400 hover:text-ink-100"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="w-9 h-9 rounded-full border border-ink-700 text-ink-400 hover:text-ink-100 flex items-center justify-center transition-colors"
          >
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>

          {session ? (
            <>
              <Button
                size="sm"
                className="bg-naija-600 hover:bg-naija-700 text-white"
                onClick={() => navigate("/dashboard")}
              >
                Dashboard
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="text-ink-400 hover:text-ink-100"
                onClick={signOut}
              >
                Sign out
              </Button>
            </>
          ) : (
            <>
              <Button
                size="sm"
                variant="ghost"
                className="text-ink-300 hover:text-ink-50"
                onClick={() => navigate("/login")}
              >
                Sign in
              </Button>
              <Button
                size="sm"
                className="bg-naija-600 hover:bg-naija-700 text-white"
                onClick={() => navigate("/signup")}
              >
                Get started
                <ArrowRight size={14} className="ml-1" />
              </Button>
            </>
          )}
        </div>
      </nav>

      {/* Mobile tab switcher */}
      <div className="sm:hidden flex items-center gap-1 bg-ink-900 border-b border-ink-800 px-4 py-2 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
              tab === t.id
                ? "bg-naija-600 text-white"
                : "text-ink-400 hover:text-ink-100"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Product area */}
      <div className="flex-1">
        {tab === "insidenaija" && <InsideNaija />}
        {tab === "shopeasy" && <ShopEasy />}
        {tab === "b2b" && <B2B />}
        {tab === "lab" && (
          <LanguageGate
            storageKey="lab_lang"
            title="NaijaPersona Lab"
            subtitle="Pick a default language for the developer console."
          >
            {() => <App />}
          </LanguageGate>
        )}
      </div>

      {/* Save-work banner — only shown to logged-out users */}
      {!session && (
        <div className="border-t border-ink-800 bg-ink-900 px-6 py-3 flex items-center justify-between">
          <p className="text-sm text-ink-400">
            <span className="text-ink-200 font-medium">Like what you see?</span>
            {" "}Sign up to save projects, track history and export reports.
          </p>
          <Button
            size="sm"
            className="bg-naija-600 hover:bg-naija-700 text-white shrink-0 ml-4"
            onClick={() => navigate("/signup")}
          >
            Sign up free
          </Button>
        </div>
      )}
    </div>
  );
}
