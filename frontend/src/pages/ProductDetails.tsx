import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link, useParams } from "react-router-dom"
import { getProduct } from "../services/productService"
import { useCartStore } from "../store/cartStore"

const SIZES = ["S", "M", "L", "XL", "XXL"]

export default function ProductDetails() {
  const { productId } = useParams()
  const id = Number(productId)
  const addToCart = useCartStore((state) => state.addToCart)

  const [selectedSize, setSelectedSize] = useState<string>("L")
  const [quantity, setQuantity] = useState<number>(1)
  const [justAdded, setJustAdded] = useState<boolean>(false)

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
  const isDevara = product.name.toLowerCase().includes("devara")
  const isApparel =
    product.category.toLowerCase().includes("fashion") ||
    product.name.toLowerCase().includes("shirt") ||
    product.name.toLowerCase().includes("dress") ||
    product.name.toLowerCase().includes("t-shirt")

  const originalPrice = isDevara ? 999 : null
  const discountLabel = isDevara ? "40% off" : null
  const stockCount = typeof product.stock === "number" ? product.stock : 25
  const isOutOfStock = stockCount <= 0

  const handleAddToCart = () => {
    if (isOutOfStock) return
    addToCart(product, quantity)
    setJustAdded(true)
    setTimeout(() => setJustAdded(false), 2000)
  }

  return (
    <section className="product-detail-page">
      <Link className="continue-link" to="/">← Back to the shop</Link>
      <article className="product-detail">
        <div className="product-detail-image-wrapper">
          <img
            src={product.image}
            alt={product.name}
            className="product-detail-image"
            width={600}
            height={450}
          />
          {discountLabel && (
            <span className="product-detail-badge" aria-label={`Discount: ${discountLabel}`}>
              {discountLabel}
            </span>
          )}
        </div>

        <div className="product-detail-info">
          <p className="eyebrow">
            {isDevara ? "Fashion → Unisex T-Shirts" : product.category}
          </p>
          <h1>{product.name}</h1>

          {/* Pricing & Discount */}
          <div className="product-detail-pricing">
            <span className="product-detail-price">
              ₹{product.price.toLocaleString("en-IN")}
            </span>
            {originalPrice && (
              <span className="product-original-price" aria-label={`Original price: ₹${originalPrice}`}>
                ₹{originalPrice.toLocaleString("en-IN")}
              </span>
            )}
            {discountLabel && (
              <span className="discount-pill">{discountLabel}</span>
            )}
          </div>

          {/* Stock Status */}
          <div className="stock-status-row">
            <span
              className={`stock-indicator ${stockCount > 0 ? "in-stock" : "out-of-stock"}`}
              aria-label={stockCount > 0 ? `${stockCount} pieces in stock` : "Out of stock"}
            >
              {stockCount > 0 ? `● In Stock (${stockCount} pieces available)` : "✕ Out of Stock"}
            </span>
            {isDevara && <span className="color-tag">Color: <strong>White</strong></span>}
          </div>

          {/* Sizes Selector for Apparel */}
          {isApparel && (
            <div className="product-size-section">
              <div className="size-header">
                <span className="section-subtitle">Select Size:</span>
                <span className="selected-size-label">Size {selectedSize}</span>
              </div>
              <div className="size-pills-row" role="radiogroup" aria-label="Available Sizes">
                {SIZES.map((size) => (
                  <button
                    key={size}
                    type="button"
                    role="radio"
                    aria-checked={selectedSize === size}
                    className={`size-pill-btn ${selectedSize === size ? "active" : ""}`}
                    onClick={() => setSelectedSize(size)}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Quantity Selector */}
          <div className="quantity-section">
            <span className="section-subtitle">Quantity:</span>
            <div className="quantity-controls">
              <button
                type="button"
                className="qty-btn"
                disabled={quantity <= 1 || isOutOfStock}
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                aria-label="Decrease quantity"
              >
                −
              </button>
              <span className="qty-value" aria-label={`Selected quantity: ${quantity}`}>
                {quantity}
              </span>
              <button
                type="button"
                className="qty-btn"
                disabled={quantity >= stockCount || isOutOfStock}
                onClick={() => setQuantity((q) => Math.min(stockCount, q + 1))}
                aria-label="Increase quantity"
              >
                +
              </button>
            </div>
          </div>

          {/* Description */}
          {product.description && (
            <div className="product-description-block">
              <h3 className="section-subtitle">About this item</h3>
              <p className="product-description-text">{product.description}</p>
            </div>
          )}

          {/* Add to Cart CTA */}
          <div className="product-actions-row">
            <button
              className="primary-button add-to-cart-cta"
              onClick={handleAddToCart}
              type="button"
              disabled={isOutOfStock}
              aria-label="Add to Cart"
            >
              {justAdded ? "✓ Added to Bag!" : isOutOfStock ? "Out of Stock" : "Add to Cart"}
            </button>
          </div>
        </div>
      </article>
    </section>
  )
}
