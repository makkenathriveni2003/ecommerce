import { jsonRequest, requestJson } from "./apiClient"

export interface TaskTriggerParams {
  steps?: number
  delay?: number
  name?: string
}

export interface TaskStatusResponse {
  task_id: string
  status: "PENDING" | "STARTED" | "PROGRESS" | "SUCCESS" | "FAILURE" | string
  percent: number
  message: string
  result?: Record<string, unknown> | null
  error?: string | null
}

export async function triggerBackgroundTask(
  params?: TaskTriggerParams,
  token?: string,
): Promise<{ success: boolean; task_id: string; name: string; status: string; message: string }> {
  return (await requestJson(
    "/tasks/run",
    jsonRequest(params ?? { steps: 8, delay: 0.4, name: "Sample Background Job" }, token, "POST"),
  )) as { success: boolean; task_id: string; name: string; status: string; message: string }
}

export async function fetchTaskStatus(
  taskId: string,
): Promise<TaskStatusResponse> {
  return (await requestJson(`/tasks/${encodeURIComponent(taskId)}/status`)) as TaskStatusResponse
}
