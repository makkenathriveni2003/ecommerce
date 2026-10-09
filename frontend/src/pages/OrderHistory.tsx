import { useQuery } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router-dom"
import { getMyOrders } from "../services/orderService"
import { useAuthStore } from "../store/authStore"
import { OrderInvoiceButton } from "../components/OrderInvoiceButton"

const formatPrice = (price: number) => `₹${price.toLocaleString("en-IN")}`

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
          <p className="eyebrow">YOUR ACCOUNT</p>
          <h1>Order history<span className="brand-dot">.</span></h1>
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
          <p>When you place an order, it will appear here.</p>
          <Link className="primary-button" to="/">Explore the shop</Link>
        </div>
      ) : (
        <div className="order-history-list">
          {orders.map((order) => (
            <article className="history-order" key={order.id}>
              <header>
                <div>
                  <p className="eyebrow">ORDER #{order.id}</p>
                  <p>{new Date(order.created_at).toLocaleString()}</p>
                </div>
                <div className="history-order-status">
                  <span className={`status-chip status-${order.status.toLowerCase()}`}>
                    {order.status.replaceAll("_", " ")}
                  </span>
                  <strong>{formatPrice(order.total)}</strong>
                </div>
              </header>
              <ul>
                {order.items.map((item) => (
                  <li key={item.id}>
                    <span>{item.name} × {item.quantity}</span>
                    <span>{formatPrice(item.unit_price * item.quantity)}</span>
                  </li>
                ))}
              </ul>
              <footer style={{ marginTop: "1rem", paddingTop: "0.75rem", borderTop: "1px dashed var(--line, #e2e8f0)", display: "flex", justifyContent: "flex-end" }}>
                <OrderInvoiceButton orderId={order.id} />
              </footer>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
