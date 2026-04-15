"""
Run history store.

Records worker run results to Postgres for audit trail and analytics.
Recording is non-blocking — failures are logged but never fail the run.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..logging import logger

try:
    import asyncpg
except ImportError:
    asyncpg = None  # type: ignore[assignment]


class RunStore:
    """Non-blocking run history recorder."""

    def __init__(self, database_url: str):
        if asyncpg is None:
            raise RuntimeError("asyncpg is required for RunStore")
        self._database_url = database_url
        self._pool: Optional[Any] = None

    async def connect(self) -> None:
        self._pool = await asyncpg.create_pool(self._database_url, min_size=1, max_size=5)
        logger.info("RunStore connected to database")

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()

    async def record_run(
        self,
        *,
        run_id: str,
        company_id: str,
        worker_instance_id: str,
        blueprint_id: str,
        blueprint_version: str,
        task_kind: str,
        input_message: str,
        input_data: Optional[Dict[str, Any]],
        run_overrides: Optional[Dict[str, Any]],
        resolved_config: Dict[str, Any],
        status: str,
        classification: Optional[Dict[str, Any]],
        artifacts: List[Dict[str, Any]],
        runtime_adapter: str,
        model_used: str,
        tokens_used: int,
        duration_ms: int,
        error_code: Optional[str],
        error_message: Optional[str],
        started_at: datetime,
        completed_at: datetime,
    ) -> None:
        """Record a run result. Failures are logged but never raised."""
        if not self._pool:
            logger.warning("RunStore not connected, skipping record for run %s", run_id)
            return

        try:
            await self._pool.execute(
                """
                INSERT INTO run_history (
                    run_id, company_id, worker_instance_id,
                    blueprint_id, blueprint_version, task_kind,
                    input_message, input_data, run_overrides, resolved_config,
                    status, classification, artifacts,
                    runtime_adapter, model_used, tokens_used, duration_ms,
                    error_code, error_message,
                    started_at, completed_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6,
                    $7, $8, $9, $10,
                    $11, $12, $13,
                    $14, $15, $16, $17,
                    $18, $19,
                    $20, $21
                )
                """,
                run_id,
                company_id,
                worker_instance_id,
                blueprint_id,
                blueprint_version,
                task_kind,
                input_message,
                json.dumps(input_data) if input_data else None,
                json.dumps(run_overrides) if run_overrides else None,
                json.dumps(resolved_config),
                status,
                json.dumps(classification) if classification else None,
                json.dumps(artifacts),
                runtime_adapter,
                model_used,
                tokens_used,
                duration_ms,
                error_code,
                error_message,
                started_at,
                completed_at,
            )
            logger.info("Recorded run %s to history", run_id)
        except Exception as exc:
            logger.error("Failed to record run %s: %s", run_id, exc)
