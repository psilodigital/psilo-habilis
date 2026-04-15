"""
Typed HTTP client for the self-hosted Paperclip control plane API.

Provides methods for company management, task tracking, and run callbacks.
All methods are defensive — unknown response shapes are logged but not fatal.
"""

from typing import Any, Dict, List, Optional

import httpx

from ..config import settings
from ..logging import logger
from .auth import generate_auth_header
from .models import (
    CreateCompanyRequest,
    PaperclipAgent,
    PaperclipCompany,
    PaperclipTask,
    RunCallbackPayload,
    UpdateCompanyRequest,
)


class PaperclipClientError(Exception):
    """Raised when a Paperclip API call fails."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Paperclip API error {status_code}: {message}")


class PaperclipClient:
    """Typed async client for the Paperclip control plane API."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        base_url: Optional[str] = None,
    ):
        self._client = http_client
        self._base_url = (base_url or settings.paperclip_base_url).rstrip("/")

    def _headers(self) -> Dict[str, str]:
        """Build request headers with auth."""
        headers = {"Content-Type": "application/json"}
        headers.update(generate_auth_header())
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        timeout: float = 10.0,
    ) -> Dict[str, Any]:
        """Make an authenticated request to Paperclip."""
        url = f"{self._base_url}{path}"
        try:
            resp = await self._client.request(
                method,
                url,
                headers=self._headers(),
                json=json,
                timeout=timeout,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except httpx.HTTPStatusError as exc:
            body = exc.response.text[:500]
            logger.error("Paperclip %s %s → %s: %s", method, path, exc.response.status_code, body)
            raise PaperclipClientError(exc.response.status_code, body) from exc
        except Exception as exc:
            logger.error("Paperclip %s %s failed: %s", method, path, exc)
            raise

    # --- Health ---

    async def health(self) -> Dict[str, Any]:
        """GET /api/health — check Paperclip health."""
        return await self._request("GET", "/api/health")

    # --- Companies ---

    async def list_companies(self) -> List[Dict[str, Any]]:
        """GET /api/companies — list all companies."""
        data = await self._request("GET", "/api/companies")
        return data if isinstance(data, list) else data.get("companies", [])

    async def get_company(self, company_id: str) -> Dict[str, Any]:
        """GET /api/companies/{id} — get a single company."""
        return await self._request("GET", f"/api/companies/{company_id}")

    async def create_company(self, request: CreateCompanyRequest) -> Dict[str, Any]:
        """POST /api/companies — create a new company."""
        return await self._request("POST", "/api/companies", json=request.model_dump(exclude_none=True))

    async def update_company(
        self, company_id: str, request: UpdateCompanyRequest
    ) -> Dict[str, Any]:
        """PATCH /api/companies/{id} — update an existing company."""
        return await self._request(
            "PATCH",
            f"/api/companies/{company_id}",
            json=request.model_dump(exclude_none=True),
        )

    # --- Agents ---

    async def list_agents(self, company_id: str) -> List[Dict[str, Any]]:
        """GET /api/companies/{id}/agents — list agents for a company."""
        data = await self._request("GET", f"/api/companies/{company_id}/agents")
        return data if isinstance(data, list) else data.get("agents", [])

    # --- Tasks ---

    async def list_tasks(self, company_id: str) -> List[Dict[str, Any]]:
        """GET /api/companies/{id}/tasks — list tasks for a company."""
        data = await self._request("GET", f"/api/companies/{company_id}/tasks")
        return data if isinstance(data, list) else data.get("tasks", [])

    async def get_task(self, company_id: str, task_id: str) -> Dict[str, Any]:
        """GET /api/companies/{id}/tasks/{task_id}."""
        return await self._request("GET", f"/api/companies/{company_id}/tasks/{task_id}")

    # --- Run callbacks ---

    async def complete_run(self, callback_url: str, payload: RunCallbackPayload) -> Dict[str, Any]:
        """POST to the callback URL with run results."""
        try:
            resp = await self._client.post(
                callback_url,
                headers=self._headers(),
                json=payload.model_dump(exclude_none=True),
                timeout=10.0,
            )
            resp.raise_for_status()
            return resp.json() if resp.content else {}
        except Exception as exc:
            logger.error("Paperclip callback to %s failed: %s", callback_url, exc)
            raise
