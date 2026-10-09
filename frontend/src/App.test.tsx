import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { within } from "@testing-library/react"
import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"
import App from "./App"
import { createProduct } from "./services/productService"
import { server } from "./test/server"
import { renderApp } from "./test/testUtils"

describe("storefront user journeys", () => {
  it("adds a product to the bag, changes quantity, and removes it", async () => {
    const user = userEvent.setup()
    renderApp(<App />)

    expect(await screen.findByRole("heading", { name: "Headphones" })).toBeVisible()
    await user.click(screen.getAllByRole("button", { name: "Add to Cart" })[0])
    await user.click(screen.getByRole("link", { name: /Bag 1/ }))

    expect(await screen.findByRole("heading", { name: "Your bag." })).toBeVisible()
    const summary = screen.getByRole("complementary", { name: "Order summary" })
    expect(within(summary).getAllByText("₹3,000")).toHaveLength(2)
    await user.click(screen.getByRole("button", { name: "Increase Headphones quantity" }))
    expect(within(summary).getAllByText("₹6,000")).toHaveLength(2)
    await user.click(screen.getByRole("button", { name: "Remove Headphones from bag" }))

    expect(screen.getByText("Your bag is taking a break.")).toBeVisible()
    await waitFor(() => expect(screen.getByRole("link", { name: /Bag 0/ })).toBeVisible())
  })

  it("lets a user register and sign in but restricts product management to admins", async () => {
    const user = userEvent.setup()
    server.use(
      http.post("*/auth/register", () =>
        HttpResponse.json({ success: true, message: "Registration successful" }),
      ),
      http.post("*/auth/login", () =>
        HttpResponse.json({
          success: true,
          token: "test-token",
          user: { name: "Shop Owner", email: "owner@example.com", role: "shopper" },
        }),
      ),
      http.post("*/products", async ({ request }) => {
        expect(request.headers.get("Authorization")).toBe("Bearer test-token")
        return HttpResponse.json({
          id: 99,
          name: "Test lamp",
          price: 25,
          category: "Home",
          image: "https://example.com/lamp.jpg",
        })
      }),
    )
    renderApp(<App />)

    await user.click(screen.getByRole("link", { name: "Sign in" }))
    await user.click(await screen.findByRole("button", { name: "Create an account" }))
    await user.type(screen.getByLabelText("Name"), "Shop Owner")
    await user.type(screen.getByLabelText("Email"), "owner@example.com")
    await user.type(screen.getByLabelText("Password"), "secure-password")
    await user.click(screen.getByRole("button", { name: "Create account" }))

    expect(await screen.findByText("Hi, Shop Owner")).toBeVisible()
    expect(await screen.findByRole("heading", { name: "Administrator access required." })).toBeVisible()
    expect(screen.queryByLabelText("Product name")).not.toBeInTheDocument()
    expect(screen.queryByRole("link", { name: "Admin" })).not.toBeInTheDocument()
    expect(screen.queryByRole("link", { name: "Add products" })).not.toBeInTheDocument()
    server.use(
      http.post("*/products", () =>
        HttpResponse.json(
          { detail: "Administrator access required." },
          { status: 403 },
        ),
      ),
    )
    await expect(
      createProduct(
        { name: "Test lamp", price: 25, category: "Home", image: "https://example.com/lamp.jpg" },
        "test-token",
      ),
    ).rejects.toThrow("You don’t have permission to do that.")
  })

  it("explains when the backend cannot be reached during sign-in", async () => {
    const user = userEvent.setup()
    server.use(
      http.post("*/auth/login", () => HttpResponse.error()),
    )
    renderApp(<App />)

    await user.click(screen.getByRole("link", { name: "Sign in" }))
    await user.type(screen.getByLabelText("Email"), "owner@example.com")
    await user.type(screen.getByLabelText("Password"), "secure-password")
    await user.click(screen.getByRole("button", { name: "Sign in" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Cannot reach the backend at http://127.0.0.1:8000.",
    )
  })

  it("loads the graphic shirts with the next product page", async () => {
    const user = userEvent.setup()
    renderApp(<App />)

    expect(await screen.findByRole("heading", { name: "Headphones" })).toBeVisible()
    await user.click(screen.getByRole("button", { name: "Load more products" }))

    expect(await screen.findByRole("heading", { name: "Film Night Graphic Tee" })).toBeVisible()
    expect(screen.getAllByText("Shirts")).toHaveLength(2)
  })

  it("switches between light and dark themes and remembers the choice", async () => {
    const user = userEvent.setup()
    renderApp(<App />)

    await user.click(screen.getByRole("button", { name: "Switch to dark mode" }))
    expect(document.documentElement).toHaveAttribute("data-theme", "dark")
    expect(localStorage.getItem("daylight-theme")).toBe("dark")

    await user.click(screen.getByRole("button", { name: "Switch to light mode" }))
    expect(document.documentElement).toHaveAttribute("data-theme", "light")
    expect(localStorage.getItem("daylight-theme")).toBe("light")
  })
})
