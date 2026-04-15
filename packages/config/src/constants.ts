/** Default service ports */
export const PORTS = {
  POSTGRES: 5432,
  REDIS: 6379,
  LITELLM: 4000,
  PAPERCLIP: 3100,
  AGENTZERO: 50080,
  WORKER_GATEWAY: 8080,
  DASHBOARD: 3000,
} as const;

/** Internal Docker network service URLs */
export const INTERNAL_URLS = {
  POSTGRES: "postgresql://postgres:5432",
  REDIS: "redis://redis:6379",
  LITELLM: "http://litellm:4000",
  PAPERCLIP: "http://paperclip:3100",
  AGENTZERO: "http://agentzero:80",
  WORKER_GATEWAY: "http://worker-gateway:8080",
} as const;

/** Docker container name prefix */
export const CONTAINER_PREFIX = "psilo" as const;

/** Docker network name */
export const DOCKER_NETWORK = "workerstack" as const;
