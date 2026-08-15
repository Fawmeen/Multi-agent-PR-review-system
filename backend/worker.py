"""
ARQ background worker for the AI-PR Review Agent.
Processes review jobs from the Redis queue.

Run with: arq worker.py

This worker:
1. Fetches PR diff from GitHub
2. Runs the multi-agent LangGraph orchestration
3. Stores findings in Tiger database
4. Updates review status
"""
import logging
import asyncio
import uuid
from typing import Optional
# pyrefly: ignore [missing-import]
from arq.connections import RedisSettings
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.core.config import get_settings
from app.integrations import get_github_client
from app.orchestrator import build_review_graph, ReviewState
from app.database.postgres import AsyncSessionLocal
from app.database.repository import ReviewRepository, EventRepository
from app.database.models import ReviewModel, FindingModel
from app.models.enums import ReviewStatus
from app.memory.memory_service import MemoryService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()
github_client = get_github_client()


def _parse_redis_url(url: str) -> RedisSettings:
    """
    Parse a Redis URL into ARQ's RedisSettings.
    """
    parsed = urlparse(url)
    password = parsed.password
    
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=password,
        ssl=(parsed.scheme == "rediss"),
    )


async def start_review_workflow(ctx, payload: dict) -> dict:
    """
    ARQ job handler: processes a GitHub PR for review.
    
    Args:
        ctx: ARQ context (job metadata)
        payload: GitHub webhook payload
        
    Returns:
        Status dict with workflow result
        
    Error handling:
        - If GitHub fetch fails: returns error status
        - If orchestrator fails: creates review with error status
        - If database save fails: logs error and returns failure
    """
    try:
        # Extract PR details from webhook payload
        pr_data = payload.get("pull_request", {})
        repo_data = payload.get("repository", {})
        
        pr_number = pr_data.get("number")
        repository = repo_data.get("full_name")
        commit_sha = pr_data.get("head", {}).get("sha")
        action = payload.get("action")
        
        logger.info(
            f"🔔 [WORKER] Job started: {repository}#{pr_number} "
            f"(action={action}, commit={commit_sha[:8] if commit_sha else 'N/A'})"
        )
        
        # Validate payload
        if not pr_number or not repository:
            logger.error(f"Invalid webhook payload: missing PR number or repository")
            return {
                "status": "failed",
                "error": "Invalid payload: missing pr_number or repository"
            }
        
        # Generate workflow ID
        workflow_run_id = str(uuid.uuid4())
        
        # ========== Step 1: Fetch PR Diff from GitHub ==========
        logger.info(f"[WORKER] Fetching diff for {repository}#{pr_number}")
        try:
            diff = await github_client.get_pr_diff(repository, pr_number)
            logger.info(f"[WORKER] Diff fetched successfully ({len(diff)} bytes)")
        except Exception as e:
            logger.error(f"[WORKER] Failed to fetch diff: {e}")
            return {
                "status": "failed",
                "error": f"Failed to fetch diff from GitHub: {str(e)}"
            }
        
        # ========== Step 1.5: Ingest into RAG Memory ==========
        logger.info(f"[WORKER] Ingesting diff into Memory Service")
        try:
            async with AsyncSessionLocal() as session:
                memory_service = MemoryService(session)
                await memory_service.ingest_file(
                    content=diff, 
                    file_path=f"pr_{pr_number}.diff", 
                    repository=repository
                )
                await session.commit()
        except Exception as e:
            logger.error(f"[WORKER] Memory ingestion failed (continuing without it): {e}")
        logger.info(f"[WORKER] Building and invoking orchestrator graph")
        
        # Build initial state
        state = ReviewState(
            repository=repository,
            pr_number=pr_number,
            commit_sha=commit_sha,
            diff=diff,
            workflow_run_id=workflow_run_id,
            findings=[]
        )
        
        # Build and compile the graph
        graph = build_review_graph()
        
        # Invoke the graph (run all agents sequentially)
        try:
            logger.info(f"[WORKER] Running orchestrator for {repository}#{pr_number}")
            # Use LangGraph's async ainvoke
            result = await graph.ainvoke(state.model_dump())
            
            # Convert result dict back to ReviewState
            final_state = ReviewState(**result)
            findings = final_state.findings
            summary = final_state.summary or {}
            events = final_state.agent_events
            total_tokens_used = final_state.total_tokens_used
            total_cost_usd = final_state.total_cost_usd
            
            logger.info(
                f"[WORKER] Orchestrator completed: "
                f"findings={len(findings)}, summary={summary}, events={len(events)}"
            )
        except Exception as e:
            logger.error(f"[WORKER] Orchestrator failed: {e}", exc_info=True)
            findings = []
            summary = {"error": str(e)}
            events = []
            total_tokens_used = 0
            total_cost_usd = 0.0
        
        # ========== Step 3: Persist Review, Findings, and Events to Tiger ==========
        logger.info(f"[WORKER] Saving review, {len(findings)} findings, and {len(events)} events to Tiger")
        
        async with AsyncSessionLocal() as session:
            try:
                # Determine review status
                review_status = (
                    ReviewStatus.AWAITING_APPROVAL 
                    if findings 
                    else ReviewStatus.APPROVED
                )
                
                # Create Review record
                review_model = ReviewModel(
                    id=workflow_run_id,
                    repository=repository,
                    pr_number=pr_number,
                    commit_sha=commit_sha,
                    status=review_status,
                    workflow_run_id=workflow_run_id,
                    summary=summary,
                    total_tokens_used=total_tokens_used,
                    total_cost_usd=total_cost_usd,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                )
                
                session.add(review_model)
                await session.flush()
                logger.info(f"[WORKER] Created review record: {workflow_run_id}")
                
                # Create Finding records
                for finding in findings:
                    finding_model = FindingModel(
                        id=finding.id,
                        review_id=workflow_run_id,
                        agent=finding.agent,
                        category=finding.category,
                        severity=finding.severity,
                        file_path=finding.file_path,
                        line_start=finding.line_start,
                        line_end=finding.line_end,
                        title=finding.title,
                        description=finding.description,
                        suggestion=finding.suggestion,
                        rule_reference=finding.rule_reference,
                    )
                    session.add(finding_model)
                
                await session.flush()
                logger.info(f"[WORKER] Created {len(findings)} finding records")
                
                # Create Event records
                if events:
                    event_repo = EventRepository(session)
                    await event_repo.log_events(events)
                    logger.info(f"[WORKER] Created {len(events)} agent event records")
                
                # Commit transaction
                await session.commit()
                logger.info(f"[WORKER] Review, findings, and events committed to Tiger")
                
            except Exception as e:
                logger.error(f"[WORKER] Database error: {e}", exc_info=True)
                await session.rollback()
                return {
                    "status": "failed",
                    "error": f"Failed to save review to Tiger: {str(e)}"
                }
        
        # ========== Step 4: Success Response ==========
        logger.info(
            f"✅ [WORKER] Workflow completed for {repository}#{pr_number}: "
            f"workflow_id={workflow_run_id}, findings={len(findings)}, status={review_status}"
        )
        
        return {
            "status": "completed",
            "workflow_run_id": workflow_run_id,
            "repository": repository,
            "pr_number": pr_number,
            "findings_count": len(findings),
            "review_status": review_status,
        }
    
    except Exception as e:
        logger.error(f"❌ [WORKER] Unhandled error in start_review_workflow: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": f"Unhandled error: {str(e)}"
        }


# Worker configuration
class WorkerSettings:
    """
    Settings for ARQ background worker.
    
    To run: arq worker.WorkerSettings
    """
    functions = [start_review_workflow]
    redis_settings = _parse_redis_url(settings.upstash_redis_url)
    queue_name = "review_queue"
    max_jobs = 10
    job_timeout = 300  # 5 minutes per job
    poll_delay = 0.5