/**
 * LabGate — smart entry point for /lab
 *
 * Signed in to either product (Supabase session exists):
 *   - Fetch language_preference from DB persona
 *   - Pre-set lab_lang in localStorage so App picks it up
 *   - Skip LanguageGate entirely → straight into the Lab
 *
 * Not signed in (or session not found):
 *   - Existing public flow: LanguageGate → pick language → Lab
 *
 * Why we don't use useAuthStore here:
 *   The Zustand store starts as null and is populated asynchronously by
 *   AuthProvider's useEffect — so on the first render, session is always
 *   null even for logged-in users. We check Supabase directly instead.
 */
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { getShopPersona } from "@/lib/apiClient";
import { LanguageGate } from "@/LanguageGate";
import App from "@/App";

export default function LabGate() {
  // Never start ready — always wait for the async session check
  const [ready, setReady] = useState(false);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) {
        // No session — show public LanguageGate flow
        setReady(true);
        return;
      }

      // Session exists — fetch language from DB persona
      setSignedIn(true);
      getShopPersona()
        .then((persona) => {
          if (persona.language) {
            localStorage.setItem("lab_lang", persona.language);
          }
        })
        .catch(() => {
          // No persona yet — fine, proceed without pre-setting language
        })
        .finally(() => setReady(true));
    });
  }, []);

  if (!ready) {
    return (
      <div className="min-h-screen bg-ink-950 flex items-center justify-center">
        <Loader2 size={24} className="text-ink-500 animate-spin" />
      </div>
    );
  }

  // Signed in → skip LanguageGate
  if (signedIn) return <App />;

  // Not signed in → public flow
  return (
    <LanguageGate
      storageKey="lab_lang"
      title="NaijaPersona Labz"
      subtitle="Pick a language for the developer console."
    >
      {() => <App />}
    </LanguageGate>
  );
}
