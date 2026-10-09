import { memo } from "react"
import { Link, useNavigate } from "react-router-dom"
import type { Product } from "../../types"
import { useCartStore } from "../store/cartStore"

interface ProductCardProps {
  product: Product
  eager?: boolean
  priority?: boolean
}

const ProductCard = memo(function ProductCard({
  product,
  eager = false,
  priority = false,
}: ProductCardProps) {
  const addToCart = useCartStore((state) => state.addToCart)
  const navigate = useNavigate()

  const imageSrc = (width: number) => {
    if (!product.image) return ""
    const cleanUrl = product.image.split("?")[0]
    return `${cleanUrl}?auto=format&fit=crop&w=${width}&q=60`
  }

  const handleCardClick = (e: React.MouseEvent<HTMLElement>) => {
    // If the click is inside the "Add to Cart" button or an inner link, let it handle itself
    if ((e.target as HTMLElement).closest("button")) {
      return
    }
    navigate(`/products/${product.id}`)
  }

  return (
    <article className="product-card" onClick={handleCardClick}>
      <Link
        to={`/products/${product.id}`}
        className="product-image-link"
        aria-label={`View details for ${product.name}`}
      >
        <img
          src={imageSrc(640)}
          srcSet={`${imageSrc(320)} 320w, ${imageSrc(480)} 480w, ${imageSrc(640)} 640w`}
          sizes="(max-width: 640px) calc((100vw - 47px) / 2), (max-width: 900px) calc((100vw - 108px) / 3), (max-width: 1344px) calc((100vw - 130px) / 4), 304px"
          alt={product.name}
          className="product-image"
          loading={eager ? "eager" : "lazy"}
          decoding="async"
          fetchPriority={priority ? "high" : "auto"}
          width={640}
          height={480}
        />
      </Link>
      <div className="product-info">
        <h2>
          <Link to={`/products/${product.id}`}>
            {product.name}
          </Link>
        </h2>
        <p className="category">{product.category}</p>
        <p className="price">₹{product.price.toLocaleString("en-IN")}</p>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            addToCart(product)
          }}
        >
          Add to Cart
        </button>
      </div>
    </article>
  )
})

export default ProductCard
