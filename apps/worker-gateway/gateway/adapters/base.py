"""
Runtime adapter interface.

Every runtime adapter must implement this interface.
The gateway calls the adapter to execute the actual worker task.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..models import Artifact, Classification


class RuntimeResult:
    """Result returned by a runtime adapter after executing a worker task."""

    def __init__(
        self,
        *,
        classification: Classification | None = None,
        artifacts: List[Artifact] | None = None,
        tokens_used: int = 0,
        model_used: str = "",
        error_code: str | None = None,
        error_message: str | None = None,
    ):
        self.classification = classification
        self.artifacts = artifacts or []
        self.tokens_used = tokens_used
        self.model_used = model_used
        self.error_code = error_code
        self.error_message = error_message

    @property
    def is_error(self) -> bool:
        return self.error_code is not None


class RuntimeAdapter(ABC):
    """Abstract base class for runtime adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter name (e.g. 'agentzero', 'stub')."""
        ...

    @abstractmethod
    async def execute(
        self,
        *,
        task_kind: str,
        input_message: str,
        input_data: Dict[str, Any] | None,
        merged_config: Dict[str, Any],
        blueprint: Dict[str, Any],
        client_context: Dict[str, str],
    ) -> RuntimeResult:
        """
        Execute a worker task and return the result.

        Args:
            task_kind: The kind of task (e.g. "inbound_email_triage")
            input_message: The primary input message
            input_data: Structured input data
            merged_config: Resolved config (blueprint + client + run overrides)
            blueprint: Full blueprint dict
            client_context: Client context files (stem → content)

        Returns:
            RuntimeResult with classification, artifacts, and metadata.
        """
        ...
