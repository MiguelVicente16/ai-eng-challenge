import { cn } from "@/lib/utils";

type Bubble = { role: "user" | "assistant"; content: string };

export function TranscriptBubbles({
  messages,
}: {
  messages: Bubble[];
}) {
  if (!messages.length) {
    return (
      <p className="py-6 text-center text-sm text-muted-foreground">
        No transcript.
      </p>
    );
  }
  return (
    <div className="flex flex-col gap-2">
      {messages.map((m, i) => (
        <div
          key={i}
          className={cn(
            "flex",
            m.role === "user" ? "justify-end" : "justify-start",
          )}
        >
          <div
            className={cn(
              "max-w-[78%] rounded-2xl px-3.5 py-2 text-sm leading-relaxed",
              m.role === "user"
                ? "bg-[hsl(var(--brand))] text-[hsl(var(--brand-foreground))]"
                : "bg-muted text-foreground",
            )}
          >
            {m.content}
          </div>
        </div>
      ))}
    </div>
  );
}
