import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Clock,
  Phone,
  User2,
  XCircle,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { TranscriptBubbles } from "@/features/summaries/TranscriptBubbles";
import { useMetrics } from "@/features/configure/useConfig";
import { api } from "@/lib/api";
import type { Metric } from "@/lib/schemas";
import { cn } from "@/lib/utils";

const SENTIMENT_STYLE: Record<string, string> = {
  positive: "bg-[hsl(var(--success))]",
  neutral: "bg-muted-foreground/60",
  negative: "bg-destructive",
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString([], {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function MetricValue({ metric, value }: { metric: Metric; value: unknown }) {
  if (value === undefined || value === null)
    return <span className="text-muted-foreground">—</span>;
  if (metric.type === "enum") {
    const dot = SENTIMENT_STYLE[String(value)] ?? "bg-muted-foreground/50";
    return (
      <span className="flex items-center gap-2">
        <span className={cn("inline-block size-1.5 rounded-full", dot)} />
        {String(value)}
      </span>
    );
  }
  if (metric.type === "boolean")
    return value ? (
      <span className="flex items-center gap-1.5 text-[hsl(var(--success))]">
        <CheckCircle2 className="size-4" /> Yes
      </span>
    ) : (
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <XCircle className="size-4" /> No
      </span>
    );
  if (metric.type === "list") {
    const items = (value as unknown[]) ?? [];
    if (items.length === 0) return <span className="text-muted-foreground">—</span>;
    return (
      <div className="flex flex-wrap gap-1.5">
        {items.map((v, i) => (
          <Badge key={i} variant="secondary" className="font-normal">
            {String(v)}
          </Badge>
        ))}
      </div>
    );
  }
  return <span>{String(value)}</span>;
}

function InfoItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Clock;
  label: string;
  value: string | null | undefined;
}) {
  return (
    <div className="flex items-start gap-3">
      <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="min-w-0">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="truncate text-sm text-foreground">
          {value || <span className="text-muted-foreground">—</span>}
        </div>
      </div>
    </div>
  );
}

export function SummaryDetail() {
  const { id = "" } = useParams();
  const { data, isLoading } = useQuery({
    queryKey: ["summary", id],
    queryFn: () => api.getSummary(id),
    enabled: !!id,
  });
  const metrics = useMetrics();

  if (isLoading || metrics.isLoading) {
    return <Skeleton className="h-[60vh] w-full" />;
  }
  if (!data) {
    return (
      <Card>
        <CardContent className="py-16 text-center text-muted-foreground">
          Summary not found.
        </CardContent>
      </Card>
    );
  }

  const summaryText = String(data.metrics?.summary ?? "");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3">
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="-ml-2 w-fit text-muted-foreground"
        >
          <Link to="/summaries">
            <ArrowLeft className="mr-1 size-4" />
            All summaries
          </Link>
        </Button>
        <div className="space-y-1">
          <Badge variant="secondary" className="font-mono text-[11px]">
            {data.session_id}
          </Badge>
          {summaryText && (
            <h1 className="max-w-3xl text-xl font-semibold leading-snug tracking-tight">
              {summaryText}
            </h1>
          )}
        </div>
      </div>

      {/* Outcome run */}
      <Card>
        <CardContent className="grid gap-4 px-4 py-4 md:grid-cols-4">
          <InfoItem
            icon={Clock}
            label="When"
            value={formatDateTime(data.timestamp)}
          />
          <InfoItem
            icon={User2}
            label="Caller"
            value={data.caller_phone_masked ?? "anonymous"}
          />
          <InfoItem
            icon={Building2}
            label="Service"
            value={data.matched_service ?? null}
          />
          <InfoItem
            icon={Phone}
            label="Stage"
            value={data.stage ?? null}
          />
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px]">
        {/* Transcript */}
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Transcript</CardTitle>
          </CardHeader>
          <Separator />
          <CardContent className="pt-4">
            <TranscriptBubbles messages={data.transcript} />
          </CardContent>
        </Card>

        {/* Metrics sidebar */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Metrics</CardTitle>
            </CardHeader>
            <Separator />
            <CardContent className="space-y-3 pt-4 text-sm">
              {(metrics.data?.metrics ?? []).map((m) => (
                <div key={m.name} className="space-y-1">
                  <div className="text-xs text-muted-foreground">{m.name}</div>
                  <div>
                    <MetricValue metric={m} value={data.metrics?.[m.name]} />
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {data.tier && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm font-medium">Tier</CardTitle>
              </CardHeader>
              <Separator />
              <CardContent className="pt-4 text-sm capitalize">
                {data.tier}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Raw */}
      <Card>
        <Collapsible>
          <CardHeader className="py-3">
            <CollapsibleTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="-ml-2 w-fit text-xs text-muted-foreground"
              >
                Show raw record
              </Button>
            </CollapsibleTrigger>
          </CardHeader>
          <CollapsibleContent>
            <Separator />
            <CardContent className="pt-4">
              <pre className="overflow-auto rounded-md bg-muted p-3 font-mono text-[11px] leading-relaxed">
                {JSON.stringify(data, null, 2)}
              </pre>
            </CardContent>
          </CollapsibleContent>
        </Collapsible>
      </Card>
    </div>
  );
}
