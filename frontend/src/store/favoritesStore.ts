import { create } from "zustand"
import { createJSONStorage, persist } from "zustand/middleware"
import type { Product } from "../../types"

interface FavoritesState {
  favorites: Product[]
  addFavorite: (product: Product) => void
  removeFavorite: (productId: number) => void
  toggleFavorite: (product: Product) => boolean
  isFavorite: (productId: number) => boolean
  clearFavorites: () => void
  getFavoritesCount: () => number
}

export const useFavoritesStore = create<FavoritesState>()(
  persist(
    (set, get) => ({
      favorites: [],
      addFavorite: (product) =>
        set((state) => {
          if (state.favorites.some((item) => item.id === product.id)) return state
          return { favorites: [...state.favorites, product] }
        }),
      removeFavorite: (productId) =>
        set((state) => ({
          favorites: state.favorites.filter((item) => item.id !== productId),
        })),
      toggleFavorite: (product) => {
        const { favorites } = get()
        const exists = favorites.some((item) => item.id === product.id)
        if (exists) {
          set({ favorites: favorites.filter((item) => item.id !== product.id) })
          return false
        } else {
          set({ favorites: [...favorites, product] })
          return true
        }
      },
      isFavorite: (productId) => {
        return get().favorites.some((item) => item.id === productId)
      },
      clearFavorites: () => set({ favorites: [] }),
      getFavoritesCount: () => get().favorites.length,
    }),
    {
      name: "genzzone_favorites_storage",
      storage: createJSONStorage(() => localStorage),
    },
  ),
)
