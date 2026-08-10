from app.agents.base import BaseAgent
from app.models.enums import AgentName, FindingCategory
from app.prompts.registry import SECURITY_AGENT_PROMPT

class SecurityAgent(BaseAgent):
    agent_name = AgentName.SECURITY
    category = FindingCategory.SECURITY
    prompt = SECURITY_AGENT_PROMPT