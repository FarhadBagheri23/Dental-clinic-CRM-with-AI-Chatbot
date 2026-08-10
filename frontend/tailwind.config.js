/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Deep clinical teal. Deliberately darker and less saturated than
        // Tailwind's stock `cyan` (which the old site used renamed as
        // `brand`) — the stock swatch reads neon on large surfaces.
        brand: {
          50: "#f0faf9",
          100: "#d8f2f0",
          200: "#b3e4e2",
          300: "#83cfcf",
          400: "#4fb0b3",
          500: "#2f9296",
          600: "#1f757b",
          700: "#1c5d64",
          800: "#1b4b51",
          900: "#1a3f45",
          950: "#0a252a",
        },
        // Warm counterweight so an all-teal UI doesn't read cold and sterile.
        accent: {
          50: "#fdf8ed",
          100: "#f8ecd0",
          200: "#f0d69f",
          300: "#e5bb66",
          400: "#d9a441",
          500: "#c98b28",
          600: "#a86d1d",
          700: "#85531b",
        },
        // Neutrals carry a slight green cast to sit with the teal, instead of
        // the blue-cast slate that fights it.
        ink: {
          50: "#f7f8f8",
          100: "#eef0f0",
          200: "#dfe3e3",
          300: "#c3caca",
          400: "#9aa4a5",
          500: "#788384",
          600: "#5f6a6b",
          700: "#4d5657",
          800: "#3a4142",
          900: "#232829",
          950: "#141819",
        },
      },
      fontFamily: {
        sans: ["Vazirmatn Variable", "Vazirmatn", "system-ui", "sans-serif"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(20,24,25,.04), 0 8px 24px -12px rgba(20,24,25,.18)",
        lift: "0 2px 4px rgba(20,24,25,.05), 0 16px 40px -16px rgba(20,24,25,.28)",
      },
      keyframes: {
        "fade-up": {
          from: { opacity: 0, transform: "translateY(8px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
        shake: {
          "0%,100%": { transform: "translateX(0)" },
          "25%": { transform: "translateX(-4px)" },
          "75%": { transform: "translateX(4px)" },
        },
      },
      animation: {
        "fade-up": "fade-up .4s cubic-bezier(.16,1,.3,1) both",
        shake: "shake .3s ease-in-out",
      },
    },
  },
  plugins: [],
};
