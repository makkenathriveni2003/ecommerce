import React, { useState } from "react"
import { useAuthStore } from "../store/authStore"
import { generateOrderInvoice } from "../services/orderService"
import { useBackgroundTask } from "../hooks/useBackgroundTask"
import { API_URL } from "../services/apiClient"

export interface OrderInvoiceButtonProps {
  orderId: number
}

export const OrderInvoiceButton: React.FC<OrderInvoiceButtonProps> = ({ orderId }) => {
  const token = useAuthStore((state) => state.token)
  const [downloadReady, setDownloadReady] = useState(false)
  const [triggerError, setTriggerError] = useState<string | null>(null)

  const task = useBackgroundTask({
    pollInterval: 600,
    onSuccess: () => {
      setDownloadReady(true)
    },
  })

  const handleGenerateInvoice = async () => {
    if (!token) return
    setTriggerError(null)
    setDownloadReady(false)

    try {
      const resp = await generateOrderInvoice(orderId, token)
      task.trackTask(resp.task_id)
    } catch (err) {
      setTriggerError(err instanceof Error ? err.message : "Failed to queue invoice generation")
    }
  }

  const handleDownload = () => {
    const downloadUrl = `${API_URL}/orders/${orderId}/invoice/download${token ? `?token=${encodeURIComponent(token)}` : ""}`
    const anchor = document.createElement("a")
    anchor.href = downloadUrl
    anchor.target = "_blank"
    anchor.rel = "noopener noreferrer"
    anchor.download = `ShopZone_Invoice_${orderId}.pdf`
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
  }

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.75rem",
        flexWrap: "wrap",
      }}
      data-testid={`order-invoice-container-${orderId}`}
    >
      {/* 1. Initial State: Generate Invoice Button */}
      {!task.isRunning && !downloadReady && (
        <button
          type="button"
          onClick={handleGenerateInvoice}
          data-testid={`generate-invoice-btn-${orderId}`}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            fontSize: "0.85rem",
            fontWeight: 600,
            padding: "0.45rem 0.9rem",
            borderRadius: "6px",
            border: "1px solid var(--color-border, #cbd5e1)",
            background: "var(--color-surface, #ffffff)",
            color: "var(--color-primary, #2563eb)",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          Generate Invoice
        </button>
      )}

      {/* 2. Generating / Progress State */}
      {task.isRunning && (
        <div
          data-testid={`invoice-progress-${orderId}`}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.5rem",
            fontSize: "0.82rem",
            color: "var(--color-primary, #2563eb)",
            background: "var(--color-bg-secondary, #f0fdf4)",
            padding: "0.35rem 0.75rem",
            borderRadius: "6px",
            border: "1px solid #bbf7d0",
          }}
        >
          <span
            style={{
              width: "12px",
              height: "12px",
              border: "2px solid #2563eb",
              borderTopColor: "transparent",
              borderRadius: "50%",
              display: "inline-block",
              animation: "spin 0.8s linear infinite",
            }}
          />
          <span>Generating PDF ({task.percent}%)...</span>
        </div>
      )}

      {/* 3. Ready State: Download Button */}
      {downloadReady && (
        <div style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
          <span
            data-testid={`invoice-ready-badge-${orderId}`}
            style={{
              fontSize: "0.75rem",
              fontWeight: 700,
              textTransform: "uppercase",
              padding: "0.2rem 0.5rem",
              borderRadius: "4px",
              background: "#dcfce7",
              color: "#166534",
              border: "1px solid #bbf7d0",
            }}
          >
            Invoice Ready
          </span>

          <button
            type="button"
            onClick={handleDownload}
            data-testid={`download-invoice-btn-${orderId}`}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              fontSize: "0.85rem",
              fontWeight: 600,
              padding: "0.45rem 0.9rem",
              borderRadius: "6px",
              border: "none",
              background: "var(--color-primary, #2563eb)",
              color: "#ffffff",
              cursor: "pointer",
            }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            Download Invoice (PDF)
          </button>
        </div>
      )}

      {/* 4. Error State */}
      {(triggerError || task.isFailed) && (
        <div style={{ display: "inline-flex", alignItems: "center", gap: "0.4rem" }}>
          <span
            data-testid={`invoice-error-${orderId}`}
            style={{
              fontSize: "0.8rem",
              color: "#991b1b",
              background: "#fee2e2",
              padding: "0.3rem 0.6rem",
              borderRadius: "4px",
            }}
          >
            {triggerError || task.error || "Generation failed"}
          </span>
          <button
            type="button"
            onClick={handleGenerateInvoice}
            style={{
              fontSize: "0.8rem",
              padding: "0.3rem 0.6rem",
              borderRadius: "4px",
              border: "1px solid #f87171",
              background: "#fff",
              color: "#991b1b",
              cursor: "pointer",
            }}
          >
            Retry
          </button>
        </div>
      )}
    </div>
  )
}
