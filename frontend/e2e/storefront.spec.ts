import { expect, test } from "@playwright/test"
import { testProducts } from "../src/test/products"

test("shopper can add an item and update the bag", async ({ page }) => {
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

  await page.goto("/")
  await expect(page.getByRole("heading", { name: "Headphones" })).toBeVisible()
  await page.getByRole("button", { name: "Add to Cart" }).first().click()
  await page.getByRole("link", { name: /Bag 1/ }).click()

  await expect(page.getByRole("heading", { name: "Your bag." })).toBeVisible()
  const summary = page.getByRole("complementary", { name: "Order summary" })
  await expect(summary.getByText("₹3,000").first()).toBeVisible()
  await page.getByRole("button", { name: "Increase Headphones quantity" }).click()
  await expect(summary.getByText("₹6,000").first()).toBeVisible()
})
