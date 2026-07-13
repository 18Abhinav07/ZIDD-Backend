"""School V2 projection into the global learning profile tables."""

from __future__ import annotations

from typing import Any

from app.services.school_v2_readiness import (
    AttemptEvidence,
    SkillReadinessState,
    classify_skill_status,
)


SCHOOL_DOMAIN = "school"


def _safe_score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value or 0.0))), 4)
    except (TypeError, ValueError):
        return 0.0


class SchoolLearningProfileService:
    """Append School V2 evidence and keep the user/skill projection current."""

    def __init__(self, store: Any):
        self.store = store

    async def record_attempt(
        self,
        *,
        attempt_id: str,
        user_id: str,
        subject_id: str,
        class_no: int,
        session_id: str,
        chapter_id: str,
        node_id: str,
        skill_state: SkillReadinessState,
        evidence: AttemptEvidence,
        criteria_json: list | dict,
        evidence_json: dict,
        source: str = "lesson_attempt",
        task_type: str = "school_lesson",
        gap: str = "",
        model_name: str | None = None,
        prompt_version: str = "school-v2-eval-v1",
    ) -> None:
        status = classify_skill_status(skill_state)
        readiness = (
            skill_state.certified_readiness
            if skill_state.certified_readiness is not None
            else skill_state.practice_readiness
        )
        confidence = skill_state.last_confidence or evidence.evaluator_confidence
        blockers = sorted(set(skill_state.active_blockers or evidence.blockers))
        source_event_key = f"school_v2_attempt:{attempt_id}:{skill_state.skill_id}"
        scenario_json = {
            "subject_id": subject_id,
            "class_no": int(class_no),
            "chapter_id": chapter_id or "",
        }
        event_evidence = {
            **dict(evidence_json or {}),
            "skill_ids": list(evidence.skill_ids),
            "practice_readiness": skill_state.practice_readiness,
            "certified_readiness": skill_state.certified_readiness,
            "ready_source": skill_state.ready_source,
            "status": status,
            "independent_passes": skill_state.independent_passes,
            "transfer_passes": skill_state.transfer_passes,
        }

        await self.store.record_learning_event(
            source_event_key=source_event_key,
            user_id=user_id,
            domain=SCHOOL_DOMAIN,
            task_type=task_type,
            module_id=chapter_id or subject_id,
            session_id=session_id,
            node_id=node_id,
            skill_id=skill_state.skill_id,
            source=source,
            attempt_type=evidence.attempt_type,
            score=_safe_score(evidence.evaluator_score),
            confidence=_safe_score(confidence),
            criteria_json=criteria_json or [],
            evidence_json=event_evidence,
            blockers=blockers,
            gap=gap,
            scenario_json=scenario_json,
            caveats=[],
            model_name=model_name,
            prompt_version=prompt_version,
        )
        await self.store.upsert_learner_skill_profile(
            user_id=user_id,
            domain=SCHOOL_DOMAIN,
            skill_id=skill_state.skill_id,
            module_id=chapter_id or subject_id,
            task_type=task_type,
            readiness=_safe_score(readiness),
            mastery=1.0 if status == "mastered" else 0.0,
            confidence=_safe_score(confidence),
            attempts=max(1, skill_state.total_attempts),
            strengths_json=[],
            gaps_json=[gap] if gap else [],
            evidence_json=event_evidence,
            recommended_next_action=gap,
            source_summary=gap or status,
        )
