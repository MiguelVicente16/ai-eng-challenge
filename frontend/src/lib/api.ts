import {
  Health,
  MetricsConfig,
  PhrasesConfig,
  SessionState,
  SummariesPage,
  SummaryListItem,
  ServicesConfig,
  healthSchema,
  metricsConfigSchema,
  phrasesConfigSchema,
  servicesConfigSchema,
  sessionStateSchema,
  summariesPageSchema,
  summaryListItemSchema,
} from "@/lib/schemas";

async function request<T>(
  path: string,
  schema: { parse: (v: unknown) => T },
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return schema.parse(await res.json());
}

export type ChatTurnRequest = {
  message: string;
  session_id?: string;
  caller_phone?: string;
  audio_base64?: string;
  audio_encoding?: string;
  audio_sample_rate?: number;
};

export type ChatTurnResponse = {
  response: string;
  session_id: string;
  audio_base64: string | null;
  transcript: string | null;
};

export const api = {
  getHealth: () => request("/api/health", healthSchema),
  getRouting: () => request("/api/config/routing", servicesConfigSchema),
  putRouting: (cfg: ServicesConfig) =>
    request("/api/config/routing", servicesConfigSchema, {
      method: "PUT",
      body: JSON.stringify(cfg),
    }),
  getPhrases: () => request("/api/config/phrases", phrasesConfigSchema),
  putPhrases: (cfg: PhrasesConfig) =>
    request("/api/config/phrases", phrasesConfigSchema, {
      method: "PUT",
      body: JSON.stringify(cfg),
    }),
  getMetrics: () => request("/api/config/metrics", metricsConfigSchema),
  putMetrics: (cfg: MetricsConfig) =>
    request("/api/config/metrics", metricsConfigSchema, {
      method: "PUT",
      body: JSON.stringify(cfg),
    }),
  listSummaries: async (params: Record<string, string | number | boolean | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== null) qs.set(k, String(v));
    });
    return request(`/api/summaries?${qs.toString()}`, summariesPageSchema);
  },
  getSummary: (id: string) => request(`/api/summaries/${encodeURIComponent(id)}`, summaryListItemSchema),
  getSessionState: (id: string) =>
    request(`/api/sessions/${encodeURIComponent(id)}/state`, sessionStateSchema),
  postChat: async (payload: ChatTurnRequest): Promise<ChatTurnResponse> => {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return (await res.json()) as ChatTurnResponse;
  },
};

export type { Health, SessionState, SummariesPage, SummaryListItem };
