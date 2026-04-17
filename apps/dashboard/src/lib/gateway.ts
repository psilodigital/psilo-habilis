const GATEWAY_URL =
  process.env.WORKER_GATEWAY_URL || "http://localhost:8080";

export async function fetchGatewayInfo() {
  const res = await fetch(`${GATEWAY_URL}/info`, { next: { revalidate: 30 } });
  if (!res.ok) return null;
  return res.json();
}

export interface RunSummary {
  runId: string;
  status: string;
  blueprint: { id: string; version: string; name: string };
  company: { id: string; name: string };
  workerInstance: { instanceId: string; blueprintId: string };
  metadata: {
    durationMs: number;
    modelUsed: string;
    tokensUsed: number;
    startedAt: string;
    completedAt: string;
    runtimeAdapter: string;
  };
  error?: { code: string; message: string } | null;
}

export async function fetchRuns(
  limit = 50
): Promise<RunSummary[]> {
  const res = await fetch(`${GATEWAY_URL}/v1/runs?limit=${limit}`, {
    next: { revalidate: 10 },
  });
  if (!res.ok) return [];
  return res.json();
}
