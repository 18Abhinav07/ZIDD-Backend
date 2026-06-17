"""Phase 6 — school_english explicit grade -> chapter -> node hierarchy.

school_english is a primary-grade ladder (grades 2-5), placed by grade not CEFR
(Phase 0.3). The module must therefore expose its structure as an explicit
grade hierarchy and carry NO CEFR coupling — a Grade-2 child's progress is a
grade/chapter position, not a CEFR band.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content import registry  # noqa: E402

def grade_of(node_id: str) -> int:
    return int(node_id[1])

def school_grades() -> dict[int, list[str]]:
    mod = registry.get_module("school_english")
    grades = {}
    for node in mod.nodes:
        g = grade_of(node.id)
        grades.setdefault(g, []).append(node.id)
    return grades


# ---------- grade_of (pure) ----------

def test_grade_of_parses_prefix():
    assert grade_of("c2_alphabet_sounds") == 2
    assert grade_of("c3_action_words") == 3
    assert grade_of("c4_past_tense") == 4
    assert grade_of("c5_tenses_mix") == 5


# ---------- school_grades hierarchy ----------

def test_grades_ascending_and_grouped():
    grades = school_grades()
    assert list(grades.keys()) == [2, 3, 4, 5]


def test_four_nodes_per_grade():
    grades = school_grades()
    for g in (2, 3, 4, 5):
        assert len(grades[g]) == 4, f"grade {g} should have 4 nodes"


def test_grade_node_ids_match_module_order():
    mod = registry.get_module("school_english")
    flattened = [nid for g in (2, 3, 4, 5) for nid in school_grades()[g]]
    assert flattened == mod.order


def test_each_grade_block_is_contiguous():
    mod = registry.get_module("school_english")
    order_grades = [grade_of(nid) for nid in mod.order]
    assert order_grades == sorted(order_grades)


def test_grade_first_node_matches_registry_start():
    grades = school_grades()
    for g, start in registry.SCHOOL_GRADE_START.items():
        assert grades[g][0] == start


# ---------- prerequisite chain ----------

def test_prerequisites_form_single_chain():
    nodes = registry.get_module("school_english").nodes
    assert nodes[0].prerequisites == []
    for prev, node in zip(nodes, nodes[1:]):
        assert node.prerequisites == [prev.id]


# ---------- no CEFR coupling ----------

def test_no_school_node_has_cefr():
    for n in registry.get_module("school_english").nodes:
        assert n.cefr == "", f"{n.id} must not carry a CEFR band"


# ---------- picker surfaces grade, not CEFR, for school ----------

def test_picker_school_uses_grade_range_not_cefr():
    mods = {m["id"]: m for m in registry.list_modules()}
    school_card = mods["school_english"]
    assert school_card["grade_range"] == "2-5"
    assert school_card["cefr_range"] == ""


def test_picker_cefr_modules_keep_cefr_range():
    mods = {m["id"]: m for m in registry.list_modules()}
    assert mods["communication"]["cefr_range"]
    assert mods["communication"]["grade_range"] == ""

