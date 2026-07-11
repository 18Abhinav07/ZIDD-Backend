"""Assemble the tutor decision graph.

Shape:
    entry_router ─turn0──────────────► teach ─► END
                 └─else─► evaluate ─route_node─► bridge     ─► END
                                               ├ strengthen ─► END
                                               ├ teach      ─► END
                                               └ challenge  ─► END

Compiled WITHOUT a checkpointer: there are no interrupt nodes, and SessionStore
(service layer) owns canonical runtime state, passing it into ainvoke each turn.
The graph is a pure decision brain — token streaming lives in the service.

entry_router handles the opening turn WITHOUT touching route_node, so the locked
route.py bridge-guard test stays green (route_node must still map a fresh
low-score state to "bridge").
"""
from functools import lru_cache

from langgraph.graph import END, StateGraph

from app.graph.nodes.bridge import bridge_node
from app.graph.nodes.challenge import challenge_node
from app.graph.nodes.clarify import clarify_node
from app.graph.nodes.ease import ease_node
from app.graph.nodes.evaluate import evaluate_node
from app.graph.nodes.evaluation_retry import evaluation_retry_node
from app.graph.nodes.redirect import redirect_node
from app.graph.nodes.strengthen import strengthen_node
from app.graph.nodes.teach import teach_node
from app.graph.route import route_node
from app.models import TutorState


def entry_router(state: dict) -> str:
    """Opening turn (no answer yet) -> teach. Otherwise score the answer."""
    return "teach" if state.get("turn_count", 0) == 0 else "evaluate"


def _build() -> StateGraph:
    g = StateGraph(TutorState)

    g.add_node("evaluate", evaluate_node)
    g.add_node("evaluation_retry", evaluation_retry_node)
    g.add_node("teach", teach_node)
    g.add_node("bridge", bridge_node)
    g.add_node("strengthen", strengthen_node)
    g.add_node("challenge", challenge_node)
    g.add_node("redirect", redirect_node)
    g.add_node("clarify", clarify_node)
    g.add_node("ease", ease_node)

    g.set_conditional_entry_point(
        entry_router, {"teach": "teach", "evaluate": "evaluate"}
    )
    g.add_conditional_edges(
        "evaluate",
        route_node,
        {
            "bridge": "bridge",
            "strengthen": "strengthen",
            "teach": "teach",
            "challenge": "challenge",
            "redirect": "redirect",
            "clarify": "clarify",
            "ease": "ease",
            "evaluation_retry": "evaluation_retry",
        },
    )
    for node in ("evaluate", "teach", "bridge", "strengthen", "challenge",
                 "redirect", "clarify", "ease", "evaluation_retry"):
        if node != "evaluate":
            g.add_edge(node, END)
    return g


@lru_cache
def get_graph():
    """Compiled graph, built once. No checkpointer (stateless per ainvoke)."""
    return _build().compile()
