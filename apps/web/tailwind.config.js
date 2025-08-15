/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}",],
  theme: {
    extend: {
      colors: {
        bg: "#f9fafb",
        surface: "#ffffff",
        text: "#111827",
        primary: "#6366f1",
        secondary: "#ec4899",
        danger: "#dc2626",
      },
      fontFamily: {
        sans: ["system-ui", "Avenir", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};