/**
 * Connector registry — static catalog of available connectors.
 *
 * In v1, this is a hardcoded map. Future versions may load
 * from a database or external config.
 */

import type { ConnectorDefinition } from "./connector.js";

export const CONNECTOR_REGISTRY: Record<string, ConnectorDefinition> = {
  gmail: {
    id: "gmail",
    name: "Gmail",
    provider: "google",
    authType: "oauth2",
    scopes: ["email_read"],
    mcpServerUrl: "http://gmail-mcp:8090/mcp",
    oauthConfig: {
      authorizationUrl: "https://accounts.google.com/o/oauth2/v2/auth",
      tokenUrl: "https://oauth2.googleapis.com/token",
      clientScopes: [
        "https://www.googleapis.com/auth/gmail.readonly",
      ],
    },
    tools: [
      {
        id: "gmail_list_messages",
        description: "List recent emails from a Gmail inbox",
        policyScope: "email_read",
      },
      {
        id: "gmail_get_message",
        description: "Get full email content by message ID",
        policyScope: "email_read",
      },
      {
        id: "gmail_search",
        description: "Search emails using Gmail query syntax",
        policyScope: "email_read",
      },
    ],
    status: "available",
  },
};

export function getConnector(id: string): ConnectorDefinition | undefined {
  return CONNECTOR_REGISTRY[id];
}

export function listConnectors(): ConnectorDefinition[] {
  return Object.values(CONNECTOR_REGISTRY);
}
