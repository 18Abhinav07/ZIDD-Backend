"""Deep authored manifest for Class 3 English Chapter 1.

The official chapter was used only to map sections, themes, and exercise
forms. Every learner-facing passage, prompt, option, rubric, and answer is
original Zidd content.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

CHAPTER_ID = "eng_c3_ch01"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/cesa101.pdf"


_GRAMMAR_PRESERVING_CLASS_3_REPLACEMENTS = (
    ("central idea", "main idea"),
    ("justify", "give a reason for"),
    ("infer", "work out"),
    ("concise", "short and clear"),
    ("infers", "works out"),
    ("supplied", "given"),
    ("concisely", "in a short, clear way"),
    ("accurately", "correctly"),
)


_SEMANTIC_REQUIRED_PART = re.compile(r"\s+Required part \d+\.$")
_SEMANTIC_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|[0-9]+")
_SEMANTIC_LABEL_STOP_WORDS = {
    "about",
    "action",
    "add",
    "after",
    "answer",
    "assessment",
    "because",
    "before",
    "card",
    "change",
    "choose",
    "complete",
    "doer",
    "doers",
    "draft",
    "details",
    "facts",
    "fragment",
    "from",
    "given",
    "jumbled",
    "letters",
    "meaning",
    "object",
    "parts",
    "passage",
    "place",
    "prompt",
    "scene",
    "sentence",
    "target",
    "the",
    "their",
    "there",
    "this",
    "these",
    "they",
    "those",
    "through",
    "use",
    "using",
    "which",
    "while",
    "with",
    "word",
    "words",
}
_SEMANTIC_LEADING_IMPERATIVES = (
    ("Correctly identifies or uses", "Identify or use"),
    ("Produces", "Produce"),
    ("Preserves", "Preserve"),
    ("Proposes", "Propose"),
    ("Explains", "Explain"),
    ("Identifies", "Identify"),
    ("Includes", "Include"),
    ("Answers", "Answer"),
    ("Builds", "Build"),
    ("Captures", "Summarise"),
    ("Chooses", "Choose"),
    ("Connects", "Connect"),
    ("Defines", "Define"),
    ("Forms", "Form"),
    ("Links", "Link"),
    ("Names", "Name"),
    ("Orders", "Order"),
    ("Places", "Place"),
    ("Repairs", "Repair"),
    ("States", "State"),
    ("Uses", "Use"),
    ("Writes", "Write"),
    ("Works out", "Work out"),
)


def _semantic_context_label(passage: str) -> str:
    tokens = [
        token.casefold()
        for token in _SEMANTIC_WORD.findall(passage)
        if len(token) >= 4
        and token.casefold() not in _SEMANTIC_LABEL_STOP_WORDS
    ]
    unique: list[str] = []
    for token in tokens:
        if token not in unique:
            unique.append(token)
        if len(unique) == 4:
            break
    return " ".join(unique) or "new example"


def _semantic_label_list(label: str) -> str:
    words = label.split()
    if len(words) == 1:
        return words[0]
    if len(words) == 2:
        return f"{words[0]} and {words[1]}"
    return f"{', '.join(words[:-1])}, and {words[-1]}"


def _semantic_contextual_prompt(
    passage: str,
    prompt: str,
    phase: str,
) -> str:
    label = _semantic_label_list(_semantic_context_label(passage))
    lead = {
        "co_construct": "Follow",
        "guided": "Use the clues",
        "independent": "Work from",
        "transfer": "Consider",
        "review": "Review",
        "bridge": "Use the clues",
        "masterclass": "Use the clues",
        "revision_level_1": "Use the clues",
        "revision_level_2": "Use the clues",
        "revision_level_3": "Use the clues",
    }.get(phase, "Use")
    task = prompt.strip()
    if task:
        task = task[0].upper() + task[1:]
    return f"{lead} {label}. {task}"


def _semantic_specific_instruction(slots: list[dict[str, Any]]) -> str:
    instructions: list[str] = []
    for slot in slots:
        description = _SEMANTIC_REQUIRED_PART.sub(
            ".", slot["description"]
        ).replace("..", ".")
        description = description.replace("whole-card", "whole passage")
        description = description.replace("target ", "focus ")
        for old, new in _SEMANTIC_LEADING_IMPERATIVES:
            if description.startswith(old):
                description = new + description[len(old) :]
                break
        for old, new in (
            (" and cites ", " and cite "),
            (" and explains ", " and explain "),
            (" and gives ", " and give "),
            (" and states ", " and state "),
            (" and uses ", " and use "),
            (" and writes ", " and write "),
            (" or uses ", " or use "),
        ):
            description = description.replace(old, new)
        if description not in instructions:
            instructions.append(description)
    instruction = (
        " ".join(instructions) + " Write in complete sentences."
        if instructions
        else "Answer every part using a clear detail from the passage."
    )
    for old, new in (
        ("Explain the focus colour expression", "Explain the colour expression"),
        ("Form the focus spelling or compound", "Form the required spelling or compound"),
        ("Use the focus chapter word", "Use the chapter word"),
        ("Use the focus chapter trait", "Use the chapter trait"),
        ("and explains its effect", "and explain its effect"),
        ("and cites the relevant step", "and cite the relevant step"),
        ("Cites a visible behaviour", "Cite a visible behaviour"),
        (
            "and explains its rhythmic or meaning effect",
            "and explain its rhythmic or meaning effect",
        ),
    ):
        instruction = instruction.replace(old, new)
    return instruction


def _class3_text(value: str) -> str:
    cleaned = value.strip()
    # Context-sensitive words such as "attribute" must be authored in place.
    # These remaining substitutions preserve the source phrase's grammar.
    for old, new in _GRAMMAR_PRESERVING_CLASS_3_REPLACEMENTS:
        cleaned = re.sub(
            rf"\b{re.escape(old)}\b",
            new,
            cleaned,
            flags=re.IGNORECASE,
        )
    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned


def _normalized_authority(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().casefold()
    return re.sub(r"\s+", " ", normalized)


def _authority_matches(answer: str, alias: str) -> bool:
    normalized_answer = _normalized_authority(answer)
    normalized_alias = _normalized_authority(alias)
    pattern = re.escape(normalized_alias).replace(r"\ ", r"\s+")
    return bool(re.search(rf"(?<!\w){pattern}(?!\w)", normalized_answer))


def _natural_authority(alias: str) -> str:
    cleaned = alias.strip()
    lowered = cleaned.casefold()
    if lowered.endswith(" capital"):
        stem = cleaned[:-8].strip()
        if (
            len(stem.split()) <= 4
            and " is " not in stem.casefold()
            and "begins" not in stem.casefold()
            and "with" not in stem.casefold()
        ):
            return f"capital letter for {stem}"
        return cleaned
    for suffix, replacement in (
        (" naming words", " are naming words"),
        (" naming word", " is the naming word"),
        (" action words", " are action words"),
        (" action word", " is the action word"),
        (" describing words", " are describing words"),
        (" describing word", " is a describing word"),
        (" nouns", " are nouns"),
        (" noun", " is a noun"),
        (" verbs", " are verbs"),
        (" verb", " is the verb"),
        (" adjectives", " are describing words"),
        (" adjective", " is a describing word"),
    ):
        if lowered.endswith(suffix):
            stem = cleaned[:-len(suffix)].strip()
            lowered_stem = stem.casefold()
            if replacement.startswith(" are") and lowered_stem.endswith(" are"):
                return cleaned
            if replacement.startswith(" is") and re.search(
                r"\bis(?:\s+(?:a|the))?$",
                lowered_stem,
            ):
                return cleaned
            return f"{stem}{replacement}"
    return cleaned


def _closed_open_authority(
    model_answer: str,
    evidence: list[tuple[str, str, list[str]]],
    *,
    ordered: bool,
) -> tuple[str, list[tuple[str, str, list[str]]]]:
    """Make the approved answer obey independently authored concept slots."""

    closed_evidence: list[tuple[str, str, list[str]]] = []
    missing_authorities: list[str] = []
    alias_owners: dict[str, str] = {}
    for suffix, description, raw_aliases in evidence:
        aliases = list(
            dict.fromkeys(
                _natural_authority(alias.strip()) for alias in raw_aliases
            )
        )
        natural = aliases[0]
        for alias in aliases:
            normalized_alias = _normalized_authority(alias)
            previous_owner = alias_owners.get(normalized_alias)
            if previous_owner is not None and previous_owner != suffix:
                raise ValueError(
                    f"class3_open_alias_shared:{previous_owner}:{suffix}:"
                    f"{normalized_alias}"
                )
            alias_owners[normalized_alias] = suffix
        if not any(_authority_matches(model_answer, alias) for alias in aliases):
            missing_authorities.append(natural)
        closed_evidence.append((suffix, description, aliases))

    closed_model = model_answer.strip()
    if missing_authorities:
        key_line = "; ".join(missing_authorities)
        label = "Order ideas" if ordered else "Key ideas"
        closed_model = f"{closed_model} {label}: {key_line}."

    for _, _, aliases in closed_evidence:
        if not any(_authority_matches(closed_model, alias) for alias in aliases):
            raise ValueError("class3_open_model_answer_does_not_close")
    return closed_model, closed_evidence


def _relevance_terms(
    evidence: list[tuple[str, str, list[str]]],
) -> list[str]:
    terms = list(
        dict.fromkeys(
            alias
            for _, _, aliases in evidence
            for alias in aliases
            if len(alias.strip()) >= 3
        )
    )
    if len(terms) < 2:
        raise ValueError("class3_open_task_needs_two_authored_relevance_terms")
    return terms


def _task(
    passage: str,
    prompt: str,
    model_answer: str,
    evidence: list[tuple[str, str, list[str]]],
    *,
    interaction_type: str = "evidence_text",
    min_words: int = 6,
    skills: list[str] | None = None,
    ordered: bool = False,
) -> dict[str, Any]:
    return {
        "passage": passage,
        "prompt": _class3_text(prompt),
        "model_answer": model_answer,
        "evidence": evidence,
        "interaction_type": interaction_type,
        "min_words": min_words,
        "skills": skills,
        "ordered": ordered,
    }


def _choice(
    passage: str,
    prompt: str,
    correct: str,
    distractors: list[str],
    *,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "passage": passage,
        "prompt": _class3_text(prompt),
        "correct": correct,
        "distractors": distractors,
        "skills": skills,
    }


def _evidence(
    key: str,
    description: str,
    *phrases: str,
) -> tuple[str, str, list[str]]:
    return key, _class3_text(description), list(phrases)


def _required_claim_evidence(
    *,
    key_prefix: str,
    description: str,
    raw_claims: list[Any],
) -> list[tuple[str, str, list[str]]]:
    """Compile each co-required claim as its own slot.

    A nested list represents true alternative phrasings of one claim. A plain
    string is one independently required claim.
    """

    evidence: list[tuple[str, str, list[str]]] = []
    for claim_index, raw_claim in enumerate(raw_claims, start=1):
        aliases = [raw_claim] if isinstance(raw_claim, str) else list(raw_claim)
        aliases = list(dict.fromkeys(alias.strip() for alias in aliases))
        if not aliases or any(not alias for alias in aliases):
            raise ValueError("class3_open_required_claim_empty")
        claim_description = (
            description
            if len(raw_claims) == 1
            else f"{description} Required part {claim_index}."
        )
        evidence.append(
            _evidence(
                f"{key_prefix}_claim_{claim_index}",
                claim_description,
                *aliases,
            )
        )
    return evidence


def _open_activity(
    *,
    level_id: str,
    phase: str,
    index: int,
    level_skills: list[str],
    task: dict[str, Any],
    teaching_block: str | None = None,
) -> dict[str, Any]:
    activity_id = f"{level_id}:{phase}:{index}"
    model_answer, evidence = _closed_open_authority(
        task["model_answer"],
        task["evidence"],
        ordered=task["ordered"],
    )
    slots = []
    criteria = []
    for suffix, description, aliases in evidence:
        slot_id = f"{activity_id}:{suffix}"
        slots.append(
            {"id": slot_id, "description": description, "any_of": aliases}
        )
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.7,
            }
        )
    payload = {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": teaching_block or _semantic_specific_instruction(slots),
        "passage": task["passage"],
        "prompt": _semantic_contextual_prompt(
            task["passage"], task["prompt"], phase
        ),
        "skill_ids": list(task.get("skills") or level_skills),
        "interaction_type": task["interaction_type"],
        "rubric_criteria": criteria,
        "concept_slots": slots,
        "forbidden_phrases": [
            "The card does not matter",
            "I copied a hidden answer",
        ],
        "min_response_words": task["min_words"],
        "relevance_terms": _relevance_terms(evidence),
        "model_answer": model_answer,
        "pass_score": 0.8,
    }
    return payload


def _choice_activity(
    *,
    level_id: str,
    phase: str,
    index: int,
    level_skills: list[str],
    task: dict[str, Any],
    teaching_block: str | None = None,
) -> dict[str, Any]:
    activity_id = f"{level_id}:{phase}:{index}"
    raw_options = [task["correct"], *task["distractors"]]
    shift = sum(ord(char) for char in activity_id) % len(raw_options)
    options = raw_options[shift:] + raw_options[:shift]
    return {
        "kind": "selected_option",
        "activity_id": activity_id,
        "teaching_block": teaching_block
        or (
            "Read the card and the question. Find the clue that answers the "
            "question, then choose one option."
        ),
        "passage": task["passage"],
        "prompt": _semantic_contextual_prompt(
            task["passage"], task["prompt"], phase
        ),
        "skill_ids": list(task.get("skills") or level_skills),
        "options": options,
        "accepted_answers": [task["correct"]],
    }


def _activity(
    *,
    level_id: str,
    phase: str,
    index: int,
    level_skills: list[str],
    task: dict[str, Any],
    teaching_block: str | None = None,
) -> dict[str, Any]:
    if "correct" in task:
        return _choice_activity(
            level_id=level_id,
            phase=phase,
            index=index,
            level_skills=level_skills,
            task=task,
            teaching_block=teaching_block,
        )
    return _open_activity(
        level_id=level_id,
        phase=phase,
        index=index,
        level_skills=level_skills,
        task=task,
        teaching_block=teaching_block,
    )


def _worked_example(task: dict[str, Any]) -> str:
    answer = task.get("correct") or task["model_answer"]
    return f"Card: {task['passage']} Answer: {answer}"


def _support_teaching_block(
    *,
    support_name: str,
    remediation: str,
    worked_task: dict[str, Any],
) -> str:
    closing = {
        "bridge": "Use the new card and try the first step again.",
        "masterclass": "The new card is another case. Show every step.",
        "revision_level_1": (
            "Use the new card for another case. Try the first step, then answer."
        ),
        "revision_level_2": "Use the new card for another case. Check each clue.",
        "revision_level_3": "Use the new card for another case. Check your full answer.",
    }[support_name]
    label = {
        "bridge": "Start again",
        "masterclass": "See the whole method",
        "revision_level_1": "Practise step one",
        "revision_level_2": "Practise with two clues",
        "revision_level_3": "Practise the full method",
    }[support_name]
    return _class3_text(
        f"Worked example - {label}: {_worked_example(worked_task)} "
        f"Fix it this way: {remediation} {closing}"
    )


def _level(spec: dict[str, Any]) -> dict[str, Any]:
    level_id = spec["level_id"]
    skills = spec["skill_ids"]
    support_names = (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    worked_tasks = (
        spec["co_construct"],
        spec["guided"][0],
        spec["guided"][1],
        spec["co_construct"],
        spec["guided"][0],
    )
    support = {
        name: _activity(
            level_id=level_id,
            phase=name,
            index=index,
            level_skills=skills,
            task=spec["support"][index - 1],
            teaching_block=_support_teaching_block(
                support_name=name,
                remediation=spec["remediation"],
                worked_task=worked_tasks[index - 1],
            ),
        )
        for index, name in enumerate(support_names, start=1)
    }
    support_ids = [support[name]["activity_id"] for name in support_names]
    return {
        "level_id": level_id,
        "title": _class3_text(spec["title"]),
        "focus": _class3_text(spec["focus"]),
        "outcome": _class3_text(spec["outcome"]),
        "skill_ids": skills,
        "episode_kind": spec["episode_kind"],
        "source_anchor_ids": spec["source_anchor_ids"],
        "connect": {
            **spec["connect"],
            "teaching_block": _class3_text(spec["connect"]["teaching_block"]),
            "prompt": _class3_text(spec["connect"]["prompt"]),
        },
        "co_construct": _activity(
            level_id=level_id,
            phase="co_construct",
            index=1,
            level_skills=skills,
            task=spec["co_construct"],
        ),
        "guided_variants": [
            _activity(
                level_id=level_id,
                phase="guided",
                index=index,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(spec["guided"], start=1)
        ],
        "independent_variants": [
            _open_activity(
                level_id=level_id,
                phase="independent",
                index=index,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(spec["independent"], start=1)
        ],
        "transfer_variants": [
            _open_activity(
                level_id=level_id,
                phase="transfer",
                index=index,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(spec["transfer"], start=1)
        ],
        "review_variants": [
            _open_activity(
                level_id=level_id,
                phase="review",
                index=index,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(spec["review"], start=1)
        ],
        "misconception_clusters": [
            {
                "cluster_id": spec["cluster_id"],
                "skill_ids": skills,
                "misconception": _class3_text(spec["misconception"]),
                "remediation": _class3_text(spec["remediation"]),
                "support_check_ids": support_ids,
            }
        ],
        "support_checks": support,
    }


def _q(
    passage: str,
    correct: str,
    distractors: list[str],
    *,
    prompt: str | None = None,
    skills: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "kind": "choice",
        "passage": passage,
        "correct": correct,
        "distractors": distractors,
        "prompt": prompt,
        "skills": skills,
    }


def _r(
    passage: str,
    model_answer: str,
    slot_phrases: list[list[str]],
    *,
    prompt: str | None = None,
    skills: list[str] | None = None,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
) -> dict[str, Any]:
    return {
        "kind": "response",
        "passage": passage,
        "model_answer": model_answer,
        "slot_phrases": slot_phrases,
        "prompt": prompt,
        "skills": skills,
        "interaction_type": interaction_type,
        "min_words": min_words,
        "ordered": ordered,
    }


def _crunch(
    records: list[tuple[str, str, list[str], list[str]]],
    *,
    prompt: str,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
) -> list[dict[str, Any]]:
    """Compile five explicitly authored, outcome-specific fresh tasks."""

    if len(records) != 5:
        raise ValueError("class3_crunch_bar_requires_five_fresh_records")
    return [
        _r(
            passage,
            model_answer,
            [first_slot, second_slot],
            prompt=prompt,
            interaction_type=interaction_type,
            min_words=min_words,
            ordered=ordered,
        )
        for passage, model_answer, first_slot, second_slot in records
    ]


def _launch_depth_case(
    passage: str,
    prompt: str,
    model_answer: str,
    answer_authority: str,
    grounding_authority: str,
    *,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    ordered: bool = False,
    answer_description: str = "Answers every part of the question for this card.",
    grounding_description: str = "Uses the card detail that proves the answer.",
) -> dict[str, Any]:
    """Author one fresh certifying case with closed answer authority."""

    return _task(
        passage,
        prompt,
        model_answer,
        [
            _evidence(
                "answer",
                answer_description,
                answer_authority,
            ),
            _evidence(
                "grounding",
                grounding_description,
                grounding_authority,
            ),
        ],
        interaction_type=interaction_type,
        min_words=min_words,
        ordered=ordered,
    )


def _add_launch_depth_variants(
    levels: list[dict[str, Any]],
    cases_by_level: dict[str, list[dict[str, Any]]],
) -> None:
    """Add one transfer and two review cases without reusing support authority."""

    levels_by_id = {level["level_id"]: level for level in levels}
    if set(cases_by_level) != set(levels_by_id):
        raise ValueError("class3_launch_depth_level_map_mismatch")
    for level_id, cases in cases_by_level.items():
        if len(cases) != 3:
            raise ValueError(f"{level_id}_requires_three_launch_depth_cases")
        level = levels_by_id[level_id]
        skills = level["skill_ids"]
        level["transfer_variants"].append(
            _open_activity(
                level_id=level_id,
                phase="transfer",
                index=4,
                level_skills=skills,
                task=cases[0],
            )
        )
        for index, case in enumerate(cases[1:], start=3):
            level["review_variants"].append(
                _open_activity(
                    level_id=level_id,
                    phase="review",
                    index=index,
                    level_skills=skills,
                    task=case,
                )
            )


def _scenario_prompt(passage: str, prompt: str) -> str:
    """Keep the reusable task while activity construction adds a short clue label."""

    if not passage.strip():
        raise ValueError("class3_scenario_prompt_requires_passage_words")
    return _class3_text(prompt)


def _make_level(
    *,
    level_id: str,
    title: str,
    focus: str,
    outcome: str,
    skill_ids: list[str],
    choice_skill_ids: list[str],
    episode_kind: str,
    source_anchor_ids: list[str],
    principle: str,
    connect: dict[str, str],
    choice_prompt: str,
    response_prompt: str,
    rubric_descriptions: list[str],
    examples: list[dict[str, Any]],
    crunch_bar: list[dict[str, Any]],
    misconception: str,
    remediation: str,
) -> dict[str, Any]:
    """Assemble one level from nineteen explicitly authored task records."""

    if len(examples) != 14:
        raise ValueError(f"{level_id}_requires_fourteen_authored_examples")
    if len(crunch_bar) != 5 or any(
        example["kind"] != "response" for example in crunch_bar
    ):
        raise ValueError(f"{level_id}_requires_five_fresh_open_tasks")

    tasks: list[dict[str, Any]] = []
    for index, example in enumerate([*examples, *crunch_bar], start=1):
        prompt = example.get("prompt")
        if example["kind"] == "choice":
            scenario_prompt = _scenario_prompt(
                example["passage"],
                prompt or f"{title}: {choice_prompt}",
            )
            tasks.append(
                _choice(
                    example["passage"],
                    scenario_prompt,
                    example["correct"],
                    example["distractors"],
                    skills=example.get("skills") or choice_skill_ids,
                )
            )
            continue

        slot_phrases = example["slot_phrases"]
        if len(slot_phrases) != len(rubric_descriptions):
            raise ValueError(f"{level_id}_rubric_slot_count_mismatch_{index}")
        claim_evidence = [
            evidence
            for slot_index, (description, phrases) in enumerate(
                zip(rubric_descriptions, slot_phrases, strict=True),
                start=1,
            )
            for evidence in _required_claim_evidence(
                key_prefix=f"part_{slot_index}",
                description=description,
                raw_claims=phrases,
            )
        ]
        scenario_prompt = _scenario_prompt(
            example["passage"],
            prompt or f"{title}: {response_prompt}",
        )
        tasks.append(
            _task(
                example["passage"],
                scenario_prompt,
                example["model_answer"],
                claim_evidence,
                interaction_type=example["interaction_type"],
                min_words=example["min_words"],
                skills=example.get("skills") or skill_ids,
                ordered=example["ordered"],
            )
        )

    return _level(
        {
            "level_id": level_id,
            "title": title,
            "focus": focus,
            "outcome": outcome,
            "skill_ids": skill_ids,
            "episode_kind": episode_kind,
            "source_anchor_ids": source_anchor_ids,
            "principle": principle,
            "connect": connect,
            "co_construct": tasks[0],
            "guided": [*tasks[1:3], *tasks[14:16]],
            "independent": [*tasks[3:5], *tasks[16:18]],
            "transfer": [*tasks[5:7], tasks[18]],
            "review": tasks[7:9],
            "cluster_id": f"{level_id}-misconception",
            "misconception": misconception,
            "remediation": remediation,
            "support": tasks[9:14],
        }
    )


def _aq_pair(
    skill_id: str,
    prompt: str,
    first: tuple[str, str, list[str]],
    second: tuple[str, str, list[str]],
    *,
    second_prompt: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "choice",
        "skill_id": skill_id,
        "prompt": prompt,
        "prompts": (prompt, second_prompt or prompt),
        "forms": (first, second),
    }


def _ar_pair(
    skill_id: str,
    prompt: str,
    description: str,
    first: tuple[str, str, list[str]],
    second: tuple[str, str, list[str]],
    *,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
) -> dict[str, Any]:
    return {
        "kind": "response",
        "skill_id": skill_id,
        "prompt": prompt,
        "description": description,
        "forms": (first, second),
        "interaction_type": interaction_type,
        "min_words": min_words,
    }


def _assessment_items(
    chapter_id: str,
    pairs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if len(pairs) != 14:
        raise ValueError(f"{chapter_id}_requires_fourteen_assessment_pairs")

    items: list[dict[str, Any]] = []
    for form_index in range(2):
        for pair_index, pair in enumerate(pairs, start=1):
            item_no = form_index * 14 + pair_index
            item_id = f"{chapter_id}:assessment:{item_no:02d}"
            passage, answer, support = pair["forms"][form_index]
            if pair["kind"] == "choice":
                raw_options = [answer, *support]
                shift = item_no % len(raw_options)
                options = raw_options[shift:] + raw_options[:shift]
                items.append(
                    {
                        "kind": "selected_option",
                        "activity_id": item_id,
                        "teaching_block": (
                            "Read the new card and the question. Find the clue that "
                            "answers the question, then choose one option."
                        ),
                        "passage": passage,
                        "prompt": _class3_text(pair["prompts"][form_index]),
                        "skill_ids": [pair["skill_id"]],
                        "options": options,
                        "accepted_answers": [answer],
                    }
                )
                continue

            model_answer, evidence = _closed_open_authority(
                answer,
                _required_claim_evidence(
                    key_prefix="evidence",
                    description=pair["description"],
                    raw_claims=support,
                ),
                ordered=False,
            )
            criteria = []
            slots = []
            for suffix, criterion_description, aliases in evidence:
                criterion_id = f"{item_id}:{suffix}"
                criteria.append(
                    {
                        "id": criterion_id,
                        "description": criterion_description,
                        "required": True,
                        "min_quality": 0.7,
                    }
                )
                slots.append(
                    {
                        "id": criterion_id,
                        "description": criterion_description,
                        "any_of": aliases,
                    }
                )
            items.append(
                {
                    "kind": "open_response",
                    "activity_id": item_id,
                    "teaching_block": (
                        "Read the new card. Write a clear answer in your own words "
                        "and include every part the question asks for."
                    ),
                    "passage": passage,
                    "prompt": _class3_text(pair["prompt"]),
                    "skill_ids": [pair["skill_id"]],
                    "interaction_type": pair["interaction_type"],
                    "rubric_criteria": criteria,
                    "concept_slots": slots,
                    "forbidden_phrases": [
                        "The reference card can be ignored",
                        "I copied a hidden answer",
                    ],
                    "min_response_words": pair["min_words"],
                    "relevance_terms": _relevance_terms(evidence),
                    "model_answer": model_answer,
                    "pass_score": 0.8,
                }
            )
    return items


def _build_manifest(
    *,
    chapter_id: str,
    chapter_no: int,
    title: str,
    unit_title: str,
    source_url: str,
    page_extract: str,
    source_anchors: list[dict[str, Any]],
    levels: list[dict[str, Any]],
    assessment_pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    assessment_items = _assessment_items(chapter_id, assessment_pairs)
    taught_skills = {
        skill_id for level in levels for skill_id in level["skill_ids"]
    }
    assessed_skills = {
        skill_id for item in assessment_items for skill_id in item["skill_ids"]
    }
    if taught_skills != assessed_skills:
        raise ValueError(f"{chapter_id}_teaching_assessment_skill_drift")

    strands = []
    for level in levels:
        level_skills = set(level["skill_ids"])
        matching_items = [
            item
            for item in assessment_items
            if set(item["skill_ids"]).issubset(level_skills)
        ]
        forms = sorted(
            {
                "selected_option"
                if item["kind"] == "selected_option"
                else "constructed_response"
                for item in matching_items
            }
        )
        strands.append(
            {
                "strand_id": f"{level['level_id']}-assessment",
                "skill_ids": level["skill_ids"],
                "minimum_items": len(matching_items),
                "evidence_forms": forms,
                "remediation_level_ids": [level["level_id"]],
            }
        )

    return {
        "schema_version": "school-class5-deep-manifest-v1",
        "chapter": {
            "chapter_id": chapter_id,
            "chapter_no": chapter_no,
            "title": title,
            "book_title": "Santoor",
            "unit_title": unit_title,
            "source_url": source_url,
            "source_note": (
                "NCERT structural alignment only. Every teaching passage, "
                "question, option, rubric, and answer is original Zidd content."
            ),
            "content_version": "2026-07-15.2",
            "certification_version": "2026-07-15.2",
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": (
                    f"{page_extract} structural section and exercise review; "
                    "no textbook prose retained"
                ),
            },
        },
        "source_anchors": source_anchors,
        "levels": levels,
        "chapter_assessment": {
            "items_per_attempt": 14,
            "pass_score": 0.8,
            "max_attempts": 2,
            "bank_item_count": 28,
            "items": assessment_items,
            "strands": strands,
        },
    }


SOURCE_ANCHORS = [
    {
        "anchor_id": f"{CHAPTER_ID}:picture:1-3",
        "section_label": "Picture Reading: Friendship and a Shared Crossing",
        "page_start": 1,
        "page_end": 3,
        "source_url": f"{SOURCE_URL}#page=1",
        "coverage_treatment": "textbook_companion",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:recite:4",
        "section_label": "Let us Recite text used for poetry reading: Colours and Sharing",
        "page_start": 4,
        "page_end": 4,
        "source_url": f"{SOURCE_URL}#page=4",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:think:5",
        "section_label": "Let us Think: Meaning, Reasons, and Colour Choices",
        "page_start": 5,
        "page_end": 5,
        "source_url": f"{SOURCE_URL}#page=5",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:speak:6-7",
        "section_label": "Let us Speak: Sound Clusters and Oral Colour Game",
        "page_start": 6,
        "page_end": 7,
        "source_url": f"{SOURCE_URL}#page=6",
        "coverage_treatment": "offline_group_activity",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:learn-actions:7-8",
        "section_label": "Let us Learn: Action Words in Complete Sentences",
        "page_start": 7,
        "page_end": 8,
        "source_url": f"{SOURCE_URL}#page=7",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:learn-letters:8-12",
        "section_label": "Let us Learn: Letter Patterns and Word Recognition",
        "page_start": 8,
        "page_end": 12,
        "source_url": f"{SOURCE_URL}#page=8",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:arrange:13",
        "section_label": "Let us Arrange: Alphabetical and Sentence Order",
        "page_start": 13,
        "page_end": 13,
        "source_url": f"{SOURCE_URL}#page=13",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:do:14",
        "section_label": "Let us Do: Friend Words and Compound Meanings",
        "page_start": 14,
        "page_end": 14,
        "source_url": f"{SOURCE_URL}#page=14",
        "coverage_treatment": "textbook_companion",
        "required_for_chapter_certification": False,
    },
]


CRUNCH_BAR = {
    "colours_context_and_idea": _crunch(
        [
            (
                "A lime border glowed around the bus-stop chart during grey fog, so waiting families could still read the route names.",
                "Lime means a bright yellow-green shade. The bright border helped families read routes in fog.",
                ["bright yellow-green shade", "sharp green-yellow colour"],
                ["families read routes in fog", "border kept route names clear"],
            ),
            (
                "An old blue shelf tab had become pale and hard to see. Replacing it with an orange tab helped pupils sort atlases quickly.",
                "Pale means weak in colour. A clear orange tab made atlas sorting quicker.",
                ["weak in colour", "colour was no longer strong"],
                ["orange tab made sorting quicker", "clear tab helped sort atlases"],
            ),
            (
                "The garden group wrote seed names on maroon cards. The dark red cards stood out against fresh green leaves.",
                "Maroon is a dark red colour. Its contrast with green leaves kept the seed names easy to find.",
                ["dark red colour", "deep red shade"],
                ["seed names easy to find", "contrast helped gardeners find labels"],
            ),
            (
                "A silver stripe on the rain barrel reflected a torch at dusk. The caretaker found the barrel without stepping into the wet beds.",
                "Silver means a shiny grey colour. The reflecting stripe helped the caretaker find the barrel safely at dusk.",
                ["shiny grey colour", "bright metal-like shade"],
                ["find the barrel safely", "reflecting stripe showed the barrel"],
            ),
            (
                "The theatre chart used teal for front rows and cream for back rows. Children matched their ticket colour to the correct entrance.",
                "Teal is a blue-green colour. The two colours guided children to the right rows and entrances.",
                ["blue-green colour", "greenish blue shade"],
                ["guided children to the right rows", "ticket colours showed each entrance"],
            ),
        ],
        prompt="Explain the colour word from the card and tell the main idea.",
    ),
    "sharing_inference_and_reason": _crunch(
        [
            (
                "Two groups need the only pair of long rulers. One group needs it for two lines now; the other needs it for a chart after ten minutes.",
                "Let the first group draw its two lines, then pass the rulers to the chart group because the needs happen at different times.",
                ["draw two lines then pass the rulers", "take turns with the rulers"],
                ["needs happen at different times", "chart group needs them later"],
            ),
            (
                "Meera has filled her water cup. Arif's cup is empty, and the shared jug is too heavy for him to lift alone.",
                "Meera should help pour water for Arif because her cup is full and he cannot lift the heavy jug safely alone.",
                ["help pour water for Arif", "steady the jug for Arif"],
                ["cannot lift the heavy jug alone", "his cup is empty"],
            ),
            (
                "Three pupils reach one dry umbrella stand during sudden rain. One pupil has a large umbrella, while two have none.",
                "The pupil with the large umbrella should walk with the other two because sharing its cover keeps all three drier.",
                ["walk under the large umbrella together", "share the umbrella cover"],
                ["two pupils have none", "keeps all three drier"],
            ),
            (
                "A paint table has one clean blue tray and two children need blue next. One child needs three drops; the other needs a full brush load.",
                "Give three drops first, then pass the tray for the larger amount because the small need can finish without delaying the longer turn.",
                ["give three drops first", "pass the tray for the larger amount"],
                ["small need finishes quickly", "longer turn follows"],
            ),
            (
                "Ninety seed packets must be counted. Rohan has counted thirty, while two classmates are still sorting the rest into piles.",
                "Rohan should join the sorting after checking his thirty because sharing the remaining work will finish the count sooner.",
                ["join the sorting", "help with the remaining packets"],
                ["finish the count sooner", "classmates are still sorting"],
            ),
        ],
        prompt="Choose a fair action and give a reason from the card.",
    ),
    "action_words_complete_sentences": _crunch(
        [
            (
                "Word card: patient / courier / balances / parcel. Place card: at the gate.",
                "The patient courier balances the parcel at the gate. Courier and parcel are nouns, balances is the verb, and patient is a describing word.",
                ["courier and parcel are nouns", "balances is the verb"],
                ["patient courier balances the parcel", "at the gate"],
            ),
            (
                "Word card: tiny / crab / crawls / rock. Place card: beside the pool.",
                "A tiny crab crawls over the rock beside the pool. Crab and rock are nouns, crawls is the verb, and tiny describes the crab.",
                ["crab and rock are nouns", "crawls is the verb"],
                ["tiny crab crawls over the rock", "beside the pool"],
            ),
            (
                "Word card: careful / nurse / carries / bottle. Time card: after lunch.",
                "The careful nurse carries the bottle after lunch. Nurse and bottle are nouns, carries is the verb, and careful describes the nurse.",
                ["nurse and bottle are nouns", "carries is the verb"],
                ["careful nurse carries the bottle", "after lunch"],
            ),
            (
                "Word card: striped / kite / rises / field. Place card: above the field.",
                "The striped kite rises above the field. Kite and field are nouns, rises is the verb, and striped describes the kite.",
                ["kite and field are nouns", "rises is the verb"],
                ["striped kite rises", "above the field"],
            ),
            (
                "Word card: wooden / cart / carries / pumpkins. Place card: through the market.",
                "The wooden cart carries pumpkins through the market. Cart and pumpkins are nouns, carries is the verb, and wooden describes the cart.",
                ["cart and pumpkins are nouns", "carries is the verb"],
                ["wooden cart carries pumpkins", "through the market"],
            ),
        ],
        prompt="Make the full sentence, then name the nouns, verb, and describing word.",
    ),
    "events_and_sentence_order": _crunch(
        [
            (
                "Events: the class folded paper boats; it tested them in a tub; it dried the strongest boat. Parts: after the test / the class / dried / the strongest boat.",
                "The class folded boats first, tested them next, and dried the strongest boat last. After the test, the class dried the strongest boat.",
                ["folded first", "tested next", "dried last"],
                ["after the test the class dried", "the strongest boat"],
            ),
            (
                "Events: Uma labelled three jars; she filled them with buttons; she placed them on the craft shelf. Parts: on the craft shelf / Uma / placed / the filled jars.",
                "Uma labelled the jars first, filled them second, and shelved them last. Uma placed the filled jars on the craft shelf.",
                ["labelled first", "filled second", "shelved last"],
                ["Uma placed the filled jars", "on the craft shelf"],
            ),
            (
                "Events: the cook washed mint; he chopped it; he mixed it into curd. Parts: before serving / the cook / mixed / mint / into the curd.",
                "The cook washed mint first, chopped it next, and mixed it last. Before serving, the cook mixed mint into the curd.",
                ["washed first", "chopped next", "mixed last"],
                ["before serving the cook mixed", "mint into the curd"],
            ),
            (
                "Events: Jatin checked the tyre; he pumped in air; he rode slowly around the yard. Parts: around the yard / Jatin / rode / slowly / after pumping air.",
                "Jatin checked the tyre first, pumped air next, and rode last. Jatin rode slowly around the yard after pumping air.",
                ["checked first", "pumped next", "rode last"],
                ["Jatin rode slowly", "around the yard after pumping air"],
            ),
            (
                "Events: the team counted saplings; it dug six holes; it planted one sapling in each hole. Parts: in six holes / the team / planted / the saplings / this morning.",
                "The team counted first, dug holes next, and planted last. The team planted the saplings in six holes this morning.",
                ["counted first", "dug next", "planted last"],
                ["team planted the saplings", "in six holes this morning"],
            ),
        ],
        prompt="Put the events in order and build the sentence from every part.",
        interaction_type="short_text",
        ordered=True,
    ),
    "spelling_and_compound_words": _crunch(
        [
            (
                "Letter tiles: b, a, s, k, e, t. Compound parts: rain + coat.",
                "The tiles spell basket. Raincoat joins rain and coat to name clothing that keeps rain off.",
                ["tiles spell basket", "basket uses every tile"],
                ["rain and coat", "clothing that keeps rain off"],
            ),
            (
                "Letter tiles: p, u, r, p, l, e. Compound parts: sun + light.",
                "The tiles spell purple. Sunlight joins sun and light to name light that comes from the sun.",
                ["tiles spell purple", "purple uses both p tiles"],
                ["sun and light", "light from the sun"],
            ),
            (
                "Letter tiles: f, r, i, e, n, d. Compound parts: class + room.",
                "The tiles spell friend. Classroom joins class and room to name a room where a class learns.",
                ["tiles spell friend", "friend ends with nd"],
                ["class and room", "room where a class learns"],
            ),
            (
                "Letter tiles: o, r, a, n, g, e. Compound parts: door + bell.",
                "The tiles spell orange. Doorbell joins door and bell to name a bell used at a door.",
                ["tiles spell orange", "orange begins with or"],
                ["door and bell", "bell used at a door"],
            ),
            (
                "Letter tiles: y, e, l, l, o, w. Compound parts: book + shelf.",
                "The tiles spell yellow. Bookshelf joins book and shelf to name a shelf that holds books.",
                ["tiles spell yellow", "yellow has two l letters"],
                ["book and shelf", "shelf that holds books"],
            ),
        ],
        prompt="Spell the tile word, split the compound, and explain its meaning.",
        interaction_type="short_text",
    ),
    "poetic_pattern_and_short_answer": _crunch(
        [
            (
                "Blue on the bucket, blue on the gate; blue marks the place where helpers wait.",
                "Repeating blue links the two places and makes the waiting point easy to remember.",
                ["repeating blue links the places", "blue appears three times"],
                ["waiting point easy to remember", "pattern points to the helper place"],
            ),
            (
                "Pass it gently, pass it slow; pass the chalk so all can show.",
                "Repeating pass it gives a steady beat and stresses that everyone gets a turn.",
                ["repeating pass it gives a beat", "pass it starts each part"],
                ["everyone gets a turn", "sharing is the main idea"],
            ),
            (
                "Red sign shining, red sign bright; red sign guides us in the night.",
                "The repeated red sign makes the guide easy to picture and shows that colour supports safe travel at night.",
                ["repeated red sign", "red sign appears in each part"],
                ["supports safe travel at night", "guide is easy to picture"],
            ),
            (
                "Together we sort, together we stack; together we put every storybook back.",
                "Repeating together creates a team rhythm and shows that shared work returns the books.",
                ["repeating together creates rhythm", "together begins each action"],
                ["shared work returns the books", "teamwork is the main idea"],
            ),
            (
                "Gold in the morning, silver at noon; colours keep changing under the moon.",
                "The changing colour images move through the day and show that light can make one place look different.",
                ["colour images move through the day", "gold silver and moonlight"],
                ["light changes how the place looks", "one place looks different"],
            ),
        ],
        prompt="Name the word or image pattern and explain what it helps us understand.",
        interaction_type="short_text",
    ),
}


LEVELS = [
    _make_level(
        level_id="colours_context_and_idea",
        title="Read colour clues and the whole idea",
        focus="infer colour vocabulary in context and state a passage main idea",
        outcome="Use nearby clues to explain a colour word, then combine the important details into one accurate main-idea sentence.",
        skill_ids=[
            "reading.word_meaning_context",
            "reading.paragraph_main_idea",
        ],
        choice_skill_ids=["reading.word_meaning_context"],
        episode_kind="comprehension_studio",
        source_anchor_ids=[
            f"{CHAPTER_ID}:think:5",
            f"{CHAPTER_ID}:learn-letters:8-12",
        ],
        principle="Use the words around an unfamiliar colour description, then ask what change or message connects the whole card.",
        connect={
            "teaching_block": "Colour words can describe more than a name. A nearby object, brightness clue, or change can reveal meaning, while the full group of details reveals the main idea.",
            "passage": "Grey clouds covered the lane, but a bright saffron flag made the doorway easy to notice. The colour clue and the contrast guide two different kinds of reading.",
            "prompt": "Notice the nearby clue for saffron and the larger contrast between the dull lane and the visible doorway.",
        },
        choice_prompt="Which meaning is supported by the nearby colour clue?",
        response_prompt="explain the colour expression and state the central idea using the visible evidence.",
        rubric_descriptions=[
            "Explains the target colour expression from a specific nearby clue.",
            "States the whole-card idea without listing unrelated details.",
        ],
        crunch_bar=CRUNCH_BAR["colours_context_and_idea"],
        examples=[
            _q("The pale blue ribbon looked almost white beside the deep blue cloth.", "very light in colour", ["rough to touch", "full of holes", "moving quickly"]),
            _q("The crimson kite matched the ripe red berries painted on its tail.", "a strong red colour", ["a soft green colour", "a pale grey colour", "a bright yellow colour"]),
            _r("A dull courtyard became lively when children hung orange, green, and white streamers above the gate. Neighbours stopped to admire the cheerful entrance.", "The colour display transformed a dull courtyard into a cheerful entrance that drew the neighbours' attention.", [["colour display transformed", "streamers changed the courtyard"], ["cheerful entrance", "neighbours' attention"]]),
            _r("At dawn, the lake looked silver because it reflected the first weak light. As the sun rose, the surface became golden and the rowers began their trip.", "Silver means softly shining like reflected metal; the passage mainly shows morning light changing the lake as the rowers set out.", [["softly shining", "reflected first light"], ["morning light changing the lake", "rowers set out"]]),
            _r("Nila used one bright yellow card among six brown cards. The yellow card marked the library book that needed repair, so the helper found it at once.", "Bright yellow means easy to notice, and the main idea is that a contrasting colour helped the helper locate the damaged book.", [["easy to notice", "contrasting yellow"], ["helped locate the damaged book", "found it at once"]]),
            _r("A football team wore navy shirts, a very dark shade of blue. The dark shirts made the white numbers clear enough for the scorekeeper to read.", "Navy means very dark blue, and the passage explains how colour contrast made the players' numbers readable.", [["very dark blue", "dark shade of blue"], ["contrast made numbers readable", "white numbers clear"]]),
            _r("The clay pot looked earthy, with a brown colour like dry soil. A child chose it for a seedling because its natural shade suited the garden shelf.", "Earthy describes the soil-like brown shade, and the central idea is that the pot's natural colour suited a garden display.", [["soil-like brown", "like dry soil"], ["natural colour suited the garden", "chosen for the garden shelf"]]),
            _r("A faded poster had lost most of its strong colours after months in sunlight. The art club replaced it with a clear new sign that visitors could read from the path.", "Faded means the colours had become weak, and the passage is mainly about replacing an unclear old poster with a readable sign.", [["colours became weak", "lost strong colours"], ["replacing an unclear poster", "readable new sign"]]),
            _r("Violet paint covered one small corner of the class chart. That purple-blue corner identified the box for storybooks while other colours marked science and art.", "Violet is the purple-blue colour, and the main idea is that colour coding helped organise books by subject.", [["purple-blue colour", "violet corner"], ["colour coding organised books", "marked subjects"]]),
            _q("The amber lamp gave a warm yellow-orange glow beside the bed.", "a warm yellow-orange colour", ["a cold blue shade", "a black shadow", "a colourless surface"]),
            _r("The path markers were fluorescent, so their unusually bright green colour remained visible in the evening. Walkers followed them safely to the hall.", "Fluorescent means unusually bright and easy to see; the card mainly shows bright markers guiding walkers safely in low light.", [["unusually bright", "easy to see"], ["markers guided walkers safely", "visible in evening"]]),
            _q("The charcoal wall was nearly black, much darker than the grey floor.", "nearly black", ["bright pink", "light blue", "shining white"]),
            _r("A pastel banner used soft pink, green, and blue rather than strong colours. Its gentle shades made a calm background for the reading corner.", "Pastel means soft and light in colour, and the passage explains how gentle shades created a calm reading space.", [["soft and light", "gentle shades"], ["created a calm reading space", "background for reading corner"]]),
            _r("The safety box was scarlet, a vivid red that stood out against the cream wall. Staff could point visitors toward it quickly during a drill.", "Scarlet means vivid red, and the central idea is that a strongly contrasting colour made the safety box easy to locate.", [["vivid red", "strong red"], ["made safety box easy to locate", "stood out against wall"]]),
        ],
        misconception="The learner guesses a colour from memory without using the sentence clue, or reports one object instead of the idea connecting the whole passage.",
        remediation="Find the phrase that explains or contrasts the colour, state the result or purpose, and join both ideas in one clue-based main-idea sentence.",
    ),
    _make_level(
        level_id="sharing_inference_and_reason",
        title="Infer a fair sharing choice",
        focus="infer motives from visible evidence and write a supported reason answer",
        outcome="Identify what a character is likely trying to achieve and justify a fair action with a because-clause grounded in the supplied facts.",
        skill_ids=["reading.inference_reason", "writing.reason_answer"],
        choice_skill_ids=["reading.inference_reason"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:think:5"],
        principle="An idea worked out from clues must fit every visible clue, and a fair recommendation must name both the action and the reason it helps the group.",
        connect={
            "teaching_block": "Stories often leave a motive unstated. We can infer it from actions, then propose a fair response by linking the action to its likely effect.",
            "passage": "Ira moved her unused green pencil toward Dev, who had stopped drawing because his pencil had broken. Dev smiled and continued the group poster.",
            "prompt": "Connect Ira's action, Dev's problem, and the result before deciding why she moved the pencil.",
        },
        choice_prompt="Which idea fits every visible clue?",
        response_prompt="state the fair action and justify it with the strongest clue and result.",
        rubric_descriptions=[
            "States a fair or helpful action that fits the situation.",
            "Uses a visible clue to explain why that action is reasonable.",
        ],
        crunch_bar=CRUNCH_BAR["sharing_inference_and_reason"],
        examples=[
            _q("Tara split six sketch pens into two groups of three before inviting Noman to colour beside her.", "She wanted both children to have pens to use.", ["She wanted to hide every pen.", "She had finished the picture alone.", "She planned to throw the pens away."]),
            _q("Ravi kept the only sharpener in the centre of the table and told each partner to return it after one pencil.", "He wanted everyone to take a fair turn.", ["He wanted no one to sharpen a pencil.", "He forgot where the sharpener was.", "He wanted to keep it in his bag."]),
            _r("Two teams need the same blue chart paper. Team A needs half for a title; Team B needs half for a map. The sheet is large enough for both tasks.", "The teams should measure and divide the sheet equally because each task needs only half and both can then finish.", [["measure and divide equally", "split the sheet in half"], ["each needs only half", "both can finish"]]),
            _r("Maya has four crayons and Ali has none after his box spills into water. The class activity needs only two colours per person.", "Maya should lend Ali two crayons because she will still have two for her own work and Ali can join the activity.", [["lend Ali two crayons", "share two crayons"], ["still has two", "Ali can join"]]),
            _r("A younger child waits beside a high shelf for the red paint. Leela can reach it, and the teacher has said pupils may pass closed paint pots to one another.", "Leela should hand down the closed red pot because she can reach it safely and the teacher has allowed that kind of help.", [["hand down the closed pot", "help reach the paint"], ["can reach safely", "teacher allowed it"]]),
            _r("At a picnic, one group has eight paper cups for six people. A late visitor arrives without a cup, while two cups remain unused.", "The group should offer one spare cup to the visitor because two cups are unused and sharing one leaves enough for everyone.", [["offer one spare cup", "share an unused cup"], ["two are unused", "enough for everyone"]]),
            _r("Neer has finished outlining the class banner. Sumi is still waiting for the black marker, and Neer is holding it while talking.", "Neer should pass the marker to Sumi because his outlining is complete and she needs it to continue the shared banner.", [["pass the marker to Sumi", "give Sumi the marker"], ["outlining is complete", "she needs it to continue"]]),
            _r("Only one magnifying glass is available. Three pupils each need thirty seconds to inspect a leaf, and the timer is ready.", "They should use a timed turn for each pupil because equal thirty-second turns let everyone inspect the leaf.", [["timed turn for each pupil", "take equal turns"], ["thirty-second turns", "everyone can inspect"]]),
            _r("Asha brings a box of twelve chalk pieces for a four-person pavement game. Each player needs three pieces to mark a route.", "Asha should give three chalk pieces to each player because twelve pieces divide evenly among four people.", [["three pieces to each", "divide evenly"], ["twelve among four", "each player needs three"]]),
            _q("Kabir notices that his partner keeps rubbing cold hands and slides the spare pair of gloves across the bench.", "Kabir thinks the gloves may warm his partner's hands.", ["Kabir wants the gloves to stay unused.", "Kabir thinks the bench is broken.", "Kabir has forgotten his partner is present."]),
            _r("During clean-up, Pia has stacked all the books while her partner still has many colour cards scattered on the floor.", "Pia should help gather the colour cards because her own task is finished and shared clean-up will end sooner.", [["help gather the cards", "join the clean-up"], ["own task is finished", "clean-up ends sooner"]]),
            _q("The group places the glue beside the middle of the collage instead of next to one person's chair.", "They want every member to reach the shared glue.", ["They want the glue to dry unopened.", "They have decided not to make a collage.", "They want one person to block it."]),
            _r("A new pupil cannot find the art room. Omi knows the route and has five minutes before his own club begins.", "Omi should walk with the new pupil to the art room because he knows the route and has enough time to guide them.", [["walk with the new pupil", "guide them to art room"], ["knows the route", "has five minutes"]]),
            _r("Two friends both want the purple ribbon for separate bookmarks. The ribbon is forty centimetres long, and each bookmark needs twenty centimetres.", "They should measure and cut two equal twenty-centimetre pieces because the ribbon is exactly long enough for both bookmarks.", [["cut two equal pieces", "twenty centimetres each"], ["exactly long enough", "both bookmarks"]]),
        ],
        misconception="The learner invents a motive that conflicts with the actions, or names a kind act without explaining how the supplied facts make it fair or useful.",
        remediation="Name the clue and the motive it suggests, then write the fair action after 'should' with a because-clause using a quantity, permission, need, or result from the card.",
    ),
    _make_level(
        level_id="action_words_complete_sentences",
        title="Build complete action sentences",
        focus="distinguish naming, action, and describing words and construct complete sentences",
        outcome="Identify a word's job in a sentence and write a complete subject-action-detail sentence with correct meaning and capitalization.",
        skill_ids=["grammar.noun_verb_adjective", "writing.complete_sentence"],
        choice_skill_ids=["grammar.noun_verb_adjective"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:learn-actions:7-8"],
        principle="A naming word tells who or what, an action word tells what happens, and a describing word adds a useful quality; a complete sentence needs a clear doer and action.",
        connect={
            "teaching_block": "The same topic can contain different word jobs. Finding the doer and action first helps us classify words and avoid sentence fragments.",
            "passage": "The careful painter mixes bright colours. Painter names the doer, mixes names the action, and careful and bright describe nouns.",
            "prompt": "Locate the doer and action before noticing the two describing words.",
        },
        choice_prompt="Which word performs the named grammar job?",
        response_prompt="classify the target words and write the requested complete action sentence.",
        rubric_descriptions=[
            "Correctly identifies or uses the required naming, action, or describing word.",
            "Produces a complete sentence with a clear doer, action, and relevant detail.",
        ],
        crunch_bar=CRUNCH_BAR["action_words_complete_sentences"],
        examples=[
            _q("The cheerful child opens the paint box.", "opens", ["cheerful", "child", "paint"]),
            _q("A tiny brush rests beside the jar.", "tiny", ["brush", "rests", "jar"]),
            _r("Word card: birds / carry / thin / twigs / to the nest.", "Thin birds is incorrect for this meaning; a complete sentence is: The birds carry thin twigs to the nest.", [["thin describes twigs", "describing word beside twigs"], ["The birds carry", "to the nest"]]),
            _r("Scene card: Mina; carefully folds; a square paper; at the desk.", "Mina carefully folds a square paper at the desk. Mina is the naming word for the doer, and folds is the action word.", [["Mina is the doer", "folds is the action"], ["Mina carefully folds", "at the desk"]]),
            _r("Fragment: The playful puppies. Action detail: chase a yellow ball across the yard.", "The playful puppies chase a yellow ball across the yard. Puppies names the doers, chase shows the action, and playful and yellow describe nouns.", [["puppies names doers", "chase shows action"], ["The playful puppies chase", "across the yard"]]),
            _r("Facts: one patient student; waits; beside the busy paint table.", "One patient student waits beside the busy paint table. Student is a naming word, waits is an action word, and patient and busy are describing words.", [["student names", "waits is action"], ["patient student waits", "busy paint table"]]),
            _r("Words: smooth / stone / rolls / down / the short slope.", "The smooth stone rolls down the short slope. Stone names the object, rolls shows its action, and smooth and short describe nouns.", [["stone names object", "rolls shows action"], ["smooth stone rolls", "short slope"]]),
            _r("Draft: Bright. Add the doer 'the lantern', the action 'glows', and the place 'near the door'.", "The bright lantern glows near the door. Lantern is the naming word, glows is the action word, and bright describes the lantern.", [["lantern naming word", "glows action word"], ["The bright lantern glows", "near the door"]]),
            _r("Sentence: The quick runner carries a blue flag. Replace the action with 'waves' and keep a complete sensible sentence.", "The quick runner waves a blue flag. Runner names the doer, waves is the new action, and quick and blue are describing words.", [["runner names doer", "waves is action"], ["quick runner waves", "blue flag"]]),
            _q("In 'The red cart moves slowly,' which word names the object?", "cart", ["red", "moves", "slowly"]),
            _r("Fragment: jumps over the low rope. Supplied doer: The tall athlete.", "The tall athlete jumps over the low rope. Athlete names the doer, jumps gives the action, and tall and low describe nouns.", [["athlete names doer", "jumps gives action"], ["The tall athlete jumps", "over the low rope"]]),
            _q("The soft blanket covers the sleeping child. Which word describes blanket?", "soft", ["blanket", "covers", "child"]),
            _r("Facts: a noisy bell; rings; before the morning class.", "A noisy bell rings before the morning class. Bell is a naming word, rings is an action word, and noisy and morning describe nouns.", [["bell naming word", "rings action word"], ["A noisy bell rings", "before the morning class"]]),
            _r("Draft: The green. Repair it with the supplied noun 'parrot' and action detail 'pecks a ripe guava'.", "The green parrot pecks a ripe guava. Parrot and guava are naming words, pecks is the action, and green and ripe describe them.", [["parrot and guava naming words", "pecks action"], ["green parrot pecks", "ripe guava"]]),
        ],
        misconception="The learner labels a word from its position rather than its job, or writes a fragment that lacks either a named doer or a meaningful action.",
        remediation="Find the doer, action, and useful describing words, then check that the sentence tells one complete event.",
    ),
    _make_level(
        level_id="events_and_sentence_order",
        title="Order events and sentence parts",
        focus="track a short event sequence and arrange sentence parts in natural order",
        outcome="Reconstruct first-next-final events from a visible card and form a natural sentence with subject, action, object, place, and time.",
        skill_ids=["reading.event_sequence", "grammar.sentence_order"],
        choice_skill_ids=["reading.event_sequence"],
        episode_kind="retrieval_challenge",
        source_anchor_ids=[
            f"{CHAPTER_ID}:arrange:13",
        ],
        principle="Time clues control event order, while a clear sentence usually places the doer before the action and keeps place or time details where they read naturally.",
        connect={
            "teaching_block": "A sequence can be checked with first, next, and finally. After ordering the ideas, arrange each sentence so the reader immediately knows who did what.",
            "passage": "First, the class sorted the colour cards. Next, they tied the cards into sets. Finally, they placed each set in a labelled tray.",
            "prompt": "Trace the three time markers and notice that every sentence begins with the doer before the action.",
        },
        choice_prompt="Which event or sentence position follows the visible order?",
        response_prompt="reconstruct the sequence and write the supplied sentence parts in natural order.",
        rubric_descriptions=[
            "Places the supplied events in the correct first-to-final sequence.",
            "Builds a natural complete sentence from all required parts.",
        ],
        crunch_bar=CRUNCH_BAR["events_and_sentence_order"],
        examples=[
            _q("Mira sharpened the pencils, placed them in cups, and then carried the cups to each table.", "She carried the cups to each table.", ["She sharpened the pencils.", "She placed pencils in cups.", "She opened a paint bottle."], prompt="What did Mira do last?"),
            _q("Before lunch, Dev washed the brushes. After lunch, he dried them near the window.", "Dev dried the brushes near the window.", ["Dev washed brushes after drying them.", "Dev ate paint before lunch.", "Dev closed the window before washing."], prompt="Which event happened second?"),
            _r("Events: rain begins; children move the poster indoors; they wipe the wet edge. Parts: the children / wiped / the poster edge / in the hall.", "Rain began first, the children moved the poster indoors next, and they wiped the wet edge last. The children wiped the poster edge in the hall.", [["rain began first", "moved poster next", "wiped last"], ["The children wiped", "in the hall"]], ordered=True),
            _r("Card: First Ria drew three circles. Then she added stems. At last she coloured the flowers. Parts: Ria / coloured / the flowers / after adding stems.", "Ria drew circles first, added stems next, and coloured the flowers last. Ria coloured the flowers after adding stems.", [["drew circles first", "added stems next", "coloured last"], ["Ria coloured the flowers", "after adding stems"]], ordered=True),
            _r("Card: Omar found a loose label, read the name, and returned the box to Tara. Parts: Omar / returned / the labelled box / to Tara.", "Omar found the label first, read the name next, and returned the box last. Omar returned the labelled box to Tara.", [["found first", "read next", "returned last"], ["Omar returned", "to Tara"]], ordered=True),
            _r("Morning task: open the curtain; compare paint in daylight; choose the matching shade. Parts: the team / chose / the matching shade / by the window.", "The team opened the curtain first, compared the paint next, and chose the shade last. The team chose the matching shade by the window.", [["opened first", "compared next", "chose last"], ["The team chose", "by the window"]], ordered=True),
            _r("Trip card: board the bus; cross the river bridge; reach the museum. Parts: our class / reached / the museum / before noon.", "Our class boarded the bus first, crossed the bridge next, and reached the museum last. Our class reached the museum before noon.", [["boarded first", "crossed next", "reached last"], ["Our class reached", "before noon"]], ordered=True),
            _r("Repair card: notice a torn corner; fetch clear tape; press the tape flat. Parts: Salim / pressed / the clear tape / over the tear.", "Salim noticed the tear first, fetched tape next, and pressed it flat last. Salim pressed the clear tape over the tear.", [["noticed first", "fetched next", "pressed last"], ["Salim pressed", "over the tear"]], ordered=True),
            _r("Plant card: fill a pot with soil; place a seed; water gently. Parts: the child / watered / the planted seed / gently.", "The child filled the pot first, placed the seed next, and watered it last. The child watered the planted seed gently.", [["filled first", "placed next", "watered last"], ["The child watered", "gently"]], ordered=True),
            _q("Asha folded the card, wrote a name, and sealed the envelope. What happened immediately before sealing?", "She wrote a name.", ["She folded after sealing.", "She mailed an empty box.", "She erased the envelope."]),
            _r("Snack card: wash the apple; slice it with an adult; place slices on a plate. Parts: the adult / placed / the apple slices / on a clean plate.", "The apple was washed first, sliced next, and placed on the plate last. The adult placed the apple slices on a clean plate.", [["washed first", "sliced next", "placed last"], ["The adult placed", "on a clean plate"]], ordered=True),
            _q("The group counted five cards, checked the numbers, and tied the set. Which action came second?", "They checked the numbers.", ["They tied the set first.", "They counted after tying.", "They painted the numbers."]),
            _r("Safety card: see spilled water; warn nearby pupils; wipe the floor. Parts: the monitor / wiped / the wet floor / with a cloth.", "The monitor saw the spill first, warned pupils next, and wiped the floor last. The monitor wiped the wet floor with a cloth.", [["saw first", "warned next", "wiped last"], ["The monitor wiped", "with a cloth"]], ordered=True),
            _r("Library card: choose a book; record its number; place it in the return basket later. Parts: Neha / recorded / the book number / at the desk.", "Neha chose the book first, recorded its number next, and returned it later. Neha recorded the book number at the desk.", [["chose first", "recorded next", "returned later"], ["Neha recorded", "at the desk"]], ordered=True),
        ],
        misconception="The learner follows the order in which answer choices are printed, or arranges sentence parts without checking who performs the action and when it occurs.",
        remediation="Use the time clues to order the events, find the doer and action, then rebuild the sentence before adding place and time details.",
    ),
    _make_level(
        level_id="spelling_and_compound_words",
        title="Build and spell useful colour words",
        focus="repair spelling from letter clues and form compounds from meaningful word parts",
        outcome="Use all supplied letters to spell a target word and explain how two base words combine to create a compound meaning.",
        skill_ids=["vocab.spelling", "vocab.word_formation"],
        choice_skill_ids=["vocab.spelling"],
        episode_kind="language_lab",
        source_anchor_ids=[
            f"{CHAPTER_ID}:learn-letters:8-12",
        ],
        principle="Spelling checks every letter in order; compound-word meaning checks how both complete base words contribute to the new idea.",
        connect={
            "teaching_block": "A letter jumble can be solved by matching every letter to a known word. A compound is different: it joins two meaningful bases and keeps a contribution from each.",
            "passage": "The letters L, B, U, E can form BLUE. The bases sun and flower form sunflower, a flower whose head often resembles a bright sun.",
            "prompt": "Check letter use in BLUE, then identify the contribution of both bases in sunflower.",
        },
        choice_prompt="Which spelling or word build uses the supplied parts correctly?",
        response_prompt="show the correct spelling or compound split and explain how the supplied parts support the meaning.",
        rubric_descriptions=[
            "Forms the target spelling or compound from all supplied parts accurately.",
            "Explains the letter check or the meaning contributed by each base word.",
        ],
        crunch_bar=CRUNCH_BAR["spelling_and_compound_words"],
        examples=[
            _q("Jumbled colour letters: N, G, E, E, R.", "GREEN", ["GREAN", "GEREN", "GRNEE"]),
            _q("The bases rain and coat name clothing worn in wet weather.", "raincoat", ["coatrain", "rainingcoat", "raincoated"]),
            _r("Jumbled letters: P, U, R, P, L, E. Meaning clue: a colour between red and blue.", "The correct spelling is PURPLE. It uses both P letters and every supplied letter once.", [["PURPLE", "correct spelling"], ["both P letters", "every supplied letter"]]),
            _r("Bases: class + room. Reference clue: a room where a class learns together.", "Classroom combines class and room and means the room used by a class for learning.", [["classroom", "class + room"], ["room used by a class", "class learns there"]]),
            _r("Jumbled letters: O, R, A, N, G, E. Check clue: the word has six letters and begins with O.", "The correct spelling is ORANGE; it begins with O and uses all six supplied letters.", [["ORANGE", "six-letter spelling"], ["begins with O", "uses all six letters"]]),
            _r("Bases: foot + print. Clue: a mark left by a foot on soft ground.", "Footprint combines foot and print and means a mark made where a foot pressed the ground.", [["footprint", "foot + print"], ["mark made by a foot", "pressed the ground"]]),
            _r("Jumbled letters: Y, E, L, L, O, W. One learner writes YELOW.", "The correct spelling is YELLOW. The draft needs a second L before O.", [["YELLOW", "correct spelling"], ["second L", "before O"]]),
            _r("Bases: note + book. Clue: bound pages used for writing notes.", "Notebook combines note and book and means a book in which a learner writes notes.", [["notebook", "note + book"], ["book for notes", "writes notes"]]),
            _r("Draft colour: B-R-O-N-W. Letter card says the last two letters should be W-N.", "The correct spelling is BROWN; the final pair is W-N, not N-W.", [["BROWN", "correct spelling"], ["final pair W-N", "not N-W"]]),
            _q("The bases basket and ball name a game played with a raised basket.", "basketball", ["ballbasket", "basketingball", "basketballed"]),
            _r("Bases: news + paper. Clue: printed sheets carrying reports and notices.", "Newspaper combines news and paper and means printed paper that carries news and notices.", [["newspaper", "news + paper"], ["paper carrying news", "reports and notices"]]),
            _q("Jumbled colour letters: K, C, A, L, B.", "BLACK", ["BLCAK", "BACKL", "BALCK"]),
            _r("Bases: earth + worm. Clue: a small soil-dwelling animal with a long soft body.", "Earthworm combines earth and worm and names a worm that lives in soil.", [["earthworm", "earth + worm"], ["worm that lives in soil", "soil-dwelling"]]),
            _r("Jumbled letters: E, W, H, I, T. Meaning clue: the lightest common colour name in the set.", "The correct spelling is WHITE; W comes first and the sequence ends with T-E.", [["WHITE", "correct spelling"], ["W comes first", "ends with T-E"]]),
        ],
        misconception="The learner accepts a familiar-looking spelling without checking every letter, or joins two words while explaining only one base word's contribution.",
        remediation="Check each supplied letter once. For a compound, separate the two base words and explain what each one adds to the meaning.",
    ),
    _make_level(
        level_id="poetic_pattern_and_short_answer",
        title="Notice poetic patterns and answer precisely",
        focus="interpret repetition and colour imagery and write concise supported answers",
        outcome="Explain how a repeated word or colour image shapes a short poem and answer a focused question in one or two clear sentences using poem clues.",
        skill_ids=["reading.poetic_language", "writing.short_answer"],
        choice_skill_ids=["reading.poetic_language"],
        episode_kind="expression_workshop",
        source_anchor_ids=[
            f"{CHAPTER_ID}:recite:4",
        ],
        principle="Poetic repetition creates emphasis or rhythm, while a strong short answer names the pattern and explains its effect with a clear clue.",
        connect={
            "teaching_block": "A poem may repeat a colour, action, or sentence shape so the reader notices a feeling or shared idea. A short answer should explain the effect instead of copying the line.",
            "passage": "Blue on the gate, blue on the wall, blue paper stars brighten the hall. Repeating blue keeps attention on the colour spreading through the scene.",
            "prompt": "Notice what the repeated colour connects and how the final action changes the mood.",
        },
        choice_prompt="Which explanation best describes the poetic pattern?",
        response_prompt="identify the pattern and give a concise explanation of its effect using the supplied lines.",
        rubric_descriptions=[
            "Identifies the relevant repeated word, sound, comparison, or colour image.",
            "Explains the pattern's effect in a short answer supported by a poem clue.",
        ],
        crunch_bar=CRUNCH_BAR["poetic_pattern_and_short_answer"],
        examples=[
            _q("Red on the drum, red on the kite, red makes the fair look warm and bright.", "Repeating red links several fair objects into one bright scene.", ["Red proves every object is identical.", "The lines describe only the sound of a drum.", "Repeating red makes the fair disappear."]),
            _q("Share one brush, share one tray, share the colours through the day.", "Repeating share emphasises working together.", ["Repeating share shows everyone worked alone.", "The line says the tray is broken.", "The poem warns readers never to use colour."]),
            _r("Green climbs the fence, green shades the seat, green leaves cool the dusty street.", "The repeated word green connects plants across the scene and emphasises how their colour brings shade and coolness.", [["repeated word green", "green connects plants"], ["brings shade and coolness", "cools the street"]], interaction_type="short_text"),
            _r("Yellow wakes the window, yellow warms the floor; morning lays a golden path beside the door.", "Yellow is repeated and compared with warmth, making the morning light feel welcoming as it enters the room.", [["yellow repeated", "golden path"], ["morning feels welcoming", "light warms the room"]], interaction_type="short_text"),
            _r("One crayon for Tara, one crayon for Lee; two different pictures, one shared box for three.", "Repeating one highlights fair turns, while the shared box image shows that separate pictures can come from common materials.", [["repeating one", "fair turns"], ["shared box", "common materials"]], interaction_type="short_text"),
            _r("Black is the road and silver the rain; bright are the windows that guide us again.", "The dark road and silver rain create a dim scene, while the bright windows become a hopeful guide through it.", [["dark road and silver rain", "colour contrast"], ["bright windows guide", "hopeful guide"]], interaction_type="short_text"),
            _r("Pass the paper, pass the glue, pass a kind idea or two.", "Repeating pass creates a steady rhythm and emphasises that both materials and helpful ideas can be shared.", [["repeating pass", "steady rhythm"], ["materials and ideas shared", "helpful ideas"]], interaction_type="short_text"),
            _r("Purple at sunset, purple on the hill; slowly the market grows quiet and still.", "Purple links the evening sky and hill, while quiet and still show the market settling as daylight fades.", [["purple links sky and hill", "evening colour"], ["market settling", "quiet and still"]], interaction_type="short_text"),
            _r("Mix a little red, mix a little blue; watch a different colour come into view.", "Repeating mix focuses on the action, and the final line creates anticipation for the new colour made from red and blue.", [["repeating mix", "focuses on action"], ["anticipation for new colour", "red and blue combine"]], interaction_type="short_text"),
            _q("Bright on the banner, bright in each eye, bright is the cheer as the team marches by.", "Repeating bright connects the banner, faces, and cheerful mood.", ["Bright means the march happens at night.", "The team hides the banner from view.", "Each line describes a different silent room."]),
            _r("Round goes the brush, round goes the sun; round little patterns appear one by one.", "Repeating round connects the brush movement, sun shape, and growing pattern while giving the lines a turning rhythm.", [["repeating round", "connects shapes"], ["turning rhythm", "patterns appear"]], interaction_type="short_text"),
            _q("Together we plan, together we draw, together we check every line that we saw.", "Repeating together stresses cooperation through all three actions.", ["Together means one person did everything.", "The lines describe an unfinished meal.", "The repeated word removes all action."]),
            _r("Orange on the marigold, orange in the flame; two very different things can carry one colour name.", "The repeated orange compares a flower and flame through colour while clearly keeping them as different objects.", [["orange compares flower and flame", "shared colour"], ["different objects", "not the same thing"]], interaction_type="short_text"),
            _r("Give a turn, take a turn, let the busy colour wheel spin; fair hands around the table help everyone begin.", "The repeated word turn creates rhythm and emphasises fairness, while the final line explains that equal access lets everyone participate.", [["repeated turn", "emphasises fairness"], ["equal access", "everyone participates"]], interaction_type="short_text"),
        ],
        misconception="The learner only names a repeated word without explaining its effect, or writes a long personal response that does not answer the focused question from the supplied lines.",
        remediation="Find the repeated or image-making words, complete the frame 'This pattern emphasises...', and keep the response to two sentences that both use the visible poem clues.",
    ),
]


ASSESSMENT_PAIRS = [
    _aq_pair("reading.word_meaning_context", "What does pale green mean in this sentence?", ("The pale green cloth looked almost white beside the dark leaf.", "very light green", ["rough brown", "deep black", "bright red"]), ("The vivid blue sign remained clear even from the far gate.", "strong and bright blue", ["weak grey", "hidden brown", "colourless glass"]), second_prompt="What does vivid blue mean in this sentence?"),
    _ar_pair("reading.paragraph_main_idea", "State the main idea in one sentence.", "Captures the central change and result rather than one minor detail.", ("A grey reading corner became cheerful after pupils added coloured labels. The labels also helped everyone return books to the correct shelf.", "Coloured labels brightened the reading corner and helped pupils organise its books.", [["coloured labels brightened the reading corner", "bright shelf tags made the corner welcoming"], ["helped pupils organise its books", "showed where each book belonged"]]), ("The class used one colour for urgent notices and another for weekly news. Visitors began finding information more quickly.", "A simple colour system helped visitors find different kinds of class information quickly.", ["colour system", "find information quickly"]), interaction_type="summary"),
    _ar_pair("reading.inference_reason", "State the best-supported idea and cite the deciding action.", "States a plausible motive and grounds it in the visible action or need.", ("Rohan moves his unused ruler toward a partner whose ruler has snapped.", "Rohan wants to help the partner continue measuring, as shown by moving his unused ruler toward the broken one.", ["help the partner continue measuring", "moving his unused ruler"]), ("Mili places the shared paint tray in the middle before four pupils begin.", "Mili wants every pupil to reach the tray, as shown by placing it in the middle before they start.", ["every pupil to reach", "placing it in the middle"])),
    _ar_pair("writing.reason_answer", "Write the fair action and support it with a because-clause.", "States a suitable action and a reason grounded in the quantities or needs supplied.", ("There are six brushes for three pairs, and every pair needs two.", "Give two brushes to each pair because six brushes divide equally among three pairs.", ["two brushes to each pair", "divide equally"]), ("A visitor needs a seat, and two chairs beside the group are empty.", "Offer the visitor one empty chair because the group has two spare seats.", ["offer one empty chair", "two spare seats"])),
    _aq_pair("grammar.noun_verb_adjective", "Which word is the action word?", ("The patient artist mixes orange paint.", "mixes", ["patient", "artist", "orange"]), ("A small child carries the poster carefully.", "carries", ["small", "child", "poster"])),
    _ar_pair("writing.complete_sentence", "Use every supplied detail in one complete sentence.", "Includes a named doer, a clear action, and all relevant supplied details.", ("Doer: the careful monitor; action: closes; detail: the paint jars after class.", "The careful monitor closes the paint jars after class.", ["careful monitor closes", "paint jars after class"]), ("Doer: two friends; action: share; detail: a box of coloured pencils at lunch.", "Two friends share a box of coloured pencils at lunch.", ["Two friends share", "coloured pencils at lunch"]), interaction_type="short_text"),
    _aq_pair("reading.event_sequence", "What was the last event on this card?", ("Lina sorted the cards, checked their labels, and placed them in a tray.", "She placed the cards in a tray.", ["She sorted the cards.", "She checked labels.", "She tore every card."]), ("The team opened the map, marked the route, and followed it to the hall.", "The team followed the route to the hall.", ["The team opened the map.", "The team marked the route.", "The team hid the hall."])),
    _ar_pair("grammar.sentence_order", "Arrange all parts into one natural sentence.", "Uses every supplied part in a natural subject-action-detail order.", ("Parts: at noon / the art club / displayed / its new banner / near the gate.", "At noon, the art club displayed its new banner near the gate.", ["art club displayed", "new banner", "near the gate"]), ("Parts: carefully / Saira / placed / the wet brushes / beside the sink.", "Saira carefully placed the wet brushes beside the sink.", ["Saira carefully placed", "wet brushes", "beside the sink"]), interaction_type="short_text"),
    _aq_pair("vocab.spelling", "Which spelling uses every supplied letter correctly?", ("Letters: B, R, O, W, N.", "BROWN", ["BRWON", "BORWN", "BROWNN"]), ("Letters: W, H, I, T, E.", "WHITE", ["WHIET", "WITHE", "WHITT"])),
    _ar_pair("vocab.word_formation", "Form the compound, split its bases, and explain its meaning.", "Forms the compound and explains the contribution of both base words.", ("Bases: rain + bow. Clue: a coloured arc that may appear with rain and light.", "Rainbow combines rain and bow and names a bow-shaped band of colour sometimes seen when rain and light meet.", ["rainbow", "rain and bow", "band of colour"]), ("Bases: sun + light. Clue: light that comes from the sun.", "Sunlight combines sun and light and means the light that comes from the sun.", ["sunlight", "sun and light", "light from the sun"])),
    _aq_pair("reading.poetic_language", "Which explanation best describes the repeated word?", ("Share the red, share the blue, share a bright idea too.", "Share emphasises cooperation with materials and ideas.", ["Share means everyone works alone.", "Share describes a broken chair.", "Share removes the rhythm."]), ("Green in the garden, green by the gate, green leaves rustle while children wait.", "Green links plant details across the scene.", ["Green proves the gate is a leaf.", "The lines only describe noise.", "Green means the garden vanished."])),
    _ar_pair("writing.short_answer", "Explain the pattern and its effect in one or two sentences.", "Identifies the visible poetic pattern and explains its effect concisely.", ("Pass the brush, pass the tray; pass kind help along the way.", "Repeating pass creates rhythm and emphasises sharing both tools and help.", ["repeating pass", "sharing tools and help"]), ("Silver on the river, silver in the rain; silver light guides the walkers home again.", "Repeating silver connects the water and light, creating a calm guiding image.", ["repeating silver", "calm guiding image"]), interaction_type="short_text"),
    _ar_pair("reading.paragraph_main_idea", "Summarise the whole card without listing every detail.", "Combines the central problem, response, and result accurately.", ("A box of mixed pencils slowed the art class. Pupils sorted them by colour, labelled six cups, and found supplies faster afterward.", "Sorting and labelling the mixed pencils made art supplies easier to find.", ["sorting and labelling", "easier to find"]), ("The poster text was hard to read on a dark background. The group changed it to white, and people could read it from the doorway.", "Changing the poster text to a contrasting colour made it readable from farther away.", ["contrasting colour", "readable farther away"]), interaction_type="summary"),
    _ar_pair("writing.complete_sentence", "Turn the fragment and supplied detail into one complete sentence.", "Produces a capitalized complete sentence with a clear doer, action, and relevant detail.", ("Fragment: paints a blue circle. Doer and place: Nia, on the class chart.", "Nia paints a blue circle on the class chart.", ["Nia paints", "blue circle", "class chart"]), ("Fragment: carry the paper stars. Doers and destination: The helpers, to the hall.", "The helpers carry the paper stars to the hall.", ["helpers carry", "paper stars", "to the hall"]), interaction_type="short_text"),
]


LAUNCH_DEPTH_CASES = {
    "colours_context_and_idea": [
        _launch_depth_case(
            "At the monsoon coat rack, amber tags mark raincoats that still need drying. Green tags mark coats ready to wear, and the helper moves each dry coat to the collection rail.",
            "What does amber mean on the monsoon coat rack, and what is the coat-rack card mainly about?",
            "Amber means the warm yellow-orange tag for a coat that is still wet. The card is mainly about using colour tags to sort raincoats by whether they are ready.",
            "amber means the warm yellow-orange tag",
            "colour tags sort raincoats by whether they are ready",
        ),
        _launch_depth_case(
            "A fruit stall uses crimson cards beside baskets that must be sold today. The deep red cards help the seller notice ripe fruit before it softens too much.",
            "Explain crimson on the fruit-stall cards and state the main idea of the ripe-fruit system.",
            "Crimson means deep red. The main idea is that deep red cards help the seller find and sell ripe fruit in time.",
            "crimson means deep red",
            "deep red cards help the seller find and sell ripe fruit",
        ),
        _launch_depth_case(
            "In the seedling corner, pale green sticks show pots that received little sunlight. Dark green sticks show pots that grew in bright light, so the class can compare the leaves.",
            "What does pale green show in the seedling corner, and what is the comparison mainly teaching?",
            "Pale green means a light green shade on the low-sunlight pots. The card is mainly about using coloured sticks to compare how much light seedlings received.",
            "pale green means a light green shade",
            "coloured sticks compare how much light seedlings received",
        ),
    ],
    "sharing_inference_and_reason": [
        _launch_depth_case(
            "Three children have one tray of clay. Ishan rolls long pieces for handles, Tara shapes bowls, and Mehul keeps a damp cloth over unused clay so it does not dry.",
            "What are Ishan, Tara, and Mehul trying to achieve with one clay tray, and why is their plan fair?",
            "They are trying to finish a set of clay cups together. Their plan is fair because each child has a useful job and everyone protects the shared clay.",
            "finish a set of clay cups together",
            "each child has a useful job",
        ),
        _launch_depth_case(
            "At a games station, only one water jug is full. Nida pours one cup for each team, Arav refills the jug, and both wait until every runner has water before taking seconds.",
            "What do Nida and Arav want at the games station, and what fair action should continue?",
            "They want every runner to get water. They should keep serving one cup each before seconds because the single jug must cover all teams.",
            "every runner to get water",
            "one cup each before seconds",
        ),
        _launch_depth_case(
            "A library puzzle has four envelopes of pieces. Sana opens one envelope at a time, shares its pieces across the table, and saves the final envelope for classmates arriving late.",
            "What is Sana likely trying to protect in the library puzzle, and why should she save the final envelope?",
            "Sana is trying to protect everyone's chance to join the puzzle. She should save the final envelope because late classmates need unused pieces too.",
            "protect everyone's chance to join the puzzle",
            "late classmates need unused pieces",
        ),
    ],
    "action_words_complete_sentences": [
        _launch_depth_case(
            "The bright kite glides above the wheat field. Kite names the object, bright describes it, and glides tells its action.",
            "Name the jobs of bright, kite, and glides, then write a complete wheat-field sentence with those words.",
            "Kite is a noun, bright is an adjective, and glides is a verb. The bright kite glides above the wheat field.",
            "kite is a noun, bright is an adjective, and glides is a verb",
            "the bright kite glides above the wheat field",
        ),
        _launch_depth_case(
            "A silver bell rang beside the school gate at noon. Bell names a thing, silver tells its colour, and rang tells what happened.",
            "Identify silver, bell, and rang, then write the complete school-gate sentence.",
            "Bell is a noun, silver is an adjective, and rang is a verb. A silver bell rang beside the school gate at noon.",
            "bell is a noun, silver is an adjective, and rang is a verb",
            "a silver bell rang beside the school gate at noon",
        ),
        _launch_depth_case(
            "The tiny seedling bends after heavy rain. Seedling names the plant, tiny describes its size, and bends shows the action.",
            "Explain the word jobs in tiny seedling bends, then write the full heavy-rain sentence.",
            "Seedling is a noun, tiny is an adjective, and bends is a verb. The tiny seedling bends after heavy rain.",
            "seedling is a noun, tiny is an adjective, and bends is a verb",
            "the tiny seedling bends after heavy rain",
        ),
    ],
    "events_and_sentence_order": [
        _launch_depth_case(
            "First Leela checks the torch batteries. Next she places the torch in the science kit. Finally she carries the kit to the dark-room table before class.",
            "Retell Leela's torch and science-kit events, then form one natural sentence about the final action.",
            "First Leela checks the batteries, next she packs the torch, and finally she carries the kit to the table. Leela carried the science kit to the dark-room table before class.",
            "first Leela checks the batteries, next she packs the torch, and finally she carries the kit",
            "Leela carried the science kit to the dark-room table before class",
            ordered=True,
        ),
        _launch_depth_case(
            "A coach first counts the blue bibs, then gives one to each player, and finally hangs the spare bibs behind the goal after practice.",
            "Put the blue-bib events in order and write a natural sentence about where the coach hangs the spares.",
            "First the coach counts the bibs, next each player receives one, and finally the spares are hung up. The coach hangs the spare bibs behind the goal after practice.",
            "first the coach counts the bibs, next each player receives one, and finally the spares are hung up",
            "the coach hangs the spare bibs behind the goal after practice",
            ordered=True,
        ),
        _launch_depth_case(
            "Maya finds a lunchbox under the bus seat, reads the class label, gives it to the driver, and watches the driver place it in the school office.",
            "Order Maya's lunchbox actions and write one complete sentence about the driver and school office.",
            "Maya finds the lunchbox, reads its label, gives it to the driver, and then it reaches the office. The driver placed the labelled lunchbox in the school office.",
            "finds the lunchbox, reads its label, gives it to the driver, and then it reaches the office",
            "the driver placed the labelled lunchbox in the school office",
            ordered=True,
        ),
    ],
    "spelling_and_compound_words": [
        _launch_depth_case(
            "A garden card gives the base words sun and flower beside a tall yellow plant. Every letter in both words is needed for the plant name.",
            "Spell the compound made from sun and flower, and explain its meaning from the garden card.",
            "Sun and flower join to spell sunflower. A sunflower is the tall yellow flower named by the two base words.",
            "sun and flower join to spell sunflower",
            "the tall yellow flower named by the two base words",
        ),
        _launch_depth_case(
            "The rainy-day shelf shows rain and coat beside a waterproof jacket. The label must use all eight letters without a space.",
            "Build and spell the rainy-day compound from rain and coat, then tell what it names.",
            "Rain and coat combine to spell raincoat. A raincoat is a coat worn to keep rain off the wearer.",
            "rain and coat combine to spell raincoat",
            "a coat worn to keep rain off the wearer",
        ),
        _launch_depth_case(
            "On the school map, play and ground appear beside the open area with swings and a slide. The two bases form one place word.",
            "Spell the place word from play and ground and explain why it fits the school map.",
            "Play and ground join to spell playground. The map uses playground for the ground where children play on swings and a slide.",
            "play and ground join to spell playground",
            "ground where children play on swings and a slide",
        ),
    ],
    "poetic_pattern_and_short_answer": [
        _launch_depth_case(
            "Gold on the branch, gold on the lane, gold in the puddle after rain. The repeated colour follows autumn leaves from tree to ground.",
            "How does repeated gold shape the autumn-leaf lines, and what short answer gives their main picture?",
            "Repeating gold ties the branch, lane, and puddle into one bright pattern. The lines picture autumn leaves spreading colour after rain.",
            "repeating gold ties the branch, lane, and puddle",
            "autumn leaves spreading colour after rain",
        ),
        _launch_depth_case(
            "Tap at the window, tap on the tin, tap goes the rain as the clouds roll in. The repeated tap copies one small sound in three places.",
            "What effect does repeated tap create in the window-and-tin lines, and what is happening?",
            "The repeated tap makes a quick rain rhythm. The short poem shows raindrops striking the window and tin as clouds arrive.",
            "repeated tap makes a quick rain rhythm",
            "raindrops striking the window and tin",
        ),
        _launch_depth_case(
            "A silver road crosses the pond when the moon rises, but it breaks into pieces whenever the water ripples.",
            "Explain the silver-road image on the moonlit pond and answer why the road seems to break.",
            "The silver road is moonlight reflected across the pond. It seems to break because ripples split the reflected light into moving pieces.",
            "silver road is moonlight reflected across the pond",
            "ripples split the reflected light",
        ),
    ],
}

_add_launch_depth_variants(LEVELS, LAUNCH_DEPTH_CASES)


_SEMANTIC_OPTION_REPLACEMENTS = {'Repeating share shows everyone worked alone.': 'Repeating share focuses only on the '
                                                 'materials being passed.',
 'The poem warns readers never to use colour.': 'The repeated word makes the colours '
                                                'seem difficult to share.'}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch01:assessment:01': {'accepted_answers': ['very light green'],
                               'options': ['rough brown',
                                           'deep black',
                                           'bright red',
                                           'very light green'],
                               'passage': 'A painter mixed one drop of green into a '
                                          'cup of white paint, making a pale green '
                                          'shade.',
                               'prompt': 'What does pale green mean in this sentence?'}}


_SEMANTIC_CONNECTOR_OPTIONS = ("and", "but", "because", "so", "although")
_SEMANTIC_MALFORMED_CONNECTORS = (
    "why",
    "without contrast",
    "without reason",
    "without cause",
    "unless so",
    "therefore",
)
_SEMANTIC_COPY_REPLACEMENTS = (
    ("an clue-based inference", "a clue-based conclusion"),
    ("an careful check", "a careful check"),
    ("asks a shelf for", "chooses from a shelf"),
)


def _semantic_replace_malformed_connectors(activity: dict[str, Any]) -> None:
    options = activity.get("options") or []
    accepted = activity.get("accepted_answers") or []
    if len(accepted) != 1 or accepted[0] not in _SEMANTIC_CONNECTOR_OPTIONS:
        return
    if not any(
        any(fragment in option.casefold() for fragment in _SEMANTIC_MALFORMED_CONNECTORS)
        for option in options
    ):
        return
    correct = accepted[0]
    retained = {
        option
        for option in options
        if not any(
            fragment in option.casefold()
            for fragment in _SEMANTIC_MALFORMED_CONNECTORS
        )
    }
    replacements = [
        option
        for option in _SEMANTIC_CONNECTOR_OPTIONS
        if option != correct and option not in retained
    ]
    replacement_index = 0
    cleaned: list[str] = []
    for option in options:
        malformed = any(
            fragment in option.casefold()
            for fragment in _SEMANTIC_MALFORMED_CONNECTORS
        )
        if malformed:
            while replacements[replacement_index] in cleaned:
                replacement_index += 1
            option = replacements[replacement_index]
            replacement_index += 1
        cleaned.append(option)
    activity["options"] = cleaned


def _apply_semantic_copy_corrections(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in tuple(value.items()):
            if isinstance(item, str):
                for old, new in _SEMANTIC_COPY_REPLACEMENTS:
                    item = item.replace(old, new)
                value[key] = item
        if value.get("options"):
            value["options"] = [
                _SEMANTIC_OPTION_REPLACEMENTS.get(option, option)
                for option in value["options"]
            ]
            _semantic_replace_malformed_connectors(value)
        for child in value.values():
            _apply_semantic_copy_corrections(child)
    elif isinstance(value, list):
        for child in value:
            _apply_semantic_copy_corrections(child)


def _apply_semantic_assessment_overrides(manifest: dict[str, Any]) -> None:
    items = {
        item["activity_id"]: item
        for item in manifest["chapter_assessment"]["items"]
    }
    for item_id, override in _SEMANTIC_ASSESSMENT_OVERRIDES.items():
        item = items[item_id]
        item["passage"] = override["passage"]
        item["prompt"] = override["prompt"]
        if "options" in override:
            item["options"] = list(override["options"])
            item["accepted_answers"] = list(override["accepted_answers"])
            continue
        item["model_answer"] = override["model_answer"]
        item["relevance_terms"] = list(override["relevance_terms"])
        aliases = override["slot_aliases"]
        if len(aliases) != len(item["concept_slots"]):
            raise ValueError(f"class3_semantic_slot_count:{item_id}")
        for slot, slot_aliases in zip(item["concept_slots"], aliases, strict=True):
            slot["any_of"] = list(slot_aliases)

MANIFEST = _build_manifest(
    chapter_id=CHAPTER_ID,
    chapter_no=1,
    title="Colours",
    unit_title="Fun with Friends",
    source_url=SOURCE_URL,
    page_extract="/tmp/zidd-ncert-class2-3/eng_c3_ch01.txt",
    source_anchors=SOURCE_ANCHORS,
    levels=LEVELS,
    assessment_pairs=ASSESSMENT_PAIRS,
)

_apply_semantic_copy_corrections(MANIFEST["levels"])
_apply_semantic_copy_corrections(
    MANIFEST["chapter_assessment"]["items"]
)
_apply_semantic_assessment_overrides(MANIFEST)
