"""Wave 4.2 — sim-mode UX: neutral assessor avatar + no cross-mode fake zeros.

(a) A TEST-mode assessment defers scoring to the closing report, so there is no
    per-turn score. The avatar must not read that absent score as a fail and show
    "concerned" for the whole session — it shows a neutral-engaged assessor.
(b) The scorer emits all five sub-scores and zeroes the inapplicable ones; the
    closing report must null the OTHER mode's sub-scores so the learner never sees
    a hard 0 on a metric their session never measured.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.api.routes import _state_snapshot  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services.session_service import _project_report_subscores  # noqa: E402


def test_test_mode_avatar_is_engaged_not_concerned():
    state = {
        "session_id": "s1",
        "competency_node": "int_08_quantify_impact",
        "current_mastery": 0.0,        # no per-skill EMA in assessment
        "turn_count": 3,
        "task_type": TaskType.INTERVIEW_TEST.value,
        "last_diagnosis": {},          # no eval ran -> would default to 'concerned'
    }
    snap = _state_snapshot(state)
    assert snap["avatar_emotion"] == "engaged"


def test_coaching_low_score_still_concerned():
    state = {
        "session_id": "s2",
        "competency_node": "comm_00_greetings",
        "current_mastery": 0.2,
        "turn_count": 1,
        "task_type": "communication",
        "last_eval_score": 0.2,
        "last_diagnosis": {"affect": "neutral", "on_task": True, "english": True},
    }
    assert _state_snapshot(state)["avatar_emotion"] == "concerned"


def _full_report():
    return {
        "score": 0.6, "summary": "ok", "strengths": [], "improvements": [],
        "participation_score": 0.0, "relevance_score": 0.0, "language_score": 0.7,
        "clarity_score": 0.8, "confidence_score": 0.7,
    }


def test_interview_report_nulls_gd_only_subscores():
    r = _project_report_subscores(_full_report(), TaskType.INTERVIEW_TEST.value)
    assert r["participation_score"] is None
    assert r["relevance_score"] is None
    assert r["language_score"] is None
    assert r["clarity_score"] == 0.8     # interview metric kept
    assert r["confidence_score"] == 0.7


def test_gd_report_nulls_interview_only_subscores():
    r = _project_report_subscores(_full_report(), TaskType.GD_TEST.value)
    assert r["clarity_score"] is None
    assert r["confidence_score"] is None
    assert r["participation_score"] == 0.0  # GD metric kept (a real measured 0)
    assert r["language_score"] == 0.7
