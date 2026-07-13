"""Engine state + API schemas.

TutorState is the LangGraph state object. Includes the two council fixes:
  - user_input  : current turn text (was missing — graph had no input boundary)
  - bridge_attempts guard lives in route_node, not here
"""
from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, ConfigDict, Field


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
    last_rubric_result: Optional[dict]
    tutor_turn_plan: Optional[dict]
    evaluation_retry_required: bool
    evaluation_integrity_failure: Optional[dict]
    last_eval_score: float
    last_clean_pass_score: float
    bridge_attempts: int
    # NOTE: every key a graph NODE returns must be declared here. LangGraph's
    # StateGraph(TutorState) treats the TypedDict keys as the only channels, and
    # SILENTLY DROPS any returned key not listed — an undeclared counter would be
    # computed by the node and then lost on the way back to the service. These
    # remediation counters are all written by graph nodes, so they live here.
    clarify_attempts: int         # consecutive "say it in English" nudges (clarify cap)
    redirect_attempts: int        # consecutive fluent-off-task steer-backs (redirect cap)
    attempts: int                 # scored answers this node (clean-pass tracking)
    session_attempts: int         # scored answers THIS session (ceiling-escape gate)
    node_mastered: bool
    display_status: str
    best_independent_score: float
    independent_passes: int
    transfer_passes: int
    pressure_passes: int
    scaffold_successes: int
    meaningful_attempts: int
    readiness_score: float
    last_gap: str
    mastery_evidence: list
    core_qualified: bool
    core_qualification_turn_id: Optional[str]
    core_qualification_evidence: Optional[dict]
    # Pre-authored bridge bookkeeping: the served exercise's answer key (so the
    # NEXT turn can grade a fill_blank/MCQ deterministically instead of by fuzzy
    # rubric) and the ids already served this node (so bridge never repeats one).
    pending_answer_key: Optional[dict]
    served_bridge_ids: list
    active_game_prompt: Optional[dict]  # public-safe copy of the visible card for reload restore
    active_prompt_attempt_type: Optional[str]  # marker for the last committed visible prompt
    pending_prompt_attempt_type: Optional[str]  # transient marker for the in-flight prompt
    active_gd_prompt_topic: Optional[str]  # exact motion attached to the committed learner prompt
    pending_gd_prompt_topic: Optional[str]  # exact motion staged for the next visible prompt
    # True only on a turn that graded a served BRIDGE fill against its answer key
    # (set by evaluate_node, read by _update_progress). A correct bridge fill is a
    # scaffolded sub-step, NOT a clean pass at this node, so the advance-streak
    # increment is gated on this being False (H1) — otherwise two scaffolded-down
    # fills would promote a struggling learner to harder content.
    last_graded_bridge: Optional[bool]
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
    remediation: bool
    tester_level: bool
    review_level: bool
    session_learning_delta: dict
    session_over: bool            # learner ended the session with a goodbye
    # TEST-mode (assessment) simulation state; empty/None for coaching sessions.
    sim_topic: str                # the topic the persona panel debates/probes
    personas: Optional[list]      # roster cached after the first simulation round
    blackboard: Optional[dict]    # writers'-room group memory; lazy-init on the first simulation round
    probe_items: Optional[list]   # prep-weakness probe bank threaded into the Director prompt (test mode)
    career_context: Optional[dict]  # private, sanitized career context for prompts
    scenario_config: Optional[dict] # public-safe scenario labels and selected setup
    context_hash: str              # task/profile hash for context-aware probe cache


# ===== API contract v0 (skeleton — wired when graph lands) =====


class SessionStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    competency_node: str
    test_mode: bool = False   # True -> open on the assessment TaskType variant
    confirm: bool = False     # True -> learner accepted the credit charge (two-tap gate)
    reattempt_confirmed: bool = False
    simulation_config: dict = Field(default_factory=dict)
    client_start_id: Optional[str] = None
    source_session_id: Optional[str] = None
    source_transition_id: Optional[str] = None
    source_action: Optional[Literal["advance", "reattempt", "advance_reattempt"]] = None


class SessionStartResponse(BaseModel):
    session_id: str
    node_title: str
    first_message: str
    current_mastery: float
    resumed: bool = False
    display_status: str = "active"
    node_mastered: bool = False
    readiness_score: float = 0.0
    best_independent_score: float = 0.0


class AssessmentClientAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["ask_panelist", "clarify", "new_angle", "move_on"]
    speaker_id: Optional[str] = None
    speaker_name: Optional[str] = None
    label: Optional[str] = None
    source: Literal["quick_action", "typed_control"] = "quick_action"


class SessionTurnRequest(BaseModel):
    session_id: str
    user_input: str
    client_turn_id: Optional[str] = None
    expected_session_version: Optional[int] = None
    assessment_action: Optional[AssessmentClientAction] = None


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
    turn_id: str | None = None


class NodeAdvanceFrame(BaseModel):
    """event: node_advance — learner completed current node, new node begins."""
    from_node: str
    to_node: str


class ProgressUpdateFrame(BaseModel):
    """event: progress_update — per-turn mastery signal for the progress bar."""
    node_id: str
    mastery: float          # current EMA mastery (0.0–1.0)
    readiness_score: float
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
    score_metric: str = "mastery"
    readiness_score: float = 0.0
    mastery_score: float = 0.0
    avg_score: Optional[float] = None  # deprecated compatibility alias


class SpeakerFrame(BaseModel):
    """event: speaker — TEST mode only; new persona bubble begins."""
    speaker_id: str
    name: str


class SimulationStateFrame(BaseModel):
    """event: simulation_state — TEST mode only; tension update."""
    turn: int
    speaker_id: str
    tension: float
    should_close: bool = False   # Director wind-down / hard round-cap signal


class AdaptationCueFrame(BaseModel):
    """event: adaptation_cue — selector rationale when the learning path adapts."""
    action: str        # "ADVANCE" | "REMEDIATE"
    band: str          # "foundational" | "standard" | "stretch"
    rationale: str     # short human-readable reason from the selector


class DoneFrame(BaseModel):
    """event: done — always the final frame; full post-turn state snapshot."""
    session_id: str
    competency_node: str
    task_type: str = ""
    module_id: str = ""
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
    node_mastered: bool = False
    display_status: str = "active"
    best_independent_score: float = 0.0
    independent_passes: int = 0
    transfer_passes: int = 0
    pressure_passes: int = 0
    scaffold_successes: int = 0
    meaningful_attempts: int = 0
    readiness_score: float = 0.0
    last_gap: str = ""
    mastery_evidence: list[str] = []
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
    # TEST-mode persona roster (interview panel / GD debaters): list of
    # {speaker_id, name, stance|role}. None for coaching sessions and the first
    # simulation frame. Lets the simulator UI label bubbles/avatars with the real
    # roster instead of a hardcoded fallback.
    personas: Optional[list] = None
    scenario_config: Optional[dict] = None
    status: str = "active"
    session_over: bool = False
    simulation_round: int = 0
    simulation_score: Optional[float] = None
    simulation_report: Optional[dict] = None
    session_version: int = 1
    pending_transition: Optional[dict] = None
    input_allowed: bool = True
    block_reason: Optional[str] = None
