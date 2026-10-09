import { useCallback, useEffect, useRef, useState } from "react"
import { fetchTaskStatus, triggerBackgroundTask } from "../services/taskService"
import type { TaskStatusResponse, TaskTriggerParams } from "../services/taskService"

export interface UseBackgroundTaskOptions {
  pollInterval?: number
  onSuccess?: (res: TaskStatusResponse) => void
  onError?: (error: string) => void
}

export function useBackgroundTask(options: UseBackgroundTaskOptions = {}) {
  const { pollInterval = 800, onSuccess, onError } = options

  const [taskId, setTaskId] = useState<string | null>(null)
  const [status, setStatus] = useState<string>("IDLE")
  const [percent, setPercent] = useState<number>(0)
  const [message, setMessage] = useState<string>("")
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState<boolean>(false)

  const onSuccessRef = useRef(onSuccess)
  const onErrorRef = useRef(onError)

  useEffect(() => {
    onSuccessRef.current = onSuccess
    onErrorRef.current = onError
  }, [onSuccess, onError])

  const pollTimerRef = useRef<number | null>(null)
  const pollStatusRef = useRef<(id: string) => Promise<void>>(async () => {})

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current !== null) {
      window.clearTimeout(pollTimerRef.current)
      pollTimerRef.current = null
    }
    setIsPolling(false)
  }, [])

  const pollStatus = useCallback(
    async (id: string) => {
      try {
        const data = await fetchTaskStatus(id)
        setStatus(data.status)
        setPercent(data.percent)
        setMessage(data.message)

        if (data.status === "SUCCESS") {
          setResult(data.result ?? null)
          setError(null)
          stopPolling()
          if (onSuccessRef.current) {
            onSuccessRef.current(data)
          }
          return
        }

        if (data.status === "FAILURE") {
          const errMsg = data.error || data.message || "Task failed"
          setError(errMsg)
          stopPolling()
          if (onErrorRef.current) {
            onErrorRef.current(errMsg)
          }
          return
        }

        // Continue polling if still running or queued
        pollTimerRef.current = window.setTimeout(() => {
          void pollStatusRef.current(id)
        }, pollInterval)
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Failed to query task status"
        setError(errMsg)
        stopPolling()
        if (onErrorRef.current) {
          onErrorRef.current(errMsg)
        }
      }
    },
    [pollInterval, stopPolling],
  )

  useEffect(() => {
    pollStatusRef.current = pollStatus
  }, [pollStatus])

  const trackTask = useCallback(
    (id: string) => {
      stopPolling()
      setTaskId(id)
      setStatus("PENDING")
      setPercent(0)
      setMessage("Task submitted, checking status...")
      setError(null)
      setResult(null)
      setIsPolling(true)
      void pollStatusRef.current(id)
    },
    [stopPolling],
  )

  const startTask = useCallback(
    async (params?: TaskTriggerParams, token?: string) => {
      stopPolling()
      setError(null)
      setResult(null)
      setStatus("PENDING")
      setPercent(0)
      setMessage("Submitting task to Celery queue...")
      setIsPolling(true)

      try {
        const resp = await triggerBackgroundTask(params, token)
        setTaskId(resp.task_id)
        setMessage(resp.message)
        void pollStatusRef.current(resp.task_id)
        return resp.task_id
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Failed to start background task"
        setError(errMsg)
        setStatus("FAILURE")
        setIsPolling(false)
        if (onErrorRef.current) {
          onErrorRef.current(errMsg)
        }
        return null
      }
    },
    [stopPolling],
  )

  const resetTask = useCallback(() => {
    stopPolling()
    setTaskId(null)
    setStatus("IDLE")
    setPercent(0)
    setMessage("")
    setResult(null)
    setError(null)
  }, [stopPolling])

  useEffect(() => {
    return () => {
      if (pollTimerRef.current !== null) {
        window.clearTimeout(pollTimerRef.current)
      }
    }
  }, [])

  return {
    taskId,
    status,
    percent,
    message,
    result,
    error,
    isPolling,
    isRunning: status === "STARTED" || status === "PROGRESS" || status === "PENDING",
    isCompleted: status === "SUCCESS",
    isFailed: status === "FAILURE",
    startTask,
    trackTask,
    resetTask,
  }
}
