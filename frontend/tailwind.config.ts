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
        blob: {
          "0%": {
            transform: "translate(0px, 0px) scale(1)",
          },
          "33%": {
            transform: "translate(30px, -50px) scale(1.1)",
          },
          "66%": {
            transform: "translate(-20px, 20px) scale(0.9)",
          },
          "100%": {
            transform: "translate(0px, 0px) scale(1)",
          },
        },
      },
      animation: {
        "pulse-once": "pulse-once 1s ease-in-out 1",
        blob: "blob 7s infinite",
      },
      animationDelay: {
        "2000": "2s",
        "4000": "4s",
      },
    },
  },
  plugins: [
    // Plugin para animation-delay
    function ({ addUtilities }: any) {
      const newUtilities = {
        ".animation-delay-2000": {
          "animation-delay": "2s",
        },
        ".animation-delay-4000": {
          "animation-delay": "4s",
        },
      };
      addUtilities(newUtilities);
    },
  ],
};

export default config;
