"""
Repository classes for data access.
Encapsulates all SQL queries; routes call these methods.
"""
from typing import Sequence
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy import select, update
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import ReviewModel, FindingModel


class ReviewRepository:
    """Handles CRUD for reviews."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, review: ReviewModel) -> ReviewModel:
        self.session.add(review)
        await self.session.flush()  # Get ID without committing transaction
        return review

    async def get_by_id(self, review_id: str) -> ReviewModel | None:
        return await self.session.get(ReviewModel, review_id)

    async def update_status(self, review_id: str, status: str) -> None:
        stmt = (
            update(ReviewModel)
            .where(ReviewModel.id == review_id)
            .values(status=status, updated_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    async def add_findings(self, review_id: str, findings: list[FindingModel]) -> None:
        self.session.add_all(findings)
        await self.session.flush()

    async def update_approval(self, review_id: str, approved_by: str) -> None:
        now = datetime.now(timezone.utc)
        stmt = (
            update(ReviewModel)
            .where(ReviewModel.id == review_id)
            .values(status="approved", approved_by=approved_by, approved_at=now, updated_at=now)
        )
        await self.session.execute(stmt)

    async def list_reviews(self, limit: int = 20) -> Sequence[ReviewModel]:
        result = await self.session.execute(
            select(ReviewModel).order_by(ReviewModel.created_at.desc()).limit(limit)
        )
        return result.scalars().all()


class FindingRepository:
    """Handles HITL operations on findings."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_pending_approvals(self, review_id: str) -> Sequence[FindingModel]:
        result = await self.session.execute(
            select(FindingModel)
            .where(FindingModel.review_id == review_id, FindingModel.is_approved == False)
            .order_by(FindingModel.created_at)
        )
        return result.scalars().all()

    async def approve_finding(self, finding_id: str) -> None:
        stmt = (
            update(FindingModel)
            .where(FindingModel.id == finding_id)
            .values(is_approved=True)
        )
        await self.session.execute(stmt)

    async def dispute_finding(self, finding_id: str) -> None:
        stmt = (
            update(FindingModel)
            .where(FindingModel.id == finding_id)
            .values(is_disputed=True)
        )
        await self.session.execute(stmt)

    async def bulk_approve(self, review_id: str) -> None:
        stmt = (
            update(FindingModel)
            .where(FindingModel.review_id == review_id)
            .values(is_approved=True)
        )
        await self.session.execute(stmt)