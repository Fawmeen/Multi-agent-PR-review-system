"""
State definition for the LangGraph workflow.
"""
from typing import TypedDict, Annotated, List
import operator
from app.models.findings import Finding


class ReviewState(TypedDict):
    """
    State that flows through all nodes in the graph.
    LangGraph merges the return dict of each node into this state.
    """

    # Input
    diff: str                                # The git diff to review
    repository: str                          # e.g., "org/repo"
    pr_number: int                           # PR number
    workflow_run_id: str                     # Unique ID for this run

    # Findings from each agent (accumulated)
    findings: Annotated[List[Finding], operator.add]  # Merges lists across parallel nodes

    # Aggregator output
    consolidated_findings: List[dict]        # Final sorted/deduped findings

    # Error tracking
    agent_errors: Annotated[dict, operator.ior]  # Merges dicts across parallel nodes