/** @type {import('tailwindcss').Config} */

/*
 * LUMEN Tailwind config — driven entirely by the design tokens in
 * app/src/design/tokens/tokens.css (master spec §31.1 + arch §F). Every value
 * here is `var(--token)`, so the CSS custom properties are the single source of
 * truth and there is no second hard-coded palette (spec §31, §33 row-16:
 * "Zero hard-coded colours"). The prototype's gold/serif theme is removed.
 */
export default {
  content: ['./index.html', './app/src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class', // dark is the only theme (§F); class kept for the root data-attr
  theme: {
    extend: {
      colors: {
        void: 'var(--bg-void)',
        panel: 'var(--bg-panel)',
        raised: 'var(--bg-raised)',
        line: 'var(--line)',
        ink: {
          primary: 'var(--ink-primary)',
          muted: 'var(--ink-muted)',
          faint: 'var(--ink-faint)',
        },
        signal: 'var(--signal)',
        risk: {
          critical: 'var(--risk-critical)',
          high: 'var(--risk-high)',
          medium: 'var(--risk-medium)',
          low: 'var(--risk-low)',
        },
        confidence: {
          high: 'var(--confidence-high)',
          med: 'var(--confidence-med)',
          low: 'var(--confidence-low)',
        },
        degraded: 'var(--state-degraded)',
      },
      fontFamily: {
        display: 'var(--font-display)',
        body: 'var(--font-body)',
        mono: 'var(--font-mono)',
      },
      fontSize: {
        'page-title': ['var(--text-page-title)', 'var(--leading-page-title)'],
        'panel-title': ['var(--text-panel-title)', 'var(--leading-panel-title)'],
        body: ['var(--text-body)', 'var(--leading-body)'],
        dense: ['var(--text-dense)', 'var(--leading-dense)'],
        caption: ['var(--text-caption)', 'var(--leading-caption)'],
      },
      spacing: {
        1: 'var(--space-1)',
        2: 'var(--space-2)',
        3: 'var(--space-3)',
        4: 'var(--space-4)',
        6: 'var(--space-6)',
        8: 'var(--space-8)',
      },
      borderRadius: {
        DEFAULT: 'var(--radius)',
        sm: 'var(--radius)',
        md: 'var(--radius)',
      },
      boxShadow: {
        panel: 'var(--shadow-panel)',
      },
      transitionTimingFunction: {
        ease: 'var(--motion-ease)',
      },
      transitionDuration: {
        DEFAULT: 'var(--motion-duration)',
      },
      zIndex: {
        rail: 'var(--z-rail)',
        topbar: 'var(--z-topbar)',
        inspector: 'var(--z-inspector)',
        overlay: 'var(--z-overlay)',
        tooltip: 'var(--z-tooltip)',
        toast: 'var(--z-toast)',
      },
    },
  },
  plugins: [],
};
