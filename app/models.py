"""Engine state + API schemas.

TutorState is the LangGraph state object. Includes the two council fixes:
  - user_input  : current turn text (was missing — graph had no input boundary)
  - bridge_attempts guard lives in route_node, not here
"""
from typing import Literal, Optional, TypedDict

from pydantic import BaseModel


class TutorState(TypedDict):
    user_id: str
    session_id: str
    competency_node: str
    task_type: str                # TaskType.value — drives per-TaskType BehaviorPack
    user_input: str               # council fix: current user turn text
    current_mastery: float
    turn_count: int
    messages: list[dict]
    last_diagnosis: dict
    last_eval_score: float
    bridge_attempts: int
    attempts: int                 # scored answers this node (clean-pass tracking)
    memory_context: list   # list[dict] from load_context; str accepted for legacy compat
    weakness_context: list        # aggregated prior weaknesses (get_weaknesses rows)
    session_summary: Optional[str]
    pending: Optional[object]     # GenSpec the service will stream after the graph
    pending_game: Optional[dict]  # FillBlankGame dict; set by teach_node on scaffold>=1
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
    frustration_turns: int        # consecutive turns flagged as frustrated/confused
    session_over: bool            # learner ended the session with a goodbye
    # TEST-mode (assessment) simulation state; empty/None for coaching sessions.
    sim_topic: str                # the topic the persona panel debates/probes
    personas: Optional[list]      # roster cached after the first simulation round


# ===== API contract v0 (skeleton — wired when graph lands) =====


class SessionStartRequest(BaseModel):
    user_id: str
    competency_node: str
    test_mode: bool = False   # True -> open on the assessment TaskType variant
    confirm: bool = False     # True -> learner accepted the credit charge (two-tap gate)


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
    grade: Optional[int] = None         # school_english only: primary grade 2-5


# ===== SSE frame schemas (UI component contract) =====
#
# Every SSE frame the client receives is one of these shapes. The API layer
# serialises them manually; these models exist so the frontend team has a typed
# contract and so tests can assert against structured objects instead of raw JSON.
#
# Frame lifecycle per /session/turn:
#   1. Zero or more plain `data: "<token>"` frames (streaming coach text)
#   2. Exactly one `event: progress_update` frame (mastery bar update)
#   3. IF module complete: exactly one `event: session_recap` frame
#      ELSE IF node advanced: exactly one `event: node_advance` frame
#            followed by zero or more plain tokens (new-node opening)
#   4. Exactly one `event: done` frame (full state snapshot, always last)
#
# GD/interview TEST sessions also emit `event: speaker` frames before each
# persona's text tokens.


class GamePromptFrame(BaseModel):
    """event: game_prompt — scaffold teach turn; client renders a gamified widget.

    `answer_key` is intentionally omitted from this frame (server-side only).
    The learner submits their fill as normal text; the next turn scores it."""
    type: Literal["fill_blank", "multiple_choice", "spoken"] = "fill_blank"
    sentence: str       # sentence with ___ gap
    hint: str           # grammar/vocab category label
    context: str        # why this gap targets the teaching focus
    options: list[str] | None = None


class NodeAdvanceFrame(BaseModel):
    """event: node_advance — learner completed current node, new node begins."""
    from_node: str
    to_node: str


class ProgressUpdateFrame(BaseModel):
    """event: progress_update — per-turn mastery signal for the progress bar."""
    node_id: str
    mastery: float          # current EMA mastery (0.0–1.0)
    clean_streak: int       # consecutive passing answers on this node
    attempts: int           # total scored answers on this node


class WeaknessRow(BaseModel):
    """One row from the weakness table, embedded in SessionRecapFrame."""
    skill_id: str
    hit_count: int
    last_raw: Optional[str] = None   # raw model next_focus hint, for display


class SessionRecapFrame(BaseModel):
    """event: session_recap — emitted when all module nodes are complete."""
    nodes_completed: list[str]       # node_id strings in completion order
    weaknesses: list[WeaknessRow]
    avg_score: float                 # final EMA mastery at session close (0.0–1.0)


class SpeakerFrame(BaseModel):
    """event: speaker — TEST mode only; new persona bubble begins."""
    speaker_id: str
    name: str


class SimulationStateFrame(BaseModel):
    """event: simulation_state — TEST mode only; tension update."""
    turn: int
    speaker_id: str
    tension: float


class DoneFrame(BaseModel):
    """event: done — always the final frame; full post-turn state snapshot."""
    session_id: str
    competency_node: str
    node_title: str
    current_mastery: float
    turn_count: int
    last_route: Optional[str] = None
    last_eval_score: Optional[float] = None
    bridge_attempts: int = 0
    strengthen_attempts: int = 0
    attempts: int = 0
    clean_streak: int = 0
    scaffold: int = 0
    remediation: bool = False
    module_done: bool = False
    phase: str = ""           # macro lifecycle label (e.g. "early", "mid", "late")
    level_kind: str = ""      # node type label (e.g. "intro", "bridge", "challenge")
    tester_level: bool = False
    weaknesses: list[WeaknessRow] = []
    on_task: bool = True
    english: bool = True
    affect: str = "neutral"   # Literal["neutral","frustrated","confident","confused"]
    avatar_emotion: str = "neutral"  # derived from affect + last_eval_score
