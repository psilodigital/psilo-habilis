"""
Psilodigital Worker Gateway
Bridges Paperclip HTTP adapter wake events to Agent Zero's External API.

Flow:
  1. Paperclip POSTs to /paperclip/wake with run context
  2. Gateway accepts immediately (202) and dispatches a background task
  3. Background task sends the input to Agent Zero via POST /api_message
  4. On completion, gateway calls back to Paperclip with results
"""

import asyncio
import base64
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    port: int = 8080
    log_level: str = "INFO"

    # Agent Zero
    agentzero_base_url: str = "http://agentzero:80"
    agentzero_api_token: str = ""  # from Agent Zero UI: Settings > External Services
    agentzero_auth_login: str = "admin"
    agentzero_auth_password: str = ""

    # LiteLLM (for future direct model calls from the gateway)
    litellm_base_url: str = "http://litellm:4000"
    litellm_master_key: str = ""

    # Paperclip (for callbacks)
    paperclip_base_url: str = "http://paperclip:3100"

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()

# ---------------------------------------------------------------------------
# Logging — structured JSON
# ---------------------------------------------------------------------------

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json
        log_obj = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_obj["exc"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(settings.log_level.upper())
logger = logging.getLogger("worker-gateway")

# ---------------------------------------------------------------------------
# HTTP client lifecycle
# ---------------------------------------------------------------------------

http_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global http_client
    http_client = httpx.AsyncClient(timeout=httpx.Timeout(300.0, connect=10.0))
    logger.info("Worker gateway started")
    yield
    await http_client.aclose()
    logger.info("Worker gateway stopped")

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Psilodigital Worker Gateway",
    version="0.2.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class PaperclipWakePayload(BaseModel):
    """Payload sent by Paperclip's HTTP adapter on wake."""
    runId: str
    agentId: str
    companyId: str
    input: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    callbackUrl: Optional[str] = None
    # Accept arbitrary extra fields from Paperclip
    model_config = {"extra": "allow"}


class WakeResponse(BaseModel):
    accepted: bool
    runId: str
    message: str

# ---------------------------------------------------------------------------
# Helper — resolve Agent Zero API token
# ---------------------------------------------------------------------------

def _get_a0_api_token() -> str:
    """Return the Agent Zero API token.

    Priority:
      1. Explicit AGENTZERO_API_TOKEN env var (copied from A0 UI).
      2. Fall back to computing base64(login:password) — works for basic auth
         but may not match A0's internal token format; prefer the explicit token.
    """
    if settings.agentzero_api_token:
        return settings.agentzero_api_token
    if settings.agentzero_auth_login and settings.agentzero_auth_password:
        creds = f"{settings.agentzero_auth_login}:{settings.agentzero_auth_password}"
        return base64.b64encode(creds.encode()).decode()
    return ""

# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/healthz")
async def healthz() -> Dict[str, Any]:
    """Liveness/readiness probe with optional downstream checks."""
    result: Dict[str, Any] = {"status": "ok", "downstream": {}}

    async def _check(name: str, url: str):
        try:
            r = await http_client.get(url, timeout=5.0)
            result["downstream"][name] = "ok" if r.status_code < 500 else "degraded"
        except Exception:
            result["downstream"][name] = "unreachable"

    await asyncio.gather(
        _check("agentzero", f"{settings.agentzero_base_url}/"),
        _check("litellm", f"{settings.litellm_base_url}/health"),
    )

    if any(v == "unreachable" for v in result["downstream"].values()):
        result["status"] = "degraded"

    return result

# ---------------------------------------------------------------------------
# Wake endpoint
# ---------------------------------------------------------------------------

@app.post("/paperclip/wake", response_model=WakeResponse, status_code=202)
async def paperclip_wake(
    payload: PaperclipWakePayload,
    request: Request,
    background_tasks: BackgroundTasks,
) -> WakeResponse:
    """Accept a Paperclip wake event and process it asynchronously."""
    logger.info("Wake received: runId=%s agentId=%s companyId=%s",
                payload.runId, payload.agentId, payload.companyId)

    # TODO: Validate Paperclip signature / auth header if you add one.
    # auth = request.headers.get("Authorization")

    background_tasks.add_task(_process_wake, payload.model_dump())

    return WakeResponse(
        accepted=True,
        runId=payload.runId,
        message="Wake accepted, processing in background",
    )

# ---------------------------------------------------------------------------
# Background processing
# ---------------------------------------------------------------------------

async def _process_wake(payload: Dict[str, Any]) -> None:
    """Forward the wake payload to Agent Zero and call back to Paperclip."""
    run_id = payload.get("runId", "unknown")
    agent_id = payload.get("agentId", "unknown")

    logger.info("Processing run %s for agent %s", run_id, agent_id)

    # -- Step 1: Send task to Agent Zero ---------------------------------
    a0_token = _get_a0_api_token()
    context_id: Optional[str] = None
    a0_response: Optional[str] = None
    status = "completed"
    error_detail: Optional[str] = None

    if not a0_token:
        logger.warning("No Agent Zero API token configured — "
                       "set AGENTZERO_API_TOKEN in .env (from A0 UI: Settings > External Services)")
        status = "error"
        error_detail = "Worker gateway has no Agent Zero API token configured"
    else:
        task_input = payload.get("input") or f"Execute task for run {run_id}"
        try:
            resp = await http_client.post(
                f"{settings.agentzero_base_url}/api_message",
                headers={
                    "Content-Type": "application/json",
                    "X-API-KEY": a0_token,
                },
                json={
                    "message": task_input,
                    "lifetime_hours": 24,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            a0_response = data.get("response", "")
            context_id = data.get("context_id")
            logger.info("Agent Zero responded for run %s (context=%s): %s",
                        run_id, context_id, a0_response[:200] if a0_response else "")
        except httpx.HTTPStatusError as exc:
            logger.error("Agent Zero HTTP %s for run %s: %s",
                         exc.response.status_code, run_id, exc.response.text[:500])
            status = "error"
            error_detail = f"Agent Zero returned HTTP {exc.response.status_code}"
        except Exception as exc:
            logger.error("Agent Zero call failed for run %s: %s", run_id, exc)
            status = "error"
            error_detail = f"Agent Zero unreachable: {exc}"

    # -- Step 2: Cleanup Agent Zero context ------------------------------
    if context_id and a0_token:
        try:
            await http_client.post(
                f"{settings.agentzero_base_url}/api_terminate_chat",
                headers={"Content-Type": "application/json", "X-API-KEY": a0_token},
                json={"context_id": context_id},
            )
            logger.info("Terminated Agent Zero context %s", context_id)
        except Exception as exc:
            logger.warning("Failed to terminate A0 context %s: %s", context_id, exc)

    # -- Step 3: Call back to Paperclip ----------------------------------
    await _callback_to_paperclip(run_id, {
        "status": status,
        "output": a0_response,
        "error": error_detail,
        "agentId": agent_id,
    })


async def _callback_to_paperclip(run_id: str, result: Dict[str, Any]) -> None:
    """Report task results back to Paperclip.

    TODO: The exact callback endpoint depends on your Paperclip HTTP adapter
    configuration. The path below is a reasonable guess — adjust once you
    confirm the adapter's expected callback contract.
    """
    callback_url = f"{settings.paperclip_base_url}/api/runs/{run_id}/complete"
    logger.info("Calling back to Paperclip: %s status=%s", callback_url, result.get("status"))

    try:
        resp = await http_client.post(
            callback_url,
            json=result,
            timeout=30.0,
        )
        logger.info("Paperclip callback response: HTTP %s", resp.status_code)
    except Exception as exc:
        # Don't crash — the callback is best-effort. Paperclip may also poll.
        logger.error("Paperclip callback failed for run %s: %s", run_id, exc)
