import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"
import { useCartStore } from "../store/cartStore"
import { server } from "../test/server"
import { testProducts } from "../test/products"
import { renderApp } from "../test/testUtils"
import App from "../App"

describe("product details", () => {
  it("loads a product from the product details API", async () => {
    server.use(
      http.get("*/products/1", () => HttpResponse.json(testProducts[0])),
    )
    renderApp(<App />, { route: "/products/1" })
    expect(await screen.findByRole("heading", { name: "Headphones" })).toBeVisible()
    expect(screen.getByText("₹3,000")).toBeVisible()
  })

  it("adds the product to the shared cart from its detail page", async () => {
    server.use(
      http.get("*/products/1", () => HttpResponse.json(testProducts[0])),
    )
    const visitor = userEvent.setup()
    renderApp(<App />, { route: "/products/1" })
    await visitor.click(await screen.findByRole("button", { name: "Add to Cart" }))
    expect(useCartStore.getState().getCartItemCount()).toBe(1)
  })

  it("shows a friendly not-found message for an unknown product", async () => {
    server.use(
      http.get("*/products/999", () =>
        HttpResponse.json({ detail: "Product not found" }, { status: 404 }),
      ),
    )
    renderApp(<App />, { route: "/products/999" })
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The requested item could not be found.",
    )
  })

  it("rejects malformed product data from the API", async () => {
    server.use(
      http.get("*/products/1", () => HttpResponse.json({ id: "bad" })),
    )
    renderApp(<App />, { route: "/products/1" })
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The product API returned an invalid response",
    )
  })
})
