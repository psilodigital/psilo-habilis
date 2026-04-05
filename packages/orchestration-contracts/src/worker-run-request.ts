/**
 * WorkerRunRequest — the inbound contract for POST /v1/workers/run
 *
 * This is what the caller sends to execute a worker.
 * The gateway uses this to resolve blueprint + client + instance config.
 */

export interface WorkerRunRequest {
  /** Company identifier (e.g. "psilodigital") */
  companyId: string;

  /** Worker instance identifier (e.g. "psilodigital.inbox-worker") */
  workerInstanceId: string;

  /** Blueprint pack identifier (e.g. "inbox-worker") */
  blueprintId: string;

  /** Blueprint version (e.g. "1.0.0") */
  blueprintVersion: string;

  /** The kind of task to execute (e.g. "inbound_email_triage") */
  taskKind: string;

  /** Task-specific input payload */
  input: WorkerTaskInput;

  /** Optional: override config for this specific run */
  runOverrides?: Partial<WorkerRunConfig>;
}

export interface WorkerTaskInput {
  /** The primary content/message for the task */
  message: string;

  /** Structured data relevant to the task kind */
  data?: Record<string, unknown>;

  /** Optional metadata about the input source */
  source?: {
    type: string;       // e.g. "email", "webhook", "manual"
    ref?: string;       // external reference id
    timestamp?: string; // ISO 8601
  };
}

export interface WorkerRunConfig {
  model: string;
  maxTokens: number;
  temperature: number;
  approvalRequired: boolean;
  timeoutSeconds: number;
}
