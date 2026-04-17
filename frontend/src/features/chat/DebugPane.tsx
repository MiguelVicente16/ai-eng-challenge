import { AlertTriangle, HelpCircle } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { useSessionState } from "@/features/chat/useSessionState";
import { cn } from "@/lib/utils";

/**
 * Maps the raw AgentState.stage values to positions on the 5-step UX strip.
 * The graph has more stages than the strip; several collapse to a single
 * step so the operator sees a steady left-to-right progression.
 */
type StepKey = "new" | "identity" | "verify" | "route" | "done";
const STRIP: { key: StepKey; label: string }[] = [
  { key: "new", label: "New" },
  { key: "identity", label: "Identity" },
  { key: "verify", label: "Verify" },
  { key: "route", label: "Route" },
  { key: "done", label: "Done" },
];

const STAGE_TO_STEP: Record<string, StepKey> = {
  new_session: "new",
  awaiting_problem: "new",
  collecting_identity: "identity",
  ask_secret: "verify",
  verifying_secret: "verify",
  routing: "route",
  clarifying: "route",
  completed: "done",
  failed: "done",
};

function StageStrip({ stage }: { stage: string | undefined }) {
  const stepKey = stage ? STAGE_TO_STEP[stage] : undefined;
  const currentIdx = stepKey ? STRIP.findIndex((s) => s.key === stepKey) : -1;
  const isFailed = stage === "failed";
  const isClarifying = stage === "clarifying";

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1.5">
        {STRIP.map((s, i) => {
          const active = i <= currentIdx;
          const isCurrent = i === currentIdx;
          return (
            <div
              key={s.key}
              className={cn(
                "flex-1 rounded-full px-2 py-1 text-center text-[10px] font-medium transition-colors",
                active
                  ? isFailed
                    ? "bg-destructive/10 text-destructive"
                    : "bg-foreground/10 text-foreground"
                  : "bg-muted text-muted-foreground",
                isCurrent && !isFailed && "ring-1 ring-foreground/30",
                isCurrent && isFailed && "ring-1 ring-destructive/40",
              )}
            >
              {s.label}
            </div>
          );
        })}
      </div>
      {isFailed && (
        <div className="flex items-center gap-1.5 rounded-md bg-destructive/10 px-2 py-1 text-[11px] text-destructive">
          <AlertTriangle className="size-3" />
          Call ended in failure
        </div>
      )}
      {isClarifying && (
        <div className="flex items-center gap-1.5 rounded-md bg-muted px-2 py-1 text-[11px] text-muted-foreground">
          <HelpCircle className="size-3" />
          Waiting for the caller to clarify
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: unknown }) {
  const empty = value === null || value === undefined || value === "";
  return (
    <div className="flex items-baseline justify-between gap-3 text-sm">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span
        className={cn(
          "min-w-0 truncate text-right",
          empty && "text-muted-foreground",
        )}
      >
        {empty ? "—" : String(value)}
      </span>
    </div>
  );
}

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
      {children}
    </div>
  );
}

export function DebugPane({
  sessionId,
  latencies,
}: {
  sessionId?: string;
  latencies: number[];
}) {
  const { data } = useSessionState(sessionId);
  const last = latencies.length ? latencies[latencies.length - 1] : undefined;
  const avg = latencies.length
    ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)
    : undefined;
  const min = latencies.length ? Math.min(...latencies) : undefined;
  const max = latencies.length ? Math.max(...latencies) : undefined;

  const verified = Boolean(data?.extracted_iban);

  return (
    <Card className="h-full">
      <CardContent className="flex h-full flex-col gap-3 px-3 py-3">
        <div className="space-y-1.5">
          <SectionTitle>Stage</SectionTitle>
          <StageStrip stage={data?.stage} />
          <div className="text-[11px] text-muted-foreground">
            Raw: <span className="font-mono text-foreground">{data?.stage ?? "—"}</span>
          </div>
        </div>

        <div className="border-t pt-2">
          <div className="mb-1 flex items-center justify-between gap-2">
            <SectionTitle>Identity</SectionTitle>
            {verified && (
              <span className="rounded-full bg-[hsl(var(--success))]/10 px-1.5 py-0.5 text-[10px] font-medium text-[hsl(var(--success))]">
                verified
              </span>
            )}
          </div>
          <div className="space-y-0.5">
            <Row label="Name" value={data?.extracted_name ?? data?.known_name_hint} />
            <Row label="IBAN" value={data?.extracted_iban} />
            <Row label="Phone" value={data?.extracted_phone} />
            <Row label="Recognized" value={data?.caller_recognized ? "yes" : undefined} />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 border-t pt-2">
          <div>
            <SectionTitle>Routing</SectionTitle>
            <div className="mt-1 space-y-0.5">
              <Row label="Service" value={data?.matched_service} />
              <Row label="Tier" value={data?.tier} />
            </div>
          </div>
          <div>
            <SectionTitle>Retries</SectionTitle>
            <div className="mt-1 space-y-0.5">
              <Row label="Stage" value={data?.retry_count} />
              <Row label="Clarify" value={data?.clarify_retry_count} />
            </div>
          </div>
        </div>

        <div className="mt-auto border-t pt-2">
          <SectionTitle>Latency</SectionTitle>
          <div className="mt-1 space-y-0.5">
            <Row label="Last" value={last !== undefined ? `${last} ms` : undefined} />
            <Row label="Avg" value={avg !== undefined ? `${avg} ms` : undefined} />
            <Row
              label="Range"
              value={
                min !== undefined && max !== undefined ? `${min} – ${max} ms` : undefined
              }
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
