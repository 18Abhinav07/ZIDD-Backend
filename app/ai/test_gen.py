"""Phase 4 — assessment test-item generation.

A TEST-mode session (gd_test, interview_test) is scored, not coached: the panel
presses the learner with prepared probe items and feedback is deferred to the
end. `generate_test_items` builds that bank up front. It reads the learner's
PREP-side weaknesses (via prep_counterpart, mirroring the Phase 3.3 seeding) so
the assessment concentrates exactly where they struggled, and rides the same
`_local()` dispatch as every other structured call so it runs offline on qwen.

A TEST session must never open with an empty roster, so an empty or failed
generation falls back to a deterministic per-task set.
"""
from app.ai.behaviors import behavior_for
from app.ai.calls import _local
from app.ai.clients import get_gemini_client
from app.ai.local import ollama_structured
from app.ai.prompts import build_test_gen_prompt
from app.ai.schemas import ProbeItem, ProbeSet
from app.ai.structured import call_with_structured_output
from app.content.skills import SkillID
from app.content.task_types import TaskType, prep_counterpart
from app.storage import get_storage

__all__ = ["ProbeItem", "ProbeSet", "generate_test_items"]


# Deterministic safety net: a TEST session must never open with no items, and an
# OFFLINE assessment (Ollama down) must be as full and skill-diverse as an online
# one — so each bank covers ALL of its mode's micro-skills with >= n_items
# (default 4) probes. Used when the engine returns an empty set or the call fails.
# Keyed on task_type value; an unknown task_type falls through to a generic prompt.
_FALLBACK: dict[str, list[ProbeItem]] = {
    TaskType.GD_TEST.value: [
        ProbeItem(
            skill_id=SkillID.GD_STANCE_CLARITY.value,
            prompt="Motion: 'Remote work helps society more than it harms it.' "
            "Open by stating your stance in one sentence, then defend it.",
            aim="Commits to a clear side before reasoning.",
        ),
        ProbeItem(
            skill_id=SkillID.GD_REBUTTAL.value,
            prompt="Another participant says your stance ignores the people who "
            "cannot work remotely. Respond.",
            aim="Directly rebuts the point instead of restating their own.",
        ),
        ProbeItem(
            skill_id=SkillID.GD_TURN_TAKING.value,
            prompt="Two members are talking over each other and a quieter member "
            "hasn't spoken yet. Bring them in without losing your own point.",
            aim="Makes space for others while holding the thread of the discussion.",
        ),
        ProbeItem(
            skill_id=SkillID.GD_CONSENSUS_BUILDING.value,
            prompt="The group is split down the middle. Propose a position both "
            "sides could accept.",
            aim="Builds toward shared ground without abandoning a stance.",
        ),
        ProbeItem(
            skill_id=SkillID.GD_STANCE_CLARITY.value,
            prompt="In one closing line, sum up the group's discussion and where "
            "you now stand.",
            aim="Synthesises the exchange and restates a clear final position.",
        ),
    ],
    TaskType.INTERVIEW_TEST.value: [
        ProbeItem(
            skill_id=SkillID.STRUCTURE_STAR_METHOD.value,
            prompt="Tell me about a time you faced a difficult problem at work or "
            "school and how you handled it.",
            aim="Answers with situation, task, action, and result.",
        ),
        ProbeItem(
            skill_id=SkillID.SPECIFICITY_EXAMPLES.value,
            prompt="What is a strength of yours? Give a concrete example that "
            "proves it.",
            aim="Backs the claim with a specific, real example.",
        ),
        ProbeItem(
            skill_id=SkillID.ANSWER_RELEVANCE.value,
            prompt="Tell me about a time you failed. What actually went wrong — "
            "not what you would do differently?",
            aim="Answers the exact question asked and owns the failure honestly.",
        ),
        ProbeItem(
            skill_id=SkillID.CONFIDENCE_TONE.value,
            prompt="Why should we choose you over other candidates?",
            aim="Answers with composed, confident, specific language.",
        ),
        ProbeItem(
            skill_id=SkillID.STRUCTURE_STAR_METHOD.value,
            prompt="Describe a time you disagreed with a teammate. What did you do, "
            "and how did it turn out?",
            aim="Structures the answer and lands on a concrete result.",
        ),
    ],
}

_GENERIC_FALLBACK = [
    ProbeItem(
        skill_id=SkillID.ANSWER_RELEVANCE.value,
        prompt="Speak for a minute on a topic you care about and explain why.",
        aim="Stays on topic with clear, competent English.",
    ),
]


def _fallback_items(task_type: str) -> list[ProbeItem]:
    return list(_FALLBACK.get(task_type, _GENERIC_FALLBACK))


async def generate_test_items(
    user_id: str, task_type: str, n_items: int = 4
) -> list[ProbeItem]:
    """Build the assessment probe bank for a TEST-mode session.

    Reads the learner's prep-side weaknesses (prep_counterpart resolves the
    sibling task type), asks the engine for items concentrated there, and falls
    back to a deterministic set if generation is empty or errors.
    """
    prep_tt = prep_counterpart(task_type)
    try:
        weaknesses = await get_storage().get_weaknesses(user_id, prep_tt)
    except Exception:
        weaknesses = []

    behavior = behavior_for(TaskType(task_type))
    prompt = build_test_gen_prompt(behavior, weaknesses, n_items)

    try:
        if _local():
            result = await ollama_structured(prompt, ProbeSet)
        else:
            result = await call_with_structured_output(
                get_gemini_client(), prompt, ProbeSet
            )
        items = list(result.items)
    except Exception:
        items = []

    return items if items else _fallback_items(task_type)
