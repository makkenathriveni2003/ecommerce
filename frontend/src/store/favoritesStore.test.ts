import { beforeEach, describe, expect, it } from "vitest"
import { useFavoritesStore } from "./favoritesStore"
import type { Product } from "../../types"

const mockProductA: Product = {
  id: 101,
  name: "Ganzee Acid Wash Oversized Tee",
  price: 799,
  category: "Fashion",
  image: "https://example.com/tee.jpg",
  stock: 25,
}

const mockProductB: Product = {
  id: 102,
  name: "Apple iPhone 15 Pro",
  price: 134900,
  category: "Electronics",
  image: "https://example.com/iphone.jpg",
  stock: 12,
}

describe("favoritesStore (Wishlist & LocalStorage persistence)", () => {
  beforeEach(() => {
    useFavoritesStore.getState().clearFavorites()
    localStorage.clear()
  })

  it("initializes with empty favorites", () => {
    expect(useFavoritesStore.getState().favorites).toEqual([])
    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(0)
  })

  it("adds a product to favorites and prevents duplicates", () => {
    useFavoritesStore.getState().addFavorite(mockProductA)
    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(1)
    expect(useFavoritesStore.getState().isFavorite(101)).toBe(true)

    // Adding same product again should not duplicate
    useFavoritesStore.getState().addFavorite(mockProductA)
    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(1)
  })

  it("toggles favorite state on and off", () => {
    const isNowFav = useFavoritesStore.getState().toggleFavorite(mockProductA)
    expect(isNowFav).toBe(true)
    expect(useFavoritesStore.getState().isFavorite(101)).toBe(true)

    const isRemoved = useFavoritesStore.getState().toggleFavorite(mockProductA)
    expect(isRemoved).toBe(false)
    expect(useFavoritesStore.getState().isFavorite(101)).toBe(false)
  })

  it("removes a favorite by product ID", () => {
    useFavoritesStore.getState().addFavorite(mockProductA)
    useFavoritesStore.getState().addFavorite(mockProductB)
    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(2)

    useFavoritesStore.getState().removeFavorite(101)
    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(1)
    expect(useFavoritesStore.getState().isFavorite(101)).toBe(false)
    expect(useFavoritesStore.getState().isFavorite(102)).toBe(true)
  })

  it("clears all favorites at once", () => {
    useFavoritesStore.getState().addFavorite(mockProductA)
    useFavoritesStore.getState().addFavorite(mockProductB)
    useFavoritesStore.getState().clearFavorites()

    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(0)
    expect(useFavoritesStore.getState().favorites).toEqual([])
  })
})
