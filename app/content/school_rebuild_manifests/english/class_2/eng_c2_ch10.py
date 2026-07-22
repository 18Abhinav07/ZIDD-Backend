"""Original deep manifest for Class 2 English Chapter 10, The Crow."""

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
CHAPTER_ID = "eng_c2_ch10"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/bemr110.pdf"


LEVELS: list[dict[str, Any]] = [
    {
        "level_id": f"{CHAPTER_ID}:feather_choice_chain",
        "title": "Track the crow's choices",
        "focus": "follow a bird's actions, results, and changing understanding in order",
        "outcome": "Retell an action chain and explain from visible clues how a character's feeling or decision changes.",
        "skill_ids": [S["comprehension"], S["sequence"]],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:poem:1-2", f"{CHAPTER_ID}:speak:3"],
        "principle": "A character change becomes clear when the reader links choice, result, and response in order rather than judging appearance alone.",
        "connect": {
            "teaching_block": "Stories about self-worth often show a character trying a change, seeing its result, and learning from a caring response.",
            "passage": "A young crow hides his glossy black wing under a bright leaf. The leaf falls, and his flock praises how bravely he warned them of danger.",
            "prompt": "Notice the crow's choice, the result, and the flock's reason for praise.",
        },
        "co": choice_task(
            "Melu pins a blue feather beside her brown feathers. It slips during flight, but her friend says her steady landing matters more.",
            "What happens immediately after the blue feather slips?",
            "Her friend praises the steady landing.",
            ["Melu grows a new blue wing.", "The friend hides every feather."],
        ),
        "guided": [
            choice_task(
                "A crow collects shiny threads, ties them around his tail, and trips on one loose strand. He removes the threads before flying home.",
                "Which action happens last?",
                "He removes the threads.",
                ["He collects shiny threads.", "He ties them around his tail."],
            ),
            open_task(
                "Kavi paints one feather gold to impress a flock. Rain washes the colour away, and the flock still welcomes him because he shares food.",
                "Retell the three events and state the clue showing why Kavi is accepted.",
                "Kavi paints a feather, rain removes the colour, and the flock accepts him because he shares food.",
                [
                    evidence("Orders painting before rain.", "paints a feather", "rain removes", "rain washes"),
                    evidence("Links acceptance to sharing food.", "accepts him because he shares food", "welcomes him for sharing")
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set(
            [
                (
                    "A small crow borrows a ribbon, struts beside the pond, and loses the ribbon in a gust. Later he guides two chicks safely to a branch.",
                    "Sequence the crow's actions and identify the action that shows a good quality.",
                    "The crow borrows and loses the ribbon, then guides two chicks safely to a branch. This shows care.",
                    [
                        evidence("Keeps borrowing before losing.", "borrows", "loses the ribbon"),
                        evidence("Names guiding chicks as the caring action.", "guides two chicks", "shows care")
                    ],
                ),
                (
                    "Rumi adds three coloured leaves to her nest. The leaves blow away, but her careful weaving keeps every egg secure.",
                    "Explain the contrast between the decoration and the useful quality.",
                    "The coloured leaves disappear, but Rumi's careful weaving protects the eggs.",
                    [
                        evidence("States that the leaves blow away.", "leaves blow away", "leaves disappear"),
                        evidence("Links careful weaving to safe eggs.", "careful weaving", "protects the eggs")
                    ],
                ),
            ],
            ordered=True,
        ),
        "transfer": _open_set(
            [
                (
                    "A plain brown dog wears a sparkling collar for a show. The collar breaks, yet the dog finds a lost child by following footprints.",
                    "Transfer the action-result lesson and explain what truly earns praise.",
                    "The collar breaks, then the dog's tracking action helps find the child and earns praise.",
                    [
                        evidence("Includes the broken decoration.", "collar breaks"),
                        evidence("Links praise to finding the child.", "tracking action", "find the child", "earns praise")
                    ],
                ),
                (
                    "A bicycle has bright streamers, but one wheel is loose. Its owner removes the streamers and asks an adult to repair the wheel first.",
                    "Sequence the safer decision and explain why it matters more than decoration.",
                    "The owner notices the loose wheel, removes the streamers, and seeks repair because safety matters more than decoration.",
                    [
                        evidence("Orders noticing before repair.", "loose wheel", "seeks repair"),
                        evidence("States the safety-over-decoration idea.", "safety matters more", "more than decoration")
                    ],
                ),
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "A crow covers his black tail with flower petals. The petals fall during a storm, and he then shelters a wet sparrow under his wing.",
                    "Retell the events and identify the quality shown at the end.",
                    "The crow adds petals, loses them in the storm, and finally shows kindness by sheltering the sparrow.",
                    [
                        evidence("Orders petals before the storm.", "adds petals", "loses them"),
                        evidence("Names kindness in sheltering.", "shows kindness", "sheltering the sparrow")
                    ],
                ),
                (
                    "Tara admires a bird's bright crest. After watching longer, she also notices that the bird patiently feeds its chicks.",
                    "Compare the first noticed feature with the later valued action.",
                    "Tara first notices the bright crest, but later values the bird's patient care for its chicks.",
                    [
                        evidence("States the bright crest first.", "bright crest"),
                        evidence("Contrasts it with patient care.", "patient care", "feeds its chicks")
                    ],
                ),
            ],
            ordered=True,
        ),
        "cluster_id": f"{CHAPTER_ID}:appearance_action_sequence",
        "misconception": "The learner remembers only the colourful object, skips the action-result chain, or claims that appearance alone explains acceptance.",
        "remediation": "Use three boxes for choice, result, and caring response; underline the action that shows a quality before stating why the character is accepted.",
        "support": _open_set(
            [
                ("A crow adds a red leaf, the wind removes it, and the crow then warns the flock about a cat.", "Order the events and name the useful final action.", "The crow adds and loses the leaf, then usefully warns the flock about a cat.", [evidence("Keeps leaf events before warning.", "adds", "loses the leaf", "warns the flock")]),
                ("A peahen has plain feathers and patiently leads her chicks away from a road.", "State the visible feature and the caring action.", "The peahen has plain feathers, but she shows care by leading her chicks away from danger.", [evidence("Includes plain feathers and safe leading.", "plain feathers", "leading her chicks", "danger")]),
                ("A crow wears a paper crown. Rain softens it, so he removes it before flying.", "Give the cause and result in order.", "Rain softens the paper crown, so the crow removes it before flying.", [evidence("Links rain to removing the crown.", "rain softens", "removes it")]),
                ("The flock welcomes Kalu after he shares grain with a hungry bird.", "Explain the stated reason for the welcome.", "The flock welcomes Kalu because he shares grain with a hungry bird.", [evidence("Uses sharing as the acceptance reason.", "because he shares grain", "hungry bird")]),
                ("First a bird boasts about a ribbon. Later she returns a fallen chick to its nest.", "Which later action shows a caring quality, and why?", "Returning the fallen chick shows care because the action keeps it safe.", [evidence("Names the return and safety result.", "returning the fallen chick", "keeps it safe")]),
            ],
            ordered=True,
        ),
    },
    {
        "level_id": f"{CHAPTER_ID}:bird_words_in_context",
        "title": "Understand bird and quality words",
        "focus": "infer feather, flock, admire, strut, and accept from visible context",
        "outcome": "Explain a bird or character-quality word from its sentence clue and use it accurately in a new idea.",
        "skill_ids": [S["word_context"], S["word_use"]],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [f"{CHAPTER_ID}:poem:1-2", f"{CHAPTER_ID}:speak:3"],
        "principle": "A nearby action or result reveals a word's meaning; a new sentence must preserve that exact bird or quality meaning.",
        "connect": {
            "teaching_block": "Do not guess from a word's sound. Read the action, description, or result placed beside it.",
            "passage": "The bird begins to strut, walking proudly with its head held high.",
            "prompt": "Notice how walking proudly explains strut before continuing.",
        },
        "co": choice_task("A flock of mynas rises together; the whole group turns toward the banyan tree.", "Which meaning fits flock?", "a group of birds", ["one loose feather", "a bird's sharp call"]),
        "guided": [
            choice_task("The children admire the crow's clever nest and speak warmly about its careful design.", "Which phrase explains admire?", "think highly of", ["try to damage", "forget completely"]),
            open_task("A feather is one light piece covering a bird's body; this one falls from a wing.", "Define feather from context and use it in a fresh bird sentence.", "A feather is a light body covering. One grey feather rested beside the nest.", [evidence("Defines the light bird covering.", "light body covering", "covering a bird"), evidence("Uses feather in a bird setting.", "grey feather", "feather beside the nest")]),
        ],
        "independent": _open_set([
            ("The flock accepts the new crow, allowing him to rest and feed beside everyone else.", "Explain accepts and use it in another belonging sentence.", "Accepts means welcomes or includes. The team accepts Mira as a new member.", [evidence("Defines welcome or include.", "welcomes", "includes"), evidence("Uses accepts for belonging.", "team accepts", "group accepts")]),
            ("Malu boasts about his shiny tail, speaking as if his feathers make him better than every bird.", "Infer boasts and write a different accurate use.", "Boasts means speaks too proudly. Malu boasts that his nest is the finest.", [evidence("Defines too-proud speech.", "speaks too proudly", "talks proudly"), evidence("Uses boasts for proud speech.", "boasts that")]),
        ]),
        "transfer": _open_set([
            ("The class values Neeraj's patience, considering that quality important during group work.", "Transfer the meaning of values to a bird-quality sentence.", "Values means considers important. The flock values the crow's courage.", [evidence("Defines considers important.", "considers important"), evidence("Uses values with a bird quality.", "flock values", "crow's courage")]),
            ("A disguise changes how an actor appears so that others may not recognise the person.", "Explain disguise and use it for a bird scene.", "A disguise changes appearance. Leaves made a temporary disguise around the crow's tail.", [evidence("Explains changed appearance.", "changes appearance"), evidence("Uses disguise with the crow.", "disguise", "crow's tail")]),
        ]),
        "review": _open_set([
            ("The friends reassure Chiku, telling him again that his black feathers are fine and he is welcome.", "Explain reassure and use it in a new caring response.", "Reassure means help someone stop worrying. The flock reassures Chiku by welcoming him.", [evidence("Defines reducing worry.", "stop worrying", "feel less worried"), evidence("Uses reassures with welcome.", "flock reassures", "welcoming him")]),
            ("A bird is unique because its markings and habits are not exactly the same as another bird's.", "State the context meaning and create a new use.", "Unique means one of a kind. Each crow has a unique call and pattern.", [evidence("Defines one of a kind.", "one of a kind", "not exactly the same"), evidence("Uses unique for a bird feature.", "unique call", "unique pattern")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:bird_word_context_gap",
        "misconception": "The learner chooses a related bird word without using the sentence clue or uses a quality word as if it named a visible body part.",
        "remediation": "Underline the clue action, replace the target with a plain meaning, and test that meaning in one new sentence about a bird or caring quality.",
        "support": _open_set([
            ("The crow perches on a branch, resting with both feet around it.", "Explain perches from the visible action.", "Perches means rests on a raised place such as a branch.", [evidence("Defines resting on a raised place.", "rests on", "raised place", "branch")]),
            ("A glossy wing looks smooth and shiny in sunlight.", "Define glossy and use it for a feather.", "Glossy means smooth and shiny. The crow has one glossy black feather.", [evidence("Defines and uses smooth shine.", "smooth and shiny", "glossy black feather")]),
            ("The flock teases a bird by making unkind jokes about his leaf hat.", "Explain teases using the context.", "Teases means makes unkind jokes about someone.", [evidence("Names the unkind-joke meaning.", "unkind jokes", "makes jokes")]),
            ("The crow removes the borrowed ribbon, taking it off his tail.", "Define removes and use it with a feather.", "Removes means takes away. The bird removes a loose feather from the nest.", [evidence("Defines and uses taking away.", "takes away", "removes a loose feather")]),
            ("Her friends appreciate her kindness and show that they are thankful for it.", "Explain appreciate and transfer it to a flock.", "Appreciate means value with gratitude. The flock appreciates the crow's helpful warning.", [evidence("Defines value with gratitude.", "value with gratitude", "thankful"), evidence("Uses appreciates with helpful action.", "flock appreciates", "helpful warning")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:printed_bird_spellings",
        "title": "Build bird-word spellings",
        "focus": "use visible chunks and rhyme patterns to spell bird vocabulary",
        "outcome": "Produce a standard bird-word spelling from printed evidence and use it accurately in a complete sentence.",
        "skill_ids": [S["spelling"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:listen:6", f"{CHAPTER_ID}:write-rhyme:7"],
        "principle": "Printed syllable chunks and rhyme patterns support spelling here; no audio, clapping, or spoken performance is certified.",
        "connect": {
            "teaching_block": "Join every visible chunk, check the whole word, and confirm that it fits the bird sentence.",
            "passage": "Printed chunks: fea + ther = feather; col + our + ful = colourful.",
            "prompt": "Notice that no chunk disappears when the whole word is formed.",
        },
        "co": choice_task("Candidates: peacock, peecock, peakok. The sentence names a colourful bird.", "Which candidate is the standard bird spelling?", "peacock", ["peecock", "peakok"]),
        "guided": [
            choice_task("Candidates: sparrow, sparow, sparroe. The clue names a small brown bird.", "Which spelling fits the clue?", "sparrow", ["sparow", "sparroe"]),
            open_task("Chunks: beau + ti + ful. Meaning clue: pleasing to see.", "Join the chunks and use the completed word for a caring quality.", "The word is beautiful. A beautiful act can be kind and brave.", [evidence("Spells beautiful correctly.", "beautiful"), evidence("Uses it for an act or quality.", "beautiful act", "kind and brave")]),
        ],
        "independent": _open_set([
            ("Missing letters: f e a t h _ r. The clue names one light bird covering.", "Complete the word and use it in a sentence.", "The word is feather. A black feather lay near the tree.", [evidence("Spells feather correctly.", "feather"), evidence("Uses feather meaningfully.", "black feather", "feather lay")]),
            ("Scrambled letters: w r o c. The clue names the chapter bird.", "Unscramble the word and write one complete sentence.", "The word is crow. The crow carried a twig to its nest.", [evidence("Spells crow correctly.", "crow"), evidence("Uses crow in a complete action.", "crow carried", "crow built")]),
        ]),
        "transfer": _open_set([
            ("Rhyme clue: grow begins with g. Replace g with c to name a black bird.", "Build the new word and use it in a quality sentence.", "The word is crow. The crow is clever and watchful.", [evidence("Builds crow from the visible change.", "crow"), evidence("Uses crow with a quality.", "clever", "watchful")]),
            ("Base word: colour. Add ful to describe many bright colours.", "Build and use the new word in a bird sentence.", "The word is colourful. A colourful bird rested near the pond.", [evidence("Builds colourful correctly.", "colourful"), evidence("Uses it to describe a bird.", "colourful bird")]),
        ]),
        "review": _open_set([
            ("Correct the printed word anothar in a sentence about one more feather.", "Write the corrected word and full sentence.", "The corrected word is another. The crow found another feather.", [evidence("Corrects another.", "another"), evidence("Uses it with feather.", "another feather")]),
            ("Missing letters: w _ n g s. The clue names the two body parts used for flight.", "Complete the word and use it in a sentence.", "The word is wings. The crow spread its wings above the branch.", [evidence("Spells wings correctly.", "wings"), evidence("Uses wings for flight movement.", "spread its wings", "wings above")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:bird_chunk_spelling",
        "misconception": "The learner drops a printed syllable, changes a rhyme pattern inconsistently, or supplies a correctly spelled word that does not match the bird clue.",
        "remediation": "Point to every chunk or changed letter, rebuild the whole word, check the bird meaning, and use it in a short written sentence.",
        "support": _open_set([
            ("Chunks: pick + ed. The clue means lifted something from a place.", "Join and use the action word.", "The word is picked. The crow picked a twig from the path.", [evidence("Spells and uses picked.", "picked", "picked a twig")]),
            ("Chunks: col + our. The clue names what can be black, blue, or green.", "Build the word and write a sentence.", "The word is colour. Black is the crow's feather colour.", [evidence("Spells and uses colour.", "colour", "feather colour")]),
            ("Candidates: parrot, parot, parrrot. The clue names a bird with a curved beak.", "Write the standard spelling in a sentence.", "The word is parrot. A green parrot held a seed.", [evidence("Spells and uses parrot.", "parrot", "green parrot")]),
            ("Scrambled letters: v e l o. The clue names caring affection.", "Unscramble and use the word.", "The word is love. The flock shows love by welcoming the crow.", [evidence("Spells and uses love.", "love", "shows love")]),
            ("Correct this word: blak. The colour word needs c before k.", "Repair and use the colour word.", "The corrected word is black. The crow has glossy black feathers.", [evidence("Corrects and uses black.", "black", "black feathers")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:bird_word_jobs",
        "title": "Find jobs in bird sentences",
        "focus": "identify nouns, verbs, and adjectives in descriptions of birds and qualities",
        "outcome": "Classify requested words by their job in a visible sentence and justify the action or description link.",
        "skill_ids": [S["word_jobs"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:speak:3", f"{CHAPTER_ID}:write-sentences:8"],
        "principle": "Bird, feather, and quality words have jobs inside sentences: names are nouns, actions are verbs, and details are adjectives.",
        "connect": {
            "teaching_block": "Read the complete sentence before naming a word job. An important idea can still be a noun, verb, or adjective.",
            "passage": "The clever crow carries a thin twig. Crow and twig name, carries acts, and clever and thin describe.",
            "prompt": "Notice the naming, action, and describing evidence before continuing.",
        },
        "co": choice_task("A glossy feather shines.", "Which word describes the feather?", "glossy", ["feather", "shines"]),
        "guided": [
            choice_task("Three noisy crows gather nearby.", "Which word tells what the crows do?", "gather", ["noisy", "crows"]),
            open_task("The patient bird feeds hungry chicks.", "Label bird, feeds, patient, and hungry by job.", "Bird is a noun, feeds is a verb, and patient and hungry are adjectives.", [evidence("Labels bird and feeds.", "bird is a noun", "feeds is a verb"), evidence("Labels both adjectives.", "patient", "hungry")]),
        ],
        "independent": _open_set([
            ("A bright ribbon decorates the black tail.", "Classify ribbon, decorates, bright, and black.", "Ribbon is a noun, decorates is a verb, and bright and black are adjectives.", [evidence("Labels the noun and verb.", "ribbon is a noun", "decorates is a verb"), evidence("Labels bright and black.", "bright", "black")]),
            ("Kind friends welcome the worried crow.", "Identify the action and two describing words.", "Welcome is the action, and kind and worried are describing words.", [evidence("Names welcome as action.", "welcome is the action", "welcome is a verb"), evidence("Names kind and worried.", "kind", "worried")]),
        ]),
        "transfer": _open_set([
            ("A sturdy nest protects tiny eggs.", "Label sturdy, nest, protects, and tiny.", "Sturdy and tiny are adjectives, nest is a noun, and protects is a verb.", [evidence("Labels both adjectives.", "sturdy", "tiny"), evidence("Labels nest and protects.", "nest is a noun", "protects is a verb")]),
            ("The helpful dog finds a lost child.", "Transfer the word-job check to helpful, dog, and finds.", "Helpful is an adjective, dog is a noun, and finds is a verb.", [evidence("Classifies all three requested words.", "helpful is an adjective", "dog is a noun", "finds is a verb")]),
        ]),
        "review": _open_set([
            ("The proud crow struts beside the quiet pond.", "Identify the noun crow, action, and both describing words.", "Crow is a noun, struts is a verb, and proud and quiet are adjectives.", [evidence("Labels crow and struts.", "crow is a noun", "struts is a verb"), evidence("Labels proud and quiet.", "proud", "quiet")]),
            ("Soft feathers cover the dark wing.", "Classify feathers, cover, soft, and dark.", "Feathers is a noun, cover is a verb, and soft and dark are adjectives.", [evidence("Labels noun and verb.", "feathers is a noun", "cover is a verb"), evidence("Labels soft and dark.", "soft", "dark")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:bird_word_job_confusion",
        "misconception": "The learner labels every bird-related word a noun or treats a describing quality such as kind as an action.",
        "remediation": "Use the sentence tests who or what, what happens, and what kind; attach each answer to the exact word before labelling it.",
        "support": _open_set([
            ("The black crow hops.", "Label black, crow, and hops.", "Black is an adjective, crow is a noun, and hops is a verb.", [evidence("Labels all three jobs.", "black is an adjective", "crow is a noun", "hops is a verb")]),
            ("A loose feather falls.", "Which word describes the feather, and which word tells what happens?", "Loose describes the feather, and falls shows the action.", [evidence("Distinguishes loose and falls.", "loose describes", "falls shows")]),
            ("Friendly birds share grain.", "Classify friendly, birds, and share.", "Friendly is an adjective, birds is a noun, and share is a verb.", [evidence("Classifies all requested words.", "friendly is an adjective", "birds is a noun", "share is a verb")]),
            ("The colourful tail opens.", "Explain why colourful is not the action.", "Colourful describes the tail, while opens is the action.", [evidence("Contrasts description and action.", "colourful describes", "opens is the action")]),
            ("Brave Kalu warns the flock.", "Label brave, Kalu, and warns.", "Brave is an adjective, Kalu is a noun, and warns is a verb.", [evidence("Labels all three words.", "brave is an adjective", "Kalu is a noun", "warns is a verb")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:bird_sentence_builder",
        "title": "Arrange bird sentences",
        "focus": "order visible bird words and finish statements or questions correctly",
        "outcome": "Use every supplied word in sensible order, begin with a capital, and add the end mark required by the sentence purpose.",
        "skill_ids": [S["sentence_order"], S["punctuation"]],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:write-rhyme:7", f"{CHAPTER_ID}:write-sentences:8"],
        "principle": "Find the naming part and action, arrange the remaining details, then check capital and end punctuation.",
        "connect": {
            "teaching_block": "A bird sentence is complete only when the words form a clear idea and the written boundaries match a statement or question.",
            "passage": "Word set: crow / the / flies / home. Finished form: The crow flies home.",
            "prompt": "Notice the naming part, action, capital, and full stop.",
        },
        "co": choice_task("Word set: feathers / crow / the / collects", "Which option builds the complete crow statement?", "The crow collects feathers.", ["Feathers the crow collects.", "the Crow feathers collects"]),
        "guided": [
            choice_task("Word set: why / bird / strut / does / the", "Which option is a correctly punctuated question?", "Why does the bird strut?", ["Why the bird does strut.", "why does strut the bird?"]),
            open_task("Word set: flock / the / kind / welcomes / crow / the", "Arrange all words as one statement.", "The kind flock welcomes the crow.", [evidence("Uses complete correct order.", "kind flock welcomes the crow"), evidence("Adds capital and full stop.", "The", ".")]),
        ],
        "independent": _open_set([
            ("Word set: black / beautiful / are / feathers / the", "Build the complete statement about the feathers.", "The black feathers are beautiful.", [evidence("Uses the correct complete order.", "black feathers are beautiful"), evidence("Adds statement boundaries.", "The", ".")]),
            ("Word set: feather / where / find / crow / did / the / a", "Build and punctuate the complete question.", "Where did the crow find a feather?", [evidence("Uses correct question order.", "where did the crow find a feather"), evidence("Adds capital and question mark.", "Where", "?")]),
        ]),
        "transfer": _open_set([
            ("Word set: chicks / careful / protects / mother / the / her", "Transfer the ordering skill to a caring action.", "The careful mother protects her chicks.", [evidence("Uses all words in sensible order.", "careful mother protects her chicks"), evidence("Adds statement boundaries.", "The", ".")]),
            ("Word set: quality / admire / which / you / do", "Create the finished question.", "Which quality do you admire?", [evidence("Uses correct question order.", "which quality do you admire"), evidence("Adds capital and question mark.", "Which", "?")]),
        ]),
        "review": _open_set([
            ("Unfinished line: the friendly crows share grain", "Repair the sentence boundaries.", "The friendly crows share grain.", [evidence("Keeps the complete statement.", "friendly crows share grain"), evidence("Adds capital and full stop.", "The", ".")]),
            ("Jumbled line: tail / ribbon / the / did / lose / its / bird", "Write the ordered question with correct punctuation.", "Did the bird lose its tail ribbon?", [evidence("Uses correct question order.", "did the bird lose its tail ribbon"), evidence("Adds capital and question mark.", "Did", "?")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:bird_sentence_order_boundary",
        "misconception": "The learner keeps a rhyme-list order, drops a small supplied word, or adds a full stop to a question without checking purpose.",
        "remediation": "Box the bird or person, underline the action, place details around them, and run a final capital-plus-end-mark check.",
        "support": _open_set([
            ("Word set: crow / one / remains / quiet", "Build and finish the statement.", "One crow remains quiet.", [evidence("Builds and punctuates the statement.", "one crow remains quiet", "One", ".")]),
            ("Word set: is / feather / whose / this", "Build the ownership question.", "Whose feather is this?", [evidence("Builds and punctuates the question.", "whose feather is this", "Whose", "?")]),
            ("Line needing repair: kind friends accept Kalu", "Add correct sentence boundaries.", "Kind friends accept Kalu.", [evidence("Adds capital and full stop.", "Kind friends accept Kalu", ".")]),
            ("Word set: black / shines / wing / the", "Arrange the bird statement.", "The black wing shines.", [evidence("Uses every word in order.", "black wing shines", "The", ".")]),
            ("Line needing repair: what quality does the crow show", "Repair the crow-quality question and its end mark.", "What quality does the crow show?", [evidence("Adds capital and question mark.", "What quality does the crow show", "?")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:quality_sentence_writer",
        "title": "Write about real beauty",
        "focus": "construct complete evidence-based sentences about action, quality, and acceptance",
        "outcome": "Write a complete sentence that names a caring or useful action and the quality it shows, using only the visible reference.",
        "skill_ids": [S["comprehension"], S["sentence"]],
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:poem:1-2", f"{CHAPTER_ID}:speak:3"],
        "principle": "A fair quality sentence points to what someone does, then names the quality shown; appearance can be noticed without ranking people's worth.",
        "connect": {
            "teaching_block": "Words such as kind, brave, patient, and honest need action evidence. The reference supplies that evidence.",
            "passage": "A black crow waits beside an injured bird and brings it water twice.",
            "prompt": "Notice the repeated helpful action before deciding which quality it shows.",
        },
        "co": choice_task("A crow warns three chicks before a cat reaches the tree.", "Which sentence fairly connects action and quality?", "The crow shows care by warning the chicks.", ["The crow is best because it is black.", "The chicks make the crow colourful."], skills=[S["comprehension"]]),
        "guided": _open_set([
            ("A myna drops her own grain beside a hungry sparrow.", "Write one complete sentence naming the action and quality.", "The myna shows kindness by sharing her grain with the hungry sparrow.", [evidence("Names sharing grain.", "sharing her grain", "drops her grain"), evidence("Names kindness.", "shows kindness", "is kind")]),
            ("A crow keeps rebuilding a nest after strong wind moves the twigs.", "Describe the action and the quality it proves.", "The crow shows persistence by rebuilding the nest after the wind moves the twigs.", [evidence("Includes rebuilding after wind.", "rebuilding the nest", "after the wind"), evidence("Names persistence or determination.", "shows persistence", "determined")]),
        ]),
        "independent": _open_set([
            ("A plain grey bird guides a younger bird around a glass wall and waits until it is safe.", "Write a complete evidence-based quality sentence.", "The grey bird shows patience and care by guiding the younger bird and waiting for safety.", [evidence("Uses guiding and waiting actions.", "guiding the younger bird", "waiting"), evidence("Names patience or care.", "patience", "care")]),
            ("A colourful bird knocks seeds from a feeder, then returns and helps gather every seed.", "State the repaired action and the quality shown at the end.", "The bird shows responsibility by returning to gather the spilled seeds.", [evidence("Names returning and gathering.", "returning", "gather the spilled seeds"), evidence("Names responsibility.", "shows responsibility", "responsible")]),
        ]),
        "transfer": _open_set([
            ("A child wears a simple uniform and quietly helps a new learner find the classroom.", "Transfer the quality-writing pattern to the child.", "The child shows kindness by helping the new learner find the classroom.", [evidence("Names the helping action.", "helping the new learner", "find the classroom"), evidence("Names kindness.", "shows kindness", "kind")]),
            ("A bright kite tears, but its owner admits the mistake and repairs a friend's kite first.", "Write the honest action and quality as one complete idea.", "The owner shows honesty and fairness by admitting the mistake and repairing the friend's kite first.", [evidence("Includes admitting and repairing.", "admitting the mistake", "repairing the friend's kite"), evidence("Names honesty or fairness.", "honesty", "fairness")]),
        ]),
        "review": _open_set([
            ("A crow with one bent feather carries nest grass to an older bird every morning.", "Explain what the repeated action shows without judging the feather.", "The crow shows helpfulness by carrying nest grass to the older bird each morning.", [evidence("Uses the repeated carrying action.", "carrying nest grass", "each morning"), evidence("Names helpfulness.", "shows helpfulness", "helpful")]),
            ("Two birds look different, but both take turns guarding the same nest.", "Write a complete sentence about the shared quality and difference.", "The birds look different, but both show responsibility by taking turns guarding the nest.", [evidence("Acknowledges difference and shared action.", "look different", "both", "guarding the nest"), evidence("Names responsibility.", "show responsibility", "responsible")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:quality_without_action",
        "misconception": "The learner praises or rejects appearance without using the supplied action, or names a quality in a sentence fragment with no evidence.",
        "remediation": "Underline the helpful, brave, honest, or patient action; choose the matching quality; then write a complete who-did-what sentence.",
        "support": _open_set([
            ("A crow shares water with a thirsty pigeon.", "Write the action and quality in one sentence.", "The crow shows kindness by sharing water with the thirsty pigeon.", [evidence("Links sharing water to kindness.", "sharing water", "shows kindness")]),
            ("A bird waits beside its chick during a loud storm.", "Name the visible action and caring quality.", "The bird shows care by staying beside its chick during the storm.", [evidence("Links staying nearby to care.", "staying beside", "shows care")]),
            ("Kalu returns a feather that belongs to another bird.", "Write the honest choice as a complete sentence.", "Kalu shows honesty by returning the other bird's feather.", [evidence("Links returning to honesty.", "returning", "shows honesty")]),
            ("A small bird tries three times before lifting a heavy twig.", "Describe the repeated effort and quality.", "The bird shows determination by trying three times to lift the twig.", [evidence("Links three tries to determination.", "trying three times", "shows determination")]),
            ("The flock welcomes a new bird and makes space on the branch.", "Write the acceptance action and quality.", "The flock shows inclusion by welcoming the bird and making space.", [evidence("Links welcome and space to inclusion.", "welcoming the bird", "making space", "inclusion")]),
        ]),
    },
]


EXTRA_DEPTH = {
    f"{CHAPTER_ID}:feather_choice_chain": {
        "guided": [
            choice_task(
                "A crow ties grass around his tail to look grand. The grass falls off, and he later guides a young bird away from a kite string.",
                "Which event shows the crow's useful change?",
                "He guides the young bird away from the string.",
                ["He ties grass around his tail.", "The grass falls off."],
            ),
            open_task(
                "Mira admires a bird's painted ring. Rain washes the paint away, but the bird still shares its dry shelter with two finches.",
                "Retell the change and explain which action shows a lasting quality.",
                "Rain removes the painted ring, but sharing the dry shelter shows the bird's lasting kindness.",
                [
                    evidence("States the visible change.", "rain removes the painted ring", "paint washes away in rain"),
                    evidence("Names the helpful action.", "sharing the dry shelter", "shares shelter with the finches"),
                    evidence("Names the lasting quality.", "lasting kindness", "shows kindness"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set([
            (
                "A rook borrows a bright bell to gain attention. The bell snags on a twig, so she leaves it and then calls loudly when a cat nears the nest.",
                "Sequence the choice, problem, and helpful response.",
                "The rook borrows the bell, leaves it after it snags, and then helps by warning the nest about the cat.",
                [
                    evidence("States the first choice.", "borrows the bell", "takes the bright bell first"),
                    evidence("States the problem response.", "leaves it after it snags", "bell snags so she leaves it"),
                    evidence("States the helpful ending.", "warns the nest about the cat", "calls when the cat nears"),
                ],
            ),
            (
                "A plain pigeon is ignored beside a decorated cage. During a gust, the pigeon pushes a loose latch shut and keeps the smaller birds safe.",
                "Explain why the final action matters more than the decoration.",
                "The cage is decorated, but the plain pigeon proves helpful by shutting the latch and keeping the smaller birds safe.",
                [
                    evidence("Contrasts the appearances.", "cage is decorated", "plain pigeon"),
                    evidence("Names the useful action.", "shutting the latch", "pushes the loose latch shut"),
                    evidence("States the safe result.", "keeps the smaller birds safe", "smaller birds stay safe"),
                ],
            ),
        ], ordered=True),
        "transfer": _open_set([
            (
                "A child chooses a shiny lunch box with a weak clasp. After it opens, she uses a plain box that closes firmly and keeps the food secure.",
                "Transfer the appearance-and-action lesson to the two boxes.",
                "The shiny box looks attractive but opens, while the plain box has a firm clasp that keeps the food secure.",
                [
                    evidence("States the shiny-box problem.", "shiny box opens", "weak clasp lets it open"),
                    evidence("States the plain-box strength.", "plain box has a firm clasp", "plain box closes firmly"),
                    evidence("States the useful result.", "keeps the food secure", "food stays safe inside"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:bird_words_in_context": {
        "guided": [
            choice_task(
                "The heron glides above the lake, moving smoothly without flapping for several moments.",
                "Which meaning fits glides?",
                "moves smoothly through the air",
                ["pecks at hard seeds", "calls in a rough voice"],
            ),
            open_task(
                "The flock shelters a tired bird by making a dry space for it beneath the thick branches.",
                "Explain shelters and use it in a new caring sentence.",
                "Shelters means gives a protected place. A broad leaf shelters two chicks from rain.",
                [
                    evidence("Explains shelters.", "gives a protected place", "keeps someone safe under cover"),
                    evidence("Uses shelters freshly.", "broad leaf shelters two chicks", "leaf keeps the chicks safe from rain"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "The myna is wary of the open trap; it pauses and watches because it senses possible danger.",
                "Infer wary and use it in another bird situation.",
                "Wary means careful about possible danger. A wary sparrow checks the ground before landing.",
                [
                    evidence("Explains wary.", "careful about possible danger", "watchful because danger may be near"),
                    evidence("Uses wary accurately.", "wary sparrow checks the ground", "sparrow watches before landing"),
                ],
            ),
            (
                "The chicks imitate their mother, copying the way she taps the shell to open a seed.",
                "Explain imitate and create a different accurate use.",
                "Imitate means copy an action. The young crow imitates an older bird's careful hop.",
                [
                    evidence("Explains imitate.", "means copy an action", "do an action in the same way"),
                    evidence("Uses imitate freshly.", "young crow imitates an older bird", "crow copies the careful hop"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "A dependable teammate can be trusted to complete a promised job each time.",
                "Infer dependable and use it for a helpful bird.",
                "Dependable means able to be trusted. The dependable crow warns the flock whenever danger appears.",
                [
                    evidence("Explains dependable.", "able to be trusted", "can be trusted to help"),
                    evidence("Transfers the word.", "dependable crow warns the flock", "crow can be trusted to warn others"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:printed_bird_spellings": {
        "guided": [
            choice_task(
                "Candidates: pigeon, pidgeon, pigen. The sentence names a common city bird.",
                "Which candidate has the standard spelling?",
                "pigeon",
                ["pidgeon", "pigen"],
            ),
            open_task(
                "Visible chunks: gen + tle. The clue describes a soft, careful action.",
                "Join the chunks and use the completed word for a bird.",
                "The word is gentle. The gentle bird feeds the smallest chick first.",
                [
                    evidence("Builds the spelling.", "word is gentle", "spell it gentle"),
                    evidence("Uses gentle accurately.", "gentle bird feeds the smallest chick", "bird acts gently with the chick"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Missing letters: k i n d n _ s s. The clue names caring behaviour.",
                "Complete the word and show its meaning in a sentence.",
                "The word is kindness. Sharing grain with a hungry bird shows kindness.",
                [
                    evidence("Completes the spelling.", "word is kindness", "spell it kindness"),
                    evidence("Shows the meaning.", "sharing grain shows kindness", "kindness is shown by feeding a hungry bird"),
                ],
            ),
            (
                "Scrambled letters: n e s t. The clue names a bird's home for eggs or chicks.",
                "Unscramble the word and use it in a complete action sentence.",
                "The word is nest. Two swallows repair their nest with dry grass.",
                [
                    evidence("Unscrambles the word.", "word is nest", "spell it nest"),
                    evidence("Uses nest meaningfully.", "swallows repair their nest", "birds fix a nest with grass"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Base word: care. Add ful to describe someone who acts with attention.",
                "Build the new word and use it for a bird's safe action.",
                "The new word is careful. A careful crow checks the road before crossing.",
                [
                    evidence("Builds the new spelling.", "new word is careful", "spell it careful"),
                    evidence("Uses careful in context.", "careful crow checks the road", "crow acts carefully before crossing"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:bird_word_jobs": {
        "guided": [
            choice_task(
                "The alert parrot watches the open window.",
                "Which word describes the parrot?",
                "alert",
                ["parrot", "watches"],
            ),
            open_task(
                "A noisy magpie carries a silver ring.",
                "Classify magpie, carries, noisy, and silver.",
                "Magpie is a noun, carries is a verb, and noisy and silver are adjectives.",
                [
                    evidence("Labels magpie.", "magpie is a noun", "magpie names a bird"),
                    evidence("Labels carries.", "carries is a verb", "carries shows action"),
                    evidence("Labels noisy.", "noisy is an adjective", "noisy describes the magpie"),
                    evidence("Labels silver.", "silver is an adjective", "silver describes the ring"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "The brave robin guards three tiny eggs.",
                "Give the jobs of robin, guards, brave, and tiny.",
                "Robin is a noun, guards is a verb, and brave and tiny are adjectives.",
                [
                    evidence("Labels robin.", "robin is a noun", "robin names a bird"),
                    evidence("Labels guards.", "guards is a verb", "guards shows action"),
                    evidence("Labels brave.", "brave is an adjective", "brave describes the robin"),
                    evidence("Labels tiny.", "tiny is an adjective", "tiny describes the eggs"),
                ],
            ),
            (
                "Patient storks build sturdy nests.",
                "Classify storks, build, patient, and sturdy.",
                "Storks is a noun, build is a verb, and patient and sturdy are adjectives.",
                [
                    evidence("Labels storks.", "storks is a noun", "storks name birds"),
                    evidence("Labels build.", "build is a verb", "build shows action"),
                    evidence("Labels patient.", "patient is an adjective", "patient describes storks"),
                    evidence("Labels sturdy.", "sturdy is an adjective", "sturdy describes nests"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "A thoughtful neighbour fills the empty bird bowl.",
                "Transfer the word-job check to neighbour, fills, thoughtful, and empty.",
                "Neighbour is a noun, fills is a verb, and thoughtful and empty are adjectives.",
                [
                    evidence("Labels neighbour.", "neighbour is a noun", "neighbour names a person"),
                    evidence("Labels fills.", "fills is a verb", "fills shows action"),
                    evidence("Labels thoughtful.", "thoughtful is an adjective", "thoughtful describes the neighbour"),
                    evidence("Labels empty.", "empty is an adjective", "empty describes the bowl"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:bird_sentence_builder": {
        "guided": [
            choice_task(
                "Word set: branch / the / quietly / crow / leaves / the",
                "Which option forms the complete statement?",
                "The crow leaves the branch quietly.",
                ["Crow the branch quietly leaves the.", "the crow Leaves quietly branch the"],
            ),
            open_task(
                "Word set: bird / which / shared / the / grain",
                "Arrange all words as a finished question.",
                "Which bird shared the grain?",
                [
                    evidence("Uses the question order.", "which bird shared the grain", "ask which bird shared grain"),
                    evidence("Uses a natural question ending.", "shared the grain?", "the grain?"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Word set: nest / repairs / careful / the / rook / the",
                "Build a complete bird-action statement.",
                "The careful rook repairs the nest.",
                [
                    evidence("Uses every word in order.", "careful rook repairs the nest", "the rook repairs the nest"),
                    evidence("Uses a natural statement ending.", "repairs the nest.", "the nest."),
                ],
            ),
            (
                "Line needing repair: why did the flock welcome him",
                "Add the correct beginning and end mark.",
                "Why did the flock welcome him?",
                [
                    evidence("Keeps the complete question.", "why did the flock welcome him", "ask why the flock welcomed him"),
                    evidence("Uses a natural question ending.", "welcome him?", "flock welcome him?"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Word set: gate / close / please / chicks / the / for / the",
                "Transfer the ordering steps to a caring request.",
                "Please close the gate for the chicks.",
                [
                    evidence("Uses the polite request order.", "please close the gate for the chicks", "close the gate for the chicks please"),
                    evidence("Uses a natural statement ending.", "for the chicks.", "the chicks."),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:quality_sentence_writer": {
        "guided": [
            choice_task(
                "Action card: A plain crow brings twigs to repair a nest after wind breaks it.",
                "Which sentence names the action and a quality it shows?",
                "Repairing the nest shows the crow's helpfulness.",
                ["The twigs make the crow colourful.", "A broken nest proves every bird is careless."],
                skills=[S["comprehension"]],
            ),
            open_task(
                "Action card: A myna waits while a smaller chick drinks first. Result: both birds get water safely.",
                "Write one sentence naming the action, result, and quality.",
                "By letting the smaller chick drink first, the myna shows patience and helps both birds drink safely.",
                [
                    evidence("Names the action.", "lets the smaller chick drink first", "waits for the smaller chick"),
                    evidence("Names the safe result.", "both birds drink safely", "both get water safely"),
                    evidence("Names the quality.", "shows patience", "patient action"),
                ],
                interaction="creative_continuation",
            ),
        ],
        "independent": _open_set([
            (
                "Action card: A pigeon calls the caretaker when string tangles around a sapling. Result: the string is removed without pulling the plant.",
                "Explain what the pigeon does and which quality the choice shows.",
                "The pigeon gets safe help, the string is removed without pulling the sapling, and the choice shows good judgement and care.",
                [
                    evidence("Names the safe action.", "calls the caretaker", "gets safe help"),
                    evidence("Names the plant result.", "string is removed without pulling the plant", "sapling is not pulled"),
                    evidence("Names a relevant quality.", "good judgement and care", "shows careful thinking"),
                ],
            ),
            (
                "Action card: One bird finds a single berry but divides it between two hungry nestlings.",
                "Write a complete response linking the action to a quality.",
                "The bird shows generosity by dividing its berry between the two hungry nestlings.",
                [
                    evidence("Names the sharing action.", "dividing its berry", "shares the berry"),
                    evidence("Names both receivers.", "two hungry nestlings", "both hungry young birds"),
                    evidence("Names the quality.", "shows generosity", "generous action"),
                ],
            ),
        ], interaction="creative_continuation"),
        "transfer": _open_set([
            (
                "Action card: During group work, Nitin notices a quiet pupil has no scissors and offers his spare pair.",
                "Transfer the quality check to this classroom action.",
                "Nitin notices that the pupil has no scissors, offers his spare pair, and shows thoughtfulness.",
                [
                    evidence("Names what Nitin notices.", "pupil has no scissors", "notices the pupil's need"),
                    evidence("Names his response.", "offers his spare pair", "shares his spare scissors"),
                    evidence("Names the quality.", "shows thoughtfulness", "thoughtful action"),
                ],
            )
        ], interaction="creative_continuation"),
    },
}

LAUNCH_DEPTH = {
    f"{CHAPTER_ID}:feather_choice_chain": {
        "transfer": _open_set(
            [
                (
                    "For the nature display, Diya finds a loose feather, checks that no bird is nearby, asks the park guide, and places it in a clear box after permission.",
                    "Sequence Diya's careful choices from finding to display.",
                    "Diya finds the loose feather, checks for a bird, asks the guide, and after receiving permission, displays it.",
                    [
                        evidence("States the discovery.", "finds the loose feather", "Diya finds"),
                        evidence("States the bird check.", "checks for a bird", "no bird is nearby"),
                        evidence("States the permission step.", "asks the guide", "after receiving permission"),
                        evidence("States the final display.", "displays it", "places it in a clear box"),
                    ],
                )
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "A crow tests a thin twig, drops it when it bends, chooses a sturdy twig, and carries that twig to its nest.",
                    "Retell the choice chain and explain why the second twig fits.",
                    "The crow drops the bending twig, chooses the sturdy twig, and carries it because the second twig stays firm.",
                    [
                        evidence("States the rejected twig.", "drops the bending twig", "thin twig bends"),
                        evidence("States the new choice.", "chooses the sturdy twig", "sturdy twig"),
                        evidence("Explains the fit.", "because the second twig stays firm", "stays firm"),
                    ],
                ),
                (
                    "For a paper bird, Omar compares a heavy card wing with a light paper wing. He chooses the light wing because it moves in the fan's breeze.",
                    "Explain Omar's comparison, choice, and evidence.",
                    "Omar compares the heavy card with light paper and chooses the light wing because the fan can move it.",
                    [
                        evidence("States the comparison.", "compares", "heavy card with light paper"),
                        evidence("States the choice.", "chooses the light wing", "light wing"),
                        evidence("Uses the movement evidence.", "because the fan can move it", "moves in the fan's breeze"),
                    ],
                ),
            ],
            ordered=True,
        ),
    },
    f"{CHAPTER_ID}:bird_words_in_context": {
        "transfer": _open_set(
            [
                (
                    "The myna's glossy feathers look smooth and shiny when sunlight reaches them.",
                    "Explain glossy from the clue and use it for another object.",
                    "Glossy means smooth and shiny. The glossy blue tile reflected the window light.",
                    [
                        evidence("Explains glossy.", "smooth and shiny", "Glossy means"),
                        evidence("Uses glossy freshly.", "glossy blue tile reflected the window light", "glossy blue tile"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "A sturdy nest stays firm during strong wind because its twigs are thick and tightly joined.",
                    "State what sturdy means and use it in a school sentence.",
                    "Sturdy means strong and not easily broken. The sturdy book box held the heavy dictionaries.",
                    [
                        evidence("Explains sturdy.", "strong and not easily broken", "stays firm"),
                        evidence("Uses sturdy accurately.", "sturdy book box held the heavy dictionaries", "sturdy book box"),
                    ],
                ),
                (
                    "The children admire the tailorbird's neat nest, looking at it with warm approval without touching it.",
                    "Explain admire and write one respectful new use.",
                    "Admire means look at something with approval. We admire the mural from behind the safety line.",
                    [
                        evidence("Explains admire.", "look at something with approval", "warm approval"),
                        evidence("Uses admire respectfully.", "admire the mural from behind the safety line", "We admire the mural"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:printed_bird_spellings": {
        "transfer": _open_set(
            [
                (
                    "Visible chunks: fea + ther. The clue names one light covering from a bird's body.",
                    "Complete the bird word, then place it in a sentence about where it was found.",
                    "The word is feather. A small brown feather rested beside the garden path.",
                    [
                        evidence("Spells the target word.", "word is feather", "spell it feather"),
                        evidence("Uses feather accurately.", "small brown feather rested beside the garden path", "brown feather"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Base word: colour. Add ful to describe something with many bright colours.",
                    "Build the new word and use it for a bird picture.",
                    "The new word is colourful. A colourful bird picture hangs above the art shelf.",
                    [
                        evidence("Builds the spelling.", "new word is colourful", "spell it colourful"),
                        evidence("Uses colourful in context.", "colourful bird picture hangs above the art shelf", "colourful bird picture"),
                    ],
                ),
                (
                    "Candidates: graceful, gracefull, graseful. The sentence needs the word for smooth, elegant movement.",
                    "Choose the standard spelling and write a bird sentence.",
                    "The standard spelling is graceful. The graceful heron stepped slowly through the pond.",
                    [
                        evidence("Gives the standard spelling.", "standard spelling is graceful", "spell it graceful"),
                        evidence("Uses graceful accurately.", "graceful heron stepped slowly through the pond", "graceful heron"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:bird_word_jobs": {
        "transfer": _open_set(
            [
                (
                    "The alert robin watches a tiny insect.",
                    "Classify robin, watches, alert, and tiny.",
                    "Robin is a noun, watches is a verb, and alert and tiny are adjectives.",
                    [
                        evidence("Labels robin.", "Robin is a noun", "robin names a bird"),
                        evidence("Labels watches.", "watches is a verb", "watches shows action"),
                        evidence("Labels alert.", "alert is an adjective", "alert describes the robin"),
                        evidence("Labels tiny.", "tiny is an adjective", "tiny describes the insect"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "A noisy parrot cracks the hard seed.",
                    "Give the jobs of parrot, cracks, noisy, and hard.",
                    "Parrot is a noun, cracks is a verb, and noisy and hard are adjectives.",
                    [
                        evidence("Labels parrot.", "Parrot is a noun", "parrot names a bird"),
                        evidence("Labels cracks.", "cracks is a verb", "cracks shows action"),
                        evidence("Labels noisy.", "noisy is an adjective", "noisy describes the parrot"),
                        evidence("Labels hard.", "hard is an adjective", "hard describes the seed"),
                    ],
                ),
                (
                    "The patient watcher sketches a bright wing.",
                    "Name the noun, verb, and two adjectives in this sentence.",
                    "Watcher is a noun, sketches is a verb, and patient and bright are adjectives.",
                    [
                        evidence("Labels watcher.", "Watcher is a noun", "watcher names a person"),
                        evidence("Labels sketches.", "sketches is a verb", "sketches shows action"),
                        evidence("Labels patient.", "patient is an adjective", "patient describes the watcher"),
                        evidence("Labels bright.", "bright is an adjective", "bright describes the wing"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:bird_sentence_builder": {
        "transfer": _open_set(
            [
                (
                    "Word set: near the rain barrel / two sparrows / gather / dry grass",
                    "Build one bird sentence from all four word-set parts.",
                    "Two sparrows gather dry grass near the rain barrel.",
                    [
                        evidence("Uses natural subject-action order.", "Two sparrows gather dry grass", "sparrows gather"),
                        evidence("Keeps the place phrase.", "near the rain barrel", "grass near the rain barrel"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Unfinished question: which bird made this round nest",
                    "Add the capital beginning and correct end mark.",
                    "Which bird made this round nest?",
                    [
                        evidence("Uses the capital opening.", "Which bird", "Which"),
                        evidence("Uses the question ending.", "round nest?", "nest?"),
                    ],
                ),
                (
                    "Word set: gently / the young crow / opens / its wings",
                    "Build one correctly ordered movement sentence.",
                    "The young crow gently opens its wings.",
                    [
                        evidence("Orders the subject and action.", "young crow gently opens", "crow opens"),
                        evidence("Keeps the object.", "opens its wings", "its wings"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:quality_sentence_writer": {
        "transfer": _open_set(
            [
                (
                    "Bird-study cards: the weaverbird builds a tightly woven nest; the kingfisher dives quickly; the crow solves a lid puzzle.",
                    "Write two complete sentences comparing any two stated strengths.",
                    "The weaverbird is a careful builder with its woven nest. The crow is a clever problem-solver because it opens the lid.",
                    [
                        evidence("Uses one stated bird strength.", "weaverbird is a careful builder", "woven nest"),
                        evidence("Uses a second stated strength.", "crow is a clever problem-solver", "opens the lid"),
                    ],
                )
            ],
            interaction="paragraph_text",
        ),
        "review": _open_set(
            [
                (
                    "Mila's paper bird has plain grey wings, but its balanced folds let it glide farther than the decorated birds.",
                    "Write a complete sentence valuing the bird's useful quality.",
                    "Mila's grey paper bird is special because its balanced folds help it glide far.",
                    [
                        evidence("Names the useful quality.", "balanced folds", "folds help"),
                        evidence("States the result.", "help it glide far", "glide farther"),
                        evidence("Uses an accepting statement.", "paper bird is special because", "is special"),
                    ],
                ),
                (
                    "Three classmates contribute differently: Ritu draws clear labels, Samir measures carefully, and Noor explains the display kindly.",
                    "Write two sentences showing why different qualities help the group.",
                    "Ritu's clear labels and Samir's careful measuring make the display accurate. Noor's kind explanation helps visitors understand it.",
                    [
                        evidence("Uses the label strength.", "Ritu's clear labels", "clear labels"),
                        evidence("Uses the measuring strength.", "Samir's careful measuring", "careful measuring"),
                        evidence("Uses the explaining strength.", "Noor's kind explanation helps visitors", "kind explanation"),
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
            choice_task("The bird is modest; it does not boast about its clever nest.", "Which meaning fits modest?", "not boastful", ["very colourful", "unable to fly"], skills=[S["word_context"]]),
            choice_task("A black crow waits by the nest while a brown crow gathers twigs.", "Which crow gathers twigs?", "the brown crow", ["the black crow", "both crows"], skills=[S["comprehension"]]),
            choice_task("First the ribbon loosens, next it falls, and last the bird picks it up.", "Which event happens second?", "The ribbon falls.", ["The ribbon loosens.", "The bird picks it up."], skills=[S["sequence"]]),
            choice_task("Sentence frame: The flock ___ the helpful new bird.", "Which chapter word means welcomes into the group?", "accepts", ["scatters", "hides"], skills=[S["word_use"]]),
            choice_task("Candidates: feather, feathar, fether. The sentence names a bird covering.", "Which candidate is standard?", "feather", ["feathar", "fether"], skills=[S["spelling"]]),
            choice_task("The patient crow guards the nest.", "Which word shows the action?", "guards", ["patient", "crow"], skills=[S["word_jobs"]]),
            open_task("Word set: patiently / rook / waits / the", "Build a complete bird statement from the displayed words.", "The rook waits patiently.", [evidence("Uses the complete statement order.", "the rook waits patiently", "rook waits patiently")], skills=[S["sentence_order"]]),
            open_task("Unfinished question: why did the feather fall", "Add the correct sentence boundaries.", "Why did the feather fall?", [evidence("Uses a capital beginning.", "Why"), evidence("Uses a question mark.", "?")], skills=[S["punctuation"]]),
            open_task("A crow carries food to an injured bird.", "Explain which trait the carrying action demonstrates.", "The crow shows kindness by carrying food to the injured bird.", [evidence("Uses the carrying action.", "carrying food", "injured bird"), evidence("Names kindness.", "shows kindness")], skills=[S["sentence"]]),
            open_task("A bird adds a flower, loses it in rain, and then shelters a chick.", "Retell the order and identify the useful final action.", "The bird adds and loses the flower, then usefully shelters the chick.", [evidence("Orders adding before losing.", "adds", "loses the flower"), evidence("Ends with sheltering the chick.", "shelters the chick")], skills=[S["comprehension"], S["sequence"]], ordered=True),
            open_task("To appreciate is to value with gratitude. Use appreciate with a correctly spelled bird word.", "State the meaning and create the new use.", "Appreciate means value with gratitude. The flock appreciates the crow's helpful warning.", [evidence("Explains value with gratitude.", "value with gratitude"), evidence("Uses flock and appreciates accurately.", "flock appreciates", "helpful warning")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
            open_task("Word set: quality / does / show / which / crow / the", "Turn the word set into the finished quality question.", "Which quality does the crow show?", [evidence("Uses correct question order.", "which quality does the crow show"), evidence("Uses capital and question mark.", "Which", "?")], skills=[S["sentence_order"], S["punctuation"]]),
        ]
    return [
        choice_task("The flock reassures Kavi, helping him stop worrying about his plain feathers.", "Which meaning fits reassures?", "helps him stop worrying", ["makes him boast", "changes his colour"], skills=[S["word_context"]]),
        choice_task("The peahen feeds two chicks while the crow guards the branch.", "Who guards the branch?", "the crow", ["the peahen", "the chicks"], skills=[S["comprehension"]]),
        choice_task("A leaf hat tears, drops, and finally blows beyond the pond.", "What happens immediately before it blows away?", "It drops.", ["It tears.", "It becomes a feather."], skills=[S["sequence"]]),
        choice_task("Sentence frame: We ___ the bird's patient care.", "Which chapter word means value highly?", "admire", ["remove", "scatter"], skills=[S["word_use"]]),
        choice_task("Candidates: colourful, colorfull, colourfol. The sentence describes many colours.", "Which spelling is standard?", "colourful", ["colorfull", "colourfol"], skills=[S["spelling"]]),
        choice_task("A glossy feather shines near the nest.", "Which word describes the feather?", "glossy", ["feather", "shines"], skills=[S["word_jobs"]]),
        open_task("Word set: crow / shares / the / grain / kind", "Arrange the complete statement.", "The kind crow shares grain.", [evidence("Uses correct complete order.", "kind crow shares grain"), evidence("Uses all supplied words.", "the kind crow")], skills=[S["sentence_order"]]),
        open_task("Unfinished line: the black feathers are beautiful", "Repair the sentence boundaries.", "The black feathers are beautiful.", [evidence("Uses a capital beginning.", "The"), evidence("Uses a full stop.", ".")], skills=[S["punctuation"]]),
        open_task("A bird returns a ribbon that is not hers.", "Name the quality and support it with the bird's action.", "The bird shows honesty by returning the ribbon to its owner.", [evidence("Uses the returning action.", "returning the ribbon", "to its owner"), evidence("Names honesty.", "shows honesty")], skills=[S["sentence"]]),
        open_task("The crow finds a shiny thread, wears it, trips, and removes it before flying.", "Give the action chain and safe final choice.", "The crow finds and wears the thread, trips, and safely removes it before flying.", [evidence("Orders wearing before tripping.", "wears the thread", "trips"), evidence("Ends with safe removal.", "removes it before flying")], skills=[S["comprehension"], S["sequence"]], ordered=True),
        open_task("Unique means one of a kind. Use unique with a correctly spelled bird feature.", "State the meaning and write the new use.", "Unique means one of a kind. The crow has a unique feather pattern.", [evidence("Explains one of a kind.", "one of a kind"), evidence("Uses unique and feather accurately.", "unique feather pattern")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
        open_task("Word set: did / bird / why / ribbon / remove / the / its", "Build the finished question with correct punctuation.", "Why did the bird remove its ribbon?", [evidence("Uses correct question order.", "why did the bird remove its ribbon"), evidence("Uses capital and question mark.", "Why", "?")], skills=[S["sentence_order"], S["punctuation"]]),
    ]


CONFIG = {
    "chapter_id": CHAPTER_ID,
    "chapter_no": 10,
    "title": "The Crow",
    "unit_title": "Life Around Us",
    "source_url": SOURCE_URL,
    "extract_path": "/tmp/zidd-ncert-class2-3/eng_c2_ch10.txt",
    "source_anchors": [
        {"anchor_id": f"{CHAPTER_ID}:poem:1-2", "section_label": "Poem: crow, feathers, and acceptance", "page_start": 1, "page_end": 2, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:speak:3", "section_label": "Let us speak: birds, uniqueness, and good qualities", "page_start": 3, "page_end": 3, "source_url": SOURCE_URL, "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:write-birds:4", "section_label": "Let us write: picture-based bird naming", "page_start": 4, "page_end": 4, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:draw:5", "section_label": "Let us draw: favourite bird", "page_start": 5, "page_end": 5, "source_url": SOURCE_URL, "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:listen:6", "section_label": "Let us listen: teacher-led syllable activity", "page_start": 6, "page_end": 6, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:write-rhyme:7", "section_label": "Let us write: printed rhyme and bird words", "page_start": 7, "page_end": 7, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:write-sentences:8", "section_label": "Let us write: sentence construction", "page_start": 8, "page_end": 8, "source_url": SOURCE_URL, "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    ],
    "levels": LEVELS,
    "assessment_forms": [_assessment_form("a"), _assessment_form("b")],
}


MANIFEST = build_manifest(CONFIG)
