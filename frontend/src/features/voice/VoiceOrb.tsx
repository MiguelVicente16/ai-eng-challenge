import { useEffect, useRef, useState, type RefObject } from "react";
import { Mic, Square } from "lucide-react";

import { cn } from "@/lib/utils";

type Status = "idle" | "connecting" | "listening" | "error";
type Speaker = "none" | "user" | "assistant";

const SPEAKING_THRESHOLD = 0.04;

export function VoiceOrb({
  status,
  onToggle,
  micAnalyserRef,
  ttsAnalyserRef,
}: {
  status: Status;
  onToggle: () => void;
  micAnalyserRef: RefObject<AnalyserNode | null>;
  ttsAnalyserRef: RefObject<AnalyserNode | null>;
}) {
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [speaker, setSpeaker] = useState<Speaker>("none");
  const active = status === "listening";
  const connecting = status === "connecting";

  useEffect(() => {
    const el = wrapperRef.current;
    if (!active) {
      if (el) {
        el.style.setProperty("--mic", "0");
        el.style.setProperty("--tts", "0");
      }
      setSpeaker("none");
      return;
    }
    let raf = 0;
    const micBuf = new Uint8Array(1024);
    const ttsBuf = new Uint8Array(1024);
    let lastSpeaker: Speaker = "none";

    const rms = (buf: Uint8Array): number => {
      let sum = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = (buf[i] - 128) / 128;
        sum += v * v;
      }
      return Math.sqrt(sum / buf.length);
    };

    const tick = () => {
      const mic = micAnalyserRef.current;
      const tts = ttsAnalyserRef.current;
      let micLvl = 0;
      let ttsLvl = 0;
      if (mic) {
        mic.getByteTimeDomainData(micBuf);
        micLvl = rms(micBuf);
      }
      if (tts) {
        tts.getByteTimeDomainData(ttsBuf);
        ttsLvl = rms(ttsBuf);
      }

      if (el) {
        // Clamp to a sensible visual range so loud bursts don't blow out scale.
        const mNorm = Math.min(1, micLvl * 2.5);
        const tNorm = Math.min(1, ttsLvl * 2.5);
        el.style.setProperty("--mic", mNorm.toFixed(3));
        el.style.setProperty("--tts", tNorm.toFixed(3));
      }

      // Assistant takes precedence — our own mic picks up TTS playback and we
      // don't want the orb to flicker between speakers.
      const next: Speaker =
        ttsLvl > SPEAKING_THRESHOLD
          ? "assistant"
          : micLvl > SPEAKING_THRESHOLD
            ? "user"
            : "none";
      if (next !== lastSpeaker) {
        lastSpeaker = next;
        setSpeaker(next);
      }

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [active, micAnalyserRef, ttsAnalyserRef]);

  const speakerLabel =
    status === "error"
      ? "Unavailable"
      : status === "connecting"
        ? "Connecting…"
        : !active
          ? "Tap to start"
          : speaker === "assistant"
            ? "Assistant speaking"
            : speaker === "user"
              ? "You're speaking"
              : "Listening";

  return (
    <div className="relative flex flex-col items-center gap-5 py-8">
      <div
        ref={wrapperRef}
        className="relative flex size-56 items-center justify-center"
        style={{ "--mic": "0", "--tts": "0" } as React.CSSProperties}
      >
        {/* Concentric reactive rings */}
        <span
          aria-hidden
          className={cn(
            "voice-ring absolute inset-0 rounded-full ring-2 transition-colors",
            speaker === "assistant"
              ? "ring-[hsl(var(--success))]/40"
              : active
                ? "ring-[hsl(var(--brand))]/40"
                : "ring-foreground/10",
          )}
          style={{ "--scale": "0.4", "--floor": "0.25" } as React.CSSProperties}
        />
        <span
          aria-hidden
          className={cn(
            "voice-ring absolute -inset-6 rounded-full ring-1 transition-colors",
            speaker === "assistant"
              ? "ring-[hsl(var(--success))]/30"
              : active
                ? "ring-[hsl(var(--brand))]/30"
                : "ring-foreground/5",
          )}
          style={{ "--scale": "0.6", "--floor": "0.15" } as React.CSSProperties}
        />
        <span
          aria-hidden
          className={cn(
            "voice-ring absolute -inset-12 rounded-full ring-1 transition-colors",
            speaker === "assistant"
              ? "ring-[hsl(var(--success))]/20"
              : active
                ? "ring-[hsl(var(--brand))]/20"
                : "ring-foreground/[0.03]",
          )}
          style={{ "--scale": "0.8", "--floor": "0.08" } as React.CSSProperties}
        />

        {/* Orb */}
        <button
          type="button"
          onClick={onToggle}
          aria-label={active ? "Stop streaming" : "Start streaming"}
          aria-pressed={active}
          className={cn(
            "voice-orb relative flex size-32 items-center justify-center rounded-full text-background shadow-2xl transition-colors",
            speaker === "assistant"
              ? "bg-[hsl(var(--success))] shadow-[hsl(var(--success))]/30"
              : active
                ? "bg-destructive shadow-destructive/30"
                : status === "error"
                  ? "bg-muted text-muted-foreground"
                  : "bg-foreground text-background shadow-foreground/20",
            connecting && "animate-pulse",
          )}
        >
          <span
            aria-hidden
            className="voice-orb-glow pointer-events-none absolute inset-0 rounded-full bg-current opacity-20 blur-2xl"
          />
          {active ? (
            <Square className="relative size-7 fill-current" />
          ) : (
            <Mic className="relative size-8" />
          )}
        </button>
      </div>

      <div className="flex flex-col items-center gap-1">
        <div
          className={cn(
            "text-base font-medium tabular-nums transition-colors",
            speaker === "assistant"
              ? "text-[hsl(var(--success))]"
              : speaker === "user"
                ? "text-[hsl(var(--brand))]"
                : "text-foreground",
          )}
        >
          {speakerLabel}
        </div>
        <div className="text-xs text-muted-foreground">
          {active
            ? "Live · streaming over WebSocket"
            : status === "error"
              ? "Voice streaming is not available"
              : "Click the orb to begin"}
        </div>
      </div>
    </div>
  );
}
