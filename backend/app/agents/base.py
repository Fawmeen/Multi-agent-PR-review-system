"""
Base agent class — all specialist agents inherit from this.
Now uses OpenRouter (OpenAI-compatible API) instead of Gemini.
"""
import json
import logging
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from app.core.config import get_settings
from app.models.findings import Finding
from app.models.enums import AgentName, FindingCategory
from app.core.exceptions import AgentExecutionError
from pydantic import ValidationError

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseAgent(ABC):
    """
    Abstract base for all specialist agents.
    Subclasses only need to set `agent_name`, `category`, and `prompt`.
    """

    agent_name: AgentName
    category: FindingCategory
    prompt: str  # System instruction

    def __init__(self):
        # Initialize the async OpenAI client pointing at OpenRouter
        self.client = AsyncOpenAI(
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            default_headers={
                "HTTP-Referer": "http://localhost:3000",  # Optional, for OpenRouter rankings
                "X-Title": "AI-PR Agent",
            },
        )

    async def run(self, diff: str) -> list[Finding]:
        """
        Send the diff to the LLM (via OpenRouter) and parse the response.

        Args:
            diff: The git diff string to review.

        Returns:
            List of Finding objects (empty if no issues).
        """
        logger.info(f"Running {self.agent_name} on a diff of length {len(diff)}")
        try:
            response = await self.client.chat.completions.create(
                model=settings.openrouter_model,
                messages=[
                    {"role": "system", "content": self.prompt},
                    {"role": "user", "content": diff},
                ],
                temperature=0.1,
                max_tokens=8000,
                response_format={"type": "json_object"},  # Force JSON output
            )

            raw_text = response.choices[0].message.content
            # The JSON object may contain the array under a key; we'll handle both cases.
            try:
                data = json.loads(raw_text)
                if isinstance(data, list):
                    findings_data = data
                elif isinstance(data, dict):
                    # Often the model wraps in {"findings": [...]}
                    findings_data = data.get("findings", [])
                else:
                    findings_data = []
            except json.JSONDecodeError:
                findings_data = []

            # Convert to Finding objects, validating each item and skipping invalid ones
            findings = []
            for item in findings_data:
                if not isinstance(item, dict):
                    continue
                item["agent"] = self.agent_name
                item["category"] = self.category
                try:
                    validated: Finding = Finding.model_validate(item)
                    findings.append(validated)
                except ValidationError as ve:
                    logger.error(f"Invalid finding from {self.agent_name}: {ve}")
                    # Skip invalid findings rather than failing the whole agent
                    continue

            return findings

        except Exception as e:
            logger.error(f"Agent {self.agent_name} error: {e}")
            raise AgentExecutionError(self.agent_name, str(e))