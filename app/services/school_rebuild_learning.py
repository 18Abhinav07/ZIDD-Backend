"""Durable School learning-profile projection and next-session memory."""

from __future__ import annotations

from typing import Any


SCHOOL_DOMAIN = "school"
_ATTEMPT_ALPHA = {
    "guided_check": 0.12,
    "bridge": 0.10,
    "masterclass": 0.15,
    "revision_level_1": 0.12,
    "revision_level_2": 0.12,
    "revision_level_3": 0.12,
    "independent_check": 0.35,
    "transfer_check": 0.45,
    "chapter_check": 0.50,
}


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
        readiness = _score(raw.get("readiness"))
        mastery = _score(raw.get("mastery"))
        gaps = [str(value).strip() for value in raw.get("gaps_json") or [] if str(value).strip()]
        evidence = raw.get("evidence_json") if isinstance(raw.get("evidence_json"), dict) else {}
        latest_evidence = ledger_evidence.get(skill_id) or {}
        if mastery >= 0.95:
            bucket = "mastered_skills"
        elif readiness < 0.65:
            bucket = "active_gaps"
        elif readiness < 0.85:
            bucket = "improving_gaps"
        else:
            bucket = "strong_skills"
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
        existing = {
            str(profile.get("skill_id") or ""): profile
            for profile in graph.get("profiles") or []
            if isinstance(profile, dict) and profile.get("domain") == SCHOOL_DOMAIN
        }
        evaluator_score = _score(score)
        passed_without_blockers = bool(attempt_passed) and not blockers
        certifying = attempt_type in {
            "independent_check",
            "transfer_check",
            "chapter_check",
        }
        readiness_signal = (
            evaluator_score
            if passed_without_blockers and certifying
            else min(evaluator_score, 0.79)
            if passed_without_blockers
            else min(evaluator_score, 0.59)
        )
        alpha = _ATTEMPT_ALPHA.get(attempt_type, 0.2)
        unique_skill_ids = list(dict.fromkeys(skill_id for skill_id in skill_ids if skill_id))
        for skill_id in unique_skill_ids:
            previous = existing.get(skill_id) or {}
            previous_evidence = (
                previous.get("evidence_json")
                if isinstance(previous.get("evidence_json"), dict)
                else {}
            )
            previous_attempts = int(previous.get("attempts") or 0)
            previous_readiness = _score(previous.get("readiness"))
            readiness = (
                readiness_signal
                if previous_attempts == 0
                else round(
                    (1.0 - alpha) * previous_readiness
                    + alpha * readiness_signal,
                    4,
                )
            )
            is_strong = (
                certifying
                and passed_without_blockers
                and evaluator_score >= 0.8
                and readiness >= 0.65
            )
            previous_gaps = [
                str(value).strip()
                for value in previous.get("gaps_json") or []
                if str(value).strip()
            ]
            gap = (
                ""
                if is_strong
                else previous_gaps[0]
                if passed_without_blockers and previous_gaps
                else focus
            )
            evidence_json = {
                "session_id": session_id,
                "chapter_id": chapter_id,
                "level_id": level_id,
                "attempt_type": attempt_type,
                "latest_quote": str(answer_excerpt or "")[:320],
                "criteria": list(criteria),
                "blockers": list(blockers),
                "evaluator_score": evaluator_score,
                "attempt_passed": bool(attempt_passed),
            }
            if preserve_latest_evidence:
                evidence_json = {
                    **(
                        previous_evidence
                        if previous_evidence
                        else {
                            "session_id": session_id,
                            "chapter_id": chapter_id,
                            "level_id": level_id,
                            "attempt_type": attempt_type,
                            "latest_quote": "",
                            "criteria": [],
                            "blockers": [],
                        }
                    ),
                    "latest_certification": {
                        "session_id": session_id,
                        "chapter_id": chapter_id,
                        "score": evaluator_score,
                    },
                }
            await self.store.upsert_learner_skill_profile(
                user_id=user_id,
                domain=SCHOOL_DOMAIN,
                skill_id=skill_id,
                module_id=chapter_id,
                task_type="school_rebuild_curriculum",
                mastery=(
                    1.0
                    if chapter_certified and is_strong
                    else _score(previous.get("mastery"))
                ),
                readiness=readiness,
                confidence=_score(confidence),
                attempts=previous_attempts + 1,
                strengths_json=([focus] if is_strong and certifying else []),
                gaps_json=([gap] if gap else []),
                evidence_json=evidence_json,
                recommended_next_action=(
                    "Continue with a new independent example."
                    if is_strong
                    else f"Try this skill without support: {focus}."
                    if passed_without_blockers
                    else f"Rebuild this skill: {focus}."
                ),
                source_summary=(
                    f"Strong {attempt_type} evidence in {chapter_id}."
                    if is_strong
                    else f"Supported improvement with {focus}."
                    if passed_without_blockers
                    else f"Needs more support with {focus}."
                ),
            )
            existing[skill_id] = {
                "domain": SCHOOL_DOMAIN,
                "skill_id": skill_id,
                "mastery": 1.0 if chapter_certified and is_strong else _score(previous.get("mastery")),
                "readiness": readiness,
                "attempts": previous_attempts + 1,
            }

    async def record_chapter_certification(
        self,
        *,
        user_id: str,
        session_id: str,
        chapter_id: str,
        skill_scores: dict[str, float],
    ) -> None:
        """Project the completed assessment's aggregate evidence for every skill."""

        for skill_id, raw_score in skill_scores.items():
            cleaned_skill_id = str(skill_id).strip()
            if not cleaned_skill_id:
                continue
            score = _score(raw_score)
            focus = cleaned_skill_id.replace(".", " ").replace("_", " ")
            await self.record_curriculum_attempt(
                user_id=user_id,
                session_id=session_id,
                chapter_id=chapter_id,
                level_id="chapter_assessment",
                focus=focus,
                skill_ids=[cleaned_skill_id],
                attempt_type="chapter_check",
                score=score,
                confidence=1.0,
                criteria=[{
                    "id": "chapter_skill_score",
                    "met": score >= 0.8,
                    "quality": score,
                    "evidence_quote": f"Aggregate chapter score: {score:.2f}",
                }],
                blockers=[] if score >= 0.8 else ["chapter_skill_gap"],
                answer_excerpt=f"Chapter assessment aggregate for {cleaned_skill_id}",
                attempt_passed=score >= 0.8,
                chapter_certified=True,
                preserve_latest_evidence=True,
            )
