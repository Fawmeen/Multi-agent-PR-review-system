"""
LangGraph state definition for the multi-agent review workflow.
"""
from typing import Annotated
from pydantic import BaseModel, Field
from app.models.findings import Finding


class ReviewState(BaseModel):
    """
    Shared state passed between all agents in the LangGraph workflow.
    
    Each agent reads from this state and updates the findings list.
    LangGraph merges updates automatically using the Annotated[list] pattern.
    """
    
    # PR metadata
    repository: str = Field(..., description="Repository name (owner/repo)")
    pr_number: int = Field(..., description="Pull request number")
    commit_sha: str | None = Field(None, description="Commit SHA (if available)")
    
    # The PR diff (input to all agents)
    diff: str = Field(..., description="Unified diff of the PR")
    
    # Workflow tracking
    workflow_run_id: str = Field(..., description="Unique workflow ID (UUID)")
    
    # Findings accumulated by agents
    findings: list[Finding] = Field(
        default_factory=list,
        description="List of findings discovered by agents"
    )
    
    # Agent-specific context (optional, for debugging)
    agent_errors: dict[str, str] = Field(
        default_factory=dict,
        description="Errors from any agent (agent_name -> error_message)"
    )
    
    # Aggregation result (optional)
    summary: dict | None = Field(
        None,
        description="Aggregated summary from the aggregator node"
    )
    
    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
