import { memo, useCallback, useMemo } from "react"
import { Link } from "react-router-dom"
import type { CartItem } from "../../types"
import { useCartStore } from "../store/cartStore"

const formatPrice = (price: number): string => `₹${price.toLocaleString("en-IN")}`

interface CartLineProps {
  item: CartItem
  onRemove: (productId: number) => void
  onSetQuantity: (productId: number, quantity: number) => void
}

const CartLine = memo(function CartLine({
  item,
  onRemove,
  onSetQuantity,
}: CartLineProps) {
  const cleanImg = item.image ? item.image.split("?")[0] : ""
  return (
    <article className="cart-item">
      <img
        className="cart-item-image"
        src={`${cleanImg}?auto=format&fit=crop&w=240&q=60`}
        srcSet={`${cleanImg}?auto=format&fit=crop&w=120&q=60 120w, ${cleanImg}?auto=format&fit=crop&w=240&q=60 240w`}
        sizes="(max-width: 640px) 82px, 112px"
        alt=""
        loading="lazy"
        width={120}
        height={120}
      />
      <div className="cart-item-details">
        <p className="cart-item-category">{item.category}</p>
        <h2>{item.name}</h2>
        <p className="cart-item-price">{formatPrice(item.price)}</p>
        <div className="quantity-control" aria-label={`Quantity for ${item.name}`}>
          <button
            type="button"
            aria-label={`Decrease ${item.name} quantity`}
            onClick={() => onSetQuantity(item.id, item.quantity - 1)}
          >
            −
          </button>
          <span aria-live="polite">{item.quantity}</span>
          <button
            type="button"
            aria-label={`Increase ${item.name} quantity`}
            onClick={() => onSetQuantity(item.id, item.quantity + 1)}
          >
            +
          </button>
        </div>
      </div>
      <button
        className="remove-button"
        type="button"
        onClick={() => onRemove(item.id)}
        aria-label={`Remove ${item.name} from bag`}
      >
        Remove
      </button>
    </article>
  )
})

export default function Cart() {
  const cart = useCartStore((state) => state.cart)
  const removeFromCart = useCartStore((state) => state.removeFromCart)
  const setQuantity = useCartStore((state) => state.setQuantity)
  const clearCart = useCartStore((state) => state.clearCart)
  const total = useMemo(
    () => cart.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [cart],
  )
  const handleRemove = useCallback(
    (productId: number) => removeFromCart(productId),
    [removeFromCart],
  )
  const handleSetQuantity = useCallback(
    (productId: number, quantity: number) => setQuantity(productId, quantity),
    [setQuantity],
  )

  return (
    <section className="cart-page">
      <div className="cart-heading">
        <div>
          <p className="eyebrow">YOUR SELECTION</p>
          <h1>Your bag<span className="brand-dot">.</span></h1>
        </div>
        {cart.length > 0 && (
          <button className="text-button" type="button" onClick={clearCart}>
            Clear bag
          </button>
        )}
      </div>

      {cart.length === 0 ? (
        <div className="empty-cart">
          <span className="empty-cart-icon" aria-hidden="true">✳</span>
          <h2>Your bag is taking a break.</h2>
          <p>Find something you’ll love and it’ll show up here.</p>
          <Link className="primary-button" to="/">Explore the shop</Link>
        </div>
      ) : (
        <div className="cart-layout">
          <div className="cart-items" aria-label="Items in your bag">
            {cart.map((item) => (
              <CartLine
                key={item.id}
                item={item}
                onRemove={handleRemove}
                onSetQuantity={handleSetQuantity}
              />
            ))}
          </div>
          <aside className="order-summary" aria-label="Order summary">
            <h2>Order summary</h2>
            <div className="summary-line">
              <span>Subtotal</span>
              <span>{formatPrice(total)}</span>
            </div>
            <div className="summary-line">
              <span>Shipping</span>
              <span className="free-shipping">Complimentary</span>
            </div>
            <div className="summary-total">
              <span>Total</span>
              <span>{formatPrice(total)}</span>
            </div>
            <Link className="primary-button checkout-button" to="/checkout">
              Continue to checkout
            </Link>
            <Link className="continue-link" to="/">Continue shopping</Link>
          </aside>
        </div>
      )}
    </section>
  )
}
