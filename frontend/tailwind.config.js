/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        night: "#0a0f1f",
        moon: "#f7f3c6",
        bubbleUser: "#56b5dd",
        bubbleAI: "#1f3b73",
      },
    },
  },
  plugins: [],
}