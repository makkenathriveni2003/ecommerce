import { beforeEach, describe, expect, it } from "vitest"
import type { Product } from "../../types"
import { useCartStore } from "./cartStore"

const headphones: Product = {
  id: 1,
  name: "Headphones",
  price: 3000,
  category: "Accessories",
  image: "https://example.com/headphones.jpg",
}

const watch: Product = {
  id: 2,
  name: "Watch",
  price: 5000,
  category: "Accessories",
  image: "https://example.com/watch.jpg",
}

describe("global cart store", () => {
  beforeEach(() => {
    useCartStore.setState({ cart: [] })
    localStorage.removeItem("day14-cart")
  })

  it("adds a product with quantity one", () => {
    useCartStore.getState().addToCart(headphones)
    expect(useCartStore.getState().cart).toEqual([{ ...headphones, quantity: 1 }])
  })

  it("increments quantity when the same product is added again", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.addToCart(headphones)
    expect(useCartStore.getState().cart[0].quantity).toBe(2)
  })

  it("keeps different products as separate cart lines", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.addToCart(watch)
    expect(useCartStore.getState().cart).toHaveLength(2)
  })

  it("removes the selected product", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.addToCart(watch)
    cart.removeFromCart(headphones.id)
    expect(useCartStore.getState().cart.map((item) => item.id)).toEqual([watch.id])
  })

  it("increases item quantity", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.increaseQuantity(headphones.id)
    expect(useCartStore.getState().cart[0].quantity).toBe(2)
  })

  it("decreases quantity without removing an item above one", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.increaseQuantity(headphones.id)
    cart.decreaseQuantity(headphones.id)
    expect(useCartStore.getState().cart[0].quantity).toBe(1)
  })

  it("removes an item when quantity is decreased below one", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.decreaseQuantity(headphones.id)
    expect(useCartStore.getState().cart).toEqual([])
  })

  it("sets quantity and removes an item at zero", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.setQuantity(headphones.id, 4)
    expect(useCartStore.getState().cart[0].quantity).toBe(4)
    cart.setQuantity(headphones.id, 0)
    expect(useCartStore.getState().cart).toEqual([])
  })

  it("calculates the cart total from item prices and quantities", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.addToCart(watch)
    cart.increaseQuantity(headphones.id)
    expect(cart.getCartTotal()).toBe(11000)
  })

  it("counts all units across cart lines", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.addToCart(watch)
    cart.increaseQuantity(headphones.id)
    expect(cart.getCartItemCount()).toBe(3)
  })

  it("clears every cart line", () => {
    const cart = useCartStore.getState()
    cart.addToCart(headphones)
    cart.addToCart(watch)
    cart.clearCart()
    expect(useCartStore.getState().cart).toEqual([])
  })

  it("persists the cart for a browser refresh", () => {
    useCartStore.getState().addToCart(headphones)
    const saved = JSON.parse(localStorage.getItem("day14-cart") ?? "{}")
    expect(saved.state.cart).toEqual([{ ...headphones, quantity: 1 }])
  })
})
