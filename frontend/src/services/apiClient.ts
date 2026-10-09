import { useAuthStore } from "../store/authStore"

export const API_URL = (
  import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"
).replace(/\/+$/, "")

export const WS_URL = (
  import.meta.env.VITE_WS_URL ?? "ws://127.0.0.1:8000/ws"
).replace(/\/+$/, "")


export async function requestJson(
  path: string,
  init: RequestInit = {},
): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, init)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Cannot reach the backend at ${API_URL}. Start the backend and check its database connection.`,
      )
    }
    throw error
  }

  const payload: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    if (
      response.status === 401 &&
      new Headers(init.headers).has("Authorization")
    ) {
      useAuthStore.getState().logout()
    }
    const rawDetail =
      typeof payload === "object" &&
      payload !== null &&
      "detail" in payload &&
      payload.detail !== undefined
        ? payload.detail
        : undefined
    const detail = typeof rawDetail === "string"
      ? rawDetail
      : Array.isArray(rawDetail)
        ? rawDetail
            .flatMap((issue) =>
              typeof issue === "object" &&
              issue !== null &&
              "msg" in issue &&
              typeof issue.msg === "string"
                ? [issue.msg]
                : [],
            )
            .join(" ")
        : ""
    const message =
      response.status === 400
        ? "We couldn’t process that request. Please check your information and try again."
        : response.status === 401
          ? "Please sign in again."
          : response.status === 403
            ? "You don’t have permission to do that."
            : response.status === 404
              ? "The requested item could not be found."
              : response.status === 409
                ? (detail || "This email is already registered. Please sign in instead.")
                : response.status === 429
                  ? "Too many requests. Please wait a moment and try again."
                  : response.status >= 500
                    ? "The server encountered a problem. Please try again."
                    : detail ||
                      (response.status === 422
                        ? "Please check the submitted information."
                        : `Request failed (${response.status}).`)

    throw new Error(message)
  }
  return payload
}

export function jsonRequest(
  body: unknown,
  token?: string,
  method = "POST",
): RequestInit {
  return {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  }
}
