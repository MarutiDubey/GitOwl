import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // Forwards to the local FastAPI dev server (uvicorn playground.api.review:app).
      '/api': 'http://127.0.0.1:8123',
    },
  },
})
