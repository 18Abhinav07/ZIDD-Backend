"""Content registry — aggregates every module into one lookup surface.

The engine was originally hardcoded to the communication module. This registry
replaces those direct imports: graph nodes, the service, and the API all resolve
nodes through here, so adding a module is a one-line `MODULES` entry with no
engine changes.

Responsibilities:
  - resolve any node id -> CommNode, across all modules
  - next-node advance within a module (module ends -> None)
  - list modules for the onboarding picker
  - placement: map an estimated CEFR level -> the right STARTING node so an
    advanced learner skips trivial early levels instead of always starting at 1.
"""
from dataclasses import dataclass

from app.content.comm_module import (
    COMM_NODES,
    CommNode,
    MODULE_DESCRIPTION as COMM_DESC,
    MODULE_ID as COMM_ID,
    MODULE_TITLE as COMM_TITLE,
)
from app.content.gd_module import (
    GD_NODES,
    MODULE_DESCRIPTION as GD_DESC,
    MODULE_ID as GD_ID,
    MODULE_TITLE as GD_TITLE,
)
from app.content.interview_module import (
    INTERVIEW_NODES,
    MODULE_DESCRIPTION as INT_DESC,
    MODULE_ID as INT_ID,
    MODULE_TITLE as INT_TITLE,
)
from app.content.school_english_module import (
    SCHOOL_NODES,
    MODULE_DESCRIPTION as SCHOOL_DESC,
    MODULE_ID as SCHOOL_ID,
    MODULE_TITLE as SCHOOL_TITLE,
)


@dataclass(frozen=True)
class Module:
    id: str
    title: str
    description: str
    nodes: list[CommNode]

    @property
    def order(self) -> list[str]:
        return [n.id for n in self.nodes]


MODULES: list[Module] = [
    Module(COMM_ID, COMM_TITLE, COMM_DESC, COMM_NODES),
    Module(INT_ID, INT_TITLE, INT_DESC, INTERVIEW_NODES),
    Module(GD_ID, GD_TITLE, GD_DESC, GD_NODES),
    Module(SCHOOL_ID, SCHOOL_TITLE, SCHOOL_DESC, SCHOOL_NODES),
]

_BY_MODULE: dict[str, Module] = {m.id: m for m in MODULES}
# node_id -> (module_id, CommNode)
_NODE_INDEX: dict[str, tuple[str, CommNode]] = {
    n.id: (m.id, n) for m in MODULES for n in m.nodes
}

# CEFR ordering for placement. Higher rank == more advanced.
CEFR_RANK: dict[str, int] = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
# Self-report buckets the onboarding UI offers, mapped to a target CEFR band.
SELF_REPORT_CEFR: dict[str, str] = {
    "beginner": "A2",
    "intermediate": "B1",
    "advanced": "B2",
    "fluent": "C1",
}


def get_node(node_id: str) -> CommNode:
    """Resolve any node id across all modules. Raises KeyError if unknown."""
    return _NODE_INDEX[node_id][1]


def module_of(node_id: str) -> str:
    """The module id that owns this node. Raises KeyError if unknown."""
    return _NODE_INDEX[node_id][0]


def next_node(node_id: str) -> str | None:
    """Next node id within the SAME module, or None at the module's last level."""
    module_id, _ = _NODE_INDEX[node_id]
    order = _BY_MODULE[module_id].order
    idx = order.index(node_id)
    return order[idx + 1] if idx + 1 < len(order) else None


def all_node_ids() -> set[str]:
    return set(_NODE_INDEX)


def get_module(module_id: str) -> Module:
    return _BY_MODULE[module_id]


def list_modules() -> list[dict]:
    """Onboarding picker payload: module id/title/description + level count."""
    return [
        {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "level_count": len(m.nodes),
            "cefr_range": _cefr_range(m),
        }
        for m in MODULES
    ]


def _cefr_range(m: Module) -> str:
    bands = [n.cefr for n in m.nodes if n.cefr]
    if not bands:
        return ""
    lo = min(bands, key=lambda b: CEFR_RANK.get(b, 0))
    hi = max(bands, key=lambda b: CEFR_RANK.get(b, 0))
    return lo if lo == hi else f"{lo}-{hi}"


def placement_node(module_id: str, target_cefr: str) -> CommNode:
    """Pick the STARTING node in a module for a learner at `target_cefr`.

    Places the learner at the first node whose CEFR band is at least their
    level, so a B2 learner entering a B2-C1 module starts at level 1, while a
    C1 learner skips the B2 ramp. Falls back to level 1 if the learner is below
    the whole module, and to the last node if at/above its ceiling.
    """
    module = _BY_MODULE[module_id]
    target = CEFR_RANK.get(target_cefr, 0)
    for node in module.nodes:
        if CEFR_RANK.get(node.cefr, 0) >= target:
            return node
    return module.nodes[-1]
