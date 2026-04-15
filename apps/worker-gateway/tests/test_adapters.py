"""Tests for runtime adapters."""

import pytest
from gateway.adapters.stub import StubRuntimeAdapter


class TestStubAdapter:
    @pytest.fixture
    def adapter(self):
        return StubRuntimeAdapter()

    def test_name(self, adapter):
        assert adapter.name == "stub"

    @pytest.mark.asyncio
    async def test_execute_inbound_email_triage(self, adapter):
        result = await adapter.execute(
            task_kind="inbound_email_triage",
            input_message="Subject: Hello\n\nI want to know about your services.",
            input_data=None,
            merged_config={"model": "test", "approvalRequired": True, "timeoutSeconds": 60},
            blueprint={"id": "inbox-worker", "taskKinds": ["inbound_email_triage"]},
            client_context={},
        )
        assert not result.is_error
        assert result.classification is not None
        assert len(result.artifacts) > 0

    @pytest.mark.asyncio
    async def test_execute_returns_model_used(self, adapter):
        result = await adapter.execute(
            task_kind="inbound_email_triage",
            input_message="Test message",
            input_data=None,
            merged_config={"model": "openai/gpt-4o-mini", "approvalRequired": False, "timeoutSeconds": 60},
            blueprint={"id": "inbox-worker", "taskKinds": ["inbound_email_triage"]},
            client_context={},
        )
        assert result.model_used != ""

    @pytest.mark.asyncio
    async def test_execute_with_client_context(self, adapter):
        result = await adapter.execute(
            task_kind="inbound_email_triage",
            input_message="Test",
            input_data={"from": "test@example.com"},
            merged_config={"model": "test", "approvalRequired": True, "timeoutSeconds": 60},
            blueprint={"id": "inbox-worker", "taskKinds": ["inbound_email_triage"]},
            client_context={"company-profile": "We are a tech company."},
        )
        assert not result.is_error
