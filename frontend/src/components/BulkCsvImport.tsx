import React, { useRef, useState } from "react"
import { useBackgroundTask } from "../hooks/useBackgroundTask"
import { uploadProductsCsv } from "../services/productService"
import { useAuthStore } from "../store/authStore"

interface BulkCsvImportProps {
  onImportComplete?: () => void
}

interface ImportResult {
  status: string
  percent: number
  imported_count?: number
  failed_count?: number
  total_rows?: number
  errors?: Array<{ row?: number; name?: string; reason?: string }>
  message?: string
}

export const BulkCsvImport: React.FC<BulkCsvImportProps> = ({ onImportComplete }) => {
  const token = useAuthStore((state) => state.token)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState<boolean>(false)

  const task = useBackgroundTask({
    pollInterval: 600,
    onSuccess: () => {
      if (onImportComplete) {
        onImportComplete()
      }
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError(null)
    const file = e.target.files?.[0]
    if (!file) {
      setSelectedFile(null)
      return
    }
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setUploadError("Please select a valid CSV file (.csv)")
      setSelectedFile(null)
      return
    }
    setSelectedFile(file)
  }

  const handleStartImport = async () => {
    if (!selectedFile) {
      setUploadError("Please select a CSV file first.")
      return
    }
    if (!token) {
      setUploadError("Authentication required. Please sign in as admin.")
      return
    }

    setIsUploading(true)
    setUploadError(null)

    try {
      const resp = await uploadProductsCsv(selectedFile, token)
      task.trackTask(resp.task_id)
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to upload CSV"
      setUploadError(msg)
    } finally {
      setIsUploading(false)
    }
  }

  const handleDownloadSampleCsv = () => {
    const sample =
      "name,price,category,image,description,stock\n" +
      "Mechanical RGB Keyboard,4999.0,Electronics,https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=500,Premium mechanical tactile gaming keyboard,25\n" +
      "Studio Headphones,7499.0,Electronics,https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500,Over-ear studio monitor headphones,15\n" +
      "Leather Travel Bag,3499.0,Bags,https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=500,Full-grain genuine leather weekender bag,10\n"

    const blob = new Blob([sample], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const link = document.createElement("a")
    link.href = url
    link.setAttribute("download", "shopzone_products_sample.csv")
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const importResult = task.result as ImportResult | null

  return (
    <div
      style={{
        border: "1px solid var(--color-border, #e2e8f0)",
        borderRadius: "12px",
        padding: "1.5rem",
        background: "var(--color-surface, #ffffff)",
        boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
        marginTop: "1.5rem",
      }}
      data-testid="bulk-csv-import-card"
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
          flexWrap: "wrap",
          gap: "0.5rem",
        }}
      >
        <div>
          <h2
            style={{
              fontSize: "1.25rem",
              fontWeight: 600,
              color: "var(--color-text, #1e293b)",
              margin: 0,
            }}
          >
            Bulk Product CSV Import
          </h2>
          <p
            style={{
              color: "var(--color-text-muted, #64748b)",
              fontSize: "0.875rem",
              margin: "0.25rem 0 0 0",
            }}
          >
            Upload a CSV to batch import or update catalog products asynchronously via Celery.
          </p>
        </div>

        <button
          type="button"
          onClick={handleDownloadSampleCsv}
          data-testid="download-sample-csv-btn"
          style={{
            padding: "0.375rem 0.75rem",
            fontSize: "0.8125rem",
            borderRadius: "6px",
            border: "1px solid var(--color-border, #cbd5e1)",
            background: "transparent",
            cursor: "pointer",
            color: "var(--color-text, #334155)",
          }}
        >
          ⬇ Download Sample CSV
        </button>
      </div>

      {/* File Selector */}
      <div
        style={{
          border: "2px dashed var(--color-border, #cbd5e1)",
          borderRadius: "8px",
          padding: "1.5rem",
          textAlign: "center",
          background: "var(--color-background, #f8fafc)",
          marginBottom: "1rem",
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          style={{ display: "none" }}
          data-testid="csv-file-input"
          id="csv-file-input"
        />
        <label
          htmlFor="csv-file-input"
          style={{
            cursor: "pointer",
            display: "inline-block",
            padding: "0.5rem 1rem",
            borderRadius: "6px",
            background: "var(--color-surface, #ffffff)",
            border: "1px solid var(--color-border, #cbd5e1)",
            fontWeight: 500,
            color: "var(--color-text, #1e293b)",
            marginBottom: "0.5rem",
          }}
        >
          Select CSV File
        </label>

        {selectedFile ? (
          <div
            style={{
              marginTop: "0.5rem",
              fontSize: "0.875rem",
              color: "var(--color-text, #334155)",
              fontWeight: 500,
            }}
            data-testid="selected-file-info"
          >
            📄 {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
          </div>
        ) : (
          <div
            style={{
              fontSize: "0.8125rem",
              color: "var(--color-text-muted, #94a3b8)",
            }}
          >
            Choose a .csv file containing columns: name, price, category, image, description, stock
          </div>
        )}
      </div>

      {/* Action Button */}
      <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
        <button
          type="button"
          onClick={handleStartImport}
          disabled={!selectedFile || isUploading || task.isRunning}
          data-testid="start-csv-import-btn"
          style={{
            padding: "0.625rem 1.25rem",
            borderRadius: "6px",
            border: "none",
            background: !selectedFile || isUploading || task.isRunning ? "#94a3b8" : "#2563eb",
            color: "#ffffff",
            fontWeight: 600,
            fontSize: "0.875rem",
            cursor: !selectedFile || isUploading || task.isRunning ? "not-allowed" : "pointer",
          }}
        >
          {isUploading ? "Uploading..." : task.isRunning ? "Processing in Celery..." : "Start CSV Import"}
        </button>

        {(task.isCompleted || task.isFailed) && (
          <button
            type="button"
            onClick={() => {
              task.resetTask()
              setSelectedFile(null)
              if (fileInputRef.current) fileInputRef.current.value = ""
            }}
            data-testid="reset-csv-import-btn"
            style={{
              padding: "0.625rem 1rem",
              borderRadius: "6px",
              border: "1px solid var(--color-border, #cbd5e1)",
              background: "transparent",
              cursor: "pointer",
              fontSize: "0.875rem",
            }}
          >
            Clear / Import Another
          </button>
        )}
      </div>

      {/* Upload Error */}
      {uploadError && (
        <div
          role="alert"
          data-testid="csv-upload-error"
          style={{
            marginTop: "1rem",
            padding: "0.75rem",
            borderRadius: "6px",
            background: "#fef2f2",
            border: "1px solid #fecaca",
            color: "#b91c1c",
            fontSize: "0.875rem",
          }}
        >
          {uploadError}
        </div>
      )}

      {/* Celery Task Progress Section */}
      {task.status !== "IDLE" && (
        <div
          style={{
            marginTop: "1.25rem",
            padding: "1rem",
            borderRadius: "8px",
            background: "var(--color-background, #f8fafc)",
            border: "1px solid var(--color-border, #e2e8f0)",
          }}
          data-testid="csv-task-progress-section"
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "0.5rem",
            }}
          >
            <span
              style={{
                fontSize: "0.875rem",
                fontWeight: 600,
                color: "var(--color-text, #1e293b)",
              }}
            >
              Status:{" "}
              <span
                data-testid="csv-task-status-badge"
                style={{
                  display: "inline-block",
                  padding: "0.125rem 0.5rem",
                  borderRadius: "9999px",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  backgroundColor:
                    task.status === "SUCCESS"
                      ? "#dcfce7"
                      : task.status === "FAILURE"
                      ? "#fee2e2"
                      : "#dbeafe",
                  color:
                    task.status === "SUCCESS"
                      ? "#15803d"
                      : task.status === "FAILURE"
                      ? "#b91c1c"
                      : "#1d4ed8",
                }}
              >
                {task.status}
              </span>
            </span>

            <span
              data-testid="csv-task-percent"
              style={{
                fontSize: "0.875rem",
                fontWeight: 700,
                color: "var(--color-text, #0f172a)",
              }}
            >
              {task.percent}%
            </span>
          </div>

          {/* Progress Bar */}
          <div
            style={{
              width: "100%",
              height: "8px",
              borderRadius: "4px",
              backgroundColor: "var(--color-border, #e2e8f0)",
              overflow: "hidden",
              marginBottom: "0.75rem",
            }}
            data-testid="csv-progress-bar-track"
          >
            <div
              data-testid="csv-progress-bar-fill"
              style={{
                height: "100%",
                width: `${task.percent}%`,
                backgroundColor:
                  task.status === "SUCCESS"
                    ? "#16a34a"
                    : task.status === "FAILURE"
                    ? "#dc2626"
                    : "#2563eb",
                transition: "width 0.3s ease",
              }}
            />
          </div>

          <p
            data-testid="csv-task-message"
            style={{
              fontSize: "0.8125rem",
              color: "var(--color-text-muted, #475569)",
              margin: 0,
            }}
          >
            {task.message}
          </p>

          {/* Error Message */}
          {task.error && (
            <div
              role="alert"
              data-testid="csv-task-error-alert"
              style={{
                marginTop: "0.75rem",
                padding: "0.5rem 0.75rem",
                borderRadius: "6px",
                background: "#fef2f2",
                color: "#b91c1c",
                fontSize: "0.8125rem",
              }}
            >
              {task.error}
            </div>
          )}

          {/* Completed Metrics Summary */}
          {task.isCompleted && importResult && (
            <div
              style={{
                marginTop: "1rem",
                padding: "0.75rem",
                borderRadius: "6px",
                backgroundColor: "var(--color-surface, #ffffff)",
                border: "1px solid var(--color-border, #cbd5e1)",
              }}
              data-testid="csv-import-summary"
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
                  gap: "0.5rem",
                  marginBottom: "0.5rem",
                }}
              >
                <div style={{ textAlign: "center", padding: "0.5rem", background: "#f0fdf4", borderRadius: "6px" }}>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#16a34a" }} data-testid="imported-count">
                    {importResult.imported_count ?? 0}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#15803d" }}>Imported / Updated</div>
                </div>

                <div style={{ textAlign: "center", padding: "0.5rem", background: "#fef2f2", borderRadius: "6px" }}>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#dc2626" }} data-testid="failed-count">
                    {importResult.failed_count ?? 0}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#b91c1c" }}>Failed Rows</div>
                </div>

                <div style={{ textAlign: "center", padding: "0.5rem", background: "#f8fafc", borderRadius: "6px" }}>
                  <div style={{ fontSize: "1.25rem", fontWeight: 700, color: "#334155" }} data-testid="total-rows-count">
                    {importResult.total_rows ?? 0}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "#64748b" }}>Total Processed</div>
                </div>
              </div>

              {/* Row Failures Detail List */}
              {importResult.errors && importResult.errors.length > 0 && (
                <div style={{ marginTop: "0.75rem" }} data-testid="csv-errors-list">
                  <h4 style={{ fontSize: "0.8125rem", color: "#b91c1c", margin: "0 0 0.25rem 0" }}>
                    Row Validation Errors:
                  </h4>
                  <ul
                    style={{
                      margin: 0,
                      paddingLeft: "1.25rem",
                      fontSize: "0.75rem",
                      color: "#b91c1c",
                      maxHeight: "120px",
                      overflowY: "auto",
                    }}
                  >
                    {importResult.errors.map((err, i) => (
                      <li key={i}>
                        Row {err.row}: {err.reason} {err.name ? `(Product: ${err.name})` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
