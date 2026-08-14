"""
GitHub API integration for fetching PR information and diffs.
"""
import logging
from typing import Optional
import httpx

from app.core.config import get_settings
from app.reliability.retry import retry_with_backoff

logger = logging.getLogger(__name__)

settings = get_settings()


class GitHubClient:
    """Async GitHub API client with retry logic."""
    
    BASE_URL = "https://api.github.com"
    TIMEOUT = httpx.Timeout(30.0)  # 30 second timeout for requests
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub API token (defaults to settings.github_token)
        """
        self.token = token or settings.github_token
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-PR-Review-Agent/1.0",
        }
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def get_pr_diff(
        self, 
        repo_full_name: str, 
        pr_number: int
    ) -> str:
        """
        Fetch the unified diff for a pull request.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            Unified diff content as a string
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If repo_full_name format is invalid
        """
        if "/" not in repo_full_name:
            raise ValueError(
                f"Invalid repository name: {repo_full_name}. "
                "Expected format: 'owner/repo'"
            )
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/pulls/{pr_number}"
        
        logger.info(f"Fetching PR diff for {repo_full_name}#{pr_number}")
        
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            # Request the diff in unified format
            diff_headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
            response = await client.get(url, headers=diff_headers)
            response.raise_for_status()
            
            diff_content = response.text
            logger.info(
                f"Successfully fetched PR diff: {repo_full_name}#{pr_number} "
                f"({len(diff_content)} bytes)"
            )
            
            return diff_content
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def get_pr_info(
        self, 
        repo_full_name: str, 
        pr_number: int
    ) -> dict:
        """
        Fetch pull request metadata.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            pr_number: Pull request number
            
        Returns:
            PR metadata dictionary
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        if "/" not in repo_full_name:
            raise ValueError(
                f"Invalid repository name: {repo_full_name}. "
                "Expected format: 'owner/repo'"
            )
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/pulls/{pr_number}"
        
        logger.info(f"Fetching PR info for {repo_full_name}#{pr_number}")
        
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            pr_data = response.json()
            logger.info(f"Successfully fetched PR info: {repo_full_name}#{pr_number}")
            
            return pr_data
    
    @retry_with_backoff(max_retries=3, initial_delay=1.0)
    async def get_file_content(
        self, 
        repo_full_name: str, 
        path: str,
        ref: str = "main"
    ) -> str:
        """
        Fetch file content from repository.
        
        Args:
            repo_full_name: Repository in format "owner/repo"
            path: Path to file in repository
            ref: Git reference (branch, tag, commit SHA) - defaults to 'main'
            
        Returns:
            File content as a string
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        if "/" not in repo_full_name:
            raise ValueError(
                f"Invalid repository name: {repo_full_name}. "
                "Expected format: 'owner/repo'"
            )
        
        url = f"{self.BASE_URL}/repos/{repo_full_name}/contents/{path}"
        params = {"ref": ref}
        
        logger.info(f"Fetching file {path} from {repo_full_name}@{ref}")
        
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            # Use raw media type to get content directly (not base64)
            headers = {**self.headers, "Accept": "application/vnd.github.v3.raw"}
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            logger.info(f"Successfully fetched file: {repo_full_name}/{path}")
            
            return response.text


# Singleton instance
_client: Optional[GitHubClient] = None


def get_github_client() -> GitHubClient:
    """
    Get or create a GitHub client singleton.
    
    Returns:
        GitHubClient instance
    """
    global _client
    if _client is None:
        _client = GitHubClient()
    return _client
