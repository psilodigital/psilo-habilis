import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, Request

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("worker-gateway")

app = FastAPI(title="Psilodigital Worker Gateway", version="0.1.0")


@app.get("/healthz")
def healthz() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/paperclip/wake")
async def paperclip_wake(request: Request) -> Dict[str, Any]:
    payload = await request.json()
    logger.info("Received Paperclip wake payload: %s", payload)

    # TODO:
    # 1) Validate Paperclip signature / auth headers if you add them.
    # 2) Start or route a worker session.
    # 3) Call Agent Zero (or your own orchestration code).
    # 4) Call back into Paperclip using the callback/auth data you decide to use.
    #
    # This placeholder deliberately returns a simple accepted payload so the
    # bridge service is deployable from day one. Replace with your real flow.

    return {
        "accepted": True,
        "message": "Wake payload received by worker-gateway. Replace this stub with your Agent Zero bridge logic.",
        "runId": payload.get("runId"),
        "agentId": payload.get("agentId"),
        "companyId": payload.get("companyId"),
    }
