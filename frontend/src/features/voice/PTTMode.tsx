import { Mic, MicOff } from "lucide-react";

import { ChatMessages } from "@/features/chat/ChatMessages";
import { useChat } from "@/features/chat/useChat";
import { usePTT } from "@/features/voice/usePTT";
import { cn } from "@/lib/utils";

export function PTTMode() {
  const chat = useChat();
  const ptt = usePTT({
    onAudio: async (b64) => {
      const res = await chat.send("", { audio_base64: b64, audio_encoding: "mp3" });
      if (res?.audio_base64) {
        const audio = new Audio(`data:audio/mpeg;base64,${res.audio_base64}`);
        audio.play().catch(() => {});
      }
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-3 py-6">
        <button
          type="button"
          onMouseDown={ptt.start}
          onMouseUp={ptt.stop}
          onTouchStart={ptt.start}
          onTouchEnd={ptt.stop}
          className={cn(
            "relative flex size-24 items-center justify-center rounded-full transition-colors select-none",
            ptt.recording
              ? "bg-destructive text-destructive-foreground"
              : "bg-[hsl(var(--brand))] text-[hsl(var(--brand-foreground))]",
            "shadow-lg shadow-[hsl(var(--brand))]/10 active:scale-[0.97]",
          )}
          aria-label={ptt.recording ? "Recording" : "Hold to talk"}
        >
          {ptt.recording && (
            <span className="pointer-events-none absolute inset-0 animate-ping rounded-full bg-destructive/30" />
          )}
          {ptt.recording ? <MicOff className="size-7" /> : <Mic className="size-7" />}
        </button>
        <p className="text-sm text-muted-foreground">
          {ptt.recording ? "Recording — release to send" : "Hold to talk"}
        </p>
        {ptt.error && <p className="text-sm text-destructive">{ptt.error}</p>}
      </div>
      <ChatMessages messages={chat.messages} />
    </div>
  );
}
