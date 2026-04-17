import { useEffect, useMemo, useState } from "react";
import { Info } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { usePhrases, usePutPhrases } from "@/features/configure/useConfig";
import {
  PHRASE_GROUPS,
  PHRASE_HINTS,
  groupForKey,
  humanPhraseLabel,
} from "@/features/configure/phrases-map";
import { cn } from "@/lib/utils";

function detectVars(template: string): string[] {
  const out = new Set<string>();
  for (const m of template.matchAll(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}/g)) {
    out.add(m[1]);
  }
  return [...out];
}

function PhraseEditor({
  phraseKey,
  value,
  onSave,
}: {
  phraseKey: string;
  value: string;
  onSave: (v: string) => void;
}) {
  const [draft, setDraft] = useState(value);
  useEffect(() => {
    setDraft(value);
  }, [value, phraseKey]);
  const dirty = draft !== value;
  const vars = detectVars(draft);
  const group = groupForKey(phraseKey);
  const hint = PHRASE_HINTS[phraseKey];

  return (
    <div className="space-y-5">
      <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wide text-muted-foreground">
          {group && <span>{group.title}</span>}
          {group && <span className="text-muted-foreground/50">·</span>}
          <span className="font-mono text-[11px] normal-case tracking-normal">
            {phraseKey}
          </span>
        </div>
        <h3 className="text-base font-semibold tracking-tight">
          {humanPhraseLabel(phraseKey)}
        </h3>
        {hint && (
          <div className="flex items-start gap-2 rounded-md bg-muted/50 px-3 py-2 text-xs text-muted-foreground">
            <Info className="mt-0.5 size-3.5 shrink-0" />
            <span>{hint}</span>
          </div>
        )}
      </div>

      <div className="space-y-2">
        <div className="text-sm font-medium">Template</div>
        <Textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={4}
          className="resize-y leading-relaxed"
        />
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-muted-foreground">Variables:</span>
          {vars.length === 0 ? (
            <span className="text-muted-foreground">none</span>
          ) : (
            vars.map((v) => (
              <span
                key={v}
                className="rounded bg-muted px-1.5 py-0.5 font-mono text-[11px]"
              >
                {`{${v}}`}
              </span>
            ))
          )}
        </div>
      </div>

      <div className="flex justify-end border-t pt-4">
        <Button disabled={!dirty} onClick={() => onSave(draft)}>
          Save changes
        </Button>
      </div>
    </div>
  );
}

export function PhrasesTab() {
  const { data, isLoading } = usePhrases();
  const mutate = usePutPhrases();
  const [local, setLocal] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      setLocal(data.phrases);
      const firstMappedKey = PHRASE_GROUPS.flatMap((g) => g.keys).find(
        (k) => data.phrases[k] !== undefined,
      );
      const fallback = Object.keys(data.phrases)[0] ?? null;
      const next = firstMappedKey ?? fallback;
      setSelected((prev) =>
        prev && data.phrases[prev] !== undefined ? prev : next,
      );
    }
  }, [data]);

  const sections = useMemo(() => {
    const mappedKeys = new Set(PHRASE_GROUPS.flatMap((g) => g.keys));
    const all = Object.keys(local);
    const known = PHRASE_GROUPS.map((g) => ({
      ...g,
      keys: g.keys.filter((k) => local[k] !== undefined),
    })).filter((g) => g.keys.length > 0);
    const unmapped = all.filter((k) => !mappedKeys.has(k));
    if (unmapped.length > 0) {
      known.push({
        id: "other",
        title: "Other",
        description: "Phrases not yet grouped by flow stage.",
        keys: unmapped,
      });
    }
    return known;
  }, [local]);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const save = (key: string, newValue: string) => {
    const next = { ...local, [key]: newValue };
    setLocal(next);
    mutate.mutate({ phrases: next });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
      <div className="space-y-5">
        {sections.map((section) => (
          <div key={section.id} className="space-y-2">
            <div>
              <h3 className="text-sm font-semibold">{section.title}</h3>
              <p className="text-xs text-muted-foreground">
                {section.description}
              </p>
            </div>
            <div className="space-y-1">
              {section.keys.map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setSelected(key)}
                  className={cn(
                    "flex w-full flex-col items-start gap-0.5 rounded-lg px-3 py-2 text-left transition-colors",
                    key === selected
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent/50",
                  )}
                >
                  <span className="text-sm font-medium">
                    {humanPhraseLabel(key)}
                  </span>
                  <span className="line-clamp-1 text-xs text-muted-foreground">
                    {local[key]}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <Card>
        <CardContent className="px-6 py-6">
          {selected !== null && local[selected] !== undefined ? (
            <PhraseEditor
              key={selected}
              phraseKey={selected}
              value={local[selected]}
              onSave={(v) => save(selected, v)}
            />
          ) : (
            <p className="py-12 text-center text-sm text-muted-foreground">
              Select a phrase on the left.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
