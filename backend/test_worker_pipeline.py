"""
Integration tests for the worker pipeline.
Tests the end-to-end flow: webhook -> GitHub fetch -> orchestrator -> Tiger save.

Run with: pytest test_worker_pipeline.py -v
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from app.orchestrator import ReviewState
from app.models.findings import Finding
from app.models.enums import FindingSeverity, FindingCategory, AgentName, ReviewStatus
from worker import start_review_workflow


@pytest.fixture
def sample_webhook_payload():
    """GitHub webhook payload for a pull request."""
    return {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "head": {
                "sha": "abc123def456"
            }
        },
        "repository": {
            "full_name": "test-org/test-repo"
        }
    }


@pytest.fixture
def sample_diff():
    """Sample PR diff for testing."""
    return """--- a/src/auth.py
+++ b/src/auth.py
@@ -10,5 +10,10 @@ def authenticate(username, password):
     # TODO: Implement authentication
-    return True
+    query = f"SELECT * FROM users WHERE name='{username}'"
+    # TODO: Add proper SQL parameterization
+    return True"""


@pytest.fixture
def sample_findings():
    """Sample findings from orchestrator."""
    return [
        Finding(
            agent=AgentName.SECURITY,
            category=FindingCategory.SECURITY,
            severity=FindingSeverity.CRITICAL,
            file_path="src/auth.py",
            line_start=13,
            line_end=14,
            title="SQL Injection vulnerability",
            description="Direct string interpolation in SQL query allows SQL injection attacks",
            suggestion="Use parameterized queries: connection.query(..., params=[username])",
            rule_reference="OWASP Top 10 A03:2021 - Injection"
        ),
        Finding(
            agent=AgentName.QUALITY,
            category=FindingCategory.CODE_QUALITY,
            severity=FindingSeverity.MEDIUM,
            file_path="src/auth.py",
            line_start=13,
            line_end=13,
            title="Incomplete comment",
            description="TODO comment indicates unfinished implementation",
            suggestion="Complete the TODO or use a tracking system like GitHub Issues",
            rule_reference="PEP 8 - Style Guidelines"
        ),
    ]


@pytest.mark.asyncio
async def test_worker_full_pipeline(sample_webhook_payload, sample_diff, sample_findings):
    """
    Test the full worker pipeline:
    1. Fetch diff from GitHub
    2. Run orchestrator
    3. Save to Tiger
    """
    # Mock GitHub client
    with patch('worker.github_client') as mock_github:
        # Use AsyncMock for async methods
        mock_github.get_pr_diff = AsyncMock(return_value=sample_diff)
        
        # Mock the orchestrator graph
        with patch('worker.build_review_graph') as mock_build_graph:
            mock_graph = MagicMock()
            
            # Mock the graph's invoke method to return findings
            def mock_invoke(state_dict):
                state = ReviewState(**state_dict)
                state.findings = sample_findings
                state.summary = {
                    "total_findings": len(sample_findings),
                    "by_severity": {"critical": 1, "medium": 1},
                    "by_category": {"security": 1, "code_quality": 1},
                    "by_agent": {"security_agent": 1, "quality_agent": 1},
                }
                return state.model_dump()
            
            mock_graph.invoke = mock_invoke
            mock_build_graph.return_value = mock_graph
            
            # Mock the database session and repository
            with patch('worker.AsyncSessionLocal') as mock_session_local:
                mock_session = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_session
                
                # Run the worker
                ctx = MagicMock()
                result = await start_review_workflow(ctx, sample_webhook_payload)
        
        # Verify results
        assert result["status"] == "completed"
        assert result["workflow_run_id"] is not None
        assert result["repository"] == "test-org/test-repo"
        assert result["pr_number"] == 42
        assert result["findings_count"] == 2
        assert result["review_status"] == ReviewStatus.AWAITING_APPROVAL
        
        # Verify GitHub client was called
        mock_github.get_pr_diff.assert_called_once_with("test-org/test-repo", 42)


@pytest.mark.asyncio
async def test_worker_github_fetch_failure(sample_webhook_payload):
    """Test handling of GitHub fetch failures."""
    with patch('worker.github_client') as mock_github:
        mock_github.get_pr_diff = AsyncMock(side_effect=Exception("GitHub API error"))
        
        ctx = MagicMock()
        result = await start_review_workflow(ctx, sample_webhook_payload)
    
    assert result["status"] == "failed"
    assert "GitHub" in result["error"]


@pytest.mark.asyncio
async def test_worker_invalid_payload():
    """Test handling of invalid webhook payload."""
    invalid_payload = {"action": "opened"}  # Missing PR and repository info
    
    ctx = MagicMock()
    result = await start_review_workflow(ctx, invalid_payload)
    
    assert result["status"] == "failed"
    assert "Invalid payload" in result["error"]


@pytest.mark.asyncio
async def test_worker_no_findings(sample_webhook_payload, sample_diff):
    """Test when orchestrator returns no findings (all good)."""
    with patch('worker.github_client') as mock_github:
        mock_github.get_pr_diff = AsyncMock(return_value=sample_diff)
        
        with patch('worker.build_review_graph') as mock_build_graph:
            mock_graph = MagicMock()
            
            # Return empty findings
            def mock_invoke(state_dict):
                state = ReviewState(**state_dict)
                state.findings = []  # No findings = approved
                state.summary = {"total_findings": 0}
                return state.model_dump()
            
            mock_graph.invoke = mock_invoke
            mock_build_graph.return_value = mock_graph
            
            with patch('worker.AsyncSessionLocal') as mock_session_local:
                mock_session = AsyncMock()
                mock_session_local.return_value.__aenter__.return_value = mock_session
                
                ctx = MagicMock()
                result = await start_review_workflow(ctx, sample_webhook_payload)
        
        assert result["status"] == "completed"
        assert result["findings_count"] == 0
        assert result["review_status"] == ReviewStatus.APPROVED


@pytest.mark.asyncio
async def test_worker_database_error(sample_webhook_payload, sample_diff, sample_findings):
    """Test handling of database errors."""
    with patch('worker.github_client') as mock_github:
        mock_github.get_pr_diff = AsyncMock(return_value=sample_diff)
        
        with patch('worker.build_review_graph') as mock_build_graph:
            mock_graph = MagicMock()
            
            def mock_invoke(state_dict):
                state = ReviewState(**state_dict)
                state.findings = sample_findings
                state.summary = {"total_findings": len(sample_findings)}
                return state.model_dump()
            
            mock_graph.invoke = mock_invoke
            mock_build_graph.return_value = mock_graph
            
            # Mock database error
            with patch('worker.AsyncSessionLocal') as mock_session_local:
                mock_session = AsyncMock()
                mock_session.flush.side_effect = Exception("Database connection failed")
                mock_session_local.return_value.__aenter__.return_value = mock_session
                
                ctx = MagicMock()
                result = await start_review_workflow(ctx, sample_webhook_payload)
        
        assert result["status"] == "failed"
        assert "Database" in result["error"] or "Tiger" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
