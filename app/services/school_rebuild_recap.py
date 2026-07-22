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
from app.services.school_rebuild_curriculum import (
    _open_answer_preflight_failure,
    accepted_answer_matches,
    decide_open_answer_evaluation,
)
from app.services.school_rebuild_language import localized_teaching_support


ENGINE_VERSION = "school-rebuild-recap-1"
RECAP_PASS_THRESHOLD = 1.0
REVISION_STEPS = ("revision_level_1", "revision_level_2", "revision_level_3")
RECAP_AUTHORED_STAGES = (
    "guided_check",
    "bridge",
    "masterclass",
    *REVISION_STEPS,
    "independent_check",
    "transfer_check",
)

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


def _deterministic_recap_check(
    source_item_id: str,
    source_class_no: int,
    passage: str,
    prompt: str,
    accepted_answers: tuple[str, ...],
    *,
    options: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "source_item_id": source_item_id,
        "source_class_no": source_class_no,
        "passage": passage,
        "prompt": prompt,
        "options": list(options),
        "accepted_answers": list(accepted_answers),
        "evaluation_mode": "deterministic",
        "rubric_ref": None,
    }


def _rubric_recap_check(
    source_item_id: str,
    source_class_no: int,
    passage: str,
    prompt: str,
    rubric_ref: str,
) -> dict[str, Any]:
    return {
        "source_item_id": source_item_id,
        "source_class_no": source_class_no,
        "passage": passage,
        "prompt": prompt,
        "options": [],
        "accepted_answers": [],
        "evaluation_mode": "strict_rubric",
        "rubric_ref": rubric_ref,
    }


RECAP_TRACK_CHECK_BANK: dict[str, dict[str, dict[str, Any]]] = {
    "english.c2.sentence_detail_place": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_guided",
            1,
            "The puppy naps inside the blue basket.",
            "Where does the puppy nap?",
            ("inside the blue basket",),
            options=("inside the blue basket", "under the table", "near the gate"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_bridge",
            1,
            "Maya puts her crayons in the yellow box after drawing.",
            "Which words tell where the crayons are?",
            ("in the yellow box",),
            options=("in the yellow box", "after drawing", "her crayons"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_masterclass",
            1,
            "The rabbit hides under the bench. Its carrot lies beside the gate.",
            "Where does the rabbit hide, not the carrot?",
            ("under the bench",),
            options=("under the bench", "beside the gate", "with the carrot"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_revision_1",
            1,
            "After lunch, Ali leaves his bottle near the classroom door.",
            "Where does Ali leave his bottle?",
            (
                "near the classroom door",
                "by the classroom door",
                "the classroom door",
                "near the door",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_revision_2",
            2,
            "The red scarf hangs between the two coats in the hall.",
            "What is on each side of the scarf?",
            ("the two coats",),
            options=("the two coats", "the hall doors", "the red scarf"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_revision_3",
            2,
            "Tara keeps the storybook on the top shelf, while the game stays in a drawer.",
            "Where does Tara keep the storybook?",
            ("on the top shelf",),
            options=("on the top shelf", "in a drawer", "beside the game"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_independent",
            2,
            "During art time, Omar sets the wet brushes beside the sink.",
            "Find the exact place where Omar sets the brushes.",
            ("beside the sink", "by the sink", "the sink"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c2_sentence_detail_place_transfer",
            2,
            "At the bus stop, Grandma waits beneath the striped umbrella.",
            "What is Grandma standing beneath while she waits?",
            ("the striped umbrella", "striped umbrella"),
        ),
    },
    "english.c2.sentence_detail_action": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_guided",
            1,
            "Nina feeds the ducks by the pond.",
            "Who feeds the ducks?",
            ("Nina",),
            options=("Nina", "the ducks", "the pond"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_bridge",
            1,
            "The baker mixes the dough while Sam watches.",
            "Which person mixes the dough?",
            ("the baker", "baker"),
            options=("the baker", "Sam", "the dough"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_masterclass",
            1,
            "Ira packs the bag. Her brother closes the door.",
            "Who closes the door after Ira packs the bag?",
            ("her brother", "Ira's brother", "brother"),
            options=("her brother", "Ira", "the bag"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_revision_1",
            1,
            "Before school, Papa ties Rohan's shoelace.",
            "Who ties Rohan's shoelace?",
            ("Papa",),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_revision_2",
            2,
            "Meena and Jo visit the garden. Jo waters the roses.",
            "Who waters the roses?",
            ("Jo",),
            options=("Jo", "Meena", "the garden"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_revision_3",
            2,
            "The coach blows the whistle, and the players begin to run.",
            "Who blows the whistle?",
            ("the coach", "coach"),
            options=("the coach", "the players", "the whistle"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_independent",
            2,
            "When the lights go out, Aarav finds a torch for everyone.",
            "Who finds a torch for everyone?",
            ("Aarav",),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c2_sentence_detail_action_transfer",
            2,
            "At the clinic, the nurse gives Ritu a clean bandage.",
            "Who gives Ritu the bandage?",
            ("the nurse", "nurse"),
        ),
    },
    "english.c2.context_word": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_context_word_guided",
            1,
            "The fluffy kitten feels soft when I stroke it.",
            "What does fluffy mean here?",
            ("covered with soft fur",),
            options=("covered with soft fur", "ready to bite", "wet from rain"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_context_word_bridge",
            1,
            "The path is narrow, so only one child can walk on it.",
            "What does narrow mean?",
            ("not wide",),
            options=("not wide", "very long", "full of stones"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_context_word_masterclass",
            1,
            "Ravi felt chilly and pulled on a sweater.",
            "Which clue shows that chilly means cold?",
            ("pulled on a sweater",),
            options=("pulled on a sweater", "Ravi felt", "a sweater"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c2_context_word_revision_1",
            1,
            "The mango is ripe. It is soft, sweet, and ready to eat.",
            "What does ripe mean in this passage?",
            ("ready to eat",),
            options=("ready to eat", "hard and green", "too high to reach"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c2_context_word_revision_2",
            2,
            "The puppy was eager; it jumped at the door when the walk began.",
            "What does eager mean here?",
            ("excited and ready",),
            options=("excited and ready", "tired and slow", "lost and afraid"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c2_context_word_revision_3",
            2,
            "Mira whispered because the baby was dozing in the cot.",
            "What does dozing mean?",
            ("sleeping lightly",),
            options=("sleeping lightly", "crying loudly", "drinking milk"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c2_context_word_independent",
            2,
            "The puddle vanished after the hot sun dried the road.",
            "Use the sentence to tell what vanished means.",
            ("disappeared", "went away"),
            options=("disappeared", "grew deeper", "became cold"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c2_context_word_transfer",
            2,
            "The old bridge is sturdy, so many people can cross it safely.",
            "What does sturdy mean in this sentence?",
            ("strong",),
            options=("strong", "new", "narrow"),
        ),
    },
    "english.c2.word_choice": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_word_choice_guided",
            1,
            "The room is dark. Please ___ the lamp.",
            "Which word tells what to do?",
            ("light",),
            options=("light", "eat", "fold"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_word_choice_bridge",
            1,
            "The baby is asleep, so we should speak ___.",
            "Choose the word that tells how to speak.",
            ("softly",),
            options=("softly", "outside", "purple"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_word_choice_masterclass",
            1,
            "Rina has two apples. She will ___ one with her friend.",
            "Which action word fits the whole sentence?",
            ("share",),
            options=("share", "sleep", "draw"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c2_word_choice_revision_1",
            1,
            "I cannot reach the shelf. It is too ___.",
            "Pick the word that explains why I cannot reach.",
            ("high",),
            options=("high", "kind", "empty"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c2_word_choice_revision_2",
            2,
            "The muddy shoes will make the clean floor ___.",
            "Choose the word that completes the result.",
            ("dirty",),
            options=("dirty", "sweet", "quiet"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c2_word_choice_revision_3",
            2,
            "Anu checked both bags but could not ___ her cap.",
            "Which word completes Anu's action?",
            ("find",),
            options=("find", "bake", "push"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c2_word_choice_independent",
            2,
            "Please ___ the door gently when you leave.",
            "Choose the action that makes sense at the door.",
            ("close",),
            options=("close", "peel", "count"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c2_word_choice_transfer",
            2,
            "The plant looks dry, so Veer will ___ it before school.",
            "Which word best completes the new sentence?",
            ("water",),
            options=("water", "wear", "carry"),
        ),
    },
    "english.c2.naming_words": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_naming_words_guided",
            1,
            "The puppy plays.",
            "Which word names an animal?",
            ("puppy",),
            options=("puppy", "plays", "the"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_naming_words_bridge",
            1,
            "Rosa visits the farm.",
            "Which word names a place?",
            ("farm",),
            options=("farm", "visits", "Rosa"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_naming_words_masterclass",
            1,
            "The cook carries a basket.",
            "Which two words name a person and a thing?",
            ("cook and basket",),
            options=("cook and basket", "carries and basket", "the and a"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c2_naming_words_revision_1",
            1,
            "A train stops at the station.",
            "Which naming word tells where the train stops?",
            ("station",),
            options=("station", "stops", "at"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c2_naming_words_revision_2",
            2,
            "The clever fox crossed the field.",
            "Which word names the animal?",
            ("fox",),
            options=("fox", "clever", "crossed", "field"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c2_naming_words_revision_3",
            2,
            "My aunt bought mangoes from the market.",
            "Which three words name a person, things, and a place?",
            ("aunt, mangoes, market",),
            options=(
                "aunt, mangoes, market",
                "bought, from, the",
                "my, bought, market",
            ),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c2_naming_words_independent",
            2,
            "Kiran placed the silver key beside the clock.",
            "Find the two words that name things.",
            ("key and clock",),
            options=("key and clock", "Kiran and silver", "placed and beside"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c2_naming_words_transfer",
            2,
            "During the picnic, families rested near the river.",
            "Which naming word gives a place in nature?",
            ("river",),
            options=("river", "rested", "families", "during"),
        ),
    },
    "english.c2.sentence_order": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_sentence_order_guided",
            1,
            "Words: cats / jump",
            "Put the words in sentence order.",
            ("Cats jump.", "cats jump"),
            options=("Cats jump.", "Jump cats.", "Cats."),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_sentence_order_bridge",
            1,
            "Words: eats / Meera / rice",
            "Build a sentence that names who eats.",
            ("Meera eats rice.", "Meera eats rice"),
            options=("Meera eats rice.", "Rice Meera eats.", "Eats rice Meera."),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_sentence_order_masterclass",
            1,
            "Words: blue / is / sky / the",
            "Choose the order that makes a clear statement.",
            ("The sky is blue.", "The sky is blue"),
            options=("The sky is blue.", "Blue the sky is.", "Is blue sky the."),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c2_sentence_order_revision_1",
            1,
            "Words: little / sleeps / baby / the",
            "Arrange all the words into one sentence.",
            ("The little baby sleeps.", "The little baby sleeps"),
            options=(
                "The little baby sleeps.",
                "Sleeps the baby little.",
                "Little the sleeps baby.",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c2_sentence_order_revision_2",
            2,
            "Words: after school / football / we / play",
            "Write the words as a sentence with the time last.",
            ("We play football after school.", "We play football after school"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c2_sentence_order_revision_3",
            2,
            "Words: the window / because / I / hot / opened / it was",
            "Order the parts to tell why the window opened.",
            (
                "I opened the window because it was hot.",
                "I opened the window because it was hot",
            ),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c2_sentence_order_independent",
            2,
            "Words: on the branch / two sparrows / quietly / sat",
            "Make one clear sentence using every part.",
            (
                "Two sparrows sat quietly on the branch.",
                "Two sparrows sat on the branch quietly.",
            ),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c2_sentence_order_transfer",
            2,
            "Words: before dinner / her homework / finished / Lata",
            "Build a new sentence that begins with Lata.",
            ("Lata finished her homework before dinner.",),
        ),
    },
    "english.c2.complete_sentence_action": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_complete_sentence_action_guided",
            1,
            "A boy kicks a ball across the field.",
            "Which sentence tells the boy's action?",
            ("The boy kicks the ball.",),
            options=("The boy kicks the ball.", "The blue ball.", "Across the field."),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_complete_sentence_action_bridge",
            1,
            "A hen pecks seeds near the fence.",
            "Choose the full sentence about what the hen does.",
            ("The hen pecks seeds.",),
            options=("The hen pecks seeds.", "The brown hen.", "Near the fence."),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_complete_sentence_action_masterclass",
            1,
            "Sumi uses a cloth to clean the table.",
            "Which answer has a person and a full action?",
            ("Sumi cleans the table.",),
            options=("Sumi cleans the table.", "A clean table.", "With a cloth."),
        ),
        "revision_level_1": _rubric_recap_check(
            "recap_c2_complete_sentence_action_revision_1",
            1,
            "A frog jumps from a rock into the pond.",
            "Write one full sentence about what the frog does.",
            "school.strict.complete_sentence.foundation.v1",
        ),
        "revision_level_2": _rubric_recap_check(
            "recap_c2_complete_sentence_action_revision_2",
            2,
            "Two children pull a red wagon up the path.",
            "Write a complete sentence that tells their action.",
            "school.strict.complete_sentence.class2.v1",
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c2_complete_sentence_action_revision_3",
            2,
            "A worker measures a wooden board before cutting it.",
            "In one sentence, tell what the worker is doing.",
            "school.strict.complete_sentence.class2.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c2_complete_sentence_action_independent",
            2,
            "Priya folds the clean towels and puts them in a basket.",
            "In one complete sentence, tell what Priya does.",
            "school.strict.complete_sentence.class2.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c2_complete_sentence_action_transfer",
            2,
            "At the market, a shopkeeper weighs tomatoes for a customer.",
            "Write one complete sentence about the shopkeeper's action.",
            "school.strict.complete_sentence.class2.v1",
        ),
    },
    "english.c2.complete_sentence_idea": {
        "guided_check": _deterministic_recap_check(
            "recap_c2_complete_sentence_idea_guided",
            1,
            "A rainbow appears after the rain.",
            "Which choice is one complete idea about the rainbow?",
            ("The rainbow appears after the rain.",),
            options=(
                "The rainbow appears after the rain.",
                "After the rain.",
                "A bright rainbow.",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c2_complete_sentence_idea_bridge",
            1,
            "Mohan's new shoes are wet from the puddle.",
            "Choose the sentence that gives a whole idea.",
            ("Mohan's shoes are wet.",),
            options=("Mohan's shoes are wet.", "His new shoes.", "From the puddle."),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c2_complete_sentence_idea_masterclass",
            1,
            "The class pet sleeps in a small cage.",
            "Which answer tells who and what is happening?",
            ("The class pet sleeps.",),
            options=("The class pet sleeps.", "In a small cage.", "The sleepy pet."),
        ),
        "revision_level_1": _rubric_recap_check(
            "recap_c2_complete_sentence_idea_revision_1",
            1,
            "The moon shines above the quiet houses.",
            "Write one full sentence about the moon.",
            "school.strict.complete_sentence.foundation.v1",
        ),
        "revision_level_2": _rubric_recap_check(
            "recap_c2_complete_sentence_idea_revision_2",
            2,
            "Our class planted three bean seeds in a pot.",
            "Write one complete idea about what the class did.",
            "school.strict.complete_sentence.class2.v1",
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c2_complete_sentence_idea_revision_3",
            2,
            "The picnic ended when dark clouds covered the sky.",
            "Write one complete sentence about why the picnic ended.",
            "school.strict.complete_sentence.class2.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c2_complete_sentence_idea_independent",
            2,
            "A lost puppy waits beside the guard's chair.",
            "Write one complete sentence about the puppy.",
            "school.strict.complete_sentence.class2.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c2_complete_sentence_idea_transfer",
            2,
            "The library closes early because workers are fixing a pipe.",
            "Write one complete sentence that explains why the library closes early.",
            "school.strict.complete_sentence.class2.v1",
        ),
    },
    "english.c3.sentence_detail": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_sentence_detail_guided",
            1,
            "A red cap rests on the chair.",
            "What rests on the chair?",
            ("a red cap", "red cap", "cap"),
            options=("a red cap", "a blue bag", "a chair"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_sentence_detail_bridge",
            1,
            "Neel keeps his lunch box under the desk.",
            "Which words tell where the lunch box is?",
            ("under the desk",),
            options=("under the desk", "his lunch box", "Neel keeps"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_sentence_detail_masterclass",
            2,
            "The brown goat eats leaves beside the fence, while the calf drinks water.",
            "What does the goat eat?",
            ("leaves",),
            options=("leaves", "water", "the fence"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_sentence_detail_revision_1",
            2,
            "At noon, Lila hangs her wet raincoat behind the classroom door.",
            "Where does Lila hang the raincoat?",
            ("behind the classroom door", "behind the door"),
            options=(
                "behind the classroom door",
                "at noon",
                "inside her school bag",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c3_sentence_detail_revision_2",
            3,
            "On Tuesday morning, Arjun carries two storybooks to the reading corner.",
            "How many storybooks does Arjun carry?",
            ("two", "2", "two storybooks"),
            options=("two", "three", "one"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c3_sentence_detail_revision_3",
            3,
            "The music lesson begins after lunch in Room 4, but dance practice starts before lunch.",
            "When does the music lesson begin?",
            ("after lunch",),
            options=("after lunch", "before lunch", "in Room 4"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c3_sentence_detail_independent",
            3,
            "Meera packed a silver spoon and a green cup for the picnic. She left the plate at home.",
            "Which two things did Meera pack?",
            (
                "a silver spoon and a green cup",
                "the silver spoon and the green cup",
                "a spoon and a cup",
                "spoon and cup",
            ),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c3_sentence_detail_transfer",
            3,
            "The library van stops near the post office every Friday at three o'clock.",
            "Where and when does the library van stop?",
            (
                "near the post office every Friday at three o'clock",
                "near the post office at three o'clock every Friday",
                "near the post office on Friday at three o'clock",
            ),
        ),
    },
    "english.c3.main_idea": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_main_idea_guided",
            1,
            "Ravi gives the calf grass. He fills its water bowl.",
            "What are both sentences mostly about?",
            ("Ravi caring for the calf",),
            options=(
                "Ravi caring for the calf",
                "Ravi washing a bowl",
                "The calf running away",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_main_idea_bridge",
            1,
            "Mina sweeps the room. She puts the toys away.",
            "Which choice tells what Mina is doing?",
            ("Mina tidies the room",),
            options=(
                "Mina tidies the room",
                "Mina buys new toys",
                "Mina leaves the room",
            ),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_main_idea_masterclass",
            2,
            "Bees visit flowers, collect nectar, and carry it back to their hive.",
            "What is the whole passage mostly about?",
            ("bees gathering food",),
            options=(
                "bees gathering food",
                "flowers changing colour",
                "a hive falling down",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_main_idea_revision_1",
            2,
            "Jai washed his bicycle, dried the seat, and checked both tyres before riding.",
            "Which idea links all three bicycle jobs?",
            ("Jai prepared his bicycle for a ride",),
            options=(
                "Jai prepared his bicycle for a ride",
                "Jai bought a new bicycle",
                "Jai lost one tyre",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c3_main_idea_revision_2",
            3,
            "Students loosened the soil, planted marigolds, and watered the new garden bed.",
            "What main idea connects these actions?",
            ("students planting a garden bed",),
            options=(
                "students planting a garden bed",
                "students cleaning a classroom",
                "students picking wild flowers",
            ),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c3_main_idea_revision_3",
            3,
            "Two sparrows carried grass to a branch, tucked in twigs, and shaped a small nest.",
            "Which choice best tells what the sparrows are doing?",
            ("the sparrows are building a nest",),
            options=(
                "the sparrows are building a nest",
                "the sparrows are eating seeds",
                "the sparrows are leaving the tree",
            ),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c3_main_idea_independent",
            3,
            "Families brought storybooks to the park. Volunteers read aloud, and children exchanged books when each story ended.",
            "What is the passage mainly about?",
            ("a reading day in the park",),
            options=(
                "a reading day in the park",
                "a race through the park",
                "families selling food",
            ),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c3_main_idea_transfer",
            3,
            "Neighbours fixed the swings, painted the slide, and cleared stones from the play area before children returned.",
            "Which main idea covers the whole passage?",
            ("neighbours repaired the play area",),
            options=(
                "neighbours repaired the play area",
                "children painted pictures",
                "stones covered every swing",
            ),
        ),
    },
    "english.c3.reason_inference": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_reason_inference_guided",
            1,
            "Sia closes the window because rain is blowing into the room.",
            "Why does Sia close the window?",
            ("rain is blowing into the room", "because rain is blowing in"),
            options=(
                "rain is blowing into the room",
                "the room is too bright",
                "she wants to hear the rain",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_reason_inference_bridge",
            1,
            "Arun sees spilled water on the floor, so he wipes it with a cloth.",
            "What made Arun wipe the floor?",
            ("spilled water on the floor", "the water was spilled"),
            options=(
                "spilled water on the floor",
                "a cloth was missing",
                "the floor was already dry",
            ),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_reason_inference_masterclass",
            2,
            "Cold wind enters the playground. Neha rubs her arms and asks for her sweater.",
            "Why does Neha ask for her sweater?",
            ("she feels cold", "because she is cold", "the wind is cold"),
            options=("she feels cold", "she feels hungry", "she wants to swim"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_reason_inference_revision_1",
            2,
            "Thunder boomed above the house. The puppy ran under the bed and stayed there.",
            "What caused the puppy to hide?",
            ("the thunder", "thunder", "the loud thunder"),
            options=("the thunder", "the bed", "the quiet room"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c3_reason_inference_revision_2",
            3,
            "The afternoon sun heated the bench. Omar moved beneath a tree before opening his lunch box.",
            "Why did Omar move beneath the tree?",
            ("to get shade", "the bench was hot", "to move out of the hot sun"),
            options=("to get shade", "to climb the tree", "to find his lunch box"),
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c3_reason_inference_revision_3",
            3,
            "A small nest rested beside the path. Rohan read a sign asking walkers to stay back, so he chose another way.",
            "Why did Rohan take another path? Use one clue from the text.",
            "school.strict.reason_from_text.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c3_reason_inference_independent",
            3,
            "The weather report promised a very hot afternoon. Before the hike, Maya packed an extra water bottle.",
            "Why did Maya pack extra water? Support your answer with the forecast clue.",
            "school.strict.reason_from_text.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c3_reason_inference_transfer",
            3,
            "Dark clouds gathered above the courtyard, and cool drops began to fall. The team carried the display books inside.",
            "Why did the team carry the books inside? Explain with one passage clue.",
            "school.strict.reason_from_text.v1",
        ),
    },
    "english.c3.context_word": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_context_word_guided",
            1,
            "The smooth pebble had no rough edges.",
            "What does smooth mean here?",
            ("not rough",),
            options=("not rough", "very heavy", "full of holes"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_context_word_bridge",
            1,
            "Ritu wore a woollen cap because the morning was chilly and cold.",
            "Which word tells what chilly means?",
            ("cold",),
            options=("cold", "woollen", "morning"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_context_word_masterclass",
            2,
            "Handle the fragile cup gently because it can crack easily.",
            "What does fragile mean in this sentence?",
            ("easy to break",),
            options=("easy to break", "safe to drop", "made of wood"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_context_word_revision_1",
            2,
            "Kunal was eager to begin; he reached the game early and waited by the gate.",
            "What does eager mean here?",
            ("excited and ready",),
            options=("excited and ready", "angry and loud", "too tired to start"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c3_context_word_revision_2",
            3,
            "After the long ride, Pihu felt drowsy and kept yawning in her seat.",
            "Which meaning fits drowsy?",
            ("sleepy",),
            options=("sleepy", "hungry", "cheerful", "lost"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c3_context_word_revision_3",
            3,
            "The ancient well was built hundreds of years ago and still stood in the village.",
            "What does ancient mean in the passage?",
            ("very old",),
            options=("very old", "newly built", "full of water", "hard to find"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c3_context_word_independent",
            3,
            "The rabbit vanished behind the bushes. We looked again, but it was gone.",
            "What does vanished mean here?",
            ("disappeared",),
            options=("disappeared", "grew larger", "made a sound", "fell asleep"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c3_context_word_transfer",
            3,
            "Veer was reluctant to jump into the pool. He stayed at the edge and said he was not ready.",
            "Which meaning best fits reluctant?",
            ("not willing",),
            options=("not willing", "ready at once", "unable to swim", "very noisy"),
        ),
    },
    "english.c3.word_roles": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_word_roles_guided",
            1,
            "The baker smiles at us.",
            "Which word names a person?",
            ("baker",),
            options=("baker", "smiles", "at"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_word_roles_bridge",
            1,
            "Birds flap their wings.",
            "Which word shows an action?",
            ("flap",),
            options=("flap", "birds", "wings"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_word_roles_masterclass",
            2,
            "The soft pillow fell onto the floor.",
            "Which word describes the pillow?",
            ("soft",),
            options=("soft", "pillow", "fell"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_word_roles_revision_1",
            2,
            "A noisy bus stopped outside the school gate.",
            "What job does noisy do in this sentence?",
            ("describes the bus",),
            options=("describes the bus", "names the gate", "shows an action"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c3_word_roles_revision_2",
            3,
            "The young fox chased a rabbit across the field.",
            "Which word is the action in the sentence?",
            ("chased",),
            options=("chased", "young", "fox", "field"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c3_word_roles_revision_3",
            3,
            "We water the plants after school.",
            "What job does water do here?",
            ("shows an action",),
            options=("shows an action", "names a thing", "describes the plants"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c3_word_roles_independent",
            3,
            "Dad filled the glass with fresh water.",
            "What job does water do in this sentence?",
            ("names a thing",),
            options=("names a thing", "shows an action", "describes the glass"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c3_word_roles_transfer",
            3,
            "The clean plates shine on the shelf.",
            "What job does clean do in the new sentence?",
            ("describes the plates",),
            options=("describes the plates", "shows an action", "names the shelf"),
        ),
    },
    "english.c3.past_tense": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_past_tense_guided",
            1,
            "Today I clap. Yesterday I clapped.",
            "Which word shows the action from yesterday?",
            ("clapped",),
            options=("clapped", "clap", "today"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_past_tense_bridge",
            1,
            "Last night, the baby cried before falling asleep.",
            "Which action already happened?",
            ("cried",),
            options=("cried", "baby", "asleep"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_past_tense_masterclass",
            2,
            "Asha goes to music class today. She went to art class yesterday.",
            "Which word is the past form of go?",
            ("went",),
            options=("went", "goes", "today"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_past_tense_revision_1",
            2,
            "Last evening, we ___ carrom with our neighbours.",
            "Choose the verb that fits the past time clue.",
            ("played",),
            options=("played", "play", "will play"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c3_past_tense_revision_2",
            3,
            "This morning, Imran ___ toast before school.",
            "Which verb correctly completes the sentence?",
            ("ate",),
            options=("ate", "eats", "will eat"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c3_past_tense_revision_3",
            3,
            "The bell rang, and the pupils ___ the room quietly.",
            "Choose the past-tense action that matches rang.",
            ("left",),
            options=("left", "leave", "will leave"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c3_past_tense_independent",
            3,
            "Yesterday, Mina ___ a letter to her cousin.",
            "Use the past form of write to fill the blank.",
            ("wrote",),
            options=("wrote", "writes", "will write"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c3_past_tense_transfer",
            3,
            "Last Saturday, Uncle Ravi ___ fresh fruit from the market.",
            "Which past form of bring belongs in the sentence?",
            ("brought",),
            options=("brought", "brings", "will bring"),
        ),
    },
    "english.c3.complete_sentence": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_complete_sentence_guided",
            1,
            "A kitten sleeps in a basket.",
            "Which choice is a complete sentence?",
            ("The kitten sleeps in a basket.",),
            options=(
                "The kitten sleeps in a basket.",
                "In a basket.",
                "The sleepy kitten.",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_complete_sentence_bridge",
            1,
            "Asha waves from the bus.",
            "Which answer tells who and the full action?",
            ("Asha waves from the bus.",),
            options=("Asha waves from the bus.", "From the bus.", "Asha on the bus."),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_complete_sentence_masterclass",
            2,
            "The boys build a sandcastle near the water.",
            "Which sentence includes the action and the place?",
            ("The boys build a sandcastle near the water.",),
            options=(
                "The boys build a sandcastle near the water.",
                "The boys near the water.",
                "A large sandcastle.",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_complete_sentence_revision_1",
            2,
            "Words: the baby / after lunch / slept",
            "Put all the parts into one complete sentence.",
            ("The baby slept after lunch.", "The baby slept after lunch"),
            options=(
                "The baby slept after lunch.",
                "After lunch the baby.",
                "Slept the after baby lunch.",
            ),
        ),
        "revision_level_2": _rubric_recap_check(
            "recap_c3_complete_sentence_revision_2",
            3,
            "Two girls share an umbrella as they walk home in the rain.",
            "Write one complete sentence about what the girls are doing.",
            "school.strict.complete_sentence.class3.v1",
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c3_complete_sentence_revision_3",
            3,
            "A mechanic checks the bicycle brakes before the child rides away.",
            "Write one complete sentence about what the mechanic does.",
            "school.strict.complete_sentence.class3.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c3_complete_sentence_independent",
            3,
            "The class carries seedlings outside and plants them beside the wall.",
            "Write one complete sentence that includes the action and place.",
            "school.strict.complete_sentence.class3.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c3_complete_sentence_transfer",
            3,
            "When the lights go out, Dev finds a torch in the cupboard.",
            "Write one complete sentence explaining what Dev does when the lights go out.",
            "school.strict.complete_sentence.class3.v1",
        ),
    },
    "english.c3.short_answer": {
        "guided_check": _deterministic_recap_check(
            "recap_c3_short_answer_guided",
            1,
            "Nia keeps her red scarf on the bedroom hook.",
            "Which short answer tells where the scarf is?",
            ("It is on the bedroom hook.",),
            options=(
                "It is on the bedroom hook.",
                "It is red.",
                "Nia has a scarf.",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c3_short_answer_bridge",
            1,
            "Before school, Sam sprinkles food into the fish tank.",
            "Which answer tells when Sam feeds the fish?",
            ("He feeds them before school.",),
            options=(
                "He feeds them before school.",
                "He feeds the fish tank.",
                "The food is in the tank.",
            ),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c3_short_answer_masterclass",
            2,
            "The class made cheerful cards. Iqbal carried the cards to the health clinic.",
            "Who carried the cards, and where?",
            ("Iqbal carried them to the health clinic.",),
            options=(
                "Iqbal carried them to the health clinic.",
                "The class went to a shop.",
                "The clinic made the cards.",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c3_short_answer_revision_1",
            2,
            "Mira wore boots because the lane was muddy after the rain.",
            "Which answer clearly explains why Mira wore boots?",
            ("She wore boots because the lane was muddy.",),
            options=(
                "She wore boots because the lane was muddy.",
                "She wore boots after the lane.",
                "The rain wore muddy boots.",
            ),
        ),
        "revision_level_2": _rubric_recap_check(
            "recap_c3_short_answer_revision_2",
            3,
            "After the match, Zoya returned the borrowed bat to her coach and thanked her.",
            "What two things did Zoya do? Answer in one or two sentences.",
            "school.strict.short_answer.v1",
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c3_short_answer_revision_3",
            3,
            "The library closes at five. Rohan arrived at 4:45 and chose one book quickly.",
            "Why did Rohan choose quickly? Include the time detail in your answer.",
            "school.strict.short_answer.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c3_short_answer_independent",
            3,
            "Asha noticed a tap dripping. She turned it off and told her teacher about the leak.",
            "State the problem and tell both things Asha did in one or two sentences.",
            "school.strict.short_answer.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c3_short_answer_transfer",
            3,
            "During a trip, the bus stopped. The driver found a loose tyre bolt, tightened it, and continued the journey.",
            "Why did the bus stop, and how did the driver solve the problem?",
            "school.strict.short_answer.v1",
        ),
    },
    "english.c4.sentence_detail": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_sentence_detail_guided",
            2,
            "Mina keeps her yellow umbrella beside the front door.",
            "Where does Mina keep her umbrella?",
            ("beside the front door",),
            options=("beside the front door", "under her bed", "near the bus"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_sentence_detail_bridge",
            2,
            "The fruit seller opens his cart at seven each morning.",
            "When does the fruit seller open his cart?",
            ("at seven each morning", "at seven", "seven each morning"),
            options=("at seven each morning", "after lunch", "on Sunday night"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_sentence_detail_masterclass",
            3,
            "Tara placed two glass jars on the top shelf before the guests arrived.",
            "What did Tara place, and where?",
            ("two glass jars on the top shelf",),
            options=(
                "two glass jars on the top shelf",
                "two guests near the shelf",
                "one jar under the table",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_sentence_detail_revision_1",
            3,
            "On Thursday, the science club meets in the library after lunch.",
            "Where and when does the science club meet?",
            ("in the library after lunch",),
            options=(
                "in the library after lunch",
                "in the lab before lunch",
                "outside on Friday",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c4_sentence_detail_revision_2",
            4,
            "Ravi carried a blue toolkit from the store room to the garden at noon.",
            "Which details tell what Ravi carried and where he took it?",
            ("a blue toolkit to the garden",),
            options=(
                "a blue toolkit to the garden",
                "a garden to the store room",
                "a lunch box to the gate",
            ),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c4_sentence_detail_revision_3",
            4,
            "The red bus leaves Gate 2 at 8:15, while the green bus leaves Gate 4 at 8:30.",
            "Which gate and time belong to the green bus?",
            ("Gate 4 at 8:30", "gate 4 and 8:30"),
            options=("Gate 4 at 8:30", "Gate 2 at 8:15", "Gate 4 at 8:15"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c4_sentence_detail_independent",
            4,
            "Before assembly, Fatima pinned the music notice above the drinking-water tap.",
            "What did Fatima pin, and where did she pin it?",
            ("the music notice above the drinking-water tap",),
            options=(
                "the music notice above the drinking-water tap",
                "the assembly list below the window",
                "the water tap beside the notice",
            ),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c4_sentence_detail_transfer",
            4,
            "The health van visits Rampur School on the first Monday of each month and parks beside the office.",
            "When and where does the health van visit?",
            ("on the first Monday of each month beside the office",),
            options=(
                "on the first Monday of each month beside the office",
                "every Friday behind the library",
                "on the last Monday near the gate",
            ),
        ),
    },
    "english.c4.main_idea": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_main_idea_guided",
            2,
            "Kunal fills the bird bowl. He scatters grain beside it.",
            "What are both sentences mostly about?",
            ("Kunal feeding the birds",),
            options=("Kunal feeding the birds", "Kunal washing a bowl", "Birds flying away"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_main_idea_bridge",
            2,
            "Nisha folds the blankets, arranges the pillows, and sweeps the floor.",
            "Which choice covers all of Nisha's actions?",
            ("Nisha tidies the room",),
            options=("Nisha tidies the room", "Nisha buys a blanket", "Nisha leaves home"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_main_idea_masterclass",
            3,
            "Ants carried crumbs through a crack, stored them underground, and returned for more food.",
            "What is the passage mainly about?",
            ("ants collecting and storing food",),
            options=(
                "ants collecting and storing food",
                "ants building a tall tree",
                "crumbs growing underground",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_main_idea_revision_1",
            3,
            "The team checked the ropes, packed drinking water, and studied the trail map before leaving.",
            "Which idea connects all three actions?",
            ("the team prepared for a walk",),
            options=(
                "the team prepared for a walk",
                "the team won a race",
                "the team drew a new map",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c4_main_idea_revision_2",
            4,
            "Residents sorted paper and plastic, placed labelled bins near shops, and taught children how to use them.",
            "What main idea joins these details?",
            ("residents improved waste sorting",),
            options=(
                "residents improved waste sorting",
                "residents opened new shops",
                "children made paper toys",
            ),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c4_main_idea_revision_3",
            4,
            "A gardener loosened dry soil, mixed in compost, planted spinach seeds, and watered each row.",
            "Which sentence best states the main idea?",
            ("the gardener planted a spinach bed",),
            options=(
                "the gardener planted a spinach bed",
                "the gardener sold vegetables",
                "rain flooded the garden",
            ),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c4_main_idea_independent",
            4,
            "Students collected old newspapers, rolled them into pencils, and sold the pencils to fund new library books.",
            "What is this passage mainly about?",
            ("students reused paper to support the library",),
            options=(
                "students reused paper to support the library",
                "students closed the library",
                "students delivered daily newspapers",
            ),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c4_main_idea_transfer",
            4,
            "Farmers dug shallow trenches, covered the soil with leaves, and saved rainwater in a small pond for dry weeks.",
            "Which main idea covers the whole passage?",
            ("farmers saved water for dry weather",),
            options=(
                "farmers saved water for dry weather",
                "farmers removed every leaf",
                "farmers built a playground",
            ),
        ),
    },
    "english.c4.reason_inference": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_reason_inference_guided",
            2,
            "Aman carried a closed umbrella. The road was dry and the sun was bright.",
            "Why was Aman's umbrella probably closed?",
            ("it was not raining",),
            options=("it was not raining", "the road was flooded", "the umbrella was a kite"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_reason_inference_bridge",
            2,
            "The puppy scratched at the door and looked at its empty water bowl.",
            "Which clue best shows that the puppy may be thirsty?",
            ("its empty water bowl",),
            options=("its empty water bowl", "the closed door", "its soft tail"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_reason_inference_masterclass",
            3,
            "Sana whispered and pointed toward the nest while the parent bird fed its chicks.",
            "Why did Sana probably whisper?",
            ("she did not want to disturb the birds",),
            options=(
                "she did not want to disturb the birds",
                "she wanted the chicks to fly away",
                "she had forgotten how to speak",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_reason_inference_revision_1",
            3,
            "The shopkeeper moved the fruit baskets indoors when dark clouds gathered and the wind grew strong.",
            "What was the shopkeeper probably expecting?",
            ("rain or a storm", "rain", "a storm"),
            options=("rain or a storm", "a sunny afternoon", "more fruit to grow"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c4_reason_inference_revision_2",
            4,
            "The classroom windows were open, loose papers blew across desks, and Iqbal placed a stone on his notebook.",
            "Which detail explains why Iqbal used the stone?",
            ("loose papers blew across desks",),
            options=(
                "loose papers blew across desks",
                "the windows had glass",
                "the notebook had pages",
            ),
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c4_reason_inference_revision_3",
            4,
            "Mira found wet paw marks from the back door to the sofa, and the dog hid behind a chair.",
            "What probably happened? Explain with one clue from the passage.",
            "school.strict.inference.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c4_reason_inference_independent",
            4,
            "The school garden gate stood open. Fresh hoof marks crossed the beds, and several bean plants were chewed.",
            "What probably entered the garden? Support your answer with evidence.",
            "school.strict.inference.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c4_reason_inference_transfer",
            4,
            "When the train arrived, Ritu checked the coach number twice and held her ticket where she could see it.",
            "How was Ritu probably feeling, and what detail supports your idea?",
            "school.strict.inference.v1",
        ),
    },
    "english.c4.context_word": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_context_word_guided",
            2,
            "The kitten was timid, so it hid when the visitors entered.",
            "What does timid mean here?",
            ("shy",),
            options=("shy", "noisy", "hungry", "striped"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_context_word_bridge",
            2,
            "The path was narrow; only one child could walk on it at a time.",
            "Which clue helps explain narrow?",
            ("only one child could walk on it at a time",),
            options=(
                "only one child could walk on it at a time",
                "the path was outdoors",
                "children wore shoes",
            ),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_context_word_masterclass",
            3,
            "The thirsty travellers were relieved when they finally saw a well.",
            "What does relieved mean in this sentence?",
            ("glad that a worry ended",),
            options=("glad that a worry ended", "angry about the road", "ready to sleep"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_context_word_revision_1",
            3,
            "The glass bowl was fragile, so Neeraj carried it with both hands.",
            "What does fragile mean?",
            ("easy to break",),
            options=("easy to break", "very heavy", "full of water", "brightly coloured"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c4_context_word_revision_2",
            4,
            "The crowd began to disperse; people left the square in different directions.",
            "Which meaning fits disperse?",
            ("spread out and leave",),
            options=("spread out and leave", "stand closer together", "sing loudly", "wait silently"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c4_context_word_revision_3",
            4,
            "Unlike the noisy market, the reading room was tranquil and still.",
            "What does tranquil mean here?",
            ("calm and quiet",),
            options=("calm and quiet", "crowded and loud", "bright and hot", "closed and dark"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c4_context_word_independent",
            4,
            "The team was reluctant to cross the shaky bridge, but the guide showed them it was safe.",
            "What does reluctant most nearly mean?",
            ("not willing or unsure",),
            options=("not willing or unsure", "eager to begin", "unable to see", "ready to celebrate"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c4_context_word_transfer",
            4,
            "Water became scarce after months without rain, so each family received only two buckets a day.",
            "Which meaning of scarce fits the passage?",
            ("hard to find or not enough",),
            options=("hard to find or not enough", "clean and cold", "free for everyone", "flowing very fast"),
        ),
    },
    "english.c4.connectors": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_connectors_guided",
            2,
            "Rina wore a sweater ___ the morning was cold.",
            "Which word gives the reason?",
            ("because",),
            options=("because", "but", "and"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_connectors_bridge",
            2,
            "The box looked heavy, ___ it was empty.",
            "Which word shows the surprise or contrast?",
            ("but",),
            options=("but", "because", "and"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_connectors_masterclass",
            3,
            "Imran packed bread ___ fruit for the journey.",
            "Which connector adds one item to another?",
            ("and",),
            options=("and", "but", "because"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_connectors_revision_1",
            3,
            "The match continued ___ light rain was falling.",
            "Choose the connector that shows contrast.",
            ("although",),
            options=("although", "because", "so"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c4_connectors_revision_2",
            4,
            "The stream was rising, ___ the hikers moved to higher ground.",
            "Which connector shows the result?",
            ("so",),
            options=("so", "although", "and"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c4_connectors_revision_3",
            4,
            "Nina practised daily ___ she wanted to play the song smoothly.",
            "Which connector best links the action to its reason?",
            ("because",),
            options=("because", "but", "although"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c4_connectors_independent",
            4,
            "The road was muddy, ___ the delivery van reached the village on time.",
            "Choose the connector that makes the meaning clear.",
            ("but",),
            options=("but", "because", "so"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c4_connectors_transfer",
            4,
            "The solar lamp charged all day, ___ it shone through the night.",
            "Which connector shows what happened as a result?",
            ("so",),
            options=("so", "but", "although"),
        ),
    },
    "english.c4.tense": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_tense_guided",
            2,
            "Yesterday, Lata ___ a letter to her cousin.",
            "Which verb matches yesterday?",
            ("wrote",),
            options=("wrote", "writes", "will write"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_tense_bridge",
            2,
            "Every morning, the milkman ___ at six.",
            "Which verb matches every morning?",
            ("arrives",),
            options=("arrives", "arrived", "will arrive"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_tense_masterclass",
            3,
            "Next week, our class ___ the museum.",
            "Choose the verb phrase for a future plan.",
            ("will visit",),
            options=("will visit", "visited", "visits yesterday"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_tense_revision_1",
            3,
            "While the teacher spoke, the students ___ notes.",
            "Which verb shows an action happening then?",
            ("were taking",),
            options=("were taking", "will take", "take tomorrow"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c4_tense_revision_2",
            4,
            "By the time the bell rang, Ali ___ his drawing.",
            "Which verb phrase shows the drawing was already finished?",
            ("had completed",),
            options=("had completed", "will complete", "is completing tomorrow"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c4_tense_revision_3",
            4,
            "Right now, workers ___ the broken footpath.",
            "Which verb phrase matches right now?",
            ("are repairing",),
            options=("are repairing", "repaired last year", "will repair next month"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c4_tense_independent",
            4,
            "Last night the power failed, so we ___ candles.",
            "Choose the correct past-tense verb.",
            ("lit",),
            options=("lit", "light", "will light"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c4_tense_transfer",
            4,
            "When the rains begin next month, farmers ___ rice seedlings.",
            "Which verb phrase fits the future time clue?",
            ("will plant",),
            options=("will plant", "planted yesterday", "are planting last year"),
        ),
    },
    "english.c4.summary": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_summary_guided",
            2,
            "A pot fell and spilled soil. Jay swept the floor and put the plant into a new pot.",
            "Which sentence keeps the problem and solution?",
            ("A fallen pot made a mess, and Jay cleaned it and replanted the plant.",),
            options=(
                "A fallen pot made a mess, and Jay cleaned it and replanted the plant.",
                "Jay owns a broom and a flower pot.",
                "The floor was inside a room.",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_summary_bridge",
            2,
            "A kite caught in a tree. Roshni used a long stick to bring it down safely.",
            "Which detail belongs in a short retelling?",
            ("Roshni safely freed the kite from the tree.",),
            options=(
                "Roshni safely freed the kite from the tree.",
                "The stick was longer than her shoe.",
                "Trees have many green leaves.",
            ),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_summary_masterclass",
            3,
            "Heavy rain filled the playground. Staff moved games into the hall and marked the wet area with rope.",
            "Which choice tells the main event without small details?",
            ("Rain flooded the playground, so staff moved games indoors and closed the wet area.",),
            options=(
                "Rain flooded the playground, so staff moved games indoors and closed the wet area.",
                "The hall had a floor and some rope.",
                "Staff watched rain from a window.",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_summary_revision_1",
            3,
            "A library shelf broke. Volunteers repaired it, sorted the books, and returned them by subject.",
            "Which one-sentence retelling includes the central event and response?",
            ("Volunteers repaired a broken shelf and organised the books again.",),
            options=(
                "Volunteers repaired a broken shelf and organised the books again.",
                "The library owns books on many subjects.",
                "A volunteer carried one red book.",
            ),
        ),
        "revision_level_2": _rubric_recap_check(
            "recap_c4_summary_revision_2",
            4,
            "The village pond was choked with weeds. Residents cleared the weeds, added bins nearby, and agreed to clean the bank each month.",
            "Retell the problem and the residents' response in one sentence.",
            "school.strict.summary.v1",
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c4_summary_revision_3",
            4,
            "A storm damaged the school roof. Classes moved to the community hall while workers replaced the broken sheets.",
            "Summarize what happened and how the school responded.",
            "school.strict.summary.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c4_summary_independent",
            4,
            "Many children could not reach the distant library. A volunteer began carrying a box of books to each neighbourhood every Saturday.",
            "Write a short summary of the need and the solution in your own words.",
            "school.strict.summary.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c4_summary_transfer",
            4,
            "Farmers lost vegetables when monkeys entered open fields. They planted fruit trees at the forest edge and used strong nets around crops.",
            "Summarize the problem and both actions without copying the passage.",
            "school.strict.summary.v1",
        ),
    },
    "english.c4.reason_answer": {
        "guided_check": _deterministic_recap_check(
            "recap_c4_reason_answer_guided",
            2,
            "The floor was wet, so Jiya walked slowly.",
            "Which answer clearly tells why Jiya walked slowly?",
            ("Jiya walked slowly because the floor was wet.",),
            options=(
                "Jiya walked slowly because the floor was wet.",
                "Jiya walked the wet floor.",
                "The floor walked slowly.",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c4_reason_answer_bridge",
            2,
            "Dev closed the window because dust was blowing inside.",
            "Which words give Dev's reason?",
            ("because dust was blowing inside", "dust was blowing inside"),
            options=("because dust was blowing inside", "Dev closed", "the window"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c4_reason_answer_masterclass",
            3,
            "The seedlings bent in the strong wind, so Mala tied them to small sticks.",
            "Which answer links Mala's action to the passage clue?",
            ("Mala tied the seedlings because the strong wind bent them.",),
            options=(
                "Mala tied the seedlings because the strong wind bent them.",
                "Mala tied strong wind to a stick.",
                "The sticks grew into seedlings.",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c4_reason_answer_revision_1",
            3,
            "Arun carried an extra bottle because the walk would be long and hot.",
            "Which response answers why Arun carried extra water?",
            ("He carried extra water because the walk would be long and hot.",),
            options=(
                "He carried extra water because the walk would be long and hot.",
                "He carried a long and hot walk.",
                "The bottle walked with Arun.",
            ),
        ),
        "revision_level_2": _rubric_recap_check(
            "recap_c4_reason_answer_revision_2",
            4,
            "The class moved its paper models away from the window when rain began to blow inside.",
            "Why did the class move the models? Answer with a clear reason.",
            "school.strict.reason_answer.v1",
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c4_reason_answer_revision_3",
            4,
            "The doctor asked Rohan to rest because his ankle was swollen after the game.",
            "Why was Rohan told to rest? Use the important detail in your answer.",
            "school.strict.reason_answer.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c4_reason_answer_independent",
            4,
            "The town planted trees beside the road after summer temperatures rose and walkers had no shade.",
            "Why did the town plant roadside trees? Give a complete reason.",
            "school.strict.reason_answer.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c4_reason_answer_transfer",
            4,
            "The coach shortened practice when lightning flashed beyond the field and thunder followed.",
            "Why did the coach shorten practice? Support your answer with the passage.",
            "school.strict.reason_answer.v1",
        ),
    },
    "english.c5.sentence_detail": {
        "guided_check": _deterministic_recap_check(
            "recap_c5_sentence_detail_guided",
            4,
            "The art club meets in Room 6 on Wednesday afternoon to finish its mural.",
            "Where and when does the art club meet?",
            (
                "in Room 6 on Wednesday afternoon",
                "Room 6 on Wednesday afternoon",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c5_sentence_detail_bridge",
            4,
            "Leena left the green folder beside the computer before lunch.",
            "Which two details tell exactly where and when Leena left the folder?",
            ("beside the computer and before lunch",),
            options=(
                "beside the computer and before lunch",
                "green and Leena",
                "folder and lunch",
            ),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c5_sentence_detail_masterclass",
            4,
            (
                "The notice says the chess match starts at 2:00 in the activity hall. "
                "Practice starts at 1:30 in the classroom."
            ),
            "Which statement uses details from the chess match, not the practice?",
            ("The chess match starts at 2:00 in the activity hall.",),
            options=(
                "The chess match starts at 2:00 in the activity hall.",
                "The chess match starts at 1:30 in the classroom.",
                "The chess match starts at 2:00 in the classroom.",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c5_sentence_detail_revision_1",
            4,
            "Nikhil placed the wet umbrella outside the office door after assembly.",
            "What did Nikhil place, and where did he place it?",
            (
                "the wet umbrella outside the office door",
                "He placed the wet umbrella outside the office door.",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c5_sentence_detail_revision_2",
            5,
            (
                "The blue bus reaches Hill Road at 8:10. The yellow bus reaches "
                "Lake Road at 8:25."
            ),
            "Which bus reaches Lake Road, and at what time?",
            (
                "the yellow bus at 8:25",
                "The yellow bus reaches Lake Road at 8:25.",
            ),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c5_sentence_detail_revision_3",
            5,
            (
                "Although the sports shop closed at six, online orders placed "
                "before five were packed that evening by Tara."
            ),
            "Who packed the orders, and which orders were packed that evening?",
            (
                "Tara packed the online orders placed before five.",
                "Tara, the online orders placed before five",
            ),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c5_sentence_detail_independent",
            5,
            (
                "The science team will test the water samples in Lab 2 immediately "
                "after the morning break."
            ),
            "Where and when will the science team test the samples?",
            (
                "in Lab 2 immediately after the morning break",
                "Lab 2 after the morning break",
            ),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c5_sentence_detail_transfer",
            5,
            (
                "Concert tickets bought online can be collected from Window B "
                "between four and six on Friday."
            ),
            "From where and during which time can online tickets be collected?",
            (
                "from Window B between four and six on Friday",
                "Window B between four and six on Friday",
            ),
        ),
    },
    "english.c5.main_idea": {
        "guided_check": _deterministic_recap_check(
            "recap_c5_main_idea_guided",
            4,
            (
                "The class measured an empty wall, drew a plan, and painted a map "
                "of India on it for geography lessons."
            ),
            "Which idea is supported by all three actions?",
            ("the class created a wall map for learning",),
            options=(
                "the class created a wall map for learning",
                "the class measured one wall",
                "India has many geography lessons",
            ),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c5_main_idea_bridge",
            4,
            (
                "Mina labelled each herb, noted how much sun it received, and "
                "recorded its growth every week."
            ),
            "Which repeated idea links Mina's actions?",
            ("Mina studied how the herbs grew",),
            options=(
                "Mina studied how the herbs grew",
                "Mina wrote one label",
                "The sun was hot every week",
            ),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c5_main_idea_masterclass",
            4,
            (
                "A detail tells one part; the main idea covers the whole passage. "
                "Residents fixed broken swings, added soft ground, and installed "
                "lights around the park."
            ),
            "Choose the whole-passage idea rather than one small detail.",
            ("residents made the park safer",),
            options=(
                "residents made the park safer",
                "workers installed lights",
                "the park had one swing",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c5_main_idea_revision_1",
            4,
            (
                "Students collected old uniforms, washed them, sorted them by size, "
                "and gave them to families who needed them."
            ),
            "What is the passage mostly about?",
            ("students reused uniforms to help families",),
            options=(
                "students reused uniforms to help families",
                "students learned to measure sizes",
                "families bought new washing machines",
            ),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c5_main_idea_revision_2",
            5,
            (
                "The town added ramps at public buildings, lowered some bus steps, "
                "and marked wider parking spaces."
            ),
            "Which central idea connects these changes?",
            ("the town improved access for people with limited mobility",),
            options=(
                "the town improved access for people with limited mobility",
                "the town bought larger buses",
                "public buildings needed new paint",
            ),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c5_main_idea_revision_3",
            5,
            (
                "Farmers shared weather reports, changed sowing dates, and chose "
                "seeds that needed less water during a dry season."
            ),
            "What larger response do the details describe?",
            ("farmers adapted their plans to dry weather",),
            options=(
                "farmers adapted their plans to dry weather",
                "farmers sold weather reports",
                "all seeds need the same amount of water",
            ),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c5_main_idea_independent",
            5,
            (
                "A school team counted traffic near the gate, spoke with parents, "
                "and asked the council for a crossing guard."
            ),
            "What is the central idea?",
            ("the school team worked to make arrival safer",),
            options=(
                "the school team worked to make arrival safer",
                "parents counted the school gates",
                "the council hired a sports coach",
            ),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c5_main_idea_transfer",
            5,
            (
                "A theatre replaced paper tickets with reusable cards, fitted LED "
                "lights, and placed water refill stations in the lobby."
            ),
            "Which idea best joins the theatre's changes?",
            ("the theatre reduced waste and energy use",),
            options=(
                "the theatre reduced waste and energy use",
                "the theatre sold more paper tickets",
                "the lobby became a stage",
            ),
        ),
    },
    "english.c5.context_word": {
        "guided_check": _deterministic_recap_check(
            "recap_c5_context_word_guided",
            4,
            "The corridor was dim, so Noor switched on a torch to see the doors.",
            "What does dim mean in this sentence?",
            ("not brightly lit",),
            options=("not brightly lit", "very noisy", "full of people"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c5_context_word_bridge",
            4,
            "The puppy was timid and hid behind Ravi when visitors arrived.",
            "Which nearby clue best helps explain timid?",
            ("hid behind Ravi",),
            options=("hid behind Ravi", "visitors arrived", "Ravi had a puppy"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c5_context_word_masterclass",
            4,
            (
                "Do not choose a meaning from the word alone. In 'Sia was reluctant "
                "to enter; she paused at the door and stepped back,' her actions "
                "show how she felt."
            ),
            "What does reluctant mean here?",
            ("unwilling or unsure",),
            options=("unwilling or unsure", "eager to hurry", "unable to hear"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c5_context_word_revision_1",
            4,
            "After the long climb, the hikers were weary and rested beside the path.",
            "What does weary mean?",
            ("tired",),
            options=("tired", "lost", "cheerful"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c5_context_word_revision_2",
            5,
            (
                "The glass ornament was fragile, so Mehul wrapped it in cloth and "
                "carried it with both hands."
            ),
            "What precise meaning does fragile have here?",
            ("easily broken",),
            options=("easily broken", "very expensive", "difficult to carry"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c5_context_word_revision_3",
            5,
            (
                "The coach's instructions were concise: she explained the three "
                "steps clearly in only two sentences."
            ),
            "What does concise mean in this passage?",
            ("brief but clear",),
            options=("brief but clear", "confusing and long", "spoken very softly"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c5_context_word_independent",
            5,
            (
                "The stream was shallow; the water reached only to Ishan's ankles "
                "as he crossed it."
            ),
            "What does shallow mean here?",
            ("not deep",),
            options=("not deep", "flowing quickly", "unsafe to cross"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c5_context_word_transfer",
            5,
            (
                "The engineer called the first design impractical because it needed "
                "materials the village could not obtain."
            ),
            "What does impractical mean in this situation?",
            ("not workable",),
            options=("not workable", "carefully measured", "cheap to build"),
        ),
    },
    "english.c5.word_usage": {
        "guided_check": _deterministic_recap_check(
            "recap_c5_word_usage_guided",
            4,
            "Please ___ the wet floor with a sign so nobody slips.",
            "Choose the word that means give a clear warning.",
            ("mark",),
            options=("mark", "fold", "borrow"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c5_word_usage_bridge",
            4,
            "The monitor will ___ the books equally among four tables.",
            "Which word means share out the books?",
            ("distribute",),
            options=("distribute", "discover", "describe"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c5_word_usage_masterclass",
            4,
            (
                "A word must fit both meaning and sentence form. The committee will "
                "___ the safety plan after checking every step."
            ),
            "Choose the action word that completes the sentence.",
            ("approve",),
            options=("approve", "approval", "approved yesterday"),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c5_word_usage_revision_1",
            4,
            "Dark clouds may ___ the match until the rain stops.",
            "Choose the precise verb for moving an event to a later time.",
            ("postpone",),
            options=("postpone", "protect", "perform"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c5_word_usage_revision_2",
            5,
            "Planting grass can ___ loose soil from washing away.",
            "Choose the verb that means stop something from happening.",
            ("prevent",),
            options=("prevent", "permit", "predict"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c5_word_usage_revision_3",
            5,
            "The judges will ___ each model using the same three rules.",
            "Choose the word for examining quality by set rules.",
            ("evaluate",),
            options=("evaluate", "exchange", "entertain"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c5_word_usage_independent",
            5,
            "After comparing both routes, I would ___ the shaded forest path.",
            "Choose the verb for suggesting the better choice.",
            ("recommend",),
            options=("recommend", "remember", "remove"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c5_word_usage_transfer",
            5,
            "Scientists ___ results from several tests before reaching a conclusion.",
            "Choose the precise verb for looking for similarities and differences.",
            ("compare",),
            options=("compare", "compose", "collect"),
        ),
    },
    "english.c5.tense": {
        "guided_check": _deterministic_recap_check(
            "recap_c5_tense_guided",
            4,
            "Yesterday evening, Kavya ___ the final page of her project.",
            "Which verb matches the past-time clue?",
            ("completed",),
            options=("completed", "completes now", "will complete tomorrow"),
        ),
        "bridge": _deterministic_recap_check(
            "recap_c5_tense_bridge",
            4,
            "At this moment, the mechanics are checking the school bus.",
            "Which words show that the action is happening now?",
            ("at this moment",),
            options=("at this moment", "school bus", "the mechanics"),
        ),
        "masterclass": _deterministic_recap_check(
            "recap_c5_tense_masterclass",
            4,
            (
                "Keep the time clue and verb together. The sentence 'Last night, "
                "Zain checks the lock' mixes past time with present tense."
            ),
            "Which sentence repairs the tense mismatch?",
            ("Last night, Zain checked the lock.",),
            options=(
                "Last night, Zain checked the lock.",
                "Last night, Zain checks the lock.",
                "Tomorrow, Zain checked the lock.",
            ),
        ),
        "revision_level_1": _deterministic_recap_check(
            "recap_c5_tense_revision_1",
            4,
            "Look! The cooks ___ the bread from the oven now.",
            "Choose the verb phrase that matches now.",
            ("are taking",),
            options=("are taking", "took yesterday", "will take later"),
        ),
        "revision_level_2": _deterministic_recap_check(
            "recap_c5_tense_revision_2",
            5,
            "Next week, our class ___ the planetarium.",
            "Choose the future verb phrase.",
            ("will visit",),
            options=("will visit", "visited", "is visiting yesterday"),
        ),
        "revision_level_3": _deterministic_recap_check(
            "recap_c5_tense_revision_3",
            5,
            "When we reached the cinema, the film ___.",
            "Which phrase shows that the film started earlier?",
            ("had already started",),
            options=("had already started", "starts tomorrow", "is starting yesterday"),
        ),
        "independent_check": _deterministic_recap_check(
            "recap_c5_tense_independent",
            5,
            "Mira opened the box and ___ the old photographs inside.",
            "Which verb keeps both actions in the past?",
            ("found",),
            options=("found", "finds", "will find"),
        ),
        "transfer_check": _deterministic_recap_check(
            "recap_c5_tense_transfer",
            5,
            "By next Friday, the builders ___ the new ramp.",
            "Which phrase shows an action that will be finished by that future time?",
            ("will have completed",),
            options=("will have completed", "completed yesterday", "complete now"),
        ),
    },
    "english.c5.sentence_order": {
        "guided_check": {
            "source_item_id": "recap_c5_sentence_order_guided",
            "source_class_no": 4,
            "passage": (
                "Parts: because the hall was being cleaned / the assembly / "
                "moved outside"
            ),
            "prompt": "Build one sentence that gives the reason for moving outside.",
            "options": [],
            "accepted_answers": [
                "The assembly moved outside because the hall was being cleaned.",
                "Because the hall was being cleaned, the assembly moved outside.",
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "bridge": {
            "source_item_id": "recap_c5_sentence_order_bridge",
            "source_class_no": 4,
            "passage": (
                "Start with who did the action, then add the reason. Parts: "
                "the hikers / waited near the gate / because the path was slippery"
            ),
            "prompt": "Put the parts into one clear sentence.",
            "options": [],
            "accepted_answers": [
                "The hikers waited near the gate because the path was slippery."
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "masterclass": {
            "source_item_id": "recap_c5_sentence_order_masterclass",
            "source_class_no": 4,
            "passage": (
                "Keep the contrast first and the main action second. Parts: "
                "although the rain continued / the volunteers / finished / "
                "covering the books"
            ),
            "prompt": "Build the complete contrast sentence.",
            "options": [],
            "accepted_answers": [
                "Although the rain continued, the volunteers finished covering the books."
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "revision_level_1": {
            "source_item_id": "recap_c5_sentence_order_revision_1",
            "source_class_no": 4,
            "passage": "Parts: before the guests arrived / the team / arranged / the chairs",
            "prompt": "Build a sentence that makes the timing clear.",
            "options": [],
            "accepted_answers": [
                "Before the guests arrived, the team arranged the chairs.",
                "The team arranged the chairs before the guests arrived.",
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "revision_level_2": {
            "source_item_id": "recap_c5_sentence_order_revision_2",
            "source_class_no": 5,
            "passage": "Parts: after the experiment ended / the students / checked / each result",
            "prompt": "Build a sentence that keeps the events in order.",
            "options": [],
            "accepted_answers": [
                "After the experiment ended, the students checked each result.",
                "The students checked each result after the experiment ended.",
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "revision_level_3": {
            "source_item_id": "recap_c5_sentence_order_revision_3",
            "source_class_no": 5,
            "passage": (
                "Parts: although the first route was blocked / the driver / "
                "found / another road"
            ),
            "prompt": "Build one sentence that preserves the contrast.",
            "options": [],
            "accepted_answers": [
                "Although the first route was blocked, the driver found another road.",
                "The driver found another road although the first route was blocked.",
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "independent_check": {
            "source_item_id": "recap_c5_sentence_order_independent",
            "source_class_no": 5,
            "passage": "Parts: because the microphone failed / the speaker / spoke / loudly",
            "prompt": "Build the sentence independently.",
            "options": [],
            "accepted_answers": [
                "The speaker spoke loudly because the microphone failed.",
                "Because the microphone failed, the speaker spoke loudly.",
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "transfer_check": {
            "source_item_id": "recap_c5_sentence_order_transfer",
            "source_class_no": 5,
            "passage": (
                "Parts: before the science fair opened / the group / tested / "
                "every switch on its model"
            ),
            "prompt": "Use the same sentence-order skill in this new situation.",
            "options": [],
            "accepted_answers": [
                "Before the science fair opened, the group tested every switch on its model.",
                "The group tested every switch on its model before the science fair opened.",
            ],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
    },
    "english.c5.inference": {
        "guided_check": {
            "source_item_id": "recap_c5_inference_guided",
            "source_class_no": 4,
            "passage": (
                "Rohan came inside with drops on his hair and folded a wet "
                "raincoat beside the door."
            ),
            "prompt": "What probably happened outside? Explain with one clue.",
            "options": [],
            "accepted_answers": [],
            "evaluation_mode": "strict_rubric",
            "rubric_ref": "school.strict.inference.v1",
        },
        "bridge": {
            "source_item_id": "recap_c5_inference_bridge",
            "source_class_no": 4,
            "passage": (
                "The snack tray was empty. Crumbs covered the table, and a "
                "chocolate mark was on Dev's fingers."
            ),
            "prompt": "Which clue most strongly suggests that Dev ate the snack?",
            "options": [
                "The chocolate mark on Dev's fingers",
                "The table was near a window",
                "The tray was made of metal",
            ],
            "accepted_answers": ["The chocolate mark on Dev's fingers"],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "masterclass": {
            "source_item_id": "recap_c5_inference_masterclass",
            "source_class_no": 4,
            "passage": (
                "Neha closed the curtains and moved her chair away from the "
                "bright patch on the floor before she continued reading."
            ),
            "prompt": "Why did Neha move her chair? Link your answer to a clue.",
            "options": [],
            "accepted_answers": [],
            "evaluation_mode": "strict_rubric",
            "rubric_ref": "school.strict.inference.v1",
        },
        "revision_level_1": {
            "source_item_id": "recap_c5_inference_revision_1",
            "source_class_no": 4,
            "passage": (
                "The lights flickered, every fan stopped, and the caretaker "
                "walked straight to the main switch."
            ),
            "prompt": "Which detail is the strongest evidence of a power problem?",
            "options": [
                "Every fan stopped",
                "The caretaker wore shoes",
                "The room had a door",
            ],
            "accepted_answers": ["Every fan stopped"],
            "evaluation_mode": "deterministic",
            "rubric_ref": None,
        },
        "revision_level_2": {
            "source_item_id": "recap_c5_inference_revision_2",
            "source_class_no": 5,
            "passage": (
                "A crowd waited outside the bakery, but the door stayed locked "
                "and a SOLD OUT sign hung in the window."
            ),
            "prompt": "Why could the crowd not buy bread? Use evidence.",
            "options": [],
            "accepted_answers": [],
            "evaluation_mode": "strict_rubric",
            "rubric_ref": "school.strict.inference.v1",
        },
        "revision_level_3": {
            "source_item_id": "recap_c5_inference_revision_3",
            "source_class_no": 5,
            "passage": (
                "Meera had soil on both hands, an empty seed packet lay beside "
                "her, and six new seedlings stood in the garden bed."
            ),
            "prompt": "What had Meera probably been doing? Explain with a clue.",
            "options": [],
            "accepted_answers": [],
            "evaluation_mode": "strict_rubric",
            "rubric_ref": "school.strict.inference.v1",
        },
        "independent_check": {
            "source_item_id": "recap_c5_inference_independent",
            "source_class_no": 5,
            "passage": (
                "The library return cart was overflowing, and several spaces "
                "on the shelves were empty after the long weekend."
            ),
            "prompt": "What probably happened over the weekend? Use one clue.",
            "options": [],
            "accepted_answers": [],
            "evaluation_mode": "strict_rubric",
            "rubric_ref": "school.strict.inference.v1",
        },
        "transfer_check": {
            "source_item_id": "recap_c5_inference_transfer",
            "source_class_no": 5,
            "passage": (
                "Arjun returned at sunset with mud on his shoes, grass on his "
                "knees, and a football tucked under his arm."
            ),
            "prompt": "What had Arjun probably been doing? Explain with evidence.",
            "options": [],
            "accepted_answers": [],
            "evaluation_mode": "strict_rubric",
            "rubric_ref": "school.strict.inference.v1",
        },
    },
    "english.c5.summary": {
        "guided_check": _rubric_recap_check(
            "recap_c5_summary_guided",
            4,
            (
                "A bicycle chain slipped during the ride. Farah stopped, put the "
                "chain back on the wheel, and rode home safely."
            ),
            "Summarize the problem and solution in one English sentence.",
            "school.strict.summary.v1",
        ),
        "bridge": _deterministic_recap_check(
            "recap_c5_summary_bridge",
            4,
            (
                "A leaking pipe soaked the classroom floor. The caretaker closed "
                "the water valve and dried the room."
            ),
            "Which idea must a useful summary include?",
            ("A leak was stopped and the wet room was dried.",),
            options=(
                "A leak was stopped and the wet room was dried.",
                "The classroom had a floor.",
                "The caretaker entered a room.",
            ),
        ),
        "masterclass": _rubric_recap_check(
            "recap_c5_summary_masterclass",
            4,
            (
                "Rohan missed the first practice because his bus was late. He asked "
                "the coach for the plan, practised at home, and joined the team the "
                "next day."
            ),
            (
                "Retell the main problem and response in your own words. Leave out "
                "small details that do not change the event."
            ),
            "school.strict.summary.v1",
        ),
        "revision_level_1": _rubric_recap_check(
            "recap_c5_summary_revision_1",
            4,
            (
                "Wind scattered the class display across the courtyard. Students "
                "collected the pages and fixed them to a board with clips."
            ),
            "Write one sentence that keeps the problem and what students did.",
            "school.strict.summary.v1",
        ),
        "revision_level_2": _rubric_recap_check(
            "recap_c5_summary_revision_2",
            5,
            (
                "The playground became muddy after heavy rain. The school moved "
                "games to the hall and spread gravel on the wet path."
            ),
            "Summarize the situation and the school's response in your own words.",
            "school.strict.summary.v1",
        ),
        "revision_level_3": _rubric_recap_check(
            "recap_c5_summary_revision_3",
            5,
            (
                "Local fish numbers fell when rubbish gathered near the river bank. "
                "Volunteers cleared the waste and began checking the water each month."
            ),
            "Summarize the cause and the action taken in one or two sentences.",
            "school.strict.summary.v1",
        ),
        "independent_check": _rubric_recap_check(
            "recap_c5_summary_independent",
            5,
            (
                "A reading club had few books in different languages. Families "
                "donated stories, and older students organised them on labelled shelves."
            ),
            "Summarize how the reading club improved its collection.",
            "school.strict.summary.v1",
        ),
        "transfer_check": _rubric_recap_check(
            "recap_c5_summary_transfer",
            5,
            (
                "A baker noticed that many unsold loaves were thrown away each evening. "
                "She began offering them to a community kitchen before closing time."
            ),
            "Summarize the issue and the baker's new action without copying the passage.",
            "school.strict.summary.v1",
        ),
    },
}


def new_recap_state(
    report: dict[str, Any],
    *,
    preferred_teaching_language: str = "en",
    en_production_confidence: float = 0.0,
) -> dict[str, Any]:
    modules = [_module_from_report_item(item) for item in report.get("recommended_recap_modules") or []]
    return normalize_recap_state({
        "engine_version": ENGINE_VERSION,
        "profile_version_id": str(report["profile_version_id"]),
        "source_placement_report_id": str(report["report_id"]),
        "source_placement_session_id": str(report["placement_session_id"]),
        "subject_id": report["subject_id"],
        "target_class_no": int(report["target_class_no"]),
        "active_learning_class_no": int(report["active_learning_class_no"]),
        "preferred_teaching_language": str(
            preferred_teaching_language or "en"
        ),
        "en_production_confidence": max(
            0.0,
            min(1.0, float(en_production_confidence)),
        ),
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
    open_answer_preflight_failed: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = normalize_recap_state(state)
    activity = _current_activity(normalized)
    if not activity or activity["activity_id"] != activity_id:
        raise ValueError("unexpected_recap_activity")

    evaluator_activity = evaluator_activity_for_answer(activity)
    if evaluator_activity is not None:
        if open_answer_preflight_failed:
            answer_evaluation = _open_answer_preflight_failure(evaluator_activity)
        elif open_answer_evaluation is None:
            raise ValueError("open_answer_evaluation_required")
        else:
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
        elif activity["kind"] == "masterclass" and (
            _has_deep_authored_sequence(module) or attempt_no >= 2
        ):
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
            missing_criteria=[
                str(criterion_id)
                for criterion_id in answer_evaluation["missing_criteria"]
            ],
        ),
        "next_move": _feedback_next_move(
            activity,
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
        "grading_mode": "strict_open_rubric",
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
    language_support = localized_teaching_support(
        preferred_language=str(
            state.get("preferred_teaching_language") or "en"
        ),
        skill_ids=[str(module["primary_skill_id"])],
        stage=str(step),
        en_production_confidence=float(
            state.get("en_production_confidence") or 0.0
        ),
    )
    authored_teaching_block = (
        module["teaching_block"]
        if step == "guided_check"
        else _support_block(module, step)
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
        "teaching_block": " ".join(
            part
            for part in (language_support, authored_teaching_block)
            if part
        ),
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

    authored_checks = RECAP_TRACK_CHECK_BANK.get(track_id)
    if authored_checks is not None:
        return _validated_authored_checks(track, authored_checks)
    if target_class_no in {2, 3, 4, 5}:
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


def _validated_authored_checks(
    track: Any,
    checks: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    if tuple(checks) != RECAP_AUTHORED_STAGES:
        raise ValueError("recap_content_not_authored")

    source_item_ids = [
        str(check.get("source_item_id") or "").strip()
        for check in checks.values()
    ]
    task_pairs = [
        (_normalize(str(check.get("prompt") or "")), _normalize(str(check.get("passage") or "")))
        for check in checks.values()
    ]
    prompts = [prompt for prompt, _ in task_pairs]
    passages = [passage for _, passage in task_pairs]
    if (
        any(not source_item_id for source_item_id in source_item_ids)
        or len(set(source_item_ids)) != len(RECAP_AUTHORED_STAGES)
        or any(not prompt or not passage for prompt, passage in task_pairs)
        or len(set(prompts)) != len(RECAP_AUTHORED_STAGES)
        or len(set(passages)) != len(RECAP_AUTHORED_STAGES)
        or len(set(task_pairs)) != len(RECAP_AUTHORED_STAGES)
    ):
        raise ValueError("recap_content_not_authored")

    placement_items = [
        track.snapshot_item,
        *(item for band in track.bands for item in band.variants),
    ]
    placement_pairs = {
        (_normalize(item.prompt), _normalize(item.passage))
        for item in placement_items
    }
    if placement_pairs.intersection(task_pairs):
        raise ValueError("recap_content_not_authored")

    copied: dict[str, dict[str, Any]] = {}
    for name, check in checks.items():
        evaluation_mode = str(check.get("evaluation_mode") or "")
        accepted_answers = list(check.get("accepted_answers") or [])
        rubric_ref = str(check.get("rubric_ref") or "")
        if evaluation_mode == "deterministic":
            if not accepted_answers or rubric_ref:
                raise ValueError("recap_content_not_authored")
        elif evaluation_mode == "strict_rubric":
            if accepted_answers or rubric_ref not in STRICT_RUBRIC_CRITERIA_BY_REF:
                raise ValueError("recap_content_not_authored")
        else:
            raise ValueError("recap_content_not_authored")
        copied[name] = {
            **check,
            "options": list(check.get("options") or []),
            "accepted_answers": accepted_answers,
        }
    return copied


def _has_deep_authored_sequence(module: dict[str, Any]) -> bool:
    checks = dict(module.get("checks") or {})
    if set(checks) != set(RECAP_AUTHORED_STAGES):
        return False
    source_item_ids = [
        str(checks[stage].get("source_item_id") or "")
        for stage in RECAP_AUTHORED_STAGES
    ]
    return (
        all(source_item_ids)
        and len(set(source_item_ids)) == len(RECAP_AUTHORED_STAGES)
    )


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
    return accepted_answer_matches(
        answer,
        list(activity.get("accepted_answers") or []),
    )


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

    def revision_check(source: dict[str, Any], *, passage: str) -> dict[str, Any]:
        # Preserve the source check's grading contract. Dropping evaluation_mode
        # here turns strict-rubric revisions into impossible deterministic items.
        return {
            **source,
            "passage": passage,
            "options": list(source.get("options") or []),
            "accepted_answers": list(source.get("accepted_answers") or []),
        }

    return {
        **checks,
        "revision_level_1": revision_check(
            bridge,
            passage=(
                f"Revision 1: start with the strongest clue. "
                f"{bridge.get('passage') or ''}"
            ).strip(),
        ),
        "revision_level_2": revision_check(
            independent,
            passage=(
                f"Revision 2: try a nearby example. "
                f"{independent.get('passage') or ''}"
            ).strip(),
        ),
        "revision_level_3": revision_check(
            masterclass,
            passage=(
                f"Revision 3: one final supported check. "
                f"{masterclass.get('passage') or ''}"
            ).strip(),
        ),
    }


def _feedback_message(
    activity: dict[str, Any],
    correct: bool,
    *,
    next_step: str,
    missing_criteria: list[str] | None = None,
) -> str:
    if correct and activity["kind"] == "independent_check":
        return "Good. One more step: use the same skill in a new passage."
    if correct and activity["kind"] == "transfer_check":
        return "Good. You used the skill in a new passage, so this foundation module is complete."
    if correct and activity["kind"] in {"revision_level_1", "revision_level_2"}:
        return "Good. Move to the next revision level."
    if correct:
        return "Good. Now try the same skill without hints."
    missing_instruction = next(
        (
            RUBRIC_REMEDIATION_BY_CRITERION[criterion_id]
            for criterion_id in missing_criteria or []
            if criterion_id in RUBRIC_REMEDIATION_BY_CRITERION
        ),
        "",
    )
    learner_move = f" {missing_instruction}" if missing_instruction else ""
    if activity["kind"] == "bridge":
        return f"Not yet.{learner_move} Zidd is opening a focused masterclass for this skill."
    if activity["kind"] == "masterclass" and next_step == "revision_level_1":
        return f"This needs a short revision run before trying again.{learner_move}"
    if activity["kind"] == "masterclass":
        return f"Not yet.{learner_move} Stay in the masterclass and try one more supported check."
    if activity["kind"] in REVISION_STEPS:
        return f"Not yet.{learner_move} Stay on this revision level and rebuild the clue."
    return f"Not yet.{learner_move} Zidd will slow this down with a bridge check before moving ahead."


def _feedback_next_move(
    activity: dict[str, Any],
    *,
    next_step: str,
) -> dict[str, str]:
    """Give the learner a skill-specific move without disclosing an answer key."""

    skill_ids = [str(skill_id) for skill_id in activity.get("skill_ids") or []]
    primary_skill_id = skill_ids[0] if skill_ids else ""
    strategy = TEACHING_BLOCK_BY_SKILL.get(
        primary_skill_id,
        "Read the prompt again, find the useful clue, then answer only what it asks.",
    )
    return {
        "stage": next_step or "guided_check",
        "focus": str(activity.get("focus") or "this skill"),
        "strategy": strategy,
    }


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().lower().replace(".", "").replace(",", "").split())


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")[:48]
