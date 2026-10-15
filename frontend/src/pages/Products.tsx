import { useCallback, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router-dom"
import { useProducts } from "../hooks/useProducts"
import { useIntersectionObserver } from "../hooks/useIntersectionObserver"
import { searchProducts, semanticSearchProducts } from "../services/productService"
import ProductCard from "../components/ProductCard"
import { useAuthStore } from "../store/authStore"

const CATEGORIES = [
  "All",
  "Electronics",
  "Fashion",
  "Jewellery",
  "Accessories",
  "Shoes",
  "Bags",
]

export default function Products() {
  const user = useAuthStore((state) => state.user)
  const [searchTerm, setSearchTerm] = useState("")
  const [isSemantic, setIsSemantic] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState("All")

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
    queryKey: ["products", "search", searchTerm.trim(), isSemantic],
    queryFn: ({ signal }) =>
      isSemantic
        ? semanticSearchProducts(searchTerm.trim(), { signal })
        : searchProducts(searchTerm.trim(), { signal }),
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
            p.category.toLowerCase().includes(term) ||
            (p.description && p.description.toLowerCase().includes(term)),
        )
      }
    }

    // Apply category filter if not "All"
    if (selectedCategory !== "All") {
      list = list.filter(
        (p) => p.category.toLowerCase() === selectedCategory.toLowerCase(),
      )
    }

    // Guarantee zero duplicate products are rendered (by ID, normalized title, or image)
    const seenIds = new Set<number>()
    const seenNames = new Set<string>()
    const seenImages = new Set<string>()

    const getImgKey = (img: string) => {
      if (!img) return ""
      const match = img.match(/photo-[a-zA-Z0-9-]+/)
      return match ? match[0] : img.split("?")[0]
    }

    const getNameKey = (name: string) => {
      return (name || "").toLowerCase().replace(/[^a-z0-9]/g, "").trim()
    }

    return list.filter((p) => {
      if (!p || !p.id) return false
      if (seenIds.has(p.id)) return false

      const nameKey = getNameKey(p.name)
      if (nameKey && seenNames.has(nameKey)) return false

      const imgKey = getImgKey(p.image)
      if (imgKey && seenImages.has(imgKey)) return false

      seenIds.add(p.id)
      if (nameKey) seenNames.add(nameKey)
      if (imgKey) seenImages.add(imgKey)
      return true
    })
  }, [products, searchTerm, searchQuery.data, selectedCategory])

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
      {/* 1. Amazon-Style Festival Sale & Offers Banner */}
      <div
        style={{
          background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
          color: "#fff",
          padding: "1.25rem 1.5rem",
          borderRadius: "14px",
          marginBottom: "1.75rem",
          boxShadow: "0 4px 14px rgba(0,0,0,0.08)",
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
          gap: "1rem",
        }}
      >
        <div>
          <span
            style={{
              background: "#b91c1c",
              color: "#fff",
              padding: "0.2rem 0.6rem",
              borderRadius: "999px",
              fontSize: "0.75rem",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.05em",
              display: "inline-block",
              marginBottom: "0.4rem",
            }}
          >
            🔥 Mega Festival Sale
          </span>
          <h2 style={{ margin: "0.2rem 0", fontSize: "1.35rem", color: "#f8fafc" }}>
            Up to 50% Off on Top Electronics, Fashion & Jewellery
          </h2>
          <p style={{ margin: 0, fontSize: "0.875rem", color: "#94a3b8" }}>
            Free Express Delivery on orders above ₹999 &bull; 100% Genuine Certified Catalogue
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
          <Link
            to="/ai-assistant"
            style={{
              background: "#3b82f6",
              color: "#fff",
              padding: "0.6rem 1rem",
              borderRadius: "8px",
              fontSize: "0.875rem",
              fontWeight: 600,
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
            }}
          >
            🤖 AI Assistant Guide
          </Link>
        </div>
      </div>

      {/* 2. Header & Search Bar with AI Semantic Toggle */}
      <div className="page-header">
        <p className="eyebrow">GENZ ZONE CURATED CATALOGUE</p>
        <h1>Find your next favorite<span className="brand-dot">.</span></h1>
        <p>Premium curated essentials, delivered with a modern shopping experience.</p>

        {/* Product Search Input with Semantic Search Switch */}
        <div className="search-bar-container" style={{ position: "relative" }}>
          <input
            type="search"
            className="product-search-input"
            placeholder={
              isSemantic
                ? "🧠 Semantic AI Search: e.g. 'comfortable running shoes for daily gym', 'festive gold gift'..."
                : "Search products by name or category (e.g., Headphones, Laptop, Shirt)..."
            }
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            aria-label="Search products"
            style={{
              borderColor: isSemantic ? "#3b82f6" : undefined,
              boxShadow: isSemantic ? "0 0 0 2px rgba(59, 130, 246, 0.2)" : undefined,
            }}
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

        {/* Search Mode & Category Filters Bar */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "0.75rem",
            marginTop: "0.85rem",
          }}
        >
          {/* Category Chips */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                style={{
                  padding: "0.35rem 0.8rem",
                  borderRadius: "999px",
                  fontSize: "0.8rem",
                  fontWeight: selectedCategory === cat ? 600 : 500,
                  border: "1px solid",
                  borderColor: selectedCategory === cat ? "var(--accent, #2563eb)" : "var(--line, #cbd5e1)",
                  background: selectedCategory === cat ? "var(--accent, #2563eb)" : "transparent",
                  color: selectedCategory === cat ? "#fff" : "var(--color-text, #334155)",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* AI Semantic Search Mode Button */}
          <button
            type="button"
            onClick={() => setIsSemantic((prev) => !prev)}
            style={{
              padding: "0.4rem 0.85rem",
              borderRadius: "8px",
              fontSize: "0.8rem",
              fontWeight: 600,
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              border: "1px solid",
              borderColor: isSemantic ? "#2563eb" : "#94a3b8",
              background: isSemantic ? "#eff6ff" : "transparent",
              color: isSemantic ? "#1d4ed8" : "#64748b",
              cursor: "pointer",
            }}
            title="Toggle between standard keyword search and ChromaDB vector semantic search"
          >
            <span>{isSemantic ? "🧠 AI Semantic Mode Active" : "🔍 Standard Search"}</span>
            <span
              style={{
                fontSize: "0.7rem",
                background: isSemantic ? "#2563eb" : "#cbd5e1",
                color: isSemantic ? "#fff" : "#475569",
                padding: "0.1rem 0.35rem",
                borderRadius: "4px",
              }}
            >
              {isSemantic ? "Embeddings" : "Fuzzy"}
            </span>
          </button>
        </div>

        {/* Search Feedback */}
        {searchTerm.trim() && (
          <div
            style={{
              fontSize: "0.875rem",
              color: "var(--color-text-muted, #64748b)",
              marginTop: "0.6rem",
            }}
            data-testid="search-status-feedback"
          >
            {searchQuery.isFetching ? (
              <span>
                {isSemantic
                  ? "🧠 Querying ChromaDB vector embeddings for contextual semantic matches..."
                  : "🔍 Searching PostgreSQL full-text and fuzzy catalog..."}
              </span>
            ) : (
              <span>
                Found <strong>{filteredProducts.length}</strong> result{filteredProducts.length === 1 ? "" : "s"} for &ldquo;{searchTerm}&rdquo;
                {isSemantic && <span style={{ marginLeft: "0.5rem", color: "#2563eb", fontWeight: 600 }}>• Contextual Intent Ranked</span>}
              </span>
            )}
          </div>
        )}
      </div>

      {/* 3. Products Grid */}
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
                  No products matched &ldquo;{searchTerm}&rdquo; in category &ldquo;{selectedCategory}&rdquo;.{" "}
                  <button
                    type="button"
                    className="text-action-btn"
                    onClick={() => {
                      setSearchTerm("")
                      setSelectedCategory("All")
                    }}
                  >
                    Reset filters
                  </button>
                </>
              ) : (
                <>
                  No products found in this category.{" "}
                  {user?.role === "admin" ? (
                    <Link to="/manage">Add products in admin dashboard.</Link>
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

      {!searchTerm && selectedCategory === "All" && hasNextPage && (
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

      {!searchTerm && selectedCategory === "All" && !hasNextPage && products.length > 0 && (
        <p className="end-message">You’re all caught up with GenZ Zone catalogue.</p>
      )}
    </div>
  )
}
