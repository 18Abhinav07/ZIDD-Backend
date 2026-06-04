"""Structured-output schemas for the engine's AI calls.

Council rule (structured.py): Flash-Lite ignores schema `description` fields,
so instructions live in the prompt, not here. Keep string fields short.
"""
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
    affect: str = "neutral"     # neutral | frustrated | confident


class PlacementEval(BaseModel):
    """Flash-Lite read of an onboarding writing sample -> CEFR estimate.

    Drives placement: `cefr` maps (in the registry) to the learner's STARTING
    node so an advanced learner skips trivial early levels. `rationale` is shown
    to the learner so the placement feels transparent, not arbitrary.
    """

    cefr: str = Field(pattern="^(A1|A2|B1|B2|C1|C2)$")
    rationale: str              # one-line justification shown to the learner
