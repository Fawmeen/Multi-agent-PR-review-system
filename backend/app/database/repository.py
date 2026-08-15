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
from app.database.models import ReviewModel, FindingModel, AgentEventModel
from app.models.review import Review
from app.models.findings import Finding


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
    
    async def list_reviews(self, limit: int = 20, offset: int = 0) -> Sequence[ReviewModel]:
        result = await self.session.execute(
            select(ReviewModel)
            .order_by(ReviewModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

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

    async def save_review_with_findings(
        self, 
        review: Review, 
        findings: list[Finding]
    ) -> ReviewModel:
        """
        Save a review and its findings in a single transaction.
        
        Converts Pydantic models to SQLAlchemy models and persists to database.
        
        Args:
            review: Review Pydantic model
            findings: List of Finding Pydantic models
            
        Returns:
            Persisted ReviewModel
            
        Note: Caller must handle session.commit() after calling this method.
        """
        # Convert Review Pydantic model to ReviewModel
        review_model = ReviewModel(
            id=review.id,
            repository=review.repository,
            pr_number=review.pr_number,
            commit_sha=review.commit_sha,
            status=review.status,
            workflow_run_id=review.workflow_run_id,
            summary=review.summary.model_dump() if review.summary else {},
            total_tokens_used=review.total_tokens_used,
            total_cost_usd=review.total_cost_usd,
            approved_by=review.approved_by,
            approved_at=review.approved_at,
            started_at=review.started_at,
            completed_at=review.completed_at,
        )
        
        # Add review to session
        self.session.add(review_model)
        await self.session.flush()
        
        # Convert Finding Pydantic models to FindingModel and add to session
        finding_models = []
        for finding in findings:
            finding_model = FindingModel(
                id=finding.id,
                review_id=review.id,
                agent=finding.agent,
                category=finding.category,
                severity=finding.severity,
                file_path=finding.file_path,
                line_start=finding.line_start,
                line_end=finding.line_end,
                title=finding.title,
                description=finding.description,
                suggestion=finding.suggestion,
                rule_reference=finding.rule_reference,
            )
            finding_models.append(finding_model)
            self.session.add(finding_model)
        
        await self.session.flush()
        
        return review_model


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


class EventRepository:
    """Handles insertions for observability events."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_events(self, events: list[dict]) -> None:
        """
        Log multiple raw agent events into the TimescaleDB hypertable.
        """
        if not events:
            return
            
        event_models = []
        for evt in events:
            # Provide defaults for fields missing from dict
            event_model = AgentEventModel(
                time=evt.get("time", datetime.now(timezone.utc)),
                event_type=evt.get("event_type", "llm_call"),
                agent_name=evt.get("agent_name"),
                workflow_run_id=evt.get("workflow_run_id"),
                tokens_used=evt.get("tokens_used", 0),
                duration_ms=evt.get("duration_ms"),
                extra_data=evt.get("extra_data", {})
            )
            event_models.append(event_model)
            
        self.session.add_all(event_models)
        # Flush is optional if commit is called later, but good practice
        await self.session.flush()