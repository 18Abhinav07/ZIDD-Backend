"""Schema-core tests for the foundation ContentGroup taxonomy and the additive
Concept/BridgeExercise fields (role, exemplars, band).

These guard that:
  - real module JSON keeps validating with zero migration (new fields default),
  - the new BridgeExercise.band field behaves (explicit value vs None default),
  - Concept.role / Concept.exemplars round-trip explicit values,
  - the recursive ContentGroup model validates nested and flat.
"""
import json
from pathlib import Path

import pytest

from app.content.schema import BridgeExercise, Concept, ContentGroup, Module

# Mirror app/content/registry.py:_load_modules — JSON curricula live here and
# are mapped onto Module via model_validate / Module(**data).
DATA_DIR = Path(__file__).resolve().parents[1] / "app" / "content" / "data"


def _load_first_real_module() -> Module:
    """Glob the real content JSON and return the first file that parses as a
    Module (has a "nodes" key), validated through Module(**data)."""
    for json_file in sorted(DATA_DIR.glob("*.json")):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "nodes" in data:
            return Module(**data)
    pytest.skip("no real module JSON with 'nodes' found in app/content/data")


def test_real_module_validates_with_new_field_defaults():
    """(a) An existing real module JSON still validates as Module with zero
    migration, and the additive Concept/BridgeExercise fields default correctly
    when a JSON omits them.

    The defaults are proved against a synthetic minimal module rather than the
    first real module: Spec B Depth-2 authoring deliberately populates
    ``exemplars``/``band`` on the real comm/gd/interview modules, so asserting
    those stay empty would only re-assert that no content has been authored.
    The guarantee that matters is that a JSON which *omits* the fields still
    validates with the documented fallbacks."""
    module = _load_first_real_module()
    assert module.nodes, "expected the real module to have at least one node"

    minimal = Module(
        id="m_min",
        title="Minimal",
        description="omits every additive field",
        nodes=[
            {
                "id": "n1",
                "title": "Node one",
                "level": 1,
                "level_type": "text",
                "skill": "s",
                "teach_focus": "t",
                "success_criteria": "sc",
                "bridge_focus": "bf",
                "bridge_exercises": [
                    {
                        "id": "n1_bx1",
                        "type": "fill_blank",
                        "sentence": "I ___ home.",
                        "hint": "past of go",
                        "context": "narration",
                        "answer_key": "went",
                    }
                ],
            }
        ],
    )
    concept = minimal.nodes[0]
    assert concept.role == "core"
    assert concept.exemplars == []
    assert concept.bridge_exercises[0].band is None


def test_bridge_exercise_band_explicit_and_default():
    """(b) band='stretch' is kept; omitting band yields None."""
    with_band = BridgeExercise(
        id="bx_stretch",
        type="fill_blank",
        sentence="I ___ to the store.",
        hint="past tense of go",
        context="narration",
        answer_key="went",
        band="stretch",
    )
    assert with_band.band == "stretch"

    without_band = BridgeExercise(
        id="bx_plain",
        type="fill_blank",
        sentence="I ___ to the store.",
        hint="past tense of go",
        context="narration",
        answer_key="went",
    )
    assert without_band.band is None


def test_concept_role_and_exemplars_round_trip():
    """(c) Explicit role and exemplars survive construction."""
    concept = Concept(
        id="c_remediation",
        title="Remediation node",
        level=1,
        level_type="text",
        skill="recover a missed concept",
        teach_focus="targeted re-teach",
        success_criteria="learner produces the form correctly",
        bridge_focus="single scaffolded sentence",
        role="remediation",
        exemplars=["sample"],
    )
    assert concept.role == "remediation"
    assert concept.exemplars == ["sample"]


def test_content_group_recursion_validates():
    """(d) A parent ContentGroup with a nested child ContentGroup validates and
    the recursion preserves child fields and parent defaults."""
    child = ContentGroup(id="comm_group", title="Communication", modules=["comm"])
    parent = ContentGroup(id="root", title="Root", children=[child])
    assert parent.children[0].modules == ["comm"]
    assert parent.locked is False
    assert parent.unlock_rule is None
    assert parent.tests == []


def test_content_group_flat_defaults():
    """(e) A flat ContentGroup validates with all defaults."""
    group = ContentGroup(id="svc", title="Service")
    assert group.description == ""
    assert group.children == []
    assert group.modules == []
    assert group.locked is False
    assert group.unlock_rule is None
    assert group.tests == []
