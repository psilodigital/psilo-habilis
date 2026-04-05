/**
 * WorkerRunResponse — the outbound contract from POST /v1/workers/run
 *
 * This is what the gateway returns after processing a worker run request.
 */

/** Possible run statuses */
export type RunStatus =
  | "completed"
  | "awaiting_approval"
  | "running"
  | "error"
  | "timeout";

/** Possible approval statuses for artifacts */
export type ApprovalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "not_required";

export interface WorkerRunResponse {
  /** Unique run identifier */
  runId: string;

  /** Final status of the run */
  status: RunStatus;

  /** Resolved blueprint info */
  blueprint: {
    id: string;
    version: string;
    name: string;
  };

  /** Resolved client info */
  client: {
    id: string;
    name: string;
  };

  /** Resolved worker instance info */
  workerInstance: {
    instanceId: string;
    blueprintId: string;
  };

  /** Merged configuration that was used for this run */
  resolvedConfig: {
    model: string;
    maxTokens: number;
    temperature: number;
    approvalRequired: boolean;
    timeoutSeconds: number;
  };

  /** Classification result (for inbox-worker tasks) */
  classification?: {
    intent: string;
    urgency: string;
    sentiment: string;
    language: string;
  };

  /** Output artifacts produced by the run */
  artifacts: Artifact[];

  /** Execution metadata */
  metadata: RunMetadata;

  /** Error details (present when status is "error") */
  error?: RunError;
}

export interface Artifact {
  /** Artifact type (e.g. "draft_reply", "classification_report") */
  type: string;

  /** Artifact content */
  content: string;

  /** Approval status for this artifact */
  approvalStatus: ApprovalStatus;

  /** Additional metadata about the artifact */
  metadata?: Record<string, unknown>;
}

export interface RunMetadata {
  /** Total execution duration in milliseconds */
  durationMs: number;

  /** LiteLLM model alias used */
  modelUsed: string;

  /** Total tokens consumed */
  tokensUsed: number;

  /** Blueprint identifiers */
  blueprintId: string;
  blueprintVersion: string;

  /** Client identifier */
  clientId: string;

  /** Worker instance identifier */
  workerInstanceId: string;

  /** ISO 8601 timestamp of run start */
  startedAt: string;

  /** ISO 8601 timestamp of run completion */
  completedAt: string;

  /** Runtime adapter used */
  runtimeAdapter: string;
}

export interface RunError {
  /** Machine-readable error code */
  code: string;

  /** Human-readable error message */
  message: string;

  /** Whether this error is retryable */
  retryable?: boolean;
}

/**
 * ApprovalRequest — emitted when a run requires human approval
 */
export interface ApprovalRequest {
  runId: string;
  clientId: string;
  workerInstanceId: string;
  artifactIndex: number;
  artifact: Artifact;
  expiresAt?: string;
}
