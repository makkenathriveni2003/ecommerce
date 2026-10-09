import { http, HttpResponse, ws } from "msw"
import { testProducts } from "./products"

const liveWs = ws.link(/.*\/ws.*/)

export const handlers = [
  liveWs.addEventListener("connection", ({ client }) => {
    client.send(
      JSON.stringify({
        type: "CONNECTION_ESTABLISHED",
        data: {
          admin_online: true,
          message: "Connected to Mock WebSocket",
        },
      }),
    )
  }),

  http.get("*/products", ({ request }) => {
    const url = new URL(request.url)
    const skip = Number(url.searchParams.get("skip") ?? "0")
    const limit = Number(url.searchParams.get("limit") ?? "100")
    return HttpResponse.json(testProducts.slice(skip, skip + limit))
  }),

  http.get("*/products/:productId", ({ params }) => {
    const product = testProducts.find(
      (item) => item.id === Number(params.productId),
    )
    return product
      ? HttpResponse.json(product)
      : HttpResponse.json({ message: "Product not found" }, { status: 404 })
  }),

  http.get("*/chat/messages", () => {
    return HttpResponse.json([])
  }),

  http.post("*/chat/messages", async ({ request }) => {
    const body = (await request.json()) as { recipient_email?: string; message?: string }
    return HttpResponse.json({
      success: true,
      data: {
        id: 1,
        sender_email: "shopper@example.com",
        sender_name: "Shopper User",
        sender_role: "shopper",
        recipient_email: body.recipient_email || "admin",
        text: body.message,
        created_at: new Date().toISOString(),
      },
    })
  }),

  http.post("*/tasks/run", async ({ request }) => {
    const body = ((await request.json().catch(() => ({}))) || {}) as { name?: string }
    return HttpResponse.json({
      success: true,
      task_id: "test-task-12345",
      name: body.name || "Sample Background Job",
      status: "PENDING",
      message: "Task queued successfully",
    })
  }),

  http.get("*/tasks/:taskId/status", ({ params }) => {
    const id = String(params.taskId)
    if (id.includes("csv")) {
      return HttpResponse.json({
        task_id: id,
        status: "SUCCESS",
        percent: 100,
        message: "CSV import completed: 3 imported/updated, 0 failed.",
        result: {
          status: "SUCCESS",
          percent: 100,
          imported_count: 3,
          failed_count: 0,
          total_rows: 3,
          errors: [],
          message: "CSV import completed: 3 imported/updated, 0 failed.",
        },
        error: null,
      })
    }
    return HttpResponse.json({
      task_id: params.taskId,
      status: "SUCCESS",
      percent: 100,
      message: "Task completed successfully!",
      result: { status: "SUCCESS", percent: 100, filename: "ShopZone_Invoice_1.pdf" },
      error: null,
    })
  }),

  http.post("*/orders/:orderId/invoice", ({ params }) => {
    return HttpResponse.json({
      success: true,
      task_id: `mock-invoice-task-${params.orderId}`,
      status: "PENDING",
      message: `Invoice generation task queued for order #${params.orderId}`,
    })
  }),

  http.get("*/products/search", ({ request }) => {
    const url = new URL(request.url)
    const q = (url.searchParams.get("q") || "").toLowerCase().trim()
    const matches = testProducts.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q) ||
        (q === "laptpo" && p.name.toLowerCase().includes("laptop")) ||
        (q === "iphnoe" && p.name.toLowerCase().includes("phone")),
    )
    return HttpResponse.json(matches)
  }),

  http.post("*/admin/products/import-csv", () => {
    return HttpResponse.json({
      success: true,
      task_id: "mock-csv-task-12345",
      status: "PENDING",
      filename: "import.csv",
      message: "CSV import queued with task ID mock-csv-task-12345",
    })
  }),
]
