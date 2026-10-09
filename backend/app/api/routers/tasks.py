from typing import Any
from fastapi import APIRouter, Request
from celery.result import AsyncResult

from ...core.config import settings
from ...core.rate_limit import limiter
from ...schemas.schemas import TaskStatusResponse, TaskTriggerRequest
from ...tasks.celery_app import celery_app
from ...tasks.celery_tasks import sample_background_job_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/run")
@limiter.limit(settings.TASK_RATE_LIMIT)
def trigger_background_task(
    request: Request,
    data: TaskTriggerRequest | None = None,
) -> dict[str, Any]:
    steps = data.steps if data else 8
    delay = data.delay if data else 0.4
    name = data.name if data else "Sample Background Job"
    task = sample_background_job_task.delay(total_steps=steps, step_delay=delay)
    return {
        "success": True,
        "task_id": task.id,
        "name": name,
        "status": "PENDING",
        "message": f"Task '{name}' queued successfully",
    }


@router.get("/{task_id}", response_model=TaskStatusResponse)
@router.get("/{task_id}/status", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> dict[str, Any]:
    res = AsyncResult(task_id, app=celery_app)
    state = res.state

    if state == "PENDING":
        return {
            "task_id": task_id,
            "status": "PENDING",
            "percent": 0,
            "message": "Task queued in Redis, awaiting worker...",
            "result": None,
            "error": None,
        }
    elif state == "STARTED":
        return {
            "task_id": task_id,
            "status": "STARTED",
            "percent": 10,
            "message": "Celery worker started task execution.",
            "result": None,
            "error": None,
        }
    elif state == "PROGRESS":
        info = res.info or {}
        if isinstance(info, dict):
            percent = int(info.get("percent", 50))
            message = str(info.get("message", "Task in progress..."))
        else:
            percent = 50
            message = str(info)
        return {
            "task_id": task_id,
            "status": "PROGRESS",
            "percent": percent,
            "message": message,
            "result": info if isinstance(info, dict) else None,
            "error": None,
        }
    elif state == "SUCCESS":
        return {
            "task_id": task_id,
            "status": "SUCCESS",
            "percent": 100,
            "message": "Task completed successfully!",
            "result": res.result,
            "error": None,
        }
    elif state == "FAILURE":
        return {
            "task_id": task_id,
            "status": "FAILURE",
            "percent": 100,
            "message": "Task execution failed.",
            "result": None,
            "error": str(res.result),
        }
    else:
        return {
            "task_id": task_id,
            "status": state,
            "percent": 0,
            "message": f"Task state: {state}",
            "result": None,
            "error": None,
        }
