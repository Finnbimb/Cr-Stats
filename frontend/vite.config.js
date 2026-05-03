import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import http from 'node:http'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        agent: new http.Agent({ keepAlive: false }),
      },
    },
  },
})
