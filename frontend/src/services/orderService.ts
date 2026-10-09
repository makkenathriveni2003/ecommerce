import type { Order } from "../../types"
import { jsonRequest, requestJson } from "./apiClient"

export interface CheckoutRequest {
  full_name: string
  email: string
  phone: string
  address: string
  city: string
  state: string
  pincode: string
  payment_method: "cash_on_delivery" | "card" | "upi"
  items: Array<{ product_id: number; quantity: number }>
}

interface CreateOrderResponse {
  success: boolean
  message: string
  order: Order
}

export async function createOrder(
  checkout: CheckoutRequest,
  token: string,
): Promise<CreateOrderResponse> {
  const payload = await requestJson(
    "/orders",
    jsonRequest(checkout, token),
  )
  if (
    typeof payload !== "object" ||
    payload === null ||
    !("success" in payload) ||
    payload.success !== true ||
    !("message" in payload) ||
    typeof payload.message !== "string" ||
    !("order" in payload) ||
    !isOrder(payload.order)
  ) {
    throw new Error("The order API returned an invalid response")
  }
  return {
    success: payload.success,
    message: payload.message,
    order: payload.order,
  }
}

export async function getMyOrders(
  token: string,
  signal?: AbortSignal,
): Promise<Order[]> {
  return readOrders(
    await requestJson("/orders", {
      headers: { Authorization: `Bearer ${token}` },
      signal,
    }),
  )
}

export interface AdminOrder extends Order {
  email: string
  full_name: string
  phone: string
  address: string
  city: string
  state: string
  pincode: string
  payment_method: string
}

function isOrderItem(value: unknown): value is Order["items"][number] {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    Number.isInteger(value.id) &&
    "product_id" in value &&
    Number.isInteger(value.product_id) &&
    "name" in value &&
    typeof value.name === "string" &&
    "quantity" in value &&
    Number.isInteger(value.quantity) &&
    "unit_price" in value &&
    typeof value.unit_price === "number" &&
    Number.isFinite(value.unit_price)
  )
}

function isOrder(value: unknown): value is Order {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    Number.isInteger(value.id) &&
    "status" in value &&
    typeof value.status === "string" &&
    "total" in value &&
    typeof value.total === "number" &&
    Number.isFinite(value.total) &&
    "created_at" in value &&
    typeof value.created_at === "string" &&
    "items" in value &&
    Array.isArray(value.items) &&
    value.items.every(isOrderItem)
  )
}

function readOrders(payload: unknown): Order[] {
  if (!Array.isArray(payload) || !payload.every(isOrder)) {
    throw new Error("The orders API returned an invalid response")
  }
  return payload
}

function isAdminOrder(value: unknown): value is AdminOrder {
  return (
    isOrder(value) &&
    "email" in value &&
    typeof value.email === "string" &&
    "full_name" in value &&
    typeof value.full_name === "string" &&
    "phone" in value &&
    typeof value.phone === "string" &&
    "address" in value &&
    typeof value.address === "string" &&
    "city" in value &&
    typeof value.city === "string" &&
    "state" in value &&
    typeof value.state === "string" &&
    "pincode" in value &&
    typeof value.pincode === "string" &&
    "payment_method" in value &&
    typeof value.payment_method === "string"
  )
}

function readAdminOrders(payload: unknown): AdminOrder[] {
  if (!Array.isArray(payload) || !payload.every(isAdminOrder)) {
    throw new Error("The admin orders API returned an invalid response")
  }
  return payload
}

export async function getAdminOrders(
  token: string,
  signal?: AbortSignal,
): Promise<AdminOrder[]> {
  return readAdminOrders(
    await requestJson("/admin/orders", {
      headers: { Authorization: `Bearer ${token}` },
      signal,
    }),
  )
}

export async function updateOrderStatus(
  orderId: number,
  status: string,
  token: string,
): Promise<void> {
  const payload = await requestJson(
    `/admin/orders/${orderId}/status`,
    jsonRequest({ status }, token, "PATCH"),
  )
  if (
    typeof payload !== "object" ||
    payload === null ||
    !("order" in payload) ||
    typeof payload.order !== "object" ||
    payload.order === null ||
    !("id" in payload.order) ||
    payload.order.id !== orderId ||
    !("status" in payload.order) ||
    payload.order.status !== status
  ) {
    throw new Error("The order status API returned an invalid response")
  }
}

export async function generateOrderInvoice(
  orderId: number,
  token: string,
): Promise<{ success: boolean; task_id: string; order_id: number; status: string; message: string }> {
  const payload = await requestJson(
    `/orders/${orderId}/invoice`,
    jsonRequest({}, token, "POST"),
  )
  return payload as { success: boolean; task_id: string; order_id: number; status: string; message: string }
}

export function getOrderInvoiceDownloadUrl(orderId: number, token?: string): string {
  const base = `/orders/${orderId}/invoice/download`
  return token ? `${base}?token=${encodeURIComponent(token)}` : base
}
