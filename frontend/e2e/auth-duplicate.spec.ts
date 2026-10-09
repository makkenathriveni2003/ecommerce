import { test, expect } from "@playwright/test"

test.use({ baseURL: "http://127.0.0.1:5173" })

test("Registration with existing email shows friendly conflict message and allows sign in", async ({
  page,
}) => {
  // Clear any persisted session
  await page.addInitScript(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  await page.goto("/manage")

  // Toggle to "Create an account"
  const toggleBtn = page.locator(".auth-mode-toggle")
  await expect(toggleBtn).toBeVisible()
  await toggleBtn.click()

  await expect(page.getByRole("heading", { name: "Create an account." })).toBeVisible()

  // Fill in existing email
  await page.getByLabel("Name").fill("Thriveni")
  await page.getByLabel("Email").fill("thriveni@gmail.com")
  await page.getByLabel("Password").fill("password123")

  // Submit
  await page.getByRole("button", { name: "Create account" }).click()

  // Verify the friendly conflict message appears instead of a generic backend reachability error
  const errorMessage = page.locator(".form-message.error-message")
  await expect(errorMessage).toBeVisible()
  await expect(errorMessage).toContainText("Email already registered. Please sign in instead.")

  // Switch to sign in
  await toggleBtn.click()
  await expect(page.getByRole("heading", { name: "Welcome back." })).toBeVisible()
})
