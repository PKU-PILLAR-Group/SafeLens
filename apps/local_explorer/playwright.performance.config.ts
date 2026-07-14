import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: ["performance-budget.spec.ts", "matrix-performance.spec.ts"],
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "line",
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:7862",
    screenshot: "only-on-failure",
    trace: "retain-on-failure"
  },
  projects: [{ name: "chromium-production" }],
  webServer: {
    command: "npm run build && vite preview --host 127.0.0.1 --port 7862",
    url: "http://127.0.0.1:7862",
    reuseExistingServer: false,
    timeout: 30_000
  }
});
