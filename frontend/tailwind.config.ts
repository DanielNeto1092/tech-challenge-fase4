import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sentinela: {
          bg: "#07090F",
          surface: "rgba(15, 19, 31, 0.82)",
          elevated: "rgba(22, 28, 43, 0.86)",
          border: "rgba(125, 249, 255, 0.14)",
          "border-med": "rgba(125, 249, 255, 0.26)",
          text: "#F2F7FB",
          "text-2": "#B8C7D9",
          "text-3": "#718198",
          primary: "#38E8FF",
          "primary-hover": "#20CFE8",
          success: "#6AF2B7",
          warning: "#FFB84D",
          danger: "#FF5C8A",
        },
      },
      fontFamily: {
        serif: ["DM Serif Display", "Georgia", "serif"],
        sans: [
          "DM Sans",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
      },
      borderRadius: {
        xl: "10px",
        "2xl": "14px",
      },
      boxShadow: {
        panel: "0 18px 60px rgba(0, 0, 0, 0.38)",
        glow: "0 0 28px rgba(56, 232, 255, 0.24)",
        danger: "0 0 28px rgba(255, 92, 138, 0.24)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
