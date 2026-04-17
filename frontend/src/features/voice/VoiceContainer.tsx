import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PTTMode } from "@/features/voice/PTTMode";
import { StreamingMode } from "@/features/voice/StreamingMode";

export function VoiceContainer() {
  // Push-to-talk is the default operational mode. Streaming is kept in the
  // UI for completeness but disabled — see docs/architecture.md → Voice
  // limitations for the Deepgram Flux pump issue still pending.
  return (
    <Tabs defaultValue="ptt" className="w-full">
      <TabsList>
        <TabsTrigger value="ptt">Push-to-talk</TabsTrigger>
        <TabsTrigger
          value="stream"
          title="Streaming mode is not yet operational — see architecture docs"
        >
          Streaming (preview)
        </TabsTrigger>
      </TabsList>
      <TabsContent value="ptt" className="mt-4">
        <PTTMode />
      </TabsContent>
      <TabsContent value="stream" className="mt-4">
        <StreamingMode />
      </TabsContent>
    </Tabs>
  );
}
