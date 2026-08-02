"""
Centralized configuration using Pydantic BaseSettings.
Reads from .env file and environment variables automatically.
"""
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "AI-PR Review Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-pro"  # Default model, can override
    
    # Tiger Database (TimescaleDB + pgvectorscale)
    tiger_database_url: str
    tiger_pool_size: int = 10  # Connection pool size
    tiger_pool_overflow: int = 5  # Extra connections when pool is full
    
    # Upstash Redis
    upstash_redis_url: str
    
    # GitHub Webhook
    github_webhook_secret: str
    
    # Security
    allowed_hosts: list[str] = ["*"]  # CORS - restrict in production
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # Allows UPPER_CASE in .env


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    Using lru_cache ensures we only read .env once.
    This is a FastAPI best practice for dependency injection.
    """
    return Settings()