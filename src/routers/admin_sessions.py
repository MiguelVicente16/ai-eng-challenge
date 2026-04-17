"""Admin API: debug/inspect the LangGraph state for a session."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from langchain_core.messages import AIMessage, HumanMessage

from src.agents.messages import message_text
from src.routers.chat import get_chat_service

router = APIRouter()


@router.get("/sessions/{session_id}/state")
async def get_session_state(session_id: str) -> dict:
    service = get_chat_service()
    snapshot = await service._graph.aget_state({"configurable": {"thread_id": session_id}})
    values = snapshot.values or {}
    if not values:
        raise HTTPException(status_code=404, detail="no checkpoint for this session")

    # Strip bytes from input_audio/output_audio so JSON can serialize
    sanitized = {k: v for k, v in values.items() if k not in {"input_audio", "output_audio"}}
    # Serialize LangChain messages to {role, content} pairs
    if "messages" in sanitized:
        serialized: list[dict] = []
        for msg in sanitized["messages"]:
            if isinstance(msg, HumanMessage):
                serialized.append({"role": "user", "content": message_text(msg)})
            elif isinstance(msg, AIMessage):
                serialized.append({"role": "assistant", "content": message_text(msg)})
        sanitized["messages"] = serialized
    return sanitized
