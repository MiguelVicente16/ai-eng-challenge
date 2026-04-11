"""Chat router — handles the /chat endpoint."""

from fastapi import APIRouter

from src.schemas.api import ChatRequest, ChatResponse
from src.services.chat import ChatService

router = APIRouter()
chat_service = ChatService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message and return a response."""
    return chat_service.handle_message(request)
