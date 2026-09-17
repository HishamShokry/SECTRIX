/** Brand configuration, ported verbatim from the inline Play CDN config that
 *  used to live in templates/base.html. */
module.exports = {
  darkMode: 'class',
  content: [
    './templates/**/*.html',
    // Form widget classes are declared in Python, not markup.
    './apps/**/*.py',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          50:  '#F1F4FA', 100: '#DCE2EE', 200: '#B4C0D6', 300: '#7E90B3',
          400: '#4D618A', 500: '#2C3E66', 600: '#1B2C4F', 700: '#142243',
          800: '#0E1F3A', 900: '#0A1830', 950: '#060F22',
        },
        graphite: {
          100: '#E2E5EB', 200: '#C2C8D3', 300: '#9AA2B3', 400: '#6C7589',
          500: '#4A5466', 600: '#363D4B', 700: '#262C37', 800: '#1A1F28',
          900: '#11151C',
        },
        accent: {
          DEFAULT: '#00B4F0',
          soft:    '#34C7F4',
          deep:    '#0096C7',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
        display: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.04em',
        'wider-2': '0.16em',
        'wider-3': '0.24em',
      },
      boxShadow: {
        'glow-accent': '0 0 40px -10px rgba(0,180,240,0.45)',
        'inset-line':  'inset 0 1px 0 0 rgba(255,255,255,0.06)',
      },
      backgroundImage: {
        'grid-faint': "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
        'radial-fade': "radial-gradient(ellipse at top, rgba(0,180,240,0.10), transparent 60%)",
      },
      backgroundSize: {
        'grid-32': '32px 32px',
      },
      animation: {
        'fade-up':    'fadeUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both',
        'fade-in':    'fadeIn 0.6s ease both',
        'pulse-slow': 'pulseSlow 4s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: { '0%': { opacity: 0, transform: 'translateY(14px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        fadeIn: { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        pulseSlow: { '0%, 100%': { opacity: 0.35 }, '50%': { opacity: 0.85 } },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ],
};
