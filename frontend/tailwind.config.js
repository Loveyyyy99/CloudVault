export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: { sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"], mono: ["JetBrains Mono", "ui-monospace", "monospace"] },
      colors: { ink: "#0b1220", b2: "#e21e29", supabase: "#3ecf8e" },
    },
  },
  plugins: [],
};
