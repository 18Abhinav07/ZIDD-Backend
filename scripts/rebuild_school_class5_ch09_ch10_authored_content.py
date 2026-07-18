#!/usr/bin/env python3
"""Apply the bounded Class 5 Chapters 9-10 authored-content revision."""

from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_5"
)
CHAPTER_IDS = ("eng_c5_ch09", "eng_c5_ch10")
CONTENT_VERSION = "2026-07-16.4"
STAGE_LABEL = re.compile(
    r"\b(?:opening|worked example|"
    r"(?:first|second|third|fourth) (?:guided example|solo practice|new situation|recap task)|"
    r"bridge hint|focused practice|(?:first|second|third) repair) note\b",
    re.IGNORECASE,
)
SUBSTANTIVE_MARKERS = (
    "a learner kept",
    "in an original reflective verse",
    "a class studied",
    "context clue card:",
    "editing board:",
    "language repair card:",
    "fact card:",
    "planning notes:",
    "bounded fact card:",
    "production process notes:",
    "design record:",
    "community impact note:",
    "semantic association card:",
    "unedited line:",
    "two past events:",
    "procedure fact packet:",
    "recount planner:",
    "bounded inquiry packet:",
)
CLAIM_ALIAS_OVERRIDES = {
    "eng_c5_ch09_work_realities-transfer-3": {
        "demanding_reality": [
            "standing beside noisy traffic through hot afternoons"
        ],
    },
    "eng_c5_ch09_work_realities-transfer-4": {
        "demanding_reality": ["early start and need to lift heavy cans"],
    },
    "eng_c5_ch09_work_realities-review-4": {
        "demanding_reality": [
            "early shift and careful work around unpleasant waste"
        ],
    },
    "eng_c5_ch10_tradition_innovation-transfer-3": {
        "changed_feature": ["removable liner"],
        "outcome": ["leaves the woven outside recognisable"],
    },
    "eng_c5_ch10_tradition_innovation-transfer-4": {
        "changed_feature": ["washable colour"],
        "outcome": ["motif stayed visible after washing"],
    },
    "eng_c5_ch10_tradition_innovation-review-3": {
        "outcome": ["stood steadily in the test"],
    },
    "eng_c5_ch10_tradition_innovation-review-4": {
        "changed_feature": ["detachable backing"],
        "outcome": ["families can wash the backing separately"],
    },
}
CONTEXT_REFRAMES = {
    "eng_c5_ch09_workday_sequence-independent-1": (
        "A clinic coordinator must turn three duty records into a morning-to-night schedule."
    ),
    "eng_c5_ch09_workday_sequence-review-2": (
        "A railway-station display needs a final timeline before the evening board is printed."
    ),
    "eng_c5_ch09_perceived_freedom-review-1": (
        "For a reading journal, a pupil revisits one admired job and checks what the later line changes."
    ),
    "eng_c5_ch09_work_realities-review-1": (
        "The class equality board needs one balanced caption about contribution and effort."
    ),
    "eng_c5_ch09_work_realities-review-2": (
        "A community newsletter editor checks whether a short job profile hides its hardest condition."
    ),
    "eng_c5_ch09_words_and_tools-review-1": (
        "A market glossary editor must confirm one meaning from the surrounding action."
    ),
    "eng_c5_ch09_agreement_repair-review-1": (
        "The school office is proofreading a short instruction before it reaches every class."
    ),
    "eng_c5_ch09_wh_questions-review-1": (
        "A class quiz writer checks whether one question can be answered from the card alone."
    ),
    "eng_c5_ch09_vocation_paragraph-review-1": (
        "The wall magazine has room for one tightly organised work profile with no unrelated detail."
    ),
    "eng_c5_ch09_vocation_fact_report-review-1": (
        "An exhibition label is being checked for invented claims before visitors arrive."
    ),
    "eng_c5_ch10_production_sequence-review-1": (
        "A craft manual editor checks whether the preparation, making, and finishing stages can really work."
    ),
    "eng_c5_ch10_tradition_innovation-review-1": (
        "A curator needs a caption that separates what makers retained from what they changed."
    ),
    "eng_c5_ch10_tradition_innovation-review-2": (
        "A product team checks whether its improvement still leaves the craft identity visible."
    ),
    "eng_c5_ch10_community_effects-review-1": (
        "A local newspaper needs a cause-and-effect caption rather than a loose list of jobs."
    ),
    "eng_c5_ch10_community_effects-review-2": (
        "A cooperative meeting traces which workers benefited directly and which supported them."
    ),
    "eng_c5_ch10_semantic_associations-review-1": (
        "A dictionary club checks whether a word pair shares a real use, place, or action."
    ),
    "eng_c5_ch10_punctuation_editor-review-1": (
        "A festival programme editor prepares one final line for public display."
    ),
    "eng_c5_ch10_past_perfect_sequence-review-1": (
        "A learner checks a two-event memory by ordering meaning before choosing tense."
    ),
    "eng_c5_ch10_procedure_writer-review-1": (
        "A younger class will follow this procedure, so no action or safety condition can be missing."
    ),
    "eng_c5_ch10_festival_recount-review-1": (
        "A class anthology editor checks that one memory has order, reflection, and closure."
    ),
    "eng_c5_ch10_craft_and_savings-review-1": (
        "A savings club studies one small record and separates its proven idea from wider banking topics."
    ),
}

SUPPORT_CUES = {
    "eng_c5_ch09_workday_sequence-bridge": "Start clue: 11:40 before noon must come before both afternoon and night.",
    "eng_c5_ch09_workday_sequence-masterclass": "Tempting error: one learner sorted the jobs alphabetically instead of reading the clock clues.",
    "eng_c5_ch09_workday_sequence-revision-level-1": "Repair cue: underline the earliest printed time and place that worker first.",
    "eng_c5_ch09_workday_sequence-revision-level-2": "Repair cue: compare noon, afternoon, and night before drawing the arrows.",
    "eng_c5_ch09_workday_sequence-revision-level-3": "Final check: each worker and each printed time should appear once.",
    "eng_c5_ch09_perceived_freedom-masterclass": "Tempting error: an outdoor setting is mistaken for proof that the worker has no duties.",
    "eng_c5_ch09_perceived_freedom-revision-level-1": "Repair cue: circle the image the child admires, then box the later responsibility.",
    "eng_c5_ch09_perceived_freedom-revision-level-2": "Repair cue: begin with the child's viewpoint, not an adult judgement of the job.",
    "eng_c5_ch09_perceived_freedom-revision-level-3": "Final check: the answer must hold admiration and responsibility together.",
    "eng_c5_ch09_work_realities-masterclass": "Tempting error: the appealing contribution is treated as the whole story of the work.",
    "eng_c5_ch09_work_realities-revision-level-1": "Repair cue: name the service first, then the difficult condition.",
    "eng_c5_ch09_work_realities-revision-level-2": "Repair cue: use one detail from each side of the vocation card.",
    "eng_c5_ch09_work_realities-revision-level-3": "Final check: difficulty should not erase dignity, and praise should not erase effort.",
    "eng_c5_ch09_words_and_tools-bridge": "Start clue: identify what the worker does with the target word in this sentence.",
    "eng_c5_ch09_agreement_repair-bridge": "Start clue: cover the nearby noun and find the head word of the full subject.",
    "eng_c5_ch09_tense_and_adverbs-bridge": "Start clue: ask whether the marked expression tells when, where, how, or how often.",
    "eng_c5_ch09_wh_questions-bridge": "Start clue: choose the answer on the fact card before forming the question.",
    "eng_c5_ch09_vocation_paragraph-revision-level-1": "Repair cue: write one topic sentence that can control every later detail.",
    "eng_c5_ch09_vocation_paragraph-revision-level-2": "Repair cue: keep two details that explain the same central idea.",
    "eng_c5_ch09_vocation_paragraph-revision-level-3": "Final check: remove any sentence that the closing idea cannot connect to.",
    "eng_c5_ch09_vocation_fact_report-bridge": "Start clue: select only two actions printed on the source card.",
    "eng_c5_ch09_vocation_fact_report-masterclass": "Tempting error: a likely fact about the job is added even though the card never states it.",
    "eng_c5_ch09_vocation_fact_report-revision-level-1": "Repair cue: point to the exact card phrase behind the first reported fact.",
    "eng_c5_ch09_vocation_fact_report-revision-level-2": "Repair cue: attribute the facts before adding the source boundary.",
    "eng_c5_ch09_vocation_fact_report-revision-level-3": "Final check: every claim must be traceable to this card, not general knowledge.",
    "eng_c5_ch10_production_sequence-bridge": "Start clue: identify the prepared material before considering any making step.",
    "eng_c5_ch10_production_sequence-masterclass": "Tempting error: a finishing step is placed early because it appears first in the shuffled note.",
    "eng_c5_ch10_production_sequence-revision-level-1": "Repair cue: ask what must already exist before each action can happen.",
    "eng_c5_ch10_production_sequence-revision-level-2": "Repair cue: separate preparation, making, and finishing into three columns.",
    "eng_c5_ch10_production_sequence-revision-level-3": "Final check: test every neighbouring pair for a workable dependency.",
    "eng_c5_ch10_tradition_innovation-masterclass": "Tempting error: every changed feature is called an improvement without checking the stated outcome.",
    "eng_c5_ch10_tradition_innovation-revision-level-1": "Repair cue: mark retained, changed, and outcome in three different places.",
    "eng_c5_ch10_tradition_innovation-revision-level-2": "Repair cue: explain why the object remains recognisable after the change.",
    "eng_c5_ch10_tradition_innovation-revision-level-3": "Final check: do not invent a motive beyond the design record.",
    "eng_c5_ch10_community_effects-masterclass": "Tempting error: direct and supporting work are listed without showing the cause between them.",
    "eng_c5_ch10_community_effects-revision-level-1": "Repair cue: begin with the event that changed demand.",
    "eng_c5_ch10_community_effects-revision-level-2": "Repair cue: label the first worker effect direct and the next service effect supporting.",
    "eng_c5_ch10_community_effects-revision-level-3": "Final check: connect every effect back to the original change.",
    "eng_c5_ch10_semantic_associations-bridge": "Start clue: complete the sentence 'This word is used for...' before judging the pair.",
    "eng_c5_ch10_punctuation_editor-bridge": "Start clue: decide whether the line is a statement, question, list, or quotation.",
    "eng_c5_ch10_past_perfect_sequence-bridge": "Start clue: number the two events by meaning before choosing either verb form.",
    "eng_c5_ch10_procedure_writer-masterclass": "Tempting error: polished sequence words hide one missing action and one missing safety condition.",
    "eng_c5_ch10_procedure_writer-revision-level-1": "Repair cue: act out the four steps mentally and stop where the process breaks.",
    "eng_c5_ch10_procedure_writer-revision-level-2": "Repair cue: pair each sequence word with one complete action.",
    "eng_c5_ch10_procedure_writer-revision-level-3": "Final check: a younger learner should know both what to do and how to do it safely.",
    "eng_c5_ch10_festival_recount-masterclass": "Tempting error: an event list is mistaken for a recount even though it has no reflection.",
    "eng_c5_ch10_festival_recount-revision-level-1": "Repair cue: anchor the opening in one named gathering.",
    "eng_c5_ch10_festival_recount-revision-level-2": "Repair cue: use time links to move through the three supplied moments.",
    "eng_c5_ch10_festival_recount-revision-level-3": "Final check: the closing thought should explain why the memory mattered.",
}

PROMPT_CUES = {
    "eng_c5_ch09_workday_sequence": (
        "Check the earliest time first.",
        "Compare the middle and final times before ordering.",
        "Use all three clock clues in the explanation.",
        "Confirm that no worker appears twice.",
    ),
    "eng_c5_ch09_perceived_freedom": (
        "Name the image the child admires.",
        "Contrast that image with the later duty.",
        "Keep the viewpoint separate from an objective job description.",
        "Show why admiration does not erase responsibility.",
    ),
    "eng_c5_ch09_work_realities": (
        "State the worker's contribution first.",
        "Pair the useful service with its difficult condition.",
        "Explain why effort does not reduce the work's dignity.",
        "Check that neither side of the vocation card is missing.",
    ),
    "eng_c5_ch09_words_and_tools": (
        "Substitute the meaning back into the sentence.",
        "Point to the action that reveals the tool or word.",
        "Reject a related meaning that does not fit this context.",
        "Use the smallest clue that proves the meaning.",
    ),
    "eng_c5_ch09_agreement_repair": (
        "Find the head word of the complete subject.",
        "Ignore the nearby noun until the subject is clear.",
        "Read the repaired sentence aloud to check the verb.",
        "Explain why singular or plural controls the form.",
    ),
    "eng_c5_ch09_tense_and_adverbs": (
        "Underline the expression that controls time or manner.",
        "Test the complete sentence, not the verb by itself.",
        "Name whether the clue tells when, where, how, or how often.",
        "Check that the explanation matches the chosen form.",
    ),
    "eng_c5_ch09_wh_questions": (
        "Choose the supported answer before forming the question.",
        "Check the helping verb and word order.",
        "Match the WH word to the type of fact requested.",
        "End with a question mark and verify the answer on the card.",
    ),
    "eng_c5_ch09_vocation_paragraph": (
        "Let one topic sentence control the paragraph.",
        "Connect both details to the same central idea.",
        "Use the closing sentence to explain why the work matters.",
        "Remove any detail that cannot support the topic.",
    ),
    "eng_c5_ch09_vocation_fact_report": (
        "Point to the source phrase behind the first fact.",
        "Choose a second fact that adds new information.",
        "Attribute the card before stating its boundary.",
        "Delete any likely detail that the source does not supply.",
    ),
    "eng_c5_ch10_production_sequence": (
        "Identify the prepared material before the making step.",
        "Test whether each action can happen before the next.",
        "Separate preparation, making, and finishing.",
        "Check the dependency that fixes the middle order.",
    ),
    "eng_c5_ch10_tradition_innovation": (
        "Mark the retained feature first.",
        "Name the changed feature without calling it automatically better.",
        "Connect both design clues to the stated outcome.",
        "Avoid inventing a motive beyond the record.",
    ),
    "eng_c5_ch10_community_effects": (
        "Begin with the event that changed demand.",
        "Separate the direct worker effect from supporting work.",
        "Use cause words to connect the chain.",
        "Trace both effects back to the original change.",
    ),
    "eng_c5_ch10_semantic_associations": (
        "Name the concrete relation between the words.",
        "Decide whether the link is use, place, action, feeling, or idea.",
        "Explain the relation without calling the words synonyms.",
        "Test the pair in a short factual sentence.",
    ),
    "eng_c5_ch10_punctuation_editor": (
        "Decide what kind of sentence the line is.",
        "Mark proper names and sentence beginnings first.",
        "Explain the job of one punctuation mark.",
        "Read the corrected line once for meaning and once for marks.",
    ),
    "eng_c5_ch10_past_perfect_sequence": (
        "Number the two events by meaning first.",
        "Apply had plus past participle only to the earlier completed event.",
        "Keep the later event in simple past.",
        "Check meaning rather than clause position.",
    ),
    "eng_c5_ch10_procedure_writer": (
        "State the purpose before the first action.",
        "Place one complete action after each sequence word.",
        "Include the supplied safety or quality condition.",
        "Mentally follow the steps to find any missing action.",
    ),
    "eng_c5_ch10_festival_recount": (
        "Anchor the opening in one named gathering.",
        "Use time links to order the supplied moments.",
        "Add a reflection that grows from an event detail.",
        "Close by explaining why the memory mattered.",
    ),
    "eng_c5_ch10_craft_and_savings": (
        "Attribute the exact packet before reporting the fact.",
        "Separate the proven idea from wider background knowledge.",
        "Use the recorded number or place as evidence.",
        "State one limit on what the small example proves.",
    ),
}

REPEATED_INDEPENDENT_PROMPT = (
    "Make the evidence visible without relying on options."
)

PHASE_PROMPT_ACTIONS = {
    "guided_variants": "Show the clue used while making the choice.",
    "independent_variants": "",
    "transfer_variants": "Explain how the reasoning works in this new setting.",
    "review_variants": "State the final check that confirms the answer.",
}


def _all_activities(manifest: dict):
    for level in manifest["levels"]:
        yield level["connect"]
        yield level["co_construct"]
        for pool_name in (
            "guided_variants",
            "independent_variants",
            "transfer_variants",
            "review_variants",
        ):
            yield from level[pool_name]
        yield from level["support_checks"].values()
    yield from manifest["chapter_assessment"]["items"]


def _activity_index(manifest: dict) -> dict[str, dict]:
    return {
        activity["activity_id"]: activity
        for activity in _all_activities(manifest)
        if activity.get("activity_id")
    }


def _set_selected(
    activities: dict[str, dict],
    activity_id: str,
    *,
    passage: str,
    options: list[str],
    answer: str,
    prompt: str | None = None,
) -> None:
    activity = activities[activity_id]
    assert activity["kind"] == "selected_option"
    assert len(options) == 4 and answer in options
    activity["passage"] = passage
    activity["options"] = options
    activity["accepted_answers"] = [answer]
    if prompt is not None:
        activity["prompt"] = prompt


def _set_open(
    activities: dict[str, dict],
    activity_id: str,
    *,
    passage: str,
    model_answer: str,
    core_aliases: list[str],
    support_aliases: list[str],
    prompt: str | None = None,
) -> None:
    activity = activities[activity_id]
    assert activity["kind"] == "open_response"
    slots = {slot["id"]: slot for slot in activity["concept_slots"]}
    if set(slots) != {"core", "support"}:
        if "work_realities" in activity_id:
            descriptions = (
                "Presents a balanced or dignity-based claim about the vocation.",
                "Supports the claim with the stated contribution and demanding reality.",
            )
        elif "tradition_innovation" in activity_id:
            descriptions = (
                "Explains or compares the relationship between retained tradition and purposeful innovation.",
                "Uses both design clues and the stated outcome rather than inventing a motive.",
            )
        else:
            raise AssertionError(f"unexpected_authored_claim_shape:{activity_id}")
        activity["rubric_criteria"] = [
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.7,
            }
            for slot_id, description in zip(
                ("core", "support"), descriptions, strict=True
            )
        ]
        activity["concept_slots"] = [
            {"id": slot_id, "description": description, "any_of": ["pending"]}
            for slot_id, description in zip(
                ("core", "support"), descriptions, strict=True
            )
        ]
        slots = {slot["id"]: slot for slot in activity["concept_slots"]}
    assert set(slots) == {"core", "support"}
    activity["passage"] = passage
    activity["model_answer"] = model_answer
    slots["core"]["any_of"] = core_aliases
    slots["support"]["any_of"] = support_aliases
    activity["relevance_terms"] = [*core_aliases, *support_aliases]
    if prompt is not None:
        activity["prompt"] = prompt


def _replace_claim_slots(
    activity: dict,
    claims: list[tuple[str, str, list[str]]],
) -> None:
    alias_overrides = CLAIM_ALIAS_OVERRIDES.get(activity["activity_id"], {})
    claims = [
        (
            claim_id,
            description,
            alias_overrides.get(claim_id, aliases),
        )
        for claim_id, description, aliases in claims
    ]
    min_quality = max(
        float(criterion.get("min_quality", 0.7))
        for criterion in activity["rubric_criteria"]
    )
    activity["rubric_criteria"] = [
        {
            "id": claim_id,
            "description": description,
            "required": True,
            "min_quality": min_quality,
        }
        for claim_id, description, _aliases in claims
    ]
    activity["concept_slots"] = [
        {
            "id": claim_id,
            "description": description,
            "any_of": aliases,
        }
        for claim_id, description, aliases in claims
    ]
    activity["relevance_terms"] = [
        alias for _claim_id, _description, aliases in claims for alias in aliases
    ]
    activity.pop("ordered_concept_slot_ids", None)


def _tighten_composite_claims(manifest: dict) -> None:
    """Require the visible facts, not generic labels for composite answers."""

    for activity in _all_activities(manifest):
        if activity.get("kind") != "open_response":
            continue
        slots = {slot["id"]: slot for slot in activity["concept_slots"]}
        alias_overrides = CLAIM_ALIAS_OVERRIDES.get(activity["activity_id"], {})
        if alias_overrides and set(slots) != {"core", "support"}:
            for slot_id, aliases in alias_overrides.items():
                slots[slot_id]["any_of"] = aliases
            activity["relevance_terms"] = [
                alias
                for slot in activity["concept_slots"]
                for alias in slot["any_of"]
            ]
            continue
        if set(slots) != {"core", "support"}:
            continue

        core = slots["core"]
        support = slots["support"]
        core_aliases = list(core["any_of"])
        support_aliases = list(support["any_of"])

        if core["description"].startswith(
            "Presents a balanced or dignity-based claim"
        ):
            if len(core_aliases) == len(support_aliases) == 1:
                contribution_aliases = core_aliases
                demanding_aliases = support_aliases
            elif core_aliases[0] == "central contribution":
                contribution_aliases = [core_aliases[1]]
                demanding_aliases = [support_aliases[-1]]
            elif core_aliases[0] == "appealing":
                contribution_aliases = [core_aliases[1]]
                demanding_aliases = [core_aliases[3]]
            elif len(support_aliases) >= 3:
                contribution_aliases = [support_aliases[0]]
                demanding_aliases = support_aliases[1:]
            else:
                raise AssertionError(
                    "unmapped_work_reality_claims:"
                    f"{activity['activity_id']}"
                )
            _replace_claim_slots(
                activity,
                [
                    (
                        "contribution",
                        "Names the concrete contribution stated in the vocation card.",
                        contribution_aliases,
                    ),
                    (
                        "demanding_reality",
                        "Names a demanding reality stated in the vocation card.",
                        demanding_aliases,
                    ),
                ],
            )
            continue

        if not core["description"].startswith(
            "Explains or compares the relationship between retained tradition"
        ):
            continue
        if len(core_aliases) == len(support_aliases) == 1:
            _replace_claim_slots(
                activity,
                [
                    (
                        "design_change",
                        "Names both the retained and changed design features.",
                        core_aliases,
                    ),
                    (
                        "outcome",
                        "States the resulting effect shown in the design record.",
                        support_aliases,
                    ),
                ],
            )
            continue

        if support_aliases == ["retained", "changed", "stated outcome"]:
            facts = core_aliases
        elif len(support_aliases) == 3:
            facts = support_aliases
        else:
            raise AssertionError(
                "unmapped_tradition_innovation_claims:"
                f"{activity['activity_id']}"
            )
        assert len(facts) == 3, activity["activity_id"]
        _replace_claim_slots(
            activity,
            [
                (
                    "retained_feature",
                    "Names the retained traditional feature in the design record.",
                    [facts[0]],
                ),
                (
                    "changed_feature",
                    "Names the changed or newly added feature in the design record.",
                    [facts[1]],
                ),
                (
                    "outcome",
                    "States the resulting effect shown in the design record.",
                    [facts[2]],
                ),
            ],
        )


def _clean_stage_copy(manifest: dict) -> None:
    transfer_instruction = (
        "Use only the passage details, explain your thinking, and check that "
        "every part of the question is answered."
    )
    review_instruction = (
        "Use only the passage details. After writing, check that your answer "
        "is complete and clear."
    )

    for activity in _all_activities(manifest):
        for field_name in ("teaching_block", "passage", "prompt"):
            text = activity.get(field_name)
            if not text:
                continue
            text = text.replace(
                "Use the evidence in the who controls the verb?",
                "Use the sentence evidence to identify which subject controls the verb.",
            )
            text = text.replace(
                "Work from the supplied evidence, test each required claim, "
                "and check the response before submitting.",
                transfer_instruction,
            )
            text = text.replace(
                "Solve from the supplied evidence, then check each rubric "
                "claim before submitting the recap.",
                review_instruction,
            )
            text = text.replace(
                "Reduce the task to one decisive clue before rebuilding the "
                "complete response.",
                "Start with the clearest clue. Use it to build one short "
                "answer before adding the rest.",
            )
            text = text.replace(
                "Map the misconception explicitly, compare it with the "
                "evidence, and repair the reasoning.",
                "Compare the tempting answer with the passage. Explain the "
                "mistake, then repair it with the strongest clue.",
            )

            lowered = text.casefold()
            marker_positions = [
                position
                for marker in SUBSTANTIVE_MARKERS
                if (position := lowered.find(marker)) >= 0
            ]
            if field_name == "passage" and marker_positions:
                text = text[min(marker_positions) :]
            elif STAGE_LABEL.search(text):
                sentences = re.split(r"(?<=[.!?])\s+", text)
                text = " ".join(
                    sentence
                    for sentence in sentences
                    if not STAGE_LABEL.search(sentence)
                )
            if (
                field_name == "prompt"
                and activity.get("kind") == "open_response"
                and any(
                    phase_marker in activity.get("activity_id", "")
                    for phase_marker in ("-transfer-", "-review-")
                )
                and not any(
                    marker in text.casefold()
                    for marker in (
                        "evidence",
                        "passage",
                        "note",
                        "packet",
                        "text",
                        "sentence",
                        "facts",
                        "details",
                    )
                )
            ):
                text = f"{text} Use the details in the passage."
            activity[field_name] = text.strip()


def _apply_contextual_depth(manifest: dict) -> None:
    activities = _activity_index(manifest)
    for activity_id, context in CONTEXT_REFRAMES.items():
        activity = activities.get(activity_id)
        if activity is None:
            continue
        passage = activity["passage"]
        if not passage.startswith(context):
            activity["passage"] = f"{context} {passage}"

    for activity_id, cue in SUPPORT_CUES.items():
        activity = activities.get(activity_id)
        if activity is None:
            continue
        passage = activity["passage"]
        if not passage.startswith(cue):
            activity["passage"] = f"{cue} {passage}"

    for level in manifest["levels"]:
        level_id = level["level_id"]
        cues = PROMPT_CUES[level_id]
        co_construct = level["co_construct"]
        co_action = (
            "Work through one clue and test it against every possible response."
        )
        if not co_construct["prompt"].endswith(co_action):
            co_construct["prompt"] = f"{co_construct['prompt']} {co_action}"

        for pool_name, phase_action in PHASE_PROMPT_ACTIONS.items():
            pool = level[pool_name]
            assert len(pool) == len(cues) == 4
            for activity, cue in zip(pool, cues, strict=True):
                if pool_name == "independent_variants":
                    activity["prompt"] = " ".join(
                        activity["prompt"]
                        .replace(REPEATED_INDEPENDENT_PROMPT, "")
                        .split()
                    )
                addition = " ".join(
                    part for part in (phase_action, cue) if part
                )
                if not activity["prompt"].endswith(addition):
                    activity["prompt"] = f"{activity['prompt']} {addition}"


def _author_chapter_9(manifest: dict) -> None:
    activities = _activity_index(manifest)

    _set_selected(
        activities,
        "eng_c5_ch09_workday_sequence-guided-1-depth-3",
        passage=(
            "A learner kept a work diary: at 6:45 in the morning, a newspaper "
            "seller bundled papers; at 10:30 before noon, a school cook "
            "prepared lunch; at 3:20 in the afternoon, a tailor closed the shop."
        ),
        options=[
            "school cook -> newspaper seller -> tailor",
            "newspaper seller -> school cook -> tailor",
            "tailor -> school cook -> newspaper seller",
            "newspaper seller -> tailor -> school cook",
        ],
        answer="newspaper seller -> school cook -> tailor",
    )
    _set_selected(
        activities,
        "eng_c5_ch09_workday_sequence-guided-2-depth-4",
        passage=(
            "A learner kept a work diary: at 6:30 in the morning, a bus cleaner "
            "checked the seats; at 1:10 in the afternoon, a librarian shelved "
            "returned books; at 7:45 in the evening, a pharmacist locked the store."
        ),
        options=[
            "pharmacist -> librarian -> bus cleaner",
            "librarian -> bus cleaner -> pharmacist",
            "bus cleaner -> pharmacist -> librarian",
            "bus cleaner -> librarian -> pharmacist",
        ],
        answer="bus cleaner -> librarian -> pharmacist",
    )
    _set_open(
        activities,
        "eng_c5_ch09_workday_sequence-independent-1-depth-3",
        passage=(
            "A learner kept a work diary: at 6:50 in the morning, a tea seller "
            "heated water; at 12:15 after noon, a courier collected parcels; "
            "at 8:10 at night, a nurse began the night shift."
        ),
        model_answer=(
            "The time sequence is tea seller -> courier -> nurse. The clues move "
            "from 6:50 in the morning to 12:15 after noon and finally 8:10 at night."
        ),
        core_aliases=["tea seller -> courier -> nurse"],
        support_aliases=[
            "from 6:50 in the morning to 12:15 after noon and finally 8:10 at night"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_workday_sequence-independent-2-depth-4",
        passage=(
            "A learner kept a work diary: at 5:30 in the morning, a baker mixed "
            "dough; at 1:25 in the afternoon, an electrician tested a switch; "
            "at 7:30 in the evening, a cinema usher checked the aisle."
        ),
        model_answer=(
            "The time sequence is baker -> electrician -> cinema usher. The clues "
            "move from 5:30 in the morning to 1:25 in the afternoon and finally "
            "7:30 in the evening."
        ),
        core_aliases=["baker -> electrician -> cinema usher"],
        support_aliases=[
            "from 5:30 in the morning to 1:25 in the afternoon and finally 7:30 in the evening"
        ],
    )

    _set_open(
        activities,
        "eng_c5_ch09_perceived_freedom-guided-1-depth-3",
        passage=(
            "In an original reflective verse, a child admires a mobile-library "
            "driver who visits a different village each day. A later line says "
            "the driver sorts returned books and carries heavy boxes after every stop."
        ),
        model_answer=(
            "The child imagines freedom because the mobile-library driver travels "
            "between villages. The later clue shows responsibility because the "
            "driver sorts returned books and carries heavy boxes after every stop."
        ),
        core_aliases=["the mobile-library driver travels between villages"],
        support_aliases=[
            "sorts returned books and carries heavy boxes after every stop"
        ],
    )
    _set_selected(
        activities,
        "eng_c5_ch09_perceived_freedom-guided-2-depth-4",
        passage=(
            "In an original reflective verse, a child admires a ferry helper who "
            "works beside the wide river. A later line says the helper checks ropes "
            "and life jackets before passengers board."
        ),
        options=[
            "The job is free of duties because it happens beside a river.",
            "The child admires the riverside work, while the safety checks show responsibility.",
            "The helper only watches the water and never prepares the ferry.",
            "The later clue proves that the child dislikes all outdoor work.",
        ],
        answer=(
            "The child admires the riverside work, while the safety checks show responsibility."
        ),
    )
    _set_open(
        activities,
        "eng_c5_ch09_perceived_freedom-independent-1-depth-3",
        passage=(
            "In an original reflective verse, a child admires a street photographer "
            "who chooses new viewpoints around the town. A later line says the "
            "photographer asks permission and protects the camera in sudden rain."
        ),
        model_answer=(
            "The child imagines freedom because the street photographer chooses new "
            "viewpoints. The later clue shows responsibility because the photographer "
            "asks permission and protects the camera in sudden rain."
        ),
        core_aliases=["the street photographer chooses new viewpoints"],
        support_aliases=[
            "asks permission and protects the camera in sudden rain"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_perceived_freedom-independent-2-depth-4",
        passage=(
            "In an original reflective verse, a child admires a flower seller who "
            "works among bright colours. A later line says the seller lifts heavy "
            "baskets and reaches the market before dawn."
        ),
        model_answer=(
            "The child imagines freedom because the flower seller works among bright "
            "colours. The later clue shows responsibility because the seller lifts "
            "heavy baskets and reaches the market before dawn."
        ),
        core_aliases=["the flower seller works among bright colours"],
        support_aliases=[
            "lifts heavy baskets and reaches the market before dawn"
        ],
    )

    _set_open(
        activities,
        "eng_c5_ch09_work_realities-guided-1-depth-3",
        passage=(
            "A class studied a vocation card. Contribution: a crossing guard guides "
            "children across a busy road. Demanding reality: the guard stands in heat "
            "and traffic noise while staying alert."
        ),
        model_answer=(
            "The crossing guard contributes by guiding children across a busy road. "
            "A fair view also includes the demanding work of standing in heat and "
            "traffic noise while staying alert."
        ),
        core_aliases=["guiding children across a busy road"],
        support_aliases=["standing in heat and traffic noise while staying alert"],
    )
    _set_selected(
        activities,
        "eng_c5_ch09_work_realities-guided-2-depth-4",
        passage=(
            "A class studied a vocation card. Contribution: a water-tank cleaner "
            "helps keep stored water safe. Demanding reality: the worker enters wet, "
            "cramped spaces and must use protective gear."
        ),
        options=[
            "The work matters because clean tanks support safer water, although the worker faces cramped, wet conditions.",
            "Protective gear makes the work effortless and removes every risk.",
            "The only important detail is that the tank is a large object.",
            "The difficult conditions mean the work makes no useful contribution.",
        ],
        answer=(
            "The work matters because clean tanks support safer water, although the worker faces cramped, wet conditions."
        ),
    )
    _set_open(
        activities,
        "eng_c5_ch09_work_realities-independent-1-depth-3",
        passage=(
            "A class studied a vocation card. Contribution: a delivery cyclist "
            "brings medicines to people who cannot travel. Demanding reality: the "
            "cyclist rides through changing weather and keeps each package dry."
        ),
        model_answer=(
            "The delivery cyclist contributes by bringing medicines to people who "
            "cannot travel. A complete view also includes riding through changing "
            "weather and keeping each package dry."
        ),
        core_aliases=["bringing medicines to people who cannot travel"],
        support_aliases=[
            "riding through changing weather and keeping each package dry"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_work_realities-independent-2-depth-4",
        passage=(
            "A class studied a vocation card. Contribution: a school cook prepares "
            "meals for many children. Demanding reality: the cook manages heat, "
            "timing, and many portions at once."
        ),
        model_answer=(
            "The school cook contributes by preparing meals for many children. A fair "
            "view also recognises the effort of managing heat, timing, and many "
            "portions at once."
        ),
        core_aliases=["preparing meals for many children"],
        support_aliases=["managing heat, timing, and many portions at once"],
    )

    _set_selected(
        activities,
        "eng_c5_ch09_words_and_tools-guided-1-depth-3",
        passage=(
            "Context clue card: The baker tied an apron over her clothes before "
            "mixing flour, so spills would not stain her uniform."
        ),
        prompt="Which meaning of 'apron' fits this sentence?",
        options=[
            "a cloth cover worn over clothes for protection",
            "a shelf used to cool bread",
            "a metal tool for cutting dough",
            "a list of ingredients in a recipe",
        ],
        answer="a cloth cover worn over clothes for protection",
    )
    _set_selected(
        activities,
        "eng_c5_ch09_words_and_tools-guided-2-depth-4",
        passage=(
            "Context clue card: The shopkeeper wrote every sale and payment in a "
            "ruled ledger before closing the counter."
        ),
        prompt="Which meaning of 'ledger' fits this sentence?",
        options=[
            "a bag used to carry coins",
            "a ruled book used to record money details",
            "a sign placed above a shop",
            "a drawer that locks automatically",
        ],
        answer="a ruled book used to record money details",
    )
    _set_open(
        activities,
        "eng_c5_ch09_words_and_tools-independent-1-depth-3",
        passage=(
            "Context clue card: The young apprentice watched the potter, practised "
            "each step, and asked for guidance while learning the craft."
        ),
        prompt=(
            "What does 'apprentice' mean here, and which detail in the sentence "
            "proves that meaning?"
        ),
        model_answer=(
            "Here, 'apprentice' means a learner training under a skilled worker. The "
            "clue is that the young learner watches, practises, and asks the potter "
            "for guidance."
        ),
        core_aliases=["a learner training under a skilled worker"],
        support_aliases=[
            "the young learner watches, practises, and asks the potter for guidance"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_words_and_tools-independent-2-depth-4",
        passage=(
            "Context clue card: The nurse's shift began at six in the evening and "
            "ended at midnight, when another nurse took over."
        ),
        prompt=(
            "What does 'shift' mean here, and which detail in the sentence proves "
            "that meaning?"
        ),
        model_answer=(
            "Here, 'shift' means a set period of work. The clue is that the nurse's "
            "duty runs from six in the evening to midnight before another nurse takes over."
        ),
        core_aliases=["a set period of work"],
        support_aliases=[
            "from six in the evening to midnight before another nurse takes over"
        ],
    )

    _set_selected(
        activities,
        "eng_c5_ch09_agreement_repair-guided-1-depth-3",
        passage="Editing board: The bus drivers checks the route map each morning.",
        options=[
            "The bus drivers checks the route map each morning.",
            "The bus drivers check the route map each morning.",
            "The bus driver check the route map each morning.",
            "The bus drivers checking the route map each morning.",
        ],
        answer="The bus drivers check the route map each morning.",
    )
    _set_selected(
        activities,
        "eng_c5_ch09_agreement_repair-guided-2-depth-4",
        passage="Editing board: Every shopkeeper count the change twice.",
        options=[
            "Every shopkeeper count the change twice.",
            "Every shopkeepers counts the change twice.",
            "Every shopkeeper counts the change twice.",
            "Every shopkeeper counting the change twice.",
        ],
        answer="Every shopkeeper counts the change twice.",
    )
    _set_open(
        activities,
        "eng_c5_ch09_agreement_repair-independent-1-depth-3",
        passage="Editing board: The boxes of chalk belongs in the cupboard.",
        model_answer=(
            "The corrected sentence is 'The boxes of chalk belong in the cupboard.' "
            "The controlling subject is 'boxes', so the verb must be 'belong'."
        ),
        core_aliases=["The boxes of chalk belong in the cupboard."],
        support_aliases=["The controlling subject is 'boxes'"],
    )
    _set_open(
        activities,
        "eng_c5_ch09_agreement_repair-independent-2-depth-4",
        passage="Editing board: A basket of tools sit beside the bench.",
        model_answer=(
            "The corrected sentence is 'A basket of tools sits beside the bench.' "
            "The controlling subject is 'basket', so the verb must be 'sits'."
        ),
        core_aliases=["A basket of tools sits beside the bench."],
        support_aliases=["The controlling subject is 'basket'"],
    )

    _set_selected(
        activities,
        "eng_c5_ch09_tense_and_adverbs-guided-1-depth-3",
        passage="Language repair card: The carpenter measured the shelf twice.",
        options=[
            "'carpenter' tells how often the measuring happened.",
            "'shelf' tells when the measuring happened.",
            "'twice' tells how often the measuring happened.",
            "'measured' tells where the measuring happened.",
        ],
        answer="'twice' tells how often the measuring happened.",
    )
    _set_selected(
        activities,
        "eng_c5_ch09_tense_and_adverbs-guided-2-depth-4",
        passage=(
            "Language repair card: Tomorrow evening, the baker ___ the dough. "
            "Use the verb prepare."
        ),
        options=[
            "Tomorrow evening, the baker prepared the dough.",
            "Tomorrow evening, the baker will prepare the dough.",
            "Tomorrow evening, the baker has prepare the dough.",
            "Tomorrow evening, the baker preparing the dough.",
        ],
        answer="Tomorrow evening, the baker will prepare the dough.",
    )
    _set_open(
        activities,
        "eng_c5_ch09_tense_and_adverbs-independent-1-depth-3",
        passage=(
            "Language repair card: Since the clinic opened, the nurse ___ the "
            "patient list three times. Use the verb update."
        ),
        model_answer=(
            "The time clue 'Since the clinic opened' requires 'has updated'. The "
            "complete sentence is: Since the clinic opened, the nurse has updated "
            "the patient list three times."
        ),
        core_aliases=["the nurse has updated the patient list three times"],
        support_aliases=["The time clue 'Since the clinic opened'"],
    )
    _set_open(
        activities,
        "eng_c5_ch09_tense_and_adverbs-independent-2-depth-4",
        passage="Language repair card: The guard waited outside quietly.",
        model_answer=(
            "In 'The guard waited outside quietly', 'outside' tells where the guard "
            "waited, while 'quietly' tells how the guard waited."
        ),
        core_aliases=["'outside' tells where the guard waited"],
        support_aliases=["'quietly' tells how the guard waited"],
    )

    _set_selected(
        activities,
        "eng_c5_ch09_wh_questions-guided-1-depth-3",
        passage="Fact card: Rohan stores clean brushes in the blue cupboard.",
        options=[
            "Why does the blue cupboard?",
            "Where does Rohan store clean brushes?",
            "When clean brushes the cupboard?",
            "Who does Rohan in the blue cupboard?",
        ],
        answer="Where does Rohan store clean brushes?",
    )
    _set_selected(
        activities,
        "eng_c5_ch09_wh_questions-guided-2-depth-4",
        passage="Fact card: The potter wraps the finished bowls in newspaper.",
        options=[
            "What does the potter wrap in newspaper?",
            "Where the potter wraps newspaper?",
            "Why does the finished bowls?",
            "When newspaper the potter?",
        ],
        answer="What does the potter wrap in newspaper?",
    )
    _set_open(
        activities,
        "eng_c5_ch09_wh_questions-independent-1-depth-3",
        passage="Fact card: The gardener waters the seedlings before assembly.",
        model_answer="Question: What does the gardener water? Answer: The seedlings.",
        core_aliases=["What does the gardener water?"],
        support_aliases=["Answer: The seedlings."],
    )
    _set_open(
        activities,
        "eng_c5_ch09_wh_questions-independent-2-depth-4",
        passage="Fact card: The nurse checks the medicine shelf after lunch.",
        model_answer=(
            "Question: When does the nurse check the medicine shelf? Answer: After lunch."
        ),
        core_aliases=["When does the nurse check the medicine shelf?"],
        support_aliases=["Answer: After lunch."],
    )

    _set_open(
        activities,
        "eng_c5_ch09_vocation_paragraph-guided-1-depth-3",
        passage=(
            "Planning notes: community librarian; brings books to smaller reading "
            "groups; records each loan; careful records help every book return."
        ),
        model_answer=(
            "A community librarian helps readers reach books. The librarian brings "
            "books to smaller reading groups and records each loan. These careful "
            "records help every book return for another reader. This work combines "
            "service with organisation."
        ),
        core_aliases=["A community librarian helps readers reach books."],
        support_aliases=[
            "brings books to smaller reading groups and records each loan"
        ],
    )
    _set_selected(
        activities,
        "eng_c5_ch09_vocation_paragraph-guided-2-depth-4",
        passage=(
            "Planning notes: school gardener; cares for shared green spaces; plans "
            "watering for each season; patient planning keeps plants healthy."
        ),
        options=[
            "Topic: gardening tools. Detail: buses carry children. Detail: rain falls. Closing: work is useful.",
            "Topic: A school gardener cares for shared green spaces. Details: plans seasonal watering and watches plant needs. Closing: patient planning keeps the garden healthy.",
            "Topic: The school has rooms. Details: flowers have colours and lunch is served. Closing: seasons change.",
            "Topic: Gardens are green. Detail: tools are metal. Closing: every job is exactly the same.",
        ],
        answer=(
            "Topic: A school gardener cares for shared green spaces. Details: plans seasonal watering and watches plant needs. Closing: patient planning keeps the garden healthy."
        ),
    )
    _set_open(
        activities,
        "eng_c5_ch09_vocation_paragraph-independent-1-depth-3",
        passage=(
            "Planning notes: water tester; checks drinking-water samples; labels "
            "each bottle; accurate records support public safety."
        ),
        model_answer=(
            "A water tester helps protect public health. The worker checks "
            "drinking-water samples and labels each bottle carefully. Accurate "
            "records connect each result to the correct sample. This vocation shows "
            "why careful scientific work matters."
        ),
        core_aliases=["A water tester helps protect public health."],
        support_aliases=[
            "checks drinking-water samples and labels each bottle carefully"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_vocation_paragraph-independent-2-depth-4",
        passage=(
            "Planning notes: bus conductor; helps passengers; checks tickets and "
            "stops; attention and courtesy keep the route orderly."
        ),
        model_answer=(
            "A bus conductor helps a route run smoothly. The conductor assists "
            "passengers and checks tickets and stops. Attention keeps the journey "
            "orderly, while courtesy helps people feel respected. This work depends "
            "on both accuracy and care."
        ),
        core_aliases=["A bus conductor helps a route run smoothly."],
        support_aliases=["assists passengers and checks tickets and stops"],
    )

    _set_selected(
        activities,
        "eng_c5_ch09_vocation_fact_report-guided-1-depth-3",
        passage=(
            "Bounded fact card - bicycle mechanic: diagnoses faults; replaces worn "
            "parts; tests the brakes before returning a bicycle. No other facts are supplied."
        ),
        options=[
            "diagnoses faults and tests the brakes",
            "designs bridges and controls traffic lights",
            "grows rice and studies rainfall",
            "writes novels and repairs musical instruments",
        ],
        answer="diagnoses faults and tests the brakes",
    )
    _set_selected(
        activities,
        "eng_c5_ch09_vocation_fact_report-guided-2-depth-4",
        passage=(
            "Bounded fact card - school archivist: labels old records; protects "
            "documents from damage; logs each borrowed file. No other facts are supplied."
        ),
        options=[
            "labels records and logs borrowed files",
            "drives a train and checks railway tracks",
            "sells vegetables and repairs umbrellas",
            "paints houses and delivers medicine",
        ],
        answer="labels records and logs borrowed files",
    )
    _set_open(
        activities,
        "eng_c5_ch09_vocation_fact_report-independent-1-depth-3",
        passage=(
            "Bounded fact card - seed-bank assistant: dries labelled seed samples; "
            "records each collection place; checks that storage containers stay dry. "
            "No other facts are supplied."
        ),
        model_answer=(
            "The supplied fact card says that a seed-bank assistant dries labelled "
            "seed samples and records each collection place. It also states that the "
            "worker checks storage containers; I have not added facts beyond the card."
        ),
        core_aliases=[
            "dries labelled seed samples and records each collection place"
        ],
        support_aliases=["I have not added facts beyond the card"],
    )
    _set_open(
        activities,
        "eng_c5_ch09_vocation_fact_report-independent-2-depth-4",
        passage=(
            "Bounded fact card - audio technician: checks cables before an event; "
            "balances microphone sound; uses hearing protection near loud speakers. "
            "No other facts are supplied."
        ),
        model_answer=(
            "The supplied fact card says that an audio technician checks cables "
            "before an event and balances microphone sound. It also states that the "
            "worker uses hearing protection; I have not added facts beyond the card."
        ),
        core_aliases=[
            "checks cables before an event and balances microphone sound"
        ],
        support_aliases=["I have not added facts beyond the card"],
    )

    activities[
        "eng_c5_ch09_tense_and_adverbs-independent-1"
    ]["passage"] = (
        "Language repair card: Since sunrise, the porter ___ many parcels. "
        "Use the verb carry."
    )
    activities["eng_c5_ch09_tense_and_adverbs-transfer-1"]["passage"] = (
        "Language repair card: Before the shop opened, the vendor ___ the baskets. "
        "Use the verb arrange."
    )
    activities["eng_c5_ch09_tense_and_adverbs-review-1"]["passage"] = (
        "Language repair card: By next Monday, the tailor ___ the uniforms. "
        "Use the verb finish."
    )
    activities[
        "eng_c5_ch09-assessment-grammar-tense_usage-2"
    ]["passage"] = (
        "Language repair card: For the past two hours, the engineer ___ the backup "
        "system. Use the verb test."
    )

    _set_open(
        activities,
        "eng_c5_ch09_work_realities-review-2",
        passage=(
            "A night bus mechanic keeps school buses safe by checking their brakes "
            "after the final route. The job involves lifting heavy parts in a noisy "
            "workshop late at night."
        ),
        prompt=(
            "Write a balanced caption that names the mechanic's contribution and "
            "one demanding reality from the note."
        ),
        model_answer=(
            "The mechanic contributes by keeping school buses safe through brake "
            "checks. The demanding reality is lifting heavy parts in a noisy "
            "workshop late at night."
        ),
        core_aliases=["keeping school buses safe through brake checks"],
        support_aliases=[
            "lifting heavy parts in a noisy workshop late at night"
        ],
    )

    _set_open(
        activities,
        "eng_c5_ch09_perceived_freedom-bridge",
        passage=(
            "In an original reflective verse, a child admires a window cleaner's "
            "open view above the street. A later line says the cleaner checks a "
            "harness and every rope before climbing."
        ),
        model_answer=(
            "The child imagines freedom because the window cleaner sees an open view "
            "above the street. The safety clue shows responsibility because the "
            "cleaner checks a harness and every rope before climbing."
        ),
        core_aliases=["an open view above the street"],
        support_aliases=["checks a harness and every rope before climbing"],
    )
    _set_open(
        activities,
        "eng_c5_ch09_work_realities-bridge",
        passage=(
            "A class studied a short vocation card. Contribution: a school crossing "
            "helper guides children safely. Demanding reality: the helper watches "
            "moving traffic while standing in heat."
        ),
        model_answer=(
            "The crossing helper contributes by guiding children safely. The work "
            "also demands watching moving traffic while standing in heat."
        ),
        core_aliases=["guiding children safely"],
        support_aliases=["watching moving traffic while standing in heat"],
    )
    _set_open(
        activities,
        "eng_c5_ch09_vocation_paragraph-bridge",
        passage=(
            "Planning notes: community nurse; checks patients; records each medicine; "
            "careful records support safe care."
        ),
        model_answer=(
            "A community nurse supports safe care. The nurse checks patients and "
            "records each medicine. Careful records help the next health worker "
            "understand what has been given."
        ),
        core_aliases=["A community nurse supports safe care."],
        support_aliases=["checks patients and records each medicine"],
    )
    _set_selected(
        activities,
        "eng_c5_ch09_vocation_paragraph-masterclass",
        passage=(
            "Planning notes for a paragraph about a bicycle repairer: finds faults, "
            "replaces worn parts, tests each bicycle, grows roses for a flower show."
        ),
        prompt=(
            "Which detail breaks the paragraph's central idea about bicycle repair?"
        ),
        options=[
            "finds faults",
            "replaces worn parts",
            "tests each bicycle",
            "grows roses for a flower show",
        ],
        answer="grows roses for a flower show",
    )


def _author_chapter_10(manifest: dict) -> None:
    activities = _activity_index(manifest)

    _set_selected(
        activities,
        "eng_c5_ch10_production_sequence-guided-1-depth-3",
        passage=(
            "Production process notes: smooth a clay slab; press the letters into "
            "the surface; trim the rough edges; dry the nameplate in the shade."
        ),
        options=[
            "press letters -> smooth clay -> dry -> trim edges",
            "smooth clay -> press letters -> trim edges -> dry in shade",
            "dry in shade -> trim edges -> press letters -> smooth clay",
            "trim edges -> dry in shade -> smooth clay -> press letters",
        ],
        answer="smooth clay -> press letters -> trim edges -> dry in shade",
    )
    _set_selected(
        activities,
        "eng_c5_ch10_production_sequence-guided-2-depth-4",
        passage=(
            "Production process notes: measure the cloth; cut the two pieces with "
            "adult supervision; stitch the side seams; attach the button loop."
        ),
        options=[
            "stitch seams -> measure cloth -> attach loop -> cut pieces",
            "measure cloth -> attach loop -> cut pieces -> stitch seams",
            "measure cloth -> cut pieces -> stitch seams -> attach loop",
            "attach loop -> stitch seams -> cut pieces -> measure cloth",
        ],
        answer="measure cloth -> cut pieces -> stitch seams -> attach loop",
    )
    _set_open(
        activities,
        "eng_c5_ch10_production_sequence-independent-1-depth-3",
        passage=(
            "Production process notes: mark the fold lines on a paper sheet; cut "
            "slots with adult help; join the short edges; add a paper handle."
        ),
        model_answer=(
            "The production process is mark the fold lines -> cut the slots with "
            "adult help -> join the short edges -> add a paper handle. The folds "
            "must be marked before cutting, and the handle is added after the lantern "
            "body has been joined."
        ),
        core_aliases=[
            "mark the fold lines -> cut the slots with adult help -> join the short edges -> add a paper handle"
        ],
        support_aliases=[
            "The folds must be marked before cutting, and the handle is added after the lantern body has been joined"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_production_sequence-independent-2-depth-4",
        passage=(
            "Production process notes: soak waste-paper scraps; mash them into pulp; "
            "mix in a few seeds; press the sheet and dry it in the shade."
        ),
        model_answer=(
            "The production process is soak the scraps -> mash them into pulp -> mix "
            "in the seeds -> press and shade-dry the sheet. The scraps must soften "
            "before they can become pulp, and seeds are mixed in before the final "
            "pressing and drying."
        ),
        core_aliases=[
            "soak the scraps -> mash them into pulp -> mix in the seeds -> press and shade-dry the sheet"
        ],
        support_aliases=[
            "The scraps must soften before they can become pulp, and seeds are mixed in before the final pressing and drying"
        ],
    )

    _set_open(
        activities,
        "eng_c5_ch10_tradition_innovation-guided-1-depth-3",
        passage=(
            "Design record: basket makers retained a familiar diagonal weave and "
            "added a removable, washable cloth liner. The basket still looked local "
            "and became easier to clean after carrying vegetables."
        ),
        model_answer=(
            "The makers combined tradition and innovation so the basket stayed "
            "recognisable and became easier to clean. They retained the familiar "
            "diagonal weave and added a removable, washable cloth liner."
        ),
        core_aliases=[
            "the basket stayed recognisable and became easier to clean"
        ],
        support_aliases=[
            "retained the familiar diagonal weave and added a removable, washable cloth liner"
        ],
    )
    _set_selected(
        activities,
        "eng_c5_ch10_tradition_innovation-guided-2-depth-4",
        passage=(
            "Design record: printers kept a traditional flower block and tested a "
            "washable dye. The cloth retained the old motif, and its colour lasted "
            "through repeated washing."
        ),
        options=[
            "They removed the flower motif and changed nothing else.",
            "They kept the flower block, tested washable dye, and gained longer-lasting colour.",
            "They invented the old motif after testing the finished cloth.",
            "They used washable dye because every traditional feature was unsuitable.",
        ],
        answer=(
            "They kept the flower block, tested washable dye, and gained longer-lasting colour."
        ),
    )
    _set_open(
        activities,
        "eng_c5_ch10_tradition_innovation-independent-1-depth-3",
        passage=(
            "Design record: puppet makers retained the painted face style and added "
            "a stronger shoulder joint. The character remained familiar and the arms "
            "moved without loosening quickly."
        ),
        model_answer=(
            "The retained feature is the painted face style. The innovation is a "
            "stronger shoulder joint, and the stated outcome is that the familiar "
            "character can move without the arms loosening quickly."
        ),
        core_aliases=[
            "The retained feature is the painted face style. The innovation is a stronger shoulder joint"
        ],
        support_aliases=[
            "the familiar character can move without the arms loosening quickly"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_tradition_innovation-independent-2-depth-4",
        passage=(
            "Design record: potters kept a carved border used on serving bowls and "
            "made the base slightly wider. The border remained visible, while the "
            "bowl stood more steadily on a table."
        ),
        model_answer=(
            "The makers retained the carved border and widened the base. The stated "
            "outcome is that the bowl remains recognisable and stands more steadily "
            "on a table."
        ),
        core_aliases=["retained the carved border and widened the base"],
        support_aliases=[
            "the bowl remains recognisable and stands more steadily on a table"
        ],
    )

    _set_open(
        activities,
        "eng_c5_ch10_community_effects-guided-1-depth-3",
        passage=(
            "Community impact note: a weekend handloom market attracted more buyers. "
            "As a direct result, weavers received larger orders. In supporting work, "
            "dyers prepared more thread and local vans carried finished cloth."
        ),
        model_answer=(
            "Because the weekend handloom market attracted more buyers, weavers "
            "received larger orders. The increase also led dyers to prepare more "
            "thread and local vans to carry finished cloth."
        ),
        core_aliases=[
            "the weekend handloom market attracted more buyers, weavers received larger orders"
        ],
        support_aliases=[
            "dyers to prepare more thread and local vans to carry finished cloth"
        ],
    )
    _set_selected(
        activities,
        "eng_c5_ch10_community_effects-guided-2-depth-4",
        passage=(
            "Community impact note: a school ordered two hundred cloth book bags. "
            "As a direct result, local tailors added stitching hours. In supporting "
            "work, a button supplier and an ironing service received more requests."
        ),
        options=[
            "The school order directly increased tailoring and indirectly increased button and ironing work.",
            "The button supplier caused the school to stop using book bags.",
            "Only the ironing service was affected by the order.",
            "The tailors worked less because the school ordered more bags.",
        ],
        answer=(
            "The school order directly increased tailoring and indirectly increased button and ironing work."
        ),
    )
    _set_open(
        activities,
        "eng_c5_ch10_community_effects-independent-1-depth-3",
        passage=(
            "Community impact note: a festival committee ordered more clay lamps. "
            "As a direct result, potters shaped extra lamps. In supporting work, a "
            "clay supplier and packing team handled larger loads."
        ),
        model_answer=(
            "The larger festival order directly led potters to shape extra lamps. "
            "It indirectly increased work for the clay supplier and packing team, "
            "which handled larger loads."
        ),
        core_aliases=[
            "The larger festival order directly led potters to shape extra lamps"
        ],
        support_aliases=[
            "indirectly increased work for the clay supplier and packing team"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_community_effects-independent-2-depth-4",
        passage=(
            "Community impact note: families brought old appliances to a repair fair. "
            "As a direct result, technicians completed more repairs. In supporting "
            "work, spare-parts shops and bicycle couriers filled more requests."
        ),
        model_answer=(
            "Because families brought old appliances to the repair fair, technicians "
            "completed more repairs. The activity also created supporting work for "
            "spare-parts shops and bicycle couriers."
        ),
        core_aliases=[
            "families brought old appliances to the repair fair, technicians completed more repairs"
        ],
        support_aliases=[
            "supporting work for spare-parts shops and bicycle couriers"
        ],
    )

    _set_selected(
        activities,
        "eng_c5_ch10_semantic_associations-guided-1-depth-3",
        passage=(
            "Semantic association card: needle -> stitching. A needle passes thread "
            "through cloth to form stitches."
        ),
        options=[
            "needle -> stitching",
            "needle -> thunder",
            "needle -> swimming pool",
            "needle -> sunrise",
        ],
        answer="needle -> stitching",
    )
    _set_selected(
        activities,
        "eng_c5_ch10_semantic_associations-guided-2-depth-4",
        passage=(
            "Semantic association card: kiln -> heat. A kiln uses controlled heat to "
            "harden clay objects."
        ),
        options=[
            "kiln -> whisper",
            "kiln -> heat",
            "kiln -> rainfall",
            "kiln -> pillow",
        ],
        answer="kiln -> heat",
    )
    _set_open(
        activities,
        "eng_c5_ch10_semantic_associations-independent-1-depth-3",
        passage=(
            "Semantic association card: loom -> weaving. Threads cross on a loom to "
            "make woven cloth."
        ),
        model_answer=(
            "A loom is meaningfully linked with weaving because threads cross on the "
            "loom to make woven cloth. The words are related by tool and action, not "
            "because they are synonyms."
        ),
        core_aliases=["A loom is meaningfully linked with weaving"],
        support_aliases=["threads cross on the loom to make woven cloth"],
    )
    _set_open(
        activities,
        "eng_c5_ch10_semantic_associations-independent-2-depth-4",
        passage=(
            "Semantic association card: market -> exchange. At a market, people "
            "exchange money for goods and services."
        ),
        model_answer=(
            "A market is meaningfully linked with exchange because people exchange "
            "money for goods and services there. The relation is place and activity, "
            "not synonymy."
        ),
        core_aliases=["A market is meaningfully linked with exchange"],
        support_aliases=["people exchange money for goods and services there"],
    )

    _set_selected(
        activities,
        "eng_c5_ch10_punctuation_editor-guided-1-depth-3",
        passage="Unedited line: anita asked where is the craft fair",
        options=[
            "anita asked where is the craft fair.",
            "Anita asked, Where is the craft fair?",
            "Anita asked, \"Where is the craft fair?\"",
            "Anita asked \"where is the craft fair.\"",
        ],
        answer="Anita asked, \"Where is the craft fair?\"",
    )
    _set_selected(
        activities,
        "eng_c5_ch10_punctuation_editor-guided-2-depth-4",
        passage="Unedited line: we packed thread needles cloth and buttons",
        options=[
            "We packed thread needles cloth and buttons.",
            "We packed thread, needles, cloth, and buttons.",
            "we packed thread, needles cloth and buttons",
            "We packed: thread needles cloth and buttons?",
        ],
        answer="We packed thread, needles, cloth, and buttons.",
    )
    _set_open(
        activities,
        "eng_c5_ch10_punctuation_editor-independent-1-depth-3",
        passage="Unedited line: the workshop opens on monday wednesday and friday",
        model_answer=(
            "Corrected line: The workshop opens on Monday, Wednesday, and Friday. "
            "The sentence begins with a capital, day names take capitals, commas "
            "separate the list, and a full stop closes the statement."
        ),
        core_aliases=[
            "The workshop opens on Monday, Wednesday, and Friday."
        ],
        support_aliases=[
            "day names take capitals, commas separate the list, and a full stop closes the statement"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_punctuation_editor-independent-2-depth-4",
        passage="Unedited line: mina said i finished the border",
        model_answer=(
            "Corrected line: Mina said, \"I finished the border.\" The names and "
            "quoted sentence take capitals, a comma introduces the quotation, and "
            "quotation marks show Mina's exact words."
        ),
        core_aliases=["Mina said, \"I finished the border.\""],
        support_aliases=[
            "a comma introduces the quotation, and quotation marks show Mina's exact words"
        ],
    )

    _set_selected(
        activities,
        "eng_c5_ch10_past_perfect_sequence-guided-1-depth-3",
        passage=(
            "Two past events: the printer mixed the dye; later, she dipped the cloth."
        ),
        options=[
            "The printer had mixed the dye before she dipped the cloth.",
            "The printer mixed the dye before she had dipped the cloth.",
            "The printer has mixed the dye before she dipped the cloth.",
            "The printer had mix the dye before she dip the cloth.",
        ],
        answer="The printer had mixed the dye before she dipped the cloth.",
    )
    _set_selected(
        activities,
        "eng_c5_ch10_past_perfect_sequence-guided-2-depth-4",
        passage=(
            "Two past events: Kabir saved every receipt; later, he checked the total."
        ),
        options=[
            "Kabir had saved every receipt before he checked the total.",
            "Kabir saved every receipt before he had checked the total.",
            "Kabir has saved every receipt before he checked the total.",
            "Kabir had save every receipt before he check the total.",
        ],
        answer="Kabir had saved every receipt before he checked the total.",
    )
    _set_open(
        activities,
        "eng_c5_ch10_past_perfect_sequence-independent-1-depth-3",
        passage=(
            "Two past events: the artisan polished the wooden toy; later, she packed it."
        ),
        model_answer=(
            "The artisan had polished the wooden toy before she packed it. Use had + "
            "past participle for the completed earlier event and simple past for the "
            "later event."
        ),
        core_aliases=[
            "The artisan had polished the wooden toy before she packed it."
        ],
        support_aliases=[
            "had + past participle for the completed earlier event and simple past for the later event"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_past_perfect_sequence-independent-2-depth-4",
        passage=(
            "Two past events: Meera planned the budget; later, she bought the thread."
        ),
        model_answer=(
            "Meera had planned the budget before she bought the thread. Use had + "
            "past participle for the completed earlier event and simple past for the "
            "later event."
        ),
        core_aliases=["Meera had planned the budget before she bought the thread."],
        support_aliases=[
            "had + past participle for the completed earlier event and simple past for the later event"
        ],
    )

    _set_open(
        activities,
        "eng_c5_ch10_procedure_writer-guided-1-depth-3",
        passage=(
            "Procedure fact packet: wash the lemon; cut it with adult help; squeeze "
            "the juice into water; stir in the prepared sugar. Safety note: use a "
            "clean board and let an adult handle the knife."
        ),
        model_answer=(
            "To make the lemon drink, first wash the lemon. Next, let an adult cut "
            "it. Then, squeeze the juice into water. Finally, stir in the prepared "
            "sugar. Use a clean board and let an adult handle the knife."
        ),
        core_aliases=[
            "first wash the lemon. Next, let an adult cut it. Then, squeeze the juice into water. Finally, stir in the prepared sugar"
        ],
        support_aliases=[
            "Use a clean board and let an adult handle the knife."
        ],
    )
    _set_selected(
        activities,
        "eng_c5_ch10_procedure_writer-guided-2-depth-4",
        passage=(
            "Procedure fact packet: write the plant name; cover the card with clear "
            "tape; attach it to a stick; place the label beside the seedling."
        ),
        options=[
            "attach to stick -> write name -> place label -> cover card",
            "write name -> cover card -> attach to stick -> place beside seedling",
            "place beside seedling -> cover card -> write name -> attach to stick",
            "cover card -> place label -> attach to stick -> write name",
        ],
        answer=(
            "write name -> cover card -> attach to stick -> place beside seedling"
        ),
    )
    _set_open(
        activities,
        "eng_c5_ch10_procedure_writer-independent-1-depth-3",
        passage=(
            "Procedure fact packet: fold the paper like a fan; press each crease; "
            "tie one end; open the folds. Quality note: keep the folds even."
        ),
        model_answer=(
            "To make the paper fan, first fold the paper back and forth. Next, press "
            "each crease. Then, tie one end. Finally, open the folds. Keep the folds even."
        ),
        core_aliases=[
            "first fold the paper back and forth. Next, press each crease. Then, tie one end. Finally, open the folds"
        ],
        support_aliases=["Keep the folds even."],
    )
    _set_open(
        activities,
        "eng_c5_ch10_procedure_writer-independent-2-depth-4",
        passage=(
            "Procedure fact packet: place two cloth squares together; stitch three "
            "sides; turn the cover outward; fill it and close the last side. Safety "
            "note: use a blunt needle with adult guidance."
        ),
        model_answer=(
            "To make the cloth coaster, first place two cloth squares together. Next, "
            "stitch three sides. Then, turn the cover outward and fill it. Finally, "
            "close the last side. Use a blunt needle with adult guidance."
        ),
        core_aliases=[
            "first place two cloth squares together. Next, stitch three sides. Then, turn the cover outward and fill it. Finally, close the last side"
        ],
        support_aliases=["Use a blunt needle with adult guidance."],
    )

    _set_open(
        activities,
        "eng_c5_ch10_festival_recount-guided-1-depth-3",
        passage=(
            "Recount planner: monsoon welcome; first made paper boats; later listened "
            "to grandparents' rain stories; before leaving cleaned the courtyard; "
            "reflection: celebration and care can belong together."
        ),
        model_answer=(
            "Recently, I joined a monsoon welcome. First, we made paper boats. Later, "
            "we listened to grandparents' rain stories, which connected the day to "
            "family memories. Before leaving, we cleaned the courtyard. I learned "
            "that celebration and care can belong together."
        ),
        core_aliases=["Recently, I joined a monsoon welcome."],
        support_aliases=[
            "First, we made paper boats. Later, we listened to grandparents' rain stories"
        ],
    )
    _set_selected(
        activities,
        "eng_c5_ch10_festival_recount-guided-2-depth-4",
        passage=(
            "Recount planner: local music evening; first arranged chairs; later heard "
            "three neighbourhood groups; before leaving thanked the performers; "
            "reflection: many styles can share one stage."
        ),
        options=[
            "Opening: music exists. Detail: chairs are objects. Closing: stages have lights.",
            "Opening: I joined a local music evening. Sequence: arranged chairs, heard three groups, thanked performers. Reflection: many styles can share one stage.",
            "Opening: We thanked performers. Sequence: left first, arranged chairs later, then began the event. Reflection: none.",
            "Opening: The neighbourhood has roads. Details: one song and an unrelated shopping list. Closing: music is loud.",
        ],
        answer=(
            "Opening: I joined a local music evening. Sequence: arranged chairs, heard three groups, thanked performers. Reflection: many styles can share one stage."
        ),
    )
    _set_open(
        activities,
        "eng_c5_ch10_festival_recount-independent-1-depth-3",
        passage=(
            "Recount planner: school garden day; first planted herb cuttings; later "
            "labelled each bed; before leaving shared watering duties; reflection: "
            "a shared garden needs shared care."
        ),
        model_answer=(
            "Recently, I joined our school garden day. First, we planted herb "
            "cuttings. Later, we labelled each bed so others could identify the plants. "
            "Before leaving, we shared the watering duties. I understood that a shared "
            "garden needs shared care."
        ),
        core_aliases=["Recently, I joined our school garden day."],
        support_aliases=[
            "First, we planted herb cuttings. Later, we labelled each bed"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_festival_recount-independent-2-depth-4",
        passage=(
            "Recount planner: reading festival; first exchanged bookmarks; later "
            "heard a storyteller; before leaving donated books to the class shelf; "
            "reflection: stories grow when readers share them."
        ),
        model_answer=(
            "Recently, I joined a reading festival. First, we exchanged bookmarks. "
            "Later, we heard a storyteller and discussed the ending. Before leaving, "
            "we donated books to the class shelf. I learned that stories grow when "
            "readers share them."
        ),
        core_aliases=["Recently, I joined a reading festival."],
        support_aliases=[
            "First, we exchanged bookmarks. Later, we heard a storyteller"
        ],
    )

    _set_open(
        activities,
        "eng_c5_ch10_craft_and_savings-guided-1-depth-3",
        passage=(
            "Bounded inquiry packet: Riya places 80 rupees into her savings account. "
            "The passbook records the deposit and shows a higher balance. This example "
            "does not explain every banking service."
        ),
        model_answer=(
            "The key saving idea is that a deposit adds recorded money to an account: "
            "Riya's passbook records 80 rupees and shows a higher balance. The packet "
            "does not prove how every banking service works."
        ),
        core_aliases=[
            "a deposit adds recorded money to an account"
        ],
        support_aliases=[
            "The packet does not prove how every banking service works."
        ],
    )
    _set_selected(
        activities,
        "eng_c5_ch10_craft_and_savings-guided-2-depth-4",
        passage=(
            "Bounded inquiry packet: exhibition label - Kutch embroidery, Gujarat. "
            "The sample uses bright thread and small mirror work."
        ),
        options=[
            "Kutch embroidery -> Gujarat",
            "Kutch embroidery -> Kerala",
            "Kutch embroidery -> Sikkim",
            "Kutch embroidery -> Odisha",
        ],
        answer="Kutch embroidery -> Gujarat",
    )
    _set_open(
        activities,
        "eng_c5_ch10_craft_and_savings-independent-1-depth-3",
        passage=(
            "Bounded inquiry packet: exhibition label - blue pottery, Jaipur in "
            "Rajasthan. The displayed bowl has a smooth glazed surface and blue designs."
        ),
        model_answer=(
            "According to the supplied exhibition label, blue pottery is connected "
            "with Jaipur in Rajasthan. The displayed bowl has a smooth glazed surface "
            "and blue designs; no wider origin story is claimed."
        ),
        core_aliases=[
            "blue pottery is connected with Jaipur in Rajasthan"
        ],
        support_aliases=["no wider origin story is claimed"],
    )
    _set_open(
        activities,
        "eng_c5_ch10_craft_and_savings-independent-2-depth-4",
        passage=(
            "Bounded inquiry packet: Nisha sets a saving goal of 240 rupees for books. "
            "She records each weekly amount and compares the running total with the goal. "
            "The card does not discuss interest or account fees."
        ),
        model_answer=(
            "The key idea is a saving goal: Nisha records each weekly amount and "
            "compares the running total with 240 rupees. The example does not explain "
            "interest or account fees."
        ),
        core_aliases=[
            "Nisha records each weekly amount and compares the running total with 240 rupees"
        ],
        support_aliases=["does not explain interest or account fees"],
    )

    _set_open(
        activities,
        "eng_c5_ch10_tradition_innovation-review-2",
        passage=(
            "Design record from a metalwork studio: makers retained a punched star "
            "pattern and added a heat-resistant handle. The lamp remained "
            "recognisable and became safer to carry after use."
        ),
        prompt=(
            "Identify the retained feature, the changed feature, and the stated "
            "outcome using only the design record."
        ),
        model_answer=(
            "The makers retained the punched star pattern and added a heat-resistant "
            "handle. The lamp stayed recognisable and became safer to carry after use."
        ),
        core_aliases=[
            "retained the punched star pattern and added a heat-resistant handle"
        ],
        support_aliases=[
            "stayed recognisable and became safer to carry after use"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_tradition_innovation-bridge",
        passage=(
            "Design record: makers kept a familiar checked weave on a lunch bag and "
            "added a washable inner cloth. The outside remained familiar, and the bag "
            "became easier to clean."
        ),
        model_answer=(
            "The makers kept the familiar checked weave and added a washable inner "
            "cloth. The result is a recognisable bag that is easier to clean."
        ),
        core_aliases=[
            "kept the familiar checked weave and added a washable inner cloth"
        ],
        support_aliases=["a recognisable bag that is easier to clean"],
    )
    _set_open(
        activities,
        "eng_c5_ch10_community_effects-bridge",
        passage=(
            "Community impact note: a hostel ordered cane baskets. Basket makers "
            "added work shifts, while a bamboo supplier and delivery van received "
            "more work."
        ),
        model_answer=(
            "The hostel order directly gave basket makers more work shifts. It also "
            "created supporting work for the bamboo supplier and delivery van."
        ),
        core_aliases=["gave basket makers more work shifts"],
        support_aliases=[
            "supporting work for the bamboo supplier and delivery van"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_procedure_writer-bridge",
        passage=(
            "Procedure fact packet: fold a paper strip; seal the two sides; add dry "
            "seeds; label the packet. Quality note: use glue sparingly so the packet opens."
        ),
        model_answer=(
            "To make the seed envelope, first fold the paper strip. Next, seal the two "
            "sides. Then, add the dry seeds. Finally, label the packet. Use glue "
            "sparingly so the packet opens."
        ),
        core_aliases=[
            "first fold the paper strip. Next, seal the two sides. Then, add the dry seeds. Finally, label the packet"
        ],
        support_aliases=["Use glue sparingly so the packet opens."],
    )
    _set_open(
        activities,
        "eng_c5_ch10_festival_recount-bridge",
        passage=(
            "Recount planner: neighbourhood kite morning; first decorated kites; "
            "later watched a safe-flying demonstration; before leaving collected "
            "broken strings; reflection: fun includes responsibility."
        ),
        model_answer=(
            "Recently, I joined a neighbourhood kite morning. First, we decorated "
            "kites. Later, we watched a safe-flying demonstration. Before leaving, "
            "we collected broken strings. I learned that fun includes responsibility."
        ),
        core_aliases=[
            "Recently, I joined a neighbourhood kite morning."
        ],
        support_aliases=[
            "First, we decorated kites. Later, we watched a safe-flying demonstration."
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_craft_and_savings-bridge",
        passage=(
            "Bounded inquiry packet: Rina deposits 50 rupees. Her account record "
            "shows the deposit and a balance that is 50 rupees higher. The card gives "
            "no information about other banking services."
        ),
        model_answer=(
            "The key idea is a recorded deposit: Rina adds 50 rupees and the balance "
            "becomes 50 rupees higher. The card gives no information about other "
            "banking services."
        ),
        core_aliases=[
            "Rina adds 50 rupees and the balance becomes 50 rupees higher"
        ],
        support_aliases=[
            "The card gives no information about other banking services."
        ],
    )


def _author_chapter_9_transfer_twos(manifest: dict) -> None:
    activities = _activity_index(manifest)

    _set_open(
        activities,
        "eng_c5_ch09_perceived_freedom-transfer-2",
        passage=(
            "Harbour careers postcard. Child's snapshot: a lighthouse keeper "
            "watches the open sea from a tower. Duty log: before storms, the "
            "keeper tests the warning lamp and carries emergency batteries up "
            "the stairs."
        ),
        prompt=(
            "What freedom does the child's snapshot suggest, and how does the "
            "duty log qualify that view? Use both labelled pieces of evidence."
        ),
        model_answer=(
            "The child imagines freedom because the lighthouse keeper watches "
            "the open sea from a tower. The duty log qualifies that view because "
            "the keeper tests the warning lamp and carries emergency batteries "
            "up the stairs before storms."
        ),
        core_aliases=[
            "the lighthouse keeper watches the open sea from a tower"
        ],
        support_aliases=[
            "tests the warning lamp and carries emergency batteries up the stairs"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_work_realities-transfer-2",
        passage=(
            "Community-service interview. Contribution: an animal-rescue "
            "dispatcher turns emergency calls into routes for the rescue van. "
            "Demanding condition: during overnight shifts, the dispatcher stays "
            "alert while several callers speak at once."
        ),
        prompt=(
            "Give a fair view of this work by pairing its contribution with its "
            "demanding condition. Use one detail from each interview label."
        ),
        model_answer=(
            "The dispatcher contributes by turning emergency calls into routes "
            "for the rescue van. A fair view also recognises the demanding work "
            "of staying alert during overnight shifts while several callers "
            "speak at once."
        ),
        core_aliases=[
            "turning emergency calls into routes for the rescue van"
        ],
        support_aliases=[
            "staying alert during overnight shifts while several callers speak at once"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_words_and_tools-transfer-2",
        passage=(
            "Workshop repair ticket. Problem: the clay cups remained soft. "
            "Technician's finding: the kiln did not heat, so the potter could "
            "not harden the cups."
        ),
        prompt=(
            "What does 'kiln' mean in this ticket, and which finding proves the "
            "meaning? Use the repair evidence."
        ),
        model_answer=(
            "Here, 'kiln' means a heated chamber used to harden clay. The repair "
            "evidence is that the failed heater left the cups soft, so the potter "
            "could not harden them."
        ),
        core_aliases=["a heated chamber used to harden clay"],
        support_aliases=["the failed heater left the cups soft"],
    )
    _set_open(
        activities,
        "eng_c5_ch09_agreement_repair-transfer-2",
        passage=(
            "Depot proofreading slip | printed line: A crate of helmets need a "
            "new shelf label."
        ),
        prompt=(
            "Correct the printed line and identify the head subject that controls "
            "the verb. Use the sentence evidence."
        ),
        model_answer=(
            "The corrected line is 'A crate of helmets needs a new shelf label.' "
            "The controlling subject is 'crate', so the singular verb is 'needs'."
        ),
        core_aliases=["A crate of helmets needs a new shelf label."],
        support_aliases=["The controlling subject is 'crate'"],
    )
    _set_open(
        activities,
        "eng_c5_ch09_tense_and_adverbs-transfer-2",
        passage=(
            "Weather-station radio transcript: At dawn yesterday, the technician "
            "calibrated the rain gauge precisely."
        ),
        prompt=(
            "Identify the expression that tells when and the expression that "
            "tells how. Explain each choice from the transcript."
        ),
        model_answer=(
            "At dawn yesterday tells when the calibration happened. Precisely "
            "tells how the technician calibrated the gauge."
        ),
        core_aliases=[
            "At dawn yesterday tells when the calibration happened"
        ],
        support_aliases=[
            "Precisely tells how the technician calibrated the gauge"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_wh_questions-transfer-2",
        passage=(
            "Visitor-board row | person: Salma | task: tests solar lanterns | "
            "place: roof lab | time: Thursday afternoon."
        ),
        prompt=(
            "Write a WH question whose answer is the place in the visitor-board "
            "row, then give the supported answer."
        ),
        model_answer=(
            "Where does Salma test solar lanterns? Salma tests them in the roof lab."
        ),
        core_aliases=["Where does Salma test solar lanterns?"],
        support_aliases=["Salma tests them in the roof lab."],
    )
    _set_open(
        activities,
        "eng_c5_ch09_vocation_paragraph-transfer-2",
        passage=(
            "Career-podcast notes. Role: a prosthetic-limb technician. Clip 1: "
            "measures each user carefully. Clip 2: adjusts every joint before "
            "delivery. Editor's focus: careful fitting makes a support useful."
        ),
        prompt=(
            "Turn the podcast notes into one organised vocation paragraph with a "
            "topic sentence, both evidence details, and a closing idea."
        ),
        model_answer=(
            "Careful fitting makes a prosthetic support useful. A prosthetic-limb "
            "technician measures each user carefully and adjusts every joint before "
            "delivery. These connected steps show why precise preparation matters "
            "in this vocation."
        ),
        core_aliases=["careful fitting makes a prosthetic support useful"],
        support_aliases=[
            "measures each user carefully and adjusts every joint before delivery"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch09_vocation_fact_report-transfer-2",
        passage=(
            "Aquarium source envelope. Strip A: the keeper records water "
            "temperature. Strip B: the keeper prepares measured feed. Strip C: "
            "the keeper cleans viewing glass. The envelope gives no facts about "
            "diving or animal medicine."
        ),
        prompt=(
            "Report two keeper duties and state the source boundary. Use only the "
            "evidence strips, without adding likely duties."
        ),
        model_answer=(
            "The source envelope says that the aquarium keeper records water "
            "temperature and prepares measured feed. The envelope gives no facts "
            "about diving or animal medicine."
        ),
        core_aliases=[
            "records water temperature and prepares measured feed"
        ],
        support_aliases=[
            "The envelope gives no facts about diving or animal medicine."
        ],
    )


def _author_chapter_10_transfer_twos(manifest: dict) -> None:
    activities = _activity_index(manifest)

    _set_open(
        activities,
        "eng_c5_ch10_production_sequence-transfer-2",
        passage=(
            "Pressed-leaf bookmark prototype board. Movable tiles: trim the "
            "sealed sheet; choose and flatten a leaf; place the leaf between "
            "clear sheets; seal the sheets. Dependency arrows: flatten before "
            "placing; seal before trimming."
        ),
        prompt=(
            "Rebuild the four-step process and explain the dependency that fixes "
            "the last two positions. Use the prototype-board evidence."
        ),
        model_answer=(
            "The workable sequence is choose and flatten a leaf -> place the leaf "
            "between clear sheets -> seal the sheets -> trim the sealed sheet. "
            "Flattening must happen before sealing, and sealing before trimming."
        ),
        core_aliases=[
            "choose and flatten a leaf -> place the leaf between clear sheets -> seal the sheets -> trim the sealed sheet"
        ],
        support_aliases=[
            "Flattening must happen before sealing, and sealing before trimming."
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_tradition_innovation-transfer-2",
        passage=(
            "Bicycle-bag field-test table. Kept feature: a hand-block-printed "
            "mango-leaf border. New feature: a reflective edge strip. Night-test "
            "result: riders saw the bag sooner while the printed border remained "
            "visible."
        ),
        prompt=(
            "Explain how the design combines tradition with a purposeful change. "
            "Use the kept feature, new feature, and test result as evidence."
        ),
        model_answer=(
            "The makers retained the hand-block-printed mango-leaf border and "
            "added a reflective edge strip. Riders saw the bag sooner while the "
            "printed border remained visible, so the change served a new need "
            "without hiding the traditional design."
        ),
        core_aliases=[
            "retained the hand-block-printed mango-leaf border",
            "added a reflective edge strip",
            "riders saw the bag sooner while the printed border remained visible",
        ],
        support_aliases=["retained", "changed", "stated outcome"],
    )
    _set_open(
        activities,
        "eng_c5_ch10_community_effects-transfer-2",
        passage=(
            "Cooperative invoice trail: a clinic ordered 300 washable cloth "
            "masks -> the stitching unit added two paid shifts -> the thread shop "
            "supplied 40 extra spools and a cycle courier made three deliveries."
        ),
        prompt=(
            "Turn the invoice trail into a cause-and-effect explanation. Separate "
            "the direct worker effect from the supporting services in the record."
        ),
        model_answer=(
            "Because the clinic ordered 300 washable cloth masks, the stitching "
            "unit added two paid shifts. That order also meant that the thread "
            "shop supplied 40 extra spools and a cycle courier made three deliveries."
        ),
        core_aliases=[
            "the clinic ordered 300 washable cloth masks",
            "the stitching unit added two paid shifts",
        ],
        support_aliases=[
            "the thread shop supplied 40 extra spools and a cycle courier made three deliveries"
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_semantic_associations-transfer-2",
        passage=(
            "Word-lab sorting tray | pair: kiln + clay pot | candidate relation "
            "labels: place of making, synonym, opposite."
        ),
        prompt=(
            "Choose the meaningful relation label and explain how the two words "
            "connect. Use the sorting-tray details."
        ),
        model_answer=(
            "A kiln is meaningfully linked with a clay pot by place of making, "
            "because the pot is hardened inside the kiln. The words are not synonyms."
        ),
        core_aliases=["a kiln is meaningfully linked with a clay pot"],
        support_aliases=["the pot is hardened inside the kiln"],
    )
    _set_open(
        activities,
        "eng_c5_ch10_punctuation_editor-transfer-2",
        passage=(
            "Archive caption draft | speaker: Dr Mehta | exact words: the loom is ready"
        ),
        prompt=(
            "Rewrite the caption as a correctly punctuated quotation and explain "
            "one mark that makes the speaker's exact words clear."
        ),
        model_answer=(
            "Corrected caption: Dr Mehta said, \"The loom is ready.\" The comma "
            "introduces the quotation, and quotation marks enclose the exact words."
        ),
        core_aliases=["Dr Mehta said, \"The loom is ready.\""],
        support_aliases=[
            "The comma introduces the quotation, and quotation marks enclose the exact words."
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_past_perfect_sequence-transfer-2",
        passage=(
            "Repair-room timestamp strip: 14:05 - the technician disconnected "
            "the power; 14:20 - the supervisor opened the machine panel."
        ),
        prompt=(
            "Combine the timestamped events in one sentence, using past perfect "
            "for the earlier action and simple past for the later action. State "
            "the rule shown by the strip."
        ),
        model_answer=(
            "The technician had disconnected the power before the supervisor "
            "opened the machine panel. Had plus past participle marks the earlier "
            "completed action, while simple past marks the later action."
        ),
        core_aliases=[
            "The technician had disconnected the power before the supervisor opened the machine panel."
        ],
        support_aliases=[
            "Had plus past participle marks the earlier completed action, while simple past marks the later action."
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_procedure_writer-transfer-2",
        passage=(
            "Tool-library assembly cards for a cardboard cable holder. Actions: "
            "fold the side tabs; mark two slots; fasten the tabs; ask an adult to "
            "cut along the marks. Safety condition: the adult handles the craft knife."
        ),
        prompt=(
            "Write a usable procedure from the assembly cards. Include all four "
            "actions, sequence words, and the stated safety condition."
        ),
        model_answer=(
            "To make the cable holder, first mark two slots. Next, ask an adult "
            "to cut along the marks. Then, fold the side tabs. Finally, fasten "
            "the tabs. The adult must handle the craft knife."
        ),
        core_aliases=[
            "first mark two slots. Next, ask an adult to cut along the marks. Then, fold the side tabs. Finally, fasten the tabs"
        ],
        support_aliases=["The adult must handle the craft knife."],
    )
    _set_open(
        activities,
        "eng_c5_ch10_festival_recount-transfer-2",
        passage=(
            "Archive box for a neighbourhood lantern evening. 5:00 card: shaped "
            "paper shades. Dusk audio note: listened to residents tell lane "
            "stories. 8:00 photograph: carried battery lamps home. Reflection "
            "slip: shared light made unfamiliar lanes welcoming."
        ),
        prompt=(
            "Write a chronological recount from the archive items, with a clear "
            "opening, time links, the supplied reflection, and a closing sentence."
        ),
        model_answer=(
            "Recently, I joined a neighbourhood lantern evening. At 5:00, we "
            "shaped paper shades. At dusk, we listened to residents tell lane "
            "stories. By 8:00, we carried battery lamps home. I learned that "
            "shared light can make unfamiliar lanes feel welcoming."
        ),
        core_aliases=[
            "Recently, I joined a neighbourhood lantern evening."
        ],
        support_aliases=[
            "At 5:00, we shaped paper shades. At dusk, we listened to residents tell lane stories."
        ],
    )
    _set_open(
        activities,
        "eng_c5_ch10_craft_and_savings-transfer-2",
        passage=(
            "Savings-goal thermometer. Target: 500 rupees for a replacement "
            "science kit. Week 1 total: 70 rupees. Week 2 total: 150 rupees. "
            "Week 3 total: 240 rupees. Boundary note: no account, interest, or "
            "fee information is shown."
        ),
        prompt=(
            "Explain the saving idea demonstrated by the changing totals and one "
            "limit on what this thermometer proves. Use only the displayed record."
        ),
        model_answer=(
            "The recorded totals show progress toward a 500-rupee saving goal. "
            "The thermometer does not show account, interest, or fee information."
        ),
        core_aliases=[
            "the recorded totals show progress toward a 500-rupee saving goal"
        ],
        support_aliases=[
            "The thermometer does not show account, interest, or fee information."
        ],
    )


def _write_manifest(chapter_id: str) -> None:
    path = MANIFEST_ROOT / f"{chapter_id}.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["chapter"]["content_version"] = CONTENT_VERSION
    manifest["chapter"]["certification_version"] = CONTENT_VERSION
    if chapter_id == "eng_c5_ch09":
        _author_chapter_9(manifest)
        _author_chapter_9_transfer_twos(manifest)
    else:
        _author_chapter_10(manifest)
        _author_chapter_10_transfer_twos(manifest)
    _tighten_composite_claims(manifest)
    _clean_stage_copy(manifest)
    _apply_contextual_depth(manifest)
    lingering = [
        (activity.get("activity_id"), field_name)
        for activity in _all_activities(manifest)
        for field_name in ("teaching_block", "passage", "prompt")
        if STAGE_LABEL.search(activity.get(field_name, ""))
    ]
    assert not lingering, lingering
    path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    for chapter_id in CHAPTER_IDS:
        _write_manifest(chapter_id)


if __name__ == "__main__":
    main()
