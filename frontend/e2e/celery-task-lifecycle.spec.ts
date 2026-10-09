import { test, expect } from "@playwright/test"

test.describe("Celery Background Task Lifecycle in React", () => {
  test("triggers Celery task from UI, polls status, shows progress, and completes successfully", async ({ page }) => {
    // 1. Navigate to Background Jobs page
    await page.goto("/tasks")

    // Verify page header
    await expect(page.getByTestId("background-jobs-page")).toBeVisible()
    await expect(page.getByRole("heading", { name: "Celery Background Jobs" })).toBeVisible()

    // 2. Configure task parameters (Quick 4-step job with 0.2s delay for fast E2E test)
    await page.locator("#job-name-input").fill("Playwright E2E Celery Job")
    await page.locator("#steps-input").selectOption("4")
    await page.locator("#delay-input").selectOption("0.2")

    // 3. Trigger the Celery background task
    const triggerBtn = page.getByTestId("trigger-task-btn")
    await expect(triggerBtn).toBeEnabled()
    await triggerBtn.click()

    // 4. Verify Task Progress Card appears with real-time updates
    const taskCard = page.getByTestId("task-progress-card")
    await expect(taskCard).toBeVisible({ timeout: 5000 })

    // Verify task status badge is visible
    const statusBadge = page.getByTestId("task-status-badge")
    await expect(statusBadge).toBeVisible()

    // 5. Verify progress updates and eventual completion to 100%
    await expect(statusBadge).toHaveText("Completed", { timeout: 15000 })
    await expect(page.getByTestId("task-percent")).toHaveText("100%")

    // Verify progress bar is at 100% width
    const progressBar = page.getByTestId("task-progress-bar")
    await expect(progressBar).toHaveCSS("width", /.+/)

    // 6. Verify result alert is rendered with success
    const resultAlert = page.getByTestId("task-result-alert")
    await expect(resultAlert).toBeVisible()
    await expect(resultAlert).toContainText("SUCCESS")
  })
})
