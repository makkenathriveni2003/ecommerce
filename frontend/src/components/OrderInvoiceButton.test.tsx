import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import { OrderInvoiceButton } from "./OrderInvoiceButton"
import { useAuthStore } from "../store/authStore"
import { server } from "../test/server"

describe("OrderInvoiceButton", () => {
  beforeEach(() => {
    useAuthStore.getState().login(
      { name: "Shopper", email: "shopper@example.com", role: "shopper" },
      "test-auth-token",
    )
  })

  it("renders the initial Generate Invoice button", () => {
    render(<OrderInvoiceButton orderId={101} />)
    expect(screen.getByTestId("generate-invoice-btn-101")).toBeInTheDocument()
    expect(screen.getByText("Generate Invoice")).toBeInTheDocument()
  })

  it("triggers invoice generation and transitions to ready state when task completes", async () => {
    const user = userEvent.setup()

    server.use(
      http.post("*/orders/:orderId/invoice", () => {
        return HttpResponse.json({
          success: true,
          task_id: "test-pdf-task-101",
          status: "PENDING",
          message: "Task queued",
        })
      }),
      http.get("*/tasks/:taskId/status", () => {
        return HttpResponse.json({
          task_id: "test-pdf-task-101",
          status: "SUCCESS",
          percent: 100,
          message: "Invoice generated successfully",
          result: { file_path: "generated_invoices/invoice_101.pdf" },
          error: null,
        })
      }),
    )

    render(<OrderInvoiceButton orderId={101} />)

    const btn = screen.getByTestId("generate-invoice-btn-101")
    await user.click(btn)

    // Eventually status becomes SUCCESS -> Download ready
    await waitFor(() => {
      expect(screen.getByTestId("invoice-ready-badge-101")).toBeInTheDocument()
    })
    expect(screen.getByTestId("download-invoice-btn-101")).toBeInTheDocument()
    expect(screen.getByText("Download Invoice (PDF)")).toBeInTheDocument()
  })

  it("handles trigger failure with error badge and retry button", async () => {
    const user = userEvent.setup()

    server.use(
      http.post("*/orders/:orderId/invoice", () => {
        return HttpResponse.json(
          { detail: "Failed to schedule invoice task" },
          { status: 500 },
        )
      }),
    )

    render(<OrderInvoiceButton orderId={101} />)
    const btn = screen.getByTestId("generate-invoice-btn-101")
    await user.click(btn)

    await waitFor(() => {
      expect(screen.getByTestId("invoice-error-101")).toBeInTheDocument()
    })
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument()
  })

  it("triggers file download when Download Invoice is clicked", async () => {
    const user = userEvent.setup()

    server.use(
      http.post("*/orders/:orderId/invoice", () => {
        return HttpResponse.json({
          success: true,
          task_id: "test-pdf-task-101",
          status: "PENDING",
        })
      }),
      http.get("*/tasks/:taskId/status", () => {
        return HttpResponse.json({
          task_id: "test-pdf-task-101",
          status: "SUCCESS",
          percent: 100,
        })
      }),
    )

    render(<OrderInvoiceButton orderId={101} />)
    await user.click(screen.getByTestId("generate-invoice-btn-101"))

    await waitFor(() => {
      expect(screen.getByTestId("download-invoice-btn-101")).toBeInTheDocument()
    })

    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})

    await user.click(screen.getByTestId("download-invoice-btn-101"))
    expect(clickSpy).toHaveBeenCalled()

    clickSpy.mockRestore()
  })
})
