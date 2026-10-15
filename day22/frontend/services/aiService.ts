import { API_URL, requestJson } from "./apiClient"
import type { AICitation, AIStatus } from "../../types"

export interface StreamChatOptions {
  message: string
  conversationHistory?: Array<{ role: string; content: string }>
  category?: string
  signal?: AbortSignal
  onChunk: (text: string) => void
  onCitations: (citations: AICitation[]) => void
  onProvider: (providerInfo: { provider: string; model: string }) => void
  onProviderChange?: (changeInfo: { from: string; to: string; reason: string }) => void
  onError: (errorMsg: string) => void
  onDone: (summary: { provider?: string; citationsCount?: number }) => void
}

/**
 * Fetch AI service configuration and vector index metrics.
 */
export async function getAIStatus(): Promise<AIStatus> {
  const data = await requestJson("/api/ai/status")
  return data as AIStatus
}

/**
 * Admin action to re-index products into the ChromaDB vector store.
 */
export async function reindexCatalog(token: string): Promise<{
  products_indexed: number
  chunks_indexed: number
  total_vectors: number
  message: string
}> {
  const response = await fetch(`${API_URL}/api/ai/index/reindex`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error("Admin authorization required to re-index the catalogue.")
    }
    throw new Error(`Catalogue reindexing failed (HTTP ${response.status}).`)
  }

  return response.json()
}

/**
 * Fetch-based SSE streaming client for POST /api/ai/chat/stream.
 * Standard EventSource does not support POST payloads or custom request bodies,
 * so we parse the response.body ReadableStream with a resilient line-buffered decoder.
 */
export async function streamAIChat(options: StreamChatOptions): Promise<void> {
  const {
    message,
    conversationHistory = [],
    category,
    signal,
    onChunk,
    onCitations,
    onProvider,
    onProviderChange,
    onError,
    onDone,
  } = options

  let response: Response
  try {
    response = await fetch(`${API_URL}/api/ai/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory,
        category: category || null,
      }),
      signal,
    })
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      // User aborted stream cleanly
      return
    }
    const errMsg = err instanceof Error ? err.message : "Network error"
    onError(`Cannot reach the AI Assistant at ${API_URL}. (${errMsg})`)
    return
  }

  if (!response.ok) {
    if (response.status === 429) {
      onError("You have reached the AI message rate limit. Please wait a moment before sending another query.")
    } else {
      onError(`AI service encountered an issue (HTTP ${response.status}). Please try again.`)
    }
    return
  }

  if (!response.body) {
    onError("Streaming response body is unavailable in this environment.")
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder("utf-8")
  let buffer = ""
  let currentEvent = "message"

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() ?? ""

      for (const line of lines) {
        const trimmed = line.trim()
        if (!trimmed) {
          currentEvent = "message"
          continue
        }

        if (trimmed.startsWith("event:")) {
          currentEvent = trimmed.replace("event:", "").trim()
          continue
        }

        if (trimmed.startsWith("data:")) {
          const rawData = trimmed.replace("data:", "").trim()
          let parsedData: unknown
          try {
            parsedData = JSON.parse(rawData)
          } catch {
            parsedData = rawData
          }

          if (currentEvent === "provider") {
            const info = parsedData as { provider: string; model: string }
            onProvider(info)
          } else if (currentEvent === "citations") {
            const citations = (parsedData as AICitation[]) || []
            onCitations(citations)
          } else if (currentEvent === "chunk") {
            const chunkObj = parsedData as { text?: string }
            const text = typeof parsedData === "string" ? parsedData : chunkObj.text ?? ""
            onChunk(text)
          } else if (currentEvent === "provider_change") {
            const change = parsedData as { from: string; to: string; reason: string }
            onProviderChange?.(change)
          } else if (currentEvent === "error") {
            const errObj = parsedData as { error?: string }
            const msg = typeof parsedData === "string" ? parsedData : errObj.error ?? "An error occurred."
            onError(msg)
          } else if (currentEvent === "done") {
            const summary = parsedData as { provider?: string; citations_count?: number }
            onDone(summary)
          }
        }
      }
    }
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      // Clean cancellation
      return
    }
    onError("Streaming response was interrupted. Please retry.")
  } finally {
    reader.releaseLock()
  }
}

export interface AIDescriptionResult {
  name: string
  category: string
  description: string
  bullet_points: string[]
  provider: string
  model: string
  cached: boolean
}

/**
 * Generate Amazon-standard e-commerce product description via AI.
 */
export async function generateAIDescription(params: {
  name: string
  category: string
  price?: number
  keywords?: string[]
  tone?: string
}): Promise<AIDescriptionResult> {
  const response = await fetch(`${API_URL}/api/ai/generate-description`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(params),
  })

  if (!response.ok) {
    const errorData = (await response.json().catch(() => ({}))) as { detail?: string }
    throw new Error(errorData.detail || `AI Description generation failed (HTTP ${response.status})`)
  }

  return response.json()
}

