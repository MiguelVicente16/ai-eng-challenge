/**
 * Maps each phrase key to the conversation stage where it fires + a short
 * human label and a "when" description. Keys not listed here fall into the
 * "Other" group so an operator can still edit freshly-added phrases that
 * haven't been mapped yet.
 */

export type PhraseGroup = {
  id: string;
  title: string;
  description: string;
  keys: string[];
};

export const PHRASE_GROUPS: PhraseGroup[] = [
  {
    id: "opener",
    title: "Opening the call",
    description:
      "The very first thing the caller hears. Chosen based on whether the caller ID is known.",
    keys: ["opener_known_caller", "opener_unknown_caller"],
  },
  {
    id: "auth",
    title: "Asking for identity",
    description:
      "After the caller states their problem, the assistant collects the details it needs to identify them.",
    keys: [
      "auth_kickoff_known_caller",
      "auth_kickoff_unknown_caller",
      "greeter_need_more_info",
      "greeter_identity_not_found",
    ],
  },
  {
    id: "verify",
    title: "Verifying identity",
    description:
      "Security question + confirmation once the caller's identity matches a record.",
    keys: ["verifier_ask_secret", "verifier_success"],
  },
  {
    id: "clarify",
    title: "Clarification & retries",
    description:
      "When the assistant can't parse the last turn, it asks again rather than guess.",
    keys: [
      "retry_unclear_problem",
      "retry_unclear_identity",
      "retry_unclear_secret",
      "specialist_clarify",
    ],
  },
  {
    id: "route",
    title: "Routing & hand-off",
    description:
      "After verification the caller is routed to the right team with the matching phone number.",
    keys: ["premium_response", "regular_response", "non_customer_response"],
  },
  {
    id: "fallback",
    title: "Fallbacks",
    description:
      "Safety nets when the flow can't complete — retries exhausted or guardrails tripped.",
    keys: ["fallback_to_general", "guardrails_fallback"],
  },
  {
    id: "end",
    title: "Ending the call",
    description: "Closing line once the call reaches a terminal state.",
    keys: ["session_ended"],
  },
];

export const PHRASE_LABELS: Record<string, string> = {
  opener_known_caller: "Greeting — known caller",
  opener_unknown_caller: "Greeting — unknown caller",
  auth_kickoff_known_caller: "Ask for name + IBAN",
  auth_kickoff_unknown_caller: "Ask for name + phone or IBAN",
  greeter_need_more_info: "Ask for the missing field",
  greeter_identity_not_found: "Identity not found",
  verifier_ask_secret: "Ask the secret question",
  verifier_success: "Identity verified",
  retry_unclear_problem: "Retry — unclear problem",
  retry_unclear_identity: "Retry — unclear identity",
  retry_unclear_secret: "Retry — unclear secret answer",
  fallback_to_general: "Hand off to general support",
  premium_response: "Premium customer routed",
  regular_response: "Regular customer routed",
  non_customer_response: "Caller is not a customer",
  guardrails_fallback: "Guardrails fallback",
  specialist_clarify: "Specialist asks for clarification",
  session_ended: "Session ended",
};

export const PHRASE_HINTS: Record<string, string> = {
  opener_known_caller:
    "Plays on the first turn when the incoming caller ID matches a known customer.",
  opener_unknown_caller:
    "Plays on the first turn when the caller's phone is not in the database.",
  auth_kickoff_known_caller:
    "After the caller describes their problem — asks them to confirm name + IBAN.",
  auth_kickoff_unknown_caller:
    "After the caller describes their problem — asks for name + phone or IBAN.",
  greeter_need_more_info:
    "When identity lookup needs one more field. Uses {missing_field}.",
  greeter_identity_not_found:
    "When the provided details don't match any customer and retries are exhausted.",
  verifier_ask_secret:
    "Identity matched — asks the account's security question. Uses {secret_question}.",
  verifier_success:
    "Plays as soon as the secret answer is confirmed correct.",
  retry_unclear_problem:
    "The caller's first utterance was ambiguous or unintelligible; asks again.",
  retry_unclear_identity:
    "Identity details couldn't be parsed from the reply; asks again.",
  retry_unclear_secret:
    "Security-question answer couldn't be parsed; asks again.",
  fallback_to_general:
    "After too many failed attempts — hands off to general support. Uses {dept_phone}.",
  premium_response:
    "Premium-tier customer, verified. Final hand-off phrase with {name}, {service_label}, {dept_phone}.",
  regular_response:
    "Regular-tier customer, verified. Final hand-off phrase with {name}, {service_label}, {dept_phone}.",
  non_customer_response:
    "Caller is not in the customer database — suggests they call their own bank.",
  guardrails_fallback:
    "Safety catch if the assistant emits something off-policy. Uses {dept_phone}.",
  specialist_clarify:
    "The router couldn't confidently pick a service — asks a follow-up. Uses {clarification}.",
  session_ended: "Plays once the call reaches a terminal state.",
};

export function groupForKey(key: string): PhraseGroup | undefined {
  return PHRASE_GROUPS.find((g) => g.keys.includes(key));
}

export function humanPhraseLabel(key: string): string {
  if (PHRASE_LABELS[key]) return PHRASE_LABELS[key];
  return key
    .split("_")
    .map((p) => p.charAt(0).toUpperCase() + p.slice(1))
    .join(" ");
}
