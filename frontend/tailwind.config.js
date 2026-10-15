/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        jira: {
          bg: '#0F172A',
          card: '#1E293B',
          column: '#111827',
          border: '#334155',
          text: '#F8FAFC',
          muted: '#94A3B8'
        }
      }
    },
  },
  plugins: [],
}
