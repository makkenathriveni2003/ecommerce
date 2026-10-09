import { describe, it, expect, beforeEach } from "vitest"
import { useChatStore } from "./chatStore"

describe("useChatStore", () => {
  beforeEach(() => {
    useChatStore.setState({
      messages: [],
      isOpen: false,
      activeCustomer: null,
      adminOnline: false,
      unreadCount: 0,
    })
  })

  it("adds chat messages and updates unread count when window is closed", () => {
    const store = useChatStore.getState()
    store.addMessage({
      id: 1,
      sender_email: "customer@example.com",
      sender_name: "Customer",
      sender_role: "shopper",
      recipient_email: "admin",
      text: "Hello support!",
      created_at: new Date().toISOString(),
    })

    const state = useChatStore.getState()
    expect(state.messages).toHaveLength(1)
    expect(state.unreadCount).toBe(1)
    expect(state.messages[0].text).toBe("Hello support!")
  })

  it("resets unread count when chat window is opened", () => {
    const store = useChatStore.getState()
    store.addMessage({
      id: 1,
      sender_email: "c@example.com",
      sender_name: "C",
      sender_role: "shopper",
      recipient_email: "admin",
      text: "Hi",
      created_at: new Date().toISOString(),
    })
    expect(useChatStore.getState().unreadCount).toBe(1)

    store.setIsOpen(true)
    expect(useChatStore.getState().isOpen).toBe(true)
    expect(useChatStore.getState().unreadCount).toBe(0)
  })

  it("toggles admin online status", () => {
    const store = useChatStore.getState()
    expect(store.adminOnline).toBe(false)
    store.setAdminOnline(true)
    expect(useChatStore.getState().adminOnline).toBe(true)
  })
})
