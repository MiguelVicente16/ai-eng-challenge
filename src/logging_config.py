"""Logging configuration for the DEUS Bank customer support system.

Every log line is prefixed with a short `[Tag]` derived from the logger name,
so developers can see at a glance which component is logging. The tag is
computed from the last dotted component of the logger name — e.g., a logger
named `src.agents.nodes.greeter` renders as `[Greeter]`.
"""

from __future__ import annotations

import logging
import os
import sys

# Special-case tags where the default title-case conversion would be ugly.
_TAG_OVERRIDES: dict[str, str] = {
    "stt": "STT",
    "tts": "TTS",
    "chat": "ChatService",
    "intent_cache": "IntentCache",
    "logging_config": "LoggingConfig",
}


def _tag_for(logger_name: str) -> str:
    """Turn a dotted logger name into a short bracketed tag."""
    last = logger_name.rsplit(".", 1)[-1]
    if last in _TAG_OVERRIDES:
        return f"[{_TAG_OVERRIDES[last]}]"
    parts = last.split("_")
    return "[" + "".join(p.capitalize() for p in parts) + "]"


class _TagFilter(logging.Filter):
    """Inject a `tag` attribute onto every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.tag = _tag_for(record.name)
        return True


def setup_logging() -> None:
    """Configure application-wide logging.

    Reads LOG_LEVEL environment variable (default INFO) and installs a
    single stdout handler with a readable tagged format. Safe to call
    multiple times.
    """
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)-5s %(tag)-16s  %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    handler.addFilter(_TagFilter())

    root = logging.getLogger()
    root.setLevel(level)
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root.addHandler(handler)

    for noisy in ("httpx", "httpcore", "google_genai", "google.generativeai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def mask(value: str | None, keep: int = 4) -> str:
    """Mask a sensitive value, keeping the first and last `keep` chars."""
    if not value:
        return "<none>"
    if len(value) <= keep * 2:
        return "***"
    return f"{value[:keep]}...{value[-keep:]}"


def trim(text: str | None, max_len: int = 80) -> str:
    """Trim long text to a max length with ellipsis, returning a repr-style string."""
    if text is None:
        return "<none>"
    if len(text) <= max_len:
        return repr(text)
    return repr(text[:max_len] + "...")
