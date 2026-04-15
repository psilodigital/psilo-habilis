import type { BlueprintStatus, BlueprintCategory } from "@habilis/shared-types";

/**
 * Worker blueprint defaults — overridable per instance and per run.
 * Mirrors pack.yaml → defaults
 */
export interface BlueprintDefaults {
  model: string;
  maxTokens: number;
  temperature: number;
  approvalRequired: boolean;
  memoryEnabled: boolean;
  maxConcurrentRuns: number;
  timeoutSeconds: number;
}

/**
 * Worker blueprint — a reusable worker pack definition.
 * Mirrors worker-packs/<id>/pack.yaml
 */
export interface WorkerBlueprint {
  id: string;
  version: string;
  name: string;
  description: string;
  category: BlueprintCategory;
  status: BlueprintStatus;

  /** Task kinds this worker can handle */
  taskKinds: string[];

  /** Agent definitions — references to agent config files */
  agents: Record<string, string>;

  /** Policy file references */
  policies: {
    approval: string;
    model: string;
    memory: string;
    tools: string;
  };

  /** Output schema reference */
  outputs: {
    runResult: string;
  };

  /** Default configuration */
  defaults: BlueprintDefaults;

  /** Persona markdown file reference */
  persona: string;

  /** Playbook markdown file reference */
  playbook: string;
}
