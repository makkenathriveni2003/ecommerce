import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it } from "vitest"
import { useCartStore } from "../store/cartStore"
import { useFavoritesStore } from "../store/favoritesStore"
import { renderApp } from "../test/testUtils"
import Favorites from "./Favorites"
import type { Product } from "../../types"

const sampleFavorite: Product = {
  id: 201,
  name: "Ganzee Streetwear Oversized Tee",
  price: 899,
  category: "Fashion",
  image: "https://example.com/tee.jpg",
  stock: 20,
}

describe("Favorites (Wishlist) Page", () => {
  beforeEach(() => {
    useFavoritesStore.getState().clearFavorites()
    useCartStore.getState().clearCart()
  })

  it("renders empty state when there are no favorites", () => {
    renderApp(<Favorites />)
    expect(screen.getByText("Your Wishlist is Empty")).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: /Explore Trending Ganzee Styles/i }),
    ).toBeInTheDocument()
    expect(screen.getByText(/genzzone_favorites_storage/i)).toBeInTheDocument()
  })

  it("renders saved favorite products and allows moving to bag", async () => {
    useFavoritesStore.getState().addFavorite(sampleFavorite)
    const user = userEvent.setup()

    renderApp(<Favorites />)

    expect(screen.getByText("Ganzee Streetwear Oversized Tee")).toBeInTheDocument()
    expect(screen.getByText("₹899")).toBeInTheDocument()

    // Click "Move to Bag"
    const moveBtn = screen.getByRole("button", { name: /Move to Bag/i })
    await user.click(moveBtn)

    // Should be added to cart and removed from favorites
    expect(useCartStore.getState().getCartItemCount()).toBe(1)
    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(0)
  })

  it("removes a single favorite when clicking the remove button", async () => {
    useFavoritesStore.getState().addFavorite(sampleFavorite)
    const user = userEvent.setup()

    renderApp(<Favorites />)

    const removeBtn = screen.getByRole("button", {
      name: `Remove ${sampleFavorite.name} from wishlist`,
    })
    await user.click(removeBtn)

    expect(useFavoritesStore.getState().getFavoritesCount()).toBe(0)
    expect(screen.getByText("Your Wishlist is Empty")).toBeInTheDocument()
  })
})
