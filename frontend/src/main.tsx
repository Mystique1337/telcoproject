import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import InsideNaija from "./InsideNaija";
import ShopEasy from "./ShopEasy";
import { LanguageGate } from "./LanguageGate";
import "./index.css";

// Hash router across the two products + the dev lab.
//   (default)   InsideNaija — Task A product (synthetic panel)
//   #shopeasy   ShopEasy    — Task B product (search + recommend)
//   #lab        App         — original multi-tab developer console
// ShopEasy + the lab show the language gate before their main page.
function Root() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const on = () => setHash(window.location.hash);
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);

  if (hash === "#shopeasy") return <ShopEasy />;
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
