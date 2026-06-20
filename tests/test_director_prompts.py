"""Writers'-room prompt builders — pure string composition, no model call.

build_director_prompt and build_persona_prompt only return strings: they make
no LLM calls and import nothing from app.ai.calls. These guards prove the
blackboard, roster, transcript, and the director's/persona's instructions all
reach the rendered prompt, and that the persona is barred from self-tagging.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import build_director_prompt, build_persona_prompt  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402


def _bb() -> dict:
    return {
        "topic": "Remote work",
        "phase": "probing",
        "tension": 0.4,
        "turn": 2,
        "covered": ["intro"],
        "open_threads": ["cohesion"],
        "positions": {},
        "last_quality": 0.5,
    }


def _personas() -> list[dict]:
    return [
        {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"},
        {"speaker_id": "gd_b", "name": "Meera", "stance": "strongly against"},
    ]


# ---------- director prompt ----------

def test_director_prompt_includes_topic_and_transcript():
    transcript = "[Learner]: Remote work boosts focus for me."
    prompt = build_director_prompt(_bb(), _personas(), TaskType.GD_TEST, transcript)
    assert "Remote work" in prompt
    assert transcript in prompt


def test_director_prompt_lists_every_persona_name_and_speaker_id():
    prompt = build_director_prompt(
        _bb(), _personas(), TaskType.GD_TEST, "[Learner]: hello"
    )
    for p in _personas():
        assert p["name"] in prompt
        assert p["speaker_id"] in prompt


def test_director_prompt_coaches_all_six_decisions():
    prompt = build_director_prompt(
        _bb(), _personas(), TaskType.GD_TEST, "[Learner]: hello"
    ).lower()
    # who speaks next + an intent + a tension/quality judgement, in prose
    assert "next" in prompt
    assert "intent" in prompt
    assert "tension" in prompt
    assert "quality" in prompt
    assert "speaker_id" in prompt
    assert "close" in prompt


def test_director_prompt_embeds_blackboard_state():
    prompt = build_director_prompt(
        _bb(), _personas(), TaskType.GD_TEST, "[Learner]: hello"
    )
    assert "probing" in prompt          # current phase
    assert "0.4" in prompt              # current tension
    assert "intro" in prompt            # covered
    assert "cohesion" in prompt         # open thread


# ---------- persona prompt ----------

def test_persona_prompt_includes_name_intent_topic_and_transcript():
    persona = {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"}
    intent = "Press the learner for a concrete metric."
    transcript = "[Learner]: I think remote work is fine."
    prompt = build_persona_prompt(persona, intent, transcript, _bb())
    assert "Aarav" in prompt
    assert intent in prompt
    assert "Remote work" in prompt
    assert transcript in prompt


def test_persona_prompt_forbids_self_tagging():
    persona = {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"}
    prompt = build_persona_prompt(
        persona,
        "Press the learner for a concrete metric.",
        "[Learner]: I think remote work is fine.",
        _bb(),
    )
    # bars a "[Name]:" / name-prefix self-tag
    assert "Aarav:" in prompt           # the forbidden tag is quoted in the rule
    lower = prompt.lower()
    assert "do not prefix" in lower
    assert "speaker label" in lower


def test_persona_prompt_stays_in_character_no_coaching():
    persona = {"speaker_id": "gd_b", "name": "Meera", "stance": "strongly against"}
    prompt = build_persona_prompt(
        persona, "Challenge the learner's last claim.", "[Learner]: hi", _bb()
    ).lower()
    assert "in character" in prompt
    assert "do not coach" in prompt
