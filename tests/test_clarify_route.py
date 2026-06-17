"""B11/B12 (Test-fix-01): english=False routes to 'clarify', not 'bridge'.

Defect: route_node sent a non-English / gibberish / empty answer (english=False)
down the score<0.4 path to 'bridge'. Bridge scaffolds the competency SKILL for a
present-but-shaky learner — wrong move for someone who didn't write competent
English at all. They need a warm "say that in English" nudge (clarify), not a
sub-step drill on a skill they never attempted in English.

english=True off-task still routes to 'redirect'; english=True low-score still
routes to 'bridge'. Only english=False changes.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.graph import route  # noqa: E402


def _state(english: bool, on_task: bool, score: float) -> dict:
    return {
        "last_eval_score": score,
        "current_mastery": 0.3,
        "last_diagnosis": {"english": english, "on_task": on_task},
        "bridge_attempts": 0,
        "strengthen_attempts": 0,
        "level_fails": 0,
        "attempts": 0,
    }


def test_non_english_routes_to_clarify():
    # gibberish / non-English: english=False, scored 0.0 by the rubric.
    assert route.route_node(_state(english=False, on_task=False, score=0.0)) == "clarify"


def test_non_english_does_not_route_to_bridge_even_at_low_score():
    assert route.route_node(_state(english=False, on_task=True, score=0.2)) == "clarify"


def test_english_offtask_still_redirects():
    assert route.route_node(_state(english=True, on_task=False, score=0.0)) == "redirect"


def test_english_low_score_still_bridges():
    assert route.route_node(_state(english=True, on_task=True, score=0.2)) == "bridge"
