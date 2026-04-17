import { useCallback, useRef, useState } from "react";

type Bubble = { role: "user" | "assistant"; content: string };
type Status = "idle" | "connecting" | "listening" | "error";

export function useVoiceStream() {
  const [messages, setMessages] = useState<Bubble[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const wsRef = useRef<WebSocket | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const playbackTimeRef = useRef(0);
  const micAnalyserRef = useRef<AnalyserNode | null>(null);
  const ttsAnalyserRef = useRef<AnalyserNode | null>(null);

  const start = useCallback(async () => {
    setStatus("connecting");
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const proto = location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(`${proto}//${location.host}/voice`);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = async () => {
        setStatus("listening");
        try {
          if (typeof window !== "undefined" && "AudioContext" in window) {
            const ctx = new AudioContext();
            ctxRef.current = ctx;
            playbackTimeRef.current = ctx.currentTime;
            await ctx.audioWorklet.addModule("/worklets/pcm-capture.js");
            const source = ctx.createMediaStreamSource(stream);
            const node = new AudioWorkletNode(ctx, "pcm-capture");
            node.port.onmessage = (ev) => {
              if (ws.readyState === WebSocket.OPEN) ws.send(ev.data);
            };
            source.connect(node);

            // Amplitude probes powering the reactive orb.
            const micAnalyser = ctx.createAnalyser();
            micAnalyser.fftSize = 1024;
            micAnalyser.smoothingTimeConstant = 0.6;
            source.connect(micAnalyser);
            micAnalyserRef.current = micAnalyser;

            const ttsAnalyser = ctx.createAnalyser();
            ttsAnalyser.fftSize = 1024;
            ttsAnalyser.smoothingTimeConstant = 0.6;
            ttsAnalyser.connect(ctx.destination);
            ttsAnalyserRef.current = ttsAnalyser;
          }
        } catch {
          // AudioContext / worklet unavailable (test env or restricted browser) — streaming becomes one-way
        }
      };

      ws.onmessage = (ev) => {
        if (typeof ev.data === "string") {
          const payload = JSON.parse(ev.data);
          if (payload.type === "turn") {
            setSessionId(payload.session_id);
            setMessages((m) => {
              const next: Bubble[] = [...m];
              // Skip the user bubble on the opener turn (empty transcript).
              if (payload.transcript) {
                next.push({ role: "user", content: payload.transcript });
              }
              next.push({ role: "assistant", content: payload.response });
              return next;
            });
          }
        } else {
          const ctx = ctxRef.current;
          if (!ctx) return;
          const pcm = new Int16Array(ev.data as ArrayBuffer);
          const buffer = ctx.createBuffer(1, pcm.length, 16000);
          const ch = buffer.getChannelData(0);
          for (let i = 0; i < pcm.length; i++) ch[i] = pcm[i] / 0x8000;
          const source = ctx.createBufferSource();
          source.buffer = buffer;
          source.connect(ttsAnalyserRef.current ?? ctx.destination);
          const when = Math.max(ctx.currentTime, playbackTimeRef.current);
          source.start(when);
          playbackTimeRef.current = when + buffer.duration;
        }
      };

      ws.onerror = () => setError("connection error");
      ws.onclose = (ev) => {
        setStatus("idle");
        if (ev.code === 1011) {
          setError(ev.reason || "backend not configured for voice");
        }
        streamRef.current?.getTracks().forEach((t) => t.stop());
        ctxRef.current?.close();
        micAnalyserRef.current = null;
        ttsAnalyserRef.current = null;
      };
    } catch (e) {
      setStatus("error");
      setError((e as Error).message);
    }
  }, []);

  const stop = useCallback(() => {
    wsRef.current?.send("__end__");
    wsRef.current?.close();
    wsRef.current = null;
  }, []);

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
