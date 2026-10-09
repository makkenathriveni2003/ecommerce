import { test, expect } from "@playwright/test"

test.use({ baseURL: "http://127.0.0.1:5173" })

test("Admin login for Thriveni opens Admin Dashboard and Product Management", async ({
  page,
}) => {
  // 1. Visit Manage page and ensure fresh state
  await page.goto("/manage")
  await page.evaluate(() => {
    localStorage.clear()
    sessionStorage.clear()
  })
  await page.reload()

  await expect(page.getByRole("heading", { name: "Welcome back." })).toBeVisible()

  // 2. Sign in with the new admin account
  await page.getByLabel("Email").fill("thriveni@gmail.com")
  await page.getByLabel("Password").fill("12345678")
  await page.getByRole("button", { name: "Sign in" }).click()

  // 3. Verify user is authenticated as Thriveni
  await expect(page.getByText("Hi, Thriveni")).toBeVisible()

  // 4. Verify Manage Products form is accessible (only available for admin role)
  await expect(page.getByRole("heading", { name: "Add a product." })).toBeVisible()

  // 5. Navigate to full Admin Dashboard
  await page.goto("/admin")
  await expect(page.getByRole("heading", { name: /Dashboard/i })).toBeVisible()
  await expect(page.getByRole("heading", { name: "Orders" })).toBeVisible()
  await expect(page.getByRole("heading", { name: "Products" })).toBeVisible()
})
