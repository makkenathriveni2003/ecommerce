import React from "react"

export interface TaskProgressCardProps {
  title?: string
  taskId: string | null
  status: string
  percent: number
  message: string
  result?: Record<string, unknown> | null
  error?: string | null
  onReset?: () => void
}

export const TaskProgressCard: React.FC<TaskProgressCardProps> = ({
  title = "Background Task Tracker",
  taskId,
  status,
  percent,
  message,
  result,
  error,
  onReset,
}) => {
  if (!taskId && status === "IDLE") {
    return null
  }

  const getStatusBadge = () => {
    switch (status) {
      case "PENDING":
        return {
          label: "Queued / Pending",
          badgeClass: "badge-warning",
          bg: "#fef3c7",
          color: "#92400e",
          border: "#fde68a",
        }
      case "STARTED":
      case "PROGRESS":
        return {
          label: status === "STARTED" ? "Started / Running" : `In Progress (${percent}%)`,
          badgeClass: "badge-info",
          bg: "#dbeafe",
          color: "#1e40af",
          border: "#bfdbfe",
        }
      case "SUCCESS":
        return {
          label: "Completed",
          badgeClass: "badge-success",
          bg: "#dcfce7",
          color: "#166534",
          border: "#bbf7d0",
        }
      case "FAILURE":
        return {
          label: "Failed",
          badgeClass: "badge-danger",
          bg: "#fee2e2",
          color: "#991b1b",
          border: "#fecaca",
        }
      default:
        return {
          label: status,
          badgeClass: "badge-neutral",
          bg: "#f3f4f6",
          color: "#374151",
          border: "#e5e7eb",
        }
    }
  }

  const badgeInfo = getStatusBadge()

  return (
    <div
      style={{
        border: "1px solid var(--color-border, #e2e8f0)",
        borderRadius: "12px",
        padding: "1.25rem",
        background: "var(--color-surface, #ffffff)",
        boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)",
        marginBottom: "1.25rem",
      }}
      data-testid="task-progress-card"
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "0.75rem",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <h4
            style={{
              margin: 0,
              fontSize: "1.05rem",
              fontWeight: 600,
              color: "var(--color-text, #1e293b)",
            }}
          >
            {title}
          </h4>
          {taskId && (
            <span
              style={{
                fontSize: "0.75rem",
                color: "var(--color-text-muted, #64748b)",
                fontFamily: "monospace",
                background: "var(--color-bg-secondary, #f1f5f9)",
                padding: "2px 6px",
                borderRadius: "4px",
              }}
              title={taskId}
            >
              ID: {taskId.slice(0, 8)}...
            </span>
          )}
        </div>

        <span
          data-testid="task-status-badge"
          style={{
            fontSize: "0.8rem",
            fontWeight: 600,
            padding: "4px 10px",
            borderRadius: "9999px",
            backgroundColor: badgeInfo.bg,
            color: badgeInfo.color,
            border: `1px solid ${badgeInfo.border}`,
            display: "inline-flex",
            alignItems: "center",
            gap: "4px",
          }}
        >
          {(status === "STARTED" || status === "PROGRESS") && (
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                backgroundColor: badgeInfo.color,
                display: "inline-block",
                animation: "pulse 1.5s infinite",
              }}
            />
          )}
          {badgeInfo.label}
        </span>
      </div>

      {/* Progress Bar Container */}
      <div
        style={{
          width: "100%",
          height: "10px",
          backgroundColor: "var(--color-bg-secondary, #e2e8f0)",
          borderRadius: "9999px",
          overflow: "hidden",
          margin: "0.75rem 0",
          position: "relative",
        }}
        data-testid="task-progress-bar-container"
      >
        <div
          data-testid="task-progress-bar"
          style={{
            width: `${Math.min(Math.max(percent, 0), 100)}%`,
            height: "100%",
            backgroundColor:
              status === "FAILURE"
                ? "#ef4444"
                : status === "SUCCESS"
                  ? "#22c55e"
                  : "var(--color-primary, #3b82f6)",
            transition: "width 0.3s ease-in-out",
            borderRadius: "9999px",
          }}
        />
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.85rem",
          color: "var(--color-text-muted, #64748b)",
          marginTop: "0.25rem",
        }}
      >
        <span data-testid="task-message">{message || "Working..."}</span>
        <span style={{ fontWeight: 600 }} data-testid="task-percent">
          {percent}%
        </span>
      </div>

      {/* Error Details */}
      {error && (
        <div
          data-testid="task-error-alert"
          style={{
            marginTop: "0.75rem",
            padding: "0.5rem 0.75rem",
            borderRadius: "6px",
            backgroundColor: "#fee2e2",
            color: "#991b1b",
            fontSize: "0.85rem",
            border: "1px solid #fecaca",
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Completed Result details */}
      {status === "SUCCESS" && result && (
        <div
          data-testid="task-result-alert"
          style={{
            marginTop: "0.75rem",
            padding: "0.5rem 0.75rem",
            borderRadius: "6px",
            backgroundColor: "#f0fdf4",
            color: "#166534",
            fontSize: "0.85rem",
            border: "1px solid #bbf7d0",
          }}
        >
          <strong>Result:</strong> {typeof result === "object" ? JSON.stringify(result) : String(result)}
        </div>
      )}

      {onReset && (status === "SUCCESS" || status === "FAILURE") && (
        <div style={{ marginTop: "0.75rem", textAlign: "right" }}>
          <button
            type="button"
            onClick={onReset}
            style={{
              fontSize: "0.8rem",
              padding: "4px 12px",
              borderRadius: "6px",
              border: "1px solid var(--color-border, #cbd5e1)",
              background: "var(--color-surface, #ffffff)",
              color: "var(--color-text, #475569)",
              cursor: "pointer",
            }}
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  )
}
