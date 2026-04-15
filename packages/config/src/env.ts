import { z } from "zod";

/**
 * Shared environment variable schema.
 * Validates the env vars that multiple services depend on.
 */
export const sharedEnvSchema = z.object({
  // Postgres
  POSTGRES_USER: z.string().default("postgres"),
  POSTGRES_PASSWORD: z.string().min(1, "POSTGRES_PASSWORD is required"),
  POSTGRES_DB: z.string().default("postgres"),

  // Redis
  REDIS_URL: z.string().url().optional(),

  // LiteLLM
  LITELLM_BASE_URL: z.string().url().default("http://litellm:4000"),
  LITELLM_MASTER_KEY: z
    .string()
    .startsWith("sk-", "LITELLM_MASTER_KEY must start with sk-"),

  // Paperclip
  PAPERCLIP_BASE_URL: z.string().url().default("http://paperclip:3100"),
  PAPERCLIP_AGENT_JWT_SECRET: z
    .string()
    .min(32, "PAPERCLIP_AGENT_JWT_SECRET must be at least 32 characters"),

  // Agent Zero
  AGENTZERO_BASE_URL: z.string().url().default("http://agentzero:80"),
  AGENTZERO_AUTH_LOGIN: z.string().default("admin"),
  AGENTZERO_AUTH_PASSWORD: z.string().min(1, "AGENTZERO_AUTH_PASSWORD is required"),
});

export type SharedEnv = z.infer<typeof sharedEnvSchema>;
