import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#0a0a0f",
          secondary: "#111118",
          tertiary: "#1a1a24",
        },
        border: {
          default: "#27272a",
        },
        accent: {
          blue: "#6366f1",
          cyan: "#22d3ee",
          green: "#4ade80",
          red: "#f87171",
          yellow: "#facc15",
        },
      },
    },
  },
  plugins: [],
};

export default config;
