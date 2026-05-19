import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        naija: {
          50: "#e8f7ee",
          100: "#c4ead2",
          200: "#9ddbb4",
          300: "#73cd95",
          400: "#4cc079",
          500: "#22b35d",
          600: "#008751", // Nigerian flag green
          700: "#006d40",
          800: "#005232",
          900: "#003820",
        },
        ink: {
          50: "#f7f8fa",
          100: "#edf0f5",
          200: "#d6dce6",
          300: "#a8b3c4",
          400: "#6e7c92",
          500: "#48556b",
          600: "#2f3a4d",
          700: "#1f2738",
          800: "#141925",
          850: "#0e1320",
          900: "#0a0e18",
          950: "#060912",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
