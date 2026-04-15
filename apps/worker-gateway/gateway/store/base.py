"""
Config store interface.

Abstracts company and worker instance resolution so the resolver
can delegate to file-based or database-backed storage.

Blueprints are always resolved from YAML files on disk (they are
versioned product definitions, not tenant data).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ConfigStore(ABC):
    """Abstract base class for config stores."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Store identifier (e.g. 'file', 'db')."""
        ...

    @abstractmethod
    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """
        Load company config by ID.

        Raises:
            KeyError: if company not found.
        """
        ...

    @abstractmethod
    async def get_worker_instance(
        self, company_id: str, instance_id: str
    ) -> Dict[str, Any]:
        """
        Load worker instance config.

        Raises:
            KeyError: if instance not found.
            ValueError: if instance is disabled.
        """
        ...

    @abstractmethod
    async def get_company_context(self, company_id: str) -> Dict[str, str]:
        """
        Load company context files (markdown content keyed by stem).

        Returns empty dict if no context files exist.
        """
        ...
