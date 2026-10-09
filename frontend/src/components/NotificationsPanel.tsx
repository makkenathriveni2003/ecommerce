import { useRef, useEffect } from "react"
import { useNotificationStore } from "../store/notificationStore"
import type { NotificationType } from "../../types"

function getBadgeClass(type: NotificationType): string {
  switch (type) {
    case "confirmed":
    case "pending":
      return "status-pending"
    case "processing":
      return "status-processing"
    case "shipped":
      return "status-shipped"
    case "delivered":
      return "status-delivered"
    case "cancelled":
      return "status-cancelled"
    default:
      return "status-info"
  }
}

function getIcon(type: NotificationType): string {
  switch (type) {
    case "confirmed":
      return "✓"
    case "processing":
      return "⚙"
    case "shipped":
      return "🚚"
    case "delivered":
      return "📦"
    case "cancelled":
      return "✕"
    default:
      return "ℹ"
  }
}

export default function NotificationsPanel() {
  const {
    notifications,
    unreadCount,
    isOpen,
    setIsOpen,
    markAsRead,
    markAllAsRead,
    clearAll,
  } = useNotificationStore()

  const panelRef = useRef<HTMLDivElement>(null)

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [isOpen, setIsOpen])

  return (
    <div className="notifications-wrapper" ref={panelRef}>
      <button
        type="button"
        className="icon-button notification-bell-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label={`Notifications (${unreadCount} unread)`}
        aria-expanded={isOpen}
      >
        <span className="bell-symbol" aria-hidden="true">🔔</span>
        {unreadCount > 0 && (
          <span className="notification-badge" aria-label={`${unreadCount} unread notifications`}>
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notifications-panel" role="dialog" aria-label="Notifications panel">
          <div className="notifications-header">
            <div className="panel-title-area">
              <h3>Notifications</h3>
              {unreadCount > 0 && (
                <span className="unread-pill">{unreadCount} new</span>
              )}
            </div>
            <div className="panel-actions">
              {unreadCount > 0 && (
                <button
                  type="button"
                  className="text-action-btn"
                  onClick={markAllAsRead}
                >
                  Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  type="button"
                  className="text-action-btn danger-action"
                  onClick={clearAll}
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          <div className="notifications-body">
            {notifications.length === 0 ? (
              <div className="empty-notifications">
                <span className="empty-bell" aria-hidden="true">🔔</span>
                <p>No notifications yet.</p>
                <small>Real-time order and shipment updates will appear here.</small>
              </div>
            ) : (
              <ul className="notification-list">
                {notifications.map((item) => (
                  <li
                    key={item.id}
                    className={`notification-item ${item.read ? "read" : "unread"}`}
                    onClick={() => markAsRead(item.id)}
                  >
                    <div className={`notification-icon ${getBadgeClass(item.type)}`}>
                      {getIcon(item.type)}
                    </div>
                    <div className="notification-content">
                      <div className="notification-title-row">
                        <strong>{item.title}</strong>
                        {!item.read && <span className="unread-dot" aria-label="Unread" />}
                      </div>
                      <p>{item.message}</p>
                      <time dateTime={item.created_at}>
                        {new Date(item.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </time>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
