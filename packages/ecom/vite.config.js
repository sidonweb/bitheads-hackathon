import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const apiTarget = process.env.VITE_PROXY_TARGET || 'http://localhost:3002';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    // Allow the Playwright container to reach the dev server via the host alias.
    allowedHosts: ['host.docker.internal', 'localhost', 'ecom-web'],
    proxy: {
      '/events': { target: apiTarget, changeOrigin: true },
      '/experiments': { target: apiTarget, changeOrigin: true },
    },
  },
});
