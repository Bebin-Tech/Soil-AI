import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: { proxy: { '/api': 'http://127.0.0.1:8000' } },
  build: { rollupOptions: { output: { manualChunks: {
    react: ['react','react-dom','react-router-dom'],
    forms: ['react-hook-form','@hookform/resolvers/zod','zod'],
    charts: ['recharts'],
    localization: ['i18next','react-i18next'],
  } } } },
});
