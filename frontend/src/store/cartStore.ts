import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import type { CartItem, Product } from "../../types"

interface CartState {
  cart: CartItem[]
  addToCart: (product: Product) => void
  removeFromCart: (productId: number) => void
  increaseQuantity: (productId: number) => void
  decreaseQuantity: (productId: number) => void
  setQuantity: (productId: number, quantity: number) => void
  clearCart: () => void
  getCartTotal: () => number
  getCartItemCount: () => number
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      cart: [],
      addToCart: (product) =>
        set((state) => {
          const existingProduct = state.cart.find((item) => item.id === product.id)
          if (existingProduct) {
            return {
              cart: state.cart.map((item) =>
                item.id === product.id ? { ...item, quantity: item.quantity + 1 } : item,
              ),
            }
          }
          return { cart: [...state.cart, { ...product, quantity: 1 }] }
        }),
      removeFromCart: (productId) =>
        set((state) => ({ cart: state.cart.filter((item) => item.id !== productId) })),
      increaseQuantity: (productId) =>
        set((state) => ({
          cart: state.cart.map((item) =>
            item.id === productId ? { ...item, quantity: item.quantity + 1 } : item,
          ),
        })),
      decreaseQuantity: (productId) =>
        set((state) => ({
          cart: state.cart.flatMap((item) =>
            item.id === productId
              ? item.quantity <= 1
                ? []
                : [{ ...item, quantity: item.quantity - 1 }]
              : [item],
          ),
        })),
      setQuantity: (productId, quantity) =>
        set((state) => ({
          cart:
            quantity <= 0
              ? state.cart.filter((item) => item.id !== productId)
              : state.cart.map((item) =>
                  item.id === productId ? { ...item, quantity } : item,
                ),
        })),
      clearCart: () => set({ cart: [] }),
      getCartTotal: () =>
        get().cart.reduce((total, item) => total + item.price * item.quantity, 0),
      getCartItemCount: () =>
        get().cart.reduce((total, item) => total + item.quantity, 0),
    }),
    {
      name: "day14-cart",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ cart: state.cart }),
    },
  ),
)
