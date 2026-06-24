/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      boxShadow: {
        soft: "0 18px 50px rgba(15, 23, 42, 0.14)",
        glow: "0 0 0 1px rgba(34, 211, 238, 0.14), 0 16px 40px rgba(14, 165, 233, 0.18)",
      },
      backgroundImage: {
        mesh:
          "radial-gradient(circle at 15% 20%, rgba(56, 189, 248, 0.18), transparent 0 28%), radial-gradient(circle at 85% 10%, rgba(16, 185, 129, 0.18), transparent 0 26%), radial-gradient(circle at 50% 100%, rgba(99, 102, 241, 0.18), transparent 0 30%)",
      },
      borderRadius: {
        "3xl": "1.75rem",
      },
      colors: {
        brand: {
          50: "#eef9ff",
          100: "#d8f0ff",
          200: "#b4e2ff",
          300: "#7fd0ff",
          400: "#37b4ff",
          500: "#1692ff",
          600: "#0f73e6",
          700: "#0f5dcc",
          800: "#124aa5",
          900: "#143f83",
        },
      },
    },
  },
  plugins: [],
};
