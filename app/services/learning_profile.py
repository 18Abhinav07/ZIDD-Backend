"""Canonical learning-profile projection for career prep/test evidence."""
from __future__ import annotations

import re
from typing import Any

from app.content.registry import module_of
from app.services.career_skill_taxonomy import (
    canonicalize_report_gaps,
    focus_node_for_observation,
    skill_for_id,
    unmapped_report_observations,
)


CAREER_DOMAIN = "career"
SCHOOL_ADAPTER_DOMAIN = "school_adapter"

_CAREER_TASK_TYPES_BY_MODULE = {
    "interview": {"interview_prep", "interview_test"},
    "group_discussion": {"gd_prep", "gd_test"},
}

_LEGACY_HASHED_REPORT_SKILL_RE = re.compile(
    r"^(?:interview_test|gd_test):.+:[0-9a-f]{8,64}$",
    re.I,
)
_GROUNDING_ATTEMPT_TYPES = {"independent", "pressure", "transfer"}


def _module_for_task_type(task_type: str) -> str:
    for module_id, task_types in _CAREER_TASK_TYPES_BY_MODULE.items():
        if task_type in task_types:
            return module_id
    return ""


def _row_matches_career_module(row: dict[str, Any], module_id: str) -> bool:
    """Match only explicit registry/module/task relationships.

    A scoped prompt must fail closed when a row has no structural ownership.
    Text inside a gap, report, or skill label is never used to infer its mode.
    """
    if not module_id:
        return True
    owners: list[str] = []
    explicit_module = str(row.get("module_id") or "").strip()
    if explicit_module:
        owners.append(explicit_module)
    task_module = _module_for_task_type(str(row.get("task_type") or "").strip())
    if task_module:
        owners.append(task_module)
    node_id = str(row.get("node_id") or row.get("competency_node") or "").strip()
    node_module = _career_module_for_node(node_id) if node_id else ""
    if node_module:
        owners.append(node_module)
    return bool(owners) and all(owner == module_id for owner in owners)


def _current_profile_rows(
    profiles: list[dict[str, Any]],
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    _ = reports
    current_by_skill: dict[tuple[str, str], tuple[bool, dict[str, Any]]] = {}
    for profile in profiles:
        skill_id = str(profile.get("skill_id") or "").strip()
        if (
            not skill_id
            or skill_id == "insufficient_assessment_evidence"
            or _LEGACY_HASHED_REPORT_SKILL_RE.fullmatch(skill_id)
        ):
            continue
        row = dict(profile)
        domain = str(row.get("domain") or "").strip()
        exact_canonical = skill_for_id(skill_id) is not None
        key = (domain, str(row.get("skill_id") or ""))
        previous = current_by_skill.get(key)
        if previous is None or (exact_canonical and not previous[0]):
            current_by_skill[key] = (exact_canonical, row)
    return [row for _exact, row in current_by_skill.values()]


def _safe_score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value or 0.0))), 4)
    except (TypeError, ValueError):
        return 0.0


def _report_skill_score(overall_score: float, gap: dict[str, Any]) -> float:
    status = str(gap.get("status") or "active_gap")
    caps = {"active_gap": 0.49, "improving": 0.79, "resolved": 0.95}
    explicit = gap.get("skill_score")
    score = _safe_score(explicit) if explicit is not None else overall_score
    return min(score, caps.get(status, 0.49))


def _first(items: list[Any], default: str = "") -> str:
    for item in items:
        text = str(item or "").strip()
        if text:
            return text
    return default


def _clean_string_list(values: Any, *, limit: int = 8, item_limit: int = 120) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        text = text[:item_limit]
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= limit:
            break
    return out


def _row_dict(row: Any) -> dict[str, Any]:
    if hasattr(row, "model_dump"):
        row = row.model_dump()
    return row if isinstance(row, dict) else {}


_EVIDENCE_CRITERION_PRIORITY = (
    "result",
    "progress_evidence",
    "quantified_before_after",
    "impact_signal",
    "impact_claim",
    "learner_contribution",
    "learner_action",
    "actions",
    "specific_evidence",
    "concrete_evidence",
    "evidence_defense",
    "pressure_response",
)


def _first_criterion_quote(criteria: list[Any], fallback: str = "") -> str:
    normalized_fallback = " ".join(str(fallback or "").split()).lower()
    candidates: list[tuple[int, int, str]] = []
    for index, raw in enumerate(criteria):
        row = _row_dict(raw)
        quote = " ".join(str(row.get("evidence_quote") or "").split())
        if (
            row.get("met") is True
            and quote
            and (not normalized_fallback or quote.lower() in normalized_fallback)
        ):
            criterion_id = str(row.get("id") or row.get("criterion_id") or "").strip()
            try:
                priority = _EVIDENCE_CRITERION_PRIORITY.index(criterion_id)
            except ValueError:
                priority = len(_EVIDENCE_CRITERION_PRIORITY)
            candidates.append((priority, index, quote[:320]))
    return min(candidates, default=(0, 0, ""))[2]


def _quote(value: Any) -> str:
    return " ".join(str(value or "").split())[:320]


def _latest_evidence(evidence: Any, *, allow_answer_excerpt: bool = False) -> str:
    """Return only row-owned learner quotes.

    Report-wide quote lists, summaries, labels, gaps, and recommendations are
    intentionally excluded. A prep event owns its answer excerpt because it is
    already scoped to one assessed skill.
    """
    if not isinstance(evidence, dict):
        return ""
    answer_excerpt = evidence.get("answer_excerpt") if allow_answer_excerpt else ""
    criteria = evidence.get("criteria")
    if isinstance(criteria, list) and str(answer_excerpt or "").strip():
        criterion_quote = _first_criterion_quote(
            criteria,
            str(answer_excerpt),
        )
        if criterion_quote:
            return criterion_quote
    for key in ("evidence_quote", "latest_quote"):
        direct = _quote(evidence.get(key))
        if direct:
            return direct
    if allow_answer_excerpt:
        return _quote(evidence.get("answer_excerpt"))
    return ""


def _gap_status(*, readiness: float, mastery: float, confidence: float) -> str:
    if mastery >= 0.95:
        return "mastered"
    if readiness >= 0.88 and mastery >= 0.5 and confidence >= 0.7:
        return "resolved"
    if readiness >= 0.65:
        return "improving"
    return "active_gap"


def _career_module_for_node(node_id: str) -> str:
    try:
        module_id = module_of(node_id)
    except Exception:
        return ""
    return module_id if module_id in {"interview", "group_discussion"} else ""


def _prep_task_type_for_module(module_id: str) -> str:
    if module_id == "group_discussion":
        return "gd_prep"
    if module_id == "interview":
        return "interview_prep"
    return ""


def _progression_evidence(row: dict[str, Any]) -> str:
    evidence = row.get("mastery_evidence")
    if isinstance(evidence, list):
        for item in reversed(evidence):
            if not isinstance(item, dict):
                continue
            for criterion in reversed(item.get("criteria") or []):
                if not isinstance(criterion, dict):
                    continue
                quote = " ".join(str(criterion.get("evidence_quote") or "").split())
                if quote:
                    return quote[:320]
    return ""


def _progression_readiness(row: dict[str, Any]) -> float:
    for key in ("readiness_score", "best_independent_score", "best_ema", "ema", "mastery"):
        value = _safe_score(row.get(key))
        if value > 0:
            return value
    return 0.0


def _base_item_from_profile(profile: dict[str, Any]) -> dict[str, Any] | None:
    skill_id = str(profile.get("skill_id") or "").strip()
    if not skill_id:
        return None
    task_type = str(profile.get("task_type") or "").strip()
    readiness = _safe_score(profile.get("readiness"))
    mastery = _safe_score(profile.get("mastery"))
    confidence = _safe_score(profile.get("confidence"))
    gaps = [str(item).strip() for item in profile.get("gaps_json") or [] if str(item).strip()]
    evidence_json = profile.get("evidence_json") if isinstance(profile.get("evidence_json"), dict) else {}
    skill = skill_for_id(skill_id)
    focus_id = str(evidence_json.get("recommended_node_id") or "").strip()
    if focus_id and skill_for_id(focus_id) is None:
        focus_id = ""
    if not focus_id and skill is not None:
        focus_id = skill.recommended_node_id
    if not focus_id:
        focus_id = focus_node_for_observation(task_type, skill_id, *gaps)
    explicit_status = str(evidence_json.get("gap_status") or "").strip()
    status = (
        explicit_status
        if explicit_status in {"active_gap", "improving", "resolved"}
        else _gap_status(readiness=readiness, mastery=mastery, confidence=confidence)
    )
    if status == "resolved" and mastery < 0.95:
        status = "improving"
    missing_criteria = _clean_string_list(
        evidence_json.get("required_missing") or evidence_json.get("missing_criteria"),
        limit=5,
    )
    blockers = _clean_string_list(evidence_json.get("blockers"), limit=5)
    return {
        "skill_id": skill_id,
        "focus_id": focus_id,
        "module_id": str(profile.get("module_id") or ""),
        "task_type": task_type,
        "status": status,
        "readiness": readiness,
        "confidence": confidence,
        "attempts": int(profile.get("attempts") or 0),
        "gap": _first(gaps),
        "latest_evidence": _latest_evidence(
            evidence_json,
            allow_answer_excerpt=task_type.endswith("_prep"),
        ),
        "recommended_next_action": str(profile.get("recommended_next_action") or "").strip(),
        "missing_criteria": missing_criteria,
        "blockers": blockers,
        "milestone_mastered": mastery >= 0.95,
        "provenance": ["profile"],
    }


def _base_item_from_progression(row: dict[str, Any]) -> dict[str, Any] | None:
    skill_id = str(row.get("node_id") or row.get("competency_node") or "").strip()
    if not skill_id:
        return None
    module_id = _career_module_for_node(skill_id)
    if not module_id:
        return None
    readiness = _progression_readiness(row)
    mastery = 1.0 if row.get("node_mastered") else _safe_score(row.get("ema") or row.get("mastery"))
    confidence = 0.85 if row.get("node_mastered") else 0.7 if row.get("node_completed") else 0.55
    status = _gap_status(readiness=readiness, mastery=mastery, confidence=confidence)
    if status == "resolved" and not row.get("node_mastered"):
        status = "improving"
    latest_evidence = _progression_evidence(row)
    gap = str(row.get("last_gap") or "").strip()
    return {
        "skill_id": skill_id,
        "focus_id": skill_id,
        "module_id": module_id,
        "task_type": _prep_task_type_for_module(module_id),
        "status": status,
        "readiness": readiness,
        "confidence": confidence,
        "attempts": int(row.get("attempts") or 0),
        "gap": gap,
        "latest_evidence": latest_evidence,
        "recommended_next_action": gap,
        "missing_criteria": [],
        "blockers": [],
        "milestone_mastered": bool(row.get("node_mastered")),
        "provenance": ["progression"],
    }


def _durable_event_skill_id(event: dict[str, Any]) -> str:
    skill_id = str(event.get("skill_id") or event.get("node_id") or "").strip()
    if not skill_id or _LEGACY_HASHED_REPORT_SKILL_RE.fullmatch(skill_id):
        return ""
    source = str(event.get("source") or "").strip()
    task_type = str(event.get("task_type") or "").strip()
    if source in {"test_report", "prep_report"} or task_type.endswith("_test"):
        return skill_id if skill_for_id(skill_id) is not None else ""
    return skill_id


def _chronological_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order durable rows for reduction without changing the graph API contract."""
    if not any(row.get("occurred_at") is not None for row in rows):
        return rows

    def occurred_at_key(indexed: tuple[int, dict[str, Any]]) -> tuple[str, int]:
        index, row = indexed
        value = row.get("occurred_at")
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        return str(value or ""), index

    return [
        row
        for _index, row in sorted(enumerate(rows), key=occurred_at_key)
    ]


def _event_observation(event: dict[str, Any]) -> dict[str, Any] | None:
    skill_id = _durable_event_skill_id(event)
    if not skill_id:
        return None
    evidence = event.get("evidence_json") if isinstance(event.get("evidence_json"), dict) else {}
    source = str(event.get("source") or "").strip()
    task_type = str(event.get("task_type") or "").strip()
    quote = _latest_evidence(
        evidence,
        allow_answer_excerpt=source == "prep_turn" and task_type.endswith("_prep"),
    )
    proof = evidence.get("proof") if isinstance(evidence.get("proof"), dict) else {}
    grounded = bool(quote) and proof.get("grounded") is not False
    if not grounded:
        return None

    status = str(evidence.get("gap_status") or "").strip()
    required_missing = _clean_string_list(evidence.get("required_missing"), limit=5)
    blockers = _clean_string_list(evidence.get("blockers") or event.get("blockers"), limit=5)
    pass_eligible = evidence.get("pass_eligible")
    if source in {"test_report", "prep_report"}:
        kind = "failure" if status == "active_gap" else "positive" if status in {"improving", "resolved"} else ""
    elif source == "prep_turn":
        if pass_eligible is True and not required_missing and not blockers:
            kind = "positive"
        elif pass_eligible is False or required_missing or blockers:
            kind = "failure"
        else:
            kind = "positive" if _safe_score(event.get("score")) >= 0.8 else "failure"
    else:
        kind = (
            "failure"
            if status == "active_gap" or _safe_score(event.get("score")) < 0.65
            else "positive"
            if status in {"improving", "resolved"} or _safe_score(event.get("score")) >= 0.8
            else ""
        )
    if not kind:
        return None
    focus_id = str(evidence.get("recommended_node_id") or "").strip()
    if focus_id and skill_for_id(focus_id) is None:
        focus_id = ""
    if not focus_id:
        focus_id = focus_node_for_observation(task_type, skill_id, event.get("gap"))
    gap = str(event.get("gap") or "").strip()
    if skill_id == "int_03_weakness_framing" and not required_missing and not blockers:
        normalized_answer = " ".join(str(evidence.get("answer_excerpt") or "").split()).lower()
        grounded_met_ids: set[str] = set()
        for row in evidence.get("criteria") or []:
            item = _row_dict(row)
            criterion_quote = _quote(item.get("evidence_quote"))
            if (
                item.get("met") is True
                and criterion_quote
                and criterion_quote.lower() in normalized_answer
            ):
                grounded_met_ids.add(
                    str(item.get("id") or item.get("criterion_id") or "").strip()
                )
        weakness_ids = {
            "real_weakness",
            "mitigation_habit",
            "progress_evidence",
            "non_self_sabotage",
        }
        stale_focus_terms = (
            "frame the weakness",
            "honest weakness",
            "disqualif",
            "self-sabot",
            "humble-brag",
            "real weakness",
            "mitigation habit",
            "corrective habit",
            "progress evidence",
            "concrete progress",
        )
        if weakness_ids.issubset(grounded_met_ids) and any(
            term in gap.lower() for term in stale_focus_terms
        ):
            gap = (
                "Pressure-test the answer against one follow-up about stakeholder "
                "pushback or what changed after the rollout."
            )
    return {
        "skill_id": skill_id,
        "focus_id": focus_id,
        "kind": kind,
        "quote": quote,
        "score": _safe_score(event.get("score")),
        "confidence": _safe_score(event.get("confidence")),
        "session_id": str(event.get("session_id") or event.get("source_event_key") or ""),
        "source_event_key": str(event.get("source_event_key") or ""),
        "source": source or "legacy_event",
        "attempt_type": str(event.get("attempt_type") or "").strip(),
        "task_type": task_type,
        "module_id": str(event.get("module_id") or "").strip(),
        "gap": gap,
        "missing_criteria": required_missing,
        "blockers": blockers,
    }


def _distinct_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    distinct: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for observation in observations:
        identity = (
            str(observation.get("session_id") or ""),
            str(observation.get("quote") or "").lower(),
        )
        if identity in seen:
            continue
        seen.add(identity)
        distinct.append(observation)
    return distinct


def _reduce_skill_item(
    skill_id: str,
    *,
    base: dict[str, Any] | None,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    item = dict(base or {"skill_id": skill_id})
    observations = [obs for event in events if (obs := _event_observation(event)) is not None]
    latest = observations[-1] if observations else None
    milestone_mastered = bool(item.get("milestone_mastered"))

    latest_failure_index = max(
        (index for index, obs in enumerate(observations) if obs["kind"] == "failure"),
        default=-1,
    )
    recoveries = _distinct_observations([
        obs
        for obs in observations[latest_failure_index + 1:]
        if obs["kind"] == "positive" and obs.get("attempt_type") in _GROUNDING_ATTEMPT_TYPES
    ])
    current_failures: list[dict[str, Any]] = []
    for observation in reversed(observations):
        if observation["kind"] == "positive":
            break
        if observation["kind"] == "failure":
            current_failures.append(observation)
    current_failures = _distinct_observations(list(reversed(current_failures)))
    review_failures = [
        observation
        for observation in current_failures
        if observation.get("attempt_type") in _GROUNDING_ATTEMPT_TYPES
    ]

    if milestone_mastered and len(review_failures) >= 2:
        status = "needs_review"
    elif milestone_mastered:
        status = "mastered"
    elif latest and latest["kind"] == "failure":
        status = "active_gap"
    elif latest_failure_index >= 0 and len(recoveries) >= 2:
        status = "resolved"
    elif latest and latest["kind"] == "positive":
        status = "improving"
    else:
        status = str(item.get("status") or "active_gap")
        if status in {"resolved", "mastered"}:
            status = "improving"

    if latest:
        item.update({
            "module_id": latest.get("module_id") or item.get("module_id", ""),
            "task_type": latest.get("task_type") or item.get("task_type", ""),
            "focus_id": latest.get("focus_id") or item.get("focus_id") or "",
            "readiness": latest["score"],
            "confidence": latest["confidence"] or item.get("confidence", 0.0),
            "gap": latest.get("gap") or item.get("gap") or "",
            "recommended_next_action": (
                latest.get("gap") or item.get("recommended_next_action") or ""
            ),
            "latest_evidence": latest["quote"],
            "missing_criteria": latest["missing_criteria"],
            "blockers": latest["blockers"],
        })
    item.setdefault("module_id", "")
    item.setdefault("focus_id", "")
    item.setdefault("task_type", "")
    item.setdefault("readiness", 0.0)
    item.setdefault("confidence", 0.0)
    item.setdefault("gap", "")
    item.setdefault("latest_evidence", "")
    item.setdefault("recommended_next_action", "")
    item.setdefault("missing_criteria", [])
    item.setdefault("blockers", [])
    item["attempts"] = max(
        int(item.get("attempts") or 0),
        len({str(event.get("source_event_key") or index) for index, event in enumerate(events)}),
    )
    item.update({
        "status": status,
        "current_competence_status": status,
        "milestone_mastered": milestone_mastered,
        "repeat_count": len(current_failures),
        "historical_failure_count": sum(obs["kind"] == "failure" for obs in observations),
        "growth": {
            "grounded_recovery_count": sum(obs["kind"] == "positive" for obs in observations),
            "recoveries_since_latest_failure": len(recoveries),
        },
        "provenance": list(dict.fromkeys([
            *list(item.get("provenance") or []),
            *(obs["source"] for obs in observations),
        ])),
    })
    return item


def scope_career_memory_context(
    memory: dict[str, Any],
    module_id: str,
) -> dict[str, Any]:
    """Project an existing memory payload onto one career module.

    This is also used at the prompt boundary as defense in depth for callers
    that still hold an older, broad memory payload.
    """
    scoped_buckets: dict[str, list[dict[str, Any]]] = {}
    retained_issue_keys: set[str] = set()
    for key in ("active_gaps", "improving_gaps", "resolved_gaps", "mastered_skills"):
        rows = memory.get(key) if isinstance(memory.get(key), list) else []
        scoped_rows = [
            dict(row)
            for row in rows
            if isinstance(row, dict) and _row_matches_career_module(row, module_id)
        ]
        scoped_buckets[key] = scoped_rows
        for row in scoped_rows:
            # Repeat counts are safe to retain only when keyed by a structurally
            # owned identity. Free-form gap prose can be identical across modes
            # ("Add evidence") and a broad legacy aggregate cannot be split later.
            for identity_key in ("skill_id", "focus_id"):
                identity = str(row.get(identity_key) or "").strip()
                if identity:
                    retained_issue_keys.add(identity)

    repeated = memory.get("repeated_issue_counts")
    scoped_repeated = {
        str(key): value
        for key, value in (repeated.items() if isinstance(repeated, dict) else [])
        if str(key) in retained_issue_keys
    }
    reports = memory.get("recent_reports") if isinstance(memory.get("recent_reports"), list) else []
    scoped_reports = [
        dict(report)
        for report in reports
        if isinstance(report, dict) and _row_matches_career_module(report, module_id)
    ]
    return {
        **scoped_buckets,
        "repeated_issue_counts": scoped_repeated,
        "recent_reports": scoped_reports,
    }


def build_career_memory_context(
    graph: dict[str, Any],
    module_id: str = "",
) -> dict[str, Any]:
    """Compress durable career evidence into prompt-safe adaptive memory."""
    raw_profiles = [
        row for row in graph.get("profiles") or []
        if isinstance(row, dict) and str(row.get("domain") or "") == CAREER_DOMAIN
        and _row_matches_career_module(row, module_id)
    ]
    reports = [
        row for row in graph.get("reports") or []
        if isinstance(row, dict) and _row_matches_career_module(row, module_id)
    ]
    profiles = _current_profile_rows(raw_profiles, reports)
    events = _chronological_events([
        row for row in graph.get("events") or []
        if isinstance(row, dict) and str(row.get("domain") or "") == CAREER_DOMAIN
        and _row_matches_career_module(row, module_id)
    ])
    progression = [
        row for row in graph.get("progression") or []
        if isinstance(row, dict) and _row_matches_career_module(row, module_id)
    ]

    base_by_skill: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        item = _base_item_from_profile(profile)
        if not item:
            continue
        base_by_skill[str(item["skill_id"])] = item

    for row in progression:
        progression_item = _base_item_from_progression(row)
        if not progression_item:
            continue
        skill_id = str(progression_item["skill_id"])
        existing = base_by_skill.get(skill_id)
        if existing is None:
            base_by_skill[skill_id] = progression_item
            continue
        existing["attempts"] = max(
            int(existing.get("attempts") or 0),
            int(progression_item.get("attempts") or 0),
        )
        existing["milestone_mastered"] = bool(
            existing.get("milestone_mastered") or progression_item.get("milestone_mastered")
        )
        if not existing.get("latest_evidence"):
            existing["latest_evidence"] = progression_item.get("latest_evidence", "")
        existing["provenance"] = list(dict.fromkeys([
            *list(existing.get("provenance") or []),
            "progression",
        ]))

    events_by_skill: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        skill_id = _durable_event_skill_id(event)
        if skill_id:
            events_by_skill.setdefault(skill_id, []).append(event)

    buckets: dict[str, list[dict[str, Any]]] = {
        "active_gap": [],
        "improving": [],
        "resolved": [],
        "mastered": [],
    }
    repeated_issue_counts: dict[str, int] = {}
    for skill_id in dict.fromkeys([*base_by_skill, *events_by_skill]):
        item = _reduce_skill_item(
            skill_id,
            base=base_by_skill.get(skill_id),
            events=events_by_skill.get(skill_id, []),
        )
        repeat_count = int(item.get("repeat_count") or 0)
        if repeat_count:
            repeated_issue_counts[skill_id] = repeat_count
        status = str(item.get("status") or "active_gap")
        bucket = "active_gap" if status == "needs_review" else status
        buckets[bucket].append(item)

    for items in buckets.values():
        items.sort(
            key=lambda row: (
                -int(row.get("repeat_count") or 0),
                float(row.get("readiness") or 0.0),
            )
        )

    recent_reports: list[dict[str, Any]] = []
    usable_reports = [
        report for report in reports
        if str(report.get("status") or "").strip()
        not in {"invalid_simulation", "insufficient_evidence"}
    ]
    for report in usable_reports[:5]:
        recent_reports.append({
            "task_type": str(report.get("task_type") or ""),
            "status": str(report.get("status") or ""),
            "score": _safe_score(report.get("score")),
            "summary": str(report.get("summary") or "")[:360],
            "recommended_actions": list(report.get("recommended_actions_json") or [])[:3],
        })

    return {
        "active_gaps": buckets["active_gap"][:6],
        "improving_gaps": buckets["improving"][:6],
        "resolved_gaps": buckets["resolved"][:6],
        "mastered_skills": buckets["mastered"][:6],
        "repeated_issue_counts": repeated_issue_counts,
        "recent_reports": recent_reports,
    }


def _public_context(state: dict[str, Any]) -> dict[str, Any]:
    career = dict(state.get("career_context") or {})
    scenario = dict(state.get("scenario_config") or {})
    gd_topics = career.get("gd_topics")
    topic_from_list = gd_topics[0] if isinstance(gd_topics, list) and gd_topics else ""
    return {
        "role": career.get("primary_role") or scenario.get("target_role") or "",
        "module": state.get("module_id") or "",
        "topic": (
            career.get("gd_topic")
            or topic_from_list
        )
        or scenario.get("resolved_topic")
        or scenario.get("topic")
        or "",
    }


class CareerLearningProfileService:
    """Append learning evidence and keep fast user/skill projections current."""

    def __init__(self, store: Any):
        self.store = store

    async def record_prep_turn_evaluation(
        self,
        *,
        evaluation_id: str,
        state: dict[str, Any],
        rubric_result: dict[str, Any],
        tutor_plan: dict[str, Any],
        user_answer: str,
        attempt_index: int,
    ) -> None:
        user_id = str(state.get("user_id") or "")
        node_id = str(state.get("competency_node") or "")
        task_type = str(state.get("task_type") or "")
        score = _safe_score(rubric_result.get("effective_score", rubric_result.get("raw_score")))
        criteria = list(rubric_result.get("criteria") or [])
        blockers = list(rubric_result.get("blockers") or [])
        errors = list(rubric_result.get("errors") or [])
        required_missing = _clean_string_list(rubric_result.get("required_missing"), limit=5)
        gap = str(rubric_result.get("next_focus") or "")
        confidence = 0.45 if blockers else 0.75
        if rubric_result.get("pass_eligible"):
            confidence = max(confidence, 0.8)
        raw_strengths = list(rubric_result.get("strengths") or [])
        proof_blocked = bool(blockers) or any(
            "missing required rubric proof" in str(error).lower()
            for error in errors
        )
        profile_strengths = [] if proof_blocked else raw_strengths
        latest_quote = _first_criterion_quote(criteria, user_answer)

        event = {
            "source_event_key": f"turn_evaluation:{evaluation_id}",
            "user_id": user_id,
            "domain": CAREER_DOMAIN,
            "task_type": task_type,
            "module_id": str(state.get("module_id") or ""),
            "session_id": str(state.get("session_id") or ""),
            "node_id": node_id,
            "skill_id": node_id,
            "source": "prep_turn",
            "attempt_type": str(rubric_result.get("attempt_type") or "independent"),
            "score": score,
            "confidence": confidence,
            "criteria_json": criteria,
            "evidence_json": {
                "criteria": criteria,
                "answer_excerpt": str(user_answer or "")[:500],
                "latest_quote": latest_quote,
                "pass_eligible": bool(rubric_result.get("pass_eligible")),
                "mastery_eligible": bool(rubric_result.get("mastery_eligible")),
                "required_missing": required_missing,
                "blockers": _clean_string_list(blockers, limit=5),
                "proof": {
                    "grounded": bool(latest_quote or str(user_answer or "").strip()),
                    "criterion_quote_count": sum(
                        bool(_quote(_row_dict(criterion).get("evidence_quote")))
                        for criterion in criteria
                    ),
                },
                "tutor_plan": dict(tutor_plan or {}),
            },
            "blockers": blockers,
            "gap": gap,
            "scenario_json": _public_context(state),
            "caveats": errors,
            "model_name": None,
            "prompt_version": "prep-eval-v1",
        }
        profile = {
            "user_id": user_id,
            "domain": CAREER_DOMAIN,
            "skill_id": node_id,
            "module_id": str(state.get("module_id") or ""),
            "task_type": task_type,
            "readiness": score,
            "mastery": 1.0 if state.get("node_mastered") else 0.0,
            "confidence": confidence,
            "attempts": max(1, int(attempt_index or 0)),
            "strengths_json": profile_strengths,
            "gaps_json": [gap] if gap else [],
            "evidence_json": {
                "latest_event": event["source_event_key"],
                "criteria": criteria,
                "answer_excerpt": str(user_answer or "")[:500],
                "blockers": blockers,
                "caveats": errors,
                "latest_quote": latest_quote,
                "pass_eligible": bool(rubric_result.get("pass_eligible")),
                "mastery_eligible": bool(rubric_result.get("mastery_eligible")),
                "required_missing": required_missing,
                "proof": {
                    "grounded": bool(latest_quote or str(user_answer or "").strip()),
                },
            },
            "recommended_next_action": gap,
            "source_summary": _first(profile_strengths, gap),
        }
        await self.store.record_learning_event_and_update_profile(
            event=event,
            profile=profile,
        )

    async def record_session_report(
        self,
        *,
        user_id: str,
        session_id: str,
        report_type: str,
        task_type: str,
        module_id: str,
        report: dict[str, Any],
    ) -> None:
        score = _safe_score(report.get("score"))
        legacy_caveats = list(report.get("assessment_caveats") or report.get("caveats") or [])
        learner_caveats = list(report.get("learner_assessment_caveats") or [])
        integrity_notes = list(report.get("simulator_integrity_notes") or [])
        for item in legacy_caveats:
            text = str(item or "").strip()
            if text and not text.startswith("Simulator caveat:") and text not in learner_caveats:
                learner_caveats.append(text)
        learner_caveats = list(dict.fromkeys(str(item).strip() for item in learner_caveats if str(item).strip()))
        simulator_notes: list[str] = []
        for item in integrity_notes:
            text = str(item or "").strip()
            if text and text not in simulator_notes:
                simulator_notes.append(text)
        caveats = list(learner_caveats)
        caveats.extend(f"Simulator integrity: {item}" for item in simulator_notes)
        explicit_validity = str(report.get("validity_status") or "").strip()
        if explicit_validity in {"invalid_simulation", "insufficient_evidence", "partial"}:
            status = explicit_validity
        else:
            status = "partial" if learner_caveats else str(report.get("status") or "final")
        canonical_gaps = canonicalize_report_gaps(
            task_type,
            skill_gaps=report.get("skill_gaps") or [],
            observed_skill_gaps=report.get("observed_skill_gaps") or [],
            recommended_next_nodes=report.get("recommended_next_nodes") or [],
            improvements=report.get("improvements") or [],
        )
        unmapped = [
            *[
                dict(item)
                for item in report.get("unmapped_report_observations") or []
                if isinstance(item, dict)
            ],
            *unmapped_report_observations(
                task_type,
                skill_gaps=report.get("skill_gaps") or [],
                observed_skill_gaps=report.get("observed_skill_gaps") or [],
                recommended_next_nodes=report.get("recommended_next_nodes") or [],
                improvements=report.get("improvements") or [],
            ),
        ]
        unmapped = list({
            (str(item.get("raw_skill_id") or ""), str(item.get("label") or "")): item
            for item in unmapped
        }.values())
        gaps = [gap["label"] for gap in canonical_gaps]
        strengths = list(report.get("strengths") or [])
        durable_strengths = strengths if status == "final" and not learner_caveats else []
        recommendations = [gap["recommended_action"] for gap in canonical_gaps]

        await self.store.upsert_session_report(
            report_id=f"report:{session_id}",
            session_id=session_id,
            user_id=user_id,
            report_type=report_type,
            task_type=task_type,
            module_id=module_id,
            status=status,
            score=score,
            readiness_score=_safe_score(report.get("readiness_score", score)),
            summary=str(report.get("summary") or ""),
            strengths_json=strengths,
            gaps_json=gaps,
            evidence_json={
                "role_focus": report.get("role_focus") or "",
                "topic": report.get("topic") or "",
                "scorable_turn_count": report.get("scorable_turn_count") or 0,
                "coverage_map": report.get("coverage_map") or {},
                "subscores": {
                    key: report.get(key)
                    for key in (
                        "clarity_score",
                        "confidence_score",
                        "participation_score",
                        "relevance_score",
                        "language_score",
                    )
                    if report.get(key) is not None
                },
                "evidence_quotes": list(report.get("evidence_quotes") or []),
                "skill_gaps": canonical_gaps,
                "unmapped_report_observations": unmapped,
            },
            recommended_actions_json=recommendations,
            validity_json={
                "caveats": caveats,
                "learner_assessment_caveats": learner_caveats,
                "simulator_integrity_notes": simulator_notes,
                "status": status,
                "scorable_turn_count": report.get("scorable_turn_count") or 0,
                "coverage_map": report.get("coverage_map") or {},
            },
            public_context_json={
                "role_focus": report.get("role_focus") or "",
                "scenario_label": report.get("scenario_label") or "",
                "topic": report.get("topic") or "",
            },
        )

        if status in {"insufficient_evidence", "invalid_simulation"}:
            return

        profile_confidence = 0.85 if status == "final" and not learner_caveats else 0.65
        existing_profiles: dict[str, dict[str, Any]] = {}
        if hasattr(self.store, "get_learning_graph"):
            graph = await self.store.get_learning_graph(user_id)
            existing_profiles = {
                str(row.get("skill_id") or ""): row
                for row in graph.get("profiles") or []
                if isinstance(row, dict)
                and str(row.get("domain") or "") == CAREER_DOMAIN
            }
        profile_rows: list[dict[str, Any]] = []
        for gap in canonical_gaps:
            skill_id = gap["skill_id"]
            gap_status = gap["status"]
            if gap_status == "resolved" and not gap["evidence_quote"]:
                gap_status = "improving"
            per_skill_score = _report_skill_score(score, {**gap, "status": gap_status})
            previous = existing_profiles.get(skill_id, {})
            previous_evidence = (
                previous.get("evidence_json")
                if isinstance(previous.get("evidence_json"), dict)
                else {}
            )
            report_history = [
                dict(item)
                for item in previous_evidence.get("report_history") or []
                if isinstance(item, dict)
            ]
            previous_report_id = str(previous_evidence.get("latest_report") or "").strip()
            if not report_history and previous_report_id:
                report_history.append({
                    "report_id": previous_report_id,
                    "status": str(previous_evidence.get("gap_status") or "active_gap"),
                    "evidence_quote": str(previous_evidence.get("latest_quote") or ""),
                    "score": _safe_score(previous.get("readiness")),
                })
            history_item = {
                "report_id": f"report:{session_id}",
                "status": gap_status,
                "evidence_quote": gap["evidence_quote"],
                "score": per_skill_score,
            }
            report_already_seen = any(
                item.get("report_id") == history_item["report_id"]
                for item in report_history
            )
            if not report_already_seen:
                report_history.append(history_item)
            event_key = f"session_report:{session_id}:{skill_id}"
            await self.store.record_learning_event(
                source_event_key=event_key,
                user_id=user_id,
                domain=CAREER_DOMAIN,
                task_type=task_type,
                module_id=module_id,
                session_id=session_id,
                node_id=skill_id,
                skill_id=skill_id,
                source="test_report" if task_type.endswith("_test") else "prep_report",
                attempt_type=str(gap.get("attempt_type") or "pressure"),
                score=per_skill_score,
                confidence=profile_confidence,
                criteria_json=[],
                evidence_json={
                    "strengths": durable_strengths,
                    "scorable_turn_count": report.get("scorable_turn_count") or 0,
                    "coverage_map": report.get("coverage_map") or {},
                    "evidence_quote": gap["evidence_quote"],
                    "gap_status": gap_status,
                    "pass_eligible": bool(gap["evidence_quote"]) and gap_status != "active_gap",
                    "mastery_eligible": False,
                    "required_missing": [],
                    "proof": {
                        "grounded": bool(gap["evidence_quote"]),
                        "scope": "gap_specific",
                    },
                    "recommended_action": gap["recommended_action"],
                    "recommended_node_id": gap["recommended_node_id"],
                },
                blockers=[],
                gap=gap["label"],
                scenario_json={
                    "role_focus": report.get("role_focus") or "",
                    "topic": report.get("topic") or "",
                },
                caveats=caveats,
                model_name=None,
                prompt_version="simulation-report-v1",
            )
            profile_rows.append({
                "skill_id": skill_id,
                "module_id": module_id,
                "task_type": task_type,
                "readiness": per_skill_score,
                "mastery": 0.0,
                "confidence": profile_confidence,
                "attempts": int(previous.get("attempts") or 0) + (0 if report_already_seen else 1),
                "strengths_json": durable_strengths,
                "gaps_json": [gap["label"]],
                "evidence_json": {
                    "latest_report": f"report:{session_id}",
                    "latest_quote": gap["evidence_quote"],
                    "gap_status": gap_status,
                    "pass_eligible": bool(gap["evidence_quote"]) and gap_status != "active_gap",
                    "mastery_eligible": False,
                    "required_missing": [],
                    "proof": {
                        "grounded": bool(gap["evidence_quote"]),
                        "scope": "gap_specific",
                    },
                    "recommended_node_id": gap["recommended_node_id"],
                    "report_history": report_history[-20:],
                    "caveats": caveats,
                    "learner_assessment_caveats": learner_caveats,
                    "simulator_integrity_notes": simulator_notes,
                    "validity_status": status,
                    "scorable_turn_count": report.get("scorable_turn_count") or 0,
                    "coverage_map": report.get("coverage_map") or {},
                },
                "recommended_next_action": gap["recommended_action"],
                "source_summary": str(report.get("summary") or ""),
            })

        if hasattr(self.store, "reconcile_learner_skill_profiles_for_report"):
            await self.store.reconcile_learner_skill_profiles_for_report(
                user_id=user_id,
                domain=CAREER_DOMAIN,
                task_type=task_type,
                report_id=f"report:{session_id}",
                profiles=profile_rows,
            )
        else:
            for profile_row in profile_rows:
                await self.store.upsert_learner_skill_profile(
                    user_id=user_id,
                    domain=CAREER_DOMAIN,
                    **profile_row,
                )

    async def get_learning_graph(self, user_id: str) -> dict[str, Any]:
        if hasattr(self.store, "get_learning_graph"):
            graph = await self.store.get_learning_graph(user_id)
        else:
            graph = {"profiles": [], "reports": [], "events": []}
        if "progression" not in graph and hasattr(self.store, "get_progression"):
            graph = {**graph, "progression": await self.store.get_progression(user_id)}
        if "active_sessions" not in graph and hasattr(
            self.store,
            "get_active_career_session_runtimes",
        ):
            graph = {
                **graph,
                "active_sessions": await self.store.get_active_career_session_runtimes(user_id),
            }
        elif "active_sessions" not in graph:
            graph = {**graph, "active_sessions": []}
        graph = {
            **graph,
            "profiles": _current_profile_rows(
                [row for row in graph.get("profiles") or [] if isinstance(row, dict)],
                [row for row in graph.get("reports") or [] if isinstance(row, dict)],
            ),
        }
        return graph

    async def get_career_memory_context(
        self,
        user_id: str,
        module_id: str = "",
    ) -> dict[str, Any]:
        graph = await self.get_learning_graph(user_id)
        return build_career_memory_context(graph, module_id=module_id)
