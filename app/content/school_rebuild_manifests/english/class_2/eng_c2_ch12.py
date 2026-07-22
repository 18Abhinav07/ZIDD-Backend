"""Original deep manifest for Class 2 English Chapter 12, Little Drops of Water."""

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
CHAPTER_ID = "eng_c2_ch12"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/bemr112.pdf"


LEVELS: list[dict[str, Any]] = [
    {
        "level_id": f"{CHAPTER_ID}:small_steps_grow",
        "title": "Track how small parts add up",
        "focus": "follow repeated small actions and their larger result in order",
        "outcome": "Retell a build-up sequence and explain from visible quantities how repeated small parts create a larger result.",
        "skill_ids": [S["comprehension"], S["sequence"]],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:song:1", f"{CHAPTER_ID}:write:5-6"],
        "principle": "A build-up chain names each small contribution, keeps time order, and connects the repeated action to the final amount or effect.",
        "connect": {
            "teaching_block": "Small parts become important when they repeat or join. Readers count the contributions and identify the result they create together.",
            "passage": "Each child adds one cup of water to a dry tree basin. After twelve cups, the soil is evenly wet.",
            "prompt": "Notice the repeated cup action and the larger final result before continuing.",
        },
        "co": choice_task(
            "Mira places one book on the shelf each morning. By Friday, five books are ready for the reading group.",
            "Which result comes from the repeated small action?",
            "Five books are ready on the shelf.",
            ["The shelf disappears.", "Friday comes before every morning."],
        ),
        "guided": [
            choice_task(
                "A tap drips into a bowl once each minute. The bowl slowly fills and reaches the marked line after many minutes.",
                "What happens after many small drops collect?",
                "The water reaches the marked line.",
                ["The bowl becomes a tap.", "Every drop leaves the bowl."],
            ),
            open_task(
                "Four neighbours each plant two seeds along the lane. They water the spots daily, and eight seedlings appear.",
                "Retell the small contributions and final result in order.",
                "Four neighbours plant two seeds each, water them daily, and together grow eight seedlings.",
                [
                    evidence("Includes the planting contribution.", "plant two seeds each", "four neighbours plant"),
                    evidence("Ends with eight seedlings.", "eight seedlings", "grow eight")
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Every learner writes one kind note for the notice board. When twenty notes are posted, the board carries encouragement for the whole class.",
                    "Explain how the individual deed becomes a shared result.",
                    "Each learner writes one kind note, and the twenty notes together encourage the whole class.",
                    [
                        evidence("Names one note from each learner.", "each learner", "one kind note"),
                        evidence("Connects twenty notes to class encouragement.", "twenty notes", "encourage the whole class")
                    ],
                ),
                (
                    "A family saves half a cup of rinsing water each day. At week's end, the collected water is enough for six balcony pots.",
                    "Sequence the daily saving and explain the larger use.",
                    "The family saves half a cup each day, collects it through the week, and waters six balcony pots.",
                    [
                        evidence("States the daily half-cup saving.", "half a cup each day"),
                        evidence("Ends with six watered pots.", "six balcony pots", "waters six")
                    ],
                ),
            ],
            ordered=True,
        ),
        "transfer": _open_set(
            [
                (
                    "A repair team tightens one loose screw on each classroom chair. After checking every chair, the entire room is safer.",
                    "Transfer the small-parts pattern to this safety task.",
                    "The team tightens each loose screw one by one, and the completed checks make the whole room safer.",
                    [
                        evidence("Names one-by-one screw repair.", "each loose screw", "one by one"),
                        evidence("Connects all checks to a safer room.", "completed checks", "whole room safer")
                    ],
                ),
                (
                    "One family brings a spoonful of grain for a community bird tray. Many families join, and the tray holds enough food for the morning flock.",
                    "Explain the contribution chain from spoonful to full tray.",
                    "Each family contributes a spoonful of grain, and the combined grain fills the tray for the flock.",
                    [
                        evidence("Includes each spoonful contribution.", "each family contributes", "spoonful of grain"),
                        evidence("Ends with food for the flock.", "fills the tray", "for the flock")
                    ],
                ),
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "The art club folds one paper flower at every meeting. After ten meetings, the flowers form a bright welcome chain.",
                    "Retell the repeated step and the completed creation.",
                    "The club folds one flower at each meeting, and ten flowers become a welcome chain.",
                    [
                        evidence("States one flower at each meeting.", "one flower", "each meeting"),
                        evidence("Connects ten flowers to the chain.", "ten flowers", "welcome chain")
                    ],
                ),
                (
                    "Ravi wipes one table while Sana stacks one set of chairs. Other classmates take one task each, so the hall is ready before lunch.",
                    "Explain how separate actions combine into the final result.",
                    "Each classmate completes one small task, and together their actions prepare the hall before lunch.",
                    [
                        evidence("Includes separate small tasks.", "one small task", "wipes one table", "stacks"),
                        evidence("Connects them to the ready hall.", "prepare the hall", "before lunch")
                    ],
                ),
            ],
            ordered=True,
        ),
        "cluster_id": f"{CHAPTER_ID}:small_part_result_gap",
        "misconception": "The learner reports only the final large result, ignores the repeated small actions, or assumes one tiny part alone produced everything.",
        "remediation": "Use a contribution counter with one-part, repeated-parts, and combined-result boxes; require the response to name both scale points.",
        "support": _open_set(
            [
                ("Three pupils each add one pencil to a supply box, making three pencils together.", "State the small action and total result.", "Each pupil adds one pencil, so the box gains three pencils altogether.", [evidence("Links one each to three total.", "one pencil", "three pencils")]),
                ("A drop falls every minute. Ten drops collect at the bottom of the jar.", "Explain the repeated action and result.", "One drop falls each minute, and ten drops collect in the jar.", [evidence("Connects repeated drops to ten collected.", "one drop", "each minute", "ten drops")]),
                ("Every child clears one scrap. Soon no scraps remain on the floor.", "Name the contributions and final condition.", "Each child clears one scrap, and together they leave the floor clear.", [evidence("Links one scrap each to a clear floor.", "one scrap", "floor clear")]),
                ("Five spoonfuls of sand fill the small mould.", "State how the mould becomes full.", "Five separate spoonfuls of sand are added until the mould becomes full.", [evidence("Uses five spoonfuls and full mould.", "five", "spoonfuls", "mould becomes full")]),
                ("A kind word from each teammate creates a page of welcome messages.", "Explain the small-to-large message chain.", "Each teammate contributes one kind word, and the words create a full welcome page.", [evidence("Links each kind word to the page.", "one kind word", "welcome page")]),
            ],
            ordered=True,
        ),
    },
    {
        "level_id": f"{CHAPTER_ID}:amount_and_kindness_words",
        "title": "Use amount and kindness vocabulary",
        "focus": "infer drop, grain, mighty, deed, pleasant, and kindness from context",
        "outcome": "Explain a chapter word from its visible amount or action clue and use the word accurately in a new sentence.",
        "skill_ids": [S["word_context"], S["word_use"]],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [f"{CHAPTER_ID}:song:1", f"{CHAPTER_ID}:write:5-6"],
        "principle": "Amount words are proved by what they count, while kindness words are proved by a caring action and its effect.",
        "connect": {
            "teaching_block": "Read the noun beside an amount word and the action beside a quality word. Those nearby details rule out a merely related guess.",
            "passage": "A drop is one very small round amount of liquid resting on the leaf.",
            "prompt": "Notice the liquid and small-amount clues before continuing.",
        },
        "co": choice_task("A grain of rice is one tiny, hard piece from the bowl.", "Which meaning fits grain here?", "one small piece of a cereal food", ["a full cup of juice", "a large cloth bag"]),
        "guided": [
            choice_task("The mighty river is extremely large and powerful after the rains.", "Which phrase explains mighty?", "large and powerful", ["dry and empty", "quietly folded"]),
            open_task("A deed is an action someone does. Helping a younger child carry books is a kind deed.", "Explain deed and use it in a fresh kindness sentence.", "A deed is an action. Sharing lunch with a hungry classmate is a kind deed.", [evidence("Defines deed as an action.", "deed is an action", "an action"), evidence("Uses deed with a caring act.", "kind deed", "sharing lunch")]),
        ],
        "independent": _open_set([
            ("The garden is pleasant because its shade, clean path, and soft breeze make visitors comfortable.", "Define pleasant from the clues and write a new use.", "Pleasant means enjoyable or comfortable. The cool reading corner is a pleasant place to rest.", [evidence("Defines enjoyable or comfortable.", "enjoyable", "comfortable"), evidence("Uses pleasant for a suitable place.", "pleasant place", "pleasant corner")]),
            ("Kindness appears when Asha notices a lonely child and invites the child into the game.", "Explain kindness and use it with a different visible action.", "Kindness means caring helpful behaviour. Offering water to a tired visitor is kindness.", [evidence("Defines caring helpful behaviour.", "caring", "helpful behaviour"), evidence("Uses a different caring action.", "offering water", "is kindness")]),
        ]),
        "transfer": _open_set([
            ("Many coins accumulate in the jar, adding one after another until the jar becomes heavy.", "Infer accumulate and transfer it to water drops.", "Accumulate means collect over time. Rain drops accumulate in the bucket.", [evidence("Defines collecting over time.", "collect over time", "adding one after another"), evidence("Uses accumulate with drops.", "drops accumulate", "water accumulates")]),
            ("A contribution is one part given to a shared effort, such as one seed added to a class garden.", "Explain contribution and use it for a helpful task.", "A contribution is a part someone gives. Sweeping one corner is Ravi's contribution to clean-up.", [evidence("Defines a given part.", "part someone gives", "part given"), evidence("Uses contribution with a task.", "contribution to clean-up", "my contribution")]),
        ]),
        "review": _open_set([
            ("A tiny act may look small, but it can still help someone in a clear way.", "Explain tiny and use it with a useful action.", "Tiny means very small. A tiny note of thanks can brighten a friend's day.", [evidence("Defines very small.", "very small"), evidence("Uses tiny with a helpful act.", "tiny note", "brighten")]),
            ("Harmony grows when people cooperate peacefully instead of pulling a group in different directions.", "State the context meaning and create a new use.", "Harmony means peaceful cooperation. The team works in harmony while preparing the garden.", [evidence("Defines peaceful cooperation.", "peaceful cooperation"), evidence("Uses harmony with joint work.", "works in harmony", "in harmony")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:amount_quality_context_gap",
        "misconception": "The learner treats every small object as a drop or grain, or names kindness without identifying any caring action.",
        "remediation": "Check what is being measured, replace the target with a plain phrase, and require a visible action for deed or kindness uses.",
        "support": _open_set([
            ("A droplet is one small bit of liquid hanging from the tap.", "Explain droplet and use it with rain.", "A droplet means a small drop of liquid. One rain droplet rested on the window.", [evidence("Defines and uses a small liquid drop.", "small drop of liquid", "rain droplet")]),
            ("A handful is the amount that can fit in one hand.", "Define handful and use it with grain.", "A handful is an amount held in one hand. Meera added a handful of grain.", [evidence("Defines and uses one-hand amount.", "held in one hand", "handful of grain")]),
            ("The generous child gives part of her snack without being asked.", "Explain generous from the action.", "Generous means willing to give or share. The generous child shares her snack.", [evidence("Defines and uses willing sharing.", "willing to give", "shares her snack")]),
            ("A peaceful room is calm and free from quarrels.", "Define peaceful and use it for teamwork.", "Peaceful means calm without conflict. The group reaches a peaceful decision.", [evidence("Defines and uses calm without conflict.", "calm", "peaceful decision")]),
            ("The result is gradual because it grows slowly through many small steps.", "Explain gradual and use it for filling a jar.", "Gradual means happening slowly in steps. The jar shows a gradual rise in water.", [evidence("Defines and uses slow steps.", "slowly in steps", "gradual rise")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:visible_harmony_spellings",
        "title": "Build water and kindness spellings",
        "focus": "use printed chunks and visible letter patterns to spell chapter words",
        "outcome": "Produce a standard spelling from printed evidence and use the amount or kindness word in a meaningful sentence.",
        "skill_ids": [S["spelling"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:song:1", f"{CHAPTER_ID}:write:5-6"],
        "principle": "Visible chunks and letters provide all spelling evidence; no sung, spoken, or listening performance is assessed.",
        "connect": {
            "teaching_block": "Join every printed chunk, compare the completed word with its meaning clue, and then use it in writing.",
            "passage": "Printed chunks: kind + ness = kindness; peace + ful = peaceful.",
            "prompt": "Notice how the base word remains visible in each longer spelling.",
        },
        "co": choice_task("Candidates: water, watter, woter. The sentence needs the liquid word.", "Which candidate is the standard drop word?", "water", ["watter", "woter"]),
        "guided": [
            choice_task("Candidates: grain, grane, graine. The clue names one tiny cereal piece.", "Which spelling fits the clue?", "grain", ["grane", "graine"]),
            open_task("Chunks: kind + ness. Meaning clue: caring behaviour.", "Build the caring-behaviour word, then show that behaviour in one sentence.", "The word is kindness. Reena shows kindness by sharing her umbrella.", [evidence("Spells kindness correctly.", "kindness"), evidence("Uses kindness with a caring action.", "shows kindness", "sharing her umbrella")]),
        ],
        "independent": _open_set([
            ("Missing letters: o c e _ n. The clue names a very large body of salt water.", "Complete the word and write one sentence.", "The word is ocean. Many rivers carry water toward the ocean.", [evidence("Spells ocean correctly.", "ocean"), evidence("Uses ocean with water.", "toward the ocean", "ocean water")]),
            ("Scrambled letters: d e e d. The clue names an action someone performs.", "Unscramble the word and use it for a helpful act.", "The word is deed. Carrying the bag was a helpful deed.", [evidence("Spells deed correctly.", "deed"), evidence("Uses deed with a helpful action.", "helpful deed", "carrying the bag")]),
        ]),
        "transfer": _open_set([
            ("Base word: might. Add y to describe something powerful.", "Build the new word and use it for a river.", "The word is mighty. The mighty river moved around the rocks.", [evidence("Builds mighty correctly.", "mighty"), evidence("Uses mighty for a powerful river.", "mighty river")]),
            ("Chunks: pleas + ant. The clue describes something enjoyable.", "Join the chunks and write a complete sentence.", "The word is pleasant. The shaded path is pleasant in the afternoon.", [evidence("Spells pleasant correctly.", "pleasant"), evidence("Uses pleasant for an enjoyable place.", "path is pleasant", "pleasant afternoon")]),
        ]),
        "review": _open_set([
            ("Correct the printed word happyness in a sentence about smiles.", "Write the corrected word and sentence.", "The corrected word is happiness. Kind words can spread happiness.", [evidence("Corrects happiness.", "happiness"), evidence("Uses it with kind words.", "spread happiness", "kind words")]),
            ("Missing letters: d r _ p. The clue names one small bit of liquid.", "Complete the word and use it accurately.", "The word is drop. One drop of water shone on the leaf.", [evidence("Spells drop correctly.", "drop"), evidence("Uses drop with liquid.", "drop of water", "one drop")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:harmony_chunk_spelling",
        "misconception": "The learner changes a visible base word, drops a chunk, or chooses a spelling that does not match the amount or kindness clue.",
        "remediation": "Trace base and ending, join all letters, verify the clue meaning, and use the completed word in one written sentence.",
        "support": _open_set([
            ("Chunks: sand + y. The clue describes ground containing much sand.", "Join and use the describing word.", "The word is sandy. We walked along a sandy path.", [evidence("Spells and uses sandy.", "sandy", "sandy path")]),
            ("Chunks: smile + s. The clue names more than one happy expression.", "Build and use the plural word.", "The word is smiles. Kind notes brought smiles to the group.", [evidence("Spells and uses smiles.", "smiles", "brought smiles")]),
            ("Candidates: liquid, liqued, liqid. The clue names a substance that flows.", "Write the standard word in a sentence.", "The word is liquid. Water is a liquid that flows.", [evidence("Spells and uses liquid.", "liquid", "water is a liquid")]),
            ("Scrambled letters: r i c e. The clue names a cereal grain.", "Unscramble and use the word.", "The word is rice. One grain of rice fell beside the bowl.", [evidence("Spells and uses rice.", "rice", "grain of rice")]),
            ("Correct this word: peece. The harmony word uses ea.", "Repair and use the word in a sentence.", "The corrected word is peace. The friends solve the problem in peace.", [evidence("Corrects and uses peace.", "peace", "in peace")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:amount_word_jobs",
        "title": "Find jobs in amount sentences",
        "focus": "identify nouns, verbs, and adjectives in water, grain, and kindness statements",
        "outcome": "Classify requested words by their job and explain how an action or description relates to the named amount or deed.",
        "skill_ids": [S["word_jobs"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:write:5-6", f"{CHAPTER_ID}:speak:2"],
        "principle": "Amount and kindness sentences still use naming, action, and describing jobs; the sentence determines each label.",
        "connect": {
            "teaching_block": "Ask what is named, what happens, and what kind. Do not label a word by whether it sounds important.",
            "passage": "Tiny drops fill the deep bowl. Drops and bowl name, fill acts, and tiny and deep describe.",
            "prompt": "Notice how each word job is proved by the complete sentence.",
        },
        "co": choice_task("A pleasant breeze cools the garden.", "Which word describes the breeze?", "pleasant", ["breeze", "cools"]),
        "guided": [
            choice_task("Kind deeds spread warm smiles.", "Which word tells what the kind deeds do?", "spread", ["kind", "deeds"]),
            open_task("The mighty river carries fine sand.", "Label river, carries, mighty, and fine.", "River is a noun, carries is a verb, and mighty and fine are adjectives.", [evidence("Labels river and carries.", "river is a noun", "carries is a verb"), evidence("Labels mighty and fine.", "mighty", "fine")]),
        ],
        "independent": _open_set([
            ("A small cup holds clean water.", "Classify cup, holds, small, and clean.", "Cup is a noun, holds is a verb, and small and clean are adjectives.", [evidence("Labels cup and holds.", "cup is a noun", "holds is a verb"), evidence("Labels small and clean.", "small", "clean")]),
            ("Generous neighbours share fresh grain.", "Identify the action and both describing words.", "Share is the action, while generous and fresh are describing words.", [evidence("Names share as action.", "share is the action", "share is a verb"), evidence("Names generous and fresh.", "generous", "fresh")]),
        ]),
        "transfer": _open_set([
            ("The gradual rise fills the marked jar.", "Label gradual, rise, fills, and marked.", "Gradual and marked are adjectives, rise is a noun, and fills is a verb.", [evidence("Labels both adjectives.", "gradual", "marked"), evidence("Labels rise and fills.", "rise is a noun", "fills is a verb")]),
            ("A thoughtful child writes a short note.", "Transfer the word-job check to thoughtful, child, and writes.", "Thoughtful is an adjective, child is a noun, and writes is a verb.", [evidence("Classifies all requested words.", "thoughtful is an adjective", "child is a noun", "writes is a verb")]),
        ]),
        "review": _open_set([
            ("Many little grains cover the wet ground.", "Name the action and two describing words.", "Cover is the action, and little and wet are describing words.", [evidence("Names cover as action.", "cover is the action", "cover is a verb"), evidence("Names little and wet.", "little", "wet")]),
            ("The peaceful group completes a shared task.", "Classify group, completes, peaceful, and shared.", "Group is a noun, completes is a verb, and peaceful and shared are adjectives.", [evidence("Labels group and completes.", "group is a noun", "completes is a verb"), evidence("Labels peaceful and shared.", "peaceful", "shared")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:amount_word_job_confusion",
        "misconception": "The learner treats every amount word as a noun or calls a quality such as kind an action without checking the sentence.",
        "remediation": "Apply what, happens, and what kind tests to the full sentence and point to the exact word before choosing its job.",
        "support": _open_set([
            ("The blue drop falls.", "Label blue, drop, and falls.", "Blue is an adjective, drop is a noun, and falls is a verb.", [evidence("Labels all three jobs.", "blue is an adjective", "drop is a noun", "falls is a verb")]),
            ("A kind child helps a visitor.", "Which word describes the child, and which word tells what happens?", "Kind describes the child, and helps shows the action.", [evidence("Distinguishes kind and helps.", "kind describes", "helps shows")]),
            ("Tiny seeds grow slowly.", "Classify tiny, seeds, and grow.", "Tiny is an adjective, seeds is a noun, and grow is a verb.", [evidence("Classifies all requested words.", "tiny is an adjective", "seeds is a noun", "grow is a verb")]),
            ("The full glass jar tips sideways.", "Explain why full is not the action.", "Full describes the jar, while tips is the action.", [evidence("Contrasts full and tips.", "full describes", "tips is the action")]),
            ("Pleasant words spread smiles.", "Label pleasant, words, and spread.", "Pleasant is an adjective, words is a noun, and spread is a verb.", [evidence("Labels all three words.", "pleasant is an adjective", "words is a noun", "spread is a verb")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:harmony_sentence_builder",
        "title": "Arrange amount and kindness sentences",
        "focus": "order visible words and punctuate statements or questions",
        "outcome": "Use every supplied word in a sensible sentence, begin with a capital, and add a full stop or question mark that matches purpose.",
        "skill_ids": [S["sentence_order"], S["punctuation"]],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:write:5-6", f"{CHAPTER_ID}:song:1"],
        "principle": "Find the naming part and action, arrange amount or quality details, and finish with the correct sentence boundaries.",
        "connect": {
            "teaching_block": "Word order shows who does what, while capitals and end marks show where the complete thought begins and ends.",
            "passage": "Word set: drops / fill / little / the / cup. Finished form: Little drops fill the cup.",
            "prompt": "Notice the complete order, capital L, and full stop.",
        },
        "co": choice_task("Word set: deeds / smiles / kind / spread", "Which option builds the complete kindness statement?", "Kind deeds spread smiles.", ["Deeds smiles kind spread.", "kind Spread deeds smiles"]),
        "guided": [
            choice_task("Word set: many / jar / drops / how / fill / the", "Which option forms a correct question?", "How many drops fill the jar?", ["How the jar many drops fill.", "how many jar fill the drops?"]),
            open_task("Word set: grain / each / small / adds / to / the / pile", "Arrange every word as one statement.", "Each small grain adds to the pile.", [evidence("Uses sensible complete order.", "each small grain adds to the pile"), evidence("Adds capital and full stop.", "Each", ".")]),
        ],
        "independent": _open_set([
            ("Word set: water / save / we / every / day", "Build the complete conservation statement.", "We save water every day.", [evidence("Uses every word in correct order.", "we save water every day"), evidence("Adds capital and full stop.", "We", ".")]),
            ("Word set: kindness / how / help / can / one / act / of", "Build and punctuate the complete question.", "How can one act of kindness help?", [evidence("Uses correct question order.", "how can one act of kindness help"), evidence("Adds capital and question mark.", "How", "?")]),
        ]),
        "transfer": _open_set([
            ("Word set: notes / welcome / write / classmates / small", "Transfer the ordering steps to a class action.", "Classmates write small welcome notes.", [evidence("Uses all words in sensible order.", "classmates write small welcome notes"), evidence("Adds capital and full stop.", "Classmates", ".")]),
            ("Word set: cup / which / holds / oil / the", "Arrange the complete object question.", "Which cup holds the oil?", [evidence("Uses correct question order.", "which cup holds the oil"), evidence("Adds capital and question mark.", "Which", "?")]),
        ]),
        "review": _open_set([
            ("Unfinished line: many grains fill the bag", "Repair the statement boundaries.", "Many grains fill the bag.", [evidence("Keeps the complete statement.", "many grains fill the bag"), evidence("Adds capital and full stop.", "Many", ".")]),
            ("Jumbled line: how / this / action / does / show / kindness", "Write the ordered question with correct punctuation.", "How does this action show kindness?", [evidence("Uses the supplied question order.", "how does this action show kindness"), evidence("Adds capital and question mark.", "How", "?")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:harmony_sentence_boundary",
        "misconception": "The learner keeps the jumbled order, drops an amount word, or gives a question the punctuation of a statement.",
        "remediation": "Box the naming part, underline the action, place quantity or quality details, and run the capital-plus-purpose-mark check.",
        "support": _open_set([
            ("Word set: drop / one / falls / slowly", "Build and finish the statement.", "One drop falls slowly.", [evidence("Builds and punctuates the statement.", "one drop falls slowly", "One", ".")]),
            ("Word set: is / grain / which / rice", "Build the identity question.", "Which grain is rice?", [evidence("Builds and punctuates the question.", "which grain is rice", "Which", "?")]),
            ("Line needing repair: kind words bring smiles", "Add complete statement boundaries.", "Kind words bring smiles.", [evidence("Adds capital and full stop.", "Kind words bring smiles", ".")]),
            ("Word set: fills / water / clean / bottle / the", "Arrange the water statement.", "Clean water fills the bottle.", [evidence("Uses every word in order.", "clean water fills the bottle", "Clean", ".")]),
            ("Line needing repair: how many drops are here", "Repair the drop-count question and its end mark.", "How many drops are here?", [evidence("Adds capital and question mark.", "How many drops are here", "?")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:small_kind_action_writer",
        "title": "Write how small actions matter",
        "focus": "construct complete cause-and-result sentences from visible contributions",
        "outcome": "Write a complete sentence naming one small action and the helpful larger effect it can create when repeated or joined.",
        "skill_ids": [S["comprehension"], S["sentence"]],
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:song:1", f"{CHAPTER_ID}:draw:4", f"{CHAPTER_ID}:write:5-6"],
        "principle": "A meaningful small-action sentence names the deed, states its visible effect, and avoids claiming that one act solves an unlimited problem.",
        "connect": {
            "teaching_block": "Small actions matter through a specific effect or through repetition. The reference gives both the action and the realistic result.",
            "passage": "Action: I refill one bird bowl. Visible effect: birds have water during the hot afternoon.",
            "prompt": "Notice the one action and its limited but useful effect.",
        },
        "co": choice_task("Action: Kavya writes one welcome note. Effect: a new learner knows where to sit.", "Which sentence accurately joins action and effect?", "Kavya's welcome note helps the new learner find a seat.", ["One note fixes every problem in school.", "The learner becomes a note."], skills=[S["comprehension"]]),
        "guided": _open_set([
            ("Action: Each pupil saves one sheet for reuse. Effect: the class has enough paper for tomorrow's draft work.", "Write one complete cause-and-result sentence.", "Because each pupil saves one sheet, the class has enough reuse paper for tomorrow's drafts.", [evidence("Names one saved sheet from each pupil.", "each pupil saves one sheet"), evidence("Names tomorrow's reuse result.", "enough reuse paper", "tomorrow's drafts")]),
            ("Action: Rahul thanks the bus helper. Effect: the helper knows the assistance was noticed.", "Compose a complete kindness sentence from both details.", "Rahul's words of thanks show the bus helper that the assistance was noticed.", [evidence("Includes Rahul's thanks.", "Rahul", "thanks"), evidence("Includes noticed assistance.", "assistance was noticed", "help was noticed")]),
        ]),
        "independent": _open_set([
            ("Action: Six families each bring one cup of soil. Effect: together they fill a planter for a neem sapling.", "Explain the combined contribution in one or two complete sentences.", "Each family brings one cup of soil, and the six cups together fill the neem planter.", [evidence("Includes one cup from each family.", "each family", "one cup of soil"), evidence("Connects six cups to the planter.", "six cups", "fill the neem planter")]),
            ("Action: Meena invites a quiet classmate into a game. Effect: the classmate joins instead of standing alone.", "Write the deed and its visible kindness effect.", "Meena shows kindness by inviting the quiet classmate, who then joins the game instead of standing alone.", [evidence("Names the invitation.", "inviting the quiet classmate"), evidence("Names joining instead of being alone.", "joins the game", "standing alone")]),
        ]),
        "transfer": _open_set([
            ("Action: One child closes a dripping tap after washing. Repeated effect: many saved drops remain in the tank over time.", "Transfer the small-action pattern to water saving.", "Closing the dripping tap saves small amounts of water that add up in the tank over time.", [evidence("Names closing the dripping tap.", "closing the dripping tap"), evidence("Connects saved drops over time.", "saved drops", "add up", "over time")]),
            ("Action: Each teammate learns one line of a welcome message. Combined effect: the group can present the whole message clearly.", "Write how the separate parts create the shared result.", "Each teammate learns one line, and the learned parts combine into the group's complete welcome message.", [evidence("Includes one line per teammate.", "each teammate", "one line"), evidence("Connects parts to complete message.", "combine", "complete welcome message")]),
        ]),
        "review": _open_set([
            ("Action: Asha places one seed in every empty patch. Effect: after steady care, flowers grow across the border.", "Write a realistic action-and-result sentence.", "Asha plants one seed in each empty patch, and steady care helps flowers grow across the border.", [evidence("Names one seed in each patch.", "one seed", "each empty patch"), evidence("Includes steady care and flowers.", "steady care", "flowers grow")]),
            ("Action: Every child offers one respectful word during a disagreement. Effect: the group becomes calm enough to choose a plan.", "Compose the small-deed and harmony result.", "Each respectful word helps calm the disagreement until the group can choose a plan together.", [evidence("Names respectful words during disagreement.", "respectful word", "disagreement"), evidence("Connects calm to choosing a plan.", "calm", "choose a plan")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:small_action_overclaim",
        "misconception": "The learner omits the small action, states only a vague kindness slogan, or claims one tiny deed instantly solves every large problem.",
        "remediation": "Box the exact action and realistic effect, add repetition only when stated, and write one complete cause-and-result sentence with both boxes.",
        "support": _open_set([
            ("Action: One child fills a water cup. Effect: one thirsty visitor can drink.", "Write the limited helpful result.", "Filling one water cup helps one thirsty visitor have a drink.", [evidence("Links one cup to one visitor.", "one water cup", "one thirsty visitor")]),
            ("Action: Each pupil adds one grain scoop. Effect: the bird tray becomes full.", "State the combined contribution.", "Each pupil adds one scoop of grain, and together the scoops fill the bird tray.", [evidence("Links each scoop to the full tray.", "each pupil", "one scoop", "fill the bird tray")]),
            ("Action: Mira smiles and greets a new child. Effect: the child answers and joins the line.", "Write the kindness action and result.", "Mira's greeting helps the new child answer and join the line.", [evidence("Links greeting to joining.", "greeting", "join the line")]),
            ("Action: Ravi reuses one box. Effect: fewer new containers are needed for his project.", "Write the realistic reuse effect.", "Ravi reuses one box, so his project needs one fewer new container.", [evidence("Links one reused box to one fewer container.", "reuses one box", "one fewer")]),
            ("Action: Two friends each carry one book. Effect: all books reach the shelf.", "Explain how the shared task finishes.", "Each friend carries a book, and their combined effort returns all books to the shelf.", [evidence("Links each carried book to shelf result.", "each friend", "carries a book", "all books", "shelf")]),
        ]),
    },
]


EXTRA_DEPTH = {
    f"{CHAPTER_ID}:small_steps_grow": {
        "guided": [
            choice_task(
                "One bead is placed on a string each morning. After ten mornings, the string holds ten beads.",
                "What makes the bead string grow?",
                "adding one bead each morning",
                ["removing the string", "painting one bead twice"],
            ),
            open_task(
                "A rain jar starts empty. Three small showers add one mark of water each, and the water reaches the third line.",
                "Explain the repeated small part and the larger result.",
                "Each shower adds one mark of water, so three showers raise the jar to the third line.",
                [
                    evidence("Names the repeated part.", "each shower adds one mark", "one water mark from every shower"),
                    evidence("States the larger result.", "jar reaches the third line", "water rises to line three"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set([
            (
                "Four teams each bring two clean cans for a model. The class then has eight cans to build with.",
                "Show how the small team amounts create the class total.",
                "Each of four teams brings two cans, so their contributions make a total of eight cans.",
                [
                    evidence("States each team's amount.", "each team brings two cans", "two cans from every team"),
                    evidence("States the number of teams.", "four teams", "there are four teams"),
                    evidence("States the total.", "total of eight cans", "class has eight cans"),
                ],
            ),
            (
                "A reading chart gains one star whenever a pair finishes a book. Five pairs finish, so five stars appear.",
                "Explain the action-to-total chain without claiming one pair earned all the stars.",
                "Each finishing pair adds one star, and five pairs together add five stars to the chart.",
                [
                    evidence("States the earning rule.", "each finishing pair adds one star", "one star for every pair"),
                    evidence("States the group count.", "five pairs together", "five pairs finish"),
                    evidence("States the chart result.", "five stars on the chart", "chart gains five stars"),
                ],
            ),
        ], ordered=True),
        "transfer": _open_set([
            (
                "A path is repaired one stone at a time. Six neighbours each set one loose stone firmly, leaving six safe spots.",
                "Transfer small-parts reasoning to the path repair.",
                "Each neighbour fixes one loose stone, so six neighbours create six safer spots on the path.",
                [
                    evidence("States one person's part.", "each neighbour fixes one stone", "one loose stone per neighbour"),
                    evidence("States the joined amount.", "six neighbours", "six stones are set firmly"),
                    evidence("States the limited result.", "six safer spots", "six spots become safer"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:amount_and_kindness_words": {
        "guided": [
            choice_task(
                "The stream is shallow, with water low enough for the tops of several stones to remain visible.",
                "Which meaning fits shallow?",
                "not deep",
                ["moving very fast", "filled with salt"],
            ),
            open_task(
                "A contribution is one part given to a shared effort; Mira's contribution is a bundle of old newspapers.",
                "Explain contribution and use it in another class effort.",
                "A contribution is a part given to help a group. My contribution is two seeds for the class garden.",
                [
                    evidence("Explains contribution.", "part given to help a group", "something added to a shared effort"),
                    evidence("Uses contribution freshly.", "my contribution is two seeds", "two seeds for the class garden"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "The bucket gradually fills because a little water enters it over many minutes.",
                "Infer gradually and use it in a different growing process.",
                "Gradually means little by little over time. The seedling gradually grows taller each week.",
                [
                    evidence("Explains gradually.", "little by little over time", "changes slowly across time"),
                    evidence("Uses gradually accurately.", "seedling gradually grows taller", "plant grows little by little"),
                ],
            ),
            (
                "The children cooperate by sharing jobs and working together to fill the bird bowls.",
                "Explain cooperate and create a new helpful use.",
                "Cooperate means work together. Two pupils cooperate to carry the book box safely.",
                [
                    evidence("Explains cooperate.", "means work together", "share work toward one goal"),
                    evidence("Uses cooperate freshly.", "pupils cooperate to carry the book box", "two pupils work together with the box"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "A steady light remains even and does not keep fading or flashing.",
                "Infer steady and use it for a repeated helpful action.",
                "Steady means even and continuing. Steady care keeps the small garden watered each day.",
                [
                    evidence("Explains steady.", "even and continuing", "keeps going at the same rate"),
                    evidence("Transfers steady to care.", "steady care keeps the garden watered", "regular care waters the garden each day"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:visible_harmony_spellings": {
        "guided": [
            choice_task(
                "Candidates: harmony, harmany, harmonny. The clue means people working peacefully together.",
                "Which spelling is standard?",
                "harmony",
                ["harmany", "harmonny"],
            ),
            open_task(
                "Printed chunks: lit + tle. The clue describes a small amount.",
                "Join the chunks and use the word in one complete sentence.",
                "The word is little. A little water remains in the cup.",
                [
                    evidence("Builds the spelling.", "word is little", "spell it little"),
                    evidence("Uses little accurately.", "little water remains in the cup", "small amount of water is left"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Missing letters: t o g e t h _ r. The clue means with one another as a group.",
                "Complete the word and use it in a helpful sentence.",
                "The word is together. We work together to move the light chairs.",
                [
                    evidence("Completes the spelling.", "word is together", "spell it together"),
                    evidence("Uses together meaningfully.", "work together to move the chairs", "move chairs as a group"),
                ],
            ),
            (
                "Scrambled letters: d r o p. The clue names one small round bit of liquid.",
                "Unscramble the word and use it with water.",
                "The word is drop. One drop of water fell from the leaf.",
                [
                    evidence("Unscrambles the word.", "word is drop", "spell it drop"),
                    evidence("Uses drop accurately.", "one drop of water fell", "water drop fell from the leaf"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Base word: help. Add ful to describe something that gives help.",
                "Build the new word and use it for a small action.",
                "The new word is helpful. Labelling one box is a helpful action for the group.",
                [
                    evidence("Builds the new spelling.", "new word is helpful", "spell it helpful"),
                    evidence("Uses helpful in context.", "labelling one box is helpful", "helpful action for the group"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:amount_word_jobs": {
        "guided": [
            choice_task(
                "Several tiny drops fill the glass.",
                "Which word tells what the drops do?",
                "fill",
                ["tiny", "drops"],
            ),
            open_task(
                "A generous neighbour shares fresh fruit.",
                "Classify neighbour, shares, generous, and fresh.",
                "Neighbour is a noun, shares is a verb, and generous and fresh are adjectives.",
                [
                    evidence("Labels neighbour.", "neighbour is a noun", "neighbour names a person"),
                    evidence("Labels shares.", "shares is a verb", "shares shows action"),
                    evidence("Labels generous.", "generous is an adjective", "generous describes the neighbour"),
                    evidence("Labels fresh.", "fresh is an adjective", "fresh describes the fruit"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Many small coins fill the heavy purse.",
                "Give the jobs of coins, fill, small, and heavy.",
                "Coins is a noun, fill is a verb, and small and heavy are adjectives.",
                [
                    evidence("Labels coins.", "coins is a noun", "coins name things"),
                    evidence("Labels fill.", "fill is a verb", "fill shows action"),
                    evidence("Labels small.", "small is an adjective", "small describes coins"),
                    evidence("Labels heavy.", "heavy is an adjective", "heavy describes the purse"),
                ],
            ),
            (
                "Kind messages brighten a lonely afternoon.",
                "Classify messages, brighten, kind, and lonely.",
                "Messages is a noun, brighten is a verb, and kind and lonely are adjectives.",
                [
                    evidence("Labels messages.", "messages is a noun", "messages name things"),
                    evidence("Labels brighten.", "brighten is a verb", "brighten shows action"),
                    evidence("Labels kind.", "kind is an adjective", "kind describes messages"),
                    evidence("Labels lonely.", "lonely is an adjective", "lonely describes the afternoon"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "A patient baker adds thin layers slowly.",
                "Transfer the word-job check to baker, adds, patient, and thin.",
                "Baker is a noun, adds is a verb, and patient and thin are adjectives.",
                [
                    evidence("Labels baker.", "baker is a noun", "baker names a person"),
                    evidence("Labels adds.", "adds is a verb", "adds shows action"),
                    evidence("Labels patient.", "patient is an adjective", "patient describes the baker"),
                    evidence("Labels thin.", "thin is an adjective", "thin describes the layers"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:harmony_sentence_builder": {
        "guided": [
            choice_task(
                "Word set: drops / ten / bottle / fill / the",
                "Which option forms the complete statement?",
                "Ten drops fill the bottle.",
                ["Drops the bottle ten fill.", "ten Fill drops bottle the"],
            ),
            open_task(
                "Word set: shared / who / the / last / cup",
                "Arrange every word as a finished question.",
                "Who shared the last cup?",
                [
                    evidence("Uses the question order.", "who shared the last cup", "ask who shared the cup"),
                    evidence("Uses a natural question ending.", "last cup?", "the last cup?"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Word set: seeds / each / brings / child / two",
                "Build the complete amount statement.",
                "Each child brings two seeds.",
                [
                    evidence("Uses every word in order.", "each child brings two seeds", "two seeds are brought by each child"),
                    evidence("Uses a natural statement ending.", "two seeds.", "brings two seeds."),
                ],
            ),
            (
                "Line needing repair: how can one small note help",
                "Add the correct beginning and end mark.",
                "How can one small note help?",
                [
                    evidence("Keeps the complete question.", "how can one small note help", "ask how the note can help"),
                    evidence("Uses a natural question ending.", "note help?", "small note help?"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Word set: brick / each / wall / strengthens / the",
                "Transfer the ordering steps to a building statement.",
                "Each brick strengthens the wall.",
                [
                    evidence("Uses the statement order.", "each brick strengthens the wall", "the wall is strengthened by each brick"),
                    evidence("Uses a natural statement ending.", "the wall.", "strengthens the wall."),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:small_kind_action_writer": {
        "guided": [
            choice_task(
                "Action card: Each learner adds one useful word to a shared class list. Effect: the list has many words for story writing.",
                "Which sentence joins the small action to its stated effect?",
                "Each learner adds one word, so the class builds a larger story-word list.",
                ["One word writes every story by itself.", "The list removes all the learners."],
                skills=[S["comprehension"]],
            ),
            open_task(
                "Action card: I hold the door for one pupil carrying books. Effect: the pupil enters without dropping the stack.",
                "Write a complete sentence linking the action and realistic effect.",
                "Holding the door helps the pupil enter without dropping the books.",
                [
                    evidence("Names the small action.", "holding the door", "I hold the door"),
                    evidence("Names the receiver.", "pupil carrying books", "the pupil with the books"),
                    evidence("States the realistic effect.", "enters without dropping the books", "keeps the book stack safe"),
                ],
                interaction="creative_continuation",
            ),
        ],
        "independent": _open_set([
            (
                "Action card: Six families each donate one storybook. Effect: the reading corner gains six different books.",
                "Explain how the separate actions create the exact shared result.",
                "When each of six families gives one storybook, the reading corner gains six books.",
                [
                    evidence("States one family's part.", "each family gives one storybook", "one book from every family"),
                    evidence("States the number of families.", "six families", "there are six families"),
                    evidence("States the exact result.", "reading corner gains six books", "six books are added"),
                ],
            ),
            (
                "Action card: Leena listens while a new pupil explains a game rule. Effect: the pupil finishes the idea and the group understands it.",
                "Write a kindness sentence using the action and both stated effects.",
                "Leena shows respect by listening, which lets the new pupil finish and helps the group understand the rule.",
                [
                    evidence("Names Leena's action.", "Leena listens", "listening to the new pupil"),
                    evidence("States the pupil's result.", "pupil finishes the idea", "new pupil can finish speaking"),
                    evidence("States the group result.", "group understands the rule", "others understand the game rule"),
                    evidence("Names the quality.", "shows respect", "respectful listening"),
                ],
            ),
        ], interaction="creative_continuation"),
        "transfer": _open_set([
            (
                "Action card: Four neighbours each report one broken streetlight number. Effect: the repair team receives a complete list of four locations.",
                "Transfer small-action reasoning without claiming the reports repair the lights.",
                "Each neighbour reports one location, so the repair team receives a four-place list to inspect.",
                [
                    evidence("States each small action.", "each neighbour reports one location", "one streetlight number per neighbour"),
                    evidence("States the combined list.", "four-place list", "list of four locations"),
                    evidence("Keeps the result realistic.", "repair team receives the list to inspect", "reports do not repair the lights"),
                ],
            )
        ], interaction="creative_continuation"),
    },
}

LAUNCH_DEPTH = {
    f"{CHAPTER_ID}:small_steps_grow": {
        "transfer": _open_set(
            [
                (
                    "For a class mosaic, each child adds one coloured square. The first row fills, the second row fills, and finally the separate pieces make one large sun.",
                    "Explain how the small additions create the final picture in order.",
                    "Each child adds one square, the rows fill one by one, and the small pieces finally form a large sun.",
                    [
                        evidence("States the repeated small action.", "Each child adds one square", "adds one coloured square"),
                        evidence("States the growing middle.", "rows fill one by one", "first row fills"),
                        evidence("States the final whole.", "small pieces finally form a large sun", "make one large sun"),
                    ],
                )
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "The reading team returns five books each day. The return shelf becomes fuller through the week, and by Friday every borrowed book is back.",
                    "Connect the daily action to the Friday result.",
                    "The team returns five books each day, so the shelf fills through the week and all borrowed books are back by Friday.",
                    [
                        evidence("States the daily amount.", "returns five books each day", "five books each day"),
                        evidence("States the gradual change.", "shelf fills through the week", "becomes fuller"),
                        evidence("States the final result.", "all borrowed books are back by Friday", "by Friday"),
                    ],
                ),
                (
                    "During garden care, one group loosens soil, another adds compost, and a third waters the seedlings. Together the three small jobs prepare the whole bed.",
                    "Sequence the jobs and explain their shared result.",
                    "One group loosens soil, another adds compost, and the third waters seedlings, so together they prepare the whole garden bed.",
                    [
                        evidence("States the soil job.", "loosens soil", "one group loosens"),
                        evidence("States the compost job.", "adds compost", "another adds"),
                        evidence("States the watering job.", "waters seedlings", "third waters"),
                        evidence("States the shared result.", "together they prepare the whole garden bed", "prepare the whole bed"),
                    ],
                ),
            ],
            ordered=True,
        ),
    },
    f"{CHAPTER_ID}:amount_and_kindness_words": {
        "transfer": _open_set(
            [
                (
                    "The amount of rice in a bowl means how much rice the bowl holds. A full bowl has a greater amount than one spoonful.",
                    "Explain amount and use it in a fresh comparison.",
                    "Amount means how much of something there is. The large bottle holds a greater amount of water than the cup.",
                    [
                        evidence("Explains amount.", "how much of something there is", "Amount means"),
                        evidence("Uses amount accurately.", "greater amount of water than the cup", "amount of water"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "When Jatin shares his umbrella with a classmate in the rain, his helpful action shows kindness.",
                    "State what kindness means and use it in another school action.",
                    "Kindness means caring through helpful action. Helping a new learner find the classroom is an act of kindness.",
                    [
                        evidence("Explains kindness.", "caring through helpful action", "helpful action"),
                        evidence("Uses kindness freshly.", "find the classroom is an act of kindness", "act of kindness"),
                    ],
                ),
                (
                    "To contribute means to give a useful part to shared work. Noor contributes two labels to the class display.",
                    "Explain contribute and write one different group example.",
                    "Contribute means add a useful part to shared work. I contribute a drawing to our nature chart.",
                    [
                        evidence("Explains contribute.", "add a useful part to shared work", "give a useful part"),
                        evidence("Uses contribute accurately.", "contribute a drawing to our nature chart", "I contribute a drawing"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:visible_harmony_spellings": {
        "transfer": _open_set(
            [
                (
                    "Missing letters: s h _ r e. The clue names giving part of what you have to another person.",
                    "Complete the action word and use it in a sentence about grain.",
                    "The word is share. The neighbours share a bag of grain.",
                    [
                        evidence("Completes the spelling.", "word is share", "spell it share"),
                        evidence("Uses share accurately.", "neighbours share a bag of grain", "share grain with neighbours"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Visible parts: to + gether. The clue means people acting with one another as a group.",
                    "Join the parts and use the word in a team sentence.",
                    "The word is together. Four classmates carry the long chart together.",
                    [
                        evidence("Spells the joined word.", "word is together", "spell it together"),
                        evidence("Uses together in context.", "classmates carry the long chart together", "chart together"),
                    ],
                ),
                (
                    "Candidates: kindness, kindnes, kindniss. The message needs the standard word for caring action.",
                    "Choose the correct spelling and write one complete use.",
                    "The standard spelling is kindness. Sharing the shaded seat shows kindness.",
                    [
                        evidence("Gives the standard spelling.", "standard spelling is kindness", "spell it kindness"),
                        evidence("Uses kindness accurately.", "Sharing the shaded seat shows kindness", "shows kindness"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:amount_word_jobs": {
        "transfer": _open_set(
            [
                (
                    "The generous baker shares warm rolls.",
                    "Classify baker, shares, generous, and warm.",
                    "Baker is a noun, shares is a verb, and generous and warm are adjectives.",
                    [
                        evidence("Labels baker.", "Baker is a noun", "baker names a person"),
                        evidence("Labels shares.", "shares is a verb", "shares shows action"),
                        evidence("Labels generous.", "generous is an adjective", "generous describes the baker"),
                        evidence("Labels warm.", "warm is an adjective", "warm describes the rolls"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "A small donation fills the empty jar.",
                    "Give the jobs of donation, fills, small, and empty.",
                    "Donation is a noun, fills is a verb, and small and empty are adjectives.",
                    [
                        evidence("Labels donation.", "Donation is a noun", "donation names a thing"),
                        evidence("Labels fills.", "fills is a verb", "fills shows action"),
                        evidence("Labels small.", "small is an adjective", "small describes the donation"),
                        evidence("Labels empty.", "empty is an adjective", "empty describes the jar"),
                    ],
                ),
                (
                    "The caring neighbour carries a heavy basket.",
                    "Classify neighbour, carries, caring, and heavy in this helpful-action sentence.",
                    "Neighbour is a noun, carries is a verb, and caring and heavy are adjectives.",
                    [
                        evidence("Labels neighbour.", "Neighbour is a noun", "neighbour names a person"),
                        evidence("Labels carries.", "carries is a verb", "carries shows action"),
                        evidence("Labels caring.", "caring is an adjective", "caring describes the neighbour"),
                        evidence("Labels heavy.", "heavy is an adjective", "heavy describes the basket"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:harmony_sentence_builder": {
        "transfer": _open_set(
            [
                (
                    "Word set: before assembly / our class / shares / the art supplies",
                    "Build a sharing sentence that keeps the class, supplies, and time detail.",
                    "Our class shares the art supplies before assembly.",
                    [
                        evidence("Uses natural subject-action order.", "Our class shares the art supplies", "class shares"),
                        evidence("Keeps the time phrase.", "before assembly", "supplies before assembly"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Unfinished question: how can we help the new student",
                    "Add the capital beginning and correct end mark.",
                    "How can we help the new student?",
                    [
                        evidence("Uses the capital opening.", "How can", "How"),
                        evidence("Uses the question ending.", "new student?", "student?"),
                    ],
                ),
                (
                    "Word set: gently / Mira / places / the sleeping kitten / on a mat",
                    "Build one correctly ordered caring sentence.",
                    "Mira gently places the sleeping kitten on a mat.",
                    [
                        evidence("Orders the person and action.", "Mira gently places", "Mira places"),
                        evidence("Keeps the animal and place.", "sleeping kitten on a mat", "kitten on a mat"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:small_kind_action_writer": {
        "transfer": _open_set(
            [
                (
                    "The class library has twelve mixed books and three empty labelled baskets. Four learners have ten minutes before the next lesson.",
                    "Write a practical two-sentence plan showing how small actions help.",
                    "Each learner can sort three books into the labelled baskets. Their small turns will organise all twelve books before the lesson.",
                    [
                        evidence("Uses the shared amount.", "Each learner can sort three books", "three books"),
                        evidence("Uses the labelled baskets.", "into the labelled baskets", "labelled baskets"),
                        evidence("States the combined result.", "organise all twelve books before the lesson", "all twelve books"),
                    ],
                )
            ],
            interaction="paragraph_text",
        ),
        "review": _open_set(
            [
                (
                    "A classmate's pencil box opens and pencils roll under two desks. The bell will ring in five minutes, and three children are nearby.",
                    "Write a kind group response with a reason.",
                    "The three children can each collect a few pencils because working together will refill the box before the bell.",
                    [
                        evidence("Uses the nearby helpers.", "three children can each collect a few pencils", "three children"),
                        evidence("States the shared action.", "collect a few pencils", "refill the box"),
                        evidence("Uses the time reason.", "before the bell", "bell will ring"),
                    ],
                ),
                (
                    "The community garden needs thirty seed labels. Six families can make five labels each from clean ice-cream sticks.",
                    "Explain a fair plan and its complete result.",
                    "Each family can make five labels from clean sticks, so six equal contributions will provide all thirty garden labels.",
                    [
                        evidence("States each family's part.", "Each family can make five labels", "five labels"),
                        evidence("Uses the supplied material.", "from clean sticks", "clean ice-cream sticks"),
                        evidence("States the total result.", "provide all thirty garden labels", "all thirty"),
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
            choice_task("The result is cumulative because each new part adds to what is already there.", "Which meaning fits cumulative?", "growing by added parts", ["vanishing at once", "remaining completely separate"], skills=[S["word_context"]]),
            choice_task("Mira adds water while Om adds soil. Only Om uses the small scoop.", "Who uses the scoop?", "Om", ["Mira", "both children"], skills=[S["comprehension"]]),
            choice_task("First one seed is planted, next it is watered, and last a shoot appears.", "Which event happens second?", "The seed is watered.", ["The seed is planted.", "A shoot appears."], skills=[S["sequence"]]),
            choice_task("Sentence frame: One kind ___ can help a lonely classmate.", "Which chapter word names an action?", "deed", ["ocean", "grain"], skills=[S["word_use"]]),
            choice_task("Candidates: kindness, kindnes, kyndness. The sentence names caring behaviour.", "Which spelling is standard?", "kindness", ["kindnes", "kyndness"], skills=[S["spelling"]]),
            choice_task("The tiny drop fills the mark slowly.", "Which word describes the drop?", "tiny", ["drop", "fills"], skills=[S["word_jobs"]]),
            open_task("Word set: each / small stream / joins / the / river", "Arrange the complete statement.", "Each small stream joins the river.", [evidence("Starts with the complete subject.", "each small stream", "small stream"), evidence("Places the action and destination after the subject.", "joins the river", "the river")], skills=[S["sentence_order"]]),
            open_task("Unfinished question: how many grains are here", "Add the correct sentence boundaries.", "How many grains are here?", [evidence("Uses a capital beginning.", "How"), evidence("Uses a question mark.", "?")], skills=[S["punctuation"]]),
            open_task("Action: Each learner writes one friendly word. Effect: a welcome poster is completed.", "Explain how the class reaches the poster result.", "Each learner writes one friendly word, and together the words complete the welcome poster.", [evidence("Names one word from each learner.", "each learner", "one friendly word"), evidence("Connects words to the poster.", "complete the welcome poster")], skills=[S["sentence"]]),
            open_task("One cup is added daily, seven cups collect, and the stored water later serves three plants.", "Retell the build-up and final use in order.", "One cup is added each day, seven cups collect, and the water later serves three plants.", [evidence("States one cup each day.", "one cup", "each day"), evidence("Connects seven cups to three plants.", "seven cups", "three plants")], skills=[S["comprehension"], S["sequence"]], ordered=True),
            open_task("Generous means willing to share. Use generous with a correctly spelled chapter word.", "State the meaning and create the new use.", "Generous means willing to share. A generous child offers grain for the bird tray.", [evidence("Explains willing to share.", "willing to share"), evidence("Uses generous and grain accurately.", "generous child", "grain")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
            open_task("Word set: why / does / every / little / effort / matter", "Build the finished question and close it correctly.", "Why does every little effort matter?", [evidence("Uses the supplied question order.", "why does every little effort matter"), evidence("Uses capital and question mark.", "Why", "?")], skills=[S["sentence_order"], S["punctuation"]]),
        ]
    return [
        choice_task("The effort is gradual, changing slowly through several small steps.", "Which meaning fits gradual?", "happening slowly in steps", ["finished before it starts", "broken into unrelated facts"], skills=[S["word_context"]]),
        choice_task("Rina fills cups while Kabir counts grains. Only Rina closes the tap.", "Who closes the tap?", "Rina", ["Kabir", "both children"], skills=[S["comprehension"]]),
        choice_task("A drop falls, joins another drop, and finally the small pool reaches the line.", "What happens immediately before the pool reaches the line?", "The drop joins another drop.", ["A drop falls.", "The line disappears."], skills=[S["sequence"]]),
        choice_task("Sentence frame: The team works in ___ while sharing tasks.", "Which chapter word means peaceful cooperation?", "harmony", ["wrapper", "shadow"], skills=[S["word_use"]]),
        choice_task("Candidates: pleasant, pleasent, plesent. The sentence describes an enjoyable place.", "Which spelling is standard?", "pleasant", ["pleasent", "plesent"], skills=[S["spelling"]]),
        choice_task("The patient farmer gathers tiny grains.", "Which word shows the action?", "gathers", ["patient", "farmer"], skills=[S["word_jobs"]]),
        open_task("Word set: deeds / smiles / small / spread", "Arrange the complete statement.", "Small deeds spread smiles.", [evidence("Uses correct statement order.", "small deeds spread smiles"), evidence("Uses every word.", "small", "smiles")], skills=[S["sentence_order"]]),
        open_task("Unfinished line: one drop can join many others", "Repair both sentence boundaries.", "One drop can join many others.", [evidence("Uses a capital beginning.", "One"), evidence("Uses a full stop.", ".")], skills=[S["punctuation"]]),
        open_task("Action: Every family adds one seed. Effect: the community bed has enough seeds for one row.", "Write one complete combined-contribution sentence.", "Every family adds one seed, and together the seeds fill one garden row.", [evidence("Names one seed per family.", "every family", "one seed"), evidence("Connects seeds to one row.", "fill one garden row")], skills=[S["sentence"]]),
        open_task("A class saves one sheet per day, gathers ten sheets, and uses them for a draft booklet.", "Give the repeated action and final use in order.", "The class saves one sheet daily, gathers ten sheets, and uses them for a draft booklet.", [evidence("States one sheet daily.", "one sheet", "daily"), evidence("Connects ten sheets to booklet.", "ten sheets", "draft booklet")], skills=[S["comprehension"], S["sequence"]], ordered=True),
        open_task("Accumulate means collect over time. Use accumulate with a correctly spelled amount word.", "State the meaning and write the new use.", "Accumulate means collect over time. Small drops accumulate inside the covered jar.", [evidence("Explains collect over time.", "collect over time"), evidence("Uses drops and accumulate accurately.", "drops accumulate", "covered jar")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
        open_task("Word set: where / does / rainwater / collect / after / the shower", "Build the finished question with correct punctuation.", "Where does rainwater collect after the shower?", [evidence("Uses correct question order.", "where does rainwater collect", "collect after the shower"), evidence("Uses capital and question mark.", "Where does rainwater", "after the shower?")], skills=[S["sentence_order"], S["punctuation"]]),
    ]


CONFIG = {
    "chapter_id": CHAPTER_ID,
    "chapter_no": 12,
    "title": "Little Drops of Water",
    "unit_title": "Harmony",
    "source_url": SOURCE_URL,
    "extract_path": "/tmp/zidd-ncert-class2-3/eng_c2_ch12.txt",
    "source_anchors": [
        {"anchor_id": f"{CHAPTER_ID}:song:1", "section_label": "Song: small drops, grains, kindness, and larger results", "page_start": 1, "page_end": 1, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:speak:2", "section_label": "Let us speak: water uses and scene description", "page_start": 2, "page_end": 2, "source_url": SOURCE_URL, "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:listen:3", "section_label": "Let us listen: teacher-led colouring directions", "page_start": 3, "page_end": 3, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:draw:4", "section_label": "Let us draw: idea for a more beautiful earth", "page_start": 4, "page_end": 4, "source_url": SOURCE_URL, "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:write:5-6", "section_label": "Let us write: amount phrases, containers, sentence order, and punctuation", "page_start": 5, "page_end": 6, "source_url": SOURCE_URL, "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:project:7", "section_label": "Project: offline kitchen texture exploration", "page_start": 7, "page_end": 7, "source_url": SOURCE_URL, "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
    ],
    "levels": LEVELS,
    "assessment_forms": [_assessment_form("a"), _assessment_form("b")],
}


MANIFEST = build_manifest(CONFIG)
