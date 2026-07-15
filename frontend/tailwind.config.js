/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'edu-green': '#10B981',
        'edu-orange': '#F59E0B',
      }
    },
  },
  plugins: [],
}
