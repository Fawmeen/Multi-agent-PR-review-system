"""
LangGraph graph builder for the multi-agent review workflow.
"""
import logging
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

logger = logging.getLogger(__name__)


def build_review_graph():
    """
    Build and compile the review graph.
    
    The graph runs agents sequentially to avoid overwhelming free-tier API quotas:
    start -> security -> quality -> test -> docs -> aggregator -> END
    
    When billing is enabled, this can be switched to parallel fan-out for faster execution.
    
    Returns:
        Compiled LangGraph application (without persistence for now)
    """
    workflow = StateGraph(ReviewState)

    # Add nodes for each agent and the aggregator
    workflow.add_node("security_agent", security_agent_node)
    workflow.add_node("quality_agent", quality_agent_node)
    workflow.add_node("test_agent", test_agent_node)
    workflow.add_node("docs_agent", docs_agent_node)
    workflow.add_node("aggregator", aggregator_node)

    # Add a dummy start node to initialize the state
    # (StateGraph requires an entry point node)
    async def start_node(state: ReviewState) -> dict:
        """No-op start node that just passes through the state."""
        logger.info(f"Starting review workflow for PR #{state.pr_number}")
        return {}

    workflow.add_node("start", start_node)
    workflow.set_entry_point("start")

    # Sequential chain: start -> security -> quality -> test -> docs -> aggregator -> END
    # Rationale: Free-tier OpenRouter has per-minute rate limits; sequential avoids 429 errors
    workflow.add_edge("start", "security_agent")
    workflow.add_edge("security_agent", "quality_agent")
    workflow.add_edge("quality_agent", "test_agent")
    workflow.add_edge("test_agent", "docs_agent")
    workflow.add_edge("docs_agent", "aggregator")
    workflow.add_edge("aggregator", END)

    # Compile the graph
    # Note: No persistence layer for now (no Redis state storage)
    compiled_graph = workflow.compile()
    
    logger.info("Review workflow graph compiled successfully")
    
    return compiled_graph
