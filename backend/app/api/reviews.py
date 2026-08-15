"""
Reviews API: exposes review data and findings.
"""
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any

from app.database.postgres import get_db_session
from app.database.repository import ReviewRepository, FindingRepository, EventRepository

router = APIRouter(prefix="/reviews", tags=["reviews"])

@router.get("/")
async def list_reviews(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    List all reviews with pagination.
    Returns basic review metadata and summaries.
    """
    repo = ReviewRepository(db)
    reviews = await repo.list_reviews(limit=limit, offset=offset)
    return {
        "reviews": [
            {
                "id": r.id,
                "repository": r.repository,
                "pr_number": r.pr_number,
                "commit_sha": r.commit_sha,
                "status": r.status,
                "workflow_run_id": r.workflow_run_id,
                "summary": r.summary,
                "total_tokens_used": r.total_tokens_used,
                "total_cost_usd": r.total_cost_usd,
                "started_at": r.started_at,
                "completed_at": r.completed_at,
            }
            for r in reviews
        ],
        "limit": limit,
        "offset": offset,
    }

@router.get("/{review_id}")
async def get_review_details(
    review_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Any:
    """
    Get detailed information about a specific review.
    Includes the review metadata, all associated findings, and agent events.
    """
    review_repo = ReviewRepository(db)
    finding_repo = FindingRepository(db)
    event_repo = EventRepository(db)
    
    review = await review_repo.get_by_id(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
        
    findings = await finding_repo.get_findings_by_review_id(review_id)
    events = await event_repo.get_events_by_review_id(review_id)
    
    return {
        "review": {
            "id": review.id,
            "repository": review.repository,
            "pr_number": review.pr_number,
            "commit_sha": review.commit_sha,
            "status": review.status,
            "summary": review.summary,
            "total_tokens_used": review.total_tokens_used,
            "total_cost_usd": review.total_cost_usd,
            "approved_by": review.approved_by,
            "approved_at": review.approved_at,
            "started_at": review.started_at,
            "completed_at": review.completed_at,
        },
        "findings": [
            {
                "id": f.id,
                "agent": f.agent,
                "category": f.category,
                "severity": f.severity,
                "file_path": f.file_path,
                "line_start": f.line_start,
                "line_end": f.line_end,
                "title": f.title,
                "description": f.description,
                "suggestion": f.suggestion,
                "is_approved": f.is_approved,
                "is_disputed": f.is_disputed,
            }
            for f in findings
        ],
        "events": [
            {
                "time": e.time,
                "event_type": e.event_type,
                "agent_name": e.agent_name,
                "tokens_used": e.tokens_used,
                "duration_ms": e.duration_ms,
                "extra_data": e.extra_data,
            }
            for e in events
        ]
    }
