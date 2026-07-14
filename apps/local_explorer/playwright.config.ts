import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testIgnore: ["performance-budget.spec.ts", "matrix-performance.spec.ts"],
  fullyParallel: true,
  workers: 8,
  retries: 0,
  reporter: "line",
  use: {
    baseURL: "http://127.0.0.1:7860",
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
    url: "http://127.0.0.1:7860",
    reuseExistingServer: true,
    timeout: 30_000
  }
});
