import { Card, CardContent } from "@/components/ui/card";
import { ChatMessages } from "@/features/chat/ChatMessages";
import { usePipecatStream } from "@/features/voice/usePipecatStream";
import { VoiceOrb } from "@/features/voice/VoiceOrb";

/**
 * Streaming voice mode — mic → Pipecat pipeline (Deepgram STT → LangGraph
 * bridge → Deepgram TTS) → speakers, over a single WebSocket.
 *
 * The orb toggles connection; speakers animate off mic + TTS amplitude.
 * Chat bubbles are rendered from RTVI user-transcript / bot-llm-text events.
 */
export function StreamingMode() {
  const voice = usePipecatStream();
  const connected = voice.status === "listening" || voice.status === "connecting";

  const handleToggle = () => {
    if (connected) {
      void voice.stop();
    } else {
      void voice.start();
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col gap-4">
      <Card className="shrink-0 overflow-hidden">
        <CardContent className="px-6 py-4">
          <VoiceOrb
            status={voice.status}
            onToggle={handleToggle}
            micAnalyserRef={voice.micAnalyserRef}
            ttsAnalyserRef={voice.ttsAnalyserRef}
          />
          {voice.error && (
            <p className="text-center text-sm text-destructive">{voice.error}</p>
          )}
        </CardContent>
      </Card>
      <div className="min-h-0 flex-1">
        <ChatMessages messages={voice.messages} />
      </div>
    </div>
  );
}
