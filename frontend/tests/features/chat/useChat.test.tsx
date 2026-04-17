import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { useChat } from "@/features/chat/useChat";

const server = setupServer(
  http.post("/chat", async ({ request }) => {
    const body = (await request.json()) as any;
    return HttpResponse.json({
      response: `Echo: ${body.message}`,
      session_id: body.session_id ?? "sess-1",
      audio_base64: null,
      transcript: null,
    });
  }),
);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function _wrap() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
  };
}

describe("useChat", () => {
  it("should_send_message_and_append_bubbles", async () => {
    // Arrange
    const { result } = renderHook(() => useChat(), { wrapper: _wrap() });

    // Act
    await act(async () => {
      await result.current.send("hello");
    });

    // Assert
    await waitFor(() => expect(result.current.messages).toHaveLength(2));
    expect(result.current.messages[0]).toMatchObject({ role: "user", content: "hello" });
    expect(result.current.messages[1]).toMatchObject({ role: "assistant", content: "Echo: hello" });
    expect(result.current.sessionId).toBe("sess-1");
  });

  it("should_reset_on_new_session", () => {
    // Arrange
    const { result } = renderHook(() => useChat(), { wrapper: _wrap() });

    // Act
    act(() => result.current.newSession());

    // Assert
    expect(result.current.messages).toEqual([]);
    expect(result.current.sessionId).toBeUndefined();
  });
});
