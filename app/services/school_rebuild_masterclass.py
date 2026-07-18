"""Linked focused-practice session for a paused School curriculum level."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from app.services import school_rebuild_curriculum as curriculum
from app.services.school_rebuild_language import localized_teaching_support


ENGINE_VERSION = "school-rebuild-masterclass-3"
REMEDIATION_SEQUENCE = (
    ("supported_practice", "masterclass", "supported"),
    ("independent_check", "independent_check", "certifying"),
    ("transfer_check", "transfer_check", "certifying"),
)
DEEP_REMEDIATION_SEQUENCE = (
    ("supported_practice", "masterclass", "supported"),
    ("misconception_rebuild", "revision_level_1", "supported"),
    ("independent_check", "independent_application", "certifying"),
    ("transfer_check", "transfer", "certifying"),
)


def _unique_skill_ids(values: Any) -> list[str]:
    return list(dict.fromkeys(
        str(value)
        for value in values or []
        if str(value)
    ))


def _masterclass_skill_scope(
    level: dict[str, Any],
    interrupt: dict[str, Any],
) -> list[str]:
    level_skill_ids = _unique_skill_ids(level.get("skill_ids"))
    if not level_skill_ids:
        raise ValueError("masterclass_level_skills_missing")
    trigger_skill_ids = _unique_skill_ids(interrupt.get("skill_ids"))
    if (
        str(interrupt.get("runtime_contract") or "") == "v2"
        and trigger_skill_ids
    ):
        level_skill_set = set(level_skill_ids)
        scoped = [
            skill_id
            for skill_id in trigger_skill_ids
            if skill_id in level_skill_set
        ]
        if not scoped:
            raise ValueError("masterclass_trigger_skills_missing")
        return scoped
    return level_skill_ids


def _scoped_authored_activity(
    activity: dict[str, Any],
    trigger_skill_ids: list[str],
) -> dict[str, Any] | None:
    trigger_skill_set = set(trigger_skill_ids)
    assessed_skill_ids = [
        skill_id
        for skill_id in _unique_skill_ids(activity.get("knowledge_components"))
        if skill_id in trigger_skill_set
    ]
    if not assessed_skill_ids:
        return None
    return {
        **activity,
        "knowledge_components": assessed_skill_ids,
        "skill_ids": assessed_skill_ids,
        "assessed_skill_ids": assessed_skill_ids,
    }


def new_masterclass_state(
    *,
    curriculum_session_id: str,
    curriculum_state: dict[str, Any],
) -> dict[str, Any]:
    interrupt = curriculum_state.get("active_interrupt")
    if (
        curriculum_state.get("status") != "paused_for_masterclass"
        or curriculum_state.get("phase") != "paused_for_masterclass"
        or not isinstance(interrupt, dict)
    ):
        raise ValueError("curriculum_not_paused_for_masterclass")
    level_id = str(interrupt.get("level_id") or "")
    level = next(
        (
            candidate
            for candidate in curriculum_state.get("levels") or []
            if str(candidate.get("level_id") or "") == level_id
        ),
        None,
    )
    if not isinstance(level, dict):
        raise ValueError("masterclass_level_not_found")
    skill_ids = _masterclass_skill_scope(level, interrupt)
    state = {
        "engine_version": ENGINE_VERSION,
        "status": "active",
        "curriculum_session_id": curriculum_session_id,
        "chapter_id": str(
            (curriculum_state.get("chapter") or {}).get("chapter_id") or ""
        ),
        "source_provenance": _source_provenance_context(
            curriculum_state.get("chapter")
        ),
        "interrupt_id": str(interrupt.get("interrupt_id") or ""),
        "level_id": level_id,
        "focus": str(level.get("focus") or ""),
        "skill_ids": skill_ids,
        "preferred_teaching_language": str(
            curriculum_state.get("preferred_teaching_language") or "en"
        ),
        "en_production_confidence": float(
            curriculum_state.get("en_production_confidence") or 0.0
        ),
        "trigger_count": int(interrupt.get("trigger_count") or 0),
        "phase_index": 0,
        "attempts": [],
        "last_feedback": None,
    }
    if level.get("teaching_steps"):
        pools = _deep_phase_activity_pools(
            level,
            curriculum_state=curriculum_state,
            trigger_skill_ids=skill_ids,
        )
        state["remediation_sequence"] = [
            {
                "phase": remediation_phase,
                "check_kind": check_kind,
                "evidence_role": evidence_role,
            }
            for remediation_phase, check_kind, evidence_role
            in DEEP_REMEDIATION_SEQUENCE
        ]
        state["phase_activity_pools"] = pools
        return state

    authored_checks = dict(level.get("checks") or {})
    checks = {}
    for remediation_phase, check_kind, evidence_role in REMEDIATION_SEQUENCE:
        check = dict(authored_checks.get(check_kind) or {})
        if not _authored_check_is_evaluable(check):
            raise ValueError(f"masterclass_content_required:{check_kind}")
        check = _scoped_authored_activity(check, skill_ids)
        if check is None:
            raise ValueError(f"masterclass_content_required:{check_kind}")
        checks[remediation_phase] = {
            **check,
            "check_kind": check_kind,
            "evidence_role": evidence_role,
        }
    state["checks"] = checks
    return state


def current_activity(state: dict[str, Any]) -> dict[str, Any] | None:
    if state.get("status") != "active":
        return None
    attempts = list(state.get("attempts") or [])
    attempt_no = len(attempts) + 1
    phase_index = int(state.get("phase_index") or 0)
    sequence = _remediation_sequence(state)
    if phase_index < 0 or phase_index >= len(sequence):
        raise ValueError("masterclass_phase_invalid")
    remediation_phase, check_kind, evidence_role = sequence[phase_index]
    activity_pools = dict(state.get("phase_activity_pools") or {})
    phase_pool = [
        dict(item)
        for item in activity_pools.get(remediation_phase) or []
        if isinstance(item, dict)
    ]
    if phase_pool:
        phase_attempt_count = sum(
            1
            for attempt in attempts
            if attempt.get("remediation_phase") == remediation_phase
        )
        check = dict(phase_pool[min(phase_attempt_count, len(phase_pool) - 1)])
    else:
        checks = dict(state.get("checks") or {})
        check = dict(checks.get(remediation_phase) or {})
    if not check and state.get("check"):
        # Existing in-progress sessions from engine v1 remain recoverable.
        remediation_phase = "supported_practice"
        check = dict(state.get("check") or {})
    if not check:
        raise ValueError("masterclass_content_not_authored")
    check = _scoped_authored_activity(
        check,
        _unique_skill_ids(state.get("skill_ids")),
    )
    if check is None:
        raise ValueError("masterclass_assessed_skills_missing")
    assessed_skill_ids = list(check["assessed_skill_ids"])
    language_support = localized_teaching_support(
        preferred_language=str(
            state.get("preferred_teaching_language") or "en"
        ),
        skill_ids=assessed_skill_ids,
        stage=remediation_phase,
        en_production_confidence=float(
            state.get("en_production_confidence") or 0.0
        ),
    )
    return {
        **check,
        "activity_id": (
            f"{state['interrupt_id']}:{remediation_phase}:attempt:{attempt_no}"
        ),
        "kind": "masterclass",
        "remediation_phase": remediation_phase,
        "check_kind": check.get("check_kind") or check_kind,
        "evidence_role": check.get("evidence_role") or evidence_role,
        "source_activity_id": str(
            check.get("source_activity_id")
            or check.get("variant_id")
            or f"{state['level_id']}:{remediation_phase}"
        ),
        "phase_index": phase_index,
        "phase_count": len(sequence),
        "level_id": state["level_id"],
        "focus": state["focus"],
        "skill_ids": assessed_skill_ids,
        "assessed_skill_ids": assessed_skill_ids,
        "knowledge_components": assessed_skill_ids,
        "teaching_block": " ".join(
            part
            for part in (language_support, str(check.get("teaching_block") or ""))
            if part
        ),
        "chapter_id": str(state.get("chapter_id") or ""),
        "title": f"Focused practice: {state['focus']}",
        "attempt_no": attempt_no,
        "can_answer": True,
    }


def consumed_source_activity_ids(state: dict[str, Any]) -> tuple[str, ...]:
    """Return every authored source already answered or shown in this child."""

    consumed: list[str] = []
    for attempt in state.get("attempts") or []:
        if not isinstance(attempt, dict):
            continue
        source_activity_id = str(attempt.get("source_activity_id") or "")
        if source_activity_id and source_activity_id not in consumed:
            consumed.append(source_activity_id)
    activity = current_activity(state)
    if activity:
        source_activity_id = str(activity.get("source_activity_id") or "")
        if source_activity_id and source_activity_id not in consumed:
            consumed.append(source_activity_id)
    return tuple(consumed)


def qualifies_for_curriculum_resume(
    state: dict[str, Any],
    *,
    curriculum_session_id: str,
    interrupt_id: str,
    level_id: str,
    skill_ids: list[str] | tuple[str, ...],
) -> bool:
    """Require linked independent and transfer evidence before parent resume."""

    if (
        state.get("status") != "complete"
        or str(state.get("curriculum_session_id") or "")
        != curriculum_session_id
        or str(state.get("interrupt_id") or "") != interrupt_id
        or str(state.get("level_id") or "") != level_id
    ):
        return False
    expected_skill_ids = set(_unique_skill_ids(skill_ids))
    child_skill_ids = set(_unique_skill_ids(state.get("skill_ids")))
    if not expected_skill_ids or not expected_skill_ids.issubset(child_skill_ids):
        return False

    required_phases = {
        remediation_phase
        for remediation_phase, _check_kind, evidence_role in _remediation_sequence(state)
        if evidence_role == "certifying"
    }
    qualified_phases: set[str] = set()
    for raw_attempt in state.get("attempts") or []:
        if not isinstance(raw_attempt, dict):
            continue
        attempt_skill_ids = set(_unique_skill_ids(raw_attempt.get("skill_ids")))
        if (
            raw_attempt.get("correct") is True
            and not list(raw_attempt.get("blockers") or [])
            and expected_skill_ids.issubset(attempt_skill_ids)
        ):
            qualified_phases.add(str(raw_attempt.get("remediation_phase") or ""))
    return bool(required_phases) and required_phases.issubset(qualified_phases)


def persistence_attempt_type(evaluation: dict[str, Any]) -> str:
    """Map child evidence to readiness attempt types without certifying support."""

    if str(evaluation.get("evidence_role") or "") != "certifying":
        return "masterclass"
    remediation_phase = str(evaluation.get("remediation_phase") or "")
    if remediation_phase in {"independent_check", "transfer_check"}:
        return remediation_phase
    return "masterclass"


def apply_masterclass_answer(
    state: dict[str, Any],
    *,
    activity_id: str,
    answer: str,
    open_answer_evaluation: dict[str, Any] | None = None,
    open_answer_preflight_failed: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    activity = current_activity(state)
    if not activity or activity["activity_id"] != activity_id:
        raise ValueError("unexpected_masterclass_activity")
    evaluator_activity = curriculum.evaluator_activity_for_answer(activity, answer)
    if evaluator_activity is None:
        answer_evaluation = curriculum.evaluate_deterministic_answer(activity, answer)
    elif open_answer_preflight_failed:
        answer_evaluation = curriculum._open_answer_preflight_failure(activity)
    elif open_answer_evaluation is None:
        raise ValueError("open_answer_evaluation_required")
    else:
        answer_evaluation = curriculum.decide_open_answer_evaluation(
            evaluator_activity,
            open_answer_evaluation,
            answer=answer,
        )
    correct = bool(answer_evaluation["correct"])
    phase_index = int(activity["phase_index"])
    sequence = _remediation_sequence(state)
    final_phase = phase_index == len(sequence) - 1
    attempt = {
        "activity_id": activity_id,
        "attempt_no": int(activity["attempt_no"]),
        "remediation_phase": activity["remediation_phase"],
        "source_activity_id": activity.get("source_activity_id"),
        "skill_ids": list(activity.get("assessed_skill_ids") or []),
        "answer": answer,
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "blockers": list(answer_evaluation["blockers"]),
    }
    next_phase_index = phase_index + 1 if correct and not final_phase else phase_index
    updated = {
        **state,
        "attempts": list(state.get("attempts") or []) + [attempt],
        "phase_index": next_phase_index,
        "status": "complete" if correct and final_phase else "active",
        "last_feedback": {
            "activity_id": activity_id,
            "correct": correct,
            "message": (
                "Good. You rebuilt the skill in a new situation and can return to the chapter."
                if correct and final_phase
                else "Good. Now show the same skill with less support."
                if correct
                else "Not yet. Use the teaching clue, then try a fresh focused example."
            ),
        },
    }
    return updated, {
        "activity_id": activity_id,
        "kind": "masterclass",
        "level_id": state["level_id"],
        "focus": state["focus"],
        "skill_ids": list(activity.get("assessed_skill_ids") or []),
        "chapter_id": str(state.get("chapter_id") or ""),
        "attempt_no": int(activity["attempt_no"]),
        "remediation_phase": activity["remediation_phase"],
        "source_activity_id": activity.get("source_activity_id"),
        "evidence_role": activity.get("evidence_role"),
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "blockers": list(answer_evaluation["blockers"]),
        "misconception_tags": list(answer_evaluation["misconception_tags"]),
        "language_detected": answer_evaluation["language_detected"],
    }


def public_masterclass_response(
    session_row: dict[str, Any],
    *,
    parent_session: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = dict(session_row.get("state_json") or {})
    activity = current_activity(state)
    source_provenance = _source_provenance_for_public_response(
        session_row,
        state,
        parent_session=parent_session,
    )
    return {
        "session_id": str(session_row["session_id"]),
        "flow_type": "masterclass",
        "status": state.get("status") or session_row.get("status"),
        "linked_curriculum_session_id": str(
            state.get("curriculum_session_id")
            or session_row.get("linked_session_id")
            or ""
        ),
        "interrupt_id": str(state.get("interrupt_id") or ""),
        "level_id": str(state.get("level_id") or ""),
        "focus": str(state.get("focus") or ""),
        "trigger_count": int(state.get("trigger_count") or 0),
        "remediation_phase": (
            activity.get("remediation_phase") if activity else "complete"
        ),
        "completed_phases": int(state.get("phase_index") or 0),
        "total_phases": len(_remediation_sequence(state)),
        "current_activity": _public_activity(
            activity,
            source_provenance=source_provenance,
        ),
        "last_feedback": state.get("last_feedback"),
    }


def _source_provenance_context(chapter: Any) -> dict[str, Any]:
    """Keep only the parent metadata needed to locate an activity source."""

    chapter = chapter if isinstance(chapter, dict) else {}
    anchors = []
    for anchor in chapter.get("source_anchors") or []:
        if not isinstance(anchor, dict):
            continue
        anchor_id = str(anchor.get("anchor_id") or "")
        if not anchor_id:
            continue
        anchors.append({
            "anchor_id": anchor_id,
            "section_label": str(anchor.get("section_label") or ""),
            "page_start": int(anchor.get("page_start") or 0),
            "page_end": int(anchor.get("page_end") or 0),
            "source_url": str(anchor.get("source_url") or ""),
        })
    return {
        "book_title": str(chapter.get("book_title") or ""),
        "chapter_title": str(chapter.get("title") or ""),
        "source_anchors": anchors,
    }


def _official_ncert_source_url(value: Any) -> str | None:
    source_url = str(value or "")
    try:
        parsed = urlparse(source_url)
        port = parsed.port
    except ValueError:
        return None
    if (
        parsed.scheme != "https"
        or parsed.hostname != "ncert.nic.in"
        or parsed.username is not None
        or parsed.password is not None
        or port not in (None, 443)
    ):
        return None
    return source_url


def _source_provenance_from_snapshot(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return _source_provenance_context({
        "book_title": value.get("book_title"),
        "title": value.get("chapter_title"),
        "source_anchors": value.get("source_anchors"),
    })


def _legacy_parent_matches_masterclass(
    session_row: dict[str, Any],
    state: dict[str, Any],
    parent_session: dict[str, Any] | None,
) -> bool:
    if not isinstance(parent_session, dict):
        return False
    child_session_id = str(session_row.get("session_id") or "")
    linked_session_id = str(session_row.get("linked_session_id") or "")
    state_parent_id = str(state.get("curriculum_session_id") or "")
    parent_session_id = str(parent_session.get("session_id") or "")
    if (
        not child_session_id
        or not parent_session_id
        or not linked_session_id
        or linked_session_id != parent_session_id
        or (state_parent_id and state_parent_id != parent_session_id)
        or parent_session.get("api_version") != "rebuild"
        or parent_session.get("flow_type") != "curriculum"
        or str(parent_session.get("user_id") or "")
        != str(session_row.get("user_id") or "")
    ):
        return False
    for lineage_field in (
        "profile_version_id",
        "source_placement_report_id",
    ):
        child_value = str(session_row.get(lineage_field) or "")
        parent_value = str(parent_session.get(lineage_field) or "")
        if not child_value or not parent_value or child_value != parent_value:
            return False
    parent_state = parent_session.get("state_json")
    if (
        parent_session.get("status") != "paused_for_masterclass"
        or not isinstance(parent_state, dict)
        or parent_state.get("status") != "paused_for_masterclass"
        or parent_state.get("phase") != "paused_for_masterclass"
    ):
        return False
    interrupt = parent_state.get("active_interrupt")
    return bool(
        isinstance(interrupt, dict)
        and str(interrupt.get("masterclass_session_id") or "")
        == child_session_id
        and str(interrupt.get("interrupt_id") or "")
        == str(state.get("interrupt_id") or "")
        and str(interrupt.get("level_id") or "")
        == str(state.get("level_id") or "")
    )


def _source_provenance_for_public_response(
    session_row: dict[str, Any],
    state: dict[str, Any],
    *,
    parent_session: dict[str, Any] | None,
) -> dict[str, Any] | None:
    current = _source_provenance_from_snapshot(
        state.get("source_provenance")
    )
    if current and current.get("source_anchors"):
        return current
    if not _legacy_parent_matches_masterclass(
        session_row,
        state,
        parent_session,
    ):
        return None
    parent_state = dict(parent_session.get("state_json") or {})
    return _source_provenance_context(parent_state.get("chapter"))


def _public_source_reference(
    activity: dict[str, Any],
    source_provenance: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Resolve parent anchor IDs without exposing internal provenance fields."""

    if not isinstance(source_provenance, dict):
        return None
    anchors_by_id = {
        str(anchor.get("anchor_id") or ""): anchor
        for anchor in source_provenance.get("source_anchors") or []
        if isinstance(anchor, dict) and str(anchor.get("anchor_id") or "")
    }
    public_anchors = []
    for anchor_id in activity.get("source_anchor_ids") or []:
        anchor = anchors_by_id.get(str(anchor_id))
        if not anchor:
            continue
        source_url = _official_ncert_source_url(anchor.get("source_url"))
        if not source_url:
            continue
        public_anchors.append({
            "section_label": str(anchor.get("section_label") or ""),
            "page_start": int(anchor.get("page_start") or 0),
            "page_end": int(anchor.get("page_end") or 0),
            "source_url": source_url,
        })
    if not public_anchors:
        return None
    return {
        "book_title": str(source_provenance.get("book_title") or ""),
        "chapter_title": str(source_provenance.get("chapter_title") or ""),
        "anchors": public_anchors,
    }


def _public_activity(
    activity: dict[str, Any] | None,
    *,
    source_provenance: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not activity:
        return None
    public = {
        "activity_id": activity["activity_id"],
        "kind": "masterclass",
        "remediation_phase": activity["remediation_phase"],
        "phase_index": int(activity["phase_index"]),
        "phase_count": int(activity["phase_count"]),
        "level_id": activity["level_id"],
        "focus": activity["focus"],
        "title": activity["title"],
        "teaching_block": activity["teaching_block"],
        "passage": activity["passage"],
        "prompt": activity["prompt"],
        "options": list(activity.get("options") or []) or None,
        "attempt_no": int(activity["attempt_no"]),
        "can_answer": True,
    }
    source_reference = _public_source_reference(activity, source_provenance)
    if source_reference is not None:
        public["source_reference"] = source_reference
    return public


def _authored_check_is_evaluable(check: dict[str, Any]) -> bool:
    return bool(
        check
        and (
            check.get("accepted_answers")
            or check.get("answer_rule") == "concept_slots"
            or check.get("evaluation_mode") == "llm_rubric"
        )
    )


def _remediation_sequence(
    state: dict[str, Any],
) -> tuple[tuple[str, str, str], ...]:
    authored = list(state.get("remediation_sequence") or [])
    if not authored:
        return REMEDIATION_SEQUENCE
    sequence = tuple(
        (
            str(item.get("phase") or ""),
            str(item.get("check_kind") or ""),
            str(item.get("evidence_role") or "supported"),
        )
        for item in authored
        if isinstance(item, dict)
    )
    if not sequence or any(not phase for phase, _kind, _role in sequence):
        raise ValueError("masterclass_remediation_sequence_invalid")
    return sequence


def _activity_fingerprint(activity: dict[str, Any]) -> tuple[str, str]:
    def normalized(value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip().casefold())

    return normalized(activity.get("passage")), normalized(activity.get("prompt"))


def _deep_phase_activity_pools(
    level: dict[str, Any],
    *,
    curriculum_state: dict[str, Any],
    trigger_skill_ids: list[str],
) -> dict[str, list[dict[str, Any]]]:
    checks = dict(level.get("checks") or {})
    memory = dict(curriculum_state.get("hot_session_memory") or {})
    used_variant_ids = {
        str(item)
        for item in (
            list(memory.get("used_variant_ids") or [])
            + list(level.get("used_variant_ids") or [])
        )
    }
    steps_by_phase = {
        str(step.get("phase") or ""): dict(step)
        for step in level.get("teaching_steps") or []
        if isinstance(step, dict)
    }

    def prepared_check(check_kind: str) -> dict[str, Any] | None:
        check = dict(checks.get(check_kind) or {})
        if not _authored_check_is_evaluable(check):
            raise ValueError(f"masterclass_content_required:{check_kind}")
        scoped = _scoped_authored_activity(check, trigger_skill_ids)
        if scoped is None:
            return None
        return {
            **scoped,
            "check_kind": check_kind,
            "source_activity_id": f"{level['level_id']}:check:{check_kind}",
        }

    def fresh_variants(
        teaching_phase: str,
        *,
        canonical_check_kind: str | None = None,
    ) -> list[dict[str, Any]]:
        step = steps_by_phase.get(teaching_phase) or {}
        canonical_fingerprint = (
            _activity_fingerprint(dict(checks.get(canonical_check_kind) or {}))
            if canonical_check_kind
            else None
        )
        variants = []
        for item in step.get("variant_pool") or []:
            if not isinstance(item, dict):
                continue
            candidate = dict(item)
            variant_id = str(candidate.get("variant_id") or "")
            if (
                not variant_id
                or variant_id in used_variant_ids
                or (
                    canonical_fingerprint is not None
                    and _activity_fingerprint(candidate) == canonical_fingerprint
                )
                or not _authored_check_is_evaluable(candidate)
            ):
                continue
            candidate = _scoped_authored_activity(candidate, trigger_skill_ids)
            if candidate is None:
                continue
            variants.append({
                **candidate,
                "source_activity_id": variant_id,
            })
        return sorted(
            variants,
            key=lambda item: -len(item.get("assessed_skill_ids") or []),
        )

    supported = []
    for check_kind in ("masterclass", "bridge"):
        if support_check := prepared_check(check_kind):
            supported.append(support_check)
    supported.extend(fresh_variants("guided_practice"))
    supported.sort(
        key=lambda item: -len(item.get("assessed_skill_ids") or [])
    )
    misconception_rebuild = []
    for check_kind in (
            "revision_level_1",
            "revision_level_2",
            "revision_level_3",
    ):
        if not checks.get(check_kind):
            continue
        if revision_check := prepared_check(check_kind):
            misconception_rebuild.append(revision_check)
    pools = {
        "supported_practice": supported,
        "misconception_rebuild": misconception_rebuild,
        "independent_check": fresh_variants(
            "independent_application",
            canonical_check_kind="independent_check",
        ),
        "transfer_check": fresh_variants(
            "transfer",
            canonical_check_kind="transfer_check",
        ),
    }
    for remediation_phase, activities in pools.items():
        if not activities:
            raise ValueError(
                f"masterclass_content_required:{remediation_phase}"
            )
    return pools
