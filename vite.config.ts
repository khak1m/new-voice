import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@new-voice/ui': path.resolve(__dirname, './packages/ui/src'),
      '@new-voice/api-client': path.resolve(__dirname, './packages/api-client/src'),
      '@new-voice/shared': path.resolve(__dirname, './packages/shared/src'),
      '@new-voice/types': path.resolve(__dirname, './packages/types/src'),
    },
  },
  server: {
    port: 5173,
    hmr: {
      overlay: true,
    },
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': {
        target: 'http://77.233.212.58:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
})
