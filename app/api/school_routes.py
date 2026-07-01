"""School curriculum + assessment API.

The legacy session API has no test path. This exposes the NCERT class -> chapter
structure and a serve / submit / score loop for chapter tests and milestone exams,
backed by the deterministic assessment engine. Answer keys stay server-side: the
learner receives items, submits answers, and gets a scored report naming the exact
skills they still need to work on.
"""
import logging

from fastapi import APIRouter, Body, HTTPException, Request

from app.content import curriculum as cur
from app.content.assessment import milestone_due, score_assessment
from app.storage import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/school", tags=["school"])


def _uid(request: Request) -> str:
    return getattr(request.state, "user_id", None) or ""


def _public_item(item) -> dict:
    """Strip the answer key — a learner must never receive it with the question."""
    return {"id": item.id, "type": item.type, "prompt": item.prompt,
            "options": item.options, "skill": item.skill}


@router.get("/classes")
async def classes() -> list[dict]:
    out = []
    for n in cur.all_classes():
        c = cur.get_class(n)
        out.append({
            "class_no": c.class_no, "title": c.title, "description": c.description,
            "chapter_count": cur.chapter_count(n),
        })
    return out


@router.get("/class/{class_no}")
async def class_detail(class_no: int) -> dict:
    try:
        c = cur.get_class(class_no)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Unknown class") from e
    chapters = [
        {
            "id": ch.id, "title": ch.title, "ncert_unit": ch.ncert_unit,
            "chapter_no": ch.chapter_no, "genre": ch.genre,
            "levels": [{"id": n.id, "title": n.title} for n in ch.nodes],
            "chapter_test_id": ch.chapter_test.id if ch.chapter_test else None,
        }
        for ch in cur.class_chapters(class_no)
    ]
    return {
        "class_no": c.class_no, "title": c.title, "description": c.description,
        "chapters": chapters,
        "milestones": [
            {"id": m.id, "title": m.title, "at_percent": m.at_percent}
            for m in c.milestones
        ],
    }


@router.get("/test/{test_id}")
async def get_test(test_id: str) -> dict:
    a = cur.find_assessment(test_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Unknown test")
    return {
        "id": a.id, "title": a.title, "kind": a.kind, "pass_mark": a.pass_mark,
        "items": [_public_item(i) for i in a.items],
    }


@router.post("/test/{test_id}/submit")
async def submit_test(
    test_id: str, request: Request, answers: dict = Body(..., embed=True)
) -> dict:
    a = cur.find_assessment(test_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Unknown test")
    if not isinstance(answers, dict):
        raise HTTPException(status_code=400, detail="answers must map item_id -> response")
    r = score_assessment(a, answers)
    by_skill = [
        {"skill": s.skill, "correct": s.correct, "total": s.total,
         "mastery": round(s.mastery, 4)}
        for s in r.by_skill
    ]
    # Persist the result + fold per-skill ratios into the learner's school
    # mastery so progress is durable AND the live 'Learn' tutor can target real
    # weak spots. Best-effort: a storage hiccup must never fail a graded submit.
    user_id = _uid(request)
    if user_id:
        try:
            await get_storage().record_assessment_result(
                user_id=user_id,
                test_id=r.assessment_id,
                class_no=cur.class_of_assessment(test_id) or 0,
                kind=r.kind,
                score=r.score,
                passed=r.passed,
                by_skill=[{"skill": s.skill, "correct": s.correct, "total": s.total}
                          for s in r.by_skill],
            )
        except Exception:
            logger.warning(
                "submit_test: failed to persist result for user=%s test=%s",
                user_id, test_id, exc_info=True,
            )
    return {
        "test_id": r.assessment_id, "title": r.title, "kind": r.kind,
        "score": r.score, "correct": r.correct, "total": r.total, "passed": r.passed,
        "by_skill": by_skill,
        "weak_skills": r.weak_skills, "missed_item_ids": r.missed_item_ids,
    }


@router.get("/progress")
async def progress(request: Request, class_no: int | None = None) -> dict:
    """Durable, server-side learning record for the authenticated learner.

    Replaces localStorage-only progress: which chapter tests / milestones were
    passed, the per-skill mastery EMA, and the current weak skills — the same
    signal the live 'Learn' tutor uses to personalise. Empty when nothing has
    been attempted yet."""
    user_id = _uid(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    store = get_storage()
    results = await store.get_school_results(user_id, class_no)
    mastery = await store.get_school_skill_mastery(user_id)
    passed_tests = sorted(r["test_id"] for r in results if r["passed"])
    overall = round(sum(r["score"] for r in results) / len(results), 4) if results else 0.0
    return {
        "class_no": class_no,
        "results": [
            {"test_id": r["test_id"], "class_no": r["class_no"], "kind": r["kind"],
             "score": r["score"], "passed": r["passed"], "weak_skills": r["weak_skills"]}
            for r in results
        ],
        "passed_tests": passed_tests,
        "skill_mastery": [
            {"skill": m["skill"], "mastery": round(m["ema"], 4), "attempts": m["attempts"]}
            for m in mastery
        ],
        "weak_skills": await store.get_school_weak_skills(user_id),
        "overall": overall,
    }


@router.get("/class/{class_no}/milestone")
async def milestone_status(class_no: int, chapters_done: int = 0, fired: str = "") -> dict:
    """Which milestone exam is unlocked at this much class progress (stateless).

    `chapters_done` and `fired` (comma-separated already-taken percents) come from
    the learner's progress, so the client can prompt the right milestone."""
    try:
        c = cur.get_class(class_no)
    except KeyError as e:
        raise HTTPException(status_code=404, detail="Unknown class") from e
    fired_set = {int(p) for p in fired.split(",") if p.strip().isdigit()}
    due = milestone_due(chapters_done, cur.chapter_count(class_no), c.milestones, fired_set)
    return {
        "due": (
            {"id": due.id, "title": due.title, "at_percent": due.at_percent}
            if due else None
        )
    }
