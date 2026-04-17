import { afterAll, afterEach, beforeAll, describe, expect, it } from "vitest";
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

import { api } from "@/lib/api";

const server = setupServer(
  http.get("/api/health", () => HttpResponse.json({ status: "ok", deepgram: true, mongo: false })),
  http.get("/api/config/routing", () =>
    HttpResponse.json({ services: { general: { label: "General", dept_phone: "+1", yes_rules: [], no_rules: [] } } }),
  ),
  http.put("/api/config/routing", async ({ request }) => HttpResponse.json(await request.json())),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe("api", () => {
  it("should_get_health", async () => {
    // Act
    const health = await api.getHealth();
    // Assert
    expect(health.status).toBe("ok");
  });

  it("should_get_routing_config", async () => {
    // Act
    const cfg = await api.getRouting();
    // Assert
    expect(cfg.services.general.label).toBe("General");
  });

  it("should_put_routing_config_and_return_parsed_response", async () => {
    // Arrange
    const payload = {
      services: { cards: { label: "Cards", dept_phone: "+1", yes_rules: [], no_rules: [] } },
    };
    // Act
    const result = await api.putRouting(payload);
    // Assert
    expect(result.services.cards.label).toBe("Cards");
  });
});
