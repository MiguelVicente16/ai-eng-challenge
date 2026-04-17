import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { SummaryList } from "@/features/summaries/SummaryList";

const server = setupServer(
  http.get("/api/summaries", ({ request }) => {
    const url = new URL(request.url);
    const sentiment = url.searchParams.get("sentiment");
    const items =
      sentiment === "negative"
        ? [
            {
              session_id: "b",
              timestamp: "2026-02-01T00:00:00+00:00",
              caller_phone_masked: "+1\u2022\u2022\u2022234",
              metrics: {
                sentiment: "negative",
                resolved: false,
                topics: ["loans"],
                summary: "bad",
              },
              transcript: [],
            },
          ]
        : [
            {
              session_id: "a",
              timestamp: "2026-01-01T00:00:00+00:00",
              caller_phone_masked: "+1\u2022\u2022\u2022111",
              metrics: {
                sentiment: "positive",
                resolved: true,
                topics: ["cards"],
                summary: "good",
              },
              transcript: [],
            },
            {
              session_id: "b",
              timestamp: "2026-02-01T00:00:00+00:00",
              caller_phone_masked: "+1\u2022\u2022\u2022234",
              metrics: {
                sentiment: "negative",
                resolved: false,
                topics: ["loans"],
                summary: "bad",
              },
              transcript: [],
            },
          ];
    return HttpResponse.json({ items, total: items.length, page: 1, size: 20 });
  }),
);
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function _render() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={qc}>
        <SummaryList />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe("SummaryList", () => {
  it("should_render_rows_from_api", async () => {
    // Arrange + Act
    _render();
    // Assert — session ids are shown in short form ("a".slice(0,8) === "a", "b".slice(0,8) === "b")
    await waitFor(() => expect(screen.getByText("a")).toBeInTheDocument());
    expect(screen.getByText("b")).toBeInTheDocument();
  });

  it("should_filter_by_sentiment", async () => {
    // Arrange
    const user = userEvent.setup();
    _render();
    await waitFor(() => screen.getByText("a"));

    // Act — open sentiment Select, choose "negative"
    await user.click(screen.getByLabelText(/sentiment/i));
    await user.click(await screen.findByRole("option", { name: /negative/i }));

    // Assert
    await waitFor(() => expect(screen.queryByText("a")).not.toBeInTheDocument());
    expect(screen.getByText("b")).toBeInTheDocument();
  });
});
