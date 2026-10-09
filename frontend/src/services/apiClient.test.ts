import { http, HttpResponse } from "msw"
import { describe, expect, it } from "vitest"
import { requestJson } from "./apiClient"
import { server } from "../test/server"
import { useAuthStore } from "../store/authStore"

describe("API client errors", () => {
  it("clears an expired signed-in session after an authorized 401", async () => {
    useAuthStore.getState().login(
      { name: "Shopper", email: "shopper@example.com", role: "shopper" },
      "expired-token",
    )
    server.use(
      http.get("*/private", () =>
        HttpResponse.json({ detail: "Invalid or expired access token" }, { status: 401 }),
      ),
    )

    await expect(
      requestJson("/private", {
        headers: { Authorization: "Bearer expired-token" },
      }),
    ).rejects.toThrow("Please sign in again.")
    expect(useAuthStore.getState().user).toBeNull()
    expect(sessionStorage.getItem("daylight-session")).toBeNull()
  })

  it.each([
    [400, "We couldn’t process that request. Please check your information and try again."],
    [401, "Please sign in again."],
    [403, "You don’t have permission to do that."],
    [404, "The requested item could not be found."],
    [429, "Too many requests. Please wait a moment and try again."],
    [500, "The server encountered a problem. Please try again."],
  ])("shows a friendly message for HTTP %i", async (status, message) => {
    server.use(
      http.get("*/status-error", () =>
        HttpResponse.json({ detail: "Raw internal backend detail" }, { status }),
      ),
    )

    await expect(requestJson("/status-error")).rejects.toThrow(message)
  })

  it("shows validation messages returned by FastAPI", async () => {
    server.use(
      http.post("*/invalid", () =>
        HttpResponse.json(
          { detail: [{ loc: ["body", "pincode"], msg: "Invalid pincode" }] },
          { status: 422 },
        ),
      ),
    )

    await expect(requestJson("/invalid", { method: "POST" })).rejects.toThrow(
      "Invalid pincode",
    )
  })

  it("shows a clear unavailable-backend message for network failures", async () => {
    server.use(http.get("*/offline", () => HttpResponse.error()))
    await expect(requestJson("/offline")).rejects.toThrow(
      "Cannot reach the backend at http://127.0.0.1:8000.",
    )
  })
})
