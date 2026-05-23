import { useState } from "react";
import { useAuthStore } from "@/store/auth";
import { loadProfile } from "@/Onboarding";
import ShopEasy from "@/ShopEasy";
import ShopEasySetupModal from "@/components/ShopEasySetupModal";

export default function ShopGate() {
  const session = useAuthStore((s) => s.session);

  // profileReady: true if localStorage already has a ShopEasy profile
  const [profileReady, setProfileReady] = useState(() => !!loadProfile());

  // Show the setup popup only when the user is signed into InsideNaija
  // via Supabase but hasn't set up a ShopEasy persona yet
  const needsSetup = !!session && !profileReady;

  const displayName =
    session?.user?.user_metadata?.full_name ||
    session?.user?.email?.split("@")[0] ||
    "there";

  if (needsSetup) {
    return (
      <ShopEasySetupModal
        userName={displayName}
        onComplete={() => setProfileReady(true)}
        onSkip={() => setProfileReady(true)}
      />
    );
  }

  return <ShopEasy />;
}
