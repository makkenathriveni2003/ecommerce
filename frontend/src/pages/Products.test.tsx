import { screen, fireEvent } from "@testing-library/react"
import { describe, it, expect } from "vitest"
import Products from "./Products"
import { renderApp } from "../test/testUtils"

describe("Products page with Search", () => {
  it("renders catalog products and filters by search query", async () => {
    renderApp(<Products />)

    // Wait for products to load from MSW handlers
    expect(await screen.findByRole("heading", { name: "Headphones" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Watch" })).toBeInTheDocument()

    // Test search functionality
    const searchInput = screen.getByRole("searchbox", { name: /Search products/i })
    fireEvent.change(searchInput, { target: { value: "Watch" } })

    expect(screen.getByRole("heading", { name: "Watch" })).toBeInTheDocument()
    expect(screen.queryByRole("heading", { name: "Headphones" })).not.toBeInTheDocument()

    // Clear search
    const clearBtn = screen.getByRole("button", { name: /Clear search/i })
    fireEvent.click(clearBtn)

    expect(screen.getByRole("heading", { name: "Headphones" })).toBeInTheDocument()
  })

  it("displays friendly empty message when search yields no matches", async () => {
    renderApp(<Products />)

    expect(await screen.findByRole("heading", { name: "Headphones" })).toBeInTheDocument()

    const searchInput = screen.getByRole("searchbox", { name: /Search products/i })
    fireEvent.change(searchInput, { target: { value: "NonExistentItem999" } })

    expect(screen.getByText(/No products matched “NonExistentItem999”/i)).toBeInTheDocument()
  })
})
