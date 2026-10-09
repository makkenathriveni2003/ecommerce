import { test, expect } from "@playwright/test"

test.use({ baseURL: "http://127.0.0.1:5173" })

test.describe("PostgreSQL Full-Text and Typo-Tolerant Fuzzy Search Flow", () => {
  test("shopper can search products with typos (laptpo, iphnoe) and keywords via PostgreSQL", async ({
    page,
  }) => {
    // 1. Visit storefront
    await page.goto("/")

    // Verify initial products rendered from PostgreSQL
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible({ timeout: 10000 })

    const searchInput = page.getByRole("searchbox", { name: /Search products/i })
    await expect(searchInput).toBeVisible()

    // 2. Test Typo Search: 'laptpo' -> matches 'Laptop'
    await searchInput.fill("laptpo")

    // Verify search feedback appears
    await expect(page.getByTestId("search-status-feedback")).toBeVisible({ timeout: 10000 })
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Denim Jeans" })).not.toBeVisible()

    // 3. Test Typo Search: 'iphnoe' -> matches iPhone
    await searchInput.fill("iphnoe")
    await expect(page.getByTestId("search-status-feedback")).toBeVisible({ timeout: 10000 })
    await expect(page.getByRole("heading", { name: /iPhone/i })).toBeVisible()

    // 4. Test Category Full-Text Search: 'electronics'
    await searchInput.fill("electronics")
    await expect(page.getByTestId("search-status-feedback")).toBeVisible({ timeout: 10000 })
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()

    // 5. Clear Search and restore catalog
    const clearBtn = page.getByRole("button", { name: "Clear search" })
    await clearBtn.click()

    await expect(searchInput).toHaveValue("")
    await expect(page.getByRole("heading", { name: "Laptop" })).toBeVisible()
    await expect(page.getByRole("heading", { name: "Mobile" })).toBeVisible()
  })
})
