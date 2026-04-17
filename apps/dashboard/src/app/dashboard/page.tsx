import { fetchGatewayInfo } from "@/lib/gateway";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default async function WorkerOverview() {
  const info = await fetchGatewayInfo();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Workers</h2>
        <p className="text-muted-foreground">
          Overview of configured workers and system status.
        </p>
      </div>

      {/* System status */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Gateway</CardDescription>
            <CardTitle className="text-lg">
              {info ? (
                <Badge variant="default">Online</Badge>
              ) : (
                <Badge variant="destructive">Offline</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-xs text-muted-foreground">
              {info
                ? `v${info.version} — ${info.runtimeAdapter} adapter`
                : "Cannot reach worker gateway"}
            </p>
          </CardContent>
        </Card>

        {info?.downstream &&
          Object.entries(info.downstream).map(([name, url]) => (
            <Card key={name}>
              <CardHeader className="pb-2">
                <CardDescription className="capitalize">{name}</CardDescription>
                <CardTitle className="text-lg">
                  <Badge variant="secondary">Configured</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground font-mono truncate">
                  {url as string}
                </p>
              </CardContent>
            </Card>
          ))}
      </div>

      {/* Workers list */}
      <div>
        <h3 className="text-lg font-semibold mb-3">Configured Workers</h3>
        <div className="grid gap-4 md:grid-cols-2">
          <WorkerCard
            name="Inbox Worker"
            blueprint="inbox-worker"
            version="1.0.0"
            status="active"
            taskKinds={["inbound_email_triage"]}
            description="Triages inbound emails: classifies intent, urgency, and sentiment, then drafts contextual replies."
          />
        </div>
      </div>
    </div>
  );
}

function WorkerCard({
  name,
  blueprint,
  version,
  status,
  taskKinds,
  description,
}: {
  name: string;
  blueprint: string;
  version: string;
  status: "active" | "idle" | "error";
  taskKinds: string[];
  description: string;
}) {
  const statusVariant =
    status === "active"
      ? "default"
      : status === "error"
        ? "destructive"
        : "secondary";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">{name}</CardTitle>
          <Badge variant={statusVariant}>{status}</Badge>
        </div>
        <CardDescription>
          {blueprint}@{version}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-sm text-muted-foreground">{description}</p>
        <div className="flex gap-1.5 flex-wrap">
          {taskKinds.map((kind) => (
            <Badge key={kind} variant="outline" className="text-xs">
              {kind}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
