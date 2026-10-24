/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#060911',
        surface: '#0c1220',
        panel: '#111a2e',
        elevated: '#16223b',
        border: 'rgba(255, 255, 255, 0.08)',
        gold: '#f59e0b',
        emerald: '#10b981',
        cyan: '#06b6d4',
        crimson: '#ef4444',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'system-ui', 'sans-serif'],
        arabic: ['IBM Plex Sans Arabic', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
};
