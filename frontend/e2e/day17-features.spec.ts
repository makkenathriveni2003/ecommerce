import { expect, test } from "@playwright/test"
import { testProducts } from "../src/test/products"

test.describe("Day 17 Real-Time ShopZone features", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/products?*", async (route) => {
      const url = new URL(route.request().url())
      const skip = Number(url.searchParams.get("skip") ?? "0")
      const limit = Number(url.searchParams.get("limit") ?? "100")
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(testProducts.slice(skip, skip + limit)),
      })
    })

    await page.route("**/chat/messages*", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      })
    })
  })

  test("shopper can search products, open notifications panel, and open live chat", async ({
    page,
  }) => {
    await page.goto("/")

    // 1. Verify Products load
    await expect(page.getByRole("heading", { name: "Headphones" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Watch" })).toBeVisible()

    // 2. Test Search
    const searchInput = page.getByRole("searchbox", { name: /Search products/i })
    await searchInput.fill("Watch")
    await expect(page.getByRole("heading", { name: "Watch" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Headphones" })).not.toBeVisible()

    // Clear search
    await page.getByRole("button", { name: "Clear search" }).click()
    await expect(page.getByRole("heading", { name: "Headphones" })).toBeVisible()

    // 3. Test Notifications Panel
    const notifBtn = page.getByRole("button", { name: /Notifications/i })
    await expect(notifBtn).toBeVisible()
    await notifBtn.click()
    await expect(page.getByRole("dialog", { name: /Notifications panel/i })).toBeVisible()
    await expect(page.getByText(/No notifications yet/i)).toBeVisible()

    // 4. Test Live Chat Widget
    const chatBtn = page.getByRole("button", { name: /Live Chat/i })
    await expect(chatBtn).toBeVisible()
    await chatBtn.click()
    await expect(page.getByRole("dialog", { name: /live chat/i })).toBeVisible()
    await expect(page.getByPlaceholder(/Type your message here/i)).toBeVisible()

    // Type a message in live chat
    await page.getByPlaceholder(/Type your message here/i).fill("Hello from customer!")

    const sendBtn = page.getByRole("button", { name: "Send" })
    await expect(sendBtn).toBeEnabled()

    // Close chat
    await page.getByRole("button", { name: "Close chat window" }).click()
    await expect(page.getByRole("dialog", { name: /live chat/i })).not.toBeVisible()
  })

  test("shopper can toggle dark and light mode theme", async ({ page }) => {
    await page.goto("/")
    const themeBtn = page.getByRole("button", { name: /Switch to dark mode/i })
    await themeBtn.click()
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark")

    const lightBtn = page.getByRole("button", { name: /Switch to light mode/i })
    await lightBtn.click()
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light")
  })
})
