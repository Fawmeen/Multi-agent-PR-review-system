class AppException(Exception):
    """Base exception for the application."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class WebhookValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class AgentExecutionError(AppException):
    def __init__(self, agent_name: str, detail: str):
        super().__init__(f"Agent {agent_name} failed: {detail}", status_code=500)