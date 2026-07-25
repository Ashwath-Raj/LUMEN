import js from '@eslint/js';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import globals from 'globals';

// LUMEN frontend lint config (flat). TypeScript is the source language (arch
// §G); `tsc --strict` is the primary correctness gate, ESLint the style/hooks
// layer. Covers .ts/.tsx with the TS parser + React rules.
export default [
  { ignores: ['dist', 'node_modules'] },
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      parser: tseslint.parser,
      globals: {
        ...globals.browser,
      },
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: {
      '@typescript-eslint': tseslint.plugin,
      react,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...js.configs.recommended.rules,
      ...tseslint.configs.recommended.rules,
      ...react.configs.recommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react/react-in-jsx-scope': 'off',
      'react/prop-types': 'off',
      'react-refresh/only-export-components': 'warn',
      // tsc handles unused vars with better semantics; avoid double-reporting.
      'no-unused-vars': 'off',
    },
    settings: { react: { version: 'detect' } },
  },
  {
    // Node-context config/tooling files (Playwright, Vite) run outside the
    // browser bundle and legitimately use `process`.
    files: ['*.config.{js,ts}', 'playwright.config.ts', 'e2e/**/*.{ts,tsx}'],
    languageOptions: {
      globals: { ...globals.node },
    },
  },
];
