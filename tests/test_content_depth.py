"""Spec B Depth-2 authoring invariants (regression lock).

Depth-2 authoring means every node in the three authored modules
(communication, group_discussion, interview) ships at least two band-spanning
bridge exercises plus 1-2 exemplars, so the engine can serve structured
scaffolding without an on-the-fly LLM call. school_english is INTENTIONALLY
EXCLUDED — its grade-placed content is out of Depth-2 scope and must carry no
authored bridge exercises at all.

These are PURE tests: get_module reads the in-memory registry, so there is no
async, no I/O, no env vars. They guard, per node:
  - >= 2 bridge exercises, spanning >= 2 distinct bands,
  - every band/type is a known literal (band never None),
  - multiple_choice carries >= 3 unique options containing answer_key,
  - non-multiple_choice carries no options,
  - fill_blank has exactly one ``___`` blank,
  - required string fields are non-blank,
  - 1-2 exemplars.
Plus cross-cutting: exercise ids are globally unique, and school_english is
excluded.
"""
import pytest

from app.content.registry import get_module, get_node, next_node

AUTHORED_MODULES = ["communication", "group_discussion", "interview"]
VALID_BANDS = {"foundational", "standard", "stretch"}
VALID_TYPES = {"fill_blank", "multiple_choice", "spoken"}
REQUIRED_STR_FIELDS = ("id", "sentence", "hint", "context", "answer_key")
_BAND_RANK = {"foundational": 0, "standard": 1, "stretch": 2}


# ---------- per-node Depth-2 invariants ----------

@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_each_node_has_band_spanning_depth(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        where = f"{module_id}:{node.id}"
        exercises = node.bridge_exercises

        assert len(exercises) >= 2, (
            f"{where} must have >= 2 bridge exercises, got {len(exercises)}"
        )

        bands = {ex.band for ex in exercises}
        assert len(bands) >= 2, (
            f"{where} exercises must span >= 2 distinct bands, got {sorted(bands)}"
        )


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_each_exercise_band_is_known_and_set(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        for ex in node.bridge_exercises:
            where = f"{module_id}:{node.id}:{ex.id}"
            assert ex.band is not None, f"{where} band must not be None"
            assert ex.band in VALID_BANDS, (
                f"{where} band {ex.band!r} not in {sorted(VALID_BANDS)}"
            )


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_each_exercise_type_is_known(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        for ex in node.bridge_exercises:
            where = f"{module_id}:{node.id}:{ex.id}"
            assert ex.type in VALID_TYPES, (
                f"{where} type {ex.type!r} not in {sorted(VALID_TYPES)}"
            )


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_multiple_choice_options_well_formed(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        for ex in node.bridge_exercises:
            if ex.type != "multiple_choice":
                continue
            where = f"{module_id}:{node.id}:{ex.id}"
            assert ex.options, f"{where} multiple_choice must have options"
            assert len(ex.options) >= 3, (
                f"{where} multiple_choice needs >= 3 options, got {len(ex.options)}"
            )
            assert len(ex.options) == len(set(ex.options)), (
                f"{where} multiple_choice options must be unique, got {ex.options}"
            )
            assert ex.answer_key in ex.options, (
                f"{where} answer_key {ex.answer_key!r} not among options {ex.options}"
            )


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_non_multiple_choice_has_no_options(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        for ex in node.bridge_exercises:
            if ex.type == "multiple_choice":
                continue
            where = f"{module_id}:{node.id}:{ex.id}"
            assert not ex.options, (
                f"{where} non-multiple_choice must carry no options, got {ex.options}"
            )


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_fill_blank_has_exactly_one_blank(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        for ex in node.bridge_exercises:
            if ex.type != "fill_blank":
                continue
            where = f"{module_id}:{node.id}:{ex.id}"
            assert ex.sentence.count("___") == 1, (
                f"{where} fill_blank must have exactly one '___' blank, "
                f"got {ex.sentence.count('___')} in {ex.sentence!r}"
            )


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_node_bands_escalate_to_a_stretch_finish(module_id):
    """Bridge exercises must get HARDER down the list (never regress in band) and
    the last slot — the hardest — must be a 'stretch'. Guards two real authoring
    bugs: int_08 banded its MCQ 'stretch' and its spoken task 'standard' (inverted,
    so the severity-aware bridge selector handed a weaker learner the harder task);
    comm_08 ended a voice node on an easier recognition MCQ at 'standard' with no
    stretch at all (a difficulty regression in the final slot)."""
    module = get_module(module_id)
    for node in module.nodes:
        exercises = node.bridge_exercises
        if not exercises:
            continue
        where = f"{module_id}:{node.id}"
        ranks = [_BAND_RANK[ex.band] for ex in exercises]
        assert ranks == sorted(ranks), (
            f"{where} bands must not regress in difficulty, got "
            f"{[ex.band for ex in exercises]}"
        )
        assert exercises[-1].band == "stretch", (
            f"{where} last (hardest) exercise must be 'stretch', got "
            f"{exercises[-1].band!r}"
        )


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_fill_blank_hint_word_count_matches_answer_key(module_id):
    """When a fill_blank hint promises a 'two-word' (or one-word) answer, the
    answer_key must actually have that many words. comm_06 had a 'two-word linking
    phrase' hint over a single-word blank ('For'), because the second word
    ('example') was already printed after the ___ — a hint/blank arity mismatch
    that quietly fails a learner who writes the full phrase the hint asked for."""
    module = get_module(module_id)
    for node in module.nodes:
        for ex in node.bridge_exercises:
            if ex.type != "fill_blank":
                continue
            hint = ex.hint.lower()
            n_words = len(ex.answer_key.split())
            where = f"{module_id}:{node.id}:{ex.id}"
            if "two-word" in hint or "two word" in hint:
                assert n_words == 2, (
                    f"{where} hint promises two words but answer_key "
                    f"{ex.answer_key!r} has {n_words}"
                )
            if "one-word" in hint or "single word" in hint or "single-word" in hint:
                assert n_words == 1, (
                    f"{where} hint promises one word but answer_key "
                    f"{ex.answer_key!r} has {n_words}"
                )


# ---------- targeted content regressions (specific authored fixes) ----------

def test_comm_06_blank_captures_the_full_two_word_phrase():
    bx1 = get_node("comm_06_persuade").bridge_exercises[0]
    assert bx1.answer_key == "For example"
    assert "___ example" not in bx1.sentence   # the leftover printed word is gone
    assert bx1.sentence.count("___") == 1


def test_int_02_exemplar_is_not_a_run_on():
    # the two independent clauses are joined with ', and', not a comma-splice run-on
    exemplar = get_node("int_02_strength_with_evidence").exemplars[0]
    assert "onboarding docs, and support tickets" in exemplar


def test_int_12_exemplar_gap_is_not_a_comma_splice():
    # two independent clauses split into separate sentences, not joined by a comma
    # (was: '...nothing bad to say about the team, it just wasn't the direction...')
    exemplar = get_node("int_12_explain_a_gap").exemplars[1]
    assert "to say about the team. It just wasn't" in exemplar


def test_no_node_skill_demands_physical_pointing():
    """The app is a TEXT-only chat (TUTOR_PERSONA bans 'point to' / 'look at'), and a
    node's `skill` string can ride into prompts (e.g. the end-of-session summary
    builder). So no `skill` may instruct physical deixis the medium cannot support —
    c2_this_that read 'Point to near and far things...', which a text learner cannot do."""
    all_modules = AUTHORED_MODULES + ["school_english"]
    for module_id in all_modules:
        for node in get_module(module_id).nodes:
            skill = node.skill.lower()
            assert "point to" not in skill and "point at" not in skill, (
                f"{module_id}:{node.id} skill demands physical pointing in a "
                f"text-only medium: {node.skill!r}"
            )


def test_voice_node_criteria_are_text_observable():
    # comm_08/09 are voice nodes graded on a TEXT transcript (the LLM never hears
    # audio), so their success_criteria — which IS the grading rubric — must not
    # hinge on audio-only qualities ("steady pace", "no long freezes",
    # "recoverable hesitations") and must name transcript-checkable elements.
    sc8 = get_node("comm_08_voice_intro").success_criteria.lower()
    assert "no long freezes" not in sc8 and "steady pace" not in sc8
    assert "sentence" in sc8 and "name" in sc8 and "role" in sc8

    sc9 = get_node("comm_09_voice_convo").success_criteria.lower()
    assert "recoverable hesitations" not in sc9
    assert "three" in sc9 and "question" in sc9


def test_new_interview_nodes_exist_and_chain_off_the_close():
    # int_11 (salary negotiation) + int_12 (gap/departure) authored as the new
    # interview tail; the linear advance must walk into them off int_10.
    ids = [n.id for n in get_module("interview").nodes]
    assert ids[-2:] == ["int_11_salary_negotiation", "int_12_explain_a_gap"]
    assert next_node("int_10_close_strong") == "int_11_salary_negotiation"
    assert next_node("int_11_salary_negotiation") == "int_12_explain_a_gap"
    assert next_node("int_12_explain_a_gap") is None   # the module's new last level
    # the authored skill intent survives (not a placeholder)
    assert "salary" in get_node("int_11_salary_negotiation").skill.lower()
    assert get_node("int_12_explain_a_gap").cefr == "C1"


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_required_string_fields_non_blank(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        for ex in node.bridge_exercises:
            for field in REQUIRED_STR_FIELDS:
                value = getattr(ex, field)
                where = f"{module_id}:{node.id}:{ex.id}"
                assert value.strip(), f"{where} field {field!r} must be non-blank"


@pytest.mark.parametrize("module_id", AUTHORED_MODULES)
def test_each_node_has_one_or_two_exemplars(module_id):
    module = get_module(module_id)
    for node in module.nodes:
        where = f"{module_id}:{node.id}"
        assert 1 <= len(node.exemplars) <= 2, (
            f"{where} must have 1-2 exemplars, got {len(node.exemplars)}"
        )


# ---------- cross-cutting / module-spanning invariants ----------

def test_exercise_ids_globally_unique():
    all_ids = [
        ex.id
        for module_id in AUTHORED_MODULES
        for node in get_module(module_id).nodes
        for ex in node.bridge_exercises
    ]
    # Soft floor: emptied content would collapse the id pool and is a regression
    # even though the uniqueness check below would still pass on an empty set.
    assert len(all_ids) >= 60, (
        f"expected a meaningful pool of bridge exercises, got {len(all_ids)}"
    )
    assert len(all_ids) == len(set(all_ids)), "duplicate bridge_exercise id across modules"


def test_school_english_excluded_from_depth():
    module = get_module("school_english")
    total = sum(len(n.bridge_exercises) for n in module.nodes)
    assert total == 0, (
        f"school_english is grade-placed and out of Depth-2 scope; "
        f"it must carry zero bridge exercises, got {total}"
    )
