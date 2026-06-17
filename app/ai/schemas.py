"""Structured-output schemas for the engine's AI calls.

Council rule (structured.py): Flash-Lite ignores schema `description` fields,
so instructions live in the prompt, not here. Keep string fields short.
"""
from typing import Literal

from pydantic import BaseModel, Field


class DiagnosisEval(BaseModel):
    """Flash-Lite structured read of one learner answer.

    `score` drives routing (route_node). The text fields feed the next
    pedagogy prompt so the tutor references the learner's actual answer.
    """

    score: float = Field(ge=0.0, le=1.0)
    understanding: str          # one-line read of what the learner grasped
    errors: list[str]           # concrete mistakes (empty if none)
    strengths: list[str]        # what they did well (empty if none)
    next_focus: str             # the single thing to work on next
    # Routing split (council fix #1/#6): an off-task answer scores 0.0 by the
    # rubric, but a fluent off-task answer (on_task=False, english=True) needs a
    # REDIRECT, while a genuine non-answer (english=False) needs a bridge. Affect
    # (#5) lets a frustrated/discouraged read flip support without regex. Defaults
    # keep old callers/back-compat decodes valid.
    on_task: bool = True        # did the answer attempt the assessed skill?
    english: bool = True        # competent English (vs empty/gibberish/non-English)?
    affect: Literal["neutral", "frustrated", "confident", "confused"] = "neutral"
    goodbye: bool = False       # learner is ending the session (natural farewell)


class SimulationReport(BaseModel):
    """End-of-session score for a TEST-mode simulation (interview_test / gd_test).

    Test sessions are scored, not coached mid-stream: the round runner streams
    persona turns with no feedback, and this report is produced once at the end.
    `score` (0-1) gates progression like DiagnosisEval.score; the text fields are
    the deferred feedback shown to the learner after the session closes.

    GD rubric sub-scores (0-1, default 0.0 for non-GD sessions):
      participation_score — claimed the floor, interjected, held space.
      relevance_score     — stayed on topic, built coherent arguments.
      language_score      — fluency, grammar, vocabulary under pressure.
    """

    score: float = Field(ge=0.0, le=1.0)
    summary: str                # one-paragraph read of the whole performance
    strengths: list[str]        # what landed (empty if none)
    improvements: list[str]     # the few things to work on next
    # GD rubric dimensions — 0.0 default keeps old callers (interview_test) valid
    participation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    language_score: float = Field(default=0.0, ge=0.0, le=1.0)
    # Interview rubric dimensions — 0.0 default keeps GD callers valid
    clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ProbeItem(BaseModel):
    """One probe item for a TEST-mode assessment (gd_test / interview_test).

    Generated up front (not mid-stream) so the persona panel / interviewer has a
    ready bank to press the learner with. `skill_id` ties the item back to a
    SkillID the learner was weak on in prep, so the test concentrates there.
    """

    skill_id: str               # SkillID value the item probes (ties to a weakness)
    prompt: str                 # the question / debate motion / scenario shown
    aim: str                    # one line: what a strong answer demonstrates


class ProbeSet(BaseModel):
    """Wrapper so the structured call returns a single model (a list of items)."""

    items: list[ProbeItem]


class FillBlankGame(BaseModel):
    """Gamified teach item for scaffold turns (scaffold >= 1).

    Rendered by the client as an interactive fill-in-the-blank widget. The
    learner's fill is submitted as the next turn answer and scored normally —
    the graph stays intact. `answer_key` stays server-side (not sent to client).
    """

    sentence: str       # one natural sentence with exactly one ___ gap
    hint: str           # short grammar/vocab category label — NOT the answer
    answer_key: str     # correct fill, shown only after the learner submits
    context: str        # one line: why this gap targets the current teaching focus


class PlacementEval(BaseModel):
    """Flash-Lite read of an onboarding writing sample -> CEFR estimate.

    Drives placement: `cefr` maps (in the registry) to the learner's STARTING
    node so an advanced learner skips trivial early levels. `rationale` is shown
    to the learner so the placement feels transparent, not arbitrary.
    """

    cefr: str = Field(pattern="^(A1|A2|B1|B2|C1|C2)$")
    rationale: str              # one-line justification shown to the learner


class DirectorDecision(BaseModel):
    """Writers'-room Director output: who speaks next and with what intent.

    Produced once per round; drives blackboard updates and persona selection.
    `tension` and `answer_quality` are plain float (no Field bounds) so a
    slightly out-of-range LLM value doesn't crash the turn — clamping happens
    downstream in apply_decision.
    """

    action: Literal["probe_deeper", "pivot_topic", "escalate_pressure", "wind_down"]
    next_speaker: str           # speaker_id from roster
    intent: str                 # concrete instruction to the persona, cites the transcript
    tension: float              # 0.0-1.0 target after this turn
    answer_quality: float       # director's read of the learner's last answer (0-1)
    should_close: bool          # signal the simulation should wrap
