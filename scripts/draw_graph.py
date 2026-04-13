"""Render the compiled LangGraph as a Mermaid PNG.

The LangGraph built-in draw_mermaid_png() POSTs to https://mermaid.ink and
returns PNG bytes. No local graphviz install required. Output is written
to docs/graph.png — this is the architecture-diagram deliverable.

Usage:
    uv run python scripts/draw_graph.py
    # or:
    make draw-graph
"""

from __future__ import annotations

from pathlib import Path

from src.agents.graph import build_graph

_OUTPUT = Path(__file__).parent.parent / "docs" / "graph.png"


def main() -> None:
    build_graph.cache_clear()
    graph = build_graph()
    png = graph.get_graph(xray=True).draw_mermaid_png()
    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_bytes(png)
    print(f"wrote {_OUTPUT} ({len(png)} bytes)")


if __name__ == "__main__":
    main()
