import { test, expect } from "@playwright/test"
import path from "node:path"
import fs from "node:fs"

test.use({ baseURL: "http://127.0.0.1:5173" })

test.describe("Day 18 Master E2E Complete Integration Flow", () => {
  test("Executes all Day 18 features end-to-end on live PostgreSQL, Redis, Celery, and FastAPI", async ({
    page,
  }) => {
    test.setTimeout(60000)
    // -------------------------------------------------------------
    // STEP 1: Storefront & Real-Time Connection
    // -------------------------------------------------------------
    await page.goto("/")
    await expect(page).toHaveTitle(/ShopZone|daylight/i)

    // Check Live WebSocket indicator
    const wsBadge = page.locator(".ws-status-badge")
    await expect(wsBadge).toBeVisible()
    await expect(wsBadge.getByText("Live")).toBeVisible()

    // -------------------------------------------------------------
    // STEP 2: PostgreSQL Full-Text & Fuzzy Typo Search
    // -------------------------------------------------------------
    const searchInput = page.getByRole("searchbox", { name: /Search products/i })

    // Typo 1: "laptpo" -> matches "Laptop"
    await searchInput.fill("laptpo")
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible({ timeout: 5000 })

    // Typo 2: "iphnoe" -> matches "Apple iPhone 15 Pro"
    await searchInput.fill("iphnoe")
    await expect(page.getByRole("heading", { name: /iPhone/i })).toBeVisible({ timeout: 5000 })

    // Clear search
    await page.getByRole("button", { name: "Clear search" }).click()
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()

    // -------------------------------------------------------------
    // STEP 3: Celery Background Jobs Lifecycle Page
    // -------------------------------------------------------------
    await page.goto("/tasks")
    await expect(page.getByTestId("background-jobs-page")).toBeVisible()
    await expect(page.getByRole("heading", { name: "Celery Background Jobs" })).toBeVisible()

    // Configure fast 4-step task
    await page.locator("#job-name-input").fill("Master E2E Task")
    await page.locator("#steps-input").selectOption("4")
    await page.locator("#delay-input").selectOption("0.2")

    // Trigger task
    const triggerBtn = page.getByTestId("trigger-task-btn")
    await triggerBtn.click()

    // Verify task progress card
    const taskCard = page.getByTestId("task-progress-card")
    await expect(taskCard).toBeVisible()
    const statusBadge = page.getByTestId("task-status-badge")
    await expect(statusBadge).toHaveText("Completed", { timeout: 15000 })
    await expect(page.getByTestId("task-percent")).toHaveText("100%")

    // -------------------------------------------------------------
    // STEP 4: Admin Login & Bulk CSV Product Import
    // -------------------------------------------------------------
    await page.goto("/admin")
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
    await page.reload()

    await expect(page.getByRole("heading", { name: /Admin sign-in/i })).toBeVisible()
    await page.getByLabel("Email").fill("admin@example.com")
    await page.getByLabel("Password").fill("Admin@12345")
    await page.getByRole("button", { name: "Sign in" }).click()

    // Verify Admin Dashboard loads
    await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible({ timeout: 10000 })

    // Verify Bulk CSV Import card exists
    const csvCard = page.getByTestId("bulk-csv-import-card")
    await expect(csvCard).toBeVisible()

    // Create unique CSV with 1 valid and 1 invalid row
    const timestamp = Date.now()
    const uniqueItem = `Master E2E Drone ${timestamp}`
    const csvContent =
      "name,price,category,image,description,stock\n" +
      `${uniqueItem},49999.0,Electronics,https://images.unsplash.com/photo-1527977966376-1c8408f9f108?w=500,4K Camera Quadcopter Drone,10\n` +
      "Invalid Drone,-500.0,Electronics,https://example.com/drone.jpg,Bad price,2\n"

    const tempDir = path.resolve("e2e-temp")
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true })
    const testCsvFile = path.join(tempDir, `master_import_${timestamp}.csv`)
    fs.writeFileSync(testCsvFile, csvContent, "utf-8")

    // Upload CSV
    const fileInput = page.getByTestId("csv-file-input")
    await fileInput.setInputFiles(testCsvFile)
    await expect(page.getByTestId("selected-file-info")).toBeVisible()

    // Trigger Celery Import
    const startBtn = page.getByTestId("start-csv-import-btn")
    await expect(startBtn).toBeEnabled()
    await startBtn.click()

    // Verify Celery task progress & completion
    const csvStatusBadge = page.getByTestId("csv-task-status-badge")
    await expect(csvStatusBadge).toBeVisible({ timeout: 10000 })
    await expect(csvStatusBadge).toHaveText("SUCCESS", { timeout: 25000 })
    await expect(page.getByTestId("csv-task-percent")).toHaveText("100%")

    // Verify metrics summary
    await expect(page.getByTestId("imported-count")).toHaveText("1")
    await expect(page.getByTestId("failed-count")).toHaveText("1")

    // -------------------------------------------------------------
    // STEP 5: Verify Imported Product in Storefront
    // -------------------------------------------------------------
    await page.goto("/")
    const verifySearch = page.getByRole("searchbox", { name: /Search products/i })
    await verifySearch.fill(`Drone ${timestamp}`)
    await expect(page.getByRole("heading", { name: uniqueItem })).toBeVisible({ timeout: 10000 })

    // Cleanup temp CSV
    try {
      fs.unlinkSync(testCsvFile)
    } catch {
      // ignore
    }
  })
})
