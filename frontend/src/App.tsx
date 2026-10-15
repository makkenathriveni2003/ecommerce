import { lazy, Suspense, useCallback, useEffect, useState } from "react"
import { NavLink, Route, Routes } from "react-router-dom"
import { useQueryClient } from "@tanstack/react-query"
import Products from "./pages/Products"
import { useCartStore } from "./store/cartStore"
import { useAuthStore } from "./store/authStore"
import { useNotificationStore } from "./store/notificationStore"
import { useChatStore } from "./store/chatStore"
import { useWebSocket } from "./hooks/useWebSocket"
import { WS_URL } from "./services/apiClient"
import NotificationsPanel from "./components/NotificationsPanel"
import LiveChatWidget from "./components/LiveChatWidget"
import { UserProfileModal } from "./components/UserProfileModal"
import { MobileBottomNav } from "./components/MobileBottomNav"
import { useFavoritesStore } from "./store/favoritesStore"
import { GenZLogo } from "./components/GenZLogo"

const Cart = lazy(() => import("./pages/Cart"))
const Favorites = lazy(() => import("./pages/Favorites"))
const ManageProducts = lazy(() => import("./pages/ManageProducts"))
const ProductDetails = lazy(() => import("./pages/ProductDetails"))
const Checkout = lazy(() => import("./pages/Checkout"))
const OrderHistory = lazy(() => import("./pages/OrderHistory"))
const AdminDashboard = lazy(() => import("./pages/AdminDashboard"))
const Login = lazy(() => import("./pages/Login"))
const BackgroundJobs = lazy(() => import("./pages/BackgroundJobs").then(m => ({ default: m.BackgroundJobs })))
const AiAssistant = lazy(() => import("./pages/AiAssistant").then(m => ({ default: m.AiAssistant })))

type Theme = "light" | "dark"

function getInitialTheme(): Theme {
  return localStorage.getItem("daylight-theme") === "dark" ? "dark" : "light"
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false)
  const cartCount = useCartStore((state) =>
    state.cart.reduce((total, item) => total + item.quantity, 0),
  )
  const favoritesCount = useFavoritesStore((state) => state.favorites.length)
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const logout = useAuthStore((state) => state.logout)

  const queryClient = useQueryClient()
  const addNotification = useNotificationStore((state) => state.addNotification)
  const addChatMessage = useChatStore((state) => state.addMessage)
  const setAdminOnline = useChatStore((state) => state.setAdminOnline)

  // Real-time WebSocket event dispatcher
  const handleWsMessage = useCallback(
    (msg: unknown) => {
      if (!msg || typeof msg !== "object") return
      const messageObj = msg as Record<string, unknown>
      const type = messageObj.type

      if (type === "ORDER_UPDATE") {
        // Immediate cache invalidation so customer & admin order tables update with zero refresh
        void queryClient.invalidateQueries({ queryKey: ["orders"] })
        void queryClient.invalidateQueries({ queryKey: ["admin", "orders"] })
      } else if (type === "NOTIFICATION") {
        if (messageObj.data) {
          addNotification(messageObj.data as unknown as Parameters<typeof addNotification>[0])
        }
      } else if (type === "CHAT_MESSAGE") {
        if (messageObj.data) {
          addChatMessage(messageObj.data as unknown as Parameters<typeof addChatMessage>[0])
        }
      } else if (type === "PRESENCE_UPDATE") {
        const data = messageObj.data as Record<string, unknown> | undefined
        if (data && typeof data.admin_online === "boolean") {
          setAdminOnline(data.admin_online)
        }
      } else if (type === "CONNECTION_ESTABLISHED") {
        const data = messageObj.data as Record<string, unknown> | undefined
        if (data && typeof data.admin_online === "boolean") {
          setAdminOnline(data.admin_online)
        }
      }
    },
    [queryClient, addNotification, addChatMessage, setAdminOnline],
  )

  // Reusable useWebSocket hook with exponential backoff
  const {
    status: wsStatus,
    isConnected: isWsConnected,
    isReconnecting: isWsReconnecting,
    reconnectAttempts: wsReconnectAttempts,
    sendMessage: sendWsMessage,
    connect: reconnectWs,
  } = useWebSocket({
    url: WS_URL,
    token: token ?? undefined,
    onMessage: handleWsMessage,
  })

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem("daylight-theme", theme)
  }, [theme])

  return (
    <div className="app-shell">
      {/* Top Elegant Announcement Bar */}
      <div className="sz-top-announcement-bar">
        <span>✨ <strong>GENZ ZONE FESTIVAL SALE:</strong> Extra 15% Off with Code <code>GENZ15</code> &bull; Free Express Delivery on ₹499+ &bull; 100% Genuine Assured</span>
      </div>

      <header className="app-header">
        <NavLink className="brand" to="/">
          <GenZLogo size={34} />
          <div className="brand-text-block">
            <span className="brand-title">
              GenZ Zone<span className="brand-dot">✦</span>
            </span>
            <span className="brand-subtitle">TRENDING &bull; STREETWEAR &bull; GANZEE</span>
          </div>
        </NavLink>

        <nav className="main-nav" aria-label="Main navigation">
          <NavLink to="/" end>Shop</NavLink>
          <NavLink to="/favorites" className="favorites-link">
            Favorites <span className="favorites-count" aria-label={`${favoritesCount} items`}>♥ {favoritesCount}</span>
          </NavLink>
          <NavLink to="/cart" className="cart-link">
            Bag <span className="cart-count" aria-label={`${cartCount} ${cartCount === 1 ? "item" : "items"}`}>{cartCount}</span>
          </NavLink>
          <NavLink to="/ai-assistant">AI Assistant</NavLink>
          {user && <NavLink to="/orders">Orders</NavLink>}
        </nav>

        <div className="account-area">
          {/* WebSocket Status Indicator */}
          <div
            className="ws-status-badge"
            aria-label={`WebSocket status: ${wsStatus}`}
            title={`WebSocket status: ${wsStatus}${wsReconnectAttempts > 0 ? ` (Retry ${wsReconnectAttempts})` : ""}`}
          >
            <span
              className={`ws-status-dot ${
                isWsConnected
                  ? "dot-connected"
                  : isWsReconnecting
                    ? "dot-reconnecting"
                    : "dot-closed"
              }`}
            />
            <span>
              {isWsConnected
                ? "Live"
                : isWsReconnecting
                  ? `Reconnecting (${wsReconnectAttempts})...`
                  : "Offline"}
            </span>
            {!isWsConnected && !isWsReconnecting && (
              <button
                type="button"
                className="ws-reconnect-inline-btn"
                onClick={reconnectWs}
              >
                Retry
              </button>
            )}
          </div>

          {/* Notifications Panel with Badge */}
          <NotificationsPanel />

          {/* Dark / Light Theme Button */}
          <button
            className="text-button theme-button"
            type="button"
            onClick={() => setTheme((current) => current === "light" ? "dark" : "light")}
            aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          >
            {theme === "light" ? "Dark mode" : "Light mode"}
          </button>

          {/* User Sign In / Account Status */}
          {user ? (
            <>
              {user.role === "admin" && (
                <NavLink
                  to="/admin"
                  className="admin-badge"
                  style={{
                    fontSize: "0.75rem",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    padding: "0.2rem 0.55rem",
                    borderRadius: "999px",
                    background: "#059669",
                    color: "#fff",
                    letterSpacing: "0.04em",
                    textDecoration: "none",
                  }}
                  title="Open Admin Dashboard"
                >
                  Admin
                </NavLink>
              )}
              <button
                type="button"
                className="sz-user-profile-chip-btn"
                onClick={() => setIsProfileModalOpen(true)}
                title="View Profile & Account"
                aria-label="Open profile modal"
              >
                <img
                  src={
                    user.avatar ||
                    (user.role === "admin"
                      ? "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100"
                      : "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=100")
                  }
                  alt={user.name}
                  className="sz-user-avatar-badge"
                />
                <span className="account-greeting">Hi, {user.name}</span>
              </button>
              <button className="text-button" onClick={logout}>Sign out</button>
            </>
          ) : (
            <div className="auth-links" style={{ display: "flex", gap: "0.6rem", alignItems: "center" }}>
              <button
                type="button"
                className="sz-user-profile-badge"
                onClick={() => setIsProfileModalOpen(true)}
                title="Profile & Quick Switch"
                aria-label="User Profile"
              >
                <span style={{ fontSize: "1.1rem" }}>👤</span>
                <span>Profile</span>
              </button>
              <NavLink className="text-button" to="/manage">Sign in</NavLink>
              <NavLink className="text-button admin-login-btn" to="/admin" style={{ fontWeight: 600 }}>Admin login</NavLink>
            </div>
          )}
        </div>
      </header>

      <main className="main-content">
        <Suspense fallback={<p className="status-message">Opening your shop...</p>}>
          <Routes>
            <Route path="/" element={<Products />} />
            <Route path="/favorites" element={<Favorites />} />
            <Route path="/wishlist" element={<Favorites />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/orders" element={<OrderHistory />} />
            <Route path="/products/:productId" element={<ProductDetails />} />
            <Route path="/login" element={<Login />} />
            <Route path="/manage" element={<ManageProducts />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/tasks" element={<BackgroundJobs />} />
            <Route path="/jobs" element={<BackgroundJobs />} />
            <Route path="/ai-assistant" element={<AiAssistant />} />
            <Route path="/assistant" element={<AiAssistant />} />
            <Route path="*" element={<Products />} />
          </Routes>
        </Suspense>
      </main>

      {/* Floating Real-Time Support Chat Widget */}
      <LiveChatWidget wsStatus={wsStatus} sendMessage={sendWsMessage} />

      {/* Ganzee Zoon User Profile Modal */}
      <UserProfileModal
        isOpen={isProfileModalOpen}
        onClose={() => setIsProfileModalOpen(false)}
      />

      {/* Mobile-Optimized Bottom App Navigation Bar */}
      <MobileBottomNav
        cartCount={cartCount}
        onOpenProfile={() => setIsProfileModalOpen(true)}
        user={user}
      />

      <footer className="site-footer">
        <span style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}>
          <GenZLogo size={20} />
          <strong>GenZ Zone</strong><span className="brand-dot">✦</span>
        </span>
        <span>Trending Ganzee Apparel, Streetwear &amp; Everyday Essentials. Powered by AI Streaming, Semantic Search &amp; Live Tracking.</span>
      </footer>
    </div>
  )
}
