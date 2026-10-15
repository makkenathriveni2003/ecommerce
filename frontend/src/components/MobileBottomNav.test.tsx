import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"
import { renderApp } from "../test/testUtils"
import MobileBottomNav from "./MobileBottomNav"

describe("MobileBottomNav Component", () => {
  it("renders mobile navigation items and cart count", () => {
    const handleOpenProfile = vi.fn()
    renderApp(
      <MobileBottomNav
        cartCount={3}
        onOpenProfile={handleOpenProfile}
        user={null}
      />
    )

    expect(screen.getByRole("link", { name: "Shop" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "AI Assistant" })).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /Bag, 3 items/i })).toBeInTheDocument()
    expect(screen.getByText("3")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "Orders" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Open Profile and Account" })).toBeInTheDocument()
  })

  it("calls onOpenProfile when profile button is tapped", async () => {
    const user = userEvent.setup()
    const handleOpenProfile = vi.fn()
    renderApp(
      <MobileBottomNav
        cartCount={0}
        onOpenProfile={handleOpenProfile}
        user={{ name: "John Doe", email: "john@example.com", role: "shopper" }}
      />
    )

    const profileBtn = screen.getByRole("button", { name: "Open Profile and Account" })
    await user.click(profileBtn)
    expect(handleOpenProfile).toHaveBeenCalledTimes(1)
  })

  it("shows Admin label when user is administrator", () => {
    renderApp(
      <MobileBottomNav
        cartCount={0}
        onOpenProfile={vi.fn()}
        user={{ name: "Admin User", email: "admin@smartbazaar.com", role: "admin" }}
      />
    )

    expect(screen.getByText("Admin")).toBeInTheDocument()
  })
})
