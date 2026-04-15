"""Tests for the FastAPI routes."""

import pytest
from httpx import AsyncClient, ASGITransport

import app as app_module
from app import app
from gateway.adapters.stub import StubRuntimeAdapter
from gateway.store.file_store import FileConfigStore
from gateway.paperclip.client import PaperclipClient
import httpx


@pytest.fixture
async def client():
    # Manually initialize globals that the lifespan normally sets up
    app_module.http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    app_module.runtime_adapter = StubRuntimeAdapter()
    app_module.config_store = FileConfigStore()
    app_module.paperclip_client = PaperclipClient(app_module.http_client)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await app_module.http_client.aclose()


class TestRoutes:
    @pytest.mark.asyncio
    async def test_root(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "worker-gateway"
        assert data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_info(self, client):
        resp = await client.get("/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "endpoints" in data
        assert "downstream" in data

    @pytest.mark.asyncio
    async def test_health(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    @pytest.mark.asyncio
    async def test_healthz_alias(self, client):
        resp = await client.get("/healthz")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_run_worker_success(self, client, sample_run_request):
        resp = await client.post("/v1/workers/run", json=sample_run_request)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("completed", "awaiting_approval")
        assert data["blueprint"]["id"] == "inbox-worker"
        assert data["company"]["id"] == "psilodigital"

    @pytest.mark.asyncio
    async def test_run_worker_blueprint_not_found(self, client, sample_run_request):
        sample_run_request["blueprintId"] = "nonexistent"
        resp = await client.post("/v1/workers/run", json=sample_run_request)
        assert resp.status_code == 200  # API returns 200 with error status
        data = resp.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "BLUEPRINT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_run_worker_unsupported_task(self, client, sample_run_request):
        sample_run_request["taskKind"] = "unsupported_task"
        resp = await client.post("/v1/workers/run", json=sample_run_request)
        data = resp.json()
        assert data["status"] == "error"
        assert data["error"]["code"] == "UNSUPPORTED_TASK_KIND"

    @pytest.mark.asyncio
    async def test_wake_endpoint(self, client):
        payload = {
            "runId": "run-test-001",
            "agentId": "agent-001",
            "companyId": "psilodigital",
            "input": "Test wake",
        }
        resp = await client.post("/paperclip/wake", json=payload)
        assert resp.status_code == 202
        data = resp.json()
        assert data["accepted"] is True
