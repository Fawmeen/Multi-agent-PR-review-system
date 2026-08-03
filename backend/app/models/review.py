"""
Review model — the final output of the multi-agent pipeline.
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.models.enums import ReviewStatus
from app.models.findings import Finding


class ReviewSummary(BaseModel):
    """Aggregated statistics about a review."""
    total_findings: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    by_category: dict[str, int] = Field(default_factory=dict)
    by_agent: dict[str, int] = Field(default_factory=dict)
    files_affected: int = 0


class Review(BaseModel):
    """
    The complete review output from the multi-agent system.
    This is what gets stored in Tiger and displayed on the dashboard.
    """
    
    # Unique review ID
    id: str = Field(
        default_factory=lambda: f"review_{datetime.now(timezone.utc).timestamp()}"
    )
    
    # Link to the PR
    repository: str
    pr_number: int
    commit_sha: str | None = None
    
    # The findings from all agents
    findings: list[Finding] = Field(default_factory=list)
    
    # Overall status
    status: ReviewStatus = ReviewStatus.PENDING
    
    # Summary statistics (computed after aggregation)
    summary: ReviewSummary = Field(default_factory=ReviewSummary)
    
    # Workflow metadata
    workflow_run_id: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None
    
    # Cost tracking
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    per_agent_tokens: dict[str, int] = Field(default_factory=dict)
    
    # Human interaction
    approved_by: str | None = None
    approved_at: datetime | None = None
    disputed_findings: list[str] = Field(
        default_factory=list,
        description="List of finding IDs that were disputed"
    )
    
    def compute_summary(self):
        """Compute the summary from findings. Called after aggregation."""
        self.summary = ReviewSummary(
            total_findings=len(self.findings),
            critical=sum(1 for f in self.findings if f.severity == "critical"),
            high=sum(1 for f in self.findings if f.severity == "high"),
            medium=sum(1 for f in self.findings if f.severity == "medium"),
            low=sum(1 for f in self.findings if f.severity == "low"),
            info=sum(1 for f in self.findings if f.severity == "info"),
            by_category=self._count_by("category"),
            by_agent=self._count_by("agent"),
            files_affected=len(set(f.file_path for f in self.findings)),
        )
    
    def _count_by(self, field: str) -> dict[str, int]:
        """Count findings grouped by a field."""
        counts: dict[str, int] = {}
        for finding in self.findings:
            value = getattr(finding, field)
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    class Config:
        use_enum_values = True