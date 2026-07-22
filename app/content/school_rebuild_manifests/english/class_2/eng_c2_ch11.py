"""Original deep manifest for Class 2 English Chapter 11, The Smart Monkey."""

from __future__ import annotations

from typing import Any

from app.content.school_rebuild_manifests.english.class_2.eng_c2_ch08 import (
    CLASS2_SKILLS,
    _open_set,
    build_manifest,
    choice_task,
    evidence,
    open_task,
)


S = CLASS2_SKILLS
CHAPTER_ID = "eng_c2_ch11"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/bemr111.pdf"


LEVELS: list[dict[str, Any]] = [
    {
        "level_id": f"{CHAPTER_ID}:litter_cleanup_chain",
        "title": "Follow a clean-up example",
        "focus": "sequence littering, noticing, and responsible repair actions",
        "outcome": "Retell a clean-up chain in order and explain how one visible example changes another person's decision.",
        "skill_ids": [S["comprehension"], S["sequence"]],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-3", f"{CHAPTER_ID}:write:6"],
        "principle": "A responsibility chain links an action, its effect on a shared place, a visible example, and a repair choice in time order.",
        "connect": {
            "teaching_block": "Readers track who drops, notices, models, and repairs. The responsible lesson must be tied to a stated action.",
            "passage": "Ria leaves a juice straw on a bench. A younger child places his wrapper in a dustbin, so Ria returns and clears the straw.",
            "prompt": "Notice the first litter, the example, and Ria's final repair before continuing.",
        },
        "co": choice_task(
            "A vendor drops a paper tie. A cleaner picks it up and sorts it into a dry-waste bin. The vendor then collects two more ties.",
            "What happens immediately after the cleaner sorts the first tie?",
            "The vendor collects two more ties.",
            ["The cleaner drops every tie.", "The bin moves to the shop."],
        ),
        "guided": [
            choice_task(
                "Kabir finishes a snack, folds the wrapper, walks to the blue bin, and drops it inside.",
                "Which action happens just before the wrapper enters the bin?",
                "Kabir walks to the blue bin.",
                ["Kabir finishes the snack.", "Kabir opens another wrapper."],
            ),
            open_task(
                "Two children leave cups near a tree. A gardener carries her empty cup to the dustbin. The children notice, return, and clear both cups.",
                "Retell the actions and explain what prompts the children to repair the place.",
                "The children leave cups, see the gardener use the dustbin, and then return to clear their litter.",
                [
                    evidence("Orders leaving before noticing.", "leave cups", "see the gardener", "notice"),
                    evidence("Links the gardener's example to clearing litter.", "use the dustbin", "return to clear")
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set(
            [
                (
                    "A family leaves a fruit peel beside a park path. They see a cyclist stop to move the slippery peel into a bin, then they collect their remaining waste.",
                    "Sequence the problem, example, and repair, including why the peel mattered.",
                    "The family leaves a slippery peel, sees the cyclist bin it for safety, and then collects the remaining waste.",
                    [
                        evidence("Names the slippery peel problem.", "slippery peel", "leaves a fruit peel"),
                        evidence("Orders cyclist example before family repair.", "cyclist", "bin it", "collects the remaining waste")
                    ],
                ),
                (
                    "Navi drops a bus ticket near the gate. A monkey carries a banana skin to a nearby dustbin, and Navi feels uneasy, picks up the ticket, and bins it.",
                    "Explain the visible cause of Navi's changed action and retell the order.",
                    "Navi drops the ticket, notices the monkey use the dustbin, and changes course by picking up and binning the ticket.",
                    [
                        evidence("Keeps dropping before noticing.", "drops the ticket", "notices the monkey"),
                        evidence("Links the example to picking up the ticket.", "use the dustbin", "picking up", "binning the ticket")
                    ],
                ),
            ],
            ordered=True,
        ),
        "transfer": _open_set(
            [
                (
                    "In a classroom, paint-paper scraps cover one table. A pupil sorts her own scraps into a reuse tray, and the group follows her example.",
                    "Transfer the example-and-repair chain to the classroom.",
                    "The table is messy, one pupil models sorting into the reuse tray, and the group follows by sorting its scraps.",
                    [
                        evidence("States the paper-scrap problem.", "table is messy"),
                        evidence("Shows the pupil's model.", "models sorting", "reuse tray"),
                        evidence("Shows the group applying the model.", "group follows by sorting its scraps")
                    ],
                ),
                (
                    "A dripping tap leaves water on the floor. Arman closes it and places a warning sign; after seeing him, his friend wipes the wet patch.",
                    "Sequence the safety actions and explain the friend's response.",
                    "Arman closes the tap and posts a warning, then his friend wipes the wet floor and follows the example.",
                    [
                        evidence("Orders closing before wiping.", "closes the tap", "friend", "wiping"),
                        evidence("Connects the example to the response.", "wet floor", "follows the example")
                    ],
                ),
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "Lina puts an empty bottle under a seat. She watches a child carry a torn bag to the waste station, then retrieves and sorts her bottle.",
                    "Give the complete action chain and the responsible final choice.",
                    "Lina hides the bottle, sees the child use the waste station, and responsibly returns to sort her bottle.",
                    [
                        evidence("Orders hiding before watching.", "puts an empty bottle", "sees the child"),
                        evidence("Names returning and sorting as repair.", "responsibly", "returns", "sort her bottle")
                    ],
                ),
                (
                    "The picnic team leaves a cloth on the grass. Wind pushes it toward a pond, so Mehul catches it and reminds everyone to pack loose items.",
                    "Explain cause, immediate action, and prevention in order.",
                    "Wind pushes the cloth toward the pond, Mehul catches it, and the team prevents another problem by packing loose items.",
                    [
                        evidence("Links wind to the risky movement.", "wind pushes", "toward the pond"),
                        evidence("Orders catching before prevention.", "catches it", "packing loose items")
                    ],
                ),
            ],
            ordered=True,
        ),
        "cluster_id": f"{CHAPTER_ID}:cleanup_order_example_gap",
        "misconception": "The learner remembers only the animal or bin, reverses the repair sequence, or states a lesson without naming the visible example that caused change.",
        "remediation": "Build four boxes for problem, model, noticing, and repair; require one exact action in each before stating the responsibility lesson.",
        "support": _open_set(
            [
                ("A wrapper falls, a child notices it, and she places it in the dustbin.", "Order the three clean-up events.", "The wrapper falls, the child notices it, and she puts it in the dustbin.", [evidence("Keeps fall, notice, and bin in order.", "wrapper falls", "notices", "dustbin")]),
                ("A monkey carries a peel to a bin while Ravi's cup remains on the ground.", "State the clean example and Ravi's needed repair.", "The monkey models using the bin, and Ravi should pick up and bin his cup.", [evidence("Connects the model to cup repair.", "monkey models", "pick up", "bin his cup")]),
                ("Oil spills near a step. Sana marks the spot, then an adult cleans it.", "Give the safety actions in order.", "Sana marks the spill first, and an adult cleans the dangerous spot next.", [evidence("Orders marking before cleaning.", "marks the spill", "adult cleans")]),
                ("The class sees the monitor sort paper and then sorts its own paper.", "Explain why the class changes its action.", "The monitor's sorting example prompts the class to sort its own paper.", [evidence("Links example to changed action.", "sorting example", "class", "sort its own paper")]),
                ("A bottle blocks the path. Ishan moves it into a recycling bin.", "State the problem and responsible result.", "The bottle blocks the path, and Ishan responsibly clears it into the recycling bin.", [evidence("Includes blocked path and cleared bottle.", "blocks the path", "clears it", "recycling bin")]),
            ],
            ordered=True,
        ),
    },
    {
        "level_id": f"{CHAPTER_ID}:clean_place_words",
        "title": "Use clean-place vocabulary",
        "focus": "infer litter, nearby, empty, ashamed, dispose, and responsible from context",
        "outcome": "Explain a clean-place word from visible clues and use it accurately in a new shared-space sentence.",
        "skill_ids": [S["word_context"], S["word_use"]],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-3", f"{CHAPTER_ID}:speak:4"],
        "principle": "The surrounding action or result reveals a clean-place word; a fresh use must preserve the same safety or responsibility meaning.",
        "connect": {
            "teaching_block": "Context can show where something is, whether it contains anything, and how a person feels after noticing a mistake.",
            "passage": "The bin is nearby, only two steps from the bench.",
            "prompt": "Notice how two steps from the bench explains nearby.",
        },
        "co": choice_task("Paper cups and wrappers left across the lawn become litter instead of being placed in a bin.", "Which meaning fits litter?", "waste left in the wrong place", ["plants growing in a row", "clean tools on a shelf"]),
        "guided": [
            choice_task("The bottle is empty; no juice remains inside it.", "Which phrase explains empty?", "nothing remains inside", ["the bottle is heavy", "the juice is fresh"]),
            open_task("Rohan feels ashamed after noticing that his dropped packet made the clean path messy.", "Explain ashamed from the clue and use it in a new repair sentence.", "Ashamed means sorry or embarrassed about a wrong action. Rohan feels ashamed and picks up the packet.", [evidence("Explains regret or embarrassment.", "sorry", "embarrassed", "wrong action"), evidence("Uses ashamed with repair.", "feels ashamed", "picks up")]),
        ],
        "independent": _open_set([
            ("To dispose of the broken cup safely, Mira places it in the marked waste container.", "Define dispose from context and write a different accurate use.", "Dispose means put waste in the proper place. We dispose of wrappers in the correct bin.", [evidence("Explains proper waste placement.", "put waste in the proper place", "correct bin"), evidence("Uses dispose with waste.", "dispose of wrappers", "dispose of litter")]),
            ("A responsible visitor carries every picnic item away and leaves the shared table clean.", "Explain responsible and use it for a classroom action.", "Responsible means taking proper care of duties and effects. A responsible learner clears art scraps from the desk.", [evidence("Defines proper care or duty.", "proper care", "duties", "effects"), evidence("Uses responsible with a clean action.", "responsible learner", "clears art scraps")]),
        ]),
        "transfer": _open_set([
            ("The caretaker separates paper from food waste, placing each type in a different container.", "Infer separates and use it for a recycling task.", "Separates means divides into groups. Our class separates clean paper from wet waste.", [evidence("Defines dividing into groups.", "divides into groups"), evidence("Uses separates with two waste types.", "separates clean paper", "wet waste")]),
            ("The floor is spotless after every crumb and mark has been removed.", "Explain spotless and transfer it to a desk sentence.", "Spotless means completely clean. Leena left the shared desk spotless after craft time.", [evidence("Defines completely clean.", "completely clean"), evidence("Uses spotless for a cleaned place.", "desk spotless", "room spotless")]),
        ]),
        "review": _open_set([
            ("A wrapper creates a hazard because someone could slip on it near the steps.", "Explain hazard and use it in another clean-place idea.", "A hazard is something that may cause harm. Spilled water is a slipping hazard.", [evidence("Defines possible harm.", "may cause harm", "danger"), evidence("Uses hazard with a safety example.", "slipping hazard", "water is a hazard")]),
            ("The clean-up team restores the garden, returning it to a tidy state after the event.", "State the meaning of restores and create a new use.", "Restores means brings back a good earlier state. Sorting and sweeping restores the reading corner.", [evidence("Explains bringing back a state.", "brings back", "earlier state"), evidence("Uses restores with a place.", "restores the reading corner", "restores the room")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:clean_word_surface_guess",
        "misconception": "The learner chooses a general cleaning word without matching the nearby action, place, feeling, or safety result.",
        "remediation": "Underline the context result, replace the target with a plain phrase, and test the phrase in one new sentence about a shared place.",
        "support": _open_set([
            ("The dustbin is adjacent to the gate, directly beside it.", "Explain adjacent from the location clue.", "Adjacent means directly beside or next to something.", [evidence("Uses the beside meaning.", "directly beside", "next to")]),
            ("The packet is crumpled, pressed into many untidy folds.", "Define crumpled and use it with paper.", "Crumpled means pressed into messy folds. A crumpled paper lay near the bin.", [evidence("Defines and uses messy folds.", "messy folds", "crumpled paper")]),
            ("The group regrets leaving cups behind and wishes it had cleared them.", "Explain regrets from the clue.", "Regrets means feels sorry about a past action.", [evidence("States feeling sorry about the past.", "feels sorry", "past action")]),
            ("The sorted bottles are recyclable, so they can be processed and used again.", "Define recyclable and use it accurately.", "Recyclable means able to be processed for use again. Clean glass bottles are recyclable.", [evidence("Explains use again.", "processed for use again", "used again"), evidence("Uses recyclable with bottles.", "bottles are recyclable")]),
            ("The path is tidy because every loose item is in its proper place.", "Explain tidy and use it for a classroom.", "Tidy means neat with things in proper places. The class keeps its reading corner tidy.", [evidence("Defines and uses neat order.", "things in proper places", "corner tidy")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:visible_cleanup_spellings",
        "title": "Build clean-up spellings",
        "focus": "use printed chunks and blends to spell clean-place words",
        "outcome": "Produce a standard spelling from visible letter evidence and use the clean-up word in a meaningful sentence.",
        "skill_ids": [S["spelling"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:listen:5", f"{CHAPTER_ID}:speak-blends:8"],
        "principle": "This text-only lab uses printed chunks and blends; it does not claim evidence from clapping, pronunciation, or listening.",
        "connect": {
            "teaching_block": "Read each visible chunk, join every letter, and check that the whole spelling fits the clean-place clue.",
            "passage": "Printed chunks: dust + bin = dustbin; class + room = classroom.",
            "prompt": "Notice that two meaningful chunks combine into each whole word.",
        },
        "co": choice_task("Candidates: packet, paket, packit. The clue names a small wrapper or container.", "Which candidate is the standard litter-item spelling?", "packet", ["paket", "packit"]),
        "guided": [
            choice_task("Candidates: flower, flouer, flowar. The sentence needs a garden plant word.", "Which printed word is standard?", "flower", ["flouer", "flowar"]),
            open_task("Chunks: clean + er. The clue names a person who cleans.", "Build the person word, then tell one clean-up action that person performs.", "The word is cleaner. The cleaner emptied the dry-waste bin.", [evidence("Spells cleaner correctly.", "cleaner"), evidence("Uses cleaner with a clean-up action.", "cleaner emptied", "cleaner swept")]),
        ],
        "independent": _open_set([
            ("Missing letters: l i t t _ r. The clue means waste left in the wrong place.", "Complete the word and use it in a sentence.", "The word is litter. We picked up litter beside the path.", [evidence("Spells litter correctly.", "litter"), evidence("Uses litter as misplaced waste.", "picked up litter", "litter beside")]),
            ("Scrambled letters: p e e l. The clue names the outer skin removed from fruit.", "Unscramble the word and write a clean-up sentence.", "The word is peel. Rani put the fruit peel in the correct bin.", [evidence("Spells peel correctly.", "peel"), evidence("Uses peel with correct disposal.", "fruit peel", "correct bin")]),
        ]),
        "transfer": _open_set([
            ("Base word: care. Add ful to describe an action done with attention.", "Build the new word and use it in a cleaning sentence.", "The word is careful. A careful pupil checks the waste label.", [evidence("Builds careful correctly.", "careful"), evidence("Uses careful with a responsible action.", "careful pupil", "checks the waste label")]),
            ("Chunks: re + use. The clue means use an item again.", "Join the chunks and write one complete sentence.", "The word is reuse. We reuse a clean jar for pencils.", [evidence("Spells reuse correctly.", "reuse"), evidence("Uses reuse for using again.", "reuse a clean jar", "reuse the box")]),
        ]),
        "review": _open_set([
            ("Correct the printed word emptie in a sentence about a bottle with nothing inside.", "Write the corrected word and sentence.", "The corrected word is empty. The empty bottle belongs in the marked bin.", [evidence("Corrects empty.", "empty"), evidence("Uses it with a bottle and bin.", "empty bottle", "marked bin")]),
            ("Missing letters: c l _ a n. The clue means free from dirt or litter.", "Complete the word and use it for a place.", "The word is clean. We left the picnic table clean.", [evidence("Spells clean correctly.", "clean"), evidence("Uses clean for a shared place.", "table clean", "room clean")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:cleanup_chunk_spelling",
        "misconception": "The learner drops a visible blend or compound chunk, or chooses a familiar spelling that does not match the clean-up clue.",
        "remediation": "Trace each printed chunk, join all letters, check the waste or place meaning, and finish with one short written use.",
        "support": _open_set([
            ("Chunks: mar + ket. The clue names a place with shops.", "Join and use the place word.", "The word is market. The market has bins near each gate.", [evidence("Spells and uses market.", "market", "market has bins")]),
            ("Chunks: mon + key. The clue names the animal in the chapter theme.", "Build the word and write a sentence.", "The word is monkey. The monkey placed a peel in the dustbin.", [evidence("Spells and uses monkey.", "monkey", "placed a peel")]),
            ("Candidates: floor, flor, floore. The clue names the surface under our feet.", "Write the standard spelling in a clean sentence.", "The word is floor. We wiped the wet floor carefully.", [evidence("Spells and uses floor.", "floor", "wiped the wet floor")]),
            ("Scrambled letters: c l p a. The clue means strike hands together, but here only spelling is checked.", "Unscramble and use the word in writing.", "The word is clap. The sign says, 'Clap only after the clean-up report.'", [evidence("Spells and uses clap in text.", "clap", "sign says")]),
            ("Correct this word: botle. The container word needs two t letters.", "Repair and use the word.", "The corrected word is bottle. The bottle went into the recycling bin.", [evidence("Corrects and uses bottle.", "bottle", "recycling bin")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:cleanup_word_jobs",
        "title": "Find jobs in clean-place sentences",
        "focus": "identify nouns, verbs, and adjectives in responsible-action sentences",
        "outcome": "Classify requested words by their sentence job and connect action verbs to clean-up choices.",
        "skill_ids": [S["word_jobs"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:write:6", f"{CHAPTER_ID}:speak-blends:8"],
        "principle": "Clean-place sentences name items and places, show actions, and describe conditions; the whole sentence proves each word job.",
        "connect": {
            "teaching_block": "Ask what is named, what happens, and what kind. A clean-up word can have a different job from another word on the same topic.",
            "passage": "The careful child lifts an empty bottle. Child and bottle name, lifts acts, and careful and empty describe.",
            "prompt": "Notice the job evidence attached to each visible word.",
        },
        "co": choice_task("A nearby dustbin holds dry paper.", "Which word describes the dustbin?", "nearby", ["dustbin", "holds"]),
        "guided": [
            choice_task("Responsible pupils sort the waste.", "Which word tells what the pupils do?", "sort", ["responsible", "pupils"]),
            open_task("The smart monkey carries a yellow peel.", "Label monkey, carries, smart, and yellow.", "Monkey is a noun, carries is a verb, and smart and yellow are adjectives.", [evidence("Labels monkey and carries.", "monkey is a noun", "carries is a verb"), evidence("Labels both adjectives.", "smart", "yellow")]),
        ],
        "independent": _open_set([
            ("A clean path welcomes careful walkers.", "Classify path, welcomes, clean, and careful.", "Path is a noun, welcomes is a verb, and clean and careful are adjectives.", [evidence("Labels path and welcomes.", "path is a noun", "welcomes is a verb"), evidence("Labels clean and careful.", "clean", "careful")]),
            ("The ashamed visitor retrieves the crumpled packet.", "Identify the action and both describing words.", "Retrieves is the action, while ashamed and crumpled are describing words.", [evidence("Names retrieves as action.", "retrieves is the action", "retrieves is a verb"), evidence("Names ashamed and crumpled.", "ashamed", "crumpled")]),
        ]),
        "transfer": _open_set([
            ("A blue tray stores reusable paper.", "Label blue, tray, stores, and reusable.", "Blue and reusable are adjectives, tray is a noun, and stores is a verb.", [evidence("Labels both adjectives.", "blue", "reusable"), evidence("Labels tray and stores.", "tray is a noun", "stores is a verb")]),
            ("The alert monitor marks a slippery floor.", "Transfer the word-job check to alert, monitor, and marks.", "Alert is an adjective, monitor is a noun, and marks is a verb.", [evidence("Classifies all three requested words.", "alert is an adjective", "monitor is a noun", "marks is a verb")]),
        ]),
        "review": _open_set([
            ("Two empty cups block the narrow step.", "Name the action and both describing words.", "Block is the action, and empty and narrow are describing words.", [evidence("Names block as action.", "block is the action", "block is a verb"), evidence("Names empty and narrow.", "empty", "narrow")]),
            ("The green bin receives clean bottles.", "Classify bin, receives, green, and clean.", "Bin is a noun, receives is a verb, and green and clean are adjectives.", [evidence("Labels noun and verb.", "bin is a noun", "receives is a verb"), evidence("Labels green and clean.", "green", "clean")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:cleanup_word_job_confusion",
        "misconception": "The learner calls every cleaning word an action or confuses a condition such as empty with the item it describes.",
        "remediation": "Use what, happens, and what kind tests on the complete sentence; point to each answer before applying noun, verb, or adjective.",
        "support": _open_set([
            ("The brown wrapper falls.", "Label brown, wrapper, and falls.", "Brown is an adjective, wrapper is a noun, and falls is a verb.", [evidence("Labels all three jobs.", "brown is an adjective", "wrapper is a noun", "falls is a verb")]),
            ("A tidy reading room shines.", "Which word describes the room, and which word tells what happens?", "Tidy describes the room, and shines shows the action.", [evidence("Distinguishes tidy and shines.", "tidy describes", "shines shows")]),
            ("Helpful Mina empties the bin.", "Classify helpful, Mina, and empties.", "Helpful is an adjective, Mina is a noun, and empties is a verb.", [evidence("Classifies all requested words.", "helpful is an adjective", "Mina is a noun", "empties is a verb")]),
            ("The full basket tips.", "Explain why full is not the action.", "Full describes the basket, while tips is the action.", [evidence("Contrasts description and action.", "full describes", "tips is the action")]),
            ("Responsible Arjun clears litter.", "Label responsible, Arjun, and clears.", "Responsible is an adjective, Arjun is a noun, and clears is a verb.", [evidence("Labels all three words.", "responsible is an adjective", "Arjun is a noun", "clears is a verb")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:cleanup_sentence_builder",
        "title": "Arrange clean-up sentences",
        "focus": "order visible words and punctuate clean-place statements and questions",
        "outcome": "Build a complete clean-up sentence from every supplied word and finish it with the correct written boundaries.",
        "skill_ids": [S["sentence_order"], S["punctuation"]],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:write:6", f"{CHAPTER_ID}:speak:4"],
        "principle": "Find who or what, place the clean-up action, add the remaining detail, and check capital plus end mark.",
        "connect": {
            "teaching_block": "A responsibility message needs clear order and complete punctuation so the action cannot be misunderstood.",
            "passage": "Word set: bin / the / wrapper / in / put / the. Finished form: Put the wrapper in the bin.",
            "prompt": "Notice the command order, capital P, and full stop.",
        },
        "co": choice_task("Word set: monkey / dustbin / uses / the / the", "Which option builds the complete cleanup statement?", "The monkey uses the dustbin.", ["The dustbin monkey the uses.", "the Monkey uses dustbin the"]),
        "guided": [
            choice_task("Word set: where / nearest / is / bin / the", "Which option forms a complete question?", "Where is the nearest bin?", ["Where the nearest bin is.", "where is bin nearest the?"]),
            open_task("Word set: litter / path / remove / the / from / please", "Arrange every word as a polite command.", "Please remove the litter from the path.", [evidence("Uses complete command order.", "please remove the litter from the path"), evidence("Adds capital and full stop.", "Please", ".")]),
        ],
        "independent": _open_set([
            ("Word set: bottle / empty / pick / the / up", "Build the complete clean-up command.", "Pick up the empty bottle.", [evidence("Uses every word in correct order.", "pick up the empty bottle"), evidence("Adds capital and full stop.", "Pick", ".")]),
            ("Word set: cups / who / sorted / the", "Build and punctuate the question.", "Who sorted the cups?", [evidence("Uses the supplied question order.", "who sorted the cups"), evidence("Adds capital and question mark.", "Who", "?")]),
        ]),
        "transfer": _open_set([
            ("Word set: paper / tray / reusable / the / place / in", "Transfer the ordering steps to a reuse instruction.", "Place the reusable paper in the tray.", [evidence("Uses all words in clear order.", "place the reusable paper in the tray"), evidence("Adds command boundaries.", "Place", ".")]),
            ("Word set: floor / why / wet / the / is", "Arrange the complete safety question.", "Why is the floor wet?", [evidence("Uses correct question order.", "why is the floor wet"), evidence("Adds capital and question mark.", "Why", "?")]),
        ]),
        "review": _open_set([
            ("Unfinished line: responsible visitors clear their table", "Repair the statement boundaries.", "Responsible visitors clear their table.", [evidence("Keeps the complete statement.", "responsible visitors clear their table"), evidence("Adds capital and full stop.", "Responsible", ".")]),
            ("Jumbled line: dustbin / is / nearby / a / there", "Write the ordered statement with correct punctuation.", "There is a dustbin nearby.", [evidence("Uses correct statement order.", "there is a dustbin nearby"), evidence("Adds capital and full stop.", "There", ".")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:cleanup_sentence_boundary",
        "misconception": "The learner leaves the action after the place phrase, drops a small supplied word, or uses a full stop for a direct question.",
        "remediation": "Box the person or item, underline the action, attach place details, and run a final purpose check for statement, command, or question punctuation.",
        "support": _open_set([
            ("Word set: peel / the / bin / in / goes / the", "Build and finish the statement.", "The peel goes in the bin.", [evidence("Builds and punctuates the statement.", "peel goes in the bin", "The", ".")]),
            ("Word set: wrapper / whose / is / this", "Build the ownership question.", "Whose wrapper is this?", [evidence("Builds and punctuates the question.", "whose wrapper is this", "Whose", "?")]),
            ("Line needing repair: keep the classroom clean", "Add complete command boundaries.", "Keep the classroom clean.", [evidence("Adds capital and full stop.", "Keep the classroom clean", ".")]),
            ("Word set: sorts / paper / she / dry", "Arrange the clean-up statement.", "She sorts dry paper.", [evidence("Uses every word in order.", "she sorts dry paper", "She", ".")]),
            ("Line needing repair: where should this bottle go", "Repair the bottle-sorting question and its end mark.", "Where should this bottle go?", [evidence("Adds capital and question mark.", "Where should this bottle go", "?")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:responsible_message_writer",
        "title": "Write a responsible clean-place message",
        "focus": "construct complete reminders and action explanations from visible problems",
        "outcome": "Write a respectful complete sentence that identifies a clean-place problem and gives a specific safe action or reason.",
        "skill_ids": [S["comprehension"], S["sentence"]],
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:speak:4", f"{CHAPTER_ID}:write:6"],
        "principle": "A useful reminder names the visible problem, gives a doable action, and stays respectful rather than blaming a person.",
        "connect": {
            "teaching_block": "A shared-place message works when the reader can see exactly what needs attention and what safe action to take.",
            "passage": "Visible problem: two cups block the classroom doorway. Available action: place them in the wash tray.",
            "prompt": "Notice that the reminder can name the cups and the wash tray without accusing anyone.",
        },
        "co": choice_task("Visible problem: a wrapper lies on a stair. Available action: move it to the dry-waste bin.", "Which message is clear and respectful?", "Please move the wrapper from the stair to the dry-waste bin.", ["Someone here is always careless.", "The stair should clean itself."], skills=[S["comprehension"]]),
        "guided": _open_set([
            ("Visible problem: water has spilled beside the sink. Safe actions: tell an adult and keep others away.", "Write one complete safety reminder using both actions.", "Please tell an adult about the spill and keep others away from the wet floor.", [evidence("Names the spill and adult help.", "tell an adult", "spill"), evidence("Includes keeping others away.", "keep others away", "wet floor")]),
            ("Visible problem: clean paper is mixed with food scraps. Available action: separate paper into the blue tray.", "Create a respectful sorting message.", "Please separate the clean paper from the food scraps and place it in the blue tray.", [evidence("Names separation from food scraps.", "separate the clean paper", "food scraps"), evidence("Names the blue tray destination.", "blue tray")]),
        ]),
        "independent": _open_set([
            ("Visible problem: three empty bottles remain under a park bench. Nearby option: a marked recycling bin.", "Write a complete action message and include why the path should stay clear.", "Please place the empty bottles in the recycling bin so the path stays clear and safe.", [evidence("Names bottles and recycling bin.", "empty bottles", "recycling bin"), evidence("Includes clear or safe path reason.", "path stays clear", "safe")]),
            ("Visible problem: fruit peels are beside the play area. Safe action: use the food-waste container before someone slips.", "Compose a responsible reminder with the safety reason.", "Please put the fruit peels in the food-waste container before someone slips.", [evidence("Names peels and correct container.", "fruit peels", "food-waste container"), evidence("Includes slipping risk.", "before someone slips", "slip")]),
        ]),
        "transfer": _open_set([
            ("Visible problem: paint brushes are drying on a walkway. Available place: the labelled art rack.", "Transfer the reminder pattern to the art room.", "Please move the drying brushes from the walkway to the labelled art rack.", [evidence("Names brushes and walkway.", "drying brushes", "walkway"), evidence("Names the labelled art rack.", "labelled art rack")]),
            ("Visible problem: a library book lies open near a window where rain may enter. Action: close it and return it to the trolley.", "Write a careful two-action message.", "Please close the open book and return it to the trolley before rain reaches it.", [evidence("Includes closing the book.", "close the open book"), evidence("Includes trolley and rain reason.", "return it to the trolley", "before rain")]),
        ]),
        "review": _open_set([
            ("Visible problem: the class bin is full. Available action: inform the caretaker instead of adding more waste.", "Write one complete responsible response.", "The bin is full, so please inform the caretaker before adding more waste.", [evidence("States that the bin is full.", "bin is full"), evidence("Gives caretaker action before more waste.", "inform the caretaker", "before adding")]),
            ("Visible problem: loose paper may blow from the balcony. Available action: stack it in a covered tray.", "Create a clear prevention message.", "Please stack the loose paper in the covered tray so it cannot blow from the balcony.", [evidence("Names loose paper and covered tray.", "loose paper", "covered tray"), evidence("Includes the blowing prevention reason.", "cannot blow", "from the balcony")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:vague_or_blaming_reminder",
        "misconception": "The learner writes a vague slogan, blames an unnamed person, omits the visible problem, or suggests an unsafe action.",
        "remediation": "Circle the stated problem, choose one available safe action, name its destination, and frame the complete sentence with please or a neutral reason.",
        "support": _open_set([
            ("Problem: one cup is on the floor. Action: use the wash tray.", "Write the complete respectful reminder.", "Please place the cup from the floor in the wash tray.", [evidence("Names cup, floor, and wash tray.", "cup", "floor", "wash tray")]),
            ("Problem: paper covers a desk. Action: sort reusable sheets.", "Write a specific clean-up sentence.", "Please sort the reusable sheets and clear them from the desk.", [evidence("Names reusable sheets and desk clearing.", "reusable sheets", "clear", "desk")]),
            ("Problem: a peel is near the stairs. Action: use the food bin.", "Create the safe reminder.", "Please move the peel away from the stairs and into the food bin.", [evidence("Names stairs and food bin action.", "away from the stairs", "food bin")]),
            ("Problem: the recycling bin is full. Action: tell the monitor.", "Write a complete response without adding waste.", "The recycling bin is full, so please tell the monitor before adding anything.", [evidence("States full bin and monitor action.", "bin is full", "tell the monitor")]),
            ("Problem: chalk dust remains on the shared ledge. Action: ask an adult for the proper cloth.", "Write the respectful request.", "Please ask an adult for the proper cloth to clean the shared ledge.", [evidence("Includes adult, cloth, and ledge.", "ask an adult", "proper cloth", "shared ledge")]),
        ]),
    },
]


EXTRA_DEPTH = {
    f"{CHAPTER_ID}:litter_cleanup_chain": {
        "guided": [
            choice_task(
                "A wrapper lands near the tap. Dev sees the monitor place paper in a dry-waste bin, so he carries the wrapper to the same bin.",
                "Which event changes Dev's decision?",
                "He sees the monitor sort paper.",
                ["The wrapper lands near the tap.", "The tap becomes a bin."],
            ),
            open_task(
                "A visitor leaves an empty carton on a bench. She watches two pupils flatten boxes for recycling and then adds her carton to their stack.",
                "Retell the mistake, example, and corrected action in order.",
                "The visitor leaves the carton, sees the pupils flatten boxes, and then flattens and stacks her carton for recycling.",
                [
                    evidence("States the first mistake.", "leaves the carton", "carton is left on the bench"),
                    evidence("States the visible example.", "pupils flatten boxes", "sees boxes being flattened"),
                    evidence("States the corrected action.", "flattens and stacks her carton", "adds a flattened carton to the recycling stack"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set([
            (
                "A boy drops a straw beside the court. He notices a younger child carry loose straws to the marked container, then picks up his own straw and follows.",
                "Explain the full action change and the example that causes it.",
                "The boy drops a straw, sees the younger child use the marked container, and then picks up and sorts his own straw.",
                [
                    evidence("States the first action.", "drops a straw", "straw is dropped beside the court"),
                    evidence("States the example.", "younger child uses the marked container", "sees the child carry straws"),
                    evidence("States the repair.", "picks up and sorts his own straw", "puts his straw in the container"),
                ],
            ),
            (
                "A snack packet blows toward a drain. Rupa sees a gardener stop another packet with a broom, so she blocks hers with her shoe and asks for a litter picker.",
                "Sequence Rupa's safe response and name the model she follows.",
                "Rupa sees the gardener stop litter, blocks her packet before the drain, and asks for a litter picker.",
                [
                    evidence("Names the model.", "gardener stops litter", "sees the gardener stop a packet"),
                    evidence("States the quick response.", "blocks her packet before the drain", "stops the packet with her shoe"),
                    evidence("States the safe tool request.", "asks for a litter picker", "requests the litter picker"),
                ],
            ),
        ], ordered=True),
        "transfer": _open_set([
            (
                "In an art room, paint water is beside the sink. A learner sees the teacher pour used paint water into the labelled collection tub, then follows with her own cup.",
                "Transfer example-and-repair thinking to this art-room routine.",
                "The learner sees the teacher use the labelled tub and then safely pours her own used paint water into it.",
                [
                    evidence("States the model action.", "teacher uses the labelled tub", "teacher pours paint water into the tub"),
                    evidence("States the learner's response.", "pours her own paint water into it", "follows with her cup"),
                    evidence("Keeps the action safe.", "safely pours", "uses the labelled collection tub"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:clean_place_words": {
        "guided": [
            choice_task(
                "The floor is cluttered because scattered bags and books leave little room to walk.",
                "Which meaning fits cluttered?",
                "covered with many untidy things",
                ["washed with clean water", "marked with one straight line"],
            ),
            open_task(
                "The path is accessible because its wide, clear surface lets everyone reach the gate easily.",
                "Explain accessible and use it in a different shared-place sentence.",
                "Accessible means easy to reach or use. A clear ramp makes the library accessible.",
                [
                    evidence("Explains accessible.", "easy to reach or use", "people can reach it easily"),
                    evidence("Uses accessible freshly.", "clear ramp makes the library accessible", "library is easy to reach by the ramp"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "The caretaker sanitises the shared handles, cleaning them carefully to reduce germs.",
                "Infer sanitises and create a different accurate use.",
                "Sanitises means cleans to reduce germs. An adult sanitises the lunch tables after use.",
                [
                    evidence("Explains sanitises.", "cleans to reduce germs", "removes many germs by cleaning"),
                    evidence("Uses sanitises in context.", "adult sanitises the lunch tables", "lunch tables are cleaned for germs"),
                ],
            ),
            (
                "The bottles are reusable because they can be cleaned and used again instead of being thrown away.",
                "Explain reusable and use it with a new classroom item.",
                "Reusable means able to be used again. This sturdy folder is reusable next term.",
                [
                    evidence("Explains reusable.", "able to be used again", "can be cleaned and used another time"),
                    evidence("Uses reusable freshly.", "sturdy folder is reusable", "folder can be used next term"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "A workshop tool is misplaced when it is left on the paint table instead of its labelled drawer.",
                "Infer misplaced and use the word in a clean-up message.",
                "Misplaced means left in the wrong place. Please return the misplaced brush to its labelled drawer.",
                [
                    evidence("Explains misplaced.", "left in the wrong place", "not put in its proper place"),
                    evidence("Uses misplaced accurately.", "misplaced brush to its labelled drawer", "return the brush to the proper drawer"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:visible_cleanup_spellings": {
        "guided": [
            choice_task(
                "Candidates: recycle, recycel, resycle. The poster needs the word for processing material for another use.",
                "Which spelling is standard?",
                "recycle",
                ["recycel", "resycle"],
            ),
            open_task(
                "Printed chunks: lit + ter. The clue names waste left in the wrong place.",
                "Join the chunks and use the word in a clear sentence.",
                "The word is litter. Loose litter can block the rain drain.",
                [
                    evidence("Builds the spelling.", "word is litter", "spell it litter"),
                    evidence("Uses litter accurately.", "loose litter can block the drain", "litter lies in the wrong place"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Missing letters: c o n t a i n _ r. The clue names something that holds sorted waste.",
                "Complete the word and use it in a clean-up sentence.",
                "The word is container. The marked container holds clean paper scraps.",
                [
                    evidence("Completes the spelling.", "word is container", "spell it container"),
                    evidence("Uses container accurately.", "marked container holds paper scraps", "paper goes in the container"),
                ],
            ),
            (
                "Scrambled letters: s w e e p. The clue names an action done with a broom.",
                "Unscramble the action word and use it with a place.",
                "The word is sweep. We sweep the dry leaves from the path.",
                [
                    evidence("Unscrambles the word.", "word is sweep", "spell it sweep"),
                    evidence("Uses sweep meaningfully.", "sweep the dry leaves from the path", "use a broom to sweep the path"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Base word: use. Add re at the front to mean use another time.",
                "Build the new word and write a practical sentence.",
                "The new word is reuse. We reuse one-sided paper for rough drawings.",
                [
                    evidence("Builds the new spelling.", "new word is reuse", "spell it reuse"),
                    evidence("Uses reuse in context.", "reuse one-sided paper", "use the paper again for drawings"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:cleanup_word_jobs": {
        "guided": [
            choice_task(
                "The careful monitor empties the full tray.",
                "Which word shows the monitor's action?",
                "empties",
                ["careful", "tray"],
            ),
            open_task(
                "A blue cart carries heavy boxes.",
                "Classify cart, carries, blue, and heavy.",
                "Cart is a noun, carries is a verb, and blue and heavy are adjectives.",
                [
                    evidence("Labels cart.", "cart is a noun", "cart names a thing"),
                    evidence("Labels carries.", "carries is a verb", "carries shows action"),
                    evidence("Labels blue.", "blue is an adjective", "blue describes the cart"),
                    evidence("Labels heavy.", "heavy is an adjective", "heavy describes the boxes"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Responsible pupils sort dry wrappers.",
                "Give the jobs of pupils, sort, responsible, and dry.",
                "Pupils is a noun, sort is a verb, and responsible and dry are adjectives.",
                [
                    evidence("Labels pupils.", "pupils is a noun", "pupils name people"),
                    evidence("Labels sort.", "sort is a verb", "sort shows action"),
                    evidence("Labels responsible.", "responsible is an adjective", "responsible describes pupils"),
                    evidence("Labels dry.", "dry is an adjective", "dry describes wrappers"),
                ],
            ),
            (
                "The small brush reaches narrow corners.",
                "Classify brush, reaches, small, and narrow.",
                "Brush is a noun, reaches is a verb, and small and narrow are adjectives.",
                [
                    evidence("Labels brush.", "brush is a noun", "brush names a thing"),
                    evidence("Labels reaches.", "reaches is a verb", "reaches shows action"),
                    evidence("Labels small.", "small is an adjective", "small describes the brush"),
                    evidence("Labels narrow.", "narrow is an adjective", "narrow describes corners"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "An alert cook wipes the wet counter.",
                "Transfer the word-job check to cook, wipes, alert, and wet.",
                "Cook is a noun, wipes is a verb, and alert and wet are adjectives.",
                [
                    evidence("Labels cook.", "cook is a noun", "cook names a person"),
                    evidence("Labels wipes.", "wipes is a verb", "wipes shows action"),
                    evidence("Labels alert.", "alert is an adjective", "alert describes the cook"),
                    evidence("Labels wet.", "wet is an adjective", "wet describes the counter"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:cleanup_sentence_builder": {
        "guided": [
            choice_task(
                "Word set: bottles / rinse / the / first / please",
                "Which option forms a complete clean-up request?",
                "Please rinse the bottles first.",
                ["Bottles the first please rinse.", "please Rinse first bottles the"],
            ),
            open_task(
                "Word set: paper / where / clean / does / go",
                "Arrange the words as a finished question.",
                "Where does clean paper go?",
                [
                    evidence("Uses the question order.", "where does clean paper go", "ask where clean paper goes"),
                    evidence("Uses a natural question ending.", "paper go?", "clean paper go?"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Word set: tray / place / cups / wash / the / in / the",
                "Turn the word set into a clear wash-tray direction.",
                "Place the cups in the wash tray.",
                [
                    evidence("Uses every word in order.", "place the cups in the wash tray", "cups go in the wash tray"),
                    evidence("Uses a natural statement ending.", "wash tray.", "the wash tray."),
                ],
            ),
            (
                "Line needing repair: is this carton ready for recycling",
                "Add the correct beginning and end mark.",
                "Is this carton ready for recycling?",
                [
                    evidence("Keeps the complete question.", "is this carton ready for recycling", "ask if the carton is ready"),
                    evidence("Uses a natural question ending.", "for recycling?", "ready for recycling?"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Word set: brushes / return / art / please / the / shelf / to / the",
                "Transfer the sentence pattern to an art-room request.",
                "Please return the brushes to the art shelf.",
                [
                    evidence("Uses the polite request order.", "please return the brushes to the art shelf", "return the brushes to the art shelf please"),
                    evidence("Uses a natural statement ending.", "art shelf.", "the art shelf."),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:responsible_message_writer": {
        "guided": [
            choice_task(
                "Problem card: Wet leaves make the steps slippery. Safe action: tell an adult and keep people away until the steps are cleared.",
                "Which message uses the visible problem and safe action?",
                "Please tell an adult about the wet leaves and stay off the steps.",
                ["Run over the leaves to crush them.", "Someone should clean everything somehow."],
                skills=[S["comprehension"]],
            ),
            open_task(
                "Problem card: A cracked jar is beside the sorting table. Safe action: do not touch it; ask the teacher to move it.",
                "Write one respectful warning with the problem and action.",
                "Please do not touch the cracked jar; ask the teacher to move it safely.",
                [
                    evidence("Names the danger.", "cracked jar", "jar is cracked"),
                    evidence("States what to avoid.", "do not touch", "keep hands away"),
                    evidence("Gives the safe action.", "ask the teacher to move it", "teacher should move it safely"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Problem card: Used tissues are on a desk. Safe action: tell an adult and use the covered waste container; do not sort them by hand.",
                "Create a specific, safe clean-up message.",
                "Please tell an adult about the used tissues and put them in the covered container without sorting them by hand.",
                [
                    evidence("Names the problem.", "used tissues are on a desk", "used tissues on the desk"),
                    evidence("Includes adult help.", "tell an adult", "ask an adult for help"),
                    evidence("Names the safe container.", "covered container", "covered waste container"),
                    evidence("Avoids hand sorting.", "without sorting them by hand", "do not handle them for sorting"),
                ],
            ),
            (
                "Problem card: A pile of books blocks the fire exit. Safe action: ask the librarian where to move them and keep the exit clear.",
                "Write a respectful message that includes the reason.",
                "Please ask the librarian where to move the books so the fire exit stays clear.",
                [
                    evidence("Names the blocking problem.", "books block the fire exit", "pile is by the fire exit"),
                    evidence("Names the helper.", "ask the librarian", "librarian gives the safe place"),
                    evidence("States the reason.", "fire exit stays clear", "keep the exit clear"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Problem card: A charging cable crosses the computer-room walkway. Safe action: stop before it and alert the teacher; pupils must not unplug it.",
                "Transfer responsible-message writing to this new safety problem.",
                "Please stop before the cable and alert the teacher because pupils should not unplug it themselves.",
                [
                    evidence("Names the walkway danger.", "cable crosses the walkway", "charging cable is in the path"),
                    evidence("Gives the immediate action.", "stop before the cable", "do not step over the cable"),
                    evidence("Names teacher help.", "alert the teacher", "tell the teacher"),
                    evidence("States the limit.", "pupils should not unplug it", "do not unplug it yourself"),
                ],
            )
        ]),
    },
}

LAUNCH_DEPTH = {
    f"{CHAPTER_ID}:litter_cleanup_chain": {
        "transfer": _open_set(
            [
                (
                    "After craft time, the team gathers paper strips, removes the pieces with wet glue, sorts clean paper into the blue box, and wipes the table.",
                    "Sequence the clean-up from gathering to the final wipe.",
                    "The team gathers the strips, removes sticky pieces, sorts clean paper into the blue box, and finally wipes the table.",
                    [
                        evidence("States the gathering step.", "gathers the strips", "gathers paper strips"),
                        evidence("States the sticky-paper step.", "removes sticky pieces", "pieces with wet glue"),
                        evidence("States the sorting step.", "sorts clean paper into the blue box", "blue box"),
                        evidence("States the final wipe.", "finally wipes the table", "wipes the table"),
                    ],
                )
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "Wind scatters snack wrappers near the court. Iqra asks players to pause, collects the wrappers with tongs, puts them in the dry-waste bin, and washes her hands.",
                    "Retell Iqra's safe response in order.",
                    "Iqra pauses the players, collects wrappers with tongs, uses the dry-waste bin, and then washes her hands.",
                    [
                        evidence("States the pause.", "pauses the players", "asks players to pause"),
                        evidence("States the safe collection.", "collects wrappers with tongs", "with tongs"),
                        evidence("States the correct bin.", "uses the dry-waste bin", "dry-waste bin"),
                        evidence("States the final hygiene step.", "washes her hands", "then washes"),
                    ],
                ),
                (
                    "At the reading corner, Dev stacks returned books, places torn bookmarks in the repair tray, and carries an empty cup to the wash area.",
                    "Explain the three tidy actions from first to last.",
                    "Dev stacks the books, puts torn bookmarks in the repair tray, and takes the empty cup to the wash area.",
                    [
                        evidence("States the book action.", "stacks the books", "stacks returned books"),
                        evidence("States the repair sorting.", "torn bookmarks in the repair tray", "repair tray"),
                        evidence("States the cup action.", "takes the empty cup to the wash area", "wash area"),
                    ],
                ),
            ],
            ordered=True,
        ),
    },
    f"{CHAPTER_ID}:clean_place_words": {
        "transfer": _open_set(
            [
                (
                    "To recycle a clean glass jar means to process it so its material can become something useful again.",
                    "Explain recycle and use it in a school sentence.",
                    "Recycle means make used material useful again. Our class sends clean paper to a centre that can recycle it.",
                    [
                        evidence("Explains recycle.", "make used material useful again", "Recycle means"),
                        evidence("Uses recycle accurately.", "centre that can recycle it", "recycle clean paper"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Vegetable peels can become compost, a dark soil-like material made when food scraps break down.",
                    "State what compost means and write one garden use.",
                    "Compost is soil-like material made from broken-down food scraps. We add compost around the tomato plants.",
                    [
                        evidence("Explains compost.", "soil-like material made from broken-down food scraps", "food scraps break down"),
                        evidence("Uses compost in a garden.", "add compost around the tomato plants", "compost around"),
                    ],
                ),
                (
                    "A reusable bottle can be washed and used many times instead of being thrown away after one drink.",
                    "Explain reusable and use it for another object.",
                    "Reusable means able to be used many times. I carry lunch in a reusable steel box.",
                    [
                        evidence("Explains reusable.", "able to be used many times", "used many times"),
                        evidence("Uses reusable freshly.", "reusable steel box", "lunch in a reusable"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:visible_cleanup_spellings": {
        "transfer": _open_set(
            [
                (
                    "Visible parts: dust + bin. The clue names a container for small dry rubbish.",
                    "Join the parts and use the word in a complete sentence.",
                    "The word is dustbin. Rohan puts the dry wrapper in the green dustbin.",
                    [
                        evidence("Builds the joined spelling.", "word is dustbin", "spell it dustbin"),
                        evidence("Uses dustbin accurately.", "dry wrapper in the green dustbin", "green dustbin"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Base word: use. Add re before it and able after it to form the word for something used again.",
                    "Build the complete word and write a lunch sentence.",
                    "The word is reusable. My reusable spoon returns home in the lunch bag.",
                    [
                        evidence("Spells the built word.", "word is reusable", "spell it reusable"),
                        evidence("Uses reusable in context.", "reusable spoon returns home in the lunch bag", "reusable spoon"),
                    ],
                ),
                (
                    "Candidates: rubbish, rubish, rubbiss. The notice needs the standard word for unwanted waste.",
                    "Choose the standard spelling and use it in a tidy-place sentence.",
                    "The standard spelling is rubbish. We remove rubbish from the path before visitors arrive.",
                    [
                        evidence("Gives the standard spelling.", "standard spelling is rubbish", "spell it rubbish"),
                        evidence("Uses rubbish accurately.", "remove rubbish from the path", "rubbish from the path"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:cleanup_word_jobs": {
        "transfer": _open_set(
            [
                (
                    "The careful monitor empties a full basket.",
                    "Classify monitor, empties, careful, and full.",
                    "Monitor is a noun, empties is a verb, and careful and full are adjectives.",
                    [
                        evidence("Labels monitor.", "Monitor is a noun", "monitor names a person"),
                        evidence("Labels empties.", "empties is a verb", "empties shows action"),
                        evidence("Labels careful.", "careful is an adjective", "careful describes the monitor"),
                        evidence("Labels full.", "full is an adjective", "full describes the basket"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "A responsible neighbour cleans the shared staircase.",
                    "Give the jobs of neighbour, cleans, responsible, and shared.",
                    "Neighbour is a noun, cleans is a verb, and responsible and shared are adjectives.",
                    [
                        evidence("Labels neighbour.", "Neighbour is a noun", "neighbour names a person"),
                        evidence("Labels cleans.", "cleans is a verb", "cleans shows action"),
                        evidence("Labels responsible.", "responsible is an adjective", "responsible describes the neighbour"),
                        evidence("Labels shared.", "shared is an adjective", "shared describes the staircase"),
                    ],
                ),
                (
                    "The young gardener fills a brown compost pot.",
                    "Name the noun, verb, and two adjectives in this sentence.",
                    "Gardener is a noun, fills is a verb, and young and brown are adjectives.",
                    [
                        evidence("Labels gardener.", "Gardener is a noun", "gardener names a person"),
                        evidence("Labels fills.", "fills is a verb", "fills shows action"),
                        evidence("Labels young.", "young is an adjective", "young describes the gardener"),
                        evidence("Labels brown.", "brown is an adjective", "brown describes the pot"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:cleanup_sentence_builder": {
        "transfer": _open_set(
            [
                (
                    "Word set: after lunch / the helpers / wipe / every table",
                    "Order the helpers, action, object, and time into one clean-up statement.",
                    "The helpers wipe every table after lunch.",
                    [
                        evidence("Uses natural subject-action order.", "helpers wipe every table", "The helpers wipe"),
                        evidence("Keeps the time phrase.", "after lunch", "table after lunch"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Unfinished question: where should this banana peel go",
                    "Add the capital beginning and correct end mark.",
                    "Where should this banana peel go?",
                    [
                        evidence("Uses the capital opening.", "Where should", "Where"),
                        evidence("Uses the question ending.", "banana peel go?", "peel go?"),
                    ],
                ),
                (
                    "Word set: beside the gate / two volunteers / place / a labelled bin",
                    "Build one correctly ordered clean-up sentence.",
                    "Two volunteers place a labelled bin beside the gate.",
                    [
                        evidence("Orders the people and action.", "Two volunteers place a labelled bin", "volunteers place"),
                        evidence("Keeps the location.", "beside the gate", "bin beside the gate"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:responsible_message_writer": {
        "transfer": _open_set(
            [
                (
                    "Park notice facts: dry wrappers go in the blue bin; fruit peels go in the compost tub; both containers stand near the exit.",
                    "Write two clear visitor sentences using every fact.",
                    "Please put dry wrappers in the blue bin and fruit peels in the compost tub. Both containers are near the park exit.",
                    [
                        evidence("Gives the wrapper instruction.", "dry wrappers in the blue bin", "blue bin"),
                        evidence("Gives the peel instruction.", "fruit peels in the compost tub", "compost tub"),
                        evidence("Gives the shared location.", "Both containers are near the park exit", "near the park exit"),
                    ],
                )
            ],
            interaction="paragraph_text",
        ),
        "review": _open_set(
            [
                (
                    "The water station has one refill tap and a tray for reusable bottles. Disposable cups are not provided.",
                    "Write a kind message telling visitors what to do and why.",
                    "Please bring a reusable bottle and refill it at the tap so the station creates less cup waste.",
                    [
                        evidence("Gives the bottle action.", "bring a reusable bottle", "reusable bottle"),
                        evidence("Gives the refill place.", "refill it at the tap", "refill tap"),
                        evidence("Explains the waste benefit.", "creates less cup waste", "less cup waste"),
                    ],
                ),
                (
                    "After a school fair, clean paper flags can be stored for next year. Torn paper can go for recycling, and wet food scraps belong in compost.",
                    "Create a two-sentence sorting message with all three actions.",
                    "Save the clean paper flags for next year's fair and send torn paper for recycling. Put wet food scraps in the compost container.",
                    [
                        evidence("Gives the reuse action.", "Save the clean paper flags for next year's fair", "clean paper flags"),
                        evidence("Gives the recycling action.", "send torn paper for recycling", "torn paper"),
                        evidence("Gives the compost action.", "wet food scraps in the compost container", "food scraps"),
                    ],
                ),
            ],
            interaction="paragraph_text",
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
            choice_task("The path is obstructed because a carton blocks the way.", "Which meaning fits obstructed?", "blocked", ["freshly painted", "carefully swept"], skills=[S["word_context"]]),
            choice_task("Ravi sorts paper while Leela carries bottles. Only Leela uses the green bin.", "Who uses the green bin?", "Leela", ["Ravi", "both children"], skills=[S["comprehension"]]),
            choice_task("First the cup tips, next water spills, and last Mina marks the wet floor.", "Which event happens second?", "Water spills.", ["The cup tips.", "Mina marks the floor."], skills=[S["sequence"]]),
            choice_task("Sentence frame: Please ___ the wrapper in the dry-waste bin.", "Which clean-up word fits the action?", "place", ["admire", "forget"], skills=[S["word_use"]]),
            choice_task("Candidates: dustbin, dustben, dusbin. The sentence names a waste container.", "Which spelling is standard?", "dustbin", ["dustben", "dusbin"], skills=[S["spelling"]]),
            choice_task("The responsible child clears the table.", "Which word shows the action?", "clears", ["responsible", "child"], skills=[S["word_jobs"]]),
            open_task("Word set: carry / the / empty bottle / to / the / recycling box", "Arrange the complete command.", "Carry the empty bottle to the recycling box.", [evidence("Uses correct complete order.", "carry the empty bottle", "to the recycling box"), evidence("Uses every supplied word.", "empty bottle", "recycling box")], skills=[S["sentence_order"]]),
            open_task("Unfinished question: where is the recycling bin", "Add the correct sentence boundaries.", "Where is the recycling bin?", [evidence("Uses a capital beginning.", "Where"), evidence("Uses a question mark.", "?")], skills=[S["punctuation"]]),
            open_task("Problem: a bottle blocks the gate. Action: move it to the marked bin.", "Write one complete respectful reminder.", "Please move the bottle from the gate to the marked bin.", [evidence("Names bottle and gate.", "bottle", "gate"), evidence("Names the marked-bin action.", "marked bin", "move")], skills=[S["sentence"]]),
            open_task("A visitor drops a cup, sees a child sort paper, and then picks up and sorts the cup.", "Retell the chain and identify the example that changes the action.", "The visitor drops the cup, sees the child's paper sorting, and then repairs the mistake by sorting the cup.", [evidence("Orders dropping before seeing.", "drops the cup", "sees"), evidence("Links the child's sorting to repair.", "paper sorting", "sorting the cup")], skills=[S["comprehension"], S["sequence"]], ordered=True),
            open_task("Spotless means completely clean. Use spotless with a correctly spelled clean-place word.", "State the meaning and create the new use.", "Spotless means completely clean. The classroom floor looked spotless after sweeping.", [evidence("Explains completely clean.", "completely clean"), evidence("Uses classroom and spotless accurately.", "classroom floor", "spotless")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
            open_task("Word set: who / put / the / empty / bottle / in / the / bin", "Build and punctuate the complete question.", "Who put the empty bottle in the bin?", [evidence("Uses supplied question order.", "who put the empty bottle in the bin"), evidence("Uses capital and question mark.", "Who", "?")], skills=[S["sentence_order"], S["punctuation"]]),
        ]
    return [
        choice_task("The visitor is remorseful, feeling sorry after leaving litter behind.", "Which meaning fits remorseful?", "feeling sorry for a wrong action", ["proud of a mess", "unable to see waste"], skills=[S["word_context"]]),
        choice_task("A monkey bins a peel while a child retrieves a wrapper. The child carries the wrapper to the blue bin.", "Who uses the blue bin?", "the child", ["the monkey", "both"], skills=[S["comprehension"]]),
        choice_task("A wrapper blows from a bench, crosses the path, and stops beside a drain.", "What happens immediately before it stops?", "It crosses the path.", ["It blows from the bench.", "It enters the dustbin."], skills=[S["sequence"]]),
        choice_task("Sentence frame: We ___ clean paper from food waste.", "Which chapter word fits sorting into groups?", "separate", ["decorate", "forget"], skills=[S["word_use"]]),
        choice_task("Candidates: wrapper, wraper, wrappur. The sentence names snack packaging.", "Which spelling is standard?", "wrapper", ["wraper", "wrappur"], skills=[S["spelling"]]),
        choice_task("The empty bottle rolls away.", "Which word describes the bottle?", "empty", ["bottle", "rolls"], skills=[S["word_jobs"]]),
        open_task("Word set: clean / keep / path / the", "Arrange the complete command.", "Keep the path clean.", [evidence("Uses the complete command order.", "keep the path clean", "the command is keep the path clean")], skills=[S["sentence_order"]]),
        open_task("Unfinished line: please sort the dry paper", "Repair both sentence boundaries.", "Please sort the dry paper.", [evidence("Uses a capital beginning.", "Please"), evidence("Uses a full stop.", ".")], skills=[S["punctuation"]]),
        open_task("Situation: a juice box blocks the doorway. Available place: the rinsing tray beside the sink.", "Write one safe, respectful action sentence.", "Please move the juice box from the doorway to the rinsing tray.", [evidence("Names the blocked doorway.", "juice box blocks the doorway", "box from the doorway"), evidence("Names the safe destination.", "rinsing tray", "tray beside the sink")], skills=[S["sentence"]]),
        open_task("A pupil leaves paper, watches a monitor reuse a sheet, and then moves her paper into the reuse tray.", "Give the ordered change and visible model.", "The pupil leaves paper, sees the monitor reuse a sheet, and follows the model by using the reuse tray.", [evidence("Orders leaving before watching.", "leaves paper", "sees the monitor"), evidence("Links the model to reuse tray.", "reuse a sheet", "reuse tray")], skills=[S["comprehension"], S["sequence"]], ordered=True),
        open_task("Recyclable means able to be processed and used again. Use recyclable with a correctly spelled item.", "Give its meaning, then use it accurately with the item.", "Recyclable means able to be used again after processing. This clean bottle is recyclable.", [evidence("Explains use again after processing.", "used again", "processing"), evidence("Uses bottle and recyclable accurately.", "bottle is recyclable")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
        open_task("Word set: where / should / packet / this / go", "Build the finished question with correct punctuation.", "Where should this packet go?", [evidence("Uses correct question order.", "where should this packet go"), evidence("Uses capital and question mark.", "Where", "?")], skills=[S["sentence_order"], S["punctuation"]]),
    ]


CONFIG = {
    "chapter_id": CHAPTER_ID,
    "chapter_no": 11,
    "title": "The Smart Monkey",
    "unit_title": "Life Around Us",
    "source_url": SOURCE_URL,
    "extract_path": "/tmp/zidd-ncert-class2-3/eng_c2_ch11.txt",
    "source_anchors": [
        {"anchor_id": f"{CHAPTER_ID}:read:1-3", "section_label": "Let us read: litter, example, and clean-up sequence", "page_start": 1, "page_end": 3, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:speak:4", "section_label": "Let us speak: clean places and responsible habits", "page_start": 4, "page_end": 4, "source_url": SOURCE_URL, "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:draw:4", "section_label": "Let us draw: household cleaning tools", "page_start": 4, "page_end": 4, "source_url": SOURCE_URL, "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:listen:5", "section_label": "Let us listen: teacher-led syllable and name clapping", "page_start": 5, "page_end": 5, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:write:6", "section_label": "Let us write: comprehension, completion, and clean actions", "page_start": 6, "page_end": 6, "source_url": SOURCE_URL, "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:project:7", "section_label": "Project: shop visit reflection and pictures", "page_start": 7, "page_end": 7, "source_url": SOURCE_URL, "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:speak-blends:8", "section_label": "Let us speak: printed fl and cl blend words", "page_start": 8, "page_end": 8, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
    ],
    "levels": LEVELS,
    "assessment_forms": [_assessment_form("a"), _assessment_form("b")],
}


MANIFEST = build_manifest(CONFIG)
