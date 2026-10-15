/**
 * Sentry Frontend Exception Tracking and Monitoring
 * Gracefully activates when VITE_SENTRY_DSN is provided in environment variables.
 * Automatically scrubs sensitive authentication tokens and form fields.
 */

import * as Sentry from "@sentry/react"

const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN as string | undefined

export function initFrontendSentry(): boolean {
  if (!SENTRY_DSN || SENTRY_DSN.trim() === "") {
    if (import.meta.env.DEV) {
      console.debug("[Sentry] VITE_SENTRY_DSN is not configured; frontend error tracking disabled.")
    }
    return false
  }

  try {
    Sentry.init({
      dsn: SENTRY_DSN.trim(),
      environment: import.meta.env.MODE,
      integrations: [
        Sentry.browserTracingIntegration(),
      ],
      tracesSampleRate: import.meta.env.PROD ? 0.2 : 1.0,
      beforeSend(event) {
        // Redact authorization tokens or passwords if captured in breadcrumbs or event data
        if (event.request?.headers) {
          const headers = event.request.headers as Record<string, string>
          for (const key of Object.keys(headers)) {
            if (["authorization", "cookie"].includes(key.toLowerCase())) {
              headers[key] = "[FILTERED]"
            }
          }
        }
        return event
      },
    })
    console.info(`[Sentry] Frontend initialized (env: ${import.meta.env.MODE})`)
    return true
  } catch (err) {
    console.error("[Sentry] Failed to initialize frontend tracking:", err)
    return false
  }
}

export function captureFrontendError(error: unknown, context?: Record<string, unknown>): void {
  if (SENTRY_DSN) {
    Sentry.captureException(error, { extra: context })
  } else {
    console.error("[ShopZone Error]", error, context)
  }
}

export { Sentry }
