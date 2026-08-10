from app.agents.base import BaseAgent
from app.models.enums import AgentName, FindingCategory
from app.prompts.registry import TEST_AGENT_PROMPT

class TestAgent(BaseAgent):
    agent_name = AgentName.TEST
    category = FindingCategory.TESTING
    prompt = TEST_AGENT_PROMPT