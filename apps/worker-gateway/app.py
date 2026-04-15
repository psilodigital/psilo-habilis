"""
Psilodigital Worker Gateway — v1

Orchestration boundary between callers and the worker runtime.

Routes:
  GET  /           — root info
  GET  /health     — health check
  GET  /info       — service metadata
  POST /v1/workers/run — execute a worker task (blueprint-driven)
  POST /paperclip/wake — legacy Paperclip wake endpoint (preserved)
"""

import asyncio
import base64
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, Request
from gateway.config import settings
from gateway.logging import logger
from gateway.models import (
    Artifact,
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
from gateway.paperclip.models import RunCallbackPayload

# ---------------------------------------------------------------------------
# HTTP client + adapter lifecycle
# ---------------------------------------------------------------------------

http_client: Optional[httpx.AsyncClient] = None
runtime_adapter = None
paperclip_client: Optional[PaperclipClient] = None
config_store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client, runtime_adapter, paperclip_client, config_store
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

    logger.info(
        "Worker gateway v1.0.0 started — adapter=%s, store=%s, repo_root=%s",
        runtime_adapter.name,
        config_store.name,
        settings.repo_root,
    )
    yield
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

    # --- Step 2: Execute via runtime adapter ---
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
# POST /paperclip/wake — legacy endpoint (preserved)
# ---------------------------------------------------------------------------

@app.post("/paperclip/wake", response_model=WakeResponse, status_code=202)
async def paperclip_wake(
    payload: PaperclipWakePayload,
    request: Request,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
) -> WakeResponse:
    """Accept a Paperclip wake event and process it asynchronously."""
    # Validate auth if enabled
    if not validate_wake_auth(authorization):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "message": "Invalid or missing authorization"},
        )

    logger.info(
        "Wake received: runId=%s agentId=%s companyId=%s",
        payload.runId,
        payload.agentId,
        payload.companyId,
    )
    background_tasks.add_task(_process_wake, payload.model_dump())
    return WakeResponse(
        accepted=True,
        runId=payload.runId,
        message="Wake accepted, processing in background",
    )


async def _process_wake(payload: Dict[str, Any]) -> None:
    """Forward the wake payload to Agent Zero and call back to Paperclip."""
    run_id = payload.get("runId", "unknown")
    agent_id = payload.get("agentId", "unknown")
    callback_url = payload.get("callbackUrl")
    logger.info("Processing wake run %s for agent %s", run_id, agent_id)

    a0_token = _get_a0_api_token()
    a0_response: Optional[str] = None
    context_id: Optional[str] = None
    status = "completed"
    error_detail: Optional[str] = None

    if not a0_token:
        logger.warning("No Agent Zero API token configured")
        status = "error"
        error_detail = "No Agent Zero API token configured"
    else:
        task_input = payload.get("input") or f"Execute task for run {run_id}"
        try:
            resp = await http_client.post(
                f"{settings.agentzero_base_url}/api_message",
                headers={"Content-Type": "application/json", "X-API-KEY": a0_token},
                json={"message": task_input, "lifetime_hours": 24},
            )
            resp.raise_for_status()
            data = resp.json()
            a0_response = data.get("response", "")
            context_id = data.get("context_id")
        except Exception as exc:
            logger.error("Agent Zero call failed for run %s: %s", run_id, exc)
            status = "error"
            error_detail = str(exc)

    if context_id and a0_token:
        try:
            await http_client.post(
                f"{settings.agentzero_base_url}/api_terminate_chat",
                headers={"Content-Type": "application/json", "X-API-KEY": a0_token},
                json={"context_id": context_id},
            )
        except Exception as exc:
            logger.warning("Failed to terminate A0 context %s: %s", context_id, exc)

    # Callback to Paperclip using typed client
    target_url = callback_url or f"{settings.paperclip_base_url}/api/runs/{run_id}/complete"
    try:
        cb_payload = RunCallbackPayload(
            runId=run_id,
            status=status,
            output={"response": a0_response} if a0_response else None,
            error={"message": error_detail} if error_detail else None,
            metadata={"agentId": agent_id},
        )
        await paperclip_client.complete_run(target_url, cb_payload)
    except Exception as exc:
        logger.error("Paperclip callback failed for run %s: %s", run_id, exc)


def _get_a0_api_token() -> str:
    if settings.agentzero_api_token:
        return settings.agentzero_api_token
    if settings.agentzero_auth_login and settings.agentzero_auth_password:
        creds = f"{settings.agentzero_auth_login}:{settings.agentzero_auth_password}"
        return base64.b64encode(creds.encode()).decode()
    return ""
