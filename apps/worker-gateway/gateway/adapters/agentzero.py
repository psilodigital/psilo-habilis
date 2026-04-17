"""
Agent Zero runtime adapter.

Integrates with Agent Zero's External API to execute worker tasks.
Uses PromptAssembler for proper persona/playbook/context injection
and ResponseParser for structured output extraction.
"""

import base64
from typing import Any, Dict, Optional

import httpx

from ..config import settings
from ..logging import logger
from ..models import Artifact
from ..prompt import AssembledPrompt, PromptAssembler
from ..resolver import load_blueprint_assets
from ..response_parser import ResponseParser
from .base import RuntimeAdapter, RuntimeResult


class AgentZeroAdapter(RuntimeAdapter):
    """Adapter that delegates execution to Agent Zero's External API."""

    def __init__(self, http_client: httpx.AsyncClient):
        self._client = http_client
        self._assembler = PromptAssembler()
        self._parser = ResponseParser()

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

    async def _terminate_context(self, context_id: str, token: str) -> None:
        """Clean up Agent Zero chat context after run completion."""
        try:
            await self._client.post(
                f"{settings.agentzero_base_url}/api_terminate_chat",
                headers={"Content-Type": "application/json", "X-API-KEY": token},
                json={"context_id": context_id},
                timeout=10.0,
            )
            logger.info("Terminated A0 context: %s", context_id)
        except Exception as exc:
            logger.warning("Failed to terminate A0 context %s: %s", context_id, exc)

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

        # Load blueprint assets and assemble prompt
        blueprint_id = blueprint.get("id", "unknown")
        assets = load_blueprint_assets(blueprint_id)

        assembled = self._assembler.assemble(
            task_kind=task_kind,
            input_message=input_message,
            input_data=input_data,
            blueprint=blueprint,
            persona=assets["persona"],
            playbook=assets["playbook"],
            policies=assets["policies"],
            output_schema=assets["output_schema"],
            client_context=client_context,
            merged_config=merged_config,
        )

        # Combine system + user prompt for Agent Zero's single-message API
        full_prompt = (
            f"{assembled.system_prompt}\n\n"
            f"---\n\n"
            f"{assembled.user_prompt}"
        )

        context_id: Optional[str] = None

        # Build A0 API payload (field names confirmed from A0 source).
        # Do NOT send context_id on the first message — A0 creates a new
        # context and returns its id. Sending a non-existent id causes 404.
        a0_payload: Dict[str, Any] = {
            "message": full_prompt,
            "lifetime_hours": 1,
        }

        try:
            resp = await self._client.post(
                f"{settings.agentzero_base_url}/api_message",
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": token,
                },
                json=a0_payload,
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

            # Parse response into structured data
            parse_result = self._parser.parse(
                a0_response,
                output_schema=assets["output_schema"],
            )

            return RuntimeResult(
                classification=parse_result.classification,
                artifacts=parse_result.artifacts,
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
        finally:
            # Clean up A0 context after each run
            if context_id and token:
                await self._terminate_context(context_id, token)
