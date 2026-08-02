"""
Abstract workflow engine interface.
The orchestrator module will implement this using LangGraph.
This follows the Dependency Inversion Principle: high-level modules
depend on this abstraction, not on LangGraph directly.
"""
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass, field


@dataclass
class WorkflowResult:
    """Standard result from any workflow execution."""
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    node_results: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


class WorkflowEngine(ABC):
    """
    Abstract base class for workflow engines.
    The orchestrator will subclass this.
    """
    
    @abstractmethod
    async def execute(self, input_data: dict[str, Any]) -> WorkflowResult:
        """
        Execute the workflow with given input.
        
        Args:
            input_data: The PR diff, metadata, etc.
            
        Returns:
            WorkflowResult with findings and metadata.
        """
        pass
    
    @abstractmethod
    async def resume(self, checkpoint_id: str) -> WorkflowResult:
        """
        Resume a workflow from a checkpoint.
        
        Args:
            checkpoint_id: The ID of the saved checkpoint.
            
        Returns:
            WorkflowResult with completed findings.
        """
        pass
    
    @abstractmethod
    async def get_status(self, run_id: str) -> dict[str, Any]:
        """
        Get the current status of a workflow run.
        
        Args:
            run_id: The unique run identifier.
            
        Returns:
            Status dict with current node, progress, etc.
        """
        pass
    