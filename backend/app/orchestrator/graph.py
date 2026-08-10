"""
LangGraph graph for the multi‑agent review workflow.
"""
# pyrefly: ignore [missing-import]
from langgraph.graph import StateGraph, END
from app.orchestrator.state import ReviewState
from app.orchestrator.nodes import (
    security_agent_node,
    quality_agent_node,
    test_agent_node,
    docs_agent_node,
    aggregator_node,
)


def build_review_graph():
    """
    Build and compile the review graph.
    Returns a compiled LangGraph app (without persistence for now).
    """
    workflow = StateGraph(ReviewState)

    # Add nodes
    workflow.add_node("security_agent", security_agent_node)
    workflow.add_node("quality_agent", quality_agent_node)
    workflow.add_node("test_agent", test_agent_node)
    workflow.add_node("docs_agent", docs_agent_node)
    workflow.add_node("aggregator", aggregator_node)

    # Fan-out: we'll start from a dummy start? Actually, we can set entry point to a "distribute" node,
    # but it's cleaner to create a small start node that just passes state and fans out.
    # Alternative: we can add a `start` node that does nothing, then fan out to all four.
    # Let's do that to avoid artificial ordering.
    async def start_node(state: ReviewState) -> dict:
        return {}  # Just pass through

    workflow.add_node("start", start_node)
    workflow.set_entry_point("start")

    # Sequential chain: start -> security -> quality -> test -> docs -> aggregator
    # This avoids parallel API calls that exhaust free-tier per-minute quota.
    # Switch back to parallel fan-out when billing is enabled.
    workflow.add_edge("start", "security_agent")
    workflow.add_edge("security_agent", "quality_agent")
    workflow.add_edge("quality_agent", "test_agent")
    workflow.add_edge("test_agent", "docs_agent")
    workflow.add_edge("docs_agent", "aggregator")

    # End after aggregator
    workflow.add_edge("aggregator", END)

    return workflow.compile()