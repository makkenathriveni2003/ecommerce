import { test, expect } from "@playwright/test"

test.use({ baseURL: "http://127.0.0.1:5173" })

test("END-TO-END LIVE INTEGRATION: Login, Products, Search, Cart, Theme, JWT, WebSocket, Notifications, Chat", async ({
  page,
}) => {
  // 1. Visit Storefront
  await page.goto("/")
  await expect(page).toHaveTitle(/ShopZone|daylight/i)

  // 2. Check WebSocket Live Status indicator
  const wsBadge = page.locator(".ws-status-badge")
  await expect(wsBadge).toBeVisible()
  await expect(wsBadge.getByText("Live")).toBeVisible()

  // 3. Products Load from PostgreSQL
  await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()

  // 4. Test Search
  const searchInput = page.getByRole("searchbox", { name: /Search products/i })
  await searchInput.fill("Headphones")
  await expect(page.getByRole("heading", { name: "Headphones" })).toBeVisible()
  await expect(page.getByRole("heading", { name: "Laptop" })).not.toBeVisible()

  // Clear search
  await page.getByRole("button", { name: "Clear search" }).click()
  await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()

  // 5. Test Theme Switcher
  const themeBtn = page.getByRole("button", { name: /Switch to dark mode/i })
  await themeBtn.click()
  await expect(page.locator("html")).toHaveAttribute("data-theme", "dark")
  const lightBtn = page.getByRole("button", { name: /Switch to light mode/i })
  await lightBtn.click()
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light")

  // 6. Test Login & JWT Flow
  await page.getByRole("link", { name: "Sign in" }).click()
  await expect(page.getByRole("heading", { name: "Welcome back." })).toBeVisible()

  await page.getByLabel("Email").fill("shopper@example.com")
  await page.getByLabel("Password").fill("Shopper@12345")
  await page.getByRole("button", { name: "Sign in" }).click()

  // Verify successful authentication and greeting
  await expect(page.getByText("Hi, Shopper User")).toBeVisible()

  // 7. Test Add to Cart
  await page.getByRole("link", { name: "Shop", exact: true }).click()
  await page.getByRole("button", { name: "Add to Cart" }).first().click()
  await expect(page.getByRole("link", { name: /Bag 1/ })).toBeVisible()

  // 8. Test Live Chat Widget
  const uniqueMessage = `Live test message ${Date.now()}`
  const chatBtn = page.getByRole("button", { name: /Live Chat/i })
  await expect(chatBtn).toBeVisible()
  await chatBtn.click()

  await expect(page.getByRole("dialog", { name: /live chat/i })).toBeVisible()
  const chatInput = page.getByPlaceholder(/Type your message here/i)
  await chatInput.fill(uniqueMessage)
  await page.getByRole("button", { name: "Send" }).click()

  // Verify message in thread
  await expect(page.getByText(uniqueMessage).first()).toBeVisible()
  await page.getByRole("button", { name: "Close chat window" }).click()

  // 9. Test Notifications Panel
  const notifBtn = page.getByRole("button", { name: /Notifications/i })
  await notifBtn.click()
  await expect(page.getByRole("dialog", { name: /Notifications panel/i })).toBeVisible()
  await notifBtn.click() // close panel

  // 10. Test Orders Page
  await page.getByRole("link", { name: "Orders" }).click()
  await expect(page.getByRole("heading", { name: /Order history/i })).toBeVisible()
})
