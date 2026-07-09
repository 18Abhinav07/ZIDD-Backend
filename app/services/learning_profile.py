"""Canonical learning-profile projection for career prep/test evidence."""
from __future__ import annotations

from typing import Any


CAREER_DOMAIN = "career"
SCHOOL_ADAPTER_DOMAIN = "school_adapter"


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
        gap = str(rubric_result.get("next_focus") or "")
        confidence = 0.45 if blockers else 0.75
        if rubric_result.get("pass_eligible"):
            confidence = max(confidence, 0.8)

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
                "tutor_plan": dict(tutor_plan or {}),
            },
            "blockers": blockers,
            "gap": gap,
            "scenario_json": _public_context(state),
            "caveats": list(rubric_result.get("errors") or []),
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
            strengths_json=list(rubric_result.get("strengths") or []),
            gaps_json=[gap] if gap else [],
            evidence_json={
                "latest_event": event["source_event_key"],
                "criteria": criteria,
                "blockers": blockers,
            },
            recommended_next_action=gap,
            source_summary=_first(list(rubric_result.get("strengths") or []), gap),
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
        caveats = list(report.get("assessment_caveats") or report.get("caveats") or [])
        explicit_validity = str(report.get("validity_status") or "").strip()
        if explicit_validity and explicit_validity != "final":
            status = explicit_validity
        else:
            status = str(report.get("status") or ("partial" if caveats else "final"))
        gaps = list(report.get("observed_skill_gaps") or report.get("improvements") or [])
        strengths = list(report.get("strengths") or [])
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
            },
            recommended_actions_json=recommendations,
            validity_json={
                "caveats": caveats,
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

        tracked_gaps = [str(gap).strip() for gap in gaps if str(gap).strip()] or [module_id]
        for gap in tracked_gaps:
            event_key = f"session_report:{session_id}:{gap}"
            await self.store.record_learning_event(
                source_event_key=event_key,
                user_id=user_id,
                domain=CAREER_DOMAIN,
                task_type=task_type,
                module_id=module_id,
                session_id=session_id,
                node_id="",
                skill_id=gap,
                source="test_report" if task_type.endswith("_test") else "prep_report",
                attempt_type="report",
                score=score,
                confidence=0.65 if caveats else 0.85,
                criteria_json=[],
                evidence_json={
                    "summary": report.get("summary") or "",
                    "strengths": strengths,
                    "improvements": list(report.get("improvements") or []),
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
            await self.store.upsert_learner_skill_profile(
                user_id=user_id,
                domain=CAREER_DOMAIN,
                skill_id=gap,
                module_id=module_id,
                task_type=task_type,
                readiness=score,
                mastery=0.0,
                confidence=0.65 if caveats else 0.85,
                attempts=1,
                strengths_json=strengths,
                gaps_json=[gap],
                evidence_json={
                    "latest_report": f"report:{session_id}",
                    "caveats": caveats,
                    "validity_status": status,
                    "scorable_turn_count": report.get("scorable_turn_count") or 0,
                    "coverage_map": report.get("coverage_map") or {},
                },
                recommended_next_action=_first(list(report.get("improvements") or []), gap),
                source_summary=str(report.get("summary") or ""),
            )

    async def get_learning_graph(self, user_id: str) -> dict[str, Any]:
        if hasattr(self.store, "get_learning_graph"):
            return await self.store.get_learning_graph(user_id)
        return {"profiles": [], "reports": [], "events": []}
