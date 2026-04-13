"""Phrase catalog loader and renderer."""

from functools import lru_cache
from pathlib import Path

import yaml

_PHRASES_PATH = Path(__file__).parent / "phrases.yaml"


@lru_cache(maxsize=1)
def load_phrases() -> dict[str, str]:
    """Load the phrase catalog from YAML. Cached for the process lifetime."""
    with _PHRASES_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"phrases.yaml must be a mapping, got {type(data).__name__}")
    return {k: str(v).strip() for k, v in data.items()}


def render(key: str, variables: dict[str, str] | None = None) -> str:
    """Render a phrase by key with variable substitution.

    Raises KeyError if the phrase key is unknown or a required variable is missing.
    """
    phrases = load_phrases()
    if key not in phrases:
        raise KeyError(f"Unknown phrase key: {key}")
    template = phrases[key]
    return template.format(**(variables or {}))
