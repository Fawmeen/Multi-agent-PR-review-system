"""
Service for calculating LLM token costs and economics.
"""

# Standard cost dictionary for models per 1k tokens (USD)
MODEL_PRICING = {
    "gpt-4": {"prompt": 0.03, "completion": 0.06},
    "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
    "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
    "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
    "default": {"prompt": 0.01, "completion": 0.02} # fallback
}

class EconomicsTracker:
    @staticmethod
    def calculate_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate the USD cost of an LLM call.
        
        Args:
            model_name: The LLM model name (e.g. gpt-4)
            prompt_tokens: Number of prompt/input tokens
            completion_tokens: Number of completion/output tokens
            
        Returns:
            The total cost in USD
        """
        pricing = MODEL_PRICING.get(model_name.lower(), MODEL_PRICING["default"])
        prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1000) * pricing["completion"]
        return prompt_cost + completion_cost
