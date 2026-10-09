import { test, expect } from "@playwright/test"

test.use({ baseURL: "http://127.0.0.1:5173" })

test.describe("PDF Invoice Generation End-to-End Flow", () => {
  test("shopper can log in, view order history, generate invoice via Celery, and access PDF", async ({
    page,
  }) => {
    // 1. Visit Manage / Login page
    await page.goto("/manage")
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
    await page.reload()

    await expect(page.getByRole("heading", { name: "Welcome back." })).toBeVisible()

    // 2. Sign in as shopper
    await page.getByLabel("Email").fill("shopper@example.com")
    await page.getByLabel("Password").fill("Shopper@12345")
    await page.getByRole("button", { name: "Sign in" }).click()

    // Verify user is authenticated
    await expect(page.getByText(/Hi,/i)).toBeVisible({ timeout: 10000 })

    // 3. Navigate to Order History
    await page.goto("/orders")
    await expect(page.getByRole("heading", { name: /Order history/i })).toBeVisible()

    // 4. Verify orders list is rendered
    const generateBtn = page.getByTestId(/^generate-invoice-btn-/).first()
    await expect(generateBtn).toBeVisible({ timeout: 10000 })
    await expect(generateBtn).toHaveText(/Generate Invoice/i)

    // 5. Trigger PDF invoice generation
    await generateBtn.click()

    // 6. Verify invoice generation completes through Celery and shows ready badge
    const readyBadge = page.getByTestId(/^invoice-ready-badge-/).first()
    await expect(readyBadge).toBeVisible({ timeout: 20000 })
    await expect(readyBadge).toHaveText(/Invoice Ready/i)

    // 7. Verify Download Invoice (PDF) button is present
    const downloadBtn = page.getByTestId(/^download-invoice-btn-/).first()
    await expect(downloadBtn).toBeVisible()
    await expect(downloadBtn).toHaveText(/Download Invoice/i)

    // 8. Test download initiation
    const downloadPromise = page.waitForEvent("download")
    await downloadBtn.click()
    const download = await downloadPromise
    expect(download.suggestedFilename()).toMatch(/ShopZone_Invoice_\d+\.pdf/)
  })
})
