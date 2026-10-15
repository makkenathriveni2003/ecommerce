import React, { useCallback, useEffect, useRef, useState } from "react"
import { useAuthStore } from "../store/authStore"
import { getAIStatus, reindexCatalog, streamAIChat } from "../services/aiService"
import { AICitationCard } from "../components/AICitationCard"
import { GenZLogo } from "../components/GenZLogo"
import type { AIChatMessage, AICitation, AIStatus } from "../../types"

const SAMPLE_PROMPTS = [
  "Which headphones are available under ₹3,000?",
  "Show me laptops and computers in stock",
  "Do you have jewellery like necklaces or earrings?",
  "What running shoes or sneakers are available?",
  "Recommend a stylish women's dress under ₹2,000",
]

export const AiAssistant: React.FC = () => {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)

  const [messages, setMessages] = useState<AIChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Hello! I am the GenZ Zone AI Shopping Assistant. Ask me anything about our trending Ganzee apparel, current pricing in ₹ (INR), stock availability, or recommendations!",
      provider: "System",
      timestamp: "Today",
    },
  ])

  const [input, setInput] = useState("")
  const [isGenerating, setIsGenerating] = useState(false)
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null)
  const [reindexing, setReindexing] = useState(false)
  const [reindexMessage, setReindexMessage] = useState<string | null>(null)

  const messageCounterRef = useRef(1)
  const abortControllerRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  // Scroll to bottom when messages update
  const scrollToBottom = useCallback(() => {
    if (typeof messagesEndRef.current?.scrollIntoView === "function") {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Fetch AI status on mount with cleanup
  useEffect(() => {
    let isCurrent = true
    void getAIStatus()
      .then((data) => {
        if (isCurrent) setAiStatus(data)
      })
      .catch(() => {})
    return () => {
      isCurrent = false
    }
  }, [])

  // Handle Admin Catalog Reindex
  const handleReindex = async () => {
    if (!token) return
    try {
      setReindexing(true)
      setReindexMessage(null)
      const res = await reindexCatalog(token)
      setReindexMessage(`Indexed ${res.products_indexed} products (${res.chunks_indexed} vectors).`)
      const updated = await getAIStatus()
      setAiStatus(updated)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Reindex failed"
      setReindexMessage(`Error: ${msg}`)
    } finally {
      setReindexing(false)
    }
  }

  // Stop Generation
  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
      setIsGenerating(false)
    }
  }

  // Send Message with Streaming
  const handleSend = async (textToSend?: string) => {
    const query = (textToSend ?? input).trim()
    if (!query || isGenerating) return

    setInput("")
    const currentCount = messageCounterRef.current
    messageCounterRef.current += 2
    const userMsgId = `user_${currentCount}`
    const assistantMsgId = `assistant_${currentCount + 1}`
    const timeStr = "Now"

    const userMessage: AIChatMessage = {
      id: userMsgId,
      role: "user",
      content: query,
      timestamp: timeStr,
    }

    const assistantPlaceholder: AIChatMessage = {
      id: assistantMsgId,
      role: "assistant",
      content: "",
      isStreaming: true,
      timestamp: timeStr,
      citations: [],
    }

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder])
    setIsGenerating(true)

    const controller = new AbortController()
    abortControllerRef.current = controller

    // Conversation history for context
    const conversationHistory = messages
      .filter((m) => m.id !== "welcome" && !m.error)
      .slice(-6)
      .map((m) => ({ role: m.role, content: m.content }))

    let accumulatedText = ""
    let currentProvider = "AI"
    let currentModel = ""
    let currentCitations: AICitation[] = []

    await streamAIChat({
      message: query,
      conversationHistory,
      signal: controller.signal,
      onProvider: (info) => {
        currentProvider = info.provider
        currentModel = info.model
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? { ...msg, provider: info.provider, model: info.model }
              : msg,
          ),
        )
      },
      onCitations: (citations) => {
        currentCitations = citations
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, citations } : msg,
          ),
        )
      },
      onChunk: (chunk) => {
        accumulatedText += chunk
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? { ...msg, content: accumulatedText }
              : msg,
          ),
        )
      },
      onProviderChange: (change) => {
        // Fallback occurred
        currentProvider = change.to
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  provider: `${change.to} (fallback from ${change.from})`,
                }
              : msg,
          ),
        )
      },
      onError: (errorMsg) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  isStreaming: false,
                  error: errorMsg,
                  content: accumulatedText || "Unable to complete response.",
                }
              : msg,
          ),
        )
        setIsGenerating(false)
        abortControllerRef.current = null
      },
      onDone: (summary) => {
        setIsGenerating(false)
        abortControllerRef.current = null
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content: accumulatedText || msg.content,
                  isStreaming: false,
                  provider: summary.provider || currentProvider,
                  model: currentModel,
                  citations: currentCitations.length > 0 ? currentCitations : msg.citations,
                }
              : msg,
          ),
        )
      },
    })
  }

  // Handle Retry
  const handleRetry = (failedMsg: AIChatMessage) => {
    // Find the preceding user message
    const index = messages.findIndex((m) => m.id === failedMsg.id)
    if (index > 0) {
      const priorUserMsg = messages[index - 1]
      if (priorUserMsg && priorUserMsg.role === "user") {
        // Remove both messages and re-send
        setMessages((prev) => prev.filter((m) => m.id !== failedMsg.id && m.id !== priorUserMsg.id))
        void handleSend(priorUserMsg.content)
      }
    }
  }

  // Keydown listener for Enter / Shift+Enter
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      void handleSend()
    }
  }

  return (
    <div className="ai-assistant-page">
      {/* Page Header */}
      <div className="ai-assistant-header">
        <div className="ai-header-titles">
          <h2 style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
            <GenZLogo size={28} />
            <span>GenZ Zone AI Assistant</span>
            <span className="ai-live-badge">RAG Powered</span>
          </h2>
          <p className="ai-header-desc">
            Ask natural shopping queries. Grounded in real GenZ Zone catalogue inventory, prices, and stock.
          </p>
        </div>

        {/* AI System Status & Admin Controls */}
        <div className="ai-header-status-panel">
          {!aiStatus && (
            <div className="ai-status-chips">
              <span className="ai-status-chip">Connecting to AI service...</span>
            </div>
          )}
          {aiStatus && (
            <div className="ai-status-chips">
              <span className="ai-status-chip" title="Primary provider configured in backend">
                Primary: <strong>{aiStatus.primary_provider.toUpperCase()}</strong>
              </span>
              <span className="ai-status-chip" title="Fallbacks in priority order">
                Fallback: <strong>{aiStatus.fallback_providers.join(" &rarr; ") || "None"}</strong>
              </span>
              <span className="ai-status-chip" title="ChromaDB vector collection size">
                Catalogue: <strong>{aiStatus.indexed_vectors_count} vectors</strong>
              </span>
            </div>
          )}

          {user?.role === "admin" && (
            <div className="ai-admin-actions">
              <button
                type="button"
                className="ai-reindex-btn"
                onClick={handleReindex}
                disabled={reindexing}
              >
                {reindexing ? "Reindexing ChromaDB..." : "Reindex Catalogue (Admin)"}
              </button>
              {reindexMessage && (
                <span className="ai-reindex-toast">{reindexMessage}</span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Suggested Quick Questions */}
      <div className="ai-suggestions-container" aria-label="Suggested search prompts">
        <span className="ai-suggestions-label">Try asking:</span>
        <div className="ai-suggestions-list">
          {SAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="ai-suggestion-chip"
              onClick={() => void handleSend(prompt)}
              disabled={isGenerating}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Log */}
      <div className="ai-chat-thread" aria-live="polite">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`ai-message-row ${msg.role === "user" ? "user-row" : "assistant-row"}`}
          >
            <div className={`ai-message-bubble ${msg.role === "user" ? "user-bubble" : "assistant-bubble"}`}>
              {/* Bubble Header */}
              <div className="ai-message-meta">
                <span className="ai-sender-name">
                  {msg.role === "user" ? (user?.name ? user.name : "You") : "GenZ Zone Assistant"}
                </span>
                {msg.provider && msg.role === "assistant" && (
                  <span className="ai-provider-pill" title={`Processed by ${msg.provider} (${msg.model || "default"})`}>
                    {msg.provider}
                  </span>
                )}
                <span className="ai-timestamp">{msg.timestamp}</span>
              </div>

              {/* Bubble Body */}
              <div className="ai-message-text">
                {msg.content ? (
                  <div className="ai-rendered-content">{msg.content}</div>
                ) : msg.isStreaming ? (
                  <span className="ai-loading-dots">
                    Retrieving catalogue and thinking<span>.</span><span>.</span><span>.</span>
                  </span>
                ) : null}
                {msg.isStreaming && <span className="ai-cursor" />}
              </div>

              {/* Source Citations Section */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="ai-citations-section">
                  <div className="ai-citations-title">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
                      <circle cx="12" cy="10" r="3" />
                    </svg>
                    Verified Catalogue Sources ({msg.citations.length})
                  </div>
                  <div className="ai-citations-grid">
                    {msg.citations.map((citation) => (
                      <AICitationCard key={citation.product_id} citation={citation} />
                    ))}
                  </div>
                </div>
              )}

              {/* Error & Retry State */}
              {msg.error && (
                <div className="ai-error-banner">
                  <p className="ai-error-text">{msg.error}</p>
                  <button
                    type="button"
                    className="ai-retry-btn"
                    onClick={() => handleRetry(msg)}
                  >
                    Retry Question
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input & Controls */}
      <div className="ai-input-bar-container">
        <form
          className="ai-input-form"
          onSubmit={(e) => {
            e.preventDefault()
            void handleSend()
          }}
        >
          <textarea
            ref={textareaRef}
            className="ai-textarea"
            rows={2}
            placeholder="Ask about products, prices in ₹, categories, or recommendations... (Enter to send, Shift+Enter for new line)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isGenerating}
          />

          <div className="ai-input-buttons">
            {isGenerating ? (
              <button
                type="button"
                className="ai-stop-btn"
                onClick={handleStop}
                title="Stop AI generation"
              >
                Stop
              </button>
            ) : (
              <button
                type="submit"
                className="ai-send-btn"
                disabled={!input.trim() || isGenerating}
                title="Send query"
              >
                Send &rarr;
              </button>
            )}

            {messages.length > 1 && !isGenerating && (
              <button
                type="button"
                className="ai-clear-btn"
                onClick={() =>
                  setMessages([
                    {
                      id: "welcome",
                      role: "assistant",
                      content:
                        "Conversation cleared. How can I help you discover products in GenZ Zone today?",
                      provider: "System",
                      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
                    },
                  ])
                }
                title="Clear conversation"
              >
                Clear
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}

export default AiAssistant
