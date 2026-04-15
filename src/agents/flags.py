"""Stage, tier, and service literal types that drive graph routing."""

from typing import Literal

Stage = Literal[
    "new_session",
    "awaiting_problem",
    "collecting_identity",
    "ask_secret",
    "verifying_secret",
    "routing",
    "clarifying",
    "completed",
    "failed",
]

Tier = Literal["premium", "regular", "non_customer"]

Service = Literal["investments", "insurance", "loans", "cards", "general"]
