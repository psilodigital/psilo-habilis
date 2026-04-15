"""Tests for the Paperclip API client."""

import pytest
import httpx
import respx
from gateway.paperclip.client import PaperclipClient, PaperclipClientError
from gateway.paperclip.models import CreateCompanyRequest, RunCallbackPayload


@pytest.fixture
def mock_client():
    return httpx.AsyncClient()


class TestPaperclipClient:
    @respx.mock
    @pytest.mark.asyncio
    async def test_health(self, mock_client):
        respx.get("http://paperclip:3100/api/health").mock(
            return_value=httpx.Response(200, json={"status": "ok"})
        )
        client = PaperclipClient(mock_client, base_url="http://paperclip:3100")
        result = await client.health()
        assert result["status"] == "ok"

    @respx.mock
    @pytest.mark.asyncio
    async def test_list_companies(self, mock_client):
        respx.get("http://paperclip:3100/api/companies").mock(
            return_value=httpx.Response(200, json=[{"id": "test", "name": "Test Co"}])
        )
        client = PaperclipClient(mock_client, base_url="http://paperclip:3100")
        result = await client.list_companies()
        assert len(result) == 1
        assert result[0]["id"] == "test"

    @respx.mock
    @pytest.mark.asyncio
    async def test_create_company(self, mock_client):
        respx.post("http://paperclip:3100/api/companies").mock(
            return_value=httpx.Response(201, json={"id": "new-co", "name": "New Company"})
        )
        client = PaperclipClient(mock_client, base_url="http://paperclip:3100")
        req = CreateCompanyRequest(name="New Company")
        result = await client.create_company(req)
        assert result["id"] == "new-co"

    @respx.mock
    @pytest.mark.asyncio
    async def test_complete_run_callback(self, mock_client):
        respx.post("http://paperclip:3100/api/runs/run-123/complete").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        client = PaperclipClient(mock_client, base_url="http://paperclip:3100")
        payload = RunCallbackPayload(runId="run-123", status="completed", output={"result": "ok"})
        result = await client.complete_run("http://paperclip:3100/api/runs/run-123/complete", payload)
        assert result["ok"] is True

    @respx.mock
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_client):
        respx.get("http://paperclip:3100/api/companies/bad").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )
        client = PaperclipClient(mock_client, base_url="http://paperclip:3100")
        with pytest.raises(PaperclipClientError) as exc_info:
            await client.get_company("bad")
        assert exc_info.value.status_code == 404
