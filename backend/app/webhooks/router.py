"""
Route validated webhooks to the job queue.
Uses ARQ (async task queue backed by Redis) for background processing.
"""
# pyrefly: ignore [missing-import]
from arq import create_pool
# pyrefly: ignore [missing-import]
from arq.connections import RedisSettings
from app.core.config import get_settings
from app.models.webhook import WebhookPayload
from app.core.exceptions import WebhookError
from urllib.parse import urlparse

settings = get_settings()

# We'll create a single Redis pool (lazy initialization).
_redis_pool = None


def _parse_redis_url(url: str) -> RedisSettings:
    """
    Parse a Redis URL into ARQ's RedisSettings.
    
    Handles formats like:
    - redis://user:pass@host:port/db
    - rediss://:pass@host:port  (Upstash TLS)
    
    Returns a RedisSettings object ARQ understands.
    """
    parsed = urlparse(url)
    
    # Extract password (Upstash puts it in the password field, sometimes username is empty)
    password = parsed.password
    
    # Build RedisSettings
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=password,
        ssl=(parsed.scheme == "rediss"),  # TLS if rediss://
    )


async def get_redis_pool():
    """
    Returns a shared Redis connection pool.
    Created once and reused across requests.
    """
    global _redis_pool
    if _redis_pool is None:
        redis_settings = _parse_redis_url(settings.upstash_redis_url)
        _redis_pool = await create_pool(redis_settings)
    return _redis_pool


async def route_webhook(payload: WebhookPayload) -> str:
    """
    Validate the event type and enqueue a review job.

    Args:
        payload: Validated webhook payload.

    Returns:
        job_id: The ARQ job ID for tracking.
    """
    # Only process pull_request events for now.
    if payload.event_type != "pull_request":
        raise WebhookError(f"Unsupported event type: {payload.event_type}")

    if not payload.pull_request:
        raise WebhookError("Pull request data missing")

    # Enqueue a task to the 'review_queue' queue.
    pool = await get_redis_pool()
    job = await pool.enqueue_job(
        "start_review_workflow",  # function name in worker.py
        payload.model_dump(mode="json"),  # pass the full payload as dict
        _queue_name="review_queue",
    )
    return job.job_id