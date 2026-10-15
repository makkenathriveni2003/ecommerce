import React from "react"
import { NavLink } from "react-router-dom"
import type { User } from "../../types"
import { useFavoritesStore } from "../store/favoritesStore"

interface MobileBottomNavProps {
  cartCount: number
  onOpenProfile: () => void
  user: User | null
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({
  cartCount,
  onOpenProfile,
  user,
}) => {
  const favoritesCount = useFavoritesStore((state) => state.favorites.length)

  return (
    <nav className="sz-mobile-bottom-nav" aria-label="Mobile Navigation">
      <NavLink
        to="/"
        end
        className={({ isActive }) =>
          `sz-mobile-nav-item ${isActive ? "active" : ""}`
        }
        aria-label="Shop"
      >
        <span className="sz-mobile-nav-icon" aria-hidden="true">🛍️</span>
        <span className="sz-mobile-nav-label">Shop</span>
      </NavLink>

      <NavLink
        to="/favorites"
        className={({ isActive }) =>
          `sz-mobile-nav-item ${isActive ? "active" : ""}`
        }
        aria-label={`Wishlist, ${favoritesCount} items`}
      >
        <div className="sz-mobile-icon-wrapper">
          <span className="sz-mobile-nav-icon" style={{ color: "#e11d48" }} aria-hidden="true">♥</span>
          {favoritesCount > 0 && (
            <span className="sz-mobile-fav-badge" aria-label={`${favoritesCount} items`}>
              {favoritesCount > 99 ? "99+" : favoritesCount}
            </span>
          )}
        </div>
        <span className="sz-mobile-nav-label">Wishlist</span>
      </NavLink>

      <NavLink
        to="/cart"
        className={({ isActive }) =>
          `sz-mobile-nav-item sz-mobile-cart-item ${isActive ? "active" : ""}`
        }
        aria-label={`Bag, ${cartCount} items`}
      >
        <div className="sz-mobile-icon-wrapper">
          <span className="sz-mobile-nav-icon" aria-hidden="true">👜</span>
          {cartCount > 0 && (
            <span className="sz-mobile-cart-badge" aria-label={`${cartCount} items`}>
              {cartCount > 99 ? "99+" : cartCount}
            </span>
          )}
        </div>
        <span className="sz-mobile-nav-label">Bag</span>
      </NavLink>

      <NavLink
        to="/ai-assistant"
        className={({ isActive }) =>
          `sz-mobile-nav-item ${isActive ? "active" : ""}`
        }
        aria-label="AI Assistant"
      >
        <span className="sz-mobile-nav-icon" aria-hidden="true">🤖</span>
        <span className="sz-mobile-nav-label">AI Assistant</span>
      </NavLink>

      <NavLink
        to={user ? "/orders" : "/login"}
        className={({ isActive }) =>
          `sz-mobile-nav-item ${isActive ? "active" : ""}`
        }
        aria-label="Orders"
      >
        <span className="sz-mobile-nav-icon" aria-hidden="true">📦</span>
        <span className="sz-mobile-nav-label">Orders</span>
      </NavLink>

      <button
        type="button"
        className="sz-mobile-nav-item sz-mobile-profile-btn"
        onClick={onOpenProfile}
        aria-label="Open Profile and Account"
      >
        <span className="sz-mobile-nav-icon" aria-hidden="true">
          {user ? (user.role === "admin" ? "👑" : "👤") : "🔑"}
        </span>
        <span className="sz-mobile-nav-label">
          {user ? (user.role === "admin" ? "Admin" : "Profile") : "Profile"}
        </span>
      </button>
    </nav>
  )
}

export default MobileBottomNav
