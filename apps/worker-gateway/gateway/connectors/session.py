"""
Short-lived session tokens for MCP connector authentication.

The gateway creates a JWT containing {company_id, connector_id, scopes}
and injects it into the prompt. MCP servers validate this token to look up
the correct company's OAuth credentials via the gateway internal API.
"""

import time
from typing import Any, Dict, List

import jwt

from ..config import settings
from ..logging import logger


_ALGORITHM = "HS256"
_DEFAULT_TTL = 300  # 5 minutes


def _get_signing_key() -> str:
    key = settings.connector_encryption_key
    if not key:
        raise RuntimeError("CONNECTOR_ENCRYPTION_KEY is required for session tokens")
    return key


def create_session_token(
    *,
    company_id: str,
    connector_id: str,
    scopes: List[str],
    ttl: int = _DEFAULT_TTL,
) -> str:
    """Create a short-lived JWT for MCP tool authentication."""
    now = int(time.time())
    payload = {
        "sub": company_id,
        "cid": connector_id,
        "scopes": scopes,
        "iat": now,
        "exp": now + ttl,
    }
    token = jwt.encode(payload, _get_signing_key(), algorithm=_ALGORITHM)
    logger.info(
        "Created session token for company=%s connector=%s ttl=%ds",
        company_id,
        connector_id,
        ttl,
    )
    return token


def validate_session_token(token: str) -> Dict[str, Any]:
    """
    Validate and decode a session token.

    Returns:
        Dict with keys: sub (company_id), cid (connector_id), scopes

    Raises:
        jwt.ExpiredSignatureError: Token has expired
        jwt.InvalidTokenError: Token is invalid
    """
    payload = jwt.decode(token, _get_signing_key(), algorithms=[_ALGORITHM])
    return {
        "company_id": payload["sub"],
        "connector_id": payload["cid"],
        "scopes": payload.get("scopes", []),
    }
