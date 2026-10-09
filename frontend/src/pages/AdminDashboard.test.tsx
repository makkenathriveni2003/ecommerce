import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"
import { useAuthStore } from "../store/authStore"
import { server } from "../test/server"
import { renderApp } from "../test/testUtils"
import AdminDashboard from "./AdminDashboard"

const existingProduct = {
  id: 5,
  name: "Desk lamp",
  price: 1200,
  category: "Home",
  image: "https://example.com/lamp.jpg",
}
const adminOrder = {
  id: 19,
  status: "pending",
  total: 2400,
  created_at: "2026-10-05T10:00:00Z",
  email: "buyer@example.com",
  full_name: "Buyer User",
  phone: "9876543210",
  address: "1 Main Road",
  city: "Mumbai",
  state: "Maharashtra",
  pincode: "400001",
  payment_method: "cash_on_delivery",
  items: [
    { id: 1, product_id: 5, name: "Desk lamp", quantity: 2, unit_price: 1200 },
  ],
}

function signIn(role: "shopper" | "admin") {
  useAuthStore.getState().login(
    { name: "Account", email: "account@example.com", role },
    "admin-test-token",
  )
}

describe("admin dashboard", () => {
  it("denies access to shopper accounts", () => {
    signIn("shopper")
    renderApp(<AdminDashboard />, { route: "/admin" })
    expect(screen.getByRole("heading", { name: "Admin access required." })).toBeVisible()
  })

  it("loads products and customer order information from admin APIs", async () => {
    signIn("admin")
    server.use(
      http.get("*/admin/products", () => HttpResponse.json([existingProduct])),
      http.get("*/admin/orders", ({ request }) => {
        expect(request.headers.get("Authorization")).toBe("Bearer admin-test-token")
        return HttpResponse.json([adminOrder])
      }),
    )
    renderApp(<AdminDashboard />, { route: "/admin" })

    expect(await screen.findByText("Desk lamp")).toBeVisible()
    const row = screen.getByText("Buyer User").closest("tr")
    expect(row?.textContent).toContain("buyer@example.com")
    expect(row?.textContent).toContain("9876543210")
    expect(row?.textContent).toContain("1 Main Road")
    expect(screen.getByText("Desk lamp × 2")).toBeVisible()
    expect(screen.getByLabelText("Update status for order 19")).toHaveValue("pending")
  })

  it("creates, updates, and deletes products through protected APIs", async () => {
    signIn("admin")
    let products = [existingProduct]
    server.use(
      http.get("*/admin/products", () => HttpResponse.json(products)),
      http.get("*/admin/orders", () => HttpResponse.json([])),
      http.post("*/admin/products", async ({ request }) => {
        expect(request.headers.get("Authorization")).toBe("Bearer admin-test-token")
        const body = await request.json() as Omit<typeof existingProduct, "id">
        const saved = { id: 9, ...body }
        products = [...products, saved]
        return HttpResponse.json(saved)
      }),
      http.put("*/admin/products/:productId", async ({ request, params }) => {
        const body = await request.json() as Omit<typeof existingProduct, "id">
        const saved = { id: Number(params.productId), ...body }
        products = products.map((item) => item.id === saved.id ? saved : item)
        return HttpResponse.json(saved)
      }),
      http.delete("*/admin/products/:productId", ({ params }) => {
        products = products.filter((item) => item.id !== Number(params.productId))
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const visitor = userEvent.setup()
    renderApp(<AdminDashboard />, { route: "/admin" })

    await visitor.type(screen.getByLabelText("Name"), "Table lamp")
    await visitor.type(screen.getByLabelText("Price"), "800")
    await visitor.type(screen.getByLabelText("Category"), "Home")
    await visitor.type(screen.getByLabelText("Image URL"), "https://example.com/table.jpg")
    await visitor.click(screen.getByRole("button", { name: "Create product" }))
    expect(await screen.findByText("Table lamp")).toBeVisible()

    const tableRow = screen.getByText("Table lamp").closest("tr")
    expect(tableRow).not.toBeNull()
    await visitor.click(within(tableRow!).getByRole("button", { name: "Edit" }))
    const nameInput = screen.getByLabelText("Name")
    await visitor.clear(nameInput)
    await visitor.type(nameInput, "Updated table lamp")
    await visitor.click(screen.getByRole("button", { name: "Save changes" }))
    expect(await screen.findByText("Updated table lamp")).toBeVisible()

    const updatedRow = screen.getByText("Updated table lamp").closest("tr")
    expect(updatedRow).not.toBeNull()
    await visitor.click(within(updatedRow!).getByRole("button", { name: "Delete" }))
    await waitFor(() => expect(screen.queryByText("Updated table lamp")).not.toBeInTheDocument())
  })

  it("updates order status through the admin endpoint", async () => {
    signIn("admin")
    let status = "pending"
    server.use(
      http.get("*/admin/products", () => HttpResponse.json([])),
      http.get("*/admin/orders", () => HttpResponse.json([{ ...adminOrder, status }])),
      http.patch("*/admin/orders/19/status", async ({ request }) => {
        const body = await request.json() as { status: string }
        status = body.status
        return HttpResponse.json({ ...adminOrder, status })
      }),
    )
    const visitor = userEvent.setup()
    renderApp(<AdminDashboard />, { route: "/admin" })

    const statusSelect = await screen.findByLabelText("Update status for order 19")
    await visitor.selectOptions(statusSelect, "shipped")
    await waitFor(() => expect(status).toBe("shipped"))
  })
})
