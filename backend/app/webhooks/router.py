"""
Route validated webhooks to the job queue.
Uses ARQ (async task queue backed by Redis) for background processing.
"""
# pyrefly: ignore [missing-import]
from arq import create_pool
from app.core.config import get_settings
from app.models.webhook import WebhookPayload
from app.core.exceptions import WebhookError

settings = get_settings()

# We'll create a single Redis pool (lazy initialization).
_redis_pool = None

async def get_redis_pool():
    """
    Returns a shared Redis connection pool.
    Created once and reused across requests.
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = await create_pool(
            settings_=settings.upstash_redis_url
        )
    return _redis_pool


async def route_webhook(payload: WebhookPayload) -> str:
    """
    Validate the event type and enqueue a review job.

    Returns:
        job_id: The ARQ job ID for tracking.
    """
    # Only process pull_request events for now.
    if payload.event_type != "pull_request":
        raise WebhookError(f"Unsupported event type: {payload.event_type}")

    if not payload.pull_request:
        raise WebhookError("Pull request data missing")

    # Enqueue a task to the 'review_queue' queue.
    # The task name 'start_review_workflow' must match the worker's function.
    pool = await get_redis_pool()
    job = await pool.enqueue_job(
        "start_review_workflow",  # function name (we'll define it later in worker.py)
        payload.model_dump(mode="json"),   # pass the full payload as dict
        _queue_name="review_queue",
    )
    return job.job_id