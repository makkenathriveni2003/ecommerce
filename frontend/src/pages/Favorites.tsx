import { useState } from "react"
import { Link } from "react-router-dom"
import { useCartStore } from "../store/cartStore"
import { useFavoritesStore } from "../store/favoritesStore"

export default function Favorites() {
  const favorites = useFavoritesStore((state) => state.favorites)
  const removeFavorite = useFavoritesStore((state) => state.removeFavorite)
  const clearFavorites = useFavoritesStore((state) => state.clearFavorites)
  const addToCart = useCartStore((state) => state.addToCart)

  const [notification, setNotification] = useState<string | null>(null)

  const showNotification = (msg: string) => {
    setNotification(msg)
    setTimeout(() => setNotification(null), 2500)
  }

  const handleMoveToBag = (item: typeof favorites[0]) => {
    addToCart(item, 1)
    removeFavorite(item.id)
    showNotification(`Added "${item.name}" to Bag & removed from Wishlist!`)
  }

  const handleAddAllToBag = () => {
    favorites.forEach((item) => addToCart(item, 1))
    showNotification(`All ${favorites.length} favorite items added to Bag!`)
  }

  return (
    <section className="favorites-page">
      {/* Toast Notification */}
      {notification && (
        <div className="favorites-toast" role="status" aria-live="polite">
          ✨ {notification}
        </div>
      )}

      {/* Header Banner */}
      <div className="favorites-header">
        <div>
          <nav className="breadcrumb-nav" aria-label="Breadcrumb">
            <Link to="/">Home</Link>
            <span className="breadcrumb-separator">&gt;</span>
            <span className="breadcrumb-current">My Wishlist</span>
          </nav>
          <h1>
            My Saved Favorites <span className="favorites-count-badge">♥ {favorites.length}</span>
          </h1>
          <p className="favorites-subtitle">
            Curated items you love from GenZ Zone. Saved persistently in your browser session for seamless checkout.
          </p>
        </div>

        {favorites.length > 0 && (
          <div className="favorites-bulk-actions">
            <button
              type="button"
              className="primary-button"
              onClick={handleAddAllToBag}
              title="Move all items into shopping bag"
            >
              🛒 Move All to Bag
            </button>
            <button
              type="button"
              className="text-button remove-all-btn"
              onClick={clearFavorites}
              title="Clear all saved favorites"
            >
              Clear All
            </button>
          </div>
        )}
      </div>

      {/* Storage Information Note */}
      <div className="favorites-storage-info-bar">
        <span className="storage-icon">💾</span>
        <span>
          <strong>Storage Status:</strong> Your wishlist is saved in your device's persistent storage (<code>genzzone_favorites_storage</code>). It stays safe across page refreshes and browser visits!
        </span>
      </div>

      {favorites.length === 0 ? (
        <div className="empty-favorites-card">
          <div className="empty-favorites-icon">♡</div>
          <h2>Your Wishlist is Empty</h2>
          <p>
            You haven't saved any products yet! Tap the heart icon (<strong>♡</strong>) on any product card or details page to build your GenZ style wishlist.
          </p>
          <Link to="/" className="primary-button explore-btn">
            Explore Trending Ganzee Styles ⚡
          </Link>
        </div>
      ) : (
        <div className="favorites-grid" role="list" aria-label="Favorite Products">
          {favorites.map((product) => (
            <article key={product.id} className="favorite-item-card" role="listitem">
              <div className="favorite-image-wrapper">
                <Link to={`/products/${product.id}`} aria-label={`View ${product.name}`}>
                  <img
                    src={product.image}
                    alt={product.name}
                    className="favorite-image"
                    loading="lazy"
                  />
                </Link>
                <button
                  type="button"
                  className="favorite-remove-corner-btn"
                  onClick={() => {
                    removeFavorite(product.id)
                    showNotification(`Removed "${product.name}" from Wishlist`)
                  }}
                  title="Remove from wishlist"
                  aria-label={`Remove ${product.name} from wishlist`}
                >
                  ✕
                </button>
                <span className="favorite-category-pill">{product.category}</span>
              </div>

              <div className="favorite-details">
                <h2 className="favorite-title">
                  <Link to={`/products/${product.id}`}>{product.name}</Link>
                </h2>

                <div className="favorite-pricing">
                  <span className="favorite-current-price">₹{product.price.toLocaleString("en-IN")}</span>
                  <span className="favorite-mrp">₹{Math.round(product.price * 1.3).toLocaleString("en-IN")}</span>
                  <span className="favorite-discount">23% off</span>
                </div>

                <div className="favorite-stock-status">
                  <span className="in-stock-dot">●</span> In Stock &bull; Ready for Express Dispatch
                </div>

                <div className="favorite-actions">
                  <button
                    type="button"
                    className="primary-button add-to-bag-btn"
                    onClick={() => handleMoveToBag(product)}
                  >
                    <span>🛒</span> Move to Bag
                  </button>
                  <Link
                    to={`/products/${product.id}`}
                    className="secondary-button view-details-btn"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
