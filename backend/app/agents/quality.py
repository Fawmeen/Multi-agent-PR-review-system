from app.agents.base import BaseAgent
from app.models.enums import AgentName, FindingCategory
from app.prompts.registry import QUALITY_AGENT_PROMPT

class QualityAgent(BaseAgent):
    agent_name = AgentName.QUALITY
    category = FindingCategory.CODE_QUALITY
    prompt = QUALITY_AGENT_PROMPT