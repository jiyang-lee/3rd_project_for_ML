import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    emptyOutDir: false
  },
  server: {
    proxy: {
      '/cards': 'http://127.0.0.1:8000',
      '/tickets': 'http://127.0.0.1:8000',
      '/llm': 'http://127.0.0.1:8000',
      '/rag': 'http://127.0.0.1:8000',
      '/replay': 'http://127.0.0.1:8000',
      '/timeseries': 'http://127.0.0.1:8000',
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true
      }
    }
  }
})
