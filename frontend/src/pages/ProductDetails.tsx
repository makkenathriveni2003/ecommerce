import { useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link, useParams } from "react-router-dom"
import { getProduct, getSimilarProducts } from "../services/productService"
import { useCartStore } from "../store/cartStore"
import { useFavoritesStore } from "../store/favoritesStore"
import { getProductVariants } from "../utils/productVariants"
import { getProductRatingData } from "../utils/productReviews"

export default function ProductDetails() {
  const { productId } = useParams()
  const id = Number(productId)
  const addToCart = useCartStore((state) => state.addToCart)

  const isFavorite = useFavoritesStore((state) => state.isFavorite(id))
  const toggleFavorite = useFavoritesStore((state) => state.toggleFavorite)
  const favoritesCount = useFavoritesStore((state) => state.getFavoritesCount())

  const [selectedColor, setSelectedColor] = useState<string>("")
  const [selectedSize, setSelectedSize] = useState<string>("M")
  const [quantity, setQuantity] = useState<number>(1)
  const [activeImageIndex, setActiveImageIndex] = useState<number>(0)
  const [wishlistToast, setWishlistToast] = useState<string | null>(null)
  const [justAdded, setJustAdded] = useState<boolean>(false)
  const [detailsOpen, setDetailsOpen] = useState<boolean>(true)
  const [isZoomed, setIsZoomed] = useState<boolean>(false)
  const [zoomPos, setZoomPos] = useState<{ x: number; y: number }>({ x: 50, y: 50 })
  const [deliveryPincode, setDeliveryPincode] = useState<string>("500001")
  const [pincodeInput, setPincodeInput] = useState<string>("")
  const [pincodeStatus, setPincodeStatus] = useState<string | null>(
    "Eligible for Free Express Delivery by Tomorrow, 11 AM • Cash on Delivery available"
  )

  const handleImageMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100))
    const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100))
    setZoomPos({ x, y })
  }

  const handleCheckPincode = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = pincodeInput.trim()
    if (/^\d{6}$/.test(trimmed)) {
      setDeliveryPincode(trimmed)
      setPincodeStatus(`✓ Eligible for Free Express Delivery by Tomorrow to ${trimmed}! Cash on Delivery available.`)
      setPincodeInput("")
    } else {
      setPincodeStatus("Please enter a valid 6-digit Indian PIN code (e.g., 500001).")
    }
  }

  const productQuery = useQuery({
    queryKey: ["product", id],
    queryFn: ({ signal }) => getProduct(id, { signal }),
    enabled: Number.isInteger(id) && id > 0,
  })

  const similarQuery = useQuery({
    queryKey: ["similar-products", id],
    queryFn: ({ signal }) => getSimilarProducts(id, 4, { signal }),
    enabled: Number.isInteger(id) && id > 0,
  })

  const product = productQuery.data

  const variantConfig = useMemo(() => {
    if (!product) return null
    return getProductVariants(product)
  }, [product])

  const ratingData = useMemo(() => {
    if (!product) return null
    return getProductRatingData(product)
  }, [product])

  if (!Number.isInteger(id) || id < 1) {
    return <p className="status-message" role="alert">That product ID is invalid.</p>
  }
  if (productQuery.isPending) {
    return <p className="status-message" role="status">Loading product...</p>
  }
  if (productQuery.isError || !product || !variantConfig) {
    return <p className="status-message" role="alert">{productQuery.error?.message || "Product not found"}</p>
  }

  // Active color variant (defaults to first variant if none selected)
  const activeColorName = selectedColor || variantConfig.defaultColor
  const activeVariant =
    variantConfig.colors.find((col) => col.name === activeColorName) ||
    variantConfig.colors[0]
  const activeSize = selectedSize || variantConfig.defaultSize

  // Multi-angle views gallery for the active selected color
  const galleryViews = activeVariant.angles
  const activeImage = galleryViews[activeImageIndex]?.full || galleryViews[0].full

  const categoryLower = (product.category || "").toLowerCase()
  const nameLower = (product.name || "").toLowerCase()

  const isApparel = variantConfig.isApparel
  const isElectronics =
    categoryLower.includes("electronic") ||
    categoryLower.includes("tech") ||
    categoryLower.includes("gadget") ||
    nameLower.includes("phone") ||
    nameLower.includes("headphone") ||
    nameLower.includes("wireless") ||
    nameLower.includes("watch")

  const originalPrice = Math.round(product.price * 1.3)
  const discountLabel = "23% off"
  const stockCount = typeof product.stock === "number" ? product.stock : 50
  const isOutOfStock = stockCount <= 0

  const handleColorChange = (colorName: string) => {
    setSelectedColor(colorName)
    setActiveImageIndex(0) // Reset to front showcase of the selected color!
  }

  const handleAddToCart = () => {
    if (isOutOfStock) return
    addToCart(product, quantity)
    setJustAdded(true)
    setTimeout(() => setJustAdded(false), 2000)
  }

  const handleToggleWishlist = () => {
    const isNowFav = toggleFavorite(product)
    setWishlistToast(
      isNowFav
        ? `Saved "${product.name}" (${activeColorName}) to Favorites ♥`
        : `Removed from Favorites`,
    )
    setTimeout(() => setWishlistToast(null), 2800)
  }

  return (
    <section className="product-detail-page">
      {/* Interactive Wishlist Notification Toast */}
      {wishlistToast && (
        <div className="product-detail-toast" role="status" aria-live="polite">
          <span>✨ {wishlistToast}</span>
          <Link to="/favorites" className="toast-link">
            Open Wishlist ({favoritesCount}) &rarr;
          </Link>
        </div>
      )}

      {/* Breadcrumb Navigation + Wishlist Link */}
      <div className="breadcrumb-wrapper">
        <nav className="breadcrumb-nav" aria-label="Breadcrumb">
          <Link to="/">Home</Link>
          <span className="breadcrumb-separator">&gt;</span>
          <Link to="/">{product.category}</Link>
          <span className="breadcrumb-separator">&gt;</span>
          <span className="breadcrumb-current">{product.name}</span>
        </nav>
        <Link to="/favorites" className="top-wishlist-indicator" title="Go to My Favorites">
          ♥ Wishlist ({favoritesCount})
        </Link>
      </div>

      <article className="product-detail">
        {/* Left Column: 3 Distinct Gallery Thumbnails + Main Showcase Image */}
        <div className="product-detail-gallery-container">
          {galleryViews.length > 1 && (
            <div className="product-gallery-thumbnails" role="tablist" aria-label="Product Image Views">
              {galleryViews.map((item, idx) => (
                <button
                  key={idx}
                  type="button"
                  role="tab"
                  aria-selected={activeImageIndex === idx}
                  className={`gallery-thumb-btn ${activeImageIndex === idx ? "active" : ""}`}
                  onClick={() => setActiveImageIndex(idx)}
                  onMouseEnter={() => setActiveImageIndex(idx)}
                  title={`${item.label} (${activeColorName})`}
                >
                  <img
                    src={item.thumb}
                    alt={`${product.name} ${item.label}`}
                    onError={(e) => {
                      const target = e.currentTarget
                      if (target.src !== product.image) {
                        target.src = product.image
                      }
                    }}
                  />
                  <span className="thumb-angle-label">{item.label}</span>
                </button>
              ))}
            </div>
          )}

          <div
            className="product-main-image-card"
            onMouseEnter={() => setIsZoomed(true)}
            onMouseLeave={() => setIsZoomed(false)}
            onMouseMove={handleImageMouseMove}
          >
            <div className="product-image-zoom-viewport">
              <img
                src={activeImage}
                alt={`${product.name} - ${activeColorName} (${galleryViews[activeImageIndex]?.label || "View"})`}
                className="product-detail-image"
                width={520}
                height={520}
                style={{
                  transformOrigin: `${zoomPos.x}% ${zoomPos.y}%`,
                  transform: isZoomed ? "scale(2.2)" : "scale(1)",
                  transition: isZoomed ? "transform 0.05s ease-out" : "transform 0.25s ease-out",
                  cursor: isZoomed ? "crosshair" : "zoom-in",
                }}
                onError={(e) => {
                  const target = e.currentTarget
                  if (target.src !== product.image) {
                    target.src = product.image
                  }
                }}
              />
            </div>

            {discountLabel && (
              <span className="product-detail-badge" aria-label={`Discount: ${discountLabel}`}>
                🔥 Festive Deal: {discountLabel}
              </span>
            )}

            {/* Amazon-Style HD Clarity & Zoom Status Bar */}
            <div className={`amazon-zoom-status-bar ${isZoomed ? "active" : ""}`} aria-live="polite">
              <span className="zoom-icon">🔍</span>
              <span className="zoom-angle-tag">{galleryViews[activeImageIndex]?.label || "Front View"}</span>
              <span className="zoom-divider">•</span>
              <span className="zoom-hint-text">
                {isZoomed
                  ? "2.2x Optical Clarity Zoom — Move cursor to inspect texture & stitching"
                  : "Hover image to zoom & inspect HD clarity"}
              </span>
            </div>

            {/* Pagination indicator dots */}
            {galleryViews.length > 1 && (
              <div className="gallery-indicator-dots" aria-hidden="true">
                {galleryViews.map((_, idx) => (
                  <span
                    key={idx}
                    className={`indicator-dot ${activeImageIndex === idx ? "active" : ""}`}
                    onClick={() => setActiveImageIndex(idx)}
                    title={`View ${galleryViews[idx].label}`}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Title, Selected Color, Rating, Price, Options, Add to Cart */}
        <div className="product-detail-info">
          <div className="product-brand-tag">GENZ ZONE OFFICIAL</div>
          <h1>{product.name}</h1>
          {activeColorName && (
            <div className="product-selected-variant-tag">
              Color Style: <strong>{activeColorName}</strong>
            </div>
          )}

          {/* Star Rating & Reviews */}
          <div className="product-reviews-row">
            <span className="stars-row" aria-label={`Rating: ${ratingData?.score || 4.8} out of 5 stars`}>
              {"★".repeat(Math.floor(ratingData?.score || 4.8))}
            </span>
            <span className="rating-score">{ratingData?.score || 4.8}</span>
            <span className="reviews-count">({ratingData?.totalReviews || 184} verified reviews)</span>
          </div>

          {/* Pricing & Stock Badge */}
          <div className="product-detail-pricing">
            <span className="product-detail-price">
              ₹{product.price.toLocaleString("en-IN")}
            </span>
            {originalPrice > product.price && (
              <span className="product-original-price" aria-label={`M.R.P.: ₹${originalPrice}`}>
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
              aria-label={stockCount > 0 ? `${stockCount} units available` : "Out of stock"}
            >
              {stockCount > 0 ? `In Stock (${stockCount} units left)` : "Out of Stock"}
            </span>
            <span className="fast-shipping-badge">⚡ Prime Same-Day Delivery eligible</span>
          </div>

          {/* Description */}
          {product.description && (
            <p className="product-hero-description">{product.description}</p>
          )}

          {/* Amazon-Style Color Selection Swatches with Visual Feedback */}
          <div className="product-swatches-section">
            <div className="swatches-label-row">
              <span className="section-label">
                Color: <strong>{activeColorName}</strong>
              </span>
              <span className="swatches-count-hint">
                ({variantConfig.colors.length} Amazon-style color finishes)
              </span>
            </div>
            <div className="color-swatches-row" role="radiogroup" aria-label="Select Color">
              {variantConfig.colors.map((col) => (
                <button
                  key={col.name}
                  type="button"
                  role="radio"
                  aria-checked={activeColorName === col.name}
                  className={`color-swatch-btn ${activeColorName === col.name ? "active" : ""}`}
                  onClick={() => handleColorChange(col.name)}
                  style={{ backgroundColor: col.hex }}
                  title={`${col.name} (Click to switch images & angles)`}
                  aria-label={`Color: ${col.name}`}
                >
                  <span className="color-swatch-tick">{activeColorName === col.name ? "✓" : ""}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Size / Option Selector */}
          {variantConfig.sizes && variantConfig.sizes.length > 1 && (
            <div className="product-size-section">
              <span className="section-label">
                {variantConfig.optionLabel}: <strong>{activeSize}</strong>
              </span>
              <div className="size-pills-row" role="radiogroup" aria-label={variantConfig.optionLabel}>
                {variantConfig.sizes.map((size) => (
                  <button
                    key={size}
                    type="button"
                    role="radio"
                    aria-checked={activeSize === size}
                    className={`size-pill-btn ${activeSize === size ? "active" : ""}`}
                    onClick={() => setSelectedSize(size)}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Amazon-Style Pincode Delivery Options */}
          <div className="pincode-delivery-card">
            <div className="pincode-card-header">
              <span className="pincode-icon">📍</span>
              <span className="pincode-title">
                Deliver to: <strong>{deliveryPincode}</strong>
              </span>
            </div>
            <form className="pincode-input-row" onSubmit={handleCheckPincode}>
              <input
                type="text"
                className="pincode-input"
                placeholder="Enter 6-digit PIN code"
                value={pincodeInput}
                onChange={(e) => setPincodeInput(e.target.value.replace(/\D/g, "").slice(0, 6))}
                maxLength={6}
                aria-label="Enter PIN code for delivery estimate"
              />
              <button type="submit" className="pincode-check-btn">
                Check
              </button>
            </form>
            {pincodeStatus && (
              <p className={`pincode-status-text ${pincodeStatus.startsWith("✓") ? "success" : "info"}`}>
                {pincodeStatus}
              </p>
            )}
          </div>

          {/* Quantity Selector + Add to Cart + Persistent Favorites Button */}
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
              className={`wishlist-toggle-btn ${isFavorite ? "active" : ""}`}
              onClick={handleToggleWishlist}
              aria-label={isFavorite ? "Remove from wishlist" : "Add to wishlist"}
              title={isFavorite ? "Remove from Favorites" : "Save to Favorites"}
            >
              {isFavorite ? "♥" : "♡"}
            </button>
          </div>

          {/* Trust Badges */}
          <div className="trust-badges-grid">
            <div className="trust-badge-item">
              <span className="trust-icon">🚚</span>
              <div className="trust-text">
                <strong>Free Delivery</strong>
                <span>On orders above ₹499</span>
              </div>
            </div>
            <div className="trust-badge-item">
              <span className="trust-icon">🔄</span>
              <div className="trust-text">
                <strong>7 Days Replacement</strong>
                <span>Hassle-free guarantee</span>
              </div>
            </div>
            <div className="trust-badge-item">
              <span className="trust-icon">🛡️</span>
              <div className="trust-text">
                <strong>100% Genuine</strong>
                <span>GenZ Zone Assured</span>
              </div>
            </div>
          </div>
        </div>
      </article>

      {/* Feature Highlights Banner */}
      <div className="features-highlights-banner">
        <div className="feature-highlight-card">
          <span className="feature-icon">{isApparel ? "☁️" : isElectronics ? "⚡" : "✨"}</span>
          <div>
            <h4>{isApparel ? "100% Breathable Cotton" : isElectronics ? "High Performance" : "GenZ Zone Select"}</h4>
            <p>{isApparel ? "All-Day Comfort" : isElectronics ? "Next-Gen Architecture" : "Verified Quality"}</p>
          </div>
        </div>
        <div className="feature-highlight-card">
          <span className="feature-icon">🛡️</span>
          <div>
            <h4>Premium Grade</h4>
            <p>10-Point Quality Inspected</p>
          </div>
        </div>
        <div className="feature-highlight-card">
          <span className="feature-icon">{isApparel ? "🪶" : "📦"}</span>
          <div>
            <h4>{isApparel ? "Regular Fit" : "Eco-Friendly Packaging"}</h4>
            <p>{isApparel ? "Standard Indian Sizing" : "Damage-Proof Delivery"}</p>
          </div>
        </div>
      </div>

      {/* Product Details Specs Accordion */}
      <div className="product-spec-accordion">
        <button
          type="button"
          className="spec-accordion-header"
          onClick={() => setDetailsOpen((prev) => !prev)}
          aria-expanded={detailsOpen}
        >
          <h2>Product Specifications &amp; Variant Details</h2>
          <span className="accordion-arrow">{detailsOpen ? "⌃" : "⌄"}</span>
        </button>

        {detailsOpen && (
          <div className="spec-accordion-body">
            <div className="spec-grid-row">
              <div className="spec-item">
                <span className="spec-label">Selected Color</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">{activeColorName}</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Category</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">{product.category}</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Material / Fabric</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">
                  {isApparel
                    ? "100% Breathable Combed Cotton / Silk-Touch Modal / Premium Denim"
                    : product.category === "Shoes"
                    ? "Premium Vegan Leather & Responsive Memory Foam Insole"
                    : product.category === "Jewellery"
                    ? "22K Royal Gold Plating with Anti-Tarnish Finish"
                    : product.category === "Bags"
                    ? "Structured Italian Vegan Leather & Weatherproof Lining"
                    : "Aerospace-Grade Alloy & Precision Circuitry"}
                </span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Fit / Style Profile</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">
                  {isApparel
                    ? "Athletic Modern Fit (Standard Indian sizing)"
                    : product.category === "Shoes"
                    ? "Ergonomic Comfort Insole (UK/India sizing)"
                    : "Precision Luxury Craftsmanship"}
                </span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Pattern &amp; Weave</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">
                  {isApparel ? "Artisanal Dye & Reinforced Flatlock Seams" : "High-Gloss Laser Finish"}
                </span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Occasion</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">
                  {isApparel
                    ? "Streetwear, Athleisure, Festive Ethnic & Everyday Casual"
                    : "Daily Performance & Lifestyle"}
                </span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Care Instructions</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">
                  {isApparel
                    ? "Machine Wash Cold (30°C), Tumble Dry Low, Do Not Bleach"
                    : "Wipe clean with a soft dry cloth"}
                </span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Country of Origin</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">India (GenZ Zone Certified Authentic)</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Seller</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">GenZ Zone Official Flagship Store</span>
              </div>
              <div className="spec-item">
                <span className="spec-label">Warranty &amp; Returns</span>
                <span className="spec-colon">:</span>
                <span className="spec-val">1 Year Brand Warranty • 7-Day Doorstep Replacement</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Customer Ratings & Reviews Breakdown */}
      <section className="product-reviews-breakdown-section" aria-label="Customer Reviews">
        <div className="reviews-section-header">
          <div>
            <p className="eyebrow">CUSTOMER FEEDBACK</p>
            <h3>Customer Reviews &amp; Ratings</h3>
          </div>
          <span className="verified-purchases-badge">✓ 100% Verified Shoppers</span>
        </div>

        <div className="ratings-summary-grid">
          <div className="ratings-overall-card">
            <div className="big-rating-number">{ratingData?.score || 4.8}</div>
            <div className="stars-row">{"★".repeat(Math.floor(ratingData?.score || 4.8))}</div>
            <p className="rating-subtitle">Based on {ratingData?.totalReviews || 184} verified reviews</p>
            <div className="recommend-percent-pill">👍 {ratingData?.recommendPercent || 96}% of buyers recommend this product</div>
          </div>

          <div className="ratings-bars-list">
            <div className="rating-bar-row">
              <span className="bar-star-label">5 Star</span>
              <div className="rating-bar-track">
                <div className="rating-bar-fill" style={{ width: `${ratingData?.distribution.star5 || 84}%` }}></div>
              </div>
              <span className="bar-star-percent">{ratingData?.distribution.star5 || 84}%</span>
            </div>
            <div className="rating-bar-row">
              <span className="bar-star-label">4 Star</span>
              <div className="rating-bar-track">
                <div className="rating-bar-fill" style={{ width: `${ratingData?.distribution.star4 || 11}%` }}></div>
              </div>
              <span className="bar-star-percent">{ratingData?.distribution.star4 || 11}%</span>
            </div>
            <div className="rating-bar-row">
              <span className="bar-star-label">3 Star</span>
              <div className="rating-bar-track">
                <div className="rating-bar-fill" style={{ width: `${ratingData?.distribution.star3 || 3}%` }}></div>
              </div>
              <span className="bar-star-percent">{ratingData?.distribution.star3 || 3}%</span>
            </div>
            <div className="rating-bar-row">
              <span className="bar-star-label">2 Star</span>
              <div className="rating-bar-track">
                <div className="rating-bar-fill" style={{ width: `${ratingData?.distribution.star2 || 1}%` }}></div>
              </div>
              <span className="bar-star-percent">{ratingData?.distribution.star2 || 1}%</span>
            </div>
            <div className="rating-bar-row">
              <span className="bar-star-label">1 Star</span>
              <div className="rating-bar-track">
                <div className="rating-bar-fill" style={{ width: `${ratingData?.distribution.star1 || 1}%` }}></div>
              </div>
              <span className="bar-star-percent">{ratingData?.distribution.star1 || 1}%</span>
            </div>
          </div>
        </div>

        <div className="featured-reviews-grid">
          {(ratingData?.reviews || []).map((rev, idx) => (
            <div key={idx} className="featured-review-card">
              <div className="review-top-row">
                <span className="stars-row">{"★".repeat(rev.stars)}</span>
                <span className="verified-badge">✓ Verified Buyer</span>
              </div>
              <h4 className="review-title">&ldquo;{rev.title}&rdquo;</h4>
              <p className="review-comment">&ldquo;{rev.comment}&rdquo;</p>
              <span className="reviewer-author">— {rev.author}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Complete The Look • Style With Different Clothes Section */}
      {similarQuery.data && similarQuery.data.length > 0 && (
        <section className="similar-products-section" aria-label="Style With Different Clothes">
          <div className="similar-products-header">
            <div>
              <p className="eyebrow">COMPLETE THE LOOK • STYLED BY GENZ ZONE</p>
              <h3>Style With Different Clothes &amp; Accessories</h3>
            </div>
            <span className="similar-verified-tag">✨ Curated Outfit Pairings</span>
          </div>

          <div className="similar-products-grid">
            {similarQuery.data.map((item) => (
              <div key={item.id} className="similar-product-card">
                <Link to={`/products/${item.id}`} className="similar-card-image-wrap">
                  <img
                    src={item.image}
                    alt={item.name}
                    loading="lazy"
                    onError={(e) => {
                      const target = e.currentTarget
                      target.src = "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=500"
                    }}
                  />
                  <span className="similar-card-badge">{item.category}</span>
                </Link>
                <div className="similar-card-body">
                  <h4 className="similar-card-title">
                    <Link to={`/products/${item.id}`} title={item.name}>{item.name}</Link>
                  </h4>
                  <div className="similar-card-price-row">
                    <span className="similar-card-price">₹{item.price.toLocaleString("en-IN")}</span>
                    <button
                      type="button"
                      className="similar-card-add-btn"
                      onClick={() => addToCart(item, 1)}
                      title="Add to Bag"
                      aria-label={`Add ${item.name} to Bag`}
                    >
                      + Bag
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </section>
  )
}
