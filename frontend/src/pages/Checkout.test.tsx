import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"
import { useAuthStore } from "../store/authStore"
import { useCartStore } from "../store/cartStore"
import { server } from "../test/server"
import { renderApp } from "../test/testUtils"
import App from "../App"

const user = { name: "Shopper", email: "shopper@example.com", role: "shopper" as const }
const product = {
  id: 1,
  name: "Headphones",
  price: 3000,
  category: "Accessories",
  image: "https://example.com/headphones.jpg",
}
const order = {
  id: 24,
  status: "pending",
  total: 6000,
  created_at: "2026-10-06T05:00:00Z",
  items: [
    { id: 1, product_id: 1, name: "Headphones", quantity: 2, unit_price: 3000 },
  ],
}

async function prepareCheckout() {
  useAuthStore.getState().login(user, "checkout-test-token")
  useCartStore.getState().addToCart(product)
  useCartStore.getState().increaseQuantity(product.id)
  renderApp(<App />, { route: "/checkout" })
  await screen.findByLabelText("Full name")
}

async function fillValidCheckout() {
  await prepareCheckout()
  const visitor = userEvent.setup()
  await visitor.type(screen.getByLabelText("Phone"), "9876543210")
  await visitor.type(screen.getByLabelText("Address"), "123 Main Street")
  await visitor.type(screen.getByLabelText("City"), "Mumbai")
  await visitor.type(screen.getByLabelText("State"), "Maharashtra")
  await visitor.type(screen.getByLabelText("Pincode"), "400001")
  return visitor
}

describe("checkout", () => {
  it("requires a signed-in account", async () => {
    renderApp(<App />, { route: "/checkout" })
    expect(await screen.findByRole("alert")).toHaveTextContent("Sign in before checking out.")
  })

  it("shows an empty-cart state when there is nothing to order", async () => {
    useAuthStore.getState().login(user, "checkout-test-token")
    renderApp(<App />, { route: "/checkout" })
    expect(await screen.findByRole("heading", { name: "Your bag is empty." })).toBeVisible()
  })

  it("renders checkout fields and the current cart summary", async () => {
    await prepareCheckout()
    expect(screen.getByLabelText("Full name")).toHaveValue("Shopper")
    expect(screen.getByLabelText("Email")).toHaveValue("shopper@example.com")
    expect(screen.getByLabelText("Payment method")).toHaveValue("cash_on_delivery")
    expect(screen.getAllByText("₹6,000")).toHaveLength(2)
  })

  it("shows required field validation errors", async () => {
    const visitor = userEvent.setup()
    await prepareCheckout()
    await visitor.clear(screen.getByLabelText("Full name"))
    await visitor.click(screen.getByRole("button", { name: "Place order" }))
    expect(await screen.findByText("Enter your full name.")).toBeVisible()
    expect(screen.getByText("Enter a valid 10-digit mobile number.")).toBeVisible()
    expect(screen.getByText("Enter a complete street address.")).toBeVisible()
  })

  it("rejects an invalid email", async () => {
    const visitor = userEvent.setup()
    await prepareCheckout()
    await visitor.clear(screen.getByLabelText("Email"))
    await visitor.type(screen.getByLabelText("Email"), "not-an-email")
    await visitor.click(screen.getByRole("button", { name: "Place order" }))
    expect(await screen.findByText("Enter a valid email.")).toBeVisible()
  })

  it("rejects an invalid pincode", async () => {
    const visitor = userEvent.setup()
    await prepareCheckout()
    await visitor.type(screen.getByLabelText("Pincode"), "123")
    await visitor.click(screen.getByRole("button", { name: "Place order" }))
    expect(await screen.findByText("Enter a valid 6-digit pincode.")).toBeVisible()
  })

  it("sends authenticated items to the backend and clears cart after success", async () => {
    let submitted: Record<string, unknown> | null = null
    server.use(
      http.post("*/orders", async ({ request }) => {
        expect(request.headers.get("Authorization")).toBe("Bearer checkout-test-token")
        submitted = await request.json() as Record<string, unknown>
        return HttpResponse.json({ success: true, message: "ok", order })
      }),
      http.get("*/orders", () => HttpResponse.json([order])),
    )
    const visitor = await fillValidCheckout()
    await visitor.click(screen.getByRole("button", { name: "Place order" }))
    expect(await screen.findByText("Thank you — order #24 was placed successfully.")).toBeVisible()
    expect(submitted).toMatchObject({
      email: "shopper@example.com",
      items: [{ product_id: 1, quantity: 2 }],
      payment_method: "cash_on_delivery",
    })
    await waitFor(() => expect(useCartStore.getState().cart).toEqual([]))
  })

  it("keeps the cart and shows backend validation errors when order creation fails", async () => {
    server.use(
      http.post("*/orders", () =>
        HttpResponse.json({ detail: "One or more products were not found" }, { status: 404 }),
      ),
    )
    const visitor = await fillValidCheckout()
    await visitor.click(screen.getByRole("button", { name: "Place order" }))
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The requested item could not be found.",
    )
    expect(useCartStore.getState().cart).toHaveLength(1)
  })

  it("shows a friendly server error and keeps the cart when order placement fails", async () => {
    server.use(
      http.post("*/orders", () =>
        HttpResponse.json({ detail: "Database password or query details" }, { status: 500 }),
      ),
    )
    const visitor = await fillValidCheckout()
    await visitor.click(screen.getByRole("button", { name: "Place order" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The server encountered a problem. Please try again.",
    )
    expect(screen.queryByText(/Database password|query details/)).not.toBeInTheDocument()
    expect(useCartStore.getState().cart).toHaveLength(1)
  })
})
