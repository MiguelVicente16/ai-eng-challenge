import { useMemo, useState } from "react";
import { CheckCircle2, Search as SearchIcon, XCircle } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSummariesQuery } from "@/features/summaries/useSummaries";
import { cn } from "@/lib/utils";

const SENTIMENT_STYLE: Record<
  string,
  { dot: string; text: string }
> = {
  positive: { dot: "bg-[hsl(var(--success))]", text: "text-foreground" },
  neutral: { dot: "bg-muted-foreground/60", text: "text-foreground" },
  negative: { dot: "bg-destructive", text: "text-foreground" },
};

type FilterState = {
  page: number;
  size: number;
  sentiment: string;
  resolved: "" | boolean;
  q: string;
  from: string;
  to: string;
};

const DEFAULT_FILTERS: FilterState = {
  page: 1,
  size: 20,
  sentiment: "",
  resolved: "",
  q: "",
  from: "",
  to: "",
};

function formatTime(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString([], { month: "short", day: "numeric" }),
    time: d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  };
}

function Stat({
  label,
  value,
  caption,
}: {
  label: string;
  value: string | number;
  caption?: string;
}) {
  return (
    <Card className="py-3">
      <CardContent className="px-4">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="mt-0.5 text-2xl font-semibold tabular-nums tracking-tight">
          {value}
        </div>
        {caption && (
          <div className="text-xs text-muted-foreground">{caption}</div>
        )}
      </CardContent>
    </Card>
  );
}

export function SummaryList() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const { data, isLoading } = useSummariesQuery(filters);

  const patch = (p: Partial<FilterState>) =>
    setFilters((f) => ({ ...f, page: 1, ...p }));

  const kpi = useMemo(() => {
    const items = data?.items ?? [];
    const total = data?.total ?? items.length;
    const resolved = items.filter((r) => r.metrics?.resolved === true).length;
    const positive = items.filter((r) => r.metrics?.sentiment === "positive").length;
    const resolvedPct = items.length ? Math.round((resolved / items.length) * 100) : 0;
    const positivePct = items.length ? Math.round((positive / items.length) * 100) : 0;
    return { total, resolvedPct, positivePct };
  }, [data]);

  const hasFilters =
    filters.sentiment !== "" ||
    filters.resolved !== "" ||
    filters.q !== "" ||
    filters.from !== "" ||
    filters.to !== "";

  return (
    <div className="space-y-6">
      {/* KPI strip */}
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Total calls" value={kpi.total} caption="in view" />
        <Stat
          label="Resolution rate"
          value={`${kpi.resolvedPct}%`}
          caption={`${kpi.total ? `${(data?.items ?? []).filter((r) => r.metrics?.resolved).length} of ${data?.items.length}` : "—"}`}
        />
        <Stat
          label="Positive sentiment"
          value={`${kpi.positivePct}%`}
          caption="of current page"
        />
      </div>

      {/* Toolbar: filters on one row */}
      <Card>
        <CardContent className="flex flex-col gap-3 px-4 py-3 md:flex-row md:items-center">
          <div className="relative flex-1">
            <SearchIcon className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="search"
              value={filters.q}
              onChange={(e) => patch({ q: e.target.value })}
              placeholder="Search summaries or topics"
              className="pl-9"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Select
              value={filters.sentiment || "all"}
              onValueChange={(v) => patch({ sentiment: v === "all" ? "" : v })}
            >
              <SelectTrigger id="sentiment" aria-label="Sentiment" className="w-[160px]">
                <SelectValue placeholder="Sentiment" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All sentiment</SelectItem>
                <SelectItem value="positive">Positive</SelectItem>
                <SelectItem value="neutral">Neutral</SelectItem>
                <SelectItem value="negative">Negative</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={filters.resolved === "" ? "all" : String(filters.resolved)}
              onValueChange={(v) =>
                patch({ resolved: v === "all" ? "" : v === "true" })
              }
            >
              <SelectTrigger id="resolved" aria-label="Resolved" className="w-[160px]">
                <SelectValue placeholder="Resolved" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All outcomes</SelectItem>
                <SelectItem value="true">Resolved</SelectItem>
                <SelectItem value="false">Unresolved</SelectItem>
              </SelectContent>
            </Select>
            <Input
              type="date"
              value={filters.from}
              onChange={(e) => patch({ from: e.target.value })}
              aria-label="From"
              className="w-[150px]"
            />
            <Input
              type="date"
              value={filters.to}
              onChange={(e) => patch({ to: e.target.value })}
              aria-label="To"
              className="w-[150px]"
            />
          </div>
        </CardContent>
      </Card>

      {/* Table / empty / loading */}
      {isLoading || !data ? (
        <Skeleton className="h-64 w-full" />
      ) : data.items.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 px-6 py-16 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
              <SearchIcon className="size-5" />
            </div>
            <div className="space-y-1">
              <p className="font-medium">No summaries yet</p>
              <p className="max-w-sm text-sm text-muted-foreground">
                {hasFilters
                  ? "Nothing matches these filters. Try clearing them, or run a test call to populate the log."
                  : "Generate one by running a call via Test Chat or Test Voice."}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card className="overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[160px]">When</TableHead>
                <TableHead className="w-[140px]">Session</TableHead>
                <TableHead className="w-[140px]">Sentiment</TableHead>
                <TableHead className="w-[120px]">Outcome</TableHead>
                <TableHead>Summary</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((row) => {
                const sentiment = String(row.metrics?.sentiment ?? "unknown");
                const style = SENTIMENT_STYLE[sentiment] ?? {
                  dot: "bg-muted-foreground/40",
                  text: "text-muted-foreground",
                };
                const resolved = row.metrics?.resolved === true;
                const topics = (row.metrics?.topics as string[] | undefined) ?? [];
                const { date, time } = formatTime(row.timestamp);
                return (
                  <TableRow
                    key={row.session_id}
                    onClick={() => navigate(`/summaries/${row.session_id}`)}
                    className="cursor-pointer"
                  >
                    <TableCell>
                      <div className="flex flex-col leading-tight">
                        <span className="text-sm">{date}</span>
                        <span className="text-xs text-muted-foreground">{time}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {row.session_id.slice(0, 8)}
                    </TableCell>
                    <TableCell>
                      <span className={cn("flex items-center gap-2 text-sm", style.text)}>
                        <span className={cn("inline-block size-1.5 rounded-full", style.dot)} />
                        {sentiment}
                      </span>
                    </TableCell>
                    <TableCell>
                      {resolved ? (
                        <span className="flex items-center gap-1.5 text-sm text-[hsl(var(--success))]">
                          <CheckCircle2 className="size-4" />
                          Resolved
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                          <XCircle className="size-4" />
                          Unresolved
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="min-w-0 whitespace-normal">
                      <div className="line-clamp-2 max-w-[520px] text-sm">
                        {String(row.metrics?.summary ?? "")}
                      </div>
                      {topics.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1 text-[11px] text-muted-foreground">
                          {topics.slice(0, 3).map((t) => (
                            <span
                              key={t}
                              className="rounded bg-muted px-1.5 py-0.5"
                            >
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </Card>
      )}

      {data && data.total > data.size && (
        <Pagination>
          <PaginationContent>
            <PaginationItem>
              <PaginationPrevious
                onClick={() =>
                  setFilters((f) => ({ ...f, page: Math.max(1, f.page - 1) }))
                }
              />
            </PaginationItem>
            <PaginationItem>
              <PaginationLink isActive>{filters.page}</PaginationLink>
            </PaginationItem>
            <PaginationItem>
              <PaginationNext
                onClick={() => setFilters((f) => ({ ...f, page: f.page + 1 }))}
              />
            </PaginationItem>
          </PaginationContent>
        </Pagination>
      )}
    </div>
  );
}
