/**
 * LabGate — smart entry point for /lab
 *
 * Signed in:
 *   - Fetch language from DB persona
 *   - Pre-set lab_lang in localStorage so App picks it up
 *   - Skip LanguageGate entirely → straight to Lab
 *
 * Not signed in:
 *   - Existing public flow: LanguageGate → pick language → Lab
 */
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { getShopPersona } from "@/lib/apiClient";
import { LanguageGate } from "@/LanguageGate";
import App from "@/App";

export default function LabGate() {
  const session = useAuthStore((s) => s.session);
  // If no session, we're ready immediately (public flow)
  const [ready, setReady] = useState(!session);

  useEffect(() => {
    if (!session) { setReady(true); return; }

    getShopPersona()
      .then((persona) => {
        if (persona.language) {
          localStorage.setItem("lab_lang", persona.language);
        }
      })
      .catch(() => {
        // No persona set up yet — proceed without pre-setting language
      })
      .finally(() => setReady(true));
  }, [session?.user?.id]);

  if (!ready) {
    return (
      <div className="min-h-screen bg-ink-950 flex items-center justify-center">
        <Loader2 size={24} className="text-ink-500 animate-spin" />
      </div>
    );
  }

  // Signed in → go straight to the lab (language pre-set from DB)
  if (session) return <App />;

  // Not signed in → public LanguageGate flow
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
