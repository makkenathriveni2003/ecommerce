import { useState, type FormEvent } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "../store/authStore"
import { createProduct, type NewProduct } from "../services/productService"
import { generateAIDescription } from "../services/aiService"
import Login from "./Login"

const emptyProduct: NewProduct = {
  name: "",
  price: 0,
  category: "",
  image: "",
  description: "",
  stock: 50,
}

export default function ManageProducts() {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const queryClient = useQueryClient()
  const [product, setProduct] = useState<NewProduct>(emptyProduct)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [isGeneratingDesc, setIsGeneratingDesc] = useState(false)

  const productMutation = useMutation({
    mutationFn: () => createProduct(product, token!),
    onSuccess: async (created) => {
      setProduct(emptyProduct)
      setError(null)
      setNotice(`${created.name} was added to the GenZ Zone shop database.`)
      await queryClient.invalidateQueries({ queryKey: ["products"] })
    },
    onError: (productError) => setError(productError.message),
  })

  async function handleAiGenerateDescription() {
    if (!product.name.trim() || !product.category.trim()) {
      setError("Please enter product name and category first so the AI copywriter has context.")
      return
    }
    setError(null)
    setIsGeneratingDesc(true)
    try {
      const res = await generateAIDescription({
        name: product.name.trim(),
        category: product.category.trim(),
        price: product.price > 0 ? product.price : undefined,
      })
      setProduct((prev) => ({ ...prev, description: res.description }))
      setNotice(`✨ AI description generated via ${res.provider}!`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "AI generation failed"
      setError(msg)
    } finally {
      setIsGeneratingDesc(false)
    }
  }

  function handleProductSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setNotice(null)
    productMutation.mutate()
  }

  if (!user || !token) {
    return <Login />
  }

  if (user.role !== "admin") {
    return (
      <section className="manage-page">
        <div className="manage-panel">
          <h1>Administrator access required.</h1>
          <p className="manage-intro">
            Only a GenZ Zone administrator can add or manage products.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="manage-page">
      <div className="manage-panel">
        <p className="eyebrow">GENZ ZONE CATALOGUE MANAGEMENT</p>
        <h1>Add a product<span className="brand-dot">.</span></h1>
        <p className="manage-intro">
          Add product details below and they’ll be saved to your PostgreSQL database and indexed for semantic AI search.
        </p>
        <form className="manage-form" onSubmit={handleProductSubmit}>
          <label>
            Product name
            <input
              maxLength={200}
              placeholder="e.g. Wireless Noise Cancelling Headphones"
              onChange={(event) => setProduct({ ...product, name: event.target.value })}
              required
              value={product.name}
            />
          </label>
          <div className="form-row">
            <label>
              Price (₹)
              <input
                min="0"
                onChange={(event) =>
                  setProduct({ ...product, price: Number(event.target.value) })
                }
                required
                step="0.01"
                type="number"
                value={product.price}
              />
            </label>
            <label>
              Category
              <input
                maxLength={100}
                placeholder="Electronics, Fashion, etc."
                onChange={(event) => setProduct({ ...product, category: event.target.value })}
                required
                value={product.category}
              />
            </label>
            <label>
              Stock
              <input
                min="0"
                type="number"
                value={product.stock ?? 50}
                onChange={(event) => setProduct({ ...product, stock: Number(event.target.value) })}
              />
            </label>
          </div>
          <label>
            Image URL
            <input
              onChange={(event) => setProduct({ ...product, image: event.target.value })}
              required
              type="url"
              placeholder="https://images.unsplash.com/..."
              value={product.image}
            />
          </label>

          {/* AI Description Generator */}
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
                }}
              >
                {isGeneratingDesc ? "✨ Generating Copy..." : "✨ AI Generate Description"}
              </button>
            </div>
            <textarea
              rows={4}
              placeholder="Persuasive description and key specifications..."
              value={product.description || ""}
              onChange={(event) => setProduct({ ...product, description: event.target.value })}
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

          {(error || productMutation.error) && (
            <p className="form-message error-message" role="alert">
              {error ?? productMutation.error?.message}
            </p>
          )}
          {notice && <p className="form-message success-message" role="status">{notice}</p>}
          <button className="primary-button" disabled={productMutation.isPending} type="submit" style={{ marginTop: "1rem" }}>
            {productMutation.isPending ? "Saving to PostgreSQL..." : "Add product"}
          </button>
        </form>
      </div>
    </section>
  )
}
