import { useCallback, useMemo, useState } from "react";

import { api, type ChatTurnRequest } from "@/lib/api";

export type Bubble = {
  role: "user" | "assistant";
  content: string;
  latencyMs?: number;
  ts: number;
};

export function useChat() {
  const [messages, setMessages] = useState<Bubble[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [callerPhone, setCallerPhone] = useState<string | undefined>();

  const send = useCallback(
    async (text: string, extra?: Partial<ChatTurnRequest>) => {
      if (!text.trim() && !extra?.audio_base64) return;
      setPending(true);
      setError(null);
      const sentAt = Date.now();
      setMessages((m) => [
        ...m,
        { role: "user", content: text || "(audio)", ts: sentAt },
      ]);
      const started = performance.now();
      try {
        const payload: ChatTurnRequest = {
          message: text,
          session_id: sessionId,
          ...extra,
        };
        // Attach caller phone only on the very first turn of a session.
        if (!sessionId && callerPhone) {
          payload.caller_phone = callerPhone;
        }
        const res = await api.postChat(payload);
        setSessionId(res.session_id);
        const latencyMs = Math.round(performance.now() - started);
        setMessages((m) => {
          const next = [...m];
          if (res.transcript && extra?.audio_base64) {
            next[next.length - 1] = {
              role: "user",
              content: res.transcript,
              ts: sentAt,
            };
          }
          return [
            ...next,
            {
              role: "assistant",
              content: res.response,
              latencyMs,
              ts: Date.now(),
            },
          ];
        });
        return res;
      } catch (e) {
        setError((e as Error).message);
        return null;
      } finally {
        setPending(false);
      }
    },
    [sessionId, callerPhone],
  );

  const newSession = useCallback((nextCallerPhone?: string) => {
    setMessages([]);
    setSessionId(undefined);
    setError(null);
    setCallerPhone(nextCallerPhone);
  }, []);

  const startSession = useCallback(async (nextCallerPhone?: string) => {
    setMessages([]);
    setSessionId(undefined);
    setError(null);
    setCallerPhone(nextCallerPhone);
    setPending(true);
    const started = performance.now();
    try {
      const payload: ChatTurnRequest = { message: "" };
      if (nextCallerPhone) payload.caller_phone = nextCallerPhone;
      const res = await api.postChat(payload);
      setSessionId(res.session_id);
      const latencyMs = Math.round(performance.now() - started);
      setMessages([
        {
          role: "assistant",
          content: res.response,
          latencyMs,
          ts: Date.now(),
        },
      ]);
      return res;
    } catch (e) {
      setError((e as Error).message);
      return null;
    } finally {
      setPending(false);
    }
  }, []);

  const turnCount = useMemo(
    () => messages.filter((m) => m.role === "user").length,
    [messages],
  );

  return {
    messages,
    sessionId,
    pending,
    error,
    send,
    newSession,
    startSession,
    setSessionId,
    callerPhone,
    setCallerPhone,
    turnCount,
  };
}
