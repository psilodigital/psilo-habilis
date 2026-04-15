"""
Pydantic models for Paperclip API interactions.

These model the data exchanged with the self-hosted Paperclip control plane.
Paperclip's API is not fully documented, so these are defensive and permissive —
extra fields are allowed and optional fields have safe defaults.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Paperclip entities
# ---------------------------------------------------------------------------


class PaperclipCompany(BaseModel):
    """A company/workspace in Paperclip."""

    id: str
    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    model_config = {"extra": "allow"}


class PaperclipAgent(BaseModel):
    """An agent registered in Paperclip for a company."""

    id: str
    name: str
    type: Optional[str] = None
    status: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    model_config = {"extra": "allow"}


class PaperclipTask(BaseModel):
    """A task/run tracked by Paperclip."""

    id: str
    companyId: str
    agentId: Optional[str] = None
    status: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    model_config = {"extra": "allow"}


# ---------------------------------------------------------------------------
# Request/callback payloads
# ---------------------------------------------------------------------------


class CreateCompanyRequest(BaseModel):
    """Payload for creating a new company in Paperclip."""

    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class UpdateCompanyRequest(BaseModel):
    """Payload for updating an existing company in Paperclip."""

    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class RunCallbackPayload(BaseModel):
    """Payload sent back to Paperclip when a worker run completes."""

    runId: str
    status: str  # completed | error | timeout
    output: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
