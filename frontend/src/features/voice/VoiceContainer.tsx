import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PTTMode } from "@/features/voice/PTTMode";
import { StreamingMode } from "@/features/voice/StreamingMode";

export function VoiceContainer() {
  // Streaming runs the Pipecat pipeline (Deepgram STT → LangGraph bridge →
  // Deepgram TTS). Push-to-talk still works for low-bandwidth or no-mic
  // scenarios and is kept as a second tab.
  return (
    <Tabs defaultValue="stream" className="flex h-full w-full flex-col">
      <TabsList>
        <TabsTrigger value="stream">Streaming</TabsTrigger>
        <TabsTrigger value="ptt">Push-to-talk</TabsTrigger>
      </TabsList>
      <TabsContent value="stream" className="mt-4 min-h-0 flex-1">
        <StreamingMode />
      </TabsContent>
      <TabsContent value="ptt" className="mt-4 min-h-0 flex-1">
        <PTTMode />
      </TabsContent>
    </Tabs>
  );
}
