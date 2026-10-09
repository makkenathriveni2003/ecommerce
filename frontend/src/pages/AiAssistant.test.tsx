import { screen, fireEvent, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"
import { AiAssistant } from "./AiAssistant"
import { renderApp } from "../test/testUtils"
import * as aiService from "../services/aiService"

describe("AiAssistant Page Component", () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(aiService, "getAIStatus").mockResolvedValue({
      primary_provider: "gemini",
      fallback_providers: ["groq", "mistral"],
      embedding_provider: "local_hash",
      indexed_vectors_count: 38,
      configured_providers: {
        gemini: true,
        groq: true,
        mistral: false,
        openai_compatible: false,
      },
    })
    vi.spyOn(aiService, "streamAIChat").mockImplementation(async (options) => {
      options.onChunk("Sample response chunk")
      options.onDone({ provider: "gemini" })
    })
  })

  it("renders the AI assistant header, status chips, and sample prompts", async () => {
    renderApp(<AiAssistant />)

    expect(screen.getByRole("heading", { name: /ShopZone AI Assistant/i })).toBeInTheDocument()
    expect(screen.getByText(/Grounded in real ShopZone catalogue/i)).toBeInTheDocument()

    // Status chips
    expect(await screen.findByText(/Primary:/i)).toBeInTheDocument()
    expect(screen.getByText(/38 vectors/i)).toBeInTheDocument()

    // Sample prompt chips
    expect(screen.getByRole("button", { name: /Which headphones are available under ₹3,000\?/i })).toBeInTheDocument()

    // Welcome message
    expect(screen.getByText(/Ask me anything about our products, current pricing/i)).toBeInTheDocument()
  })

  it("sends a user question and renders streaming response and citations", async () => {
    // Mock streamAIChat to invoke callbacks
    vi.spyOn(aiService, "streamAIChat").mockImplementation(async (options) => {
      options.onProvider({ provider: "gemini", model: "gemini-1.5-flash" })
      options.onCitations([
        {
          product_id: 3,
          product_name: "Headphones",
          category: "Accessories",
          price: 3000,
          stock: 50,
          url: "/products/3",
        },
      ])
      options.onChunk("ShopZone has ")
      options.onChunk("Headphones available for ₹3,000.00.")
      options.onDone({ provider: "gemini", citationsCount: 1 })
    })

    renderApp(<AiAssistant />)

    const textarea = screen.getByPlaceholderText(/Ask about products, prices in ₹/i)
    fireEvent.change(textarea, { target: { value: "Which headphones are available under ₹3,000?" } })

    const sendBtn = screen.getByRole("button", { name: /Send/i })
    await waitFor(() => {
      expect(sendBtn).not.toBeDisabled()
    })
    fireEvent.click(sendBtn)

    // Verify user message appears in thread
    expect(screen.getAllByText("Which headphones are available under ₹3,000?").length).toBeGreaterThanOrEqual(1)

    // Verify streamed response content appears
    await waitFor(() => {
      expect(screen.getByText(/Headphones available for ₹3,000.00/i)).toBeInTheDocument()
    })

    // Verify citation card appears and links to product
    const citationLink = await screen.findByRole("link", { name: /View product: Headphones/i })
    expect(citationLink).toHaveAttribute("href", "/products/3")
    expect(screen.getByText(/In Stock \(50\)/i)).toBeInTheDocument()
  })

  it("handles user cancellation (Stop button)", async () => {
    let abortListener: (() => void) | undefined
    vi.spyOn(aiService, "streamAIChat").mockImplementation(async (options) => {
      options.signal?.addEventListener("abort", () => {
        abortListener?.()
      })
      options.onChunk("Thinking...")
      // Hangs until aborted
      await new Promise<void>((resolve) => {
        abortListener = resolve
      })
    })

    renderApp(<AiAssistant />)

    const textarea = screen.getByPlaceholderText(/Ask about products, prices in ₹/i)
    fireEvent.change(textarea, { target: { value: "Show laptops" } })

    const sendBtn = screen.getByRole("button", { name: /Send/i })
    await waitFor(() => {
      expect(sendBtn).not.toBeDisabled()
    })
    fireEvent.click(sendBtn)

    // Stop button appears while generating
    const stopBtn = await screen.findByRole("button", { name: /Stop/i })
    expect(stopBtn).toBeInTheDocument()

    fireEvent.click(stopBtn)

    // Generator stops and Send button returns
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: /Stop/i })).not.toBeInTheDocument()
    })
  })

  it("clears conversation when Clear button is clicked", async () => {
    renderApp(<AiAssistant />)

    // Clicking sample prompt sends message
    const promptChip = screen.getByRole("button", { name: /Which headphones are available under ₹3,000\?/i })
    fireEvent.click(promptChip)

    // Wait for response to finish generating
    await waitFor(() => {
      expect(screen.getByText(/Sample response chunk/i)).toBeInTheDocument()
    })

    // Clear button should become visible once there are more messages
    const clearBtn = await screen.findByRole("button", { name: /Clear/i })
    fireEvent.click(clearBtn)

    expect(screen.getByText(/Conversation cleared. How can I help you discover products/i)).toBeInTheDocument()
  })
})
