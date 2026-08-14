"""
Integration modules for external services (GitHub, etc).
"""
from app.integrations.github_client import GitHubClient, get_github_client

__all__ = ["GitHubClient", "get_github_client"]
