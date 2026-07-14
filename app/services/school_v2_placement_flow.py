"""School V2 placement flow helpers.

This module is intentionally deterministic for the first product slice: authored
items are scored by answer keys, and the backend owns progression and readiness
seeding.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.school_v2_learning import SchoolLearningProfileService
from app.services.school_v2_placement import (
    BAND_ORDER,
    DifficultyBand,
    PlacementItem,
    PlacementSessionState,
    apply_placement_attempt,
    apply_ready_verdicts,
    next_band_for_skill,
    placement_outcome,
)
from app.services.school_v2_readiness import AttemptEvidence, classify_skill_status


@dataclass(frozen=True)
class PlacementBankItem:
    item_id: str
    skill_id: str
    difficulty_band: DifficultyBand
    item_type: str
    prompt: str
    answer_key: str
    options: tuple[str, ...] = ()


PLACEMENT_BANK: tuple[PlacementBankItem, ...] = (
    PlacementBankItem(
        item_id="plc_eng_vocab_target_1",
        skill_id="eng.c5.vocab.context",
        difficulty_band="target",
        item_type="multiple_choice",
        prompt="In the sentence 'Meena was gentle with the puppy', what does gentle mean?",
        answer_key="kind",
        options=("kind", "angry", "noisy", "late"),
    ),
    PlacementBankItem(
        item_id="plc_eng_event_target_1",
        skill_id="eng.c5.comprehension.event",
        difficulty_band="target",
        item_type="fill_blank",
        prompt="Riya planted flowers in the __.",
        answer_key="garden",
    ),
    PlacementBankItem(
        item_id="plc_eng_reason_target_1",
        skill_id="eng.c5.answer.reason",
        difficulty_band="target",
        item_type="short_answer",
        prompt="Why did Riya's plant grow well?",
        answer_key="because she watered the plant",
    ),
    PlacementBankItem(
        item_id="plc_eng_vocab_target_2",
        skill_id="eng.c5.vocab.context",
        difficulty_band="target",
        item_type="multiple_choice",
        prompt="In 'The tiny seed was hard to see', tiny means __.",
        answer_key="small",
        options=("small", "heavy", "bright", "old"),
    ),
    PlacementBankItem(
        item_id="plc_eng_event_target_2",
        skill_id="eng.c5.comprehension.event",
        difficulty_band="target",
        item_type="fill_blank",
        prompt="Arjun packed his bag before going to __.",
        answer_key="school",
    ),
    PlacementBankItem(
        item_id="plc_eng_reason_target_2",
        skill_id="eng.c5.answer.reason",
        difficulty_band="target",
        item_type="short_answer",
        prompt="Why was Arjun late?",
        answer_key="because he missed the bus",
    ),
    PlacementBankItem(
        item_id="plc_eng_vocab_target_3",
        skill_id="eng.c5.vocab.context",
        difficulty_band="target",
        item_type="multiple_choice",
        prompt="In 'Sara felt cheerful after helping', cheerful means __.",
        answer_key="happy",
        options=("happy", "hungry", "afraid", "tired"),
    ),
    PlacementBankItem(
        item_id="plc_eng_event_target_3",
        skill_id="eng.c5.comprehension.event",
        difficulty_band="target",
        item_type="fill_blank",
        prompt="The children borrowed books from the __.",
        answer_key="library",
    ),
    PlacementBankItem(
        item_id="plc_eng_vocab_entry_1",
        skill_id="eng.c5.vocab.context",
        difficulty_band="entry",
        item_type="multiple_choice",
        prompt="Big means __.",
        answer_key="large",
        options=("large", "wet", "fast", "kind"),
    ),
    PlacementBankItem(
        item_id="plc_eng_event_entry_1",
        skill_id="eng.c5.comprehension.event",
        difficulty_band="entry",
        item_type="fill_blank",
        prompt="A child reads a book. The child is reading a __.",
        answer_key="book",
    ),
    PlacementBankItem(
        item_id="plc_eng_reason_entry_1",
        skill_id="eng.c5.answer.reason",
        difficulty_band="entry",
        item_type="short_answer",
        prompt="Why did Tara drink water?",
        answer_key="because she was thirsty",
    ),
    PlacementBankItem(
        item_id="plc_eng_vocab_foundational_1",
        skill_id="eng.c5.vocab.context",
        difficulty_band="foundational",
        item_type="multiple_choice",
        prompt="Hot means __.",
        answer_key="warm",
        options=("warm", "cold", "late", "small"),
    ),
    PlacementBankItem(
        item_id="plc_eng_event_foundational_1",
        skill_id="eng.c5.comprehension.event",
        difficulty_band="foundational",
        item_type="fill_blank",
        prompt="Ravi runs. Ravi can __.",
        answer_key="run",
    ),
    PlacementBankItem(
        item_id="plc_eng_reason_foundational_1",
        skill_id="eng.c5.answer.reason",
        difficulty_band="foundational",
        item_type="multiple_choice",
        prompt="Which word helps give a reason?",
        answer_key="because",
        options=("because", "blue", "table", "quickly"),
    ),
)


def required_skill_ids(target_class_no: int) -> tuple[str, ...]:
    if target_class_no != 5:
        return ()
    return (
        "eng.c5.vocab.context",
        "eng.c5.comprehension.event",
        "eng.c5.answer.reason",
    )


def public_item(item: PlacementBankItem) -> dict:
    return {
        "item_id": item.item_id,
        "skill_id": item.skill_id,
        "difficulty_band": item.difficulty_band,
        "type": item.item_type,
        "prompt": item.prompt,
        "options": list(item.options) if item.options else None,
    }


def find_item(item_id: str) -> PlacementBankItem:
    for item in PLACEMENT_BANK:
        if item.item_id == item_id:
            return item
    raise KeyError(item_id)


def next_item(state: PlacementSessionState) -> PlacementBankItem | None:
    if placement_outcome(state) != "in_progress":
        return None
    answered = set(state.answered_item_ids)
    adaptive = _adaptive_step_down_item(state, answered)
    if adaptive:
        return adaptive
    for item in PLACEMENT_BANK:
        if item.item_id not in answered:
            return item
    return None


def _adaptive_step_down_item(
    state: PlacementSessionState,
    answered: set[str],
) -> PlacementBankItem | None:
    if not state.answered_item_ids:
        return None
    try:
        previous = find_item(state.answered_item_ids[-1])
    except KeyError:
        return None
    next_band = next_band_for_skill(state, previous.skill_id, previous.difficulty_band)
    if next_band == previous.difficulty_band:
        return None
    for item in PLACEMENT_BANK:
        if (
            item.skill_id == previous.skill_id
            and item.difficulty_band == next_band
            and item.item_id not in answered
        ):
            return item
    return None


def score_answer(item: PlacementBankItem, answer: str) -> float:
    expected = _normalize(item.answer_key)
    actual = _normalize(answer)
    if item.item_type == "short_answer":
        return 1.0 if expected in actual else 0.0
    return 1.0 if actual == expected else 0.0


def apply_answer(
    state: PlacementSessionState,
    item: PlacementBankItem,
    answer: str,
) -> PlacementSessionState:
    score = score_answer(item, answer)
    updated = apply_placement_attempt(
        state,
        PlacementItem(
            item_id=item.item_id,
            skill_id=item.skill_id,
            difficulty_band=item.difficulty_band,
        ),
        evaluator_score=score,
        evaluator_confidence=1.0,
        scorable=True,
    )
    if placement_outcome(updated) == "complete":
        ready_skill_ids = tuple(
            skill_id
            for skill_id, skill_state in updated.skill_states.items()
            if (skill_state.practice_readiness or 0.0) >= 0.80
        )
        updated = apply_ready_verdicts(updated, ready_skill_ids=ready_skill_ids, confidence=1.0)
    return updated


async def record_placement_attempts(
    store,
    *,
    placement_session_id: str,
    user_id: str,
    state: PlacementSessionState,
) -> None:
    service = SchoolLearningProfileService(store)
    for skill_id, skill_state in state.skill_states.items():
        status = classify_skill_status(skill_state)
        await service.record_attempt(
            attempt_id=f"{placement_session_id}:seed",
            user_id=user_id,
            subject_id=state.subject_id,
            class_no=state.target_class_no,
            session_id=placement_session_id,
            chapter_id="",
            node_id="placement",
            skill_state=skill_state,
            evidence=AttemptEvidence(
                attempt_type="placement",
                evaluator_score=skill_state.practice_readiness or 0.0,
                evaluator_confidence=skill_state.last_confidence or 1.0,
                skill_ids=(skill_id,),
                support_level="independent",
            ),
            criteria_json=[],
            evidence_json={"placement_session_id": placement_session_id},
            source="placement_attempt",
            task_type="school_placement",
            gap="" if status in {"ready", "mastered"} else "catch_up_required",
        )


def readiness_summary(state: PlacementSessionState) -> dict:
    skills = [
        {
            "skill_id": skill_id,
            "practice_readiness": skill.practice_readiness,
            "certified_readiness": skill.certified_readiness,
            "ready_source": skill.ready_source,
            "status": classify_skill_status(skill),
        }
        for skill_id, skill in sorted(state.skill_states.items())
    ]
    return {
        "skill_count": len(skills),
        "ready_skill_count": sum(1 for skill in skills if skill["status"] in {"ready", "mastered"}),
        "suggested_start_band": _suggested_start_band(state),
        "suggested_start_class_no": _suggested_start_class_no(_suggested_start_band(state)),
        "skills": skills,
    }


def _suggested_start_band(state: PlacementSessionState) -> DifficultyBand:
    upcoming = next_item(state)
    if upcoming:
        return upcoming.difficulty_band
    weak_skill_ids = {
        skill_id
        for skill_id, skill in state.skill_states.items()
        if classify_skill_status(skill) not in {"ready", "mastered"}
    }
    weak_attempted_bands = [
        band
        for (skill_id, band), misses in state.band_misses.items()
        if skill_id in weak_skill_ids and misses > 0
    ]
    if weak_attempted_bands:
        return min(weak_attempted_bands, key=BAND_ORDER.index)
    return "target"


def _suggested_start_class_no(band: DifficultyBand) -> int:
    if band == "foundational":
        return 3
    if band == "entry":
        return 4
    return 5


def _normalize(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())
