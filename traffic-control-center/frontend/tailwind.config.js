/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'bg-dark': '#0B1221',
        'card-bg': '#111827',
        'card-border': 'rgba(255, 255, 255, 0.08)',
        'accent-cyan': '#22D3EE',
        'accent-blue': '#3B82F6',
        'warning-yellow': '#F59E0B',
        'alert-red': '#EF4444',
        'success-green': '#10B981',
        dark: {
          900: '#0B1221',
          800: '#111827',
          700: '#1D273B',
          600: '#2A3752',
        },
        cyan: {
          400: '#22D3EE',
          500: '#06B6D4',
          glowing: '#00f3ff',
        },
        traffic: {
          red: '#EF4444',
          yellow: '#F59E0B',
          green: '#10B981',
        }
      },
      animation: {
        'pulse-glow': 'pulseGlow 2s infinite ease-in-out',
      },
      keyframes: {
        pulseGlow: {
          '0%, 100%': { opacity: 0.8, filter: 'drop-shadow(0 0 8px rgba(34, 211, 238, 0.6))' },
          '50%': { opacity: 1, filter: 'drop-shadow(0 0 16px rgba(34, 211, 238, 0.9))' },
        }
      }
    },
  },
  plugins: [],
}
