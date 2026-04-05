"""
Agent Zero runtime adapter.

Integrates with Agent Zero's External API to execute worker tasks.

STATUS: Scaffold only. Real integration requires:
  - Agent Zero project-scoped execution (one project per client)
  - Structured output parsing from A0 responses
  - Persona/playbook injection into A0 message context
  - A0 API token management per-project

TODO:
  1. Confirm A0 /api_message supports project scoping
  2. Implement persona/playbook prompt assembly
  3. Parse A0 free-text response into structured Classification + Artifacts
  4. Add proper error handling for A0-specific failure modes
  5. Implement A0 context cleanup after each run
  6. Add timeout handling aligned with merged config timeoutSeconds
"""

import base64
from typing import Any, Dict

import httpx

from ..config import settings
from ..logging import logger
from ..models import Artifact
from .base import RuntimeAdapter, RuntimeResult


class AgentZeroAdapter(RuntimeAdapter):
    """Adapter that delegates execution to Agent Zero's External API."""

    def __init__(self, http_client: httpx.AsyncClient):
        self._client = http_client

    @property
    def name(self) -> str:
        return "agentzero"

    def _get_api_token(self) -> str:
        """Resolve the Agent Zero API token."""
        if settings.agentzero_api_token:
            return settings.agentzero_api_token
        if settings.agentzero_auth_login and settings.agentzero_auth_password:
            creds = f"{settings.agentzero_auth_login}:{settings.agentzero_auth_password}"
            return base64.b64encode(creds.encode()).decode()
        return ""

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
        token = self._get_api_token()
        if not token:
            return RuntimeResult(
                error_code="AGENTZERO_NO_TOKEN",
                error_message=(
                    "Agent Zero API token not configured. "
                    "Set AGENTZERO_API_TOKEN in .env."
                ),
            )

        # TODO: Assemble prompt from persona + playbook + client context + input
        prompt = f"[task_kind: {task_kind}]\n\n{input_message}"

        try:
            resp = await self._client.post(
                f"{settings.agentzero_base_url}/api_message",
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": token,
                },
                json={
                    "message": prompt,
                    "lifetime_hours": 24,
                },
                timeout=float(merged_config.get("timeoutSeconds", 120)),
            )
            resp.raise_for_status()
            data = resp.json()

            a0_response = data.get("response", "")
            context_id = data.get("context_id")

            logger.info(
                "Agent Zero responded (context=%s): %s",
                context_id,
                a0_response[:200] if a0_response else "",
            )

            # TODO: Parse a0_response into structured Classification + Artifacts
            # For now, return the raw response as a single artifact
            return RuntimeResult(
                artifacts=[
                    Artifact(
                        type="raw_agentzero_response",
                        content=a0_response,
                        approvalStatus="pending",
                    )
                ],
                tokens_used=0,  # TODO: extract from A0 response if available
                model_used=merged_config.get("model", "unknown"),
            )

        except httpx.HTTPStatusError as exc:
            logger.error(
                "Agent Zero HTTP %s: %s",
                exc.response.status_code,
                exc.response.text[:500],
            )
            return RuntimeResult(
                error_code="AGENTZERO_HTTP_ERROR",
                error_message=f"Agent Zero returned HTTP {exc.response.status_code}",
            )
        except Exception as exc:
            logger.error("Agent Zero call failed: %s", exc)
            return RuntimeResult(
                error_code="AGENTZERO_UNREACHABLE",
                error_message=f"Agent Zero unreachable: {exc}",
            )
