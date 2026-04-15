/**
 * Approval policy — controls when human approval is required.
 * Mirrors worker-packs/<id>/policies/approval-policy.yaml
 */
export interface ApprovalRule {
  action: "draft_reply" | "auto_archive" | "forward" | "escalate";
  approval: "require_approval" | "none";
  description: string;
}

export interface ApprovalPolicy {
  id: string;
  name: string;
  description: string;
  rules: {
    default: "require_approval" | "none";
    overrides: Record<string, ApprovalRule>;
  };
}

/**
 * Model policy — controls model routing, overrides, and budget.
 * Mirrors worker-packs/<id>/policies/model-policy.yaml
 */
export interface ModelPolicyAgent {
  model: string;
  reason: string;
}

export interface ModelPolicy {
  id: string;
  name: string;
  description: string;
  default: string;
  agents: Record<string, ModelPolicyAgent>;
  budget: {
    maxTokensPerRun: number;
    maxCostPerRun: string;
  };
  routing: {
    gateway: string;
    baseUrl: string;
  };
}

/**
 * Memory policy — controls cross-run persistence.
 * Mirrors worker-packs/<id>/policies/memory-policy.yaml
 */
export interface MemoryPolicy {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  remember: string[];
  doNotRemember: string[];
  isolation: {
    scope: string;
    description: string;
  };
}

/**
 * Tool entry — a single tool reference within a tool policy.
 */
export interface ToolEntry {
  id: string;
  description: string;
  scope?: string;
  reason?: string;
}

/**
 * Tool policy — controls which tools the worker can use.
 * Mirrors worker-packs/<id>/policies/tool-policy.yaml
 */
export interface ToolPolicy {
  id: string;
  name: string;
  description: string;
  allowed: ToolEntry[];
  denied: ToolEntry[];
  planned: ToolEntry[];
}
