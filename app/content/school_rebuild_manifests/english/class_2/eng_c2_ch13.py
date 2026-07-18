"""Original deep manifest for Class 2 English Chapter 13, We are all Indians."""

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
CHAPTER_ID = "eng_c2_ch13"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/bemr113.pdf"


LEVELS: list[dict[str, Any]] = [
    {
        "level_id": f"{CHAPTER_ID}:profile_fact_reader",
        "title": "Read a child's profile carefully",
        "focus": "match a person with visible place, language, interest, and question details",
        "outcome": "Retrieve two or more stated profile facts and distinguish them from a nearby person's details without using an unseen picture.",
        "skill_ids": [S["comprehension"]],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:read-profiles:1-7"],
        "principle": "A profile is a fact set about one person; names, places, languages, interests, and questions must stay attached to the correct speaker.",
        "connect": {
            "teaching_block": "Read one profile at a time and build a name-to-detail link. A detail from another profile is not evidence.",
            "passage": "Profile: My name is Aarav. I live in Goa. I speak Konkani. I enjoy repairing toy boats.",
            "prompt": "Notice the four facts attached only to Aarav before continuing.",
        },
        "co": choice_task(
            "Profile A: Sumi lives in Assam and grows orchids. Profile B: Jatin lives in Haryana and plays hockey.",
            "Which detail belongs to Sumi?",
            "She grows orchids.",
            ["She plays hockey.", "She lives in Haryana."],
        ),
        "guided": [
            choice_task(
                "Profile: I am Lobsang. I live in Ladakh. I speak Ladakhi at home and enjoy making clay lamps.",
                "Which language is stated in Lobsang's profile?",
                "Ladakhi",
                ["Konkani", "Odia"],
            ),
            open_task(
                "Profile: My name is Parul. I live in Chhattisgarh. I learn folk painting from my aunt and care for a mango sapling.",
                "Write Parul's place and two interests from the visible profile.",
                "Parul lives in Chhattisgarh, learns folk painting, and cares for a mango sapling.",
                [
                    evidence("States Chhattisgarh.", "lives in Chhattisgarh", "Chhattisgarh"),
                    evidence("Includes both activities.", "folk painting", "mango sapling")
                ],
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Profile: I am Naren from Tripura. I speak Kokborok with my grandparents. My favourite school task is caring for the herb bed.",
                    "Introduce Naren using the place, language, and school interest.",
                    "Naren is from Tripura, speaks Kokborok with his grandparents, and enjoys caring for the herb bed.",
                    [
                        evidence("Includes Tripura and Kokborok.", "Tripura", "Kokborok"),
                        evidence("Includes caring for the herb bed.", "caring for the herb bed", "herb bed")
                    ],
                ),
                (
                    "Profile A: Alka lives in Bihar and practises kite making. Profile B: Tashi lives in Arunachal Pradesh and collects leaf shapes.",
                    "Compare one correct fact about Alka with one correct fact about Tashi.",
                    "Alka practises kite making in Bihar, while Tashi collects leaf shapes in Arunachal Pradesh.",
                    [
                        evidence("Keeps Alka with Bihar and kite making.", "Alka", "Bihar", "kite making"),
                        evidence("Keeps Tashi with Arunachal Pradesh and leaves.", "Tashi", "Arunachal Pradesh", "leaf shapes")
                    ],
                ),
            ]
        ),
        "transfer": _open_set(
            [
                (
                    "Library card: Name: Hina. Home district: Kutch. Languages read: Gujarati and English. Chosen club: Story Circle.",
                    "Transfer profile reading to the card and state all four details.",
                    "Hina is from Kutch, reads Gujarati and English, and has chosen the Story Circle club.",
                    [
                        evidence("States Hina and Kutch.", "Hina", "Kutch"),
                        evidence("Includes both languages and Story Circle.", "Gujarati", "English", "Story Circle")
                    ],
                ),
                (
                    "Team badge: Member: Vikram. State represented: Jharkhand. Skill: drumming. Shared task: welcome poster.",
                    "Write a complete two-fact team introduction plus the shared task.",
                    "Vikram represents Jharkhand, contributes drumming, and helps make the team's welcome poster.",
                    [
                        evidence("Includes Vikram, Jharkhand, and drumming.", "Vikram", "Jharkhand", "drumming"),
                        evidence("Includes the welcome poster task.", "welcome poster")
                    ],
                ),
            ]
        ),
        "review": _open_set(
            [
                (
                    "Profile: My name is Elsa. I live in Nagaland. I speak Ao with family and weave bright paper strips in art class.",
                    "Retrieve the name, place, language, and art activity.",
                    "Elsa lives in Nagaland, speaks Ao with her family, and weaves bright paper strips in art class.",
                    [
                        evidence("Includes Elsa, Nagaland, and Ao.", "Elsa", "Nagaland", "speaks Ao"),
                        evidence("Includes weaving paper strips.", "weaves bright paper strips", "paper strips")
                    ],
                ),
                (
                    "Profile A: Farhan grows marigolds in Telangana. Profile B: Renu learns bamboo craft in Mizoram.",
                    "Write one accurate sentence for each person without swapping details.",
                    "Farhan grows marigolds in Telangana. Renu learns bamboo craft in Mizoram.",
                    [
                        evidence("Keeps Farhan with Telangana and marigolds.", "Farhan", "Telangana", "marigolds"),
                        evidence("Keeps Renu with Mizoram and bamboo craft.", "Renu", "Mizoram", "bamboo craft")
                    ],
                ),
            ]
        ),
        "cluster_id": f"{CHAPTER_ID}:profile_detail_swap",
        "misconception": "The learner combines attractive details from different profiles, drops the person's name, or supplies a place or language not present in the visible card.",
        "remediation": "Draw one box per name, copy only that box's stated facts, and check each response detail against the same visible profile before submitting.",
        "support": _open_set([
            ("Profile: Name: Gita. Place: Sikkim. Interest: seed collecting.", "State Gita's place and interest.", "Gita is from Sikkim and enjoys collecting seeds.", [evidence("Keeps both facts with Gita.", "Gita", "Sikkim", "collecting seeds")]),
            ("Profile: Name: Ali. Language: Urdu. Instrument: flute.", "Introduce Ali with both details.", "Ali speaks Urdu and enjoys playing the flute.", [evidence("Includes Ali, Urdu, and flute.", "Ali", "Urdu", "flute")]),
            ("Profile A: Mili likes pottery. Profile B: Dev likes chess.", "Give one correct interest for each child.", "Mili likes pottery, while Dev likes chess.", [evidence("Keeps pottery with Mili and chess with Dev.", "Mili", "pottery", "Dev", "chess")]),
            ("Card: Pema; home: Himachal Pradesh; tree: deodar.", "Turn the card into a complete sentence.", "Pema lives in Himachal Pradesh and likes the deodar tree.", [evidence("Uses all three card facts.", "Pema", "Himachal Pradesh", "deodar")]),
            ("Profile: Zubin studies in Pune and enjoys making clay animals.", "Retrieve the city and activity.", "Zubin studies in Pune and makes clay animals for enjoyment.", [evidence("Includes Pune and clay animals.", "Pune", "clay animals")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:inquiry_and_festival_sequence",
        "title": "Follow discovery and festival information",
        "focus": "sequence questions, clues, explanations, and festival facts",
        "outcome": "Retell an inquiry or festival process in order and identify the visible clue that supports the final explanation.",
        "skill_ids": [S["comprehension"], S["sequence"]],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:something-new:13-14", f"{CHAPTER_ID}:festival-read:16-17"],
        "principle": "Inquiry moves from observation to question to evidence-based explanation; festival information keeps time, place, and activity attached correctly.",
        "connect": {
            "teaching_block": "A discovery sequence begins with what people can see, continues through useful questions, and ends with an explanation supported by a clue.",
            "passage": "A class finds a wooden tool with a wheel and thread. They ask what it does, and a craftsperson explains that turning the wheel twists fibre into yarn.",
            "prompt": "Notice the object clues, question, and demonstrated purpose.",
        },
        "co": choice_task(
            "Children see flower baskets at a doorway. They ask why they are there, and an elder explains that families are welcoming spring visitors.",
            "Which event comes immediately before the elder's explanation?",
            "The children ask why the baskets are there.",
            ["The families remove every flower.", "Spring ends before the question."],
        ),
        "guided": [
            choice_task(
                "A festival note states: morning river cleaning, afternoon seed sharing, evening lantern walk.",
                "Which activity happens second?",
                "seed sharing",
                ["river cleaning", "lantern walk"],
            ),
            open_task(
                "A learner notices a hand tool with a wooden frame and tight strings. She asks how it works. The artisan pulls one string to show how threads become even.",
                "Retell the observation, question, and demonstration in order.",
                "The learner notices the framed strings, asks how the tool works, and watches the artisan even the threads.",
                [
                    evidence("Starts with the framed-string observation.", "wooden frame", "framed strings", "tight strings"),
                    evidence("Orders the question before demonstration.", "asks how", "artisan", "even the threads")
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Festival card: At dawn families decorate a shared well. At noon they serve millet dishes. At sunset children carry leaf lamps along the lane.",
                    "Sequence the three activities and include their time clues.",
                    "Families decorate the well at dawn, serve millet at noon, and carry leaf lamps at sunset.",
                    [
                        evidence("Places decoration at dawn and food at noon.", "decorate the well at dawn", "serve millet at noon"),
                        evidence("Ends with leaf lamps at sunset.", "leaf lamps", "at sunset")
                    ],
                ),
                (
                    "A museum table holds a small loom, a woven strip, and loose yarn. A guide first points to the yarn, next passes it through the loom, and finally shows the woven strip.",
                    "Explain how the three visible items reveal the process.",
                    "The guide begins with loose yarn, passes it through the loom, and ends with the woven strip.",
                    [
                        evidence("Begins with loose yarn.", "begins with loose yarn", "loose yarn"),
                        evidence("Orders loom before woven strip.", "through the loom", "woven strip")
                    ],
                ),
            ],
            ordered=True,
        ),
        "transfer": _open_set(
            [
                (
                    "At a science fair, pupils see a wheel, belt, and tiny light. They ask why the light turns on; a mentor spins the wheel, which moves the belt and powers the light.",
                    "Transfer the inquiry sequence from object to explanation.",
                    "The pupils observe the wheel, belt, and light, ask their question, and learn that spinning the wheel powers the light through the belt.",
                    [
                        evidence("Includes the observed parts and question.", "wheel", "belt", "light", "ask"),
                        evidence("Explains the wheel-to-light link.", "spinning the wheel", "powers the light")
                    ],
                ),
                (
                    "Community-day plan: first neighbours exchange seed packets, then teams plant a shared border, and last everyone labels the new plants.",
                    "State the complete process and why labels come last.",
                    "Neighbours exchange seeds, plant the border, and finally label the plants because the plants must be placed before they can be named.",
                    [
                        evidence("Orders exchange before planting.", "exchange seeds", "plant the border"),
                        evidence("Places labels last with a reason.", "finally label", "placed before")
                    ],
                ),
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "A festival description gives three clues: it welcomes the rainy season, honours a local lake, and ends with a shared boat-lighting ceremony.",
                    "List the three linked festival ideas in the order given.",
                    "The festival welcomes rain, honours the lake, and ends with a shared boat-lighting ceremony.",
                    [
                        evidence("Starts with welcoming rain and honouring the lake.", "welcomes rain", "honours the lake"),
                        evidence("Ends with boat lighting.", "boat-lighting ceremony", "lighting boats")
                    ],
                ),
                (
                    "Students find a curved wooden frame, ask whether it is a toy, and learn from a weaver that it holds yarn while a pattern is formed.",
                    "Retell the mistaken guess and corrected explanation.",
                    "The students first guess that the frame is a toy, then learn that a weaver uses it to hold yarn for a pattern.",
                    [
                        evidence("Includes the toy guess first.", "guess", "frame is a toy"),
                        evidence("Corrects it with yarn and pattern use.", "holds yarn", "pattern")
                    ],
                ),
            ],
            ordered=True,
        ),
        "cluster_id": f"{CHAPTER_ID}:inquiry_or_festival_order",
        "misconception": "The learner treats an early guess as the final fact, swaps festival times, or omits the demonstrated clue that explains an unfamiliar object.",
        "remediation": "Use observe, ask, explain boxes for inquiry and time, activity, purpose boxes for festivals; verify each final fact against its visible clue.",
        "support": _open_set([
            ("Children see a clay wheel, ask its use, and watch a potter shape a bowl.", "Order observation, question, and demonstration.", "The children see the wheel, ask its use, and then watch the potter shape a bowl.", [evidence("Keeps all three inquiry steps in order.", "see the wheel", "ask its use", "shape a bowl")]),
            ("Morning: clean the pond edge. Afternoon: plant reeds. Evening: share a conservation pledge.", "Retell the timed plan.", "The group cleans in the morning, plants reeds in the afternoon, and shares the pledge in the evening.", [evidence("Uses all three time-activity pairs.", "morning", "afternoon", "evening", "plants reeds")]),
            ("A visitor guesses that a wooden press is a stool. The maker demonstrates that it flattens paper pulp.", "State the guess and corrected use.", "The visitor guesses stool, but the maker shows that the wooden press flattens paper pulp.", [evidence("Contrasts stool guess with paper-press use.", "guesses stool", "flattens paper pulp")]),
            ("First families gather flowers, next they make doorway patterns, and last elders offer fruit.", "Give the festival chain in order.", "Families gather flowers, make doorway patterns, and finally receive fruit from elders.", [evidence("Keeps gathering, patterns, and fruit in order.", "gather flowers", "doorway patterns", "fruit")]),
            ("A tool has a handle and toothed wheel. A gardener turns it to cut a neat seed line.", "Explain the visible clue and demonstrated purpose.", "The toothed wheel and the gardener's demonstration show that the tool cuts a seed line.", [evidence("Links toothed wheel to seed-line use.", "toothed wheel", "cuts a seed line")]),
        ], ordered=True),
    },
    {
        "level_id": f"{CHAPTER_ID}:culture_and_belonging_words",
        "title": "Use culture and belonging vocabulary",
        "focus": "infer language, festival, neighbour, unique, monument, and belong from context",
        "outcome": "Explain a culture or belonging word from visible clues and use it respectfully in a fresh sentence.",
        "skill_ids": [S["word_context"], S["word_use"]],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [f"{CHAPTER_ID}:read-profiles:1-7", f"{CHAPTER_ID}:festival-read:16-17"],
        "principle": "Culture words are defined by stated practices, places, or relationships; respectful use describes difference without ranking people.",
        "connect": {
            "teaching_block": "Read the example beside a culture word and replace the target with a plain meaning before writing a new sentence.",
            "passage": "A language is a system people use to share words and meaning; this family uses Khasi at home.",
            "prompt": "Notice the communication clue and the named example before continuing.",
        },
        "co": choice_task("A festival is a special time when a community gathers for shared traditions and celebration.", "Which meaning fits festival?", "a special community celebration", ["an ordinary pencil", "one private address"]),
        "guided": [
            choice_task("A neighbour lives near us; Mr Sen's home is beside our lane.", "Which phrase explains neighbour?", "a person who lives nearby", ["a visitor from a book", "a distant mountain"]),
            open_task("Each handprint is unique because its pattern is not exactly the same as another person's pattern.", "Explain unique and use it for a harmless profile detail.", "Unique means one of a kind. Asha has a unique way of arranging paper flowers.", [evidence("Defines one of a kind.", "one of a kind", "not exactly the same"), evidence("Uses unique respectfully.", "unique way", "unique pattern")]),
        ],
        "independent": _open_set([
            ("A monument is an important structure kept to remember people, events, or history; the old memorial arch is one example.", "Define monument and use it in a new travel sentence.", "A monument is an important structure connected with history. Our class visited a riverside monument.", [evidence("Explains important historical structure.", "important structure", "history"), evidence("Uses monument as a place.", "visited", "monument")]),
            ("People belong to a team when they are accepted as members and take part in its shared work.", "Explain belong and use it in a welcoming sentence.", "Belong means be an accepted member. Every learner belongs in our reading circle.", [evidence("Defines accepted membership.", "accepted member"), evidence("Uses belongs for inclusion.", "learner belongs", "belongs in our")]),
        ]),
        "transfer": _open_set([
            ("A tradition is a practice passed through families or communities, such as making leaf lamps each year.", "Infer tradition and write another accurate use.", "A tradition is a practice continued over time. Sharing seed stories is a village tradition.", [evidence("Defines continued practice.", "practice continued over time", "passed through"), evidence("Uses tradition with a practice.", "village tradition", "family tradition")]),
            ("Diversity means a group includes different languages, foods, arts, or experiences rather than being all the same.", "Explain diversity and use it for a classroom.", "Diversity means having many kinds of people or practices. Our classroom's language diversity helps us learn new words.", [evidence("Defines many kinds or differences.", "many kinds", "different languages"), evidence("Uses diversity respectfully.", "language diversity", "classroom")]),
        ]),
        "review": _open_set([
            ("A community is a group connected by place, work, or shared care, such as families who look after the same lake.", "State the context meaning and create a new use.", "A community is a connected group. The garden community shares tools and water duties.", [evidence("Defines a connected group.", "connected group"), evidence("Uses community with shared work.", "garden community", "shares tools")]),
            ("Respect means treating another person's language or custom with care even when it differs from one's own.", "Explain respect and use it in a language sentence.", "Respect means treating others and their practices with care. We show respect by learning a classmate's name correctly.", [evidence("Defines treating with care.", "treating", "with care"), evidence("Uses respect through correct naming.", "show respect", "name correctly")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:culture_word_stereotype",
        "misconception": "The learner uses a culture word as a label for every person from a place, ranks differences, or ignores the context definition.",
        "remediation": "Underline the exact practice or relationship, give a plain neutral meaning, and write a new sentence about one stated example without generalising.",
        "support": _open_set([
            ("A region is an area of land, such as a coastal area with several towns.", "Explain region and use it in a place sentence.", "A region is an area of land. This coastal region has many fishing towns.", [evidence("Defines and uses an area of land.", "area of land", "coastal region")]),
            ("A custom is a usual community practice, like greeting visitors with a flower tray.", "Define custom and create a new use.", "A custom is a usual practice. Sharing sweet rice is a local custom.", [evidence("Defines and uses a usual practice.", "usual practice", "local custom")]),
            ("A resident is someone who lives in a place.", "Explain resident and use it for a town.", "A resident is a person who lives there. Each town resident helped map the trees.", [evidence("Defines and uses a person living there.", "person who lives", "town resident")]),
            ("Inclusive means welcoming people into shared activities.", "Define inclusive and use it for a club.", "Inclusive means welcoming participation. The inclusive club gives every member a task.", [evidence("Defines and uses welcoming participation.", "welcoming participation", "inclusive club", "every member")]),
            ("Heritage includes valued stories, places, crafts, or practices carried from earlier times.", "Explain heritage and use it with a craft.", "Heritage means valued culture from earlier times. Basket weaving is part of the area's craft heritage.", [evidence("Defines and uses valued culture from earlier times.", "earlier times", "craft heritage")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:visible_culture_spellings",
        "title": "Build culture-word spellings",
        "focus": "use printed chunks and letter patterns to spell profile and festival words",
        "outcome": "Produce a standard spelling from visible evidence and use the culture word in a respectful complete sentence.",
        "skill_ids": [S["spelling"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:speak-listen:10", f"{CHAPTER_ID}:write:11-12", f"{CHAPTER_ID}:festival-read:16-17"],
        "principle": "Look closely at the printed letters, word chunks, and meaning clue before you build the spelling.",
        "connect": {
            "teaching_block": "Join every visible chunk, check the whole spelling against its meaning, and use it in a sentence that does not stereotype a person.",
            "passage": "Printed chunks: fes + ti + val = festival; lan + guage = language.",
            "prompt": "Notice that all chunks remain visible in the completed words.",
        },
        "co": choice_task("Candidates: Indian, Indain, Indeian. The sentence names a person from India.", "Which candidate is the standard profile word?", "Indian", ["Indain", "Indeian"]),
        "guided": [
            choice_task("Candidates: bridge, brigde, brige. The clue names a crossing over water or a road.", "Which printed word is standard?", "bridge", ["brigde", "brige"]),
            open_task("Chunks: neigh + bour. Meaning clue: a person living nearby.", "Build the nearby-person word, then use it respectfully in a community sentence.", "The word is neighbour. Our neighbour teaches us a seed-saving custom.", [evidence("Spells neighbour correctly.", "neighbour"), evidence("Uses neighbour respectfully.", "our neighbour", "neighbour teaches")]),
        ],
        "independent": _open_set([
            ("Missing letters: l a n g u _ g e. The clue names a system of words.", "Complete the word and use it in a profile sentence.", "The word is language. Mira learns one new word from her friend's language.", [evidence("Spells language correctly.", "language"), evidence("Uses language respectfully.", "friend's language", "new word")]),
            ("Scrambled letters: l e v a r t. The clue means go from one place to another.", "Unscramble the word and write a complete sentence.", "The word is travel. We travel by train to visit the craft fair.", [evidence("Spells travel correctly.", "travel"), evidence("Uses travel for movement.", "travel by train", "travel to")]),
        ]),
        "transfer": _open_set([
            ("Base word: nation. Add al to describe something related to a nation.", "Build the new word and use it for a celebration.", "The word is national. The library displayed a national celebration calendar.", [evidence("Builds national correctly.", "national"), evidence("Uses national without ranking cultures.", "national celebration", "calendar")]),
            ("Chunks: mon + u + ment. The clue names an important historical structure.", "Join the chunks and write a place sentence.", "The word is monument. The class read a sign beside the old monument.", [evidence("Spells monument correctly.", "monument"), evidence("Uses monument as a place.", "old monument", "beside the monument")]),
        ]),
        "review": _open_set([
            ("Correct the printed word festivel in a sentence about a spring event.", "Write the corrected word and sentence.", "The corrected word is festival. The spring festival includes a shared flower walk.", [evidence("Corrects festival.", "festival"), evidence("Uses it with a stated event.", "spring festival", "flower walk")]),
            ("Missing letters: u n i q _ e. The clue means one of a kind.", "Complete the word and use it respectfully.", "The word is unique. Each profile includes a unique chosen interest.", [evidence("Spells unique correctly.", "unique"), evidence("Uses unique for a chosen detail.", "unique chosen interest", "unique interest")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:culture_chunk_spelling",
        "misconception": "The learner drops a visible syllable, changes a proper place spelling without evidence, or uses the completed word in a stereotyped statement.",
        "remediation": "Trace every printed chunk, rebuild the word, check the neutral meaning, and use it with one visible profile or festival fact.",
        "support": _open_set([
            ("Chunks: cul + ture. The clue names shared arts, practices, and ideas.", "Join and use the word respectfully.", "The word is culture. Food is one part of culture, not the whole profile of a person.", [evidence("Spells and uses culture carefully.", "culture", "one part")]),
            ("Chunks: In + di + a. The clue names the country.", "Build the proper name and write a sentence.", "The word is India. India has many languages and landscapes.", [evidence("Spells and uses India.", "India", "many languages")]),
            ("Candidates: puppet, pupet, puppit. The clue names a figure moved in a show.", "Write the standard spelling in a sentence.", "The word is puppet. The craft table displays a cloth puppet.", [evidence("Spells and uses puppet.", "puppet", "cloth puppet")]),
            ("Scrambled letters: f r a m e. The clue names a border or support around something.", "Unscramble and use the word.", "The word is frame. A wooden frame holds the woven sample.", [evidence("Spells and uses frame.", "frame", "wooden frame")]),
            ("Correct this word: belongg. The membership word has one final g.", "Repair and use the word in a welcome sentence.", "The corrected word is belong. Every child can belong in the activity group.", [evidence("Corrects and uses belong.", "belong", "activity group")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:profile_word_jobs",
        "title": "Find jobs in profile sentences",
        "focus": "identify nouns, verbs, and adjectives in place, language, art, and festival statements",
        "outcome": "Classify requested words by their job in a visible profile sentence without treating every proper name as a description.",
        "skill_ids": [S["word_jobs"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:read-profiles:1-7", f"{CHAPTER_ID}:write:11-12"],
        "principle": "Names of people and places are nouns, actions are verbs, and words that tell what kind are adjectives; the sentence proves each job.",
        "connect": {
            "teaching_block": "Read the full profile before labelling. Capital letters may mark a proper noun, but they do not turn an action into a name.",
            "passage": "Cheerful Mira paints bright patterns. Mira and patterns name, paints acts, and cheerful and bright describe.",
            "prompt": "Notice the job evidence for every requested word.",
        },
        "co": choice_task("A skilled drummer plays the dhol.", "Which word names the drummer's action?", "plays", ["skilled", "drummer"]),
        "guided": [
            choice_task("The colourful festival welcomes visitors.", "Which word describes the festival?", "colourful", ["festival", "welcomes"]),
            open_task("Young Tanu learns a local craft.", "Label Tanu, learns, young, and local.", "Tanu is a noun, learns is a verb, and young and local are adjectives.", [evidence("Labels Tanu and learns.", "Tanu is a noun", "learns is a verb"), evidence("Labels young and local.", "young", "local")]),
        ],
        "independent": _open_set([
            ("The ancient monument attracts curious visitors.", "Classify monument, attracts, ancient, and curious.", "Monument is a noun, attracts is a verb, and ancient and curious are adjectives.", [evidence("Labels monument and attracts.", "monument is a noun", "attracts is a verb"), evidence("Labels ancient and curious.", "ancient", "curious")]),
            ("Kind neighbours share festive rice.", "Identify the action and both describing words.", "Share is the action, while kind and festive are describing words.", [evidence("Names share as action.", "share is the action", "share is a verb"), evidence("Names kind and festive.", "kind", "festive")]),
        ]),
        "transfer": _open_set([
            ("A wooden tool twists loose fibre.", "Label wooden, tool, twists, and loose.", "Wooden and loose are adjectives, tool is a noun, and twists is a verb.", [evidence("Labels both adjectives.", "wooden", "loose"), evidence("Labels tool and twists.", "tool is a noun", "twists is a verb")]),
            ("The inclusive club welcomes new members.", "Transfer the word-job check to inclusive, club, and welcomes.", "Inclusive is an adjective, club is a noun, and welcomes is a verb.", [evidence("Classifies all requested words.", "inclusive is an adjective", "club is a noun", "welcomes is a verb")]),
        ]),
        "review": _open_set([
            ("Many regional languages enrich the shared library.", "Name the action and two describing words.", "Enrich is the action, and regional and shared are describing words.", [evidence("Names enrich as action.", "enrich is the action", "enrich is a verb"), evidence("Names regional and shared.", "regional", "shared")]),
            ("The spring festival begins a joyful week.", "Classify festival, begins, spring, and joyful.", "Festival is a noun, begins is a verb, and spring and joyful are adjectives.", [evidence("Labels festival and begins.", "festival is a noun", "begins is a verb"), evidence("Labels spring and joyful.", "spring", "joyful")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:profile_word_job_confusion",
        "misconception": "The learner calls every culture-related word a noun, labels a proper name as an adjective, or treats a quality such as inclusive as an action.",
        "remediation": "Apply who or what, what happens, and what kind tests to the exact sentence, then point to each word before assigning its label.",
        "support": _open_set([
            ("The bright lamp glows.", "Label bright, lamp, and glows.", "Bright is an adjective, lamp is a noun, and glows is a verb.", [evidence("Labels all three jobs.", "bright is an adjective", "lamp is a noun", "glows is a verb")]),
            ("A local artist teaches.", "Which word describes the artist, and which word tells what happens?", "Local describes the artist, and teaches shows the action.", [evidence("Distinguishes local and teaches.", "local describes", "teaches shows")]),
            ("Curious Pema asks politely.", "Classify curious, Pema, and asks.", "Curious is an adjective, Pema is a noun, and asks is a verb.", [evidence("Classifies all requested words.", "curious is an adjective", "Pema is a noun", "asks is a verb")]),
            ("The unique pattern repeats.", "Explain why unique is not the action.", "Unique describes the pattern, while repeats is the action.", [evidence("Contrasts unique and repeats.", "unique describes", "repeats is the action")]),
            ("Friendly residents protect heritage trees.", "Label friendly, residents, and protect.", "Friendly is an adjective, residents is a noun, and protect is a verb.", [evidence("Labels all three words.", "friendly is an adjective", "residents is a noun", "protect is a verb")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:profile_question_builder",
        "title": "Arrange profile questions and replies",
        "focus": "order visible words and punctuate respectful identity questions and statements",
        "outcome": "Build a clear profile question or reply using all supplied words, a capital beginning, and the correct end mark.",
        "skill_ids": [S["sentence_order"], S["punctuation"]],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:speak:8", f"{CHAPTER_ID}:write:11-12"],
        "principle": "A respectful profile question asks only the visible topic, keeps question order, and uses a capital plus question mark.",
        "connect": {
            "teaching_block": "Decide whether the words form a question or statement, arrange person and action, and complete the written boundaries.",
            "passage": "Word set: language / which / speak / you / do. Finished form: Which language do you speak?",
            "prompt": "Notice the question order, capital W, and question mark.",
        },
        "co": choice_task("Word set: festival / favourite / your / is / which", "Which option forms a complete question?", "Which festival is your favourite?", ["Your which festival favourite is.", "which is Festival your favourite?"]),
        "guided": [
            choice_task("Word set: please / book / may / borrow / I / your", "Which option is a finished polite question?", "May I please borrow your book?", ["Please your book I may borrow.", "may Borrow book your please I?"]),
            open_task("Word set: my / Bengali / neighbour / speaks", "Arrange every word as one statement.", "My neighbour speaks Bengali.", [evidence("Uses correct complete order.", "my neighbour speaks Bengali"), evidence("Adds capital and full stop.", "My", ".")]),
        ],
        "independent": _open_set([
            ("Word set: monument / have / which / visited / you", "Build the complete travel question.", "Which monument have you visited?", [evidence("Uses correct question order.", "which monument have you visited"), evidence("Adds capital and question mark.", "Which", "?")]),
            ("Unfinished reply: thank you for teaching me that word", "Repair the respectful statement boundaries.", "Thank you for teaching me that word.", [evidence("Keeps the gratitude message.", "thank you for teaching me that word"), evidence("Adds capital and full stop.", "Thank", ".")]),
        ]),
        "transfer": _open_set([
            ("Word set: craft / local / what / you / learn / did", "Transfer the ordering skill to a craft question.", "What local craft did you learn?", [evidence("Uses correct question order.", "what local craft did you learn"), evidence("Adds capital and question mark.", "What", "?")]),
            ("Word set: all / group / belong / our / in / we", "Arrange the complete belonging statement.", "We all belong in our group.", [evidence("Uses all words in sensible order.", "we all belong in our group"), evidence("Adds capital and full stop.", "We", ".")]),
        ]),
        "review": _open_set([
            ("Jumbled line: your / what / tree / favourite / is", "Write the correctly ordered question.", "What is your favourite tree?", [evidence("Uses correct question order.", "what is your favourite tree"), evidence("Adds capital and question mark.", "What", "?")]),
            ("Unfinished line: many languages enrich our class", "Add the missing sentence boundaries.", "Many languages enrich our class.", [evidence("Keeps the complete statement.", "many languages enrich our class"), evidence("Adds capital and full stop.", "Many", ".")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:profile_question_boundary",
        "misconception": "The learner preserves jumbled order, omits a respectful word, or ends a direct profile question with a full stop.",
        "remediation": "Choose question or statement, box the person and action, arrange topic details, and check the capital-plus-purpose-mark pair.",
        "support": _open_set([
            ("Word set: name / is / my / Tara", "Build the identity statement.", "The finished statement is: My name is Tara.", [evidence("Builds and punctuates the statement.", "my name is Tara", "My", ".")]),
            ("Word set: do / where / live / you", "Build the place question.", "The finished question is: Where do you live?", [evidence("Builds and punctuates the question.", "where do you live", "Where", "?")]),
            ("Line needing repair: please tell me about the festival", "Add complete statement boundaries.", "Please tell me about the festival.", [evidence("Adds capital and full stop.", "Please tell me", "festival", ".")]),
            ("Word set: plays / she / drum / the", "Arrange the music statement.", "The finished statement is: She plays the drum.", [evidence("Uses every word in order.", "she plays the drum", "She", ".")]),
            ("Line needing repair: which language is on the card", "Repair the language-card question and its end mark.", "Which language is on the card?", [evidence("Adds capital and question mark.", "Which language is on the card", "?")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:welcome_and_belonging_writer",
        "title": "Write a respectful welcome",
        "focus": "construct complete comparisons and welcome messages from visible profile facts",
        "outcome": "Write a complete sentence that values both a stated difference and shared belonging without inventing or ranking identities.",
        "skill_ids": [S["comprehension"], S["sentence"]],
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:read-profiles:1-7", f"{CHAPTER_ID}:speak:8", f"{CHAPTER_ID}:write:11-12"],
        "principle": "A respectful comparison uses only volunteered facts, treats each difference neutrally, and names a real shared activity or belonging link.",
        "connect": {
            "teaching_block": "People can differ in language or interests and still share a class, team, or country. A strong sentence includes both truths.",
            "passage": "Profile A: Reva speaks Marathi and enjoys chess. Profile B: Noor speaks Urdu and enjoys chess. Shared fact: both join the chess club.",
            "prompt": "Notice one difference and the stated shared interest before continuing.",
        },
        "co": choice_task("Asha enjoys pottery; Kabir enjoys gardening. Both help decorate the class entrance.", "Which sentence respects difference and shared work?", "Asha and Kabir enjoy different activities, but both help decorate the entrance.", ["Pottery makes Asha better than Kabir.", "They must have the same hobby to belong."], skills=[S["comprehension"]]),
        "guided": _open_set([
            ("Profile A: Lila speaks Malayalam. Profile B: Sonam speaks Tibetan. Shared fact: both read stories to younger pupils.", "Write one complete difference-and-belonging sentence.", "Lila and Sonam speak different languages, but both help by reading stories to younger pupils.", [evidence("Includes both language facts neutrally.", "Malayalam", "Tibetan", "different languages"), evidence("Includes the shared reading action.", "both", "reading stories", "younger pupils")]),
            ("New learner: Abhay from Uttarakhand; chosen interest: bird watching. Group fact: the Nature Club has an open place.", "Write a warm welcome using only the supplied facts.", "Welcome, Abhay. Your interest in bird watching can be part of our Nature Club.", [evidence("Welcomes Abhay by name.", "Welcome, Abhay", "welcome Abhay"), evidence("Links bird watching to Nature Club.", "bird watching", "Nature Club")]),
        ]),
        "independent": _open_set([
            ("Profile A: Mahi celebrates a harvest day with family. Profile B: Ishan marks a river day with family. Shared fact: both bring thank-you cards for community workers.", "Compare the family events and state the shared action respectfully.", "Mahi and Ishan mark different family events, but both thank community workers with cards.", [evidence("States different family events without ranking.", "different family events", "harvest", "river"), evidence("Includes shared thank-you cards.", "both", "thank community workers", "cards")]),
            ("New teammate: Joya; language used at home: Santali; chosen skill: seed sorting. Team task: prepare the garden bed.", "Write a complete welcome message using the volunteered details.", "Welcome, Joya. Your seed-sorting skill can help our team prepare the garden bed, and Santali is part of your profile.", [evidence("Welcomes Joya and includes seed sorting.", "Welcome, Joya", "seed-sorting"), evidence("Includes garden task and Santali neutrally.", "garden bed", "Santali")]),
        ]),
        "transfer": _open_set([
            ("Two neighbours cook different festival dishes. Shared fact: each brings one dish to the same community meal.", "Transfer the belonging pattern to the shared meal.", "The neighbours prepare different festival dishes, but both contribute to the same community meal.", [evidence("Names different dishes neutrally.", "different festival dishes"), evidence("Names shared contribution and meal.", "both contribute", "community meal")]),
            ("Team members use different scripts on their name cards. Shared goal: every card must be readable by its owner and include an English label below.", "Write one inclusive plan sentence from the visible goal.", "The cards may use different scripts, and every owner can read the card while an English label helps the whole team.", [evidence("Includes different scripts and owner readability.", "different scripts", "owner can read"), evidence("Includes the English label's shared purpose.", "English label", "whole team")]),
        ]),
        "review": _open_set([
            ("Profile A: Tanu plays a drum. Profile B: Veer paints signs. Shared event: both contribute to the school welcome day.", "Write a complete comparison that values both contributions.", "Tanu plays music and Veer paints signs, but both contribute useful skills to welcome day.", [evidence("Includes both different skills.", "Tanu", "music", "Veer", "paints signs"), evidence("Includes equal shared contribution.", "both contribute", "welcome day")]),
            ("New classmate: Neha from Odisha; chosen interest: shell patterns. Shared class project: map natural shapes.", "Compose a respectful two-sentence welcome and project link.", "Welcome, Neha. Your interest in shell patterns can add useful ideas to our natural-shapes map.", [evidence("Welcomes Neha by name.", "Welcome, Neha", "welcome Neha"), evidence("Links shell patterns to the map.", "shell patterns", "natural-shapes map")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:difference_ranking_or_invention",
        "misconception": "The learner ranks languages or customs, invents identity facts, erases differences, or writes a vague welcome with no shared activity.",
        "remediation": "Highlight one volunteered difference and one stated shared link, remove judging words, and build a complete both-and or different-but-belong sentence.",
        "support": _open_set([
            ("Ami likes weaving; Raj likes clay work. Both join the craft table.", "Write the difference and shared place respectfully.", "Ami and Raj like different crafts, but both belong at the craft table.", [evidence("Includes both crafts and shared belonging.", "different crafts", "both belong", "craft table")]),
            ("New learner: Pritam. Interest: maps. Open group: travel-reading circle.", "Write one factual welcome.", "Welcome, Pritam. Your interest in maps fits our travel-reading circle.", [evidence("Welcomes Pritam and links maps to the circle.", "Welcome, Pritam", "maps", "travel-reading circle")]),
            ("One child speaks Kannada; another speaks Hindi. Both solve the same puzzle.", "Create a neutral shared-action sentence.", "The children speak different languages, but both solve the puzzle together.", [evidence("Includes different languages and shared solving.", "different languages", "both solve", "together")]),
            ("Two families mark different local festivals. Both clean the shared lane afterward.", "Write a respectful comparison.", "The families mark different festivals, but both care for the lane by cleaning it.", [evidence("Includes different festivals and shared care.", "different festivals", "both", "cleaning")]),
            ("New member: Tara. Skill: flower arranging. Shared task: welcome table.", "Write the complete welcome link.", "Welcome, Tara. Your flower-arranging skill can help prepare our shared welcome table.", [evidence("Welcomes Tara and links skill to shared task.", "Welcome, Tara", "flower-arranging", "welcome table")]),
        ]),
    },
]


EXTRA_DEPTH = {
    f"{CHAPTER_ID}:profile_fact_reader": {
        "guided": [
            choice_task(
                "Profile A: Meera lives in Kochi and enjoys chess. Profile B: Arif lives in Jaipur and enjoys cycling.",
                "Who enjoys cycling?",
                "Arif",
                ["Meera", "both children"],
            ),
            open_task(
                "Profile card: Name: Tashi. Home state: Sikkim. Chosen school club: Nature Club. Favourite club task: caring for seedlings.",
                "State Tashi's home state and two club facts without adding anything else.",
                "Tashi is from Sikkim, belongs to the Nature Club, and enjoys caring for seedlings there.",
                [
                    evidence("States the home state.", "from Sikkim", "home state is Sikkim"),
                    evidence("States the club.", "belongs to the Nature Club", "chosen club is Nature Club"),
                    evidence("States the club task.", "caring for seedlings", "cares for seedlings in the club"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Profile A: Tara speaks Bengali at home and collects leaf shapes. Profile B: Joseph speaks Malayalam at home and builds toy bridges.",
                "Write one accurate sentence about each child using the language and interest shown.",
                "Tara speaks Bengali at home and collects leaf shapes. Joseph speaks Malayalam at home and builds toy bridges.",
                [
                    evidence("States Tara's language.", "Tara speaks Bengali", "Bengali is spoken by Tara at home"),
                    evidence("States Tara's interest.", "collects leaf shapes", "Tara collects leaves by shape"),
                    evidence("States Joseph's language.", "Joseph speaks Malayalam", "Malayalam is spoken by Joseph at home"),
                    evidence("States Joseph's interest.", "builds toy bridges", "Joseph makes toy bridges"),
                ],
            ),
            (
                "Profile card: Name: Bina. City: Ranchi. Favourite meal named by Bina: rice and dal. Weekend activity: practising the tabla.",
                "Summarise all three details that follow Bina's name.",
                "Bina lives in Ranchi, names rice and dal as her favourite meal, and practises the tabla on weekends.",
                [
                    evidence("States the city.", "lives in Ranchi", "city is Ranchi"),
                    evidence("States the named meal.", "rice and dal as her favourite meal", "favourite meal is rice and dal"),
                    evidence("States the weekend activity.", "practises the tabla on weekends", "weekend activity is tabla practice"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Library member card: Name: Naved. Reading language chosen today: Urdu. Shelf choice: animal stories. Borrowed item: one book.",
                "Transfer careful profile reading to the library card and report the three chosen details.",
                "Naved chooses Urdu for reading today, selects animal stories, and borrows one book.",
                [
                    evidence("States the reading language.", "chooses Urdu for reading", "reading language today is Urdu"),
                    evidence("States the shelf choice.", "selects animal stories", "chooses the animal-story shelf"),
                    evidence("States the borrowed amount.", "borrows one book", "one book is borrowed"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:inquiry_and_festival_sequence": {
        "guided": [
            choice_task(
                "First Isha asks her grandfather about a harvest song. Next she writes his answer. Last she checks the song title on a festival card.",
                "What does Isha do immediately before checking the card?",
                "She writes her grandfather's answer.",
                ["She checks the song title.", "She invents a new festival."],
            ),
            open_task(
                "A class wants to learn why lamps are placed along a local street. They ask a resident, note that the lamps guide an evening walk, and confirm the route on a notice.",
                "Retell the inquiry and name the clue supporting the explanation.",
                "The class asks a resident, records that the lamps guide the evening walk, and confirms the route on the notice.",
                [
                    evidence("States the first inquiry action.", "asks a resident", "class questions a resident"),
                    evidence("States the explanation.", "lamps guide the evening walk", "lights show the walking route"),
                    evidence("Names the confirming clue.", "route on the notice", "notice confirms the route"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set([
            (
                "To learn about a spring fair, Omar first reads its date on a board, then asks an organiser about the seed exchange, and finally writes that visitors trade labelled seeds.",
                "Sequence Omar's three information steps and state what he learns.",
                "Omar reads the date, asks the organiser, and then records that visitors exchange labelled seeds.",
                [
                    evidence("States the board step.", "reads the date", "date is read on the board"),
                    evidence("States the organiser step.", "asks the organiser", "questions an organiser next"),
                    evidence("States the learned fact.", "visitors exchange labelled seeds", "labelled seeds are traded"),
                ],
            ),
            (
                "Asha hears that a community meal begins at noon. She checks the printed programme, sees the same time, and then tells her group to arrive before twelve.",
                "Explain how Asha checks the information and uses it.",
                "Asha compares the stated noon time with the programme and then asks her group to arrive before twelve.",
                [
                    evidence("States the first information.", "meal begins at noon", "hears the noon time"),
                    evidence("States the check.", "checks the printed programme", "programme shows the same time"),
                    evidence("States how she uses it.", "group should arrive before twelve", "tells the group to come before noon"),
                ],
            ),
        ], ordered=True),
        "transfer": _open_set([
            (
                "A museum label says a clay pot was used for storing grain. Ritu reads the label, asks the guide why the lid is tight, and learns that the lid helped keep insects out.",
                "Transfer inquiry sequencing and identify the evidence for the lid's purpose.",
                "Ritu reads the label, asks the guide, and learns that the tight lid helped protect the grain from insects.",
                [
                    evidence("States the reading step.", "reads the label", "museum label is read first"),
                    evidence("States the question step.", "asks the guide", "questions the guide about the lid"),
                    evidence("States the supported purpose.", "lid kept insects out", "tight lid protected the grain"),
                ],
            )
        ], ordered=True),
    },
    f"{CHAPTER_ID}:culture_and_belonging_words": {
        "guided": [
            choice_task(
                "The club is inclusive because every child can join its games and nobody is left out.",
                "Which meaning fits inclusive?",
                "welcoming everyone into the group",
                ["choosing only one winner", "keeping all doors locked"],
            ),
            open_task(
                "A tradition is a practice that a group keeps and passes on, such as sharing a yearly neighbourhood meal.",
                "Explain tradition and use it respectfully in a new example.",
                "A tradition is a practice passed on in a group. Our reading club has a tradition of exchanging bookmarks each year.",
                [
                    evidence("Explains tradition.", "practice passed on in a group", "custom kept across time"),
                    evidence("Uses tradition freshly.", "reading club tradition of exchanging bookmarks", "club exchanges bookmarks each year"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "People show solidarity when they stand together and support one another during a difficult task.",
                "Infer solidarity and create an age-appropriate school example.",
                "Solidarity means supporting one another as a group. The class shows solidarity by helping rebuild the reading corner.",
                [
                    evidence("Explains solidarity.", "supporting one another as a group", "standing together to help"),
                    evidence("Uses solidarity appropriately.", "class helps rebuild the reading corner", "group supports the reading-corner work"),
                ],
            ),
            (
                "A community is a group of people connected by a place or shared activity; the garden volunteers form one community.",
                "Explain community and use it without assuming everyone is the same.",
                "A community is a connected group. Our library community includes readers with many different interests.",
                [
                    evidence("Explains community.", "connected group", "people linked by a place or activity"),
                    evidence("Uses community respectfully.", "library community includes different interests", "readers with many interests belong"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "A team has diversity when its members bring different experiences or ideas while working toward one goal.",
                "Infer diversity and use it in a welcoming group sentence.",
                "Diversity means having different experiences or ideas. Our project team values diversity and listens to every member.",
                [
                    evidence("Explains diversity.", "different experiences or ideas", "members are not all the same"),
                    evidence("Uses diversity respectfully.", "team values diversity", "listens to every member"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:visible_culture_spellings": {
        "guided": [
            choice_task(
                "Candidates: culture, culcher, cultuer. The profile needs the word for a group's shared ways and ideas.",
                "Which spelling is standard?",
                "culture",
                ["culcher", "cultuer"],
            ),
            open_task(
                "Printed chunks: wel + come. The clue names a friendly greeting or reception.",
                "Join the chunks and use the word in a respectful sentence.",
                "The word is welcome. We welcome every new member to the reading circle.",
                [
                    evidence("Builds the spelling.", "word is welcome", "spell it welcome"),
                    evidence("Uses welcome respectfully.", "welcome every new member", "new members are greeted warmly"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Missing letters: t o g e t h _ r. The clue means with one another in one group.",
                "Complete the word and use it in a belonging sentence.",
                "The word is together. Children with different hobbies learn together in our class.",
                [
                    evidence("Completes the spelling.", "word is together", "spell it together"),
                    evidence("Uses together inclusively.", "different hobbies learn together", "children learn as one class"),
                ],
            ),
            (
                "Scrambled letters: I n d i a. The clue names our country's proper name.",
                "Unscramble the proper noun and use its capital letter correctly.",
                "The word is India. Many languages are spoken across India.",
                [
                    evidence("Builds the proper noun.", "word is India", "spell it India"),
                    evidence("Uses the capital correctly.", "across India", "India begins with a capital"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Base word: belong. Add ing to name the feeling of being accepted in a group.",
                "Build the new word and use it in a complete sentence.",
                "The new word is belonging. A warm greeting can build a feeling of belonging.",
                [
                    evidence("Builds the new spelling.", "new word is belonging", "spell it belonging"),
                    evidence("Uses belonging accurately.", "feeling of belonging", "warm greeting helps people feel accepted"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:profile_word_jobs": {
        "guided": [
            choice_task(
                "Cheerful Nima teaches a new game.",
                "Which word tells what Nima does?",
                "teaches",
                ["cheerful", "game"],
            ),
            open_task(
                "The young artist paints a bright banner.",
                "Classify artist, paints, young, and bright.",
                "Artist is a noun, paints is a verb, and young and bright are adjectives.",
                [
                    evidence("Labels artist.", "artist is a noun", "artist names a person"),
                    evidence("Labels paints.", "paints is a verb", "paints shows action"),
                    evidence("Labels young.", "young is an adjective", "young describes the artist"),
                    evidence("Labels bright.", "bright is an adjective", "bright describes the banner"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Helpful Raman shares local stories.",
                "Give the jobs of Raman, shares, helpful, and local.",
                "Raman is a proper noun, shares is a verb, and helpful and local are adjectives.",
                [
                    evidence("Labels Raman.", "Raman is a proper noun", "Raman names one person"),
                    evidence("Labels shares.", "shares is a verb", "shares shows action"),
                    evidence("Labels helpful.", "helpful is an adjective", "helpful describes Raman"),
                    evidence("Labels local.", "local is an adjective", "local describes stories"),
                ],
            ),
            (
                "A skilled drummer leads the lively parade.",
                "Classify drummer, leads, skilled, and lively.",
                "Drummer is a noun, leads is a verb, and skilled and lively are adjectives.",
                [
                    evidence("Labels drummer.", "drummer is a noun", "drummer names a person"),
                    evidence("Labels leads.", "leads is a verb", "leads shows action"),
                    evidence("Labels skilled.", "skilled is an adjective", "skilled describes the drummer"),
                    evidence("Labels lively.", "lively is an adjective", "lively describes the parade"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Curious Leela studies an old map.",
                "Transfer the word-job check to Leela, studies, curious, and old.",
                "Leela is a proper noun, studies is a verb, and curious and old are adjectives.",
                [
                    evidence("Labels Leela.", "Leela is a proper noun", "Leela names one person"),
                    evidence("Labels studies.", "studies is a verb", "studies shows action"),
                    evidence("Labels curious.", "curious is an adjective", "curious describes Leela"),
                    evidence("Labels old.", "old is an adjective", "old describes the map"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:profile_question_builder": {
        "guided": [
            choice_task(
                "Word set: language / home / which / at / do / use / you",
                "Which option forms the complete respectful question?",
                "Which language do you use at home?",
                ["Language home which you do use at.", "which Language at home use you"],
            ),
            open_task(
                "Word set: activity / favourite / your / what / is",
                "Arrange every word as a finished profile question.",
                "What is your favourite activity?",
                [
                    evidence("Uses the question order.", "what is your favourite activity", "ask about the favourite activity"),
                    evidence("Uses a natural question ending.", "favourite activity?", "your favourite activity?"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Word set: festival / family / does / your / which / name",
                "Build a question that asks for a volunteered festival name.",
                "Which festival does your family name?",
                [
                    evidence("Uses the supplied order.", "which festival does your family name", "ask which festival the family names"),
                    evidence("Uses a natural question ending.", "family name?", "your family name?"),
                ],
            ),
            (
                "Reply needing repair: my chosen club is the music circle",
                "Add complete statement boundaries to the profile reply.",
                "My chosen club is the Music Circle.",
                [
                    evidence("Keeps the complete reply.", "my chosen club is the Music Circle", "chosen club is the Music Circle"),
                    evidence("Uses a natural statement ending.", "Music Circle.", "the Music Circle."),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Word set: museum / chose / why / this / object / you / did",
                "Transfer profile-question ordering to a museum choice.",
                "Why did you choose this museum object?",
                [
                    evidence("Uses the question order.", "why did you choose this museum object", "ask why this object was chosen"),
                    evidence("Uses a natural question ending.", "museum object?", "this museum object?"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:welcome_and_belonging_writer": {
        "guided": [
            choice_task(
                "Welcome card: Noor enjoys kite making. Dia enjoys seed collecting. Shared group: both join the craft-and-nature fair.",
                "Which sentence values the difference and shared group?",
                "Noor and Dia bring different interests to the same fair group.",
                ["One interest is better than the other.", "They must enjoy exactly the same activity."],
                skills=[S["comprehension"]],
            ),
            open_task(
                "Welcome card: Pavi reads Tamil stories. Karan reads Hindi stories. Both choose to help arrange the multilingual book shelf.",
                "Write a respectful sentence using both differences and the shared action.",
                "Pavi and Karan read stories in different languages, and both help arrange the multilingual shelf.",
                [
                    evidence("States Pavi's fact.", "Pavi reads Tamil stories", "Tamil stories are Pavi's choice"),
                    evidence("States Karan's fact.", "Karan reads Hindi stories", "Hindi stories are Karan's choice"),
                    evidence("States the shared action.", "both help arrange the multilingual shelf", "work together on the book shelf"),
                ],
                interaction="creative_continuation",
            ),
        ],
        "independent": _open_set([
            (
                "Welcome card: Lobsang brings a family recipe card for dumplings. Sara brings a recipe card for lemon rice. Both cards join the class food-stories folder.",
                "Write a belonging response that names each contribution without ranking them.",
                "Lobsang and Sara share different family recipe cards, and both contributions belong in the class food-stories folder.",
                [
                    evidence("Names Lobsang's contribution.", "Lobsang brings a dumpling recipe", "recipe card for dumplings"),
                    evidence("Names Sara's contribution.", "Sara brings a lemon-rice recipe", "recipe card for lemon rice"),
                    evidence("States equal belonging.", "both contributions belong", "both cards join the class folder"),
                ],
            ),
            (
                "Welcome card: One new pupil uses a wheelchair and chooses scorekeeping. Another new pupil prefers drawing team signs. Both roles help the sports day.",
                "Create a respectful welcome that values the two chosen roles.",
                "We welcome both pupils: scorekeeping and drawing signs are different roles that help our sports day.",
                [
                    evidence("Welcomes both pupils.", "welcome both pupils", "both new pupils are welcome"),
                    evidence("Names scorekeeping.", "scorekeeping", "keeping the scores"),
                    evidence("Names drawing signs.", "drawing signs", "making team signs"),
                    evidence("States the shared value.", "both roles help sports day", "different roles support the event"),
                ],
            ),
        ], interaction="creative_continuation"),
        "transfer": _open_set([
            (
                "Team card: Aman solves number puzzles quickly. Reva explains directions clearly. The group needs both skills to plan a treasure trail.",
                "Transfer belonging writing to this mixed-skill team.",
                "Aman's number skill and Reva's clear directions are different strengths that both help the treasure-trail team.",
                [
                    evidence("Names Aman's strength.", "Aman's number skill", "Aman solves number puzzles"),
                    evidence("Names Reva's strength.", "Reva's clear directions", "Reva explains directions clearly"),
                    evidence("States shared team value.", "both help the treasure-trail team", "different strengths support the same plan"),
                ],
            )
        ], interaction="creative_continuation"),
    },
}

LAUNCH_DEPTH = {
    f"{CHAPTER_ID}:profile_fact_reader": {
        "transfer": _open_set(
            [
                (
                    "Fictional profile card: Lina lives near the sea, speaks Konkani with her grandmother, and enjoys making shell patterns.",
                    "State Lina's place, language, family link, and activity.",
                    "Lina lives near the sea, speaks Konkani with her grandmother, and likes making shell patterns.",
                    [
                        evidence("Reports the place.", "lives near the sea", "near the sea"),
                        evidence("Reports the language.", "speaks Konkani", "Konkani"),
                        evidence("Reports the family link.", "with her grandmother", "grandmother"),
                        evidence("Reports the activity.", "likes making shell patterns", "shell patterns"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Fictional learner note: Tenzin moved from a hill town in June. He reads adventure comics and uses Tibetan at home with his parents.",
                    "Give the move, month, reading interest, and home-language facts.",
                    "Tenzin moved from a hill town in June, reads adventure comics, and uses Tibetan with his parents at home.",
                    [
                        evidence("Reports the move and month.", "moved from a hill town in June", "hill town in June"),
                        evidence("Reports the reading interest.", "reads adventure comics", "adventure comics"),
                        evidence("Reports the home language.", "uses Tibetan with his parents", "Tibetan"),
                    ],
                ),
                (
                    "Fictional club badge: Mariam is in Class 2B, belongs to the nature club, and brings leaf rubbings made with her older cousin.",
                    "Report Mariam's class, club, project, and helper.",
                    "Mariam is in Class 2B, joins the nature club, and makes leaf rubbings with her older cousin.",
                    [
                        evidence("Reports the class.", "in Class 2B", "Class 2B"),
                        evidence("Reports the club.", "joins the nature club", "nature club"),
                        evidence("Reports the project.", "makes leaf rubbings", "leaf rubbings"),
                        evidence("Reports the helper.", "with her older cousin", "older cousin"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:inquiry_and_festival_sequence": {
        "transfer": _open_set(
            [
                (
                    "For a family-food inquiry, Ana asks her father for the dish name, watches her aunt shape the dough, and writes the ingredients after tasting with permission.",
                    "Sequence Ana's respectful inquiry from question to notes.",
                    "Ana asks for the dish name, watches her aunt shape the dough, and writes the ingredients after receiving permission to taste.",
                    [
                        evidence("States the first question.", "asks for the dish name", "asks her father"),
                        evidence("States the observation.", "watches her aunt shape the dough", "shape the dough"),
                        evidence("States the permission.", "receiving permission to taste", "with permission"),
                        evidence("States the final note.", "writes the ingredients", "ingredients"),
                    ],
                )
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "Before the neighbourhood lantern evening, children clean glass jars, adults fit safe lights, and everyone places the lanterns along the wall after sunset.",
                    "Retell the preparation and display steps in order.",
                    "The children clean the jars, adults fit safe lights, and everyone places the lanterns along the wall after sunset.",
                    [
                        evidence("States the cleaning step.", "children clean the jars", "clean glass jars"),
                        evidence("States the light step.", "adults fit safe lights", "safe lights"),
                        evidence("States the display step.", "places the lanterns along the wall after sunset", "after sunset"),
                    ],
                ),
                (
                    "To learn a harvest song's meaning, Kabir asks the singer, listens to one line, repeats the meaning in his own words, and thanks her.",
                    "Sequence Kabir's inquiry and respectful ending.",
                    "Kabir asks the singer, listens to one line, explains its meaning in his own words, and then thanks her.",
                    [
                        evidence("States the question step.", "asks the singer", "Kabir asks"),
                        evidence("States the listening step.", "listens to one line", "one line"),
                        evidence("States the paraphrase.", "explains its meaning in his own words", "own words"),
                        evidence("States the thanks.", "then thanks her", "thanks her"),
                    ],
                ),
            ],
            ordered=True,
        ),
    },
    f"{CHAPTER_ID}:culture_and_belonging_words": {
        "transfer": _open_set(
            [
                (
                    "A tradition is a valued practice shared over time. In this fictional family, everyone plants one herb on the first rainy Sunday each year.",
                    "Explain tradition and use it for a different repeated practice.",
                    "A tradition is a valued practice repeated over time. Our class tradition is to display a new friendship quilt each year.",
                    [
                        evidence("Explains tradition.", "valued practice repeated over time", "shared over time"),
                        evidence("Uses tradition freshly.", "class tradition is to display a new friendship quilt each year", "class tradition"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Belong means feel accepted as part of a group. Rupa belongs in the chess club because teammates listen to her ideas and include her turns.",
                    "State what belong means and use it in another welcoming sentence.",
                    "Belong means feel accepted in a group. Every child can belong in our reading circle and share an idea.",
                    [
                        evidence("Explains belong.", "feel accepted in a group", "Belong means"),
                        evidence("Uses belong inclusively.", "Every child can belong in our reading circle", "can belong"),
                    ],
                ),
                (
                    "A bilingual sign gives the same library message in Hindi and English. Bilingual means using two languages.",
                    "Explain bilingual and write one accurate community use.",
                    "Bilingual means using two languages. The clinic has a bilingual welcome board in Tamil and English.",
                    [
                        evidence("Explains bilingual.", "using two languages", "Bilingual means"),
                        evidence("Uses bilingual accurately.", "bilingual welcome board in Tamil and English", "bilingual welcome board"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:visible_culture_spellings": {
        "transfer": _open_set(
            [
                (
                    "Visible parts: fest + ival. The clue names a special time of shared celebration.",
                    "Join the parts and use the completed word in a sentence.",
                    "The word is festival. Our fictional town holds a kite festival in the open field.",
                    [
                        evidence("Spells the target word.", "word is festival", "spell it festival"),
                        evidence("Uses festival accurately.", "town holds a kite festival in the open field", "kite festival"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Candidates: language, langauge, languge. The profile sentence needs the standard word for a system people speak or sign.",
                    "Choose the correct spelling and write one complete use.",
                    "The standard spelling is language. Sign language helps people share ideas with hand shapes and movement.",
                    [
                        evidence("Gives the standard spelling.", "standard spelling is language", "spell it language"),
                        evidence("Uses language accurately.", "Sign language helps people share ideas", "Sign language"),
                    ],
                ),
                (
                    "Base word: welcome. Add ing to name the act of receiving someone kindly.",
                    "Build the new word and use it in a school sentence.",
                    "The new word is welcoming. A welcoming class makes space for every new learner.",
                    [
                        evidence("Builds the spelling.", "new word is welcoming", "spell it welcoming"),
                        evidence("Uses welcoming accurately.", "welcoming class makes space for every new learner", "welcoming class"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:profile_word_jobs": {
        "transfer": _open_set(
            [
                (
                    "The proud dancer wears a silver scarf.",
                    "Classify dancer, wears, proud, and silver.",
                    "Dancer is a noun, wears is a verb, and proud and silver are adjectives.",
                    [
                        evidence("Labels dancer.", "Dancer is a noun", "dancer names a person"),
                        evidence("Labels wears.", "wears is a verb", "wears shows action"),
                        evidence("Labels proud.", "proud is an adjective", "proud describes the dancer"),
                        evidence("Labels silver.", "silver is an adjective", "silver describes the scarf"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "A skilled potter shapes the soft clay.",
                    "Give the jobs of potter, shapes, skilled, and soft.",
                    "Potter is a noun, shapes is a verb, and skilled and soft are adjectives.",
                    [
                        evidence("Labels potter.", "Potter is a noun", "potter names a person"),
                        evidence("Labels shapes.", "shapes is a verb", "shapes shows action"),
                        evidence("Labels skilled.", "skilled is an adjective", "skilled describes the potter"),
                        evidence("Labels soft.", "soft is an adjective", "soft describes the clay"),
                    ],
                ),
                (
                    "The joyful family shares a special meal.",
                    "Classify family, shares, joyful, and special in this community-meal sentence.",
                    "Family is a noun, shares is a verb, and joyful and special are adjectives.",
                    [
                        evidence("Labels family.", "Family is a noun", "family names a group"),
                        evidence("Labels shares.", "shares is a verb", "shares shows action"),
                        evidence("Labels joyful.", "joyful is an adjective", "joyful describes the family"),
                        evidence("Labels special.", "special is an adjective", "special describes the meal"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:profile_question_builder": {
        "transfer": _open_set(
            [
                (
                    "Word set: which / languages / are / on / this welcome sign",
                    "Arrange every word as one respectful question.",
                    "Which languages are on this welcome sign?",
                    [
                        evidence("Uses natural question order.", "Which languages are on this welcome sign", "Which languages"),
                        evidence("Uses the question ending.", "welcome sign?", "sign?"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Unfinished question: may i ask about your favourite family tradition",
                    "Add correct capitals and the question ending.",
                    "May I ask about your favourite family tradition?",
                    [
                        evidence("Uses the opening capitals.", "May I ask", "May I"),
                        evidence("Uses the complete question ending.", "family tradition?", "tradition?"),
                    ],
                ),
                (
                    "Word set: how / do / you / say / welcome / in Malayalam",
                    "Build a complete polite language question.",
                    "How do you say welcome in Malayalam?",
                    [
                        evidence("Uses natural question order.", "How do you say welcome", "How do you say"),
                        evidence("Capitalizes the language name.", "in Malayalam?", "Malayalam"),
                        evidence("Uses the question mark.", "Malayalam?", "welcome in Malayalam?"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:welcome_and_belonging_writer": {
        "transfer": _open_set(
            [
                (
                    "Fictional new-learner card: Pema loves skipping games, understands English and Nepali, and feels unsure about joining at recess.",
                    "Write two welcoming sentences using all three facts.",
                    "Welcome, Pema! You can join our skipping game, and we can use English or Nepali while we play together.",
                    [
                        evidence("Uses the person's name.", "Welcome, Pema", "Pema"),
                        evidence("Uses the activity interest.", "join our skipping game", "skipping game"),
                        evidence("Uses both languages.", "English or Nepali", "Nepali"),
                        evidence("Creates belonging.", "play together", "join our"),
                    ],
                )
            ],
            interaction="paragraph_text",
        ),
        "review": _open_set(
            [
                (
                    "The culture table has space for six cards. Learners offer a recipe memory, a greeting, a family game, and three festival drawings.",
                    "Write a two-sentence display plan that includes every contribution fairly.",
                    "Place the recipe memory, greeting, and family-game cards in the first row. Display the three festival drawings equally across the second row.",
                    [
                        evidence("Uses the three card contributions.", "recipe memory, greeting, and family-game cards", "first row"),
                        evidence("Uses all three drawings.", "three festival drawings", "second row"),
                        evidence("States fair display.", "equally across", "includes every contribution"),
                    ],
                ),
                (
                    "A class celebration includes one song in Bengali, a Tamil welcome message, and a silent hand-sign greeting. The programme has three equal time slots.",
                    "Create an inclusive programme in two complete sentences.",
                    "Give one equal time slot to the Bengali song and one to the Tamil welcome. Use the third slot for the hand-sign greeting so every contribution is included.",
                    [
                        evidence("Includes the Bengali song.", "time slot to the Bengali song", "Bengali song"),
                        evidence("Includes the Tamil welcome.", "one to the Tamil welcome", "Tamil welcome"),
                        evidence("Includes the signed greeting.", "third slot for the hand-sign greeting", "hand-sign greeting"),
                        evidence("Uses the equal-time condition.", "one equal time slot", "every contribution is included"),
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
            choice_task("A custom is customary when a community follows it regularly over time.", "Which meaning fits customary?", "usual in a community", ["hidden from everyone", "finished only once by accident"], skills=[S["word_context"]]),
            choice_task("Profile A: Jaya speaks Assamese. Profile B: Manu speaks Nepali. Only Manu collects leaf prints.", "Who collects leaf prints?", "Manu", ["Jaya", "both children"], skills=[S["comprehension"]]),
            choice_task("First pupils see a wooden wheel, next they ask its use, and last a maker demonstrates it.", "Which event happens second?", "They ask its use.", ["They see the wheel.", "The maker demonstrates it."], skills=[S["sequence"]]),
            choice_task("Sentence frame: Every learner can ___ in our reading group.", "Which chapter word means be an accepted member?", "belong", ["scatter", "vanish"], skills=[S["word_use"]]),
            choice_task("Candidates: festival, festivel, festivle. The sentence names a special celebration.", "Which spelling is standard?", "festival", ["festivel", "festivle"], skills=[S["spelling"]]),
            choice_task("A patient guide explains the ancient monument.", "Which word shows the action?", "explains", ["patient", "guide"], skills=[S["word_jobs"]]),
            open_task("Word set: which / language / do / you / speak / at home", "Build the profile question.", "Which language do you speak at home?", [evidence("Uses the complete question order.", "which language do you speak at home", "language do you speak")], skills=[S["sentence_order"]]),
            open_task("Unfinished line: many profiles belong in our class book", "Add the correct sentence boundaries.", "Many profiles belong in our class book.", [evidence("Uses a capital beginning.", "Many"), evidence("Uses a full stop.", ".")], skills=[S["punctuation"]]),
            open_task("Asha speaks Marathi; Noor speaks Urdu. Shared fact: both make labels for the garden map.", "Write one respectful difference-and-shared-action sentence.", "Asha and Noor speak different languages, but both make labels for the garden map.", [evidence("Includes both language difference neutrally.", "different languages", "Asha", "Noor"), evidence("Includes shared label task.", "both", "labels", "garden map")], skills=[S["sentence"]]),
            open_task("A class sees a loom, asks how it works, and then watches yarn become a narrow strip.", "Retell the inquiry and final demonstration in order.", "The class observes the loom, asks how it works, and watches yarn become a narrow strip.", [evidence("Orders observation before question.", "observes the loom", "asks how"), evidence("Ends with yarn becoming a strip.", "yarn", "narrow strip")], skills=[S["comprehension"], S["sequence"]], ordered=True),
            open_task("Inclusive means welcoming participation. Use inclusive with a correctly spelled chapter word.", "State the meaning and create the new use.", "Inclusive means welcoming participation. The inclusive festival team gives every member a task.", [evidence("Explains welcoming participation.", "welcoming participation"), evidence("Uses inclusive and festival accurately.", "inclusive festival team", "every member")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
            open_task("Word set: tradition / which / does / class / share / the", "Build and punctuate the complete question.", "Which tradition does the class share?", [evidence("Uses correct question order.", "which tradition does the class share"), evidence("Uses capital and question mark.", "Which", "?")], skills=[S["sentence_order"], S["punctuation"]]),
        ]
    return [
        choice_task("The neighbourhood is diverse because residents use several languages and practise different arts.", "Which meaning fits diverse?", "containing different kinds", ["having only one kind", "empty of people"], skills=[S["word_context"]]),
        choice_task("Profile A: Ritu paints masks. Profile B: Pawan plays the flute. Only Ritu lives in Ranchi.", "Who lives in Ranchi?", "Ritu", ["Pawan", "both children"], skills=[S["comprehension"]]),
        choice_task("A festival plan begins with tree care, continues with a seed fair, and ends with a lantern walk.", "What happens immediately before the lantern walk?", "the seed fair", ["tree care", "a puppet show"], skills=[S["sequence"]]),
        choice_task("Sentence frame: A ___ is an important structure linked with history.", "Which chapter word fits the definition?", "monument", ["wrapper", "droplet"], skills=[S["word_use"]]),
        choice_task("Candidates: India, Indea, Indiya. A profile lists the country beside the learner's city.", "Which spelling is standard?", "India", ["Indea", "Indiya"], skills=[S["spelling"]]),
        choice_task("The skilled artisan twists loose fibre.", "Which word describes the artisan?", "skilled", ["artisan", "twists"], skills=[S["word_jobs"]]),
        open_task("Word set: our / class / welcomes / every / new child", "Arrange the complete statement.", "Our class welcomes every new child.", [evidence("Uses correct statement order.", "our class welcomes every new child", "welcomes every new child"), evidence("Uses every word.", "our class", "new child")], skills=[S["sentence_order"]]),
        open_task("Unfinished question: what local craft did you learn", "Repair both sentence boundaries.", "What local craft did you learn?", [evidence("Uses a capital beginning.", "What"), evidence("Uses a question mark.", "?")], skills=[S["punctuation"]]),
        open_task("Mira enjoys dance; Kabir enjoys painting. Shared fact: both help prepare welcome day.", "Write one respectful comparison with the shared result.", "Mira and Kabir enjoy different arts, but both help prepare welcome day.", [evidence("Includes different arts neutrally.", "different arts", "Mira", "Kabir"), evidence("Includes shared welcome task.", "both", "prepare welcome day")], skills=[S["sentence"]]),
        open_task("Children notice a toothed tool, ask its purpose, and watch it mark a straight seed line.", "Give the inquiry sequence and demonstrated use.", "The children notice the toothed tool, ask its purpose, and watch it mark a seed line.", [evidence("Orders noticing before asking.", "notice the toothed tool", "ask its purpose"), evidence("Ends with marking a seed line.", "mark a seed line")], skills=[S["comprehension"], S["sequence"]], ordered=True),
        open_task("Heritage means valued culture from earlier times. Use heritage with a correctly spelled culture word.", "State the meaning and write the new use.", "Heritage means valued culture from earlier times. The puppet festival shares part of the region's craft heritage.", [evidence("Explains valued culture from earlier times.", "valued culture", "earlier times"), evidence("Uses festival and heritage accurately.", "puppet festival", "craft heritage")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
        open_task("Word set: monument / did / which / visit / class / the", "Build the finished question with correct punctuation.", "Which monument did the class visit?", [evidence("Uses correct question order.", "which monument did the class visit"), evidence("Uses capital and question mark.", "Which", "?")], skills=[S["sentence_order"], S["punctuation"]]),
    ]


CONFIG = {
    "chapter_id": CHAPTER_ID,
    "chapter_no": 13,
    "title": "We are all Indians",
    "unit_title": "Harmony",
    "source_url": SOURCE_URL,
    "extract_path": "/tmp/zidd-ncert-class2-3/eng_c2_ch13.txt",
    "source_anchors": [
        {"anchor_id": f"{CHAPTER_ID}:read-profiles:1-7", "section_label": "Let us read: profiles, languages, places, arts, and shared belonging", "page_start": 1, "page_end": 7, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:speak:8", "section_label": "Let us speak: polite situations and partner profile questions", "page_start": 8, "page_end": 8, "source_url": SOURCE_URL, "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:draw:9", "section_label": "Let us draw: favourite home object", "page_start": 9, "page_end": 9, "source_url": SOURCE_URL, "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:speak-listen:10", "section_label": "Let us speak and listen: printed br and fr words with local musician companion", "page_start": 10, "page_end": 10, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:write:11-12", "section_label": "Let us write: country, festival, language spelling, and sentence joining", "page_start": 11, "page_end": 12, "source_url": SOURCE_URL, "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:something-new:13-14", "section_label": "Something New: classroom object inquiry and craft explanation", "page_start": 13, "page_end": 14, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:write-match:15", "section_label": "Let us write: picture-based fruit and tree matching", "page_start": 15, "page_end": 15, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:festival-read:16-17", "section_label": "Let us read: regional festival information", "page_start": 16, "page_end": 17, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:project:18", "section_label": "Project: offline family folk-song presentation", "page_start": 18, "page_end": 18, "source_url": SOURCE_URL, "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
    ],
    "levels": LEVELS,
    "assessment_forms": [_assessment_form("a"), _assessment_form("b")],
}


MANIFEST = build_manifest(CONFIG)
