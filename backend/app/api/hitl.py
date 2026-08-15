"""
Human-in-the-Loop API endpoints for reviewing findings.
"""
from typing import List

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, status
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from datetime import datetime

from app.database.postgres import get_db_session
from app.hitl.queue import (
    get_pending_findings,
    approve_finding as queue_approve_finding,
    dispute_finding as queue_dispute_finding,
    bulk_approve_review as queue_bulk_approve_review,
)

router = APIRouter(prefix="/hitl", tags=["hitl"])

class FindingResponse(BaseModel):
    id: str
    review_id: str
    agent: str
    category: str
    severity: str
    file_path: str
    line_start: int | None
    line_end: int | None
    title: str
    description: str
    suggestion: str | None
    rule_reference: str | None
    is_approved: bool
    is_disputed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class BulkApproveRequest(BaseModel):
    approved_by: str

@router.get("/reviews/{review_id}/findings/pending", response_model=List[FindingResponse])
async def list_pending_findings(review_id: str, db: AsyncSession = Depends(get_db_session)):
    """Get all unapproved findings for a specific review."""
    findings = await get_pending_findings(db, review_id)
    return findings

@router.post("/findings/{finding_id}/approve", status_code=status.HTTP_200_OK)
async def approve_finding(finding_id: str, db: AsyncSession = Depends(get_db_session)):
    """Approve a specific finding."""
    await queue_approve_finding(db, finding_id)
    return {"status": "success", "message": f"Finding {finding_id} approved"}

@router.post("/findings/{finding_id}/dispute", status_code=status.HTTP_200_OK)
async def dispute_finding(finding_id: str, db: AsyncSession = Depends(get_db_session)):
    """Dispute (reject) a specific finding."""
    await queue_dispute_finding(db, finding_id)
    return {"status": "success", "message": f"Finding {finding_id} disputed"}

@router.post("/reviews/{review_id}/approve", status_code=status.HTTP_200_OK)
async def bulk_approve_review(
    review_id: str, 
    request: BulkApproveRequest, 
    db: AsyncSession = Depends(get_db_session)
):
    """Bulk approve all findings and the review itself."""
    await queue_bulk_approve_review(db, review_id, request.approved_by)
    return {"status": "success", "message": f"Review {review_id} approved by {request.approved_by}"}
