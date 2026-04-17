"""Append the current turn's user + assistant messages to the conversation log.

Runs between `tts` and the summarizer/END split, so by the time the
summarizer fires the full transcript (including the final turn) is on
`state["messages"]`. The `add_messages` reducer on `AgentState.messages`
merges the returned list into the existing log rather than overwriting.

Opener turns (user_message empty) only append the assistant message.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from src.agents.state import AgentState


def log_turn_node(state: AgentState) -> dict:
    """Return the messages to append for this turn."""
    user_text = (state.get("user_message") or "").strip()
    ai_text = (state.get("output_text") or "").strip()
    new_messages: list = []
    if user_text:
        new_messages.append(HumanMessage(content=user_text))
    if ai_text:
        new_messages.append(AIMessage(content=ai_text))
    if not new_messages:
        return {}
    return {"messages": new_messages}
