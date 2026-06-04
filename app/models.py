"""Engine state + API schemas.

TutorState is the LangGraph state object. Includes the two council fixes:
  - user_input  : current turn text (was missing — graph had no input boundary)
  - bridge_attempts guard lives in route_node, not here
"""
from typing import Optional, TypedDict

from pydantic import BaseModel


class TutorState(TypedDict):
    user_id: str
    session_id: str
    competency_node: str
    user_input: str               # council fix: current user turn text
    current_mastery: float
    turn_count: int
    messages: list[dict]
    last_diagnosis: dict
    last_eval_score: float
    bridge_attempts: int
    attempts: int                 # scored answers this node (clean-pass tracking)
    memory_context: str
    session_summary: Optional[str]
    pending: Optional[object]     # GenSpec the service will stream after the graph
    last_route: Optional[str]     # which pedagogy node fired (for service/telemetry)
    # personalization / progression bookkeeping (service-owned; coach_view
    # projects a subset into the private coaching directive block). Declared here
    # because the full state dict is passed into graph.ainvoke, so nodes see them.
    learner_name: str             # addresses the learner by name in directives
    clean_streak: int             # consecutive clean passes at current node
    advance_streak: int           # streak length required to advance (ADVANCE_STREAK)
    level_fails: int              # consecutive hard fails at current node
    strengthen_attempts: int      # consecutive strengthens in the 0.4-0.6 plateau
    scaffold: int                 # >=1 -> scaffold HARD (down-ladder)
    needs_support: bool           # set per-turn from frustration detection
    session_over: bool            # learner ended the session with a goodbye


# ===== API contract v0 (skeleton — wired when graph lands) =====


class SessionStartRequest(BaseModel):
    user_id: str
    competency_node: str


class SessionStartResponse(BaseModel):
    session_id: str
    node_title: str
    first_message: str
    current_mastery: float


class SessionTurnRequest(BaseModel):
    session_id: str
    user_input: str


class PlacementRequest(BaseModel):
    module_id: str
    writing_sample: Optional[str] = None
    self_report: Optional[str] = None   # beginner | intermediate | advanced | fluent
