"""Agent-authored deep manifest for Class 2 English Chapter 1.

The official extract was consulted only for section order, themes, and exercise
forms. Every learner-facing passage, prompt, option, rubric, and answer here is
original Zidd content.
"""

from __future__ import annotations

import re
from typing import Any


SUPPORT_NAMES = (
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
)
_COMMON_WORDS = {
    "about",
    "after",
    "again",
    "because",
    "before",
    "from",
    "into",
    "should",
    "that",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "through",
    "using",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
}
_ALIAS_STOPWORDS = _COMMON_WORDS | {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
}


def R(
    description: str,
    *phrases: str,
    slot: str | None = None,
) -> tuple[str, list[str]] | tuple[str, list[str], str]:
    """Create one explicit rubric requirement for a constructed response."""

    requirement: tuple[str, list[str]] = (description, list(phrases))
    if slot is None:
        return requirement
    return (*requirement, slot)


def C(
    passage: str,
    prompt: str,
    correct: str,
    distractors: list[str],
    coach: str,
    *,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    """Describe an explicitly authored selected-option task."""

    return {
        "kind": "selected_option",
        "passage": passage,
        "prompt": prompt,
        "correct": correct,
        "distractors": distractors,
        "coach": coach,
        "skills": skills,
    }


def O(
    passage: str,
    prompt: str,
    model_answer: str,
    requirements: list[tuple[str, list[str]]],
    coach: str,
    *,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    """Describe an explicitly authored strict-rubric response task."""

    return {
        "kind": "open_response",
        "passage": passage,
        "prompt": prompt,
        "model_answer": model_answer,
        "requirements": requirements,
        "coach": coach,
        "interaction_type": interaction_type,
        "min_words": min_words,
        "ordered": ordered,
        "skills": skills,
    }


def D(
    guided_3: dict[str, Any],
    guided_4: dict[str, Any],
    independent_3: dict[str, Any],
    independent_4: dict[str, Any],
    transfer_3: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Group five independently authored tasks for the Class 2 depth gate."""

    return {
        "guided": [guided_3, guided_4],
        "independent": [independent_3, independent_4],
        "transfer": [transfer_3],
    }


def L(
    transfer_4: dict[str, Any],
    review_3: dict[str, Any],
    review_4: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Group the fresh certifying scenarios required for launch depth."""

    return {
        "transfer": [transfer_4],
        "review": [review_3, review_4],
    }


def _relevance_terms(task: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    source_parts = [task["model_answer"]]
    source_parts.extend(
        phrase
        for requirement in task["requirements"]
        for phrases in [requirement[1]]
        for phrase in phrases
    )
    for word in re.findall(r"[A-Za-z][A-Za-z'-]+", " ".join(source_parts)):
        normalized = word.casefold()
        if (
            len(normalized) < 4
            or normalized in _COMMON_WORDS
            or normalized in terms
        ):
            continue
        terms.append(normalized)
        if len(terms) == 5:
            break
    if len(terms) < 2:
        raise ValueError("class2_open_task_needs_relevance_terms")
    return terms


def _normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def _word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?", value))


def _content_words(value: str) -> set[str]:
    return {
        word.casefold()
        for word in re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", value)
        if word.casefold() not in _ALIAS_STOPWORDS
    }


def _requirement_groups(
    description: str,
    phrases: list[str],
) -> list[list[str]]:
    """Separate co-required claims while retaining true paraphrase alternatives."""

    lowered = description.casefold()
    if " or " in lowered and re.search(
        r"\b(?:both|all|two|three)\b", lowered
    ) is None:
        return [phrases]

    split_required = len(phrases) >= 3 or re.search(
        r"\b(?:and|both|all|two|three|before|after|begins|ends|orders|pairs|first|last)\b",
        lowered,
    ) is not None
    if not split_required or len(phrases) <= 1:
        return [phrases]

    groups: list[list[str]] = []
    for phrase in phrases:
        phrase_words = _content_words(phrase)
        related = next(
            (
                group
                for group in groups
                if phrase_words.intersection(
                    set().union(*(_content_words(item) for item in group))
                )
            ),
            None,
        )
        if related is None:
            groups.append([phrase])
        else:
            related.append(phrase)
    return groups


def _requirement_parts(
    requirement: tuple[str, list[str]] | tuple[str, list[str], str],
) -> tuple[str, list[str], str | None]:
    description, phrases, *suffix = requirement
    return description, phrases, suffix[0] if suffix else None


def _alias_spans(value: str, alias: str) -> list[tuple[int, int]]:
    normalized_value = _normalized(value)
    normalized_alias = _normalized(alias)
    if not normalized_alias:
        return []
    prefix = r"(?<!\w)" if normalized_alias[0].isalnum() else ""
    suffix = r"(?!\w)" if normalized_alias[-1].isalnum() else ""
    return [
        match.span()
        for match in re.finditer(
            f"{prefix}{re.escape(normalized_alias)}{suffix}",
            normalized_value,
        )
    ]


def _semantic_requirements(
    task: dict[str, Any],
    *,
    activity_id: str,
) -> list[tuple[str | None, str, str]]:
    """Return atomic requirements with one authored, model-backed alias each."""

    card_requirements = _sentence_card_requirements(task, activity_id=activity_id)
    if card_requirements is not None:
        return card_requirements

    atomic: list[tuple[str | None, str, list[str]]] = []
    for requirement in task["requirements"]:
        description, phrases, suffix = _requirement_parts(requirement)
        if suffix is not None:
            atomic.append((suffix, description, phrases))
            continue
        groups = _requirement_groups(description, phrases)
        for group_index, group in enumerate(groups, start=1):
            part_description = description
            if len(groups) > 1:
                part_description = (
                    f"Required part {group_index}: {group[0].strip().rstrip('.')}"
                )
            atomic.append((None, part_description, group))

    candidates: list[list[tuple[str, tuple[int, int]]]] = []
    for _, description, aliases in atomic:
        slot_candidates = [
            (alias, span)
            for alias in aliases
            for span in _alias_spans(task["model_answer"], alias)
        ]
        if not slot_candidates:
            raise ValueError(
                f"{activity_id}: model answer lacks an authored alias for {description}"
            )
        candidates.append(slot_candidates)

    selected: list[tuple[str, tuple[int, int]]] = []

    def assign(slot_index: int) -> bool:
        if slot_index == len(candidates):
            return True
        for alias, span in candidates[slot_index]:
            if any(
                span[0] < used_span[1] and used_span[0] < span[1]
                for _, used_span in selected
            ):
                continue
            if any(_normalized(alias) == _normalized(used_alias) for used_alias, _ in selected):
                continue
            selected.append((alias, span))
            if assign(slot_index + 1):
                return True
            selected.pop()
        return False

    if not assign(0):
        raise ValueError(f"{activity_id}: required slots share an alias span")
    return [
        (suffix, description, selected[index][0])
        for index, (suffix, description, _) in enumerate(atomic)
    ]


_SENTENCE_CARD_PREFIXES = (
    "jumbled parts:",
    "word cards:",
    "notes:",
    "cards:",
    "words:",
)


def _sentence_card_requirements(
    task: dict[str, Any],
    *,
    activity_id: str,
) -> list[tuple[str, str, str]] | None:
    if "_sentence_order:" not in activity_id:
        return None
    lowered_passage = task["passage"].casefold()
    if not lowered_passage.startswith(_SENTENCE_CARD_PREFIXES):
        raise ValueError(f"{activity_id}: sentence-order task lacks visible cards")

    _, raw_parts = task["passage"].split(":", 1)
    delimiter = ";" if ";" in raw_parts else "/"
    parts = [part.strip().rstrip(".") for part in raw_parts.split(delimiter)]
    if len(parts) < 2:
        raise ValueError(f"{activity_id}: sentence-order task needs two cards")

    positioned_parts = []
    for part in parts:
        spans = _alias_spans(task["model_answer"], part)
        if len(spans) != 1:
            raise ValueError(
                f"{activity_id}: visible card must appear once in model answer: {part}"
            )
        positioned_parts.append((spans[0], part))
    positioned_parts.sort()
    return [
        (
            f"card_{index}",
            f"Uses the visible card '{part}' in the finished sentence.",
            part,
        )
        for index, (_, part) in enumerate(positioned_parts, start=1)
    ]


_PHASE_ACTIONS = {
    "co_construct": "Use the worked clue with the coach.",
    "guided": "Use the passage clues and the hint.",
    "independent": "Use only the passage.",
    "transfer": "Use the same skill in this new scene.",
    "review": "Remember the skill, then check the passage.",
    "bridge": "Start with the clearest passage clue.",
    "masterclass": "Check the strongest clue before answering.",
    "revision_level_1": "Use the short clue to begin.",
    "revision_level_2": "Use the passage clue, then finish the answer.",
    "revision_level_3": "Answer from the passage without a hint.",
    "assessment": "Use only the passage and question.",
}


def _child_detail_guidance(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


def _open_direction(*, phase: str, focus: str, criterion_count: int) -> str:
    phase_action = _PHASE_ACTIONS.get(
        phase,
        "Use the visible passage to answer the question.",
    )
    return (
        f"{phase_action} To {focus.strip().rstrip('.').casefold()}, "
        f"{_child_detail_guidance(criterion_count)}."
    )


def _activity(
    task: dict[str, Any],
    *,
    activity_id: str,
    phase: str,
    phase_index: int,
    principle: str,
    focus: str,
    skills: list[str],
) -> dict[str, Any]:
    coach = task["coach"].strip().rstrip(".")
    coach = coach[:1].upper() + coach[1:]
    teaching_block = f"{principle.rstrip()} {coach}."
    activity_skills = list(task.get("skills") or skills)
    if task["kind"] == "selected_option":
        raw_options = [task["correct"], *task["distractors"]]
        shift = (sum(ord(char) for char in activity_id) + phase_index) % len(
            raw_options
        )
        options = raw_options[shift:] + raw_options[:shift]
        return {
            "kind": "selected_option",
            "activity_id": activity_id,
            "teaching_block": teaching_block,
            "passage": task["passage"],
            "prompt": task["prompt"],
            "skill_ids": activity_skills,
            "options": options,
            "accepted_answers": [task["correct"]],
        }

    criteria = []
    slots = []
    requirements = _semantic_requirements(task, activity_id=activity_id)
    for requirement_index, (suffix, description, alias) in enumerate(
        requirements,
        start=1,
    ):
        slot_suffix = suffix or f"requirement:{requirement_index}"
        slot_id = f"{activity_id}:{slot_suffix}"
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.8,
            }
        )
        slots.append(
            {
                "id": slot_id,
                "description": description,
                "any_of": [alias],
            }
        )
    direction = _open_direction(
        phase=phase,
        focus=focus,
        criterion_count=len(criteria),
    )
    payload = {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": f"{teaching_block} {direction}",
        "passage": task["passage"],
        "prompt": task["prompt"],
        "skill_ids": activity_skills,
        "interaction_type": task["interaction_type"],
        "rubric_criteria": criteria,
        "concept_slots": slots,
        "forbidden_phrases": [
            "I ignored the supplied scene",
            "A hidden answer gave me this response",
        ],
        "min_response_words": task["min_words"],
        "relevance_terms": _relevance_terms(task),
        "model_answer": task["model_answer"],
        "pass_score": 0.8,
    }
    if (
        task["ordered"] or _sentence_card_requirements(task, activity_id=activity_id)
    ) and len(slots) >= 2:
        payload["ordered_concept_slot_ids"] = [slot["id"] for slot in slots]
    return payload


def _level(spec: dict[str, Any]) -> dict[str, Any]:
    tasks = spec["tasks"]
    if len(tasks) != 14:
        raise ValueError(f"{spec['level_id']}: expected fourteen teaching tasks")
    if any(task["kind"] != "open_response" for task in tasks[3:9]):
        raise ValueError(f"{spec['level_id']}: certifying pools must be open")
    depth = spec.get("depth") or {}
    launch_depth = spec.get("launch_depth") or {}
    if (
        len(depth.get("guided", [])) != 2
        or len(depth.get("independent", [])) != 2
        or len(depth.get("transfer", [])) != 1
    ):
        raise ValueError(f"{spec['level_id']}: authored 8plus depth is incomplete")
    if any(
        task["kind"] != "open_response"
        for task in [*depth["independent"], *depth["transfer"]]
    ):
        raise ValueError(f"{spec['level_id']}: added certifying tasks must be open")
    if (
        len(launch_depth.get("transfer", [])) != 1
        or len(launch_depth.get("review", [])) != 2
        or any(
            task["kind"] != "open_response"
            for task in [
                *launch_depth.get("transfer", []),
                *launch_depth.get("review", []),
            ]
        )
    ):
        raise ValueError(f"{spec['level_id']}: launch certifying depth is incomplete")

    def make(task_index: int, phase: str, phase_index: int) -> dict[str, Any]:
        return _activity(
            tasks[task_index],
            activity_id=f"{spec['level_id']}:{phase}:{phase_index}",
            phase=phase,
            phase_index=phase_index,
            principle=spec["principle"],
            focus=spec["focus"],
            skills=spec["skill_ids"],
        )

    support = {
        name: make(9 + index, name, index + 1)
        for index, name in enumerate(SUPPORT_NAMES)
    }
    support_ids = [support[name]["activity_id"] for name in SUPPORT_NAMES]
    return {
        "level_id": spec["level_id"],
        "title": spec["title"],
        "focus": spec["focus"],
        "outcome": spec["outcome"],
        "skill_ids": list(spec["skill_ids"]),
        "episode_kind": spec["episode_kind"],
        "source_anchor_ids": list(spec["source_anchor_ids"]),
        "connect": spec["connect"],
        "co_construct": make(0, "co_construct", 1),
        "guided_variants": [
            make(1, "guided", 1),
            make(2, "guided", 2),
            _activity(
                depth["guided"][0],
                activity_id=f"{spec['level_id']}:guided:3",
                phase="guided",
                phase_index=3,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
            _activity(
                depth["guided"][1],
                activity_id=f"{spec['level_id']}:guided:4",
                phase="guided",
                phase_index=4,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
        ],
        "independent_variants": [
            make(3, "independent", 1),
            make(4, "independent", 2),
            _activity(
                depth["independent"][0],
                activity_id=f"{spec['level_id']}:independent:3",
                phase="independent",
                phase_index=3,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
            _activity(
                depth["independent"][1],
                activity_id=f"{spec['level_id']}:independent:4",
                phase="independent",
                phase_index=4,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
        ],
        "transfer_variants": [
            make(5, "transfer", 1),
            make(6, "transfer", 2),
            _activity(
                depth["transfer"][0],
                activity_id=f"{spec['level_id']}:transfer:3",
                phase="transfer",
                phase_index=3,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
            _activity(
                launch_depth["transfer"][0],
                activity_id=f"{spec['level_id']}:transfer:4",
                phase="transfer",
                phase_index=4,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
        ],
        "review_variants": [
            make(7, "review", 1),
            make(8, "review", 2),
            _activity(
                launch_depth["review"][0],
                activity_id=f"{spec['level_id']}:review:3",
                phase="review",
                phase_index=3,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
            _activity(
                launch_depth["review"][1],
                activity_id=f"{spec['level_id']}:review:4",
                phase="review",
                phase_index=4,
                principle=spec["principle"],
                focus=spec["focus"],
                skills=spec["skill_ids"],
            ),
        ],
        "misconception_clusters": [
            {
                "cluster_id": spec["misconception_id"],
                "skill_ids": list(spec["skill_ids"]),
                "misconception": spec["misconception"],
                "remediation": spec["remediation"],
                "support_check_ids": support_ids,
            }
        ],
        "support_checks": support,
    }


def build_manifest(
    *,
    chapter: dict[str, Any],
    source_anchors: list[dict[str, Any]],
    level_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    required_anchor_ids = {
        anchor["anchor_id"]
        for anchor in source_anchors
        if anchor["required_for_chapter_certification"]
    }
    for spec in level_specs:
        spec["source_anchor_ids"] = [
            anchor_id
            for anchor_id in spec["source_anchor_ids"]
            if anchor_id in required_anchor_ids
        ]
        if not spec["source_anchor_ids"]:
            raise ValueError(f"{spec['level_id']}: no required English anchor")

    assessment_items = []
    assessment_groups = []
    strands = []
    strand_by_skills: dict[tuple[str, ...], dict[str, Any]] = {}
    item_no = 0
    for spec in level_specs:
        level_items = []
        assessment_skills = list(
            spec.get("assessment_skill_ids") or spec["skill_ids"]
        )
        assessment_tasks = list(spec["assessment"])
        choice_tasks = [
            task for task in assessment_tasks if task["kind"] == "selected_option"
        ]
        open_tasks = [
            task for task in assessment_tasks if task["kind"] == "open_response"
        ]
        if len(choice_tasks) == len(open_tasks) == 2:
            assessment_tasks = [
                choice_tasks[0],
                open_tasks[0],
                choice_tasks[1],
                open_tasks[1],
            ]
        for task in assessment_tasks:
            item_no += 1
            level_items.append(
                _activity(
                    task,
                    activity_id=f"{chapter['chapter_id']}:assessment:{item_no:02d}",
                    phase="assessment",
                    phase_index=item_no,
                    principle=spec["principle"],
                    focus=spec["focus"],
                    skills=assessment_skills,
                )
            )
        assessment_items.extend(level_items)
        assessment_groups.append(level_items)
        forms = []
        if any(item["kind"] == "selected_option" for item in level_items):
            forms.append("selected_option")
        if any(item["kind"] == "open_response" for item in level_items):
            forms.append("constructed_response")
        strand_key = tuple(assessment_skills)
        existing_strand = strand_by_skills.get(strand_key)
        if existing_strand is None:
            existing_strand = {
                "strand_id": f"{spec['level_id']}:assessment",
                "skill_ids": assessment_skills,
                "minimum_items": 4,
                "evidence_forms": forms,
                "remediation_level_ids": [spec["level_id"]],
            }
            strands.append(existing_strand)
            strand_by_skills[strand_key] = existing_strand
        else:
            existing_strand["minimum_items"] += 4
            existing_strand["evidence_forms"] = [
                form
                for form in ("selected_option", "constructed_response")
                if form in set(existing_strand["evidence_forms"]) | set(forms)
            ]
            existing_strand["remediation_level_ids"].append(spec["level_id"])
    assessment_items = [
        level_items[round_index]
        for round_index in range(4)
        for level_items in assessment_groups
    ]
    if len(assessment_items) != 24:
        raise ValueError("class2_manifest_requires_twenty_four_assessment_items")

    return {
        "schema_version": "school-class5-deep-manifest-v1",
        "chapter": {
            **chapter,
            "source_note": (
                "NCERT structural alignment only. All learner-facing passages, "
                "questions, choices, rubrics, and answers are original Zidd content."
            ),
            "content_version": "2026-07-15.1",
            "certification_version": "2026-07-15.1",
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": (
                    f"/tmp/zidd-ncert-class2-3/{chapter['chapter_id']}.txt "
                    "used only for structural and exercise-form analysis"
                ),
            },
        },
        "source_anchors": source_anchors,
        "levels": [_level(spec) for spec in level_specs],
        "chapter_assessment": {
            "items_per_attempt": 12,
            "pass_score": 0.8,
            "max_attempts": 2,
            "bank_item_count": 24,
            "items": assessment_items,
            "strands": strands,
        },
    }


CHAPTER_ID = "eng_c2_ch01"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/bemr101.pdf"

SOURCE_ANCHORS = [
    {
        "anchor_id": f"{CHAPTER_ID}:poem-and-bike:1-2",
        "section_label": "Bicycle poem structure and movement vocabulary",
        "page_start": 1,
        "page_end": 2,
        "source_url": f"{SOURCE_URL}#page=1",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:parts-and-safety:2-5",
        "section_label": "Bicycle parts, functions, and safety ideas",
        "page_start": 2,
        "page_end": 5,
        "source_url": f"{SOURCE_URL}#page=2",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:language-use:4-5",
        "section_label": "Word classes and bicycle description language",
        "page_start": 4,
        "page_end": 5,
        "source_url": f"{SOURCE_URL}#page=4",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:comprehension:6-7",
        "section_label": "Visible-text comprehension and sentence responses",
        "page_start": 6,
        "page_end": 7,
        "source_url": f"{SOURCE_URL}#page=6",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:draw-magic-cycle:6-6",
        "section_label": "Draw and imagine a personal bicycle companion task",
        "page_start": 6,
        "page_end": 6,
        "source_url": f"{SOURCE_URL}#page=6",
        "coverage_treatment": "optional_creative",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:listen-and-speak:3-4",
        "section_label": "Listen, speak, and picture-supported companion work",
        "page_start": 3,
        "page_end": 4,
        "source_url": f"{SOURCE_URL}#page=3",
        "coverage_treatment": "guided_only",
        "required_for_chapter_certification": False,
    },
]


LEVEL_SPECS = [
    {
        "level_id": "bicycle_words_in_action",
        "title": "Bicycle Words at Work",
        "focus": "Use bicycle words from visible context",
        "outcome": "The learner uses bicycle-part and safety words accurately in new written scenes.",
        "skill_ids": [
            "reading.word_meaning_context",
            "vocab.chapter_word_usage",
        ],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:poem-and-bike:1-2",
            f"{CHAPTER_ID}:parts-and-safety:2-5",
        ],
        "principle": "Match each bicycle word to its job and nearby clues.",
        "connect": {
            "teaching_block": "A bicycle word becomes useful when it names a clear part, action, or safety choice.",
            "passage": "Nila checks her bicycle before a short ride to the library.",
            "prompt": "Notice which bicycle words could make this scene exact, then continue.",
        },
        "tasks": [
            C("A silver lever beside the handle helps Arun slow before the gate.", "Which bicycle word names the silver lever's job?", "brake", ["wheel", "carrier", "helmet"], "connect the slowing clue to the correct part"),
            C("Meera places both feet on the flat pieces and pushes them around.", "Which word names the pieces Meera pushes?", "pedals", ["tyres", "bell", "seat"], "follow the foot-action clue instead of the colour"),
            C("The round rubber part turns over the path while the frame stays above it.", "Which bicycle word fits the round moving part?", "wheel", ["brake", "helmet", "basket"], "match shape and movement to one bicycle noun"),
            O("Kabir reaches a busy corner and presses the brake before the white line.", "Use brake in a sentence that explains Kabir's action.", "Kabir uses the brake to slow his bicycle safely before the corner.", [R("Uses brake as the bicycle part that slows movement.", "uses the brake", "brake to slow"), R("Connects the action to the corner or safe stopping point.", "before the corner", "safely before")], "build one complete sentence from the action and safety clues"),
            O("Rina fastens a helmet, then checks that it sits firmly above her ears.", "Explain the word helmet in this riding scene.", "A helmet is protective headgear that Rina fastens before riding her bicycle.", [R("Identifies a helmet as protection worn on the head.", "protective headgear", "protects her head"), R("Links the word to preparing for a bicycle ride.", "before riding", "riding her bicycle")], "define the word through its place and purpose"),
            O("A delivery tricycle has a wide carrier holding two sealed lunch boxes.", "What does carrier mean here, and what is it carrying?", "The carrier is the bicycle platform that holds the two lunch boxes.", [R("Explains carrier as a platform or part that holds items.", "platform that holds", "part that carries"), R("Names the visible cargo accurately.", "two lunch boxes", "lunch boxes")], "separate the named bicycle part from the objects on it"),
            O("The bicycle's bell gives one bright ring as a walker nears the narrow lane.", "Use bell in a respectful warning sentence.", "The rider rings the bell once to warn the walker without startling them.", [R("Uses bell as a warning device on the bicycle.", "rings the bell", "bell once"), R("Describes a respectful purpose for the warning.", "warn the walker", "without startling")], "turn the sound clue into a considerate purpose"),
            O("After rain, mud hides the tread on the back tyre, so Isha wipes it clean.", "Explain tyre using the scene's clues.", "A tyre is the rubber covering on a wheel, and Isha cleans mud from it.", [R("Identifies the tyre as rubber around a wheel.", "rubber covering", "rubber around a wheel"), R("Uses the cleaning detail from the supplied scene.", "cleans mud", "wipes it clean")], "combine the material clue with the cleaning action"),
            O("Dev sits on the padded part above the frame and keeps both hands steady.", "Name and explain the bicycle part Dev uses.", "Dev sits on the seat, the padded bicycle part that supports the rider.", [R("Names the seat correctly.", "the seat", "sits on the seat"), R("Explains that it supports the rider.", "supports the rider", "padded bicycle part")], "name the part and state its function in one answer"),
            C("A cyclist covers her head before joining the park path.", "Which safety word completes the scene?", "helmet", ["pedal", "carrier", "tyre"], "use the head-protection clue to recover the key word"),
            C("The bicycle keeps rolling, but the rider needs to stop at a crossing.", "Which part should the rider use first?", "brake", ["seat", "wheel", "basket"], "contrast a stopping part with parts that merely support or move"),
            C("Two round parts touch the ground and carry the frame forward.", "Which bicycle word names both round parts?", "wheels", ["bells", "helmets", "handles"], "notice the plural clue and the ground contact"),
            C("The rider pushes one foot down, and the bicycle begins moving.", "Which word names the pushed bicycle piece?", "pedal", ["brake", "seat", "carrier"], "trace the foot movement to the matching part"),
            C("A small metal sound warns people beside the cycle track.", "Which chapter word matches that warning sound?", "bell", ["wheel", "helmet", "tyre"], "use purpose and material clues together"),
        ],
        "misconception_id": "bicycle-word-job-confusion",
        "misconception": "The learner chooses a bicycle word because it is familiar but ignores the part's stated job.",
        "remediation": "Re-read the action clue, name what the part does, and then compare that job with each candidate word.",
        "assessment": [
            C("Tara squeezes a lever and her bicycle slows beside the curb.", "Which word names the part Tara uses?", "brake", ["carrier", "seat", "wheel"], "match the slowing action to a bicycle part"),
            C("A round rubber part has lost air and looks flat.", "Which chapter word fits this object?", "tyre", ["bell", "handle", "helmet"], "use both shape and air clues before choosing"),
            O("A blue basket is fixed above the front wheel and holds a raincoat.", "Use basket correctly in one complete sentence.", "The bicycle basket above the front wheel holds a blue raincoat.", [R("Uses basket as the part holding an item.", "basket", "holds"), R("Includes the raincoat or front-wheel detail.", "raincoat", "front wheel")], "write from the supplied location and object clues"),
            O("Noor puts protective headgear on before she pedals away.", "Name the headgear and explain its purpose.", "Noor wears a helmet to protect her head while riding the bicycle.", [R("Names the helmet.", "helmet"), R("States its protective riding purpose.", "protect her head", "while riding")], "give both the exact word and its safety purpose"),
        ],
    },
    {
        "level_id": "bicycle_detail_detectives",
        "title": "Ride Detail Detectives",
        "focus": "Understand explicit details in short bicycle passages",
        "outcome": "The learner answers detail questions by locating and restating visible information from a short passage.",
        "skill_ids": ["reading.sentence_comprehension"],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:comprehension:6-7"],
        "principle": "Read the whole bicycle sentence and point to the exact detail.",
        "connect": {
            "teaching_block": "A clear detail answer comes from words we can point to, not from a guess about bicycles.",
            "passage": "Omi parks his green bicycle under the neem tree after lunch.",
            "prompt": "Find the colour, place, and time details in the visible sentence, then continue.",
        },
        "tasks": [
            C("Zoya carries a yellow bottle in the basket behind her handlebar.", "What colour is Zoya's bottle?", "yellow", ["blue", "green", "red"], "look only for the stated colour word"),
            C("At seven o'clock, Aman wheels his bicycle out through the side gate.", "When does Aman take the bicycle out?", "at seven o'clock", ["after noon", "at nine o'clock", "before sunrise"], "locate the explicit time phrase"),
            C("Leela leaves her bicycle beside the guard's desk during art club.", "Where does Leela leave the bicycle?", "beside the guard's desk", ["inside the art cupboard", "behind the playground", "near the bus stop"], "separate the place detail from the activity detail"),
            O("Rohan's front wheel has a white reflector, while the back wheel has a red reflector.", "Describe both reflector details accurately.", "The front wheel has a white reflector, and the back wheel has a red reflector.", [R("States the front-wheel colour correctly.", "front wheel has a white reflector", "white reflector"), R("States the back-wheel colour correctly.", "back wheel has a red reflector", "red reflector")], "pair each colour with the correct wheel", ordered=True),
            O("Mina rides to the bakery on Saturday and returns by the shaded lane.", "Where does Mina go, and how does she return?", "Mina goes to the bakery and returns by the shaded lane.", [R("Names the bakery as Mina's destination.", "goes to the bakery", "bakery"), R("Names the shaded lane as her return way.", "returns by the shaded lane", "shaded lane")], "answer both question parts from the sentence"),
            O("A mechanic tightens the loose chain before Vikram rides to football practice.", "What does the mechanic fix, and when?", "The mechanic tightens the loose chain before Vikram rides to football practice.", [R("Names the loose chain as the part being fixed.", "loose chain", slot="repair"), R("Says the repair happens before football practice.", "before Vikram rides to football practice", slot="time")], "retain the repair detail and its time relationship", ordered=True),
            O("Sara wears a silver helmet and keeps a folded map in her purple basket.", "State Sara's helmet colour, the item in her basket, and the basket colour.", "Sara wears a silver helmet and carries a folded map in her purple basket.", [R("Gives the helmet colour.", "silver helmet", slot="helmet_colour"), R("Names the item in the basket.", "folded map", slot="basket_item"), R("Gives the basket colour.", "purple basket", slot="basket_colour")], "keep each colour and item with the correct object"),
            O("The school rack has six bicycles, but only one has a striped seat cover.", "How many bicycles are there, and what makes one different?", "There are six bicycles, and one has a striped seat cover.", [R("States that the rack holds six bicycles.", "six bicycles"), R("Identifies the striped seat cover as the difference.", "striped seat cover")], "combine the number clue with the distinguishing feature"),
            O("Nitin rings once near the walking path, then waits while two children cross.", "What two actions does Nitin take?", "Nitin rings once and then waits while two children cross.", [R("States that Nitin rings once.", "rings once"), R("States that he waits for the children to cross.", "waits", "children cross")], "retell only the two stated actions", ordered=True),
            C("Pia stores her bicycle inside the covered shed during heavy rain.", "Where is Pia's bicycle during the rain?", "inside the covered shed", ["beside the open field", "under a moving bus", "behind the market"], "identify the exact shelter phrase"),
            C("The repair shop opens at eight and closes at five.", "When does the repair shop close?", "at five", ["at eight", "at noon", "at seven"], "distinguish opening time from closing time"),
            C("Hari's bicycle has a blue frame and an orange bell.", "Which part is orange?", "the bell", ["the frame", "the seat", "the tyre"], "attach the colour to the correct noun"),
            C("Asha carries library books on the rear carrier, not in the front basket.", "What is on the rear carrier?", "library books", ["a front basket", "a helmet", "a lunch plate"], "use the contrast word to avoid the nearby distractor"),
            C("The class cycles only on the marked practice loop.", "Where does the class cycle?", "on the marked practice loop", ["on the main road", "inside the classroom", "across the pond"], "select the stated route rather than a possible route"),
        ],
        "misconception_id": "bicycle-detail-guessing",
        "misconception": "The learner answers from general bicycle knowledge instead of the exact colour, place, number, or time in the passage.",
        "remediation": "Underline the question word, find the matching phrase in the visible passage, and restate that phrase without adding facts.",
        "assessment": [
            C("The red bicycle is locked beside the music room until four o'clock.", "Where is the bicycle locked?", "beside the music room", ["inside the library", "near the kitchen", "behind the bus"], "retrieve the stated location"),
            C("Mohan carries two parcels in a square basket.", "How many parcels does Mohan carry?", "two", ["one", "three", "four"], "find the number attached to parcels"),
            O("Esha checks the front light in the evening and the bell in the morning.", "State when Esha checks each part.", "Esha checks the front light in the evening and the bell in the morning.", [R("Pairs the front light with evening.", "front light in the evening", slot="front_light"), R("Pairs the bell with morning.", "bell in the morning", slot="bell")], "keep each part with its stated time", ordered=True),
            O("A small pump rests under the seat, and a green cloth lies in the basket.", "Describe where both objects are.", "The small pump is under the seat, and the green cloth is in the basket.", [R("Places the pump under the seat.", "pump", "under the seat"), R("Places the green cloth in the basket.", "green cloth", "in the basket")], "report both object-location pairs"),
        ],
    },
    {
        "level_id": "bicycle_safe_order",
        "title": "A Safe Ride in Order",
        "focus": "Sequence bicycle preparation and journey events",
        "outcome": "The learner orders stated riding events and explains the beginning, middle, and end of a short sequence.",
        "skill_ids": ["reading.event_sequence"],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:parts-and-safety:2-5",
            f"{CHAPTER_ID}:comprehension:6-7",
        ],
        "principle": "Track bicycle actions with before, next, and finally clues.",
        "connect": {
            "teaching_block": "A safe ride has an order: preparation comes before movement, and parking comes after arrival.",
            "passage": "First Iqbal checks the tyres, next he fastens his helmet, and finally he starts riding.",
            "prompt": "Trace the three visible actions from first to final, then continue.",
        },
        "tasks": [
            C("Neha unlocks the bicycle, rolls it outside, and then closes the gate.", "Which action happens second?", "Neha rolls the bicycle outside.", ["Neha unlocks the bicycle.", "Neha closes the gate.", "Neha washes the gate."], "use the middle position rather than choosing a familiar action"),
            C("First the mechanic adds air; next he tests the brake; last he wipes the seat.", "What does the mechanic do last?", "He wipes the seat.", ["He adds air.", "He tests the brake.", "He replaces the wheel."], "follow the explicit order words to the ending"),
            C("Ravi reaches the park, parks in the rack, and walks to the pond.", "What happens immediately before Ravi walks to the pond?", "He parks in the rack.", ["He reaches the park.", "He walks to the pond before parking.", "He leaves the bicycle outside the rack."], "identify the event immediately before the final action"),
            O("Anu checks the route card, rings at the blind corner, and stops at the library rack.", "Retell Anu's three actions in order.", "Anu checks the route card, rings at the blind corner, and then stops at the library rack.", [R("Begins with checking the route card.", "checks the route card"), R("Keeps the ring and library stop in the correct order.", "rings at the blind corner", "stops at the library rack")], "use sequence words without dropping any action", ordered=True),
            O("The chain slips. Omar moves off the path, asks an adult for help, and waits beside the bench.", "Explain the response sequence after the chain slips.", "After the chain slips, Omar leaves the path, asks an adult for help, and waits beside the bench.", [R("Starts with Omar moving off the path.", "moves off the path", "leaves the path"), R("Orders asking for help before waiting by the bench.", "asks an adult", "waits beside the bench")], "separate the problem from the ordered response", ordered=True),
            O("Before the picnic ride, Jia fills her bottle. She checks her helmet strap next. Her aunt checks the bicycle last.", "Write the preparation steps from first to last.", "Jia fills her bottle, checks her helmet strap, and then her aunt checks the bicycle.", [R("Starts with filling the bottle.", "fills her bottle", slot="bottle"), R("Gives the helmet-strap check next.", "checks her helmet strap", slot="strap"), R("Ends with the aunt's bicycle check.", "aunt checks the bicycle", slot="bicycle")], "convert time clues into one accurate sequence", ordered=True),
            O("A parcel rider reaches house twelve, reads the nameplate, and places the parcel in the caretaker's hands.", "Describe the delivery order using three actions.", "The rider reaches house twelve, reads the nameplate, and hands the parcel to the caretaker.", [R("Begins with reaching house twelve.", "reaches house twelve"), R("Places reading the nameplate before handing over the parcel.", "reads the nameplate", "hands the parcel")], "keep arrival, checking, and delivery in logical order", ordered=True),
            O("Lata hears thunder, turns toward home, and parks under the covered veranda before rain begins.", "What is the event order in Lata's change of plan?", "Lata hears thunder, turns toward home, and parks under the veranda before the rain.", [R("Starts with hearing thunder.", "hears thunder"), R("Orders turning home before parking under cover.", "turns toward home", "parks under the veranda")], "track the clue that causes the route change", ordered=True),
            O("At the crossing, the guard raises a hand. The riders stop, wait, and move only after the hand lowers.", "Retell the riders' actions in the correct order.", "The riders stop, wait, and move after the guard lowers a hand.", [R("Starts with stopping.", "stop", slot="stop"), R("Gives waiting as the next action.", "wait", slot="wait"), R("Moves only after the hand lowers.", "move after the guard lowers a hand", slot="move")], "preserve the safety signal and all three actions", ordered=True),
            C("Sia fastens her helmet before she unlocks the bicycle.", "Which action comes first?", "Sia fastens her helmet.", ["Sia unlocks the bicycle.", "Sia reaches the market.", "Sia removes the wheel."], "use before as the sequence clue"),
            C("The rider signals, checks the lane, and then turns left.", "What happens just before the left turn?", "The rider checks the lane.", ["The rider turns left.", "The rider parks at home.", "The rider removes the signal."], "find the action directly before turning"),
            C("After washing the bicycle, Kunal dries the frame and oils the chain.", "What does Kunal do immediately after washing?", "He dries the frame.", ["He oils the chain.", "He rides through mud.", "He locks the shop."], "distinguish the next step from the final step"),
            C("Maya reaches school, locks her bicycle, and enters the classroom.", "Which event ends the sequence?", "Maya enters the classroom.", ["Maya reaches school.", "Maya locks her bicycle.", "Maya leaves the bicycle unlocked."], "locate the last stated event"),
            C("First check the tyres, then test the bell, and finally pack the water bottle.", "Which preparation belongs in the middle?", "test the bell", ["check the tyres", "pack the water bottle", "remove the seat"], "use first and finally to isolate the middle action"),
        ],
        "misconception_id": "bicycle-sequence-swap",
        "misconception": "The learner remembers all bicycle events but swaps the middle and ending actions or ignores sequence words.",
        "remediation": "Mark each visible event with 1, 2, and 3, then retell it using first, next, and finally before answering.",
        "assessment": [
            C("The rider checks the mirror, signals right, and turns into the lane.", "Which event happens second?", "The rider signals right.", ["The rider checks the mirror.", "The rider turns into the lane.", "The rider crosses a bridge."], "locate the middle event"),
            C("Pavan parks, locks the wheel, and gives the key to his father.", "What happens last?", "Pavan gives the key to his father.", ["Pavan parks.", "Pavan locks the wheel.", "Pavan gives the key before locking the wheel."], "follow the action chain to its end"),
            O("First Ritu fills the pump, next she adds air, and last she closes the valve.", "Retell Ritu's work in order.", "Ritu fills the pump, adds air to the tyre, and then closes the valve.", [R("Begins with filling the pump.", "fills the pump"), R("Orders adding air before closing the valve.", "adds air", "closes the valve")], "retain all three maintenance actions", ordered=True),
            O("A bell strap loosens. Veer stops riding, walks home, and asks his sister to repair it.", "Sequence Veer's response to the loose strap.", "Veer stops riding, walks home, and asks his sister to repair the loose bell strap.", [R("Places stopping before walking home.", "stops riding", "walks home"), R("Ends with asking his sister for repair help.", "asks his sister", "repair")], "order the safe response from problem to help", ordered=True),
        ],
    },
    {
        "level_id": "bicycle_clue_inference",
        "title": "What the Ride Clues Tell Us",
        "focus": "Infer reasons and safe choices from bicycle clues",
        "outcome": "The learner makes a reasonable bicycle inference and supports it with a visible clue from the supplied passage.",
        "skill_ids": ["reading.sentence_comprehension"],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:parts-and-safety:2-5",
            f"{CHAPTER_ID}:comprehension:6-7",
        ],
        "principle": "Join a bicycle clue to a sensible reason, not a wild guess.",
        "connect": {
            "teaching_block": "An inference is not written directly; it must still fit every clue in the visible bicycle scene.",
            "passage": "The front tyre feels soft, and Farah carries the bicycle toward a pump.",
            "prompt": "Think what Farah has noticed and which clue supports that idea, then continue.",
        },
        "tasks": [
            C("Dark clouds gather, so Tenzin turns on the bicycle light before leaving.", "Why does Tenzin most likely switch on the light?", "The sky is becoming dark.", ["He thinks the tyres need checking before the ride.", "He wants to test the bell before leaving.", "He plans to adjust the seat before riding."], "connect the weather clue to visibility"),
            C("Asha walks her bicycle across a crowded school gate instead of riding.", "What is the best reason for Asha's choice?", "Walking gives her more control near people.", ["Her bicycle can fly.", "The gate is under water.", "She wants to remove the seat."], "infer a safe reason from the crowd clue"),
            C("The chain clicks loudly each time Ravi pedals, and he stops beside a repair stand.", "What does Ravi probably think?", "The chain needs checking.", ["The helmet is too bright.", "The basket is full of clouds.", "The bell is reading a map."], "link the repeated sound to the part being checked"),
            O("Mili sees loose gravel near a bend and slows before reaching it.", "Why does Mili slow down? Cite the gravel clue.", "Mili slows because loose gravel near the bend could make the bicycle slip.", [R("Infers that the gravel could cause slipping or loss of control.", "gravel could make", "bicycle slip"), R("Uses the bend or loose-gravel clue from the passage.", "loose gravel", "near the bend")], "state the risk and point to the clue that creates it"),
            O("A bicycle remains locked outside the clinic while its basket holds a folded prescription.", "Where is the rider probably visiting, and why?", "The rider is probably inside the clinic because the bicycle is parked there with a prescription.", [R("Infers that the rider is visiting the clinic.", "inside the clinic", "visiting the clinic"), R("Supports the inference with the prescription or parking clue.", "folded prescription", "parked there")], "separate the likely conclusion from its visible evidence"),
            O("The back reflector is muddy after a wet lane ride, and Sona wipes it before dusk.", "Infer why Sona cleans the reflector before dusk.", "Sona cleans the muddy reflector before dusk so it can be seen clearly when the light becomes low.", [R("Infers that cleaning improves visibility.", "seen clearly", "improves visibility"), R("Connects the need to mud and approaching dusk.", "muddy", "before dusk")], "combine the dirty-part clue with the time clue"),
            O("A child chooses the smaller bicycle whose feet touch the ground while seated.", "Why is the smaller bicycle probably a better fit?", "The smaller bicycle is a better fit because the child's feet can reach the ground for control.", [R("Explains that reaching the ground improves control or balance.", "feet can reach", "for control"), R("Uses the seated-size clue from the passage.", "while seated", "smaller bicycle")], "infer fit from the child's body position"),
            O("Two riders pause at a lane entrance because a parked van blocks their view.", "What danger are the riders likely considering?", "They may not see a person or vehicle coming from behind the parked van.", [R("Infers an unseen person or vehicle may approach.", "person or vehicle", "may not see"), R("Uses the blocked-view clue caused by the parked van.", "parked van", "blocks their view")], "name the hidden risk and its exact cause"),
            O("The library rack is full, so Jai asks the guard before choosing another place.", "What does Jai's action show? Use one scene clue.", "Jai acts responsibly because he asks the guard instead of leaving the bicycle in an unsafe place.", [R("Infers that Jai is being responsible or careful.", "acts responsibly", "being careful"), R("Uses asking the guard or the full rack as evidence.", "asks the guard", "rack is full")], "infer a character quality from a specific decision"),
            C("A tyre leaves a wavy track and loses air overnight.", "What likely needs repair?", "a puncture in the tyre", ["a colour on the seat", "a song in the bell", "a label on the basket"], "combine the air-loss and track clues"),
            C("The rider wears a bright vest on a foggy morning.", "Why is the bright vest useful?", "It helps other people see the rider.", ["It makes the road shorter.", "It fills the tyres with air.", "It turns the bicycle into a boat."], "connect brightness with poor visibility"),
            C("A bicycle is dry except for drops below the bottle holder.", "What probably happened?", "The bottle leaked.", ["The wheel melted.", "The helmet rang.", "The road climbed the bicycle."], "use the exact location of the drops"),
            C("Navi moves the bicycle under a roof when hail begins.", "Why does Navi choose the roof?", "to protect the bicycle and rider", ["to make the hail louder", "to hide the pedals forever", "to turn night into morning"], "infer protection from the weather change"),
            C("The cyclist raises one hand before moving toward the right lane.", "What is the hand movement probably doing?", "showing an intended turn", ["measuring the wheel", "holding up the road", "asking the bicycle to sleep"], "link the signal to the next movement"),
        ],
        "misconception_id": "bicycle-inference-without-evidence",
        "misconception": "The learner gives a possible bicycle idea but cannot connect it to a clue that appears in the supplied scene.",
        "remediation": "Say the likely idea, add because, and complete the sentence with the exact object, action, or condition that supports it.",
        "assessment": [
            O("The bicycle lamp looks dim, and Ana replaces its batteries.", "What did Ana probably notice? Support your idea.", "Ana probably noticed that the lamp needed more power because its light looked dim.", [R("Infers that the lamp needed more power.", "lamp needed more power", "needed batteries"), R("Uses the dim-light clue as support.", "looked dim", "dim light")], "connect dim light with battery power"),
            O("Raj stops before a puddle whose bottom cannot be seen.", "Why is stopping a sensible choice?", "Stopping is sensible because the deep-looking puddle may hide a hole that could catch a wheel.", [R("Infers that the puddle may hide a hole or hazard.", "may hide a hole", "hidden hazard"), R("Explains the possible bicycle risk.", "catch a wheel", "unsafe to enter")], "infer an unseen hazard from unclear depth"),
            O("A bell makes no sound, although the lever moves freely, so Iman visits a repair stall.", "What does Iman infer, and which clue supports it?", "Iman infers that the bell is faulty because its lever moves but no sound comes out.", [R("Infers that the bell is faulty or needs repair.", "bell is faulty", "needs repair"), R("Uses the moving lever and missing sound as evidence.", "lever moves", "no sound")], "state both the conclusion and the paired clues"),
            O("A rider chooses the longer park path because the short lane has broken glass.", "Why is the longer path the better choice?", "The longer park path is safer because the short lane contains broken glass that could damage a tyre.", [R("Explains that the longer path is safer.", "longer park path is safer", "safer path"), R("Uses the broken-glass tyre risk as evidence.", "broken glass", "damage a tyre")], "justify the route choice from the hazard clue"),
        ],
    },
    {
        "level_id": "bicycle_word_classes",
        "title": "Names, Actions, and Describing Words",
        "focus": "Use nouns, verbs, and adjectives in bicycle sentences",
        "outcome": "The learner identifies and uses bicycle nouns, action verbs, and fitting adjectives in complete sentences.",
        "skill_ids": ["grammar.noun_verb_adjective"],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:language-use:4-5"],
        "principle": "Build bicycle sentences with a name, an action, and a useful description.",
        "connect": {
            "teaching_block": "A noun names the bicycle or part, a verb shows action, and an adjective adds a clear detail.",
            "passage": "The careful rider polishes the dusty frame beside the gate.",
            "prompt": "Find the naming, action, and describing words in this visible sentence, then continue.",
        },
        "tasks": [
            C("The bright bell rings near the corner.", "Which word is the action verb?", "rings", ["bright", "bell", "corner"], "ask what the bell does"),
            C("A sturdy helmet protects Mira's head.", "Which word describes the helmet?", "sturdy", ["helmet", "protects", "head"], "separate the describing word from the naming word"),
            C("The mechanic oils the chain carefully.", "Which word is the bicycle-part noun?", "chain", ["mechanic", "oils", "carefully"], "find the word that names a bicycle part"),
            O("Words: rider, checks, loose, brake. Use all four in one sentence.", "Write the complete bicycle sentence.", "The rider checks the loose brake.", [R("Uses rider and brake as naming words.", "rider", "brake"), R("Uses checks as the action and loose as the description.", "checks", "loose")], "place the noun, verb, adjective, and object naturally", interaction_type="short_text", min_words=6),
            O("The sentence says: A silver bicycle waits quietly. Identify the noun and adjective, then explain their jobs.", "Which two words do you choose, and why?", "Bicycle is the noun because it names the object, and silver is the adjective because it describes the bicycle.", [R("Identifies bicycle as the naming word.", "bicycle is the noun", "bicycle names"), R("Identifies silver as the describing word.", "silver is the adjective", "silver describes")], "label each word by the job it performs"),
            O("A child pushes a heavy bicycle up a ramp.", "Name the action word and the describing word.", "Pushes is the action verb, and heavy is the adjective describing the bicycle.", [R("Identifies pushes as the action verb.", "pushes", "action verb"), R("Identifies heavy as the describing adjective.", "heavy", "adjective")], "use the movement and description clues"),
            O("A tiny bell gives a cheerful ring outside the shop.", "Write one new sentence using bell, rings, and cheerful.", "The cheerful bell rings beside the bicycle shop.", [R("Uses bell as the noun.", "bell", slot="noun"), R("Uses rings as the action.", "rings", slot="verb"), R("Uses cheerful as a describing word.", "cheerful", slot="adjective")], "use the three word jobs in a fresh sentence", interaction_type="short_text", min_words=6),
            O("Nouns: basket and map. Verb: holds. Adjective: folded.", "Combine the supplied words into one natural sentence.", "The basket holds a folded map.", [R("Uses basket and map as the named things.", "basket", "map"), R("Uses holds as the action and folded as the description.", "holds", "folded")], "keep every supplied word in a sensible role", interaction_type="short_text", min_words=6),
            O("The smooth tyre rolls over the clean path.", "Explain the jobs of smooth and rolls.", "Smooth describes the tyre, while rolls tells the tyre's action.", [R("Explains that smooth describes the tyre.", "smooth describes", "smooth tyre"), R("Explains that rolls names the action.", "rolls", "action")], "contrast a describing word with an action word"),
            C("The noisy bell warns a walker.", "Which word describes the bell?", "noisy", ["bell", "warns", "walker"], "look for the quality attached to the noun"),
            C("A rider steers around the cone.", "Which word shows the rider's action?", "steers", ["rider", "around", "cone"], "ask what the rider is doing"),
            C("The red carrier holds a box.", "Which word is the bicycle-part noun?", "carrier", ["red", "holds", "box"], "choose the named part rather than its colour"),
            C("A narrow lane curves behind the school.", "Which word describes the lane?", "narrow", ["lane", "curves", "school"], "attach the adjective to the noun it modifies"),
            C("The cyclist waves at the guard.", "Which cyclist-sentence word is the verb?", "waves", ["cyclist", "guard", "the"], "locate the action performed by the cyclist"),
        ],
        "misconception_id": "bicycle-word-class-mixup",
        "misconception": "The learner labels a word by its position in the sentence rather than by whether it names, acts, or describes.",
        "remediation": "Ask three checks in order: what is named, what happens, and what detail is added; then label each answer.",
        "assessment": [
            C("The careful mechanic tightens the loose chain.", "Which word is the action verb?", "tightens", ["careful", "mechanic", "loose"], "identify what the mechanic does"),
            C("A shiny reflector catches the light.", "Which word describes the reflector?", "shiny", ["reflector", "catches", "light"], "find the quality word before the noun"),
            O("Words: helmet, protects, young, rider. Make one complete sentence.", "How can these words form a natural sentence?", "The helmet protects the young rider.", [R("Uses helmet and rider as nouns.", "helmet", "rider"), R("Uses protects as the verb and young as the adjective.", "protects", "young")], "assign each word its grammar job", interaction_type="short_text", min_words=6),
            O("The quick cyclist pedals uphill. Identify one noun, one verb, and one adjective.", "Label the three selected words.", "Cyclist is a noun, pedals is a verb, and quick is an adjective.", [R("Correctly labels cyclist and pedals.", "cyclist is a noun", "pedals is a verb"), R("Correctly labels quick as an adjective.", "quick is an adjective", "quick describes")], "label the words from their jobs in the sentence"),
        ],
    },
    {
        "level_id": "bicycle_reasoned_responses",
        "title": "My Safe Bicycle Ideas",
        "focus": "Construct complete reasoned responses about riding",
        "outcome": "The learner writes a relevant bicycle choice and supports it with a clear reason in complete English sentences.",
        "skill_ids": [
            "reading.sentence_comprehension",
            "writing.complete_sentence",
        ],
        "assessment_skill_ids": ["writing.complete_sentence"],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:comprehension:6-7",
            f"{CHAPTER_ID}:draw-magic-cycle:6-6",
            f"{CHAPTER_ID}:listen-and-speak:3-4",
        ],
        "principle": "State a bicycle choice clearly and support it with a scene-based reason.",
        "connect": {
            "teaching_block": "A strong response tells what the rider should do and why that choice fits the visible situation.",
            "passage": "A new rider can choose a quiet practice yard or a crowded market lane.",
            "prompt": "Think of one suitable choice and one reason from the scene, then continue.",
        },
        "tasks": [
            C("Maya's helmet strap feels loose before practice, and an adult helper stands nearby.", "Who is available to help Maya with the strap?", "the adult helper", ["a distant shopkeeper", "an absent rider", "a bus driver"], "retrieve the helper named in the visible scene", skills=["reading.sentence_comprehension"]),
            O("The park path has walkers on one side and an empty marked cycle lane on the other.", "Where should the rider go, and why?", "The rider should use the marked cycle lane because it keeps the walking side clear.", [R("Chooses the marked cycle lane.", "marked cycle lane", "use the cycle lane"), R("Explains that the choice protects space for walkers.", "walking side clear", "keeps walkers safe")], "use both path details to justify the location", min_words=10),
            O("A friend's bicycle bell is broken before a ride through several blind corners.", "Suggest a responsible plan with a reason.", "The friends should repair the bell before riding because they need a clear warning at blind corners.", [R("Suggests repairing the bell before the ride.", "repair the bell", "before riding"), R("Links the repair to warning at blind corners.", "warning", "blind corners")], "identify the missing safety tool and its purpose", min_words=11),
            O("Rain starts while Reva is near a covered shop and ten minutes from home.", "What could Reva safely decide? Explain why.", "Reva could wait under the covered shop because wet roads may be slippery and the shelter is nearby.", [R("States a safe choice such as waiting under cover.", "wait under", "covered shop"), R("Supports it with the wet-road or nearby-shelter clue.", "wet roads", "slippery", "shelter")], "choose from the visible options and defend the safer one", min_words=12),
            O("You are designing a library bicycle with a waterproof book box and a soft light.", "Choose one more useful feature and explain its job.", "I would add a strong lock because it would keep the library bicycle secure while books are delivered.", [R("Adds one clear and suitable bicycle feature.", "strong lock", "add a lock"), R("Explains how the feature helps the library journey.", "keep", "secure", "books")], "invent one feature that solves a real library-ride need", interaction_type="creative_continuation", min_words=12),
            O("A school wants a bicycle route that passes a garden but avoids a busy gate.", "Propose a route choice and give one reason.", "The route should follow the garden path and enter through the quiet side gate because it avoids heavy traffic.", [R("Proposes the garden path and a quiet entrance.", "garden path", "quiet side gate"), R("Explains that the route avoids busy traffic.", "avoids heavy traffic")], "turn two route conditions into a practical suggestion", interaction_type="creative_continuation", min_words=12),
            O("A magic bicycle can carry one helpful tool to a hill village after a storm.", "What should it carry, and why would that help?", "It should carry a first-aid box because villagers may need simple medical supplies after the storm.", [R("Chooses one helpful item to carry.", "first-aid box", "medical supplies"), R("Explains why the village may need it after the storm.", "after the storm", "villagers may need")], "keep the imaginative idea useful and connected to the storm", interaction_type="creative_continuation", min_words=12),
            O("The class can paint the bicycle rack brightly or add numbered spaces with clear labels.", "Which improvement would you choose, and why?", "I would add numbered spaces because clear labels help riders find and park in the correct place.", [R("Chooses one stated rack improvement.", "numbered spaces", "paint the rack"), R("Provides a practical reason linked to parking.", "find and park in the correct place")], "select one improvement and explain its direct benefit", min_words=11),
            O("A younger child wants to practise but cannot yet start or stop smoothly.", "Write kind advice with a reason.", "Practise in a quiet open area with an adult because there is space to learn safe starts and stops.", [R("Gives kind, practical practice advice.", "quiet open area", "with an adult"), R("Explains how the setting helps starts and stops.", "space", "safe starts", "stops")], "make the advice supportive rather than blaming", min_words=12),
            O("A rider finds a deep crack across the usual path, while a smooth lane is open nearby.", "Recommend an action and justify it.", "The rider should take the smooth nearby lane because the crack could catch a wheel.", [R("Recommends the smooth nearby lane.", "smooth nearby lane", "take the smooth lane"), R("Explains the wheel danger from the crack.", "crack", "catch a wheel")], "connect the alternate route to the exact hazard", min_words=10),
            O("Your bicycle basket is small, but three heavy books must reach the reading club.", "What is a safe solution, and why?", "I would make two trips or ask an adult for help because overloading the small basket could make steering difficult.", [R("Offers a safe carrying solution.", "two trips", "ask an adult"), R("Explains the steering risk of overloading.", "overloading", "steering difficult")], "solve the carrying problem without inventing extra equipment", min_words=12),
            O("A community path has no sign where cyclists and walkers meet.", "Suggest one sign and explain its purpose.", "A 'Slow and Share the Path' sign would remind cyclists to reduce speed near walkers.", [R("Suggests a clear shared-path sign.", "Slow and Share", "share the path"), R("Explains that it guides cyclists near walkers.", "reduce speed", "near walkers")], "write a brief sign idea and its safety purpose", min_words=10),
            O("A bicycle club has one pump for six riders before a morning trip.", "How should the group use it fairly? Give a reason.", "The riders should take short turns in a list because everyone needs a fair chance to check tyre air.", [R("Proposes an ordered or timed turn system.", "short turns", "in a list"), R("Explains that every rider needs a fair chance.", "everyone", "fair chance")], "include both a workable sharing method and fairness reason", min_words=12),
            O("A child wants to decorate a helmet but must keep every safety label visible.", "Give a creative decoration idea that follows the rule.", "The child could add small star stickers between the labels so the safety information stays easy to read.", [R("Gives a specific decoration idea.", "star stickers", "small stickers"), R("Keeps safety labels visible and readable.", "between the labels", "easy to read")], "balance the creative choice with the stated safety limit", interaction_type="creative_continuation", min_words=12),
        ],
        "misconception_id": "bicycle-reason-missing-link",
        "misconception": "The learner states a bicycle preference or repeats the scene but does not explain why the choice fits the supplied conditions.",
        "remediation": "Use the frame 'I choose ___ because ___'; fill the second part with one exact benefit, risk, or need from the passage.",
        "assessment": [
            O("The usual bicycle rack is wet with paint, and a temporary rack stands beside the office.", "Where should a rider park, and why?", "The rider should use the temporary rack because the usual rack has wet paint.", [R("Chooses the temporary rack.", "temporary rack"), R("Uses the wet-paint clue as the reason.", "wet paint", "usual rack")], "state the available choice and its direct reason", min_words=10),
            O("A child can carry a glass jar in an open basket or ask an adult to transport it safely.", "Which choice is better? Explain.", "Asking an adult is better because the glass jar could fall from the open bicycle basket and break.", [R("Chooses adult help for the jar.", "asking an adult", "adult help"), R("Explains the falling or breaking risk.", "could fall", "break")], "compare the two options using the fragile-object clue", min_words=11),
            O("Design a bicycle feature for a rider who travels home after sunset on a quiet road.", "Name the feature and explain how it helps.", "I would add a bright front light because it helps the rider see the road and be noticed after sunset.", [R("Names a suitable visibility feature.", "bright front light", "reflective strip"), R("Explains its after-sunset benefit.", "see the road", "be noticed", "after sunset")], "create a feature for the stated time and setting", interaction_type="creative_continuation", min_words=12),
            O("The class has five helmets in different sizes for a practice day.", "How should learners choose fairly and safely?", "Each learner should try a helmet with adult help and use the size that fits securely, then return it for the next turn.", [R("Explains choosing a secure fit with adult help.", "fits securely", "adult help"), R("Includes a fair return or turn-taking step.", "return it", "next turn")], "combine fit safety with fair shared use", min_words=14),
        ],
    },
]


EXTRA_DEPTH = {
    "bicycle_words_in_action": D(
        C("A small metal dome on the handlebar makes a clear ring near the gate.", "Which bicycle word names the ringing part?", "bell", ["pedal", "seat", "tyre"], "use the metal-sound clue to identify the part"),
        C("A linked metal loop moves over the toothed wheels when the rider pedals.", "Which bicycle word fits the moving metal loop?", "chain", ["basket", "helmet", "brake"], "match the linked loop with its bicycle name"),
        O("A red piece shines back when a car lamp points toward the bicycle.", "Explain what the red piece does and why it helps.", "The red reflector returns light so the bicycle is easier to notice.", [R("States the reflector action.", "red reflector returns light"), R("States the visibility benefit.", "bicycle is easier to notice")], "connect reflected light with being seen", min_words=10),
        O("Mala holds the curved bar and guides her bicycle around a cone.", "Use handlebar in a sentence that includes Mala's action.", "Mala grips the handlebar firmly and steers around the cone.", [R("Uses handlebar as the held bicycle part.", "grips the handlebar"), R("States the steering action.", "steers around the cone")], "name the part and its guiding job", interaction_type="short_text", min_words=8),
        O("A cargo cycle has a broad platform above its back wheel for seed bags.", "Name the platform and explain its use.", "The cargo cycle uses a wide carrier to hold the seed bags.", [R("Names the platform as a carrier.", "wide carrier"), R("States what the carrier holds.", "hold the seed bags")], "use the part word in a working-cycle description", min_words=10),
    ),
    "bicycle_detail_detectives": D(
        C("Uma locks her bicycle beside the science room before music practice.", "Where does Uma lock the bicycle?", "beside the science room", ["inside the music cupboard", "behind the kitchen", "near the pond"], "locate the stated room rather than the later activity"),
        C("The repair note says: front tyre, thirty pumps; back tyre, twenty-eight pumps.", "How many pumps are listed for the back tyre?", "twenty-eight", ["thirty", "eighteen", "forty"], "pair the number with the correct tyre"),
        O("A green pump hangs below the shelf, and a black lock rests inside the basket.", "State where both bicycle items are kept.", "The green pump hangs below the shelf, and the black lock rests inside the basket.", [R("Places the pump below the shelf.", "green pump hangs below the shelf"), R("Places the lock inside the basket.", "black lock rests inside the basket")], "report both visible item-place pairs", min_words=12),
        O("Tanu rides on Monday morning and returns the borrowed bicycle on Tuesday evening.", "Give the riding time and the return time.", "Tanu rides on Monday morning and returns the bicycle on Tuesday evening.", [R("States the riding time.", "rides on Monday morning"), R("States the return time.", "returns the bicycle on Tuesday evening")], "keep each action with its printed time", min_words=10),
        O("A club notice says the blue rack is for visitors and the yellow rack is for members.", "Explain which rack each group should use.", "Visitors use the blue rack, while members use the yellow rack.", [R("Pairs visitors with blue.", "Visitors use the blue rack"), R("Pairs members with yellow.", "members use the yellow rack")], "match the details in a written notice", min_words=9),
    ),
    "bicycle_safe_order": D(
        C("Kavi checks the bell, fills his bottle, and finally locks the shed.", "What does Kavi do immediately before locking the shed?", "He fills his bottle.", ["He checks the bell.", "He opens the shed.", "He starts riding."], "find the middle event before the final action"),
        C("Before Nira turns right, she looks behind and gives a hand signal.", "Which action is stated before the hand signal?", "She looks behind.", ["She turns right.", "She parks the bicycle.", "She crosses a bridge."], "follow the two preparation actions in order"),
        O("First Ali wipes the seat. Next he tests the light. Last he packs his raincoat.", "Retell Ali's three preparations in order.", "Ali wipes the seat first, tests the light next, and packs his raincoat last.", [R("States the first action.", "wipes the seat first"), R("States the middle action.", "tests the light next"), R("States the final action.", "packs his raincoat last")], "turn the printed order words into one sequence", ordered=True, min_words=12),
        O("The riders stop at the red flag, wait for the path to clear, and then cross together.", "Explain the safe crossing order.", "The riders stop at the red flag, wait for a clear path, and then cross together.", [R("Places stopping first.", "stop at the red flag"), R("Places waiting second.", "wait for a clear path"), R("Places crossing last.", "then cross together")], "preserve all three safety actions", ordered=True, min_words=13),
        O("A library cart reaches the lift, enters after the doors open, and leaves on the second floor.", "Retell the library cart's journey in order.", "The cart reaches the lift, enters after the doors open, and leaves on the second floor.", [R("States the lift arrival.", "cart reaches the lift"), R("States the entry condition.", "enters after the doors open"), R("States the final floor.", "leaves on the second floor")], "apply event ordering beyond a bicycle trip", ordered=True, min_words=14),
    ),
    "bicycle_clue_inference": D(
        C("The front lamp flickers whenever the bicycle crosses a bump.", "What most likely needs checking?", "the lamp connection", ["the basket colour", "the rider's shoelace", "the road name"], "link the flicker to a loose connection"),
        C("Mira sees fresh oil under the chain and hears no squeak on the next ride.", "What probably improved the ride?", "the oiled chain", ["a painted basket", "a larger bell", "a new road sign"], "use the oil and quiet-chain clues together"),
        O("The back tyre feels soft, and the pump gauge shows a low number.", "What can the rider infer? Give the clue.", "The back tyre needs more air because the gauge shows a low number.", [R("States the likely tyre need.", "back tyre needs more air"), R("Uses the gauge evidence.", "gauge shows a low number")], "join one inference to one visible measure", min_words=11),
        O("A cyclist chooses the shaded lane after noticing steam rising from the sunny road.", "Why is the shaded lane a sensible choice?", "The shaded lane is cooler because steam rises from the sunny road.", [R("Infers the cooler route.", "shaded lane is cooler"), R("Uses the heat clue.", "steam rises from the sunny road")], "support the route inference with the printed condition", min_words=10),
        O("A trolley wheel leaves a dark line and stops turning smoothly.", "Use the clue to infer the wheel problem.", "The trolley wheel may be stuck because it leaves a dark line.", [R("States the possible problem.", "trolley wheel may be stuck"), R("Uses the dark-line clue.", "leaves a dark line")], "use clue-based reasoning for another wheel", min_words=10),
    ),
    "bicycle_word_classes": D(
        C("The patient mechanic lifts the rusty bicycle.", "Which word describes the mechanic?", "patient", ["mechanic", "lifts", "bicycle"], "attach the quality word to the person"),
        C("A narrow tyre rolls across the mat.", "Which word tells what the tyre does?", "rolls", ["narrow", "tyre", "mat"], "ask what the tyre does"),
        O("The gentle rider carries a heavy lock.", "Label rider, carries, gentle, and heavy.", "Rider is a noun, carries is a verb, and gentle and heavy are adjectives.", [R("Labels rider.", "Rider is a noun"), R("Labels carries.", "carries is a verb"), R("Labels gentle.", "gentle"), R("Labels heavy.", "heavy")], "give each visible word its grammar job", min_words=12),
        O("Words: bright, lamp, shines, steadily. Build a sentence and name the adjective.", "Write the sentence and identify the describing word.", "The bright lamp shines steadily, and bright is the adjective.", [R("Builds the supplied sentence.", "bright lamp shines steadily"), R("Labels the adjective.", "bright is the adjective")], "combine the words before naming their jobs", interaction_type="short_text", min_words=9),
        O("The quiet scooter carries a red parcel.", "Name the noun, verb, and two adjectives in the scooter sentence.", "Scooter is a noun, carries is a verb, and quiet and red are adjectives.", [R("Labels scooter.", "Scooter is a noun"), R("Labels carries.", "carries is a verb"), R("Labels quiet.", "quiet"), R("Labels red.", "red")], "classify words in a related travel sentence", min_words=12),
    ),
    "bicycle_reasoned_responses": D(
        C("The practice yard is empty, but the market lane has delivery trucks.", "Which place gives the new rider more open space?", "the practice yard", ["the market lane", "a delivery truck", "the loading gate"], "choose from the two visible settings", skills=["reading.sentence_comprehension"]),
        C("A route notice marks Pine Lane closed and River Lane open.", "Which lane is available to the rider?", "River Lane", ["Pine Lane", "both lanes", "neither lane"], "read the written route condition", skills=["reading.sentence_comprehension"]),
        O("A rider has a loose shoelace and a bench stands beside the path.", "What should the rider do, and why?", "The rider should stop beside the bench because the loose shoelace could catch.", [R("States the safe action.", "stop beside the bench"), R("States the catching risk.", "loose shoelace could catch")], "link the nearby stopping place to the visible risk", min_words=11),
        O("The cycle lane is dry, while leaves cover the shorter footpath.", "Choose the safer way and support your choice.", "The rider should use the dry cycle lane because leaves cover the footpath.", [R("Chooses the cycle lane.", "use the dry cycle lane"), R("Uses the leaf-covered path clue.", "leaves cover the footpath")], "compare both printed path conditions", min_words=11),
        O("A reading club needs a bicycle feature that keeps story cards dry in rain.", "Create one useful feature and explain its job.", "I would add a covered card box because it keeps the story cards dry.", [R("Creates a covered box feature.", "covered card box"), R("Explains the dry-card benefit.", "keeps the story cards dry")], "explain a design for a reading-club need", interaction_type="creative_continuation", min_words=12),
    ),
}

LAUNCH_DEPTH = {
    "bicycle_words_in_action": L(
        O(
            "A cycle used in the school garden has a curved mudguard above its back wheel. The cover stops muddy water from splashing the seed box.",
            "Explain mudguard from the clue and use it for this cycle.",
            "A mudguard is a wheel cover. The cycle's mudguard keeps muddy water off the seed box.",
            [
                R("Explains the part word.", "mudguard is a wheel cover", "cover above a wheel"),
                R("Uses the word for its job.", "mudguard keeps muddy water off", "stops muddy water from splashing"),
            ],
            "connect the unfamiliar part to the visible protection job",
            min_words=13,
        ),
        O(
            "A milk seller fixes a flat metal carrier above the rear wheel. A small crate rests safely on it during the morning round.",
            "State what carrier means here and use the word in a new sentence.",
            "A carrier is a platform for loads. The metal carrier holds the milk crate above the wheel.",
            [
                R("Explains carrier in context.", "carrier is a platform for loads", "platform for loads"),
                R("Uses carrier accurately.", "metal carrier holds the milk crate", "carrier holds the crate"),
            ],
            "use the platform and crate clues to explain the bicycle word",
            min_words=14,
        ),
        O(
            "At the repair corner, Noor squeezes a small brake lever beside the handle grip. The bicycle slows before the painted line.",
            "Explain the lever's job and write one sentence using brake.",
            "The lever controls the brake to slow the bicycle. Noor uses the brake before the painted line.",
            [
                R("States the slowing job.", "brake to slow the bicycle", "controls the brake"),
                R("Uses brake in the scene.", "uses the brake before the painted line", "brake before the line"),
            ],
            "link the hand control to the slowing action",
            min_words=13,
        ),
    ),
    "bicycle_detail_detectives": L(
        O(
            "The library cycle log says: Tara borrows the blue helmet at two o'clock and returns it at four o'clock beside the reading room.",
            "Report the helmet colour, borrowing time, and return place.",
            "Tara borrows the blue helmet at two o'clock and returns it beside the reading room.",
            [
                R("Gives the helmet colour.", "blue helmet", slot="helmet_colour"),
                R("Gives the borrowing time.", "two o'clock", slot="borrowing_time"),
                R("Gives the return place.", "beside the reading room", slot="return_place"),
            ],
            "keep each time and place attached to the correct action",
            min_words=14,
        ),
        O(
            "A parking card says visitors use the red rack near the gate. Staff use the silver rack behind the office.",
            "Tell which rack and place belong to each group.",
            "Visitors use the red rack near the gate, while staff use the silver rack behind the office.",
            [
                R("Gives the visitors' rack.", "red rack", slot="visitor_rack"),
                R("Gives the visitors' place.", "near the gate", slot="visitor_place"),
                R("Gives the staff rack.", "silver rack", slot="staff_rack"),
                R("Gives the staff place.", "behind the office", slot="staff_place"),
            ],
            "match each group with its printed colour and location",
            min_words=14,
        ),
        O(
            "The repair tag lists a new battery for the front light and a clean cloth for the back reflector. Both jobs are due on Friday.",
            "State the two parts, their jobs, and the shared day.",
            "The front light needs a new battery, the back reflector needs cleaning, and both jobs are due on Friday.",
            [
                R("Reports the light job.", "front light needs a new battery", "new battery for the front light"),
                R("Reports the reflector job.", "back reflector needs cleaning", "clean cloth for the back reflector"),
                R("Reports the due day.", "both jobs are due on Friday", "due on Friday"),
            ],
            "collect every exact detail from the short repair tag",
            min_words=16,
        ),
    ),
    "bicycle_safe_order": L(
        O(
            "For the seed delivery, Pihu ties the box to the carrier, checks the strap, and then rides to the school garden.",
            "Retell all three delivery steps in order.",
            "Pihu ties the seed box to the carrier, checks the strap, and then rides to the school garden.",
            [
                R("States the first step.", "ties the seed box to the carrier", "ties the box"),
                R("States the middle check.", "checks the strap", "strap check"),
                R("States the final trip.", "rides to the school garden", "then rides to the garden"),
            ],
            "preserve the securing, checking, and riding sequence",
            ordered=True,
            min_words=15,
        ),
        O(
            "A tyre loses air near the park. Rohan stops, moves the bicycle away from the road, and calls his aunt for help.",
            "Explain the safe response from first action to last.",
            "Rohan stops first, moves the bicycle away from the road, and finally calls his aunt for help.",
            [
                R("Gives the stop first.", "stops first", "Rohan stops"),
                R("Gives the safe move.", "moves the bicycle away from the road", "away from the road"),
                R("Gives the final call.", "calls his aunt for help", "finally calls his aunt"),
            ],
            "use the puncture scene to order three safety actions",
            ordered=True,
            min_words=15,
        ),
        O(
            "Before sports practice, Leela fastens her helmet, checks that the court is clear, and raises her hand before starting.",
            "Write Leela's preparation steps in the correct order.",
            "Leela fastens her helmet, checks the empty court, and raises her hand before she starts riding.",
            [
                R("Gives the helmet step.", "fastens her helmet", "helmet first"),
                R("Gives the court check.", "checks the empty court", "checks that the court is clear"),
                R("Gives the start signal.", "raises her hand before she starts", "raises her hand"),
            ],
            "track the equipment, space, and signal checks",
            ordered=True,
            min_words=14,
        ),
    ),
    "bicycle_clue_inference": L(
        O(
            "The bicycle bell stays silent when Aarav presses it. He can also see a loose wire below the bell cap.",
            "What probably needs repair, and which clue shows this?",
            "The bell connection probably needs repair because a loose wire is visible below the cap.",
            [
                R("States the likely repair.", "bell connection probably needs repair", "connection needs repair"),
                R("Uses the visible clue.", "because a loose wire is visible", "loose wire below the cap"),
            ],
            "join the silent bell to the visible wire evidence",
            min_words=12,
        ),
        O(
            "On a gentle hill, the chain slips twice even though Mehak pedals steadily. The gear teeth look worn and uneven.",
            "What can Mehak infer, and why?",
            "Mehak may infer that the worn gear needs checking because the chain keeps slipping on it.",
            [
                R("States a likely gear problem.", "may infer that the worn gear needs checking", "worn gear needs checking"),
                R("Uses the chain clue.", "because the chain keeps slipping", "chain slips twice"),
            ],
            "base the inference on both the movement and worn teeth",
            min_words=13,
        ),
        O(
            "After the ride, the bottle holder is empty and a wet trail runs from the bicycle to the tap. The bottle cap is crooked.",
            "Why is the bottle probably empty? Use two clues.",
            "The bottle probably leaked because its cap is crooked and a wet trail leads back to the tap.",
            [
                R("States the likely leak.", "bottle probably leaked", "probably empty because it leaked"),
                R("Uses the cap clue.", "because its cap is crooked", "cap is crooked"),
                R("Uses the trail clue.", "wet trail leads back to the tap", "wet trail"),
            ],
            "explain the likely cause from two stated signs",
            min_words=15,
        ),
    ),
    "bicycle_word_classes": L(
        O(
            "The cheerful courier pushes a loaded bicycle cart.",
            "Classify courier, pushes, cheerful, and loaded.",
            "Courier is a noun, pushes is a verb, and cheerful and loaded are adjectives.",
            [
                R("Labels courier.", "Courier is a noun", "courier names a person"),
                R("Labels pushes.", "pushes is a verb", "pushes shows action"),
                R("Labels cheerful.", "cheerful", "cheerful is an adjective"),
                R("Labels loaded.", "loaded", "loaded is an adjective"),
            ],
            "check what names, acts, and describes in the delivery scene",
            min_words=13,
        ),
        O(
            "A tiny silver bell rings beside the busy crossing.",
            "Give the word jobs of bell, rings, tiny, and busy.",
            "Bell is a noun, rings is a verb, and tiny and busy are adjectives.",
            [
                R("Labels bell.", "Bell is a noun", "bell names a thing"),
                R("Labels rings.", "rings is a verb", "rings shows action"),
                R("Labels tiny.", "tiny", "tiny is an adjective"),
                R("Labels busy.", "busy", "busy is an adjective"),
            ],
            "classify the naming, action, and describing words",
            min_words=13,
        ),
        O(
            "The careful child parks a muddy cycle under the shelter.",
            "Name the noun, verb, and two adjectives from the sentence.",
            "Child is a noun, parks is a verb, and careful and muddy are adjectives.",
            [
                R("Labels child.", "Child is a noun", "child names a person"),
                R("Labels parks.", "parks is a verb", "parks shows action"),
                R("Labels careful.", "careful", "careful is an adjective"),
                R("Labels muddy.", "muddy", "muddy is an adjective"),
            ],
            "use each word's job in the parking sentence",
            min_words=13,
        ),
    ),
    "bicycle_reasoned_responses": L(
        O(
            "A fallen branch blocks the usual lane to the library. A smooth paved side lane is open and reaches the same gate.",
            "Choose a route and explain why it fits the scene.",
            "The rider should take the paved side lane because the branch blocks the usual lane and both routes reach the library.",
            [
                R("Chooses the open route.", "take the paved side lane", "paved side lane"),
                R("Uses the blockage reason.", "because the branch blocks the usual lane", "branch blocks the usual lane"),
                R("Uses the shared destination.", "both routes reach the library", "reaches the same gate"),
            ],
            "make the choice from the two route conditions",
            min_words=17,
        ),
        O(
            "Four riders need one pump before practice, and the coach has written their names on a board. Practice begins in twenty minutes.",
            "Suggest a fair pump plan and give a reason.",
            "The riders should take short turns in the written order because everyone can check a tyre before practice.",
            [
                R("Gives a fair method.", "short turns in the written order", "take turns in order"),
                R("Explains the benefit.", "everyone can check a tyre before practice", "everyone gets a tyre check"),
            ],
            "use the name list and time limit to make a workable plan",
            min_words=15,
        ),
        O(
            "Dirt covers both reflectors before an evening ride. A clean cloth is in the repair basket, and sunset is near.",
            "Recommend one action and justify it from the clues.",
            "The rider should wipe both reflectors with the cloth because clean reflectors are easier to notice after sunset.",
            [
                R("Recommends the cleaning action.", "wipe both reflectors with the cloth", "clean both reflectors"),
                R("Explains the evening benefit.", "easier to notice after sunset", "visible after sunset"),
            ],
            "connect the available cloth to evening visibility",
            min_words=15,
        ),
    ),
}

for _level_spec in LEVEL_SPECS:
    _level_spec["depth"] = EXTRA_DEPTH[_level_spec["level_id"]]
    _level_spec["launch_depth"] = LAUNCH_DEPTH[_level_spec["level_id"]]


MANIFEST = build_manifest(
    chapter={
        "chapter_id": CHAPTER_ID,
        "chapter_no": 1,
        "title": "My Bicycle",
        "book_title": "Mridang",
        "unit_title": "Fun with Friends",
        "source_url": SOURCE_URL,
    },
    source_anchors=SOURCE_ANCHORS,
    level_specs=LEVEL_SPECS,
)
