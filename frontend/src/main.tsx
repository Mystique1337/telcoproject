import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import InsideNaija from "./InsideNaija";
import ShopEasy from "./ShopEasy";
import B2B from "./B2B";
import Widget from "./Widget";
import { LanguageGate } from "./LanguageGate";
import "./index.css";

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
  if (new URLSearchParams(window.location.search).has("widget")) return <Widget />;

  if (hash === "#shopeasy") return <ShopEasy />;
  if (hash === "#b2b") return <B2B />;
  if (hash === "#lab") {
    return (
      <LanguageGate storageKey="lab_lang"
                    title="NaijaPersona Lab"
                    subtitle="Pick a default language for the developer console.">
        {() => <App />}
      </LanguageGate>
    );
  }
  return <InsideNaija />;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
