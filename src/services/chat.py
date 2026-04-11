"""Chat service — orchestrates conversation flow.

This service manages session state and delegates to agents.
Agent logic (greeter, bouncer, specialist, guardrails) is
plugged in by the next phase.
"""

import uuid

from src.schemas.api import ChatRequest, ChatResponse


class ChatService:
    """Orchestrates the multi-agent conversation flow."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    def handle_message(self, request: ChatRequest) -> ChatResponse:
        """Process an incoming chat message and return a response.

        Manages session lifecycle. Agent logic is plugged in later.
        """
        session_id = request.session_id or str(uuid.uuid4())

        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "messages": [],
                "verification_stage": "collecting_info",
            }

        session = self._sessions[session_id]
        session["messages"].append({"role": "user", "content": request.message})

        # Placeholder — agent logic replaces this in the next phase
        response_text = (
            "Welcome to DEUS Bank! I'm here to help you. "
            "Could you please provide your name and at least one of: "
            "your phone number or IBAN so I can verify your identity?"
        )

        session["messages"].append({"role": "assistant", "content": response_text})

        return ChatResponse(response=response_text, session_id=session_id)
