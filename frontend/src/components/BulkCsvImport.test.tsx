import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { http, HttpResponse } from "msw"
import { BulkCsvImport } from "./BulkCsvImport"
import { useAuthStore } from "../store/authStore"
import { server } from "../test/server"

describe("BulkCsvImport Component", () => {
  beforeEach(() => {
    useAuthStore.getState().login(
      { name: "Admin", email: "admin@example.com", role: "admin" },
      "test-admin-token",
    )
  })

  it("renders upload interface and sample download button", () => {
    render(<BulkCsvImport />)
    expect(screen.getByTestId("bulk-csv-import-card")).toBeInTheDocument()
    expect(screen.getByText("Bulk Product CSV Import")).toBeInTheDocument()
    expect(screen.getByTestId("download-sample-csv-btn")).toBeInTheDocument()
    expect(screen.getByTestId("start-csv-import-btn")).toBeDisabled()
  })

  it("allows selecting a CSV file and triggers import via Celery", async () => {
    const user = userEvent.setup()
    const onComplete = vi.fn()

    server.use(
      http.post("*/admin/products/import-csv", () => {
        return HttpResponse.json({
          success: true,
          task_id: "test-csv-task-1",
          status: "PENDING",
          filename: "products.csv",
          message: "CSV import queued",
        })
      }),
      http.get("*/tasks/:taskId/status", () => {
        return HttpResponse.json({
          task_id: "test-csv-task-1",
          status: "SUCCESS",
          percent: 100,
          message: "CSV import completed: 2 imported, 0 failed.",
          result: {
            status: "SUCCESS",
            percent: 100,
            imported_count: 2,
            failed_count: 0,
            total_rows: 2,
            errors: [],
          },
          error: null,
        })
      }),
    )

    render(<BulkCsvImport onImportComplete={onComplete} />)

    // Select file
    const file = new File(["name,price\nItem1,100\nItem2,200"], "products.csv", { type: "text/csv" })
    const fileInput = screen.getByTestId("csv-file-input")
    await user.upload(fileInput, file)

    expect(screen.getByTestId("selected-file-info")).toHaveTextContent("products.csv")
    const startBtn = screen.getByTestId("start-csv-import-btn")
    expect(startBtn).not.toBeDisabled()

    // Start import
    await user.click(startBtn)

    // Wait for task completion
    await waitFor(() => {
      expect(screen.getByTestId("csv-task-status-badge")).toHaveTextContent("SUCCESS")
    })

    expect(screen.getByTestId("imported-count")).toHaveTextContent("2")
    expect(screen.getByTestId("failed-count")).toHaveTextContent("0")
    expect(onComplete).toHaveBeenCalled()
  })

  it("displays row-level error details when some rows fail validation", async () => {
    const user = userEvent.setup()

    server.use(
      http.post("*/admin/products/import-csv", () => {
        return HttpResponse.json({
          success: true,
          task_id: "test-csv-task-errors",
          status: "PENDING",
          filename: "mixed.csv",
          message: "Queued",
        })
      }),
      http.get("*/tasks/:taskId/status", () => {
        return HttpResponse.json({
          task_id: "test-csv-task-errors",
          status: "SUCCESS",
          percent: 100,
          message: "Import finished with errors",
          result: {
            status: "SUCCESS",
            percent: 100,
            imported_count: 1,
            failed_count: 1,
            total_rows: 2,
            errors: [{ row: 2, name: "Broken Item", reason: "Invalid price" }],
          },
          error: null,
        })
      }),
    )

    render(<BulkCsvImport />)

    const file = new File(["name,price\nValid,50\nBroken Item,-10"], "mixed.csv", { type: "text/csv" })
    await user.upload(screen.getByTestId("csv-file-input"), file)
    await user.click(screen.getByTestId("start-csv-import-btn"))

    await waitFor(() => {
      expect(screen.getByTestId("csv-errors-list")).toBeInTheDocument()
    })
    expect(screen.getByText(/Row 2: Invalid price/i)).toBeInTheDocument()
  })
})
