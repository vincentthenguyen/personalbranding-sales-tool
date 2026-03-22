/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Cal Sans', 'Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        bg: {
          base: '#060A14',
          card: '#0D1426',
          elevated: '#111829',
        },
        border: {
          DEFAULT: '#1A2540',
          bright: '#2A3F6A',
        },
        accent: {
          DEFAULT: '#4B83EF',
          bright: '#6FA0FF',
          dim: '#2A4E99',
        },
        grade: {
          a: '#2DD4A0',
          b: '#4B83EF',
          c: '#F5B942',
          d: '#F16060',
        },
      },
      animation: {
        'fade-up': 'fadeUp 0.5s ease forwards',
        'bar-fill': 'barFill 1s ease forwards',
        pulse: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: 0, transform: 'translateY(16px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
