"""Agent-reviewed deep manifest for Class 5 English Chapter 2.

The NCERT chapter was used only to map sections, modalities, and progression.
Every learner-facing passage, prompt, option, rubric, and answer below is
original Zidd content.
"""

from __future__ import annotations

import re
from typing import Any


CHAPTER_ID = "eng_c5_ch02"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/eesa102.pdf"


def _terms(model_answer: str) -> list[str]:
    ignored = {
        "about",
        "after",
        "because",
        "before",
        "could",
        "their",
        "there",
        "these",
        "they",
        "through",
        "which",
        "while",
        "would",
    }
    terms: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z'-]+", model_answer):
        normalized = word.casefold()
        if len(normalized) < 5 or normalized in ignored or normalized in terms:
            continue
        terms.append(normalized)
        if len(terms) == 3:
            break
    if len(terms) < 2:
        raise ValueError("chapter_2_open_task_needs_relevance_terms")
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
    preflight_rule: str = "relevant_english_response",
    learner_part_count: int | None = None,
) -> dict[str, Any]:
    return {
        "passage": passage,
        "prompt": prompt,
        "model_answer": model_answer,
        "evidence": evidence,
        "interaction_type": interaction_type,
        "min_words": min_words,
        "skills": skills,
        "ordered": ordered,
        "preflight_rule": preflight_rule,
        "learner_part_count": learner_part_count,
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
        "prompt": prompt,
        "correct": correct,
        "distractors": distractors,
        "skills": skills,
    }


_PHASE_ACTIONS = {
    "guided": "Work through the passage clues with the coach.",
    "independent": "Work from the passage without a model.",
    "transfer": "Apply the same construct to this new passage.",
    "review": "Retrieve the construct, then verify it against the passage.",
    "bridge": "Start from the strongest visible clue.",
    "masterclass": "Compare the decisive clue with a tempting alternative.",
    "revision_level_1": "Use the ordered clue sequence.",
    "revision_level_2": "Use one visible clue as a short hint.",
    "revision_level_3": "Answer without a hint.",
}


def _skill_construct(skill_ids: list[str]) -> str:
    return " and ".join(
        skill_id.split(".", 1)[-1].replace("_", " ")
        for skill_id in skill_ids
    )


def _child_detail_guidance(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


def _open_direction(
    *,
    phase: str,
    skill_ids: list[str],
    criterion_count: int,
) -> str:
    phase_action = _PHASE_ACTIONS.get(
        phase,
        f"Complete the {phase.replace('_', ' ')} from the visible passage.",
    )
    return (
        f"{phase_action} Use the visible passage to practise "
        f"{_skill_construct(skill_ids)}; "
        f"{_child_detail_guidance(criterion_count)}."
    )


def _open_activity(
    *,
    level_id: str,
    phase: str,
    index: int,
    principle: str,
    level_skills: list[str],
    task: dict[str, Any],
) -> dict[str, Any]:
    activity_id = f"{level_id}:{phase}:{index}"
    slots = []
    criteria = []
    for suffix, description, any_of in task["evidence"]:
        slot_id = f"{activity_id}:{suffix}"
        slots.append(
            {"id": slot_id, "description": description, "any_of": any_of}
        )
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.65,
            }
        )
    skill_ids = list(task.get("skills") or level_skills)
    learner_part_count = task.get("learner_part_count") or len(criteria)
    if learner_part_count < len(criteria):
        raise ValueError("chapter_2_learner_part_count_below_rubric_count")
    direction = _open_direction(
        phase=phase,
        skill_ids=skill_ids,
        criterion_count=learner_part_count,
    )
    payload = {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": f"{principle} {direction}",
        "passage": task["passage"],
        "prompt": task["prompt"],
        "skill_ids": skill_ids,
        "interaction_type": task["interaction_type"],
        "rubric_criteria": criteria,
        "concept_slots": slots,
        "forbidden_phrases": [
            "The details do not matter",
            "I copied the sample answer",
        ],
        "min_response_words": task["min_words"],
        "relevance_terms": _terms(task["model_answer"]),
        "model_answer": task["model_answer"],
        "pass_score": 0.8,
        "preflight_rule": task["preflight_rule"],
    }
    if task["ordered"] and len(slots) >= 2:
        payload["ordered_concept_slot_ids"] = [slot["id"] for slot in slots]
    return payload


def _choice_activity(
    *,
    level_id: str,
    phase: str,
    index: int,
    principle: str,
    level_skills: list[str],
    task: dict[str, Any],
) -> dict[str, Any]:
    activity_id = f"{level_id}:{phase}:{index}"
    raw_options = [task["correct"], *task["distractors"]]
    shift = sum(ord(char) for char in activity_id) % len(raw_options)
    options = raw_options[shift:] + raw_options[:shift]
    return {
        "kind": "selected_option",
        "activity_id": activity_id,
        "teaching_block": (
            f"{principle} Compare every option with the precise clue before "
            "choosing; a merely related detail is not enough."
        ),
        "passage": task["passage"],
        "prompt": task["prompt"],
        "skill_ids": list(task.get("skills") or level_skills),
        "options": options,
        "accepted_answers": [task["correct"]],
    }


def _activity(
    *,
    level_id: str,
    phase: str,
    index: int,
    principle: str,
    level_skills: list[str],
    task: dict[str, Any],
) -> dict[str, Any]:
    if "correct" in task:
        return _choice_activity(
            level_id=level_id,
            phase=phase,
            index=index,
            principle=principle,
            level_skills=level_skills,
            task=task,
        )
    return _open_activity(
        level_id=level_id,
        phase=phase,
        index=index,
        principle=principle,
        level_skills=level_skills,
        task=task,
    )


def _level(spec: dict[str, Any]) -> dict[str, Any]:
    level_id = spec["level_id"]
    skills = spec["skill_ids"]
    principle = spec["principle"]
    support_names = (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    support = {
        name: _activity(
            level_id=level_id,
            phase=name,
            index=index,
            principle=principle,
            level_skills=skills,
            task=spec["support"][index - 1],
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
        "co_construct": _choice_activity(
            level_id=level_id,
            phase="co_construct",
            index=1,
            principle=principle,
            level_skills=skills,
            task=spec["co_construct"],
        ),
        "guided_variants": [
            _activity(
                level_id=level_id,
                phase="guided",
                index=index,
                principle=principle,
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
                principle=principle,
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
                principle=principle,
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
                principle=principle,
                level_skills=skills,
                task=task,
            )
            for index, task in enumerate(spec["review"], start=1)
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


def _evidence(
    key: str,
    description: str,
    *phrases: str,
) -> tuple[str, str, list[str]]:
    return key, description, list(phrases)


EVENT_SKILLS = [
    "reading.event_sequence",
    "reading.paragraph_main_idea",
]
DIALOGUE_SKILLS = [
    "reading.dialogue_attribution",
    "writing.dialogue",
]
REASON_SKILLS = ["reading.inference_reason", "writing.reason_answer"]
WORD_SKILLS = [
    "reading.word_meaning_context",
    "vocab.word_formation",
]
CONNECTOR_SKILLS = [
    "grammar.connectors_because_and_but",
    "grammar.adverbs",
]
GRAMMAR_SKILLS = [
    "grammar.tense_usage",
    "grammar.sentence_order",
]
SYNTHESIS_SKILLS = [
    "writing.summary_own_words",
    "research.information_selection",
]


LEVEL_SPECS: list[dict[str, Any]] = [
    {
        "level_id": "scooter_event_sequence",
        "title": "Track the travelling object",
        "focus": "reconstruct a chain of events and state its main idea",
        "outcome": "Sequence a moving object's journey and explain the central event without losing cause-and-effect links.",
        "skill_ids": EVENT_SKILLS,
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:read:1-4",
            f"{CHAPTER_ID}:think:5",
        ],
        "principle": "Track the same object from one action to the next, using time and cause clues before naming the main event.",
        "connect": {
            "teaching_block": "Stories can move one object through several places. A clear reader follows the object, not every nearby detail.",
            "passage": "A shuttlecock cleared the badminton fence, landed on a fruit cart, and travelled to the next lane when the vendor moved.",
            "prompt": "Notice the shuttlecock's three locations, then continue to rebuild its route.",
        },
        "co_construct": _choice(
            "Neel placed a whistle on the bench. A rolling football knocked it into a kit bag, which the coach carried indoors.",
            "Where was the whistle immediately before it went indoors?",
            "inside the kit bag",
            ["on the bench", "under the football", "beside the indoor court"],
            skills=["reading.event_sequence"],
        ),
        "guided": [
            _choice(
                "A paper badge slipped from Tara's pocket, skidded across the court, and stopped beneath the scorer's chair.",
                "Which event happened second?",
                "The badge skidded across the court.",
                ["The badge stopped under the chair.", "Tara pinned on the badge.", "The scorer left the court."],
            ),
            _choice(
                "First, Yusuf marked the cones. Next, he carried them to the field. Last, the class arranged them in two lines.",
                "What happened just before the cones were arranged?",
                "Yusuf carried them to the field.",
                ["Yusuf marked the cones.", "The class packed the cones away.", "The coach counted two lines."],
            ),
            _choice(
                "A gust lifted a timetable from the gate. It caught on a bicycle handle, and the cyclist returned it to the guard.",
                "Which sentence states the main event?",
                "The lost timetable travelled on a bicycle and was returned.",
                ["The gate was near a bicycle.", "The guard owned a timetable.", "A cyclist rode during a gust."],
            ),
            _choice(
                "Meera rolled the practice ball to Ishan. He missed it, so it crossed the path and dropped into an empty delivery basket.",
                "What caused the ball to reach the basket?",
                "Ishan missed the rolling ball.",
                ["Meera carried the basket.", "The path was closed.", "A delivery rider threw the ball."],
            ),
        ],
        "independent": [
            _task(
                "A library token fell from Renu's book, slid down the bus aisle, and stopped beside the conductor's shoe. He returned it at the next stop.",
                "Retell the token's journey in three ordered steps.",
                "The token fell from Renu's book, slid down the aisle, and the conductor returned it.",
                [
                    _evidence("start", "Begins with the token falling from Renu's book.", "fell from Renu's book", "dropped out of the book"),
                    _evidence("middle", "Places the slide along the bus aisle second.", "slid down the aisle", "moved along the bus floor"),
                    _evidence("end", "Ends with the conductor returning the token.", "conductor returned it", "was returned at the next stop"),
                ],
                interaction_type="summary",
                ordered=True,
            ),
            _task(
                "A red scarf blew from a railing onto the roof of a parked van. The van moved to the shade, where a cleaner spotted the scarf.",
                "State the main event and two details that build it.",
                "The scarf travelled on the van by accident; wind put it on the roof, and the cleaner found it after the van moved.",
                [
                    _evidence(
                        "main",
                        "States that the scarf accidentally travelled with the van.",
                        "scarf travelled on the van",
                        "scarf travelling on the van",
                        "scarf moved with the van",
                    ),
                    _evidence(
                        "wind",
                        "Uses the wind as the first supporting event.",
                        "wind put it on the roof",
                        "blew from the railing onto the van roof",
                    ),
                    _evidence(
                        "discovery",
                        "Uses the cleaner's discovery as the later supporting event.",
                        "cleaner found it after the van moved",
                        "cleaner spotted the scarf",
                    ),
                ],
                interaction_type="evidence_text",
            ),
            _task(
                "A chalk box tipped near the stage. One stick rolled through a curtain gap, down a ramp, and into the drama club's prop case.",
                "Explain how the chalk reached the prop case in correct order.",
                "The chalk rolled through the curtain gap, then travelled down the ramp, and ended inside the prop case.",
                [
                    _evidence(
                        "route",
                        "Names the curtain gap and ramp in the correct order.",
                        "through the curtain gap, then travelled down the ramp",
                        "through the curtain gap and down the ramp",
                    ),
                    _evidence(
                        "result",
                        "Identifies the prop case as the final place.",
                        "inside the prop case",
                        "ended in the prop case",
                        "into the drama club's prop case",
                        "entered the drama club's prop case",
                    ),
                ],
                ordered=True,
            ),
            _task(
                "Kiran set a cap on a wall. A puppy tugged it down, carried it across the garden, and left it beside the water bowl.",
                "Write the central event in one sentence, then name the first and final locations.",
                "The puppy moved the cap across the garden; it started on the wall and ended beside the water bowl.",
                [
                    _evidence("main", "States that the puppy moved the cap across the garden.", "puppy moved the cap", "puppy carried the cap"),
                    _evidence("start", "Names the wall as the first location.", "started on the wall", "cap on a wall"),
                    _evidence("end", "Names the water bowl as the final location.", "ended beside the water bowl", "beside the water bowl"),
                ],
            ),
        ],
        "transfer": [
            _task(
                "During a picnic, a napkin lifted from a plate, crossed two tables, and wrapped around the handle of a departing food cart.",
                "Summarize the napkin's movement from cause to outcome.",
                "Wind lifted the napkin from the plate, carried it across the tables, and left it on the moving food cart.",
                [
                    _evidence("cause", "Identifies wind as the cause of movement.", "wind lifted the napkin", "breeze carried it"),
                    _evidence("outcome", "Ends with the napkin on the departing cart.", "on the moving food cart", "wrapped around the cart handle"),
                ],
                interaction_type="summary",
            ),
            _task(
                "A parcel label peeled off in the rain, floated along a drain channel, and lodged against the caretaker's broom.",
                "Put the three events in order and state what links them.",
                "Rain loosened the label, water carried it along the channel, and the broom stopped it; each event caused the next.",
                [
                    _evidence("loosen", "Places rain loosening the label first.", "rain loosened the label", "label peeled off in the rain"),
                    _evidence("carry", "Places water carrying the label along the channel second.", "water carried it along the channel", "floated along a drain channel"),
                    _evidence("stop", "Places the broom stopping the label third.", "broom stopped it", "lodged against the caretaker's broom"),
                    _evidence("link", "Explains that each event causes the next.", "each event caused the next", "cause-and-effect chain"),
                ],
                ordered=True,
            ),
            _task(
                "A toy boat escaped a pond edge, followed a narrow overflow stream, and stopped against a mesh gate near the garden path.",
                "State the main idea and omit details that do not change the boat's route.",
                "The toy boat drifted out of the pond through an overflow stream and stopped at a mesh gate.",
                [
                    _evidence("main", "Captures the complete route from pond to mesh gate.", "drifted out of the pond", "stopped at a mesh gate"),
                ],
                interaction_type="summary",
            ),
            _task(
                "A receipt slipped from a shopping bag onto an escalator step. It travelled upstairs until a shopper picked it up at the landing.",
                "Explain the receipt's journey using beginning, movement, and ending.",
                "The receipt began in a bag, rode upward on the escalator, and ended at the landing when a shopper collected it.",
                [
                    _evidence("beginning", "Identifies the shopping bag as the starting place.", "began in a bag", "slipped from the shopping bag"),
                    _evidence("movement", "Explains the escalator carried it upstairs.", "rode upward on the escalator", "travelled upstairs"),
                    _evidence("ending", "Ends with a shopper collecting it.", "shopper picked it up", "ended at the landing"),
                ],
                ordered=True,
            ),
        ],
        "review": [
            _task(
                "A key tag fell near the art room, was nudged by a trolley, and stopped outside the music room.",
                "Give the three events in order and one sentence stating the main event.",
                "The tag fell, the trolley pushed it, and it stopped by the music room; the main event is its accidental journey across school.",
                [
                    _evidence("fall", "Places the tag falling near the art room first.", "tag fell", "fell near the art room"),
                    _evidence("trolley", "Places the trolley moving the tag second.", "trolley pushed it", "nudged by a trolley"),
                    _evidence("stop", "Places the stop by the music room third.", "stopped by the music room", "stopped outside the music room"),
                    _evidence("main", "States the accidental journey as the main event.", "accidental journey across school", "tag travelled through school"),
                ],
                ordered=True,
            ),
            _task(
                "A paper plane left a balcony, landed in a vegetable crate, and reached the market gate when the crate was carried away.",
                "Summarize the route in one clear sentence.",
                "The paper plane flew from the balcony into a vegetable crate that carried it to the market gate.",
                [_evidence("summary", "Includes the starting point, crate, and market destination.", "from the balcony", "into a vegetable crate", "to the market gate")],
                interaction_type="summary",
            ),
            _task(
                "A seed packet slipped from a gardening tray, landed in a wheelbarrow, and reached the greenhouse when Mala pushed the barrow inside.",
                "Explain the packet's route by naming what moved it at each stage, then state the main event.",
                "The seed packet slipped from the gardening tray, rode on the wheelbarrow, and reached the greenhouse when Mala moved it. The main event is the packet's accidental journey from the tray to the greenhouse.",
                [
                    _evidence("fall", "Places the fall from the gardening tray first.", "slipped from the gardening tray", "packet slipped from the tray"),
                    _evidence("ride", "Places the wheelbarrow ride second.", "rode on the wheelbarrow", "wheelbarrow carried it"),
                    _evidence("arrival", "Places the greenhouse arrival third.", "reached the greenhouse", "Mala moved it"),
                    _evidence("main", "States the packet's accidental journey as the main event.", "packet's accidental journey", "journey from the tray to the greenhouse"),
                ],
                ordered=True,
            ),
            _task(
                "At the finish line, a gust lifted a numbered ribbon from the results table. It caught on a water carrier's bag and was found beside the practice field after he walked there.",
                "Separate the cause, movement, and outcome, then express the central event in your own words.",
                "A gust lifted the ribbon, the water carrier's bag carried it to the practice field, and it was found there. The central event is the ribbon's wind-started trip away from the results table.",
                [
                    _evidence("cause", "Names the gust as the cause.", "gust lifted the ribbon", "wind lifted the ribbon"),
                    _evidence("movement", "Explains that the bag carried the ribbon to the practice field.", "bag carried it to the practice field", "caught on a water carrier's bag"),
                    _evidence("outcome", "States that the ribbon was found at the practice field.", "it was found there", "found beside the practice field"),
                    _evidence("main", "Expresses the ribbon's wind-started trip as the central event.", "ribbon's wind-started trip", "trip away from the results table"),
                ],
                interaction_type="summary",
            ),
        ],
        "cluster_id": "scooter-event-chain-confusion",
        "misconception": "The learner lists memorable details but loses the moving object, event order, or cause-and-effect link.",
        "remediation": "Use an object-route strip with start, cause, movement, and outcome boxes before compressing the chain into a main idea.",
        "support": [
            _task(
                "A blue wristband fell at the gate, rolled under a bench, and was found there by a monitor.",
                "Name the start, middle, and ending in order.",
                "The wristband fell at the gate, rolled under the bench, and was found by the monitor.",
                [
                    _evidence("start", "Names the fall at the gate as the start.", "fell at the gate"),
                    _evidence("middle", "Names rolling under the bench as the middle.", "rolled under the bench"),
                    _evidence("end", "Names the monitor finding it as the ending.", "found by the monitor"),
                ],
                ordered=True,
            ),
            _task(
                "A foam ball crossed an open gate, landed in a baker's crate, and left the park when the delivery cycle moved.",
                "Build an event chain and state the central event.",
                "The foam ball accidentally left the park after it crossed the gate, landed in the crate, and the cycle moved.",
                [
                    _evidence("chain", "Connects gate, crate, and cycle movement.", "crossed the gate, landed in the crate, and the cycle moved", "went through the gate into the crate before the cycle carried it away"),
                    _evidence("main", "States that the ball accidentally left the park.", "ball accidentally left the park", "crate carried the ball away"),
                ],
            ),
            _task(
                "A note moved from a desk to the floor, then under the door when the fan turned on.",
                "Which event caused the note to pass under the door, and what happened before it?",
                "The fan pushed the note under the door after it fell from the desk to the floor.",
                [
                    _evidence("cause", "Names the fan as the cause.", "fan pushed the note", "fan caused it to move"),
                    _evidence("before", "Places the fall from desk to floor first.", "fell from the desk", "was on the floor first"),
                ],
            ),
            _task(
                "A bus pass slipped from a pocket, stuck to a wet umbrella, and reached the office when the umbrella was returned.",
                "Retell only the events that changed the pass's location.",
                "The pass slipped from a pocket, stuck to the umbrella, and travelled with it to the office.",
                [_evidence("essential", "Keeps the three location-changing events.", "slipped from a pocket", "stuck to the umbrella", "travelled to the office")],
                interaction_type="summary",
            ),
            _task(
                "A bookmark dropped beside a fan, blew across the reading room, and stopped in a window track.",
                "State the main event, then support it with the cause and final place.",
                "The bookmark blew across the room because of the fan and ended in the window track.",
                [
                    _evidence("main", "States the bookmark's movement across the room.", "bookmark blew across the room", "bookmark travelled across the room"),
                    _evidence("cause", "Names the fan as the cause.", "because of the fan", "fan made it blow"),
                    _evidence("final", "Names the window track as the final place.", "ended in the window track", "stopped in a window track"),
                ],
            ),
        ],
    },
    {
        "level_id": "scooter_dialogue_and_speaker",
        "title": "Follow every speaker",
        "focus": "attribute dialogue and write a responsive exchange",
        "outcome": "Identify speaker, listener, and purpose, then write a punctuated exchange in which each turn responds logically.",
        "skill_ids": DIALOGUE_SKILLS,
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:read:1-4",
            f"{CHAPTER_ID}:think:5",
            f"{CHAPTER_ID}:write:11-12",
        ],
        "principle": "Track who speaks, who hears the line, and what changes next; dialogue writing must preserve that response chain and readable punctuation.",
        "connect": {
            "teaching_block": "Dialogue is an action inside a story. Speaker labels, quotation marks, and replies show who controls each turn.",
            "passage": "'The shuttle is behind the curtain,' Asha told Kabir. 'I will fetch it while you hold the net,' he replied.",
            "prompt": "Identify the two speakers and notice how the second line answers the first.",
        },
        "co_construct": _choice(
            "'Please wait by the gate,' the coach told Mira. 'I will bring the first-aid box,' Mira answered.",
            "Who promises to bring the first-aid box?",
            "Mira",
            ["the coach", "the gatekeeper", "the injured player"],
            skills=["reading.dialogue_attribution"],
        ),
        "guided": [
            _task(
                "'This racket has Rohan's name,' Jia said to the clerk. 'Then I will call his class,' the clerk replied.",
                "Name each speaker and explain how the clerk's reply responds to Jia.",
                "Jia reports the name on the racket, and the clerk responds by promising to contact Rohan's class.",
                [
                    _evidence("first_speaker", "Identifies Jia as the first speaker.", "Jia reports", "Jia said"),
                    _evidence("second_speaker", "Identifies the clerk as the second speaker.", "clerk responds", "clerk replied"),
                    _evidence("response", "Explains that the clerk acts on the name clue.", "contact Rohan's class", "call his class"),
                ],
            ),
            _task(
                "Facts: Nikhil asks where the ball went. Farah says she saw it near the delivery gate.",
                "Write the two-line exchange with clear speaker turns and quotation punctuation.",
                "Nikhil asked, 'Where did the ball go?' Farah replied, 'I saw it near the delivery gate.'",
                [
                    _evidence("turns", "Writes one question from Nikhil and one relevant reply from Farah.", "Nikhil asked", "Farah replied"),
                    _evidence("punctuation", "Uses readable question and quotation punctuation.", "Where did the ball go?", "I saw it near the delivery gate"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "'I found this helmet strap,' Aman told the rider. 'Thank you; I will check it before leaving,' she said.",
                "Explain what Aman's line contributes and why the rider's reply is relevant.",
                "Aman reports the found strap, and the rider replies appropriately by saying she will inspect it before travelling.",
                [
                    _evidence("purpose", "Explains that Aman reports a found safety item.", "reports the found strap", "tells the rider about the strap"),
                    _evidence("reply", "Connects the rider's inspection to Aman's report.", "inspect it before travelling", "check it before leaving"),
                ],
            ),
            _task(
                "Two teammates discover that their practice ball has rolled beyond the gate. One wants to inform the guard; the other agrees to check the nearby lane.",
                "Write a three-turn exchange that reaches that plan without changing speakers mid-line.",
                "Leena said, 'The ball rolled beyond the gate.' Omar replied, 'Let us tell the guard.' Leena answered, 'Yes, and then we can check the nearby lane.'",
                [
                    _evidence("report", "Opens with Leena reporting where the ball went.", "ball rolled beyond the gate", "Leena said"),
                    _evidence("response", "Continues with Omar suggesting the guard.", "tell the guard", "Omar replied"),
                    _evidence("plan", "Ends with Leena agreeing to check the nearby lane.", "check the nearby lane", "Leena answered"),
                ],
                interaction_type="dialogue",
            ),
        ],
        "independent": [
            _task(
                "'The scoreboard key is missing,' the captain told Ravi. Ravi looked near the storage shelf and said, 'It is hanging beside the whistle.'",
                "Identify both speakers, the listener in the first line, and Ravi's contribution.",
                "The captain speaks to Ravi first. Ravi then reports that the key is hanging beside the whistle.",
                [
                    _evidence("first_speaker", "Identifies the captain as the first speaker.", "captain speaks", "captain is the first speaker"),
                    _evidence("second_speaker", "Identifies Ravi as the second speaker.", "Ravi then reports", "Ravi said"),
                    _evidence("listener", "Identifies Ravi as the listener in the first line.", "captain speaks to Ravi", "captain told Ravi"),
                    _evidence("contribution", "States that Ravi supplies the key's location.", "key is hanging beside the whistle", "reports the key's location"),
                ],
            ),
            _task(
                "After a ball disappears into a delivery cart, Priya asks the guard what to do. The guard suggests noting the cart number and calling the depot.",
                "Write a four-line dialogue in which Priya asks, the guard advises, and Priya confirms the plan.",
                "Priya asked, 'How can we find the cart?' The guard replied, 'Note its number and call the depot.' Priya said, 'I can see the number.' The guard answered, 'Good; write it down now.'",
                [
                    _evidence("question", "Opens with Priya asking how to find the cart.", "How can we find the cart?", "Priya asked"),
                    _evidence("advice", "Includes the guard's advice to note the number and call the depot.", "Note its number and call the depot", "guard replied"),
                    _evidence("confirmation", "Includes Priya confirming that she can see the number.", "I can see the number", "Priya said"),
                    _evidence("instruction", "Ends with the guard telling Priya to write the number down.", "write it down now", "guard answered"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "'Do not cross the busy road,' Mehul warned. 'I will ask the traffic marshal for help,' Saba replied.",
                "Explain the purpose of each line and how the reply addresses the warning.",
                "Mehul gives a safety warning, and Saba responds with a safe alternative by asking the traffic marshal for help.",
                [
                    _evidence("warning", "States that Mehul's line gives a safety warning.", "safety warning", "Mehul gives a safety warning"),
                    _evidence("alternative", "States that Saba's line gives a safe alternative.", "safe alternative", "Saba responds with a safe alternative"),
                    _evidence("link", "Explains that Saba avoids crossing by seeking help.", "asking the traffic marshal", "avoids crossing"),
                ],
            ),
            _task(
                "A teacher asks why the class stopped playing. The monitor explains that a scooter carried their ball away, and the teacher asks whether anyone recorded its colour.",
                "Turn the information into a three-speaker exchange with correct question marks and a logical unanswered final question.",
                "The teacher asked, 'Why did the game stop?' The monitor replied, 'A scooter carried our ball away.' The teacher then asked, 'Did anyone record its colour?'",
                [
                    _evidence("first_question", "Opens with the teacher asking why the game stopped.", "Why did the game stop?", "teacher asked"),
                    _evidence("answer", "Includes the monitor's answer about the scooter.", "scooter carried our ball", "monitor replied"),
                    _evidence("final_question", "Ends with the unanswered colour question.", "Did anyone record its colour?", "teacher then asked"),
                ],
                interaction_type="dialogue",
            ),
        ],
        "transfer": [
            _task(
                "At a railway platform, a child tells an attendant that her water bottle is on a departing trolley. The attendant asks for its colour and promises to radio the next platform.",
                "Write a short dialogue that includes the problem, clarifying question, answer, and promised action.",
                "The child said, 'My bottle is on that trolley.' The attendant asked, 'What colour is it?' She answered, 'It is green.' The attendant said, 'I will radio the next platform.'",
                [
                    _evidence("problem", "States that the bottle is on the departing trolley.", "bottle is on that trolley", "water bottle is on a departing trolley"),
                    _evidence("question", "Asks a clarifying question about the bottle's colour.", "What colour is it?", "asks for its colour"),
                    _evidence("answer", "Includes the child's answer to the colour question.", "She answered", "child answered"),
                    _evidence("action", "Promises to radio the next platform.", "radio the next platform", "will radio the next platform"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "'The museum ticket is in my other bag,' Vikram told the guide. 'You can show the booking message instead,' the guide replied.",
                "Identify speaker, listener, and the practical purpose of the guide's reply.",
                "Vikram speaks to the guide, who offers the booking message as a practical replacement for the missing ticket.",
                [
                    _evidence("speaker", "Identifies Vikram as the speaker.", "Vikram speaks", "Vikram told"),
                    _evidence("listener", "Identifies the guide as the listener.", "to the guide", "guide listens"),
                    _evidence("purpose", "Explains the alternative proof offered.", "booking message", "replacement for the missing ticket"),
                ],
            ),
            _task(
                "A shop assistant tells a customer that a parcel was placed on the wrong shelf. The customer asks when it can be moved, and the assistant promises to correct it immediately.",
                "Create the three-turn exchange and punctuate the customer's question.",
                "The assistant said, 'Your parcel was placed on the wrong shelf.' The customer asked, 'When can it be moved?' The assistant replied, 'I will correct it immediately.'",
                [
                    _evidence("report", "Opens with the assistant reporting the wrong shelf.", "wrong shelf", "assistant said"),
                    _evidence("question", "Includes the customer's punctuated timing question.", "When can it be moved?", "customer asked"),
                    _evidence("action", "Ends with the assistant promising to correct the placement.", "correct it immediately", "assistant replied"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "'The kite string is touching the power line,' Alia shouted to her brother. 'I will step back and call an adult,' he answered.",
                "Explain why the second line is a relevant and responsible response.",
                "Alia warns her brother about the power line, and he responds responsibly by moving away and calling an adult.",
                [
                    _evidence("warning", "Identifies Alia's line as a danger warning.", "warns her brother", "power line danger"),
                    _evidence("response", "Explains the two safe actions in the reply.", "moving away", "calling an adult"),
                ],
            ),
        ],
        "review": [
            _task(
                "'I heard a bell near the cycle stand,' Noor told Imran. 'Then the missing cycle may still be there,' he replied.",
                "Who is he, and what inference does his reply add?",
                "He refers to Imran, who infers from Noor's bell clue that the missing cycle may remain near the stand.",
                [
                    _evidence("referent", "Identifies Imran as the second speaker.", "He refers to Imran", "Imran replies"),
                    _evidence("contribution", "Explains the inference from bell to possible location.", "cycle may remain near the stand", "infers from the bell clue"),
                ],
            ),
            _task(
                "Facts: Ria reports a cracked helmet buckle. The coach thanks her and removes the helmet from use.",
                "Write the exchange in two clear turns and show the coach's action.",
                "Ria said, 'This helmet buckle is cracked.' The coach replied, 'Thank you for reporting it; I will remove this helmet from use.'",
                [
                    _evidence("turns", "Includes Ria's report and the coach's direct response.", "helmet buckle is cracked", "Thank you for reporting"),
                    _evidence("action", "States that the coach removes the unsafe helmet.", "remove this helmet from use", "takes the helmet out of use"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "'The sapling's leaves are drooping,' Dev told Ms Roy. 'It may need water before the afternoon heat,' she replied.",
                "Identify she, then rewrite the exchange as two labelled turns without changing the advice.",
                "Dev said, 'The sapling's leaves are drooping.' Ms Roy replied, 'It may need water before the afternoon heat.' She is Ms Roy, and her reply advises watering the plant before it becomes hotter.",
                [
                    _evidence("identity", "Identifies Ms Roy as she.", "She is Ms Roy", "she refers to Ms Roy"),
                    _evidence("observation", "Preserves Dev's observation as the first turn.", "leaves are drooping", "Dev said"),
                    _evidence("advice", "Preserves Ms Roy's watering advice as the second turn.", "need water before the afternoon heat", "her reply advises watering"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "Facts: Kabir notices that the stage curtain is torn beside the left rope. He reports it to the drama teacher. She asks exactly where he saw the tear. Kabir answers, and the teacher closes that side of the stage.",
                "Create the four-turn exchange so each reply answers the line before it and the final action is clear.",
                "Kabir said, 'The stage curtain is torn.' The drama teacher asked, 'Where did you notice it?' Kabir replied, 'Beside the left rope.' The teacher said, 'I will close that side of the stage until it is repaired.'",
                [
                    _evidence("report", "Opens with Kabir reporting the torn curtain.", "curtain is torn", "Kabir said"),
                    _evidence("question", "Includes the teacher's punctuated location question.", "Where did you notice it?", "drama teacher asked"),
                    _evidence("answer", "Includes Kabir's precise location answer.", "Beside the left rope", "Kabir replied"),
                    _evidence("action", "Ends with the teacher closing the unsafe side of the stage.", "close that side of the stage", "until it is repaired"),
                ],
                interaction_type="dialogue",
            ),
        ],
        "cluster_id": "scooter-speaker-response-confusion",
        "misconception": "The learner assigns a line to the nearest name, merges speaker turns, or writes replies that do not respond to the preceding line.",
        "remediation": "Use a speaker-listener-purpose table, then rebuild each exchange as separate turns with an explicit response arrow and punctuation check.",
        "support": [
            _task(
                "'The cone is missing,' Jay told Uma. 'I saw it beside the shed,' Uma replied.",
                "Name both speakers and state what new information Uma adds.",
                "Jay reports the missing cone, while Uma replies that it is beside the shed.",
                [
                    _evidence("first_speaker", "Identifies Jay as the first speaker.", "Jay reports", "Jay told Uma"),
                    _evidence("second_speaker", "Identifies Uma as the second speaker.", "Uma replies", "Uma replied"),
                    _evidence("information", "States that Uma locates the cone beside the shed.", "beside the shed", "cone is beside the shed"),
                ],
            ),
            _task(
                "A captain reports a lost score sheet. A volunteer asks for the team name, then promises to check the registration desk.",
                "Write the three-turn exchange with a relevant question and action.",
                "The captain said, 'Our score sheet is missing.' The volunteer asked, 'What is your team name?' Then she said, 'I will check the registration desk.'",
                [
                    _evidence("report", "Opens with the captain reporting the missing score sheet.", "score sheet is missing", "captain said"),
                    _evidence("question", "Includes the volunteer's punctuated team-name question.", "What is your team name?", "volunteer asked"),
                    _evidence("action", "Ends with the promised registration-desk check.", "check the registration desk", "Then she said"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "'Please keep the gate closed,' the caretaker said to Om. 'I will close it after the cart enters,' Om answered.",
                "Explain who receives the instruction and how the reply modifies the timing.",
                "Om receives the caretaker's instruction and agrees to close the gate after the cart has entered.",
                [
                    _evidence("listener", "Identifies Om as the listener and second speaker.", "Om receives", "Om answered"),
                    _evidence("timing", "States that closure will happen after the cart enters.", "after the cart has entered", "close it after the cart"),
                ],
            ),
            _task(
                "Facts: A pupil asks whether the road is safe. A marshal says to wait for the green signal.",
                "Write the question and response with correct punctuation.",
                "The pupil asked, 'Is the road safe to cross?' The marshal replied, 'Wait for the green signal.'",
                [
                    _evidence("question", "Writes a punctuated safety question.", "Is the road safe to cross?", "pupil asked"),
                    _evidence("reply", "Writes the marshal's relevant instruction.", "Wait for the green signal", "marshal replied"),
                ],
                interaction_type="dialogue",
            ),
            _task(
                "'The ball went beneath the van,' Nita said. 'Do not reach for it; I will ask the driver to stop,' the guard replied.",
                "State the purpose of each turn and the safe action chosen.",
                "Nita reports the ball's location, and the guard warns her not to reach while he asks the driver to stop.",
                [
                    _evidence("first_purpose", "States that Nita reports the ball's location.", "reports the ball's location", "Nita reports"),
                    _evidence("second_purpose", "States that the guard gives a safety warning.", "guard warns", "warns her not to reach"),
                    _evidence("action", "Names asking the driver to stop.", "asks the driver to stop", "driver to stop"),
                ],
            ),
        ],
    },
    {
        "level_id": "scooter_inference_and_fair_choice",
        "title": "Choose fairly from clues",
        "focus": "infer motives and justify safe, honest decisions",
        "outcome": "Infer a character's likely reason from evidence and justify an honest or safe action without inventing facts.",
        "skill_ids": REASON_SKILLS,
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:think:5"],
        "principle": "A sound inference combines a visible clue with a responsible conclusion; a reason answer must show that link rather than announce an opinion.",
        "connect": {
            "teaching_block": "When an object is found, the best choice protects its owner and nearby people. Evidence explains why that choice fits.",
            "passage": "Sonal found a labelled sports bag near the gate and carried it to the office instead of opening it.",
            "prompt": "Notice the label and Sonal's destination before judging her decision.",
        },
        "co_construct": _choice(
            "Arun found a helmet beside a crowded road. A phone number was written inside it, so he asked a traffic marshal to call the owner.",
            "Which clue best explains Arun's action?",
            "The helmet contained the owner's phone number.",
            ["The road was crowded.", "Arun wanted a new helmet.", "The marshal owned a motorcycle."],
            skills=["reading.inference_reason"],
        ),
        "guided": [
            _task(
                "A hockey stick with a class label lay near the bus bay. Meena handed it to the school receptionist.",
                "Why was Meena's choice responsible? Use the label as evidence.",
                "Meena acted responsibly because the class label could help the receptionist return the stick to its owner.",
                [
                    _evidence("reason", "States that the receptionist can return the item.", "return the stick", "find its owner"),
                    _evidence("evidence", "Uses the class label as the supporting clue.", "class label", "label could help"),
                ],
            ),
            _task(
                "A scooter rider slows near a school gate even though the road ahead looks empty. Children are gathering behind a parked bus.",
                "Infer why the rider slows and support the answer with the hidden-view clue.",
                "The rider slows because children may emerge from behind a parked bus, which blocks the view near the gate.",
                [
                    _evidence("inference", "Infers a possible child entering the road.", "children may emerge", "child could enter the road"),
                    _evidence("clue", "Uses the parked bus blocking the view.", "bus blocks the view", "behind a parked bus"),
                ],
            ),
            _task(
                "Kavya finds an unlabelled water bottle after practice. Three groups used the court that day, so she places it in the shared lost-property box.",
                "Explain why the shared box is fairer than giving the bottle to one group.",
                "The shared box is fair because the owner could belong to any of the three groups, and each group can check the same place.",
                [
                    _evidence("fairness", "Explains equal access for all three groups.", "each group can check", "equal access"),
                    _evidence("uncertainty", "Uses the lack of a label and multiple groups.", "unlabelled bottle", "any of the three groups"),
                ],
            ),
            _task(
                "Rafi's friend suggests running after a moving delivery scooter to recover their ball. Rafi instead notes the vehicle number and tells an adult.",
                "Why is Rafi's plan safer and still useful?",
                "Rafi avoids chasing a moving vehicle, while the vehicle number and an adult can help locate the scooter safely.",
                [
                    _evidence("safety", "Explains that he avoids a moving vehicle.", "avoids chasing", "moving vehicle"),
                    _evidence("useful", "Explains how the number and adult help recovery.", "vehicle number", "adult can help"),
                ],
            ),
        ],
        "independent": [
            _task(
                "Naman finds a scarf on a city bus. The route number is printed on the ticket beside it, and the conductor keeps a lost-property register.",
                "What should Naman do, and which two details support that decision?",
                "Naman should give the scarf to the conductor because the route is known and the conductor keeps a lost-property register.",
                [
                    _evidence("action", "Chooses to give the scarf to the conductor.", "give the scarf to the conductor", "hand it to the conductor"),
                    _evidence("route", "Uses the known bus route as one supporting detail.", "route is known", "route number is printed"),
                    _evidence("register", "Uses the conductor's lost-property register as the other detail.", "lost-property register", "conductor keeps a lost-property register"),
                ],
            ),
            _task(
                "A cyclist wears a helmet but leaves its chin strap loose. The lane has several speed breakers.",
                "Infer the risk and explain the safer action using both details.",
                "A loose helmet may come off at a speed breaker, so the cyclist should fasten the chin strap before riding.",
                [
                    _evidence("risk", "Identifies that the helmet may come off.", "helmet may come off", "may come off"),
                    _evidence("strap", "Uses the loose chin strap as one supporting detail.", "loose helmet", "chin strap"),
                    _evidence("breaker", "Uses the speed breakers as the other supporting detail.", "at a speed breaker", "several speed breakers"),
                    _evidence("action", "Requires fastening before riding.", "fasten the chin strap", "before riding"),
                ],
            ),
            _task(
                "A ball rolls into a neighbour's locked garden. No one is home, but a phone number is displayed near the gate.",
                "Choose a respectful recovery plan and justify it.",
                "The players should call the displayed number and wait for permission instead of climbing the locked gate.",
                [
                    _evidence("plan", "Chooses contact and permission rather than trespass.", "call the displayed number", "wait for permission"),
                    _evidence("reason", "Explains respect for the locked private space.", "instead of climbing", "locked garden"),
                ],
            ),
            _task(
                "Leela sees a rider carrying a child without a second helmet. The child is seated behind the rider on a busy street.",
                "Explain the safety problem and the change needed before travel.",
                "A child without a helmet is unprotected, so both people need properly fastened helmets before the scooter moves.",
                [
                    _evidence("problem", "Identifies the unprotected passenger.", "child without a helmet", "passenger is unprotected"),
                    _evidence("change", "Requires a fastened helmet before movement.", "helmet before the scooter moves", "properly fastened helmets"),
                ],
            ),
        ],
        "transfer": [
            _task(
                "At a fair, Iqra finds a wallet near a ticket counter. A receipt inside shows the stall number, and the fair has an announcement desk.",
                "Decide what Iqra should do and justify the decision with both clues.",
                "Iqra should take the wallet to the announcement desk because the stall number can help staff locate its owner.",
                [
                    _evidence("action", "Chooses to give the wallet to fair staff.", "Iqra should take the wallet", "give it to staff"),
                    _evidence("stall", "Uses the stall number as one clue.", "stall number", "receipt inside shows the stall number"),
                    _evidence("desk", "Uses the announcement desk as the other clue.", "announcement desk", "fair has an announcement desk"),
                ],
            ),
            _task(
                "A football enters a construction area through a gap in the fence. Machinery is operating and a supervisor stands at the entrance.",
                "Explain the safest recovery plan and why retrieving it alone is risky.",
                "The players should ask the supervisor for help because operating machinery makes entering alone dangerous.",
                [
                    _evidence("plan", "Chooses the supervisor's help.", "ask the supervisor", "supervisor for help"),
                    _evidence("risk", "Uses operating machinery as the danger.", "operating machinery", "entering alone dangerous"),
                ],
            ),
            _task(
                "A library book is left on a park bench. Its issue slip names a school, but not the pupil. The park office stores found items.",
                "Give a fair return plan using the available information.",
                "The finder should leave the book with the park office and share the school name so staff can contact the right school.",
                [
                    _evidence("plan", "Uses the park office as secure custody.", "leave the book with the park office", "park staff"),
                    _evidence("information", "Uses the school name without inventing a pupil.", "share the school name", "contact the right school"),
                ],
            ),
            _task(
                "A passenger notices smoke from a scooter's storage box. The rider has not noticed and is waiting at a red light.",
                "Infer the urgent risk and state a safe way to alert the rider.",
                "The passenger should warn the rider from a safe distance and ask them to switch off the scooter because the smoke may signal a fire.",
                [
                    _evidence("risk", "Infers possible fire from smoke.", "smoke may signal a fire", "possible fire"),
                    _evidence("action", "Suggests warning from safety and switching off.", "warn the rider", "switch off the scooter"),
                ],
            ),
        ],
        "review": [
            _task(
                "A labelled lunch bag remains after a sports meeting. The label gives only a house team, and the house captain keeps an attendance list.",
                "State the best return action and link both clues to your reason.",
                "The bag should go to the house captain because the team label and attendance list can be used together to find the owner.",
                [
                    _evidence("action", "Chooses the house captain.", "go to the house captain", "give it to the captain"),
                    _evidence("label", "Uses the house-team label as one clue.", "team label", "label gives only a house team"),
                    _evidence("list", "Uses the attendance list as the other clue.", "attendance list", "captain keeps an attendance list"),
                ],
            ),
            _task(
                "Two pupils want to cross a road for a lost ball. The signal is red for pedestrians, and a traffic marshal is nearby.",
                "Explain what they should do and why.",
                "They should wait and ask the traffic marshal for help because the red pedestrian signal means it is unsafe to cross.",
                [
                    _evidence("action", "Chooses waiting and adult help.", "wait", "ask the traffic marshal"),
                    _evidence("reason", "Uses the red signal as evidence of danger.", "red pedestrian signal", "unsafe to cross"),
                ],
            ),
            _task(
                "During a quiz, Leela finds another team's answer sheet under her chair. The team name is visible, and the referee is collecting completed sheets at the front.",
                "Choose the fairest action and explain why Leela should avoid reading the sheet.",
                "Leela should keep the answers covered and hand the sheet to the referee because the team name identifies where it belongs, while reading it could give her team an unfair advantage.",
                [
                    _evidence("action", "Keeps the answers covered and gives the sheet to the referee.", "keep the answers covered", "hand the sheet to the referee"),
                    _evidence("reason", "Links the visible team name and unread answers to fair play.", "team name identifies", "unfair advantage"),
                ],
            ),
            _task(
                "On a nature trail, rainwater covers a wooden footbridge and a loose warning rope hangs at its entrance. A marked side path leads to the map shelter, where the guide is waiting.",
                "Infer the risk and give the safest plan using the bridge, rope, and guide clues.",
                "The wet bridge and loose warning rope suggest that crossing may be unsafe, so the group should take the marked side path and tell the guide at the map shelter.",
                [
                    _evidence("risk", "Infers that crossing the footbridge may be unsafe.", "crossing may be unsafe", "footbridge may be unsafe"),
                    _evidence("bridge", "Uses the wet footbridge as one clue.", "wet bridge", "rainwater covers a wooden footbridge"),
                    _evidence("rope", "Uses the loose warning rope as another clue.", "loose warning rope", "warning rope hangs at its entrance"),
                    _evidence("guide", "Uses the waiting guide as the third clue.", "guide at the map shelter", "guide is waiting"),
                    _evidence("plan", "Chooses the marked path and informs the guide.", "take the marked side path", "tell the guide"),
                ],
            ),
        ],
        "cluster_id": "scooter-opinion-without-evidence",
        "misconception": "The learner gives a moral opinion or safety slogan without linking it to the specific clues and consequences in the scene.",
        "remediation": "Use a clue-action-consequence frame: underline two details, choose one safe or fair action, then explain how each detail supports it.",
        "support": [
            _task(
                "A named notebook is found under a bench, and the office keeps class lists.",
                "Choose the return action and use both clues.",
                "The notebook should go to the office because its name and the class lists can identify the owner.",
                [
                    _evidence("action", "Chooses to take the notebook to the office.", "notebook should go to the office", "go to the office"),
                    _evidence("name", "Uses the notebook's name as one clue.", "its name", "named notebook"),
                    _evidence("lists", "Uses the class lists as the other clue.", "class lists", "office keeps class lists"),
                ],
            ),
            _task(
                "A ball lies beyond a busy junction. A crossing guard is present, but the pedestrian signal is red.",
                "Build a safe plan and explain why waiting matters.",
                "The players should wait for the crossing guard and a safe signal rather than enter the junction while the signal is red.",
                [
                    _evidence("plan", "Uses both guard and safe signal.", "wait for the crossing guard", "safe signal"),
                    _evidence("reason", "Explains the red signal prohibits crossing.", "signal is red", "rather than enter the junction"),
                ],
            ),
            _task(
                "A water bottle has no name, but a unique club sticker is attached. The club leader has a member list.",
                "Infer the most useful next step and explain the sticker clue.",
                "The finder should ask the club leader because the sticker narrows the possible owners to people on the club list.",
                [
                    _evidence("step", "Chooses the club leader.", "ask the club leader", "contact the club leader"),
                    _evidence("clue", "Explains how the sticker narrows ownership.", "sticker narrows", "club list"),
                ],
            ),
            _task(
                "A rider has a helmet resting on the handlebar instead of on their head. Traffic is moving slowly.",
                "Explain why slow traffic does not remove the risk.",
                "Even slow traffic can involve a sudden fall, so the rider must wear and fasten the helmet rather than carry it.",
                [
                    _evidence("risk", "Names possible sudden fall despite low speed.", "sudden fall", "even slow traffic"),
                    _evidence("action", "Requires wearing and fastening the helmet.", "wear and fasten the helmet", "rather than carry it"),
                ],
            ),
            _task(
                "A pupil finds cash beside the canteen. No owner is visible, and the canteen manager records lost property.",
                "Give an honest action and evidence-based reason.",
                "The pupil should hand the cash to the manager because the lost-property record gives the owner a fair way to claim it.",
                [
                    _evidence("action", "Chooses to hand cash to the manager.", "hand the cash to the manager", "give it to the manager"),
                    _evidence("reason", "Uses the lost-property record as fair process.", "lost-property record", "fair way to claim"),
                ],
            ),
        ],
    },
    {
        "level_id": "scooter_context_vocabulary",
        "title": "Build words from context",
        "focus": "infer action words, use them, and form meaningful compounds",
        "outcome": "Infer a word from nearby clues, use it in a fresh sentence, and explain how two base words form a meaningful compound.",
        "skill_ids": WORD_SKILLS,
        "episode_kind": "language_lab",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:new-words:5",
            f"{CHAPTER_ID}:learn-a-b:6",
            f"{CHAPTER_ID}:write-b-c:11-12",
        ],
        "principle": "Use action and result clues to infer meaning, then test the word in a new context; a compound must carry a stable combined meaning.",
        "connect": {
            "teaching_block": "A strong context clue shows what changed. Word parts can then help build a related but meaningful new word.",
            "passage": "The loose basket rattled over the stones, making short hard sounds until Sia tightened it.",
            "prompt": "Use the sound and tightening clues to predict the meaning of rattled.",
        },
        "co_construct": _choice(
            "The cyclist swerved around a fallen branch instead of striking it.",
            "What does swerved mean in this scene?",
            "turned suddenly to avoid something",
            ["stopped for a long rest", "moved straight through the branch", "rang a warning bell"],
        ),
        "guided": [
            _choice(
                "The strap was secured with a double knot, so the parcel did not move during the ride.",
                "Which meaning of secured fits the result clue?",
                "fastened firmly",
                ["hidden secretly", "painted brightly", "counted twice"],
            ),
            _choice(
                "Ira glimpsed the bus number for only a second before it turned the corner.",
                "What does glimpsed mean here?",
                "saw briefly",
                ["copied neatly", "heard repeatedly", "forgot completely"],
            ),
            _choice(
                "The groundskeeper inspected the goalpost by checking every joint before the match.",
                "Which phrase best explains inspected?",
                "examined carefully",
                ["moved quickly", "painted carelessly", "announced loudly"],
            ),
            _choice(
                "A raincoat is a coat designed for rain.",
                "Which pair correctly shows how the compound is built?",
                "rain + coat",
                ["ray + coat", "rain + cot", "train + coat"],
            ),
        ],
        "independent": [
            _task(
                "The puppy darted through the open gate and reached the ball before anyone could call it back.",
                "Explain darted from context and name the clue that supports the meaning.",
                "Darted means moved very quickly; reaching the ball before anyone could react is the supporting clue.",
                [
                    _evidence("meaning", "Defines darted as moving very quickly.", "moved very quickly", "rushed suddenly"),
                    _evidence("clue", "Uses the rapid arrival before a reaction.", "before anyone could react", "reached the ball first"),
                ],
            ),
            _task(
                "A mechanic fastened the loose mirror before the rider continued.",
                "Use fastened in a new sentence that keeps the same meaning.",
                "Maya fastened the lid tightly before carrying the lunch box.",
                [_evidence("usage", "Uses fastened to mean attached or closed firmly.", "fastened the lid", "fastened the strap", "fastened the buckle")],
                interaction_type="short_text",
                skills=["reading.word_meaning_context"],
            ),
            _task(
                "The words score and board join to name the display that shows points in a game.",
                "Form the compound and explain its combined meaning.",
                "Scoreboard is formed from score and board, and it means a board that displays the score.",
                [
                    _evidence("form", "Forms scoreboard from both base words.", "scoreboard", "score + board"),
                    _evidence("meaning", "Explains that it displays scores.", "displays the score", "shows points"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "The crate creaked whenever the rider crossed a bump, and the old wooden sides rubbed together.",
                "Infer creaked and use the rubbing clue in the explanation.",
                "Creaked means made a rough squeaking sound, supported by the old wooden sides rubbing together.",
                [
                    _evidence("meaning", "Defines the rough squeaking sound.", "rough squeaking sound", "made a creaking noise"),
                    _evidence("clue", "Uses the rubbing wooden sides.", "wooden sides rubbing", "old sides rubbed"),
                ],
            ),
        ],
        "transfer": [
            _task(
                "The curtain fluttered near the open window, rising and falling with every breeze.",
                "Infer fluttered and explain which movement clue supports it.",
                "Fluttered means moved lightly back and forth, shown by the curtain rising and falling with every breeze.",
                [
                    _evidence("meaning", "Defines light repeated movement.", "moved lightly back and forth", "moved gently"),
                    _evidence("clue", "Uses rising and falling in the breeze.", "rising and falling", "with every breeze"),
                ],
            ),
            _task(
                "The compound footpath names a path meant for people walking on foot.",
                "Break the word into its bases and explain the combined meaning.",
                "Footpath combines foot and path and means a path intended for walkers.",
                [
                    _evidence("foot", "Identifies foot as the first base.", "foot", "combines foot"),
                    _evidence("path", "Identifies path as the second base.", "path", "and path"),
                    _evidence("meaning", "Explains that it is for walkers.", "path for people walking", "intended for walkers"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "The nurse examined the bandage by checking its edges and asking whether it felt tight.",
                "Replace examined with a chapter word of similar meaning and justify the choice.",
                "Inspected fits because the nurse checked the bandage carefully at several points.",
                [
                    _evidence("word", "Chooses inspected.", "inspected"),
                    _evidence("reason", "Connects inspected with careful checking.", "checked carefully", "at several points"),
                ],
                skills=["reading.word_meaning_context"],
            ),
            _task(
                "The latch clicked into place, and the gate no longer swung in the wind.",
                "Explain secured in this situation and write a second use of the word.",
                "Secured means fastened safely here. The caretaker secured the ladder to the wall with a strong rope.",
                [
                    _evidence("meaning", "Defines secured as fastened safely.", "fastened safely", "held firmly"),
                    _evidence("new_use", "Uses secured accurately in a fresh sentence.", "secured the ladder", "secured the box", "secured the rope")
                ],
            ),
        ],
        "review": [
            _task(
                "The cart lurched forward when its wheel dropped from the curb, making every box shift suddenly.",
                "Infer lurched and use the box movement as evidence.",
                "Lurched means moved forward suddenly and unevenly, as shown by all the boxes shifting at once.",
                [
                    _evidence("meaning", "Defines a sudden uneven movement.", "moved forward suddenly", "moved unevenly"),
                    _evidence("clue", "Uses the boxes shifting at once.", "boxes shifting", "shifted suddenly"),
                ],
            ),
            _task(
                "The words class and room combine to name the room where a class learns.",
                "Form the compound, explain it, and use it in a sentence.",
                "Classroom combines class and room. It is a room for teaching a class, as in: Our classroom has a reading corner.",
                [
                    _evidence("form", "Forms classroom from class and room.", "Classroom combines class and room", "classroom"),
                    _evidence("meaning", "Explains the compound's meaning.", "room for teaching a class", "room where a class learns"),
                    _evidence("use", "Uses classroom accurately in a sentence.", "Our classroom has a reading corner", "Our classroom"),
                ],
            ),
            _task(
                "During the power cut, the lantern flickered; its light brightened, dimmed, and nearly vanished several times.",
                "Infer flickered from the changing-light clues, then explain why it does not mean the lantern stayed steadily bright.",
                "Flickered means shone unsteadily, repeatedly becoming brighter and dimmer. The light nearly vanished several times, so the lantern did not stay steady.",
                [
                    _evidence("meaning", "Defines flickered as unsteady changing light.", "shone unsteadily", "brighter and dimmer"),
                    _evidence("clue", "Uses the repeated near-disappearance to reject steady light.", "nearly vanished several times", "did not stay steady"),
                ],
            ),
            _task(
                "The bases book and case can join to name a piece of furniture that stores books.",
                "Build the compound, explain how both bases shape its meaning, and write a fresh sentence with it.",
                "Bookcase combines book and case and means a case used to store books. Our bookcase keeps the class atlases beside the dictionaries.",
                [
                    _evidence("form", "Forms bookcase from book and case.", "Bookcase combines book and case", "book + case"),
                    _evidence("book", "Explains that book identifies what the furniture stores.", "store books", "stores books"),
                    _evidence("case", "Explains that case identifies the kind of storage.", "case used to store", "means a case"),
                    _evidence("use", "Uses bookcase accurately in a fresh sentence.", "Our bookcase keeps", "bookcase keeps the class atlases"),
                ],
            ),
        ],
        "cluster_id": "scooter-word-guessing-confusion",
        "misconception": "The learner guesses from a familiar-looking word, ignores action-result clues, or joins base words without checking the compound's meaning.",
        "remediation": "Underline the action and result clue, test a plain-language meaning in the sentence, then split or join base words and verify the combined meaning.",
        "support": [
            _task(
                "The loose sign clattered against the gate, making repeated hard sounds in the wind.",
                "Explain clattered using the sound clue.",
                "Clattered means made repeated hard sounds, supported by the sign striking the gate in the wind.",
                [_evidence("meaning", "Uses the repeated hard-sound clue.", "repeated hard sounds", "striking the gate")],
            ),
            _task(
                "A strap was anchored to the railing, so the banner remained fixed during the storm.",
                "Infer anchored and connect it to the result.",
                "Anchored means fixed firmly in place; the banner stayed still because the strap held it to the railing.",
                [
                    _evidence("meaning", "Defines fixed firmly.", "fixed firmly", "held in place"),
                    _evidence("result", "Uses the banner remaining still.", "banner stayed still", "remained fixed"),
                ],
            ),
            _task(
                "Sun and light combine to name natural light from the sun.",
                "Build the compound and explain why both bases matter.",
                "Sunlight combines sun and light because it names light that comes from the sun.",
                [
                    _evidence("form", "Forms sunlight from sun and light.", "Sunlight combines sun and light", "sunlight"),
                    _evidence("sun", "Explains that sun identifies the source.", "comes from the sun", "from the sun"),
                    _evidence("light", "Explains that light identifies what is named.", "names light", "light that comes"),
                ],
            ),
            _task(
                "The runner glanced at the clock and immediately returned her eyes to the track.",
                "Define glanced and use the duration clue.",
                "Glanced means looked briefly; the runner immediately returned her eyes to the track.",
                [
                    _evidence("meaning", "Defines a brief look.", "looked briefly", "quick look"),
                    _evidence("clue", "Uses the immediate return to the track.", "immediately returned", "eyes to the track"),
                ],
            ),
            _task(
                "A safety pin fastened the torn number card to the jersey for the rest of the race.",
                "Explain fastened and write a new accurate use.",
                "Fastened means attached firmly. I fastened the map to the noticeboard with two clips.",
                [
                    _evidence("meaning", "Defines attached firmly.", "attached firmly", "held in place"),
                    _evidence("use", "Uses fastened in a fresh attachment sentence.", "fastened the map", "fastened the label", "fastened the strap"),
                ],
            ),
        ],
    },
    {
        "level_id": "scooter_connectors_and_adverbs",
        "title": "Show time, cause, and contrast",
        "focus": "use connectors and adverbs to make complete event sentences",
        "outcome": "Choose precise time or frequency adverbs and connect complete ideas with cause, time, addition, or contrast relations.",
        "skill_ids": CONNECTOR_SKILLS,
        "episode_kind": "language_lab",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:learn-connectors:6",
            f"{CHAPTER_ID}:learn-adverbs:7-8",
        ],
        "principle": "First name the relation: because gives cause, but gives contrast, and time or frequency adverbs answer when or how often.",
        "connect": {
            "teaching_block": "Connectors join ideas, while adverbs sharpen an action's timing or frequency. Each word has a different job.",
            "passage": "The team usually practises after school, but today it stopped early because rain began suddenly.",
            "prompt": "Notice how usually, today, but, and because each add a different relation.",
        },
        "co_construct": _choice(
            "The rider slowed ___ children were crossing near the gate.",
            "Which connector gives the reason?",
            "because",
            ["but", "however", "when"],
            skills=["grammar.connectors_because_and_but"],
        ),
        "guided": [
            _task(
                "Mina usually cycles to practice. This morning she walked because her tyre was flat.",
                "Write one complete sentence that keeps the frequency adverb and reason.",
                "Mina usually cycles to practice, but she walked this morning because her tyre was flat.",
                [
                    _evidence("adverb", "Uses usually as a frequency adverb.", "usually cycles", "usually rides"),
                    _evidence("relation", "Uses because for the flat-tyre reason.", "because her tyre was flat", "because of the flat tyre"),
                ],
            ),
            _task(
                "The class reached the field early. The gate opened late. They waited calmly.",
                "Join the ideas using but for contrast and an adverb showing how they waited.",
                "The class reached the field early, but the gate opened late, so they waited calmly.",
                [
                    _evidence("contrast", "Uses but between early arrival and late opening.", "early, but the gate opened late", "but the gate opened late"),
                    _evidence("adverb", "Uses calmly to describe waiting.", "waited calmly", "calmly waited"),
                ],
            ),
            _task(
                "Dev often checks the brakes before riding. Yesterday he found a loose cable and stopped.",
                "Write one complete sentence showing frequency, time, and result.",
                "Dev often checks the brakes before riding, and yesterday he stopped because he found a loose cable.",
                [
                    _evidence("frequency", "Uses often to show frequency.", "often checks", "often"),
                    _evidence("time", "Uses yesterday to show time.", "yesterday he stopped", "yesterday"),
                    _evidence("result", "Connects stopping to the loose cable.", "stopped because", "loose cable"),
                ],
            ),
            _task(
                "The whistle sounded suddenly. The players did not begin until the referee raised her hand.",
                "Combine the ideas with when and include the adverb suddenly.",
                "The whistle sounded suddenly, but the players began only when the referee raised her hand.",
                [
                    _evidence("time", "Uses when to link the starting condition.", "when the referee raised", "began only when"),
                    _evidence("adverb", "Keeps suddenly attached to sounded.", "sounded suddenly", "suddenly sounded"),
                ],
            ),
        ],
        "independent": [
            _task(
                "Facts: Sana regularly wears a helmet. Today the buckle broke. She did not ride.",
                "Write one complete sentence using a frequency adverb, but, and because.",
                "Sana regularly wears a helmet, but she did not ride today because the buckle broke.",
                [
                    _evidence("frequency", "Uses regularly as frequency information.", "regularly wears", "usually wears"),
                    _evidence("contrast", "Uses but to show contrast.", "but she did not ride today", "but she did not ride"),
                    _evidence("cause", "Uses because to give the cause.", "because the buckle broke", "because her buckle broke"),
                ],
            ),
            _task(
                "The delivery cart arrived later than expected. The players patiently waited and resumed their search when it stopped.",
                "Identify the time adverb and the manner adverb, then explain each job.",
                "Later tells when the cart arrived, while patiently explains how the players waited.",
                [
                    _evidence("time", "Identifies later as answering when.", "Later tells when", "later is time"),
                    _evidence("manner", "Identifies patiently as answering how.", "patiently explains how", "patiently is manner"),
                ],
                skills=["grammar.adverbs"],
            ),
            _task(
                "The team had searched near the gate. They checked the lane since the ball had crossed the fence.",
                "Write a clear complete sentence using since to express the reason.",
                "The team checked the lane since the ball had crossed the fence near the gate.",
                [_evidence("sentence", "Uses since for the stated reason in a complete sentence.", "since the ball had crossed", "checked the lane since")],
                skills=["grammar.connectors_because_and_but"],
            ),
            _task(
                "A rider normally parks beside the bakery. This evening the space was closed, so she parked carefully near the library.",
                "Write one sentence that preserves frequency, time, manner, and cause.",
                "The rider normally parks by the bakery, but this evening she parked carefully near the library because the usual space was closed.",
                [
                    _evidence("frequency", "Uses normally to show frequency.", "normally parks", "normally"),
                    _evidence("time", "Uses this evening to show time.", "this evening", "this evening she parked"),
                    _evidence("manner", "Uses carefully to show manner.", "parked carefully", "carefully near the library"),
                    _evidence("cause", "Uses because for the closed space.", "because the usual space was closed", "because the space was closed"),
                ],
            ),
        ],
        "transfer": [
            _task(
                "The museum usually closes at five. It remained open late because a school group arrived after a delayed train.",
                "Combine the facts using usually, late, and because correctly.",
                "The museum usually closes at five, but it stayed open late because the school group arrived after a delayed train.",
                [
                    _evidence("frequency", "Uses usually to show frequency.", "usually closes", "usually closes at five"),
                    _evidence("time", "Uses late to show time.", "open late", "stayed open late"),
                    _evidence("cause", "Uses because to give the cause.", "because the school group arrived", "because a school group arrived"),
                ],
            ),
            _task(
                "Ishaan rarely forgets his library card. Today he left it at home and quietly asked the librarian for help.",
                "Explain which words show frequency, time, and manner.",
                "Rarely shows frequency, today shows time, and quietly shows how Ishaan asked for help.",
                [
                    _evidence("frequency", "Labels rarely as frequency.", "Rarely shows frequency", "rarely is frequency"),
                    _evidence("time", "Labels today as time.", "today shows time", "today is time"),
                    _evidence("manner", "Labels quietly as manner.", "quietly shows how", "quietly is manner"),
                ],
                skills=["grammar.adverbs"],
            ),
            _task(
                "The nurse arrived quickly. The patient had to wait because another emergency was being treated.",
                "Join the ideas with but and because while keeping quickly beside the action it describes.",
                "The nurse arrived quickly, but the patient had to wait because another emergency was being treated.",
                [
                    _evidence("contrast", "Uses but for contrast.", "but the patient had to wait", "but the patient waited"),
                    _evidence("cause", "Uses because for the reason.", "because another emergency", "because an emergency"),
                    _evidence("manner", "Keeps quickly beside the action it describes.", "arrived quickly", "quickly arrived"),
                ],
            ),
            _task(
                "The ferry normally leaves at noon. It waited today when thick fog covered the river.",
                "Write a complete sentence showing the usual pattern and today's time condition.",
                "The ferry normally leaves at noon, but it waited today when thick fog covered the river.",
                [
                    _evidence("pattern", "Uses normally for the regular pattern.", "normally leaves", "usual noon departure"),
                    _evidence("condition", "Uses today and when for the fog condition.", "waited today when", "when thick fog covered"),
                ],
            ),
        ],
        "review": [
            _task(
                "The club often practises outdoors. It moved indoors yesterday because the ground was wet, but everyone trained enthusiastically.",
                "Name the frequency, time, and manner adverbs and explain both connectors.",
                "Often shows frequency, yesterday shows time, and enthusiastically shows manner; because gives the wet-ground reason, while but marks contrast.",
                [
                    _evidence("frequency", "Labels often as frequency.", "Often shows frequency", "often is frequency"),
                    _evidence("time", "Labels yesterday as time.", "yesterday shows time", "yesterday is time"),
                    _evidence("manner", "Labels enthusiastically as manner.", "enthusiastically shows manner", "enthusiastically is manner"),
                    _evidence("cause", "Explains because as the reason connector.", "because gives the wet-ground reason", "because gives the reason"),
                    _evidence("contrast", "Explains but as the contrast connector.", "but marks contrast", "but shows contrast"),
                ],
            ),
            _task(
                "Facts: bus generally arrives early; today arrived late; traffic jam; pupils waited quietly.",
                "Turn every fact into one or two complete connected sentences.",
                "The bus generally arrives early, but today it arrived late because of a traffic jam. The pupils waited quietly.",
                [
                    _evidence("facts", "Includes the usual arrival, today's delay, cause, and quiet waiting.", "generally arrives early", "arrived late", "traffic jam", "waited quietly"),
                    _evidence("structure", "Uses complete connected sentences.", "but today", "because of"),
                ],
            ),
            _task(
                "Anaya normally fills the bird tray early. Today she waited patiently because a cat sat near it, but the birds returned later.",
                "Classify normally, today, patiently, and later, then explain the jobs of because and but.",
                "Normally shows frequency, today and later show time, and patiently shows manner. Because introduces the cat as the reason for waiting, while but contrasts the wait with the birds' return.",
                [
                    _evidence("normally", "Classifies normally as frequency.", "Normally shows frequency", "normally is frequency"),
                    _evidence("today", "Classifies today as time.", "today", "today shows time"),
                    _evidence("patiently", "Classifies patiently as manner.", "patiently shows manner", "patiently is manner"),
                    _evidence("later", "Classifies later as time.", "later", "later shows time"),
                    _evidence("cause", "Explains because as the reason connector.", "Because introduces the cat", "reason for waiting"),
                    _evidence("contrast", "Explains but as the contrast connector.", "but contrasts", "contrasts the wait"),
                ],
            ),
            _task(
                "Facts: repair team usually works after school; today it arrived early; a ceiling panel was loose; pupils moved calmly to the library.",
                "Use every fact in two complete sentences with but and because, placing the adverbs beside the actions they modify.",
                "The repair team usually works after school, but today it arrived early because a ceiling panel was loose. The pupils moved calmly to the library.",
                [
                    _evidence("adverbs", "Places usually, today, and calmly with the correct actions.", "usually works", "but today", "moved calmly"),
                    _evidence("links", "Uses but for the changed schedule and because for its cause.", "but today it arrived early", "because a ceiling panel was loose"),
                ],
            ),
        ],
        "cluster_id": "scooter-relation-and-adverb-confusion",
        "misconception": "The learner swaps connectors by sound, labels every time word as frequency, or places an adverb where its target action becomes unclear.",
        "remediation": "Label the intended relation and ask when, how often, or how before choosing a word; attach each adverb beside the action it modifies.",
        "support": [
            _task(
                "Nora usually walks, but today she cycled because she was late.",
                "Label usually and today, then explain but and because.",
                "Usually shows frequency and today shows time; but marks contrast, while because gives the reason for cycling.",
                [
                    _evidence("frequency", "Labels usually as frequency.", "Usually shows frequency", "usually is frequency"),
                    _evidence("time", "Labels today as time.", "today shows time", "today is time"),
                    _evidence("contrast", "Explains but as contrast.", "but marks contrast", "but shows contrast"),
                    _evidence("cause", "Explains because as cause.", "because gives the reason", "reason for cycling"),
                ],
            ),
            _task(
                "The team carefully moved the goalpost because one leg was loose, but the match began on time.",
                "Explain carefully, because, and but by their jobs.",
                "Carefully tells how the team moved it, because gives the loose-leg reason, and but contrasts the repair with the on-time start.",
                [
                    _evidence("manner", "Explains carefully as manner.", "Carefully tells how", "moved it carefully"),
                    _evidence("cause", "Explains because as cause.", "because gives the loose-leg reason", "because gives"),
                    _evidence("contrast", "Explains but as contrast.", "but contrasts", "contrasts the repair"),
                ],
            ),
            _task(
                "Facts: courier often arrives at noon; today came early; school gate still closed.",
                "Build a sentence using often, today, and but.",
                "The courier often arrives at noon, but today the courier came early while the school gate was still closed.",
                [
                    _evidence("frequency", "Uses often to show frequency.", "often arrives", "often"),
                    _evidence("time", "Uses today to show time.", "today the courier came early", "today"),
                    _evidence("contrast", "Uses but to show contrast.", "but today", "but today the courier"),
                ],
            ),
            _task(
                "The players waited patiently when the groundskeeper repaired the net.",
                "Explain which word answers how and which word connects the time.",
                "Patiently answers how the players waited, and when links their waiting to the repair time.",
                [
                    _evidence("how", "Identifies patiently as manner.", "Patiently answers how", "waited patiently"),
                    _evidence("time", "Identifies when as the time connector.", "when links", "repair time"),
                ],
            ),
            _task(
                "Facts: rider never ignores a red signal; road empty; waited until green.",
                "Write a complete sentence that keeps the frequency and contrast.",
                "The rider never ignores a red signal, so even though the road was empty, she waited until it turned green.",
                [
                    _evidence("frequency", "Uses never for the consistent habit.", "never ignores", "never crosses"),
                    _evidence("contrast", "Contrasts empty road with waiting for green.", "road was empty", "waited until it turned green"),
                ],
            ),
        ],
    },
    {
        "level_id": "scooter_precise_grammar",
        "title": "Build precise event sentences",
        "focus": "maintain past tense and arrange events in natural sentence order",
        "outcome": "Choose time-matched past-tense verbs and arrange subjects, actions, objects, places, and times into clear event sentences.",
        "skill_ids": GRAMMAR_SKILLS,
        "episode_kind": "language_lab",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:learn-adverbs:7-8",
            f"{CHAPTER_ID}:write:11-12",
        ],
        "principle": "Use the time clue to choose the verb form, then arrange who, action, object, place, and time in a natural order.",
        "connect": {
            "teaching_block": "A clear event sentence tells who acted, what happened, and when. A past-time clue requires a past-tense action, while natural order keeps the event easy to follow.",
            "passage": "Yesterday, the mechanic tightened the mirror before noon.",
            "prompt": "Notice who acted, the completed action, and where the time clues sit before continuing.",
        },
        "co_construct": _choice(
            "The noisy scooter crossed the narrow lane.",
            "Which word is the past-tense action?",
            "crossed",
            ["noisy", "scooter", "narrow"],
        ),
        "guided": [
            _choice(
                "At noon, the guard ___ the moving cart.",
                "Which verb form matches the completed past event?",
                "stopped",
                ["stop", "stops", "stopping"],
                skills=["grammar.tense_usage"],
            ),
            _choice(
                "Yesterday, Rohan ___ the ball near the gate.",
                "Which verb fits the past-time clue?",
                "found",
                ["find", "finds", "finding"],
            ),
            _choice(
                "quietly / the rider / checked / the mirror",
                "Which order makes a clear sentence?",
                "The rider checked the mirror quietly.",
                ["Checked quietly the rider the mirror.", "The mirror rider quietly checked.", "Quietly the mirror checked rider."],
                skills=["grammar.sentence_order"],
            ),
            _choice(
                "after the bell / the signal / flashed / twice",
                "Which order makes the event clear?",
                "The signal flashed twice after the bell.",
                ["Flashed the signal after twice the bell.", "After flashed twice the signal bell.", "The bell twice the signal flashed after."],
                skills=["grammar.sentence_order"],
            ),
        ],
        "independent": [
            _task(
                "Words: the careful rider / fastened / the loose strap / yesterday.",
                "Arrange the words into a clear sentence, then explain why fastened matches the time clue.",
                "The careful rider fastened the loose strap yesterday. Fastened is past tense because yesterday places the completed action in the past.",
                [
                    _evidence("sentence", "Orders all supplied parts into a grammatical sentence.", "The careful rider fastened the loose strap yesterday"),
                    _evidence("tense", "Links fastened to the past-time clue.", "fastened is past tense", "yesterday"),
                ],
                ordered=True,
            ),
            _task(
                "Time clue: last evening. Notes: delivery van; stop; outside school; driver; check; rear door.",
                "Write one or two complete past-tense sentences using every note.",
                "Last evening, the delivery van stopped outside the school, and the driver checked the rear door.",
                [
                    _evidence("tense", "Uses past-tense stopped and checked.", "van stopped", "driver checked"),
                    _evidence("details", "Includes school and rear door in clear order.", "outside the school", "rear door"),
                ],
            ),
            _task(
                "Jumbled report: before sunset / the repair team / tested / the scooter brakes / twice.",
                "Arrange every part into one natural past-tense sentence and identify the completed action.",
                "The repair team tested the scooter brakes twice before sunset. Tested is the completed past action.",
                [
                    _evidence("order", "Uses every part in natural sentence order.", "repair team tested", "scooter brakes", "twice", "before sunset"),
                    _evidence("tense", "Identifies tested as the completed past action.", "tested", "past action"),
                ],
                ordered=True,
            ),
            _task(
                "Jumbled parts: near the gate / the children / spotted / a green helmet / after lunch.",
                "Arrange the parts into a complete past-tense sentence.",
                "The children spotted a green helmet near the gate after lunch.",
                [_evidence("order", "Produces the complete ordered sentence with past tense.", "children spotted", "green helmet", "near the gate", "after lunch")],
                ordered=True,
                skills=["grammar.sentence_order", "grammar.tense_usage"],
            ),
        ],
        "transfer": [
            _task(
                "Notes from a clinic: helpful nurse; carry; heavy box; storeroom; this morning.",
                "Write one natural sentence using every note, then explain why carried is the correct time form.",
                "The helpful nurse carried the heavy box to the storeroom this morning. Carried matches this morning because the action is already complete.",
                [
                    _evidence(
                        "sentence",
                        "Uses all notes in an ordered past-time sentence.",
                        "helpful nurse carried the heavy box to the storeroom this morning",
                        "the helpful nurse carried the heavy box to the storeroom this morning",
                    ),
                    _evidence("tense", "Explains the completed past action.", "carried", "action is already complete"),
                ],
            ),
            _task(
                "Jumbled report: the guide / carefully / counted / every ticket / before the bus left.",
                "Rebuild the report and explain why counted matches the time relation.",
                "The guide carefully counted every ticket before the bus left. Counted is past tense because both events already happened.",
                [
                    _evidence("order", "Rebuilds the complete sentence.", "guide carefully counted every ticket", "before the bus left"),
                    _evidence("tense", "Explains the completed past events.", "past tense", "already happened"),
                ],
                ordered=True,
            ),
            _task(
                "Jumbled incident note: before help arrived / the bridge / shook / during the storm.",
                "Rebuild the incident note and explain which event happened later.",
                "The bridge shook during the storm before help arrived. Help arrived later because before links it after the shaking.",
                [
                    _evidence("order", "Rebuilds the incident in natural order.", "bridge shook", "during the storm", "before help arrived"),
                    _evidence("sequence", "Identifies help arriving as later.", "help arrived later", "before"),
                ],
                ordered=True,
            ),
            _task(
                "Time clue: two hours ago. Notes: airport worker; inspect; damaged suitcase; place; service trolley.",
                "Write one clear past-tense sentence in natural order.",
                "Two hours ago, an airport worker inspected the damaged suitcase and placed it on a service trolley.",
                [_evidence("sentence", "Uses both past actions and all details in natural order.", "worker inspected", "damaged suitcase", "placed it", "service trolley")],
                ordered=True,
            ),
        ],
        "review": [
            _task(
                "Words: yesterday / the alert driver / noticed / a loose wheel / beside the market.",
                "Make one natural sentence and explain how the time clue controls the verb form.",
                "Yesterday, the alert driver noticed a loose wheel beside the market. Noticed is past tense because yesterday shows that the action is complete.",
                [
                    _evidence("sentence", "Builds the complete past-time sentence.", "driver noticed", "loose wheel", "beside the market"),
                    _evidence("tense", "Links noticed to yesterday.", "noticed is past tense", "yesterday"),
                ],
            ),
            _task(
                "Jumbled parts: the red parcel / slipped / under the counter / during the rush.",
                "Arrange the sentence and explain why slipped is the correct time form.",
                "The red parcel slipped under the counter during the rush. Slipped is past tense because the event is completed.",
                [
                    _evidence("order", "Arranges all parts correctly.", "red parcel slipped", "under the counter", "during the rush"),
                    _evidence("tense", "Explains the completed past action.", "past tense", "event is completed"),
                ],
                ordered=True,
            ),
            _task(
                "Security log at 6 p.m.: corridor lights fail; caretaker fetches a torch; electrician repairs the switch.",
                "Turn the log into two natural past-tense sentences that preserve the event order, then explain the verb forms.",
                "At 6 p.m., the corridor lights failed, so the caretaker fetched a torch. The electrician then repaired the switch. Failed, fetched, and repaired are past-tense verbs because the logged events are complete.",
                [
                    _evidence("order", "Keeps the light failure before the torch and repair actions.", "lights failed", "caretaker fetched a torch", "then repaired the switch"),
                    _evidence("tense", "Explains why all three verbs use past tense.", "past-tense verbs", "events are complete"),
                ],
                ordered=True,
            ),
            _task(
                "Trip record from last Sunday: our class / walk from the museum to the bus stop / the guide wave goodbye first.",
                "Write one natural sentence that shows the goodbye happened before the walk, then explain the two verb forms.",
                "Last Sunday, after the guide waved goodbye, our class walked from the museum to the bus stop. Waved is past tense because the goodbye is complete, and walked is past tense because the journey is complete.",
                [
                    _evidence("sequence", "Places the guide's goodbye before the class walk.", "after the guide waved goodbye", "class walked from the museum"),
                    _evidence("waved", "Explains why waved is past tense.", "Waved is past tense", "goodbye is complete"),
                    _evidence("walked", "Explains why walked is past tense.", "walked is past tense", "journey is complete"),
                ],
                ordered=True,
            ),
        ],
        "cluster_id": "scooter-word-role-order-confusion",
        "misconception": "The learner chooses a verb without reading the time clue, labels words by position alone, or reproduces every jumbled part in an ungrammatical order.",
        "remediation": "Build a who-did-what frame, place the object, place and time clues, then read the sentence aloud to check order and past-tense consistency.",
        "support": [
            _task(
                "Time clue: yesterday. Notes: guard; lift; barrier; near the gate.",
                "Write one complete sentence and use the verb form required by the time clue.",
                "Yesterday, the guard lifted the barrier near the gate.",
                [_evidence("sentence", "Uses all details with a past-tense action.", "guard lifted", "barrier", "near the gate", "yesterday")],
            ),
            _task(
                "Jumbled frame: the mechanic / tightened / the loose bolt / before noon.",
                "Rebuild the sentence and mark who, action, object, and time.",
                "The mechanic tightened the loose bolt before noon: mechanic is who, tightened is the action, bolt is the object, and before noon is time.",
                [
                    _evidence("sentence", "Rebuilds the correct sentence.", "mechanic tightened the loose bolt before noon"),
                    _evidence("who", "Labels mechanic as who.", "mechanic is who", "mechanic names who"),
                    _evidence("action", "Labels tightened as the action.", "tightened is the action", "tightened names the action"),
                    _evidence("object", "Labels bolt as the object.", "bolt is the object", "bolt names the object"),
                    _evidence("time", "Labels before noon as time.", "before noon is time", "before noon names time"),
                ],
                ordered=True,
            ),
            _task(
                "Time clue: last week. Notes: school team; visit; cycle workshop; learn; safety checks.",
                "Write one or two past-tense sentences using all notes.",
                "Last week, the school team visited a cycle workshop and learned about safety checks.",
                [_evidence("past", "Uses visited and learned with all details.", "team visited", "learned about safety checks", "last week")],
            ),
            _task(
                "Jumbled frame: after the warning / the rider / covered / the parcel / with a jacket.",
                "Arrange the report and identify the completed action.",
                "The rider covered the parcel with a jacket after the warning. Covered is the completed past action.",
                [
                    _evidence("order", "Builds the natural report order.", "rider covered", "parcel", "with a jacket", "after the warning"),
                    _evidence("tense", "Identifies covered as the completed past action.", "covered", "past action"),
                ],
                ordered=True,
            ),
            _task(
                "Jumbled report: at sunset / the last bus / left / the crowded stop.",
                "Arrange the report and explain the tense choice.",
                "The last bus left the crowded stop at sunset. Left is past tense because the departure is complete.",
                [
                    _evidence("order", "Builds the natural sentence order.", "last bus left", "crowded stop", "at sunset"),
                    _evidence("tense", "Explains the completed past action.", "past tense", "departure is complete"),
                ],
                ordered=True,
            ),
        ],
    },
    {
        "level_id": "scooter_summary_and_profile",
        "title": "Summarize and report facts",
        "focus": "shape own-words summaries, paragraphs, and bounded profiles",
        "outcome": "Select central details, write an organised own-words paragraph, and report only supported facts from a supplied profile packet.",
        "skill_ids": SYNTHESIS_SKILLS,
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:write:11-12",
        ],
        "principle": "A summary keeps problem, response, and outcome; a profile paragraph selects attributed facts and never fills gaps with invention.",
        "connect": {
            "teaching_block": "Long activities become clearer when details are selected for a purpose. A summary and a profile need different kinds of evidence.",
            "passage": "A class recovered a lost ball by recording a vehicle number, contacting the depot, and collecting the ball safely the next day.",
            "prompt": "Notice the problem, two useful actions, and final outcome before shaping a paragraph.",
        },
        "co_construct": _choice(
            "Fact packet: Nisha Verma plays goalkeeper, attended a district camp, and received her school's fair-play badge. Source: school sports notice.",
            "Which sentence is fully supported by the packet?",
            "Nisha Verma attended a district camp and received a school fair-play badge.",
            ["Nisha Verma won an international final.", "Nisha Verma coaches the district team.", "Nisha Verma designed the school's sports ground."],
            skills=["research.information_selection"],
        ),
        "guided": [
            _task(
                "Problem: a practice ball travelled away in a cart. Response: pupils noted the cart number and asked the depot for help. Outcome: the driver returned it the next morning.",
                "Write a three-sentence paragraph in your own words, with an opening, connected action detail, and outcome.",
                "The pupils lost their practice ball when it travelled away in a cart. They noted the cart number and contacted the depot. The driver returned the ball the next morning.",
                [
                    _evidence("opening", "Opens with the lost practice ball.", "practice ball when it travelled away", "lost their practice ball"),
                    _evidence("action", "Includes the pupils' useful response.", "contacted the depot", "noted the cart number"),
                    _evidence("outcome", "Ends with the ball being returned.", "returned the ball the next morning", "driver returned the ball"),
                    _evidence("own_words", "Uses connected original sentences rather than copying labels.", "pupils lost", "They noted", "driver returned"),
                ],
                interaction_type="paragraph_text",
            ),
            _task(
                "Fact packet: Maya Singh; goalkeeper; trained at a district academy; led her school team in 2025; received a fair-play award. Source: school sports bulletin.",
                "Write a short factual profile using three supported facts and name the source.",
                "According to the school sports bulletin, Maya Singh is a goalkeeper who trained at a district academy, led her school team in 2025, and received a fair-play award.",
                [
                    _evidence("facts", "Selects at least three supplied facts accurately.", "goalkeeper", "district academy", "led her school team", "fair-play award"),
                    _evidence("source", "Attributes the facts to the school sports bulletin.", "According to the school sports bulletin", "school sports bulletin reports"),
                ],
                interaction_type="paragraph_text",
                learner_part_count=4,
            ),
            _task(
                "A board game packet lists: two players; one controls four tigers; the other controls twenty goats; pieces move only along marked lines; the goal depends on blocking or capturing.",
                "Write an organised overview without inventing any extra rule.",
                "The game has two players: one controls four tigers and the other twenty goats. Pieces move on marked lines, and players aim either to block or capture according to their role.",
                [
                    _evidence("selected", "Includes players, pieces, movement, and broad goals.", "two players", "four tigers", "twenty goats", "marked lines"),
                    _evidence("bounded", "Does not add unsupported moves or scoring.", "aim either to block or capture", "according to their role"),
                ],
                interaction_type="summary",
            ),
            _task(
                "A sports survey records: six pupils prefer indoor games, nine prefer outdoor games, and three enjoy both. The class plans one indoor and one outdoor activity day.",
                "Write a focused paragraph that reports the figures and explains the class plan.",
                "The survey shows that nine pupils prefer outdoor games, six prefer indoor games, and three enjoy both. Therefore, the class will hold one day for each type so both preferences are included.",
                [
                    _evidence("figures", "Reports all three survey groups accurately.", "nine pupils", "six prefer", "three enjoy both"),
                    _evidence("plan", "Connects the two-day plan to inclusion.", "one day for each", "both preferences"),
                ],
                interaction_type="paragraph_text",
            ),
        ],
        "independent": [
            _task(
                "During a match, a ball crossed the gate and landed in a vegetable van. The players recorded the van number, informed the coach, and called the market office. A vendor returned the ball that evening.",
                "Write a 45- to 65-word own-words summary with problem, response, and outcome.",
                "A ball accidentally left the field in a vegetable van. Instead of chasing it, the players recorded the vehicle number, told their coach, and contacted the market office. Their careful steps worked, and a vendor brought the ball back that evening.",
                [
                    _evidence("main", "States the accidental loss as the central problem.", "ball accidentally left", "ball travelled in a van"),
                    _evidence("response", "Includes the useful recording and contact actions.", "recorded the vehicle number", "contacted the market office"),
                    _evidence("outcome", "Ends with the ball being returned.", "brought the ball back", "vendor returned the ball"),
                ],
                interaction_type="summary",
                min_words=18,
            ),
            _task(
                "Profile packet: Zoya Khan; defender; practises four mornings a week; captained the district under-12 side; helped organise free weekend drills; source: district youth newsletter.",
                "Write a four-sentence profile using only supported facts and clear organisation.",
                "The district youth newsletter profiles Zoya Khan as a defender. She practises four mornings each week and captained the district under-12 side. She also helped organise free weekend drills. These facts show her work both as a player and a community helper.",
                [
                    _evidence("facts", "Uses role, practice, captaincy, and drills accurately.", "defender", "four mornings", "captained", "weekend drills"),
                    _evidence("source", "Attributes the packet to the district youth newsletter.", "district youth newsletter", "newsletter profiles"),
                    _evidence("structure", "Uses a focused opening, connected details, and closing idea.", "profiles Zoya Khan", "These facts show"),
                ],
                interaction_type="paragraph_text",
                min_words=20,
            ),
            _task(
                "Game notes: teams of five; soft ball; one marked target; each team gets three turns; a hit earns one point; highest total wins. Safety: throw below shoulder height.",
                "Write a clear paragraph explaining the game without adding rules.",
                "Teams of five take three turns each to throw a soft ball at one marked target. Every hit earns one point, and the highest total wins. For safety, all throws must stay below shoulder height.",
                [
                    _evidence("rules", "Includes teams, turns, target, point, and winning condition.", "teams of five", "three turns", "one point", "highest total wins"),
                    _evidence("safety", "Includes the below-shoulder rule.", "below shoulder height", "throws must stay below"),
                ],
                interaction_type="paragraph_text",
            ),
            _task(
                "Event notes: class planned a mini sports day; rain flooded the field; pupils moved two games indoors; they shortened the schedule; every team completed both games.",
                "Write an own-words paragraph with a topic sentence, two connected details, and a closing result.",
                "The class adapted its mini sports day when rain flooded the field. Pupils moved two games indoors and shortened the schedule. Because of these changes, every team still completed both games.",
                [
                    _evidence("opening", "Introduces the need to adapt sports day.", "adapted its mini sports day", "rain flooded the field"),
                    _evidence("indoor", "Includes moving two games indoors.", "moved two games indoors", "games indoors"),
                    _evidence("schedule", "Includes shortening the schedule.", "shortened the schedule", "shorter schedule"),
                    _evidence("closing", "Ends with all teams completing both games.", "every team", "completed both games"),
                ],
                interaction_type="paragraph_text",
            ),
        ],
        "transfer": [
            _task(
                "A library's reading cards blew from an outdoor table. Volunteers divided the garden into zones, collected every card, checked the numbers, and restored the full set before closing.",
                "Summarize the problem-solving process in 35 to 55 words.",
                "Wind scattered the library's reading cards across the garden. Volunteers organised the search by zones, collected the cards, and checked their numbers. Their planned search recovered the complete set before the library closed.",
                [
                    _evidence("problem", "States that wind scattered the cards.", "Wind scattered", "cards across the garden"),
                    _evidence("response", "Includes zone search and number checking.", "search by zones", "checked their numbers"),
                    _evidence("outcome", "Ends with complete recovery before closing.", "complete set", "before the library closed"),
                ],
                interaction_type="summary",
                min_words=15,
            ),
            _task(
                "Profile packet: Arjun Mehta; para-swimmer; began training at age ten; won two state medals in 2024; teaches water-safety sessions monthly; source: city sports council note.",
                "Write a sourced profile that selects the three most relevant facts for a school sports display.",
                "The city sports council note describes Arjun Mehta as a para-swimmer who began training at ten and won two state medals in 2024. He also teaches monthly water-safety sessions, linking sport with community service.",
                [
                    _evidence("role", "Selects Arjun's para-swimmer role.", "para-swimmer", "Arjun Mehta as a para-swimmer"),
                    _evidence("achievement", "Selects a supported training or medal fact.", "training at ten", "two state medals"),
                    _evidence("service", "Selects the monthly water-safety service.", "water-safety sessions", "teaches monthly water-safety"),
                    _evidence("source", "Names the city sports council note.", "city sports council note", "council note describes"),
                ],
                interaction_type="paragraph_text",
            ),
            _task(
                "A science club built a wind-powered model. The first sail tore, so members tested stronger paper, measured three shapes, and chose the one that turned most steadily. The final model ran for ten minutes.",
                "Write a paragraph that keeps the problem, testing process, and result.",
                "The science club improved its wind-powered model after the first sail tore. Members tested stronger paper and compared three shapes before choosing the steadiest design. Their final model then ran successfully for ten minutes.",
                [
                    _evidence("problem", "Identifies the torn first sail.", "first sail tore", "after the sail tore"),
                    _evidence("process", "Includes material and shape testing.", "tested stronger paper", "compared three shapes"),
                    _evidence("result", "States the ten-minute run.", "ran for ten minutes", "final model"),
                ],
                interaction_type="paragraph_text",
            ),
            _task(
                "Survey packet: 12 families walk to the market; 8 cycle; 5 use a bus; source: neighbourhood travel survey. The committee wants one safety message for the largest group.",
                "Select the relevant figures and write the recommended message without inventing data.",
                "The neighbourhood travel survey shows that walking is the largest group with twelve families, compared with eight cycling and five using a bus. The committee should therefore prepare a pedestrian-safety message.",
                [
                    _evidence("figures", "Reports all supplied figures accurately.", "twelve families", "eight cycling", "five using a bus"),
                    _evidence("selection", "Selects pedestrians because they are the largest group.", "walking is the largest", "pedestrian-safety message"),
                ],
                interaction_type="paragraph_text",
            ),
        ],
        "review": [
            _task(
                "A class's handmade game pieces went missing during cleanup. Pupils checked the activity log, searched only the recorded rooms, and found the box in the art cupboard. They updated the log afterward.",
                "Write a concise own-words summary with problem, evidence-led action, and result.",
                "The class used its activity log to trace missing game pieces. Pupils searched the recorded rooms, found the box in the art cupboard, and updated the log so future cleanup would be clearer.",
                [
                    _evidence("problem", "States that game pieces were missing.", "missing game pieces", "pieces went missing"),
                    _evidence("action", "Uses the log-led search.", "used its activity log", "searched the recorded rooms"),
                    _evidence("result", "Includes discovery and log update.", "found the box", "updated the log"),
                ],
                interaction_type="summary",
            ),
            _task(
                "Fact packet: Naina Das; hockey umpire; earned a national umpiring qualification in 2023; officiated forty school matches; mentors new umpires; source: state school-games report.",
                "Write a sourced three-sentence profile with no unsupported praise.",
                "The state school-games report identifies Naina Das as a hockey umpire who earned a national umpiring qualification in 2023. She has officiated forty school matches. She also mentors new umpires.",
                [
                    _evidence("facts", "Reports role, qualification, matches, and mentoring accurately.", "hockey umpire", "umpiring qualification in 2023", "forty school matches", "mentors new umpires"),
                    _evidence("source", "Attributes the information to the state report.", "state school-games report", "report identifies"),
                ],
                interaction_type="paragraph_text",
            ),
            _task(
                "The school radio became silent during assembly. The media club checked the battery and cable, found a loose plug, and reconnected it. The broadcast resumed, and the pupils labelled the plug before packing the equipment.",
                "Summarize the problem, investigation, and outcome in your own words without listing every action separately.",
                "When the school radio stopped during assembly, the media club traced the problem to a loose plug by checking the power parts. Reconnecting it restored the broadcast, and labelling the plug helped prevent the same confusion during future setup.",
                [
                    _evidence("problem", "States that the radio stopped during assembly.", "radio stopped during assembly", "radio became silent"),
                    _evidence("investigation", "Condenses the checks into finding the loose plug.", "traced the problem to a loose plug", "found a loose plug"),
                    _evidence("outcome", "Includes the restored broadcast and useful label.", "restored the broadcast", "labelling the plug"),
                ],
                interaction_type="summary",
                min_words=15,
            ),
            _task(
                "Community project packet: Salma Khan; coordinates a rooftop garden; organised a rainwater system; twenty-four families participate; the system saves about three hundred litres each week; favourite colour is green; source: municipal eco-club bulletin.",
                "Write a sourced two-sentence profile selecting the work and impact facts while leaving out the unrelated personal detail.",
                "The municipal eco-club bulletin profiles Salma Khan as the coordinator of a rooftop garden who organised its rainwater system. The project involves twenty-four families and saves about three hundred litres of water each week.",
                [
                    _evidence("role", "Identifies Salma's role and rainwater work.", "coordinator of a rooftop garden", "organised its rainwater system"),
                    _evidence("impact", "Reports the participation and weekly saving accurately.", "twenty-four families", "three hundred litres", "each week"),
                    _evidence("source", "Attributes the profile to the supplied bulletin.", "municipal eco-club bulletin", "bulletin profiles"),
                ],
                interaction_type="paragraph_text",
                min_words=15,
            ),
        ],
        "cluster_id": "scooter-summary-and-research-overreach",
        "misconception": "The learner copies labels, lists every detail without a central idea, or adds unsupported achievements and opinions to make a profile sound impressive.",
        "remediation": "Sort information into purpose, supporting facts, and outcome; draft a topic sentence, select only attributed evidence, and remove copied or invented detail.",
        "support": [
            _task(
                "Problem: score cards scattered. Action: teams searched assigned rows and checked numbers. Result: complete set recovered.",
                "Turn the notes into three connected own-words sentences.",
                "The score cards scattered across the ground. Teams searched assigned rows and checked each number. Their organised search recovered the complete set.",
                [_evidence("structure", "Includes problem, action, and result in connected sentences.", "score cards scattered", "searched assigned rows", "recovered the complete set")],
                interaction_type="paragraph_text",
            ),
            _task(
                "Fact packet: Rehan Ali; table-tennis player; trains at community centre; won district doubles event; source: centre notice.",
                "Write a sourced profile using every supplied fact and nothing invented.",
                "The community centre notice profiles Rehan Ali as a table-tennis player who trains at the centre and won the district doubles event.",
                [
                    _evidence("facts", "Uses role, training place, and event accurately.", "table-tennis player", "community centre", "district doubles"),
                    _evidence("source", "Names the centre notice.", "community centre notice", "notice profiles"),
                ],
                interaction_type="paragraph_text",
            ),
            _task(
                "A paragraph draft repeats that a ball was lost four times but never says how it returned. Notes show that a guard called the depot and a driver returned it.",
                "Revise the paragraph's focus in two or three sentences.",
                "A ball was lost when a delivery cart left the field. The guard contacted the depot, and the driver returned the ball. These actions solved the problem.",
                [
                    _evidence("focus", "States the problem once and prioritises solution.", "ball was lost", "guard contacted the depot"),
                    _evidence("outcome", "Includes the driver's return and resolution.", "driver returned the ball", "solved the problem"),
                ],
                interaction_type="summary",
            ),
            _task(
                "Survey facts: 10 pupils enjoy chess; 7 enjoy carrom; 4 enjoy both. Source: class game survey.",
                "Report the figures and one supported conclusion.",
                "The class game survey records ten chess players, seven carrom players, and four who enjoy both. Chess has the larger listed group, although the overlap shows some pupils enjoy both games.",
                [
                    _evidence("figures", "Reports all three counts correctly.", "ten chess", "seven carrom", "four who enjoy both"),
                    _evidence("conclusion", "Draws only a supported comparison.", "Chess has the larger", "some pupils enjoy both"),
                ],
                interaction_type="paragraph_text",
            ),
            _task(
                "Profile draft claims a runner is the country's greatest athlete. The packet only says she won the school 800-metre race and practises three evenings weekly.",
                "Rewrite the profile so every claim is supported.",
                "The runner won her school's 800-metre race and practises three evenings each week. The packet provides no evidence for a national ranking.",
                [
                    _evidence("supported", "Keeps the school race and practice facts.", "won her school's", "three evenings"),
                    _evidence("boundary", "Rejects the unsupported national claim.", "no evidence for a national ranking", "does not support greatest"),
                ],
                interaction_type="paragraph_text",
            ),
        ],
    },
]


SOURCE_ANCHORS = [
    {
        "anchor_id": f"{CHAPTER_ID}:read:1-4",
        "section_label": "Let us Read: Narrative and Dialogue",
        "page_start": 1,
        "page_end": 4,
        "source_url": f"{SOURCE_URL}#page=1",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:new-words:5",
        "section_label": "New Words",
        "page_start": 5,
        "page_end": 5,
        "source_url": f"{SOURCE_URL}#page=5",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:think:5",
        "section_label": "Let us Think: Comprehension, Imagination, and Road Safety",
        "page_start": 5,
        "page_end": 5,
        "source_url": f"{SOURCE_URL}#page=5",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:learn-a-b:6",
        "section_label": "Let us Learn: Word Meanings and Connectors",
        "page_start": 6,
        "page_end": 6,
        "source_url": f"{SOURCE_URL}#page=6",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:learn-connectors:6",
        "section_label": "Let us Learn: Cause, Time, and Contrast Connectors",
        "page_start": 6,
        "page_end": 6,
        "source_url": f"{SOURCE_URL}#page=6",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:learn-adverbs:7-8",
        "section_label": "Let us Learn: Adverbs of Frequency and Time",
        "page_start": 7,
        "page_end": 8,
        "source_url": f"{SOURCE_URL}#page=7",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:listen:9",
        "section_label": "Let us Listen: Follow Spoken Spatial Instructions",
        "page_start": 9,
        "page_end": 9,
        "source_url": f"{SOURCE_URL}#page=9",
        "coverage_treatment": "guided_only",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:speak:10",
        "section_label": "Let us Speak: Chain Story and Sound Practice",
        "page_start": 10,
        "page_end": 10,
        "source_url": f"{SOURCE_URL}#page=10",
        "coverage_treatment": "offline_group_activity",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:write:11-12",
        "section_label": "Let us Write: Dialogue, Compounds, and Spelling Clues",
        "page_start": 11,
        "page_end": 12,
        "source_url": f"{SOURCE_URL}#page=11",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:write-b-c:11-12",
        "section_label": "Let us Write: Compound Words and Letter Patterns",
        "page_start": 11,
        "page_end": 12,
        "source_url": f"{SOURCE_URL}#page=11",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:do:13-14",
        "section_label": "Let us Do: Tigers and Goats Board Game",
        "page_start": 13,
        "page_end": 14,
        "source_url": f"{SOURCE_URL}#page=13",
        "coverage_treatment": "textbook_companion",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:explore:15-17",
        "section_label": "Let us Explore: Game Survey and Sportsperson Profile",
        "page_start": 15,
        "page_end": 17,
        "source_url": f"{SOURCE_URL}#page=15",
        "coverage_treatment": "textbook_companion",
        "required_for_chapter_certification": False,
    },
]


def _assessment_choice(
    item_no: int,
    skill_id: str,
    passage: str,
    prompt: str,
    correct: str,
    distractors: list[str],
) -> dict[str, Any]:
    item_id = f"{CHAPTER_ID}:assessment:{item_no:02d}"
    raw = [correct, *distractors]
    shift = item_no % len(raw)
    options = raw[shift:] + raw[:shift]
    return {
        "kind": "selected_option",
        "activity_id": item_id,
        "teaching_block": (
            "Use the chapter strategy named in the question and verify the "
            "precise clue before selecting an answer."
        ),
        "passage": passage,
        "prompt": prompt,
        "skill_ids": [skill_id],
        "options": options,
        "accepted_answers": [correct],
    }


def _assessment_open(
    item_no: int,
    skill_id: str,
    passage: str,
    prompt: str,
    model_answer: str,
    description: str,
    phrases: list[str],
    *,
    min_words: int = 6,
) -> dict[str, Any]:
    criterion_id = f"{CHAPTER_ID}:assessment:{item_no:02d}:evidence"
    return {
        "kind": "open_response",
        "activity_id": f"{CHAPTER_ID}:assessment:{item_no:02d}",
        "teaching_block": (
            "Answer independently from the supplied evidence. Include each "
            "requested part and use original wording."
        ),
        "passage": passage,
        "prompt": prompt,
        "skill_ids": [skill_id],
        "interaction_type": "evidence_text",
        "pass_score": 0.8,
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": description,
                "required": True,
                "min_quality": 0.65,
            }
        ],
        "concept_slots": [
            {"id": criterion_id, "description": description, "any_of": phrases}
        ],
        "min_response_words": min_words,
        "forbidden_phrases": [
            "The supplied details can be ignored",
            "I copied the sample answer",
        ],
        "relevance_terms": _terms(model_answer),
        "model_answer": model_answer,
    }


ASSESSMENT_ITEMS = [
    _assessment_choice(1, "reading.event_sequence", "A cone rolled from the court into a drain channel and stopped at a mesh cover.", "Which event happened last?", "The cone stopped at the mesh cover.", ["The cone rolled from the court.", "The drain moved onto the court.", "A player carried the cone away."]),
    _assessment_open(2, "reading.event_sequence", "A receipt slipped from a bag, rode upward on an escalator, and was collected at the landing.", "Retell the receipt's route in order.", "The receipt slipped from the bag, travelled up the escalator, and was collected at the landing.", "Sequences the start, movement, and ending accurately.", ["slipped from the bag", "travelled up the escalator", "collected at the landing"]),
    _assessment_choice(3, "reading.event_sequence", "The driver placed the returned ball beside the depot register before calling the coach.", "Which action happened first?", "The driver placed the ball beside the depot register.", ["The driver called the coach.", "The coach moved the register.", "The ball rolled under the cart."]),
    _assessment_open(4, "reading.paragraph_main_idea", "A class lost a banner in the wind. Pupils divided the playground into zones, found it against a fence, and repaired one torn corner.", "State the main idea in one sentence.", "The class organised a search, recovered its windblown banner, and repaired it.", "States the organised recovery rather than one minor detail.", ["organised a search", "recovered the banner", "repaired it"]),
    _assessment_choice(5, "reading.paragraph_main_idea", "A whistle travelled in a kit bag by mistake and returned when the coach checked the labels.", "Which sentence best states the main idea?", "A misplaced whistle was carried away and recovered through a label check.", ["The coach created labels for every kit bag.", "The team packed equipment before the match.", "A whistle is useful during sports practice."]),
    _assessment_choice(6, "reading.dialogue_attribution", "'I found the missing pump,' Saira told Dev. 'I will return it to the store,' he replied.", "Who will return the pump?", "Dev", ["Saira", "the storekeeper", "the coach"]),
    _assessment_open(7, "reading.dialogue_attribution", "'The cart number is 42,' Om told Ritu. 'Then I can call the depot,' she answered.", "Identify both speakers and explain Ritu's contribution.", "Om reports the number, and Ritu responds that she can use it to call the depot.", "Attributes both lines and explains how the second responds to the first.", ["Om reports the number", "Ritu responds", "call the depot"]),
    _assessment_open(8, "writing.reason_answer", "A cap has blown onto a parked taxi's roof rack. The taxi number is visible, but the driver is absent.", "What should the finder do next, and why is that action responsible?", "The finder should note the taxi number and inform a nearby guard because this creates a safe way to return the cap without touching another person's vehicle.", "States a responsible action and supports it with a relevant safety or ownership reason.", ["note the taxi number", "inform a guard", "safe way to return"]),
    _assessment_open(9, "reading.inference_reason", "A rider slows beside a parked bus while children wait behind it.", "Why does the rider most likely slow down? Use the hidden-view clue in your reason.", "The rider slows because the parked bus may hide children who are about to enter the road.", "Infers the safety risk and grounds it in the blocked view beside the bus.", ["parked bus may hide", "children enter the road", "blocked view"]),
    _assessment_open(10, "writing.reason_answer", "A labelled racket is found after practice, and the office has team lists.", "Explain the best return action with a reason.", "The racket should go to the office because its label and the team lists can identify the owner.", "Chooses a responsible action and supports it with the supplied clues.", ["go to the office", "label", "team lists"]),
    _assessment_open(11, "writing.dialogue", "A library map tears along its fold. Zoya tells the librarian, who asks her to place both pieces flat on the repair table.", "Write their two-turn exchange with clear attribution and punctuation.", "Zoya said, 'The library map has torn along its fold.' The librarian replied, 'Please place both pieces flat on the repair table.'", "Writes two responsive, attributed, and punctuated dialogue turns grounded in the new event.", ["Zoya said", "map has torn", "librarian replied", "repair table"]),
    _assessment_open(12, "writing.dialogue", "Words spoken by Mira: where did the blue ball go", "Write Mira's line as a clearly attributed question, then add a relevant reply from Ravi.", "Mira asked, 'Where did the blue ball go?' Ravi replied, 'It rolled behind the equipment shed.'", "Writes an attributed question and a logically responsive second turn.", ["Mira asked", "Where did the blue ball go?", "Ravi replied"], min_words=10),
    _assessment_choice(13, "reading.dialogue_attribution", "The guard asks the rider whether a helmet belongs to her.", "Which line clearly attributes that exact question to the guard?", "The guard asked the rider, 'Is this your helmet?'", ["The rider asked the guard, 'Is this your helmet?'", "The guard told the rider, 'This helmet is mine.'", "The guard asked the rider, 'Where did you park the scooter?'"]),
    _assessment_open(14, "reading.inference_reason", "A ball lies beyond a locked gate. A phone number is displayed and no owner is home.", "Infer the respectful next step and cite the clue.", "The players should call the displayed number and wait because the locked gate shows they need permission.", "Infers a respectful action and uses the displayed number or locked gate as evidence.", ["call the displayed number", "wait", "locked gate"]),
    _assessment_choice(15, "reading.word_meaning_context", "The old crate creaked as its wooden sides rubbed over each bump.", "What does creaked mean here?", "made a rough squeaking sound", ["became brightly coloured", "moved without any sound", "was locked with a key"]),
    _assessment_open(16, "reading.word_meaning_context", "The flag fluttered, rising and falling lightly in the breeze.", "Explain fluttered using the movement clue.", "Fluttered means moved lightly back and forth, shown by the flag rising and falling in the breeze.", "Defines the word and cites the movement clue.", ["moved lightly", "rising and falling", "breeze"]),
    _assessment_choice(17, "reading.word_meaning_context", "The mechanic inspected every cable before approving the scooter.", "Which action uses inspected with the same meaning?", "The nurse examined the bandage carefully for loose edges.", ["The nurse covered the bandage with a clean cloth.", "The nurse replaced the bandage immediately.", "The nurse ignored the bandage until evening."]),
    _assessment_open(18, "vocab.word_formation", "A metal rail beside a staircase supports a person's hand.", "Combine hand and rail to name it, then explain the compound's meaning.", "Handrail combines hand and rail and means a rail held by the hand for support.", "Forms the fresh compound and explains how both base words contribute to its meaning.", ["handrail", "hand and rail", "rail held by the hand", "support"]),
    _assessment_choice(19, "vocab.word_formation", "A path for people travelling on foot is called a ___.", "Which compound completes the meaning?", "footpath", ["footprint", "footrest", "footbridge"]),
    _assessment_choice(20, "grammar.connectors_because_and_but", "The rider stopped ___ the signal was red.", "Which connector gives the reason?", "because", ["but", "however", "and"]),
    _assessment_open(21, "grammar.connectors_because_and_but", "Facts: science club planned an outdoor test; wind became strong; members moved the equipment indoors.", "Connect all three facts using but and because or so to show their relationship.", "The science club planned an outdoor test, but the wind became strong, so the members moved the equipment indoors.", "Uses connectors to express the contrast and resulting action accurately in the new case.", ["planned an outdoor test", "but the wind became strong", "moved the equipment indoors"]),
    _assessment_choice(22, "grammar.adverbs", "Rehan usually practises after school, but today he arrived early.", "Which word tells how often Rehan practises?", "usually", ["today", "early", "after"]),
    _assessment_open(23, "grammar.adverbs", "The courier rarely arrives late. Yesterday, she waited patiently outside.", "Identify the frequency, time, and manner adverbs.", "Rarely shows frequency, yesterday shows time, and patiently shows manner.", "Correctly labels all three adverb roles.", ["Rarely shows frequency", "yesterday shows time", "patiently shows manner"]),
    _assessment_choice(24, "grammar.tense_usage", "The careful driver checked the loose mirror yesterday.", "Which word is the past-tense action?", "checked", ["careful", "driver", "loose"]),
    _assessment_choice(25, "grammar.tense_usage", "Last evening, the driver ___ the damaged strap.", "Which form matches the time clue?", "replaced", ["replace", "replaces", "replacing"]),
    _assessment_open(26, "grammar.sentence_order", "Jumbled parts: after assembly / the music teacher / stored / the drums / in the equipment room.", "Arrange all parts into one clear sentence.", "After assembly, the music teacher stored the drums in the equipment room.", "Orders time, subject, verb, object, and place naturally.", ["after assembly", "music teacher stored", "the drums", "equipment room"]),
    _assessment_open(27, "grammar.sentence_order", "Notes: yesterday; careful mechanic; tighten; loose bolt; before noon.", "Write one natural past-tense sentence from the notes.", "Yesterday, the careful mechanic tightened the loose bolt before noon.", "Builds a natural ordered sentence with the correct past-tense action.", ["careful mechanic tightened", "loose bolt", "before noon"]),
    _assessment_choice(28, "research.information_selection", "Fact packet: a class checked kit labels, contacted the bus depot, and recovered its missing kit. Source: class activity log.", "Which claim is supported by the packet?", "Label checks and a depot call helped the class recover its missing kit.", ["The class bought a new bus.", "The depot lost every kit.", "The labels were removed before the search."]),
    _assessment_open(29, "writing.summary_own_words", "A rainstorm scattered game cards. Teams searched assigned rows, checked numbers, and restored the full set.", "Write a concise own-words summary with problem, response, and result.", "Rain scattered the game cards, but an organised row-by-row search and number check recovered the complete set.", "Includes problem, organised response, and recovery in own words.", ["rain scattered", "organised search", "recovered the complete set"]),
    _assessment_open(30, "writing.summary_own_words", "Notes: sports day moved indoors; field flooded; schedule shortened; every team completed two activities.", "Summarise the change, response, and result in two or three own-word sentences.", "The class adapted sports day after the field flooded. It moved indoors and shortened the schedule, allowing every team to complete two activities.", "Summarises the problem, response, and result without adding unsupported details.", ["field flooded", "moved indoors", "shortened the schedule", "every team"]),
    _assessment_choice(31, "research.information_selection", "Packet: Leena Rao; goalkeeper; district training camp; fair-play award. Source: school bulletin.", "Which claim is supported by the packet?", "Leena Rao received a fair-play award.", ["Leena Rao won an international final.", "Leena Rao coaches the national team.", "Leena Rao invented a new game."]),
    _assessment_open(32, "research.information_selection", "Packet: Kabir Sen; para-badminton player; began at age eleven; won a state doubles medal in 2025; source: city youth report.", "Write a sourced two- or three-sentence profile using only supported facts.", "The city youth report profiles Kabir Sen as a para-badminton player who began at eleven. He won a state doubles medal in 2025.", "Selects accurate supplied facts, attributes the source, and avoids invention.", ["city youth report", "para-badminton player", "began at eleven", "state doubles medal"]),
]


STRANDS = [
    {
        "strand_id": "scooter-narrative-tracking",
        "skill_ids": [
            "reading.event_sequence",
            "reading.paragraph_main_idea",
            "reading.dialogue_attribution",
        ],
        "minimum_items": 8,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": [
            "scooter_event_sequence",
            "scooter_dialogue_and_speaker",
        ],
    },
    {
        "strand_id": "scooter-reason-and-dialogue",
        "skill_ids": [
            "reading.inference_reason",
            "writing.reason_answer",
            "writing.dialogue",
        ],
        "minimum_items": 5,
        "evidence_forms": ["constructed_response"],
        "remediation_level_ids": [
            "scooter_inference_and_fair_choice",
            "scooter_dialogue_and_speaker",
        ],
    },
    {
        "strand_id": "scooter-word-learning",
        "skill_ids": WORD_SKILLS,
        "minimum_items": 5,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["scooter_context_vocabulary"],
    },
    {
        "strand_id": "scooter-sentence-language",
        "skill_ids": [
            "grammar.connectors_because_and_but",
            "grammar.adverbs",
            "grammar.tense_usage",
            "grammar.sentence_order",
        ],
        "minimum_items": 8,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": [
            "scooter_connectors_and_adverbs",
            "scooter_precise_grammar",
        ],
    },
    {
        "strand_id": "scooter-synthesis-and-research",
        "skill_ids": [
            "writing.summary_own_words",
            "research.information_selection",
        ],
        "minimum_items": 4,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["scooter_summary_and_profile"],
    },
]


MANIFEST = {
    "schema_version": "school-class5-deep-manifest-v1",
    "chapter": {
        "chapter_id": CHAPTER_ID,
        "chapter_no": 2,
        "title": "Gone with the Scooter",
        "book_title": "Santoor",
        "unit_title": "Let's Have Fun",
        "source_url": SOURCE_URL,
        "source_note": (
            "NCERT structural alignment only. All teaching passages, prompts, "
            "examples, choices, rubrics, and answers are original Zidd content."
        ),
        "content_version": "2026-07-15.4",
        "certification_version": "2026-07-15.4",
        "authorship": {
            "zidd_authored_original": True,
            "textbook_body_or_questions_copied": False,
            "source_analysis_reference": (
                "/tmp/eesa102.txt structural exercise and modality matrix; "
                "no textbook body retained"
            ),
        },
    },
    "source_anchors": SOURCE_ANCHORS,
    "levels": [_level(spec) for spec in LEVEL_SPECS],
    "chapter_assessment": {
        "items_per_attempt": 16,
        "pass_score": 0.8,
        "max_attempts": 2,
        "bank_item_count": 32,
        "items": ASSESSMENT_ITEMS,
        "strands": STRANDS,
    },
}
