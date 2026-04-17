import { z } from "zod";

export const healthSchema = z.object({
  status: z.string(),
  deepgram: z.boolean(),
  mongo: z.boolean(),
});
export type Health = z.infer<typeof healthSchema>;

export const serviceRuleSchema = z.object({
  label: z.string().min(1),
  dept_phone: z.string().min(1),
  yes_rules: z.array(z.string()),
  no_rules: z.array(z.string()),
});
export const servicesConfigSchema = z.object({
  services: z.record(z.string(), serviceRuleSchema),
});
export type ServicesConfig = z.infer<typeof servicesConfigSchema>;

export const phrasesConfigSchema = z.object({ phrases: z.record(z.string(), z.string()) });
export type PhrasesConfig = z.infer<typeof phrasesConfigSchema>;

const stringMetric = z.object({
  name: z.string().min(1),
  type: z.literal("string"),
  description: z.string().default(""),
  max_length: z.number().int().positive().nullish(),
});
const enumMetric = z.object({
  name: z.string().min(1),
  type: z.literal("enum"),
  description: z.string().default(""),
  values: z.array(z.string().min(1)).min(1),
});
const listMetric = z.object({
  name: z.string().min(1),
  type: z.literal("list"),
  description: z.string().default(""),
  item_type: z.enum(["string", "integer", "number"]).default("string"),
  max_items: z.number().int().positive().nullish(),
});
const booleanMetric = z.object({
  name: z.string().min(1),
  type: z.literal("boolean"),
  description: z.string().default(""),
});
const integerMetric = z.object({
  name: z.string().min(1),
  type: z.literal("integer"),
  description: z.string().default(""),
  min: z.number().int().nullish(),
  max: z.number().int().nullish(),
});
const numberMetric = z.object({
  name: z.string().min(1),
  type: z.literal("number"),
  description: z.string().default(""),
  min: z.number().nullish(),
  max: z.number().nullish(),
});
export const metricSchema = z.discriminatedUnion("type", [
  stringMetric,
  enumMetric,
  listMetric,
  booleanMetric,
  integerMetric,
  numberMetric,
]);
export type Metric = z.infer<typeof metricSchema>;
export const metricsConfigSchema = z.object({ metrics: z.array(metricSchema) });
export type MetricsConfig = z.infer<typeof metricsConfigSchema>;

export const summaryListItemSchema = z.object({
  session_id: z.string(),
  timestamp: z.string(),
  caller_phone_masked: z.string().nullable(),
  tier: z.string().nullable().optional(),
  matched_service: z.string().nullable().optional(),
  stage: z.string().nullable().optional(),
  user_problem: z.string().nullable().optional(),
  metrics: z.record(z.string(), z.any()).default({}),
  transcript: z
    .array(z.object({ role: z.enum(["user", "assistant"]), content: z.string() }))
    .default([]),
});
export const summariesPageSchema = z.object({
  items: z.array(summaryListItemSchema),
  total: z.number(),
  page: z.number(),
  size: z.number(),
});
export type SummaryListItem = z.infer<typeof summaryListItemSchema>;
export type SummariesPage = z.infer<typeof summariesPageSchema>;

export const sessionStateSchema = z
  .object({
    stage: z.string().optional(),
    matched_service: z.string().nullable().optional(),
    tier: z.string().nullable().optional(),
    caller_phone: z.string().nullable().optional(),
    caller_recognized: z.boolean().optional(),
    extracted_name: z.string().nullable().optional(),
    extracted_iban: z.string().nullable().optional(),
    extracted_phone: z.string().nullable().optional(),
    known_name_hint: z.string().nullable().optional(),
    retry_count: z.number().optional(),
    clarify_retry_count: z.number().optional(),
    messages: z
      .array(z.object({ role: z.enum(["user", "assistant"]), content: z.string() }))
      .optional(),
  })
  .passthrough();
export type SessionState = z.infer<typeof sessionStateSchema>;
