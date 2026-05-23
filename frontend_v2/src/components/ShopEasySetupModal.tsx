import { useState } from "react";
import { Loader2, MapPin, ShoppingCart, ChevronDown } from "lucide-react";
import { api } from "@/api";

const LANGUAGES = [
  { value: "english", label: "English" },
  { value: "pidgin",  label: "Pidgin" },
  { value: "yoruba",  label: "Yorùbá" },
  { value: "hausa",   label: "Hausa" },
  { value: "igbo",    label: "Igbo" },
];

const CITIES = [
  "Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt",
  "Benin City", "Kaduna", "Enugu", "Onitsha", "Warri",
  "Calabar", "Uyo", "Jos", "Ilorin", "Owerri",
  "Aba", "Abeokuta", "Maiduguri", "Sokoto", "Zaria",
];

interface Props {
  userName: string;
  onComplete: () => void;
  onSkip: () => void;
}

export default function ShopEasySetupModal({ userName, onComplete, onSkip }: Props) {
  const [language, setLanguage] = useState("english");
  const [location, setLocation] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function handleStart() {
    if (!location.trim()) { setError("Please enter your city or state."); return; }
    setSaving(true); setError("");
    try {
      const r = await api.register({
        name: userName,
        location: location.trim(),
        language,
        interests: [],
      });
      localStorage.setItem("shop_profile_id", r.profile_id);
      localStorage.setItem("shop_profile_name", userName);
      onComplete();
    } catch {
      setError("Something went wrong. Try again.");
      setSaving(false);
    }
  }

  return (
    <div className="min-h-screen bg-ink-950 flex items-center justify-center p-4 relative overflow-hidden">
      {/* Amber glow background */}
      <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-amber-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 right-1/4 w-[400px] h-[400px] bg-amber-500/6 rounded-full blur-3xl pointer-events-none" />

      <div className="relative bg-ink-900 border border-amber-700/30 rounded-2xl max-w-md w-full p-8 shadow-2xl space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-600 flex items-center justify-center shrink-0">
            <ShoppingCart size={18} className="text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-ink-50">Welcome to ShopEasy</h2>
            <p className="text-xs text-ink-500">Powered by Naija Persona</p>
          </div>
        </div>

        {/* Welcome message */}
        <p className="text-sm text-ink-300 leading-relaxed">
          Hey <span className="text-amber-300 font-medium">{userName}</span>! You're already signed in.
          Two quick things so we can personalise your shopping experience.
        </p>

        {/* Language */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-ink-200">Your preferred language</label>
          <div className="relative">
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={saving}
              className="w-full appearance-none rounded-xl border border-ink-700 bg-ink-950 px-4 py-3 pr-10 text-sm text-ink-50 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:border-transparent disabled:opacity-50"
            >
              {LANGUAGES.map((l) => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-500 pointer-events-none" />
          </div>
        </div>

        {/* Location */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-ink-200">
            <MapPin size={13} className="inline mr-1 text-amber-400" />
            Your city or state
          </label>
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleStart()}
            placeholder="e.g. Lagos, Kano, Abuja…"
            disabled={saving}
            list="cities"
            className="w-full rounded-xl border border-ink-700 bg-ink-950 px-4 py-3 text-sm text-ink-50 placeholder:text-ink-600 focus:outline-none focus:ring-2 focus:ring-amber-600 focus:border-transparent disabled:opacity-50"
          />
          <datalist id="cities">
            {CITIES.map((c) => <option key={c} value={c} />)}
          </datalist>
        </div>

        {error && (
          <p className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-2">
            {error}
          </p>
        )}

        {/* CTA */}
        <button
          onClick={handleStart}
          disabled={saving || !location.trim()}
          className="w-full flex items-center justify-center gap-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl py-3 text-sm transition-colors"
        >
          {saving
            ? <><Loader2 size={16} className="animate-spin" /> Setting up…</>
            : <>Start shopping →</>}
        </button>

        <button
          onClick={onSkip}
          className="w-full text-center text-xs text-ink-600 hover:text-ink-400 transition-colors py-1"
        >
          Skip for now — browse without personalisation
        </button>
      </div>
    </div>
  );
}
