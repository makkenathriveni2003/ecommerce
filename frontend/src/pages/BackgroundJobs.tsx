import React, { useState } from "react"
import { useBackgroundTask } from "../hooks/useBackgroundTask"
import { TaskProgressCard } from "../components/TaskProgressCard"

export const BackgroundJobs: React.FC = () => {
  const [steps, setSteps] = useState<number>(6)
  const [delay, setDelay] = useState<number>(0.5)
  const [jobName, setJobName] = useState<string>("Sample Async Task")

  const task = useBackgroundTask({
    pollInterval: 600,
  })

  const handleStartTask = async (e: React.FormEvent) => {
    e.preventDefault()
    await task.startTask({
      steps,
      delay,
      name: jobName,
    })
  }

  return (
    <div
      style={{
        maxWidth: "900px",
        margin: "0 auto",
        padding: "2rem 1rem",
        minHeight: "75vh",
      }}
      data-testid="background-jobs-page"
    >
      <div style={{ marginBottom: "2rem" }}>
        <h1
          style={{
            fontSize: "1.875rem",
            fontWeight: 700,
            color: "var(--color-text, #0f172a)",
            marginBottom: "0.5rem",
          }}
        >
          Celery Background Jobs
        </h1>
        <p style={{ color: "var(--color-text-muted, #64748b)", margin: 0 }}>
          Trigger, monitor, and inspect asynchronous background tasks executed by Celery and Redis.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: "1.5rem",
          marginBottom: "2rem",
        }}
      >
        {/* Task Trigger Card */}
        <div
          style={{
            border: "1px solid var(--color-border, #e2e8f0)",
            borderRadius: "12px",
            padding: "1.5rem",
            background: "var(--color-surface, #ffffff)",
            boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
          }}
        >
          <h2
            style={{
              fontSize: "1.25rem",
              fontWeight: 600,
              marginBottom: "1rem",
              color: "var(--color-text, #1e293b)",
            }}
          >
            Launch Background Task
          </h2>

          <form onSubmit={handleStartTask}>
            <div style={{ marginBottom: "1rem" }}>
              <label
                htmlFor="job-name-input"
                style={{
                  display: "block",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  marginBottom: "0.25rem",
                  color: "var(--color-text, #334155)",
                }}
              >
                Task Description
              </label>
              <input
                id="job-name-input"
                type="text"
                value={jobName}
                onChange={(e) => setJobName(e.target.value)}
                disabled={task.isRunning}
                style={{
                  width: "100%",
                  padding: "0.5rem 0.75rem",
                  borderRadius: "6px",
                  border: "1px solid var(--color-border, #cbd5e1)",
                  background: "var(--color-surface, #fff)",
                  color: "var(--color-text, #0f172a)",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "1rem",
                marginBottom: "1.25rem",
              }}
            >
              <div>
                <label
                  htmlFor="steps-input"
                  style={{
                    display: "block",
                    fontSize: "0.875rem",
                    fontWeight: 500,
                    marginBottom: "0.25rem",
                    color: "var(--color-text, #334155)",
                  }}
                >
                  Steps Count
                </label>
                <select
                  id="steps-input"
                  value={steps}
                  onChange={(e) => setSteps(Number(e.target.value))}
                  disabled={task.isRunning}
                  style={{
                    width: "100%",
                    padding: "0.5rem 0.75rem",
                    borderRadius: "6px",
                    border: "1px solid var(--color-border, #cbd5e1)",
                    background: "var(--color-surface, #fff)",
                    color: "var(--color-text, #0f172a)",
                  }}
                >
                  <option value={4}>4 Steps (Quick)</option>
                  <option value={6}>6 Steps</option>
                  <option value={10}>10 Steps (Standard)</option>
                  <option value={15}>15 Steps (Long)</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="delay-input"
                  style={{
                    display: "block",
                    fontSize: "0.875rem",
                    fontWeight: 500,
                    marginBottom: "0.25rem",
                    color: "var(--color-text, #334155)",
                  }}
                >
                  Step Delay (sec)
                </label>
                <select
                  id="delay-input"
                  value={delay}
                  onChange={(e) => setDelay(Number(e.target.value))}
                  disabled={task.isRunning}
                  style={{
                    width: "100%",
                    padding: "0.5rem 0.75rem",
                    borderRadius: "6px",
                    border: "1px solid var(--color-border, #cbd5e1)",
                    background: "var(--color-surface, #fff)",
                    color: "var(--color-text, #0f172a)",
                  }}
                >
                  <option value={0.2}>0.2s (Fast)</option>
                  <option value={0.5}>0.5s (Moderate)</option>
                  <option value={1.0}>1.0s (Slow)</option>
                </select>
              </div>
            </div>

            <button
              type="submit"
              disabled={task.isRunning}
              data-testid="trigger-task-btn"
              style={{
                width: "100%",
                padding: "0.75rem 1rem",
                borderRadius: "8px",
                border: "none",
                background: task.isRunning ? "#94a3b8" : "var(--color-primary, #2563eb)",
                color: "#ffffff",
                fontWeight: 600,
                cursor: task.isRunning ? "not-allowed" : "pointer",
                transition: "background-color 0.2s",
              }}
            >
              {task.isRunning ? "Task Running..." : "Queue Celery Task"}
            </button>
          </form>
        </div>

        {/* Task Lifecycle Architecture Card */}
        <div
          style={{
            border: "1px solid var(--color-border, #e2e8f0)",
            borderRadius: "12px",
            padding: "1.5rem",
            background: "var(--color-surface, #ffffff)",
            boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05)",
          }}
        >
          <h2
            style={{
              fontSize: "1.25rem",
              fontWeight: 600,
              marginBottom: "1rem",
              color: "var(--color-text, #1e293b)",
            }}
          >
            Celery Lifecycle Flow
          </h2>
          <div
            style={{
              fontSize: "0.85rem",
              lineHeight: 1.6,
              color: "var(--color-text-muted, #475569)",
            }}
          >
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <span style={{ fontWeight: 700, color: "#2563eb" }}>1.</span>
              <span><strong>Trigger:</strong> React calls <code>POST /tasks/run</code> without blocking.</span>
            </div>
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <span style={{ fontWeight: 700, color: "#2563eb" }}>2.</span>
              <span><strong>Queue:</strong> FastAPI delegates task to Redis broker & returns task UUID.</span>
            </div>
            <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.5rem" }}>
              <span style={{ fontWeight: 700, color: "#2563eb" }}>3.</span>
              <span><strong>Worker:</strong> Celery worker picks task from Redis & updates progress state.</span>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <span style={{ fontWeight: 700, color: "#2563eb" }}>4.</span>
              <span><strong>Poll:</strong> React polls <code>GET /tasks/{'{id}'}/status</code> until SUCCESS/FAILURE.</span>
            </div>
          </div>
        </div>
      </div>

      {/* Real-Time Task Progress Card */}
      {task.taskId && (
        <TaskProgressCard
          title={jobName}
          taskId={task.taskId}
          status={task.status}
          percent={task.percent}
          message={task.message}
          result={task.result}
          error={task.error}
          onReset={task.resetTask}
        />
      )}
    </div>
  )
}
