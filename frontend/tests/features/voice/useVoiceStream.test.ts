import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { useVoiceStream } from "@/features/voice/useVoiceStream";

describe("useVoiceStream", () => {
  it("should_handle_turn_events_from_websocket", async () => {
    // Arrange
    const sockets: any[] = [];
    const originalWS = (globalThis as any).WebSocket;
    (globalThis as any).WebSocket = class {
      binaryType = "";
      onopen: any;
      onmessage: any;
      onclose: any;
      onerror: any;
      send = vi.fn();
      close = vi.fn();
      constructor() {
        sockets.push(this);
      }
    };
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [] }) },
    });

    try {
      const { result } = renderHook(() => useVoiceStream());

      // Act — start hook; drive a "turn" event
      await act(async () => {
        await result.current.start();
      });
      act(() => {
        const ws = sockets[0];
        ws.onopen?.();
        ws.onmessage?.({
          data: JSON.stringify({ type: "turn", transcript: "hi", response: "hello" }),
        });
      });

      // Assert
      expect(result.current.messages).toEqual([
        { role: "user", content: "hi" },
        { role: "assistant", content: "hello" },
      ]);
    } finally {
      (globalThis as any).WebSocket = originalWS;
    }
  });
});
