import { renderHook, act } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { useWebSocket } from "./useWebSocket"

class MockWebSocket {
  static instances: MockWebSocket[] = []
  static readonly CONNECTING = 0
  static readonly OPEN = 1
  static readonly CLOSING = 2
  static readonly CLOSED = 3

  readonly CONNECTING = 0
  readonly OPEN = 1
  readonly CLOSING = 2
  readonly CLOSED = 3

  url: string
  readyState: number = 0 // CONNECTING
  onopen: ((event: Event) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  sentData: string[] = []

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  simulateOpen() {
    this.readyState = MockWebSocket.OPEN
    this.onopen?.(new Event("open"))
  }

  simulateMessage(data: unknown) {
    const text = typeof data === "string" ? data : JSON.stringify(data)
    this.onmessage?.(new MessageEvent("message", { data: text }))
  }

  simulateError() {
    this.onerror?.(new Event("error"))
  }

  simulateClose(code = 1006, reason = "Abnormal closure") {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent("close", { code, reason }))
  }

  send(data: string) {
    this.sentData.push(data)
  }

  close(code = 1000, reason = "Normal closure") {
    this.readyState = MockWebSocket.CLOSED
    this.onclose?.(new CloseEvent("close", { code, reason }))
  }
}

describe("useWebSocket hook", () => {
  beforeEach(() => {
    MockWebSocket.instances = []
    vi.stubGlobal("WebSocket", MockWebSocket)
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.useRealTimers()
  })

  it("initializes and connects to the provided URL", () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: "ws://127.0.0.1:8000/ws" }),
    )

    expect(result.current.status).toBe("CONNECTING")
    expect(MockWebSocket.instances).toHaveLength(1)
    expect(MockWebSocket.instances[0].url).toBe("ws://127.0.0.1:8000/ws")

    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })

    expect(result.current.status).toBe("OPEN")
    expect(result.current.isConnected).toBe(true)
  })

  it("appends authentication token query param when provided", () => {
    renderHook(() =>
      useWebSocket({
        url: "ws://127.0.0.1:8000/ws",
        token: "secret-token-xyz",
      }),
    )

    expect(MockWebSocket.instances[0].url).toBe(
      "ws://127.0.0.1:8000/ws?token=secret-token-xyz",
    )
  })

  it("sends message when connected and formats JSON payload", () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: "ws://127.0.0.1:8000/ws" }),
    )

    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })

    let sent = false
    act(() => {
      sent = result.current.sendMessage({ type: "PING" })
    })

    expect(sent).toBe(true)
    expect(MockWebSocket.instances[0].sentData).toEqual([
      JSON.stringify({ type: "PING" }),
    ])
  })

  it("parses received messages and calls onMessage callback", () => {
    const onMessage = vi.fn()
    const { result } = renderHook(() =>
      useWebSocket({
        url: "ws://127.0.0.1:8000/ws",
        onMessage,
      }),
    )

    act(() => {
      MockWebSocket.instances[0].simulateOpen()
      MockWebSocket.instances[0].simulateMessage({
        type: "NOTIFICATION",
        data: { title: "Order Shipped" },
      })
    })

    expect(onMessage).toHaveBeenCalledWith({
      type: "NOTIFICATION",
      data: { title: "Order Shipped" },
    })
    expect(result.current.lastMessage).toEqual({
      type: "NOTIFICATION",
      data: { title: "Order Shipped" },
    })
  })

  it("reconnects using exponential backoff when connection is interrupted", () => {
    const { result } = renderHook(() =>
      useWebSocket({
        url: "ws://127.0.0.1:8000/ws",
        autoReconnect: true,
        baseDelay: 1000,
        maxDelay: 8000,
        maxRetries: 3,
      }),
    )

    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })
    expect(result.current.isConnected).toBe(true)

    // Simulate unexpected drop
    act(() => {
      MockWebSocket.instances[0].simulateClose(1006, "Abnormal closure")
    })

    expect(result.current.status).toBe("CLOSED")
    expect(result.current.reconnectAttempts).toBe(1)
    expect(result.current.isReconnecting).toBe(true)

    // Advance time by 1000ms (first backoff delay: 1000 * 2^0 = 1000)
    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(MockWebSocket.instances).toHaveLength(2)

    // Second failure
    act(() => {
      MockWebSocket.instances[1].simulateClose(1006)
    })
    expect(result.current.reconnectAttempts).toBe(2)

    // Advance time by 2000ms (second backoff delay: 1000 * 2^1 = 2000)
    act(() => {
      vi.advanceTimersByTime(2000)
    })
    expect(MockWebSocket.instances).toHaveLength(3)

    // Connection restored
    act(() => {
      MockWebSocket.instances[2].simulateOpen()
    })
    expect(result.current.isConnected).toBe(true)
    expect(result.current.reconnectAttempts).toBe(0)
  })

  it("cleans up connection and timers on unmount", () => {
    const { unmount } = renderHook(() =>
      useWebSocket({ url: "ws://127.0.0.1:8000/ws" }),
    )

    act(() => {
      MockWebSocket.instances[0].simulateOpen()
    })

    unmount()

    expect(MockWebSocket.instances[0].readyState).toBe(MockWebSocket.CLOSED)
  })
})
