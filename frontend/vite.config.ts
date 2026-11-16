/// <reference types="vitest/config" />
import { fileURLToPath, URL } from 'node:url'

import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    // Listen on all interfaces and use a fixed port so the app is reachable
    // from the host when the dev server runs inside the Docker frontend service.
    host: true,
    port: 5173,
    strictPort: true,
  },
  test: {
    // Unit and component tests run in a jsdom DOM with global test APIs; the
    // setup file registers the jest-dom matchers and cleans up after each test.
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,
    include: ['src/**/*.test.{ts,tsx}'],
    // Pin the time zone so date/time assertions are deterministic everywhere.
    env: { TZ: 'UTC' },
  },
})
