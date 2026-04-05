"""
Pydantic models for the worker-gateway v1 API.

These are the Python equivalents of the TypeScript orchestration contracts.
The gateway is Python; the contracts package is TypeScript for dashboard/frontend use.
Both must stay in sync.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class TaskInputSource(BaseModel):
    type: str  # e.g. "email", "webhook", "manual"
    ref: Optional[str] = None
    timestamp: Optional[str] = None


class WorkerTaskInput(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
    source: Optional[TaskInputSource] = None


class RunOverrides(BaseModel):
    model: Optional[str] = None
    maxTokens: Optional[int] = None
    temperature: Optional[float] = None
    approvalRequired: Optional[bool] = None
    timeoutSeconds: Optional[int] = None


class WorkerRunRequest(BaseModel):
    clientId: str
    workerInstanceId: str
    blueprintId: str
    blueprintVersion: str
    taskKind: str
    input: WorkerTaskInput
    runOverrides: Optional[RunOverrides] = None


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class BlueprintInfo(BaseModel):
    id: str
    version: str
    name: str


class ClientInfo(BaseModel):
    id: str
    name: str


class WorkerInstanceInfo(BaseModel):
    instanceId: str
    blueprintId: str


class ResolvedConfig(BaseModel):
    model: str
    maxTokens: int
    temperature: float
    approvalRequired: bool
    timeoutSeconds: int


class Classification(BaseModel):
    intent: str
    urgency: str
    sentiment: str
    language: str


class Artifact(BaseModel):
    type: str
    content: str
    approvalStatus: str = "not_required"
    metadata: Optional[Dict[str, Any]] = None


class RunMetadata(BaseModel):
    durationMs: int
    modelUsed: str
    tokensUsed: int
    blueprintId: str
    blueprintVersion: str
    clientId: str
    workerInstanceId: str
    startedAt: str
    completedAt: str
    runtimeAdapter: str


class RunError(BaseModel):
    code: str
    message: str
    retryable: bool = False


class WorkerRunResponse(BaseModel):
    runId: str
    status: str  # completed | awaiting_approval | running | error | timeout
    blueprint: BlueprintInfo
    client: ClientInfo
    workerInstance: WorkerInstanceInfo
    resolvedConfig: ResolvedConfig
    classification: Optional[Classification] = None
    artifacts: List[Artifact] = Field(default_factory=list)
    metadata: RunMetadata
    error: Optional[RunError] = None


# ---------------------------------------------------------------------------
# Legacy models (kept for backward compatibility with /paperclip/wake)
# ---------------------------------------------------------------------------

class PaperclipWakePayload(BaseModel):
    runId: str
    agentId: str
    companyId: str
    input: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    callbackUrl: Optional[str] = None
    model_config = {"extra": "allow"}


class WakeResponse(BaseModel):
    accepted: bool
    runId: str
    message: str
