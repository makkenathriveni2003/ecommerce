import react from "@vitejs/plugin-react"
import { readFileSync } from "node:fs"
import { join } from "node:path"
import { defineConfig } from "vitest/config"

function inlineStylesheet() {
  let root = ""

  return {
    name: "inline-production-stylesheet",
    apply: "build" as const,
    configResolved(config: { root: string }) {
      root = config.root
    },
    transformIndexHtml: {
      order: "pre" as const,
      handler(html: string) {
        const css = readFileSync(join(root, "src", "index.css"), "utf8")
        return html.replace("</head>", `<style>${css}</style></head>`)
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
