"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agents.deepgram.client import get_deepgram_client
from src.config import get_settings
from src.logging_config import setup_logging
from src.routers.admin_config import router as admin_config_router
from src.routers.admin_sessions import router as admin_sessions_router
from src.routers.admin_summaries import router as admin_summaries_router
from src.routers.chat import router as chat_router
from src.routers.voice import router as voice_router

setup_logging()

app = FastAPI(
    title="DEUS Bank AI Support",
    version="1.0.0",
    description="AI-powered multi-agent customer support system",
)

# Dev: Vite on :5173 fetches /api/* from :8000. Prod serves same-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(admin_config_router, prefix="/api")
app.include_router(admin_summaries_router, prefix="/api")
app.include_router(admin_sessions_router, prefix="/api")


@app.get("/api/health")
def health() -> dict:
    """Health check + feature flags for the admin UI."""
    settings = get_settings()
    return {
        "status": "ok",
        "deepgram": get_deepgram_client() is not None,
        "mongo": bool(settings.mongodb_url),
    }
