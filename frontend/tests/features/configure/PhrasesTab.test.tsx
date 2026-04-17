import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { PhrasesTab } from "@/features/configure/PhrasesTab";

let captured: unknown = null;
const server = setupServer(
  http.get("/api/config/phrases", () =>
    HttpResponse.json({ phrases: { opener: "Hi {name}" } }),
  ),
  http.put("/api/config/phrases", async ({ request }) => {
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
      <PhrasesTab />
    </QueryClientProvider>,
  );
}

describe("PhrasesTab", () => {
  it("should_render_phrase_keys_and_show_detected_variables", async () => {
    // Arrange + Act
    _render();
    await waitFor(() => screen.getAllByText(/opener/i));
    // Assert — first phrase auto-selects; detected variable `{name}`
    // is rendered as its own chip next to the "Variables:" label.
    expect(screen.getByText("{name}")).toBeInTheDocument();
  });

  it("should_save_edited_phrase_template", async () => {
    // Arrange
    const user = userEvent.setup();
    _render();
    await waitFor(() => screen.getByDisplayValue("Hi {name}"));

    // Act
    const textarea = screen.getByDisplayValue("Hi {name}");
    await user.clear(textarea);
    // user-event v14 treats "{" as start of special key; escape a literal "{" as "{{".
    await user.type(textarea, "Hello {{name}");
    await user.click(screen.getByRole("button", { name: /save/i }));

    // Assert
    await waitFor(() => expect(captured).not.toBeNull());
    expect((captured as any).phrases.opener).toBe("Hello {name}");
  });
});
