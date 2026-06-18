module.exports = {
  darkMode: 'class',
  content: ['./app/templates/**/*.html'],
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f1f8', 100: '#d9dbed', 200: '#b3b7db', 300: '#8d93c9',
          400: '#676fb7', 500: '#4a5296', 600: '#3a4178', 700: '#2b315a',
          800: '#1e1e50', 900: '#1a1a40', 950: '#111130',
        },
        brand: { DEFAULT: '#1e1e50', light: '#2b315a', dark: '#141438' },
      },
    },
  },
  plugins: [],
}
