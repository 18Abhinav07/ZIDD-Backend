"""Wave 4.1 — GD personas are enriched, sided debaters + a non-arguing moderator.

The panel carried one-word stances ("strongly in favour"); enriching them with
topic-stable grounds, temperament, and a rhetorical signature makes qwen render
genuinely distinct voices on any motion, and pins the Moderator as a facilitator
rather than a fourth debater.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import build_persona_prompt  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services.simulation_service import build_personas  # noqa: E402


def test_gd_panel_has_four_distinct_enriched_personas():
    personas = build_personas(TaskType.GD_TEST, "any topic")
    assert len(personas) == 4
    stances = [p["stance"] for p in personas]
    assert len(set(stances)) == 4                 # all distinct
    for p in personas:
        assert len(p["stance"]) > 40              # rich, not a one-word stance


def test_moderator_is_a_nonarguing_facilitator():
    mod = next(p for p in build_personas(TaskType.GD_TEST, "t")
               if p["speaker_id"] == "moderator")
    low = mod["stance"].lower()
    assert "facilitator" in low and "never argue" in low


def test_debaters_carry_explicit_opposing_sides():
    s = {p["speaker_id"]: p["stance"].lower() for p in build_personas(TaskType.GD_TEST, "t")}
    assert "in favour" in s["gd_a"]
    assert "against" in s["gd_b"]
    assert "middle ground" in s["gd_c"]


def test_enriched_stance_reaches_persona_prompt():
    from app.services.simulation.blackboard import new_blackboard
    aarav = next(p for p in build_personas(TaskType.GD_TEST, "t")
                 if p["speaker_id"] == "gd_a")
    prompt = build_persona_prompt(aarav, "make your case", "(transcript)",
                                  new_blackboard("remote work")).lower()
    assert "in favour" in prompt and "data" in prompt
