import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// LUMEN — Karnataka State Police Crime Intelligence Platform
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), './src'),
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
