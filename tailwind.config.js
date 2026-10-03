const tokens = require('./tailwind.tokens.cjs');

module.exports = {
  darkMode: ['selector', '[data-theme="dark"]'],
  content: ['./app/templates/**/*.html'],
  theme: {
    extend: tokens.theme.extend,
  },
  plugins: [],
};
