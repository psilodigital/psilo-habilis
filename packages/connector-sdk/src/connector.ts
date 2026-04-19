/**
 * Connector definition — describes an external service integration.
 *
 * Each connector maps to an MCP server that exposes tools for
 * interacting with the external service. Credentials are managed
 * per-company via the gateway's ConnectorStore.
 */

export type AuthType = "oauth2" | "api_key" | "basic";

export type ConnectorStatus = "available" | "coming_soon" | "deprecated";

export interface OAuthConfig {
  /** Google/GitHub/etc authorization URL */
  authorizationUrl: string;
  /** Token exchange URL */
  tokenUrl: string;
  /** OAuth scopes to request from the provider */
  clientScopes: string[];
}

export interface ConnectorTool {
  /** MCP tool name (e.g. "gmail_list_messages") */
  id: string;
  /** Human-readable description */
  description: string;
  /** Maps to tool-policy scope (e.g. "email_read") */
  policyScope: string;
}

export interface ConnectorDefinition {
  /** Unique connector identifier (e.g. "gmail", "slack") */
  id: string;
  /** Display name (e.g. "Gmail", "Slack") */
  name: string;
  /** Provider/vendor (e.g. "google", "slack") */
  provider: string;
  /** How the connector authenticates with the external service */
  authType: AuthType;
  /** Tool-policy scopes this connector provides (e.g. ["email_read", "email_draft"]) */
  scopes: string[];
  /** MCP server URL (within Docker network) */
  mcpServerUrl?: string;
  /** OAuth configuration (when authType is "oauth2") */
  oauthConfig?: OAuthConfig;
  /** MCP tools exposed by this connector */
  tools: ConnectorTool[];
  /** Connector availability status */
  status: ConnectorStatus;
}
