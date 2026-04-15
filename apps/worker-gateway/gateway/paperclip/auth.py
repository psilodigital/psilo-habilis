"""
Paperclip authentication utilities.

Handles JWT token generation for outbound API calls to Paperclip,
and auth validation for inbound /paperclip/wake requests.
"""

import hashlib
import hmac
import time
from typing import Optional

from ..config import settings
from ..logging import logger


def generate_auth_header() -> dict:
    """
    Generate auth headers for outbound requests to Paperclip.

    Paperclip's authenticated mode uses a JWT secret for API authentication.
    This creates the appropriate Authorization header.
    """
    secret = settings.paperclip_jwt_secret
    if not secret:
        logger.warning("No Paperclip JWT secret configured, sending unauthenticated request")
        return {}

    # Paperclip uses Bearer token auth in authenticated mode
    # The token is the JWT secret itself for server-to-server calls
    return {"Authorization": f"Bearer {secret}"}


def validate_wake_auth(authorization: Optional[str]) -> bool:
    """
    Validate the Authorization header on inbound /paperclip/wake requests.

    Returns True if auth is valid or validation is disabled.
    """
    if not settings.paperclip_validate_wake_auth:
        return True

    if not authorization:
        logger.warning("Wake request missing Authorization header")
        return False

    expected_secret = settings.paperclip_jwt_secret
    if not expected_secret:
        logger.warning("Cannot validate wake auth: no JWT secret configured")
        return False

    # Expect: "Bearer <secret>"
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("Wake request has malformed Authorization header")
        return False

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(parts[1], expected_secret)
