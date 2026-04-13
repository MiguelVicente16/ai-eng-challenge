"""Chat router — handles the /chat endpoint."""

from functools import lru_cache

from fastapi import APIRouter, Depends

from src.schemas.api import ChatRequest, ChatResponse
from src.services.chat import ChatService

router = APIRouter()


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """Construct the ChatService lazily on first request.

    Cached so all requests share the same instance (and thus the same
    compiled graph and checkpointer).
    """
    return ChatService()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service),
) -> ChatResponse:
    """Process a chat message and return a response."""
    return await service.handle_message(request)
