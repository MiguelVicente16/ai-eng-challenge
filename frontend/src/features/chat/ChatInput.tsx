import { useRef, useState } from "react";
import { Send } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export function ChatInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled?: boolean;
}) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const submit = () => {
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
    // Refocus for rapid testing.
    requestAnimationFrame(() => ref.current?.focus());
  };

  return (
    <form
      className="space-y-1.5"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
    >
      <div className="flex items-end gap-2 rounded-xl border bg-card p-2 shadow-sm transition-colors focus-within:border-ring/60">
        <Textarea
          ref={ref}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Type a message…"
          disabled={disabled}
          rows={1}
          className="min-h-[36px] max-h-48 resize-none border-none bg-transparent px-2 py-1.5 text-sm shadow-none focus-visible:ring-0 focus-visible:ring-offset-0"
        />
        <Button
          type="submit"
          size="icon"
          disabled={disabled || !value.trim()}
          className="size-9 shrink-0 rounded-lg"
        >
          <Send className="size-4" />
        </Button>
      </div>
      <div className="px-1 text-[11px] text-muted-foreground">
        Press <kbd className="font-mono">Enter</kbd> to send ·{" "}
        <kbd className="font-mono">Shift + Enter</kbd> for a new line
      </div>
    </form>
  );
}
