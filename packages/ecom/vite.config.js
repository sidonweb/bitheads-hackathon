import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Allow the Playwright container to reach the dev server via the host alias.
    allowedHosts: ['host.docker.internal', 'localhost', 'ecom-web'],
  },
});
