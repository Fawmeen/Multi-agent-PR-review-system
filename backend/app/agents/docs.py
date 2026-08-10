from app.agents.base import BaseAgent
from app.models.enums import AgentName, FindingCategory
from app.prompts.registry import DOCS_AGENT_PROMPT

class DocsAgent(BaseAgent):
    agent_name = AgentName.DOCS
    category = FindingCategory.DOCUMENTATION
    prompt = DOCS_AGENT_PROMPT