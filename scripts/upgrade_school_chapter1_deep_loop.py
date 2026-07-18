#!/usr/bin/env python3
"""Repair Class 5 Chapter 1 within the canonical deep teaching contract.

The source chapter must already contain the authored nine-level gold structure
and reviewed Zidd-original checks. This script repairs that bank in place; it
does not reconstruct the nine-level chapter from the old six-level seed.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.content.school_rebuild_schema import LiveSchoolChapter


CHAPTER_PATH = (
    ROOT
    / "app/content/school_rebuild_chapters/english/class_5/eng_c5_ch01.json"
)
PDF_URL = "https://ncert.nic.in/textbook/pdf/eesa101.pdf"
EXPECTED_GOLD_LEVEL_IDS = (
    "papas_spectacles_poem_comprehension",
    "papas_spectacles_chapter_words",
    "papas_spectacles_personal_response",
    "papas_spectacles_order_and_pairs",
    "papas_spectacles_spelling_and_opposites",
    "papas_spectacles_prepositions",
    "papas_spectacles_poem_to_story",
    "papas_spectacles_sound_lab",
    "papas_spectacles_visual_fun_and_riddle",
)


SOURCE_ANCHORS = [
    {
        "anchor_id": "eng_c5_ch01:recite:1",
        "section_label": "Let us Recite",
        "page_start": 1,
        "page_end": 1,
        "source_url": f"{PDF_URL}#page=1",
        "coverage_treatment": "textbook_companion",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": "eng_c5_ch01:think:2-3",
        "section_label": "Let us Think",
        "page_start": 2,
        "page_end": 3,
        "source_url": f"{PDF_URL}#page=2",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": "eng_c5_ch01:learn:3-6",
        "section_label": "Let us Learn",
        "page_start": 3,
        "page_end": 6,
        "source_url": f"{PDF_URL}#page=3",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": "eng_c5_ch01:speak:7",
        "section_label": "Let us Speak",
        "page_start": 7,
        "page_end": 7,
        "source_url": f"{PDF_URL}#page=7",
        "coverage_treatment": "offline_group_activity",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": "eng_c5_ch01:listen:8",
        "section_label": "Let us Listen",
        "page_start": 8,
        "page_end": 8,
        "source_url": f"{PDF_URL}#page=8",
        "coverage_treatment": "guided_only",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": "eng_c5_ch01:write:8-9",
        "section_label": "Let us Write",
        "page_start": 8,
        "page_end": 9,
        "source_url": f"{PDF_URL}#page=8",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
]


LEVEL_META: dict[str, dict[str, Any]] = {
    "papas_spectacles_search_evidence": {
        "episode_kind": "comprehension_studio",
        "anchors": ["eng_c5_ch01:recite:1", "eng_c5_ch01:think:2-3"],
        "connect": (
            "A missing object is easiest to find when we retrace the last clear action.",
            "Isha put her sketch pen beside a plant, answered the door, and later searched her school bag.",
        ),
        "explain": (
            "Separate a stated detail from a guess. First name where the object was placed. Then use that action as evidence for the best place to check.",
            "A useful answer joins the object, its last action, and its location.",
        ),
        "model": (
            "Watch the evidence chain: object, last action, location, conclusion.",
            "Zoya slipped a receipt into a yellow cookbook before washing her hands. A careful reader checks the cookbook first because the placement action is stated directly.",
        ),
        "feedback": "Before moving on, check that your reason points to a detail in the passage rather than a random hiding place.",
    },
    "papas_spectacles_humour_and_reasons": {
        "episode_kind": "comprehension_studio",
        "anchors": [
            "eng_c5_ch01:recite:1",
            "eng_c5_ch01:think:2-3",
            "eng_c5_ch01:speak:7",
        ],
        "connect": (
            "Humour often comes from a gap between what a character believes and what the reader can notice.",
            "A coach searched for the whistle while it hung from the cord around his neck.",
        ),
        "explain": (
            "To explain a funny moment, state the character's mistaken belief and the contrasting fact. The contrast, not merely the event, creates the humour.",
            "A reason answer uses because to connect the mistaken search with the obvious location.",
        ),
        "model": (
            "Compare belief and reality in one clear explanation.",
            "Nani thinks her bookmark is lost, but it is still inside the book she is holding. The moment is funny because the object is already with her while she searches elsewhere.",
        ),
        "feedback": "Check that your explanation includes both sides of the contrast: the search and the already-visible object.",
    },
    "papas_spectacles_context_vocabulary": {
        "episode_kind": "language_lab",
        "anchors": ["eng_c5_ch01:recite:1", "eng_c5_ch01:learn:3-6"],
        "connect": (
            "A word's nearby action can reveal its meaning even when the word is new.",
            "Reva peered through the narrow gap, then stepped closer to see the label clearly.",
        ),
        "explain": (
            "Use the sentence before and after the word as clues. Replace the word with a possible meaning and test whether the whole sentence still makes sense.",
            "Context gives both meaning and the way a word is used in a complete sentence.",
        ),
        "model": (
            "Test a replacement word against the action.",
            "In 'Aman scanned the notice board and quickly found his name,' scanned means looked over carefully, not painted or carried.",
        ),
        "feedback": "Check the whole sentence after choosing a meaning; a good replacement keeps the original action sensible.",
    },
    "papas_spectacles_sequence_summary": {
        "episode_kind": "comprehension_studio",
        "anchors": [
            "eng_c5_ch01:recite:1",
            "eng_c5_ch01:think:2-3",
            "eng_c5_ch01:write:8-9",
        ],
        "connect": (
            "A useful summary keeps the problem, the important action or clue, and the result.",
            "A class badge went missing. Tara retraced the art-room visit, found it beside the paint tray, and returned it to the monitor.",
        ),
        "explain": (
            "Remove decorative details and keep the event chain in order: problem, evidence-based action, result. Use your own wording without inventing facts.",
            "A summary is shorter than the source but preserves its meaning and sequence.",
        ),
        "model": (
            "Compress three event parts into one ordered sentence.",
            "Source event: a lunch token was missing; Neel remembered using it near the canteen chart; he found it there. Summary: Neel retraced his last use of the missing token and recovered it near the canteen chart.",
        ),
        "feedback": "Check that your summary contains no new event and that the result comes after the useful clue or action.",
    },
    "papas_spectacles_precise_grammar": {
        "episode_kind": "language_lab",
        "anchors": ["eng_c5_ch01:learn:3-6"],
        "connect": (
            "Precise sentences tell who or what, what happened, and which detail makes the meaning exact.",
            "The alert librarian placed the torn atlas carefully on the repair shelf.",
        ),
        "explain": (
            "A noun names, a verb shows action or state, and an adjective describes a noun. Combining them in a complete sentence makes a search report useful.",
            "Word labels matter only when they help build clear meaning in a sentence.",
        ),
        "model": (
            "Build from facts instead of listing disconnected words.",
            "Facts: parcel; blue; slipped; under the counter. Sentence: The blue parcel slipped under the counter.",
        ),
        "feedback": "Read your sentence once for meaning: it needs a naming part, a complete action, and every required detail in a sensible order.",
    },
    "papas_spectacles_lost_found_writing": {
        "episode_kind": "expression_workshop",
        "anchors": ["eng_c5_ch01:think:2-3", "eng_c5_ch01:write:8-9"],
        "connect": (
            "A lost-and-found message succeeds when another person can identify the object and act safely.",
            "Found: a red lunch pouch with a rocket patch near the music room. Collect it from the school office after describing the name tag.",
        ),
        "explain": (
            "Include the object, one identifying detail, where or when it was found, and a safe collection point. Add a reason when the action needs explaining.",
            "Clear complete sentences are more useful than a list of vague words.",
        ),
        "model": (
            "Notice how each sentence answers a practical question.",
            "A silver water bottle with a green strap was found beside the library steps after lunch. The owner may collect it from the librarian after identifying the sticker.",
        ),
        "feedback": "Check whether a reader can identify the object, know where it was found, and understand exactly where to collect it.",
    },
}


NEW_VARIANTS: dict[str, list[dict[str, Any]]] = {
    "papas_spectacles_search_evidence": [
        {
            "id": "independent-b",
            "passage": "Meera copied a recipe, placed the cupboard key between the recipe pages, and went to answer the bell. Later she searched the key hook.",
            "prompt": "Where should Meera look first, and which action is the evidence?",
            "criteria": [
                ("recipe_location", "Names the recipe pages as the first place to look.", ["recipe pages", "between the pages", "in the recipe"]),
                ("placement_evidence", "Uses Meera's placement action as evidence.", ["placed the key", "put the key between", "left it in the recipe"]),
            ],
        },
        {
            "id": "transfer-b",
            "passage": "Arif used a compass to draw a circle, rested it in the open geometry box, and then packed only his notebook. At home he searched the notebook pocket.",
            "prompt": "Identify the best place to check and explain why.",
            "criteria": [
                ("geometry_box", "Identifies the open geometry box.", ["geometry box", "open box"]),
                ("last_action", "Connects the answer to where Arif rested the compass.", ["rested it", "put the compass", "left it"]),
            ],
        },
        {
            "id": "review-a",
            "passage": "Kabir placed a library slip behind the wall calendar while pinning a notice. Later he checked his wallet.",
            "prompt": "What should Kabir check first? Support the answer with the exact action clue.",
            "criteria": [
                ("calendar_location", "Names the space behind the wall calendar.", ["behind the calendar", "wall calendar"]),
                ("action_clue", "Uses the placement action.", ["placed the slip", "put it behind", "while pinning"]),
            ],
        },
        {
            "id": "review-b",
            "passage": "Leela tucked her bus token into a red coin purse before lending her backpack to a friend. She later searched the backpack.",
            "prompt": "Give the most evidence-based search location and reason.",
            "criteria": [
                ("purse_location", "Names the red coin purse.", ["red coin purse", "coin purse", "purse"]),
                ("tucked_evidence", "Explains that Leela tucked the token there.", ["tucked her bus token", "put the token", "placed it"]),
            ],
        },
    ],
    "papas_spectacles_humour_and_reasons": [
        {
            "id": "independent-b",
            "passage": "Uncle searched every drawer for the pencil he had pushed behind his ear while checking a shopping list.",
            "prompt": "Explain precisely why this situation is funny.",
            "criteria": [
                ("search_belief", "States that Uncle believes the pencil is missing.", ["searching", "thinks the pencil", "believes it is lost"]),
                ("visible_reality", "Contrasts the search with the pencil being behind his ear.", ["behind his ear", "already on him", "with him"]),
            ],
        },
        {
            "id": "transfer-b",
            "passage": "Auntie used her phone's torch to look under the sofa for the phone she thought she had misplaced.",
            "prompt": "Why does the reader understand the joke before Auntie does?",
            "criteria": [
                ("mistaken_search", "Identifies Auntie's mistaken search.", ["looking for the phone", "thinks it is misplaced", "searches under the sofa"]),
                ("phone_in_use", "Explains that she is already using the phone.", ["using the phone", "phone's torch", "already holding"]),
            ],
        },
        {
            "id": "review-a",
            "passage": "The goalkeeper asked who had taken his gloves while both gloves were tucked into the waistband behind him.",
            "prompt": "Use because to explain the humorous contrast.",
            "criteria": [
                ("asks_about_gloves", "States that he asks about the supposedly missing gloves.", ["asked who", "thinks the gloves", "searching for gloves"]),
                ("gloves_with_him", "States that the gloves are tucked into his own waistband.", ["waistband", "behind him", "with him"]),
            ],
        },
        {
            "id": "review-b",
            "passage": "Rina complained that her reading glasses were missing, then adjusted them on her nose to read the lost-item form.",
            "prompt": "Explain the mismatch that creates humour without merely retelling the event.",
            "criteria": [
                ("missing_claim", "Identifies Rina's belief that the glasses are missing.", ["says they are missing", "complained", "believes"]),
                ("wearing_reality", "Contrasts it with her wearing and using them.", ["on her nose", "adjusted them", "using them to read"]),
            ],
        },
    ],
    "papas_spectacles_context_vocabulary": [
        {
            "id": "independent-b",
            "passage": "The guard scanned each shelf slowly until he noticed the labelled parcel.",
            "prompt": "What does scanned mean here? Explain the context clue in a complete sentence.",
            "criteria": [
                ("scanned_meaning", "Gives the meaning looked over carefully.", ["looked over", "examined", "searched carefully"]),
                ("context_clue", "Uses each shelf or until he noticed as the clue.", ["each shelf", "until he noticed", "slowly"]),
            ],
        },
        {
            "id": "transfer-b",
            "passage": "Nakul peered through the fogged window, moving closer so that he could read the bus number.",
            "prompt": "Infer the meaning of peered and use it in a new complete sentence.",
            "criteria": [
                ("peered_meaning", "Shows that peered means looked closely or with difficulty.", ["looked closely", "looked carefully", "with difficulty"]),
                ("new_usage", "Uses peered as a looking action in a new sentence.", ["peered at", "peered through", "peered into"]),
            ],
        },
        {
            "id": "review-a",
            "passage": "Saba glanced at the clock and immediately returned to tying her shoes.",
            "prompt": "Explain what glanced means and which word shows that the look was brief.",
            "criteria": [
                ("glanced_meaning", "Explains glanced as a quick look.", ["quick look", "looked briefly", "short look"]),
                ("brief_clue", "Uses immediately returned as the clue.", ["immediately returned", "immediately", "returned to tying"]),
            ],
        },
        {
            "id": "review-b",
            "passage": "The frame around the photograph cracked, but the picture itself remained safe.",
            "prompt": "What does frame mean in this context? Use the word with the same meaning in a new sentence.",
            "criteria": [
                ("frame_meaning", "Identifies the border or holder around a picture.", ["border", "holder", "around the picture", "around a photograph"]),
                ("frame_usage", "Uses frame as a picture holder in a new sentence.", ["photo frame", "picture frame", "frame around"]),
            ],
        },
    ],
    "papas_spectacles_sequence_summary": [
        {
            "id": "independent-b",
            "passage": "A theatre ticket disappeared before the show. Uma remembered folding it inside the programme, checked there, and entered the hall on time.",
            "prompt": "Summarize the problem, evidence-based action, and result in one sentence.",
            "criteria": [
                ("problem", "Includes the missing theatre ticket.", ["ticket disappeared", "missing ticket", "lost ticket"]),
                ("action", "Includes checking the programme based on memory.", ["checked the programme", "inside the programme", "remembered folding"]),
                ("result", "Includes entering the hall on time.", ["entered the hall", "on time", "found it"]),
            ],
        },
        {
            "id": "transfer-b",
            "passage": "The class camera could not be found after assembly. Pari traced the photo team's route, discovered it near the stage steps, and handed it to the teacher.",
            "prompt": "Write a concise own-words summary that preserves the event order.",
            "criteria": [
                ("camera_problem", "Includes the missing class camera.", ["camera was missing", "could not find the camera", "lost camera"]),
                ("route_action", "Includes tracing the route or checking the stage.", ["traced the route", "stage steps", "photo team's route"]),
                ("teacher_result", "Includes finding and handing it to the teacher.", ["handed it to the teacher", "gave it to the teacher", "found it"]),
            ],
        },
        {
            "id": "review-a",
            "passage": "A seed packet fell from a project folder. Dev followed the paper trail, recovered it near the garden gate, and returned it to the group.",
            "prompt": "Summarize only the essential problem, action, and result.",
            "criteria": [
                ("packet_problem", "Includes the fallen or missing seed packet.", ["seed packet", "fell", "missing"]),
                ("trail_action", "Includes following the paper trail.", ["followed the paper trail", "paper trail", "garden gate"]),
                ("group_result", "Includes recovering and returning it.", ["returned it", "recovered it", "gave it to the group"]),
            ],
        },
        {
            "id": "review-b",
            "passage": "Mili misplaced a permission note. She recalled using it beside the printer, found it under a blank sheet there, and submitted it before class.",
            "prompt": "Write one ordered sentence that does not add any unstated detail.",
            "criteria": [
                ("note_problem", "Includes the misplaced permission note.", ["permission note", "misplaced", "missing"]),
                ("printer_clue", "Includes recalling or checking beside the printer.", ["beside the printer", "recalled using", "under a blank sheet"]),
                ("submitted_result", "Includes finding and submitting it.", ["submitted it", "found it", "before class"]),
            ],
        },
    ],
    "papas_spectacles_precise_grammar": [
        {
            "id": "independent-b",
            "passage": "Facts: parcel; narrow; slid; behind the wooden cabinet.",
            "prompt": "Write one complete sentence using the noun, adjective, verb, and exact location.",
            "criteria": [
                ("parcel_noun", "Uses parcel as the naming word.", ["parcel"]),
                ("narrow_adjective", "Uses narrow to describe the parcel.", ["narrow parcel"]),
                ("slid_verb", "Uses slid as the action.", ["slid"]),
                ("cabinet_location", "Includes behind the wooden cabinet.", ["behind the wooden cabinet", "behind the cabinet"]),
            ],
        },
        {
            "id": "transfer-b",
            "passage": "Facts: kitten; playful; carried; blue ribbon; beneath the table.",
            "prompt": "Combine every fact into one precise complete sentence.",
            "criteria": [
                ("kitten_noun", "Uses kitten as the naming word.", ["kitten"]),
                ("playful_adjective", "Uses playful to describe the kitten.", ["playful kitten"]),
                ("carried_verb", "Uses carried as the action.", ["carried"]),
                ("ribbon_object", "Includes the blue ribbon.", ["blue ribbon"]),
                ("table_location", "Includes beneath or under the table.", ["beneath the table", "under the table"]),
            ],
        },
        {
            "id": "review-a",
            "passage": "The careful monitor placed the cracked ruler inside the red supply box.",
            "prompt": "Name the noun, action verb, and one adjective, then explain which noun the adjective describes.",
            "criteria": [
                ("noun", "Names monitor, ruler, or box as a noun.", ["monitor", "ruler", "box"]),
                ("verb", "Names placed as the verb.", ["placed"]),
                ("adjective", "Names careful, cracked, red, or supply as a describing word.", ["careful", "cracked", "red"]),
                ("described_noun", "Links the adjective to the correct noun.", ["careful monitor", "cracked ruler", "red supply box"]),
            ],
        },
        {
            "id": "review-b",
            "passage": "Facts: bright scarf; fluttered; near the open window.",
            "prompt": "Turn the facts into one grammatical sentence and identify its action word.",
            "criteria": [
                ("bright_scarf", "Uses bright scarf as the noun phrase.", ["bright scarf"]),
                ("fluttered_action", "Uses and identifies fluttered as the action.", ["fluttered"]),
                ("window_location", "Includes near the open window.", ["near the open window", "by the open window"]),
            ],
        },
    ],
    "papas_spectacles_lost_found_writing": [
        {
            "id": "independent-b",
            "passage": "You find a black geometry pouch with a stitched orange star near the science lab after the final period. It is now with the lab assistant.",
            "prompt": "Write a 35 to 55 word lost-and-found notice with identifying and collection details.",
            "criteria": [
                ("object_detail", "Names the black geometry pouch and orange star.", ["black geometry pouch", "orange star", "geometry pouch"]),
                ("find_context", "Includes where or when it was found.", ["science lab", "final period", "after the final period"]),
                ("collection_point", "Directs the owner to the lab assistant.", ["lab assistant", "collect it from"]),
            ],
        },
        {
            "id": "transfer-b",
            "passage": "A silver identity-card holder marked '5B' is found on the auditorium stairs after rehearsal. The office keeps it so the owner can be checked safely.",
            "prompt": "Write a clear two-sentence message and explain the safe collection choice.",
            "criteria": [
                ("holder_identity", "Includes the silver holder and 5B mark.", ["silver", "5B", "identity-card holder", "ID card holder"]),
                ("stairs_context", "Includes auditorium stairs or rehearsal.", ["auditorium stairs", "after rehearsal", "rehearsal"]),
                ("office_collection", "Directs collection to the office.", ["office", "collect"]),
                ("safety_reason", "Explains that the office can verify the owner.", ["verify", "check the owner", "safe", "right owner"]),
            ],
        },
        {
            "id": "review-a",
            "passage": "Found: a small green diary with a peacock sticker beside the basketball court at lunch. The sports teacher has it.",
            "prompt": "Write a concise notice that lets the correct owner identify and collect the diary.",
            "criteria": [
                ("diary_details", "Includes the green diary and peacock sticker.", ["green diary", "peacock sticker", "diary"]),
                ("court_context", "Includes the basketball court or lunchtime.", ["basketball court", "at lunch", "lunchtime"]),
                ("teacher_collection", "Names the sports teacher as collection point.", ["sports teacher", "collect"]),
            ],
        },
        {
            "id": "review-b",
            "passage": "A blue raincoat labelled 'N. Rao' was left in the school bus after the morning trip. The transport desk is holding it.",
            "prompt": "Write two useful complete sentences for the lost-and-found board.",
            "criteria": [
                ("raincoat_identity", "Includes the blue raincoat and N. Rao label.", ["blue raincoat", "N. Rao", "labelled"]),
                ("bus_context", "Includes the school bus or morning trip.", ["school bus", "morning trip", "after the trip"]),
                ("desk_collection", "Names the transport desk as collection point.", ["transport desk", "collect"]),
            ],
        },
    ],
}


def _base_activity(
    *,
    level: dict[str, Any],
    meta: dict[str, Any],
    phase: str,
    teaching_block: str,
    passage: str,
    prompt: str,
) -> dict[str, Any]:
    return {
        "teaching_block": teaching_block,
        "passage": passage,
        "prompt": prompt,
        "options": [],
        "accepted_answers": [],
        "schema_version": "school-activity-v2",
        "episode_kind": meta["episode_kind"],
        "teaching_phase": phase,
        "interaction_type": "continue",
        "evidence_role": "experience",
        "source_anchor_ids": list(meta["anchors"]),
        "knowledge_components": list(level["skill_ids"]),
    }


def _continue_step(
    *,
    level: dict[str, Any],
    meta: dict[str, Any],
    phase: str,
    teaching_block: str,
    passage: str,
) -> dict[str, Any]:
    return {
        "step_id": f"{level['level_id']}:{phase}",
        "phase": phase,
        "required": True,
        "activity": _base_activity(
            level=level,
            meta=meta,
            phase=phase,
            teaching_block=teaching_block,
            passage=passage,
            prompt="Continue when you are ready for the next part.",
        ),
    }


def _adapt_check(
    *,
    level: dict[str, Any],
    meta: dict[str, Any],
    check: dict[str, Any],
    phase: str,
    evidence_role: str,
    pool_id: str,
    variant_id: str,
) -> dict[str, Any]:
    options = list(check.get("options") or [])
    payload: dict[str, Any] = {
        "teaching_block": str(check["teaching_block"]),
        "passage": str(check["passage"]),
        "prompt": str(check["prompt"]),
        "options": options,
        "accepted_answers": [],
        "pool_id": pool_id,
        "variant_id": variant_id,
        "schema_version": "school-activity-v2",
        "episode_kind": meta["episode_kind"],
        "teaching_phase": phase,
        "interaction_type": "single_choice" if options else "evidence_text",
        "evidence_role": evidence_role,
        "source_anchor_ids": list(meta["anchors"]),
        "knowledge_components": list(level["skill_ids"]),
    }
    if evidence_role == "certifying":
        payload["certifying_language"] = "en"
    if options:
        accepted = [
            answer
            for answer in check.get("accepted_answers") or []
            if answer in options
        ]
        if not accepted:
            raise ValueError(f"choice_check_has_no_literal_answer:{variant_id}")
        payload.update(
            accepted_answers=accepted,
            grading_mode="selected_option",
            response_mode="short",
        )
        return payload

    slots = [dict(slot) for slot in check.get("concept_slots") or []]
    authored_rubric = [
        dict(criterion) for criterion in check.get("rubric_criteria") or []
    ]
    if not authored_rubric:
        authored_rubric = [
            {
                "id": str(slot["id"]),
                "description": str(slot["description"]),
                "required": True,
                "min_quality": 0.7,
            }
            for slot in slots
        ]
    if not authored_rubric:
        raise ValueError(f"open_check_has_no_rubric:{variant_id}")
    prompt = str(check.get("prompt") or "")
    min_response_words = max(6, int(check.get("min_response_words") or 6))
    relevance_terms = list(check.get("relevance_terms") or [])
    if "pair" in prompt.casefold():
        # A complete sentence such as "A pair of shoes lay outside" is valid
        # evidence. Let the rubric judge its grammar and requested details.
        min_response_words = 6
    if not relevance_terms:
        relevance_terms = list(
            dict.fromkeys(
                term
                for slot in slots
                for term in slot.get("any_of") or []
            )
        )[:24]
    payload.update(
        accepted_answers=[],
        grading_mode="strict_open_rubric",
        response_mode="paragraph",
        evaluation_mode="llm_rubric",
        preflight_rule="relevant_english_response",
        pass_score=0.75 if evidence_role != "certifying" else 0.8,
        rubric_criteria=authored_rubric,
        concept_slots=slots or None,
        forbidden_phrases=list(check.get("forbidden_phrases") or []) or None,
        min_response_words=min_response_words,
        ordered_concept_slot_ids=(
            list(check.get("ordered_concept_slot_ids") or []) or None
        ),
        relevance_terms=relevance_terms or None,
    )
    return {key: value for key, value in payload.items() if value is not None}


def _new_open_activity(
    *,
    level: dict[str, Any],
    meta: dict[str, Any],
    phase: str,
    spec: dict[str, Any],
    pool_id: str,
) -> dict[str, Any]:
    criteria = list(spec["criteria"])
    return {
        "teaching_block": (
            "Work independently. Use only the details in this new passage and "
            "express the answer in your own words."
        ),
        "passage": spec["passage"],
        "prompt": spec["prompt"],
        "options": [],
        "accepted_answers": [],
        "grading_mode": "strict_open_rubric",
        "certifying_language": "en",
        "pool_id": pool_id,
        "variant_id": spec["id"],
        "response_mode": "paragraph",
        "evaluation_mode": "llm_rubric",
        "preflight_rule": "relevant_english_response",
        "pass_score": 0.8,
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": description,
                "required": True,
                "min_quality": 0.7,
            }
            for criterion_id, description, _ in criteria
        ],
        "concept_slots": [
            {
                "id": criterion_id,
                "description": description,
                "any_of": phrases,
            }
            for criterion_id, description, phrases in criteria
        ],
        "min_response_words": 6,
        "relevance_terms": list(
            dict.fromkeys(
                phrase
                for _, _, phrases in criteria
                for phrase in phrases
            )
        )[:24],
        "schema_version": "school-activity-v2",
        "episode_kind": meta["episode_kind"],
        "teaching_phase": phase,
        "interaction_type": "paragraph_text",
        "evidence_role": "certifying",
        "source_anchor_ids": list(meta["anchors"]),
        "knowledge_components": list(level["skill_ids"]),
    }


def _pool_step(
    *,
    level: dict[str, Any],
    phase: str,
    pool_id: str,
    variants: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "step_id": f"{level['level_id']}:{phase}",
        "phase": phase,
        "required": True,
        "pool_id": pool_id,
        "variant_pool": variants,
    }


def _build_steps(level: dict[str, Any]) -> list[dict[str, Any]]:
    level_id = str(level["level_id"])
    meta = LEVEL_META[level_id]
    checks = level["checks"]
    added = NEW_VARIANTS[level_id]
    independent_pool = f"{level_id}:independent"
    transfer_pool = f"{level_id}:transfer"
    review_pool = f"{level_id}:review"
    guided_pool = f"{level_id}:guided"
    connect_block, connect_passage = meta["connect"]
    explain_block, explain_passage = meta["explain"]
    model_block, model_passage = meta["model"]
    return [
        _continue_step(
            level=level,
            meta=meta,
            phase="connect",
            teaching_block=connect_block,
            passage=connect_passage,
        ),
        _continue_step(
            level=level,
            meta=meta,
            phase="explain",
            teaching_block=explain_block,
            passage=explain_passage,
        ),
        _continue_step(
            level=level,
            meta=meta,
            phase="model",
            teaching_block=model_block,
            passage=model_passage,
        ),
        {
            "step_id": f"{level_id}:co_construct",
            "phase": "co_construct",
            "required": True,
            "activity": _adapt_check(
                level=level,
                meta=meta,
                check=checks["guided_check"],
                phase="co_construct",
                evidence_role="formative",
                pool_id=f"{level_id}:co_construct",
                variant_id="co-construct-a",
            ),
        },
        _pool_step(
            level=level,
            phase="guided_practice",
            pool_id=guided_pool,
            variants=[
                _adapt_check(
                    level=level,
                    meta=meta,
                    check=checks["masterclass"],
                    phase="guided_practice",
                    evidence_role="supported",
                    pool_id=guided_pool,
                    variant_id="guided-a",
                ),
                _adapt_check(
                    level=level,
                    meta=meta,
                    check=checks["revision_level_3"],
                    phase="guided_practice",
                    evidence_role="supported",
                    pool_id=guided_pool,
                    variant_id="guided-b",
                ),
            ],
        ),
        _continue_step(
            level=level,
            meta=meta,
            phase="feedback",
            teaching_block=meta["feedback"],
            passage=(
                "Use the saved response and Zidd's feedback to name one thing "
                "to keep and one thing to improve before the no-hint check."
            ),
        ),
        _pool_step(
            level=level,
            phase="independent_application",
            pool_id=independent_pool,
            variants=[
                _adapt_check(
                    level=level,
                    meta=meta,
                    check=checks["independent_check"],
                    phase="independent_application",
                    evidence_role="certifying",
                    pool_id=independent_pool,
                    variant_id="independent-a",
                ),
                _new_open_activity(
                    level=level,
                    meta=meta,
                    phase="independent_application",
                    spec=added[0],
                    pool_id=independent_pool,
                ),
            ],
        ),
        _pool_step(
            level=level,
            phase="transfer",
            pool_id=transfer_pool,
            variants=[
                _adapt_check(
                    level=level,
                    meta=meta,
                    check=checks["transfer_check"],
                    phase="transfer",
                    evidence_role="certifying",
                    pool_id=transfer_pool,
                    variant_id="transfer-a",
                ),
                _new_open_activity(
                    level=level,
                    meta=meta,
                    phase="transfer",
                    spec=added[1],
                    pool_id=transfer_pool,
                ),
            ],
        ),
        _pool_step(
            level=level,
            phase="review",
            pool_id=review_pool,
            variants=[
                _new_open_activity(
                    level=level,
                    meta=meta,
                    phase="review",
                    spec=added[2],
                    pool_id=review_pool,
                ),
                _new_open_activity(
                    level=level,
                    meta=meta,
                    phase="review",
                    spec=added[3],
                    pool_id=review_pool,
                ),
            ],
        ),
    ]


PRODUCTION_SKILLS = {
    "grammar.connectors_because_and_but",
    "grammar.sentence_order",
    "vocab.chapter_word_usage",
    "writing.complete_sentence",
    "writing.reason_answer",
    "writing.short_answer",
    "writing.summary_own_words",
}


def _level(payload: dict[str, Any], level_id: str) -> dict[str, Any]:
    return next(
        level for level in payload["levels"] if level["level_id"] == level_id
    )


def _validate_nine_level_gold_prerequisite(payload: dict[str, Any]) -> None:
    levels = payload.get("levels")
    if not isinstance(levels, list):
        levels = []
    found_level_ids = tuple(
        str(level.get("level_id") or "<missing-level-id>")
        if isinstance(level, dict)
        else "<invalid-level>"
        for level in levels
    )
    complete_level_containers = all(
        isinstance(level, dict)
        and isinstance(level.get("teaching_steps"), list)
        and isinstance(level.get("checks"), dict)
        for level in levels
    )
    if (
        found_level_ids == EXPECTED_GOLD_LEVEL_IDS
        and complete_level_containers
    ):
        return

    missing_level_ids = tuple(
        level_id
        for level_id in EXPECTED_GOLD_LEVEL_IDS
        if level_id not in found_level_ids
    )
    raise ValueError(
        "chapter_one_nine_level_gold_structure_required: "
        "upgrade_school_chapter1_deep_loop repairs an already-authored "
        "nine-level gold chapter and does not reconstruct the old six-level "
        f"seed; expected_level_ids={EXPECTED_GOLD_LEVEL_IDS!r}; "
        f"found_level_ids={found_level_ids!r}; "
        f"missing_level_ids={missing_level_ids!r}"
    )


def _strict_open_support(
    level: dict[str, Any],
    check_name: str,
    *,
    prompt: str,
    model_answer: str,
    knowledge_components: list[str],
    relevance_terms: list[str],
    criterion_id: str,
    criterion_description: str,
    target_misconception_tags: list[str],
    min_response_words: int,
) -> None:
    check = level["checks"][check_name]
    authority = level["checks"]["independent_check"]
    for key in (
        "answer_rule",
        "concept_slots",
        "ordered_concept_slot_ids",
        "certifying_language",
    ):
        check.pop(key, None)
    check.update(
        {
            "interaction_type": "paragraph_text",
            "options": [],
            "accepted_answers": [],
            "grading_mode": "strict_open_rubric",
            "response_mode": "paragraph",
            "evaluation_mode": "llm_rubric",
            "preflight_rule": authority["preflight_rule"],
            "pass_score": authority["pass_score"],
            "prompt": prompt,
            "rubric_criteria": [
                {
                    "id": criterion_id,
                    "description": criterion_description,
                    "required": True,
                    "min_quality": 0.7,
                },
                {
                    "id": "clear_relevant_english",
                    "description": "The answer is relevant and clear in English.",
                    "required": True,
                    "min_quality": 0.6,
                },
            ],
            "min_response_words": min_response_words,
            "forbidden_phrases": list(authority["forbidden_phrases"]),
            "relevance_terms": relevance_terms,
            "model_answer": model_answer,
            "knowledge_components": knowledge_components,
            "target_misconception_tags": target_misconception_tags,
        }
    )


def _strict_open_assessment(
    item: dict[str, Any],
    *,
    prompt: str,
    model_answer: str,
    relevance_terms: list[str],
    criterion_id: str,
) -> None:
    for key in ("answer_rule", "concept_slots", "ordered_concept_slot_ids"):
        item.pop(key, None)
    item.update(
        {
            "prompt": prompt,
            "options": [],
            "accepted_answers": [],
            "grading_mode": "strict_open_rubric",
            "certifying_language": "en",
            "response_mode": "paragraph",
            "evaluation_mode": "llm_rubric",
            "preflight_rule": (
                "Write at least 8 relevant English words using both because "
                "and but."
            ),
            "pass_score": 0.75,
            "rubric_criteria": [
                {
                    "id": criterion_id,
                    "description": (
                        "Writes a relevant sentence that uses because for the "
                        "stated reason and but for the stated contrast."
                    ),
                    "required": True,
                    "min_quality": 0.7,
                },
                {
                    "id": "clear_relevant_english",
                    "description": "The answer is relevant and clear in English.",
                    "required": True,
                    "min_quality": 0.6,
                },
            ],
            "min_response_words": 8,
            "forbidden_phrases": [
                "A reason is unnecessary",
                "The contrast can be omitted",
            ],
            "relevance_terms": relevance_terms,
            "model_answer": model_answer,
        }
    )


def _repair_personal_response_checks(payload: dict[str, Any]) -> None:
    level = _level(payload, "papas_spectacles_personal_response")
    connector_skills = [
        "writing.short_answer",
        "writing.reason_answer",
        "grammar.connectors_because_and_but",
    ]
    connector_tags = [
        "unsupported_opinion",
        "situation_ignored",
        "missing_because",
        "missing_but",
    ]
    _strict_open_support(
        level,
        "bridge",
        prompt=(
            "Write one short response that uses because for Imran's search "
            "reason and but for a careful limit."
        ),
        model_answer=(
            "I would check the library table because Imran last used the ruler "
            "there, but I would not search every room at random."
        ),
        knowledge_components=connector_skills,
        relevance_terms=["Imran", "library table", "ruler"],
        criterion_id="personal_response_bridge_production",
        criterion_description=(
            "Writes a relevant short response with a reason introduced by "
            "because and a careful limit introduced by but."
        ),
        target_misconception_tags=connector_tags,
        min_response_words=10,
    )
    _strict_open_support(
        level,
        "masterclass",
        prompt=(
            "Write one short description that would help a classmate identify "
            "Tara's missing pouch."
        ),
        model_answer=(
            "Tara is looking for a small green pouch with a brass zip and her "
            "initials on one corner."
        ),
        knowledge_components=["writing.short_answer"],
        relevance_terms=["green pouch", "brass zip", "initials"],
        criterion_id="personal_response_masterclass_description",
        criterion_description=(
            "Writes a concise identifying description using the supplied pouch "
            "details."
        ),
        target_misconception_tags=["situation_ignored"],
        min_response_words=10,
    )
    _strict_open_support(
        level,
        "revision_level_1",
        prompt=(
            "Write one short search plan that uses because to connect the known "
            "location and but to set a responsible limit."
        ),
        model_answer=(
            "I would search beside the equipment cupboard because the register "
            "was signed there, but I would not open every school bag."
        ),
        knowledge_components=connector_skills,
        relevance_terms=["register", "equipment cupboard", "school bag"],
        criterion_id="personal_response_revision_1_production",
        criterion_description=(
            "Writes a focused search plan with the known reason after because "
            "and a responsible limit after but."
        ),
        target_misconception_tags=connector_tags,
        min_response_words=10,
    )
    _strict_open_support(
        level,
        "revision_level_2",
        prompt=(
            "Write one short piece of advice that uses because for the reason "
            "and but for what Naman should not do."
        ),
        model_answer=(
            "Naman should give the water bottle to the teacher because the owner "
            "may return, but he should not take it home."
        ),
        knowledge_components=connector_skills,
        relevance_terms=["water bottle", "teacher", "owner"],
        criterion_id="personal_response_revision_2_production",
        criterion_description=(
            "Writes responsible advice with the reason after because and the "
            "unsafe action after but."
        ),
        target_misconception_tags=connector_tags,
        min_response_words=10,
    )
    _strict_open_support(
        level,
        "revision_level_3",
        prompt=(
            "Write one short response that uses because to explain Sara's action "
            "and but to protect the owner's trust."
        ),
        model_answer=(
            "Sara moved the folder because the window was leaking, but she should "
            "not leave the owner uninformed."
        ),
        knowledge_components=connector_skills,
        relevance_terms=["Sara", "folder", "window"],
        criterion_id="personal_response_revision_3_production",
        criterion_description=(
            "Explains Sara's action after because and states the owner-facing "
            "limit after but."
        ),
        target_misconception_tags=connector_tags,
        min_response_words=10,
    )

    independent_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "independent_application"
    )
    clue_choice = next(
        activity
        for activity in independent_step["variant_pool"]
        if activity.get("variant_id")
        == "papas_spectacles_personal_response:independent_application:v4"
    )
    clue_choice.update(
        passage=(
            "A pencil was last used in the reading room. A friend only guesses "
            "that it may be in the art room."
        ),
        prompt=(
            "Which clue would you test first? Use because to connect your choice "
            "to the pencil's last-use fact and but to explain why the art-room "
            "claim is unsupported."
        ),
        model_answer=(
            "I would test the reading-room clue first because the pencil was last "
            "used there, but the art-room clue is only a guess."
        ),
        semantic_validator_id="evidence_over_unsupported_guess_v1",
        relevance_terms=[
            "pencil",
            "reading room",
            "last used",
            "art room",
            "only a guess",
        ],
        forbidden_phrases=[
            "No reason is needed",
            "The situation details do not matter",
            "art-room guess is best",
            "art room guess is best",
            "reading-room clue first seems useless",
            "reading room clue first seems useless",
        ],
    )


def _repair_preposition_remediation(payload: dict[str, Any]) -> None:
    level = _level(payload, "papas_spectacles_prepositions")
    _strict_open_support(
        level,
        "revision_level_3",
        prompt=(
            "Write one complete sentence that places the old banyan on the far "
            "side of the school gate. Use a precise preposition and grammatical "
            "sentence order."
        ),
        model_answer=(
            "The old banyan stands beyond the school gate, farther away from the "
            "campus."
        ),
        knowledge_components=[
            "grammar.prepositions",
            "grammar.sentence_order",
            "writing.complete_sentence",
        ],
        relevance_terms=["old banyan", "school gate", "farther away"],
        criterion_id="prepositions_revision_3_sentence_production",
        criterion_description=(
            "Writes a complete, grammatically ordered sentence with the precise "
            "preposition for the stated spatial relationship."
        ),
        target_misconception_tags=[
            "spatial_relation_reversed",
            "preposition_missing",
        ],
        min_response_words=9,
    )


def _repair_poem_to_story_checks(payload: dict[str, Any]) -> None:
    level = _level(payload, "papas_spectacles_poem_to_story")
    all_story_skills = [
        "writing.summary_own_words",
        "grammar.tense_usage",
        "writing.complete_sentence",
    ]
    all_story_tags = ["event_invented", "tense_shift", "sequence_lost"]
    _strict_open_support(
        level,
        "bridge",
        prompt=(
            "Retell the supplied setting in one complete past-tense sentence in "
            "your own words without inventing a new place."
        ),
        model_answer=(
            "Water gathered beside the flooded lane while the children watched "
            "from a doorstep."
        ),
        knowledge_components=all_story_skills,
        relevance_terms=["water", "flooded lane", "children"],
        criterion_id="poem_to_story_bridge_production",
        criterion_description=(
            "Retells the supplied setting in a complete past-tense sentence "
            "without inventing a different place."
        ),
        target_misconception_tags=all_story_tags,
        min_response_words=10,
    )
    _strict_open_support(
        level,
        "masterclass",
        prompt=(
            "Turn the three supplied kite events into a short past-tense story "
            "in your own words and keep their order."
        ),
        model_answer=(
            "The wind rose, and the kite string snapped before the kite dropped "
            "into a field."
        ),
        knowledge_components=all_story_skills,
        relevance_terms=["wind", "kite string", "field"],
        criterion_id="poem_to_story_masterclass_production",
        criterion_description=(
            "Writes complete past-tense prose that preserves all three supplied "
            "kite events in order."
        ),
        target_misconception_tags=all_story_tags,
        min_response_words=10,
    )
    level["checks"]["revision_level_1"]["passage"] = (
        "Draft facts: Mira; open the gate; walk into the garden."
    )
    _strict_open_support(
        level,
        "revision_level_1",
        prompt=(
            "Turn the draft facts into one complete sentence with every action "
            "in the past tense."
        ),
        model_answer=(
            "Mira opened the gate and walked into the garden before she looked "
            "along the path."
        ),
        knowledge_components=[
            "grammar.tense_usage",
            "writing.complete_sentence",
        ],
        relevance_terms=["Mira", "gate", "garden"],
        criterion_id="poem_to_story_revision_1_tense_production",
        criterion_description=(
            "Writes a complete sentence using the supplied actions consistently "
            "in the past tense."
        ),
        target_misconception_tags=["tense_shift"],
        min_response_words=10,
    )
    _strict_open_support(
        level,
        "revision_level_2",
        prompt=(
            "Retell the ribbon event briefly in your own words and include the "
            "supplied result without inventing a new ending."
        ),
        model_answer=(
            "A ribbon blew away, and a puppy chased it before bringing it back "
            "to Nia."
        ),
        knowledge_components=[
            "writing.summary_own_words",
            "writing.complete_sentence",
        ],
        relevance_terms=["ribbon", "puppy", "Nia"],
        criterion_id="poem_to_story_revision_2_summary_production",
        criterion_description=(
            "Retells the supplied event in a complete sentence and preserves the "
            "result without adding a different ending."
        ),
        target_misconception_tags=["event_invented"],
        min_response_words=10,
    )
    _strict_open_support(
        level,
        "revision_level_3",
        prompt=(
            "Retell Tara's lamp event as a short past-tense story in your own "
            "words and keep every action in order."
        ),
        model_answer=(
            "After a gust put out the lamp, Tara searched a drawer, found a "
            "candle, and lit it."
        ),
        knowledge_components=all_story_skills,
        relevance_terms=["gust", "Tara", "candle"],
        criterion_id="poem_to_story_revision_3_sequence_production",
        criterion_description=(
            "Writes complete past-tense prose that preserves Tara's supplied "
            "action sequence."
        ),
        target_misconception_tags=all_story_tags,
        min_response_words=10,
    )


def _repair_sound_word_usage_checks(payload: dict[str, Any]) -> None:
    level = _level(payload, "papas_spectacles_sound_lab")
    target_tags = [
        "target_word_copied_without_context",
        "word_meaning_not_demonstrated",
    ]
    _strict_open_support(
        level,
        "revision_level_2",
        prompt=(
            "Write one complete sentence using coat to show that it means "
            "clothing worn for warmth."
        ),
        model_answer="Meera wore a woollen coat during the cold walk.",
        knowledge_components=["vocab.chapter_word_usage"],
        relevance_terms=["coat", "warmth", "cold"],
        criterion_id="sound_lab_revision_2_word_production",
        criterion_description=(
            "Uses coat in a complete sentence whose context demonstrates its "
            "clothing meaning."
        ),
        target_misconception_tags=target_tags,
        min_response_words=8,
    )
    _strict_open_support(
        level,
        "revision_level_3",
        prompt=(
            "Write one complete sentence using ship to show that it carries "
            "people or goods across water."
        ),
        model_answer=(
            "The cargo ship crossed the harbour with boxes of fruit."
        ),
        knowledge_components=["vocab.chapter_word_usage"],
        relevance_terms=["ship", "goods", "water"],
        criterion_id="sound_lab_revision_3_word_production",
        criterion_description=(
            "Uses ship in a complete sentence whose context demonstrates the "
            "large-boat meaning."
        ),
        target_misconception_tags=target_tags,
        min_response_words=9,
    )


def _repair_connector_assessment(payload: dict[str, Any]) -> None:
    by_id = {
        item["item_id"]: item for item in payload["chapter_assessment"]["items"]
    }
    _strict_open_assessment(
        by_id["eng_c5_ch01:form_a:01:grammar_connectors_because_and_but"],
        prompt=(
            "Write one sentence that uses because for Rita's reason and but for "
            "the contrast shown in the passage."
        ),
        model_answer=(
            "Rita checked the shelf because she had placed the folder there, but "
            "the folder was not there."
        ),
        relevance_terms=["Rita", "shelf", "folder"],
        criterion_id="form_a_connector_production",
    )
    _strict_open_assessment(
        by_id["eng_c5_ch01:form_b:01:grammar_connectors_because_and_but"],
        prompt=(
            "Write one sentence that uses because for Aman's reason and but for "
            "the contrast shown in the passage."
        ),
        model_answer=(
            "Aman checked the balcony because he had used the spectacles there, "
            "but they were not on the chair."
        ),
        relevance_terms=["Aman", "balcony", "spectacles"],
        criterion_id="form_b_connector_production",
    )


def _repair_prompt_leaks(payload: dict[str, Any]) -> None:
    by_id = {
        item["item_id"]: item for item in payload["chapter_assessment"]["items"]
    }
    preposition = by_id["eng_c5_ch01:form_b:02:grammar_prepositions"]
    preposition["passage"] = "The blue card was tucked ____ the two red cards."
    preposition["prompt"] = (
        "Which preposition correctly completes the blue-card sentence?"
    )


_SEMANTIC_GENERIC_TERMS = {
    "answer",
    "because",
    "but",
    "complete sentence",
    "first",
    "i would",
    "location",
    "past tense",
    "reason",
    "sentence",
    "standard spelling",
    "word meaning",
    "written word",
}
_SEMANTIC_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "because",
    "but",
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
    "was",
    "were",
    "with",
}


def _normalized_phrase(value: str) -> str:
    return " ".join(value.casefold().split())


def _model_contains(model_answer: str, phrase: str) -> bool:
    normalized_model = _normalized_phrase(model_answer)
    normalized_phrase = _normalized_phrase(phrase)
    if not normalized_phrase:
        return False
    prefix = r"(?<!\w)" if normalized_phrase[0].isalnum() else ""
    suffix = r"(?!\w)" if normalized_phrase[-1].isalnum() else ""
    return (
        re.search(
            f"{prefix}{re.escape(normalized_phrase)}{suffix}",
            normalized_model,
        )
        is not None
    )


def _fallback_model_phrases(
    model_answer: str,
    existing: list[str],
) -> list[str]:
    words = [
        token.strip(".,;:!?()[]{}\"'")
        for token in model_answer.split()
    ]
    phrases: list[str] = []
    normalized_existing = {_normalized_phrase(item) for item in existing}
    for size in (3, 2):
        for index in range(len(words) - size + 1):
            phrase_words = words[index : index + size]
            if any(not word for word in phrase_words):
                continue
            if all(word.casefold() in _SEMANTIC_STOPWORDS for word in phrase_words):
                continue
            phrase = " ".join(phrase_words)
            normalized = _normalized_phrase(phrase)
            if any(
                normalized == known
                or normalized in known
                or known in normalized
                for known in normalized_existing
            ):
                continue
            phrases.append(phrase)
            normalized_existing.add(normalized)
            if len(phrases) >= 2:
                return phrases
    return phrases


def _semantic_aliases(authored: dict[str, Any]) -> list[str]:
    model_answer = str(authored.get("model_answer") or "")
    aliases: list[str] = []
    seen: set[str] = set()
    for raw_term in authored.get("relevance_terms") or []:
        term = str(raw_term).strip()
        normalized = _normalized_phrase(term)
        if (
            not term
            or normalized in _SEMANTIC_GENERIC_TERMS
            or normalized in seen
            or not _model_contains(model_answer, term)
        ):
            continue
        aliases.append(term)
        seen.add(normalized)
        if len(aliases) >= 3:
            break
    if len(aliases) < 2:
        for phrase in _fallback_model_phrases(model_answer, aliases):
            normalized = _normalized_phrase(phrase)
            if normalized in seen:
                continue
            aliases.append(phrase)
            seen.add(normalized)
            if len(aliases) >= 2:
                break
    if not aliases:
        raise ValueError(
            "strict_open_has_no_task_specific_semantic_alias:"
            + str(authored.get("variant_id") or authored.get("item_id"))
        )
    return aliases


def _semantic_authority_for(authored: dict[str, Any]) -> None:
    existing_criteria = list(authored.get("rubric_criteria") or [])
    primary = next(
        (
            criterion
            for criterion in existing_criteria
            if criterion["id"] != "clear_relevant_english"
        ),
        None,
    )
    if primary is None:
        raise ValueError(
            "strict_open_has_no_primary_rubric:"
            + str(authored.get("variant_id") or authored.get("item_id"))
        )
    aliases = _semantic_aliases(authored)
    criteria: list[dict[str, Any]] = []
    slots: list[dict[str, Any]] = []
    primary_id = str(primary["id"])
    for index, alias in enumerate(aliases):
        criterion_id = primary_id if index == 0 else f"{primary_id}:detail_{index + 1}"
        description = (
            str(primary["description"])
            if index == 0
            else (
                "Accurately includes the distinct task detail represented by "
                f"'{alias}', or a valid paraphrase grounded in the passage."
            )
        )
        criteria.append(
            {
                "id": criterion_id,
                "description": description,
                "required": True,
                "min_quality": float(primary.get("min_quality", 0.7)),
            }
        )
        slots.append(
            {
                "id": criterion_id,
                "description": description,
                "any_of": [alias],
            }
        )

    prompt = str(authored.get("prompt") or "").casefold()
    model_answer = str(authored.get("model_answer") or "").casefold()
    for connector, suffix, description in (
        (
            "because",
            "reason_link",
            "Uses because to connect the stated choice or claim to its reason.",
        ),
        (
            "but",
            "contrast_link",
            "Uses but to express the requested contrast or careful limit.",
        ),
    ):
        if connector not in prompt or connector not in model_answer:
            continue
        criterion_id = f"{primary_id}:{suffix}"
        criteria.append(
            {
                "id": criterion_id,
                "description": description,
                "required": True,
                "min_quality": 0.7,
            }
        )
        slots.append(
            {
                "id": criterion_id,
                "description": description,
                "any_of": [connector],
            }
        )

    clear = next(
        (
            criterion
            for criterion in existing_criteria
            if criterion["id"] == "clear_relevant_english"
        ),
        {
            "id": "clear_relevant_english",
            "description": "The answer is relevant and clear in English.",
            "required": True,
            "min_quality": 0.6,
        },
    )
    criteria.append(dict(clear))
    authored["rubric_criteria"] = criteria
    authored["concept_slots"] = slots
    authored.pop("ordered_concept_slot_ids", None)


def _repair_vocabulary_assessment_authority(payload: dict[str, Any]) -> None:
    by_id = {
        item["item_id"]: item for item in payload["chapter_assessment"]["items"]
    }
    specifications = {
        "eng_c5_ch01:form_a:11:vocab_chapter_word_usage": {
            "word": "glanced",
            "meaning_aliases": ["for a moment", "looked briefly", "brief look"],
            "meaning": "Uses context that shows a brief look rather than a sound or prolonged stare.",
            "forbidden": [
                "glanced means shouting",
                "glanced means yelling",
                "glanced means speaking loudly",
            ],
        },
        "eng_c5_ch01:form_b:11:vocab_chapter_word_usage": {
            "word": "hesitated",
            "meaning_aliases": ["unsure", "paused", "uncertain"],
            "meaning": "Uses context that shows a pause caused by uncertainty.",
            "forbidden": [
                "hesitated means rushed",
                "hesitated means moved immediately",
                "hesitated means certain",
            ],
        },
    }
    for item_id, specification in specifications.items():
        item = by_id[item_id]
        item["rubric_criteria"] = [
            {
                "id": "vocab_target_word",
                "description": (
                    f"Uses {specification['word']} as the target vocabulary word."
                ),
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "vocab_meaning_context",
                "description": specification["meaning"],
                "required": True,
                "min_quality": 0.75,
            },
            {
                "id": "clear_relevant_english",
                "description": "The answer is relevant and clear in English.",
                "required": True,
                "min_quality": 0.6,
            },
        ]
        item["concept_slots"] = [
            {
                "id": "vocab_target_word",
                "description": "Uses the named target vocabulary word.",
                "any_of": [specification["word"]],
            },
            {
                "id": "vocab_meaning_context",
                "description": specification["meaning"],
                "any_of": specification["meaning_aliases"],
            },
        ]
        item["forbidden_phrases"] = list(
            dict.fromkeys(
                [
                    *(item.get("forbidden_phrases") or []),
                    *specification["forbidden"],
                ]
            )
        )


def _repair_certifying_semantic_authority(payload: dict[str, Any]) -> None:
    authored: list[dict[str, Any]] = []
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
            authored.extend(
                activity
                for activity in activities
                if activity.get("grading_mode") == "strict_open_rubric"
                and activity.get("evidence_role") == "certifying"
            )
        authored.extend(
            check
            for check in level["checks"].values()
            if check.get("grading_mode") == "strict_open_rubric"
            and check.get("evidence_role") == "certifying"
        )
    authored.extend(
        item
        for item in payload["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    )
    if len(authored) != 110:
        raise ValueError(f"unexpected_chapter_one_certifying_open_count:{len(authored)}")
    for item in authored:
        _semantic_authority_for(item)
    _repair_vocabulary_assessment_authority(payload)


def _repair_poem_review_location_authority(payload: dict[str, Any]) -> None:
    """Do not require an unnecessary location noun for a supported inference."""

    level = _level(payload, "papas_spectacles_poem_comprehension")
    review_step = next(
        step
        for step in level["teaching_steps"]
        if step["step_id"] == "papas_spectacles_poem_comprehension:review"
    )
    activity = next(
        item
        for item in review_step["variant_pool"]
        if item["variant_id"] == "papas_spectacles_poem_comprehension:review:v1"
    )
    activity["prompt"] = (
        "Where should Leena look first? State the situation and use one "
        "passage detail to support your inference."
    )
    optional_desk = next(
        criterion
        for criterion in activity["rubric_criteria"]
        if criterion["id"] == "poem_comprehension_target:detail_3"
    )
    optional_desk.update(
        required=False,
        description=(
            "Optionally names the desk or an equivalent nearby search area; "
            "the exact noun is not required when the supported location is clear."
        ),
    )
    activity["concept_slots"] = [
        slot
        for slot in activity["concept_slots"]
        if slot["id"] != "poem_comprehension_target:detail_3"
    ]
    activity.get("criterion_misconception_tags", {}).pop(
        "poem_comprehension_target:detail_3",
        None,
    )


def _repair_personal_response_semantic_slots(payload: dict[str, Any]) -> None:
    level = _level(payload, "papas_spectacles_personal_response")
    authored_by_key: dict[str, dict[str, Any]] = {
        str(activity.get("variant_id")): activity
        for step in level["teaching_steps"]
        for activity in (
            [step["activity"]]
            if "activity" in step
            else step["variant_pool"]
        )
        if activity.get("variant_id")
    }
    authored_by_key["transfer_check"] = level["checks"]["transfer_check"]
    humour_review = authored_by_key[
        "papas_spectacles_personal_response:review:v2"
    ]
    humour_review.update(
        passage=(
            "During a classroom search, Kabir keeps asking where his pencil is "
            "while holding it in the same hand as his notebook. A child notices "
            "the mix-up and laughs, but Kabir looks embarrassed."
        ),
        prompt=(
            "How can you explain the humour and respond kindly? Use because for "
            "the reason and but for the kind, helpful, or no-mocking response."
        ),
        model_answer=(
            "I would explain that the moment is funny because Kabir is already "
            "holding the pencil he is searching for, but I would help him notice "
            "the pencil without mocking him."
        ),
        semantic_validator_id="affirmative_support_or_no_mocking_v1",
        relevance_terms=[
            "holding the pencil",
            "searching for",
            "because",
            "but",
            "help him notice",
            "without mocking",
        ],
        forbidden_phrases=[
            "No reason is needed",
            "The situation details do not matter",
            "not be kind to him",
            "never be kind to him",
            "refuse to be kind to him",
            "never treat him kindly",
            "never respond kindly",
            "respond without kindness",
            "would respond rudely",
            "be rude to him",
        ],
    )
    specifications = {
        "transfer_check": (
            "Grounds the fair suggestion in the unchecked bench clue or avoids "
            "blame without evidence.",
            ["water bottle", "not checked", "nobody has looked", "without evidence"],
        ),
        "papas_spectacles_personal_response:independent_application:v1": (
            "Grounds the search in the missing library card, its last use, or "
            "avoiding unrelated books.",
            ["library card", "last used", "unrelated books", "classmate"],
        ),
        "papas_spectacles_personal_response:independent_application:v3": (
            "Grounds the safe response in the unnamed bottle situation or the "
            "need to return it responsibly.",
            ["water bottle", "bottle", "name label", "owner", "return it", "stairs"],
        ),
        "papas_spectacles_personal_response:review:v1": (
            "Grounds the focused search plan in the recent route, last-used "
            "places, or the limit on repeating the same search.",
            [
                "recent route",
                "last used",
                "last-used places",
                "last used places",
                "better clues",
                "same drawer",
            ],
        ),
        "papas_spectacles_personal_response:review:v3": (
            "Grounds the choice in the last-placed clue or contrasts it with the "
            "random guess.",
            ["last placed", "last-placed clue", "strongest clue", "random guess"],
        ),
    }
    for key, (description, aliases) in specifications.items():
        authored = authored_by_key[key]
        detail_slot = next(
            slot
            for slot in authored["concept_slots"]
            if ":detail_" in str(slot.get("id") or "")
        )
        detail_criterion = next(
            criterion
            for criterion in authored["rubric_criteria"]
            if criterion["id"] == detail_slot["id"]
        )
        detail_slot.update(description=description, any_of=aliases)
        detail_criterion["description"] = description

    independent_slot_specs = {
        "papas_spectacles_personal_response:independent_application:v4": {
            "personal_response_target": (
                "Explicitly chooses the pencil's reading-room last-use clue as "
                "the first clue to test, uses because for the evidence, and "
                "uses but for the unsupported art-room claim.",
                [
                    "test the reading-room clue first",
                    "test the reading room clue first",
                    "choose the reading-room clue first",
                    "choose the reading room clue first",
                    "check the reading-room clue first",
                    "check the reading room clue first",
                    "start with the reading-room clue",
                    "start with the reading room clue",
                ],
            ),
            "personal_response_target:detail_2": (
                "States both the pencil and its last-use reading-room fact as "
                "evidence for the choice.",
                [
                    "pencil was last used in the reading room",
                    "pencil was last used there",
                    "pencil's last use was in the reading room",
                    "last used the pencil in the reading room",
                    "pencil was used last in the reading room",
                ],
            ),
            "personal_response_target:detail_3": (
                "Explicitly gives both the art-room claim and its unsupported "
                "polarity by calling it only a guess or unsupported.",
                [
                    "art-room clue is only a guess",
                    "art room clue is only a guess",
                    "art-room claim is only a guess",
                    "art room claim is only a guess",
                    "art-room claim is unsupported",
                    "art room claim is unsupported",
                    "art-room clue is unsupported",
                    "art room clue is unsupported",
                    "unsupported art-room claim",
                    "unsupported art room claim",
                    "unsupported art-room clue",
                    "unsupported art room clue",
                    "art-room guess is unsupported",
                    "art room guess is unsupported",
                ],
            ),
        },
        "papas_spectacles_personal_response:review:v2": {
            "personal_response_target": (
                "Explains both sides of the visible pencil-search mix-up: "
                "Kabir is searching for the pencil while already holding it, "
                "uses because for the reason, and uses but for the kind limit.",
                [
                    "already holding the pencil he is searching for",
                    "holding the pencil while searching for it",
                    "holding the pencil while searching",
                    "searching for the pencil he is holding",
                    "pencil he is searching for",
                    "pencil-search mix-up",
                ],
            ),
            "personal_response_target:detail_2": (
                "States one of three explicit positive responses: helps Kabir "
                "notice the pencil, explains the mix-up kindly, or refuses to "
                "mock him.",
                [
                    "help him",
                    "help Kabir",
                    "explain kindly",
                    "point out the pencil",
                    "point him",
                    "show him the pencil",
                    "show the pencil",
                    "guide him",
                    "guide Kabir",
                    "not mock him",
                    "never mock him",
                    "wouldn't mock him",
                    "won't mock him",
                    "no mocking",
                    "not make fun of him",
                    "never make fun of him",
                    "no making fun of him",
                ],
            ),
        },
    }
    for key, slot_specs in independent_slot_specs.items():
        authored = authored_by_key[key]
        for criterion_id, (description, aliases) in slot_specs.items():
            slot = next(
                (
                    item
                    for item in authored["concept_slots"]
                    if item["id"] == criterion_id
                ),
                None,
            )
            criterion = next(
                (
                    item
                    for item in authored["rubric_criteria"]
                    if item["id"] == criterion_id
                ),
                None,
            )
            if slot is None:
                slot = {"id": criterion_id, "description": "", "any_of": []}
                connector_index = next(
                    (
                        index
                        for index, item in enumerate(authored["concept_slots"])
                        if item["id"].endswith(":reason_link")
                    ),
                    len(authored["concept_slots"]),
                )
                authored["concept_slots"].insert(connector_index, slot)
            if criterion is None:
                criterion = {
                    "id": criterion_id,
                    "description": "",
                    "required": True,
                    "min_quality": 0.7,
                }
                connector_index = next(
                    (
                        index
                        for index, item in enumerate(authored["rubric_criteria"])
                        if item["id"].endswith(":reason_link")
                    ),
                    len(authored["rubric_criteria"]),
                )
                authored["rubric_criteria"].insert(connector_index, criterion)
            slot.update(description=description, any_of=aliases)
            criterion["description"] = description

        connector_ids = {
            item["id"]
            for item in authored["concept_slots"]
            if item["id"].endswith((":reason_link", ":contrast_link"))
        }
        owned_slot_ids = {*slot_specs, *connector_ids}
        authored["concept_slots"] = [
            item
            for item in authored["concept_slots"]
            if item["id"] in owned_slot_ids
        ]
        authored["rubric_criteria"] = [
            item
            for item in authored["rubric_criteria"]
            if item["id"] in owned_slot_ids
            or item["id"] == "clear_relevant_english"
        ]


def _repair_chapter_assessment_semantic_slots(payload: dict[str, Any]) -> None:
    assessment_by_id = {
        str(item["item_id"]): item
        for item in payload["chapter_assessment"]["items"]
    }
    specifications = {
        "eng_c5_ch01:form_a:15:writing_short_answer": {
            "writing_short_answer_evidence:detail_2": (
                "Hands the found object to a responsible adult or a recognized "
                "lost-and-found location.",
                [
                    "school office",
                    "teacher",
                    "lost-and-found",
                    "lost and found",
                    "trusted adult",
                ],
            ),
        },
        "eng_c5_ch01:form_a:16:writing_summary_own_words": {
            "writing_summary_own_words_evidence": (
                "Retells the essential problem, search, discovery, and return "
                "accurately in the learner's own words.",
                [
                    "lost card",
                    "losing a card",
                    "missing card",
                    "card went missing",
                ],
            ),
            "writing_summary_own_words_evidence:detail_2": (
                "Includes that the card was returned or given back.",
                [
                    "gave it back",
                    "returned it",
                    "returned the card",
                    "gave the card back",
                ],
            ),
        },
    }
    for item_id, slot_specs in specifications.items():
        item = assessment_by_id[item_id]
        slots = {
            str(slot["id"]): slot for slot in item["concept_slots"]
        }
        criteria = {
            str(criterion["id"]): criterion
            for criterion in item["rubric_criteria"]
        }
        for slot_id, (description, aliases) in slot_specs.items():
            slots[slot_id].update(description=description, any_of=aliases)
            criteria[slot_id]["description"] = description


def _repair_selected_option_skill_claims(payload: dict[str, Any]) -> None:
    selected_overrides = {
        "papas_spectacles_poem_comprehension:co_construct": [
            "reading.sentence_comprehension",
            "reading.inference_reason",
        ],
        "papas_spectacles_poem_comprehension:guided:v1": [
            "reading.inference_reason"
        ],
        "papas_spectacles_poem_comprehension:guided:v2": [
            "reading.paragraph_main_idea"
        ],
        "papas_spectacles_poem_comprehension:guided:v3": [
            "reading.sentence_comprehension",
            "reading.inference_reason",
        ],
        "papas_spectacles_poem_comprehension:guided:v4": [
            "reading.inference_reason"
        ],
        "papas_spectacles_chapter_words:co_construct": [
            "reading.word_meaning_context"
        ],
        "papas_spectacles_chapter_words:guided:v1": [],
        "papas_spectacles_chapter_words:guided:v2": [
            "reading.word_meaning_context"
        ],
        "papas_spectacles_chapter_words:guided:v3": [],
        "papas_spectacles_chapter_words:guided:v4": [],
        "papas_spectacles_order_and_pairs:co_construct": [
            "vocab.attribute_ordering"
        ],
        "papas_spectacles_order_and_pairs:guided:v1": [
            "vocab.attribute_ordering"
        ],
        "papas_spectacles_order_and_pairs:guided:v2": [
            "vocab.attribute_ordering"
        ],
        "papas_spectacles_order_and_pairs:guided:v3": [],
        "papas_spectacles_order_and_pairs:guided:v4": [],
        "papas_spectacles_poem_to_story:guided:v3": ["grammar.tense_usage"],
    }
    for level in payload["levels"]:
        level_id = str(level["level_id"])
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
            for activity in activities:
                if activity.get("grading_mode") != "selected_option":
                    continue
                activity_key = str(
                    activity.get("variant_id")
                    or f"{level_id}:{step['phase']}"
                )
                claimed = list(activity.get("knowledge_components") or [])
                activity["knowledge_components"] = list(
                    selected_overrides.get(
                        activity_key,
                        [
                            skill_id
                            for skill_id in claimed
                            if skill_id not in PRODUCTION_SKILLS
                        ],
                    )
                )
                if not activity["knowledge_components"]:
                    activity["evidence_role"] = "experience"

        for check in level["checks"].values():
            if check.get("grading_mode") != "selected_option":
                continue
            check["knowledge_components"] = [
                skill_id
                for skill_id in check.get("knowledge_components") or []
                if skill_id not in PRODUCTION_SKILLS
            ]
            if not check["knowledge_components"]:
                check["evidence_role"] = "experience"


def _repair_order_and_pairs_contract(payload: dict[str, Any]) -> None:
    level = _level(payload, "papas_spectacles_order_and_pairs")
    transfer_step = next(
        step for step in level["teaching_steps"] if step["phase"] == "transfer"
    )
    transfer = next(
        item
        for item in transfer_step["variant_pool"]
        if item["variant_id"] == "papas_spectacles_order_and_pairs:transfer:v3"
    )
    transfer.update(
        rubric_criteria=[
            {
                "id": "order_and_pairs_target",
                "description": (
                    "Uses a complete pair phrase accurately in an original sentence."
                ),
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "order_and_pairs_target:detail_2",
                "description": (
                    "Adds a clear location detail that tells where the pair is, was, "
                    "or stood."
                ),
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "clear_relevant_english",
                "description": (
                    "The response is relevant and communicates the idea in clear "
                    "English."
                ),
                "required": True,
                "min_quality": 0.6,
            },
        ],
        concept_slots=[
            {
                "id": "order_and_pairs_target",
                "description": (
                    "Uses a complete pair phrase accurately in an original sentence."
                ),
                "any_of": ["pair of"],
            },
            {
                "id": "order_and_pairs_target:detail_2",
                "description": (
                    "Adds a clear location detail that tells where the pair is, was, "
                    "or stood."
                ),
                "any_of": [
                    "beside",
                    "near",
                    "outside",
                    "inside",
                    "under",
                    "over",
                    "behind",
                    "by",
                    "at",
                    "in front of",
                    "next to",
                ],
            },
        ],
        relevance_terms=[
            "pair of",
            "beside",
            "near",
            "outside",
            "inside",
            "under",
            "behind",
            "in front of",
            "next to",
        ],
        target_misconception_tags=[
            "phrase_incomplete",
            "location_detail_missing",
        ],
    )

    support_specs = {
        "revision_level_1": {
            "passage": (
                "Two matching rain boots stand together near the classroom door."
            ),
            "prompt": (
                "Write one complete sentence using 'a pair of boots' and tell where "
                "the boots are."
            ),
            "pair_aliases": ["a pair of boots", "pair of boots", "pair of"],
            "location_aliases": ["near", "beside", "outside", "inside", "by", "at"],
            "model_answer": "A pair of boots stood near the classroom door.",
        },
        "revision_level_2": {
            "passage": "Two chopsticks are placed together beside a bowl.",
            "prompt": (
                "Write one complete sentence using 'a pair of chopsticks' and tell "
                "where they are."
            ),
            "pair_aliases": [
                "a pair of chopsticks",
                "pair of chopsticks",
                "pair of",
            ],
            "location_aliases": ["beside", "near", "inside", "outside", "by", "at"],
            "model_answer": "A pair of chopsticks rested beside the bowl.",
        },
    }
    for check_name, spec in support_specs.items():
        check = level["checks"][check_name]
        check.update(
            interaction_type="paragraph_text",
            evidence_role="supported",
            teaching_block=(
                "Build the phrase with pair of, then add a verb and a clear place."
            ),
            passage=spec["passage"],
            prompt=spec["prompt"],
            options=[],
            accepted_answers=[],
            grading_mode="strict_open_rubric",
            response_mode="paragraph",
            evaluation_mode="llm_rubric",
            preflight_rule="relevant_english_response",
            pass_score=0.75,
            rubric_criteria=[
                {
                    "id": "pair_phrase_support",
                    "description": (
                        "Uses the complete pair phrase requested by the support task."
                    ),
                    "required": True,
                    "min_quality": 0.7,
                },
                {
                    "id": "pair_phrase_support:location",
                    "description": "Adds a clear detail that tells where the pair is.",
                    "required": True,
                    "min_quality": 0.7,
                },
                {
                    "id": "clear_relevant_english",
                    "description": (
                        "The response is relevant and communicates the idea in clear "
                        "English."
                    ),
                    "required": True,
                    "min_quality": 0.6,
                },
            ],
            concept_slots=[
                {
                    "id": "pair_phrase_support",
                    "description": (
                        "Uses the complete pair phrase requested by the support task."
                    ),
                    "any_of": spec["pair_aliases"],
                },
                {
                    "id": "pair_phrase_support:location",
                    "description": "Adds a clear detail that tells where the pair is.",
                    "any_of": spec["location_aliases"],
                },
            ],
            min_response_words=6,
            forbidden_phrases=[
                "Order does not matter",
                "Any two words make a natural pair",
            ],
            relevance_terms=[*spec["pair_aliases"], *spec["location_aliases"]],
            model_answer=spec["model_answer"],
            knowledge_components=[
                "vocab.chapter_word_usage",
                "writing.complete_sentence",
            ],
            target_misconception_tags=[
                "phrase_incomplete",
                "location_detail_missing",
            ],
        )


def _repair_sound_word_use_teaching_contract(payload: dict[str, Any]) -> None:
    level = _level(payload, "papas_spectacles_sound_lab")
    for step in level["teaching_steps"]:
        activities = (
            [step["activity"]]
            if "activity" in step
            else step.get("variant_pool") or []
        )
        for activity in activities:
            if (
                activity.get("grading_mode") != "strict_open_rubric"
                or activity.get("knowledge_components")
                != ["vocab.chapter_word_usage"]
            ):
                continue
            rubric = list(activity.get("rubric_criteria") or [])
            primary = next(
                (
                    criterion
                    for criterion in rubric
                    if criterion.get("id") == "sound_lab_word_use_target"
                ),
                None,
            )
            if primary is None:
                continue
            slots = list(activity.get("concept_slots") or [])
            primary_slot = next(
                (
                    slot
                    for slot in slots
                    if slot.get("id") == "sound_lab_word_use_target"
                ),
                None,
            )
            if primary_slot is None:
                raise ValueError(
                    "sound_word_use_target_slot_missing:"
                    + str(activity.get("variant_id") or step.get("step_id") or "")
                )
            clear_english = next(
                (
                    criterion
                    for criterion in rubric
                    if criterion.get("id") == "clear_relevant_english"
                ),
                {
                    "id": "clear_relevant_english",
                    "description": (
                        "The response is relevant and communicates the idea in clear "
                        "English."
                    ),
                    "required": True,
                    "min_quality": 0.6,
                },
            )
            activity["rubric_criteria"] = [primary, clear_english]
            activity["concept_slots"] = [primary_slot]


def _repair_current_deep_loop(payload: dict[str, Any]) -> None:
    if payload.get("chapter_id") != "eng_c5_ch01":
        raise ValueError("unexpected_chapter_for_deep_loop_repair")
    source_anchors = json.dumps(payload.get("source_anchors"), sort_keys=True)
    _repair_learner_copy_labels(payload)
    _repair_personal_response_checks(payload)
    _repair_preposition_remediation(payload)
    _repair_poem_to_story_checks(payload)
    _repair_sound_word_usage_checks(payload)
    _repair_fresh_certifying_checks(payload)
    _repair_connector_assessment(payload)
    _repair_assessment_distractors(payload)
    _repair_assessment_transfer_cases(payload)
    _repair_prompt_leaks(payload)
    _repair_selected_option_skill_claims(payload)
    _repair_certifying_semantic_authority(payload)
    _repair_poem_review_location_authority(payload)
    _repair_personal_response_semantic_slots(payload)
    _repair_chapter_assessment_semantic_slots(payload)
    _repair_order_and_pairs_contract(payload)
    _repair_sound_word_use_teaching_contract(payload)
    if json.dumps(payload.get("source_anchors"), sort_keys=True) != source_anchors:
        raise RuntimeError("source_anchors_changed_during_residual_repair")


def _repair_fresh_certifying_checks(payload: dict[str, Any]) -> None:
    replacements = {
        "papas_spectacles_poem_comprehension": {
            "independent_check": {
                "passage": (
                    "During music practice, Dev searches the floor for a "
                    "drumstick that is resting across the drum in front of him."
                ),
                "prompt": "Explain the mistaken search and the clue that makes it humorous.",
                "model_answer": (
                    "Dev's search is humorous because the drumstick is already "
                    "resting across the drum in front of him."
                ),
                "relevance_terms": ["drumstick", "across the drum", "search"],
            },
            "transfer_check": {
                "passage": (
                    "On a bus, Meera asks everyone to look for her ticket while "
                    "it is tucked into the clear pocket of her badge holder."
                ),
                "prompt": "What can the reader infer before Meera does? Use the clue.",
                "model_answer": (
                    "The reader can infer that Meera already has the ticket because "
                    "it is visible in the clear pocket of her badge holder."
                ),
                "relevance_terms": ["ticket", "clear pocket", "badge holder"],
            },
        },
        "papas_spectacles_chapter_words": {
            "independent_check": {
                "passage": "Before crossing, Nita glanced at the signal and kept walking.",
                "prompt": "What does glanced mean here? Use glanced in a new sentence.",
                "model_answer": (
                    "Glanced means looked briefly. I glanced at the clock before "
                    "packing my school bag."
                ),
                "relevance_terms": ["glanced", "looked briefly", "clock"],
            },
            "transfer_check": {
                "passage": "After lunch, Kabir strolled along the quiet garden path.",
                "prompt": "Infer the meaning of strolled and use it in another setting.",
                "model_answer": (
                    "Strolled means walked slowly and calmly. We strolled beside "
                    "the lake after the picnic."
                ),
                "relevance_terms": ["strolled", "walked slowly", "lake"],
            },
        },
        "papas_spectacles_personal_response": {
            "independent_check": {
                "passage": (
                    "Your partner cannot find a notebook after using it beside "
                    "the science display."
                ),
                "prompt": (
                    "What should your partner do first? Use because for the reason "
                    "and but for a careful limit."
                ),
                "model_answer": (
                    "My partner should check beside the science display because the "
                    "notebook was last used there, but should not move other projects."
                ),
                "relevance_terms": ["science display", "notebook", "because", "but"],
            },
            "transfer_check": {
                "passage": (
                    "A teammate thinks a water bottle was taken, but the class has "
                    "not checked the bench beside the sports court."
                ),
                "prompt": (
                    "What would you suggest? Use because for the reason and but for "
                    "a fair contrast."
                ),
                "model_answer": (
                    "I would check the sports-court bench because nobody has looked "
                    "there, but I would not blame anyone without evidence."
                ),
                "relevance_terms": ["sports-court bench", "because", "but"],
            },
        },
        "papas_spectacles_prepositions": {
            "independent_check": {
                "passage": "The note slipped ____ the two library books.",
                "prompt": "Write one complete sentence and explain why the position word fits.",
                "model_answer": (
                    "The note slipped between the two library books because one book "
                    "was on each side of it."
                ),
                "relevance_terms": ["between", "library books", "note"],
            },
            "transfer_check": {
                "passage": "The puppy crawled ____ the low bench to reach its toy.",
                "prompt": "Write one complete sentence and explain the movement clearly.",
                "model_answer": (
                    "The puppy crawled under the low bench because it moved below the "
                    "seat to reach its toy."
                ),
                "relevance_terms": ["under", "bench", "puppy"],
            },
        },
        "papas_spectacles_poem_to_story": {
            "independent_check": {
                "passage": (
                    "Evening wind shook the gate; Mira found a rope; she tied the "
                    "loose latch; the gate stayed still."
                ),
                "prompt": "Turn these lines into a short, ordered past-tense story.",
                "model_answer": (
                    "The evening wind shook the gate. Mira found a rope, tied the "
                    "loose latch, and kept the gate still."
                ),
                "relevance_terms": ["wind", "Mira", "gate"],
            },
            "transfer_check": {
                "passage": (
                    "A paper boat met the rain; the stream began to rise; Imran lifted "
                    "the boat; he placed it safely on a step."
                ),
                "prompt": "Retell these events as a short past-tense story.",
                "model_answer": (
                    "Rain raised the stream around Imran's paper boat. He lifted the "
                    "boat and placed it safely on a step."
                ),
                "relevance_terms": ["paper boat", "stream", "Imran"],
            },
        },
        "papas_spectacles_sound_lab": {
            "independent_check": {
                "passage": "Complete the written word: s_ght. It means the ability to see.",
                "prompt": "Write the completed word and explain its meaning.",
                "model_answer": "The completed word is sight, which means the ability to see.",
                "relevance_terms": ["sight", "ability to see", "see"],
            },
            "transfer_check": {
                "passage": "Complete the written word: n_ght. It names the dark time after evening.",
                "prompt": "Write the completed word and use it in a sentence.",
                "model_answer": (
                    "The completed word is night, the dark time after evening. "
                    "We watched the stars at night."
                ),
                "relevance_terms": ["night", "dark time", "stars"],
            },
        },
        "papas_spectacles_visual_fun_and_riddle": {
            "independent_check": {
                "passage": "I have many pages but I am not a tree. I hold stories but I cannot speak.",
                "prompt": "What is the answer? Connect each clue to it.",
                "model_answer": (
                    "The answer is a book because it has pages and holds stories "
                    "without speaking."
                ),
                "relevance_terms": ["book", "pages", "stories"],
            },
            "transfer_check": {
                "passage": (
                    "A thin line of flour crosses the counter and ends beside the open sack."
                ),
                "prompt": "Where should the missing scoop be checked? Explain the clue.",
                "model_answer": (
                    "The scoop should be checked beside the open flour sack because "
                    "the line of flour ends there."
                ),
                "relevance_terms": ["scoop", "flour sack", "line of flour"],
            },
        },
    }
    for level_id, stage_replacements in replacements.items():
        level = _level(payload, level_id)
        for stage_name, replacement in stage_replacements.items():
            level["checks"][stage_name].update(replacement)


def _repair_learner_copy_labels(payload: dict[str, Any]) -> None:
    learner_copy_fields = {"teaching_block", "passage", "prompt", "teaching_goal"}
    prefix_pattern = re.compile(
        r"^(?:independent|transfer)\s+(?:check|checkpoint(?:\s+context)?)\s*:\s*",
        flags=re.IGNORECASE,
    )

    def clean(value: str) -> str:
        cleaned = prefix_pattern.sub("", value.strip())
        cleaned = cleaned.replace(
            " A listening check can happen later with real sound.",
            "",
        ).replace(
            " Save sound comparison for real audio or a real voice.",
            "",
        ).replace(
            "Separate creative exploration from certification.",
            "Keep creative exploration separate from this evidence question.",
        ).replace(
            "Your scored response",
            "Your answer",
        )
        if cleaned.casefold().count("explain") > 1:
            cleaned = re.sub(
                r"\s+Explain your response clearly\.$",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
        return cleaned.strip()

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in list(node.items()):
                if key in learner_copy_fields and isinstance(value, str):
                    node[key] = clean(value)
                else:
                    visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(payload)


def _repair_assessment_distractors(payload: dict[str, Any]) -> None:
    replacements = {
        "eng_c5_ch01:form_a:06:reading_paragraph_main_idea": [
            "Retracing a last action helps find a missing object.",
            "Mira should replace every item she cannot find immediately.",
            "The art room is the only useful place to search for belongings.",
            "Asking the bus driver is always the first step in a search.",
        ],
        "eng_c5_ch01:form_b:06:reading_paragraph_main_idea": [
            "A remembered action can guide an effective search.",
            "Kunal should search every room before using any clue.",
            "Science tools are most likely to be missing after lunch.",
            "A classmate's guess is stronger evidence than Kunal's last action.",
        ],
    }
    for item in payload["chapter_assessment"]["items"]:
        options = replacements.get(item["item_id"])
        if options is not None:
            item["options"] = options


def _repair_assessment_transfer_cases(payload: dict[str, Any]) -> None:
    items = {
        item["item_id"]: item for item in payload["chapter_assessment"]["items"]
    }

    sentence_order = items[
        "eng_c5_ch01:form_a:03:grammar_sentence_order"
    ]
    sentence_order.update(
        passage="Sentence parts: near the garden gate | waited | A delivery van.",
        prompt="Place the delivery-van parts in grammatical sentence order.",
    )
    sentence_order["concept_slots"] = [
        {
            "id": "slot_1",
            "description": "Position 1 is A delivery van.",
            "any_of": ["A delivery van"],
        },
        {
            "id": "slot_2",
            "description": "Position 2 is waited.",
            "any_of": ["waited"],
        },
        {
            "id": "slot_3",
            "description": "Position 3 is near the garden gate.",
            "any_of": ["near the garden gate"],
        },
    ]

    reason_answer = items[
        "eng_c5_ch01:form_a:14:writing_reason_answer"
    ]
    reason_answer.update(
        passage="A paintbrush was last used at the mural table.",
        prompt="Explain where to search first and support the answer with the clue.",
        model_answer=(
            "I would search at the mural table first because that is where the "
            "paintbrush was last used."
        ),
        relevance_terms=["paintbrush", "mural table", "last used", "search"],
    )
    reason_answer["concept_slots"][0].update(
        description="Names the missing paintbrush as the object being traced.",
        any_of=["paintbrush"],
    )
    reason_answer["concept_slots"][1].update(
        description="Uses the mural table as the last-known-location clue.",
        any_of=["mural table"],
    )
    reason_answer["rubric_criteria"][1]["description"] = (
        "Accurately uses the mural-table clue to justify the first search place."
    )

    attribute_order = items[
        "eng_c5_ch01:form_b:10:vocab_attribute_ordering"
    ]
    attribute_order.update(
        passage=(
            "Lengths in scrambled order: rope, twig, ribbon. The rope is 95 "
            "centimetres, the twig is 18 centimetres, and the ribbon is 42 "
            "centimetres."
        ),
        prompt="Place the three objects from shortest to longest.",
    )
    attribute_order["concept_slots"] = [
        {
            "id": "slot_1",
            "description": "Position 1 is twig.",
            "any_of": ["twig"],
        },
        {
            "id": "slot_2",
            "description": "Position 2 is ribbon.",
            "any_of": ["ribbon"],
        },
        {
            "id": "slot_3",
            "description": "Position 3 is rope.",
            "any_of": ["rope"],
        },
    ]


def _teaching_activities(level: dict[str, Any]) -> list[dict[str, Any]]:
    activities: list[dict[str, Any]] = []
    for step in level.get("teaching_steps") or []:
        if isinstance(step.get("activity"), dict):
            activities.append(step["activity"])
        activities.extend(
            item
            for item in step.get("variant_pool") or []
            if isinstance(item, dict)
        )
    return activities


def _author_pattern_meaning_choice(
    activity: dict[str, Any],
    *,
    passage: str,
    prompt: str,
    options: list[str],
    accepted_answer: str,
) -> None:
    for key in (
        "answer_rule",
        "evaluation_mode",
        "preflight_rule",
        "pass_score",
        "rubric_criteria",
        "concept_slots",
        "forbidden_phrases",
        "min_response_words",
        "ordered_concept_slot_ids",
        "model_answer",
        "relevance_terms",
        "wrong_answer_misconception_tags",
        "criterion_misconception_tags",
        "certifying_language",
    ):
        activity.pop(key, None)
    activity.update(
        teaching_block=(
            "Compare only the printed letters, then use each sentence to check "
            "what the two words mean."
        ),
        passage=passage,
        prompt=prompt,
        options=options,
        accepted_answers=[accepted_answer],
        grading_mode="selected_option",
        response_mode="short",
        interaction_type="single_choice",
        evidence_role="supported",
        knowledge_components=[
            "vocab.spelling",
            "reading.word_meaning_context",
        ],
        target_misconception_tags=[
            "letter_pattern_missed",
            "word_meaning_not_demonstrated",
        ],
    )


def _author_pattern_meaning_open(
    activity: dict[str, Any],
    *,
    phase: str,
    passage: str,
    prompt: str,
    model_answer: str,
    pattern_description: str,
    pattern_aliases: list[str],
    first_meaning_description: str,
    first_meaning_aliases: list[str],
    second_meaning_description: str,
    second_meaning_aliases: list[str],
    usage_word: str,
    usage_aliases: list[str],
    forbidden_phrases: list[str],
    criterion_prefix: str | None = None,
) -> None:
    if criterion_prefix is None:
        variant_id = str(activity["variant_id"])
        variant_suffix = variant_id.rsplit(":", 1)[-1].replace("-", "_")
        criterion_prefix = f"sound_lab_{phase}_{variant_suffix}"
    for key in (
        "answer_rule",
        "ordered_concept_slot_ids",
        "wrong_answer_misconception_tags",
        "criterion_misconception_tags",
    ):
        activity.pop(key, None)

    phase_blocks = {
        "independent_application": (
            "Work independently. Compare the printed letters, infer both "
            "meanings from the sentences, and prove one meaning in a fresh "
            "sentence."
        ),
        "transfer": (
            "Transfer the strategy to an unfamiliar pair and a new setting. "
            "Use printed letters and sentence context without making a sound "
            "claim."
        ),
        "review": (
            "Review the full strategy: name the written pattern, explain both "
            "contextual meanings, and use one word accurately in a new sentence."
        ),
    }
    criteria = [
        {
            "id": f"{criterion_prefix}_pattern",
            "description": pattern_description,
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": f"{criterion_prefix}_first_meaning",
            "description": first_meaning_description,
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": f"{criterion_prefix}_second_meaning",
            "description": second_meaning_description,
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": f"{criterion_prefix}_original_usage",
            "description": (
                f"Uses {usage_word} in an original complete sentence whose "
                "context demonstrates the intended meaning."
            ),
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": "clear_relevant_english",
            "description": (
                "The comparison and original sentence are relevant and clear "
                "in English."
            ),
            "required": True,
            "min_quality": 0.6,
        },
    ]
    slots = [
        {
            "id": f"{criterion_prefix}_pattern",
            "description": pattern_description,
            "any_of": pattern_aliases,
        },
        {
            "id": f"{criterion_prefix}_first_meaning",
            "description": first_meaning_description,
            "any_of": first_meaning_aliases,
        },
        {
            "id": f"{criterion_prefix}_second_meaning",
            "description": second_meaning_description,
            "any_of": second_meaning_aliases,
        },
    ]
    relevance_terms = list(
        dict.fromkeys(
            [
                *pattern_aliases,
                *first_meaning_aliases,
                *second_meaning_aliases,
                *usage_aliases,
            ]
        )
    )
    activity.update(
        teaching_block=phase_blocks[phase],
        passage=passage,
        prompt=prompt,
        options=[],
        accepted_answers=[],
        grading_mode="strict_open_rubric",
        certifying_language="en",
        response_mode="paragraph",
        evaluation_mode="llm_rubric",
        preflight_rule=(
            "Write at least 12 relevant English words that compare the written "
            "pattern, explain both meanings, and include one new complete sentence."
        ),
        pass_score=0.8,
        rubric_criteria=criteria,
        concept_slots=slots,
        forbidden_phrases=list(forbidden_phrases),
        min_response_words=12,
        relevance_terms=relevance_terms[:24],
        model_answer=model_answer,
        interaction_type="paragraph_text",
        evidence_role="certifying",
        knowledge_components=[
            "vocab.spelling",
            "reading.word_meaning_context",
            "vocab.chapter_word_usage",
        ],
        target_misconception_tags=[
            "letter_pattern_missed",
            "word_meaning_not_demonstrated",
            "target_word_copied_without_context",
        ],
    )


def _author_sound_pattern_meaning_level(level: dict[str, Any]) -> None:
    level.update(
        skill_ids=[
            "vocab.spelling",
            "reading.word_meaning_context",
            "vocab.chapter_word_usage",
        ],
        teaching_goal=(
            "Compare written letter patterns, infer precise word meanings from "
            "sentence context, and demonstrate meaning in original usage."
        ),
    )

    guided_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "guided_practice"
    )
    guided_by_id = {
        activity["variant_id"]: activity
        for activity in guided_step["variant_pool"]
    }
    guided_specs = {
        "papas_spectacles_sound_lab:guided:v1": {
            "passage": (
                "Ria used a pin to fasten her badge. Later she used a pen to "
                "sign the class list. In print, pin and pen differ only in the "
                "middle letter."
            ),
            "accepted": (
                "pin and pen differ in the middle; pin means a fastener and pen "
                "means a writing tool"
            ),
            "prompt": (
                "Which choice correctly compares the written pattern in pin and "
                "pen and each meaning shown by context?"
            ),
            "options": [
                "pin and pen share every letter; both mean a writing tool",
                "pin and pen differ in the middle; pin means a fastener and pen means a writing tool",
                "pin and pen differ at the end; both mean a fastener",
                "pin and pen look similar, so printed text proves the same pronunciation",
            ],
        },
        "papas_spectacles_sound_lab:guided:v2": {
            "passage": (
                "Aman wore a cap in the sun. His family hired a cab to reach "
                "the station. In print, cap and cab differ only in the final "
                "letter."
            ),
            "accepted": (
                "cap and cab differ at the end; cap means headwear and cab means "
                "a hired vehicle"
            ),
            "prompt": (
                "Which choice correctly compares the written pattern in cap and "
                "cab and each meaning shown by context?"
            ),
            "options": [
                "cap and cab differ at the end; cap means headwear and cab means a hired vehicle",
                "cap and cab differ in the middle; both mean headwear",
                "cap and cab share every letter; both mean a hired vehicle",
                "cap and cab look similar, so their meanings must match",
            ],
        },
        "papas_spectacles_sound_lab:guided:v3": {
            "passage": (
                "The lamp gave enough light to read. At night, the street grew "
                "quiet. In print, light and night share the ending -ight."
            ),
            "accepted": (
                "light and night share -ight; light means brightness and night "
                "means the dark hours"
            ),
            "prompt": (
                "Which choice correctly compares the written pattern in light "
                "and night and each meaning shown by context?"
            ),
            "options": [
                "light and night differ at the end; both mean darkness",
                "light and night share -ight; light means brightness and night means the dark hours",
                "light and night share every letter; both mean brightness",
                "light and night share -ight, so printed text proves identical pronunciation",
            ],
        },
        "papas_spectacles_sound_lab:guided:v4": {
            "passage": (
                "Neha buttoned her coat before the cold walk. A goat climbed a "
                "rocky ledge nearby. In print, coat and goat share the ending "
                "-oat."
            ),
            "accepted": (
                "coat and goat share -oat; coat means warm clothing, goat means "
                "a farm animal, and printed text does not prove pronunciation"
            ),
            "prompt": (
                "Which choice correctly compares the written pattern in coat and "
                "goat, each meaning, and the limit of printed evidence?"
            ),
            "options": [
                "coat and goat differ at the end; both mean an animal",
                "coat and goat share -oat; both mean warm clothing",
                "coat and goat share -oat; coat means warm clothing, goat means a farm animal, and printed text does not prove pronunciation",
                "coat and goat share an ending, so printed text proves how a speaker says them",
            ],
        },
    }
    for variant_id, spec in guided_specs.items():
        _author_pattern_meaning_choice(
            guided_by_id[variant_id],
            passage=spec["passage"],
            prompt=spec["prompt"],
            options=spec["options"],
            accepted_answer=spec["accepted"],
        )

    sound_forbidden_phrases = list(
        level["checks"]["independent_check"]["forbidden_phrases"]
    )
    open_specs: dict[str, dict[str, Any]] = {
        "papas_spectacles_sound_lab:independent_application:v1": {
            "passage": (
                "The reading lamp gave enough light for Asha to study. At "
                "night, the campsite became quiet. In print, light and night "
                "share the ending -ight."
            ),
            "prompt": (
                "Explain the written pattern and how both contexts show different "
                "meanings. Then use light in a new complete sentence."
            ),
            "model_answer": (
                "Light and night share the ending -ight. Light means brightness "
                "in the lamp sentence, while night means the dark hours after "
                "evening. A beam of light crossed my desk."
            ),
            "pattern": ["share the ending -ight", "share -ight"],
            "first": ["brightness", "lamp"],
            "second": ["dark hours", "after evening"],
            "usage_word": "light",
            "usage": ["beam of light", "light crossed my desk"],
        },
        "papas_spectacles_sound_lab:independent_application:v2": {
            "passage": (
                "Cold rain tapped the classroom window. The train arrived at "
                "platform two. In print, rain and train share the letter sequence "
                "rain, while train adds t at the start."
            ),
            "prompt": (
                "Explain the written pattern and how both contexts show different "
                "meanings. Then use train in a new complete sentence."
            ),
            "model_answer": (
                "Rain and train share the letters rain, while train adds t. Rain "
                "means water falling from clouds, while train means a rail vehicle. "
                "Our train crossed the bridge before noon."
            ),
            "pattern": ["share the letters rain", "train adds t"],
            "first": ["water falling from clouds", "rain tapped"],
            "second": ["rail vehicle", "train arrived"],
            "usage_word": "train",
            "usage": ["train crossed the bridge", "our train"],
        },
        "papas_spectacles_sound_lab:independent_application:v3": {
            "passage": (
                "Mira wore a coat during the cold walk. A goat balanced on a "
                "rock beside the path. In print, coat and goat share -oat but "
                "begin with different letters."
            ),
            "prompt": (
                "Explain the written pattern and both contextual meanings. Then "
                "use goat in a new complete sentence that makes its meaning clear."
            ),
            "model_answer": (
                "Coat and goat share -oat but begin with c and g. Coat means warm "
                "clothing, while goat means a farm animal. The young goat ate "
                "leaves beside the fence."
            ),
            "pattern": ["share -oat", "begin with c and g"],
            "first": ["warm clothing", "wore a coat"],
            "second": ["farm animal", "goat balanced"],
            "usage_word": "goat",
            "usage": ["young goat", "goat ate leaves"],
        },
        "papas_spectacles_sound_lab:independent_application:v4": {
            "passage": (
                "Leela fixed the notice with a pin. She labelled the folder with "
                "a pen. In print, pin and pen keep p and n but change the middle "
                "letter."
            ),
            "prompt": (
                "Explain the written pattern and both contextual meanings. Then "
                "use pen in a new complete sentence that makes its meaning clear."
            ),
            "model_answer": (
                "Pin and pen keep p and n but change i to e. Pin means a small "
                "fastener, while pen means an ink-writing tool. I used a red pen "
                "to mark the calendar."
            ),
            "pattern": ["change i to e", "keep p and n"],
            "first": ["small fastener", "fixed the notice"],
            "second": ["ink-writing tool", "labelled the folder"],
            "usage_word": "pen",
            "usage": ["red pen", "pen to mark"],
        },
        "papas_spectacles_sound_lab:transfer:v1": {
            "passage": (
                "Across the plain, rescue workers marked a safe landing strip. "
                "A plane circled above it. In print, plain and plane begin with "
                "pla but have different endings."
            ),
            "prompt": (
                "Explain the unfamiliar written pattern and infer both meanings "
                "from this rescue context. Then use plane in a new complete sentence."
            ),
            "model_answer": (
                "Plain and plane begin with pla but end differently. Plain means "
                "flat open land, while plane means an aircraft. The plane landed "
                "after the rescue team cleared the field."
            ),
            "pattern": ["begin with pla", "end differently"],
            "first": ["flat open land", "across the plain"],
            "second": ["aircraft", "plane circled"],
            "usage_word": "plane",
            "usage": ["plane landed", "rescue team"],
        },
        "papas_spectacles_sound_lab:transfer:v2": {
            "passage": (
                "At the science-and-farm exhibition, a model brain stood beside "
                "one grain of wheat under a lens. In print, brain and grain share "
                "-rain but begin with different letters."
            ),
            "prompt": (
                "Explain the unfamiliar written pattern and infer both meanings "
                "from the exhibition context. Then use grain in a new complete sentence."
            ),
            "model_answer": (
                "Brain and grain share -rain but begin with b and g. Brain means "
                "the thinking organ, while grain means a small cereal seed. One "
                "grain of rice remained in the bowl."
            ),
            "pattern": ["share -rain", "begin with b and g"],
            "first": ["thinking organ", "model brain"],
            "second": ["small cereal seed", "grain of wheat"],
            "usage_word": "grain",
            "usage": ["grain of rice", "grain remained"],
        },
        "papas_spectacles_sound_lab:transfer:v3": {
            "passage": (
                "After practice, the coach stored the footballs. In the biology "
                "lab, students observed a roach in a sealed case. In print, coach "
                "and roach share -oach but begin differently."
            ),
            "prompt": (
                "Explain the unfamiliar written pattern and infer both meanings "
                "from the two settings. Then use coach in a new complete sentence."
            ),
            "model_answer": (
                "Coach and roach share -oach but begin with c and r. Coach means "
                "a person who trains a team, while roach means an insect. Our coach "
                "planned a passing drill."
            ),
            "pattern": ["share -oach", "begin with c and r"],
            "first": ["trains a team", "coach stored"],
            "second": ["insect", "roach in a sealed case"],
            "usage_word": "coach",
            "usage": ["our coach", "planned a passing drill"],
        },
        "papas_spectacles_sound_lab:transfer:v4": {
            "passage": (
                "The airport board delayed one flight because of fog. A slight "
                "crack appeared in an empty display case nearby. In print, flight "
                "and slight share -light but begin differently."
            ),
            "prompt": (
                "Explain the unfamiliar written pattern and infer both meanings "
                "from the airport context. Then use slight in a new complete sentence."
            ),
            "model_answer": (
                "Flight and slight share -light but begin with f and s. Flight "
                "means a journey through the air, while slight means small or minor. "
                "A slight breeze moved the paper sign."
            ),
            "pattern": ["share -light", "begin with f and s"],
            "first": ["journey through the air", "flight delayed"],
            "second": ["small or minor", "slight crack"],
            "usage_word": "slight",
            "usage": ["slight breeze", "moved the paper sign"],
        },
        "papas_spectacles_sound_lab:review:v1": {
            "passage": (
                "Ravi chose the right answer after checking his work. At night, "
                "the moon rose above the field. In print, right and night share "
                "-ight but begin differently."
            ),
            "prompt": (
                "Explain the written pattern and both contextual meanings. Then "
                "use right in a new complete sentence that shows the same meaning."
            ),
            "model_answer": (
                "Right and night share -ight but begin with r and n. Right means "
                "correct, while night means the dark hours. Sana found the right "
                "total after adding again."
            ),
            "pattern": ["share -ight", "begin with r and n"],
            "first": ["correct", "right answer"],
            "second": [
                "dark hours",
                "dark part of the day",
                "dark time after day",
                "moon rose",
            ],
            "usage_word": "right",
            "usage": ["right total", "after adding again"],
        },
        "papas_spectacles_sound_lab:review:v2": {
            "passage": (
                "The ceiling fan moved air around the room. A delivery van waited "
                "outside. In print, fan and van keep -an but change the first letter."
            ),
            "prompt": (
                "Explain the written pattern and both contextual meanings. Then "
                "use van in a new complete sentence that shows its meaning."
            ),
            "model_answer": (
                "Fan and van share -an but begin with f and v. Fan means a device "
                "that moves air, while van means a road vehicle. The school van "
                "carried boxes to the hall."
            ),
            "pattern": ["share -an", "begin with f and v"],
            "first": ["device that moves air", "ceiling fan"],
            "second": ["road vehicle", "delivery van"],
            "usage_word": "van",
            "usage": ["school van", "carried boxes"],
        },
        "papas_spectacles_sound_lab:review:v3": {
            "passage": (
                "A cargo ship crossed the harbour. One chip broke from the edge "
                "of a clay bowl. In print, ship and chip share -hip but begin "
                "with different letters."
            ),
            "prompt": (
                "Explain the written pattern and both contextual meanings. Then "
                "use ship in a new complete sentence that shows its meaning."
            ),
            "model_answer": (
                "Ship and chip share -hip but begin with s and c. Ship means a "
                "large boat, while chip means a small broken piece. The rescue "
                "ship carried supplies across the bay."
            ),
            "pattern": ["share -hip", "begin with s and c"],
            "first": ["large boat", "cargo ship"],
            "second": ["small broken piece", "chip broke"],
            "usage_word": "ship",
            "usage": ["rescue ship", "carried supplies"],
        },
        "papas_spectacles_sound_lab:review:v4": {
            "passage": (
                "A flag stood at the top of the tower. A red sign told drivers "
                "to stop. In print, top and stop share the letters top, while stop "
                "adds s at the start."
            ),
            "prompt": (
                "Explain the written pattern and both contextual meanings. Then "
                "use top in a new complete sentence that shows its meaning."
            ),
            "model_answer": (
                "Top and stop share the letters top, while stop adds s. Top means "
                "the highest part, while stop means to halt. A weather vane turned "
                "at the top of the barn."
            ),
            "pattern": ["share the letters top", "stop adds s"],
            "first": ["highest part", "top of the tower"],
            "second": ["to halt", "told drivers to stop"],
            "usage_word": "top",
            "usage": ["top of the barn", "weather vane"],
        },
    }
    for step in level["teaching_steps"]:
        phase = str(step["phase"])
        if phase not in {"independent_application", "transfer", "review"}:
            continue
        for activity in step["variant_pool"]:
            spec = open_specs[activity["variant_id"]]
            _author_pattern_meaning_open(
                activity,
                phase=phase,
                passage=spec["passage"],
                prompt=spec["prompt"],
                model_answer=spec["model_answer"],
                pattern_description=(
                    "Accurately explains the compared written letter pattern "
                    "without claiming that print proves pronunciation."
                ),
                pattern_aliases=spec["pattern"],
                first_meaning_description=(
                    "Uses the first sentence context to explain the first word's "
                    "intended meaning."
                ),
                first_meaning_aliases=spec["first"],
                second_meaning_description=(
                    "Uses the second sentence context to explain the second word's "
                    "intended meaning."
                ),
                second_meaning_aliases=spec["second"],
                usage_word=spec["usage_word"],
                usage_aliases=spec["usage"],
                forbidden_phrases=sound_forbidden_phrases,
            )

    check_specs: dict[str, dict[str, Any]] = {
        "independent_check": {
            "phase": "independent_application",
            "passage": (
                "The telescope improved Mina's sight, so she could see a distant "
                "kite. At night, the park gates were locked. In print, sight and "
                "night share -ight but begin with different letters."
            ),
            "prompt": (
                "Explain the written pattern and how both contexts show different "
                "meanings. Then use sight in a new complete sentence."
            ),
            "model_answer": (
                "Sight and night share -ight but begin with s and n. Sight means "
                "the ability to see, while night means the dark hours after evening. "
                "The clear sky brought the mountain into sight."
            ),
            "pattern": ["share -ight", "begin with s and n"],
            "first": ["ability to see", "improved Mina's sight"],
            "second": ["dark hours", "at night"],
            "usage_word": "sight",
            "usage": ["into sight", "mountain into sight"],
        },
        "transfer_check": {
            "phase": "transfer",
            "passage": (
                "At the vision clinic, the chart tested Dev's sight. At a wildlife "
                "centre, a camera recorded the flight of a rescued eagle. In print, "
                "sight and flight end with -ight but begin differently."
            ),
            "prompt": (
                "Explain the written pattern and infer both meanings in this new "
                "context. Then use flight in a new complete sentence."
            ),
            "model_answer": (
                "Sight and flight end with -ight but begin differently. Sight means "
                "the ability to see, while flight means movement through the air. "
                "The eagle began its flight above the river."
            ),
            "pattern": ["end with -ight", "begin differently"],
            "first": ["ability to see", "chart tested Dev's sight"],
            "second": ["movement through the air", "flight of a rescued eagle"],
            "usage_word": "flight",
            "usage": ["began its flight", "above the river"],
        },
    }
    for check_name, spec in check_specs.items():
        _author_pattern_meaning_open(
            level["checks"][check_name],
            phase=spec["phase"],
            passage=spec["passage"],
            prompt=spec["prompt"],
            model_answer=spec["model_answer"],
            pattern_description=(
                "Accurately explains the compared written letter pattern without "
                "claiming that print proves pronunciation."
            ),
            pattern_aliases=spec["pattern"],
            first_meaning_description=(
                "Uses the first sentence context to explain the first word's "
                "intended meaning."
            ),
            first_meaning_aliases=spec["first"],
            second_meaning_description=(
                "Uses the second sentence context to explain the second word's "
                "intended meaning."
            ),
            second_meaning_aliases=spec["second"],
            usage_word=spec["usage_word"],
            usage_aliases=spec["usage"],
            forbidden_phrases=sound_forbidden_phrases,
            criterion_prefix=f"sound_lab_{check_name}",
        )


def _author_riddle_open_check(
    activity: dict[str, Any],
    *,
    passage: str,
    answer: str,
    answer_aliases: list[str],
    first_clue_aliases: list[str],
    second_clue_aliases: list[str],
    model_answer: str,
    prompt: str,
    forbidden_phrases: list[str],
) -> None:
    activity_id = str(
        activity.get("variant_id")
        or activity.get("activity_id")
        or "co_construct"
    )
    suffix = activity_id.rsplit(":", 1)[-1].replace("-", "_")
    prefix = f"visual_riddle_{suffix}"
    for key in (
        "answer_rule",
        "ordered_concept_slot_ids",
        "wrong_answer_misconception_tags",
        "criterion_misconception_tags",
        "certifying_language",
    ):
        activity.pop(key, None)
    criteria = [
        {
            "id": f"{prefix}_answer",
            "description": f"Identifies {answer} as the answer to the text riddle.",
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": f"{prefix}_first_clue",
            "description": "Explains how the first text clue supports the answer.",
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": f"{prefix}_second_clue",
            "description": "Explains how the second text clue supports the answer.",
            "required": True,
            "min_quality": 0.7,
        },
        {
            "id": "clear_relevant_english",
            "description": "The answer and clue-based justification are clear in English.",
            "required": True,
            "min_quality": 0.6,
        },
    ]
    slots = [
        {
            "id": f"{prefix}_answer",
            "description": f"Identifies {answer} as the answer to the text riddle.",
            "any_of": answer_aliases,
        },
        {
            "id": f"{prefix}_first_clue",
            "description": "Explains how the first text clue supports the answer.",
            "any_of": first_clue_aliases,
        },
        {
            "id": f"{prefix}_second_clue",
            "description": "Explains how the second text clue supports the answer.",
            "any_of": second_clue_aliases,
        },
    ]
    relevance_terms = list(
        dict.fromkeys(
            [*answer_aliases, *first_clue_aliases, *second_clue_aliases]
        )
    )
    activity.update(
        teaching_block=(
            "Test one answer against both text clues. A complete response names "
            "the object and justifies why every clue fits."
        ),
        passage=passage,
        prompt=prompt,
        options=[],
        accepted_answers=[],
        grading_mode="strict_open_rubric",
        response_mode="paragraph",
        evaluation_mode="llm_rubric",
        preflight_rule=(
            "Write at least 8 relevant English words that name one answer and "
            "explain both supplied clues."
        ),
        pass_score=0.75,
        rubric_criteria=criteria,
        concept_slots=slots,
        forbidden_phrases=list(forbidden_phrases),
        min_response_words=8,
        relevance_terms=relevance_terms,
        model_answer=model_answer,
        interaction_type="paragraph_text",
        knowledge_components=[
            "reading.inference_reason",
            "writing.short_answer",
        ],
        target_misconception_tags=["guess_without_clue"],
    )


def _author_visual_riddle_guidance(level: dict[str, Any]) -> None:
    riddle_forbidden_phrases = list(
        level["checks"]["independent_check"]["forbidden_phrases"]
    )
    connect = next(
        step["activity"]
        for step in level["teaching_steps"]
        if step["phase"] == "connect"
    )
    connect.update(
        teaching_block=(
            "Text riddles reward careful matching between every clue and one "
            "defensible answer."
        ),
        passage=(
            "No picture is needed. Test each clue against one answer and reject "
            "an answer if even one clue conflicts.\n\n"
            "Worked example riddle: On a picnic table, I have a narrow neck but "
            "no head, and I keep water from spilling though I have no hands. "
            "What am I?\n"
            "Model answer: A bottle. Its narrow neck fits the first clue, and "
            "holding water without hands fits the second clue."
        ),
        prompt=(
            "Notice how the model checks one answer against both clues. Continue "
            "when the justification is clear."
        ),
    )

    co_construct = next(
        step["activity"]
        for step in level["teaching_steps"]
        if step["phase"] == "co_construct"
    )
    _author_riddle_open_check(
        co_construct,
        passage=(
            "I carry many teeth in a straight row but never bite. I move through "
            "tangled hair and leave it neat."
        ),
        answer="a comb",
        answer_aliases=["comb"],
        first_clue_aliases=["teeth in a straight row", "many teeth"],
        second_clue_aliases=["tangled hair", "leave it neat"],
        model_answer=(
            "The answer is a comb because it has many teeth in a straight row "
            "but cannot bite, and it moves through tangled hair and leaves it neat."
        ),
        prompt=(
            "What is the answer? Explain how the teeth clue and the hair clue "
            "both support it."
        ),
        forbidden_phrases=riddle_forbidden_phrases,
    )

    guided_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "guided_practice"
    )
    guided_by_id = {
        activity["variant_id"]: activity
        for activity in guided_step["variant_pool"]
    }
    guided_specs = {
        "papas_spectacles_visual_fun_and_riddle:guided:v1": {
            "passage": (
                "Each time I help fill a notebook with words, I become a little "
                "shorter. I have a wooden body but no branches."
            ),
            "answer": "a pencil",
            "answer_aliases": ["pencil"],
            "first": ["become shorter", "fill a notebook"],
            "second": ["wooden body", "no branches"],
            "model_answer": (
                "The answer is a pencil because it can fill a notebook with words "
                "and become shorter as it writes; its wooden body has no branches."
            ),
            "prompt": (
                "Name the answer and explain how the shorter clue and wooden-body "
                "clue work together."
            ),
        },
        "papas_spectacles_visual_fun_and_riddle:guided:v2": {
            "passage": (
                "I stay in the top corner of an envelope while the envelope "
                "crosses cities. A printed value appears on my face."
            ),
            "answer": "a postage stamp",
            "answer_aliases": ["postage stamp", "stamp"],
            "first": ["corner of an envelope", "crosses cities"],
            "second": ["printed value", "on my face"],
            "model_answer": (
                "The answer is a postage stamp because it stays in the corner of "
                "an envelope while the envelope crosses cities, and it has a "
                "printed value on its face."
            ),
            "prompt": (
                "Name the answer and explain how the envelope-corner clue and "
                "printed-value clue support it."
            ),
        },
        "papas_spectacles_visual_fun_and_riddle:guided:v3": {
            "passage": (
                "I have black and white keys but open no locks. Pressing my keys "
                "can fill a room with music."
            ),
            "answer": "a piano",
            "answer_aliases": ["piano"],
            "first": ["black and white keys", "open no locks"],
            "second": ["fill a room with music", "pressing my keys"],
            "model_answer": (
                "The answer is a piano because its black and white keys open no "
                "locks, and pressing its keys can fill a room with music."
            ),
            "prompt": (
                "Name the answer and explain how the no-lock clue and music clue "
                "support it."
            ),
        },
        "papas_spectacles_visual_fun_and_riddle:guided:v4": {
            "passage": (
                "I open into a small roof when rain begins. When the sky clears, "
                "I fold into a narrow stick that can be carried."
            ),
            "answer": "an umbrella",
            "answer_aliases": ["umbrella"],
            "first": ["small roof", "rain begins"],
            "second": ["fold into a narrow stick", "can be carried"],
            "model_answer": (
                "The answer is an umbrella because it opens into a small roof when "
                "rain begins, then can fold into a narrow stick and can be carried."
            ),
            "prompt": (
                "Name the answer and explain how the rain-roof clue and folding "
                "clue support it."
            ),
        },
    }
    for variant_id, spec in guided_specs.items():
        _author_riddle_open_check(
            guided_by_id[variant_id],
            passage=spec["passage"],
            answer=spec["answer"],
            answer_aliases=spec["answer_aliases"],
            first_clue_aliases=spec["first"],
            second_clue_aliases=spec["second"],
            model_answer=spec["model_answer"],
            prompt=spec["prompt"],
            forbidden_phrases=riddle_forbidden_phrases,
        )

    transfer_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "transfer"
    )
    umbrella = next(
        activity
        for activity in transfer_step["variant_pool"]
        if activity["variant_id"].endswith(":v1")
    )
    for key in (
        "answer_rule",
        "ordered_concept_slot_ids",
        "wrong_answer_misconception_tags",
        "criterion_misconception_tags",
    ):
        umbrella.pop(key, None)
    umbrella.update(
        teaching_block=(
            "Transfer clue reasoning to a new location. Link an explicit placement "
            "action with a later visible result before inferring where to check."
        ),
        passage=(
            "At the community library entrance, Noor placed her striped umbrella "
            "in the drying rack before walking to the reading room. When she "
            "returned, its curved red handle was still visible above the same rack."
        ),
        prompt=(
            "Where should Noor check first? Explain how the two clues support one "
            "location."
        ),
        options=[],
        accepted_answers=[],
        grading_mode="strict_open_rubric",
        certifying_language="en",
        response_mode="paragraph",
        evaluation_mode="llm_rubric",
        preflight_rule=(
            "Write at least 10 relevant English words that identify one location "
            "and explain both supplied clues."
        ),
        pass_score=0.8,
        rubric_criteria=[
            {
                "id": "umbrella_transfer_location",
                "description": "Identifies the drying rack as the one defensible place to check.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "umbrella_transfer_placement_clue",
                "description": "Uses the clue that Noor placed the striped umbrella in the rack.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "umbrella_transfer_visible_clue",
                "description": "Uses the clue that its curved red handle remains visible above that rack.",
                "required": True,
                "min_quality": 0.7,
            },
            {
                "id": "clear_relevant_english",
                "description": "The location inference and two-clue explanation are clear in English.",
                "required": True,
                "min_quality": 0.6,
            },
        ],
        concept_slots=[
            {
                "id": "umbrella_transfer_location",
                "description": "Identifies the drying rack as the one defensible place to check.",
                "any_of": ["drying rack", "same rack"],
            },
            {
                "id": "umbrella_transfer_placement_clue",
                "description": "Uses the clue that Noor placed the striped umbrella in the rack.",
                "any_of": ["placed her striped umbrella", "placed it in the rack"],
            },
            {
                "id": "umbrella_transfer_visible_clue",
                "description": "Uses the clue that its curved red handle remains visible above that rack.",
                "any_of": ["curved red handle", "handle was still visible"],
            },
        ],
        forbidden_phrases=riddle_forbidden_phrases,
        min_response_words=10,
        relevance_terms=[
            "drying rack",
            "placed her striped umbrella",
            "curved red handle",
        ],
        model_answer=(
            "Noor should check the drying rack because she placed her striped "
            "umbrella there and its curved red handle is still visible above that rack."
        ),
        interaction_type="paragraph_text",
        evidence_role="certifying",
        knowledge_components=[
            "reading.inference_reason",
            "writing.short_answer",
            "vocab.chapter_word_usage",
        ],
        target_misconception_tags=[
            "guess_without_clue",
            "optional_asset_treated_as_required",
        ],
    )


def _author_chapter_one_remediation_targets(payload: dict[str, Any]) -> None:
    levels = {level["level_id"]: level for level in payload["levels"]}
    comprehension = levels["papas_spectacles_poem_comprehension"]
    all_comprehension_tags = [
        "unsupported_inference",
        "missed_humorous_contrast",
        "main_idea_replaced_by_detail",
    ]

    transfer_step = next(
        step
        for step in comprehension["teaching_steps"]
        if step["phase"] == "transfer"
    )
    transfer_by_id = {
        activity["variant_id"]: activity
        for activity in transfer_step["variant_pool"]
    }
    gardener = transfer_by_id[
        "papas_spectacles_poem_comprehension:transfer:v2"
    ]
    gardener_detail_slot = next(
        slot
        for slot in gardener["concept_slots"]
        if slot["id"] == "poem_comprehension_target:detail_2"
    )
    gardener_detail_slot["any_of"] = ["seed label", "label"]

    curtain = transfer_by_id[
        "papas_spectacles_poem_comprehension:transfer:v1"
    ]
    curtain.update(
        passage=(
            "During rehearsal, Kabir says the spotlight is broken, but a closed "
            "curtain is still hanging directly across the lamp."
        ),
        prompt=(
            "What can the reader infer is causing the dark stage? Use the visible "
            "clue."
        ),
        model_answer=(
            "The closed curtain is blocking the lamp, so the stage is dark even "
            "though the spotlight may still work."
        ),
        relevance_terms=["spotlight", "closed curtain", "lamp", "dark stage"],
        forbidden_phrases=[
            "There is no clue",
            "The curtain cannot affect the light",
        ],
    )
    _semantic_authority_for(curtain)

    controls = transfer_by_id[
        "papas_spectacles_poem_comprehension:transfer:v4"
    ]
    controls.update(
        passage=(
            "A cyclist keeps pressing the gear lever and complains that his bell "
            "is silent; the bell button is beside his thumb."
        ),
        prompt="Why is the moment amusing rather than mysterious? Use both controls.",
        model_answer=(
            "The cyclist is pressing the gear lever instead of the bell button, "
            "so the silent bell has a visible and amusing explanation."
        ),
        relevance_terms=["gear lever", "bell button", "pressing", "silent bell"],
        forbidden_phrases=[
            "There is no contrast",
            "The gear lever rings the bell",
        ],
    )
    _semantic_authority_for(controls)

    for activity in _teaching_activities(comprehension):
        if activity.get("options"):
            activity["target_misconception_tags"] = all_comprehension_tags
            accepted = set(activity.get("accepted_answers") or [])
            prompt = str(activity.get("prompt") or "").casefold()
            mapping: dict[str, list[str]] = {}
            for option in activity["options"]:
                if option in accepted:
                    continue
                normalized_option = option.casefold()
                if "invent" in normalized_option:
                    tag = "unsupported_inference"
                elif any(word in prompt for word in ("funny", "humour", "amusing")):
                    tag = "missed_humorous_contrast"
                elif any(word in prompt for word in ("mainly", "central", "main problem")):
                    tag = "main_idea_replaced_by_detail"
                else:
                    tag = "unsupported_inference"
                mapping[option] = [tag]
            activity["wrong_answer_misconception_tags"] = mapping

        rubric = activity.get("rubric_criteria") or []
        tags = set(activity.get("target_misconception_tags") or [])
        if rubric and len(tags) > 1:
            criterion_mapping: dict[str, list[str]] = {}
            for criterion in rubric:
                criterion_id = str(criterion["id"])
                if criterion_id == "clear_relevant_english":
                    continue
                text = f"{criterion_id} {criterion.get('description', '')}".casefold()
                if (
                    any(word in text for word in ("humor", "humour", "contrast"))
                    and "missed_humorous_contrast" in tags
                ):
                    tag = "missed_humorous_contrast"
                elif (
                    any(word in text for word in ("main idea", "central situation"))
                    and "main_idea_replaced_by_detail" in tags
                ):
                    tag = "main_idea_replaced_by_detail"
                elif "unsupported_inference" in tags:
                    tag = "unsupported_inference"
                else:
                    tag = next(iter(tags))
                criterion_mapping[criterion_id] = [tag]
            activity["criterion_misconception_tags"] = criterion_mapping

    sound_level = levels["papas_spectacles_sound_lab"]
    sound_level.update(
        title="Notice Letter Patterns and Word Meanings",
        focus="compare written letter patterns and use words in clear contexts",
        teaching_goal=(
            "Notice spelling patterns, complete word families, and show word "
            "meaning in original sentences."
        ),
    )
    connect = next(
        step["activity"]
        for step in sound_level["teaching_steps"]
        if step["phase"] == "connect"
    )
    connect.update(
        teaching_block="Compare printed letter patterns and word meanings.",
        passage=(
            "Written word pairs can share an ending while one letter changes.\n\n"
            "How to think: mark the shared letters, locate the changed letter, "
            "and then check each word's meaning in a sentence.\n\n"
            "Worked example: coat and goat share -oat, while c and g change. "
            "Printed letters show the spelling pattern; pronunciation needs a "
            "real voice and is not scored in this text lesson."
        ),
        prompt=(
            "Notice the spelling strategy and meaning check. Continue when both "
            "parts are clear."
        ),
    )
    guided_step = next(
        step
        for step in sound_level["teaching_steps"]
        if step["phase"] == "guided_practice"
    )
    honest_boundary = next(
        item
        for item in guided_step["variant_pool"]
        if item.get("variant_id") == "papas_spectacles_sound_lab:guided:v4"
    )
    honest_boundary.update(
        teaching_block="Separate what printed letters prove from what they do not.",
        passage="The printed words coat and goat share the letters -oat.",
        prompt="Which fact cannot be proved from the printed letters alone?",
        options=[
            "how a speaker pronounces the words",
            "both words end in oat",
            "coat begins with c",
            "goat begins with g",
        ],
        accepted_answers=["how a speaker pronounces the words"],
    )
    _author_sound_pattern_meaning_level(sound_level)
    _author_visual_riddle_guidance(
        levels["papas_spectacles_visual_fun_and_riddle"]
    )


def main() -> None:
    payload = json.loads(CHAPTER_PATH.read_text(encoding="utf-8"))
    _validate_nine_level_gold_prerequisite(payload)
    _repair_current_deep_loop(payload)
    _author_chapter_one_remediation_targets(payload)
    payload["approval_status"] = "agent_reviewed"
    payload["content_version"] = "2026-07-17.ch1-gold.15"
    payload["certification_version"] = "2026-07-17.ch1-gold.13"
    payload["reviewed_by"] = "Codex School content and browser review"
    payload["reviewed_at"] = "2026-07-16T17:34:45+05:30"
    payload["review_evidence"] = [
        "tests/hardening/test_school_rebuild_class5_ch1_gold_slice.py",
        "tests/hardening/test_school_rebuild_class5_ch01_ch03_launch_contract.py -k eng_c5_ch01",
        "Official /private/tmp/eesa101.pdf reviewed for section structure and page locations only; textbook body text was not ingested",
        "Zidd-original passages, prompts, distractors, support checks, transfer tasks, and assessment rubrics reviewed against the strict authoring model",
        "Authenticated browser QA: concise complete pair-phrase responses reach strict rubric evaluation without arbitrary padding",
        "All 102 authored open-answer word floors audited by task type; 98 now permit the shortest semantically complete response and 4 were retained",
        "Authenticated browser QA: replaced an ambiguous key-search choice with one evidence-backed route response and non-equivalent distractors",
        "Focused deep-loop, remediation, leakage, and Class 5 Chapter 1 contracts: 71 passed on 2026-07-15",
        "Independent correction audit: all 110 certifying strict-open activities and assessments now carry task-specific semantic claim slots",
        "Browser-grounded gold checks cover integrated pattern-and-meaning depth, distinct clue-justified riddles, and one-defensible-inference transfer evidence",
        "Original word-usage sentences are evaluator-judged and no longer constrained to model-answer-specific semantic aliases",
        "Authenticated browser QA: a valid give-the-bottle-to-a-teacher response exposed and removed first-person answer-stem semantic slots",
        "Authenticated browser QA: valid route, night-meaning, safe-handoff, and returned-it paraphrases now pass backend-owned semantic checks",
    ]

    payload["runtime_sha256"] = "0" * 64
    chapter = LiveSchoolChapter.model_validate(payload)
    payload["runtime_sha256"] = chapter.calculated_runtime_sha256()
    checked = LiveSchoolChapter.model_validate(payload)
    if checked.calculated_runtime_sha256() != payload["runtime_sha256"]:
        raise RuntimeError("chapter_runtime_hash_not_stable")
    CHAPTER_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "chapter_id": payload["chapter_id"],
                "levels": len(payload["levels"]),
                "teaching_steps": sum(
                    len(level["teaching_steps"]) for level in payload["levels"]
                ),
                "runtime_sha256": payload["runtime_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
