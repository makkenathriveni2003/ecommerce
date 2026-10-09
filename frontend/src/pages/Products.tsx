import { useCallback, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { useProducts } from "../hooks/useProducts"
import { useIntersectionObserver } from "../hooks/useIntersectionObserver"
import { searchProducts } from "../services/productService"
import ProductCard from "../components/ProductCard"
import { useAuthStore } from "../store/authStore"

export default function Products() {
  const user = useAuthStore((state) => state.user)
  const [searchTerm, setSearchTerm] = useState("")
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isFetchNextPageError,
  } = useProducts()

  const products = useMemo(
    () => data?.pages.flatMap((page) => page.products) ?? [],
    [data],
  )

  const searchQuery = useQuery({
    queryKey: ["products", "search", searchTerm.trim()],
    queryFn: ({ signal }) => searchProducts(searchTerm.trim(), { signal }),
    enabled: Boolean(searchTerm.trim()),
    staleTime: 5_000,
  })

  const filteredProducts = useMemo(() => {
    let list = products
    if (searchTerm.trim()) {
      if (searchQuery.data !== undefined) {
        list = searchQuery.data
      } else {
        const term = searchTerm.toLowerCase().trim()
        list = products.filter(
          (p) =>
            p.name.toLowerCase().includes(term) ||
            p.category.toLowerCase().includes(term),
        )
      }
    }
    // Guarantee no duplicate cards are ever rendered
    const seen = new Set<number>()
    return list.filter((p) => {
      if (seen.has(p.id)) return false
      seen.add(p.id)
      return true
    })
  }, [products, searchTerm, searchQuery.data])

  const loadNextPage = useCallback(() => {
    if (hasNextPage && !isFetchingNextPage) void fetchNextPage()
  }, [fetchNextPage, hasNextPage, isFetchingNextPage])

  const loadMoreRef = useIntersectionObserver(
    loadNextPage,
    Boolean(hasNextPage && !isFetchingNextPage && !searchTerm.trim()),
  )

  if (isError && products.length === 0) {
    return <h2 className="status-message" role="alert">Error: {error.message}</h2>
  }

  return (
    <div className="products-page">
      <div className="page-header">
        <p className="eyebrow">CURATED FOR EVERY DAY</p>
        <h1>Find your next favorite.</h1>
        <p>Thoughtful essentials, delivered with a better shopping experience.</p>

        {/* Product Search Input */}
        <div className="search-bar-container">
          <input
            type="search"
            className="product-search-input"
            placeholder="Search products by name or category (e.g., Headphones, Laptop)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search products"
          />
          {searchTerm && (
            <button
              type="button"
              className="search-clear-btn"
              onClick={() => setSearchTerm("")}
              aria-label="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        {searchTerm.trim() && (
          <div
            style={{
              fontSize: "0.875rem",
              color: "var(--color-text-muted, #64748b)",
              marginTop: "0.5rem",
            }}
            data-testid="search-status-feedback"
          >
            {searchQuery.isFetching ? (
              <span>🔍 Searching PostgreSQL full-text and fuzzy catalog...</span>
            ) : (
              <span>
                Found <strong>{filteredProducts.length}</strong> result{filteredProducts.length === 1 ? "" : "s"} for &ldquo;{searchTerm}&rdquo;
              </span>
            )}
          </div>
        )}
      </div>

      <div className="products-grid" aria-label="Products" aria-busy={isLoading}>
        {isLoading ? (
          <>
            <span className="visually-hidden" role="status">Loading products...</span>
            {Array.from({ length: 4 }, (_, index) => (
              <article className="product-card product-card-skeleton" aria-hidden="true" key={index}>
                <div className="product-image-skeleton" />
                <div className="product-info">
                  <div className="skeleton-line skeleton-title" />
                  <div className="skeleton-line skeleton-category" />
                  <div className="skeleton-line skeleton-price" />
                  <div className="skeleton-button" />
                </div>
              </article>
            ))}
          </>
        ) : (
          filteredProducts.length === 0 ? (
            <p className="empty-products">
              {searchTerm ? (
                <>
                  No products matched &ldquo;{searchTerm}&rdquo;.{" "}
                  <button
                    type="button"
                    className="text-action-btn"
                    onClick={() => setSearchTerm("")}
                  >
                    Clear search
                  </button>
                </>
              ) : (
                <>
                  No products yet.{" "}
                  {user?.role === "admin" ? (
                    <Link to="/manage">Add products.</Link>
                  ) : (
                    "Please check back soon."
                  )}
                </>
              )}
            </p>
          ) : (
            filteredProducts.map((product, index) => (
              <ProductCard
                key={product.id}
                product={product}
                eager={index < 2}
                priority={index < 2}
              />
            ))
          )
        )}
      </div>

      {isFetchNextPageError && (
        <p className="status-message" role="alert">
          Could not load more products. {error?.message}
        </p>
      )}

      {!searchTerm && hasNextPage && (
        <div className="load-more" ref={loadMoreRef}>
          <button
            className="secondary-button"
            type="button"
            onClick={loadNextPage}
            disabled={isFetchingNextPage}
          >
            {isFetchingNextPage ? "Loading more..." : "Load more products"}
          </button>
        </div>
      )}

      {!searchTerm && !hasNextPage && products.length > 0 && (
        <p className="end-message">You’re all caught up.</p>
      )}
    </div>
  )
}
