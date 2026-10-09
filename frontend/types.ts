export interface Product {
  id: number
  name: string
  price: number
  category: string
  image: string
  description?: string
  stock?: number
}

export interface CartItem extends Product {
  quantity: number
}

export interface User {
  id?: number
  name: string
  email: string
  role: "shopper" | "admin"
}

export interface OrderItem {
  id: number
  product_id: number
  name: string
  quantity: number
  unit_price: number
}

export interface Order {
  id: number
  status: string
  total: number
  created_at: string
  items: OrderItem[]
  user_id?: number
  email?: string
}

export interface ProductPage {
  products: Product[]
  nextSkip: number | undefined
}

export function isProduct(value: unknown): value is Product {
  if (typeof value !== "object" || value === null) return false

  const product = value as Record<string, unknown>
  return (
    Number.isInteger(product.id) &&
    typeof product.name === "string" &&
    typeof product.price === "number" &&
    Number.isFinite(product.price) &&
    typeof product.category === "string" &&
    typeof product.image === "string"
  )
}

export type WebSocketStatus = "CONNECTING" | "OPEN" | "CLOSING" | "CLOSED"

export type NotificationType =
  | "confirmed"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "pending"
  | "info"

export interface NotificationItem {
  id: string
  order_id?: number
  title: string
  message: string
  type: NotificationType
  created_at: string
  read: boolean
}

export interface ChatMessage {
  id: number
  sender_email: string
  sender_name: string
  sender_role: "shopper" | "admin" | "guest"
  recipient_email: string
  text: string
  created_at: string
}

export interface OrderUpdatePayload {
  order_id: number
  status: string
  total: number
  email: string
  updated_at?: string
  created_at?: string
  message?: string
  items?: OrderItem[]
}

export interface WebSocketMessage<T = unknown> {
  type:
    | "ORDER_UPDATE"
    | "NOTIFICATION"
    | "CHAT_MESSAGE"
    | "PRESENCE_UPDATE"
    | "CONNECTION_ESTABLISHED"
    | "PING"
    | "PONG"
    | "AUTH_SUCCESS"
    | "AUTH_ERROR"
  data?: T
  message?: string
}
