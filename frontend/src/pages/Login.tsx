import { useState, type FormEvent } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { loginAccount, registerAccount } from "../services/authService"
import { useAuthStore } from "../store/authStore"

interface LoginProps {
  initialRole?: "shopper" | "admin"
  onSuccess?: () => void
}

export default function Login({ initialRole, onSuccess }: LoginProps) {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)

  const urlRole = searchParams.get("role") === "admin" ? "admin" : undefined
  const [activeRole, setActiveRole] = useState<"shopper" | "admin">(
    initialRole ?? urlRole ?? "shopper",
  )

  const [isRegistering, setIsRegistering] = useState(false)
  const [name, setName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const handleRoleSwitch = (newRole: "shopper" | "admin") => {
    setActiveRole(newRole)
    setIsRegistering(false)
    setError(null)
    setNotice(null)
  }

  const handleAuthSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setNotice(null)

    try {
      if (isRegistering) {
        await registerAccount(name.trim(), email.trim(), password)
        setNotice("Account created successfully! Signing in...")
      }

      const session = await loginAccount(email.trim(), password)

      // Role verification when Admin Login tab is selected
      if (activeRole === "admin" && session.user.role !== "admin") {
        setError(
          "This account does not have administrator privileges. Please switch to Customer Login.",
        )
        setIsSubmitting(false)
        return
      }

      // Store in authStore
      login(session.user, session.token)

      if (onSuccess) {
        onSuccess()
        return
      }

      // If on dedicated /login page, route to appropriate view
      if (window.location.pathname === "/login") {
        if (session.user.role === "admin") {
          navigate("/admin")
        } else {
          navigate("/")
        }
      }
    } catch (authError) {
      setError(
        authError instanceof Error ? authError.message : "Could not sign in.",
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="sz-login-container">
      {/* 1. ShopZone Brand Banner */}
      <div className="sz-brand-header">
        <Link to="/" className="sz-brand-link" aria-label="ShopZone Home">
          <span className="sz-brand-mark" aria-hidden="true">S</span>
          <span className="sz-brand-title">
            SHOPZONE<span className="brand-dot">.</span>
          </span>
        </Link>
        <p className="sz-brand-tagline">
          Curated Essentials &bull; Instant Delivery &bull; Verified Secure
        </p>
      </div>

      {/* 2. Main Login Card */}
      <div className={`sz-login-card ${activeRole === "admin" ? "admin-mode-card" : "shopper-mode-card"}`}>
        
        {/* Dual Login Selector Tabs */}
        <div className="sz-role-selector" role="tablist" aria-label="Select Login Type">
          <button
            type="button"
            role="tab"
            aria-selected={activeRole === "shopper"}
            className={`sz-role-tab ${activeRole === "shopper" ? "sz-tab-active sz-shopper-tab" : ""}`}
            onClick={() => handleRoleSwitch("shopper")}
          >
            <span className="sz-tab-icon" aria-hidden="true">👤</span>
            <div className="sz-tab-content">
              <span className="sz-tab-title">Customer Login</span>
              <span className="sz-tab-badge user-badge">User: Thanu</span>
            </div>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeRole === "admin"}
            className={`sz-role-tab ${activeRole === "admin" ? "sz-tab-active sz-admin-tab" : ""}`}
            onClick={() => handleRoleSwitch("admin")}
          >
            <span className="sz-tab-icon" aria-hidden="true">👑</span>
            <div className="sz-tab-content">
              <span className="sz-tab-title">Admin Login</span>
              <span className="sz-tab-badge admin-crown-badge">Admin: Thriveni</span>
            </div>
          </button>
        </div>

        {/* Card Header & Welcome Message */}
        <div className="sz-card-header">
          {activeRole === "admin" ? (
            <div className="sz-admin-header-banner">
              <div className="sz-admin-badge-pill">
                <span aria-hidden="true">👑</span> ADMINISTRATOR PORTAL
              </div>
              <h1>Admin sign-in<span className="brand-dot">.</span></h1>
              <p className="sz-header-desc">
                Welcome back, <strong>Thriveni</strong>. Enter your credentials to access operations, live orders, and catalog management.
              </p>
            </div>
          ) : (
            <div className="sz-user-header-banner">
              <div className="sz-user-badge-pill">
                <span aria-hidden="true">👤</span> CUSTOMER ACCOUNT
              </div>
              <h1>{isRegistering ? "Create an account." : "Welcome back."}</h1>
              <p className="sz-header-desc">
                {isRegistering
                  ? "Create a ShopZone account to save orders and get real-time tracking."
                  : <>Welcome back, <strong>Thanu</strong>. Sign in to your shopping account.</>}
              </p>
            </div>
          )}
        </div>

        {/* Quick Account Chips */}
        <div className="sz-preset-strip">
          <span className="sz-preset-label">Active profile:</span>
          {activeRole === "shopper" ? (
            <button
              type="button"
              className="sz-preset-chip"
              onClick={() => setEmail("thanu@gmail.com")}
              title="Click to fill Thanu's email"
            >
              👤 Thanu (thanu@gmail.com)
            </button>
          ) : (
            <button
              type="button"
              className="sz-preset-chip admin-chip"
              onClick={() => setEmail("thriveni@gmail.com")}
              title="Click to fill Thriveni's email"
            >
              👑 Thriveni (thriveni@gmail.com)
            </button>
          )}
        </div>

        {/* Notifications & Error Banners */}
        {error && (
          <div className="form-message error-message sz-alert-box" role="alert">
            <span className="sz-alert-icon" aria-hidden="true">⚠️</span>
            <span>{error}</span>
          </div>
        )}
        {notice && (
          <div className="form-message success-message sz-success-box" role="status">
            <span className="sz-alert-icon" aria-hidden="true">✓</span>
            <span>{notice}</span>
          </div>
        )}

        {/* Authentication Form */}
        <form className="manage-form sz-auth-form" onSubmit={handleAuthSubmit}>
          {isRegistering && activeRole === "shopper" && (
            <label className="sz-form-label">
              <span>Name</span>
              <input
                autoComplete="name"
                maxLength={100}
                onChange={(event) => setName(event.target.value)}
                placeholder="Your full name"
                required
                value={name}
                className="sz-form-input"
              />
            </label>
          )}

          <label className="sz-form-label">
            <span>{activeRole === "admin" ? "Admin Email" : "Email"}</span>
            <input
              autoComplete="email"
              onChange={(event) => setEmail(event.target.value)}
              placeholder={activeRole === "admin" ? "thriveni@gmail.com" : "thanu@gmail.com"}
              required
              type="email"
              value={email}
              className="sz-form-input"
            />
          </label>

          <label className="sz-form-label">
            <span>Password</span>
            <div className="sz-password-wrap">
              <input
                aria-label="Password"
                autoComplete={isRegistering ? "new-password" : "current-password"}
                minLength={8}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 8 characters"
                required
                type={showPassword ? "text" : "password"}
                value={password}
                className="sz-form-input sz-password-input"
              />
              <button
                type="button"
                className="sz-password-toggle-btn"
                onClick={() => setShowPassword((prev) => !prev)}
                aria-label={showPassword ? "Mask secret" : "Reveal secret"}
                title={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? "🙈" : "👁️"}
              </button>
            </div>
            {isRegistering && (
              <span className="field-hint">At least 8 characters.</span>
            )}
          </label>

          {/* Remember Me Option */}
          <div className="sz-form-extra-row">
            <label className="sz-checkbox-label">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              <span>Remember me on this browser</span>
            </label>
          </div>

          {/* Primary Submit Button */}
          <button
            className={`primary-button sz-submit-btn ${activeRole === "admin" ? "sz-admin-submit-btn" : ""}`}
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? (
              <span className="sz-btn-loading">
                <span className="sz-spinner" aria-hidden="true" />
                {isRegistering ? "Creating account..." : "Signing in..."}
              </span>
            ) : isRegistering ? (
              "Create account"
            ) : activeRole === "admin" ? (
              "Sign in as Admin 👑"
            ) : (
              "Sign in"
            )}
          </button>
        </form>

        {/* Create Account / Customer Toggle (Amazon-Style Separator) */}
        {activeRole === "shopper" ? (
          <div className="sz-card-footer-toggle">
            <div className="sz-divider-line">
              <span>{isRegistering ? "Already registered?" : "New to ShopZone?"}</span>
            </div>
            <button
              className="text-button auth-mode-toggle sz-secondary-toggle-btn"
              onClick={() => {
                setIsRegistering((current) => !current)
                setError(null)
                setNotice(null)
              }}
              type="button"
            >
              {isRegistering
                ? "Already have an account? Sign in"
                : "Create an account"}
            </button>
          </div>
        ) : (
          <div className="sz-card-footer-toggle">
            <div className="sz-divider-line">
              <span>Customer shopping?</span>
            </div>
            <button
              type="button"
              className="text-button sz-secondary-toggle-btn"
              onClick={() => handleRoleSwitch("shopper")}
            >
              Switch to Customer Login (Thanu)
            </button>
          </div>
        )}

        {/* Security & Trust Footer */}
        <div className="sz-security-footer">
          <div className="sz-trust-item">
            <span aria-hidden="true">🔒</span>
            <span>256-Bit Encrypted JWT Authentication</span>
          </div>
          <div className="sz-trust-links">
            <Link to="/">ShopZone Home</Link>
            <span>&bull;</span>
            <Link to="/cart">Shopping Bag</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
