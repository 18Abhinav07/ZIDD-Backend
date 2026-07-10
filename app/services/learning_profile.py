"""Canonical learning-profile projection for career prep/test evidence."""
from __future__ import annotations

import hashlib
import re
from typing import Any

from app.content.registry import module_of


CAREER_DOMAIN = "career"
SCHOOL_ADAPTER_DOMAIN = "school_adapter"

_MODE_INAPPROPRIATE_GAP_TERMS = {
    "interview_test": (
        "group discussion",
        "other participants",
        "other speakers",
        "synthesizing others",
        "multiple viewpoints",
        "panelist",
        "consensus",
        "claiming the floor",
        "dominant speaker",
        "quiet participant",
        "rebuttal",
        "steer discussion",
        "steering discussion",
        "build on others",
    ),
    "gd_test": (
        "star answer",
        "star structure",
        "interviewer",
        "candidate",
        "hiring manager",
        "behavioral answer",
        "role fit",
        "resume",
        "job interview",
    ),
}


def _mode_inappropriate_gap(task_type: str, gap: str) -> bool:
    normalized = " ".join(str(gap or "").lower().split())
    return any(
        term in normalized
        for term in _MODE_INAPPROPRIATE_GAP_TERMS.get(task_type, ())
    )


def _sanitize_report_gaps(task_type: str, values: Any) -> list[str]:
    return [
        gap
        for gap in _clean_string_list(values, limit=8, item_limit=180)
        if not _mode_inappropriate_gap(task_type, gap)
    ]


def _canonical_report_skill_id(task_type: str, gap: str) -> str:
    normalized = " ".join(str(gap or "").lower().split())
    slug = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")[:64] or "focus"
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:8]
    return f"{task_type}:{slug}:{digest}"


def _current_profile_rows(
    profiles: list[dict[str, Any]],
    reports: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    latest_usable_report_by_task: dict[str, str] = {}
    for report in reports:
        task_type = str(report.get("task_type") or "").strip()
        status = str(report.get("status") or "").strip()
        if (
            task_type
            and task_type not in latest_usable_report_by_task
            and status not in {"insufficient_evidence", "invalid_simulation"}
        ):
            latest_usable_report_by_task[task_type] = str(report.get("report_id") or "").strip()

    current: list[dict[str, Any]] = []
    for profile in profiles:
        task_type = str(profile.get("task_type") or "").strip()
        skill_id = str(profile.get("skill_id") or "").strip()
        if not skill_id or skill_id == "insufficient_assessment_evidence":
            continue
        gap_values = profile.get("gaps_json") if isinstance(profile.get("gaps_json"), list) else []
        display_gap = _first([*gap_values, skill_id])
        if _mode_inappropriate_gap(task_type, display_gap):
            continue
        if task_type.endswith("_test"):
            evidence = profile.get("evidence_json") if isinstance(profile.get("evidence_json"), dict) else {}
            profile_report_id = str(evidence.get("latest_report") or "").strip()
            latest_report_id = latest_usable_report_by_task.get(task_type, "")
            if latest_report_id and profile_report_id != latest_report_id:
                continue
        current.append(profile)
    return current


def _safe_score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value or 0.0))), 4)
    except (TypeError, ValueError):
        return 0.0


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


def _first_criterion_quote(criteria: list[Any], fallback: str = "") -> str:
    normalized_fallback = " ".join(str(fallback or "").split()).lower()
    for raw in criteria:
        row = _row_dict(raw)
        quote = " ".join(str(row.get("evidence_quote") or "").split())
        if (
            row.get("met") is True
            and quote
            and quote.lower() in normalized_fallback
        ):
            return quote[:320]
    return ""


def _latest_evidence(evidence: Any) -> str:
    if not isinstance(evidence, dict):
        return ""
    direct = str(evidence.get("latest_quote") or evidence.get("answer_excerpt") or "").strip()
    if direct:
        return direct[:320]
    for key in ("evidence_quotes", "quotes"):
        values = evidence.get(key)
        if isinstance(values, list):
            for item in values:
                text = str(item or "").strip()
                if text:
                    return text[:320]
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
        for item in evidence:
            text = str(item or "").strip()
            if text:
                return text[:320]
    return str(row.get("last_gap") or "").strip()[:320]


def _progression_readiness(row: dict[str, Any]) -> float:
    for key in ("best_independent_score", "best_ema", "ema", "mastery"):
        value = _safe_score(row.get(key))
        if value > 0:
            return value
    return 0.0


def _memory_item_from_profile(
    profile: dict[str, Any],
    *,
    repeated_issue_counts: dict[str, int],
    latest_event_quote_by_gap: dict[str, str],
) -> tuple[str, dict[str, Any]] | None:
    skill_id = str(profile.get("skill_id") or "").strip()
    if not skill_id:
        return None
    task_type = str(profile.get("task_type") or "").strip()
    if _mode_inappropriate_gap(task_type, skill_id):
        return None
    readiness = _safe_score(profile.get("readiness"))
    mastery = _safe_score(profile.get("mastery"))
    confidence = _safe_score(profile.get("confidence"))
    status = _gap_status(readiness=readiness, mastery=mastery, confidence=confidence)
    gaps = [str(item).strip() for item in profile.get("gaps_json") or [] if str(item).strip()]
    evidence_json = profile.get("evidence_json") if isinstance(profile.get("evidence_json"), dict) else {}
    missing_criteria = _clean_string_list(
        evidence_json.get("required_missing") or evidence_json.get("missing_criteria"),
        limit=5,
    )
    blockers = _clean_string_list(evidence_json.get("blockers"), limit=5)
    latest_evidence = (
        _latest_evidence(evidence_json)
        or latest_event_quote_by_gap.get(skill_id, "")
        or _first(gaps)
    )
    return status, {
        "skill_id": skill_id,
        "module_id": str(profile.get("module_id") or ""),
        "task_type": task_type,
        "status": status,
        "readiness": readiness,
        "confidence": confidence,
        "attempts": int(profile.get("attempts") or 0),
        "gap": _first(gaps, skill_id),
        "latest_evidence": latest_evidence,
        "recommended_next_action": str(profile.get("recommended_next_action") or "").strip(),
        "missing_criteria": missing_criteria,
        "blockers": blockers,
        "repeat_count": repeated_issue_counts.get(skill_id, 0),
    }


def _memory_item_from_progression(
    row: dict[str, Any],
    *,
    repeated_issue_counts: dict[str, int],
) -> tuple[str, dict[str, Any]] | None:
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
    latest_evidence = _progression_evidence(row)
    gap = str(row.get("last_gap") or "").strip() or skill_id
    return status, {
        "skill_id": skill_id,
        "module_id": module_id,
        "task_type": _prep_task_type_for_module(module_id),
        "status": status,
        "readiness": readiness,
        "confidence": confidence,
        "attempts": int(row.get("attempts") or 0),
        "gap": gap,
        "latest_evidence": latest_evidence or gap,
        "recommended_next_action": gap,
        "missing_criteria": [],
        "blockers": [],
        "repeat_count": repeated_issue_counts.get(skill_id, 0),
    }


def build_career_memory_context(graph: dict[str, Any]) -> dict[str, Any]:
    """Compress durable career evidence into prompt-safe adaptive memory."""
    raw_profiles = [
        row for row in graph.get("profiles") or []
        if isinstance(row, dict) and str(row.get("domain") or "") == CAREER_DOMAIN
    ]
    reports = [
        row for row in graph.get("reports") or []
        if isinstance(row, dict)
    ]
    profiles = _current_profile_rows(raw_profiles, reports)
    events = [
        row for row in graph.get("events") or []
        if isinstance(row, dict) and str(row.get("domain") or "") == CAREER_DOMAIN
    ]
    progression = [
        row for row in graph.get("progression") or []
        if isinstance(row, dict)
    ]

    repeated_issue_counts: dict[str, int] = {}
    latest_event_quote_by_gap: dict[str, str] = {}
    resolved_issue_streaks: set[str] = set()
    for event in events:
        skill_id = str(event.get("skill_id") or "").strip()
        gap = str(event.get("gap") or "").strip()
        issue_keys = list(dict.fromkeys(key for key in (skill_id, gap) if key))
        if not issue_keys:
            continue
        quote = _latest_evidence(event.get("evidence_json"))
        for issue_key in issue_keys:
            if quote and issue_key not in latest_event_quote_by_gap:
                latest_event_quote_by_gap[issue_key] = quote
            if issue_key in resolved_issue_streaks:
                continue
            if _safe_score(event.get("score")) >= 0.8:
                repeated_issue_counts.setdefault(issue_key, 0)
                resolved_issue_streaks.add(issue_key)
                continue
            repeated_issue_counts[issue_key] = repeated_issue_counts.get(issue_key, 0) + 1

    buckets: dict[str, list[dict[str, Any]]] = {
        "active_gap": [],
        "improving": [],
        "resolved": [],
        "mastered": [],
    }
    profile_skill_ids: set[str] = set()
    for profile in profiles:
        built = _memory_item_from_profile(
            profile,
            repeated_issue_counts=repeated_issue_counts,
            latest_event_quote_by_gap=latest_event_quote_by_gap,
        )
        if not built:
            continue
        status, item = built
        profile_skill_ids.add(str(item["skill_id"]))
        buckets[status].append(item)

    for row in progression:
        built = _memory_item_from_progression(row, repeated_issue_counts=repeated_issue_counts)
        if not built:
            continue
        status, item = built
        if str(item["skill_id"]) in profile_skill_ids:
            continue
        buckets[status].append(item)

    for items in buckets.values():
        items.sort(
            key=lambda row: (
                -int(row.get("repeat_count") or 0),
                float(row.get("readiness") or 0.0),
            )
        )

    recent_reports: list[dict[str, Any]] = []
    for report in reports[:5]:
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
                "required_missing": required_missing,
                "blockers": _clean_string_list(blockers, limit=5),
                "tutor_plan": dict(tutor_plan or {}),
            },
            "blockers": blockers,
            "gap": gap,
            "scenario_json": _public_context(state),
            "caveats": errors,
            "model_name": None,
            "prompt_version": "prep-eval-v1",
        }
        await self.store.record_learning_event(**event)
        await self.store.upsert_learner_skill_profile(
            user_id=user_id,
            domain=CAREER_DOMAIN,
            skill_id=node_id,
            module_id=str(state.get("module_id") or ""),
            task_type=task_type,
            readiness=score,
            mastery=1.0 if state.get("node_mastered") else 0.0,
            confidence=confidence,
            attempts=max(1, int(attempt_index or 0)),
            strengths_json=profile_strengths,
            gaps_json=[gap] if gap else [],
            evidence_json={
                "latest_event": event["source_event_key"],
                "criteria": criteria,
                "blockers": blockers,
                "caveats": errors,
                "latest_quote": latest_quote,
                "required_missing": required_missing,
            },
            recommended_next_action=gap,
            source_summary=_first(profile_strengths, gap),
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
        if explicit_validity:
            status = explicit_validity
        else:
            status = str(report.get("status") or ("partial" if learner_caveats else "final"))
        gaps = _sanitize_report_gaps(
            task_type,
            report.get("observed_skill_gaps") or report.get("improvements") or [],
        )
        strengths = list(report.get("strengths") or [])
        durable_strengths = strengths if status == "final" and not learner_caveats else []
        recommendations = list(report.get("recommended_next_nodes") or report.get("improvements") or [])

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

        tracked_gaps = [str(gap).strip() for gap in gaps if str(gap).strip()]
        profile_confidence = 0.85 if status == "final" and not learner_caveats else 0.65
        profile_rows: list[dict[str, Any]] = []
        for gap in tracked_gaps:
            skill_id = _canonical_report_skill_id(task_type, gap)
            event_key = f"session_report:{session_id}:{skill_id}"
            await self.store.record_learning_event(
                source_event_key=event_key,
                user_id=user_id,
                domain=CAREER_DOMAIN,
                task_type=task_type,
                module_id=module_id,
                session_id=session_id,
                node_id="",
                skill_id=skill_id,
                source="test_report" if task_type.endswith("_test") else "prep_report",
                attempt_type="report",
                score=score,
                confidence=profile_confidence,
                criteria_json=[],
                evidence_json={
                    "summary": report.get("summary") or "",
                    "strengths": durable_strengths,
                    "improvements": list(report.get("improvements") or []),
                    "evidence_quotes": list(report.get("evidence_quotes") or []),
                    "scorable_turn_count": report.get("scorable_turn_count") or 0,
                    "coverage_map": report.get("coverage_map") or {},
                },
                blockers=[],
                gap=gap,
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
                "readiness": score,
                "mastery": 0.0,
                "confidence": profile_confidence,
                "attempts": 1,
                "strengths_json": durable_strengths,
                "gaps_json": [gap],
                "evidence_json": {
                    "latest_report": f"report:{session_id}",
                    "caveats": caveats,
                    "learner_assessment_caveats": learner_caveats,
                    "simulator_integrity_notes": simulator_notes,
                    "validity_status": status,
                    "scorable_turn_count": report.get("scorable_turn_count") or 0,
                    "coverage_map": report.get("coverage_map") or {},
                },
                "recommended_next_action": _first(list(report.get("improvements") or []), gap),
                "source_summary": str(report.get("summary") or ""),
            })

        if hasattr(self.store, "replace_learner_skill_profiles_for_task"):
            await self.store.replace_learner_skill_profiles_for_task(
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
        graph = {
            **graph,
            "profiles": _current_profile_rows(
                [row for row in graph.get("profiles") or [] if isinstance(row, dict)],
                [row for row in graph.get("reports") or [] if isinstance(row, dict)],
            ),
        }
        return graph

    async def get_career_memory_context(self, user_id: str) -> dict[str, Any]:
        graph = await self.get_learning_graph(user_id)
        return build_career_memory_context(graph)
