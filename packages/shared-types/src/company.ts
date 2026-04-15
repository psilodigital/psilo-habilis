import type { CompanyTier } from "./common";

/** Company contact information */
export interface CompanyContact {
  email: string;
  owner: string;
}

/** Platform isolation identifiers — maps to underlying service boundaries */
export interface PlatformIds {
  paperclip: { companyId: string };
  agentzero: { projectId: string };
}

/** Company-level settings */
export interface CompanySettings {
  timezone: string;
  locale: string;
  defaultModel: string;
}

/** Worker instance reference within a company */
export interface WorkerRef {
  instanceRef: string;
}

/**
 * Company configuration.
 * Mirrors clients/<id>/company.yaml
 */
export interface Company {
  id: string;
  name: string;
  displayName: string;
  industry: string;
  tier: CompanyTier;
  contact: CompanyContact;
  paperclip: PlatformIds["paperclip"];
  agentzero: PlatformIds["agentzero"];
  settings: CompanySettings;
  workers: WorkerRef[];
  context: string[];
}
