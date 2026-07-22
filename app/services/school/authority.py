"""Canonical endpoint ownership and registration validation for School."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Iterable


SCHOOL_ROUTE_OWNER_ATTRIBUTE = "__canonical_school_owner__"
RETIRED_SCHOOL_ENDPOINT_SPECS: tuple[tuple[str, str, str], ...] = (
    ("GET", "/school/v3/classes", "retired_school_v3_classes"),
    ("POST", "/school/v3/placement/start", "retired_school_v3_placement_start"),
    ("POST", "/school/v3/placement/{session_id}/answer", "retired_school_v3_placement_answer"),
    ("POST", "/school/v3/curriculum/start", "retired_school_v3_curriculum_start"),
    ("POST", "/school/v3/path", "retired_school_v3_path"),
    ("POST", "/school/v3/curriculum/{session_id}/answer", "retired_school_v3_curriculum_answer"),
    ("POST", "/school/v3/masterclass/{session_id}/answer", "retired_school_v3_masterclass_answer"),
    ("POST", "/school/v3/curriculum/{session_id}/resume", "retired_school_v3_curriculum_resume"),
    ("POST", "/school/v3/curriculum/{session_id}/abandon-masterclass", "retired_school_v3_curriculum_abandon"),
    ("GET", "/school/v3/language-confidence", "retired_school_v3_language_confidence"),
    ("GET", "/school/v3/streaks", "retired_school_v3_streaks"),
    ("GET", "/school/v3/badges", "retired_school_v3_badges"),
    ("GET", "/school/classes", "retired_school_classes"),
    ("POST", "/school/v2/placement/start", "retired_school_v2_placement_start"),
    ("POST", "/school/v2/placement/{placement_session_id}/answer", "retired_school_v2_placement_answer"),
    ("POST", "/school/v2/practice/start", "retired_school_v2_practice_start"),
    ("POST", "/school/v2/practice/{practice_session_id}/answer", "retired_school_v2_practice_answer"),
    ("POST", "/school/v2/curriculum/start", "retired_school_v2_curriculum_start"),
    ("POST", "/school/v2/curriculum/{curriculum_session_id}/answer", "retired_school_v2_curriculum_answer"),
    ("GET", "/school/v2/readiness", "retired_school_v2_readiness"),
    ("GET", "/school/v2/home", "retired_school_v2_home"),
    ("GET", "/school/v2/prep-path", "retired_school_v2_prep_path"),
    ("GET", "/school/class/{class_no}", "retired_school_class"),
    ("GET", "/school/test/{test_id}", "retired_school_test"),
    ("POST", "/school/test/{test_id}/submit", "retired_school_test_submit"),
    ("GET", "/school/progress", "retired_school_progress"),
    ("GET", "/school/class/{class_no}/milestone", "retired_school_milestone"),
)


@dataclass(frozen=True, order=True)
class SchoolEndpointAuthority:
    method: str
    path: str
    endpoint_name: str
    owning_service: str

    @property
    def route_key(self) -> tuple[str, str]:
        return (self.method, self.path)


CANONICAL_SCHOOL_AUTHORITY: tuple[SchoolEndpointAuthority, ...] = (
    SchoolEndpointAuthority("GET", "/school/state", "school_state", "app.services.school_rebuild_state"),
    SchoolEndpointAuthority("GET", "/school/catalog", "get_school_catalog", "app.content.school_rebuild_content"),
    SchoolEndpointAuthority("GET", "/school/catalog/{subject_id}/classes/{class_no}", "get_school_class_map", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("GET", "/school/catalog/{subject_id}/classes/{class_no}/chapters/{chapter_id}", "get_school_chapter_map", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("GET", "/school/curriculum", "get_school_curriculum_landing", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("POST", "/school/curriculum/start", "start_school_curriculum", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("GET", "/school/curriculum/{session_id}", "get_school_curriculum_session", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("GET", "/school/curriculum/{session_id}/workspace", "get_school_curriculum_workspace", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("GET", "/school/curriculum/{session_id}/answers/{activity_id}/status", "get_school_curriculum_answer_status", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("POST", "/school/curriculum/{session_id}/answer", "answer_school_curriculum", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("POST", "/school/curriculum/{session_id}/masterclass/start", "start_school_curriculum_masterclass", "app.services.school_rebuild_masterclass"),
    SchoolEndpointAuthority("GET", "/school/masterclass/{session_id}", "get_school_masterclass", "app.services.school_rebuild_masterclass"),
    SchoolEndpointAuthority("GET", "/school/masterclass/{session_id}/answers/{activity_id}/status", "get_school_masterclass_answer_status", "app.services.school_rebuild_masterclass"),
    SchoolEndpointAuthority("POST", "/school/masterclass/{session_id}/answer", "answer_school_masterclass", "app.services.school_rebuild_masterclass"),
    SchoolEndpointAuthority("POST", "/school/curriculum/{session_id}/resume-masterclass", "resume_school_curriculum_masterclass", "app.services.school_rebuild_masterclass"),
    SchoolEndpointAuthority("POST", "/school/curriculum/{session_id}/abandon-masterclass", "abandon_school_curriculum_masterclass", "app.services.school_rebuild_masterclass"),
    SchoolEndpointAuthority("POST", "/school/curriculum/{session_id}/continue-after-support-cap", "continue_school_curriculum_after_support_cap", "app.services.school_rebuild_curriculum"),
    SchoolEndpointAuthority("GET", "/school/support/{session_id}", "get_school_support", "app.services.school_rebuild_support"),
    SchoolEndpointAuthority("GET", "/school/onboarding", "school_onboarding", "app.services.school_rebuild_profile"),
    SchoolEndpointAuthority("POST", "/school/onboarding", "save_school_onboarding", "app.services.school_rebuild_profile"),
    SchoolEndpointAuthority("POST", "/school/onboarding/complete", "complete_school_onboarding", "app.services.school_rebuild_profile"),
    SchoolEndpointAuthority("POST", "/school/placement/start", "start_school_placement", "app.services.school_rebuild_placement"),
    SchoolEndpointAuthority("GET", "/school/placement/report", "get_school_placement_report", "app.services.school_rebuild_report"),
    SchoolEndpointAuthority("GET", "/school/placement/{session_id}", "get_school_placement", "app.services.school_rebuild_placement"),
    SchoolEndpointAuthority("GET", "/school/placement/{session_id}/answers/{activity_id}/status", "get_school_placement_answer_status", "app.services.school_rebuild_placement"),
    SchoolEndpointAuthority("POST", "/school/placement/{session_id}/answer", "answer_school_placement", "app.services.school_rebuild_placement"),
    SchoolEndpointAuthority("POST", "/school/placement/{session_id}/abandon", "abandon_school_placement", "app.services.school_rebuild_placement"),
    SchoolEndpointAuthority("POST", "/school/recap/start", "start_school_recap", "app.services.school_rebuild_recap"),
    SchoolEndpointAuthority("GET", "/school/recap", "get_active_school_recap", "app.services.school_rebuild_recap"),
    SchoolEndpointAuthority("GET", "/school/recap/{session_id}/answers/{activity_id}/status", "get_school_recap_answer_status", "app.services.school_rebuild_recap"),
    SchoolEndpointAuthority("POST", "/school/recap/{session_id}/answer", "answer_school_recap", "app.services.school_rebuild_recap"),
    SchoolEndpointAuthority("GET", "/school/recap/{session_id}", "get_school_recap", "app.services.school_rebuild_recap"),
    *(
        SchoolEndpointAuthority(
            method,
            path,
            endpoint_name,
            "app.api.school_retirement_routes",
        )
        for method, path, endpoint_name in RETIRED_SCHOOL_ENDPOINT_SPECS
    ),
)

DISABLED_SCHOOL_AUTHORITY: tuple[SchoolEndpointAuthority, ...] = (
    SchoolEndpointAuthority(
        "GET",
        "/school/state",
        "school_availability_state",
        "app.services.school.availability",
    ),
    *(
        SchoolEndpointAuthority(
            method,
            path,
            endpoint_name,
            "app.api.school_retirement_routes",
        )
        for method, path, endpoint_name in RETIRED_SCHOOL_ENDPOINT_SPECS
    ),
)


def school_route_owner(owning_service: str):
    """Mark a route handler with its independently declared service owner."""

    def decorate(endpoint):
        setattr(endpoint, SCHOOL_ROUTE_OWNER_ATTRIBUTE, owning_service)
        return endpoint

    return decorate


def _school_registrations(
    routes: Iterable[object],
) -> tuple[tuple[str, str, str, str | None], ...]:
    registrations: list[tuple[str, str, str, str | None]] = []
    active_containers: set[int] = set()

    def walk(nested_routes: Iterable[object], prefix: str = "") -> None:
        for route in nested_routes:
            route_path = str(getattr(route, "path", "") or "")
            effective_path = _join_route_path(prefix, route_path)
            methods = getattr(route, "methods", None)
            child_routes = getattr(route, "routes", None)

            if _is_school_path(effective_path) and not methods:
                raise ValueError(
                    f"canonical_school_non_http_route:{effective_path}"
                )

            if methods and _is_school_path(effective_path):
                endpoint = getattr(route, "endpoint", None)
                endpoint_name = str(getattr(endpoint, "__name__", ""))
                owner = getattr(endpoint, SCHOOL_ROUTE_OWNER_ATTRIBUTE, None)
                for method in sorted(methods):
                    if method not in {"HEAD", "OPTIONS"}:
                        registrations.append(
                            (method, effective_path, endpoint_name, owner)
                        )

            if child_routes is not None and id(route) not in active_containers:
                active_containers.add(id(route))
                try:
                    walk(child_routes, effective_path)
                finally:
                    active_containers.remove(id(route))

    walk(routes)
    return tuple(registrations)


def _join_route_path(prefix: str, path: str) -> str:
    if path in {"", "/"}:
        return prefix or ("/" if path == "/" else "")
    if prefix in {"", "/"}:
        return f"/{path.lstrip('/')}"
    return f"{prefix.rstrip('/')}/{path.lstrip('/')}"


def _is_school_path(path: str) -> bool:
    return path == "/school" or path.startswith("/school/")


def validate_canonical_school_routes(
    routes: Iterable[object],
    *,
    school_enabled: bool = True,
) -> None:
    """Fail startup when mounted School registrations drift from authority."""

    expected_authority = (
        CANONICAL_SCHOOL_AUTHORITY if school_enabled else DISABLED_SCHOOL_AUTHORITY
    )
    expected_keys = tuple(entry.route_key for entry in expected_authority)
    if len(expected_keys) != len(set(expected_keys)):
        raise ValueError("duplicate_canonical_school_authority")
    for entry in expected_authority:
        if not entry.owning_service.startswith("app."):
            raise ValueError(
                f"canonical_school_owner_import_error:{entry.owning_service}"
            )
        try:
            importlib.import_module(entry.owning_service)
        except ImportError as exc:
            raise ValueError(
                f"canonical_school_owner_import_error:{entry.owning_service}"
            ) from exc

    actual = _school_registrations(routes)
    actual_keys = tuple((method, path) for method, path, _name, _owner in actual)
    if len(actual_keys) != len(set(actual_keys)):
        raise ValueError("duplicate_canonical_school_route")
    if set(actual_keys) != set(expected_keys):
        missing = sorted(set(expected_keys) - set(actual_keys))
        unexpected = sorted(set(actual_keys) - set(expected_keys))
        raise ValueError(
            f"canonical_school_route_mismatch:missing={missing}:unexpected={unexpected}"
        )
    expected_by_key = {
        entry.route_key: entry for entry in expected_authority
    }
    for method, path, endpoint_name, owner in actual:
        expected = expected_by_key[(method, path)]
        if endpoint_name != expected.endpoint_name:
            raise ValueError(
                "canonical_school_route_mismatch:"
                f"{method}:{path}:expected={expected.endpoint_name}:actual={endpoint_name}"
            )
        if owner != expected.owning_service:
            raise ValueError(
                "canonical_school_route_owner_mismatch:"
                f"{method}:{path}:expected={expected.owning_service}:actual={owner}"
            )


__all__ = [
    "CANONICAL_SCHOOL_AUTHORITY",
    "DISABLED_SCHOOL_AUTHORITY",
    "SCHOOL_ROUTE_OWNER_ATTRIBUTE",
    "RETIRED_SCHOOL_ENDPOINT_SPECS",
    "SchoolEndpointAuthority",
    "school_route_owner",
    "validate_canonical_school_routes",
]
