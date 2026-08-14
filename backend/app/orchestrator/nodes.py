"""
Node functions for the LangGraph orchestrator.
Each node receives state, does work, and returns an update to the state.
"""
import logging
from app.orchestrator.state import ReviewState
from app.agents import SecurityAgent, QualityAgent, TestAgent, DocsAgent
from app.models.findings import Finding
from app.prompts.registry import AGGREGATOR_PROMPT
from app.core.config import get_settings
import json
from pydantic import ValidationError
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types

logger = logging.getLogger(__name__)
settings = get_settings()


async def security_agent_node(state: ReviewState) -> dict:
    """Node: run the security specialist."""
    agent = SecurityAgent()
    try:
        findings = await agent.run(state["diff"])
        return {"findings": findings}
    except Exception as e:
        logger.error(f"Security agent failed: {e}")
        return {"agent_errors": {"security_agent": str(e)}}


async def quality_agent_node(state: ReviewState) -> dict:
    agent = QualityAgent()
    try:
        findings = await agent.run(state["diff"])
        return {"findings": findings}
    except Exception as e:
        return {"agent_errors": {"quality_agent": str(e)}}


async def test_agent_node(state: ReviewState) -> dict:
    agent = TestAgent()
    try:
        findings = await agent.run(state["diff"])
        return {"findings": findings}
    except Exception as e:
        return {"agent_errors": {"test_agent": str(e)}}


async def docs_agent_node(state: ReviewState) -> dict:
    agent = DocsAgent()
    try:
        findings = await agent.run(state["diff"])
        return {"findings": findings}
    except Exception as e:
        return {"agent_errors": {"docs_agent": str(e)}}


async def aggregator_node(state: ReviewState) -> dict:
    """
    Node: aggregate findings from all specialists.
    Uses OpenRouter to deduplicate and sort.
    """
    findings = state.get("findings", [])
    if not findings:
        return {"consolidated_findings": []}

    # Normalize and validate findings. We accept BaseModel instances or dicts.
    findings_dicts: list[dict] = []
    for f in findings:
        try:
            # If it's a Pydantic model, prefer its JSON-safe dump
            if hasattr(f, "model_dump_json"):
                # model_dump_json returns a JSON string with datetimes serialized
                json_s = f.model_dump_json()
                d = json.loads(json_s)
            elif hasattr(f, "model_dump"):
                d = f.model_dump()
            elif isinstance(f, dict):
                d = f
            else:
                # Fallback: try to coerce to dict
                d = dict(f)

            # Validate and canonicalize via the Finding model to ensure required fields
            try:
                validated: Finding = Finding.model_validate(d)
                # Use model_dump_json to ensure JSON-safe types (datetimes -> strings)
                d = json.loads(validated.model_dump_json())
                findings_dicts.append(d)
            except ValidationError as ve:
                logger.error(f"Invalid finding from agent: {ve}")
                # Skip invalid findings
                continue
        except Exception as e:
            logger.error(f"Failed to process finding for aggregation: {e}")
            continue

    findings_json = json.dumps(findings_dicts, indent=2)

    # Use the same OpenRouter client as the agents
    from openai import AsyncOpenAI
    client = AsyncOpenAI(
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI-PR Agent",
        },
    )

    try:
        response = await client.chat.completions.create(
            model=settings.openrouter_model,
            messages=[
                {"role": "system", "content": AGGREGATOR_PROMPT},
                {"role": "user", "content": findings_json},
            ],
            temperature=0.1,
            max_tokens=8000,
            response_format={"type": "json_object"},
        )
        raw_text = response.choices[0].message.content
        data = json.loads(raw_text)
        # Expect a list, but could be inside a key
        if isinstance(data, list):
            consolidated = data
        elif isinstance(data, dict):
            consolidated = data.get("findings", [])
        else:
            consolidated = []
        return {"consolidated_findings": consolidated}
    except Exception as e:
        logger.error(f"Aggregator failed: {e}")
        # Fallback: deterministic sort
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(
            findings_dicts,
            key=lambda x: severity_order.get(x.get("severity", "info"), 5)
        )
        return {"consolidated_findings": sorted_findings, "aggregator_error": str(e)}