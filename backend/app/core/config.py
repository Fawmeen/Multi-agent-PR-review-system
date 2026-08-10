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
    
    # OpenRouter API (OpenAI-compatible)
    openrouter_api_key: str
    openrouter_model: str = "nvidia/nemotron-3-ultra-550b-a55b:free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # Tiger Database (TimescaleDB + pgvectorscale)
    tiger_database_url: str
    tiger_pool_size: int = 10
    tiger_pool_overflow: int = 5
    
    # Upstash Redis
    upstash_redis_url: str
    
    # GitHub Webhook
    github_webhook_secret: str
    
    # Security
    allowed_hosts: list[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"   # ignore unknown env vars instead of crashing


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    Using lru_cache ensures we only read .env once.
    """
    return Settings()