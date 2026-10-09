import { test, expect } from "@playwright/test"
import path from "node:path"
import fs from "node:fs"

test.use({ baseURL: "http://127.0.0.1:5173" })

test.describe("Bulk CSV Product Import End-to-End Flow", () => {
  test("admin can upload CSV, track Celery background import progress, and verify imported products", async ({
    page,
  }) => {
    // 1. Visit Admin page
    await page.goto("/admin")
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
    await page.reload()

    await expect(page.getByRole("heading", { name: /Admin sign-in/i })).toBeVisible()

    // 2. Sign in as Admin
    await page.getByLabel("Email").fill("admin@example.com")
    await page.getByLabel("Password").fill("Admin@12345")
    await page.getByRole("button", { name: "Sign in" }).click()

    // Verify Admin Dashboard loads
    await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible({ timeout: 10000 })

    // 3. Locate Bulk CSV Import Card
    const csvCard = page.getByTestId("bulk-csv-import-card")
    await expect(csvCard).toBeVisible()
    await expect(page.getByText("Bulk Product CSV Import")).toBeVisible()

    // 4. Create a test CSV file for import
    const timestamp = Date.now()
    const testProductName = `E2E Imported Item ${timestamp}`
    const csvContent =
      "name,price,category,image,description,stock\n" +
      `${testProductName},3499.0,Electronics,https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500,Auto imported test item,20\n`

    const tempDir = path.resolve("e2e-temp")
    if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir, { recursive: true })
    const testCsvPath = path.join(tempDir, `test_products_${timestamp}.csv`)
    fs.writeFileSync(testCsvPath, csvContent, "utf-8")

    // 5. Upload CSV file
    const fileInput = page.getByTestId("csv-file-input")
    await fileInput.setInputFiles(testCsvPath)

    await expect(page.getByTestId("selected-file-info")).toBeVisible()

    // 6. Click Start CSV Import
    const startBtn = page.getByTestId("start-csv-import-btn")
    await expect(startBtn).toBeEnabled()
    await startBtn.click()

    // 7. Verify Celery task progress and completion
    const statusBadge = page.getByTestId("csv-task-status-badge")
    await expect(statusBadge).toBeVisible({ timeout: 10000 })

    await expect(statusBadge).toHaveText("SUCCESS", { timeout: 25000 })
    await expect(page.getByTestId("csv-task-percent")).toHaveText("100%")

    // 8. Verify metrics summary
    const importedCount = page.getByTestId("imported-count")
    await expect(importedCount).toBeVisible()
    await expect(importedCount).toHaveText("1")

    // Cleanup temp file
    try {
      fs.unlinkSync(testCsvPath)
    } catch {
      // ignore
    }
  })
})
