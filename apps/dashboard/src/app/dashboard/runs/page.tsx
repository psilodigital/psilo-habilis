import { fetchRuns, type RunSummary } from "@/lib/gateway";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default async function RunHistoryPage() {
  const runs = await fetchRuns();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Run History</h2>
        <p className="text-muted-foreground">
          Recent worker executions and their results.
        </p>
      </div>

      {runs.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center">
          <p className="text-muted-foreground">
            No runs yet. Trigger a worker execution to see results here.
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Run ID</TableHead>
                <TableHead>Worker</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Model</TableHead>
                <TableHead>Started</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {runs.map((run) => (
                <RunRow key={run.runId} run={run} />
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}

function RunRow({ run }: { run: RunSummary }) {
  const statusVariant =
    run.status === "completed"
      ? "default"
      : run.status === "error"
        ? "destructive"
        : "secondary";

  const durationSec = (run.metadata.durationMs / 1000).toFixed(1);
  const startedAt = new Date(run.metadata.startedAt).toLocaleString();

  return (
    <TableRow>
      <TableCell className="font-mono text-xs">
        {run.runId.slice(0, 8)}...
      </TableCell>
      <TableCell>{run.blueprint.name}</TableCell>
      <TableCell>
        <Badge variant={statusVariant}>{run.status}</Badge>
      </TableCell>
      <TableCell>{durationSec}s</TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {run.metadata.modelUsed}
      </TableCell>
      <TableCell className="text-xs text-muted-foreground">
        {startedAt}
      </TableCell>
    </TableRow>
  );
}
