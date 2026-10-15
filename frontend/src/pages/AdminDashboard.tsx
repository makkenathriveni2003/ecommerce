import { useState, type FormEvent } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import {
  createAdminProduct,
  deleteProduct,
  getAdminProducts,
  updateProduct,
  type NewProduct,
} from "../services/productService"
import { getAdminOrders, updateOrderStatus } from "../services/orderService"
import { generateAIDescription } from "../services/aiService"
import Login from "./Login"
import { useAuthStore } from "../store/authStore"
import { BulkCsvImport } from "../components/BulkCsvImport"

const emptyProduct: NewProduct = { name: "", price: 0, category: "", image: "", description: "", stock: 50 }
const orderStatuses = ["pending", "processing", "shipped", "delivered", "cancelled"]

export default function AdminDashboard() {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const queryClient = useQueryClient()
  const [form, setForm] = useState<NewProduct>(emptyProduct)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isGeneratingDesc, setIsGeneratingDesc] = useState(false)

  const productsQuery = useQuery({
    queryKey: ["admin", "products"],
    queryFn: () => getAdminProducts(token!),
    enabled: user?.role === "admin" && Boolean(token),
  })
  const ordersQuery = useQuery({
    queryKey: ["admin", "orders"],
    queryFn: () => getAdminOrders(token!),
    enabled: user?.role === "admin" && Boolean(token),
  })

  const refreshProducts = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["admin", "products"] }),
      queryClient.invalidateQueries({ queryKey: ["products"] }),
    ])
  }
  const saveMutation = useMutation({
    mutationFn: () =>
      editingId === null
        ? createAdminProduct(form, token!)
        : updateProduct(editingId, form, token!),
    onSuccess: async (product) => {
      setNotice(`${product.name} saved.`)
      setError(null)
      setForm(emptyProduct)
      setEditingId(null)
      await refreshProducts()
    },
    onError: (mutationError) => setError(mutationError.message),
  })
  const deleteMutation = useMutation({
    mutationFn: (productId: number) => deleteProduct(productId, token!),
    onSuccess: async () => {
      setNotice("Product deleted.")
      setError(null)
      await refreshProducts()
    },
    onError: (mutationError) => setError(mutationError.message),
  })
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      updateOrderStatus(id, status, token!),
    onSuccess: async () => {
      setNotice("Order status updated.")
      setError(null)
      await queryClient.invalidateQueries({ queryKey: ["admin", "orders"] })
    },
    onError: (mutationError) => setError(mutationError.message),
  })

  if (!user || !token) {
    return <Login initialRole="admin" />
  }
  if (user.role !== "admin") {
    return (
      <section className="manage-page">
        <div className="manage-panel">
          <h1>Admin access required.</h1>
          <p className="manage-intro">This account does not have administrator permissions.</p>
          <Link className="primary-button" to="/">Back to shop</Link>
        </div>
      </section>
    )
  }

  function startEdit(product: NewProduct & { id: number }) {
    setEditingId(product.id)
    setForm({
      name: product.name,
      price: product.price,
      category: product.category,
      image: product.image,
      description: product.description || "",
      stock: product.stock ?? 50,
    })
    setError(null)
    setNotice(null)
  }

  async function handleAiGenerateDescription() {
    if (!form.name.trim() || !form.category.trim()) {
      setError("Please enter product name and category first so the AI copywriter has context.")
      return
    }
    setError(null)
    setIsGeneratingDesc(true)
    try {
      const res = await generateAIDescription({
        name: form.name.trim(),
        category: form.category.trim(),
        price: form.price > 0 ? form.price : undefined,
      })
      setForm((prev) => ({ ...prev, description: res.description }))
      setNotice(`✨ AI description generated via ${res.provider}!`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "AI generation failed"
      setError(msg)
    } finally {
      setIsGeneratingDesc(false)
    }
  }

  function saveProduct(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    saveMutation.mutate()
  }

  return (
    <section className="admin-page">
      <div className="cart-heading sz-admin-dashboard-header">
        <div>
          <p className="eyebrow">GENZ ZONE OPERATIONS</p>
          <h1>Admin Dashboard<span className="brand-dot">.</span></h1>
        </div>
        <div className="sz-admin-profile-card" title={`Admin Profile: ${user.name} (${user.email})`}>
          <img
            src={user.avatar || "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"}
            alt="Admin Profile"
            className="sz-admin-profile-avatar-img"
          />
          <div className="sz-admin-profile-meta">
            <div className="sz-admin-profile-title-row">
              <span className="sz-admin-profile-name">{user.name}</span>
              <span className="sz-admin-verified-badge">👑 Administrator</span>
            </div>
            <span className="sz-admin-profile-email">{user.email}</span>
          </div>
        </div>
      </div>
      {error && <p className="form-message error-message" role="alert">{error}</p>}
      {notice && <p className="form-message success-message" role="status">{notice}</p>}

      <section className="admin-section">
        <h2>{editingId === null ? "Add new catalogue product" : `Edit product #${editingId}`}</h2>
        <form className="manage-form admin-product-form" onSubmit={saveProduct}>
          <label>
            Name
            <input
              required
              maxLength={200}
              placeholder="e.g. Wireless Noise Cancelling Over-Ear Headphones"
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </label>
          <div className="form-row">
            <label>
              Price
              <input
                required
                type="number"
                min="0"
                step="0.01"
                value={form.price}
                onChange={(event) => setForm({ ...form, price: Number(event.target.value) })}
              />
            </label>
            <label>
              Category
              <input
                required
                maxLength={100}
                placeholder="Electronics, Fashion, etc."
                value={form.category}
                onChange={(event) => setForm({ ...form, category: event.target.value })}
              />
            </label>
            <label>
              Stock Units
              <input
                type="number"
                min="0"
                value={form.stock ?? 50}
                onChange={(event) => setForm({ ...form, stock: Number(event.target.value) })}
              />
            </label>
          </div>
          <label>
            Image URL
            <input
              required
              type="url"
              placeholder="https://images.unsplash.com/..."
              value={form.image}
              onChange={(event) => setForm({ ...form, image: event.target.value })}
            />
          </label>

          {/* AI-Generated Description Section */}
          <div style={{ marginTop: "0.5rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
              <label style={{ margin: 0, fontWeight: 600 }}>Product Description</label>
              <button
                type="button"
                onClick={handleAiGenerateDescription}
                disabled={isGeneratingDesc}
                style={{
                  background: "linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)",
                  color: "#fff",
                  border: "none",
                  padding: "0.35rem 0.75rem",
                  borderRadius: "6px",
                  fontSize: "0.8rem",
                  fontWeight: 600,
                  cursor: isGeneratingDesc ? "not-allowed" : "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "0.35rem",
                }}
                title="Automatically generate an Amazon-grade persuasive description using AI copywriter"
              >
                {isGeneratingDesc ? "✨ Generating Copy..." : "✨ AI Generate Description"}
              </button>
            </div>
            <textarea
              rows={4}
              placeholder="Detailed description, bullet points, and product specifications..."
              value={form.description || ""}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              style={{
                width: "100%",
                padding: "0.6rem",
                borderRadius: "6px",
                border: "1px solid var(--line, #cbd5e1)",
                fontFamily: "inherit",
                fontSize: "0.875rem",
                boxSizing: "border-box",
              }}
            />
          </div>

          <div className="admin-form-actions" style={{ marginTop: "1rem" }}>
            <button className="primary-button" disabled={saveMutation.isPending} type="submit">
              {saveMutation.isPending ? "Saving to PostgreSQL..." : editingId === null ? "Create product" : "Save changes"}
            </button>
            {editingId !== null && (
              <button className="secondary-button" type="button" onClick={() => { setEditingId(null); setForm(emptyProduct) }}>
                Cancel edit
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="admin-section">
        <h2>Products</h2>
        {productsQuery.isPending ? <p role="status">Loading products...</p> : null}
        {productsQuery.isError ? <p className="error-message" role="alert">{productsQuery.error.message}</p> : null}
        {!productsQuery.isPending && !productsQuery.isError && productsQuery.data.length === 0
          ? <p>No products have been added.</p>
          : null}
        {productsQuery.data && productsQuery.data.length > 0 && (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead><tr><th>Product</th><th>Category</th><th>Price</th><th>Actions</th></tr></thead>
              <tbody>
                {productsQuery.data.map((product) => (
                  <tr key={product.id}>
                    <td>{product.name}</td><td>{product.category}</td><td>₹{product.price.toLocaleString("en-IN")}</td>
                    <td className="table-actions">
                      <Link className="text-button" to={`/products/${product.id}`}>View</Link>
                      <button className="text-button" type="button" onClick={() => startEdit(product)}>Edit</button>
                      <button className="text-button error-message" type="button" disabled={deleteMutation.isPending} onClick={() => deleteMutation.mutate(product.id)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <BulkCsvImport onImportComplete={refreshProducts} />
      </section>

      <section className="admin-section">
        <h2>Orders</h2>
        {ordersQuery.isPending ? <p role="status">Loading orders...</p> : null}
        {ordersQuery.isError ? <p className="error-message" role="alert">{ordersQuery.error.message}</p> : null}
        {!ordersQuery.isPending && !ordersQuery.isError && ordersQuery.data.length === 0
          ? <p>No customer orders yet.</p>
          : null}
        {ordersQuery.data && ordersQuery.data.length > 0 && (
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead><tr><th>Order</th><th>Customer</th><th>Delivery</th><th>Payment</th><th>Items</th><th>Total</th><th>Status</th><th>Update</th></tr></thead>
              <tbody>
                {ordersQuery.data.map((order) => (
                  <tr key={order.id}>
                    <td>#{order.id}<br /><small>{new Date(order.created_at).toLocaleDateString()}</small></td>
                    <td>{order.full_name}<br /><small>{order.email}<br />{order.phone}</small></td>
                    <td>{order.address}<br /><small>{order.city}, {order.state} {order.pincode}</small></td>
                    <td>{order.payment_method.replaceAll("_", " ")}</td>
                    <td>{order.items.map((item) => `${item.name} × ${item.quantity}`).join(", ")}</td>
                    <td>₹{order.total.toLocaleString("en-IN")}</td>
                    <td>{order.status}</td>
                    <td>
                      <select
                        aria-label={`Update status for order ${order.id}`}
                        disabled={statusMutation.isPending}
                        value={order.status}
                        onChange={(event) => statusMutation.mutate({ id: order.id, status: event.target.value })}
                      >
                        {orderStatuses.map((status) => <option key={status} value={status}>{status}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </section>
  )
}
