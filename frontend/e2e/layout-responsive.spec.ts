import { test, expect } from "@playwright/test"

test.use({ baseURL: "http://127.0.0.1:5173" })

test.describe("ShopZone Responsive Page Layout & Screen Fitting", () => {
  const viewports = [
    { name: "Large Desktop", width: 1440, height: 900 },
    { name: "Standard Laptop", width: 1024, height: 768 },
    { name: "Tablet Portrait", width: 768, height: 1024 },
    { name: "Mobile Screen", width: 375, height: 667 },
    { name: "Small Mobile", width: 320, height: 568 },
  ]

  for (const vp of viewports) {
    test(`fits perfectly without horizontal scrollbar on ${vp.name} (${vp.width}x${vp.height})`, async ({
      page,
    }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height })
      await page.goto("/")

      // 1. Wait for product catalog to load
      await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible({ timeout: 10000 })

      // 2. Assert NO horizontal overflow
      const overflow = await page.evaluate(() => {
        const docWidth = document.documentElement.scrollWidth
        const winWidth = window.innerWidth
        return {
          scrollWidth: docWidth,
          innerWidth: winWidth,
          hasHorizontalOverflow: docWidth > winWidth,
        }
      })

      expect(overflow.hasHorizontalOverflow).toBe(false)
      expect(overflow.scrollWidth).toBeLessThanOrEqual(vp.width)

      // 3. Header fitting
      const header = page.locator(".app-header")
      await expect(header).toBeVisible()
      const headerBox = await header.boundingBox()
      expect(headerBox).not.toBeNull()
      expect(headerBox!.width).toBeLessThanOrEqual(vp.width)

      // 4. Search bar fitting
      const searchInput = page.getByRole("searchbox", { name: /Search products/i })
      await expect(searchInput).toBeVisible()
      const searchBox = await searchInput.boundingBox()
      expect(searchBox).not.toBeNull()
      expect(searchBox!.width).toBeLessThanOrEqual(vp.width)

      // 5. Product card & image fitting
      const firstCard = page.locator(".product-card").first()
      await expect(firstCard).toBeVisible()
      const cardBox = await firstCard.boundingBox()
      expect(cardBox).not.toBeNull()
      expect(cardBox!.width).toBeLessThanOrEqual(vp.width)

      const cardImage = firstCard.locator("img")
      await expect(cardImage).toBeVisible()
      const imageBox = await cardImage.boundingBox()
      expect(imageBox).not.toBeNull()
      expect(imageBox!.width).toBeLessThanOrEqual(cardBox!.width + 1) // image fits inside card

      // 6. Footer fitting
      const footer = page.locator(".site-footer")
      await expect(footer).toBeVisible()
      const footerBox = await footer.boundingBox()
      expect(footerBox).not.toBeNull()
      expect(footerBox!.width).toBeLessThanOrEqual(vp.width)
    })
  }

  test("interactive features work cleanly on desktop and mobile", async ({ page }) => {
    await page.setViewportSize({ width: 1200, height: 800 })
    await page.goto("/")

    // Search works
    const search = page.getByRole("searchbox", { name: /Search products/i })
    await search.fill("Shirt")
    await expect(page.getByRole("heading", { name: "Printed Casual Shirt" })).toBeVisible({ timeout: 5000 })

    // Add to cart works
    const addBtn = page.getByRole("button", { name: "Add to Cart" }).first()
    await addBtn.click()
    await expect(page.getByRole("link", { name: /Bag 1/i })).toBeVisible()

    // Clear search
    await page.getByRole("button", { name: "Clear search" }).click()
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()

    // Test on small screen
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()

    // No overflow on small screen
    const isOverflowing = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
    expect(isOverflowing).toBe(false)
  })
})
