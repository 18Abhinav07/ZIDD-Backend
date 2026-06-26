"""Wave 2.1 / 2.2 — interview assessment: no invented backstory, no prep-leak.

2.1 (P0): the interview examiner opened by FABRICATING the candidate's history
("your previous experience where you mentioned improving team efficiency") and
anchored the whole assessment on that phantom. The interview-test opening now
forbids invented history and makes the examiner elicit a real example first.

2.2 (D3, P1): the top logged weakness was folded into sim_topic as "Probe the
learner's known weakness: X", which became the blackboard topic the persona
prompt recites — leaking a prep instruction into the interviewer's spoken
subject for a returning learner. Weakness pressing rides probe_items (the
director, "do not read aloud") instead; sim_topic is now a neutral subject line.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import build_opening_prompt  # noqa: E402
from app.content.registry import get_node  # noqa: E402
from app.services.session_service import _seed_sim_topic  # noqa: E402

_INT_NODE = "int_08_quantify_impact"
_GD_NODE = "gd_01_stake_position"
_WEAK = [{"last_raw": "kept saying I improved things without numbers", "skill_id": "quantify"}]


def test_interview_opening_forbids_invented_backstory():
    node = get_node(_INT_NODE)
    prompt = build_opening_prompt(node, [], interview_test=True)
    low = prompt.lower()
    assert "do not invent" in low and "their own experience" in low
    # It must NOT fall through to the generic 'remembered weak spot warm-up' opener.
    assert "10-second warm-up" not in low


def test_non_interview_opening_unchanged():
    node = get_node(_INT_NODE)
    prompt = build_opening_prompt(node, [], interview_test=False)
    assert "do not invent" not in prompt.lower()


def test_interview_sim_topic_has_no_weakness_leak():
    topic = _seed_sim_topic(_INT_NODE, _WEAK)
    assert "probe the learner" not in topic.lower()
    assert "without numbers" not in topic           # the raw weakness cue is gone
    assert topic == get_node(_INT_NODE).teach_focus  # neutral subject line only


def test_gd_sim_topic_is_still_a_concrete_motion():
    topic = _seed_sim_topic(_GD_NODE, _WEAK)
    assert topic and topic != get_node(_GD_NODE).teach_focus
    assert "probe the learner" not in topic.lower()
