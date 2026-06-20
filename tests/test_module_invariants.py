"""Phase 6 — cross-module structural invariants (regression lock).

Every content module is consumed by the same content-agnostic engine, so they
must all honour the same shape contract regardless of subject. These invariants
are what the engine and placement silently rely on; this file locks them so a
future content edit can't drift a module out of the contract unnoticed.

Contract under test, for EVERY registered module:
  - the difficulty curve is the `level` field: strictly ascending and contiguous
    1..N in declared order (the engine advances by list order, the UI shows the
    level number — a gap or repeat would mislabel a node),
  - prerequisites form a single chain: the first node has none, each later node
    requires exactly its immediate predecessor (placement/advance walk this),
  - every node resolves to a TaskType that has a BehaviorPack (content<->behavior
    alignment: no node can be served with no voice/stance), and the prep/test
    split only exists for modules that declare one,
  - CEFR coupling matches placement mode: grade-placed modules (school) carry NO
    CEFR on any node; CEFR-placed modules carry a known band on EVERY node so
    placement never silently falls back.

These are deliberately NOT asserting CEFR is globally monotonic: the
communication module resets CEFR at its text->voice boundary by design (a new
modality re-enters at a lower grammar band), so monotonicity holds on `level`,
not on `cefr`.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.ai.behaviors import behavior_for  # noqa: E402
from app.content import registry  # noqa: E402
from app.content.registry import CEFR_RANK, uses_grade_placement  # noqa: E402
from app.content.task_types import TaskType, task_type_of  # noqa: E402
from app.graph.answer_check import _norm  # noqa: E402

MODULES = registry.MODULES
MODULE_IDS = [m.id for m in MODULES]


@pytest.fixture(params=MODULES, ids=MODULE_IDS)
def module(request):
    return request.param


# ---------- difficulty curve: levels strictly ascending, contiguous 1..N ----------

def test_levels_are_contiguous_one_to_n(module):
    levels = [n.level for n in module.nodes]
    assert levels == list(range(1, len(module.nodes) + 1)), (
        f"{module.id} levels must be 1..N in order, got {levels}"
    )


# ---------- prerequisites form a single chain ----------

def test_prerequisites_form_single_chain(module):
    nodes = module.nodes
    assert nodes[0].prerequisites == [], (
        f"{module.id} first node must have no prerequisites"
    )
    for prev, node in zip(nodes, nodes[1:]):
        assert node.prerequisites == [prev.id], (
            f"{module.id}: {node.id} must require only {prev.id}"
        )


def test_every_prerequisite_resolves_within_module(module):
    own_ids = {n.id for n in module.nodes}
    for node in module.nodes:
        for pre in node.prerequisites:
            assert pre in own_ids, f"{module.id}: {node.id} prereq {pre} not in module"


# ---------- content <-> behavior-pack alignment ----------

def test_every_node_resolves_to_a_behavior_pack(module):
    # Both prep and test resolutions must land on a real pack; behavior_for is
    # total over TaskType, so a missing one raises rather than silently defaults.
    for node in module.nodes:
        for test_mode in (False, True):
            pack = behavior_for(task_type_of(node.id, test_mode=test_mode))
            assert pack.persona and pack.pedagogy, (
                f"{module.id}: {node.id} ({test_mode=}) has an empty behavior pack"
            )


def test_test_mode_split_only_for_modules_that_declare_one(module):
    # interview/group_discussion have a distinct TEST variant; the rest reuse the
    # prep pack so test_mode is a harmless no-op.
    prep = task_type_of(module.nodes[0].id, test_mode=False)
    test = task_type_of(module.nodes[0].id, test_mode=True)
    if module.id in ("interview", "group_discussion"):
        assert prep is not test, f"{module.id} must have a distinct TEST task type"
    else:
        assert prep is test, f"{module.id} must be single-mode (prep == test)"


# ---------- CEFR coupling matches placement mode ----------

def test_cefr_coupling_matches_placement_mode(module):
    if uses_grade_placement(module.id):
        for n in module.nodes:
            assert n.cefr == "", (
                f"{module.id} is grade-placed; {n.id} must carry no CEFR"
            )
    else:
        for n in module.nodes:
            assert n.cefr in CEFR_RANK, (
                f"{module.id} is CEFR-placed; {n.id} has unknown band {n.cefr!r}"
            )


# ---------- ids unique across the whole registry ----------

def test_node_ids_unique_across_all_modules():
    all_ids = [n.id for m in MODULES for n in m.nodes]
    assert len(all_ids) == len(set(all_ids)), "duplicate node id across modules"


# ---------- bridge-exercise data integrity (engine + grader contract) ----------
# Every served bridge exercise is graded deterministically against its answer_key
# and selected by its band; a missing key/band or an MCQ whose key collides with a
# distractor's text would mis-grade silently. These lock the data so a future
# content edit can't drift it out of the grader's contract unnoticed.

def test_every_bridge_exercise_has_a_key_and_band(module):
    for node in module.nodes:
        for bx in node.bridge_exercises:
            assert bx.answer_key and bx.answer_key.strip(), (
                f"{node.id}: a {bx.type} bridge exercise has an empty answer_key"
            )
            assert bx.band in {"foundational", "standard", "stretch"}, (
                f"{node.id}: bridge exercise band {bx.band!r} is not a known band"
            )


def test_mcq_key_is_an_option_and_not_a_substring_of_a_distractor(module):
    # Mirrors answer_check's MCQ grading: the key must be a real option, and must
    # NOT be a substring of any WRONG option (else typing that distractor would
    # false-match the key — the grader footgun the substring fallback exposed).
    for node in module.nodes:
        for bx in node.bridge_exercises:
            if bx.type != "multiple_choice":
                continue
            opts = bx.options or []
            assert opts, f"{node.id}: an MCQ bridge exercise has no options"
            nkey = _norm(bx.answer_key)
            norm_opts = [_norm(o) for o in opts]
            assert nkey in norm_opts, (
                f"{node.id}: MCQ answer_key {bx.answer_key!r} is not among its options"
            )
            for raw_opt, norm_opt in zip(opts, norm_opts):
                if norm_opt == nkey:
                    continue   # the correct option itself
                assert nkey not in norm_opt, (
                    f"{node.id}: MCQ answer_key {bx.answer_key!r} is a substring of "
                    f"distractor {raw_opt!r} — typing it would false-match the key"
                )
