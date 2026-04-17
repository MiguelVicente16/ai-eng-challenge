"""Admin API: read/write the three YAML configs.

Each PUT validates against a pydantic shape, writes atomically
(temp-file + os.replace), then busts the relevant `@lru_cache`d loader
so the next request re-reads from disk.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from fastapi import APIRouter

from src.agents.config.phrases import load_phrases
from src.agents.config.routing import load_routing_rules
from src.agents.summary.metrics import (
    build_summary_model,
    build_summary_prompt,
    load_summary_config,
)
from src.schemas.admin import MetricsConfig, PhrasesConfig, ServicesConfig

router = APIRouter()

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "agents" / "config"
ROUTING_PATH = _CONFIG_DIR / "routing_rules.yaml"
PHRASES_PATH = _CONFIG_DIR / "phrases.yaml"
METRICS_PATH = _CONFIG_DIR / "summary_metrics.yaml"


def _atomic_write_yaml(path: Path, data: dict) -> None:
    """Write YAML to a temp sibling then os.replace — never leaves a half-written file."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    os.replace(tmp, path)


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@router.get("/config/routing")
def get_routing() -> dict:
    return _read_yaml(ROUTING_PATH)


@router.put("/config/routing")
def put_routing(config: ServicesConfig) -> dict:
    payload = config.model_dump()
    _atomic_write_yaml(ROUTING_PATH, payload)
    load_routing_rules.cache_clear()
    return payload


@router.get("/config/phrases")
def get_phrases() -> dict:
    return {"phrases": _read_yaml(PHRASES_PATH)}


@router.put("/config/phrases")
def put_phrases(config: PhrasesConfig) -> dict:
    _atomic_write_yaml(PHRASES_PATH, config.phrases)
    load_phrases.cache_clear()
    return config.model_dump()


@router.get("/config/metrics")
def get_metrics() -> dict:
    return _read_yaml(METRICS_PATH)


@router.put("/config/metrics")
def put_metrics(config: MetricsConfig) -> dict:
    payload = config.model_dump()
    _atomic_write_yaml(METRICS_PATH, payload)
    load_summary_config.cache_clear()
    build_summary_model.cache_clear()
    build_summary_prompt.cache_clear()
    return payload
