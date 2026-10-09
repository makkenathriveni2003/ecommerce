import { zodResolver } from "@hookform/resolvers/zod"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useMemo } from "react"
import { useForm } from "react-hook-form"
import { Link, useNavigate } from "react-router-dom"
import { z } from "zod"
import { createOrder, type CheckoutRequest } from "../services/orderService"
import { useAuthStore } from "../store/authStore"
import { useCartStore } from "../store/cartStore"

const checkoutSchema = z.object({
  full_name: z.string().trim().min(2, "Enter your full name."),
  email: z.email("Enter a valid email."),
  phone: z.string().regex(/^[0-9]\d{9}$/, "Enter a valid 10-digit mobile number."),
  address: z.string().trim().min(5, "Enter a complete street address."),
  city: z.string().trim().min(2, "Enter your city."),
  state: z.string().trim().min(2, "Enter your state."),
  pincode: z.string().regex(/^\d{6}$/, "Enter a valid 6-digit pincode."),
  payment_method: z.enum(["cash_on_delivery", "card", "upi"]),
})

type CheckoutFields = z.infer<typeof checkoutSchema>

const formatPrice = (price: number) => `₹${price.toLocaleString("en-IN")}`

export default function Checkout() {
  const user = useAuthStore((state) => state.user)
  const token = useAuthStore((state) => state.token)
  const cart = useCartStore((state) => state.cart)
  const clearCart = useCartStore((state) => state.clearCart)
  const total = useMemo(
    () => cart.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [cart],
  )
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CheckoutFields>({
    resolver: zodResolver(checkoutSchema),
    defaultValues: {
      full_name: user?.name ?? "",
      email: user?.email ?? "",
      phone: "",
      address: "",
      city: "",
      state: "",
      pincode: "",
      payment_method: "cash_on_delivery",
    },
  })
  const mutation = useMutation({
    mutationFn: (checkout: CheckoutRequest) => createOrder(checkout, token!),
    onSuccess: async (response) => {
      clearCart()
      await queryClient.invalidateQueries({ queryKey: ["orders"] })
      navigate(`/orders?placed=${response.order.id}`)
    },
  })

  if (!user || !token) {
    return (
      <section className="checkout-page">
        <p role="alert">Sign in before checking out.</p>
        <Link className="primary-button" to="/manage">Sign in</Link>
      </section>
    )
  }
  if (cart.length === 0) {
    return (
      <section className="checkout-page empty-cart">
        <h1>Your bag is empty.</h1>
        <Link className="primary-button" to="/">Explore the shop</Link>
      </section>
    )
  }

  const submit = handleSubmit((fields) => {
    mutation.mutate({
      ...fields,
      items: cart.map((item) => ({
        product_id: item.id,
        quantity: item.quantity,
      })),
    })
  })

  return (
    <section className="checkout-page">
      <div className="cart-heading">
        <div>
          <p className="eyebrow">SECURE CHECKOUT</p>
          <h1>Delivery details<span className="brand-dot">.</span></h1>
        </div>
      </div>
      <div className="checkout-layout">
        <form className="manage-form checkout-form" onSubmit={submit} noValidate>
          <div className="form-row">
            <label>Full name<input autoComplete="name" {...register("full_name")} /></label>
            <label>Email<input autoComplete="email" type="email" {...register("email")} /></label>
          </div>
          <label>Phone<input autoComplete="tel" inputMode="numeric" {...register("phone")} /></label>
          <label>Address<input autoComplete="street-address" {...register("address")} /></label>
          <div className="form-row">
            <label>City<input autoComplete="address-level2" {...register("city")} /></label>
            <label>State<input autoComplete="address-level1" {...register("state")} /></label>
            <label>Pincode<input autoComplete="postal-code" inputMode="numeric" {...register("pincode")} /></label>
          </div>
          <label>
            Payment method
            <select aria-label="Payment method" {...register("payment_method")}>
              <option value="cash_on_delivery">Cash on delivery</option>
              <option value="upi">UPI</option>
              <option value="card">Card</option>
            </select>
            <span className="field-hint">
              Payment options are recorded with the order; online payment processing is not connected.
            </span>
          </label>
          {Object.entries(errors).map(([field, error]) => (
            <p className="form-message error-message" key={field} role="alert">
              {error.message}
            </p>
          ))}
          {mutation.isError && (
            <p className="form-message error-message" role="alert">
              {mutation.error.message}
            </p>
          )}
          <button className="primary-button" disabled={mutation.isPending} type="submit">
            {mutation.isPending ? "Placing order..." : "Place order"}
          </button>
        </form>
        <aside className="order-summary" aria-label="Order summary">
          <h2>Order summary</h2>
          {cart.map((item) => (
            <div className="summary-line" key={item.id}>
              <span>{item.name} × {item.quantity}</span>
              <span>{formatPrice(item.price * item.quantity)}</span>
            </div>
          ))}
          <div className="summary-total">
            <span>Total</span><span>{formatPrice(total)}</span>
          </div>
          <Link className="continue-link" to="/cart">Return to your bag</Link>
        </aside>
      </div>
    </section>
  )
}
