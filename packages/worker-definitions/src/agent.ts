/**
 * Agent definition — a single agent within a worker pack.
 * Mirrors worker-packs/<id>/agents/<agent>.yaml
 */
export interface AgentDefinition {
  id: string;
  name: string;
  role: "orchestrator" | "analyst" | "drafter" | "specialist";
  description: string;
  responsibilities: string[];

  /** Agents this agent can delegate work to */
  delegatesTo?: string[];

  /** Model reference — "default" means use blueprint/instance model */
  model: string;

  /** Max tokens for this agent's model calls */
  maxTokens?: number;

  /** Temperature for this agent's model calls */
  temperature?: number;

  /** Output schema for structured responses */
  outputSchema?: {
    type: string;
    properties: Record<string, unknown>;
  };
}
