import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Moon, Sun } from "lucide-react";

import { supabase } from "@/lib/supabase";
import { useAuthStore } from "@/store/auth";
import ProtectedRoute from "@/components/ProtectedRoute";

import Login from "@/pages/auth/Login";
import Signup from "@/pages/auth/Signup";
import Landing from "@/pages/Landing";
import InsideNaijaPage from "@/pages/products/InsideNaijaPage";
import ShopEasyPage from "@/pages/products/ShopEasyPage";
import Dashboard from "@/pages/dashboard/Dashboard";
import NewProject from "@/pages/dashboard/NewProject";
import RunResults from "@/pages/dashboard/RunResults";
import History from "@/pages/dashboard/History";
import Personas from "@/pages/dashboard/Personas";

// Existing product components (preserved from v1)
import InsideNaija from "./InsideNaija";
import ShopEasy from "./ShopEasy";
import B2B from "./B2B";
import Widget from "./Widget";
import { LanguageGate } from "./LanguageGate";
import App from "./App";

import "./index.css";

const queryClient = new QueryClient();

function applyTheme(theme: "light" | "dark") {
  document.documentElement.classList.toggle("light", theme === "light");
  document.documentElement.classList.toggle("dark", theme === "dark");
}

function ThemeToggle() {
  const [theme, setTheme] = useState<"light" | "dark">(
    () => (localStorage.getItem("theme") as "light" | "dark") || "dark",
  );
  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem("theme", theme);
  }, [theme]);
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

// Auth session listener — bootstraps Zustand store on load
function AuthProvider({ children }: { children: React.ReactNode }) {
  const setSession = useAuthStore((s) => s.setSession);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });
    return () => subscription.unsubscribe();
  }, [setSession]);

  return <>{children}</>;
}

function ShopPage() {
  return (
    <ProtectedRoute>
      <ShopEasy />
    </ProtectedRoute>
  );
}

applyTheme((localStorage.getItem("theme") as "light" | "dark") || "dark");

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Public */}
            <Route path="/" element={<Landing />} />
            <Route path="/products/insidenaija" element={<InsideNaijaPage />} />
            <Route path="/products/shopeasy" element={<ShopEasyPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            {/* InsideNaija dashboard */}
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/new"
              element={
                <ProtectedRoute>
                  <NewProject />
                </ProtectedRoute>
              }
            />
            <Route
              path="/runs/:runId"
              element={
                <ProtectedRoute>
                  <RunResults />
                </ProtectedRoute>
              }
            />
            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <History />
                </ProtectedRoute>
              }
            />

            <Route
              path="/personas"
              element={
                <ProtectedRoute>
                  <Personas />
                </ProtectedRoute>
              }
            />

            {/* ShopEasy */}
            <Route path="/shop" element={<ShopPage />} />
            <Route
              path="/b2b"
              element={
                <ProtectedRoute>
                  <B2B />
                </ProtectedRoute>
              }
            />
            <Route
              path="/lab"
              element={
                <ProtectedRoute>
                  <LanguageGate
                    storageKey="lab_lang"
                    title="NaijaPersona Lab"
                    subtitle="Pick a default language for the developer console."
                  >
                    {() => <App />}
                  </LanguageGate>
                </ProtectedRoute>
              }
            />

            {/* Widget (embed, no auth) */}
            <Route path="/widget" element={<Widget />} />

            {/* Default */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
