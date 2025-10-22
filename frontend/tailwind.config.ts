import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Questrial",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      colors: {
        surface: {
          light: "#f3f4f6",
          dark: "#0b1120",
        },
      },
      keyframes: {
        "pulse-once": {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
      animation: {
        "pulse-once": "pulse-once 1s ease-in-out 1",
      },
    },
  },
  plugins: [],
};

export default config;
