"""
Gmail MCP Server — Streamable HTTP transport.

Exposes Gmail read tools (list, get, search) as MCP tools.
Authentication is via short-lived session tokens (JWTs) created
by the gateway and injected into the agent's prompt.

Each tool call:
1. Validates the auth_token (JWT)
2. Fetches decrypted OAuth credentials from the gateway internal API
3. Calls the Gmail API
4. Returns structured results
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any

from mcp.server.fastmcp import FastMCP

from auth import close_http_client, fetch_credentials, validate_token
from tools.gmail import build_gmail_service, get_message, list_messages, search_messages

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("gmail-mcp")

PORT = int(os.getenv("PORT", "8090"))


@asynccontextmanager
async def lifespan(server: FastMCP):
    logger.info("Gmail MCP server starting on port %d", PORT)
    yield
    await close_http_client()
    logger.info("Gmail MCP server stopped")


mcp = FastMCP(
    "Gmail Connector",
    description="Read-only Gmail access for Habilis workers",
    lifespan=lifespan,
)


async def _get_gmail_service(auth_token: str):
    """Validate token and build authenticated Gmail service."""
    token_data = validate_token(auth_token)
    company_id = token_data["company_id"]
    connector_id = token_data["connector_id"]
    scopes = token_data["scopes"]

    if "email_read" not in scopes:
        raise PermissionError(
            f"Token does not include 'email_read' scope. Has: {scopes}"
        )

    cred_data = await fetch_credentials(company_id, connector_id)
    oauth_tokens = cred_data.get("credentials", {})
    return build_gmail_service(oauth_tokens)


@mcp.tool()
async def gmail_list_messages(
    auth_token: str,
    max_results: int = 10,
    label: str = "INBOX",
) -> str:
    """List recent emails from a Gmail inbox.

    Args:
        auth_token: Session token provided in the prompt context
        max_results: Maximum number of messages to return (1-50, default 10)
        label: Gmail label to filter by (default INBOX)
    """
    try:
        service = await _get_gmail_service(auth_token)
        messages = list_messages(
            service, max_results=max_results, label=label
        )
        return json.dumps(messages, indent=2, default=str)
    except PermissionError as exc:
        return json.dumps({"error": "permission_denied", "message": str(exc)})
    except Exception as exc:
        logger.error("gmail_list_messages failed: %s", exc)
        return json.dumps({"error": "gmail_error", "message": str(exc)})


@mcp.tool()
async def gmail_get_message(
    auth_token: str,
    message_id: str,
) -> str:
    """Get full email content by message ID.

    Args:
        auth_token: Session token provided in the prompt context
        message_id: The Gmail message ID to retrieve
    """
    try:
        service = await _get_gmail_service(auth_token)
        message = get_message(service, message_id=message_id)
        return json.dumps(message, indent=2, default=str)
    except PermissionError as exc:
        return json.dumps({"error": "permission_denied", "message": str(exc)})
    except Exception as exc:
        logger.error("gmail_get_message failed: %s", exc)
        return json.dumps({"error": "gmail_error", "message": str(exc)})


@mcp.tool()
async def gmail_search(
    auth_token: str,
    query: str,
    max_results: int = 10,
) -> str:
    """Search emails using Gmail query syntax.

    Args:
        auth_token: Session token provided in the prompt context
        query: Gmail search query (e.g. "from:user@example.com", "is:unread", "subject:invoice")
        max_results: Maximum number of results (1-50, default 10)
    """
    try:
        service = await _get_gmail_service(auth_token)
        messages = search_messages(
            service, query=query, max_results=max_results
        )
        return json.dumps(messages, indent=2, default=str)
    except PermissionError as exc:
        return json.dumps({"error": "permission_denied", "message": str(exc)})
    except Exception as exc:
        logger.error("gmail_search failed: %s", exc)
        return json.dumps({"error": "gmail_error", "message": str(exc)})


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
