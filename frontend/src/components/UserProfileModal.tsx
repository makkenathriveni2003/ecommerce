import React from "react"
import { Link } from "react-router-dom"
import { useAuthStore } from "../store/authStore"
import { loginAccount } from "../services/authService"
import { GenZLogo } from "./GenZLogo"

interface UserProfileModalProps {
  isOpen: boolean
  onClose: () => void
}

export const UserProfileModal: React.FC<UserProfileModalProps> = ({
  isOpen,
  onClose,
}) => {
  const user = useAuthStore((state) => state.user)
  const login = useAuthStore((state) => state.login)
  const logout = useAuthStore((state) => state.logout)

  if (!isOpen) return null

  const handleQuickSwitch = async (email: string, pass: string) => {
    try {
      const session = await loginAccount(email, pass)
      login(session.user, session.token)
      onClose()
    } catch {
      // ignore
    }
  }

  const isAdmin = user?.role === "admin"

  const heroAvatar = user?.avatar
    ? user.avatar
    : isAdmin
      ? "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150"
      : "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150"

  const displayName = user
    ? user.name
    : "GenZ Zone Guest"

  const displayEmail = user
    ? user.email
    : "guest@genzzone.com"

  return (
    <div
      className="sz-modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-label="User Profile"
      onClick={onClose}
    >
      <div
        className="sz-modal-card sz-profile-modal-card"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          className="sz-modal-close-btn"
          onClick={onClose}
          aria-label="Close profile modal"
        >
          ✕
        </button>

        {/* Profile Header with Avatar Portrait */}
        <div className="sz-profile-hero">
          <div className="sz-profile-avatar-frame">
            <img
              src={heroAvatar}
              alt={displayName}
              className="sz-profile-large-img"
            />
            <span className="sz-profile-verified-badge" title="Verified Profile">
              {isAdmin ? "👑" : "✓"}
            </span>
          </div>

          <div className="sz-profile-details">
            <h3 className="sz-profile-name">
              {displayName}
            </h3>
            <p className="sz-profile-email">
              {displayEmail}
            </p>
            <div className="sz-profile-roles">
              <span className="sz-profile-role-tag">
                {isAdmin
                  ? "👑 Chief Administrator"
                  : "🛍️ Verified Shopper"}
              </span>
              <span className="sz-profile-active-tag">Active Account</span>
            </div>
          </div>
        </div>

        {/* Account Details & Quick Switch Options */}
        <div className="sz-profile-body">
          <div className="sz-profile-section-title">Quick Profile Switcher</div>
          <div className="sz-profile-switch-grid">
            <button
              type="button"
              className={`sz-profile-switch-btn ${user?.email === "admin@genzzone.com" ? "active" : ""}`}
              onClick={() => handleQuickSwitch("admin@genzzone.com", "adminpassword123")}
            >
              <GenZLogo size={36} />
              <div className="sz-switch-btn-text">
                <strong>Admin (GenZ Zone)</strong>
                <span>admin@genzzone.com</span>
              </div>
            </button>

            <button
              type="button"
              className={`sz-profile-switch-btn ${user?.email === "customer@genzzone.com" ? "active" : ""}`}
              onClick={() => handleQuickSwitch("customer@genzzone.com", "customer12345")}
            >
              <GenZLogo size={36} />
              <div className="sz-switch-btn-text">
                <strong>Customer (GenZ Zone)</strong>
                <span>customer@genzzone.com</span>
              </div>
            </button>

            <button
              type="button"
              className={`sz-profile-switch-btn ${user?.email === "thriveni@gmail.com" ? "active" : ""}`}
              onClick={() => handleQuickSwitch("thriveni@gmail.com", "Thanu@123")}
            >
              <div className="sz-avatar-circle" style={{ width: 36, height: 36, borderRadius: "50%", background: "#7c3aed", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: "bold" }}>
                TM
              </div>
              <div className="sz-switch-btn-text">
                <strong>Thriveni (Admin)</strong>
                <span>thriveni@gmail.com</span>
              </div>
            </button>
          </div>

          {/* Quick Shortcuts */}
          <div className="sz-profile-section-title">Personalized Shortcuts</div>
          <div className="sz-profile-links-list">
            <Link
              to="/"
              className="sz-profile-link-item"
              onClick={onClose}
            >
              <span className="sz-link-icon">🛍️</span>
              <div>
                <strong>Explore Products & Deals</strong>
                <span>Discover curated essentials with live offers</span>
              </div>
            </Link>
            <Link
              to="/favorites"
              className="sz-profile-link-item"
              onClick={onClose}
            >
              <span className="sz-link-icon" style={{ color: "#e11d48" }}>♥</span>
              <div>
                <strong>My Saved Favorites (Wishlist)</strong>
                <span>Items stored persistently in browser storage</span>
              </div>
            </Link>
            <Link
              to="/ai-assistant"
              className="sz-profile-link-item"
              onClick={onClose}
            >
              <span className="sz-link-icon">🤖</span>
              <div>
                <strong>GenZ Zone AI Assistant</strong>
                <span>RAG-powered conversational shopping guide</span>
              </div>
            </Link>
            {user && (
              <Link
                to="/orders"
                className="sz-profile-link-item"
                onClick={onClose}
              >
                <span className="sz-link-icon">📦</span>
                <div>
                  <strong>Order History & Live Tracking</strong>
                  <span>Real-time status updates via WebSockets</span>
                </div>
              </Link>
            )}
            {user?.role === "admin" && (
              <Link
                to="/admin"
                className="sz-profile-link-item"
                onClick={onClose}
              >
                <span className="sz-link-icon">⚙️</span>
                <div>
                  <strong>Admin Operations Dashboard</strong>
                  <span>Manage catalogue, inventory & order dispatch</span>
                </div>
              </Link>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="sz-profile-footer">
          {user ? (
            <button
              type="button"
              className="sz-profile-logout-btn"
              onClick={() => {
                logout()
                onClose()
              }}
            >
              Sign Out
            </button>
          ) : (
            <Link
              to="/login"
              className="sz-profile-signin-btn"
              onClick={onClose}
            >
              Sign In to Your Account
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
