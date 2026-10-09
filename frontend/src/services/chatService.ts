import { jsonRequest, requestJson } from "./apiClient"
import type { ChatMessage } from "../../types"

export async function getChatMessages(
  token: string,
  customer?: string,
  signal?: AbortSignal,
): Promise<ChatMessage[]> {
  const query = customer ? `?customer=${encodeURIComponent(customer)}` : ""
  const data = await requestJson(`/chat/messages${query}`, {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  })
  return Array.isArray(data) ? (data as ChatMessage[]) : []
}

export async function sendChatMessage(
  token: string,
  message: string,
  recipientEmail = "admin",
): Promise<{ success: boolean; data: ChatMessage }> {
  const response = await requestJson(
    "/chat/messages",
    jsonRequest({ message, recipient_email: recipientEmail }, token),
  )
  return response as { success: boolean; data: ChatMessage }
}
