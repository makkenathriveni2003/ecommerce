import type { User } from "../../types"
import { jsonRequest, requestJson } from "./apiClient"

interface AuthResponse {
  token: string
  user: User
}

function isAuthResponse(payload: unknown): payload is AuthResponse {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "token" in payload &&
    typeof payload.token === "string" &&
    "user" in payload &&
    typeof payload.user === "object" &&
    payload.user !== null &&
    "name" in payload.user &&
    typeof payload.user.name === "string" &&
    "email" in payload.user &&
    typeof payload.user.email === "string" &&
    "role" in payload.user &&
    (payload.user.role === "shopper" || payload.user.role === "admin")
  )
}

export async function registerAccount(
  name: string,
  email: string,
  password: string,
): Promise<void> {
  await requestJson(
    "/auth/register",
    jsonRequest({ name, email, password }),
  )
}

export async function loginAccount(
  email: string,
  password: string,
): Promise<AuthResponse> {
  const payload = await requestJson(
    "/auth/login",
    jsonRequest({ email, password }),
  )
  if (!isAuthResponse(payload)) {
    throw new Error("The login API returned an invalid response")
  }
  return payload
}
