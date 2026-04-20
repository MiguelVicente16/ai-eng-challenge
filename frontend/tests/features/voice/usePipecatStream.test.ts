import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

// Capture the callbacks passed into PipecatClient so the test can fire RTVI
// events without a real WebSocket.
type ClientCallbacks = {
  onUserTranscript?: (data: { text: string; final: boolean }) => void;
  onBotLlmStarted?: () => void;
  onBotLlmText?: (data: { text: string }) => void;
  onBotLlmStopped?: () => void;
  onTransportStateChanged?: (state: string) => void;
};

let lastCallbacks: ClientCallbacks = {};
const connectMock = vi.fn().mockResolvedValue(undefined);
const disconnectMock = vi.fn().mockResolvedValue(undefined);

vi.mock("@pipecat-ai/client-js", async () => {
  const RTVIEvent = { TrackStarted: "trackStarted" };
  class PipecatClient {
    constructor(opts: { callbacks?: ClientCallbacks }) {
      lastCallbacks = opts.callbacks ?? {};
    }
    on = vi.fn();
    connect = connectMock;
    disconnect = disconnectMock;
  }
  return { PipecatClient, RTVIEvent };
});

vi.mock("@pipecat-ai/websocket-transport", () => ({
  WebSocketTransport: class {
    constructor() {}
  },
  ProtobufFrameSerializer: class {},
}));

async function loadHook() {
  const mod = await import("@/features/voice/usePipecatStream");
  return mod.usePipecatStream;
}

describe("usePipecatStream", () => {
  beforeEach(() => {
    lastCallbacks = {};
    connectMock.mockClear();
    disconnectMock.mockClear();
  });

  it("should_connect_on_start", async () => {
    // Arrange
    const usePipecatStream = await loadHook();
    const { result } = renderHook(() => usePipecatStream());

    // Act
    await act(async () => {
      await result.current.start();
    });

    // Assert
    expect(connectMock).toHaveBeenCalledTimes(1);
    expect(connectMock.mock.calls[0][0]).toMatchObject({
      wsUrl: expect.stringContaining("/voice"),
    });
  });

  it("should_append_user_bubble_on_final_transcript_only", async () => {
    // Arrange
    const usePipecatStream = await loadHook();
    const { result } = renderHook(() => usePipecatStream());
    await act(async () => {
      await result.current.start();
    });

    // Act — partial doesn't land, final does
    act(() => {
      lastCallbacks.onUserTranscript?.({ text: "I need yach", final: false });
      lastCallbacks.onUserTranscript?.({ text: "I need yacht insurance", final: true });
    });

    // Assert
    await waitFor(() =>
      expect(result.current.messages).toEqual([
        expect.objectContaining({ role: "user", content: "I need yacht insurance" }),
      ]),
    );
  });

  it("should_concatenate_streamed_llm_text_into_one_assistant_bubble", async () => {
    // Arrange
    const usePipecatStream = await loadHook();
    const { result } = renderHook(() => usePipecatStream());
    await act(async () => {
      await result.current.start();
    });

    // Act — simulate streaming LLM output split across tokens
    act(() => {
      lastCallbacks.onBotLlmStarted?.();
      lastCallbacks.onBotLlmText?.({ text: "Sure, " });
      lastCallbacks.onBotLlmText?.({ text: "I can help " });
      lastCallbacks.onBotLlmText?.({ text: "with that." });
      lastCallbacks.onBotLlmStopped?.();
    });

    // Assert
    await waitFor(() =>
      expect(result.current.messages).toEqual([
        expect.objectContaining({ role: "assistant", content: "Sure, I can help with that." }),
      ]),
    );
  });

  it("should_reflect_transport_state_in_status", async () => {
    // Arrange
    const usePipecatStream = await loadHook();
    const { result } = renderHook(() => usePipecatStream());
    await act(async () => {
      await result.current.start();
    });

    // Act
    act(() => {
      lastCallbacks.onTransportStateChanged?.("ready");
    });

    // Assert
    await waitFor(() => expect(result.current.status).toBe("listening"));
  });

  it("should_disconnect_on_stop", async () => {
    // Arrange
    const usePipecatStream = await loadHook();
    const { result } = renderHook(() => usePipecatStream());
    await act(async () => {
      await result.current.start();
    });

    // Act
    await act(async () => {
      await result.current.stop();
    });

    // Assert
    expect(disconnectMock).toHaveBeenCalled();
    expect(result.current.status).toBe("idle");
  });
});
