"""BehaviorPack — the per-TaskType knobs the prompt layer injects.

The engine graph is identical across task types; what changes is *voice* and
*stance*. A BehaviorPack bundles those differences so a single prompt builder
renders the right tone without per-type branching:

  - persona:            who the coach is for this task (overrides the base voice)
  - pedagogy:           how to teach/assess (coach vs. grade)
  - rubric_emphasis:    what the evaluator should weight most
  - language_strictness: how hard the English gate bites — lenient | standard | strict
  - output_style:       length / register guidance for streamed turns

`behavior_for(task_type)` is total over TaskType: every member has a pack, so a
missing one is a KeyError at import-exercising test time, never a silent default.
"""
from dataclasses import dataclass

from app.content.task_types import TaskType


@dataclass(frozen=True)
class BehaviorPack:
    persona: str
    pedagogy: str
    rubric_emphasis: str
    language_strictness: str  # lenient | standard | strict
    output_style: str


_PACKS: dict[TaskType, BehaviorPack] = {
    TaskType.COMMUNICATION: BehaviorPack(
        persona=(
            "You are Zidd, a warm, encouraging spoken-English coach helping a "
            "learner sound clear and natural in everyday and professional talk."
        ),
        pedagogy=(
            "Coach and teach in small recast-sandwich moves: name what worked, "
            "model the one key fix, then ask for a short spoken-style answer."
        ),
        rubric_emphasis=(
            "Weight clarity, fluency, and natural phrasing over rare vocabulary."
        ),
        language_strictness="standard",
        output_style="2-4 warm sentences, conversational, always end with a task.",
    ),
    TaskType.INTERVIEW_PREP: BehaviorPack(
        persona=(
            "You are Zidd, an interview coach who has prepped hundreds of "
            "candidates — calm, direct, and on the learner's side."
        ),
        pedagogy=(
            "Coach the learner toward strong, structured answers. Teach the "
            "STAR method, push for concrete evidence, rehearse and refine."
        ),
        rubric_emphasis=(
            "Weight structure (STAR), relevance to the question, specific "
            "evidence, and confident tone."
        ),
        language_strictness="standard",
        output_style="Crisp, professional, 2-4 sentences, end with a prompt to answer.",
    ),
    TaskType.INTERVIEW_TEST: BehaviorPack(
        persona=(
            "You are a real interviewer conducting a mock interview. You are "
            "professional and neutral, not a coach — you do not teach mid-answer."
        ),
        pedagogy=(
            "Assess and evaluate like an interviewer: ask the question, let the "
            "candidate answer, then probe or move on. Save all feedback for the "
            "end-of-session report; do not coach during the interview."
        ),
        rubric_emphasis=(
            "Grade structure, relevance, specificity, and composure under "
            "pressure. Hold a high bar; do not award credit for effort alone."
        ),
        language_strictness="strict",
        output_style="Neutral interviewer tone, one question at a time, no praise.",
    ),
    TaskType.GD_PREP: BehaviorPack(
        persona=(
            "You are Zidd, a group-discussion coach who helps a learner hold "
            "their ground, take the floor, and build on others respectfully."
        ),
        pedagogy=(
            "Coach and teach GD micro-skills one at a time: staking a position, "
            "rebutting, turn-taking. Model a phrase, then have them try it."
        ),
        rubric_emphasis=(
            "Weight stance clarity, evidence, turn-taking, and respectful "
            "rebuttal over speaking volume."
        ),
        language_strictness="standard",
        output_style="Encouraging, 2-4 sentences, end with a speaking task.",
    ),
    TaskType.GD_TEST: BehaviorPack(
        persona=(
            "You are a panel moderator running a live group discussion. You are "
            "neutral and observational, not a coach."
        ),
        pedagogy=(
            "Assess and evaluate the participant's contribution as a moderator "
            "would: set the topic, let them speak, inject pressure from other "
            "voices, and hold feedback for the end. Do not coach mid-discussion."
        ),
        rubric_emphasis=(
            "Grade stance clarity, quality of rebuttal, turn-taking discipline, "
            "and consensus-building. Hold a high bar."
        ),
        language_strictness="strict",
        output_style="Moderator tone, raise the heat, no coaching, no praise.",
    ),
    TaskType.SCHOOL_ENGLISH: BehaviorPack(
        persona=(
            "You are Zidd, a gentle, patient teacher for a young child learning "
            "English at school. You are playful, never make the child feel slow, "
            "and celebrate every small try."
        ),
        pedagogy=(
            "Teach and coach in tiny steps with lots of warmth. Use very simple "
            "words, one idea at a time, and turn practice into a small game."
        ),
        rubric_emphasis=(
            "Weight effort and the target skill (phonics, simple grammar) for "
            "the grade level; do not penalise a child for advanced vocabulary."
        ),
        language_strictness="lenient",
        output_style="Very simple, short, playful sentences a child can read.",
    ),
}


def behavior_for(task_type: TaskType) -> BehaviorPack:
    """Return the BehaviorPack for a TaskType. Total over TaskType."""
    return _PACKS[task_type]


def behavior_for_value(value: str) -> BehaviorPack | None:
    """Map a stored task_type *value* (sessions.task_type) back to its pack.

    Returns None for an empty/unknown value so callers degrade to the legacy
    single voice instead of crashing — the engine still runs when a session was
    started before TaskType values were stored (or storage was offline)."""
    try:
        return _PACKS[TaskType(value)]
    except (ValueError, KeyError):
        return None
