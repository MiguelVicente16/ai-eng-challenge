"""FastAPI application entry point."""

from fastapi import FastAPI

from src.logging_config import setup_logging
from src.routers.chat import router as chat_router

setup_logging()

app = FastAPI(
    title="DEUS Bank AI Support",
    version="1.0.0",
    description="AI-powered multi-agent customer support system",
)

app.include_router(chat_router)


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
