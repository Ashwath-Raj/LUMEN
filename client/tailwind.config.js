/** @type {import('tailwindcss').Config} */

// Design tokens derived from the LUMEN Figma export:
// a dark "fusion-center" tactical UI with a restrained gold accent,
// status tags (critical/warning/success/info), and a serif+mono pairing
// for dossier-style headings and data readouts.
export default {
  content: ['./index.html', './app/src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: {
          0: '#0A0A0B', // app background
          1: '#131316', // panel background
          2: '#1C1C20', // raised / hover surface
          3: '#26262B', // popovers, dropdowns
        },
        border: {
          subtle: '#2A2A2E',
          strong: '#3A3A40',
        },
        ink: {
          primary: '#F3F1EC',
          secondary: '#B7B6B2',
          muted: '#8B8B93',
          disabled: '#5A5A60',
        },
        accent: {
          gold: '#C9A227',
          goldMuted: '#8A7228',
          goldSoft: 'rgba(201, 162, 39, 0.12)',
        },
        status: {
          critical: '#C0392B',
          criticalSoft: 'rgba(192, 57, 43, 0.14)',
          warning: '#D18F2A',
          warningSoft: 'rgba(209, 143, 42, 0.14)',
          success: '#3F8F5F',
          successSoft: 'rgba(63, 143, 95, 0.14)',
          info: '#3E7CB1',
          infoSoft: 'rgba(62, 124, 177, 0.14)',
        },
      },
      fontFamily: {
        display: ['"Fraunces"', 'Georgia', 'serif'],
        sans: ['"Inter"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      letterSpacing: {
        widest2: '0.18em',
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.03) inset, 0 8px 24px -12px rgba(0,0,0,0.6)',
      },
      borderRadius: {
        sm: '4px',
        md: '6px',
      },
    },
  },
  plugins: [],
};
