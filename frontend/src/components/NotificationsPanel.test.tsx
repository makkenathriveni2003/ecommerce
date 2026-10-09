import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, beforeEach } from "vitest"
import NotificationsPanel from "./NotificationsPanel"
import { useNotificationStore } from "../store/notificationStore"

describe("NotificationsPanel", () => {
  beforeEach(() => {
    useNotificationStore.getState().clearAll()
    useNotificationStore.setState({ isOpen: false })
  })

  it("renders bell button and badge when unread notifications exist", () => {
    useNotificationStore.getState().addNotification({
      id: "n-1",
      title: "Order Shipped",
      message: "Order #123 is on the way!",
      type: "shipped",
    })

    render(<NotificationsPanel />)

    const bellBtn = screen.getByRole("button", { name: /Notifications/i })
    expect(bellBtn).toBeInTheDocument()
    expect(screen.getByText("1")).toBeInTheDocument()
  })

  it("opens panel on click and displays notification items", () => {
    useNotificationStore.getState().addNotification({
      id: "n-1",
      title: "Order Delivered",
      message: "Your package has arrived.",
      type: "delivered",
    })

    render(<NotificationsPanel />)
    const bellBtn = screen.getByRole("button", { name: /Notifications/i })
    fireEvent.click(bellBtn)

    expect(screen.getByRole("dialog", { name: /Notifications panel/i })).toBeInTheDocument()
    expect(screen.getByText("Order Delivered")).toBeInTheDocument()
    expect(screen.getByText("Your package has arrived.")).toBeInTheDocument()
  })

  it("marks all notifications as read when action clicked", () => {
    useNotificationStore.getState().addNotification({
      id: "n-1",
      title: "Order Confirmed",
      message: "Confirmed",
      type: "confirmed",
    })

    render(<NotificationsPanel />)
    fireEvent.click(screen.getByRole("button", { name: /Notifications/i }))

    const markAllBtn = screen.getByRole("button", { name: /Mark all read/i })
    fireEvent.click(markAllBtn)

    expect(useNotificationStore.getState().unreadCount).toBe(0)
  })
})
