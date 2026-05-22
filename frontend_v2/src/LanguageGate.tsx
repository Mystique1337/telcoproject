// Language selection gate - shown before the main page (product + labs).
// Stores the choice in localStorage so it's asked once per browser.

import { useEffect, useState } from "react";

export type AppLang = "english" | "pidgin" | "yoruba" | "hausa" | "igbo";

export const LANG_OPTIONS: { id: AppLang; label: string; native: string; greet: string }[] = [
  { id: "english", label: "English", native: "English", greet: "Welcome" },
  { id: "pidgin", label: "Nigerian Pidgin", native: "Pidgin", greet: "How far, oga/madam" },
  { id: "yoruba", label: "Yorùbá", native: "Yorùbá", greet: "Ẹ kú àbọ̀" },
  { id: "hausa", label: "Hausa", native: "Hausa", greet: "Barka da zuwa" },
  { id: "igbo", label: "Igbo", native: "Igbo", greet: "Nnọọ" },
];

export function getStoredLang(key = "app_lang"): AppLang | null {
  const v = localStorage.getItem(key);
  return (v as AppLang) || null;
}

export function LanguageGate({
  children, storageKey = "app_lang", title = "Choose your language",
  subtitle = "Pick how you'd like to shop. You can change it anytime.",
}: {
  children: (lang: AppLang) => React.ReactNode;
  storageKey?: string;
  title?: string;
  subtitle?: string;
}) {
  const [lang, setLang] = useState<AppLang | null>(() => getStoredLang(storageKey));

  useEffect(() => {
    if (lang) localStorage.setItem(storageKey, lang);
  }, [lang, storageKey]);

  if (!lang) {
    return (
      <div className="min-h-screen bg-ink-950 flex items-center justify-center px-6">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[700px] bg-naija-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative max-w-lg w-full text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-naija-500 to-naija-800 flex items-center justify-center text-3xl mb-5">🇳🇬</div>
          <h1 className="text-2xl font-bold text-ink-50">{title}</h1>
          <p className="text-ink-400 text-sm mt-2 mb-7">{subtitle}</p>
          <div className="grid sm:grid-cols-2 gap-3">
            {LANG_OPTIONS.map((o) => (
              <button key={o.id} onClick={() => setLang(o.id)}
                      className="group bg-ink-900/60 hover:bg-ink-800 border border-ink-700 hover:border-naija-600 rounded-xl p-4 text-left transition-all">
                <div className="text-base font-semibold text-ink-100 group-hover:text-naija-300">{o.native}</div>
                <div className="text-xs text-ink-400 mt-0.5">{o.greet} · {o.label}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return <>{children(lang)}</>;
}
