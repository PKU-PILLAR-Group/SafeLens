import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:7860";

export default defineConfig({
  testDir: "./tests",
  testIgnore: ["performance-budget.spec.ts", "matrix-performance.spec.ts"],
  fullyParallel: true,
  workers: process.env.CI ? 2 : 8,
  retries: 0,
  reporter: "line",
  use: {
    baseURL,
    screenshot: "only-on-failure",
    trace: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ],
  webServer: {
    command: "npm run dev",
    url: baseURL,
    reuseExistingServer: true,
    timeout: 30_000
  }
});
