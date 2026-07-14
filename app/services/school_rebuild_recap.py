"""Recap-path planner for the rebuilt School Prep flow."""

from __future__ import annotations

from typing import Any

from app.content.school.content_schema import SchoolRubricEvaluation
from app.services.school_rebuild_profile import school_coach_identity

from app.content.school_rebuild_placement_bank import (
    SchoolPlacementBankItem,
    placement_tracks_for,
)
from app.content.school_rebuild_placement_validation import (
    RUBRIC_REMEDIATION_BY_CRITERION,
    STRICT_RUBRIC_CRITERIA_BY_REF,
)
from app.services.school_rebuild_curriculum import decide_open_answer_evaluation


ENGINE_VERSION = "school-rebuild-recap-1"
RECAP_PASS_THRESHOLD = 1.0
REVISION_STEPS = ("revision_level_1", "revision_level_2", "revision_level_3")

TEACHING_BLOCK_BY_SKILL = {
    "reading.sentence_comprehension": "Find the exact who, what, where, or when clue before forming the answer.",
    "reading.paragraph_main_idea": "The main idea is the one thought supported by most details, not one small event.",
    "reading.inference_reason": "Combine a text clue with what it reasonably shows; do not guess beyond the passage.",
    "reading.word_meaning_context": "Read around the unfamiliar word and use the nearby contrast, example, or explanation.",
    "vocab.chapter_word_usage": "Choose the word whose meaning and grammar both fit the whole sentence.",
    "grammar.noun_verb_adjective": "A naming word names a person, place, animal, or thing. An action word shows what happens, and a describing word adds a quality.",
    "grammar.sentence_order": "Build a clear sentence by placing the subject before the action and keeping connected details together.",
    "grammar.connectors_because_and_but": "Use because for a reason, and for addition, and but for a contrast.",
    "grammar.tense_usage": "Use the time clue to decide whether the action happened before, happens now, or will happen later.",
    "writing.complete_sentence": "A complete sentence needs one whole idea with a subject and an action or description.",
    "writing.short_answer": "Answer the exact question first, then add the passage detail that makes the answer complete.",
    "writing.reason_answer": "State the answer and connect it to a relevant reason with because or another clear link.",
    "writing.summary_own_words": "Keep the main event and essential details, remove repetition, and retell them in your own words.",
}

RECAP_CHECK_BANK: dict[str, dict[str, dict[str, Any]]] = {
    "recognize naming words": {
        "guided_check": {
            "passage": "The teacher reads a book.",
            "prompt": "Which word names a person?",
            "options": ["teacher", "reads", "book", "the"],
            "accepted_answers": ["teacher"],
        },
        "independent_check": {
            "passage": "The red flower opened in the morning.",
            "prompt": "Which word names a thing?",
            "options": ["flower", "opened", "red", "morning"],
            "accepted_answers": ["flower"],
        },
        "bridge": {
            "passage": "A naming word tells us a person, place, animal, or thing. The teacher is a person.",
            "prompt": "In this sentence, which word names the person?",
            "options": ["teacher", "tells", "word", "this"],
            "accepted_answers": ["teacher"],
        },
        "masterclass": {
            "passage": (
                "Masterclass: separate what a word does from what it names. "
                "In 'The teacher reads a book', reads is an action. Teacher names a person."
            ),
            "prompt": "Which word names the person?",
            "options": ["teacher", "reads", "book", "the"],
            "accepted_answers": ["teacher"],
        },
    },
    "understand a simple sentence": {
        "guided_check": {
            "passage": "Rina sat on the mat. The mat was near the window.",
            "prompt": "Where did Rina sit?",
            "options": [],
            "accepted_answers": ["mat", "the mat", "on the mat"],
        },
        "independent_check": {
            "passage": "Nila put three mangoes in the basket.",
            "prompt": "What did Nila put in the basket?",
            "options": [],
            "accepted_answers": ["mangoes", "three mangoes"],
        },
        "bridge": {
            "passage": "Read the sentence again and look for the thing after the action.",
            "prompt": "Nila put three mangoes in the basket. What thing did she put there?",
            "options": [],
            "accepted_answers": ["mangoes", "three mangoes"],
        },
    },
    "use context to understand a word": {
        "guided_check": {
            "passage": "The tiny seed was so small that Meera held it on one finger.",
            "prompt": "What does tiny mean?",
            "options": ["small", "heavy", "angry", "late"],
            "accepted_answers": ["small"],
        },
        "independent_check": {
            "passage": "The clever crow dropped stones into the pot and raised the water.",
            "prompt": "What does clever mean here?",
            "options": ["smart", "sleepy", "wet", "round"],
            "accepted_answers": ["smart", "intelligent"],
        },
        "bridge": {
            "passage": "Use the clue after the word. The tiny seed was so small.",
            "prompt": "Which clue tells you the meaning of tiny?",
            "options": ["small", "heavy", "late", "angry"],
            "accepted_answers": ["small"],
        },
    },
    "write a complete sentence": {
        "guided_check": {
            "passage": "A bird is sitting on a branch.",
            "prompt": "Complete the sentence: The bird is ___ on a branch.",
            "options": [],
            "accepted_answers": ["sitting"],
        },
        "independent_check": {
            "passage": "The dog ran after the ball.",
            "prompt": "Complete the sentence: The dog ___ after the ball.",
            "options": [],
            "accepted_answers": ["ran"],
        },
        "bridge": {
            "passage": "A complete sentence needs the action word. The dog ran.",
            "prompt": "What action word completes the sentence: The dog ___ after the ball?",
            "options": [],
            "accepted_answers": ["ran"],
        },
    },
    "answer with a reason": {
        "guided_check": {
            "passage": "The room was dark, so Kabir switched on the lamp.",
            "prompt": "Why did Kabir switch on the lamp?",
            "options": [],
            "accepted_answers": ["dark", "the room was dark", "because it was dark"],
        },
        "independent_check": {
            "passage": "Sana drank a full glass of water after running in the sun.",
            "prompt": "Why did Sana drink water?",
            "options": [],
            "accepted_answers": ["thirsty", "she was thirsty", "because she was thirsty", "after running"],
        },
        "bridge": {
            "passage": "A why answer needs a reason clue. Sana ran in the sun.",
            "prompt": "What clue explains why Sana drank water?",
            "options": [],
            "accepted_answers": ["running in the sun", "after running", "thirsty"],
        },
    },
    "find the main idea": {
        "guided_check": {
            "passage": "Aman watered the plants every morning. He removed dry leaves and kept the soil soft.",
            "prompt": "What is the passage mostly about?",
            "options": ["Aman caring for plants", "Aman losing a toy", "A rainy day", "A school race"],
            "accepted_answers": ["aman caring for plants", "caring for plants", "aman takes care of plants"],
        },
        "independent_check": {
            "passage": "The children entered quietly. They chose books, sat at a table, and read for thirty minutes.",
            "prompt": "What is the passage mostly about?",
            "options": ["children reading in a library", "children eating lunch", "children playing cricket", "children buying shoes"],
            "accepted_answers": ["children reading in a library", "reading in a library", "children read books"],
        },
        "bridge": {
            "passage": "The main idea is what most sentences are about.",
            "prompt": "Most sentences mention books and reading. What is the main idea?",
            "options": ["children reading in a library", "children eating lunch", "children buying shoes", "children running"],
            "accepted_answers": ["children reading in a library", "reading in a library"],
        },
    },
    "use because to give a reason": {
        "guided_check": {
            "passage": "Tara carried an umbrella. It was raining.",
            "prompt": "Join the ideas: Tara carried an umbrella ___ it was raining.",
            "options": [],
            "accepted_answers": ["because"],
        },
        "independent_check": {
            "passage": "Mira stayed inside. She had a fever.",
            "prompt": "Join the ideas: Mira stayed inside ___ she had a fever.",
            "options": [],
            "accepted_answers": ["because"],
        },
        "bridge": {
            "passage": "Use because when the second idea gives the reason.",
            "prompt": "Which word gives a reason: Mira stayed inside ___ she had a fever.",
            "options": [],
            "accepted_answers": ["because"],
        },
    },
    "use past tense": {
        "guided_check": {
            "passage": "Today I go to school. Yesterday I went to school.",
            "prompt": "Which word shows the past action?",
            "options": ["went", "today", "school", "I"],
            "accepted_answers": ["went"],
        },
        "independent_check": {
            "passage": "Yesterday, the children played in the park.",
            "prompt": "Choose the past-tense word.",
            "options": ["played", "children", "park", "the"],
            "accepted_answers": ["played"],
        },
        "bridge": {
            "passage": "Past tense tells what already happened. Yesterday, the children played.",
            "prompt": "Which word tells what already happened?",
            "options": ["played", "children", "park", "the"],
            "accepted_answers": ["played"],
        },
    },
}


def new_recap_state(report: dict[str, Any]) -> dict[str, Any]:
    modules = [_module_from_report_item(item) for item in report.get("recommended_recap_modules") or []]
    return normalize_recap_state({
        "engine_version": ENGINE_VERSION,
        "profile_version_id": str(report["profile_version_id"]),
        "source_placement_report_id": str(report["report_id"]),
        "source_placement_session_id": str(report["placement_session_id"]),
        "subject_id": report["subject_id"],
        "target_class_no": int(report["target_class_no"]),
        "active_learning_class_no": int(report["active_learning_class_no"]),
        "status": "active",
        "current_module_index": 0,
        "modules": modules,
        "last_feedback": None,
    })


def public_recap_response(session_row: dict[str, Any]) -> dict[str, Any]:
    state = normalize_recap_state(dict(session_row.get("state_json") or {}))
    return {
        "session_id": str(session_row["session_id"]),
        "flow_type": "recap",
        **school_coach_identity(state),
        "status": state.get("status") or session_row["status"],
        "profile_version_id": str(
            session_row.get("profile_version_id")
            or state.get("profile_version_id")
            or ""
        ),
        "source_placement_report_id": str(state.get("source_placement_report_id") or ""),
        "source_placement_session_id": str(state.get("source_placement_session_id") or ""),
        "subject_id": state.get("subject_id") or session_row.get("subject_id"),
        "target_class_no": int(state.get("target_class_no") or session_row.get("class_no") or 0),
        "active_learning_class_no": int(state.get("active_learning_class_no") or 0),
        "current_module_index": int(state.get("current_module_index") or 0),
        "modules": [_public_module(module) for module in state.get("modules") or []],
        "progress": _progress(state),
        "current_activity": _public_activity(_current_activity(state)),
        "last_feedback": state.get("last_feedback"),
    }


def normalize_recap_state(state: dict[str, Any]) -> dict[str, Any]:
    modules = []
    for index, module in enumerate(state.get("modules") or []):
        normalized = dict(module)
        normalized.setdefault("status", "in_progress" if index == int(state.get("current_module_index") or 0) else "not_started")
        normalized.setdefault("current_step", "guided_check")
        normalized.setdefault("attempts", [])
        normalized["checks"] = _checks_for_module(normalized)
        modules.append(normalized)
    if modules and not any(module.get("status") == "in_progress" for module in modules):
        current_index = min(int(state.get("current_module_index") or 0), len(modules) - 1)
        if modules[current_index].get("status") != "complete":
            modules[current_index]["status"] = "in_progress"
    status = "complete" if modules and all(module.get("status") == "complete" for module in modules) else state.get("status", "active")
    current_index = min(int(state.get("current_module_index") or 0), max(0, len(modules) - 1))
    return {
        **state,
        "engine_version": state.get("engine_version") or ENGINE_VERSION,
        "status": status,
        "current_module_index": current_index,
        "modules": modules,
        "last_feedback": state.get("last_feedback"),
    }


def apply_recap_answer(
    state: dict[str, Any],
    *,
    activity_id: str,
    answer: str,
    open_answer_evaluation: SchoolRubricEvaluation | dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = normalize_recap_state(state)
    activity = _current_activity(normalized)
    if not activity or activity["activity_id"] != activity_id:
        raise ValueError("unexpected_recap_activity")

    evaluator_activity = evaluator_activity_for_answer(activity)
    if evaluator_activity is not None:
        if open_answer_evaluation is None:
            raise ValueError("open_answer_evaluation_required")
        answer_evaluation = decide_open_answer_evaluation(
            evaluator_activity,
            open_answer_evaluation,
            answer=answer,
        )
        evaluation_mode = "llm_rubric"
    else:
        correct = _answer_matches(activity, answer)
        score = 1.0 if correct else 0.0
        answer_evaluation = {
            "correct": correct,
            "score": score,
            "confidence": 1.0,
            "criteria": [{
                "id": "accepted_answer_match",
                "met": correct,
                "quality": score,
                "evidence_quote": answer.strip() or "(empty answer)",
            }],
            "missing_criteria": [] if correct else ["accepted_answer_match"],
            "misconception_tags": [] if correct else ["recap_gap"],
            "blockers": [],
            "language_detected": "en",
            "model_score": None,
        }
        evaluation_mode = "deterministic"

    module_index = int(activity["module_index"])
    modules = list(normalized.get("modules") or [])
    module = dict(modules[module_index])
    correct = bool(answer_evaluation["correct"])
    attempt_no = 1 + sum(
        1
        for previous in module.get("attempts") or []
        if previous.get("kind") == activity["kind"]
    )
    attempt = {
        "activity_id": activity_id,
        "kind": activity["kind"],
        "attempt_no": attempt_no,
        "answer": answer,
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "blockers": list(answer_evaluation["blockers"]),
        "evaluation_mode": evaluation_mode,
    }
    module["attempts"] = list(module.get("attempts") or []) + [attempt]
    if correct:
        if activity["kind"] in REVISION_STEPS:
            current_revision_index = REVISION_STEPS.index(activity["kind"])
            if current_revision_index + 1 < len(REVISION_STEPS):
                module["status"] = "in_progress"
                module["current_step"] = REVISION_STEPS[current_revision_index + 1]
            else:
                module["status"] = "in_progress"
                module["current_step"] = "independent_check"
        elif activity["kind"] in {"guided_check", "bridge", "masterclass"}:
            module["status"] = "in_progress"
            module["current_step"] = str(
                module.get("return_step") or "independent_check"
            )
        elif activity["kind"] == "independent_check":
            module["status"] = "in_progress"
            module["current_step"] = "transfer_check"
        elif activity["kind"] == "transfer_check":
            module["status"] = "complete"
            module["current_step"] = "complete"
            next_index = module_index + 1
            if next_index < len(modules):
                next_module = dict(modules[next_index])
                next_module["status"] = "in_progress"
                next_module.setdefault("current_step", "guided_check")
                modules[next_index] = next_module
                normalized["current_module_index"] = next_index
            else:
                normalized["current_module_index"] = module_index
                normalized["status"] = "complete"
    else:
        module["status"] = "in_progress"
        if activity["kind"] in {"independent_check", "transfer_check"}:
            module["return_step"] = activity["kind"]
        if activity["kind"] in REVISION_STEPS:
            module["current_step"] = activity["kind"]
        elif activity["kind"] == "masterclass" and attempt_no >= 2:
            module["current_step"] = "revision_level_1"
            module["revision_expanded"] = True
        elif activity["kind"] in {"bridge", "masterclass"}:
            module["current_step"] = "masterclass"
        else:
            module["current_step"] = "bridge"
    modules[module_index] = module
    normalized["modules"] = modules
    normalized["last_feedback"] = {
        "activity_id": activity_id,
        "module_id": activity["module_id"],
        "kind": activity["kind"],
        "correct": correct,
        "message": _feedback_message(
            activity,
            correct,
            next_step=str(module.get("current_step") or ""),
        ),
    }
    updated = normalize_recap_state(normalized)
    return updated, {
        "activity_id": activity_id,
        "module_id": activity["module_id"],
        "kind": activity["kind"],
        "attempt_no": attempt_no,
        "focus": activity["focus"],
        "skill_ids": list(activity.get("skill_ids") or []),
        "source_class_no": int(activity["source_class_no"]),
        "correct": correct,
        "score": float(answer_evaluation["score"]),
        "confidence": float(answer_evaluation["confidence"]),
        "criteria": list(answer_evaluation["criteria"]),
        "missing_criteria": list(answer_evaluation["missing_criteria"]),
        "misconception_tags": list(answer_evaluation["misconception_tags"]),
        "blockers": list(answer_evaluation["blockers"]),
        "language_detected": str(answer_evaluation["language_detected"]),
        "model_score": answer_evaluation.get("model_score"),
        "evaluation_mode": evaluation_mode,
    }


def recap_activity_for_answer(
    state: dict[str, Any],
    *,
    activity_id: str,
) -> dict[str, Any]:
    activity = _current_activity(normalize_recap_state(state))
    if not activity or activity["activity_id"] != activity_id:
        raise ValueError("unexpected_recap_activity")
    return activity


def evaluator_activity_for_answer(
    activity: dict[str, Any],
) -> dict[str, Any] | None:
    if activity.get("evaluation_mode") != "strict_rubric":
        return None
    rubric_ref = str(activity.get("rubric_ref") or "")
    criterion_ids = STRICT_RUBRIC_CRITERIA_BY_REF.get(rubric_ref)
    if not criterion_ids:
        raise ValueError("recap_open_answer_rubric_missing")
    return {
        **activity,
        "evaluation_mode": "llm_rubric",
        "pass_score": 0.75,
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": RUBRIC_REMEDIATION_BY_CRITERION[criterion_id],
                "required": True,
                "min_quality": 0.7,
            }
            for criterion_id in criterion_ids
        ],
    }


def _module_from_report_item(item: dict[str, Any]) -> dict[str, Any]:
    focus = str(item.get("focus") or item.get("title") or "foundation skill")
    source_class_no = int(item.get("source_class_no") or 2)
    target_class_no = int(item.get("target_class_no") or source_class_no + 1)
    track_id = str(item.get("placement_track_id") or "")
    primary_skill_id = str(item.get("primary_skill_id") or "")
    if not track_id or not primary_skill_id:
        raise ValueError("recap_content_not_authored")
    checks = _checks_for_track(
        subject_id="english",
        target_class_no=target_class_no,
        track_id=track_id,
        source_class_no=source_class_no,
    )
    teaching_block = TEACHING_BLOCK_BY_SKILL.get(primary_skill_id)
    if not teaching_block:
        raise ValueError("recap_content_not_authored")
    return {
        "module_id": item.get("module_id") or _slug(focus),
        "title": item.get("title") or f"Recap: {focus}",
        "source_class_no": source_class_no,
        "target_class_no": target_class_no,
        "focus": focus,
        "placement_track_id": track_id,
        "primary_skill_id": primary_skill_id,
        "status": "not_started",
        "current_step": "guided_check",
        "attempts": [],
        "checks": checks,
        "teaching_block": teaching_block,
        "guided_check_label": f"Try one together: {focus}",
        "bridge_label": f"Extra support: {focus}",
        "independent_check_label": f"Show it on your own: {focus}",
        "transfer_check_label": f"Use it in a new Class {target_class_no} passage",
        "masterclass_trigger_rule": "If this is missed twice, Zidd opens a focused masterclass.",
    }


def _public_module(module: dict[str, Any]) -> dict[str, Any]:
    return {
        "module_id": module["module_id"],
        "title": module["title"],
        "source_class_no": int(module["source_class_no"]),
        "focus": module["focus"],
        "status": module.get("status") or "not_started",
        "teaching_block": module["teaching_block"],
        "guided_check_label": module["guided_check_label"],
        "bridge_label": module["bridge_label"],
        "independent_check_label": module["independent_check_label"],
        "transfer_check_label": module["transfer_check_label"],
        "masterclass_trigger_rule": module["masterclass_trigger_rule"],
    }


def _current_activity(state: dict[str, Any]) -> dict[str, Any] | None:
    modules = state.get("modules") or []
    if not modules or state.get("status") == "complete":
        return None
    index = min(int(state.get("current_module_index") or 0), len(modules) - 1)
    module = modules[index]
    if module.get("status") == "complete":
        return None
    step = module.get("current_step") or "guided_check"
    checks = module.get("checks") or _checks_for_module(module)
    check = checks.get(step)
    if not check:
        raise ValueError("recap_content_not_authored")
    attempt_no = 1 + sum(
        1
        for attempt in module.get("attempts") or []
        if attempt.get("kind") == step
    )
    return {
        **check,
        "module_index": index,
        "module_id": module["module_id"],
        "focus": module["focus"],
        "skill_ids": [module["primary_skill_id"]],
        "title": _activity_title(module, step),
        "source_class_no": int(check.get("source_class_no") or module["source_class_no"]),
        "kind": step,
        "activity_id": f"{module['module_id']}:{step}:attempt:{attempt_no}",
        "teaching_block": module["teaching_block"] if step == "guided_check" else _support_block(module, step),
        "attempt_no": attempt_no,
        "can_answer": True,
    }


def _public_activity(activity: dict[str, Any] | None) -> dict[str, Any] | None:
    if not activity:
        return None
    options = activity.get("options") or []
    return {
        "activity_id": activity["activity_id"],
        "module_id": activity["module_id"],
        "kind": activity["kind"],
        "title": activity["title"],
        "focus": activity["focus"],
        "source_class_no": int(activity["source_class_no"]),
        "teaching_block": activity["teaching_block"],
        "passage": activity["passage"],
        "prompt": activity["prompt"],
        "options": list(options) if options else None,
        "attempt_no": int(activity["attempt_no"]),
        "can_answer": True,
    }


def _progress(state: dict[str, Any]) -> dict[str, int]:
    modules = state.get("modules") or []
    completed = sum(1 for module in modules if module.get("status") == "complete")
    return {
        "completed_modules": completed,
        "total_modules": len(modules),
    }


def _support_block(module: dict[str, Any], step: str) -> str:
    if step == "bridge":
        return f"Use this clue before trying again: {module['teaching_block']}"
    if step == "masterclass":
        return f"Let's rebuild this step by step. {module['teaching_block']} Then test the clue in the passage."
    if step in REVISION_STEPS:
        revision_no = REVISION_STEPS.index(step) + 1
        return (
            f"Revision level {revision_no}: use this idea in a fresh supported check. "
            f"{module['teaching_block']}"
        )
    if step == "transfer_check":
        return "New passage, same skill. Apply what you learned independently in a different example."
    return "No hints now. Solve it from the passage on your own."


def _checks_for_module(module: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if module.get("checks"):
        return {
            str(name): dict(check)
            for name, check in dict(module["checks"]).items()
        }
    return _checks_for_focus(str(module.get("focus") or ""))


def _checks_for_focus(focus: str) -> dict[str, dict[str, Any]]:
    key = focus.strip().lower()
    checks = RECAP_CHECK_BANK.get(key)
    if not checks:
        raise ValueError("recap_content_not_authored")
    elif "masterclass" not in checks:
        bridge = checks.get("bridge") or checks.get("guided_check") or {}
        checks = {
            **checks,
            "masterclass": {
                "passage": f"Masterclass: slow down and rebuild {focus} before trying independently.",
                "prompt": bridge.get("prompt") or f"What is the answer for {focus}?",
                "options": list(bridge.get("options") or []),
                "accepted_answers": list(bridge.get("accepted_answers") or [focus.lower()]),
            },
        }
    checks = _with_revision_checks(focus, checks)
    return {name: dict(check) for name, check in checks.items()}


def _checks_for_track(
    *,
    subject_id: str,
    target_class_no: int,
    track_id: str,
    source_class_no: int,
) -> dict[str, dict[str, Any]]:
    track = next(
        (
            candidate
            for candidate in placement_tracks_for(subject_id, target_class_no)
            if candidate.track_id == track_id
        ),
        None,
    )
    if track is None:
        raise ValueError("recap_content_not_authored")
    bands = {band.source_class_no: band for band in track.bands}
    source_band = bands.get(source_class_no)
    target_band = bands.get(target_class_no)
    if source_band is None or target_band is None:
        raise ValueError("recap_content_not_authored")

    def item(stage: str, band) -> SchoolPlacementBankItem:
        selected = next(
            (variant for variant in band.variants if variant.stage == stage),
            None,
        )
        if selected is None:
            raise ValueError("recap_content_not_authored")
        return selected

    guided = item("targeted_diagnostic", source_band)
    bridge = item("confirmatory", source_band)
    independent = item("targeted_diagnostic", target_band)
    transfer = item("confirmatory", target_band)
    checks = {
        "guided_check": _check_from_placement_item(guided),
        "bridge": _check_from_placement_item(bridge),
        "masterclass": _check_from_placement_item(bridge),
        "independent_check": _check_from_placement_item(independent),
        "transfer_check": _check_from_placement_item(transfer),
    }
    return _with_revision_checks(track.learner_skill_label, checks)


def _check_from_placement_item(item: SchoolPlacementBankItem) -> dict[str, Any]:
    return {
        "source_item_id": item.item_id,
        "source_class_no": item.source_class_no,
        "passage": item.passage,
        "prompt": item.prompt,
        "options": list(item.options),
        "accepted_answers": list(item.accepted_answers),
        "evaluation_mode": item.evaluation_mode,
        "rubric_ref": item.rubric_ref,
    }


def _answer_matches(activity: dict[str, Any], answer: str) -> bool:
    normalized = _normalize(answer)
    return normalized in {_normalize(value) for value in activity.get("accepted_answers") or []}


def _activity_title(module: dict[str, Any], step: str) -> str:
    if step == "masterclass":
        return f"Masterclass: {module['focus']}"
    if step in REVISION_STEPS:
        return f"Revision {REVISION_STEPS.index(step) + 1}: {module['focus']}"
    return module["title"]


def _with_revision_checks(
    focus: str,
    checks: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if all(step in checks for step in REVISION_STEPS):
        return checks
    bridge = checks.get("bridge") or checks.get("guided_check") or {}
    independent = checks.get("independent_check") or bridge
    masterclass = checks.get("masterclass") or bridge
    return {
        **checks,
        "revision_level_1": {
            "passage": f"Revision 1: start with the strongest clue. {bridge.get('passage') or ''}".strip(),
            "prompt": bridge.get("prompt") or f"What is the clue for {focus}?",
            "options": list(bridge.get("options") or []),
            "accepted_answers": list(bridge.get("accepted_answers") or [focus.lower()]),
        },
        "revision_level_2": {
            "passage": f"Revision 2: try a nearby example. {independent.get('passage') or ''}".strip(),
            "prompt": independent.get("prompt") or f"What is the answer for {focus}?",
            "options": list(independent.get("options") or []),
            "accepted_answers": list(independent.get("accepted_answers") or [focus.lower()]),
        },
        "revision_level_3": {
            "passage": f"Revision 3: one final supported check. {masterclass.get('passage') or ''}".strip(),
            "prompt": masterclass.get("prompt") or f"What is the answer for {focus}?",
            "options": list(masterclass.get("options") or []),
            "accepted_answers": list(masterclass.get("accepted_answers") or [focus.lower()]),
        },
    }


def _feedback_message(activity: dict[str, Any], correct: bool, *, next_step: str) -> str:
    if correct and activity["kind"] == "independent_check":
        return "Good. One more step: use the same skill in a new passage."
    if correct and activity["kind"] == "transfer_check":
        return "Good. You used the skill in a new passage, so this foundation module is complete."
    if correct and activity["kind"] in {"revision_level_1", "revision_level_2"}:
        return "Good. Move to the next revision level."
    if correct:
        return "Good. Now try the same skill without hints."
    if activity["kind"] == "bridge":
        return "Not yet. Zidd is opening a focused masterclass for this skill."
    if activity["kind"] == "masterclass" and next_step == "revision_level_1":
        return "This needs a short revision run before trying again."
    if activity["kind"] == "masterclass":
        return "Not yet. Stay in the masterclass and try one more supported check."
    if activity["kind"] in REVISION_STEPS:
        return "Not yet. Stay on this revision level and rebuild the clue."
    return "Not yet. Zidd will slow this down with a bridge check before moving ahead."


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().lower().replace(".", "").replace(",", "").split())


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")[:48]
