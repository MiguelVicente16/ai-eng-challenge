"""Structured output models for LLM calls inside agent nodes."""

from typing import Literal

from pydantic import BaseModel, Field

from src.agents.flags import Service


class IdentityExtraction(BaseModel):
    """Identity fields extracted from a user message."""

    name: str | None = Field(
        None,
        description="Customer's name as stated. None if not mentioned.",
    )
    phone: str | None = Field(
        None,
        description="Phone number in E.164 format (e.g., +1122334455). None if not mentioned.",
    )
    iban: str | None = Field(
        None,
        description="IBAN with no spaces. None if not mentioned.",
    )


class SecretAnswer(BaseModel):
    """The customer's answer to a secret question."""

    answer: str | None = Field(
        None,
        description="The customer's answer. None if they did not answer.",
    )


class ServiceClassification(BaseModel):
    """Decision and classification for routing a customer's request.

    `decision` is a categorical flag driving specialist behavior:

    - ``route``    — confident match to a service (``service`` required)
    - ``clarify``  — plausible match to 2+ services; ask one follow-up question
    - ``escalate`` — user explicitly asked for a human operator
    - ``none``     — request is off-topic or doesn't match any service
    """

    decision: Literal["route", "clarify", "escalate", "none"] = Field(
        description=(
            "How to handle this request. "
            "'route' = confident match to a specific service; "
            "'clarify' = ambiguous between 2+ services, ask one follow-up question; "
            "'escalate' = user asked for a human operator; "
            "'none' = off-topic or unclear."
        ),
    )
    service: Service | None = Field(
        default=None,
        description="Which service to route to. Required when decision='route', otherwise omit.",
    )
    clarification: str | None = Field(
        default=None,
        description=(
            "One short follow-up question (max 120 chars) that disambiguates the request. "
            "Required when decision='clarify', otherwise omit. Must be a single direct "
            "question, no preamble, no greeting."
        ),
        max_length=120,
    )
    reasoning: str = Field(
        description="Short reason for the decision, max 10 words.",
        max_length=100,
    )
