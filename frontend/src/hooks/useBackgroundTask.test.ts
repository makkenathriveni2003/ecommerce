import { describe, it, expect, vi } from "vitest"
import { renderHook, act } from "@testing-library/react"
import { useBackgroundTask } from "./useBackgroundTask"

describe("useBackgroundTask", () => {
  it("initializes with IDLE state and zero progress", () => {
    const { result } = renderHook(() => useBackgroundTask())
    expect(result.current.status).toBe("IDLE")
    expect(result.current.percent).toBe(0)
    expect(result.current.taskId).toBeNull()
    expect(result.current.isRunning).toBe(false)
  })

  it("triggers a task and polls status to completion", async () => {
    const onSuccess = vi.fn()
    const { result } = renderHook(() =>
      useBackgroundTask({
        pollInterval: 50,
        onSuccess,
      }),
    )

    await act(async () => {
      await result.current.startTask({ steps: 2, delay: 0.1, name: "Test Unit Task" })
    })

    expect(result.current.taskId).toBe("test-task-12345")
    expect(result.current.status).toBe("SUCCESS")
    expect(result.current.percent).toBe(100)
    expect(result.current.isCompleted).toBe(true)
    expect(onSuccess).toHaveBeenCalledTimes(1)
  })

  it("can reset back to IDLE state", async () => {
    const { result } = renderHook(() => useBackgroundTask())

    await act(async () => {
      await result.current.startTask()
    })
    expect(result.current.taskId).not.toBeNull()

    act(() => {
      result.current.resetTask()
    })

    expect(result.current.status).toBe("IDLE")
    expect(result.current.taskId).toBeNull()
    expect(result.current.percent).toBe(0)
  })
})
