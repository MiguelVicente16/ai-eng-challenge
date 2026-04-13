"""Routing rules loader for the Specialist agent."""

from functools import lru_cache
from pathlib import Path

import yaml

from src.agents.flags import Service

_RULES_PATH = Path(__file__).parent / "routing_rules.yaml"


@lru_cache(maxsize=1)
def load_routing_rules() -> dict[str, dict]:
    """Load the routing rules from YAML. Cached for the process lifetime."""
    with _RULES_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict) or "services" not in data:
        raise ValueError("routing_rules.yaml must contain a top-level 'services' mapping")
    return data["services"]


def get_service_metadata(service: Service) -> dict:
    """Return the label and dept_phone for a service."""
    rules = load_routing_rules()
    if service not in rules:
        raise KeyError(f"Unknown service: {service}")
    return {
        "label": rules[service]["label"],
        "dept_phone": rules[service]["dept_phone"],
    }


def build_rules_prompt() -> str:
    """Format all services and their rules as a prompt block for the Specialist LLM."""
    rules = load_routing_rules()
    lines: list[str] = ["Available services and their routing rules:"]
    for name, meta in rules.items():
        lines.append(f"\n## {name} — {meta['label']}")
        if meta.get("yes_rules"):
            lines.append("Route HERE when:")
            for rule in meta["yes_rules"]:
                lines.append(f"  - {rule}")
        if meta.get("no_rules"):
            lines.append("Do NOT route here when:")
            for rule in meta["no_rules"]:
                lines.append(f"  - {rule}")
    return "\n".join(lines)
