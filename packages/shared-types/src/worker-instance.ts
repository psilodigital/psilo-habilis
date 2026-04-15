/**
 * Worker instance overrides — client-specific tweaks to blueprint defaults.
 * Mirrors clients/<id>/workers/<worker>.instance.yaml → overrides
 */
export interface WorkerInstanceOverrides {
  model?: string;
  temperature?: number;
  approvalRequired?: boolean;
  maxConcurrentRuns?: number;
  timeoutSeconds?: number;
  policies?: {
    approval?: { overrides?: Record<string, { approval?: string }> };
    model?: { default?: string };
  };
}

/**
 * Worker instance configuration.
 * Mirrors clients/<id>/workers/<worker>.instance.yaml
 */
export interface WorkerInstance {
  instanceId: string;
  companyId: string;
  blueprintId: string;
  blueprintVersion: string;
  enabled: boolean;
  overrides: WorkerInstanceOverrides;
  contextFiles: string[];
  notes?: string;
}
