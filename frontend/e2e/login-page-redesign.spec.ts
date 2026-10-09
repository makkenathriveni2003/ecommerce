import { test, expect } from "@playwright/test"

test.use({ baseURL: "http://127.0.0.1:5173" })

test.describe("ShopZone Modern E-Commerce Login Experience", () => {
  test("displays ShopZone branding, dual login options (Thanu & Thriveni), and password toggle", async ({
    page,
  }) => {
    // Collect console errors
    const consoleErrors: string[] = []
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text())
    })

    // 1. Visit Login page
    await page.goto("/manage")

    // Clear any previous session
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
    await page.reload()

    // 2. Verify Prominent SHOPZONE Branding
    await expect(page.locator(".sz-brand-title")).toContainText("SHOPZONE")
    await expect(page.locator(".sz-brand-mark")).toHaveText("S")
    await expect(page.locator(".sz-brand-tagline")).toBeVisible()

    // 3. Verify Two Login Options
    const userTab = page.locator(".sz-role-tab").filter({ hasText: "Customer Login" })
    const adminTab = page.locator(".sz-role-tab").filter({ hasText: "Admin Login" })
    await expect(userTab).toBeVisible()
    await expect(adminTab).toBeVisible()

    // Check display names
    await expect(userTab).toContainText("User: Thanu")
    await expect(adminTab).toContainText("Admin: Thriveni")

    // Default active tab should be Customer Login
    await expect(userTab).toHaveAttribute("aria-selected", "true")
    await expect(page.getByText("Welcome back, Thanu.")).toBeVisible()

    // 4. Test Show/Hide Password Toggle
    const passwordInput = page.getByLabel("Password")
    const toggleBtn = page.locator(".sz-password-toggle-btn")
    await passwordInput.fill("secretPassword123")
    await expect(passwordInput).toHaveAttribute("type", "password")

    await toggleBtn.click()
    await expect(passwordInput).toHaveAttribute("type", "text")

    await toggleBtn.click()
    await expect(passwordInput).toHaveAttribute("type", "password")

    // 5. Switch to Admin Login tab
    await adminTab.click()
    await expect(adminTab).toHaveAttribute("aria-selected", "true")
    await expect(page.locator(".sz-login-card")).toHaveClass(/admin-mode-card/)
    await expect(page.getByText("ADMINISTRATOR PORTAL")).toBeVisible()
    await expect(page.getByText("Welcome back, Thriveni.")).toBeVisible()
    await expect(page.getByRole("button", { name: /Sign in as Admin/i })).toBeVisible()

    // 6. Test invalid login error display
    await page.getByLabel(/Admin Email|Email/).fill("thriveni@gmail.com")
    await passwordInput.fill("WrongPassword999")
    await page.getByRole("button", { name: /Sign in as Admin/i }).click()

    const errorAlert = page.locator(".sz-alert-box[role='alert']")
    await expect(errorAlert).toBeVisible()
    await expect(errorAlert).toContainText(/Invalid email or password|Please sign in again/i)

    // 7. Verify no unexpected console errors
    const criticalErrors = consoleErrors.filter(
      (err) => !err.includes("401") && !err.includes("favicon"),
    )
    expect(criticalErrors).toHaveLength(0)
  })

  test("Customer Login authenticates Thanu and opens customer storefront", async ({
    page,
  }) => {
    await page.goto("/manage")
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
    await page.reload()

    // Click quick preset chip for Thanu
    await page.locator(".sz-preset-chip").filter({ hasText: "Thanu" }).click()
    await page.getByLabel("Password").fill("12345678")
    await page.getByRole("button", { name: "Sign in" }).click()

    // Customer should be greeted
    await expect(page.getByText("Hi, Thanu")).toBeVisible()
    // Should NOT show admin links in navigation
    await expect(page.getByRole("link", { name: "Add products" })).not.toBeVisible()
    await expect(page.getByRole("link", { name: "Admin" })).not.toBeVisible()
  })

  test("Admin Login authenticates Thriveni and opens Admin Dashboard", async ({
    page,
  }) => {
    await page.goto("/manage")
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
    await page.reload()

    // Switch to Admin Login tab
    await page.locator(".sz-role-tab").filter({ hasText: "Admin Login" }).click()

    // Click quick preset chip for Thriveni
    await page.locator(".sz-preset-chip.admin-chip").click()
    await page.getByLabel("Password").fill("12345678")
    await page.getByRole("button", { name: /Sign in as Admin/i }).click()

    // Admin should be greeted and receive Admin badge
    await expect(page.getByText("Hi, Thriveni")).toBeVisible()
    await expect(page.locator(".admin-badge")).toBeVisible()

    // Unlocks Admin Dashboard
    await page.goto("/admin")
    await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Orders" })).toBeVisible()
  })
})
