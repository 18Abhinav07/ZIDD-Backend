"""Deep authored manifest for Class 3 English Chapter 7.

The NCERT extract is used only to map chapter structure, themes, and exercise
forms. All learner-facing passages, questions, options, and rubric authority
in this manifest are original Zidd content.
"""

from __future__ import annotations

import re
from typing import Any


MANIFEST_SCHEMA_VERSION = "school-class5-deep-manifest-v1"

_PROMPT_VERBS = {
    "co_construct": "Choose",
    "guided_1": "Select",
    "guided_2": "Explain",
    "independent_1": "Build",
    "independent_2": "Write",
    "transfer_1": "Apply",
    "transfer_2": "Extend",
    "transfer_4": "Create",
    "review_1": "Recheck",
    "review_2": "Summarise",
    "review_3": "Check",
    "review_4": "Conclude",
    "bridge": "Try",
    "masterclass": "Solve",
    "revision_level_1": "Check",
    "revision_level_2": "Use",
    "revision_level_3": "Finish",
    "assessment": "Answer",
}


def _preserve_initial_case(source: str, replacement: str) -> str:
    if source and source[0].isupper():
        return replacement[0].upper() + replacement[1:]
    return replacement


def _learner_copy(value: str) -> str:
    """Replace teacher-facing labels in text shown during a lesson."""

    replacements = (
        (r"\battribute dialogue\b", "match dialogue to its speaker"),
        (r"\breconstruct an event sequence\b", "put events in order"),
        (r"\bpoetic exaggeration\b", "playful overstatement"),
        (r"\bcuriosity-driven\b", "question-led"),
        (r"\bevidence-based\b", "clue-based"),
        (r"\bcentral movement\b", "main change"),
        (r"\bordinal adjective\b", "position word"),
        (r"\breconstruct\b", "put back together"),
        (r"\bcomprehend\b", "understand"),
        (r"\bconstruct\b", "write"),
        (r"\bderive\b", "work out"),
        (r"\binfer\b", "work out"),
        (r"\binterpret\b", "explain"),
        (r"\battributes\b", "details"),
        (r"\battribute\b", "detail"),
        (r"\binvestigation\b", "careful check"),
        (r"\bclassify\b", "sort"),
        (r"\bprecisely\b", "clearly"),
        (r"\bprecise\b", "clear"),
        (r"\bgrounded\b", "supported"),
    )
    result = value
    for pattern, replacement in replacements:
        result = re.sub(
            pattern,
            lambda match: _preserve_initial_case(match.group(0), replacement),
            result,
            flags=re.IGNORECASE,
        )
    return result


def _case(
    label: str,
    passage: str,
    question: str,
    correct: str,
    wrong_1: str,
    wrong_2: str,
    reason: str,
    key_fact: str,
    key_reason: str,
) -> dict[str, str | list[str]]:
    """Store one original evidence case used by a single lesson concept."""

    return {
        "label": label,
        "passage": passage,
        "question": question,
        "correct": correct,
        "distractors": [
            wrong_1,
            wrong_2,
        ],
        "model": (
            f"For the {label} card, my answer is: {correct} "
            f"{reason}"
        ),
        "fact_terms": [
            f"For the {label} card, my answer is: {correct}",
            f"{correct} That is my answer for the {label} card.",
        ],
        "reason_terms": [reason, f"{reason} This clue supports my answer."],
        "relevance_phrases": [key_fact, key_reason],
        "reason": reason,
    }


def _fresh_case(
    label: str,
    passage: str,
    question: str,
    correct: str,
    reason: str,
    key_fact: str,
    key_reason: str,
) -> dict[str, str | list[str]]:
    """Store a fresh open-response case with short semantic paraphrases."""

    return _case(
        label,
        passage,
        question,
        correct,
        "The card gives a different result.",
        "The needed detail is not shown in that choice.",
        reason,
        key_fact,
        key_reason,
    )


def _assessment_pair(
    skill_id: str,
    form_a: dict[str, Any],
    form_b: dict[str, Any],
    *,
    kind: str,
    interaction_type: str = "evidence_text",
) -> dict[str, Any]:
    if kind not in {"choice", "open"}:
        raise ValueError("class3_assessment_pair_kind_invalid")
    if kind == "choice" and skill_id.startswith(("writing.", "speaking.", "oral.")):
        raise ValueError("class3_productive_assessment_must_be_open")
    return {
        "skill_id": skill_id,
        "forms": (form_a, form_b),
        "kind": kind,
        "interaction_type": interaction_type,
    }


def _relevance_terms(*values: str) -> list[str]:
    ignored = {
        "about",
        "after",
        "because",
        "before",
        "could",
        "should",
        "their",
        "there",
        "these",
        "through",
        "which",
        "while",
        "would",
    }
    terms: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z'-]+", " ".join(values)):
        lowered = word.casefold()
        if len(lowered) < 5 or lowered in ignored or lowered in terms:
            continue
        terms.append(lowered)
        if len(terms) == 4:
            break
    if len(terms) < 2:
        raise ValueError("class3_case_requires_relevance_terms")
    return terms


def _passage(case: dict[str, Any]) -> str:
    return str(case["passage"])


def _prompt(level: dict[str, Any], stage: str, case: dict[str, Any]) -> str:
    verb = _PROMPT_VERBS[stage]
    return _learner_copy(f"{verb}: {case['question']}")


def _choice_activity(
    chapter_id: str,
    level: dict[str, Any],
    stage: str,
    index: int,
    case: dict[str, Any],
) -> dict[str, Any]:
    activity_id = f"{chapter_id}:{level['level_id']}:{stage}:{index}"
    options = [case["correct"], *case["distractors"]]
    shift = sum(ord(char) for char in activity_id) % len(options)
    options = options[shift:] + options[:shift]
    return {
        "kind": "selected_option",
        "activity_id": activity_id,
        "teaching_block": _learner_copy(
            f"{level['principle']} Read the card once. Compare each choice with "
            "the card, then choose the best match."
        ),
        "passage": _passage(case),
        "prompt": _prompt(level, stage, case),
        "skill_ids": [level["skill_ids"][0]],
        "options": options,
        "accepted_answers": [case["correct"]],
    }


def _open_activity(
    chapter_id: str,
    level: dict[str, Any],
    stage: str,
    index: int,
    case: dict[str, Any],
    *,
    skill_ids: list[str],
    min_words: int = 8,
    interaction_type: str | None = None,
    activity_id: str | None = None,
) -> dict[str, Any]:
    activity_id = activity_id or f"{chapter_id}:{level['level_id']}:{stage}:{index}"
    fact_id = f"{activity_id}:fact"
    reason_id = f"{activity_id}:reason"
    if interaction_type is None:
        interaction_type = "evidence_text"
        if stage.startswith("transfer") and level.get("creative_transfer"):
            interaction_type = "creative_continuation"
        elif any(skill.startswith("writing.") for skill in skill_ids):
            interaction_type = "paragraph_text"
        elif stage.startswith("review"):
            interaction_type = "reflection"
    model_answer = str(case["model"])
    if len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", model_answer)) < min_words:
        model_answer += f" The {case['label']} card supports this complete answer."
    return {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": _learner_copy(
            f"{level['principle']} Read the new card. Give the answer, then tell "
            "which words helped you."
        ),
        "passage": _passage(case),
        "prompt": _prompt(level, stage, case),
        "skill_ids": skill_ids,
        "interaction_type": interaction_type,
        "rubric_criteria": [
            {
                "id": fact_id,
                "description": _learner_copy(
                    f"Answers the question about {level['concept']} on this card."
                ),
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": reason_id,
                "description": "Explains the answer with a word or detail from the card.",
                "required": True,
                "min_quality": 0.7,
            },
        ],
        "concept_slots": [
            {
                "id": fact_id,
                "description": "Answer",
                "any_of": list(case["fact_terms"]),
            },
            {
                "id": reason_id,
                "description": "Clue from the card",
                "any_of": list(case["reason_terms"]),
            },
        ],
        "forbidden_phrases": [
            "Anything can be correct",
            "I did not use the card",
            "My answer is only a guess",
        ],
        "min_response_words": min_words,
        "relevance_terms": _relevance_terms(
            str(case["correct"]),
            str(case["reason"]),
            *[str(value) for value in case["relevance_phrases"]],
        ),
        "model_answer": model_answer,
        "pass_score": 0.8,
        **(
            {"ordered_concept_slot_ids": [fact_id, reason_id]}
            if level.get("ordered_response")
            else {}
        ),
    }


def _support_activity(
    chapter_id: str,
    level: dict[str, Any],
    stage: str,
    index: int,
    case: dict[str, Any],
    *,
    min_words: int,
) -> dict[str, Any]:
    activity = _open_activity(
        chapter_id,
        level,
        stage,
        index,
        case,
        skill_ids=[level["skill_ids"][(index - 1) % len(level["skill_ids"])]],
        min_words=min_words,
    )
    support_focus = (
        "Start with the words in the card, not a guess.",
        "Make sure your reason supports the answer you chose.",
        "Give both the answer and the card detail that supports it.",
        "Keep each action or detail in the order shown.",
        "Use only ideas that the card gives.",
    )[index - 1]
    worked = level["cases"][index]
    activity["teaching_block"] = _learner_copy(
        f"{level['principle']} {support_focus} Here is an example from the "
        f"{worked['label']} card: {worked['passage']} {worked['reason']} "
        "So this answer fits: "
        f"'{worked['correct']}' For the new card, type your answer first and "
        "then type one detail that makes it fit."
    )
    activity["prompt"] = _learner_copy(
        f"Use the new card. {case['question']} Type your answer and one clue "
        "from the card."
    )
    return activity


def _level_manifest(chapter_id: str, level: dict[str, Any]) -> dict[str, Any]:
    cases = level["cases"]
    fresh_cases = level["fresh_cases"]
    if len(cases) != 7:
        raise ValueError(f"{chapter_id}:{level['level_id']}:requires_seven_cases")
    if len(fresh_cases) != 15:
        raise ValueError(
            f"{chapter_id}:{level['level_id']}:requires_fifteen_fresh_cases"
        )
    skill_a, skill_b = level["skill_ids"]
    support_stages = (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    support = {
        stage: _support_activity(
            chapter_id,
            level,
            stage,
            index,
            fresh_cases[index + 6],
            min_words=7 + index,
        )
        for index, stage in enumerate(support_stages, start=1)
    }
    support_ids = [support[stage]["activity_id"] for stage in support_stages]
    return {
        "level_id": level["level_id"],
        "title": _learner_copy(level["title"]),
        "focus": _learner_copy(level["focus"]),
        "outcome": _learner_copy(level["outcome"]),
        "skill_ids": level["skill_ids"],
        "episode_kind": level["episode_kind"],
        "source_anchor_ids": [
            f"{chapter_id}:anchor:{index}" for index in level["anchor_indexes"]
        ],
        "connect": {
            key: _learner_copy(value) for key, value in level["connect"].items()
        },
        "co_construct": _choice_activity(
            chapter_id, level, "co_construct", 1, cases[0]
        ),
        "guided_variants": [
            _choice_activity(chapter_id, level, "guided_1", 1, cases[1]),
            _open_activity(
                chapter_id,
                level,
                "guided_2",
                2,
                cases[2],
                skill_ids=[skill_b],
            ),
            _open_activity(
                chapter_id,
                level,
                "guided_2",
                3,
                cases[3],
                skill_ids=[skill_a],
            ),
            _open_activity(
                chapter_id,
                level,
                "guided_2",
                4,
                cases[4],
                skill_ids=[skill_b],
            ),
        ],
        "independent_variants": [
            _open_activity(
                chapter_id,
                level,
                "independent_1",
                1,
                cases[5],
                skill_ids=[skill_a],
            ),
            _open_activity(
                chapter_id,
                level,
                "independent_2",
                2,
                cases[6],
                skill_ids=[skill_b],
            ),
            _open_activity(
                chapter_id,
                level,
                "independent_1",
                3,
                fresh_cases[0],
                skill_ids=[skill_a],
            ),
            _open_activity(
                chapter_id,
                level,
                "independent_2",
                4,
                fresh_cases[1],
                skill_ids=[skill_b],
            ),
        ],
        "transfer_variants": [
            _open_activity(
                chapter_id,
                level,
                "transfer_1",
                1,
                fresh_cases[2],
                skill_ids=[skill_a],
            ),
            _open_activity(
                chapter_id,
                level,
                "transfer_2",
                2,
                fresh_cases[3],
                skill_ids=[skill_b],
            ),
            _open_activity(
                chapter_id,
                level,
                "transfer_1",
                3,
                fresh_cases[4],
                skill_ids=[skill_a, skill_b],
            ),
            _open_activity(
                chapter_id,
                level,
                "transfer_4",
                4,
                fresh_cases[12],
                skill_ids=[skill_a, skill_b],
            ),
        ],
        "review_variants": [
            _open_activity(
                chapter_id,
                level,
                "review_1",
                1,
                fresh_cases[5],
                skill_ids=[skill_a],
            ),
            _open_activity(
                chapter_id,
                level,
                "review_2",
                2,
                fresh_cases[6],
                skill_ids=[skill_b],
            ),
            _open_activity(
                chapter_id,
                level,
                "review_3",
                3,
                fresh_cases[13],
                skill_ids=[skill_a],
            ),
            _open_activity(
                chapter_id,
                level,
                "review_4",
                4,
                fresh_cases[14],
                skill_ids=[skill_b],
            ),
        ],
        "misconception_clusters": [
            {
                "cluster_id": f"{chapter_id}:{level['level_id']}:misconception",
                "skill_ids": level["skill_ids"],
                "misconception": _learner_copy(level["misconception"]),
                "remediation": _learner_copy(
                    "First, read the new card. Then, use the worked example to "
                    "choose an answer and a matching clue. Finally, type both "
                    "parts and check that they match the card."
                ),
                "support_check_ids": support_ids,
            }
        ],
        "support_checks": support,
    }


def _assessment_open_item(
    chapter_id: str,
    level: dict[str, Any],
    item_no: int,
    case: dict[str, Any],
    skill_id: str,
    interaction_type: str,
) -> dict[str, Any]:
    item_id = f"{chapter_id}:assessment:{item_no:02d}"
    activity = _open_activity(
        chapter_id,
        level,
        "assessment",
        item_no,
        case,
        skill_ids=[skill_id],
        min_words=8,
        interaction_type=interaction_type,
        activity_id=item_id,
    )
    activity["teaching_block"] = (
        "Work alone from this new card. Answer every part and use your own words."
    )
    activity["prompt"] = _learner_copy(str(case["question"]))
    return activity


def _assessment_choice_item(
    chapter_id: str,
    item_no: int,
    case: dict[str, Any],
    skill_id: str,
) -> dict[str, Any]:
    options = [case["correct"], *case["distractors"]]
    shift = item_no % len(options)
    return {
        "kind": "selected_option",
        "activity_id": f"{chapter_id}:assessment:{item_no:02d}",
        "teaching_block": (
            "Work alone from this new card. Check each choice against its words."
        ),
        "passage": str(case["passage"]),
        "prompt": _learner_copy(str(case["question"])),
        "skill_ids": [skill_id],
        "options": options[shift:] + options[:shift],
        "accepted_answers": [case["correct"]],
    }


def _assessment_manifest_v2(
    chapter_id: str,
    levels: list[dict[str, Any]],
    pairs: list[dict[str, Any]],
) -> dict[str, Any]:
    if len(pairs) != 14:
        raise ValueError(f"{chapter_id}:requires_fourteen_assessment_pairs")
    skill_to_level = {
        skill_id: level for level in levels for skill_id in level["skill_ids"]
    }
    items: list[dict[str, Any]] = []
    for form_index in range(2):
        for pair_index, pair in enumerate(pairs, start=1):
            item_no = form_index * 14 + pair_index
            case = pair["forms"][form_index]
            skill_id = pair["skill_id"]
            if skill_id not in skill_to_level:
                raise ValueError(f"{chapter_id}:assessment_skill_not_taught:{skill_id}")
            if pair["kind"] == "open":
                items.append(
                    _assessment_open_item(
                        chapter_id,
                        skill_to_level[skill_id],
                        item_no,
                        case,
                        skill_id,
                        pair["interaction_type"],
                    )
                )
            else:
                items.append(
                    _assessment_choice_item(chapter_id, item_no, case, skill_id)
                )

    taught_skills = set(skill_to_level)
    assessed_skills = {pair["skill_id"] for pair in pairs}
    if taught_skills != assessed_skills:
        raise ValueError(f"{chapter_id}:teaching_assessment_skill_drift")
    return {
        "items_per_attempt": 14,
        "pass_score": 0.8,
        "max_attempts": 2,
        "bank_item_count": 28,
        "items": items,
        "strands": [
            {
                "strand_id": f"{chapter_id}:{level['level_id']}:strand",
                "skill_ids": level["skill_ids"],
                "minimum_items": sum(
                    pair["skill_id"] in level["skill_ids"] for pair in pairs
                )
                * 2,
                "evidence_forms": sorted(
                    {
                        "constructed_response"
                        if pair["kind"] == "open"
                        else "selected_option"
                        for pair in pairs
                        if pair["skill_id"] in level["skill_ids"]
                    }
                ),
                "remediation_level_ids": [level["level_id"]],
            }
            for level in levels
        ],
    }


def build_manifest(spec: dict[str, Any]) -> dict[str, Any]:
    """Build one strict deep manifest from fully authored Class 3 cases."""

    chapter_id = spec["chapter_id"]
    source_url = spec["source_url"]
    anchors = [
        {
            "anchor_id": f"{chapter_id}:anchor:{index}",
            "section_label": anchor["label"],
            "page_start": anchor["page_start"],
            "page_end": anchor["page_end"],
            "source_url": f"{source_url}#page={anchor['page_start']}",
            "coverage_treatment": anchor["treatment"],
            "required_for_chapter_certification": anchor["required"],
        }
        for index, anchor in enumerate(spec["anchors"], start=1)
    ]
    levels = spec["levels"]
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "chapter": {
            "chapter_id": chapter_id,
            "chapter_no": spec["chapter_no"],
            "title": spec["title"],
            "book_title": "Santoor",
            "unit_title": spec["unit_title"],
            "source_url": source_url,
            "source_note": (
                "Official NCERT extract consulted only for chapter sequence, themes, "
                "and exercise forms; all Zidd runtime authority is original."
            ),
            "content_version": "2026-07-15.deep-v1",
            "certification_version": "school-deep-class3-v1",
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": spec["source_analysis_reference"],
            },
        },
        "source_anchors": anchors,
        "levels": [_level_manifest(chapter_id, level) for level in levels],
        "chapter_assessment": _assessment_manifest_v2(
            chapter_id, levels, spec["assessment_pairs"]
        ),
    }


def _connect(block: str, passage: str, prompt: str) -> dict[str, str]:
    return {"teaching_block": block, "passage": passage, "prompt": prompt}


SPEC: dict[str, Any] = {
    "chapter_id": "eng_c3_ch07",
    "chapter_no": 7,
    "title": "The Big Laddoo",
    "unit_title": "Good Food",
    "source_url": "https://ncert.nic.in/textbook/pdf/cesa107.pdf",
    "source_analysis_reference": (
        "/tmp/zidd-ncert-class2-3/eng_c3_ch07.txt structure review"
    ),
    "anchors": [
        {"label": "Chapter poem text under the recitation heading: playful size pattern", "page_start": 3, "page_end": 4, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us think, item 4: edible and non-edible round objects", "page_start": 5, "page_end": 5, "treatment": "zidd_equivalent", "required": True},
        {"label": "Let us learn describing words and Let us write A-B: opening blends and written animal pairs", "page_start": 6, "page_end": 7, "treatment": "taught_and_assessed", "required": True},
        {"label": "Float-and-sink object list adapted to text-only predictions", "page_start": 8, "page_end": 8, "treatment": "zidd_equivalent", "required": True},
        {"label": "Let us learn festival-food facts and Let us write A: festival food response", "page_start": 9, "page_end": 10, "treatment": "taught_and_assessed", "required": True},
        {"label": "Unit picture-reading questions about food production", "page_start": 1, "page_end": 2, "treatment": "textbook_companion", "required": False},
        {"label": "Let us speak: tactile clues for identifying a sweet", "page_start": 6, "page_end": 6, "treatment": "guided_only", "required": False},
        {"label": "Let us explore: hands-on float-and-sink tub activity", "page_start": 8, "page_end": 8, "treatment": "offline_group_activity", "required": False},
    ],
    "levels": [
        {
            "level_id": "laddoo_playful_scale",
            "title": "Spot playful giant ideas",
            "focus": "recognise poetic exaggeration and infer its playful purpose",
            "concept": "poetic exaggeration",
            "outcome": "Identify an impossible scale clue and explain how it creates a playful mental picture rather than a literal claim.",
            "skill_ids": ["reading.poetic_language", "reading.inference_reason"],
            "episode_kind": "meaning_encounter",
            "anchor_indexes": [1],
            "principle": "Poetic exaggeration deliberately stretches size or action; the impossible clue signals imagination and helps a feeling or picture stand out.",
            "connect": _connect(
                "Writers sometimes make an object impossibly large to create surprise. A reader checks whether the scale could really happen before deciding that the line is playful.",
                "At a fair, Nila joked that one pumpkin was wide enough to become a roof for the whole town.",
                "Notice the impossible size clue and picture the humorous scene it creates.",
            ),
            "misconception": "The learner treats every large object as poetic exaggeration or repeats the surprising detail without explaining why it cannot be literal.",
            "remediation": "Underline the scale clue, compare it with ordinary size, label it possible or impossible, and then state the playful effect in a because sentence.",
            "creative_transfer": True,
            "cases": [
                _case("market pumpkin", "A storyteller says a pumpkin at the market was so broad that twenty families could picnic on its top.", "Is the size literal or exaggerated, and what effect does it create?", "The pumpkin size is exaggerated for humour.", "The pumpkin is an ordinary small fruit.", "The line reports an exact market measurement.", "Twenty families could not really picnic on one pumpkin, so the impossible scale creates a funny picture.", "exaggerated pumpkin size", "impossible picnic scale"),
                _case("river spoon", "In a comic verse, a cook stirs the river with a spoon as long as a railway platform.", "Which reading explains the giant spoon accurately?", "The giant spoon is a playful exaggeration.", "The spoon is a real tool listed in a science report.", "The river becomes a kitchen by law.", "Its impossible length makes the cooking image surprising rather than factual.", "playful giant spoon", "impossible spoon length"),
                _case("festival drum", "A child writes that the festival drum boomed loudly enough to wake every cloud above the village.", "What should a careful reader infer about the waking clouds?", "Waking every cloud is an imaginative exaggeration.", "Clouds are sleeping people in the passage.", "The sentence gives a weather forecast.", "The claim cannot happen literally and magnifies the power of the drumbeat.", "imaginative waking clouds", "magnifies loud drumbeat"),
                _case("tower sandwich", "Rafi describes a sandwich stacked so high that its top brushed the moon before lunch.", "How does the moon clue shape the meaning?", "The moon clue marks an impossible tall-sandwich exaggeration.", "The sandwich was carried to space.", "Lunch happened on the moon.", "It turns ordinary hunger into a comic picture of enormous food.", "impossible tall sandwich", "comic enormous food"),
                _case("ocean cup", "Grandmother jokes that her tiny cup could hold the whole ocean when guests arrive.", "Why is the whole-ocean claim not a measurement?", "The whole-ocean claim is humorous exaggeration.", "The cup is a hidden reservoir.", "The guests measured the ocean exactly.", "A tiny cup cannot contain an ocean, so the contrast makes the welcome sound grand.", "humorous ocean claim", "tiny cup contrast"),
                _case("kite tail", "A fair poster boasts that one kite has a tail long enough to wrap around every house in the district.", "What evidence identifies the poster line as exaggeration?", "Wrapping every house is an impossible scale clue.", "Every house donated one ribbon.", "The district has only one house.", "The enormous reach is invented to make the kite sound spectacular.", "impossible house wrapping", "spectacular enormous reach"),
                _case("rice mountain", "A playful menu promises a rice mound taller than the school tower on celebration day.", "How should the menu promise be interpreted?", "The tower-high rice mound is poetic exaggeration.", "The school tower is made from rice.", "The menu gives a building instruction.", "The impossible comparison creates excitement about an abundant meal.", "tower-high rice mound", "excitement about abundance"),
            ],
        },
        {
            "level_id": "laddoo_round_clues",
            "title": "Use shape words in context",
            "focus": "infer word meaning and order useful attributes around a round object",
            "concept": "round attribute description",
            "outcome": "Use nearby clues to interpret shape vocabulary and organise size, texture, colour, and use into a precise object description.",
            "skill_ids": ["reading.word_meaning_context", "vocab.attribute_ordering"],
            "episode_kind": "language_lab",
            "anchor_indexes": [2, 3],
            "principle": "A context clue reveals what a shape word means, while an orderly description groups attributes instead of piling up unrelated labels.",
            "connect": _connect(
                "Shape words become clear when a sentence names an edge, surface, or movement. A strong description then moves from the object's identity to its visible and useful features.",
                "The potter rolled a smooth clay ball. It had no corners and turned evenly under her palm.",
                "Notice how no corners explains round, then arrange the useful details in a clear order.",
            ),
            "misconception": "The learner guesses a familiar object instead of using the context clue, or lists adjectives in a confusing order without naming the object clearly.",
            "remediation": "Box the clue that defines the word, name the object first, and rebuild the description in the order shape, size, texture, and purpose.",
            "cases": [
                _case("clay bead", "Tara rolls clay until the bead has no corners. She describes it as small, round, smooth, and ready for a necklace.", "Which description follows the clues and a useful attribute order?", "It is a small round bead with a smooth surface for a necklace.", "It is a cornered rough plate for painting.", "It is a tall square block used as a door.", "The sentence names the object before shape, texture, and purpose.", "small round bead", "shape texture purpose order"),
                _case("copper plate", "The copper plate is broad and circular, with a shiny flat surface used for serving fruit.", "What does circular mean here, and how should the details be organised?", "Circular means round, and the plate is broad, shiny, flat, and used for serving.", "Circular means pointed, and the plate is soft cloth.", "Circular means broken, and the plate is used for writing.", "The edge and serving clues support a shape-first description.", "circular means round", "shape-first plate description"),
                _case("garden pebble", "A gardener finds a palm-sized pebble whose curved edge continues all the way around its grey smooth face.", "Which words best capture the pebble's ordered attributes?", "The pebble is palm-sized, round-edged, grey, and smooth.", "The pebble is enormous, square, red, and furry.", "The pebble is liquid, sharp, green, and noisy.", "Each chosen attribute comes directly from the visible sentence clues.", "round-edged grey pebble", "direct sentence clues"),
                _case("paper disc", "Ishan cuts a flat paper disc. Its edge forms one unbroken curve, and its blue face fits inside his card.", "How does the edge clue explain disc, and which description is precise?", "A disc is a flat round shape; this one is blue and card-sized.", "A disc is a tall wooden pole; this one is red.", "A disc is a soft bag; this one holds water.", "The unbroken curved edge and flat face establish the meaning.", "flat round disc", "unbroken curved edge"),
                _case("festival sweet", "The sweet maker shapes a bite-sized golden ball with a grainy surface and places it in a paper cup.", "Arrange the stated attributes into one clear object sentence.", "The sweet is a bite-sized round golden ball with a grainy surface in a paper cup.", "The sweet is a huge blue cube with a glass surface.", "The sweet is a long silver rope under a chair.", "Identity comes first, followed by size, shape, colour, texture, and location.", "round golden sweet", "ordered size shape colour"),
                _case("wheel token", "The game token has a curved rim, a red centre, and a smooth face that spins on the table.", "Which contextual meaning and description fit the token?", "The token is a small round piece with a red smooth face that can spin.", "The token is a rough triangle that cannot move.", "The token is a long green strip used for sweeping.", "Its curved rim and spinning movement support the round meaning.", "small round token", "curved rim spins"),
                _case("moon badge", "A craft badge shows a full moon as a silver circle with a neat dark border and a pin behind it.", "How should the badge be described from object to purpose?", "It is a round silver moon badge with a dark border and a fastening pin.", "It is a square yellow shoe without a fastening.", "It is a tall cloth flag used as a spoon.", "The sentence orders identity, shape, colour, border, and use.", "round silver badge", "identity to purpose order"),
            ],
        },
        {
            "level_id": "laddoo_float_evidence",
            "title": "Explain float and sink results",
            "focus": "read a visible test result and construct a cause-based response",
            "concept": "float and sink evidence",
            "outcome": "Distinguish prediction from observation and justify a float-or-sink conclusion with the result printed in the reference.",
            "skill_ids": ["reading.sentence_comprehension", "writing.reason_answer"],
            "episode_kind": "application_mission",
            "anchor_indexes": [4],
            "principle": "A prediction comes before a test, but a conclusion must follow the observed result. The because clause must name that result, not an object's size alone.",
            "connect": _connect(
                "A fair investigation separates what someone expected from what the water test showed. The final sentence uses the observation as evidence even when the prediction was wrong.",
                "Leena expected a wax button to sink. In the bowl, it stayed on the surface for one full minute.",
                "Compare Leena's prediction with the printed observation before forming the conclusion.",
            ),
            "misconception": "The learner reports the prediction as if it were the result or decides that every heavy-looking object sinks without citing the observed water position.",
            "remediation": "Mark P beside the prediction and O beside the observation, then complete: It floated or sank because the test showed it stayed above or went below the surface.",
            "cases": [
                _case("cork test", "Dev predicts that a cork will sink. After he places it in a clear bowl, the cork remains on top of the water.", "What conclusion follows from the actual test, and why?", "The cork floats in this test.", "The cork sinks because Dev predicted it.", "The test has no result because the cork is small.", "It remains on top of the water, which is the visible observation.", "cork floats", "remains on top"),
                _case("coin test", "Maya thinks a metal coin may float. The coin drops through the water and rests on the bottom of the jar.", "How should Maya revise her prediction?", "The coin sinks in this test.", "The coin floats because it is round.", "The coin disappears before touching water.", "Resting on the bottom is evidence that it moved below the surface.", "coin sinks", "rests on bottom"),
                _case("leaf test", "A dry leaf is set gently on water. It stays at the surface while a timer counts thirty seconds.", "Which result sentence uses the observation rather than a guess?", "The dry leaf floats during the test.", "The dry leaf sinks because all leaves are heavy.", "The leaf turns into a stone in water.", "The timed observation shows it remaining at the surface.", "dry leaf floats", "stays at surface"),
                _case("clay shapes", "Two equal lumps of clay are tested. The tight clay ball sinks, but the wide clay bowl stays on the surface.", "What comparison is supported by this test?", "Shape changed the result: the ball sank while the clay bowl floated.", "Both clay shapes floated in exactly the same way.", "Colour alone made the clay ball sink.", "The material stayed equal while the printed observations differed by shape.", "ball sank bowl floated", "same material different shape"),
                _case("feather test", "Arun lowers a feather onto still water. The feather stays above the water until he removes it.", "Why is floated the accurate result word?", "The feather floated because it stayed above the water.", "The feather sank because Arun touched it.", "The feather dissolved at the bottom.", "Its position remained above the surface throughout the observation.", "feather floated", "above water position"),
                _case("rubber eraser", "A rubber eraser is released in a tub. It travels downward and stops beside a stone on the tub floor.", "Which evidence-based conclusion fits the eraser test?", "The eraser sinks and reaches the tub floor.", "The eraser floats beside the air.", "The eraser remains dry on a desk.", "Travelling downward to the floor is direct sinking evidence.", "eraser sinks", "downward to floor"),
                _case("sealed lid", "A sealed plastic lid is placed flat on water. It stays on the surface even when the bowl is gently tapped.", "What does the repeated observation allow you to conclude?", "The sealed lid floats in the stated conditions.", "The lid sinks whenever the bowl moves.", "The lid becomes metal after tapping.", "It repeatedly stays at the surface under the described test condition.", "sealed lid floats", "stays on surface"),
            ],
        },
        {
            "level_id": "laddoo_blend_wordcraft",
            "title": "Build words with opening blends",
            "focus": "spell and form meaningful words beginning with cl, pl, and bl",
            "concept": "blend word formation",
            "outcome": "Select the opening blend supported by meaning, spell the whole word, and use the formed word in a context-matched sentence.",
            "skill_ids": ["vocab.spelling", "vocab.word_formation"],
            "episode_kind": "language_lab",
            "anchor_indexes": [3],
            "principle": "In an opening blend, both consonants remain visible. Meaning confirms whether cl, pl, or bl completes the word; sound alone is not enough.",
            "connect": _connect(
                "A missing opening blend can create several letter patterns, but only one completed word will fit the sentence meaning. Readers check letters and context together.",
                "The sentence says, 'Please __ap when the song ends.' The action means bringing the hands together to applaud.",
                "Notice how the action clue supports clap with the complete cl opening blend.",
            ),
            "misconception": "The learner writes only one consonant from a blend or chooses a real word whose meaning does not fit the surrounding sentence.",
            "remediation": "Underline the meaning clue, test cl, pl, and bl in the gap, keep both opening letters, and read the completed sentence for sense.",
            "cases": [
                _case("applause word", "At the end of the puppet show, the audience will __ap to thank the performers. The missing word means applaud with the hands.", "Which completed word fits both spelling and meaning?", "The word is clap, beginning with cl.", "The word is lap, beginning with one consonant.", "The word is plan, meaning arrange ahead.", "Clap keeps both blend letters and matches the applause clue.", "clap begins cl", "matches applause clue"),
                _case("fruit word", "The basket contains one purple __um with a smooth skin and a stone inside. The clue names a fruit.", "How should the missing opening letters be completed?", "The word is plum, beginning with pl.", "The word is lum, which is incomplete here.", "The word is blue, which names a colour.", "Plum preserves the pl blend and matches the fruit description.", "plum begins pl", "fruit description clue"),
                _case("cover word", "Nani spreads a warm __anket over the sleeping child. The missing noun names a soft bed covering.", "Which blend forms the context-matched noun?", "The word is blanket, beginning with bl.", "The word is lanket without its full blend.", "The word is plant, which grows in soil.", "Blanket uses bl and fits the soft covering clue.", "blanket begins bl", "soft covering clue"),
                _case("time word", "The wall __ock shows that lunch begins at one. The missing object tells time.", "What full word belongs in the sentence?", "The word is clock, beginning with cl.", "The word is lock, which closes a door.", "The word is block, which is a solid piece.", "Clock retains cl and agrees with the tells-time clue.", "clock begins cl", "tells time clue"),
                _case("growing word", "We will __ant two bean seeds in moist soil. The missing verb means put something in the ground to grow.", "Which formed word expresses the stated action?", "The word is plant, beginning with pl.", "The word is lant without a complete opening.", "The word is blanket, which is a covering.", "Plant keeps pl and matches the growing action.", "plant begins pl", "growing action clue"),
                _case("colour word", "The artist mixes white into __ue paint to make a pale sky colour. The missing adjective names a colour.", "Which spelling completes the colour word?", "The word is blue, beginning with bl.", "The word is lue without the opening blend.", "The word is clue, which means a helpful detail.", "Blue uses bl and matches the paint-colour meaning.", "blue begins bl", "paint colour clue"),
                _case("cleaning word", "Use a soft __oth to wipe the round tray. The missing noun names a piece of fabric.", "Which opening blend produces the correct fabric word?", "The word is cloth, beginning with cl.", "The word is loth without the blend.", "The word is plot, which means a plan or piece of land.", "Cloth keeps cl and matches the wiping fabric clue.", "cloth begins cl", "wiping fabric clue"),
            ],
        },
        {
            "level_id": "laddoo_festival_information",
            "title": "Find the food idea and order",
            "focus": "identify a festival-food main idea and retell its events in order",
            "concept": "festival food main idea and sequence",
            "outcome": "State the main idea of a short festival-food card and retell its printed events in the order they happen.",
            "skill_ids": ["reading.paragraph_main_idea", "reading.event_sequence"],
            "episode_kind": "comprehension_studio",
            "anchor_indexes": [5],
            "principle": "A main idea covers the whole card. An ordered retell keeps each food event in its printed place and uses first, next, then, and finally when they help.",
            "connect": _connect(
                "Food cards can tell one big idea and several events. Readers ask what the whole card is about, then track what happened first and what happened later.",
                "At the winter fair, neighbours grind grain, cook porridge, carry bowls to the hall, and share the meal.",
                "The big idea is a shared seasonal meal; the event order runs from grinding to sharing.",
            ),
            "misconception": "The learner chooses one ingredient as the whole main idea or retells a later serving event before the food is prepared.",
            "remediation": "Circle the idea that covers every sentence, number each action where it appears, and read the retell once to check that no later step comes first.",
            "creative_transfer": True,
            "cases": [
                _case("harvest table", "After the grain harvest, families prepare different rice dishes and place them on one long table so everyone can taste and share.", "What main idea joins the harvest, dishes, and shared table?", "A harvest festival brings families together through shared food.", "Only one family eats alone after work.", "The paragraph mainly explains how to buy a table.", "The details all show community celebration through seasonal dishes.", "harvest festival shared food", "community seasonal dishes"),
                _case("neighbour recipe", "Meher's neighbour teaches her a lentil recipe used at an annual celebration. Meher writes the steps so the tradition can continue.", "Which sentence captures the paragraph and the word tradition?", "A festival food tradition is passed on through a shared recipe.", "Meher refuses to learn any cooking words.", "Tradition means a brand-new rule used once.", "The repeated annual practice moves from one neighbour to another.", "festival food tradition", "annual shared recipe"),
                _case("lentil meal order", "Farmers gather ripe lentils. Cooks wash them, simmer them with grain, and carry the finished pots to the fair table.", "Retell the four events in order.", "First gather the lentils, next wash them, then cook them with grain, and finally carry the pots to the table.", "First carry empty pots to the table, then gather the crop.", "The farmers serve a meal before any food is cooked.", "The crop is gathered and cleaned before it is cooked and served.", "gather wash cook carry", "crop before serving"),
                _case("sharing bowls", "Children carry labelled bowls from their homes to a school festival. Each label names the dish and one person who helped prepare it.", "Why are the labels a useful part of the event?", "The labels help people identify and share the festival dishes.", "The labels prevent anyone from seeing the food.", "The labels prove every bowl tastes identical.", "Names and helpers connect each bowl to its community source.", "identify share dishes", "community source labels"),
                _case("grower thanks order", "Growers bring new grain to the hall. Children label the sacks, cooks make flatbread, and the host thanks the growers before everyone eats.", "Which retell keeps the printed order?", "First growers bring grain, next children label it, then cooks make bread, and finally the host gives thanks before the meal.", "First everyone eats, and later the grain arrives.", "The host thanks growers before any sacks reach the hall.", "Arrival and labelling must happen before cooking, thanks, and eating.", "bring label cook thank", "grain arrives before meal"),
                _case("recipe exchange", "During a food festival, two families exchange recipe cards. Both dishes use lentils, but the spices and cooking times differ.", "What accurate comparison belongs in a summary?", "The families share a lentil tradition while keeping different recipe details.", "The two recipe cards are exactly the same.", "Neither family uses lentils.", "A common ingredient connects the dishes, while spices and timing vary.", "shared lentil tradition", "spices timing vary"),
                _case("welcome plate order", "Four kitchens send dishes to the hall. Volunteers label each dish, place small tastes on welcome plates, and explain the foods to visitors.", "Write the event order from arrival to explanation.", "First the dishes arrive, next volunteers label them, then they make welcome plates, and finally they explain the foods.", "First visitors hear an explanation about dishes that have not arrived.", "The labels are added after every plate is taken away.", "The dishes must arrive and be labelled before plates are made and explained.", "arrive label plate explain", "arrival before explanation"),
            ],
        },
        {
            "level_id": "laddoo_animal_pairs",
            "title": "Match animal word pairs",
            "focus": "identify animal nouns and action verbs, then use a pair in a clear sentence",
            "concept": "animal noun pair writing",
            "outcome": "Match two animal nouns that belong together, identify the action verb, and write a complete sentence that uses the pair clearly.",
            "skill_ids": ["grammar.noun_verb_adjective", "writing.complete_sentence"],
            "episode_kind": "expression_workshop",
            "anchor_indexes": [3],
            "principle": "Animal names are nouns, and action words are verbs. Check that both nouns belong to one animal kind, then give them a clear action in a complete sentence.",
            "connect": _connect(
                "A word pair is based on meaning, not matching first letters. A complete sentence can show that both animals belong to the same kind.",
                "The mare and the stallion walked beside the fence while their foal followed.",
                "Notice that mare and stallion are horse words and that the sentence tells what they did.",
            ),
            "misconception": "The learner matches words only because they begin alike or writes a fragment that does not show how the animal words belong together.",
            "remediation": "Name the animal kind for each word, keep only the pair from one kind, then write who did what in one complete sentence.",
            "creative_transfer": True,
            "cases": [
                _case("horse pair", "A stable card says, 'The mare and stallion rested.' Mare and stallion name adult horses.", "Which words are nouns, and which word is the verb?", "Mare and stallion are the animal nouns, and rested is the action verb.", "Rested is an animal noun, and mare is the action.", "Stallion and hen are both horse nouns.", "The two horse names tell who, while rested tells what they did.", "mare stallion nouns", "rested action verb"),
                _case("duck pair", "Near the pond, the drake and duck swam across the water. Both animal words name adult ducks.", "Which choice identifies the nouns and verb?", "Drake and duck are nouns, and swam is the verb.", "Swam and pond are the adult duck pair.", "Duck is the verb that tells the action.", "The pair names the animals, and swam names their action.", "drake duck nouns", "swam action verb"),
                _case("chicken pair", "The farm list puts rooster with hen because both words name adult chickens.", "Which complete sentence shows the pair?", "The rooster called while the hen guarded the chicks.", "The rooster and cow are both chickens.", "Rooster and hen near.", "Both nouns are chicken words and the verbs complete the idea.", "rooster hen chickens", "called guarded chicks"),
                _case("cattle pair", "A field card says, 'The bull grazed while the cow rested.' Bull and cow name adult cattle.", "Name the animal nouns and the action verbs.", "Bull and cow are nouns; grazed and rested are action verbs.", "Grazed and rested are the cattle nouns.", "Bull is an action, and rested is an animal.", "The cattle words name who, and the verbs tell what each did.", "bull cow nouns", "grazed rested verbs"),
                _case("peafowl pair", "A park guide names the male peafowl a peacock and the female a peahen.", "Which sentence keeps the meanings clear?", "The peacock opened his tail while the peahen walked nearby.", "The peacock and mare are both peafowl.", "Peahen the peacock.", "The guide links both nouns to peafowl and the sentence gives clear actions.", "peacock peahen pair", "tail walked nearby"),
                _case("lion pair", "The wildlife card says, 'The lion rested while the lioness watched.' Both animal words belong to one kind.", "Which words are nouns and which are verbs?", "Lion and lioness are nouns; rested and watched are verbs.", "Rested and watched are the lion pair.", "Lion is a verb, and watched is an animal noun.", "The animal names tell who, and the action words tell what happened.", "lion lioness nouns", "rested watched verbs"),
                _case("sheep pair", "The hillside note says ram for an adult male sheep and ewe for an adult female sheep.", "Which sentence uses the new pair?", "The ram followed the ewe along the hillside path.", "The ram and hen are both sheep words.", "Ram ewe along.", "Both words name sheep and followed gives the pair a clear action.", "ram ewe sheep", "followed hillside path"),
            ],
        },
    ],
}


FRESH_CASES = {
    "laddoo_playful_scale": [
        _fresh_case("lighthouse sandwich", "A comic menu shows a sandwich so tall that its top becomes a lighthouse for ships.", "What makes this picture playful instead of factual?", "The lighthouse sandwich is a funny exaggeration.", "A real sandwich cannot guide ships from high above the sea.", "funny giant sandwich", "cannot guide ships"),
        _fresh_case("whisper hill", "A rhyme says one child's whisper rolled over a hill and shook every window in the town.", "How should the whisper be understood?", "The town-shaking whisper is imaginative exaggeration.", "A whisper is normally quiet, so the huge effect is impossible.", "imaginative loud whisper", "normally quiet sound"),
        _fresh_case("ant cart", "In a silly tale, an ant pulls a cart filled with a hundred buses up a steep road.", "Which clue shows that the tale stretches reality?", "The ant pulling buses is an impossible size joke.", "A tiny ant could not move a load of buses.", "impossible ant load", "tiny ant huge load"),
        _fresh_case("soup lake", "A cook boasts that one bowl of soup could fill the village lake before sunset.", "What effect does the lake claim create?", "The lake-sized soup claim makes the boast humorous.", "One bowl holds far less than a lake.", "humorous soup boast", "bowl smaller than lake"),
        _fresh_case("moon umbrella", "A poem opens an umbrella so wide that it shades the moon during a picnic.", "Why is the umbrella image not a real report?", "The moon-shading umbrella is playful exaggeration.", "An umbrella on Earth cannot cover the moon.", "playful huge umbrella", "cannot cover moon"),
        _fresh_case("road pencil", "A school joke says Rupa's pencil was long enough to draw one line from Jaipur to Kochi.", "What does the distance clue tell the reader?", "The road-length pencil is an exaggerated comic picture.", "An ordinary pencil cannot reach between faraway cities.", "comic long pencil", "cities far apart"),
        _fresh_case("biscuit bridge", "A festival verse turns one crisp biscuit into a bridge for every truck in the market.", "How does the truck clue change the meaning?", "The biscuit bridge is an impossible playful idea.", "A small biscuit cannot carry heavy trucks.", "impossible biscuit bridge", "cannot carry trucks"),
        _fresh_case("teacup rain", "Grandfather jokes that his teacup caught all the rain that fell across the state.", "Which contrast makes the line funny?", "A tiny cup holding statewide rain is exaggeration.", "The cup is much too small for so much water.", "tiny cup huge rain", "too small for water"),
        _fresh_case("train shoe", "A storyteller says one shoe was so long that a train parked inside it for the night.", "What should a reader understand about the shoe?", "The train-sized shoe is not literal and creates humour.", "Shoes cannot contain an entire train.", "train sized shoe", "cannot hold train"),
        _fresh_case("star bell", "A child claims the school bell rang so strongly that stars covered their ears.", "Why are the stars part of an exaggeration?", "The ear-covering stars make the loud bell sound playful.", "Stars do not have ears and cannot hear a bell.", "playful loud bell", "stars have no ears"),
        _fresh_case("mango boat", "A poster promises one mango large enough to carry a class across a river like a boat.", "What is the poster trying to do?", "The boat-sized mango uses exaggeration to create excitement.", "A mango cannot safely carry a whole class.", "exciting giant mango", "cannot carry class"),
        _fresh_case("village scarf", "In a funny song, Mina's scarf wraps around every lane in her village twice.", "Which idea shows poetic exaggeration?", "The village-long scarf is an impossible picture.", "A normal scarf is far shorter than village lanes.", "impossible long scarf", "normal scarf shorter"),
        _fresh_case("schoolbag mountain", "A playground rhyme says one schoolbag grew taller than a snowy mountain before the lunch bell.", "Why is the mountain-high schoolbag playful rather than factual?", "The mountain-high schoolbag is comic exaggeration.", "A real schoolbag is far smaller than a mountain.", "comic mountain schoolbag", "real bag much smaller"),
        _fresh_case("coconut planet", "A stall poster calls one coconut a new planet that could carry every market shopper around the sun.", "Which clue makes the coconut claim an exaggeration?", "The shopper-carrying coconut is an impossible giant idea.", "A coconut cannot become a planet or carry a market crowd.", "impossible giant coconut", "cannot carry shoppers"),
        _fresh_case("railway spoon", "In a silly recipe, a spoon stretches from the kitchen to the railway station and stirs every pot on the way.", "What effect does the railway-station spoon create?", "The enormous spoon creates a humorous cooking picture.", "An ordinary spoon cannot reach a station or stir many distant pots.", "humorous enormous spoon", "ordinary spoon cannot reach"),
    ],
    "laddoo_round_clues": [
        _fresh_case("brass coin", "A brass coin has a flat face, a curved edge, and a stamped flower in its centre.", "Describe the coin from object to shape and detail.", "It is a flat round brass coin with a flower stamp.", "The curved edge shows roundness and the stamp is a smaller detail.", "round brass coin", "curved edge stamp"),
        _fresh_case("garden hoop", "The green hoop forms one large loop and has a smooth plastic surface for a garden game.", "Which ordered description fits the hoop?", "It is a large round green hoop with a smooth surface.", "The unbroken loop gives the shape before colour and texture.", "large round hoop", "unbroken smooth loop"),
        _fresh_case("jar lid", "A silver lid is palm-sized, flat, and ringed by tiny ridges that help it turn.", "How should the lid's details be placed in one sentence?", "The lid is a small round silver piece with ridged edges.", "Its ring shape comes before colour and edge texture.", "round silver lid", "ring shape ridges"),
        _fresh_case("red berry", "A berry on the card is pea-sized, red, smooth, and almost ball-shaped.", "What does ball-shaped mean here?", "Ball-shaped means round, and this berry is tiny, red, and smooth.", "The nearby size and surface words describe one round fruit.", "round tiny berry", "ball shape smooth"),
        _fresh_case("cart wheel", "The wooden cart wheel has a wide circular rim, eight spokes, and a dark brown finish.", "Build a clear shape-first description.", "It is a wide round wooden wheel with eight spokes.", "The circular rim sets the shape and the spokes add a countable detail.", "round wooden wheel", "circular rim spokes"),
        _fresh_case("glass bangle", "A thin blue bangle makes a complete circle and shines when light reaches it.", "Which sentence orders the bangle's attributes well?", "It is a thin round blue glass bangle with a shiny surface.", "The complete circle supports round before colour and material.", "round blue bangle", "complete circle shine"),
        _fresh_case("picnic plate", "A broad yellow plate has no corners and a shallow rim that keeps fruit from rolling away.", "How do the clues explain the plate's shape?", "The plate is broad, round, yellow, and shallow-rimmed.", "No corners and a continuous rim point to a round shape.", "broad round plate", "no corners rim"),
        _fresh_case("coat button", "The black coat button is small and circular with four holes in its smooth face.", "Write the button details in a useful order.", "It is a small round black button with four holes.", "Object, size, shape, colour, and holes make the description easy to follow.", "round black button", "circular four holes"),
        _fresh_case("class globe", "A blue classroom globe is shaped like a ball and stands on a short metal base.", "Which words describe shape before use or support?", "It is a round blue globe on a short metal stand.", "Ball-shaped gives round while the stand tells how it is held.", "round blue globe", "ball shape stand"),
        _fresh_case("drum top", "The top of the drum is a wide cream circle stretched tightly above its red sides.", "What exact description fits the drum top?", "The drum has a wide round cream top above red sides.", "Circle names the shape and the side colour is a later detail.", "round cream drum", "circle above sides"),
        _fresh_case("ripe orange", "The fruit is fist-sized, nearly spherical, bright orange, and rough-skinned.", "Explain spherical and describe the fruit.", "Spherical means round like a ball; the fruit is bright and rough-skinned.", "The ball comparison gives meaning while colour and skin add attributes.", "spherical round fruit", "ball bright rough"),
        _fresh_case("club badge", "A small white badge has a circular border, a green tree at the centre, and a pin behind it.", "Describe the badge from whole object to small parts.", "It is a small round white badge with a green tree and pin.", "The border gives the overall shape before the centre picture and fastening.", "round white badge", "circular border pin"),
        _fresh_case("compass dial", "A pocket compass has a small circular dial, a clear glass face, and a red needle at its centre.", "Describe the compass from overall shape to centre detail.", "It is a small round compass with a clear face and red centre needle.", "The circular dial sets the shape before the glass and needle details.", "small round compass", "circular dial red needle"),
        _fresh_case("clay bead", "The clay bead is pea-sized, smooth, purple, and shaped like a tiny ball with one hole through it.", "Explain the ball-shaped clue and order the bead's details.", "The bead is a tiny round smooth purple piece with one hole.", "Ball-shaped gives roundness, while the surface, colour, and hole add later details.", "tiny round purple bead", "ball shape one hole"),
        _fresh_case("cycle reflector", "A bicycle reflector has a wide round orange face, a bumpy plastic surface, and a screw behind it.", "Which clear description moves from reflector shape to its smaller parts?", "It is a wide round orange reflector with a bumpy face and rear screw.", "The curved face gives the overall shape before texture and fastening.", "round orange reflector", "curved face rear screw"),
    ],
    "laddoo_float_evidence": [
        _fresh_case("dry sponge", "A dry sponge is placed on water and stays at the top for forty seconds.", "What result does the timed observation support?", "The dry sponge floats during this test.", "It remains at the water's top for the whole timed check.", "dry sponge floats", "stays at top"),
        _fresh_case("glass marble", "A marble drops through the bowl and comes to rest beside the drain plug.", "Which conclusion uses the seen result?", "The glass marble sinks to the bottom.", "Moving below the surface and resting low are sinking clues.", "marble sinks bottom", "drops below surface"),
        _fresh_case("empty cup", "An empty paper cup is lowered upright. Its rim remains above water until the test ends.", "Why is floats the correct word?", "The empty cup floats with its rim above the water.", "The rim never goes below the surface in the stated test.", "empty cup floats", "rim stays above"),
        _fresh_case("steel key", "A steel key slips from the tongs, travels down, and lies flat on the tub floor.", "What should the result sentence say?", "The steel key sinks in the tub.", "The key travels downward and reaches the floor.", "steel key sinks", "reaches tub floor"),
        _fresh_case("foil boat", "A folded foil boat stays on top while a tight foil ball made from the same sheet goes down.", "What comparison is supported?", "The foil boat floats, but the foil ball sinks.", "The material is the same while the two shapes show different results.", "boat floats ball sinks", "same foil different shapes"),
        _fresh_case("river pebble", "A smooth pebble is released at the centre of a jar and settles under the water.", "How can the observation correct a guess that it would float?", "The pebble sinks, even if someone guessed it would float.", "The actual resting place below water is stronger than the guess.", "pebble sinks below", "result beats guess"),
        _fresh_case("dry twig", "A short dry twig lies across the water and does not dip under when the bowl is still.", "Which test word fits the twig?", "The dry twig floats across the surface.", "Its position remains on the surface throughout the check.", "dry twig floats", "remains on surface"),
        _fresh_case("soap bar", "A solid soap bar enters the water, moves down slowly, and stops on the bowl base.", "What evidence proves the result?", "The soap bar sinks to the bowl base.", "It moves beneath the surface until the base stops it.", "soap bar sinks", "moves to base"),
        _fresh_case("foam block", "A foam block is pressed under water and rises back to the top after release.", "What does the return to the top show?", "The foam block floats after it is released.", "Rising and staying at the top show the floating result.", "foam block floats", "rises to top"),
        _fresh_case("wet paper", "A thick paper square floats at first, then becomes soaked and drops below the surface.", "How should both moments be reported?", "The paper floats first and sinks after it becomes soaked.", "The printed positions change after water fills the paper.", "paper floats then sinks", "soaking changes position"),
        _fresh_case("bottle cap", "A closed bottle cap bobs at the top even after the jar is turned gently.", "Which conclusion fits the repeated check?", "The closed cap floats in the moving water.", "It stays at the top during each gentle turn.", "closed cap floats", "stays top repeatedly"),
        _fresh_case("shell piece", "A thick shell piece falls through the water and lands beside the glass marble.", "What simple because sentence is supported?", "The shell piece sinks because it lands at the bottom.", "Landing under the water gives a direct reason for the result.", "shell piece sinks", "lands at bottom"),
        _fresh_case("rubber eraser", "A solid rubber eraser slips below the surface and rests against the bottom edge of the bowl.", "What conclusion follows from the eraser's final position?", "The rubber eraser sinks in this test.", "Resting below the water at the bowl edge is direct sinking evidence.", "rubber eraser sinks", "rests below water"),
        _fresh_case("sealed spice lid", "The tester lowers a clean plastic spice cap horizontally onto the water. It remains at the top through three gentle taps.", "Which result is supported by the repeated spice-cap checks?", "The plastic lid floats during the repeated test.", "It stays at the surface after every gentle tap.", "plastic lid floats", "surface after three taps"),
        _fresh_case("leaf cup change", "A dry leaf cup stays on top at first, then a tear lets water in and the cup drops to the tub floor.", "How should the two leaf-cup results be reported?", "The leaf cup floats first and sinks after water enters through the tear.", "Its printed position changes from surface to floor after the leak.", "leaf cup floats then sinks", "tear changes position"),
    ],
    "laddoo_blend_wordcraft": [
        _fresh_case("classroom clue", "The sentence says, 'Our __ass has twenty desks.' The missing noun names a group of pupils.", "Which opening blend completes the noun?", "The word is class, beginning with cl.", "Both blend letters are needed and class fits the school clue.", "class begins cl", "school group clue"),
        _fresh_case("playground verb", "Children will __ay tag after lunch. The missing verb means take part in a game.", "Spell the whole action word.", "The word is play, beginning with pl.", "The pl blend and game meaning both fit.", "play begins pl", "game action clue"),
        _fresh_case("black colour", "Mira uses __ack paint for the crow's wing. The gap needs a colour word.", "What letters finish the colour?", "The word is black, beginning with bl.", "Black keeps both opening sounds and names the stated colour.", "black begins bl", "crow colour clue"),
        _fresh_case("cliff noun", "The goat stands near a steep __iff above the path. The missing noun names a high rock edge.", "Which formed word matches the place?", "The word is cliff, beginning with cl.", "Cliff uses cl and fits a steep rock edge.", "cliff begins cl", "steep rock edge"),
        _fresh_case("plate noun", "Put the sliced guava on a clean __ate. The missing object holds food.", "How is the food word completed?", "The word is plate, beginning with pl.", "Plate has the pl blend and names the serving object.", "plate begins pl", "holds food clue"),
        _fresh_case("blink verb", "The bright flash made Kavi __ink twice. The action means close and open the eyes quickly.", "Which blend builds the action word?", "The word is blink, beginning with bl.", "Blink preserves bl and matches the eye action.", "blink begins bl", "eye action clue"),
        _fresh_case("clean verb", "Please __ean the tray after the snack. The missing action means remove dirt.", "Write the complete verb.", "The word is clean, beginning with cl.", "Clean keeps cl and matches removing dirt.", "clean begins cl", "remove dirt clue"),
        _fresh_case("plane noun", "A paper __ane glides across the room. The missing noun names a flying model.", "Which spelling belongs in the sentence?", "The word is plane, beginning with pl.", "Plane uses pl and fits the flying object.", "plane begins pl", "flying model clue"),
        _fresh_case("block noun", "The child stacks one wooden __ock on another. The missing noun names a solid toy piece.", "What blend completes the toy word?", "The word is block, beginning with bl.", "Block begins with bl and fits the stacking clue.", "block begins bl", "stacking toy clue"),
        _fresh_case("clap sentence", "The audience will clap when the puppet bows. The task is to use clap in a new sentence.", "Write a sentence that keeps the applause meaning.", "We clap to thank the dancers after their show.", "The new sentence uses clap as an applause action.", "clap thanks dancers", "applause action meaning"),
        _fresh_case("plant sentence", "Plant can mean put a seed into soil. Use that meaning, not the noun meaning.", "How can plant be used as an action?", "I will plant two bean seeds in the garden bed.", "Will plant names the seed-placing action shown in the clue.", "plant bean seeds", "put into soil"),
        _fresh_case("blue sentence", "Blue is a colour word. The task asks for a complete sentence about a kite.", "Use blue so its meaning is clear.", "The blue kite rose above the yellow wall.", "Blue directly describes the kite's colour.", "blue kite rose", "describes kite colour"),
        _fresh_case("clown word", "The circus card says, 'A funny __own balances two hats.' The missing noun names the performer.", "Which opening blend completes the performer word?", "The word is clown, beginning with cl.", "Clown keeps both opening sounds and matches the circus performer clue.", "clown begins cl", "circus performer clue"),
        _fresh_case("plank word", "A short wooden __ank bridges the puddle. The missing noun means a long flat board.", "Spell the complete board word from its meaning clue.", "The word is plank, beginning with pl.", "Plank preserves pl and names the flat wooden board.", "plank begins pl", "flat board clue"),
        _fresh_case("blossom word", "One pink __ossom opens on the guava branch. The missing noun means a flower.", "What opening blend forms the flower word?", "The word is blossom, beginning with bl.", "Blossom uses bl and fits the flower opening on a branch.", "blossom begins bl", "flower branch clue"),
    ],
    "laddoo_festival_information": [
        _fresh_case("millet morning", "At a spring gathering, families cook millet porridge from the new crop and thank the farmers before sharing bowls.", "What idea joins the crop, thanks, and meal?", "The gathering celebrates new grain and the people who grew it.", "Every detail links seasonal food with shared thanks.", "celebrates new grain", "meal thanks farmers"),
        _fresh_case("recipe notebook order", "Grandmother says the bean recipe. Two cousins write it down, test the steps with her, and store the checked page for next year.", "Retell the four actions in order.", "First Grandmother says the recipe, next the cousins write it, then they test it, and finally they store the checked page.", "Speaking and writing come before testing and saving the recipe.", "say write test store", "checked before stored"),
        _fresh_case("shared oven", "Four neighbours bring different doughs to one community oven. They bake in turns and exchange a piece from each loaf.", "Which main idea covers all the actions?", "Neighbours share work and food during the celebration.", "The common oven and exchanged bread connect the details.", "neighbours share food", "oven bread exchange"),
        _fresh_case("orchard stall order", "Growers pick ripe guavas in the morning, write orchard names on cards, carry the fruit to the fair, and open the stall at noon.", "What is the orchard-to-stall order?", "First growers pick guavas, next they write the cards, then they carry the fruit, and finally they open the stall.", "Picking and labelling happen before the fruit is carried and sold.", "pick label carry open", "fruit prepared before stall"),
        _fresh_case("welcome bowl idea and order", "Hosts cook sweet rice, fill small bowls, greet visitors at the hall door, and offer each person a bowl as a welcome custom.", "State the big idea and retell the actions in order.", "The card is about welcoming visitors with food: first cook, next fill bowls, then greet, and finally offer the rice.", "Every action supports the welcome idea and follows the printed cooking-to-serving order.", "welcome with sweet rice", "cook fill greet offer"),
        _fresh_case("three kitchens", "One festival plate holds steamed cakes from the coast, flatbread from the hills, and lentils from the plain.", "What broad idea fits the whole plate?", "One celebration can share foods from several regions.", "The three named places explain the variety on one plate.", "foods from regions", "three places one plate"),
        _fresh_case("seed display order", "Children sort wheat, lentil, and sesame seeds. They label three dishes, place each seed beside its matching dish, and invite visitors to view the display.", "Which ordered retell matches the display work?", "First sort the seeds, next label the dishes, then match each seed to a dish, and finally invite visitors.", "Sorting and labels prepare the matches before visitors see them.", "sort label match invite", "prepare before visitors"),
        _fresh_case("rain meal", "After the first monsoon rain, families cook warm corn snacks and carry some to older neighbours.", "Which idea is bigger than one ingredient?", "A seasonal meal brings care and sharing to the neighbourhood.", "Rain, warm food, and giving all support that larger idea.", "seasonal sharing meal", "rain food neighbours"),
        _fresh_case("spice card order", "Pupils measure a little spice, add it to a cooked dish, write the spice name on a card, and set the card beside the bowl.", "Retell the actions without moving the label step.", "First measure the spice, next add it, then write its card, and finally place the card beside the bowl.", "The spice is measured and used before its finished dish is labelled for visitors.", "measure add write place", "spice used before label"),
        _fresh_case("community pot", "Families add measured cups of rice to one large pot. Volunteers cook it and divide the meal equally.", "What is the paragraph mainly about?", "The community combines small gifts to make a shared meal.", "Many rice cups become one dish for everyone.", "community shared meal", "small gifts one pot"),
        _fresh_case("star bread order", "A baker reads an old festival recipe, mixes the dough, shapes small stars, and bakes them for the children's table.", "What order turns the recipe into star bread?", "First read the recipe, next mix the dough, then shape the stars, and finally bake them.", "Reading and mixing prepare the dough before shaping and baking.", "read mix shape bake", "dough before bread"),
        _fresh_case("clean-up custom", "After a feast, every family washes one serving pot and returns it to the hall cupboard.", "How does the final action fit the celebration?", "Sharing the clean-up is part of caring for the community meal.", "Each family helps after everyone has eaten.", "shared clean up", "families help after meal"),
        _fresh_case("harvest cart order", "At the grain fair, children weigh millet, fill small bags, tie name cards, and load the bags onto a handcart for the hall.", "Retell the harvest-cart work in order and state its main purpose.", "First weigh millet, next fill bags, then tie cards, and finally load the cart.", "The ordered work prepares labelled grain gifts for the fair hall.", "weigh fill tie load", "prepares labelled grain gifts"),
        _fresh_case("pickle exchange", "Three families bring lemon, carrot, and bamboo-shoot pickles to one tasting table and explain how each recipe is kept in their home.", "What main idea includes all three pickle dishes?", "The tasting table shares different family food traditions.", "Three recipes and home explanations support one tradition-sharing event.", "shares family food traditions", "three recipes one table"),
        _fresh_case("corn garland sequence", "Volunteers dry corn cobs, remove the husks, tie the husks into a doorway garland, and save the kernels for the community meal.", "Give the corn preparation order and its larger festival idea.", "First dry the cobs, next remove husks, then tie the garland, and finally save kernels.", "The steps use one crop for decoration and a shared meal.", "dry remove tie save", "crop supports decoration meal"),
    ],
    "laddoo_animal_pairs": [
        _fresh_case("goat word jobs", "A farm card says, 'The buck followed the doe.' Buck and doe name adult goats.", "Which words are nouns, and which word is the verb?", "Buck and doe are animal nouns, and followed is the action verb.", "The goat words name who, while followed tells what they did.", "buck doe nouns", "followed action verb"),
        _fresh_case("pig pair", "The animal chart pairs boar with sow because both are adult pigs.", "Which sentence shows the word meanings?", "The boar rested while the sow fed her piglets.", "The chart gives one animal kind and the verbs tell two actions.", "boar sow pigs", "rested fed piglets"),
        _fresh_case("tiger word jobs", "A forest note says, 'The tiger drank, and the tigress waited.' Both names belong to one animal kind.", "Identify the nouns and action verbs.", "Tiger and tigress are nouns; drank and waited are action verbs.", "The animal names tell who, and the two verbs tell their actions.", "tiger tigress nouns", "drank waited verbs"),
        _fresh_case("fox pair", "The guide says fox for the male and vixen for the female of the same animal kind.", "What sentence keeps the pair together?", "The fox crossed the path before the vixen entered the den.", "The guide links the nouns and the sentence gives each a place in the action.", "fox vixen pair", "crossed entered den"),
        _fresh_case("goose nouns in a sentence", "At the pond, a gander and a goose swam beside their goslings. Gander and goose form an adult pair.", "Write the word jobs and one complete sentence idea.", "Gander and goose are nouns, swam is the verb, and the full sentence tells where they moved.", "The nouns name the birds, the verb gives the action, and every part forms one sentence.", "gander goose nouns", "swam verb full sentence"),
        _fresh_case("donkey word sort", "A word card gives three words from one sentence: jack, jenny, carried. Jack and jenny name donkeys.", "Sort the words into Animal nouns and Action verb.", "Animal nouns: jack and jenny. Action verb: carried.", "The two donkey names belong together, while carried tells what they did.", "jack jenny animal nouns", "carried action column"),
        _fresh_case("deer pair", "The wildlife list pairs stag with doe as adult deer words.", "Write a sentence that does not mix animal kinds.", "The stag stood at the stream while the doe moved into the trees.", "The list links both nouns to deer and the actions form a full sentence.", "stag doe deer", "stood moved trees"),
        _fresh_case("horse noun check", "The stable chart says, 'The mare walked while the foal followed.' Both animal words belong to the horse family.", "Identify the animal nouns and action verbs.", "Mare and foal are nouns; walked and followed are action verbs.", "The horse names tell who, and the verbs tell what happened.", "mare foal nouns", "walked followed verbs"),
        _fresh_case("cow young", "A dairy note pairs cow with calf because the calf is a young member of the cattle family.", "Which complete sentence fits?", "The cow called, and the calf ran across the yard.", "The meanings match one family and both parts contain actions.", "cow calf cattle", "called ran yard"),
        _fresh_case("chicken noun check", "The coop sign says, 'The hen scratched while the chick pecked.' Hen and chick belong to the chicken family.", "Which words name animals and which words name actions?", "Hen and chick are nouns; scratched and pecked are verbs.", "The nouns name the chickens, and the verbs give their two actions.", "hen chick nouns", "scratched pecked verbs"),
        _fresh_case("lion young", "A reserve card joins lioness and cub as an adult lion and a young lion.", "What sentence shows the family link?", "The lioness watched while the cub played beside a rock.", "The card supplies the animal family and the actions make the idea clear.", "lioness cub lions", "watched cub played"),
        _fresh_case("duckling noun check", "A pond poster says, 'The duck crossed the pond, and the duckling followed.' Both names belong to one bird family.", "Name the nouns and verbs in the sentence.", "Duck and duckling are nouns; crossed and followed are verbs.", "The bird names tell who, and the action words tell what they did.", "duck duckling nouns", "crossed followed verbs"),
        _fresh_case("camel family", "A desert card says, 'The camel knelt while the calf drank.' Both animal words belong to the camel family.", "Identify the animal nouns and action verbs.", "Camel and calf are nouns; knelt and drank are verbs.", "The family words name who, and the verbs tell their separate actions.", "camel calf nouns", "knelt drank verbs"),
        _fresh_case("elephant pair", "The reserve note links an elephant with its calf beside a water hole.", "Write one complete sentence that uses both related nouns.", "The elephant sprayed water while the calf stepped into the pool.", "Both nouns name one animal family and each clause has an action.", "elephant calf family", "sprayed stepped pool"),
        _fresh_case("sheep family", "A hill-farm sign says ewe for an adult sheep and lamb for a young sheep.", "Which sentence keeps the animal pair and actions clear?", "The ewe crossed the field while the lamb followed the fence.", "The two sheep nouns belong together, and crossed and followed complete the sentence.", "ewe lamb sheep", "crossed followed fence"),
    ],
}

for _level_spec in SPEC["levels"]:
    _level_spec["fresh_cases"] = FRESH_CASES[_level_spec["level_id"]]


SPEC["assessment_pairs"] = [
    _assessment_pair("reading.poetic_language", _fresh_case("cloud ladder", "A funny line says a child climbed a ladder made from clouds to fetch the morning sun.", "Explain why the cloud ladder is poetic, not real.", "The cloud ladder is an impossible playful picture.", "Clouds cannot form firm steps for a child.", "playful cloud ladder", "clouds cannot be steps"), _fresh_case("giant pea", "A menu claims one pea rolled through town and blocked every bus at once.", "What makes the pea claim an exaggeration?", "The bus-blocking pea is a comic exaggeration.", "A pea is far too small to block many buses.", "comic giant pea", "pea too small"), kind="open"),
    _assessment_pair("reading.inference_reason", _fresh_case("laughing banner", "A fair banner calls a melon 'the moon's lost little brother.' Visitors smile at the comparison.", "Why do the visitors probably smile?", "They smile because the melon is compared playfully with the moon.", "The round shape supports a funny family comparison.", "smile at moon comparison", "round playful link"), _fresh_case("drum hill", "A rhyme says a drumbeat made a hill dance. The children repeat the line with grins.", "Why are the children grinning?", "They grin because the dancing hill is a silly imagined effect.", "A real hill cannot dance to a drum.", "grin at dancing hill", "hill cannot dance"), kind="open"),
    _assessment_pair("reading.word_meaning_context", _case("circular tray", "The tray has one curved edge with no corners. The card calls it circular.", "What does circular mean in this card?", "Circular means round.", "Circular means furry.", "Circular means broken.", "The no-corner edge gives the shape meaning.", "circular means round", "no corner edge"), _case("spherical ball", "The clay piece curves evenly in every direction like a ball. The note calls it spherical.", "Which meaning fits spherical?", "Spherical means ball-shaped.", "Spherical means flat as paper.", "Spherical means full of holes.", "The direct ball comparison explains the word.", "spherical ball shaped", "curves every direction"), kind="choice"),
    _assessment_pair("vocab.attribute_ordering", _case("wooden token", "The token is small, round, red, wooden, and smooth.", "Which description puts the details in a clear order?", "It is a small round red wooden token with a smooth face.", "Smooth wooden is token a red round.", "It is a giant square cloth token.", "The sentence moves from size and shape to colour, material, and surface.", "small round red token", "shape before surface"), _case("silver plate", "The plate is broad, circular, silver, metal, and shallow.", "Choose the clearest ordered description.", "It is a broad round silver metal plate with a shallow rim.", "Shallow silver broad is plate.", "It is a narrow square paper plate.", "The object comes first, followed by useful shape and surface details.", "broad round silver plate", "object details ordered"), kind="choice"),
    _assessment_pair("reading.sentence_comprehension", _case("wax ring", "The wax ring stayed at the top of the water, but the stone bead reached the bottom.", "Which statement matches the test?", "The wax ring floated and the stone bead sank.", "Both objects sank.", "The stone bead floated above the ring.", "The two stated water positions give different results.", "ring floated bead sank", "top and bottom positions"), _case("wood chip", "A wood chip remained on the surface while a metal screw dropped to the jar floor.", "What happened to each object?", "The wood chip floated, and the screw sank.", "The screw floated above the chip.", "Both stayed out of water.", "Surface and floor are clear result clues.", "chip floated screw sank", "surface versus floor"), kind="choice"),
    _assessment_pair("writing.reason_answer", _fresh_case("orange peel", "A strip of orange peel stays on top of water for one minute.", "Write why floated is the correct result word.", "The orange peel floated because it stayed on the surface.", "Its printed position never moved below the water.", "orange peel floated", "stayed on surface"), _fresh_case("clay cube", "A clay cube moves down through the tub and rests under the water.", "Explain why sank fits this test.", "The clay cube sank because it reached the tub floor.", "The downward path and final low position show sinking.", "clay cube sank", "reached tub floor"), kind="open"),
    _assessment_pair("vocab.spelling", _case("clock gap", "The hall __ock shows nine. The missing noun tells time.", "Which spelling completes the word?", "clock", "lock", "blocke", "Clock keeps cl and matches the time clue.", "clock with cl", "tells time clue"), _case("blanket gap", "A warm __anket covers the cot. The missing noun is bedding.", "Which spelling fits?", "blanket", "lanket", "planket", "Blanket keeps bl and matches the covering clue.", "blanket with bl", "warm covering clue"), kind="choice"),
    _assessment_pair("vocab.word_formation", _fresh_case("plum use", "The letters pl complete __um, a small fruit with a stone.", "Form the word and use it in a sentence.", "The word is plum; I packed a ripe plum for lunch.", "The pl blend and fruit sentence show the right word.", "plum ripe fruit", "pl blend lunch sentence"), _fresh_case("cloth use", "The letters cl complete __oth, a piece of fabric.", "Build the word and write a matching sentence.", "The word is cloth; Renu wiped the bowl with a cloth.", "The cl blend and wiping action fit the fabric meaning.", "cloth wiping bowl", "cl blend fabric"), kind="open"),
    _assessment_pair("reading.paragraph_main_idea", _fresh_case("grain fair", "Families bring bread made from the new grain. They thank growers and share slices with every visitor.", "State the idea that covers the whole card.", "The fair celebrates new grain through thanks and shared bread.", "Growers, grain, and sharing all support one celebration idea.", "celebrates new grain", "thanks shared bread"), _fresh_case("neighbour soup", "Each home adds one vegetable to a large soup pot. At noon, everyone eats from the finished meal.", "What is the whole card mostly about?", "Neighbours combine small gifts to make one shared meal.", "Many vegetables and one pot show community sharing.", "neighbours make shared meal", "vegetables one pot"), kind="open"),
    _assessment_pair("grammar.noun_verb_adjective", _case("rabbit word jobs", "The buck and doe hopped beside the burrow. Buck and doe are adult rabbit words.", "Which choice names the nouns and verb?", "Buck and doe are nouns, and hopped is the verb.", "Hopped is a rabbit noun.", "Burrow is the action done by the rabbits.", "The animal words name who, and hopped tells the action.", "buck doe nouns", "hopped action verb"), _case("swan word jobs", "The swan and cygnet crossed the lake. The card links an adult bird with its young.", "Which words are nouns, and which word is the verb?", "Swan and cygnet are nouns, and crossed is the verb.", "Crossed is the young bird noun.", "Lake is the action completed by the birds.", "The bird words name who, and crossed tells what they did.", "swan cygnet nouns", "crossed action verb"), kind="choice"),
    _assessment_pair("writing.complete_sentence", _fresh_case("rabbit pair", "The card pairs buck and doe as adult rabbit words.", "Write one full sentence using both animal nouns.", "The buck ate a leaf while the doe rested near the burrow.", "Both nouns name rabbits and each part has an action.", "buck doe rabbits", "ate rested burrow"), _fresh_case("dog family", "The card links dog and puppy as an adult animal and its young.", "Use both related words in a complete sentence.", "The dog waited by the door while the puppy carried a sock.", "Both nouns belong to the dog family and each clause has an action.", "dog puppy family", "waited carried sock"), kind="open", interaction_type="paragraph_text"),
    _assessment_pair("reading.inference_reason", _fresh_case("empty serving bowl", "After the community meal, the largest serving bowl is empty and several guests ask for the recipe.", "What can you infer about the dish?", "The dish was probably enjoyed by many guests.", "An empty bowl and recipe requests both suggest people liked it.", "guests enjoyed dish", "empty bowl recipe requests"), _fresh_case("saved seed card", "A child places the festival seed card in a labelled folder for next year.", "Why does the child probably save the card?", "The child wants to use the seed information again next year.", "The label and future date show planned reuse.", "save for next year", "label shows reuse"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("foil cup", "A shallow foil cup remains above water while an equal foil lump drops down.", "Explain the different results using the card.", "The cup floated while the tight lump sank in this test.", "Equal material but different shapes produced the printed positions.", "cup floated lump sank", "same foil different shape"), _fresh_case("soaked leaf", "A leaf floats when dry, then fills with water and falls below the surface.", "Write a reason for the changed result.", "The leaf sank after soaking because water changed its condition.", "The card shows floating before soaking and sinking afterward.", "soaked leaf sank", "condition changed after water"), kind="open"),
    _assessment_pair("reading.event_sequence", _fresh_case("food card order", "The card says: growers cut ripe grain, a mill makes flour, a baker cooks bread, and neighbours share it.", "Retell the four events in order.", "First grain is cut, next flour is made, then bread is cooked, and finally it is shared.", "Each action supplies what the next action needs.", "cut mill bake share", "grain before bread"), _fresh_case("festival pot order", "The note says: wash the pot, add cooked beans, stir in herbs, and carry the covered pot to the table.", "Write the stated order without adding a step.", "First wash the pot, next add beans, then stir herbs, and finally carry it covered.", "Cleaning and filling happen before the finished pot reaches the table.", "wash add stir carry", "pot prepared before table"), kind="open"),
]


_SEMANTIC_OPTION_REPLACEMENTS = {'The coin disappears before touching water.': 'The coin stays near the surface '
                                               'because it is small.',
 'The test has no result because the cork is small.': 'The cork stays on top only '
                                                      'because the bowl is clear.'}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch07:assessment:07': {'accepted_answers': ['clean'],
                               'options': ['lean', 'cleen', 'clean'],
                               'passage': 'The cook wipes the table until it is __ean. '
                                          'The missing adjective means not dirty.',
                               'prompt': 'Which spelling completes the word?'}}


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

MANIFEST = build_manifest(SPEC)

_apply_semantic_copy_corrections(MANIFEST["levels"])
_apply_semantic_copy_corrections(
    MANIFEST["chapter_assessment"]["items"]
)
_apply_semantic_assessment_overrides(MANIFEST)
