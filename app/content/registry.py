"""Content registry — aggregates every module into one lookup surface.

The engine was originally hardcoded to the communication module. This registry
now loads structured JSON curricula from app/content/data/ at startup.

Responsibilities:
  - resolve any node id -> Concept, across all modules
  - next-node advance within a module (module ends -> None)
  - list modules for the onboarding picker
  - placement: map an estimated CEFR level -> the right STARTING node.
"""
import json
from pathlib import Path

from app.content.schema import Module, Concept

# Define known module IDs
COMM_ID = "communication"
INT_ID = "interview"
GD_ID = "group_discussion"
SCHOOL_ID = "school_english"

def _load_modules() -> list[Module]:
    modules = []
    data_dir = Path(__file__).parent / "data"
    for json_file in data_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            modules.append(Module.model_validate(data))
    
    # Sort modules to match previous hardcoded order, though not strictly required
    order_pref = {COMM_ID: 1, INT_ID: 2, GD_ID: 3, SCHOOL_ID: 4}
    modules.sort(key=lambda m: order_pref.get(m.id, 99))
    return modules

MODULES: list[Module] = _load_modules()

_BY_MODULE: dict[str, Module] = {m.id: m for m in MODULES}
# node_id -> (module_id, Concept)
_NODE_INDEX: dict[str, tuple[str, Concept]] = {
    n.id: (m.id, n) for m in MODULES for n in m.nodes
}

# Merge the NCERT school curriculum chapters into the engine indexes. A chapter
# IS a Module, so registering its levels here lets the EXISTING coaching engine
# (get_node / module_of / next_node / start_session) tutor a chapter's levels
# exactly like any other module — no parallel serving path needed. Chapters are
# NOT added to MODULES, so they never appear in the onboarding module picker.
from app.content import curriculum as _curriculum  # noqa: E402

for _ch in _curriculum.all_chapters():
    if _ch.id not in _BY_MODULE:
        _BY_MODULE[_ch.id] = _ch
        for _n in _ch.nodes:
            _NODE_INDEX[_n.id] = (_ch.id, _n)

# CEFR ordering for placement. Higher rank == more advanced.
CEFR_RANK: dict[str, int] = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
# Self-report buckets the onboarding UI offers, mapped to a target CEFR band.
# A self-described "beginner" lands on the A1 on-ramp (comm_00_greetings), the
# true ground floor, not mid-A2 — the on-ramp is quick to clean-pass, so an
# actual A2 who picked "beginner" advances out of it fast, while a real A1 gets
# a gentle start instead of being dropped into self-intro.
SELF_REPORT_CEFR: dict[str, str] = {
    "beginner": "A1",
    "intermediate": "B1",
    "advanced": "B2",
    "fluent": "C1",
}


# school_english is a primary-grade ladder, not a CEFR continuum: it places by
# grade (2-5), not by a self-report CEFR band. Each grade's band starts at this
# node id (the school module groups four nodes per grade, id-prefixed c2_/c3_/…).
GRADE_PLACED_MODULES = frozenset({SCHOOL_ID})
SCHOOL_GRADE_START: dict[int, str] = {
    2: "c2_alphabet_sounds",
    3: "c3_action_words",
    4: "c4_past_tense",
    5: "c5_tenses_mix",
}
_MIN_GRADE, _MAX_GRADE = 2, 5


def uses_grade_placement(module_id: str) -> bool:
    """True for modules placed by school grade instead of a CEFR band."""
    return module_id in GRADE_PLACED_MODULES


def grade_placement_node(grade: int) -> Concept:
    """STARTING node for a school_english learner in `grade` (2-5).

    Grade N starts at the first node of that grade's band. Out-of-range grades
    clamp into [2, 5] so onboarding never fails on a stray value.
    """
    g = max(_MIN_GRADE, min(_MAX_GRADE, grade))
    return get_node(SCHOOL_GRADE_START[g])


def get_node(node_id: str) -> Concept:
    """Resolve any node id across all modules. Raises KeyError if unknown.

    Returns a DEEP COPY of the canonical Concept, never the shared instance: the
    same Concept object lives in module-global _NODE_INDEX, so handing out the
    reference let any caller that mutated a returned node (e.g. tweaking a field
    in a graph step) silently corrupt the registry for every later caller."""
    return _NODE_INDEX[node_id][1].model_copy(deep=True)


def module_of(node_id: str) -> str:
    """The module id that owns this node. Raises KeyError if unknown."""
    return _NODE_INDEX[node_id][0]


def is_voice_node(node_id: str) -> bool:
    """True if a node belongs to the voice tier (level_type == 'voice').

    The voice tier is gated "coming soon" (no voice pipeline exists yet): it is
    excluded from placement and the advance ladder, and a direct session start on
    one is refused rather than coached/graded as typed text."""
    return _NODE_INDEX[node_id][1].level_type == "voice"


def next_node(node_id: str) -> str | None:
    """Next TEXT node id within the SAME module, or None at the last text level.

    Voice-tier nodes are gated "coming soon" (no voice pipeline exists yet), so
    the advance ladder skips them: a learner finishing the last text node
    completes the module instead of being advanced into a voice node that would
    silently be coached/graded as typed text."""
    module_id, _ = _NODE_INDEX[node_id]
    order = _BY_MODULE[module_id].order
    idx = order.index(node_id)
    for nxt in order[idx + 1:]:
        if not is_voice_node(nxt):
            return nxt
    return None


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
            # Count only REACHABLE nodes — voice nodes are gated "coming soon", so
            # advertising them (e.g. "11 NODES") overstated a comm module whose
            # learner can only reach 8. Mirrors placement/advance, which skip them.
            "level_count": sum(1 for n in m.nodes if n.level_type != "voice"),
            # A module is placed EITHER by grade (school) OR by CEFR band; the
            # picker surfaces only the relevant range and leaves the other empty.
            "cefr_range": "" if uses_grade_placement(m.id) else _cefr_range(m),
            "grade_range": _grade_range(m) if uses_grade_placement(m.id) else "",
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


def _grade_range(m: Module) -> str:
    """Min-max grade span of a grade-placed module, e.g. "2-5" (or "3" if one)."""
    grades = [int(n.id[1]) for n in m.nodes]
    lo, hi = min(grades), max(grades)
    return str(lo) if lo == hi else f"{lo}-{hi}"


def placement_node(module_id: str, target_cefr: str) -> Concept:
    """Pick the STARTING node in a module for a learner at `target_cefr`.

    Places the learner at the first node whose CEFR band is at least their
    level, so a B2 learner entering a B2-C1 module starts at level 1, while a
    C1 learner skips the B2 ramp. Falls back to level 1 if the learner is below
    the whole module, and to the last node if at/above its ceiling.

    Voice-tier nodes are excluded from placement (they are gated "coming soon"):
    without this, the non-monotonic comm ladder (comm_08 regresses to A2 after
    comm_07=B2) made the at/above-ceiling fallback land a strong learner on the
    last positional node — a voice node coached as text. Placement now considers
    text nodes only, so the ceiling fallback is the last TEXT node.
    """
    module = _BY_MODULE[module_id]
    target = CEFR_RANK.get(target_cefr, 0)
    pool = [n for n in module.nodes if n.level_type != "voice"] or list(module.nodes)
    for node in pool:
        if CEFR_RANK.get(node.cefr, 0) >= target:
            return node
    return pool[-1]

