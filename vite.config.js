import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: '/easibillity.github.io/',
  plugins: [react()],
  server: {
    port: 5173,
    open: true
  }
})
