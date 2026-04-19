"""
Authentication for the Gmail MCP server.

Validates session tokens (JWTs from the gateway) and fetches
decrypted OAuth credentials from the gateway's internal API.
"""

import os
from typing import Any, Dict, Optional

import httpx
import jwt

GATEWAY_INTERNAL_URL = os.getenv("GATEWAY_INTERNAL_URL", "http://worker-gateway:8080")
GATEWAY_INTERNAL_SECRET = os.getenv("GATEWAY_INTERNAL_SECRET", "")
CONNECTOR_JWT_SECRET = os.getenv("CONNECTOR_JWT_SECRET", "")

_http_client: Optional[httpx.AsyncClient] = None


def get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=10.0)
    return _http_client


async def close_http_client() -> None:
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate a session token JWT.

    Returns:
        Dict with company_id, connector_id, scopes

    Raises:
        jwt.ExpiredSignatureError: Token expired
        jwt.InvalidTokenError: Token invalid
    """
    if not CONNECTOR_JWT_SECRET:
        raise ValueError("CONNECTOR_JWT_SECRET not configured")

    payload = jwt.decode(token, CONNECTOR_JWT_SECRET, algorithms=["HS256"])
    return {
        "company_id": payload["sub"],
        "connector_id": payload["cid"],
        "scopes": payload.get("scopes", []),
    }


async def fetch_credentials(company_id: str, connector_id: str) -> Dict[str, Any]:
    """
    Fetch decrypted OAuth credentials from the gateway's internal API.

    Raises:
        httpx.HTTPStatusError: If the gateway returns an error
        RuntimeError: If credentials not found
    """
    client = get_http_client()
    resp = await client.get(
        f"{GATEWAY_INTERNAL_URL}/internal/connectors/{company_id}/{connector_id}/credentials",
        headers={"X-Internal-Secret": GATEWAY_INTERNAL_SECRET},
    )
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise RuntimeError(
            f"No credentials found for company={company_id} connector={connector_id}"
        )
    return data
