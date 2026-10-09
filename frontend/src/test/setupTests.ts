import "@testing-library/jest-dom/vitest"
import { cleanup, configure } from "@testing-library/react"
import { afterAll, afterEach, beforeAll } from "vitest"
import { useAuthStore } from "../store/authStore"
import { useCartStore } from "../store/cartStore"
import { server } from "./server"

configure({ asyncUtilTimeout: 5000 })

beforeAll(() => server.listen({ onUnhandledRequest: "error" }))
afterEach(() => {
  cleanup()
  server.resetHandlers()
  localStorage.clear()
  sessionStorage.clear()
  document.documentElement.dataset.theme = "light"
  useCartStore.setState({ cart: [] })
  useAuthStore.setState({ user: null, token: null, isAuthenticated: false })
})
afterAll(() => server.close())
