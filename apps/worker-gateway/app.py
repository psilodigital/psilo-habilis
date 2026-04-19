"""
Psilodigital Worker Gateway — v1

Orchestration boundary between callers and the worker runtime.

Routes:
  GET  /           — root info
  GET  /health     — health check
  GET  /info       — service metadata
  POST /v1/workers/run — execute a worker task (blueprint-driven)
  POST /paperclip/wake — Paperclip HTTP adapter endpoint
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Header, Request
from gateway.config import settings
from gateway.logging import logger
from gateway.models import (
    PaperclipWakePayload,
    WakeResponse,
    WorkerRunRequest,
    WorkerRunResponse,
    BlueprintInfo,
    CompanyInfo,
    WorkerInstanceInfo,
    ResolvedConfig,
    RunMetadata,
    RunError,
)
from gateway.resolver import ResolutionError, resolve_all
from gateway.adapters.stub import StubRuntimeAdapter
from gateway.adapters.agentzero import AgentZeroAdapter
from gateway.paperclip import PaperclipClient
from gateway.paperclip.auth import validate_wake_auth


# ---------------------------------------------------------------------------
# HTTP client + adapter lifecycle
# ---------------------------------------------------------------------------

http_client: Optional[httpx.AsyncClient] = None
runtime_adapter = None
paperclip_client: Optional[PaperclipClient] = None
config_store = None
run_store = None
connector_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, runtime_adapter, paperclip_client, config_store, run_store, connector_store
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0))

    # Select runtime adapter via RUNTIME_ADAPTER env var.
    # Valid values: "stub" (default), "agentzero"
    adapter_name = settings.runtime_adapter
    if adapter_name == "agentzero":
        runtime_adapter = AgentZeroAdapter(http_client)
        logger.info("Runtime adapter: agentzero (live Agent Zero integration)")
    else:
        runtime_adapter = StubRuntimeAdapter()
        if adapter_name != "stub":
            logger.warning(
                "Unknown RUNTIME_ADAPTER '%s', falling back to 'stub'", adapter_name
            )

    # Initialize Paperclip client
    paperclip_client = PaperclipClient(http_client)

    # Initialize config store
    if settings.config_store == "db" and settings.database_url:
        from gateway.store.db_store import DbConfigStore
        config_store = DbConfigStore(settings.database_url)
        await config_store.connect()
        logger.info("Config store: db (Postgres-backed)")
    else:
        from gateway.store.file_store import FileConfigStore
        config_store = FileConfigStore()
        logger.info("Config store: file (YAML on disk)")

    # Initialize run store (optional — needs asyncpg + database)
    if settings.database_url:
        try:
            from gateway.store.run_store import RunStore
            run_store = RunStore(settings.database_url)
            await run_store.connect()
            logger.info("Run store: connected")
        except Exception as exc:
            logger.warning("Run store unavailable: %s", exc)
            run_store = None

    # Initialize connector store (optional — needs encryption key + database)
    if settings.database_url and settings.connector_encryption_key:
        try:
            from gateway.store.connector_store import ConnectorStore
            connector_store = ConnectorStore(settings.database_url, settings.connector_encryption_key)
            await connector_store.connect()
            logger.info("Connector store: connected")
        except Exception as exc:
            logger.warning("Connector store unavailable: %s", exc)
            connector_store = None

    logger.info(
        "Worker gateway v1.0.0 started — adapter=%s, store=%s, repo_root=%s",
        runtime_adapter.name,
        config_store.name,
        settings.repo_root,
    )
    yield
    if connector_store and hasattr(connector_store, "close"):
        await connector_store.close()
    if run_store and hasattr(run_store, "close"):
        await run_store.close()
    if hasattr(config_store, "close"):
        await config_store.close()
    await http_client.aclose()
    logger.info("Worker gateway stopped")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Psilodigital Worker Gateway",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# GET / — root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    return {"service": "worker-gateway", "version": "1.0.0", "status": "ok"}


# ---------------------------------------------------------------------------
# GET /health — health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> Dict[str, Any]:
    """Liveness/readiness probe with optional downstream checks."""
    result: Dict[str, Any] = {"status": "ok", "version": "1.0.0", "downstream": {}}

    async def _check(name: str, url: str):
        try:
            r = await http_client.get(url, timeout=5.0)
            result["downstream"][name] = "ok" if r.status_code < 500 else "degraded"
        except Exception:
            result["downstream"][name] = "unreachable"

    await asyncio.gather(
        _check("agentzero", f"{settings.agentzero_base_url}/"),
        _check("litellm", f"{settings.litellm_base_url}/health"),
        _check("paperclip", f"{settings.paperclip_base_url}/api/health"),
    )

    if any(v == "unreachable" for v in result["downstream"].values()):
        result["status"] = "degraded"

    return result


# Preserve legacy /healthz endpoint
@app.get("/healthz")
async def healthz() -> Dict[str, Any]:
    return await health()


# ---------------------------------------------------------------------------
# GET /info — service metadata
# ---------------------------------------------------------------------------

@app.get("/info")
async def info():
    return {
        "service": "worker-gateway",
        "version": "1.0.0",
        "runtimeAdapter": runtime_adapter.name if runtime_adapter else "none",
        "endpoints": {
            "health": "/health",
            "run": "POST /v1/workers/run",
            "wake": "POST /paperclip/wake",
            "info": "/info",
        },
        "downstream": {
            "agentzero": settings.agentzero_base_url,
            "litellm": settings.litellm_base_url,
            "paperclip": settings.paperclip_base_url,
        },
    }


# ---------------------------------------------------------------------------
# POST /v1/workers/run — blueprint-driven worker execution
# ---------------------------------------------------------------------------

@app.post("/v1/workers/run", response_model=WorkerRunResponse)
async def run_worker(req: WorkerRunRequest) -> WorkerRunResponse:
    """
    Execute a worker task.

    1. Resolve blueprint + company + instance configs from disk
    2. Merge config (blueprint defaults → instance overrides → run overrides)
    3. Execute via runtime adapter
    4. Return structured response
    """
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)

    logger.info(
        "POST /v1/workers/run — runId=%s company=%s instance=%s blueprint=%s@%s task=%s",
        run_id,
        req.companyId,
        req.workerInstanceId,
        req.blueprintId,
        req.blueprintVersion,
        req.taskKind,
    )

    # --- Step 1: Resolve ---
    try:
        blueprint, company, instance, merged_config, company_context = await resolve_all(
            company_id=req.companyId,
            worker_instance_id=req.workerInstanceId,
            blueprint_id=req.blueprintId,
            blueprint_version=req.blueprintVersion,
            run_overrides=req.runOverrides.model_dump(exclude_none=True) if req.runOverrides else None,
            store=config_store,
        )
    except ResolutionError as exc:
        logger.error("Resolution failed: [%s] %s", exc.code, exc.message)
        return _error_response(
            run_id=run_id,
            req=req,
            started_at=started_at,
            error_code=exc.code,
            error_message=exc.message,
        )

    # Validate task kind against blueprint
    supported_tasks = blueprint.get("taskKinds", [])
    if supported_tasks and req.taskKind not in supported_tasks:
        logger.error(
            "Task kind '%s' not supported by blueprint '%s'. Supported: %s",
            req.taskKind,
            req.blueprintId,
            supported_tasks,
        )
        return _error_response(
            run_id=run_id,
            req=req,
            started_at=started_at,
            error_code="UNSUPPORTED_TASK_KIND",
            error_message=(
                f"Task kind '{req.taskKind}' is not supported by blueprint "
                f"'{req.blueprintId}'. Supported: {supported_tasks}"
            ),
        )

    # --- Step 1b: Resolve connectors ---
    if connector_store:
        try:
            connectors_list = await _resolve_connectors(
                company_id=req.companyId,
                blueprint=blueprint,
            )
            if connectors_list:
                merged_config["_connectors"] = connectors_list
        except Exception as exc:
            logger.warning("Connector resolution failed: %s", exc)

    # --- Step 2: Execute via runtime adapter ---
    merged_config["_run_id"] = run_id
    result = await runtime_adapter.execute(
        task_kind=req.taskKind,
        input_message=req.input.message,
        input_data=req.input.data,
        merged_config=merged_config,
        blueprint=blueprint,
        client_context=company_context,
    )

    completed_at = datetime.now(timezone.utc)
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)

    # --- Step 3: Build response ---
    if result.is_error:
        return _error_response(
            run_id=run_id,
            req=req,
            started_at=started_at,
            error_code=result.error_code,
            error_message=result.error_message,
        )

    # Determine status
    status = "completed"
    if hasattr(result, "_status_override") and result._status_override:
        status = result._status_override

    response = WorkerRunResponse(
        runId=run_id,
        status=status,
        blueprint=BlueprintInfo(
            id=req.blueprintId,
            version=req.blueprintVersion,
            name=blueprint.get("name", req.blueprintId),
        ),
        company=CompanyInfo(
            id=req.companyId,
            name=company.get("name", req.companyId),
        ),
        workerInstance=WorkerInstanceInfo(
            instanceId=req.workerInstanceId,
            blueprintId=req.blueprintId,
        ),
        resolvedConfig=ResolvedConfig(**merged_config),
        classification=result.classification,
        artifacts=result.artifacts,
        metadata=RunMetadata(
            durationMs=duration_ms,
            modelUsed=result.model_used,
            tokensUsed=result.tokens_used,
            blueprintId=req.blueprintId,
            blueprintVersion=req.blueprintVersion,
            companyId=req.companyId,
            workerInstanceId=req.workerInstanceId,
            startedAt=started_at.isoformat(),
            completedAt=completed_at.isoformat(),
            runtimeAdapter=runtime_adapter.name,
        ),
    )

    logger.info(
        "Run completed: runId=%s status=%s artifacts=%d adapter=%s duration=%dms",
        run_id,
        response.status,
        len(response.artifacts),
        runtime_adapter.name,
        duration_ms,
    )

    return response


async def _resolve_connectors(
    *, company_id: str, blueprint: Dict[str, Any]
) -> list:
    """
    Resolve active connectors for a company, cross-referenced with
    the blueprint's tool policy. Returns a list of connector dicts
    with session tokens for prompt injection.
    """
    from gateway.connectors.session import create_session_token

    if not connector_store:
        return []

    # Get allowed tool IDs from blueprint
    policies = blueprint.get("_loaded_policies", {})
    tool_policy = policies.get("tools", {})
    allowed_tool_ids = {t.get("id") for t in tool_policy.get("allowed", [])}

    # Map tool IDs to connector IDs
    _TOOL_CONNECTOR_MAP = {
        "email_read": "gmail",
        "email_draft": "gmail",
        "email_send": "gmail",
    }

    needed_connectors = set()
    for tool_id in allowed_tool_ids:
        connector_id = _TOOL_CONNECTOR_MAP.get(tool_id)
        if connector_id:
            needed_connectors.add(connector_id)

    if not needed_connectors:
        return []

    result = []
    for connector_id in needed_connectors:
        cred_data = await connector_store.get_credentials(company_id, connector_id)
        if not cred_data:
            continue

        scopes = cred_data.get("scopes", [])
        token = create_session_token(
            company_id=company_id,
            connector_id=connector_id,
            scopes=scopes,
        )
        result.append({
            "connector_id": connector_id,
            "auth_token": token,
            "scopes": scopes,
        })

    if result:
        logger.info(
            "Resolved %d connectors for company=%s: %s",
            len(result),
            company_id,
            [c["connector_id"] for c in result],
        )

    return result


def _error_response(
    *,
    run_id: str,
    req: WorkerRunRequest,
    started_at: datetime,
    error_code: str,
    error_message: str,
) -> WorkerRunResponse:
    """Build an error WorkerRunResponse."""
    completed_at = datetime.now(timezone.utc)
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)

    return WorkerRunResponse(
        runId=run_id,
        status="error",
        blueprint=BlueprintInfo(
            id=req.blueprintId,
            version=req.blueprintVersion,
            name=req.blueprintId,
        ),
        company=CompanyInfo(id=req.companyId, name=req.companyId),
        workerInstance=WorkerInstanceInfo(
            instanceId=req.workerInstanceId,
            blueprintId=req.blueprintId,
        ),
        resolvedConfig=ResolvedConfig(
            model="unknown",
            maxTokens=0,
            temperature=0,
            approvalRequired=True,
            timeoutSeconds=0,
        ),
        artifacts=[],
        metadata=RunMetadata(
            durationMs=duration_ms,
            modelUsed="none",
            tokensUsed=0,
            blueprintId=req.blueprintId,
            blueprintVersion=req.blueprintVersion,
            companyId=req.companyId,
            workerInstanceId=req.workerInstanceId,
            startedAt=started_at.isoformat(),
            completedAt=completed_at.isoformat(),
            runtimeAdapter=runtime_adapter.name if runtime_adapter else "none",
        ),
        error=RunError(code=error_code, message=error_message),
    )


# ---------------------------------------------------------------------------
# GET /v1/runs — list recent run history
# ---------------------------------------------------------------------------

@app.get("/v1/runs")
async def list_runs(
    limit: int = 50,
    companyId: Optional[str] = None,
    status: Optional[str] = None,
):
    """List recent worker runs from the run history store."""
    if not run_store:
        return []

    return await run_store.list_runs(
        limit=min(limit, 200),
        company_id=companyId,
        status=status,
    )


# ---------------------------------------------------------------------------
# POST /paperclip/wake — Paperclip HTTP adapter endpoint
# ---------------------------------------------------------------------------

@app.post("/paperclip/wake", response_model=WakeResponse)
async def paperclip_wake(
    payload: PaperclipWakePayload,
    request: Request,
    authorization: Optional[str] = Header(None),
) -> WakeResponse:
    """
    Accept a Paperclip heartbeat wake event and execute via the runtime adapter.

    Paperclip's HTTP adapter sends: { agentId, runId, context }.
    It expects a 2xx response — no callback needed.
    """
    if not validate_wake_auth(authorization):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "message": "Invalid or missing authorization"},
        )

    logger.info(
        "Wake received: runId=%s agentId=%s",
        payload.runId,
        payload.agentId,
    )

    # Extract task input from the payload
    task_input = payload.input or f"Execute task for run {payload.runId}"
    wake_context = payload.context or {}

    # Execute via the runtime adapter (same pipeline as /v1/workers/run)
    merged_config = {
        "model": "worker-default",
        "maxTokens": 4096,
        "temperature": 0.3,
        "approvalRequired": True,
        "timeoutSeconds": 120,
        "_run_id": payload.runId,
    }

    result = await runtime_adapter.execute(
        task_kind="inbound_email_triage",
        input_message=task_input,
        input_data=wake_context,
        merged_config=merged_config,
        blueprint={"id": payload.agentId, "taskKinds": ["inbound_email_triage"]},
        client_context={},
    )

    status = "error" if result.is_error else "completed"

    logger.info(
        "Wake completed: runId=%s status=%s artifacts=%d",
        payload.runId,
        status,
        len(result.artifacts),
    )

    return WakeResponse(
        accepted=True,
        runId=payload.runId,
        message=f"Wake {status}",
    )


# ---------------------------------------------------------------------------
# Connector CRUD — POST/GET/DELETE /v1/connectors
# ---------------------------------------------------------------------------

@app.post("/v1/connectors/credentials")
async def store_connector_credentials(
    request: Request,
) -> Dict[str, Any]:
    """Store connector credentials (encrypted). Called by dashboard OAuth flow."""
    if not connector_store:
        return {"error": "Connector store not available"}

    body = await request.json()
    company_id = body.get("companyId")
    connector_id = body.get("connectorId")
    scopes = body.get("scopes", [])
    credentials = body.get("credentials", {})

    if not company_id or not connector_id or not credentials:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=400,
            content={"error": "companyId, connectorId, and credentials are required"},
        )

    await connector_store.store_credentials(
        company_id=company_id,
        connector_id=connector_id,
        scopes=scopes,
        credentials=credentials,
    )
    return {"status": "stored", "companyId": company_id, "connectorId": connector_id}


@app.get("/v1/connectors/{company_id}")
async def list_connectors(company_id: str):
    """List active connectors for a company."""
    if not connector_store:
        return []
    return await connector_store.list_connectors(company_id)


@app.delete("/v1/connectors/{company_id}/{connector_id}")
async def revoke_connector(company_id: str, connector_id: str):
    """Revoke connector credentials."""
    if not connector_store:
        return {"error": "Connector store not available"}
    revoked = await connector_store.revoke_credentials(company_id, connector_id)
    return {"revoked": revoked}


# ---------------------------------------------------------------------------
# Internal API — credential lookup for MCP servers
# ---------------------------------------------------------------------------

@app.get("/internal/connectors/{company_id}/{connector_id}/credentials")
async def internal_get_credentials(
    company_id: str,
    connector_id: str,
    x_internal_secret: Optional[str] = Header(None),
):
    """
    Internal endpoint for MCP servers to fetch decrypted credentials.
    Authenticated via X-Internal-Secret header.
    """
    if not settings.gateway_internal_secret or x_internal_secret != settings.gateway_internal_secret:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=403,
            content={"error": "Forbidden"},
        )

    if not connector_store:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"error": "Connector store not available"},
        )

    result = await connector_store.get_credentials(company_id, connector_id)
    if not result:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"error": f"No active credentials for {connector_id}"},
        )

    return result
