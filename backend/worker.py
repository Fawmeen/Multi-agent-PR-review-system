"""
ARQ background worker for the AI-PR Review Agent.
Processes jobs from the Redis queue.

Run with: arq worker.py
"""
import asyncio
# pyrefly: ignore [missing-import]
from arq.connections import RedisSettings
from app.core.config import get_settings
from urllib.parse import urlparse

settings = get_settings()


def _parse_redis_url(url: str) -> RedisSettings:
    """
    Parse a Redis URL into ARQ's RedisSettings.
    """
    parsed = urlparse(url)
    password = parsed.password
    
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=password,
        ssl=(parsed.scheme == "rediss"),
    )


async def start_review_workflow(ctx, payload: dict):
    """
    Called by ARQ when a job is enqueued.
    
    In Phase 4/5/8, this will:
    - Fetch the PR diff from GitHub
    - Run the LangGraph orchestration (4 agents + aggregator)
    - Store findings in Tiger
    - Emit agent_events for tracing/cost tracking
    """
    print(f"🔔 Job received: PR #{payload.get('pull_request', {}).get('number')}")
    print(f"   Repository: {payload.get('repository', {}).get('full_name')}")
    print(f"   Action: {payload.get('action')}")
    
    # TODO: Implement full orchestrator pipeline
    await asyncio.sleep(1)
    
    return {
        "status": "completed",
        "message": "Review workflow would run here (Phase 4, 5, 8)"
    }


# Worker configuration
class WorkerSettings:
    """
    Settings for ARQ worker.
    """
    functions = [start_review_workflow]
    redis_settings = _parse_redis_url(settings.upstash_redis_url)
    queue_name = "review_queue"
    max_jobs = 10
    job_timeout = 300
    poll_delay = 0.5