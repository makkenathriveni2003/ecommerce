import { useState, type FormEvent } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "../store/authStore"
import { createProduct, type NewProduct } from "../services/productService"
import Login from "./Login"

const emptyProduct: NewProduct = {
  name: "",
  price: 0,
  category: "",
  image: "",
}

export default function ManageProducts() {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const queryClient = useQueryClient()
  const [product, setProduct] = useState<NewProduct>(emptyProduct)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const productMutation = useMutation({
    mutationFn: () => createProduct(product, token!),
    onSuccess: async (created) => {
      setProduct(emptyProduct)
      setError(null)
      setNotice(`${created.name} was added to the shop.`)
      await queryClient.invalidateQueries({ queryKey: ["products"] })
    },
    onError: (productError) => setError(productError.message),
  })

  function handleProductSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) return
    setError(null)
    setNotice(null)
    productMutation.reset()
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
            Only an administrator can add or manage products.
          </p>
        </div>
      </section>
    )
  }

  return (
    <section className="manage-page">
      <div className="manage-panel">
        <p className="eyebrow">SHOP MANAGEMENT</p>
        <h1>Add a product.</h1>
        <p className="manage-intro">
          Add product details below and they’ll be saved to your shop database.
        </p>
        <form className="manage-form" onSubmit={handleProductSubmit}>
          <label>
            Product name
            <input
              maxLength={200}
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
                onChange={(event) => setProduct({ ...product, category: event.target.value })}
                required
                value={product.category}
              />
            </label>
          </div>
          <label>
            Image URL
            <input
              onChange={(event) => setProduct({ ...product, image: event.target.value })}
              required
              type="url"
              value={product.image}
            />
          </label>
          {(error || productMutation.error) && (
            <p className="form-message error-message" role="alert">
              {error ?? productMutation.error?.message}
            </p>
          )}
          {notice && <p className="form-message success-message" role="status">{notice}</p>}
          <button className="primary-button" disabled={productMutation.isPending} type="submit">
            {productMutation.isPending ? "Saving..." : "Add product"}
          </button>
        </form>
      </div>
    </section>
  )
}
