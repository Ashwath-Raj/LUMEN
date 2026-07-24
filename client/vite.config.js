import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// LUMEN — Karnataka State Police Crime Intelligence Platform
//
// Configuration comes from the SINGLE canonical .env at the repository root
// (one level up from this client/ directory). `envDir` points Vite there, so
// the frontend and backend read the same file. Per Vite's security model,
// ONLY variables prefixed `VITE_` are exposed to the browser bundle; every
// other variable in the root .env (DATABASE_URL, CORS_ORIGINS, …) stays
// backend-only and is never shipped to the client.
const ROOT_ENV_DIR = path.resolve(process.cwd(), '..');

export default defineConfig({
  plugins: [react()],
  // Load env files from the repo root instead of client/.
  envDir: ROOT_ENV_DIR,
  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), './app/src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      // FastAPI backend — adjust target to match local backend port
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy) => {
          proxy.on('error', (err, req, res) => {
            if (err.code === 'ECONNREFUSED') {
              res.writeHead(502, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ error: 'Backend unavailable', code: 'ECONNREFUSED' }));
            }
          });
        }
      },
    },
  },
});
