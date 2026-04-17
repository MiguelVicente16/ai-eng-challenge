import { useRef } from "react";
import { Construction } from "lucide-react";

import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { VoiceOrb } from "@/features/voice/VoiceOrb";

/**
 * Streaming voice mode — currently disabled.
 *
 * The Deepgram Flux end-to-end pump (mic → WS → Flux → graph) is not
 * reliably producing turn events yet. Backend WS lifecycle is sound (see
 * `fix(voice): unblock event loop ...`) and the bot opener fires; the
 * remaining gap is verifying that audio frames arriving from the browser
 * actually trigger Flux `EndOfTurn` events. Diagnostic logging was added
 * to `src/agents/deepgram/streaming.py` to support that next pass.
 *
 * Use Push-to-talk in the meantime — it shares the same graph entry
 * point and is fully working.
 */
export function StreamingMode() {
  // Stable refs satisfy VoiceOrb's required prop shape without wiring real
  // analysers — orb stays visually idle.
  const noopRef = useRef<AnalyserNode | null>(null);

  return (
    <div className="space-y-4">
      <Alert>
        <Construction className="size-4" />
        <AlertTitle>Streaming mode is preview-only</AlertTitle>
        <AlertDescription>
          Real-time streaming is wired end-to-end but not yet emitting turn
          events reliably. Use <span className="font-medium">Push-to-talk</span>{" "}
          for a working voice flow. See{" "}
          <code className="font-mono text-xs">docs/architecture.md</code> →
          Voice limitations.
        </AlertDescription>
      </Alert>

      <Card className="overflow-hidden">
        <CardContent className="px-6 py-5">
          <VoiceOrb
            status="error"
            onToggle={() => {}}
            micAnalyserRef={noopRef}
            ttsAnalyserRef={noopRef}
          />
        </CardContent>
      </Card>
    </div>
  );
}
