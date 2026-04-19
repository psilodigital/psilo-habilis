"""
Gmail API helper.

Builds an authenticated Gmail API service from OAuth credentials
and provides convenience methods for reading emails.
"""

import base64
from email.utils import parseaddr
from typing import Any, Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def build_gmail_service(oauth_tokens: Dict[str, Any]):
    """Build an authenticated Gmail API service from stored OAuth tokens."""
    creds = Credentials(
        token=oauth_tokens.get("access_token"),
        refresh_token=oauth_tokens.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=oauth_tokens.get("client_id", ""),
        client_secret=oauth_tokens.get("client_secret", ""),
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def list_messages(
    service,
    *,
    max_results: int = 10,
    label: str = "INBOX",
    query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List recent messages with basic metadata."""
    kwargs: Dict[str, Any] = {
        "userId": "me",
        "maxResults": min(max_results, 50),
        "labelIds": [label],
    }
    if query:
        kwargs["q"] = query

    result = service.users().messages().list(**kwargs).execute()
    messages = result.get("messages", [])

    summaries = []
    for msg_ref in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="metadata")
            .execute()
        )
        summaries.append(_extract_metadata(msg))

    return summaries


def get_message(service, *, message_id: str) -> Dict[str, Any]:
    """Get full email content by ID."""
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    return _extract_full_message(msg)


def search_messages(
    service, *, query: str, max_results: int = 10
) -> List[Dict[str, Any]]:
    """Search emails by Gmail query syntax."""
    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=min(max_results, 50))
        .execute()
    )
    messages = result.get("messages", [])

    summaries = []
    for msg_ref in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_ref["id"], format="metadata")
            .execute()
        )
        summaries.append(_extract_metadata(msg))

    return summaries


def _extract_metadata(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key metadata from a Gmail message."""
    headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
    return {
        "id": msg["id"],
        "threadId": msg.get("threadId"),
        "snippet": msg.get("snippet", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "labels": msg.get("labelIds", []),
    }


def _extract_full_message(msg: Dict[str, Any]) -> Dict[str, Any]:
    """Extract full message content including body."""
    metadata = _extract_metadata(msg)
    body = _extract_body(msg.get("payload", {}))
    metadata["body"] = body
    return metadata


def _extract_body(payload: Dict[str, Any]) -> str:
    """Recursively extract the text body from a message payload."""
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # Check parts (multipart messages)
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")

    # Fall back to HTML if no plain text
    if payload.get("mimeType") == "text/html" and payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        # Recurse into nested multipart
        if part.get("parts"):
            body = _extract_body(part)
            if body:
                return body

    return ""
