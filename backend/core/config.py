import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
    # If not set, we'll use a simple API key for HITL
    API_KEY: str = os.getenv("API_KEY", "dev-secret-token")

settings = Settings()