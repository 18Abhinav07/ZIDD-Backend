from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import Mount

from app.content.school.content_schema import SchoolRubricEvaluation
from app.main import app
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_placement as placement
from app.services.school.authority import (
    CANONICAL_SCHOOL_AUTHORITY,
    DISABLED_SCHOOL_AUTHORITY,
    RETIRED_SCHOOL_ENDPOINT_SPECS,
    SCHOOL_ROUTE_OWNER_ATTRIBUTE,
    validate_canonical_school_routes,
)
from app.services.school.language_confidence import (
    LANGUAGE_CONFIDENCE_ALPHA,
    LanguageConfidenceState,
    apply_curriculum_language_signal,
    apply_language_signal,
    load_language_confidence,
    persist_language_confidence,
)
from app.services.school_core.readiness import AttemptEvidence
from app.content.school.source_map_compat import (
    PHASE_2_REMOVAL_BOUNDARY,
    legacy_flat_module_mapping,
    load_beta_source_map,
)
from scripts.audit_school_runtime_authority import (
    DEFAULT_RUNTIME_ALLOWLIST,
    audit_school_runtime_authority,
)


ROOT = Path(__file__).resolve().parents[2]
FORBIDDEN_PUBLIC_KEYS = {
    "accepted_answers",
    "answer_key",
    "answer_rule",
    "hidden_rubric",
    "model_answer",
    "pass_score",
    "rubric_criteria",
    "scoring_threshold",
}

EXPECTED_STATE = {
    "available": True,
    "profile_status": "unauthenticated",
    "target_class_no": None,
    "subject_id": None,
    "profile_version_id": None,
    "preferred_teaching_language": None,
    "coach_avatar_id": None,
    "coach_palette_id": None,
    "active_flow": "none",
    "active_session_id": None,
    "placement_status": "not_started",
    "unlock_state": "locked",
    "evaluated_class_no": None,
    "active_learning_class_no": None,
    "status": "needs_action",
    "next_action": "sign_in",
    "next_action_url": "/auth/login",
    "allowed_next_actions": ["sign_in"],
    "learner_message": "Sign in to continue your saved school path.",
    "parent_message": "School progress is available after sign-in.",
    "blocked_reason": None,
}
EXPECTED_CATALOG = {
    "boards": [
        {
            "board_id": "cbse",
            "title": "CBSE",
            "description": "CBSE curriculum aligned with approved learning material.",
            "support_status": "available",
            "subjects": [
                {
                    "subject_id": "english",
                    "title": "English",
                    "support_status": "available",
                    "classes": [
                        {
                            "class_no": class_no,
                            "title": f"Class {class_no}",
                            "support_status": "available",
                        }
                        for class_no in (2, 3, 4, 5)
                    ],
                }
            ],
        },
        {
            "board_id": "ncert",
            "title": "NCERT",
            "description": "NCERT is used as a content source for the CBSE release.",
            "support_status": "unavailable",
            "unavailable_reason": "NCERT is a content source, not a school board.",
            "subjects": [
                {
                    "subject_id": "english",
                    "title": "English",
                    "support_status": "unavailable",
                    "unavailable_reason": (
                        "Choose CBSE to use the available English release."
                    ),
                    "classes": [
                        {
                            "class_no": class_no,
                            "title": f"Class {class_no}",
                            "support_status": "unavailable",
                            "unavailable_reason": (
                                "NCERT is not a selectable school board."
                            ),
                        }
                        for class_no in (2, 3, 4, 5)
                    ],
                }
            ],
        },
    ],
}


def _fake_release_closure(monkeypatch, tmp_path: Path, chapter_count: int):
    from app.content.school import source_map_compat
    from app.content import school_rebuild_content
    from app.services.school import availability

    chapter_ids_by_class: dict[int, list[str]] = {class_no: [] for class_no in range(2, 6)}
    chapters = {}
    remaining = chapter_count
    for class_no in range(2, 6):
        class_count = min(12, remaining)
        remaining -= class_count
        class_dir = tmp_path / "english" / f"class_{class_no}"
        class_dir.mkdir(parents=True)
        for chapter_no in range(1, class_count + 1):
            chapter_id = f"eng_c{class_no}_ch{chapter_no:02d}"
            chapter_ids_by_class[class_no].append(chapter_id)
            path = class_dir / f"{chapter_id}.json"
            path.write_text("{}", encoding="utf-8")
            chapters[chapter_id] = SimpleNamespace(
                chapter_id=chapter_id,
                runtime_sha256=hashlib.sha256(chapter_id.encode("ascii")).hexdigest(),
                approval_status="human_approved",
                reviewed_by="reviewer@example.com",
                reviewed_at="2026-07-14T00:00:00Z",
                review_evidence=["manual pedagogy review", "assessment review"],
            )
    assert remaining == 0

    monkeypatch.setattr(school_rebuild_content, "LIVE_CHAPTER_ROOT", tmp_path)
    monkeypatch.setattr(
        school_rebuild_content,
        "load_live_chapter_file",
        lambda path: chapters[path.stem],
    )
    monkeypatch.setattr(
        source_map_compat,
        "load_beta_source_map",
        lambda _subject_id, class_no: {
            "chapters": [
                {"chapter_id": chapter_id}
                for chapter_id in chapter_ids_by_class[class_no]
            ]
        },
    )
    settings = SimpleNamespace(
        school_enabled=True,
        app_env="production",
        school_release_attestation_sha256="",
    )
    monkeypatch.setattr(availability, "get_settings", lambda: settings)
    return availability, settings, chapters
EXPECTED_PLACEMENT_ITEM = {
    "item_id": "spv_c03_t04_v01",
    "stage": "snapshot",
    "type": "multiple_choice",
    "source_class_no": 2,
    "target_class_no": 3,
    "learner_skill_label": "Use context to understand a word",
    "instruction": "English sentence ke clues se word chuno ya likho.",
    "support": "Blank ya diye gaye word ke aas-paas ke words padho.",
    "prompt": "What does tiny mean?",
    "passage": "The tiny seed was small enough to rest on one finger.",
    "options": ["small", "heavy", "angry"],
}
EXPECTED_PLACEMENT_RESPONSE_SHA256 = (
    "ccde9e8abb2d3041c302eb5c3af8e9a66525f4637814ef9fc5bf186048445d8a"
)
EXPECTED_CURRICULUM_RESPONSE_SHA256 = (
    "e064ab5ab34e9133ad647e6f77863a5bdf6efb6ca95ad3360e86d194ece4f480"
)


def _serialized(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def _sha256(payload: object) -> str:
    return hashlib.sha256(_serialized(payload).encode("utf-8")).hexdigest()


def _walk_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | {
            key
            for child in value.values()
            for key in _walk_keys(child)
        }
    if isinstance(value, list):
        return {key for child in value for key in _walk_keys(child)}
    return set()


def _fixture_profile() -> dict:
    return {
        "profile_version_id": "profile-fixture",
        "subject_ids": ["english"],
        "target_class_no": 3,
        "preferred_teaching_language": "hi_en",
        "prior_difficulty_signals": ["vocabulary"],
    }


def test_app_mounts_one_complete_canonical_school_authority():
    school_routes = [
        route
        for route in app.routes
        if str(getattr(route, "path", "")).startswith("/school")
    ]
    registrations = [
        (method, route.path, route.endpoint.__name__)
        for route in school_routes
        for method in sorted(route.methods or ())
        if method not in {"HEAD", "OPTIONS"}
    ]

    expected_route_count = 26 + len(RETIRED_SCHOOL_ENDPOINT_SPECS)
    assert len(CANONICAL_SCHOOL_AUTHORITY) == expected_route_count
    assert len(registrations) == expected_route_count
    assert registrations.count(("GET", "/school/state", "school_state")) == 1
    assert registrations.count(
        ("GET", "/school/support/{session_id}", "get_school_support")
    ) == 1
    assert len(registrations) == len(set(registrations))
    retired_names = {name for _method, _path, name in RETIRED_SCHOOL_ENDPOINT_SPECS}
    assert all(
        endpoint_name in retired_names
        for _method, path, endpoint_name in registrations
        if path.startswith(("/school/v2", "/school/v3"))
    )
    assert all(
        getattr(route.endpoint, SCHOOL_ROUTE_OWNER_ATTRIBUTE, None)
        for route in school_routes
    )
    validate_canonical_school_routes(app.routes)

    main_tree = ast.parse((ROOT / "app/main.py").read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in ast.walk(main_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    assert "app.api.school_rebuild_routes" in imports
    assert "app.api.school_routes" not in imports


def test_disabled_school_authority_mounts_only_state_and_retirements():
    from app.api.school_availability_routes import router as availability_router
    from app.api.school_retirement_routes import router as retirement_router

    disabled_app = FastAPI()
    disabled_app.include_router(availability_router)
    disabled_app.include_router(retirement_router)

    validate_canonical_school_routes(disabled_app.routes, school_enabled=False)
    registrations = {
        (method, route.path)
        for route in disabled_app.routes
        for method in (route.methods or ())
        if str(route.path).startswith("/school") and method not in {"HEAD", "OPTIONS"}
    }
    assert len(registrations) == len(DISABLED_SCHOOL_AUTHORITY)
    assert ("GET", "/school/state") in registrations
    assert ("GET", "/school/catalog") not in registrations


def test_production_release_closure_requires_exactly_47_chapters(
    monkeypatch,
    tmp_path,
):
    availability, settings, _chapters = _fake_release_closure(
        monkeypatch,
        tmp_path,
        42,
    )
    first = availability._release_closure()
    settings.school_release_attestation_sha256 = first.release_digest

    result = availability._release_closure()

    assert result.available is False
    assert result.reason == "school_release_chapter_closure_incomplete"
    assert result.expected_chapters == 42
    assert result.authored_chapters == 42
    assert result.human_approved_chapters == 42


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("reviewed_by", "different-reviewer@example.com"),
        ("reviewed_at", "2026-07-14T01:00:00Z"),
        ("review_evidence", ["different signed review evidence"]),
    ],
)
def test_release_attestation_binds_human_approval_evidence(
    monkeypatch,
    tmp_path,
    field,
    replacement,
):
    availability, settings, chapters = _fake_release_closure(
        monkeypatch,
        tmp_path,
        47,
    )
    first = availability._release_closure()
    settings.school_release_attestation_sha256 = first.release_digest
    assert availability._release_closure().available is True

    setattr(chapters["eng_c2_ch01"], field, replacement)
    changed = availability._release_closure()

    assert changed.available is False
    assert changed.reason == "school_release_attestation_mismatch"
    assert changed.release_digest != settings.school_release_attestation_sha256


def test_production_school_closure_failure_keeps_career_bootable():
    script = """
import sys
from app.services.school import availability

def unreadable_release():
    raise PermissionError("release corpus unreadable")

availability._release_closure = unreadable_release
import app.main

paths = {getattr(route, "path", "") for route in app.main.app.routes}
assert "/session/start" in paths
assert "/school/state" in paths
assert "/school/catalog" not in paths
assert "app.api.school_rebuild_routes" not in sys.modules
"""
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "production",
            "SCHOOL_ENABLED": "true",
            "SCHOOL_RELEASE_ATTESTATION_SHA256": "0" * 64,
        }
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_route_authority_validation_rejects_duplicate_and_missing_registration():
    school_routes = [
        route
        for route in app.routes
        if str(getattr(route, "path", "")).startswith("/school")
    ]
    with pytest.raises(ValueError, match="duplicate_canonical_school_route"):
        validate_canonical_school_routes([*school_routes, school_routes[0]])
    with pytest.raises(ValueError, match="canonical_school_route_mismatch"):
        validate_canonical_school_routes(school_routes[1:])


def test_route_authority_rejects_methodless_school_mount():
    mounted_v3 = Mount("/school/v3", app=FastAPI())

    with pytest.raises(ValueError, match="canonical_school_non_http_route"):
        validate_canonical_school_routes([*app.routes, mounted_v3])


def test_route_authority_rejects_school_route_hidden_below_root_mount():
    hidden_app = FastAPI()

    @hidden_app.get("/school/v3/legacy")
    async def hidden_legacy_school_route():
        return {"status": "legacy"}

    root_mount = Mount("/", app=hidden_app)

    with pytest.raises(ValueError, match="canonical_school_route_mismatch"):
        validate_canonical_school_routes([*app.routes, root_mount])


def test_route_authority_allows_unrelated_nested_mounts():
    unrelated_app = FastAPI()

    @unrelated_app.get("/health")
    async def unrelated_health_route():
        return {"status": "ok"}

    unrelated_mount = Mount("/internal", app=unrelated_app)

    validate_canonical_school_routes([*app.routes, unrelated_mount])


def test_route_authority_rejects_duplicate_method_path_with_another_handler():
    school_route = next(route for route in app.routes if route.path == "/school/state")

    def another_state_handler():
        return None

    setattr(
        another_state_handler,
        SCHOOL_ROUTE_OWNER_ATTRIBUTE,
        getattr(school_route.endpoint, SCHOOL_ROUTE_OWNER_ATTRIBUTE),
    )
    duplicate = SimpleNamespace(
        path=school_route.path,
        methods=set(school_route.methods),
        endpoint=another_state_handler,
    )

    with pytest.raises(ValueError, match="duplicate_canonical_school_route"):
        validate_canonical_school_routes([*app.routes, duplicate])


@pytest.mark.parametrize("owner", (None, "app.services.school_rebuild_curriculum"))
def test_route_authority_rejects_missing_or_wrong_owner(owner):
    routes = list(app.routes)
    state_route = next(route for route in routes if route.path == "/school/state")

    def copied_state_handler():
        return None

    copied_state_handler.__name__ = "school_state"
    if owner is not None:
        setattr(copied_state_handler, SCHOOL_ROUTE_OWNER_ATTRIBUTE, owner)
    replacement = SimpleNamespace(
        path=state_route.path,
        methods=set(state_route.methods),
        endpoint=copied_state_handler,
    )
    routes[routes.index(state_route)] = replacement

    with pytest.raises(ValueError, match="canonical_school_route_owner_mismatch"):
        validate_canonical_school_routes(routes)


def test_route_authority_rejects_unimportable_registry_owner(monkeypatch):
    from app.services.school import authority

    monkeypatch.setattr(
        authority,
        "CANONICAL_SCHOOL_AUTHORITY",
        (
            replace(
                CANONICAL_SCHOOL_AUTHORITY[0],
                owning_service="app.services.school.does_not_exist",
            ),
            *CANONICAL_SCHOOL_AUTHORITY[1:],
        ),
    )

    with pytest.raises(ValueError, match="canonical_school_owner_import_error"):
        authority.validate_canonical_school_routes(app.routes)


def test_runtime_import_audit_is_reachability_aware_and_narrowly_allowlisted():
    report = audit_school_runtime_authority(ROOT)
    school_report = audit_school_runtime_authority(
        ROOT,
        entry_modules=("app.api.school_rebuild_routes",),
        allowlist=(),
    )

    assert report.violations == ()
    assert report.allowlisted == ()
    assert DEFAULT_RUNTIME_ALLOWLIST == ()
    assert not {
        "app.ai.calls",
        "app.ai.prompts",
        "app.content.task_types",
        "app.content.curriculum",
    }.intersection(school_report.reachable_modules)

    calls_source = (ROOT / "app/ai/calls.py").read_text(encoding="utf-8")
    assert (
        "from app.services.school.open_answer_ai import evaluate_school_open_answer"
        in calls_source
    )
    assert "school_v3_schema" not in calls_source


def test_canonical_router_uses_isolated_school_ai_boundary():
    from app.api import school_rebuild_routes
    from app.services.school import open_answer_ai

    assert school_rebuild_routes.evaluate_school_open_answer is open_answer_ai.evaluate_school_open_answer
    route_source = (ROOT / "app/api/school_rebuild_routes.py").read_text(
        encoding="utf-8"
    )
    boundary_source = (ROOT / "app/services/school/open_answer_ai.py").read_text(
        encoding="utf-8"
    )
    assert "app.ai.calls" not in route_source
    assert "app.ai.prompts" not in boundary_source
    assert "app.content.task_types" not in boundary_source


def test_canonical_school_prompt_is_exactly_compatible_with_current_prompt():
    from app.ai.prompts import build_school_open_answer_prompt as legacy_builder
    from app.services.school.open_answer_ai import (
        build_school_open_answer_prompt as provider_builder,
    )
    from app.services.school.open_answer_prompt import build_school_open_answer_prompt

    kwargs = {
        "item_id": "open-1",
        "skill_ids": ["writing.reason_answer"],
        "task_prompt": "Why did the learner share?",
        "passage": "The learner shared a book with a friend.",
        "learner_answer": "Because the friend needed it.",
        "rubric_criteria": [
            {
                "id": "answers_question",
                "description": "Answers the question directly.",
                "required": True,
            }
        ],
    }

    assert legacy_builder is build_school_open_answer_prompt
    assert provider_builder is build_school_open_answer_prompt
    assert build_school_open_answer_prompt(**kwargs) == legacy_builder(**kwargs)


def test_shared_registry_keeps_career_modules_without_legacy_chapter_registration():
    from app.content import registry

    registry_source = (ROOT / "app/content/registry.py").read_text(encoding="utf-8")
    assert "from app.content import curriculum" not in registry_source
    assert [module.id for module in registry.MODULES] == [
        "communication",
        "interview",
        "group_discussion",
        "school_english",
    ]
    assert registry.module_of("int_01_elevator_pitch") == "interview"
    assert registry.module_of("gd_01_stake_position") == "group_discussion"
    assert registry.module_of("comm_00_greetings") == "communication"


@pytest.mark.parametrize(
    "forbidden_import",
    (
        "app.services.school_v2_learning",
        "app.services.school_v3_runtime",
        "app.content.data.school.runtime_loader",
        "scripts.generate_school_v3_seed_content",
    ),
)
def test_runtime_import_audit_rejects_reachable_forbidden_imports(
    tmp_path: Path,
    forbidden_import: str,
):
    app_root = tmp_path / "app"
    app_root.mkdir()
    (app_root / "__init__.py").write_text("", encoding="utf-8")
    (app_root / "main.py").write_text(
        f"import {forbidden_import}\n",
        encoding="utf-8",
    )

    report = audit_school_runtime_authority(
        tmp_path,
        entry_modules=("app.main",),
        allowlist=(),
    )

    assert len(report.violations) == 1
    assert report.violations[0].target == forbidden_import


def test_runtime_import_audit_resolves_relative_imports_from_package_init(
    tmp_path: Path,
):
    app_root = tmp_path / "app"
    package_root = app_root / "pkg"
    package_root.mkdir(parents=True)
    (app_root / "__init__.py").write_text("", encoding="utf-8")
    (app_root / "main.py").write_text("import app.pkg\n", encoding="utf-8")
    (package_root / "__init__.py").write_text(
        "from . import adapter\n",
        encoding="utf-8",
    )
    (package_root / "adapter.py").write_text(
        "import app.services.school_v3_runtime\n",
        encoding="utf-8",
    )

    report = audit_school_runtime_authority(
        tmp_path,
        entry_modules=("app.main",),
        allowlist=(),
    )

    assert len(report.violations) == 1
    assert report.violations[0].source_module == "app.pkg.adapter"
    assert report.violations[0].target == "app.services.school_v3_runtime"


def test_flat_source_map_projection_is_manifest_cross_validated_and_phase_bounded():
    class_two = load_beta_source_map("english", 2)
    class_three = load_beta_source_map("english", 3)
    class_four = load_beta_source_map("english", 4)
    class_five = load_beta_source_map("english", 5)

    assert "Phase 2" in PHASE_2_REMOVAL_BOUNDARY
    assert [len(value["chapters"]) for value in (class_two, class_three, class_four, class_five)] == [13, 12, 12, 10]
    assert class_two["chapters"][1]["chapter_title"] == "Picture Reading"
    assert class_three["chapters"][7]["chapter_title"] == "Thank God!"
    assert class_four["chapters"][2]["chapter_title"] == "Be Smart, Be Safe"
    assert class_four["chapters"][6]["chapter_title"] == "Fit Body, Fit Mind, Fit Nation"
    assert all(
        "Self Assessment" not in chapter["chapter_title"]
        and "Self-assessment" not in chapter["chapter_title"]
        for source_map in (class_three, class_four, class_five)
        for chapter in source_map["chapters"]
    )

    mapping = legacy_flat_module_mapping("english", 3)
    assert mapping["eng_c3_ch01"] == "eng_c3_u01_m02"
    assert mapping["eng_c3_ch08"] == "eng_c3_u03_m03"
    assert list(mapping) == [f"eng_c3_ch{index:02d}" for index in range(1, 13)]

    from app.content.school.release_loader import load_release_manifest

    manifest = load_release_manifest()
    display_titles = {
        module.module_id: module.phase_0_public_display_title
        for release in manifest.releases
        for unit in release.units
        for module in unit.modules
        if module.phase_0_public_display_title is not None
    }
    assert display_titles == {
        "eng_c3_u03_m03": "Thank God!",
        "eng_c4_u01_m03": "Be Smart, Be Safe",
        "eng_c4_u03_m01": "Fit Body, Fit Mind, Fit Nation",
    }


def test_flat_source_map_projection_rejects_beta_title_or_order_drift(
    tmp_path: Path,
    monkeypatch,
):
    from app.content.school import source_map_compat

    source_root = tmp_path / "english"
    source_root.mkdir()
    original = ROOT / "app/content/ncert_source_map/english/class_3.json"
    payload = json.loads(original.read_text(encoding="utf-8"))
    payload["chapters"][7]["chapter_title"] = "  THANK   GOD  "
    (source_root / "class_3.json").write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(source_map_compat, "LEGACY_SOURCE_MAP_ROOT", tmp_path)
    source_map_compat.load_beta_source_map.cache_clear()

    projected = source_map_compat.load_beta_source_map("english", 3)
    assert projected["chapters"][7]["chapter_title"] == "Thank God!"

    payload["chapters"][7]["chapter_title"] = "A Different Lesson"
    (source_root / "class_3.json").write_text(json.dumps(payload), encoding="utf-8")
    source_map_compat.load_beta_source_map.cache_clear()
    with pytest.raises(ValueError, match="legacy_source_title_mismatch"):
        source_map_compat.load_beta_source_map("english", 3)

    source_map_compat.load_beta_source_map.cache_clear()


def test_source_map_compat_has_one_normalization_policy_and_no_title_map():
    from app.content.school import source_map_compat

    source = (ROOT / "app/content/school/source_map_compat.py").read_text(
        encoding="utf-8"
    )
    assert "_BETA_TITLE_PROJECTION" not in source
    assert source_map_compat.normalize_compat_title(" Thank God! ") == "thank god"
    assert source_map_compat.normalize_compat_title("Be Smart, Be Safe") == "be smart be safe"
    assert (
        source_map_compat.normalize_compat_title("Fit Body, Fit Mind, Fit Nation")
        == "fit body fit mind fit nation"
    )


def test_curriculum_source_projection_failure_is_not_fabricated(monkeypatch):
    monkeypatch.setattr(
        curriculum,
        "load_beta_source_map",
        lambda _subject_id, _class_no: (_ for _ in ()).throw(
            LookupError("missing canonical projection")
        ),
    )

    with pytest.raises(LookupError, match="missing canonical projection"):
        curriculum._source_map("english", 3)


@pytest.mark.parametrize(
    "evidence",
    (
        AttemptEvidence(
            attempt_type="guided",
            evaluator_score=1.0,
            evaluator_confidence=1.0,
            skill_ids=("writing.reason_answer",),
            support_level="guided",
            language_detected="hi",
        ),
        AttemptEvidence(
            attempt_type="independent_check",
            evaluator_score=1.0,
            evaluator_confidence=0.0,
            skill_ids=("writing.reason_answer",),
            support_level="independent",
            language_required="en",
            language_detected="en",
        ),
        AttemptEvidence(
            attempt_type="independent_check",
            evaluator_score=1.0,
            evaluator_confidence=1.0,
            skill_ids=("writing.reason_answer",),
            support_level="independent",
            language_required="en",
            language_detected="en",
            blockers=("needs_human_review",),
        ),
    ),
)
def test_language_confidence_rejects_non_english_or_untrusted_positive_evidence(
    evidence,
):
    state = LanguageConfidenceState(
        user_id="learner",
        en_production_confidence=0.5,
        total_signals=3,
    )

    updated = apply_language_signal(state, evidence)

    assert updated.en_production_confidence <= state.en_production_confidence
    assert updated.total_signals == 4


def test_language_confidence_weights_positive_signal_by_evaluator_confidence():
    state = LanguageConfidenceState(user_id="learner", en_production_confidence=0.2)

    high = apply_language_signal(
        state,
        AttemptEvidence(
            attempt_type="independent_check",
            evaluator_score=1.0,
            evaluator_confidence=1.0,
            skill_ids=("writing.reason_answer",),
            support_level="independent",
            language_required="en",
            language_detected="en",
        ),
    )
    low = apply_language_signal(
        state,
        AttemptEvidence(
            attempt_type="independent_check",
            evaluator_score=1.0,
            evaluator_confidence=0.25,
            skill_ids=("writing.reason_answer",),
            support_level="independent",
            language_required="en",
            language_detected="en",
        ),
    )

    assert high.en_production_confidence > low.en_production_confidence


def test_current_public_state_catalog_and_placement_json_are_unchanged(monkeypatch):
    monkeypatch.delenv("ZIDD_ALLOW_TEST_AUTH", raising=False)
    state_response = TestClient(app).get("/school/state")
    assert state_response.status_code == 200
    assert state_response.json() == EXPECTED_STATE
    assert _sha256(state_response.json()) == "d6a9fca4e9676e8fd26b931dfddc7638aee8533e8d2234a7a7ea19f96d14c443"

    from app.services.school_rebuild_profile import public_school_catalog

    catalog = public_school_catalog()
    assert catalog == EXPECTED_CATALOG

    envelope = placement.new_placement_envelope(_fixture_profile())
    response = placement.placement_response(
        session_id="placement-fixture",
        envelope=envelope,
    )
    assert response["next_item"] == EXPECTED_PLACEMENT_ITEM
    assert _sha256(response) == EXPECTED_PLACEMENT_RESPONSE_SHA256
    assert not (_walk_keys(response) & FORBIDDEN_PUBLIC_KEYS)


def test_current_curriculum_and_language_confidence_json_are_exact():
    profile = _fixture_profile()
    state = curriculum.new_curriculum_state(
        school_profile=profile,
        placement_report={"report_id": "report-fixture"},
        recap_session=None,
        en_production_confidence=0.36,
        language_signal_count=4,
    )
    response = curriculum.public_curriculum_response(
        {
            "session_id": "curriculum-fixture",
            "status": "active",
            "subject_id": "english",
            "class_no": 3,
            "profile_version_id": "profile-fixture",
            "state_json": state,
        }
    )

    assert _sha256(response) == EXPECTED_CURRICULUM_RESPONSE_SHA256
    assert response["current_activity"]["teaching_block"].startswith(
        "Kyun ka jawab seedha na mile"
    )
    assert not (_walk_keys(response) & FORBIDDEN_PUBLIC_KEYS)

    assert LANGUAGE_CONFIDENCE_ALPHA == 0.20
    confidence = apply_curriculum_language_signal(
        LanguageConfidenceState(
            user_id="learner",
            en_production_confidence=0.5,
            total_signals=7,
        ),
        {
            "kind": "independent_check",
            "score": 1.0,
            "confidence": 0.9,
            "skill_ids": ["writing.reason_answer"],
            "language_detected": "en",
            "blockers": [],
            "hint_count": 0,
        },
    )
    public_confidence = {
        "en_production_confidence": confidence.en_production_confidence,
        "total_signals": confidence.total_signals,
    }
    assert public_confidence == {
        "en_production_confidence": 0.58,
        "total_signals": 8,
    }
    assert _sha256(public_confidence) == "9df1531a0e83de678eb1bde3051d7e97ece39bd9aa2d387df579152bdc853d09"


@pytest.mark.asyncio
async def test_canonical_language_confidence_preserves_store_defaults_and_round_trip(store):
    assert await load_language_confidence(store, "new-learner") == LanguageConfidenceState(
        user_id="new-learner"
    )
    expected = LanguageConfidenceState(
        user_id="learner",
        en_production_confidence=0.64,
        total_signals=7,
    )
    await persist_language_confidence(store, expected)
    assert await load_language_confidence(store, "learner") == expected

    source = (ROOT / "app/services/school/language_confidence.py").read_text(
        encoding="utf-8"
    )
    assert "school_v3" not in source


def test_canonical_rubric_dto_keeps_public_lists_and_scoring_shape():
    activity = {
        "activity_id": "open-1",
        "evaluation_mode": "llm_rubric",
        "skill_ids": ["writing.reason_answer"],
        "pass_score": 0.75,
        "rubric_criteria": [
            {
                "id": "answers_question",
                "required": True,
                "min_quality": 0.7,
            }
        ],
    }
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": "school-v3-rubric-1",
            "item_id": "open-1",
            "skill_ids": ["writing.reason_answer"],
            "score": 0.8,
            "confidence": 0.9,
            "language_detected": "en",
            "criteria": [
                {
                    "id": "answers_question",
                    "met": True,
                    "quality": 0.8,
                    "evidence_quote": "because it helped",
                }
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "Good reason.",
        }
    )

    result = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer="because it helped",
    )

    assert result == {
        "correct": True,
        "score": 0.8,
        "model_score": 0.8,
        "confidence": 0.9,
        "criteria": [
            {
                "id": "answers_question",
                "met": True,
                "quality": 0.8,
                "evidence_quote": "because it helped",
            }
        ],
        "missing_criteria": [],
        "misconception_tags": [],
        "blockers": [],
        "language_detected": "en",
    }
    assert isinstance(result["criteria"], list)
    assert isinstance(result["misconception_tags"], list)
