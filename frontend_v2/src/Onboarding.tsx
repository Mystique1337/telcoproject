// Passwordless onboarding wizard - builds & stores a persona from a few answers.

import { useState } from "react";
import { ArrowRight, Check, Loader2, MapPin, Sparkles, User, X } from "lucide-react";
import { api } from "./api";
import type { Persona } from "./types";

const INTERESTS = [
  "phones", "electronics", "fashion", "beauty", "home", "kitchen",
  "baby", "groceries", "gaming", "computing", "family",
];
const AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55+"];

export interface ShopProfile { id: string; name: string; persona: Persona; }

export function loadProfile(): { id: string; name: string } | null {
  const id = localStorage.getItem("shop_profile_id");
  const name = localStorage.getItem("shop_profile_name");
  return id ? { id, name: name || "there" } : null;
}

export function Onboarding({ onClose, onDone }:
  { onClose: () => void; onDone: (p: ShopProfile) => void }) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [age, setAge] = useState("");
  const [occupation, setOccupation] = useState("");
  const [interests, setInterests] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const toggle = (i: string) =>
    setInterests((xs) => xs.includes(i) ? xs.filter((x) => x !== i) : [...xs, i]);

  async function finish() {
    setSaving(true); setErr(null);
    try {
      const r = await api.register({
        name: name.trim(), location: location.trim(),
        age_range: age || undefined, occupation: occupation.trim() || undefined,
        interests,
      });
      localStorage.setItem("shop_profile_id", r.profile_id);
      localStorage.setItem("shop_profile_name", name.trim());
      onDone({ id: r.profile_id, name: name.trim(), persona: r.persona });
    } catch (e) { setErr(String(e)); }
    setSaving(false);
  }

  const canNext = step === 0 ? name.trim() && location.trim() : true;

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-ink-900 border border-ink-700 rounded-2xl max-w-md w-full p-6 shadow-2xl relative"
           onClick={(e) => e.stopPropagation()}>
        <button onClick={onClose} className="absolute top-4 right-4 text-ink-400 hover:text-ink-50"><X size={18} /></button>

        {/* progress */}
        <div className="flex gap-1.5 mb-6">
          {[0, 1, 2].map((i) => (
            <div key={i} className={`h-1 flex-1 rounded-full ${i <= step ? "bg-naija-500" : "bg-ink-700"}`} />
          ))}
        </div>

        {step === 0 && (
          <div>
            <div className="w-11 h-11 rounded-xl bg-naija-600/20 border border-naija-700/40 flex items-center justify-center mb-4"><User size={20} className="text-naija-300" /></div>
            <h2 className="text-xl font-bold text-ink-50">Let's set you up</h2>
            <p className="text-sm text-ink-400 mt-1 mb-5">No password needed - we just tailor recommendations to you.</p>
            <label className="text-xs text-ink-400">Your name</label>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Chidi"
                   className="w-full mt-1 mb-3 bg-ink-950 border border-ink-700 focus:border-naija-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" />
            <label className="text-xs text-ink-400 flex items-center gap-1"><MapPin size={12} /> Where do you shop from?</label>
            <input value={location} onChange={(e) => setLocation(e.target.value)} placeholder="e.g. Lagos, Enugu, Kano…"
                   className="w-full mt-1 bg-ink-950 border border-ink-700 focus:border-naija-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" />
          </div>
        )}

        {step === 1 && (
          <div>
            <h2 className="text-xl font-bold text-ink-50">A little about you</h2>
            <p className="text-sm text-ink-400 mt-1 mb-5">Optional - helps us model your taste.</p>
            <label className="text-xs text-ink-400">Age range</label>
            <div className="flex flex-wrap gap-2 mt-1 mb-4">
              {AGE_RANGES.map((a) => (
                <button key={a} onClick={() => setAge(age === a ? "" : a)}
                        className={`text-xs px-3 py-1.5 rounded-lg border ${age === a ? "bg-naija-600 text-white border-naija-600" : "bg-ink-800 text-ink-300 border-ink-700"}`}>{a}</button>
              ))}
            </div>
            <label className="text-xs text-ink-400">Occupation</label>
            <input value={occupation} onChange={(e) => setOccupation(e.target.value)} placeholder="e.g. teacher, trader, developer"
                   className="w-full mt-1 bg-ink-950 border border-ink-700 focus:border-naija-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" />
          </div>
        )}

        {step === 2 && (
          <div>
            <div className="w-11 h-11 rounded-xl bg-naija-600/20 border border-naija-700/40 flex items-center justify-center mb-4"><Sparkles size={20} className="text-naija-300" /></div>
            <h2 className="text-xl font-bold text-ink-50">What do you shop for?</h2>
            <p className="text-sm text-ink-400 mt-1 mb-4">Pick a few - we'll prioritise these.</p>
            <div className="flex flex-wrap gap-2">
              {INTERESTS.map((i) => (
                <button key={i} onClick={() => toggle(i)}
                        className={`text-sm px-3 py-1.5 rounded-full border capitalize transition-colors ${interests.includes(i) ? "bg-naija-600 text-white border-naija-600" : "bg-ink-800 text-ink-300 border-ink-700 hover:border-ink-600"}`}>
                  {i}
                </button>
              ))}
            </div>
          </div>
        )}

        {err && <div className="text-xs text-red-300 mt-4">{err}</div>}

        <div className="flex items-center justify-between mt-7">
          <button onClick={() => step > 0 ? setStep(step - 1) : onClose()}
                  className="text-sm text-ink-400 hover:text-ink-200">{step > 0 ? "Back" : "Skip"}</button>
          {step < 2 ? (
            <button onClick={() => canNext && setStep(step + 1)} disabled={!canNext}
                    className="inline-flex items-center gap-2 bg-naija-600 hover:bg-naija-500 disabled:opacity-50 text-white font-semibold rounded-lg px-5 py-2 text-sm transition-colors">
              Next <ArrowRight size={15} />
            </button>
          ) : (
            <button onClick={finish} disabled={saving}
                    className="inline-flex items-center gap-2 bg-naija-600 hover:bg-naija-500 disabled:opacity-50 text-white font-semibold rounded-lg px-5 py-2 text-sm transition-colors">
              {saving ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />} Finish
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
