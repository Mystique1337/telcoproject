import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { Moon, Sun } from "lucide-react";
import App from "./App";
import InsideNaija from "./InsideNaija";
import ShopEasy from "./ShopEasy";
import B2B from "./B2B";
import Widget from "./Widget";
import { LanguageGate } from "./LanguageGate";
import "./index.css";

function applyTheme(theme: "light" | "dark") {
  const el = document.documentElement;
  el.classList.toggle("light", theme === "light");
  el.classList.toggle("dark", theme === "dark");
}

// Floating light/dark toggle — present on every surface (not the embed widget).
function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") || "dark",
  );
  useEffect(() => { applyTheme(theme); localStorage.setItem("theme", theme); }, [theme]);
  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      className="fixed bottom-5 right-5 z-50 w-11 h-11 rounded-full bg-ink-900 border border-ink-700 text-ink-200 hover:text-naija-300 hover:border-naija-600 shadow-lg flex items-center justify-center transition-colors"
    >
      {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

// Routing across the products, the B2B layer, the embeddable widget + dev lab.
//   ?widget=1   Widget  — bare embeddable recommendations (for iframes)
//   (default)   InsideNaija — Task A product (synthetic panel)
//   #shopeasy   ShopEasy    — Task B product (search + recommend)
//   #b2b        B2B         — business connect + embed snippet
//   #lab        App         — original multi-tab developer console
function Root() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const on = () => setHash(window.location.hash);
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  // Embeddable widget: query-param routed so it works inside an <iframe>.
  // The embed inherits the host page's look, so no theme toggle there.
  if (new URLSearchParams(window.location.search).has("widget")) return <Widget />;

  let page: React.ReactNode;
  if (hash === "#shopeasy") page = <ShopEasy />;
  else if (hash === "#b2b") page = <B2B />;
  else if (hash === "#lab") {
    page = (
      <LanguageGate storageKey="lab_lang"
                    title="NaijaPersona Lab"
                    subtitle="Pick a default language for the developer console.">
        {() => <App />}
      </LanguageGate>
    );
  } else page = <InsideNaija />;

  return <>{page}<ThemeToggle /></>;
}

// Apply saved theme synchronously before first paint (no flash).
applyTheme((localStorage.getItem("theme") as "light" | "dark") || "dark");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
