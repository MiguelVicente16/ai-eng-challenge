import { useEffect, useState } from "react";
import { ChevronRight, Plus, Trash2, X } from "lucide-react";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { useMetrics, usePutMetrics } from "@/features/configure/useConfig";
import type { Metric } from "@/lib/schemas";
import { cn } from "@/lib/utils";

const TYPES = ["string", "enum", "list", "boolean", "integer", "number"] as const;

function newMetric(): Metric {
  return { name: "new_metric", type: "string", description: "" };
}

function TypeSpecific({
  metric,
  onChange,
}: {
  metric: Metric;
  onChange: (m: Metric) => void;
}) {
  if (metric.type === "string") {
    return (
      <div className="space-y-1.5">
        <Label>Max length</Label>
        <Input
          type="number"
          value={metric.max_length ?? ""}
          onChange={(e) =>
            onChange({
              ...metric,
              max_length: e.target.value ? Number(e.target.value) : null,
            } as Metric)
          }
          placeholder="Unlimited"
        />
        <p className="text-xs text-muted-foreground">
          Cap the summary length to keep it readable.
        </p>
      </div>
    );
  }
  if (metric.type === "enum") {
    return (
      <div className="space-y-1.5">
        <Label>Allowed values</Label>
        <ChipInput
          values={metric.values}
          onChange={(v) => onChange({ ...metric, values: v } as Metric)}
        />
        <p className="text-xs text-muted-foreground">
          Press Enter to add each value. At least one is required.
        </p>
      </div>
    );
  }
  if (metric.type === "list") {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label>Item type</Label>
          <Select
            value={metric.item_type}
            onValueChange={(v) =>
              onChange({ ...metric, item_type: v as Metric["type"] } as Metric)
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="string">string</SelectItem>
              <SelectItem value="integer">integer</SelectItem>
              <SelectItem value="number">number</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label>Max items</Label>
          <Input
            type="number"
            value={metric.max_items ?? ""}
            placeholder="Unlimited"
            onChange={(e) =>
              onChange({
                ...metric,
                max_items: e.target.value ? Number(e.target.value) : null,
              } as Metric)
            }
          />
        </div>
      </div>
    );
  }
  if (metric.type === "integer" || metric.type === "number") {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label>Minimum</Label>
          <Input
            type="number"
            value={metric.min ?? ""}
            onChange={(e) =>
              onChange({
                ...metric,
                min: e.target.value ? Number(e.target.value) : null,
              } as Metric)
            }
          />
        </div>
        <div className="space-y-1.5">
          <Label>Maximum</Label>
          <Input
            type="number"
            value={metric.max ?? ""}
            onChange={(e) =>
              onChange({
                ...metric,
                max: e.target.value ? Number(e.target.value) : null,
              } as Metric)
            }
          />
        </div>
      </div>
    );
  }
  return null;
}

function ChipInput({
  values,
  onChange,
}: {
  values: string[];
  onChange: (v: string[]) => void;
}) {
  const [draft, setDraft] = useState("");
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-md border bg-background px-2 py-1.5">
      {values.map((v, i) => (
        <Badge key={v + i} variant="secondary" className="gap-1 font-normal">
          {v}
          <button
            type="button"
            onClick={() => onChange(values.filter((_, j) => j !== i))}
          >
            <X className="size-3" />
          </button>
        </Badge>
      ))}
      <input
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && draft.trim()) {
            e.preventDefault();
            onChange([...values, draft.trim()]);
            setDraft("");
          }
        }}
        className="flex-1 bg-transparent py-1 text-sm outline-none placeholder:text-muted-foreground"
        placeholder={values.length ? "" : "Add a value…"}
      />
    </div>
  );
}

function MetricEditor({
  metric,
  onChange,
  onSave,
  onDelete,
}: {
  metric: Metric;
  onChange: (m: Metric) => void;
  onSave: () => void;
  onDelete: () => void;
}) {
  const patch = <K extends keyof Metric>(k: K, v: Metric[K]) =>
    onChange({ ...metric, [k]: v } as Metric);

  return (
    <div className="space-y-5">
      <div>
        <div className="text-xs uppercase tracking-wide text-muted-foreground">
          Metric
        </div>
        <div className="mt-0.5 font-mono text-sm">{metric.name}</div>
      </div>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label>Name</Label>
          <Input
            value={metric.name}
            onChange={(e) => patch("name", e.target.value as Metric["name"])}
          />
          <p className="text-xs text-muted-foreground">
            Used as the field name on the summary record.
          </p>
        </div>
        <div className="space-y-1.5">
          <Label>Type</Label>
          <Select
            value={metric.type}
            onValueChange={(v) =>
              onChange({
                ...newMetric(),
                name: metric.name,
                description: metric.description,
                type: v as Metric["type"],
              } as Metric)
            }
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {TYPES.map((t) => (
                <SelectItem key={t} value={t}>
                  {t}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="metric-description">Description</Label>
        <Textarea
          id="metric-description"
          value={metric.description ?? ""}
          onChange={(e) =>
            patch("description" as keyof Metric, e.target.value as unknown as Metric[keyof Metric])
          }
          rows={2}
          placeholder="What should the LLM extract for this field?"
        />
        <p className="text-xs text-muted-foreground">
          Shown to the summarizer LLM as part of the system prompt.
        </p>
      </div>
      <TypeSpecific metric={metric} onChange={onChange} />
      <div className="flex items-center justify-between border-t pt-4">
        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="mr-1 size-4" />
              Delete metric
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                Delete "{metric.name}"?
              </AlertDialogTitle>
              <AlertDialogDescription>
                New calls won't extract this metric anymore. Existing records
                are unaffected.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={onDelete}>Delete</AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
        <Button onClick={onSave}>Save changes</Button>
      </div>
    </div>
  );
}

export function MetricsTab() {
  const { data, isLoading } = useMetrics();
  const mutate = usePutMetrics();
  const [local, setLocal] = useState<Metric[]>([]);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);

  useEffect(() => {
    if (data) {
      setLocal(data.metrics);
      setSelectedIdx((prev) =>
        prev >= 0 && prev < data.metrics.length ? prev : 0,
      );
    }
  }, [data]);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const selected = local[selectedIdx];

  const save = () => {
    mutate.mutate({ metrics: local });
  };

  const addMetric = () => {
    const next = [...local, newMetric()];
    setLocal(next);
    setSelectedIdx(next.length - 1);
  };

  const deleteAt = (i: number) => {
    const next = local.filter((_, j) => j !== i);
    setLocal(next);
    setSelectedIdx(Math.max(0, Math.min(selectedIdx, next.length - 1)));
    mutate.mutate({ metrics: next });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Metrics</h3>
            <p className="text-xs text-muted-foreground">
              {local.length} defined
            </p>
          </div>
          <Button
            size="icon"
            variant="outline"
            className="size-8"
            onClick={addMetric}
          >
            <Plus className="size-4" />
          </Button>
        </div>
        <div className="space-y-1">
          {local.map((m, i) => (
            <button
              key={`${m.name}-${i}`}
              type="button"
              onClick={() => setSelectedIdx(i)}
              className={cn(
                "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
                i === selectedIdx
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50",
              )}
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">{m.name}</div>
                <div className="text-xs text-muted-foreground">{m.type}</div>
              </div>
              <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
            </button>
          ))}
        </div>
      </div>

      <Card>
        <CardContent className="px-6 py-6">
          {selected ? (
            <MetricEditor
              key={`${selected.name}-${selectedIdx}`}
              metric={selected}
              onChange={(m) =>
                setLocal(local.map((x, j) => (j === selectedIdx ? m : x)))
              }
              onSave={save}
              onDelete={() => deleteAt(selectedIdx)}
            />
          ) : (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No metrics yet. Add one to get started.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
