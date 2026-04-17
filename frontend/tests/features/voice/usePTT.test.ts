import { act, renderHook } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { usePTT } from "@/features/voice/usePTT";

describe("usePTT", () => {
  it("should_surface_mic_permission_error", async () => {
    // Arrange
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn().mockRejectedValue(new Error("NotAllowedError")) },
    });
    const { result } = renderHook(() => usePTT({ onAudio: async () => {} }));

    // Act
    await act(async () => {
      await result.current.start();
    });

    // Assert
    expect(result.current.error).toMatch(/NotAllowedError/);
  });
});
