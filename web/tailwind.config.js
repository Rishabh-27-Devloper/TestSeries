/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        tcs: {
          blue: "#1a56a5",
          darkblue: "#103a71",
          light: "#f8fafc",
          gray: "#e2e8f0",
          border: "#cbd5e1"
        }
      }
    },
  },
  plugins: [],
}
