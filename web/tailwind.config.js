/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Semantic tokens resolved from CSS variables (see src/index.css).
        // RGB-triplet tokens support alpha utilities; var() tokens do not.
        canvas: 'rgb(var(--canvas) / <alpha-value>)',
        ink: 'rgb(var(--ink) / <alpha-value>)',
        'ink-muted': 'rgb(var(--ink-muted) / <alpha-value>)',
        'ink-subtle': 'rgb(var(--ink-subtle) / <alpha-value>)',
        accent: 'rgb(var(--accent) / <alpha-value>)',
        'accent-strong': 'rgb(var(--accent-strong) / <alpha-value>)',
        'accent-soft': 'rgb(var(--accent-soft) / <alpha-value>)',
        steel: 'rgb(var(--steel) / <alpha-value>)',
        // Material + separator tokens (full color values from index.css).
        'glass-hairline': 'var(--glass-hairline)',
        'chrome-hairline': 'var(--chrome-hairline)',
        separator: 'var(--separator)',
      },
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"SF Pro Text"',
          '"SF Pro Display"',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
      },
      boxShadow: {
        glass:
          '0 0 0 1px var(--glass-edge), 0 1px 2px rgb(var(--shadow-color) / 0.05), 0 12px 40px rgb(var(--shadow-color) / 0.10), inset 0 1px 0 var(--glass-highlight)',
        'glass-lg':
          '0 0 0 1px var(--glass-edge), 0 2px 4px rgb(var(--shadow-color) / 0.06), 0 24px 64px rgb(var(--shadow-color) / 0.18), inset 0 1px 0 var(--glass-highlight)',
      },
    },
  },
  plugins: [],
};
