import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { useAuthStore } from "@/store/auth";
import { getShopPersona } from "@/lib/apiClient";
import ShopEasy from "@/ShopEasy";
import ShopEasySetupModal from "@/components/ShopEasySetupModal";

type State = "loading" | "needs-setup" | "ready";

/**
 * DB-backed gate for the ShopEasy store.
 *
 * Source of truth: PostgreSQL `personas` table.
 * Runtime cache:   localStorage (so the ShopEasy component can read it).
 *
 * Flow:
 *  1. Signed in (Supabase) → fetch persona from DB
 *     - Found   → hydrate localStorage, show store
 *     - Not found → show setup popup (saves to DB, then hydrates localStorage)
 *  2. Not signed in → show store directly (anonymous / existing localStorage flow)
 */
export default function ShopGate() {
  const session = useAuthStore((s) => s.session);
  const [state, setState] = useState<State>(session ? "loading" : "ready");

  const displayName =
    session?.user?.user_metadata?.full_name ||
    session?.user?.email?.split("@")[0] ||
    "there";

  // Hydrate localStorage from a persona object so ShopEasy.tsx can use it
  function hydrate(name: string) {
    // ShopEasy.tsx reads shop_profile_id and shop_profile_name from localStorage.
    // We store the Supabase user ID as the profile identifier so it's stable.
    localStorage.setItem("shop_profile_id", session?.user?.id ?? "guest");
    localStorage.setItem("shop_profile_name", name);
  }

  useEffect(() => {
    if (!session) { setState("ready"); return; }

    getShopPersona()
      .then((persona) => {
        hydrate(persona.display_name);
        setState("ready");
      })
      .catch(() => {
        // 404 → user hasn't set up ShopEasy yet
        setState("needs-setup");
      });
  }, [session?.user?.id]);

  if (state === "loading") {
    return (
      <div className="min-h-screen bg-ink-950 flex items-center justify-center">
        <Loader2 size={28} className="text-amber-400 animate-spin" />
      </div>
    );
  }

  if (state === "needs-setup") {
    return (
      <ShopEasySetupModal
        userName={displayName}
        onComplete={(persona) => {
          hydrate(persona.display_name);
          setState("ready");
        }}
        onSkip={() => setState("ready")}
      />
    );
  }

  return <ShopEasy />;
}
