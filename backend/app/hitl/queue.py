"""
Human-in-the-Loop (HITL) Queue Module.
Provides business logic for reviewing and approving agent findings.
"""
from typing import Sequence
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.repository import FindingRepository, ReviewRepository
from app.database.models import FindingModel

async def get_pending_findings(session: AsyncSession, review_id: str) -> Sequence[FindingModel]:
    """Retrieve all pending (unapproved) findings for a given review."""
    repo = FindingRepository(session)
    return await repo.get_pending_approvals(review_id)

async def approve_finding(session: AsyncSession, finding_id: str) -> None:
    """Mark a single finding as approved."""
    repo = FindingRepository(session)
    await repo.approve_finding(finding_id)

async def dispute_finding(session: AsyncSession, finding_id: str) -> None:
    """Mark a single finding as disputed."""
    repo = FindingRepository(session)
    await repo.dispute_finding(finding_id)

async def bulk_approve_review(session: AsyncSession, review_id: str, approved_by: str) -> None:
    """Approve all findings for a review and mark the review itself as approved."""
    finding_repo = FindingRepository(session)
    review_repo = ReviewRepository(session)
    
    await finding_repo.bulk_approve(review_id)
    await review_repo.update_approval(review_id, approved_by)
