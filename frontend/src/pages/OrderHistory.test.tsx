import { screen } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"
import { useAuthStore } from "../store/authStore"
import { server } from "../test/server"
import { renderApp } from "../test/testUtils"
import OrderHistory from "./OrderHistory"

const sampleOrder = {
  id: 42,
  status: "processing",
  total: 4500,
  created_at: "2026-10-01T10:30:00Z",
  items: [
    { id: 8, product_id: 2, name: "Watch", quantity: 1, unit_price: 4500 },
  ],
}

describe("order history", () => {
  it("asks shoppers to sign in", () => {
    renderApp(<OrderHistory />, { route: "/orders" })
    expect(screen.getByRole("alert")).toHaveTextContent("Sign in to view your orders.")
  })

  it("renders the authenticated user's saved orders from the API", async () => {
    useAuthStore.getState().login(
      { name: "Shopper", email: "shopper@example.com", role: "shopper" },
      "history-token",
    )
    server.use(
      http.get("*/orders", ({ request }) => {
        expect(request.headers.get("Authorization")).toBe("Bearer history-token")
        return HttpResponse.json([sampleOrder])
      }),
    )
    renderApp(<OrderHistory />, { route: "/orders" })

    expect(await screen.findByText("ORDER #42")).toBeVisible()
    expect(screen.getByText("Watch × 1")).toBeVisible()
    expect(screen.getAllByText("₹4,500")).toHaveLength(2)
    expect(screen.getByText("processing")).toBeVisible()
  })

  it("shows the order confirmation after checkout navigation", async () => {
    useAuthStore.getState().login(
      { name: "Shopper", email: "shopper@example.com", role: "shopper" },
      "history-token",
    )
    server.use(http.get("*/orders", () => HttpResponse.json([sampleOrder])))
    renderApp(<OrderHistory />, { route: "/orders?placed=42" })

    expect(await screen.findByText("Thank you — order #42 was placed successfully.")).toBeVisible()
  })

  it("shows an empty state when the user has no previous orders", async () => {
    useAuthStore.getState().login(
      { name: "Shopper", email: "shopper@example.com", role: "shopper" },
      "history-token",
    )
    server.use(http.get("*/orders", () => HttpResponse.json([])))
    renderApp(<OrderHistory />, { route: "/orders" })

    expect(await screen.findByText("No orders yet.")).toBeVisible()
  })

  it("shows an API error instead of pretending order history is empty", async () => {
    useAuthStore.getState().login(
      { name: "Shopper", email: "shopper@example.com", role: "shopper" },
      "history-token",
    )
    server.use(
      http.get("*/orders", () =>
        HttpResponse.json({ detail: "Database unavailable" }, { status: 503 }),
      ),
    )
    renderApp(<OrderHistory />, { route: "/orders" })

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The server encountered a problem. Please try again.",
    )
  })
})
