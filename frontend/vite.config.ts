import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to FastAPI during dev — no CORS hassles.
      "/health": "http://localhost:8765",
      "/simulate-review": "http://localhost:8765",
      "/recommend": "http://localhost:8765",
      "/docs": "http://localhost:8765",
      "/openapi.json": "http://localhost:8765",
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
