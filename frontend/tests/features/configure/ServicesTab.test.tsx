import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { ServicesTab } from "@/features/configure/ServicesTab";

let captured: unknown = null;
const server = setupServer(
  http.get("/api/config/routing", () =>
    HttpResponse.json({
      services: {
        general: { label: "General", dept_phone: "+1999", yes_rules: ["a"], no_rules: [] },
      },
    }),
  ),
  http.put("/api/config/routing", async ({ request }) => {
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
      <ServicesTab />
    </QueryClientProvider>,
  );
}

describe("ServicesTab", () => {
  it("should_render_services_from_api", async () => {
    // Arrange + Act
    _render();
    // Assert
    await waitFor(() => expect(screen.getByText("general")).toBeInTheDocument());
    expect(screen.getByDisplayValue("General")).toBeInTheDocument();
  });

  it("should_save_edited_label_via_put", async () => {
    // Arrange
    const user = userEvent.setup();
    _render();
    await waitFor(() => screen.getByDisplayValue("General"));

    // Act
    const input = screen.getByDisplayValue("General");
    await user.clear(input);
    await user.type(input, "General Support");
    await user.click(screen.getByRole("button", { name: /save/i }));

    // Assert
    await waitFor(() => expect(captured).not.toBeNull());
    expect((captured as any).services.general.label).toBe("General Support");
  });
});
