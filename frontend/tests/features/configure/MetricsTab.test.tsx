import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { MetricsTab } from "@/features/configure/MetricsTab";

let captured: unknown = null;
const server = setupServer(
  http.get("/api/config/metrics", () =>
    HttpResponse.json({
      metrics: [
        { name: "sentiment", type: "enum", values: ["positive", "negative"], description: "s" },
      ],
    }),
  ),
  http.put("/api/config/metrics", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    captured = body;
    return HttpResponse.json(body);
  }),
);
beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  captured = null;
});
afterAll(() => server.close());

function _render() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MetricsTab />
    </QueryClientProvider>,
  );
}

describe("MetricsTab", () => {
  it("should_render_existing_metrics", async () => {
    // Arrange + Act
    _render();
    // Assert — "sentiment" now shows in both the sidebar list and the
    // editor header; at least one occurrence is enough.
    await waitFor(() =>
      expect(screen.getAllByText("sentiment").length).toBeGreaterThan(0),
    );
  });

  it("should_save_metric_after_description_edit", async () => {
    // Arrange
    const user = userEvent.setup();
    _render();
    await waitFor(() => screen.getAllByText("sentiment"));

    // Act — first metric is selected by default so the editor is visible
    const desc = screen.getByLabelText(/description/i);
    await user.clear(desc);
    await user.type(desc, "updated");
    await user.click(screen.getByRole("button", { name: /save/i }));

    // Assert
    await waitFor(() => expect(captured).not.toBeNull());
    expect((captured as any).metrics[0].description).toBe("updated");
  });
});
