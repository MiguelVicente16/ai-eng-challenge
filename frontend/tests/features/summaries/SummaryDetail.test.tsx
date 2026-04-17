import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { SummaryDetail } from "@/features/summaries/SummaryDetail";

const server = setupServer(
  http.get("/api/summaries/abc", () =>
    HttpResponse.json({
      session_id: "abc",
      timestamp: "2026-04-01T10:00:00+00:00",
      caller_phone_masked: "+1\u2022\u2022\u2022111",
      tier: "premium",
      matched_service: "cards",
      stage: "completed",
      user_problem: "card lost",
      metrics: { summary: "Lost card", sentiment: "neutral", topics: ["cards"], resolved: true },
      transcript: [
        { role: "user", content: "I lost my card" },
        { role: "assistant", content: "Let me help" },
      ],
    }),
  ),
  http.get("/api/config/metrics", () =>
    HttpResponse.json({
      metrics: [
        { name: "summary", type: "string", description: "" },
        { name: "sentiment", type: "enum", values: ["positive", "neutral", "negative"], description: "" },
        { name: "topics", type: "list", item_type: "string", description: "" },
        { name: "resolved", type: "boolean", description: "" },
      ],
    }),
  ),
);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("SummaryDetail", () => {
  it("should_render_outcome_metrics_and_transcript", async () => {
    // Arrange
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    // Act
    render(
      <MemoryRouter initialEntries={["/summaries/abc"]}>
        <QueryClientProvider client={qc}>
          <Routes>
            <Route path="/summaries/:id" element={<SummaryDetail />} />
          </Routes>
        </QueryClientProvider>
      </MemoryRouter>,
    );

    // Assert — "Lost card" is now both the H1 heading and the "summary"
    // metric value, so use getAllByText and just check ≥1 occurrence.
    await waitFor(() => expect(screen.getAllByText(/Lost card/).length).toBeGreaterThan(0));
    // "cards" appears twice: once as matched_service, once as a topic badge.
    expect(screen.getAllByText("cards").length).toBeGreaterThan(0);
    expect(screen.getByText("I lost my card")).toBeInTheDocument();
    expect(screen.getByText("Let me help")).toBeInTheDocument();
  });
});
