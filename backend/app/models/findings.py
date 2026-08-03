"""
Finding model — the atomic unit of a review.
Every agent produces zero or more Findings.
"""
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.models.enums import FindingSeverity, FindingCategory, AgentName


class Finding(BaseModel):
    """
    A single actionable finding from a review agent.
    
    This is the contract (ADR-002) that every agent must fulfill.
    """
    
    # Unique identifier — generated at creation
    id: str = Field(
        default_factory=lambda: f"finding_{datetime.now(timezone.utc).timestamp()}",
        description="Unique finding ID"
    )
    
    # Which agent produced this
    agent: AgentName = Field(
        ...,
        description="The specialist agent that produced this finding"
    )
    
    # What the finding is about
    category: FindingCategory = Field(
        ...,
        description="Category of the finding"
    )
    
    # How serious it is
    severity: FindingSeverity = Field(
        ...,
        description="Severity level"
    )
    
    # Where in the code
    file_path: str = Field(
        ...,
        description="Path to the file with the issue",
        examples=["src/auth/login.py"]
    )
    line_start: int | None = Field(
        None,
        ge=1,
        description="Starting line number (1-indexed)"
    )
    line_end: int | None = Field(
        None,
        ge=1,
        description="Ending line number (inclusive)"
    )
    
    # What's wrong
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Short title of the finding",
        examples=["SQL Injection vulnerability in user input"]
    )
    
    # Detailed explanation
    description: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed explanation of the issue"
    )
    
    # Suggested fix
    suggestion: str | None = Field(
        None,
        max_length=2000,
        description="Suggested code change or fix"
    )
    
    # Reference to coding standard or rule
    rule_reference: str | None = Field(
        None,
        description="Reference to a rule or standard",
        examples=["OWASP Top 10 A03:2021", "PEP 8 E501"]
    )
    
    # When it was created
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the finding was created"
    )
    
    class Config:
        """Pydantic model configuration."""
        use_enum_values = True  # Serialize enums as their string values
        json_schema_extra = {
            "example": {
                "id": "finding_1703123456.789",
                "agent": "security_agent",
                "category": "security",
                "severity": "critical",
                "file_path": "src/auth/login.py",
                "line_start": 42,
                "line_end": 45,
                "title": "SQL Injection in login query",
                "description": "User input is directly concatenated into SQL query without parameterization.",
                "suggestion": "Use parameterized queries with sqlalchemy.text() and bound parameters.",
                "rule_reference": "OWASP Top 10 A03:2021 - Injection",
                "created_at": "2024-12-20T10:30:00Z"
            }
        }