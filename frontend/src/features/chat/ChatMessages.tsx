import { useEffect, useRef } from "react";
import { Loader2, MessageSquare, PhoneCall } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import type { Bubble } from "@/features/chat/useChat";

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function ChatMessages({
  messages,
  onStartSession,
  starting,
  pending,
}: {
  messages: Bubble[];
  onStartSession?: () => void;
  starting?: boolean;
  pending?: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  const showTyping =
    pending &&
    messages.length > 0 &&
    messages[messages.length - 1].role === "user";

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, showTyping]);

  if (messages.length === 0) {
    return (
      <ScrollArea className="h-full rounded-xl border bg-card">
        <div className="flex h-full flex-col items-center justify-center gap-6 p-10 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
            <MessageSquare className="size-5" />
          </div>
          <div className="space-y-1">
            <div className="text-base font-medium">Start a test call</div>
            <p className="max-w-sm text-sm text-muted-foreground">
              Click <span className="font-medium text-foreground">Start session</span>{" "}
              to have the assistant greet you, then reply with a scenario or your
              own message.
            </p>
          </div>
          {onStartSession && (
            <Button
              type="button"
              size="lg"
              onClick={onStartSession}
              disabled={starting}
              className="gap-2"
            >
              {starting ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Starting…
                </>
              ) : (
                <>
                  <PhoneCall className="size-4" />
                  Start session
                </>
              )}
            </Button>
          )}
        </div>
      </ScrollArea>
    );
  }

  return (
    <ScrollArea className="h-full rounded-xl border bg-card">
      <div className="flex flex-col gap-2 p-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={cn(
              "group flex",
              m.role === "user" ? "justify-end" : "justify-start",
            )}
            title={formatTime(m.ts)}
          >
            <div className="max-w-[78%]">
              <div
                className={cn(
                  "rounded-2xl px-3.5 py-2 text-sm leading-relaxed",
                  m.role === "user"
                    ? "bg-[hsl(var(--brand))] text-[hsl(var(--brand-foreground))]"
                    : "bg-muted text-foreground",
                )}
              >
                {m.content}
              </div>
              <div
                className={cn(
                  "mt-1 flex items-center gap-1.5 text-[10px] text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100",
                  m.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                <span>{formatTime(m.ts)}</span>
                {m.latencyMs !== undefined && (
                  <>
                    <span>·</span>
                    <span>{m.latencyMs} ms</span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {showTyping && (
          <div className="flex justify-start">
            <div
              className="flex items-center gap-1.5 rounded-2xl bg-muted px-3.5 py-2.5"
              aria-live="polite"
              aria-label="Assistant is typing"
            >
              <span className="size-1.5 animate-bounce rounded-full bg-foreground/40 [animation-delay:-0.3s]" />
              <span className="size-1.5 animate-bounce rounded-full bg-foreground/40 [animation-delay:-0.15s]" />
              <span className="size-1.5 animate-bounce rounded-full bg-foreground/40" />
            </div>
          </div>
        )}
        <div ref={endRef} aria-hidden className="h-px" />
      </div>
    </ScrollArea>
  );
}
