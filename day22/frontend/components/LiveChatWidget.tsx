import { useEffect, useRef, useState, type FormEvent } from "react"
import { useChatStore } from "../store/chatStore"
import { useAuthStore } from "../store/authStore"
import { getChatMessages, sendChatMessage } from "../services/chatService"
import type { WebSocketStatus } from "../../types"

interface LiveChatWidgetProps {
  wsStatus: WebSocketStatus
  sendMessage: (data: unknown) => boolean
}

export default function LiveChatWidget({
  wsStatus,
  sendMessage,
}: LiveChatWidgetProps) {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const {
    messages,
    isOpen,
    setIsOpen,
    activeCustomer,
    setActiveCustomer,
    adminOnline,
    addMessage,
    setMessages,
    unreadCount,
  } = useChatStore()

  const [inputText, setInputText] = useState("")
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const isAdmin = user?.role === "admin"

  // Load chat history when opened and authenticated
  useEffect(() => {
    if (isOpen && token) {
      let isMounted = true
      const controller = new AbortController()

      void getChatMessages(token, activeCustomer ?? undefined, controller.signal)
        .then((data) => {
          if (isMounted && data.length > 0) {
            setMessages(data)
          }
        })
        .catch(() => {
          // silently handle
        })

      return () => {
        isMounted = false
        controller.abort()
      }
    }
  }, [isOpen, token, activeCustomer, setMessages])

  // Scroll to bottom on new message
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView?.({ behavior: "smooth" })
    }
  }, [messages, isOpen])


  // Extract unique customer emails for admin view
  const customerConversations = Array.from(
    new Set(
      messages
        .filter((m) => m.sender_role !== "admin")
        .map((m) => m.sender_email),
    ),
  )

  // Filter messages for current conversation
  const displayedMessages = messages.filter((m) => {
    if (!isAdmin) return true
    if (!activeCustomer) return true
    return (
      m.sender_email.toLowerCase() === activeCustomer.toLowerCase() ||
      m.recipient_email.toLowerCase() === activeCustomer.toLowerCase()
    )
  })

  const handleSend = async (e: FormEvent) => {
    e.preventDefault()
    const text = inputText.trim()
    if (!text || isSending) return

    setIsSending(true)
    const recipient = isAdmin
      ? (activeCustomer || "shopper@example.com")
      : "admin"

    // Try sending through WebSocket first
    const sentWs = sendMessage({
      type: "CHAT_MESSAGE",
      text,
      recipient_email: recipient,
    })

    if (!sentWs && token) {
      // Fallback to REST API if WebSocket is not open
      try {
        const result = await sendChatMessage(token, text, recipient)
        if (result.success && result.data) {
          addMessage(result.data)
        }
      } catch {
        // error handling
      }
    }

    setInputText("")
    setIsSending(false)
  }

  return (
    <div className="live-chat-container">
      {/* Floating Chat Trigger Button */}
      {!isOpen && (
        <button
          type="button"
          className="chat-floating-btn"
          onClick={() => setIsOpen(true)}
          aria-label={`Open Live Chat (${unreadCount} unread)`}
        >
          <span className="chat-btn-icon" aria-hidden="true">💬</span>
          <span className="chat-btn-label">Live Chat</span>
          {unreadCount > 0 && (
            <span className="chat-unread-badge">{unreadCount}</span>
          )}
          <span
            className={`connection-dot ${wsStatus === "OPEN" ? "dot-online" : "dot-offline"}`}
            title={`WebSocket: ${wsStatus}`}
          />
        </button>
      )}

      {/* Chat Window Modal */}
      {isOpen && (
        <div className="chat-window" role="dialog" aria-label="Customer support live chat">
          <header className="chat-header">
            <div className="chat-header-info">
              <div className="chat-avatar" aria-hidden="true">
                {isAdmin ? "👑" : "💬"}
              </div>
              <div>
                <h4>{isAdmin ? "Admin Support Console" : "ShopZone Live Support"}</h4>
                <div className="chat-status-indicator">
                  <span
                    className={`status-indicator-dot ${
                      adminOnline || isAdmin ? "online" : "offline"
                    }`}
                  />
                  <span>
                    {isAdmin
                      ? `Agent: ${user?.name ?? "Admin"}`
                      : adminOnline
                        ? "Support Online"
                        : "Support Agent Available"}
                  </span>
                  <span className="ws-pill-tag">WS {wsStatus}</span>
                </div>
              </div>
            </div>

            <button
              type="button"
              className="chat-close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat window"
            >
              ✕
            </button>
          </header>

          {/* Admin Customer Conversation Tabs */}
          {isAdmin && customerConversations.length > 0 && (
            <div className="admin-chat-tabs" aria-label="Customer conversations">
              <button
                type="button"
                className={`tab-btn ${activeCustomer === null ? "active" : ""}`}
                onClick={() => setActiveCustomer(null)}
              >
                All Messages
              </button>
              {customerConversations.map((email) => (
                <button
                  key={email}
                  type="button"
                  className={`tab-btn ${activeCustomer === email ? "active" : ""}`}
                  onClick={() => setActiveCustomer(email)}
                >
                  {email.split("@")[0]}
                </button>
              ))}
            </div>
          )}

          {/* Chat Messages Thread */}
          <div className="chat-messages-scroll" role="log" aria-live="polite">
            {displayedMessages.length === 0 ? (
              <div className="chat-empty-state">
                <span className="empty-chat-icon" aria-hidden="true">💬</span>
                <h5>Welcome to ShopZone Support!</h5>
                <p>
                  Have questions about products, delivery, or your order? Type a
                  message below to start chatting with us in real time.
                </p>
              </div>
            ) : (
              displayedMessages.map((msg, index) => {
                const isOwn =
                  user &&
                  msg.sender_email.toLowerCase() === user.email.toLowerCase()

                return (
                  <div
                    key={msg.id || index}
                    className={`chat-bubble-row ${isOwn ? "own-row" : "remote-row"}`}
                  >
                    <div className={`chat-bubble ${isOwn ? "bubble-own" : "bubble-remote"}`}>
                      <div className="bubble-sender">
                        <span>{msg.sender_name}</span>
                        <span className="sender-role-tag">{msg.sender_role}</span>
                      </div>
                      <p className="bubble-text">{msg.text}</p>
                      <time className="bubble-time">
                        {new Date(msg.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </time>
                    </div>
                  </div>
                )
              })
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Message Input Form */}
          <form className="chat-input-form" onSubmit={handleSend}>
            <input
              type="text"
              className="chat-text-input"
              placeholder={
                isAdmin
                  ? `Reply to ${activeCustomer ?? "customer"}...`
                  : "Type your message here..."
              }
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={isSending}
              aria-label="Chat message"
            />
            <button
              type="submit"
              className="chat-send-btn"
              disabled={!inputText.trim() || isSending}
              aria-label="Send message"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
