"""Wave 2.4 / D4 — content schema rejects empty / malformed nodes at load time.

pydantic's shape check accepted empty required strings and a multiple_choice
whose answer_key was not among its options. These validators close that so a
broken item can never reach a learner, while every node in the shipped curriculum
still validates (asserted via the real registry load).
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from app.content.schema import BridgeExercise, Concept  # noqa: E402

_OK = dict(id="x", level=1, level_type="text", skill="s", teach_focus="t",
           success_criteria="c", bridge_focus="b", title="T")


def _ex(**over):
    base = dict(id="e", type="fill_blank", sentence="I ___ here.", hint="h",
                context="c", answer_key="am")
    base.update(over)
    return base


def test_fill_blank_without_gap_is_rejected():
    with pytest.raises(ValidationError):
        BridgeExercise(**_ex(sentence="no gap here"))


def test_fill_blank_empty_answer_key_is_rejected():
    with pytest.raises(ValidationError):
        BridgeExercise(**_ex(answer_key="  "))


def test_mc_answer_key_not_in_options_is_rejected():
    with pytest.raises(ValidationError):
        BridgeExercise(**_ex(type="multiple_choice", sentence="Pick one",
                             answer_key="z", options=["a", "b"]))


def test_mc_with_one_option_is_rejected():
    with pytest.raises(ValidationError):
        BridgeExercise(**_ex(type="multiple_choice", sentence="Pick one",
                             answer_key="a", options=["a"]))


def test_empty_required_field_is_rejected():
    with pytest.raises(ValidationError):
        BridgeExercise(**_ex(hint="   "))


def test_well_formed_exercises_pass():
    BridgeExercise(**_ex())  # fill_blank
    BridgeExercise(**_ex(type="multiple_choice", sentence="Pick", answer_key="a",
                         options=["a", "b"]))
    BridgeExercise(**_ex(type="spoken", sentence="Say it", answer_key="a model answer"))


def test_concept_empty_teach_focus_is_rejected():
    with pytest.raises(ValidationError):
        Concept(**{**_OK, "teach_focus": "   "})


def test_concept_valid_passes():
    Concept(**_OK)


def test_real_curriculum_still_loads():
    # If the validators rejected any shipped node, importing the registry (which
    # model_validates every data/*.json at import) would already have raised.
    from app.content.registry import COMM_ID, get_module
    assert len(get_module(COMM_ID).nodes) == 11
