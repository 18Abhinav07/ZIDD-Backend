"""School assessment engine — scoring, milestones, and report cards.

The NCERT school feature needs real assessment, which the curriculum never had:
a per-chapter test, cumulative milestone exams at 30/60/100% of a class, and an
evaluation a parent can read. Every item is graded by the SAME deterministic
answer_check engine the tutor uses (no LLM rubric for closed items), so a score
is exact and reproducible.

All functions here are PURE (schema in, result out) so they unit-test in
isolation, mirroring answer_check / route.
"""
from dataclasses import dataclass, field

from app.content.schema import Assessment
from app.graph.answer_check import BRIDGE_CORRECT_SCORE, grade_pending_answer


def is_item_correct(item, user_answer: str) -> bool:
    """Grade one AssessmentItem deterministically via the shared engine."""
    pending = {
        "type": item.type,
        "answer_key": item.answer_key,
        "options": item.options,
        "accept": item.accept,
    }
    return grade_pending_answer(pending, user_answer).score == BRIDGE_CORRECT_SCORE


@dataclass
class SkillScore:
    skill: str
    correct: int
    total: int

    @property
    def mastery(self) -> float:
        return self.correct / self.total if self.total else 0.0


@dataclass
class AssessmentResult:
    assessment_id: str
    title: str
    kind: str
    correct: int
    total: int
    passed: bool
    by_skill: list[SkillScore] = field(default_factory=list)
    weak_skills: list[str] = field(default_factory=list)   # skills below pass_mark
    missed_item_ids: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        return round(self.correct / self.total, 4) if self.total else 0.0


def score_assessment(assessment: Assessment, answers: dict[str, str]) -> AssessmentResult:
    """Grade a whole assessment against the learner's answers.

    `answers` maps item id -> the learner's response. A missing answer counts as
    wrong (a skipped question is not a pass). Produces an overall pass/fail at the
    assessment's `pass_mark`, plus a per-skill breakdown and the weak skills so a
    report can say exactly where the child needs more work."""
    per_skill: dict[str, list[int]] = {}   # skill -> [correct, total]
    correct = 0
    missed: list[str] = []

    for item in assessment.items:
        ok = is_item_correct(item, answers.get(item.id, ""))
        skill = item.skill or "general"
        c, t = per_skill.get(skill, [0, 0])
        per_skill[skill] = [c + (1 if ok else 0), t + 1]
        if ok:
            correct += 1
        else:
            missed.append(item.id)

    total = len(assessment.items)
    by_skill = [SkillScore(s, c, t) for s, (c, t) in per_skill.items()]
    weak = [s.skill for s in by_skill if s.mastery < assessment.pass_mark]
    overall = correct / total if total else 0.0

    return AssessmentResult(
        assessment_id=assessment.id,
        title=assessment.title,
        kind=assessment.kind,
        correct=correct,
        total=total,
        passed=overall >= assessment.pass_mark,
        by_skill=sorted(by_skill, key=lambda s: s.skill),
        weak_skills=sorted(weak),
        missed_item_ids=missed,
    )


def milestone_due(
    chapters_done: int,
    chapters_total: int,
    milestones: list[Assessment],
    fired_percents: set[int],
) -> Assessment | None:
    """Return the milestone exam newly unlocked by this much class progress.

    Fires when the learner's completion (chapters_done / chapters_total) reaches a
    milestone's at_percent threshold that has not fired yet. Returns the LOWEST
    not-yet-fired threshold at or below current progress, so milestones are never
    skipped even if the learner jumps several chapters. None when nothing is due."""
    if chapters_total <= 0:
        return None
    pct = (chapters_done / chapters_total) * 100
    candidates = [
        m for m in milestones
        if m.at_percent is not None
        and m.at_percent not in fired_percents
        and pct >= m.at_percent
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda m: m.at_percent)


def report_card(class_title: str, results: list[AssessmentResult]) -> dict:
    """Roll up a learner's assessment results into a parent-readable summary.

    Aggregates every chapter/milestone score, the skills mastered vs still-weak
    across the class, and an overall pass rate — the 'is my child learning'
    artifact the tutor chat alone can't provide."""
    if not results:
        return {"class": class_title, "assessments": 0, "overall": 0.0,
                "passed": 0, "mastered_skills": [], "weak_skills": []}
    skill_tot: dict[str, list[int]] = {}
    for r in results:
        for s in r.by_skill:
            c, t = skill_tot.get(s.skill, [0, 0])
            skill_tot[s.skill] = [c + s.correct, t + s.total]
    mastered = sorted(s for s, (c, t) in skill_tot.items() if t and c / t >= 0.8)
    weak = sorted(s for s, (c, t) in skill_tot.items() if t and c / t < 0.6)
    return {
        "class": class_title,
        "assessments": len(results),
        "overall": round(sum(r.score for r in results) / len(results), 4),
        "passed": sum(1 for r in results if r.passed),
        "mastered_skills": mastered,
        "weak_skills": weak,
    }
