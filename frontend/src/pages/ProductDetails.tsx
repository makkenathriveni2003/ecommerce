import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link, useParams } from "react-router-dom"
import { getProduct } from "../services/productService"
import { useCartStore } from "../store/cartStore"

const SIZES = ["S", "M", "L", "XL", "XXL"]

const TDP_GALLERY = [
  {
    full: "/images/tdp_front_hd.jpg",
    thumb: "/images/tdp_thumb_front.jpg",
    label: "Front View",
  },
  {
    full: "/images/tdp_back_hd.jpg",
    thumb: "/images/tdp_thumb_back.jpg",
    label: "Back View",
  },
  {
    full: "/images/tdp_print_hd.jpg",
    thumb: "/images/tdp_thumb_print.jpg",
    label: "Print Detail",
  },
  {
    full: "/images/tdp_fabric_hd.jpg",
    thumb: "/images/tdp_thumb_fabric.jpg",
    label: "Fabric Texture",
  },
]

const TDP_COLOR_IMAGES: Record<string, string> = {
  Yellow: "/images/tdp_front_hd.jpg",
  White: "/images/tdp_white_hd.jpg",
  Black: "/images/tdp_black_hd.jpg",
}

const COLORS = [
  { name: "Yellow", hex: "#f59e0b" },
  { name: "White", hex: "#ffffff" },
  { name: "Black", hex: "#111827" },
]

export default function ProductDetails() {
  const { productId } = useParams()
  const id = Number(productId)
  const addToCart = useCartStore((state) => state.addToCart)

  const [selectedSize, setSelectedSize] = useState<string>("M")
  const [selectedColor, setSelectedColor] = useState<string>("Yellow")
  const [quantity, setQuantity] = useState<number>(1)
  const [activeImageIndex, setActiveImageIndex] = useState<number>(0)
  const [isWishlisted, setIsWishlisted] = useState<boolean>(false)
  const [justAdded, setJustAdded] = useState<boolean>(false)
  const [detailsOpen, setDetailsOpen] = useState<boolean>(true)

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
  const isTdp = product.name.toLowerCase().includes("tdp")
  const isDevara = product.name.toLowerCase().includes("devara")
  const isApparel =
    product.category.toLowerCase().includes("fashion") ||
    product.name.toLowerCase().includes("shirt") ||
    product.name.toLowerCase().includes("dress") ||
    product.name.toLowerCase().includes("t-shirt")

  const galleryViews = isTdp
    ? TDP_GALLERY
    : [{ full: product.image, thumb: product.image, label: product.name }]

  const mainImageSrc = isTdp
    ? selectedColor !== "Yellow"
      ? TDP_COLOR_IMAGES[selectedColor] || TDP_GALLERY[activeImageIndex]?.full || product.image
      : TDP_GALLERY[activeImageIndex]?.full || product.image
    : product.image

  const originalPrice = isDevara ? 999 : null
  const discountLabel = isDevara ? "40% off" : null
  const stockCount = typeof product.stock === "number" ? product.stock : 50
  const isOutOfStock = stockCount <= 0

  const handleAddToCart = () => {
    if (isOutOfStock) return
    addToCart(product, quantity)
    setJustAdded(true)
    setTimeout(() => setJustAdded(false), 2000)
  }

  return (
    <section className="product-detail-page">
      {/* Breadcrumb Navigation matching mockup */}
      <nav className="breadcrumb-nav" aria-label="Breadcrumb">
        <Link to="/">Home</Link>
        <span className="breadcrumb-separator">&gt;</span>
        <Link to="/">{product.category}</Link>
        <span className="breadcrumb-separator">&gt;</span>
        {isApparel && (
          <>
            <span>T-Shirts</span>
            <span className="breadcrumb-separator">&gt;</span>
          </>
        )}
        <span className="breadcrumb-current">{product.name}</span>
      </nav>

      <article className="product-detail">
        {/* Left Column: Gallery Thumbnails + Main Showcase Image */}
        <div className="product-detail-gallery-container">
          {galleryViews.length > 1 && (
            <div className="product-gallery-thumbnails" role="tablist" aria-label="Product Image Views">
              {galleryViews.map((item, idx) => (
                <button
                  key={item.thumb}
                  type="button"
                  role="tab"
                  aria-selected={activeImageIndex === idx}
                  className={`gallery-thumb-btn ${activeImageIndex === idx ? "active" : ""}`}
                  onClick={() => {
                    setActiveImageIndex(idx)
                    if (idx > 0 && selectedColor !== "Yellow") {
                      setSelectedColor("Yellow")
                    }
                  }}
                  title={item.label}
                >
                  <img src={item.thumb} alt={`${product.name} ${item.label}`} />
                </button>
              ))}
            </div>
          )}

          <div className="product-main-image-card">
            <img
              src={mainImageSrc}
              alt={product.name}
              className="product-detail-image"
              width={520}
              height={520}
            />
            {discountLabel && (
              <span className="product-detail-badge" aria-label={`Discount: ${discountLabel}`}>
                {discountLabel}
              </span>
            )}

            {/* Pagination indicator dots */}
            {galleryViews.length > 1 && (
              <div className="gallery-indicator-dots" aria-hidden="true">
                {galleryViews.map((_, idx) => (
                  <span
                    key={idx}
                    className={`indicator-dot ${activeImageIndex === idx ? "active" : ""}`}
                    onClick={() => setActiveImageIndex(idx)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Title, Rating, Price, Options, Add to Cart */}
        <div className="product-detail-info">
          <h1>{product.name}</h1>

          {/* Star Rating & Reviews */}
          <div className="product-reviews-row">
            <span className="stars-row" aria-label="Rating: 4.8 out of 5 stars">
              ★★★★★
            </span>
            <span className="rating-score">4.8</span>
            <span className="reviews-count">(124 reviews)</span>
          </div>

          {/* Pricing & Stock Badge */}
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

          <div className="stock-status-row">
            <span
              className={`stock-indicator-pill ${stockCount > 0 ? "in-stock" : "out-of-stock"}`}
              aria-label={stockCount > 0 ? `${stockCount} pieces in stock` : "Out of stock"}
            >
              {stockCount > 0 ? "In Stock" : "Out of Stock"}
            </span>
          </div>

          {/* Description */}
          {product.description && (
            <p className="product-hero-description">{product.description}</p>
          )}

          {/* Color Selection Swatches */}
          {isApparel && (
            <div className="product-swatches-section">
              <span className="section-label">Color</span>
              <div className="color-swatches-row" role="radiogroup" aria-label="Select Color">
                {COLORS.map((col) => (
                  <button
                    key={col.name}
                    type="button"
                    role="radio"
                    aria-checked={selectedColor === col.name}
                    className={`color-swatch-btn ${selectedColor === col.name ? "active" : ""}`}
                    onClick={() => {
                      setSelectedColor(col.name)
                      setActiveImageIndex(0)
                    }}
                    style={{ backgroundColor: col.hex }}
                    title={col.name}
                    aria-label={`Color: ${col.name}`}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Size Selector */}
          {isApparel && (
            <div className="product-size-section">
              <span className="section-label">Size</span>
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

          {/* Quantity Selector + Add to Cart + Wishlist */}
          <div className="purchase-controls-row">
            <div className="quantity-controls" aria-label="Quantity selector">
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

            <button
              className="primary-button add-to-cart-hero-btn"
              onClick={handleAddToCart}
              type="button"
              disabled={isOutOfStock}
              aria-label="Add to Cart"
            >
              <span className="cart-icon">🛒</span>
              <span>{justAdded ? "✓ Added to Bag!" : isOutOfStock ? "Out of Stock" : "Add to Cart"}</span>
            </button>

            <button
              type="button"
              className={`wishlist-toggle-btn ${isWishlisted ? "active" : ""}`}
              onClick={() => setIsWishlisted((prev) => !prev)}
              aria-label={isWishlisted ? "Remove from wishlist" : "Add to wishlist"}
              title="Add to Wishlist"
            >
              {isWishlisted ? "♥" : "♡"}
            </button>
          </div>

          {/* Trust Badges matching mockup */}
          <div className="trust-badges-grid">
            <div className="trust-badge-item">
              <span className="trust-icon">🚚</span>
              <div className="trust-text">
                <strong>Free Shipping</strong>
                <span>On orders above ₹999</span>
              </div>
            </div>
            <div className="trust-badge-item">
              <span className="trust-icon">🔄</span>
              <div className="trust-text">
                <strong>Easy Returns</strong>
                <span>Within 7 days</span>
              </div>
            </div>
            <div className="trust-badge-item">
              <span className="trust-icon">🛡️</span>
              <div className="trust-text">
                <strong>Secure Payment</strong>
                <span>100% safe & trusted</span>
              </div>
            </div>
          </div>
        </div>
      </article>

      {/* Feature Highlights Banner */}
      <div className="features-highlights-banner">
        <div className="feature-highlight-card">
          <span className="feature-icon">☁️</span>
          <div>
            <h4>100% Cotton</h4>
            <p>Bio Wash</p>
          </div>
        </div>
        <div className="feature-highlight-card">
          <span className="feature-icon">🛡️</span>
          <div>
            <h4>Premium Quality</h4>
            <p>Long Lasting Print</p>
          </div>
        </div>
        <div className="feature-highlight-card">
          <span className="feature-icon">🪶</span>
          <div>
            <h4>Regular Fit</h4>
            <p>Comfortable Wear</p>
          </div>
        </div>
      </div>

      {/* Product Details Specs Accordion matching mockup */}
      <div className="product-spec-accordion">
        <button
          type="button"
          className="spec-accordion-header"
          onClick={() => setDetailsOpen((prev) => !prev)}
          aria-expanded={detailsOpen}
        >
          <h2>Product Details</h2>
          <span className="accordion-arrow">{detailsOpen ? "⌃" : "⌄"}</span>
        </button>

        {detailsOpen && (
          <div className="spec-accordion-body">
            <div className="spec-grid-row">
              <div className="spec-item">
                <span className="spec-label">Fabric</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">100% Cotton (Bio Wash)</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Print</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">High Quality, Fade Resistant Digital Print</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Fit</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">Regular Fit</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
