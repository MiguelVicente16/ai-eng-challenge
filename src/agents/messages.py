"""Helpers for working with LangChain message objects inside this app."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage


def message_text(msg: AIMessage | HumanMessage) -> str:
    """Return the message content as a plain string, flattening list-content
    (tool-use responses) down to their text blocks. Non-text blocks are
    dropped so transcripts/debug views stay readable."""
    content = msg.content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content or "")
