import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { TaskProgressCard } from "./TaskProgressCard"

describe("TaskProgressCard", () => {
  it("renders nothing when status is IDLE and taskId is null", () => {
    const { container } = render(
      <TaskProgressCard
        taskId={null}
        status="IDLE"
        percent={0}
        message=""
      />
    )
    expect(container.firstChild).toBeNull()
  })

  it("displays Pending state correctly", () => {
    render(
      <TaskProgressCard
        title="Pending Job"
        taskId="task-abc-123"
        status="PENDING"
        percent={0}
        message="Queued in Redis"
      />
    )
    expect(screen.getByText("Pending Job")).toBeInTheDocument()
    expect(screen.getByTestId("task-status-badge")).toHaveTextContent("Queued / Pending")
    expect(screen.getByTestId("task-message")).toHaveTextContent("Queued in Redis")
    expect(screen.getByTestId("task-percent")).toHaveTextContent("0%")
  })

  it("displays Running / In Progress state with progress bar width", () => {
    render(
      <TaskProgressCard
        title="Active Job"
        taskId="task-def-456"
        status="PROGRESS"
        percent={65}
        message="Processing step 3..."
      />
    )
    expect(screen.getByTestId("task-status-badge")).toHaveTextContent("In Progress (65%)")
    expect(screen.getByTestId("task-percent")).toHaveTextContent("65%")
    const progressBar = screen.getByTestId("task-progress-bar")
    expect(progressBar).toHaveStyle({ width: "65%" })
  })

  it("displays Completed state and result alert", () => {
    render(
      <TaskProgressCard
        title="Completed Job"
        taskId="task-ghi-789"
        status="SUCCESS"
        percent={100}
        message="Finished successfully"
        result={{ items: 42 }}
      />
    )
    expect(screen.getByTestId("task-status-badge")).toHaveTextContent("Completed")
    expect(screen.getByTestId("task-progress-bar")).toHaveStyle({ width: "100%" })
    expect(screen.getByTestId("task-result-alert")).toBeInTheDocument()
  })

  it("displays Failed state and error details", () => {
    render(
      <TaskProgressCard
        title="Failed Job"
        taskId="task-jkl-012"
        status="FAILURE"
        percent={100}
        message="Fatal error"
        error="Network timeout reaching remote resource"
      />
    )
    expect(screen.getByTestId("task-status-badge")).toHaveTextContent("Failed")
    expect(screen.getByTestId("task-error-alert")).toHaveTextContent("Network timeout reaching remote resource")
  })
})
