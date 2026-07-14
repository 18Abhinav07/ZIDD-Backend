"""Durable School learning-profile projection and next-session memory."""

from __future__ import annotations

from typing import Any

from app.services.school.projection import (
    SchoolAttemptEvidence,
    derive_school_projection_delta,
)
from app.services.school_core.readiness import from_profile_row, to_profile_upsert


SCHOOL_DOMAIN = "school"


def _score(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0


def _latest_ledger_evidence_by_skill(
    graph: dict[str, Any],
) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for raw in graph.get("events") or []:
        if not isinstance(raw, dict) or raw.get("domain") != SCHOOL_DOMAIN:
            continue
        evidence = raw.get("evidence_json")
        evidence = evidence if isinstance(evidence, dict) else {}
        criteria = raw.get("criteria_json")
        criteria = criteria if isinstance(criteria, list) else []
        quote = next(
            (
                str(criterion.get("evidence_quote") or "").strip()
                for criterion in criteria
                if isinstance(criterion, dict)
                and str(criterion.get("evidence_quote") or "").strip()
                not in {"", "(empty answer)"}
            ),
            "",
        )
        if not quote:
            continue
        skill_ids = [
            str(value).strip()
            for value in evidence.get("skill_ids") or []
            if str(value).strip()
        ]
        if not skill_ids and str(raw.get("skill_id") or "").strip():
            skill_ids = [str(raw["skill_id"]).strip()]
        for skill_id in skill_ids:
            if skill_id in latest:
                continue
            latest[skill_id] = {
                "latest_evidence": quote[:320],
                "last_attempt_type": str(raw.get("attempt_type") or ""),
                "last_chapter_id": str(
                    evidence.get("chapter_id") or raw.get("module_id") or ""
                ),
            }
    return latest


def build_school_memory_context(graph: dict[str, Any]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "active_gaps": [],
        "improving_gaps": [],
        "strong_skills": [],
        "mastered_skills": [],
    }
    ledger_evidence = _latest_ledger_evidence_by_skill(graph)
    for raw in graph.get("profiles") or []:
        if not isinstance(raw, dict) or raw.get("domain") != SCHOOL_DOMAIN:
            continue
        skill_id = str(raw.get("skill_id") or "").strip()
        if not skill_id:
            continue
        canonical_profile = to_profile_upsert(from_profile_row(raw))
        readiness = _score(canonical_profile["readiness"])
        mastery = _score(canonical_profile["mastery"])
        gaps = [str(value).strip() for value in raw.get("gaps_json") or [] if str(value).strip()]
        evidence = raw.get("evidence_json") if isinstance(raw.get("evidence_json"), dict) else {}
        latest_evidence = ledger_evidence.get(skill_id) or {}
        skill_status = str(canonical_profile["skill_status"])
        if skill_status == "mastered":
            bucket = "mastered_skills"
        elif skill_status == "ready":
            bucket = "strong_skills"
        elif skill_status == "practice_ready":
            bucket = "improving_gaps"
        else:
            bucket = "active_gaps"
        buckets[bucket].append({
            "skill_id": skill_id,
            "readiness": readiness,
            "mastery": mastery,
            "confidence": _score(raw.get("confidence")),
            "attempts": int(raw.get("attempts") or 0),
            "gap": gaps[0] if gaps else "",
            "latest_evidence": str(
                latest_evidence.get("latest_evidence")
                or evidence.get("latest_quote")
                or ""
            )[:320],
            "recommended_next_action": str(raw.get("recommended_next_action") or "")[:240],
            "last_attempt_type": str(
                latest_evidence.get("last_attempt_type")
                or evidence.get("attempt_type")
                or ""
            ),
            "last_chapter_id": str(
                latest_evidence.get("last_chapter_id")
                or evidence.get("chapter_id")
                or ""
            ),
        })
    for values in buckets.values():
        values.sort(key=lambda row: (row["readiness"], -row["attempts"], row["skill_id"]))
    return {key: values[:8] for key, values in buckets.items()}


class SchoolLearningProfileService:
    def __init__(self, store: Any):
        self.store = store

    async def get_memory_context(self, user_id: str) -> dict[str, Any]:
        graph = await self.store.get_school_learning_graph(user_id)
        return build_school_memory_context(graph)

    async def record_curriculum_attempt(
        self,
        *,
        user_id: str,
        session_id: str,
        chapter_id: str,
        level_id: str,
        focus: str,
        skill_ids: list[str],
        attempt_type: str,
        score: float,
        confidence: float,
        criteria: list[dict[str, Any]],
        blockers: list[str],
        answer_excerpt: str,
        attempt_passed: bool,
        chapter_certified: bool,
        preserve_latest_evidence: bool = False,
    ) -> None:
        graph = await self.store.get_school_learning_graph(user_id)
        unique_skill_ids = list(dict.fromkeys(skill_id for skill_id in skill_ids if skill_id))
        projection = derive_school_projection_delta(
            SchoolAttemptEvidence(
                session_id=session_id,
                chapter_id=chapter_id,
                level_id=level_id,
                module_id=chapter_id,
                task_type="school_rebuild_curriculum",
                focus=focus,
                skill_ids=tuple(unique_skill_ids),
                attempt_type=attempt_type,
                score=_score(score),
                confidence=_score(confidence),
                criteria=tuple(criteria),
                blockers=tuple(blockers),
                answer_excerpt=("" if preserve_latest_evidence else str(answer_excerpt or "")[:320]),
                attempt_passed=bool(attempt_passed),
                certified_skill_scores=(
                    {skill_id: _score(score) for skill_id in unique_skill_ids}
                    if chapter_certified
                    else {}
                ),
                preserve_latest_evidence=preserve_latest_evidence,
            ),
            [
                profile
                for profile in graph.get("profiles") or []
                if isinstance(profile, dict)
                and profile.get("domain") == SCHOOL_DOMAIN
            ],
        )
        await self._upsert_projection(user_id, projection)

    async def _upsert_projection(
        self,
        user_id: str,
        projection: list[dict[str, Any]],
    ) -> None:
        for row in projection:
            await self.store.upsert_learner_skill_profile(
                user_id=user_id,
                domain=str(row["domain"]),
                skill_id=str(row["skill_id"]),
                module_id=str(row["module_id"]),
                task_type=str(row["task_type"]),
                mastery=float(row["mastery"]),
                readiness=float(row["readiness"]),
                confidence=float(row["confidence"]),
                attempts=int(row["attempts"]),
                strengths_json=list(row["strengths_json"]),
                gaps_json=list(row["gaps_json"]),
                evidence_json=dict(row["evidence_json"]),
                recommended_next_action=str(row["recommended_next_action"]),
                source_summary=str(row["source_summary"]),
            )

    async def record_chapter_certification(
        self,
        *,
        user_id: str,
        session_id: str,
        chapter_id: str,
        skill_scores: dict[str, float],
    ) -> None:
        """Project the completed assessment's aggregate evidence for every skill."""

        certified_skill_scores = {
            cleaned_skill_id: _score(raw_score)
            for skill_id, raw_score in skill_scores.items()
            if (cleaned_skill_id := str(skill_id).strip())
        }
        if not certified_skill_scores:
            return
        graph = await self.store.get_school_learning_graph(user_id)
        projection = derive_school_projection_delta(
            SchoolAttemptEvidence(
                session_id=session_id,
                chapter_id=chapter_id,
                level_id="chapter_assessment",
                module_id=chapter_id,
                task_type="school_rebuild_curriculum",
                focus="chapter assessment reconciliation",
                skill_ids=(),
                attempt_type="chapter_check",
                score=0.0,
                confidence=1.0,
                criteria=(),
                blockers=(),
                answer_excerpt="",
                attempt_passed=False,
                certified_skill_scores=certified_skill_scores,
                preserve_latest_evidence=True,
            ),
            [
                profile
                for profile in graph.get("profiles") or []
                if isinstance(profile, dict)
                and profile.get("domain") == SCHOOL_DOMAIN
            ],
        )
        await self._upsert_projection(user_id, projection)
