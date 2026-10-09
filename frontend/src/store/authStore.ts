import { create } from "zustand"
import type { User } from "../../types"

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (user: User, token: string) => void
  logout: () => void
}

function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "name" in value &&
    typeof value.name === "string" &&
    "email" in value &&
    typeof value.email === "string" &&
    "role" in value &&
    (value.role === "shopper" || value.role === "admin")
  )
}

function readSession(): { user: User; token: string } | null {
  const saved = sessionStorage.getItem("daylight-session")
  if (!saved) return null

  try {
    const session: unknown = JSON.parse(saved)
    if (
      typeof session === "object" &&
      session !== null &&
      "user" in session &&
      "token" in session &&
      isUser(session.user) &&
      typeof session.token === "string"
    ) {
      return { user: session.user, token: session.token }
    }
    sessionStorage.removeItem("daylight-session")
  } catch {
    sessionStorage.removeItem("daylight-session")
  }
  return null
}

const session = readSession()

export const useAuthStore = create<AuthState>()((set) => ({
  user: session?.user ?? null,
  token: session?.token ?? null,
  isAuthenticated: session !== null,
  login: (user, token) => {
    sessionStorage.setItem("daylight-session", JSON.stringify({ user, token }))
    set({ user, token, isAuthenticated: true })
  },
  logout: () => {
    sessionStorage.removeItem("daylight-session")
    set({ user: null, token: null, isAuthenticated: false })
  },
}))
