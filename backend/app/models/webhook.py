"""
GitHub webhook payload models.
We only parse the fields we need; Pydantic ignores the rest.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.enums import WebhookEventType


class RepositoryInfo(BaseModel):
    """Relevant fields from the repository object."""
    full_name: str = Field(..., examples=["org/repo"])
    owner: str = Field(..., description="Owner login or org name")
    name: str = Field(..., description="Repo name")
    clone_url: str | None = None
    default_branch: str = "main"


class PullRequestInfo(BaseModel):
    """Relevant fields from the pull_request object."""
    number: int = Field(..., ge=1)
    title: str
    body: str | None = None
    state: str  # "open", "closed", "merged"
    html_url: str
    diff_url: str
    base_ref: str = Field(..., description="Target branch, e.g., 'main'")
    head_ref: str = Field(..., description="Source branch, e.g., 'feature/login'")
    base_sha: str
    head_sha: str
    user_login: str = Field(..., description="PR author's username")


class WebhookPayload(BaseModel):
    """
    Parsed GitHub webhook payload.
    We extract only what the orchestrator needs.
    """
    
    # Event type from the X-GitHub-Event header (set by the router, not in the JSON)
    event_type: WebhookEventType
    
    # Action from the JSON body: "opened", "synchronize", "closed", etc.
    action: str
    
    # Repository info
    repository: RepositoryInfo
    
    # PR info (only present for pull_request events)
    pull_request: PullRequestInfo | None = None
    
    # Timestamp from GitHub headers
    delivery_id: str | None = Field(
        None,
        description="X-GitHub-Delivery header — unique per event"
    )
    
    # Raw payload for audit/debugging
    raw_payload: dict = Field(
        default_factory=dict,
        description="Full original payload for audit trail"
    )
    
    received_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When our server received this webhook"
    )