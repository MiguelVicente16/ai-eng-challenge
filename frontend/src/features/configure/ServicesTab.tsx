import { useEffect, useState } from "react";
import { useForm, useFieldArray, FormProvider } from "react-hook-form";
import type { UseFieldArrayReturn, UseFormRegister } from "react-hook-form";
import { ChevronRight, Phone, Plus, Trash2 } from "lucide-react";

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
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouting, usePutRouting } from "@/features/configure/useConfig";
import type { ServicesConfig } from "@/lib/schemas";
import { cn } from "@/lib/utils";

type RuleList = { yes_rules: { value: string }[]; no_rules: { value: string }[] };
type ServiceRow = { key: string; label: string; dept_phone: string } & RuleList;

function toRow(k: string, v: ServicesConfig["services"][string]): ServiceRow {
  return {
    key: k,
    label: v.label,
    dept_phone: v.dept_phone,
    yes_rules: v.yes_rules.map((x) => ({ value: x })),
    no_rules: v.no_rules.map((x) => ({ value: x })),
  };
}

function fromRow(row: ServiceRow) {
  return {
    label: row.label,
    dept_phone: row.dept_phone,
    yes_rules: row.yes_rules.map((r) => r.value).filter(Boolean),
    no_rules: row.no_rules.map((r) => r.value).filter(Boolean),
  };
}

function RuleListEditor({
  title,
  hint,
  fa,
  inputName,
  register,
}: {
  title: string;
  hint: string;
  fa: UseFieldArrayReturn<ServiceRow, "yes_rules" | "no_rules">;
  inputName: "yes_rules" | "no_rules";
  register: UseFormRegister<ServiceRow>;
}) {
  return (
    <div className="space-y-2">
      <div>
        <div className="text-sm font-medium">{title}</div>
        <div className="text-xs text-muted-foreground">{hint}</div>
      </div>
      <div className="space-y-2">
        {fa.fields.map((f, i) => (
          <div key={f.id} className="flex gap-2">
            <Input
              {...register(`${inputName}.${i}.value` as const)}
              placeholder="e.g. Customer mentions…"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              onClick={() => fa.remove(i)}
            >
              <Trash2 className="size-4 text-muted-foreground" />
            </Button>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => fa.append({ value: "" })}
        >
          <Plus className="mr-1 size-4" />
          Add rule
        </Button>
      </div>
    </div>
  );
}

function ServiceEditor({
  row,
  onSave,
  onDelete,
}: {
  row: ServiceRow;
  onSave: (r: ServiceRow) => void;
  onDelete: () => void;
}) {
  const form = useForm<ServiceRow>({ defaultValues: row });
  const yes = useFieldArray({ control: form.control, name: "yes_rules" });
  const no = useFieldArray({ control: form.control, name: "no_rules" });

  useEffect(() => {
    form.reset(row);
  }, [row, form]);

  return (
    <FormProvider {...form}>
      <form
        className="space-y-6"
        onSubmit={form.handleSubmit((v) => onSave(v))}
      >
        <div>
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            Service key
          </div>
          <div className="mt-0.5 font-mono text-sm">{row.key}</div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor="label">Label</Label>
            <Input id="label" {...form.register("label")} />
            <p className="text-xs text-muted-foreground">
              Shown to callers, e.g. "Cards" or "Loans & Mortgages".
            </p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="dept_phone">Department phone</Label>
            <Input
              id="dept_phone"
              {...form.register("dept_phone")}
              className="font-mono"
              placeholder="+1 555 555 5555"
            />
            <p className="text-xs text-muted-foreground">
              Number the assistant hands off to.
            </p>
          </div>
        </div>
        <RuleListEditor
          title="Route to this service when"
          hint="Every rule is a short phrase the LLM evaluates against the user message."
          fa={yes}
          inputName="yes_rules"
          register={form.register}
        />
        <RuleListEditor
          title="Never route here when"
          hint="Negative examples that should land somewhere else."
          fa={no}
          inputName="no_rules"
          register={form.register}
        />
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
                Delete service
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>
                  Delete "{row.label || row.key}"?
                </AlertDialogTitle>
                <AlertDialogDescription>
                  Calls routed here will fall through to general support. This
                  can be restored by adding the service back.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={onDelete}>Delete</AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
          <Button type="submit">Save changes</Button>
        </div>
      </form>
    </FormProvider>
  );
}

function AddServiceDialog({
  onCreate,
  existingKeys,
}: {
  onCreate: (key: string, label: string) => void;
  existingKeys: string[];
}) {
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState("");
  const [label, setLabel] = useState("");

  const normalized = key.trim().toLowerCase().replace(/[^a-z0-9_-]+/g, "_");
  const duplicate = normalized !== "" && existingKeys.includes(normalized);

  const create = () => {
    if (!normalized || duplicate) return;
    onCreate(normalized, label.trim() || normalized);
    setKey("");
    setLabel("");
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button size="icon" variant="outline" className="size-8">
          <Plus className="size-4" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New service</DialogTitle>
        </DialogHeader>
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="new-key">Key</Label>
            <Input
              id="new-key"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="mortgages"
              className="font-mono"
            />
            <p className="text-xs text-muted-foreground">
              Stable identifier. Lowercase letters, numbers, and underscores
              only.
            </p>
            {duplicate && (
              <p className="text-xs text-destructive">
                A service with this key already exists.
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new-label">Label</Label>
            <Input
              id="new-label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Mortgages"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={create} disabled={!normalized || duplicate}>
            Create
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function ServicesTab() {
  const { data, isLoading } = useRouting();
  const mutate = usePutRouting();
  const [rows, setRows] = useState<ServiceRow[]>([]);
  const [selectedKey, setSelectedKey] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      const next = Object.entries(data.services).map(([k, v]) => toRow(k, v));
      setRows(next);
      setSelectedKey((prev) =>
        prev && next.some((r) => r.key === prev) ? prev : next[0]?.key ?? null,
      );
    }
  }, [data]);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const selectedRow = rows.find((r) => r.key === selectedKey);

  const saveRow = (updated: ServiceRow) => {
    const nextRows = rows.map((r) => (r.key === updated.key ? updated : r));
    setRows(nextRows);
    const payload: ServicesConfig = {
      services: Object.fromEntries(nextRows.map((r) => [r.key, fromRow(r)])),
    };
    mutate.mutate(payload);
  };

  const deleteRow = (key: string) => {
    const kept = rows.filter((r) => r.key !== key);
    setRows(kept);
    setSelectedKey(kept[0]?.key ?? null);
    const payload: ServicesConfig = {
      services: Object.fromEntries(kept.map((r) => [r.key, fromRow(r)])),
    };
    mutate.mutate(payload);
  };

  const addService = (key: string, label: string) => {
    const newRow: ServiceRow = {
      key,
      label,
      dept_phone: "",
      yes_rules: [],
      no_rules: [],
    };
    const nextRows = [...rows, newRow];
    setRows(nextRows);
    setSelectedKey(key);
    const payload: ServicesConfig = {
      services: Object.fromEntries(nextRows.map((r) => [r.key, fromRow(r)])),
    };
    mutate.mutate(payload);
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold">Services</h3>
            <p className="text-xs text-muted-foreground">
              {rows.length} configured
            </p>
          </div>
          <AddServiceDialog
            onCreate={addService}
            existingKeys={rows.map((r) => r.key)}
          />
        </div>
        <div className="space-y-1">
          {rows.map((row) => (
            <button
              key={row.key}
              type="button"
              onClick={() => setSelectedKey(row.key)}
              className={cn(
                "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors",
                row.key === selectedKey
                  ? "bg-accent text-accent-foreground"
                  : "hover:bg-accent/50",
              )}
            >
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium">
                  {row.label || row.key}
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                  <Phone className="size-3" />
                  <span className="truncate font-mono">
                    {row.dept_phone || "—"}
                  </span>
                </div>
              </div>
              <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
            </button>
          ))}
        </div>
      </div>

      <Card>
        <CardContent className="px-6 py-6">
          {selectedRow ? (
            <ServiceEditor
              key={selectedRow.key}
              row={selectedRow}
              onSave={saveRow}
              onDelete={() => deleteRow(selectedRow.key)}
            />
          ) : (
            <p className="py-12 text-center text-sm text-muted-foreground">
              Select a service on the left, or add a new one.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
