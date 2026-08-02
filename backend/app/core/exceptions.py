"""
Custom exception hierarchy for the PR review agent.
Each layer has its own exception type, making debugging and error handling precise.
"""


class PRReviewAgentError(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, detail: dict | None = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)


# --- Core Layer Exceptions ---
class ConfigurationError(PRReviewAgentError):
    """Raised when configuration is invalid or missing."""
    pass


# --- Webhook Layer Exceptions ---
class WebhookError(PRReviewAgentError):
    """Base for webhook-related errors."""
    pass

class InvalidSignatureError(WebhookError):
    """HMAC signature validation failed."""
    pass

class InvalidPayloadError(WebhookError):
    """Webhook payload is malformed."""
    pass


# --- Orchestrator Layer Exceptions ---
class WorkflowError(PRReviewAgentError):
    """Base for workflow/orchestration errors."""
    pass

class NodeExecutionError(WorkflowError):
    """A specific node in the graph failed."""
    def __init__(self, node_name: str, message: str, detail: dict | None = None):
        self.node_name = node_name
        super().__init__(f"[{node_name}] {message}", detail)


# --- Agent Layer Exceptions ---
class AgentError(PRReviewAgentError):
    """Base for agent-related errors."""
    pass

class AgentExecutionError(AgentError):
    """An agent failed during execution."""
    def __init__(self, agent_name: str, message: str):
        self.agent_name = agent_name
        super().__init__(f"Agent '{agent_name}': {message}")


# --- Memory Layer Exceptions ---
class MemoryError(PRReviewAgentError):
    """Base for memory/RAG errors."""
    pass

class RetrievalError(MemoryError):
    """Failed to retrieve from vector store."""
    pass

class EmbeddingError(MemoryError):
    """Failed to generate embeddings."""
    pass


# --- Database Layer Exceptions ---
class DatabaseError(PRReviewAgentError):
    """Base for database errors."""
    pass

class ConnectionPoolExhaustedError(DatabaseError):
    """No available database connections."""
    pass


# --- HITL Layer Exceptions ---
class HITLError(PRReviewAgentError):
    """Base for Human-in-the-Loop errors."""
    pass

class ApprovalQueueFullError(HITLError):
    """Approval queue has reached capacity."""
    pass