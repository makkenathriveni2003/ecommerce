import { describe, it, expect, beforeEach } from "vitest"
import { useNotificationStore } from "./notificationStore"

describe("useNotificationStore", () => {
  beforeEach(() => {
    useNotificationStore.getState().clearAll()
  })

  it("adds notifications and updates unread count", () => {
    const store = useNotificationStore.getState()
    expect(store.unreadCount).toBe(0)

    store.addNotification({
      id: "test-1",
      title: "Order Confirmed",
      message: "Your order #1 has been placed.",
      type: "confirmed",
    })

    const state = useNotificationStore.getState()
    expect(state.notifications).toHaveLength(1)
    expect(state.unreadCount).toBe(1)
    expect(state.notifications[0].title).toBe("Order Confirmed")
  })

  it("marks a notification as read and decrements unread count", () => {
    const store = useNotificationStore.getState()
    store.addNotification({
      id: "n-1",
      title: "Order Shipped",
      message: "Order #2 shipped",
      type: "shipped",
    })

    expect(useNotificationStore.getState().unreadCount).toBe(1)
    store.markAsRead("n-1")

    const updated = useNotificationStore.getState()
    expect(updated.unreadCount).toBe(0)
    expect(updated.notifications[0].read).toBe(true)
  })

  it("marks all notifications as read", () => {
    const store = useNotificationStore.getState()
    store.addNotification({ id: "n-1", title: "A", message: "A", type: "info" })
    store.addNotification({ id: "n-2", title: "B", message: "B", type: "info" })

    expect(useNotificationStore.getState().unreadCount).toBe(2)
    store.markAllAsRead()
    expect(useNotificationStore.getState().unreadCount).toBe(0)
  })

  it("clears all notifications", () => {
    const store = useNotificationStore.getState()
    store.addNotification({ id: "n-1", title: "A", message: "A", type: "info" })
    store.clearAll()

    expect(useNotificationStore.getState().notifications).toHaveLength(0)
    expect(useNotificationStore.getState().unreadCount).toBe(0)
  })
})
