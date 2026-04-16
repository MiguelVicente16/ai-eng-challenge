"""Dynamic pydantic model + LLM prompt built from summary_metrics.yaml.

The summary metric schema is declarative: a frontend can edit the YAML
(or the equivalent DB-backed config) to add/remove/reshape metrics with
zero code changes. This module loads that config and produces:

- ConversationSummary pydantic model (via pydantic.create_model)
- System prompt for the summarizer LLM (derived from each metric's
  `description`, so prompt and schema stay in sync)

Supported metric types:
  - string      (optional max_length)
  - enum        (required `values` list — becomes a typing.Literal)
  - list        (optional `item_type`, default "string"; optional max_items)
  - boolean
  - integer     (optional min/max)
  - number      (optional min/max; maps to float)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, create_model

_METRICS_PATH = Path(__file__).parent.parent / "config" / "summary_metrics.yaml"

_LIST_ITEM_TYPES: dict[str, type] = {"string": str, "integer": int, "number": float}


@lru_cache(maxsize=1)
def load_summary_config() -> list[dict]:
    """Load the summary metrics config from YAML. Cached for the process lifetime."""
    with _METRICS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "metrics" not in data:
        raise ValueError("summary_metrics.yaml must contain a top-level 'metrics' list")
    metrics = data["metrics"]
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("summary_metrics.yaml 'metrics' must be a non-empty list")
    return metrics


def _metric_field(metric: dict) -> tuple[type, Any]:
    """Translate one YAML metric entry to (python_type, pydantic.Field)."""
    mtype = metric["type"]
    desc = (metric.get("description") or "").strip()

    if mtype == "string":
        kwargs: dict = {"description": desc}
        if "max_length" in metric:
            kwargs["max_length"] = metric["max_length"]
        return (str, Field(..., **kwargs))

    if mtype == "enum":
        values = metric.get("values") or []
        if not values:
            raise ValueError(f"enum metric {metric['name']!r} must have non-empty 'values'")
        enum_type = Literal[tuple(values)]  # type: ignore[valid-type]
        return (enum_type, Field(..., description=desc))

    if mtype == "list":
        item_label = metric.get("item_type", "string")
        item_type = _LIST_ITEM_TYPES.get(item_label)
        if item_type is None:
            raise ValueError(f"list metric {metric['name']!r} has unsupported item_type: {item_label}")
        kwargs = {"description": desc}
        if "max_items" in metric:
            kwargs["max_length"] = metric["max_items"]
        return (list[item_type], Field(..., **kwargs))

    if mtype == "boolean":
        return (bool, Field(..., description=desc))

    if mtype in ("integer", "number"):
        python_type: type = int if mtype == "integer" else float
        kwargs = {"description": desc}
        if "min" in metric:
            kwargs["ge"] = metric["min"]
        if "max" in metric:
            kwargs["le"] = metric["max"]
        return (python_type, Field(..., **kwargs))

    raise ValueError(f"unsupported metric type: {mtype}")


@lru_cache(maxsize=1)
def build_summary_model() -> type[BaseModel]:
    """Build the ConversationSummary pydantic model from the metrics config."""
    fields: dict[str, tuple[type, Any]] = {}
    for metric in load_summary_config():
        fields[metric["name"]] = _metric_field(metric)
    return create_model("ConversationSummary", **fields)


def _type_label(metric: dict) -> str:
    """Human-readable type for the LLM prompt."""
    mtype = metric["type"]
    if mtype == "enum":
        return "enum: " + "/".join(metric["values"])
    if mtype == "list":
        max_items = metric.get("max_items")
        item = metric.get("item_type", "string")
        return f"list[{item}]" + (f", max {max_items}" if max_items else "")
    return mtype


@lru_cache(maxsize=1)
def build_summary_prompt() -> str:
    """Build the summarizer system prompt from metric descriptions."""
    lines = [
        "You are analyzing a completed customer support call for DEUS Bank.",
        "Extract the following fields from the call context below.",
        "",
    ]
    for metric in load_summary_config():
        name = metric["name"]
        desc = (metric.get("description") or "").strip()
        lines.append(f"- {name} ({_type_label(metric)}): {desc}")
    return "\n".join(lines)
