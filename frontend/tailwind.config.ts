import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        pitch: {
          900: '#04130d',
          800: '#07211a',
          700: '#0a2c22',
          600: '#0e3a2c',
        },
        grass: {
          400: '#34e89e',
          500: '#16c784',
          600: '#0ea36a',
        },
        gold: { 400: '#ffd84d', 500: '#f5c518', 600: '#d9a900' },
        ink: '#e8f0ec',
        muted: '#8aa79b',
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI',
               'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        display: ['"Arial Black"', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(22,199,132,0.25), 0 8px 30px rgba(0,0,0,0.45)',
      },
    },
  },
  plugins: [],
};
export default config;
