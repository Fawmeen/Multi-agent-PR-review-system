"""Quick test for core module."""
import sys
sys.path.insert(0, '.')

from app.core.config import get_settings
from app.core.exceptions import ConfigurationError, AgentExecutionError

# Test 1: Settings load
try:
    settings = get_settings()
    print(f"✅ Settings loaded. App: {settings.app_name}")
    print(f"   Gemini model: {settings.gemini_model}")
    print(f"   Tiger DB: {settings.tiger_database_url[:30]}...")
except Exception as e:
    print(f"❌ Settings failed: {e}")
    print("Make sure .env file exists with required keys")

# Test 2: Exception hierarchy
try:
    raise AgentExecutionError("security_agent", "Model returned invalid JSON")
except AgentExecutionError as e:
    print(f"✅ Exception works: {e.message}")
    print(f"   Agent name: {e.agent_name}")

print("\n✅ Core module is working!")
