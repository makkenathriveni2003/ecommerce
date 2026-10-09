import { useCallback, useEffect, useRef, useState } from "react"
import type { WebSocketStatus } from "../../types"

export interface UseWebSocketOptions {
  url: string
  token?: string | null
  autoReconnect?: boolean
  maxRetries?: number
  baseDelay?: number
  maxDelay?: number
  enabled?: boolean
  onMessage?: (data: unknown) => void
  onOpen?: (event: Event) => void
  onClose?: (event: CloseEvent) => void
  onError?: (event: Event) => void
}

export interface UseWebSocketReturn {
  status: WebSocketStatus
  isConnected: boolean
  isReconnecting: boolean
  reconnectAttempts: number
  sendMessage: (data: unknown) => boolean
  connect: () => void
  disconnect: () => void
  lastMessage: unknown
}

export function useWebSocket({
  url,
  token,
  autoReconnect = true,
  maxRetries = 8,
  baseDelay = 1000,
  maxDelay = 16000,
  enabled = true,
  onMessage,
  onOpen,
  onClose,
  onError,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [status, setStatus] = useState<WebSocketStatus>("CLOSED")
  const [reconnectAttempts, setReconnectAttempts] = useState(0)
  const [lastMessage, setLastMessage] = useState<unknown>(null)

  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const isManuallyClosedRef = useRef(false)
  const attemptsRef = useRef(0)

  // Keep callback refs fresh
  const onMessageRef = useRef(onMessage)
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)
  const onErrorRef = useRef(onError)
  const connectRef = useRef<() => void>(() => {})

  useEffect(() => {
    onMessageRef.current = onMessage
    onOpenRef.current = onOpen
    onCloseRef.current = onClose
    onErrorRef.current = onError
  }, [onMessage, onOpen, onClose, onError])

  const clearReconnectTimer = useCallback(() => {
    if (reconnectTimeoutRef.current !== null) {
      window.clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    clearReconnectTimer()
    isManuallyClosedRef.current = false

    // Close any previous socket cleanly
    if (socketRef.current) {
      try {
        socketRef.current.close(1000, "Reconnecting")
      } catch {
        // ignore
      }
      socketRef.current = null
    }

    // Build WebSocket URL with token query param if provided
    let targetUrl = url
    if (token) {
      const separator = targetUrl.includes("?") ? "&" : "?"
      targetUrl = `${targetUrl}${separator}token=${encodeURIComponent(token)}`
    }

    try {
      setStatus("CONNECTING")
      const ws = new WebSocket(targetUrl)
      socketRef.current = ws

      ws.onopen = (event) => {
        setStatus("OPEN")
        attemptsRef.current = 0
        setReconnectAttempts(0)
        onOpenRef.current?.(event)
      }

      ws.onmessage = (event) => {
        let parsed: unknown = event.data
        try {
          parsed = JSON.parse(event.data)
        } catch {
          // keep as raw text
        }
        setLastMessage(parsed)
        onMessageRef.current?.(parsed)
      }

      ws.onerror = (event) => {
        onErrorRef.current?.(event)
      }

      ws.onclose = (event) => {
        setStatus("CLOSED")
        socketRef.current = null
        onCloseRef.current?.(event)

        // Exponential backoff reconnection if not manually closed
        if (
          !isManuallyClosedRef.current &&
          autoReconnect &&
          event.code !== 1000
        ) {
          if (attemptsRef.current < maxRetries) {
            const nextAttempt = attemptsRef.current + 1
            attemptsRef.current = nextAttempt
            setReconnectAttempts(nextAttempt)

            // Calculate exponential backoff delay: baseDelay * 2^(attempt - 1), capped at maxDelay
            const delay = Math.min(
              baseDelay * Math.pow(2, nextAttempt - 1),
              maxDelay,
            )

            clearReconnectTimer()
            reconnectTimeoutRef.current = window.setTimeout(() => {
              connectRef.current()
            }, delay)
          }
        }
      }
    } catch {
      setStatus("CLOSED")
    }
  }, [url, token, autoReconnect, maxRetries, baseDelay, maxDelay, clearReconnectTimer])

  useEffect(() => {
    connectRef.current = connect
  }, [connect])

  const disconnect = useCallback(() => {
    isManuallyClosedRef.current = true
    clearReconnectTimer()
    attemptsRef.current = 0
    setReconnectAttempts(0)

    if (socketRef.current) {
      setStatus("CLOSING")
      socketRef.current.close(1000, "Client disconnected")
      socketRef.current = null
    }
    setStatus("CLOSED")
  }, [clearReconnectTimer])

  const sendMessage = useCallback((data: unknown): boolean => {
    if (
      socketRef.current &&
      (socketRef.current.readyState === 1 ||
        socketRef.current.readyState === WebSocket.OPEN)
    ) {

      const payload = typeof data === "string" ? data : JSON.stringify(data)
      socketRef.current.send(payload)
      return true
    }
    return false
  }, [])

  // Mount/Unmount effect
  useEffect(() => {
    if (enabled && url) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      connect()
    }
    return () => {
      disconnect()
    }
  }, [enabled, url, token, connect, disconnect])

  const isConnected = status === "OPEN"
  const isReconnecting = status !== "OPEN" && reconnectAttempts > 0

  return {
    status,
    isConnected,
    isReconnecting,
    reconnectAttempts,
    sendMessage,
    connect,
    disconnect,
    lastMessage,
  }
}
