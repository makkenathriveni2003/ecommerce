import { useQuery } from "@tanstack/react-query"
import { Link, useParams } from "react-router-dom"
import { getProduct } from "../services/productService"
import { useCartStore } from "../store/cartStore"

export default function ProductDetails() {
  const { productId } = useParams()
  const id = Number(productId)
  const addToCart = useCartStore((state) => state.addToCart)
  const productQuery = useQuery({
    queryKey: ["product", id],
    queryFn: ({ signal }) => getProduct(id, { signal }),
    enabled: Number.isInteger(id) && id > 0,
  })

  if (!Number.isInteger(id) || id < 1) {
    return <p className="status-message" role="alert">That product ID is invalid.</p>
  }
  if (productQuery.isPending) {
    return <p className="status-message" role="status">Loading product...</p>
  }
  if (productQuery.isError) {
    return <p className="status-message" role="alert">{productQuery.error.message}</p>
  }

  const product = productQuery.data
  return (
    <section className="product-detail-page">
      <Link className="continue-link" to="/">← Back to the shop</Link>
      <article className="product-detail">
        <img src={product.image} alt={product.name} />
        <div className="product-detail-info">
          <p className="eyebrow">{product.category}</p>
          <h1>{product.name}</h1>
          <p className="product-detail-price">₹{product.price.toLocaleString("en-IN")}</p>
          <button className="primary-button" onClick={() => addToCart(product)} type="button">
            Add to Cart
          </button>
        </div>
      </article>
    </section>
  )
}
