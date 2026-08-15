"""
SQLAlchemy ORM models for the PR review agent.
Maps directly to the Tiger database tables.
"""
from datetime import datetime, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, BigInteger, Index
)
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import JSONB
# pyrefly: ignore [missing-import]
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class ReviewModel(Base):
    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    repository: Mapped[str] = mapped_column(String, nullable=False)
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    total_tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    workflow_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to findings
    findings: Mapped[list["FindingModel"]] = relationship(
        "FindingModel", back_populates="review", cascade="all, delete-orphan"
    )


class FindingModel(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    review_id: Mapped[str] = mapped_column(String, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    agent: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    line_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    line_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_reference: Mapped[str | None] = mapped_column(String, nullable=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_disputed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationship back to review
    review: Mapped["ReviewModel"] = relationship("ReviewModel", back_populates="findings")


class CodeChunkModel(Base):
    __tablename__ = "code_chunks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    repository: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Special indexes handled in migration


class AgentEventModel(Base):
    __tablename__ = "agent_events"
    # Hypertable — no primary key in the traditional sense
    # We'll use a composite key if needed, but TimescaleDB handles it.
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String, nullable=True)
    workflow_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, default=dict)