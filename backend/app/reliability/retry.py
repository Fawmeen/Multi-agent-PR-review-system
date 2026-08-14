"""
Retry decorator for async functions with exponential backoff.
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
):
    """
    Decorator for async functions that retries on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries (default 3)
        backoff_factor: Multiplier for delay between retries (default 2.0)
        initial_delay: Initial delay in seconds (default 1.0)
        max_delay: Maximum delay in seconds (default 60.0)
    
    Retries on:
    - 5xx HTTP errors (500, 502, 503, 504)
    - Network timeouts
    - Connection errors
    
    Does NOT retry on:
    - 4xx client errors (400, 401, 403, 404, etc.)
    - Other non-retriable exceptions
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    # Check if error is retriable (5xx or timeout)
                    error_str = str(e).lower()
                    is_retriable = (
                        any(f"50{code}" in error_str for code in "0123456789") or
                        "timeout" in error_str or
                        "connection" in error_str or
                        "network" in error_str
                    )
                    
                    # Also check for common HTTP client errors (not retriable)
                    is_client_error = any(
                        f"40{code}" in error_str or f"4{code}" in error_str 
                        for code in "01234567890"
                    )
                    
                    if is_client_error:
                        # Don't retry client errors (4xx)
                        logger.error(f"{func.__name__} failed with client error: {e}")
                        raise
                    
                    if attempt < max_retries and is_retriable:
                        logger.warning(
                            f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        # No more retries or not retriable
                        logger.error(
                            f"{func.__name__} failed after {attempt + 1} attempts: {e}"
                        )
                        raise
        
        return wrapper
    
    return decorator
