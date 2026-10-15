import { render, screen, fireEvent } from "@testing-library/react"
import { describe, it, expect, beforeEach, vi } from "vitest"
import LiveChatWidget from "./LiveChatWidget"
import { useChatStore } from "../store/chatStore"
import { useAuthStore } from "../store/authStore"

describe("LiveChatWidget", () => {
  const mockSendMessage = vi.fn()

  beforeEach(() => {
    mockSendMessage.mockReset()
    useChatStore.setState({
      messages: [],
      isOpen: false,
      activeCustomer: null,
      adminOnline: true,
      unreadCount: 0,
    })
    useAuthStore.setState({
      user: { id: 2, name: "Shopper User", email: "shopper@example.com", role: "shopper" },
      token: "test-token",
      isAuthenticated: true,
    })
  })

  it("renders floating chat trigger button with WebSocket status", () => {
    render(<LiveChatWidget wsStatus="OPEN" sendMessage={mockSendMessage} />)

    const btn = screen.getByRole("button", { name: /Open Live Chat/i })
    expect(btn).toBeInTheDocument()
    expect(screen.getByText("Live Chat")).toBeInTheDocument()
  })

  it("opens chat window and allows typing and sending messages", () => {
    mockSendMessage.mockReturnValue(true)

    render(<LiveChatWidget wsStatus="OPEN" sendMessage={mockSendMessage} />)
    fireEvent.click(screen.getByRole("button", { name: /Open Live Chat/i }))

    expect(screen.getByRole("dialog", { name: /Customer support live chat/i })).toBeInTheDocument()
    expect(screen.getByText(/ShopZone Live Support/i)).toBeInTheDocument()

    const input = screen.getByPlaceholderText(/Type your message here/i)
    fireEvent.change(input, { target: { value: "Where is my order?" } })

    const sendBtn = screen.getByRole("button", { name: /Send message/i })
    fireEvent.click(sendBtn)

    expect(mockSendMessage).toHaveBeenCalledWith({
      type: "CHAT_MESSAGE",
      text: "Where is my order?",
      recipient_email: "admin",
    })
  })
})
