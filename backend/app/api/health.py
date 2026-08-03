"""
Health check endpoint — used by monitoring, Docker, etc.
"""
# pyrefly: ignore [missing-import]
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Returns 200 if the service is running.
    Can be extended to check database, Redis, etc.
    """
    return {
        "status": "ok",
        "service": "ai-pr-review-agent",
        "version": "0.1.0"
    }