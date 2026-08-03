"""
Standardized enums used across the entire system.
Every module imports from here, ensuring consistency.
"""
from enum import StrEnum


class FindingSeverity(StrEnum):
    """Severity level of a review finding."""
    CRITICAL = "critical"     # Must fix before merge — security vuln, broken logic
    HIGH = "high"             # Should fix — major code smell, performance issue
    MEDIUM = "medium"         # Nice to fix — style inconsistency, minor duplication
    LOW = "low"               # Optional — nitpick, suggestion
    INFO = "info"             # Informational only — no action needed


class FindingCategory(StrEnum):
    """Category of a review finding — maps to the four specialists."""
    SECURITY = "security"         # From security_agent
    CODE_QUALITY = "code_quality" # From quality_agent
    TESTING = "testing"           # From test_agent
    DOCUMENTATION = "documentation"  # From docs_agent


class ReviewStatus(StrEnum):
    """Overall status of a review."""
    PENDING = "pending"           # Workflow started, not all agents done
    AWAITING_APPROVAL = "awaiting_approval"  # All agents done, waiting for human
    APPROVED = "approved"         # Human approved the review
    DISPUTED = "disputed"         # Human disputed one or more findings
    POSTED = "posted"             # Review posted to GitHub
    FAILED = "failed"             # Review failed during processing


class ApprovalAction(StrEnum):
    """Actions a human can take on a finding."""
    APPROVE = "approve"
    DISPUTE = "dispute"
    ESCALATE = "escalate"


class AgentName(StrEnum):
    """Names of the four specialist agents."""
    SECURITY = "security_agent"
    QUALITY = "quality_agent"
    TEST = "test_agent"
    DOCS = "docs_agent"
    AGGREGATOR = "aggregator"


class WebhookEventType(StrEnum):
    """Supported GitHub webhook events."""
    PULL_REQUEST = "pull_request"
    PULL_REQUEST_REVIEW = "pull_request_review"
    PULL_REQUEST_REVIEW_COMMENT = "pull_request_review_comment"
    PUSH = "push"  # For future: check commits on push