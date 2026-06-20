"""Interview voice variants: one Interviewer, a per-session tonal manner.

build_personas attaches a deterministic `style` to the interview persona (drawn
from the topic), and build_persona_prompt renders it into the speaking prompt.
GD personas carry no style, so their prompt is byte-for-byte unchanged.
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
from app.services.simulation_service import (  # noqa: E402
    _INTERVIEWER_STYLES,
    build_personas,
)

_BB = {"topic": "Remote work", "phase": "opening", "tension": 0.2}


def test_interviewer_gets_a_style_from_the_pool():
    roster = build_personas(TaskType.INTERVIEW_TEST, "Remote work")
    assert len(roster) == 1
    assert roster[0].get("style") in _INTERVIEWER_STYLES


def test_interviewer_style_is_deterministic_per_topic():
    a = build_personas(TaskType.INTERVIEW_TEST, "Climate policy")[0]["style"]
    b = build_personas(TaskType.INTERVIEW_TEST, "Climate policy")[0]["style"]
    assert a == b  # same topic -> same manner, stable on reload


def test_interviewer_style_varies_across_topics():
    # The selector spreads across the pool: distinct topics must land on more
    # than one manner (guards a constant/degenerate mapping).
    topics = [
        "Remote work", "Climate policy", "AI regulation", "Urban transit",
        "Space funding", "Gig economy", "Online privacy", "Tourism",
    ]
    styles = {build_personas(TaskType.INTERVIEW_TEST, t)[0]["style"] for t in topics}
    assert len(styles) >= 2


def test_persona_prompt_renders_the_style():
    persona = build_personas(TaskType.INTERVIEW_TEST, "Remote work")[0]
    prompt = build_persona_prompt(persona, "Press on their last claim.", "(t)", _BB)
    assert "manner this session is" in prompt
    assert persona["style"] in prompt


def test_gd_persona_prompt_has_no_style_line():
    # A GD debater carries no style, so the manner line never appears — the GD
    # prompt is untouched by the interview feature.
    gd_persona = {"speaker_id": "gd_a", "name": "Aarav", "stance": "strongly in favour"}
    prompt = build_persona_prompt(gd_persona, "Make your case.", "(t)", _BB)
    assert "manner this session is" not in prompt
