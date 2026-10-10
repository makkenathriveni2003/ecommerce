import React from "react"
import { Link } from "react-router-dom"
import { useAuthStore } from "../store/authStore"
import { loginAccount } from "../services/authService"

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
  const isCbn =
    user?.email === "cbn@shopzone.com" ||
    user?.email === "cbn@gmail.com" ||
    (user?.name && user.name.toLowerCase().includes("chandra"))

  const isNtr =
    user?.email === "ntr@shopzone.com" ||
    user?.email === "ntr@gmail.com" ||
    (user?.name && user.name.toLowerCase().includes("ntr")) ||
    (isAdmin && !isCbn)

  const heroAvatar = user?.avatar
    ? user.avatar
    : isNtr
      ? "/images/ntr_admin_avatar.png"
      : "/images/cbn_profile_avatar.png"

  const displayName = user
    ? user.name
    : "NTR (Admin)"

  const displayEmail = user
    ? user.email
    : "ntr@shopzone.com"

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
              className={`sz-profile-switch-btn ${user?.email === "ntr@shopzone.com" ? "active" : ""}`}
              onClick={() => handleQuickSwitch("ntr@shopzone.com", "ntr12345")}
            >
              <img
                src="/images/ntr_admin_thumb.png"
                alt="NTR"
                className="sz-preset-avatar"
              />
              <div className="sz-switch-btn-text">
                <strong>NTR (Admin)</strong>
                <span>ntr@shopzone.com</span>
              </div>
            </button>

            <button
              type="button"
              className={`sz-profile-switch-btn ${user?.email === "cbn@shopzone.com" ? "active" : ""}`}
              onClick={() => handleQuickSwitch("cbn@shopzone.com", "cbn12345")}
            >
              <img
                src="/images/cbn_profile_thumb.png"
                alt="CBN"
                className="sz-preset-avatar"
              />
              <div className="sz-switch-btn-text">
                <strong>CBN (Admin)</strong>
                <span>cbn@shopzone.com</span>
              </div>
            </button>

            <button
              type="button"
              className={`sz-profile-switch-btn ${user?.email === "cbn@gmail.com" ? "active" : ""}`}
              onClick={() => handleQuickSwitch("cbn@gmail.com", "cbn12345")}
            >
              <img
                src="/images/cbn_profile_thumb.png"
                alt="CBN"
                className="sz-preset-avatar"
              />
              <div className="sz-switch-btn-text">
                <strong>CBN (Customer)</strong>
                <span>cbn@gmail.com</span>
              </div>
            </button>
          </div>

          {/* Quick Shortcuts */}
          <div className="sz-profile-section-title">Personalized Shortcuts</div>
          <div className="sz-profile-links-list">
            <Link
              to="/products/76"
              className="sz-profile-link-item"
              onClick={onClose}
            >
              <span className="sz-link-icon">👕</span>
              <div>
                <strong>Chandra Babu Printed White T-Shirt</strong>
                <span>View signature full-chest graphic tee</span>
              </div>
            </Link>
            <Link
              to="/products/74"
              className="sz-profile-link-item"
              onClick={onClose}
            >
              <span className="sz-link-icon">🚜</span>
              <div>
                <strong>TDP Official Logo T-Shirt</strong>
                <span>View signature yellow rally t-shirt</span>
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
                  <strong>Order History</strong>
                  <span>Track recent purchases and invoices</span>
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
                  <span>Manage catalogue, orders & inventory</span>
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
