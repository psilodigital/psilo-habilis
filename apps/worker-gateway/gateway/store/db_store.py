"""
Database-backed config store.

Loads company and worker instance configs from Postgres.
Requires DATABASE_URL to be configured.
"""

import json
from typing import Any, Dict, Optional

from ..logging import logger
from .base import ConfigStore

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]


class DbConfigStore(ConfigStore):
    """Config store backed by Postgres tables."""

    def __init__(self, database_url: str):
        if asyncpg is None:
            raise RuntimeError(
                "asyncpg is required for DbConfigStore. "
                "Install it with: pip install asyncpg"
            )
        self._database_url = database_url
        self._pool: Optional[Any] = None

    @property
    def name(self) -> str:
        return "db"

    async def connect(self) -> None:
        """Create the connection pool."""
        self._pool = await asyncpg.create_pool(self._database_url, min_size=2, max_size=10)
        logger.info("DbConfigStore connected to database")

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("DbConfigStore connection pool closed")

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        row = await self._pool.fetchrow(
            "SELECT * FROM companies WHERE id = $1", company_id
        )
        if not row:
            raise KeyError(f"Company '{company_id}' not found in database")

        result = dict(row)
        # Parse JSONB fields
        for field in ("settings", "context_files"):
            if field in result and isinstance(result[field], str):
                result[field] = json.loads(result[field])

        logger.info("Resolved company from DB: %s (%s)", company_id, result.get("name", "unnamed"))
        return result

    async def get_worker_instance(
        self, company_id: str, instance_id: str
    ) -> Dict[str, Any]:
        row = await self._pool.fetchrow(
            "SELECT * FROM worker_instances WHERE id = $1 AND company_id = $2",
            instance_id,
            company_id,
        )
        if not row:
            raise KeyError(
                f"Worker instance '{instance_id}' not found for company '{company_id}'"
            )

        result = dict(row)
        # Parse JSONB fields
        for field in ("overrides", "context_refs", "metadata"):
            if field in result and isinstance(result[field], str):
                result[field] = json.loads(result[field])

        if not result.get("enabled", True):
            raise ValueError(f"Worker instance '{instance_id}' is disabled.")

        logger.info("Resolved worker instance from DB: %s", instance_id)
        return result

    async def get_company_context(self, company_id: str) -> Dict[str, str]:
        row = await self._pool.fetchrow(
            "SELECT context_files FROM companies WHERE id = $1", company_id
        )
        if not row or not row["context_files"]:
            return {}

        context_files = row["context_files"]
        if isinstance(context_files, str):
            context_files = json.loads(context_files)

        # context_files is a dict mapping name → content
        if isinstance(context_files, dict):
            logger.info("Loaded %d context entries from DB for company %s", len(context_files), company_id)
            return context_files

        return {}
