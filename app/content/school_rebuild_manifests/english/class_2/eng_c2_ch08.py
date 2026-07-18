"""Original deep manifest for Class 2 English Chapter 8.

The official extract is used only for chapter structure, themes, and exercise
forms. Every learner-facing passage, question, option, and rubric is original
Zidd content. The helper functions in this module are shared only by the
assigned Class 2 Chapter 8-13 manifest batch.
"""

from __future__ import annotations

import re
import sys
from typing import Any, Literal

from scripts.build_school_deep_chapter import DeepChapterManifest as _ImportedDeepManifest


CLASS2_MANIFEST_SCHEMA_VERSION = "school-class2-deep-manifest-v1"


def _active_deep_manifest_base():
    """Use the compiler's class identity whether it runs as a module or script."""

    main_module = sys.modules.get("__main__")
    active = getattr(main_module, "DeepChapterManifest", None)
    return active or _ImportedDeepManifest


class Class2DeepChapterManifest(_active_deep_manifest_base()):
    schema_version: Literal["school-class2-deep-manifest-v1"]


Class2DeepChapterManifest.model_rebuild(_types_namespace={"Literal": Literal})


CLASS2_SKILLS = {
    "word_context": "reading.word_meaning_context",
    "comprehension": "reading.sentence_comprehension",
    "sequence": "reading.event_sequence",
    "word_use": "vocab.chapter_word_usage",
    "spelling": "vocab.spelling",
    "word_jobs": "grammar.noun_verb_adjective",
    "sentence_order": "grammar.sentence_order",
    "punctuation": "grammar.punctuation_capitalization",
    "sentence": "writing.complete_sentence",
}

READING_SKILLS = [
    CLASS2_SKILLS["comprehension"],
    CLASS2_SKILLS["sequence"],
]
VOCAB_SKILLS = [
    CLASS2_SKILLS["word_context"],
    CLASS2_SKILLS["word_use"],
    CLASS2_SKILLS["spelling"],
]
GRAMMAR_SKILLS = [
    CLASS2_SKILLS["word_jobs"],
    CLASS2_SKILLS["sentence_order"],
    CLASS2_SKILLS["punctuation"],
]
WRITING_SKILLS = [CLASS2_SKILLS["sentence"]]


def evidence(description: str, *phrases: str) -> tuple[str, list[str]]:
    """Declare one strict, visible-reference-backed rubric requirement."""

    return description, list(phrases)


def open_task(
    passage: str,
    prompt: str,
    model_answer: str,
    requirements: list[tuple[str, list[str]]],
    *,
    skills: list[str] | None = None,
    interaction: str = "evidence_text",
    min_words: int = 6,
    ordered: bool = False,
    teaching: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "open",
        "passage": passage,
        "prompt": prompt,
        "model_answer": model_answer,
        "requirements": requirements,
        "skills": skills,
        "interaction": interaction,
        "min_words": min_words,
        "ordered": ordered,
        "teaching": teaching,
    }


def choice_task(
    passage: str,
    prompt: str,
    correct: str,
    distractors: list[str],
    *,
    skills: list[str] | None = None,
    teaching: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "choice",
        "passage": passage,
        "prompt": prompt,
        "correct": correct,
        "distractors": distractors,
        "skills": skills,
        "teaching": teaching,
    }


_PHASE_TASK_LEADS = {
    "co_construct": "Work through the visible clues together for this task",
    "guided": "Use the shown clues for this task",
    "independent": "Work on your own with the visible details for this task",
    "transfer": "Use the same skill in this new setting for the task",
    "review": "Check what you remember with the visible details for this task",
    "bridge": "Start with one clear clue for this task",
    "masterclass": "Join the useful clues for this task",
    "revision_level_1": "Follow the worked example for this task",
    "revision_level_2": "Try the new case using only its visible facts for this task",
    "revision_level_3": "Build the whole answer from the visible clues for this task",
    "assessment": "Answer on your own from the visible details for this task",
}


def _relevance_terms(model_answer: str, passage: str) -> list[str]:
    ignored = {
        "about",
        "after",
        "again",
        "because",
        "before",
        "first",
        "from",
        "into",
        "then",
        "their",
        "there",
        "these",
        "they",
        "this",
        "with",
    }
    terms: list[str] = []
    for text in (model_answer, passage):
        for word in re.findall(r"[A-Za-z][A-Za-z'-]+", text):
            lowered = word.casefold()
            if len(lowered) < 4 or lowered in ignored or lowered in terms:
                continue
            terms.append(lowered)
            if len(terms) == 4:
                return terms
    if len(terms) < 2:
        raise ValueError("class2_open_task_requires_relevance_terms")
    return terms


_ALIAS_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def _words(value: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", value)


def _content_words(value: str) -> set[str]:
    return {
        word.casefold()
        for word in _words(value)
        if word.casefold() not in _ALIAS_STOPWORDS
    }


def _punctuation_aliases(model_answer: str, mark: str) -> list[str]:
    words = _words(model_answer.rstrip())
    if len(words) < 2:
        raise ValueError("class2_punctuation_authority_needs_natural_closure")
    return [
        " ".join(words[-3:]) + mark,
        " ".join(words[-2:]) + mark,
    ]


def _model_context_alias(model_answer: str, phrases: list[str]) -> str:
    """Return a short, exact model span that expresses one authored claim."""

    model_matches = list(re.finditer(r"[A-Za-z]+(?:'[A-Za-z]+)?", model_answer))
    model_words = [match.group(0) for match in model_matches]
    model_lower = [word.casefold() for word in model_words]
    candidates: list[tuple[int, int, str]] = []

    for phrase in phrases:
        cleaned = phrase.strip()
        phrase_words = _words(cleaned)
        if not phrase_words:
            continue
        if len(phrase_words) == 1:
            word_authority = re.search(
                rf"(?:the |new |corrected )?word is {re.escape(phrase_words[0])}",
                model_answer,
                flags=re.IGNORECASE,
            )
            if word_authority:
                candidates.append((120, -3, word_authority.group(0)))
                continue
        exact = re.search(re.escape(cleaned), model_answer, flags=re.IGNORECASE)
        if exact and len(phrase_words) >= 2:
            candidates.append((100 + len(phrase_words), -len(phrase_words), exact.group(0)))
            continue

        target_words = list(_content_words(cleaned)) or [
            word.casefold() for word in phrase_words
        ]
        positions = [
            index
            for index, word in enumerate(model_lower)
            if word in target_words
        ]
        if not positions:
            continue
        if len(phrase_words) == 1:
            start = positions[0]
            end = min(len(model_words), start + 3)
            if end - start < 2:
                start = max(0, end - 2)
        else:
            start = min(positions)
            end = max(positions) + 1
        while (
            len(phrase_words) > 1
            and end - start < 3
            and (start > 0 or end < len(model_words))
        ):
            if start > 0:
                start -= 1
            if end - start < 3 and end < len(model_words):
                end += 1
        if end - start > 8:
            end = min(len(model_words), start + 8)
        text = model_answer[model_matches[start].start() : model_matches[end - 1].end()]
        overlap = len(set(target_words).intersection(model_lower[start:end]))
        candidates.append((overlap * 10, -(end - start), text))

    if not candidates:
        raise ValueError(
            "class2_semantic_claim_not_grounded_in_model:"
            + " | ".join(phrases)
        )
    alias = max(candidates)[2].strip(" ,;:")
    if len(_words(alias)) < 2:
        raise ValueError("class2_semantic_alias_needs_two_words")
    return alias


def _paraphrase_alias(
    value: str,
    *,
    fallback_word: str,
    description: str,
) -> str:
    replacements = (
        (" is a noun", " names a person or thing"),
        (" is the noun", " names a person or thing"),
        (" is a verb", " shows the action"),
        (" is the verb", " shows the action"),
        (" is an adjective", " tells what kind"),
        (" is the action", " tells what happens"),
        (" means ", " can mean "),
        (" before ", " earlier than "),
        (" after ", " later than "),
        (" first", " at the start"),
        (" next", " after that"),
        (" finally", " at the end"),
        (" shows ", " makes clear "),
        (" helps ", " gives help to "),
        (" correct ", " right "),
        (" remember", " recall"),
        (" clean", " free from litter"),
    )
    alternate = value
    for old, new in replacements:
        if old in alternate.casefold():
            pattern = re.compile(re.escape(old), flags=re.IGNORECASE)
            alternate = pattern.sub(new, alternate, count=1)
            break
    if alternate.casefold() == value.casefold():
        words = _words(value)
        word_match = re.fullmatch(
            r"(?:the |new |corrected )?word is ([a-z'-]+)",
            value.casefold(),
        )
        if word_match:
            alternate = f"spell it {word_match.group(1)}"
        elif len(words) == 1:
            alternate = f"this word is {words[0]}"
        elif "capital" in description.casefold() and words[0] in {
            "How",
            "Please",
            "Thank",
            "What",
            "When",
            "Where",
            "Which",
            "Who",
            "Why",
        } and len(words) >= 2:
            alternate = " ".join(words[:2])
        elif words[0].casefold() in {"the", "a", "an"}:
            replacement = "this" if words[0].casefold() == "the" else "one"
            alternate = " ".join([replacement, *words[1:]])
        elif len(words) <= 3 and (
            words[0].casefold().endswith(("ed", "ing"))
            or words[0].casefold() in {"brought", "built", "gave", "made", "took"}
        ):
            alternate = f"it {' '.join(words)}"
        elif len(words) <= 3:
            alternate = f"the {' '.join(words)}"
        else:
            alternate = f"that is, {value[0].lower()}{value[1:]}"
    if len(_words(alternate)) < 2:
        alternate = f"the word {fallback_word}"
    return alternate


def _requirement_groups(
    description: str,
    phrases: list[str],
    model_answer: str,
) -> list[list[str]]:
    lowered = description.casefold()
    punctuation_groups = [
        [phrase] for phrase in phrases if phrase.strip() in {"?", ".", "!"}
    ]
    phrases = [
        phrase for phrase in phrases if phrase.strip() not in {"?", ".", "!"}
    ]
    if not phrases:
        return punctuation_groups
    if any(
        marker in lowered
        for marker in (
            "spells and uses",
            "builds and uses",
            "corrects and uses",
            "defines and uses",
        )
    ):
        return [[phrase] for phrase in phrases] + punctuation_groups
    if " or " in lowered and not any(
        marker in lowered for marker in ("both", "all", "two", "three")
    ):
        return [phrases, *punctuation_groups]

    if len(phrases) <= 1:
        return [phrases, *punctuation_groups]

    model_words = [word.casefold() for word in _words(model_answer)]
    positions_by_phrase = [
        {
            index
            for index, word in enumerate(model_words)
            if word in _content_words(phrase)
        }
        for phrase in phrases
    ]
    groups: list[list[str]] = []
    group_positions: list[set[int]] = []
    grounded = [
        (phrase, positions)
        for phrase, positions in zip(phrases, positions_by_phrase)
        if positions
    ]
    ungrounded = [
        phrase
        for phrase, positions in zip(phrases, positions_by_phrase)
        if not positions
    ]
    for phrase, positions in grounded:
        matching = next(
            (
                index
                for index, existing in enumerate(group_positions)
                if positions and existing.intersection(positions)
            ),
            None,
        )
        if matching is None:
            groups.append([phrase])
            group_positions.append(set(positions))
        else:
            groups[matching].append(phrase)
            group_positions[matching].update(positions)
    if not groups:
        return [phrases, *punctuation_groups]
    for phrase in ungrounded:
        phrase_terms = _content_words(phrase)
        target = next(
            (
                index
                for index, group in enumerate(groups)
                if phrase_terms.intersection(
                    set().union(*(_content_words(item) for item in group))
                )
            ),
            0,
        )
        groups[target].append(phrase)
    return [*groups, *punctuation_groups]


def _semantic_requirements(
    requirements: list[tuple[str, list[str]]],
    model_answer: str,
) -> list[tuple[str, list[str]]]:
    expanded: list[tuple[str, list[str]]] = []
    for description, phrases in requirements:
        groups = _requirement_groups(description, phrases, model_answer)
        for part_no, group in enumerate(groups, start=1):
            if not group:
                continue
            if group[0].strip() in {"?", ".", "!"}:
                aliases = _punctuation_aliases(model_answer, group[0].strip())
            else:
                primary = _model_context_alias(model_answer, group)
                aliases = [primary]
                authored = next(
                    (
                        phrase.strip()
                        for phrase in group
                        if len(_words(phrase)) >= 2
                        and phrase.strip().casefold() != primary.casefold()
                    ),
                    None,
                )
                alternate = authored or _paraphrase_alias(
                    primary,
                    fallback_word=_words(group[0])[0],
                    description=description,
                )
                if alternate.casefold() != primary.casefold():
                    aliases.append(alternate)
            while len(aliases) < 2:
                aliases.append(f"the card also shows {aliases[0]}")
            cleaned_aliases = []
            for alias in aliases:
                candidate = alias.strip()
                if len(_words(candidate)) < 2:
                    candidate = f"the word {candidate}"
                normalized = candidate.casefold()
                if normalized not in {item.casefold() for item in cleaned_aliases}:
                    cleaned_aliases.append(candidate)
            while len(cleaned_aliases) < 2:
                candidate = f"another way is {cleaned_aliases[0]}"
                cleaned_aliases.append(candidate)
            part_description = description
            if len(groups) > 1:
                part_description = (
                    f"Required part {part_no}: {group[0].strip().rstrip('.')}"
                )
            expanded.append((part_description, cleaned_aliases))
    if not expanded:
        raise ValueError("class2_open_task_requires_semantic_claims")
    keep = [True] * len(expanded)
    primary_aliases = [
        " ".join(aliases[0].casefold().split())
        for _, aliases in expanded
    ]
    comparable_aliases = [
        re.sub(r"[^a-z0-9' ]+", "", primary).strip()
        for primary in primary_aliases
    ]
    for index, primary in enumerate(primary_aliases):
        if primary.rstrip().endswith(("?", ".", "!")):
            continue
        comparable = comparable_aliases[index]
        for other_index, other in enumerate(comparable_aliases):
            if index == other_index or len(comparable) > len(other):
                continue
            if len(comparable) == len(other) and index < other_index:
                continue
            if re.search(
                rf"(?<!\w){re.escape(comparable)}(?!\w)",
                other,
            ):
                keep[index] = False
                break
    collapsed = [item for item, retained in zip(expanded, keep) if retained]
    if not collapsed:
        raise ValueError("class2_open_task_claim_collapse_removed_every_slot")
    alias_owners: dict[str, str] = {}
    for description, aliases in collapsed:
        for alias in aliases:
            normalized = " ".join(alias.casefold().split())
            owner = alias_owners.get(normalized)
            if owner is not None:
                raise ValueError(
                    "class2_semantic_alias_shared_across_slots:"
                    f"{owner}:{description}:{alias}"
                )
            alias_owners[normalized] = description
    return collapsed


def _teaching_block(principle: str, phase: str, task: dict[str, Any]) -> str:
    if task.get("teaching"):
        return str(task["teaching"])
    lead = _PHASE_TASK_LEADS.get(phase, _PHASE_TASK_LEADS["assessment"])
    return f"{principle} {lead}: {str(task['prompt']).strip()}"


def _make_activity(
    *,
    level_id: str,
    phase: str,
    index: int,
    principle: str,
    level_skills: list[str],
    task: dict[str, Any],
) -> dict[str, Any]:
    activity_id = f"{level_id}:{phase}:{index}"
    skills = list(task.get("skills") or level_skills)
    teaching_block = _teaching_block(principle, phase, task)
    if task["kind"] == "choice":
        raw_options = [task["correct"], *task["distractors"]]
        shift = sum(ord(character) for character in activity_id) % len(raw_options)
        options = raw_options[shift:] + raw_options[:shift]
        return {
            "kind": "selected_option",
            "activity_id": activity_id,
            "teaching_block": teaching_block,
            "passage": task["passage"],
            "prompt": task["prompt"],
            "skill_ids": skills,
            "options": options,
            "accepted_answers": [task["correct"]],
        }

    model_answer = str(task["model_answer"]).strip()
    min_words = int(task["min_words"])
    if len(_words(model_answer)) < min_words:
        label = "question" if model_answer.endswith("?") else "sentence"
        model_answer = f"The finished {label} is: {model_answer}"

    slots = []
    criteria = []
    semantic_requirements = _semantic_requirements(
        task["requirements"],
        model_answer,
    )
    for requirement_no, (description, phrases) in enumerate(
        semantic_requirements, start=1
    ):
        slot_id = f"{activity_id}:requirement_{requirement_no}"
        slots.append(
            {"id": slot_id, "description": description, "any_of": phrases}
        )
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.75,
            }
        )
    payload: dict[str, Any] = {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": teaching_block,
        "passage": task["passage"],
        "prompt": task["prompt"],
        "skill_ids": skills,
        "interaction_type": task["interaction"],
        "rubric_criteria": criteria,
        "concept_slots": slots,
        "forbidden_phrases": [
            "I ignored the stated details",
            "Any answer is correct",
        ],
        "min_response_words": min_words,
        "relevance_terms": _relevance_terms(
            model_answer, task["passage"]
        ),
        "model_answer": model_answer,
        "pass_score": 0.8,
    }
    if task["ordered"] and len(slots) >= 2:
        payload["ordered_concept_slot_ids"] = [slot["id"] for slot in slots]
    return payload


def _support_choice(
    task: dict[str, Any],
    *,
    teaching: str,
    prompt: str,
    skills: list[str],
) -> dict[str, Any]:
    receptive_skills = [
        skill for skill in skills if not skill.startswith(("writing.", "speaking.", "oral."))
    ]
    if not receptive_skills:
        raise ValueError("class2_support_choice_requires_receptive_skill")
    requirements = task.get("requirements") or []
    clue = (
        requirements[0][1][0]
        if requirements and requirements[0][1]
        else "the first clue"
    )
    distractors = [
        f"Only {clue} matters, so the other details can be skipped.",
        "The card gives no useful clue for this question.",
    ]
    return choice_task(
        task["passage"],
        prompt,
        task["model_answer"],
        distractors,
        skills=[receptive_skills[0]],
        teaching=teaching,
    )


def _support_open(
    task: dict[str, Any],
    *,
    teaching: str,
    interaction: str,
    min_words: int,
) -> dict[str, Any]:
    authored = dict(task)
    authored["teaching"] = teaching
    authored["interaction"] = interaction
    authored["min_words"] = min_words
    model_words = _words(authored["model_answer"])
    if len(model_words) < min_words:
        label = (
            "question"
            if str(authored["model_answer"]).strip().endswith("?")
            else "sentence"
        )
        authored["model_answer"] = (
            f"The finished {label} is: {str(authored['model_answer']).strip()}"
        )
    return authored


def _support_progression(spec: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = list(spec["support"])
    if len(tasks) != 5:
        raise ValueError("class2_level_requires_five_support_cards")
    title = spec["title"].casefold()
    return [
        _support_choice(
            tasks[0],
            teaching=(
                f"Start with one clear clue for {title}. Read the card, then "
                "choose the answer that uses that clue."
            ),
            prompt=f"Which answer uses the first helpful clue for {title}?",
            skills=list(spec["skill_ids"]),
        ),
        _support_open(
            tasks[1],
            teaching=(
                f"Use two small clues for {title}. Put them into one short "
                "sentence."
            ),
            interaction="short_text",
            min_words=6,
        ),
        _support_choice(
            tasks[2],
            teaching=(
                f"Worked example: for {title}, I find what the question asks, "
                "point to its clue, and check that both fit. Now try the new card."
            ),
            prompt=f"Which answer follows the worked example for {title}?",
            skills=list(spec["skill_ids"]),
        ),
        _support_open(
            tasks[3],
            teaching=(
                f"Another case uses {title} in a new setting. Read only this "
                "card and give one short answer."
            ),
            interaction="short_text",
            min_words=6,
        ),
        _support_open(
            tasks[4],
            teaching=(
                f"Now use every needed clue for {title}. Write the whole answer "
                "in your own words."
            ),
            interaction="evidence_text",
            min_words=8,
        ),
    ]


def _build_level(spec: dict[str, Any]) -> dict[str, Any]:
    level_id = spec["level_id"]
    skills = list(spec["skill_ids"])
    principle = spec["principle"]
    depth = spec.get("depth") or {}
    guided_tasks = [*spec["guided"], *depth.get("guided", [])]
    independent_tasks = [*spec["independent"], *depth.get("independent", [])]
    transfer_tasks = [*spec["transfer"], *depth.get("transfer", [])]
    review_tasks = [*spec["review"], *depth.get("review", [])]
    if (
        len(guided_tasks) < 4
        or len(independent_tasks) < 4
        or len(transfer_tasks) < 4
        or len(review_tasks) < 4
    ):
        raise ValueError(f"class2_level_depth_incomplete:{level_id}")
    support_tasks = _support_progression(spec)
    support_names = (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    support = {
        name: _make_activity(
            level_id=level_id,
            phase=name,
            index=index,
            principle=principle,
            level_skills=skills,
            task=support_tasks[index - 1],
        )
        for index, name in enumerate(support_names, start=1)
    }
    support_ids = [support[name]["activity_id"] for name in support_names]
    return {
        "level_id": level_id,
        "title": spec["title"],
        "focus": spec["focus"],
        "outcome": spec["outcome"],
        "skill_ids": skills,
        "episode_kind": spec["episode_kind"],
        "source_anchor_ids": spec["source_anchor_ids"],
        "connect": spec["connect"],
        "co_construct": _make_activity(
            level_id=level_id,
            phase="co_construct",
            index=1,
            principle=principle,
            level_skills=skills,
            task=spec["co"],
        ),
        "guided_variants": [
            _make_activity(
                level_id=level_id,
                phase="guided",
                index=index,
                principle=principle,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(guided_tasks, start=1)
        ],
        "independent_variants": [
            _make_activity(
                level_id=level_id,
                phase="independent",
                index=index,
                principle=principle,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(independent_tasks, start=1)
        ],
        "transfer_variants": [
            _make_activity(
                level_id=level_id,
                phase="transfer",
                index=index,
                principle=principle,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(transfer_tasks, start=1)
        ],
        "review_variants": [
            _make_activity(
                level_id=level_id,
                phase="review",
                index=index,
                principle=principle,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(review_tasks, start=1)
        ],
        "misconception_clusters": [
            {
                "cluster_id": spec["cluster_id"],
                "skill_ids": skills,
                "misconception": spec["misconception"],
                "remediation": spec["remediation"],
                "support_check_ids": support_ids,
            }
        ],
        "support_checks": support,
    }


def build_manifest(config: dict[str, Any]) -> Class2DeepChapterManifest:
    chapter_id = config["chapter_id"]
    levels = [_build_level(spec) for spec in config["levels"]]
    assessment_items = []
    for form_no, form in enumerate(config["assessment_forms"], start=1):
        for item_no, task in enumerate(form, start=1):
            assessment_items.append(
                _make_activity(
                    level_id=f"{chapter_id}:assessment_form_{form_no}",
                    phase="assessment",
                    index=item_no,
                    principle=(
                        "This chapter check uses a new, fully visible reference."
                    ),
                    level_skills=list(task["skills"]),
                    task=task,
                )
            )

    level_ids_by_skill = {
        skill_id: [
            level["level_id"]
            for level in config["levels"]
            if skill_id in level["skill_ids"]
        ]
        for skill_id in CLASS2_SKILLS.values()
    }
    strand_specs = (
        ("reading", READING_SKILLS, 6, ["selected_option", "constructed_response"]),
        ("vocabulary", VOCAB_SKILLS, 8, ["selected_option", "constructed_response"]),
        ("language", GRAMMAR_SKILLS, 8, ["selected_option", "constructed_response"]),
        ("writing", WRITING_SKILLS, 2, ["constructed_response"]),
    )
    strands = []
    for strand_name, skills, minimum_items, forms in strand_specs:
        remediation_ids = list(
            dict.fromkeys(
                level_id
                for skill_id in skills
                for level_id in level_ids_by_skill[skill_id]
            )
        )
        strands.append(
            {
                "strand_id": f"{chapter_id}:{strand_name}",
                "skill_ids": skills,
                "minimum_items": minimum_items,
                "evidence_forms": forms,
                "remediation_level_ids": remediation_ids,
            }
        )

    payload = {
        "schema_version": CLASS2_MANIFEST_SCHEMA_VERSION,
        "chapter": {
            "chapter_id": chapter_id,
            "chapter_no": config["chapter_no"],
            "title": config["title"],
            "book_title": "Mridang",
            "unit_title": config["unit_title"],
            "source_url": config["source_url"],
            "source_note": (
                "The official NCERT extract informed only section coverage, theme, "
                "and exercise form. All Zidd passages, prompts, choices, and rubrics "
                "are original and fully visible at runtime."
            ),
            "content_version": "2026-07-15.class2-deep.2",
            "certification_version": "school-class2-deep-v2",
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": config["extract_path"],
            },
        },
        "source_anchors": config["source_anchors"],
        "levels": levels,
        "chapter_assessment": {
            "items_per_attempt": 12,
            "pass_score": 0.8,
            "max_attempts": 2,
            "bank_item_count": 24,
            "items": assessment_items,
            "strands": strands,
        },
    }
    return Class2DeepChapterManifest.model_validate(payload)


def _open_set(
    rows: list[tuple[str, str, str, list[tuple[str, list[str]]]]],
    *,
    interaction: str = "evidence_text",
    ordered: bool = False,
) -> list[dict[str, Any]]:
    return [
        open_task(
            passage,
            prompt,
            model,
            requirements,
            interaction=interaction,
            ordered=ordered,
        )
        for passage, prompt, model, requirements in rows
    ]


S = CLASS2_SKILLS
CHAPTER_ID = "eng_c2_ch08"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/bemr108.pdf"


LEVELS: list[dict[str, Any]] = [
    {
        "level_id": f"{CHAPTER_ID}:changing_cloud_clues",
        "title": "Track a changing cloud",
        "focus": "read visible sky details in order and explain a simple change",
        "outcome": "Use two stated observations to tell what changed first and next without replacing evidence with an imagined shape.",
        "skill_ids": [S["comprehension"], S["sequence"]],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:poem:1-2", f"{CHAPTER_ID}:write:5"],
        "principle": "A careful sky reader separates what is observed from what is imagined and keeps changes in time order.",
        "connect": {
            "teaching_block": "Clouds can alter colour, place, and outline. Time words help a reader follow those visible changes.",
            "passage": "At sunrise, one narrow cloud rests above the gate. Minutes later, it widens and drifts past the tower.",
            "prompt": "Notice the starting shape, later shape, and movement before continuing.",
        },
        "co": choice_task(
            "First a grey cloud covers the hilltop. Next the wind moves it east, and the hilltop appears again.",
            "Which event comes immediately after the hilltop is covered?",
            "The wind moves the cloud east.",
            ["The hill becomes a cloud.", "Night begins over the hill."],
        ),
        "guided": [
            choice_task(
                "A small cloud joins two others. The cluster grows dark, then slides behind the library roof.",
                "What happens just before the cluster leaves view?",
                "The cluster grows dark.",
                ["The roof joins the clouds.", "The library becomes dark forever."],
            ),
            open_task(
                "At nine, a flat cloud is above the field. At ten, its middle rises while both ends remain low.",
                "State the earlier shape and the later change in one ordered response.",
                "The cloud is flat at nine, and its middle rises by ten.",
                [
                    evidence("Names the earlier flat shape.", "flat at nine", "cloud is flat"),
                    evidence("Names the later raised middle.", "middle rises", "raised middle"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set(
            [
                (
                    "A pale cloud enters from the west, passes the water tank, and breaks into three wisps near the playground.",
                    "Retell the cloud's route and final change in the correct order.",
                    "The cloud enters from the west, passes the tank, and finally breaks into three wisps.",
                    [
                        evidence("Begins with the westward entry.", "enters from the west", "comes from the west"),
                        evidence("Ends with three wisps.", "breaks into three wisps", "becomes three wisps"),
                    ],
                ),
                (
                    "A round cloud darkens underneath. Soon, its edge becomes ragged and a light shower reaches the garden.",
                    "Explain the two cloud changes that happen before the shower.",
                    "The underside darkens first, and then the cloud develops a ragged edge before the shower.",
                    [
                        evidence("Includes the dark underside.", "underside darkens", "darkens underneath"),
                        evidence("Includes the later ragged edge.", "ragged edge", "edge becomes ragged"),
                    ],
                ),
            ],
            ordered=True,
        ),
        "transfer": _open_set(
            [
                (
                    "Steam above a kettle begins as one thick puff, stretches toward the window, and fades into thin threads.",
                    "Use the same observation skill to sequence the steam's three changes.",
                    "The steam starts as a thick puff, stretches toward the window, and fades into thin threads.",
                    [
                        evidence("Gives the thick puff first.", "starts as a thick puff", "one thick puff"),
                        evidence("Gives stretching before fading.", "stretches toward the window", "fades into thin threads"),
                    ],
                ),
                (
                    "A chalk mark on the path is clear in the morning. After many footsteps, it spreads wider and becomes faint.",
                    "Describe the cause and the two visible results in order.",
                    "Footsteps make the chalk spread wider and then become faint.",
                    [
                        evidence("Names footsteps as the cause.", "footsteps make", "after many footsteps"),
                        evidence("Orders spreading before fading.", "spread wider", "become faint"),
                    ],
                ),
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "One cloud moves over the pond, joins a darker cloud, and later the joined cloud covers the sun.",
                    "Give the three events in order without adding an imagined object.",
                    "The first cloud crosses the pond, joins the darker cloud, and then the joined cloud covers the sun.",
                    [
                        evidence("Places crossing the pond first.", "crosses the pond", "moves over the pond"),
                        evidence("Places joining before covering the sun.", "joins the darker cloud", "covers the sun"),
                    ],
                ),
                (
                    "At noon, two bright clouds are far apart. By afternoon, both drift together and form one long band.",
                    "Compare the noon position with the afternoon result.",
                    "The clouds are apart at noon but drift together into one long band by afternoon.",
                    [
                        evidence("States that the clouds begin apart.", "apart at noon", "far apart"),
                        evidence("States the later long band.", "one long band", "form a long band"),
                    ],
                ),
            ],
            ordered=True,
        ),
        "cluster_id": f"{CHAPTER_ID}:observed_change_confusion",
        "misconception": "The learner reports an attractive imagined shape but omits a stated cloud detail or reverses the order of visible changes.",
        "remediation": "Mark time words and draw a two-box before-and-after strip; require one exact observed detail in each box before allowing imagination.",
        "support": _open_set(
            [
                (
                    "A thin cloud is above the bell. Later it is beyond the flagpole.",
                    "Name the first and later positions.",
                    "The cloud begins above the bell and later moves beyond the flagpole.",
                    [evidence("Includes both positions in order.", "above the bell", "beyond the flagpole")],
                ),
                (
                    "A white patch grows wider, turns grey, and then hides the moon.",
                    "Build the complete three-step change chain.",
                    "The patch grows wider, turns grey, and finally hides the moon.",
                    [evidence("Keeps all three changes in order.", "grows wider", "turns grey", "hides the moon")],
                ),
                (
                    "Before lunch, a cloud has one smooth edge. After lunch, the edge has three points.",
                    "Write the before-and-after shape only.",
                    "The edge is smooth before lunch and has three points afterward.",
                    [evidence("Contrasts smooth with three points.", "smooth before lunch", "three points")],
                ),
                (
                    "The cloud looks like a boat, but the stated facts are that it is low, long, and moving north.",
                    "List only the three observed facts.",
                    "The cloud is low, long, and moving north.",
                    [evidence("Uses all observed facts, not the guess.", "low", "long", "moving north")],
                ),
                (
                    "A tiny cloud joins a wide cloud. Together they travel behind the stadium.",
                    "State the joining event and the final place.",
                    "The tiny cloud joins the wide cloud, and both end behind the stadium.",
                    [evidence("Includes joining and the stadium location.", "joins the wide cloud", "behind the stadium")],
                ),
            ],
            ordered=True,
        ),
    },
    {
        "level_id": f"{CHAPTER_ID}:sky_words_in_context",
        "title": "Unlock cloud words",
        "focus": "infer and use cloud vocabulary from nearby action and description clues",
        "outcome": "Explain a sky word from context and use it accurately in a new complete idea.",
        "skill_ids": [S["word_context"], S["word_use"]],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [f"{CHAPTER_ID}:poem:1-2", f"{CHAPTER_ID}:speak:3-4"],
        "principle": "Context gives a word meaning through nearby colour, shape, movement, or result clues; a new use must keep that meaning.",
        "connect": {
            "teaching_block": "A word becomes clearer when another phrase shows its action or result. Look beside the word before guessing.",
            "passage": "The cloud begins to drift; it moves slowly away from the school roof.",
            "prompt": "Notice how the second clause explains drift, then continue.",
        },
        "co": choice_task(
            "The wispy cloud is made of thin, feathery strands that hardly cover the blue sky.",
            "Which meaning fits wispy in this reference?",
            "thin and feathery",
            ["dark and rainy", "round and solid"],
        ),
        "guided": [
            choice_task(
                "Several small clouds cluster above the station, gathering close together in one group.",
                "Which phrase explains cluster?",
                "gathering close together",
                ["moving alone", "falling to the ground"],
            ),
            open_task(
                "The sunset colours fade until the orange becomes pale and difficult to notice.",
                "Explain fade from the clue and use fade in a new sky sentence.",
                "Fade means become less clear. The pink light will fade after sunset.",
                [
                    evidence("Explains the context meaning.", "become less clear", "grow pale"),
                    evidence("Uses fade as a loss of colour or visibility.", "light will fade", "colours fade"),
                ],
            ),
        ],
        "independent": _open_set(
            [
                (
                    "The enormous cloud stretches from the river to the farms, taking up most of the sky.",
                    "Define enormous from the reference and write a different accurate use.",
                    "Enormous means very large. An enormous grey cloud covered our playground.",
                    [
                        evidence("Gives the meaning very large.", "very large", "extremely big"),
                        evidence("Uses enormous for something truly large.", "enormous grey cloud", "enormous storm cloud"),
                    ],
                ),
                (
                    "A cloud vanishes behind the mountain; after a moment, no part of it can be seen.",
                    "Show what vanishes means and use the word in a fresh sentence.",
                    "Vanishes means disappears from sight. The last white wisp vanishes at dusk.",
                    [
                        evidence("States the meaning disappears.", "disappears from sight", "cannot be seen"),
                        evidence("Uses vanishes for a visible thing disappearing.", "wisp vanishes", "cloud vanishes"),
                    ],
                ),
            ]
        ),
        "transfer": _open_set(
            [
                (
                    "Dry leaves scatter when the gate opens, so they spread across different parts of the yard.",
                    "Infer scatter and use it for clouds in one new sentence.",
                    "Scatter means spread apart. Small clouds scatter across the evening sky.",
                    [
                        evidence("Explains spreading apart.", "spread apart", "move in different directions"),
                        evidence("Transfers scatter to clouds accurately.", "clouds scatter", "wisps scatter"),
                    ],
                ),
                (
                    "A faint pencil line is so light that Mira must look closely to see it.",
                    "Use this clue to explain faint and transfer it to a sky detail.",
                    "Faint means hard to see. A faint cloud rested near the bright moon.",
                    [
                        evidence("Gives the meaning hard to see.", "hard to see", "very light"),
                        evidence("Uses faint for a subtle sky detail.", "faint cloud", "faint star"),
                    ],
                ),
            ]
        ),
        "review": _open_set(
            [
                (
                    "Clouds gather over the lake, moving from separate places into one close group.",
                    "Explain gather and use it in a weather sentence.",
                    "Gather means come together. Dark clouds gather before the rain.",
                    [
                        evidence("Defines coming together.", "come together", "form one group"),
                        evidence("Uses gather in a fitting weather sentence.", "clouds gather", "mist gathers"),
                    ],
                ),
                (
                    "A cloud glides above the trees with a smooth, quiet movement and no sudden turn.",
                    "State the meaning of glides and create another correct use.",
                    "Glides means moves smoothly. A long cloud glides past the tower.",
                    [
                        evidence("Defines smooth movement.", "moves smoothly", "smooth movement"),
                        evidence("Uses glides with a suitable subject.", "cloud glides", "kite glides"),
                    ],
                ),
            ]
        ),
        "cluster_id": f"{CHAPTER_ID}:context_word_guess",
        "misconception": "The learner chooses a familiar but unrelated meaning or repeats the target word without explaining the surrounding clue.",
        "remediation": "Underline the explanation or result next to the word, say a plain meaning, and test that meaning in one new chapter-specific sentence.",
        "support": _open_set(
            [
                (
                    "A cloud expands, becoming wider every minute.",
                    "Explain expands using the visible result.",
                    "Expands means becomes wider or larger.",
                    [evidence("Uses the widening clue.", "becomes wider", "grows larger")],
                ),
                (
                    "The clouds merge; two separate patches become one patch.",
                    "Define merge and use it in a short sky sentence.",
                    "Merge means join together. Two clouds merge above the field.",
                    [evidence("Defines and uses joining.", "join together", "clouds merge")],
                ),
                (
                    "A brilliant rim shines very brightly around the dark cloud.",
                    "What does brilliant mean here, and how could a star be brilliant?",
                    "Brilliant means very bright. A brilliant star shines over the roof.",
                    [evidence("Keeps the brightness meaning.", "very bright", "brilliant star")],
                ),
                (
                    "The cloud is motionless, staying in the same place above the tree.",
                    "Explain motionless from the action clue.",
                    "Motionless means not moving or staying in one place.",
                    [evidence("States no movement.", "not moving", "staying in one place")],
                ),
                (
                    "The grey cover thins, so more blue sky becomes visible through it.",
                    "Define thins and use it for mist.",
                    "Thins means becomes less thick. The morning mist thins after sunrise.",
                    [evidence("Explains reduced thickness and transfers it.", "less thick", "mist thins")],
                ),
            ]
        ),
    },
    {
        "level_id": f"{CHAPTER_ID}:cloud_word_spelling",
        "title": "Build sky spellings",
        "focus": "recognise and produce useful cloud words from visible letter patterns",
        "outcome": "Choose or write the standard spelling of a sky word and place it in a meaningful sentence.",
        "skill_ids": [S["spelling"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:listen:7", f"{CHAPTER_ID}:write:5"],
        "principle": "Spelling is checked with visible letters and word parts here; no sound, recording, or recitation is required.",
        "connect": {
            "teaching_block": "Long words become manageable when a learner checks each printed chunk and then reads the whole word in context.",
            "passage": "Printed chunks: thun + der = thunder; cloud + y = cloudy.",
            "prompt": "Notice how the visible chunks join before continuing.",
        },
        "co": choice_task(
            "Sentence frame: The ___ sky became dark before rain. Candidate words: clowdy, cloudy, cloudie.",
            "Which candidate has the standard spelling?",
            "cloudy",
            ["clowdy", "cloudie"],
        ),
        "guided": [
            choice_task(
                "Letter choices for the moving-air word are breeze, breze, and breese.",
                "Select the standard spelling for the sentence about gentle wind.",
                "breeze",
                ["breze", "breese"],
            ),
            open_task(
                "Visible chunks: shad + ow. Sentence idea: A cloud made a cool patch on the wall.",
                "Join the chunks, then use the completed word in a sentence.",
                "The word is shadow. A cloud shadow crossed the wall.",
                [
                    evidence("Produces the spelling shadow.", "shadow"),
                    evidence("Uses shadow meaningfully.", "cloud shadow", "shadow crossed"),
                ],
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Missing letters: d r _ f t. Meaning clue: move slowly with air.",
                    "Complete the word and write a cloud sentence with it.",
                    "The word is drift. White clouds drift above the market.",
                    [evidence("Spells drift correctly.", "drift"), evidence("Uses drift for slow movement.", "clouds drift", "cloud will drift")],
                ),
                (
                    "Scrambled letters: i s p w. Meaning clue: one thin piece of cloud.",
                    "Unscramble the sky word and use it in one complete sentence.",
                    "The word is wisp. A silver wisp crossed the moon.",
                    [evidence("Spells wisp correctly.", "wisp"), evidence("Uses wisp as a thin cloud piece.", "silver wisp", "cloud wisp")],
                ),
            ]
        ),
        "transfer": _open_set(
            [
                (
                    "Word family: bright, brighter, brightest. Sentence clue: the edge with the most light.",
                    "Write the needed family word and complete the sentence idea.",
                    "Brightest is needed. The brightest edge faced the sun.",
                    [evidence("Spells brightest correctly.", "brightest"), evidence("Uses it for the greatest brightness.", "brightest edge")],
                ),
                (
                    "Base word: mist. Add y to name weather filled with light mist.",
                    "Build the new word and write a morning sentence.",
                    "The new word is misty. It was a misty morning near the lake.",
                    [evidence("Builds misty correctly.", "misty"), evidence("Uses misty for weather.", "misty morning", "misty day")],
                ),
            ]
        ),
        "review": _open_set(
            [
                (
                    "Correct the printed word in this idea: A gental wind moved the clouds.",
                    "Write the corrected word and the full corrected sentence.",
                    "The corrected word is gentle. A gentle wind moved the clouds.",
                    [evidence("Corrects gentle.", "gentle"), evidence("Writes the complete corrected sentence.", "gentle wind moved the clouds")],
                ),
                (
                    "Choose letters to complete s _ y and c l _ u d in a sentence about weather.",
                    "Write both completed words in one clear sentence.",
                    "The words are sky and cloud. One cloud crossed the blue sky.",
                    [evidence("Spells sky and cloud.", "sky", "cloud"), evidence("Uses both in a complete idea.", "cloud crossed the blue sky")],
                ),
            ]
        ),
        "cluster_id": f"{CHAPTER_ID}:visible_spelling_pattern",
        "misconception": "The learner guesses from a remembered sound, drops a printed letter chunk, or supplies a word that does not fit the visible meaning clue.",
        "remediation": "Point to each printed chunk, rebuild the whole word, compare it with the meaning clue, and finish with a short written use.",
        "support": _open_set(
            [
                ("Chunks: rain + y. The day has frequent rain.", "Join the chunks and use the weather word.", "The word is rainy. We had a rainy afternoon.", [evidence("Spells and uses rainy.", "rainy", "rainy afternoon")]),
                ("Missing letter: s k _. The clue means the space above us.", "Complete the word and write a sky sentence.", "The word is sky. The evening sky turned pink.", [evidence("Spells and uses sky.", "sky", "evening sky")]),
                ("Candidate spellings: shape, shipe, shaep. The clue means outline.", "Write the standard word and use it for a cloud.", "The word is shape. The cloud shape changed quickly.", [evidence("Spells and uses shape.", "shape", "cloud shape")]),
                ("Scrambled letters: d w i n. The clue moves leaves and clouds.", "Unscramble the word and complete a sentence.", "The word is wind. Wind pushed the clouds east.", [evidence("Spells and uses wind.", "wind", "pushed the clouds")]),
                ("Correct this word: wite. The intended colour word has an h.", "Write the corrected colour word in a cloud sentence.", "The word is white. A white cloud floated overhead.", [evidence("Corrects and uses white.", "white", "white cloud")]),
            ]
        ),
    },
    {
        "level_id": f"{CHAPTER_ID}:cloud_word_jobs",
        "title": "Name cloud word jobs",
        "focus": "distinguish naming, action, and describing words in sky sentences",
        "outcome": "Identify a noun, verb, or adjective from a visible sentence and explain the job it performs.",
        "skill_ids": [S["word_jobs"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:write:5", f"{CHAPTER_ID}:speak:3-4"],
        "principle": "A word job depends on its sentence: nouns name, verbs show action, and adjectives describe a noun.",
        "connect": {
            "teaching_block": "The same sky scene can contain a name, an action, and a description. Read the whole sentence before labelling a word.",
            "passage": "The silver cloud drifts. Cloud names the thing, silver describes it, and drifts shows action.",
            "prompt": "Notice the three word jobs in the visible example before continuing.",
        },
        "co": choice_task("A narrow cloud crosses the field.", "Which word describes the cloud?", "narrow", ["cloud", "crosses"]),
        "guided": [
            choice_task("Three clouds gather near the moon.", "Which word tells what the clouds do?", "gather", ["clouds", "moon"]),
            open_task("The enormous cloud covered the village.", "Name the noun cloud, its describing word, and the action word.", "Cloud is the noun, enormous is the adjective, and covered is the verb.", [evidence("Labels the noun and adjective.", "cloud is the noun", "enormous is the adjective"), evidence("Labels the verb.", "covered is the verb")]),
        ],
        "independent": _open_set([
            ("A soft breeze pushes the grey mist.", "Sort breeze, pushes, and grey by word job.", "Breeze is a noun, pushes is a verb, and grey is an adjective.", [evidence("Labels breeze and pushes.", "breeze is a noun", "pushes is a verb"), evidence("Labels grey as describing.", "grey is an adjective")]),
            ("Bright sunlight warms the quiet field.", "Identify one naming word, the action, and both describing words.", "Sunlight or field is a noun, warms is the verb, and bright and quiet are adjectives.", [evidence("Names a noun and the verb.", "sunlight", "field", "warms"), evidence("Names both adjectives.", "bright", "quiet")]),
        ]),
        "transfer": _open_set([
            ("The red kite climbs above a tall tree.", "Transfer the word-job check to this ground scene and label red, kite, and climbs.", "Red is an adjective, kite is a noun, and climbs is a verb.", [evidence("Labels all three jobs correctly.", "red is an adjective", "kite is a noun", "climbs is a verb")]),
            ("Cool water fills the round bowl.", "Explain the jobs of cool, water, and fills.", "Cool describes the noun water, while fills is the action verb.", [evidence("Connects cool to water.", "cool describes", "noun water"), evidence("Labels fills as action.", "fills is the action", "fills is a verb")]),
        ]),
        "review": _open_set([
            ("A dark cloud slowly covers the sun.", "Classify dark, cloud, and covers without classifying slowly.", "Dark is an adjective, cloud is a noun, and covers is a verb.", [evidence("Classifies the three requested words.", "dark is an adjective", "cloud is a noun", "covers is a verb")]),
            ("Tiny drops sparkle on the green leaf.", "Name the action word and two describing words.", "Sparkle is the action, and tiny and green are describing words.", [evidence("Names sparkle as action.", "sparkle is the action", "sparkle is a verb"), evidence("Names tiny and green as describing.", "tiny", "green")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:word_job_by_position",
        "misconception": "The learner labels a word by its position or topic instead of checking whether it names, acts, or describes inside the sentence.",
        "remediation": "Ask three tests in order: what is named, what happens, and which word tells more about the named thing; then relabel the sentence.",
        "support": _open_set([
            ("The blue patch widens.", "Label blue, patch, and widens.", "Blue is an adjective, patch is a noun, and widens is a verb.", [evidence("Labels all three word jobs.", "blue is an adjective", "patch is a noun", "widens is a verb")]),
            ("A gentle wind bends the branch.", "Find the describing word and the action.", "Gentle is the describing word, and bends is the action.", [evidence("Finds gentle and bends.", "gentle", "bends")]),
            ("Grey mist hides the road.", "Which word names the weather thing, and which word shows its action?", "Mist names the weather thing, and hides shows its action.", [evidence("Distinguishes mist from hides.", "mist names", "hides shows")]),
            ("The round moon shines.", "Explain why round is not the action word.", "Round describes the moon, while shines is the action.", [evidence("Links round to description and shines to action.", "round describes", "shines is the action")]),
            ("Long shadows cross the yard.", "Classify long, shadows, and cross.", "Long is an adjective, shadows is a noun, and cross is a verb.", [evidence("Classifies all requested words.", "long is an adjective", "shadows is a noun", "cross is a verb")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:sky_sentence_builder",
        "title": "Arrange and finish sky sentences",
        "focus": "order visible words and add capitals and end punctuation",
        "outcome": "Turn a supplied word set into one grammatical sentence with a capital beginning and suitable end mark.",
        "skill_ids": [S["sentence_order"], S["punctuation"]],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:write:5", f"{CHAPTER_ID}:poem:1-2"],
        "principle": "A complete sentence needs sensible word order, a capital first letter, and an end mark that matches its purpose.",
        "connect": {
            "teaching_block": "Find the naming part, place the action after it, and then check the first letter and final mark.",
            "passage": "Word set: the / cloud / moves / slowly. Finished form: The cloud moves slowly.",
            "prompt": "Notice the order, capital T, and full stop before continuing.",
        },
        "co": choice_task("Word set: bright / is / the / sky", "Which option builds the complete sky statement?", "The sky is bright.", ["Bright the sky is.", "the Sky bright is"]),
        "guided": [
            choice_task("Word set: where / cloud / did / go / the", "Which option forms a correctly punctuated question?", "Where did the cloud go?", ["Where the cloud did go.", "where did go the cloud?"]),
            open_task("Word set: across / clouds / race / dark / the sky", "Arrange every word as one statement with correct punctuation.", "Dark clouds race across the sky.", [evidence("Uses sensible complete order.", "dark clouds race across the sky"), evidence("Uses a capital and full stop.", "Dark", ".")]),
        ],
        "independent": _open_set([
            ("Word set: looks / a turtle / cloud / the / like", "Build the comparison as a finished sentence.", "The cloud looks like a turtle.", [evidence("Orders the full comparison.", "cloud looks like a turtle"), evidence("Uses a capital and full stop.", "The", ".")]),
            ("Word set: can / you / see / silver edge / the", "Build the question and add its correct end mark.", "Can you see the silver edge?", [evidence("Creates the correct question order.", "can you see the silver edge"), evidence("Uses a capital and question mark.", "Can", "?")]),
        ]),
        "transfer": _open_set([
            ("Word set: leaves / the / wind / spins / dry", "Transfer the sentence-building steps to this windy scene.", "The wind spins the dry leaves.", [evidence("Uses all words in sensible order.", "wind spins the dry leaves"), evidence("Adds complete statement punctuation.", "The", ".")]),
            ("Word set: why / shadow / moving / is / the", "Arrange the inquiry and punctuate it as a question.", "Why is the shadow moving?", [evidence("Forms the why-question correctly.", "why is the shadow moving"), evidence("Adds a capital and question mark.", "Why", "?")]),
        ]),
        "review": _open_set([
            ("Unfinished line: pink clouds float above the lake", "Repair the line as a complete written sentence.", "Pink clouds float above the lake.", [evidence("Keeps the original word order.", "pink clouds float above the lake"), evidence("Adds the missing capital and full stop.", "Pink", ".")]),
            ("Jumbled line: disappear / stars / do / when / the", "Write the correctly ordered and punctuated question.", "When do the stars disappear?", [evidence("Orders the question correctly.", "when do the stars disappear"), evidence("Uses question punctuation.", "When", "?")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:sentence_boundary_order",
        "misconception": "The learner preserves the jumbled order, drops a supplied word, or treats capitals and end marks as optional decoration.",
        "remediation": "Box the naming part, underline the action, place remaining details, then run a two-point boundary check for capital and end mark.",
        "support": _open_set([
            ("Word set: cloud / one / remains / tiny", "Arrange the statement and finish it.", "One tiny cloud remains.", [evidence("Builds and punctuates the statement.", "one tiny cloud remains", "One", ".")]),
            ("Word set: is / moon / where / the", "Build the location question.", "The finished question is: Where is the moon?", [evidence("Builds and punctuates the question.", "where is the moon", "Where", "?")]),
            ("Line needing repair: the grey cloud has vanished", "Add only the missing sentence boundaries.", "The grey cloud has vanished.", [evidence("Adds capital and full stop.", "The grey cloud has vanished", ".")]),
            ("Word set: like / wing / a / bends / cloud / the", "Build the comparison without dropping a word.", "The cloud bends like a wing.", [evidence("Uses every word in correct order.", "cloud bends like a wing", "The", ".")]),
            ("Line needing repair: what shape do you notice", "Turn the line into a finished question.", "What shape do you notice?", [evidence("Adds question boundaries.", "What shape do you notice", "?")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:cloud_comparison_writer",
        "title": "Write an honest cloud comparison",
        "focus": "construct complete observation and imagination sentences from visible details",
        "outcome": "Write one complete sentence that includes a stated cloud detail and signals an imaginative comparison with like or looks like.",
        "skill_ids": [S["comprehension"], S["sentence"]],
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:poem:1-2", f"{CHAPTER_ID}:write:5"],
        "principle": "Creative cloud writing stays honest by naming an observed detail and marking the imagined object as a comparison, not a fact.",
        "connect": {
            "teaching_block": "A strong comparison has two parts: what the cloud visibly does or looks like, and what that detail reminds the writer of.",
            "passage": "Observation: one long cloud has a pointed front. Imagination: a silver train.",
            "prompt": "Notice that looks like keeps the observation separate from the imaginative idea.",
        },
        "co": choice_task(
            "Observation: a round cloud has two thin wisps above it. Imagination: a rabbit.",
            "Which sentence keeps the visible details and marks the imagined shape?",
            "The round cloud with two wisps looks like a rabbit.",
            ["A real rabbit is sitting in the sky.", "The cloud has no visible shape."],
            skills=[S["comprehension"]],
        ),
        "guided": _open_set([
            ("Observation: a wide cloud has a curved lower edge. Imagination: a boat.", "Create a complete boat comparison using the curved edge.", "The wide cloud with a curved lower edge looks like a boat.", [evidence("Uses the wide curved shape.", "wide cloud", "curved lower edge"), evidence("Marks the boat as comparison.", "looks like a boat", "like a boat")]),
            ("Observation: four small clouds move in a row. Imagination: ducklings.", "Turn the row and movement into one honest comparison.", "Four small clouds move in a row like ducklings following one another.", [evidence("Uses four clouds moving in a row.", "four small clouds", "move in a row"), evidence("Marks the duckling comparison.", "like ducklings", "look like ducklings")]),
        ], interaction="creative_continuation"),
        "independent": _open_set([
            ("Observation: a tall cloud has a broad top and a narrow base. Imagination: a mushroom.", "Write one complete sentence that joins the observation to the imagined shape.", "The tall cloud with a broad top and narrow base looks like a mushroom.", [evidence("Includes broad top and narrow base.", "broad top", "narrow base"), evidence("Uses comparison language for mushroom.", "looks like a mushroom", "like a mushroom")]),
            ("Observation: a pink cloud has two wide sides and a small centre. Imagination: a butterfly.", "Compose a vivid but accurate butterfly comparison.", "The pink cloud spreads two wide sides like a butterfly's wings.", [evidence("Includes pink and two wide sides.", "pink cloud", "two wide sides"), evidence("Signals the butterfly comparison.", "like a butterfly", "butterfly's wings")]),
        ], interaction="creative_continuation"),
        "transfer": _open_set([
            ("Observation: a puddle reflection is long and wavy. Imagination: a ribbon.", "Transfer the comparison pattern to the reflection.", "The long, wavy reflection looks like a ribbon on the water.", [evidence("Uses long and wavy details.", "long", "wavy reflection"), evidence("Marks the ribbon comparison.", "looks like a ribbon", "like a ribbon")]),
            ("Observation: a hill shadow has three sharp peaks. Imagination: a crown.", "Write a complete crown comparison without calling the shadow a real crown.", "The shadow with three sharp peaks looks like a crown.", [evidence("Includes three sharp peaks.", "three sharp peaks"), evidence("Uses looks like for the crown.", "looks like a crown", "like a crown")]),
        ], interaction="creative_continuation"),
        "review": _open_set([
            ("Observation: a dark cloud has a jagged lower edge. Imagination: mountains.", "Review the pattern by writing a complete mountain comparison.", "The dark cloud's jagged lower edge looks like a line of mountains.", [evidence("Uses dark and jagged details.", "dark cloud", "jagged lower edge"), evidence("Signals the mountain comparison.", "looks like a line of mountains", "like mountains")]),
            ("Observation: one tiny cloud trails behind a larger group. Imagination: a lost sheep.", "Write an accurate comparison that includes the cloud's position.", "The tiny cloud trailing behind the group looks like a lost sheep.", [evidence("Includes trailing behind the group.", "trailing behind", "behind the group"), evidence("Marks the sheep comparison.", "looks like a lost sheep", "like a lost sheep")]),
        ], interaction="creative_continuation"),
        "cluster_id": f"{CHAPTER_ID}:comparison_as_fact",
        "misconception": "The learner names only an imagined object, states that object as a literal sky fact, or writes a fragment with no visible cloud detail.",
        "remediation": "Use a two-column observation and imagination frame, require one detail from the first column, and insert like or looks like before completing the sentence.",
        "support": _open_set([
            ("Observation: a flat cloud has one raised end. Imagination: a slide.", "Build a complete slide comparison.", "The flat cloud with one raised end looks like a slide.", [evidence("Uses the raised-end detail and comparison.", "one raised end", "looks like a slide")]),
            ("Observation: a white cloud curls at both ends. Imagination: a moustache.", "Write the observed curl and imagined object in one sentence.", "The white cloud curls at both ends like a moustache.", [evidence("Includes both curls and marks comparison.", "curls at both ends", "like a moustache")]),
            ("Observation: three round clouds touch one another. Imagination: beads.", "Create the complete beads comparison.", "Three touching round clouds look like beads on a string.", [evidence("Includes three touching rounds and comparison.", "three", "round clouds", "look like beads")]),
            ("Observation: a thin cloud bends around the moon. Imagination: a scarf.", "Keep the observation and scarf idea separate in one sentence.", "The thin cloud bends around the moon like a scarf.", [evidence("Uses bending around the moon and like.", "bends around the moon", "like a scarf")]),
            ("Observation: a grey cloud stretches across two rooftops. Imagination: a bridge.", "Finish with a truthful bridge comparison.", "The grey cloud stretching across two rooftops looks like a bridge.", [evidence("Uses the span and comparison.", "across two rooftops", "looks like a bridge")]),
        ], interaction="creative_continuation"),
    },
]


EXTRA_DEPTH = {
    f"{CHAPTER_ID}:changing_cloud_clues": {
        "guided": [
            choice_task(
                "A narrow cloud reaches the chimney, slides across the roof, and then breaks into two pieces.",
                "What happens after the cloud crosses the roof?",
                "It breaks into two pieces.",
                ["It reaches the chimney.", "It becomes one round cloud."],
            ),
            open_task(
                "A strip of mist rises from the pond. It curls around a branch before sunlight clears it.",
                "Tell the first change and the next change before the mist clears.",
                "The mist rises from the pond and then curls around a branch.",
                [
                    evidence("States the first change.", "mist rises from the pond", "rises from the pond first"),
                    evidence("States the next change.", "curls around a branch", "then curls by the branch"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set(
            [
                (
                    "A cloud shadow enters the court, covers the bench, and grows smaller as the cloud moves away.",
                    "Retell the shadow's route and final change in order.",
                    "The shadow enters the court, covers the bench, and finally grows smaller.",
                    [
                        evidence("States the route through the court.", "enters the court", "comes into the court"),
                        evidence("States the middle event.", "covers the bench", "moves over the bench"),
                        evidence("States the final change.", "grows smaller", "becomes smaller at the end"),
                    ],
                ),
                (
                    "One puff above a bakery widens into a ring. A breeze tears the ring into several thin lines.",
                    "Explain the shape change and what causes the final change.",
                    "The puff widens into a ring, and the breeze tears it into thin lines.",
                    [
                        evidence("States the ring change.", "widens into a ring", "becomes a wide ring"),
                        evidence("Names the cause.", "the breeze tears it", "a breeze causes the tear"),
                        evidence("States the final lines.", "into thin lines", "becomes several thin lines"),
                    ],
                ),
            ],
            ordered=True,
        ),
        "transfer": _open_set(
            [
                (
                    "A wet footprint has dark edges at first. The edges dry, and the small centre mark disappears last.",
                    "Use before-and-after thinking to explain the drying order.",
                    "The dark edges dry first, while the centre mark disappears last.",
                    [
                        evidence("States what dries first.", "dark edges dry first", "edges are first to dry"),
                        evidence("States what disappears last.", "centre mark disappears last", "middle mark is last"),
                    ],
                )
            ],
            ordered=True,
        ),
    },
    f"{CHAPTER_ID}:sky_words_in_context": {
        "guided": [
            choice_task(
                "The cloud begins to billow, swelling outward into a large rounded mass.",
                "Which meaning fits billow on this card?",
                "swell outward",
                ["become flat", "drop as rain"],
            ),
            open_task(
                "A small cloud hovers above the stadium, staying over the same spot while others move away.",
                "Explain hovers and use it in a different sky sentence.",
                "Hovers means stays in one place. A pale cloud hovers above the tower.",
                [
                    evidence("Explains the staying meaning.", "stays in one place", "remains over one spot"),
                    evidence("Uses hovers in a new sky idea.", "cloud hovers above the tower", "pale cloud stays above the tower"),
                ],
            ),
        ],
        "independent": _open_set(
            [
                (
                    "A streak of cloud is a long, narrow line across the evening sky.",
                    "Define streak from the clue and use it in a fresh sentence.",
                    "A streak is a long narrow line. A red cloud streak crossed the sunset.",
                    [
                        evidence("Defines the narrow line.", "long narrow line", "thin line across the sky"),
                        evidence("Uses streak in a new sentence.", "cloud streak crossed the sunset", "red streak crossed the sky"),
                    ],
                ),
                (
                    "A cloud bank is a large group of clouds lying together near the horizon.",
                    "Explain cloud bank and make a different accurate use.",
                    "A cloud bank is a large group near the horizon. A dark cloud bank hid the distant hills.",
                    [
                        evidence("Explains the grouped clouds.", "large group near the horizon", "many clouds together low in the sky"),
                        evidence("Uses cloud bank accurately.", "dark cloud bank hid the hills", "cloud bank covered distant hills"),
                    ],
                ),
            ]
        ),
        "transfer": _open_set(
            [
                (
                    "Sunlight is dappled on the path because leaves make many small patches of light and shade.",
                    "Infer dappled and use it for light under thin clouds.",
                    "Dappled means covered with small light and dark patches. Thin clouds made dappled light on the field.",
                    [
                        evidence("Explains the patchy pattern.", "small light and dark patches", "many patches of light and shade"),
                        evidence("Transfers dappled to cloud light.", "clouds made dappled light", "dappled light under thin clouds"),
                    ],
                )
            ]
        ),
    },
    f"{CHAPTER_ID}:cloud_word_spelling": {
        "guided": [
            choice_task(
                "Candidates: thunder, thundar, thuner. The weather report needs the storm word.",
                "Which printed word has the standard spelling?",
                "thunder",
                ["thundar", "thuner"],
            ),
            open_task(
                "Visible chunks: va + pour. The clue names water carried in the air.",
                "Join the chunks and use the completed word in a sentence.",
                "The word is vapour. Water vapour rose above the warm pond.",
                [
                    evidence("Spells the target word.", "word is vapour", "spell it vapour"),
                    evidence("Uses vapour with water in air.", "water vapour rose above the pond", "vapour moved into the air"),
                ],
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Base word: storm. Add y to describe a day with frequent storms.",
                    "Build the new word and write a weather sentence.",
                    "The new word is stormy. We stayed inside on a stormy afternoon.",
                    [
                        evidence("Builds the new spelling.", "new word is stormy", "spell it stormy"),
                        evidence("Uses stormy for weather.", "stormy afternoon", "stormy day"),
                    ],
                ),
                (
                    "Printed chunks: sun + light. The clue names light that comes from the sun.",
                    "Join the chunks and use the word with a cloud.",
                    "The word is sunlight. Sunlight shone through a broken cloud.",
                    [
                        evidence("Spells the joined word.", "word is sunlight", "spell it sunlight"),
                        evidence("Uses sunlight with a cloud.", "sunlight shone through a cloud", "cloud let sunlight through"),
                    ],
                ),
            ]
        ),
        "transfer": _open_set(
            [
                (
                    "Base word: moon. Add lit to mean lighted by the moon.",
                    "Build the new word and write a night-sky sentence.",
                    "The new word is moonlit. A moonlit cloud edge looked silver.",
                    [
                        evidence("Builds the moon word.", "new word is moonlit", "spell it moonlit"),
                        evidence("Uses moonlit in the night sky.", "moonlit cloud edge", "moonlit sky"),
                    ],
                )
            ]
        ),
    },
    f"{CHAPTER_ID}:cloud_word_jobs": {
        "guided": [
            choice_task(
                "A silver wisp curls gently.",
                "Which word names the action in this sky sentence?",
                "curls",
                ["silver", "wisp"],
            ),
            open_task(
                "The pale moon lights a narrow cloud.",
                "Label moon, lights, pale, and narrow by their word jobs.",
                "Moon is a noun, lights is a verb, and pale and narrow are adjectives.",
                [
                    evidence("Labels the naming word.", "moon is a noun", "moon names a thing"),
                    evidence("Labels the action word.", "lights is a verb", "lights shows the action"),
                    evidence("Labels pale.", "pale is an adjective", "pale tells what kind"),
                    evidence("Labels narrow.", "narrow is an adjective", "narrow tells what kind"),
                ],
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Bright lightning splits the dark sky.",
                    "Classify lightning, splits, bright, and dark.",
                    "Lightning is a noun, splits is a verb, and bright and dark are adjectives.",
                    [
                        evidence("Labels lightning.", "lightning is a noun", "lightning names a thing"),
                        evidence("Labels splits.", "splits is a verb", "splits shows action"),
                        evidence("Labels bright.", "bright is an adjective", "bright describes lightning"),
                        evidence("Labels dark.", "dark is an adjective", "dark describes the sky"),
                    ],
                ),
                (
                    "A sudden shower cools the dusty road.",
                    "Give the jobs of shower, cools, sudden, and dusty.",
                    "Shower is a noun, cools is a verb, and sudden and dusty are adjectives.",
                    [
                        evidence("Labels shower.", "shower is a noun", "shower names a thing"),
                        evidence("Labels cools.", "cools is a verb", "cools shows action"),
                        evidence("Labels sudden.", "sudden is an adjective", "sudden tells what kind"),
                        evidence("Labels dusty.", "dusty is an adjective", "dusty describes the road"),
                    ],
                ),
            ]
        ),
        "transfer": _open_set(
            [
                (
                    "The blue notice warns careful walkers.",
                    "Transfer the word-job check to notice, warns, blue, and careful.",
                    "Notice is a noun, warns is a verb, and blue and careful are adjectives.",
                    [
                        evidence("Labels notice.", "notice is a noun", "notice names a thing"),
                        evidence("Labels warns.", "warns is a verb", "warns shows action"),
                        evidence("Labels blue.", "blue is an adjective", "blue describes the notice"),
                        evidence("Labels careful.", "careful is an adjective", "careful describes walkers"),
                    ],
                )
            ]
        ),
    },
    f"{CHAPTER_ID}:sky_sentence_builder": {
        "guided": [
            choice_task(
                "Word set: mist / the / covers / bridge / the",
                "Which option makes a complete sky statement?",
                "The mist covers the bridge.",
                ["Mist the bridge covers the.", "the Mist covers bridge the"],
            ),
            open_task(
                "Word set: cloud / which / is / lowest / the",
                "Arrange the words as a finished question.",
                "Which cloud is the lowest?",
                [
                    evidence("Uses the question order.", "which cloud is the lowest", "ask which cloud is lowest"),
                    evidence("Uses a natural question ending.", "cloud is the lowest?", "is the lowest?"),
                ],
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Word set: behind / moon / slips / cloud / the / the",
                    "Build one complete movement statement.",
                    "The cloud slips behind the moon.",
                    [
                        evidence("Uses every word in order.", "cloud slips behind the moon", "the cloud moves behind the moon"),
                        evidence("Uses a natural full-stop ending.", "behind the moon.", "the moon."),
                    ],
                ),
                (
                    "Word set: rain / will / when / begin / the",
                    "Turn the word set into a complete question.",
                    "When will the rain begin?",
                    [
                        evidence("Uses the question order.", "when will the rain begin", "ask when rain will begin"),
                        evidence("Uses a natural question ending.", "rain begin?", "the rain begin?"),
                    ],
                ),
            ]
        ),
        "transfer": _open_set(
            [
                (
                    "Word set: gate / please / close / the / gently",
                    "Use the same ordering steps for this polite command.",
                    "Please close the gate gently.",
                    [
                        evidence("Uses the polite command order.", "please close the gate gently", "close the gate gently please"),
                        evidence("Uses a natural statement ending.", "gate gently.", "the gate gently."),
                    ],
                )
            ]
        ),
    },
    f"{CHAPTER_ID}:cloud_comparison_writer": {
        "guided": [
            choice_task(
                "Observation: a cloud has a square middle and four short corners. Imagination: a kite.",
                "Which sentence keeps the kite as a comparison?",
                "The square cloud looks like a kite.",
                ["A real kite became the cloud.", "The cloud has no visible corners."],
                skills=[S["comprehension"]],
            ),
            open_task(
                "Observation: two thin clouds cross at the centre. Imagination: a letter X.",
                "Write one honest comparison using the crossing detail.",
                "The two thin clouds cross like the lines in a letter X.",
                [
                    evidence("Uses the visible crossing.", "two thin clouds cross", "thin clouds meet at the centre"),
                    evidence("Marks the imagined X as a comparison.", "like the lines in a letter X", "looks like a letter X"),
                ],
                interaction="creative_continuation",
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Observation: a cloud has six rounded bumps along its top. Imagination: a flower crown.",
                    "Create a complete comparison with the rounded bumps.",
                    "The cloud's six rounded bumps look like a flower crown.",
                    [
                        evidence("Uses all six rounded bumps.", "six rounded bumps", "six curved bumps"),
                        evidence("Signals the flower-crown comparison.", "look like a flower crown", "like a crown of flowers"),
                    ],
                ),
                (
                    "Observation: a low cloud forms a long arch over the field. Imagination: a doorway.",
                    "Write a truthful doorway comparison from the arch detail.",
                    "The low cloud forms a long arch like a doorway over the field.",
                    [
                        evidence("Uses the low arch detail.", "low cloud forms a long arch", "long arch over the field"),
                        evidence("Signals the doorway comparison.", "like a doorway", "looks like a doorway"),
                    ],
                ),
            ],
            interaction="creative_continuation",
        ),
        "transfer": _open_set(
            [
                (
                    "Observation: frost makes branching white lines on a window. Imagination: tiny trees.",
                    "Transfer honest comparison writing to the frost pattern.",
                    "The branching white frost lines look like tiny trees on the window.",
                    [
                        evidence("Uses the branching white lines.", "branching white frost lines", "white lines branch on the window"),
                        evidence("Signals the tree comparison.", "look like tiny trees", "like a group of tiny trees"),
                    ],
                )
            ],
            interaction="creative_continuation",
        ),
    },
}

LAUNCH_DEPTH = {
    f"{CHAPTER_ID}:changing_cloud_clues": {
        "transfer": _open_set(
            [
                (
                    "A soap bubble begins round beside the tap, stretches into an oval as it floats, and bursts against a leaf.",
                    "Apply change-order thinking to the bubble's shape and ending.",
                    "The bubble starts round, stretches into an oval, and finally bursts against the leaf.",
                    [
                        evidence("States the starting shape.", "starts round", "begins round"),
                        evidence("States the middle change.", "stretches into an oval", "becomes an oval"),
                        evidence("States the ending.", "bursts against the leaf", "finally bursts"),
                    ],
                )
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "Morning fog hides the far goalpost. Sunlight reaches the field, the fog becomes patchy, and the goalpost appears.",
                    "Explain the fog changes from hidden view to clear view.",
                    "The fog first hides the goalpost, then becomes patchy in sunlight, and finally reveals the goalpost.",
                    [
                        evidence("States the hidden start.", "first hides the goalpost", "fog hides the goalpost"),
                        evidence("States the patchy change.", "becomes patchy in sunlight", "fog becomes patchy"),
                        evidence("States the clear ending.", "reveals the goalpost", "goalpost appears"),
                    ],
                ),
                (
                    "A kite's shadow is small near noon. Later it lengthens across the terrace and reaches the flower pot.",
                    "Compare the earlier shadow with its later size and position.",
                    "The shadow is small near noon but later grows long enough to reach the flower pot.",
                    [
                        evidence("States the earlier size.", "shadow is small near noon", "small near noon"),
                        evidence("States the later change.", "grows long enough to reach the flower pot", "lengthens across the terrace"),
                    ],
                ),
            ],
            ordered=True,
        ),
    },
    f"{CHAPTER_ID}:sky_words_in_context": {
        "transfer": _open_set(
            [
                (
                    "A glimmer is a faint, unsteady light. One glimmer appears on the wet railing when the sun slips between two clouds.",
                    "Explain glimmer and use it in a different sky sentence.",
                    "A glimmer is a small faint light. A glimmer of moonlight shone through the evening cloud.",
                    [
                        evidence("Explains the light word.", "small faint light", "faint light"),
                        evidence("Uses glimmer freshly.", "glimmer of moonlight shone through the evening cloud", "glimmer of moonlight"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "The cloud layer is dense, with many thick clouds packed closely enough to hide the blue sky.",
                    "Infer dense from the clue and use it for another visible group.",
                    "Dense means packed closely together. A dense group of leaves shaded the bench.",
                    [
                        evidence("Explains dense.", "packed closely together", "closely packed"),
                        evidence("Uses dense in a new scene.", "dense group of leaves shaded the bench", "dense group of leaves"),
                    ],
                ),
                (
                    "After the wind arrives, the cloud pieces scatter, moving away from one another across different parts of the sky.",
                    "State what scatter means and write one fresh use.",
                    "Scatter means spread in different directions. The children scatter seeds across the garden bed.",
                    [
                        evidence("Explains scatter.", "spread in different directions", "move away from one another"),
                        evidence("Uses scatter accurately.", "children scatter seeds across the garden bed", "scatter seeds"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:cloud_word_spelling": {
        "transfer": _open_set(
            [
                (
                    "Visible chunks: rain + bow. The clue names a coloured arc that may appear after rain.",
                    "Join the chunks and use the completed word in a weather sentence.",
                    "The word is rainbow. A bright rainbow appeared above the wet playground.",
                    [
                        evidence("Spells the joined word.", "word is rainbow", "spell it rainbow"),
                        evidence("Uses rainbow in context.", "bright rainbow appeared above the wet playground", "rainbow appeared"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Base word: mist. Add y to describe a morning filled with light mist.",
                    "Build the new word and write a complete morning sentence.",
                    "The new word is misty. We walked carefully on a misty morning.",
                    [
                        evidence("Builds the new spelling.", "new word is misty", "spell it misty"),
                        evidence("Uses misty accurately.", "walked carefully on a misty morning", "misty morning"),
                    ],
                ),
                (
                    "Printed parts: sun + shine. The clue names bright light coming from the sun.",
                    "Join the parts and use the word beside a cloud detail.",
                    "The word is sunshine. Warm sunshine reached the field between two grey clouds.",
                    [
                        evidence("Spells the joined word.", "word is sunshine", "spell it sunshine"),
                        evidence("Uses sunshine with clouds.", "sunshine reached the field between two grey clouds", "Warm sunshine"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:cloud_word_jobs": {
        "transfer": _open_set(
            [
                (
                    "The curious child watches a distant balloon.",
                    "Classify child, watches, curious, and distant.",
                    "Child is a noun, watches is a verb, and curious and distant are adjectives.",
                    [
                        evidence("Labels child.", "Child is a noun", "child names a person"),
                        evidence("Labels watches.", "watches is a verb", "watches shows action"),
                        evidence("Labels curious.", "curious is an adjective", "curious describes the child"),
                        evidence("Labels distant.", "distant is an adjective", "distant describes the balloon"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "A sudden breeze shakes the yellow curtain.",
                    "Give the word jobs of breeze, shakes, sudden, and yellow.",
                    "Breeze is a noun, shakes is a verb, and sudden and yellow are adjectives.",
                    [
                        evidence("Labels breeze.", "Breeze is a noun", "breeze names a thing"),
                        evidence("Labels shakes.", "shakes is a verb", "shakes shows action"),
                        evidence("Labels sudden.", "sudden is an adjective", "sudden describes the breeze"),
                        evidence("Labels yellow.", "yellow is an adjective", "yellow describes the curtain"),
                    ],
                ),
                (
                    "The quiet painter mixes pale colours.",
                    "Classify painter, mixes, quiet, and pale by their jobs in this art sentence.",
                    "Painter is a noun, mixes is a verb, and quiet and pale are adjectives.",
                    [
                        evidence("Labels painter.", "Painter is a noun", "painter names a person"),
                        evidence("Labels mixes.", "mixes is a verb", "mixes shows action"),
                        evidence("Labels quiet.", "quiet is an adjective", "quiet describes the painter"),
                        evidence("Labels pale.", "pale is an adjective", "pale describes the colours"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:sky_sentence_builder": {
        "transfer": _open_set(
            [
                (
                    "Word set: after rain / small puddles / reflect / the bright sky",
                    "Build a sky sentence that uses every word-set part.",
                    "Small puddles reflect the bright sky after rain.",
                    [
                        evidence("Uses the natural subject-action order.", "Small puddles reflect the bright sky", "puddles reflect"),
                        evidence("Keeps the time phrase.", "after rain", "sky after rain"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Word set: why / the cloud / is / turning pink",
                    "Build a finished question with every word.",
                    "Why is the cloud turning pink?",
                    [
                        evidence("Uses question order.", "Why is the cloud turning pink", "cloud turning pink"),
                        evidence("Uses a natural question ending.", "turning pink?", "cloud turning pink?"),
                    ],
                ),
                (
                    "Word set: gently / across the moon / a thin cloud / drifts",
                    "Write one correctly ordered sky sentence.",
                    "A thin cloud drifts gently across the moon.",
                    [
                        evidence("Orders the subject and action.", "thin cloud drifts gently", "cloud drifts"),
                        evidence("Keeps the place phrase.", "across the moon", "gently across the moon"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:cloud_comparison_writer": {
        "transfer": _open_set(
            [
                (
                    "Observation: a long puddle reflects three round streetlights. Imagination: a string of glowing beads.",
                    "Write a truthful comparison using the reflected circles.",
                    "The three round streetlight reflections look like glowing beads in the long puddle.",
                    [
                        evidence("Uses the observed circles.", "three round streetlight reflections", "round reflections"),
                        evidence("Marks the bead idea as comparison.", "look like glowing beads", "like glowing beads"),
                    ],
                )
            ],
            interaction="creative_continuation",
        ),
        "review": _open_set(
            [
                (
                    "Observation: two curved cloud strips meet above the tower. Imagination: open wings.",
                    "Create one complete comparison from both curved strips.",
                    "The two curved cloud strips look like open wings above the tower.",
                    [
                        evidence("Uses both curved strips.", "two curved cloud strips", "curved strips meet"),
                        evidence("Signals the wing comparison.", "look like open wings", "like open wings"),
                    ],
                ),
                (
                    "Observation: a small grey cloud has a pointed front and a trailing thin end. Imagination: a paper boat.",
                    "Write an honest paper-boat comparison with the visible details.",
                    "The pointed grey cloud with its trailing thin end looks like a paper boat.",
                    [
                        evidence("Uses the pointed and trailing shape.", "pointed grey cloud with its trailing thin end", "pointed front"),
                        evidence("Signals the boat comparison.", "looks like a paper boat", "like a paper boat"),
                    ],
                ),
            ],
            interaction="creative_continuation",
        ),
    },
}

for _level in LEVELS:
    _existing_depth = EXTRA_DEPTH[_level["level_id"]]
    _launch_depth = LAUNCH_DEPTH[_level["level_id"]]
    _level["depth"] = {
        **_existing_depth,
        "transfer": [
            *_existing_depth.get("transfer", []),
            *_launch_depth["transfer"],
        ],
        "review": list(_launch_depth["review"]),
    }


def _assessment_form(label: str) -> list[dict[str, Any]]:
    if label == "a":
        return [
            choice_task("The cloud is translucent, so sunlight can partly pass through it.", "Which meaning fits translucent?", "partly see-through", ["completely black", "full of rain"], skills=[S["word_context"]]),
            choice_task("A grey cloud rests above the clock tower while two white clouds move east.", "Which cloud stays above the tower?", "the grey cloud", ["both white clouds", "no cloud"], skills=[S["comprehension"]]),
            choice_task("The mist gathers, covers the field, and later lifts after sunrise.", "Which event happens second?", "The mist covers the field.", ["The mist lifts.", "Sunrise ends."], skills=[S["sequence"]]),
            choice_task("Sentence: A gentle breeze nudges the cloud slowly.", "Which word best completes another sentence about mild wind?", "gentle", ["jagged", "motionless"], skills=[S["word_use"]]),
            choice_task("Candidates: silver, silvar, sillver. The sentence needs the colour word.", "Which candidate uses the standard spelling?", "silver", ["silvar", "sillver"], skills=[S["spelling"]]),
            choice_task("The fluffy cloud floats north.", "Which word shows the action?", "floats", ["fluffy", "cloud"], skills=[S["word_jobs"]]),
            open_task("Word set: cloud / the / above / hovers / bridge / the", "Arrange all words as one correct statement.", "The cloud hovers above the bridge.", [evidence("Uses the complete correct order.", "cloud hovers above the bridge"), evidence("Uses every supplied word.", "the cloud", "the bridge")], skills=[S["sentence_order"]]),
            open_task("Unfinished line: where did the bright cloud go", "Add the correct beginning capital and end mark.", "Where did the bright cloud go?", [evidence("Uses the capital beginning.", "Where"), evidence("Uses a question mark.", "?")], skills=[S["punctuation"]]),
            open_task("Observation: a narrow cloud curves like a hook.", "Write one complete sentence preserving the visible comparison.", "The narrow cloud curves like a hook.", [evidence("Includes the narrow curved cloud.", "narrow cloud", "curves"), evidence("Keeps the hook comparison.", "like a hook")], skills=[S["sentence"]]),
            open_task("A cloud begins beside the sun, moves over the tower, and ends beyond the river.", "Retell the route in order and include the final place.", "The cloud starts beside the sun, crosses the tower, and ends beyond the river.", [evidence("Orders the first two places.", "beside the sun", "over the tower"), evidence("Ends beyond the river.", "beyond the river")], skills=[S["comprehension"], S["sequence"]], ordered=True),
            open_task("A dense cloud is packed so thickly that the sky behind it cannot be seen. Use dense in a new sentence.", "Explain the clue meaning and write the new use.", "Dense means thick. A dense cloud covered the afternoon sky.", [evidence("Explains the thick meaning.", "means thick", "very thick"), evidence("Uses dense for a cloud.", "dense cloud")], skills=[S["word_context"], S["word_use"]]),
            open_task("Word set: clouds / do / why / gather / here", "Build and punctuate the complete question.", "Why do clouds gather here?", [evidence("Uses correct question order.", "why do clouds gather here"), evidence("Uses capital and question mark.", "Why", "?")], skills=[S["sentence_order"], S["punctuation"]]),
        ]
    return [
        choice_task("The clouds disperse, moving away until the group is spread across the sky.", "Which meaning fits disperse?", "spread away from one another", ["join into one mass", "turn into rain"], skills=[S["word_context"]]),
        choice_task("One low cloud hides the hill, but a higher cloud remains near the moon.", "Which cloud hides the hill?", "the low cloud", ["the higher cloud", "both clouds"], skills=[S["comprehension"]]),
        choice_task("First the cloud turns pink, next it grows dim, and last it vanishes after sunset.", "Which event comes immediately before vanishing?", "It grows dim.", ["It turns pink.", "It becomes sunrise."], skills=[S["sequence"]]),
        choice_task("Sentence frame: The clouds ___ apart after the wind changes.", "Which chapter word fits the movement?", "scatter", ["polish", "plant"], skills=[S["word_use"]]),
        choice_task("Candidates: weather, wether, weathar. The report needs the standard word.", "Which candidate is correctly spelled?", "weather", ["wether", "weathar"], skills=[S["spelling"]]),
        choice_task("A brilliant edge surrounds the cloud.", "Which word describes the edge?", "brilliant", ["edge", "surrounds"], skills=[S["word_jobs"]]),
        open_task("Word set: thin / two / drift / wisps / west", "Arrange the words into one complete statement.", "Two thin wisps drift west.", [evidence("Uses the correct complete order.", "two thin wisps drift west"), evidence("Keeps every content word.", "thin wisps", "west")], skills=[S["sentence_order"]]),
        open_task("Unfinished line: the cloud looks like a crown", "Repair both sentence boundaries.", "The cloud looks like a crown.", [evidence("Adds the beginning capital.", "The"), evidence("Adds the full stop.", ".")], skills=[S["punctuation"]]),
        open_task("Observation: three dark clouds move together like a slow parade.", "Write the observation as one complete sentence.", "Three dark clouds move together like a slow parade.", [evidence("Includes three dark moving clouds.", "three dark clouds", "move together"), evidence("Includes the parade comparison.", "like a slow parade")], skills=[S["sentence"]]),
        open_task("A white patch enters above the gate, widens near the hall, and splits beside the field.", "Give the movement and final change in order.", "The patch enters above the gate, widens near the hall, and splits beside the field.", [evidence("Orders entry and widening.", "above the gate", "widens near the hall"), evidence("Ends with splitting beside the field.", "splits beside the field")], skills=[S["comprehension"], S["sequence"]], ordered=True),
        open_task("A wispy cloud has thin strands. Use wispy accurately in another sentence.", "State the context meaning and create the new use.", "Wispy means thin and feathery. A wispy cloud crossed the pale sun.", [evidence("Explains thin strands.", "thin and feathery", "thin strands"), evidence("Uses wispy with a cloud.", "wispy cloud")], skills=[S["word_context"], S["word_use"]]),
        open_task("Word set: why / do / the / stars / shine / at night", "Build the finished question with correct punctuation.", "Why do the stars shine at night?", [evidence("Uses correct question order.", "why do the stars shine at night", "stars shine at night"), evidence("Uses capital and question mark.", "Why do the stars", "shine at night?")], skills=[S["sentence_order"], S["punctuation"]]),
    ]


CONFIG = {
    "chapter_id": CHAPTER_ID,
    "chapter_no": 8,
    "title": "A Show of Clouds",
    "unit_title": "Life Around Us",
    "source_url": SOURCE_URL,
    "extract_path": "/tmp/zidd-ncert-class2-3/eng_c2_ch08.txt",
    "source_anchors": [
        {"anchor_id": f"{CHAPTER_ID}:poem:1-2", "section_label": "Poem and imagined cloud forms", "page_start": 1, "page_end": 2, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:speak:3-4", "section_label": "Let us speak: sky observation and full sentences", "page_start": 3, "page_end": 4, "source_url": SOURCE_URL, "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:write:5", "section_label": "Let us write: day and night sky details", "page_start": 5, "page_end": 5, "source_url": SOURCE_URL, "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:draw:6", "section_label": "Let us draw: alphabet picture activity", "page_start": 6, "page_end": 6, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:listen:7", "section_label": "Let us listen: teacher-led printed ck word set", "page_start": 7, "page_end": 7, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
    ],
    "levels": LEVELS,
    "assessment_forms": [_assessment_form("a"), _assessment_form("b")],
}


MANIFEST = build_manifest(CONFIG)
