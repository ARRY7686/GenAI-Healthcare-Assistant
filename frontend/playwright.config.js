import { defineConfig, devices } from '@playwright/test'

// Spins up BOTH servers (FastAPI backend + Vite dev) and drives the real browser flow.
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  fullyParallel: false,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: [
    {
      command: '.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning',
      cwd: '../backend',
      url: 'http://127.0.0.1:8000/api/health',
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      // Pin to 127.0.0.1 — Vite defaults to `localhost`, which resolves to IPv6 ::1 on
      // macOS and makes the 127.0.0.1 health check / baseURL unreachable.
      command: 'npm run dev -- --port 5173 --strictPort --host 127.0.0.1',
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: true,
      timeout: 120000,
    },
  ],
})
