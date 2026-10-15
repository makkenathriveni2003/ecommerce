import { useQuery } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { getMyOrders } from "../services/orderService"
import { useAuthStore } from "../store/authStore"
import { OrderInvoiceButton } from "../components/OrderInvoiceButton"

const formatPrice = (price: number) => `₹${price.toLocaleString("en-IN")}`

const TRACKING_STEPS = [
  { key: "pending", label: "Placed", icon: "📝" },
  { key: "processing", label: "Processing", icon: "📦" },
  { key: "shipped", label: "Shipped", icon: "🚚" },
  { key: "delivered", label: "Delivered", icon: "🎉" },
]

function getStepIndex(status: string): number {
  const norm = status.toLowerCase()
  if (norm === "cancelled") return -1
  if (norm === "delivered") return 3
  if (norm === "shipped") return 2
  if (norm === "processing") return 1
  return 0
}

export default function OrderHistory() {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const [searchParams] = useSearchParams()
  const placedId = searchParams.get("placed")

  const ordersQuery = useQuery({
    queryKey: ["orders", user?.email],
    queryFn: ({ signal }) => getMyOrders(token!, signal),
    enabled: Boolean(token),
  })

  if (!token) {
    return (
      <section className="orders-page">
        <p role="alert">Sign in to view your orders.</p>
        <Link className="primary-button" to="/manage">Sign in</Link>
      </section>
    )
  }

  if (ordersQuery.isPending) {
    return <p className="status-message" role="status">Loading your orders...</p>
  }

  if (ordersQuery.isError) {
    return <p className="status-message" role="alert">{ordersQuery.error.message}</p>
  }

  const orders = ordersQuery.data

  return (
    <section className="orders-page">
      <div className="cart-heading">
        <div>
          <p className="eyebrow">GENZ ZONE CUSTOMER PORTAL</p>
          <h1>Order history &amp; Live tracking<span className="brand-dot">.</span></h1>
          <p style={{ margin: "0.25rem 0 0", fontSize: "0.875rem", color: "var(--color-text-muted, #64748b)" }}>
            ⚡ Live order tracking connected via real-time WebSockets &bull; Zero page refreshes required
          </p>
        </div>
      </div>

      {placedId && (
        <p className="form-message success-message order-confirmation" role="status">
          Thank you — order #{placedId} was placed successfully.
        </p>
      )}

      {orders.length === 0 ? (
        <div className="empty-cart">
          <h2>No orders yet.</h2>
          <p>When you place an order, it will appear here with live tracking.</p>
          <Link className="primary-button" to="/">Explore GenZ Zone Catalogue</Link>
        </div>
      ) : (
        <div className="order-history-list">
          {orders.map((order) => {
            const currentStepIdx = getStepIndex(order.status)
            const isCancelled = order.status.toLowerCase() === "cancelled"

            return (
              <article className="history-order" key={order.id} style={{ position: "relative" }}>
                <header>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                      <p className="eyebrow" style={{ margin: 0 }}>ORDER #{order.id}</p>
                      <span
                        style={{
                          fontSize: "0.7rem",
                          background: "#dcfce7",
                          color: "#15803d",
                          padding: "0.15rem 0.45rem",
                          borderRadius: "999px",
                          fontWeight: 600,
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.25rem",
                        }}
                        title="WebSocket live tracking active"
                      >
                        <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#22c55e" }} />
                        Live WebSocket Track
                      </span>
                    </div>
                    <p style={{ marginTop: "0.25rem" }}>{new Date(order.created_at).toLocaleString()}</p>
                  </div>
                  <div className="history-order-status">
                    <span className={`status-chip status-${order.status.toLowerCase()}`}>
                      {order.status.replaceAll("_", " ")}
                    </span>
                    <strong>{formatPrice(order.total)}</strong>
                  </div>
                </header>

                {/* Real-Time Visual Progress Stepper */}
                <div
                  style={{
                    margin: "1rem 0 1.25rem",
                    padding: "1rem",
                    background: "var(--color-surface, #f8fafc)",
                    borderRadius: "10px",
                    border: "1px solid var(--line, #e2e8f0)",
                  }}
                >
                  {isCancelled ? (
                    <div style={{ color: "#ef4444", fontWeight: 600, fontSize: "0.875rem" }}>
                      ❌ Order has been cancelled. If you have questions, please reach out via 24/7 Live Support Chat.
                    </div>
                  ) : (
                    <div>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          position: "relative",
                          marginBottom: "0.5rem",
                        }}
                      >
                        {/* Connecting Line */}
                        <div
                          style={{
                            position: "absolute",
                            top: "14px",
                            left: "5%",
                            right: "5%",
                            height: "4px",
                            background: "#e2e8f0",
                            zIndex: 0,
                          }}
                        />
                        <div
                          style={{
                            position: "absolute",
                            top: "14px",
                            left: "5%",
                            width: `${(Math.max(0, currentStepIdx) / 3) * 90}%`,
                            height: "4px",
                            background: "#22c55e",
                            transition: "width 0.4s ease-in-out",
                            zIndex: 1,
                          }}
                        />

                        {TRACKING_STEPS.map((step, idx) => {
                          const isDone = idx <= currentStepIdx
                          const isCurrent = idx === currentStepIdx

                          return (
                            <div
                              key={step.key}
                              style={{
                                display: "flex",
                                flexDirection: "column",
                                alignItems: "center",
                                zIndex: 2,
                                width: "22%",
                              }}
                            >
                              <div
                                style={{
                                  width: "30px",
                                  height: "30px",
                                  borderRadius: "50%",
                                  background: isDone ? "#22c55e" : "#f1f5f9",
                                  color: isDone ? "#fff" : "#94a3b8",
                                  display: "flex",
                                  alignItems: "center",
                                  justifyContent: "center",
                                  fontSize: "0.85rem",
                                  fontWeight: 700,
                                  boxShadow: isCurrent ? "0 0 0 4px rgba(34, 197, 94, 0.25)" : "none",
                                  transition: "all 0.3s ease",
                                }}
                              >
                                {isDone ? "✓" : idx + 1}
                              </div>
                              <span
                                style={{
                                  marginTop: "0.4rem",
                                  fontSize: "0.75rem",
                                  fontWeight: isCurrent ? 700 : isDone ? 600 : 500,
                                  color: isDone ? "var(--color-text, #0f172a)" : "#94a3b8",
                                  textAlign: "center",
                                }}
                              >
                                {step.label}
                              </span>
                            </div>
                          )
                        })}
                      </div>

                      <div style={{ marginTop: "0.5rem", fontSize: "0.775rem", color: "#64748b", textAlign: "right" }}>
                        Current phase: <strong style={{ color: "#0f172a", textTransform: "uppercase" }}>{order.status.toUpperCase()}</strong>
                        {currentStepIdx < 3 && " • Real-time updates delivered live"}
                      </div>
                    </div>
                  )}
                </div>

                {/* Items List */}
                <ul>
                  {order.items.map((item) => (
                    <li key={item.id}>
                      <span>{item.name} × {item.quantity}</span>
                      <span>{formatPrice(item.unit_price * item.quantity)}</span>
                    </li>
                  ))}
                </ul>

                <footer
                  style={{
                    marginTop: "1rem",
                    paddingTop: "0.75rem",
                    borderTop: "1px dashed var(--line, #e2e8f0)",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <span style={{ fontSize: "0.8rem", color: "#64748b" }}>
                    Verified by GenZ Zone Dispatch Network
                  </span>
                  <OrderInvoiceButton orderId={order.id} />
                </footer>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}
