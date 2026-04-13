"""LangGraph assembly for the customer support multi-agent router."""

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from src.agents.checkpointer import get_checkpointer
from src.agents.nodes.bouncer import bouncer_node
from src.agents.nodes.capture_problem import capture_problem_node
from src.agents.nodes.greeter import greeter_node
from src.agents.nodes.guardrails import guardrails_node
from src.agents.nodes.opener import opener_node
from src.agents.nodes.responder import responder_node
from src.agents.nodes.session_ended import session_ended_node
from src.agents.nodes.specialist import specialist_node
from src.agents.nodes.stt import stt_node
from src.agents.nodes.tts import tts_node
from src.agents.nodes.verifier import verifier_node
from src.agents.state import AgentState


def _route_by_stage(state: AgentState) -> str:
    """Decide which agent node to run next based on the current stage."""
    stage = state.get("stage") or "new_session"

    if stage == "new_session":
        return "opener"
    if stage == "awaiting_problem":
        return "capture_problem"
    if stage == "collecting_identity":
        return "greeter"
    if stage in ("ask_secret", "verifying_secret"):
        return "verifier"
    if stage == "routing":
        return "bouncer"
    if stage in ("completed", "failed"):
        return "session_ended"
    return "responder"


def _route_after_verifier(state: AgentState) -> str:
    """After verifier runs, go to bouncer immediately if identity was verified."""
    if state.get("stage") == "routing":
        return "bouncer"
    return "responder"


@lru_cache(maxsize=1)
def build_graph():
    """Build and compile the customer support graph with InMemorySaver."""
    graph = StateGraph(AgentState)

    graph.add_node("stt", stt_node)
    graph.add_node("opener", opener_node)
    graph.add_node("capture_problem", capture_problem_node)
    graph.add_node("greeter", greeter_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("bouncer", bouncer_node)
    graph.add_node("specialist", specialist_node)
    graph.add_node("session_ended", session_ended_node)
    graph.add_node("responder", responder_node)
    graph.add_node("guardrails", guardrails_node)
    graph.add_node("tts", tts_node)

    graph.add_edge(START, "stt")

    graph.add_conditional_edges(
        "stt",
        _route_by_stage,
        {
            "opener": "opener",
            "capture_problem": "capture_problem",
            "greeter": "greeter",
            "verifier": "verifier",
            "bouncer": "bouncer",
            "session_ended": "session_ended",
            "responder": "responder",
        },
    )

    graph.add_edge("opener", "responder")
    graph.add_edge("capture_problem", "responder")
    graph.add_edge("greeter", "responder")
    graph.add_edge("session_ended", "responder")
    graph.add_conditional_edges(
        "verifier",
        _route_after_verifier,
        {
            "bouncer": "bouncer",
            "responder": "responder",
        },
    )
    graph.add_edge("bouncer", "specialist")
    graph.add_edge("specialist", "responder")

    graph.add_edge("responder", "guardrails")
    graph.add_edge("guardrails", "tts")
    graph.add_edge("tts", END)

    return graph.compile(checkpointer=get_checkpointer())
