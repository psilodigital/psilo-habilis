"""
Integration tests for the Agent Zero adapter.

These tests require a running Agent Zero instance with:
  - A valid API token (AGENTZERO_API_TOKEN env var)
  - A working model backend (LiteLLM with a provider key)

Excluded from default test runs via the 'integration' marker.

Run explicitly with:
  AGENTZERO_BASE_URL=http://localhost:50080 \
    python -m pytest -m integration tests/test_agentzero_integration.py -v
"""

import httpx
import pytest

from gateway.adapters.agentzero import AgentZeroAdapter

pytestmark = pytest.mark.integration


@pytest.fixture
async def adapter():
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:
        yield AgentZeroAdapter(client)


@pytest.mark.asyncio
async def test_simple_message(adapter):
    """Verify the adapter can send a message and get a response from A0."""
    result = await adapter.execute(
        task_kind="inbound_email_triage",
        input_message=(
            "Subject: Pricing inquiry\n\n"
            "Hi, could you share your pricing for web development services?"
        ),
        input_data=None,
        merged_config={
            "model": "worker-default",
            "approvalRequired": True,
            "timeoutSeconds": 120,
            "maxTokens": 4096,
            "temperature": 0.3,
            "_run_id": "integration-test-001",
        },
        blueprint={"id": "inbox-worker", "taskKinds": ["inbound_email_triage"]},
        client_context={"company-profile": "We are a digital agency specializing in web development."},
    )

    assert not result.is_error, f"Error: {result.error_code} - {result.error_message}"
    assert result.model_used == "worker-default"


@pytest.mark.asyncio
async def test_context_isolation(adapter):
    """Verify that separate run_ids create isolated contexts."""
    result_a = await adapter.execute(
        task_kind="inbound_email_triage",
        input_message="Subject: Test A\n\nThis is test message A.",
        input_data=None,
        merged_config={
            "model": "worker-default",
            "approvalRequired": True,
            "timeoutSeconds": 120,
            "maxTokens": 4096,
            "temperature": 0.3,
            "_run_id": "isolation-test-a",
        },
        blueprint={"id": "inbox-worker", "taskKinds": ["inbound_email_triage"]},
        client_context={},
    )

    result_b = await adapter.execute(
        task_kind="inbound_email_triage",
        input_message="Subject: Test B\n\nThis is test message B.",
        input_data=None,
        merged_config={
            "model": "worker-default",
            "approvalRequired": True,
            "timeoutSeconds": 120,
            "maxTokens": 4096,
            "temperature": 0.3,
            "_run_id": "isolation-test-b",
        },
        blueprint={"id": "inbox-worker", "taskKinds": ["inbound_email_triage"]},
        client_context={},
    )

    # Both should succeed independently
    assert not result_a.is_error, f"Run A error: {result_a.error_code}"
    assert not result_b.is_error, f"Run B error: {result_b.error_code}"
