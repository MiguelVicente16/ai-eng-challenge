import { useCallback, useEffect, useRef, useState } from "react";
import {
  PipecatClient,
  RTVIEvent,
  type BotLLMTextData,
  type TranscriptData,
  type TransportState,
} from "@pipecat-ai/client-js";
import {
  ProtobufFrameSerializer,
  WebSocketTransport,
} from "@pipecat-ai/websocket-transport";

import type { Bubble } from "@/features/chat/useChat";
type Status = "idle" | "connecting" | "listening" | "error";

const STATUS_BY_TRANSPORT: Partial<Record<TransportState, Status>> = {
  initializing: "connecting",
  initialized: "connecting",
  authenticating: "connecting",
  authenticated: "connecting",
  connecting: "connecting",
  connected: "connecting",
  ready: "listening",
  disconnecting: "idle",
  disconnected: "idle",
  error: "error",
};

export function usePipecatStream() {
  const [messages, setMessages] = useState<Bubble[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  // Backend session id isn't surfaced over RTVI; left in the return shape so
  // consumers can add it later without an API change.
  const [sessionId] = useState<string | undefined>(undefined);

  const clientRef = useRef<PipecatClient | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const micAnalyserRef = useRef<AnalyserNode | null>(null);
  const ttsAnalyserRef = useRef<AnalyserNode | null>(null);
  // Buffer for assistant text streamed across onBotLlmStarted → onBotLlmText → onBotLlmStopped.
  const assistantBufferRef = useRef<string>("");

  const wireAnalyser = useCallback(
    (track: MediaStreamTrack, target: "mic" | "tts") => {
      if (!audioCtxRef.current) {
        const Ctx =
          (window as typeof window & { webkitAudioContext?: typeof AudioContext }).AudioContext ??
          (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
        if (!Ctx) return;
        audioCtxRef.current = new Ctx();
      }
      const ctx = audioCtxRef.current;
      const source = ctx.createMediaStreamSource(new MediaStream([track]));
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      analyser.smoothingTimeConstant = 0.6;
      source.connect(analyser);
      if (target === "mic") micAnalyserRef.current = analyser;
      else ttsAnalyserRef.current = analyser;
    },
    [],
  );

  const start = useCallback(async () => {
    if (clientRef.current) return;
    setStatus("connecting");
    setError(null);
    setMessages([]);
    assistantBufferRef.current = "";

    const client = new PipecatClient({
      transport: new WebSocketTransport({
        serializer: new ProtobufFrameSerializer(),
      }),
      enableMic: true,
      enableCam: false,
      callbacks: {
        onTransportStateChanged: (state) => {
          const mapped = STATUS_BY_TRANSPORT[state];
          if (mapped) setStatus(mapped);
        },
        onUserTranscript: (data: TranscriptData) => {
          if (!data.final) return;
          const text = data.text.trim();
          if (!text) return;
          setMessages((prev) => [...prev, { role: "user", content: text, ts: Date.now() }]);
        },
        onBotLlmStarted: () => {
          assistantBufferRef.current = "";
        },
        onBotLlmText: (data: BotLLMTextData) => {
          assistantBufferRef.current += data.text;
        },
        onBotLlmStopped: () => {
          const text = assistantBufferRef.current.trim();
          assistantBufferRef.current = "";
          if (!text) return;
          setMessages((prev) => [...prev, { role: "assistant", content: text, ts: Date.now() }]);
        },
      },
    });

    client.on(RTVIEvent.TrackStarted, (track, participant) => {
      if (track.kind !== "audio") return;
      const isLocal = participant?.local ?? false;
      wireAnalyser(track, isLocal ? "mic" : "tts");
    });

    clientRef.current = client;

    try {
      const proto = location.protocol === "https:" ? "wss:" : "ws:";
      await client.connect({ wsUrl: `${proto}//${location.host}/voice` });
    } catch (e) {
      setStatus("error");
      setError((e as Error).message);
      clientRef.current = null;
      await client.disconnect().catch(() => {});
    }
  }, [wireAnalyser]);

  const stop = useCallback(async () => {
    const client = clientRef.current;
    clientRef.current = null;
    micAnalyserRef.current = null;
    ttsAnalyserRef.current = null;
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    if (client) {
      await client.disconnect().catch(() => {});
    }
    setStatus("idle");
  }, []);

  useEffect(() => {
    return () => {
      void stop();
    };
  }, [stop]);

  return {
    start,
    stop,
    messages,
    status,
    error,
    sessionId,
    micAnalyserRef,
    ttsAnalyserRef,
  };
}
