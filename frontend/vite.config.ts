import react from "@vitejs/plugin-react"
import { defineConfig } from "vitest/config"

function inlineStylesheet() {
  return {
    name: "inline-production-stylesheet",
    apply: "build" as const,
    enforce: "post" as const,
    transformIndexHtml: {
      order: "post" as const,
      handler(html: string, ctx: { bundle?: Record<string, { type: string; source?: string | Uint8Array }> }) {
        if (!ctx.bundle) return html
        let minifiedCss = ""
        for (const [fileName, asset] of Object.entries(ctx.bundle)) {
          if (fileName.endsWith(".css") && asset.source) {
            minifiedCss += asset.source.toString()
          }
        }
        if (!minifiedCss) return html
        const withoutCssLink = html.replace(/<link rel="stylesheet"[^>]+href="[^"]+\.css"[^>]*>/g, "")
        return withoutCssLink.replace("</head>", `<style>${minifiedCss}</style></head>`)
      },
    },
  }
}

export default defineConfig({
  plugins: [react(), inlineStylesheet()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes("node_modules")) {
            if (id.includes("react-dom") || id.includes("/react/")) {
              return "vendor-react"
            }
            if (id.includes("react-router")) {
              return "vendor-router"
            }
            if (id.includes("@tanstack/react-query")) {
              return "vendor-query"
            }
          }
        },
      },
    },
  },
  test: {
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
    environment: "jsdom",
    setupFiles: ["./src/test/setupTests.ts"],
    restoreMocks: true,
    clearMocks: true,
  },
})
