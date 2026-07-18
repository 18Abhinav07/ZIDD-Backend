"""Deep authored manifest for Class 3 English Chapter 11.

The source extract informed chapter themes and activity forms only. All Zidd
runtime passages, questions, choices, responses, and rubrics are original.
"""

from __future__ import annotations

from typing import Any

from app.content.school_rebuild_manifests.english.class_3.eng_c3_ch07 import (
    _assessment_pair,
    _case,
    _connect,
    _fresh_case,
    build_manifest,
)


SPEC: dict[str, Any] = {
    "chapter_id": "eng_c3_ch11",
    "chapter_no": 11,
    "title": "Chanda Mama Counts the Stars",
    "unit_title": "The Sky",
    "source_url": "https://ncert.nic.in/textbook/pdf/cesa111.pdf",
    "source_analysis_reference": (
        "/tmp/zidd-ncert-class2-3/eng_c3_ch11.txt structure review"
    ),
    "anchors": [
        {"label": "Let us read: repeated star-count attempts and the Sun's resolution", "page_start": 1, "page_end": 3, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us think A-B: count comprehension and count reflection", "page_start": 4, "page_end": 4, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us learn: here and there for near and far locations", "page_start": 5, "page_end": 6, "treatment": "taught_and_assessed", "required": True},
        {"label": "Source quantity-sorting list adapted to text-only count judgments", "page_start": 7, "page_end": 7, "treatment": "zidd_equivalent", "required": True},
        {"label": "Let us write A: full-moon dialogue completion and punctuation", "page_start": 8, "page_end": 8, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us listen: sort quantities by ease of counting", "page_start": 7, "page_end": 7, "treatment": "guided_only", "required": False},
        {"label": "Let us write: picture-supported full-moon conversation", "page_start": 8, "page_end": 8, "treatment": "textbook_companion", "required": False},
        {"label": "Let us do project: build hanging Moon and star shapes", "page_start": 9, "page_end": 9, "treatment": "offline_group_activity", "required": False},
    ],
    "levels": [
        {
            "level_id": "star_counter_sequence",
            "title": "Track a repeated count",
            "focus": "order a repeated attempt and identify the story's main idea",
            "concept": "count attempt sequence",
            "outcome": "Sequence an attempt, interruption, restart, and resolution, then state a main idea about persistence and a more useful way to respond.",
            "skill_ids": ["reading.event_sequence", "reading.paragraph_main_idea"],
            "episode_kind": "comprehension_studio",
            "anchor_indexes": [1],
            "principle": "Repeated-story events are not duplicates: each attempt changes the problem or response. A main idea should explain that development rather than list numbers.",
            "connect": _connect(
                "A character may repeat a task and still move the story forward. Readers mark what interrupts each attempt and how the final response changes the character's understanding.",
                "A rooftop watcher counted lanterns, lost track when clouds covered the lane, restarted, and finally grouped the lanterns by street instead of starting over again.",
                "Trace the first count, interruption, restart, and improved method.",
            ),
            "misconception": "The learner lists numbers without tracking events or treats the final comforting idea as another failed attempt instead of a resolution.",
            "remediation": "Label attempt, interruption, repeat, and resolution; place them on a four-box line; then write one sentence about what changed by the end.",
            "ordered_response": True,
            "cases": [
                _case("lantern count", "Navi counts rooftop lanterns, loses track when a cloud darkens the lane, begins again, and then groups them by building.", "Which sequence and main idea fit?", "Navi's failed count leads to a better grouping method.", "Navi groups lanterns before seeing any roof.", "The story is mainly a list of building colours.", "The interruption causes a restart and later improvement.", "failed count better method", "interruption leads improvement"),
                _case("shell count", "Uma counts shells in a jar. The jar tips, she gathers the shells, and she restarts by placing counted shells in a second bowl.", "What progression solves the repeated problem?", "Uma loses the count and then separates counted shells to avoid another mistake.", "Uma uses the second bowl before the jar tips.", "The shells count Uma.", "The new separation method responds to the earlier confusion.", "loses count separates", "method answers problem"),
                _case("seed packets", "A gardener counts seed packets, answers a visitor, forgets the total, and finally makes groups of ten before recounting.", "Which main idea covers all events?", "An interruption makes the gardener adopt groups of ten for a reliable count.", "The visitor plants every seed before counting.", "The story is mainly about packet pictures.", "The grouped restart changes the method after forgetting.", "interruption groups ten", "reliable restart"),
                _case("bus tokens", "Rehan counts bus tokens one by one. A token rolls away, he finds it, and he starts again using rows of five.", "How does the event sequence develop?", "A lost token interrupts Rehan, and rows of five help his new count.", "Rows of five roll away before any count.", "The bus drives through the token box.", "The later arrangement directly addresses the disrupted count.", "lost token rows five", "arrangement helps count"),
                _case("library books", "Maya counts returned books, grows tired, rests, and then checks the librarian's labelled stacks instead of repeating every title.", "What is the central movement?", "Maya pauses a tiring count and uses organised stacks to finish sensibly.", "Maya labels stacks before entering the library.", "The passage is mainly about book stories.", "Rest and organisation change an exhausting method.", "tiring count organised stacks", "method changes sensibly"),
                _case("window lights", "A child counts lit windows, falls asleep, wakes after some lights are off, and realises the changing scene cannot preserve one total.", "Which summary captures the resolution?", "The child learns that a changing set of lights cannot keep the same count overnight.", "Every window stays lit forever.", "Sleeping creates new buildings.", "The changed scene explains why the old total no longer works.", "changing lights old count", "scene changes total"),
                _case("garden buds", "Javed counts buds on Monday, returns after new buds open on Tuesday, and records separate daily totals instead of correcting Monday's number.", "What sequence shows a useful solution?", "Javed notices change and keeps separate totals for each day.", "Javed records Tuesday before visiting Monday.", "The buds erase the calendar.", "Daily records respect that the group changes over time.", "change separate totals", "daily records solution"),
            ],
        },
        {
            "level_id": "count_words_context",
            "title": "Interpret quantity words",
            "focus": "infer quantity vocabulary and use count words precisely",
            "concept": "count vocabulary",
            "outcome": "Distinguish exact, estimate, total, countless, and group from visible context, then apply each word without claiming impossible precision.",
            "skill_ids": ["reading.word_meaning_context", "vocab.chapter_word_usage"],
            "episode_kind": "meaning_encounter",
            "anchor_indexes": [2, 4],
            "principle": "Quantity words differ in precision. Exact comes from complete counting, estimate is a close judgement, and countless means too many for a practical count in the situation.",
            "connect": _connect(
                "A useful count word matches the evidence available. Readers should not call a quick guess exact or claim that a small visible set is countless.",
                "There are exactly twelve crayons because Pia touched and counted each one. She estimates about fifty pebbles in the large jar without removing them.",
                "Compare the complete crayon count with the reasonable pebble estimate.",
            ),
            "misconception": "The learner treats estimate and exact as synonyms or uses countless for any group larger than ten.",
            "remediation": "Ask whether every item was checked, label the result exact or estimated, and reserve countless for a set impractical to enumerate in the stated situation.",
            "cases": [
                _case("crayon exact", "Pia touches every crayon once and records twelve. No crayon is hidden or repeated.", "Which quantity word fits the result?", "Twelve is an exact count because every crayon was checked once.", "Twelve is only a wild estimate despite complete checking.", "The crayons are countless because there are more than five.", "Complete one-to-one checking supports precision.", "exact count twelve", "every crayon checked"),
                _case("pebble estimate", "Without emptying a large jar, Om compares its layers with a ten-pebble cup and says it holds about sixty.", "What kind of quantity statement is about sixty?", "About sixty is an estimate based on comparison.", "About sixty is an exact total from touching every pebble.", "The jar contains no pebbles.", "The word about and indirect comparison signal approximation.", "estimate about sixty", "comparison not full count"),
                _case("finger total", "Rae counts five fingers on one hand and five on the other, then combines the two groups.", "Which word describes the combined ten?", "Ten is the total after combining both groups.", "Ten is countless and cannot be checked.", "Total means only the fingers on one hand.", "Adding the complete groups produces the whole amount.", "total combined ten", "both groups whole"),
                _case("bead groups", "A craft box holds forty beads arranged in four equal rows of ten.", "How does group help explain the count?", "Each row is a group of ten, and four groups make forty.", "A group means one bead hidden alone.", "Forty is only a weather estimate.", "The repeated rows make the total easy to verify.", "group of ten", "four groups forty"),
                _case("sand grains", "A child sees a bucket of fine sand and says the grains are countless for a quick classroom activity.", "What does countless mean in this context?", "Countless means too many to count practically in the available activity time.", "Countless means there are exactly twelve grains.", "Countless means the bucket is empty.", "The tiny numerous grains and limited time make full counting impractical.", "countless too many", "impractical available time"),
                _case("ticket total", "The monitor checks each numbered ticket from one through thirty and finds none missing.", "Which precision word belongs in the report?", "Thirty is the exact total because all numbered tickets were checked.", "Thirty is countless because tickets have numbers.", "Thirty is an estimate made without looking.", "Continuous numbering and full checking establish an exact total.", "exact total thirty", "all tickets checked"),
                _case("crowd estimate", "From a balcony, a guide sees ten similar rows with roughly twenty people in each and reports about two hundred people.", "How should the guide's number be described?", "About two hundred is an estimate from row size, not an exact count.", "It is exact because the guide did not count individuals.", "It is countless because rows are visible.", "Approximate row multiplication supports a reasoned estimate.", "estimate two hundred", "row size approximation"),
            ],
        },
        {
            "level_id": "here_there_location",
            "title": "Choose here or there",
            "focus": "interpret a location sentence and use here or there relative to the speaker",
            "concept": "here and there location",
            "outcome": "Identify the speaker's position, decide whether the named place is near or farther away, and complete a meaningful sentence with here or there.",
            "skill_ids": ["grammar.adverbs", "reading.sentence_comprehension"],
            "episode_kind": "language_lab",
            "anchor_indexes": [3],
            "principle": "Here points to the speaker's current near place; there points away from it. The same object may be here for one speaker and there for another.",
            "connect": _connect(
                "Location words depend on viewpoint. Readers first locate the speaker, then compare the target place with that position instead of memorising one word for each object.",
                "Mira stands beside the telescope and says, 'The eyepiece is here beside me, but the observatory gate is there across the field.'",
                "Use Mira's position to separate the nearby eyepiece from the distant gate.",
            ),
            "misconception": "The learner assumes here always means indoors or chooses there for a large object without checking distance from the stated speaker.",
            "remediation": "Mark the speaker with S, draw near and far circles, place each location in a circle, and reread the completed sentence from that viewpoint.",
            "cases": [
                _case("telescope view", "Mira is touching the telescope. She points across the field to a gate and says the telescope is ___, while the gate is ___.", "Which pair matches Mira's viewpoint?", "The telescope is here, and the gate is there.", "The telescope is there, and the gate is here.", "Both places must be here because they are visible.", "Touching marks the near place while across the field marks distance.", "telescope here gate there", "touching versus across"),
                _case("class shelf", "Arun sits beside his desk. His pencil is on the desk, and the book shelf is at the far wall.", "How should Arun use here and there?", "The pencil is here by Arun, and the shelf is there at the far wall.", "The pencil is there by Arun, and the far shelf is here.", "Distance does not affect either word.", "Beside identifies near; far wall identifies away.", "pencil here shelf there", "beside far wall"),
                _case("garden call", "Leela stands at the pump and calls, 'Bring the bucket from the shed across the garden to me.'", "Which location words fit the bucket's movement?", "The bucket is there at the shed and should be brought here to Leela.", "The bucket is here at the far shed and moves there to Leela.", "The pump and shed are the same place.", "Across the garden is away from the speaker, while to me marks her near place.", "bucket there bring here", "across versus to me"),
                _case("bus stop", "Nikhil waits at the bus stop. His sister is beside him, and their school is visible beyond the bridge.", "What sentence matches Nikhil's position?", "My sister is here, and our school is there beyond the bridge.", "My sister is there beside me, and the school is here far away.", "Both are there because school starts later.", "Beside him and beyond the bridge establish relative distance.", "sister here school there", "beside beyond bridge"),
                _case("window bird", "Rupa is inside by the window. A sparrow lands on the sill, while a kite circles above a distant tower.", "Which use of here and there is accurate?", "The sparrow is here at the sill, and the kite is there above the tower.", "The sparrow is there beside Rupa, and the distant kite is here.", "Bird size decides the location word.", "The sill is near the speaker; the tower is distant.", "sparrow here kite there", "near sill distant tower"),
                _case("moon model", "A teacher holds a moon model next to her. She points through the window toward the real moon in the sky.", "How does viewpoint change the two moon references?", "The model is here beside the teacher, and the real moon is there in the sky.", "The model is there beside her, and the real moon is here.", "Both must use here because both are moons.", "Object identity is shared, but distance from the speaker differs.", "model here moon there", "same object different distance"),
                _case("shop counter", "The shopkeeper stands behind the counter. A receipt is under her hand, and delivery boxes wait near the road outside.", "Which completed location sentence fits?", "The receipt is here, and the delivery boxes are there near the road.", "The receipt is there under her hand, and the road boxes are here.", "Here means paper and there means boxes.", "Under her hand marks near, while outside by the road marks away.", "receipt here boxes there", "hand versus outside"),
            ],
        },
        {
            "level_id": "moon_dialogue_marks",
            "title": "Track and punctuate dialogue",
            "focus": "attribute dialogue and apply capitals, commas, quotation marks, and end marks",
            "concept": "dialogue punctuation",
            "outcome": "Match each line to its speaker and write a short correctly punctuated exchange with capitals, quotation marks, and suitable question or statement marks.",
            "skill_ids": ["reading.dialogue_attribution", "grammar.punctuation_capitalization"],
            "episode_kind": "expression_workshop",
            "anchor_indexes": [5],
            "principle": "Dialogue tags tell who speaks, while punctuation separates spoken words from narration. A question needs a question mark inside the closing quotation mark.",
            "connect": _connect(
                "A dialogue line has two jobs: show the exact spoken words and identify the speaker. Capitals and end marks help a reader follow the exchange without hearing it.",
                "'Can you see the crescent?' asked Bo. 'Yes, it is above the neem tree,' replied Ina.",
                "Match each quotation to its tag and inspect the question mark and comma placement.",
            ),
            "misconception": "The learner swaps speakers, leaves a question with a full stop, or places quotation marks around the speaker tag as well as the spoken words.",
            "remediation": "Colour the spoken words and tags differently, identify question or statement, add the end mark, enclose only the speech, and check the first capital.",
            "cases": [
                _case("crescent question", "Bo asks whether Ina can see the crescent. Ina answers that it is above the neem tree.", "Which punctuated exchange assigns both speakers correctly?", "Bo asked, 'Can you see the crescent?' Ina replied, 'Yes, it is above the neem tree.'", "Ina asked the question and Bo answered despite the stated tags.", "bo asked can you see the crescent. ina replied yes.", "The question belongs to Bo and carries a question mark; Ina's reply is a statement.", "Bo asked Ina replied", "question mark statement"),
                _case("count check", "Ravi asks, 'Did we count this row?' Noor says, 'No, this row is still unchecked.'", "How should the speakers and marks be preserved?", "Ravi asked, 'Did we count this row?' Noor replied, 'No, this row is still unchecked.'", "Noor asks both lines while Ravi is silent.", "ravi asked did we count this row. noor no.", "The explicit tags and sentence purposes determine ownership and punctuation.", "Ravi asked Noor replied", "question then statement"),
                _case("telescope turn", "Mina says she has finished with the telescope. Dev asks whether he may use it next.", "Which dialogue version is accurate?", "Mina said, 'I have finished.' Dev asked, 'May I use the telescope next?'", "Dev states both lines without asking.", "mina said i have finished? dev asked may i use it.", "Mina's statement ends with a full stop and Dev's request with a question mark.", "Mina said Dev asked", "statement question marks"),
                _case("cloud warning", "Kia tells Omar that a cloud is covering the moon. Omar asks where his torch is.", "How can the exchange be punctuated?", "Kia said, 'A cloud is covering the moon.' Omar asked, 'Where is my torch?'", "Omar gives the cloud statement and Kia asks about a torch.", "kia said a cloud is covering the moon? omar where torch.", "The narration fixes speakers and distinguishes statement from question.", "Kia said Omar asked", "capital and end marks"),
                _case("window count", "Zed asks how many lit windows remain. Ami answers that four remain.", "Which dialogue line pair follows the reference?", "Zed asked, 'How many lit windows remain?' Ami replied, 'Four remain.'", "Ami asks and Zed gives the number.", "zed asked how many lit windows remain. ami four remain?", "The information request is Zed's question; the number is Ami's statement.", "Zed asked Ami replied", "request and answer"),
                _case("morning greeting", "At dawn, Tara says good morning. Her brother asks whether she saw the last star fade.", "Which punctuation supports the purposes?", "Tara said, 'Good morning.' Her brother asked, 'Did you see the last star fade?'", "Her brother says both lines as commands.", "tara said good morning? brother did you see.", "Greeting and question require different end marks and clear capitals.", "Tara said brother asked", "greeting versus question"),
                _case("drawing offer", "Jai asks if he may borrow a silver crayon. Liv says he may take it from her desk.", "How should the exchange be written?", "Jai asked, 'May I borrow a silver crayon?' Liv replied, 'You may take it from my desk.'", "Liv asks to borrow from Jai despite the narration.", "jai asked may i borrow. liv replied you may take it?", "The request and permission follow the named speakers and proper end marks.", "Jai asked Liv replied", "request permission punctuation"),
            ],
        },
        {
            "level_id": "moon_pronoun_agreement",
            "title": "Keep references clear",
            "focus": "select clear pronouns and maintain subject-verb agreement",
            "concept": "pronoun and agreement",
            "outcome": "Replace a repeated noun with an unambiguous pronoun and match singular or plural subjects with is or are in complete reference sentences.",
            "skill_ids": ["grammar.pronouns", "grammar.subject_verb_agreement"],
            "episode_kind": "language_lab",
            "anchor_indexes": [1, 3],
            "principle": "A pronoun must point to one clear earlier noun. Agreement follows the pronoun's number: it is for one thing, while they are for more than one.",
            "connect": _connect(
                "Pronouns reduce repetition only when readers can tell what they replace. After choosing the pronoun, match its singular or plural number to the verb.",
                "The silver moon model is on the desk. It is beside the globe. The two star cards are on the shelf. They are labelled.",
                "Trace it to one model and they to two cards, then check is and are.",
            ),
            "misconception": "The learner uses it after a plural noun, uses they when two possible groups make the reference unclear, or chooses a verb from the nearest noun.",
            "remediation": "Draw an arrow from pronoun to noun, mark one or many, replace an unclear pronoun with the noun, and pair it-is or they-are.",
            "cases": [
                _case("moon model", "The moon model is beside the globe. ___ is painted silver and ___ is easy to lift.", "Which pronoun and agreement complete both references?", "It is painted silver, and it is easy to lift.", "They is painted silver, and it are easy.", "It are painted because model is plural.", "One model takes the singular pronoun it and verb is.", "it is model", "singular agreement"),
                _case("star cards", "The three star cards are on the shelf. ___ are numbered from one to three.", "What clear reference belongs in the blank?", "They are numbered from one to three.", "It is numbered from one to three.", "They is numbered because shelf is singular.", "Three cards require plural they and are.", "they are cards", "plural agreement"),
                _case("telescope lens", "A clean lens is inside the case. ___ is wrapped in soft cloth.", "Which pronoun-verb pair is correct?", "It is wrapped in soft cloth.", "They are wrapped, though only one lens is named.", "It are wrapped in cloth.", "One lens is a clear singular antecedent.", "it is lens", "one antecedent"),
                _case("children count", "Mira and Dev are counting windows. ___ are using separate tally sheets.", "How should the two names be replaced?", "They are using separate tally sheets.", "It is using separate sheets.", "They is using because tally is one word.", "Two people take they and the plural verb are.", "they are Mira Dev", "two people plural"),
                _case("cloud patch", "One dark cloud is above the hill. ___ is moving toward the moon.", "Which completion maintains reference and agreement?", "It is moving toward the moon.", "They are moving, though one cloud is named.", "It are moving toward moon.", "The single cloud is clearly replaced by it.", "it is cloud", "single clear reference"),
                _case("lantern rows", "Two rows of lanterns are along the wall. ___ are equally spaced.", "Which pair agrees with rows?", "They are equally spaced.", "It is equally spaced for both rows.", "They is spaced because wall is singular.", "The plural head noun rows controls pronoun and verb.", "they are rows", "plural head noun"),
                _case("speaker ambiguity", "Rina puts the moon card beside the star cards. Then she points to the moon card and says ___ is larger.", "What pronoun is clear after the pointing clue?", "It is larger, referring to the one moon card.", "They is larger, referring to every card.", "It are larger because cards is nearby.", "Pointing identifies one singular card despite the nearby plural group.", "it is moon card", "pointing clears reference"),
            ],
        },
        {
            "level_id": "moon_kind_response",
            "title": "Infer feelings and respond kindly",
            "focus": "infer a character's need and write a friendly relevant message",
            "concept": "kind dialogue response",
            "outcome": "Use action and feeling clues to infer why someone is upset or relieved, then write a short message that acknowledges the need and offers realistic support.",
            "skill_ids": ["reading.inference_reason", "writing.friendly_message"],
            "episode_kind": "expression_workshop",
            "anchor_indexes": [1, 5],
            "principle": "A kind response begins with an evidence-based inference, not an assumption. It acknowledges the stated difficulty and offers help that the situation makes possible.",
            "connect": _connect(
                "When a character struggles with a task, readers combine visible behaviour and context to infer the need. A useful message answers that need without making an impossible promise.",
                "After losing her tally for the third time, Isha pushes the notebook away and rubs her eyes. Dev offers to make grouped marks with her.",
                "Use the repeated loss and tired action to infer frustration, then judge why Dev's offer is relevant.",
            ),
            "misconception": "The learner labels any quiet character sad or writes general praise without addressing the counting, location, or communication problem shown.",
            "remediation": "Underline one feeling clue and one task clue, state the likely need with may, and write a greeting plus one specific offer tied to that need.",
            "creative_transfer": True,
            "cases": [
                _case("lost tally", "Isha loses her count three times, closes the notebook, and rubs her eyes. Dev has a blank tally chart.", "What can Dev infer, and what message could he send?", "Isha may feel frustrated, so Dev can offer to group the next count on his tally chart.", "Isha is certainly angry about an unseen game.", "Dev should promise to count every star in space.", "Repeated failure and tired behaviour support a specific counting offer.", "may feel frustrated", "offer grouped tally"),
                _case("cloudy view", "Nora waits with a telescope, but thick clouds cover the sky. She sighs and begins packing it away.", "Which inference and friendly response fit?", "Nora may be disappointed, so a friend can suggest trying again on a clear evening.", "Nora dislikes telescopes forever.", "A friend should claim the clouds will vanish immediately.", "The blocked viewing goal supports disappointment and a realistic later plan.", "may be disappointed", "try clear evening"),
                _case("confusing directions", "Aman walks between two doors after hearing only 'over there.' He looks back and asks which door is meant.", "What need should a helpful message address?", "Aman needs a clearer location, so the reply should name the door beside a visible landmark.", "Aman needs a new pair of shoes.", "The reply should repeat only 'there' more loudly.", "His repeated movement and question show that the location phrase is unclear.", "needs clearer location", "name visible landmark"),
                _case("missed turn", "During a dialogue, Fari starts speaking twice but others continue over her. She lowers her hand and becomes quiet.", "What can a classmate infer and write?", "Fari may feel unheard, so a classmate can invite her to share her idea next.", "Fari has no idea because she becomes quiet.", "A classmate should discuss an unrelated lunch.", "Her repeated attempts show a wish to contribute.", "may feel unheard", "invite idea next"),
                _case("wrong total", "Kesh checks his groups and finds that one row has nine beads instead of ten. He frowns at the total.", "Which response supports the actual difficulty?", "Kesh may be worried about the total, so a friend can help recount the short row.", "Kesh dislikes all beads in every setting.", "A friend should hide the uneven row.", "The nine-bead row directly explains concern about accuracy.", "worried about total", "help recount row"),
                _case("forgotten word", "Mili pauses during her moon description, points to the curved edge, and says she cannot remember the shape word.", "What kind message would be relevant?", "Mili needs the word crescent, so a friend can offer the word and let her finish the description.", "Mili needs someone to replace the moon.", "A friend should write the whole answer without her.", "Her pointing and stated memory gap identify the precise support needed.", "needs word crescent", "offer then let finish"),
                _case("completed chart", "After careful grouping, Yara checks the same total twice and smiles at her completed chart.", "What inference and acknowledgement fit?", "Yara may feel relieved and proud, so a friend can praise her careful checking.", "Yara is upset because the chart is complete.", "A friend should erase the verified total.", "Repeated agreement and a smile support relief after effort.", "relieved and proud", "praise careful checking"),
            ],
        },
    ],
}


FRESH_CASES = {
    "star_counter_sequence": [
        _fresh_case("window stars", "Mina counts twelve stars, writes the number, looks again after a cloud moves, and sees seventeen.", "Retell the counting attempt.", "Mina counts, records twelve, checks again, and finds seventeen.", "The moving cloud changes what she can see after the first count.", "count record check seventeen", "cloud changes view"),
        _fresh_case("firefly jar", "Five fireflies glow near a jar. Three fly away, two new ones arrive, and Ravi counts four at the end.", "Which order explains the final count?", "Five glow, three leave, two arrive, and four remain.", "Leaving and arriving happen before the last count.", "five leave arrive four", "changes before final count"),
        _fresh_case("shell rows", "Tara makes two rows of shells, counts each row, finds one shell under the mat, and adds it to the total.", "What happens just before the total changes?", "Tara finds a hidden shell under the mat.", "The new object must be found before it can be added.", "find shell before add", "hidden item changes total"),
        _fresh_case("moving birds", "Aman counts birds on a wire, a bus passes, several birds fly, and he begins a new count.", "What is the story mostly about?", "A changing group makes Aman's first bird count unusable.", "The birds move after the first count, so he checks again.", "moving birds change count", "first total no longer works"),
        _fresh_case("button box", "Leela counts twenty buttons, sorts out four broken ones, and writes sixteen usable buttons on the label.", "How does sixteen follow?", "She removes four broken buttons from the first count of twenty.", "Sorting happens before the usable total is written.", "twenty remove four sixteen", "broken removed first"),
        _fresh_case("moon dots", "A chart shows eight dots on Monday and eleven on Tuesday. Kavi records each day in a separate column.", "Why are separate columns useful?", "They keep Monday's eight apart from Tuesday's eleven.", "The dates name two different sets.", "separate daily counts", "dates prevent mixing"),
        _fresh_case("market lamps", "Nia counts lit lamps at dusk, notes nine, returns after closing time, and finds only two still on.", "State the sequence and change.", "Nia records nine lamps first and two after shops close.", "The time change explains why the groups differ.", "nine then two lamps", "closing changes lights"),
        _fresh_case("pebble groups", "Omar makes groups of five pebbles, counts four full groups, and finds two pebbles left over.", "How should the count be described?", "There are four groups of five and two pebbles remaining.", "Grouping explains the total without losing the leftovers.", "four groups plus two", "leftovers counted separately"),
        _fresh_case("cloud gaps", "A cloud hides part of the sky. Sia counts six stars, waits for a gap, and then counts fourteen.", "Why does she wait?", "Sia waits so more of the sky becomes visible before recounting.", "The cloud is the stated block to a fuller count.", "wait for clear sky", "cloud hid stars"),
        _fresh_case("chalk tally", "Dev sees one bird at a time and adds a chalk mark for each. He groups every fifth mark with a slash.", "What is the main counting method?", "Dev uses one tally per bird and groups the marks by five.", "Each mark stands for one seen bird.", "one tally per bird", "marks grouped five"),
        _fresh_case("seed packets", "Three packets each hold ten seeds. Renu counts by tens, opens one packet, and finds two seeds missing.", "How does the final result change?", "Renu expects thirty seeds but finds twenty-eight.", "The two missing seeds reduce the expected grouped total.", "thirty becomes twenty eight", "two seeds missing"),
        _fresh_case("night list", "A child writes each star count with its time: ten at eight, thirteen at nine, and seven at ten.", "What idea covers the list?", "The visible star count changes at different times of night.", "The paired times and totals show repeated change.", "star counts change by time", "three timed totals"),
        _fresh_case("leaf tally restart", "Ira tallies leaves in a tray, a gust scatters three, she gathers them into a new row, and then restarts the count from one.", "Order Ira's attempt, interruption, response, and resolution.", "Ira tallies, the gust scatters leaves, she gathers them, and she restarts the count.", "The changed arrangement makes a fresh count more reliable than the first tally.", "tally scatter gather restart", "changed arrangement needs recount"),
        _fresh_case("library shelf count", "A monitor counts books on one shelf, two are borrowed during the count, so she checks the loan card and records the smaller final total.", "What sequence leads to the final library total?", "The monitor counts, two books leave, she checks the card, and records a new total.", "The borrowing interruption explains why the first count must be revised.", "count borrow check record", "books leave changes total"),
        _fresh_case("bus seat check", "Dev counts empty bus seats, passengers board at the next stop, he begins again from the front, and then tells the driver the correct number.", "Retell Dev's interrupted seat count and state the main idea.", "Dev counts, passengers board, he restarts from the front, and reports the new number.", "The card shows that recounting after a change gives a useful total.", "count board restart report", "recount after change"),
    ],
    "count_words_context": [
        _fresh_case("estimate jar", "Before counting, Jo says the jar may hold about forty beads. The word estimate describes this first idea.", "What does estimate mean?", "Estimate means make a sensible guess before an exact count.", "About forty and before counting give the meaning.", "estimate sensible guess", "before exact count"),
        _fresh_case("total shells", "Three red shells and five white shells make eight altogether. Eight is the total.", "Explain total.", "Total means the whole amount after the groups are combined.", "All colours are included in eight.", "total whole amount", "groups combined"),
        _fresh_case("pair socks", "Two matching socks make one pair. Six socks can make three pairs.", "What does pair mean here?", "A pair is a group of two matching items.", "The sock examples show two together.", "pair means matching two", "sock example"),
        _fresh_case("dozen eggs", "A tray holds twelve eggs. The label says one dozen.", "What number does dozen name?", "A dozen means twelve items.", "The direct tray count gives the word meaning.", "dozen means twelve", "tray count clue"),
        _fresh_case("few stars", "Only three stars can be seen through the cloud gap. The card says a few.", "What does few tell us?", "Few means a small number.", "Only three supports the quantity word.", "few small number", "only three"),
        _fresh_case("many lights", "More than fifty tiny lights cover the festival wall. The note says many.", "Which meaning fits many?", "Many means a large number.", "More than fifty is the context clue.", "many large number", "over fifty lights"),
        _fresh_case("equal groups", "Each bowl has six beads. The groups are equal.", "What does equal mean?", "Equal means having the same amount.", "Six in every bowl gives the meaning.", "equal same amount", "six each bowl"),
        _fresh_case("more buttons", "Box A has nine buttons and Box B has fourteen. Box B has more.", "What does more show?", "More means a greater number than another group.", "Fourteen is greater than nine.", "more greater number", "fourteen versus nine"),
        _fresh_case("fewer books", "Shelf One has four books and Shelf Two has ten. Shelf One has fewer.", "Explain fewer.", "Fewer means a smaller number of countable things.", "Four is less than ten.", "fewer smaller number", "four less ten"),
        _fresh_case("remain counters", "Twelve counters are on the mat. Five are removed, and seven remain.", "What does remain mean?", "Remain means are left after some are taken away.", "Seven stay after the removal.", "remain left after removal", "seven stay"),
        _fresh_case("group stars", "Ria circles every set of four stars on a card. Each circle is one group.", "What is a group here?", "A group is a set of items kept or counted together.", "Each circle gathers four stars.", "group counted together", "circle holds four"),
        _fresh_case("count action", "Vik touches each shell once while saying the number words in order. He counts the shells.", "What does count mean in this action?", "Count means match each item with a number to find how many.", "Touching once and ordered numbers explain the process.", "count items with numbers", "touch each once"),
        _fresh_case("exact tickets", "The box office scans every ticket and prints 126 as the checked number. The notice calls this the exact total.", "What does exact mean in the ticket notice?", "Exact means the fully checked number, not a guess.", "Every ticket was scanned before 126 was printed.", "exact checked number", "all tickets scanned"),
        _fresh_case("countless grains", "A handful of sand contains so many tiny grains that Tara does not try to name a precise number. She calls them countless.", "Use the sand clue to explain the quantity word countless.", "Countless means too many to count practically one by one.", "The huge number of tiny grains makes a precise count unreasonable.", "countless too many to count", "tiny grains huge number"),
        _fresh_case("button cluster", "Six blue buttons lie close together apart from the red buttons. The card calls the blue set one group.", "Explain group and use it in a fresh counting sentence.", "A group is a set kept together. New sentence: We counted each group of four shells separately.", "The six blue buttons are separated as one set.", "group means set together", "blue buttons separated set"),
    ],
    "here_there_location": [
        _fresh_case("near pencil", "The pencil is beside Mira's hand. Mira says, 'Put it here on my book.'", "Why does here fit?", "Here points to the place close to Mira.", "Her hand and book are at the speaker's place.", "here close to Mira", "near speaker place"),
        _fresh_case("far shelf", "The atlas is on a shelf across the room. Dev points and says, 'It is there.'", "What does there show?", "There points to the shelf away from Dev.", "Across the room gives the distance clue.", "there away from Dev", "far shelf clue"),
        _fresh_case("come here", "A teacher stands by the board and asks Nia to bring the chalk to the board.", "Which sentence uses here?", "The teacher says, 'Bring the chalk here.'", "Here names the teacher's current place.", "bring chalk here", "toward speaker"),
        _fresh_case("go there", "Ravi stands at the gate while the bus waits at the far corner.", "How can Ravi use there?", "Ravi says, 'The bus is waiting there at the corner.'", "The bus is away from his current place.", "bus waiting there", "far corner"),
        _fresh_case("books here", "Leena holds two books and points to the empty space beside her.", "Which location word belongs in her request?", "Leena says, 'Place the books here beside me.'", "Beside me signals the speaker's place.", "books here beside me", "close location"),
        _fresh_case("kite there", "The kite is caught in a tree on the other side of the field.", "Write a sentence with there.", "The kite is there in the tree across the field.", "Across the field marks distance from the speaker.", "kite there in tree", "other side field"),
        _fresh_case("wait here", "A guard stands at the desk and wants a visitor to stay beside it.", "What complete instruction fits?", "The guard says, 'Please wait here beside the desk.'", "Here matches the guard's nearby desk.", "wait here desk", "near guard place"),
        _fresh_case("shop there", "From her window, Uma points to a shop beyond the bridge.", "Which sentence uses there clearly?", "Uma says, 'The shop is there beyond the bridge.'", "The bridge separates her from the shop.", "shop there beyond bridge", "away from window"),
        _fresh_case("sit here", "A child pats the empty chair next to him.", "How can he invite a friend?", "He says, 'You can sit here next to me.'", "Next to me signals closeness.", "sit here next to me", "near speaker chair"),
        _fresh_case("stars there", "Mina points above a distant tower where three stars are visible.", "Use there with the shown place.", "Mina says, 'Three stars are shining there above the tower.'", "The distant tower fixes the far location.", "stars shining there", "above distant tower"),
        _fresh_case("home here", "After entering her own room, Pia says the familiar desk and bed make her glad to be back.", "Which location word fits?", "Pia says, 'I am happy to be here in my room.'", "Here refers to the room where she stands.", "happy here in room", "speaker current place"),
        _fresh_case("moon there", "A child looks through a window and points to the moon above the far hill.", "Build a clear there sentence.", "The moon is there above the far hill.", "The pointed hill is away from the child.", "moon there above hill", "far pointed place"),
        _fresh_case("clinic desk here", "A nurse stands at the clinic desk and shows a child the chair beside her.", "Which here sentence can the nurse use?", "The nurse says, 'Please sit here beside the clinic desk.'", "Here points to the chair close to the speaking nurse.", "sit here beside desk", "chair near speaker"),
        _fresh_case("field cone there", "A coach stands at the starting line and points to an orange cone at the far end of the field.", "Use there to describe the orange cone from the coach's position.", "The coach says, 'Run to the orange cone there at the far end.'", "The far end places the cone away from the speaker.", "cone there far end", "away from coach"),
        _fresh_case("balcony pot", "Rina stands inside the room while a blue flowerpot rests outside on the distant balcony ledge.", "Choose here or there and write Rina's clear location sentence.", "Rina says, 'The blue flowerpot is there on the balcony ledge.'", "There fits because the pot is away from Rina outside the room.", "flowerpot is there", "away on balcony"),
    ],
    "moon_dialogue_marks": [
        _fresh_case("count question", "Ria asks Mohan how many stars he counted. The words need capitals, quotation marks, and a question mark.", "Write Ria's line with its speech tag.", "Ria asked, 'How many stars did you count?'", "The question belongs to Ria and ends with a question mark.", "Ria asks star count", "question mark speech"),
        _fresh_case("number reply", "Mohan answers that he counted fourteen stars.", "Punctuate Mohan's reply.", "Mohan replied, 'I counted fourteen stars.'", "The speech tag names him and the statement ends with a full stop.", "Mohan counted fourteen", "reply full stop"),
        _fresh_case("moon place", "Tara asks, where is the moon now. Turn the words into dialogue.", "How should Tara's question appear?", "Tara asked, 'Where is the moon now?'", "Where begins the capitalised question inside quotation marks.", "Tara asks moon place", "where question punctuation"),
        _fresh_case("cloud answer", "Dev says the moon is behind the cloud.", "Write the spoken answer correctly.", "Dev said, 'The moon is behind the cloud.'", "The spoken statement is enclosed and ends with a full stop.", "Dev says behind cloud", "statement quotation marks"),
        _fresh_case("look command", "Nia tells her friend to look above the tree. The line is an excited command.", "Punctuate the spoken command.", "Nia called, 'Look above the tree!'", "The speech tag and exclamation mark show who calls and how.", "Nia calls look", "command exclamation mark"),
        _fresh_case("quiet request", "A child asks, please speak softly. The baby is asleep.", "Write the polite dialogue line.", "The child said, 'Please speak softly; the baby is asleep.'", "Quotation marks hold both linked ideas spoken by the child.", "child asks softly", "quoted polite request"),
        _fresh_case("telescope offer", "Mira offers her telescope by saying you can use mine.", "Add a clear speaker tag and marks.", "Mira said, 'You can use my telescope.'", "The tag assigns the helpful statement to Mira.", "Mira offers telescope", "tag names speaker"),
        _fresh_case("thanks reply", "Kavi thanks Mira for the telescope.", "How should Kavi's line be written?", "Kavi replied, 'Thank you for sharing your telescope.'", "The reply tag and quotation marks keep ownership clear.", "Kavi thanks Mira", "reply quotation marks"),
        _fresh_case("time question", "Renu wants to ask when the moon rose.", "Write her past-time question as dialogue.", "Renu asked, 'When did the moon rise?'", "The question word, helper, and question mark form a clear line.", "Renu asks when", "past question mark"),
        _fresh_case("time answer", "Sam answers that the moon rose at eight.", "Punctuate the answer with a tag.", "Sam answered, 'The moon rose at eight.'", "The statement belongs to Sam and ends inside the closing quote.", "Sam says eight", "answer statement marks"),
        _fresh_case("surprise line", "Lata sees a shooting star and says what a bright streak.", "Write the surprised line.", "Lata cried, 'What a bright streak!'", "The exclamation mark matches the strong feeling.", "Lata sees bright streak", "surprise exclamation"),
        _fresh_case("closing line", "The guide tells everyone the viewing time is over.", "Write the guide's statement.", "The guide said, 'Our viewing time is over.'", "The speech tag and full stop suit a calm statement.", "guide ends viewing", "calm quoted statement"),
        _fresh_case("chart total question", "Meera wants to ask Ali whether the chart total includes the hidden row.", "Write Meera's complete punctuated question as dialogue.", "Meera asked, 'Does the chart total include the hidden row?'", "The speaker tag, capital letter, quotation marks, and question mark make the line clear.", "Meera asks hidden row", "complete question marks"),
        _fresh_case("Ali chart reply", "Ali says he counted the hidden row after the cloud moved away.", "Punctuate Ali's answer with a reporting word.", "Ali replied, 'I counted the hidden row after the cloud moved away.'", "The reply tag assigns the past-tense statement to Ali.", "Ali counted hidden row", "reply tag statement"),
        _fresh_case("bright moon surprise", "Nora sees the full moon emerge and says how bright it looks tonight.", "Write Nora's surprised line with the correct marks.", "Nora cried, 'How bright the moon looks tonight!'", "The exclamation mark matches Nora's strong surprise.", "Nora sees bright moon", "surprise exclamation"),
    ],
    "moon_pronoun_agreement": [
        _fresh_case("Mira counts", "Mira ___ the stars and records them. Choose count or counts, then replace Mira with a pronoun.", "Write the agreeing sentence.", "She counts the stars and records them.", "Mira is one girl, so she and counts agree.", "she counts stars", "one girl agreement"),
        _fresh_case("boys watch", "Arun and Jai ___ the moon. Replace both names with a pronoun and choose watches or watch.", "Complete the sentence.", "They watch the moon from the steps.", "Two people become they and take watch.", "they watch moon", "two people plural"),
        _fresh_case("lamp glows", "The lamp ___ beside the map. Replace lamp with it and choose glow or glows.", "Which sentence fits?", "It glows beside the map.", "One object becomes it and takes glows.", "it glows beside map", "one object agreement"),
        _fresh_case("stars shine", "The stars ___ above the field. Replace stars with they and choose shines or shine.", "Write the correct sentence.", "They shine above the field.", "Plural stars become they and take shine.", "they shine above field", "plural takes shine"),
        _fresh_case("Nila asks", "Nila ___ a question about the count. Use she and choose ask or asks.", "Complete it.", "She asks a question about the count.", "One named girl becomes she and takes asks.", "she asks question", "single subject asks"),
        _fresh_case("children wait", "The children ___ near the telescope. Use they and choose waits or wait.", "Which form agrees?", "They wait near the telescope.", "Children is plural and takes wait.", "they wait telescope", "children plural"),
        _fresh_case("moon moves", "The moon ___ across the display. Use it and choose move or moves.", "Write the full sentence.", "It moves across the display.", "Moon is one thing, so it and moves agree.", "it moves display", "single thing moves"),
        _fresh_case("Ria and I", "Ria and I ___ our counts. Replace the subjects with we and choose compares or compare.", "Complete the sentence.", "We compare our counts after the second look.", "Ria and I become we and take compare.", "we compare counts", "we plural agreement"),
        _fresh_case("teacher explains", "Our teacher ___ the tally marks. Replace teacher with she and choose explain or explains.", "Which sentence is correct?", "She explains the tally marks.", "One teacher becomes she and takes explains.", "she explains tallies", "one teacher explains"),
        _fresh_case("clouds pass", "The clouds ___ over the moon. Use they and choose passes or pass.", "Write the agreeing sentence.", "They pass over the moon.", "Clouds is plural and takes pass.", "they pass moon", "plural clouds pass"),
        _fresh_case("boy points", "The boy ___ at a bright star. Use he and choose point or points.", "How should it read?", "He points at a bright star.", "One boy becomes he and takes points.", "he points star", "single boy points"),
        _fresh_case("cards show", "The cards ___ three night scenes. Use they and choose shows or show.", "Complete the idea.", "They show three night scenes.", "Plural cards become they and take show.", "they show scenes", "plural cards show"),
        _fresh_case("telescope stands", "The telescope ___ beside the rail. Replace telescope with it and choose stand or stands.", "Write the agreeing reference sentence.", "It stands beside the rail.", "One telescope becomes it and takes stands.", "it stands beside rail", "single telescope stands"),
        _fresh_case("girls record", "Nina and Salma ___ the second count. Replace both names with they and choose records or record.", "Complete the plural sentence.", "They record the second count in the chart.", "Two girls become they and use record.", "they record second count", "two girls plural"),
        _fresh_case("moon card belongs", "The moon card ___ in the blue folder. Use it and choose belong or belongs.", "Which full sentence has correct agreement?", "It belongs in the blue folder.", "One card becomes it and takes belongs.", "it belongs blue folder", "single card belongs"),
    ],
    "moon_kind_response": [
        _fresh_case("missed count", "'I lost my place after the cloud moved,' said Reva. Nikhil has a tally sheet.", "What kind reply could Nikhil give?", "Nikhil can offer his tally sheet and help Reva count again.", "The reply answers her exact counting problem.", "offers tally and recount", "helps lost place"),
        _fresh_case("shorter child", "'I cannot reach the telescope,' said a younger child. Mira stands beside a safe step stool.", "Write Mira's helpful response.", "Mira can say, 'I will ask an adult to place the safe stool for you.'", "The response helps without making an unsafe promise.", "ask adult for stool", "safe reach help"),
        _fresh_case("blurred lens", "Aman said, 'The lens looks cloudy, and I cannot see the moon.'", "How can a partner respond kindly?", "A partner can offer a clean lens cloth and wait while Aman wipes it.", "The offered item matches the cloudy-lens problem.", "offers lens cloth", "fixes cloudy view"),
        _fresh_case("wrong total", "'My tally says twelve, but I can see thirteen dots,' said Leela.", "What relevant reply fits?", "A friend can suggest checking each tally against one dot.", "The method directly addresses the different totals.", "check tally to dots", "fixes count mismatch"),
        _fresh_case("cold roof", "'My hands are cold on the roof,' said Jai during the night watch.", "Write a caring reply.", "A friend can offer gloves and suggest moving to the sheltered doorway.", "Both ideas answer the cold condition.", "offers gloves shelter", "answers cold need"),
        _fresh_case("missing pencil", "'I cannot record the next count because my pencil broke,' said Nia.", "How should Omar answer?", "Omar can lend a spare pencil so Nia can continue recording.", "The tool matches the stated barrier.", "lends spare pencil", "continues recording"),
        _fresh_case("scared of dark", "A child whispered, 'The far corner is too dark for me.'", "What kind response keeps the child safe?", "The guide can offer a torch and stay beside the child.", "Light and company answer the fear without blame.", "offers torch and company", "helps dark fear"),
        _fresh_case("confusing chart", "'I do not understand which row is Tuesday,' said Pavi.", "Write a helpful answer.", "A partner can point to the Tuesday label and explain its row.", "The reply uses the visible chart clue she needs.", "points Tuesday row", "explains label"),
        _fresh_case("late arrival", "'I missed the first star count because my bus was late,' said Kabir.", "How can the group respond?", "The group can share the first tally and invite Kabir to join the next count.", "The response replaces missing information and includes him.", "shares tally includes Kabir", "answers missed count"),
        _fresh_case("tired eyes", "'My eyes feel tired after looking for a long time,' said Zoya.", "Which friendly reply is suitable?", "A friend can suggest a short rest before Zoya looks again.", "Rest matches the stated discomfort.", "suggests short rest", "helps tired eyes"),
        _fresh_case("fallen chart", "'The wind blew my chart onto the ground,' said Rohan.", "What can Tara offer?", "Tara can help pick up the chart and hold one corner.", "Both actions answer the wind problem.", "helps chart hold corner", "wind blew it down"),
        _fresh_case("shared telescope", "'I have not had a turn yet,' said Mehul near the telescope line.", "Write a fair kind response.", "The next pupil can finish one look and then give Mehul a turn.", "The response respects the line and his stated need.", "gives Mehul next turn", "fair line response"),
        _fresh_case("erased tally", "'My sleeve rubbed out the last five tally marks,' said Aditi, looking upset. Rohan has the earlier count sheet.", "What kind message can Rohan give?", "Rohan can say, 'We can use my earlier sheet and rebuild the five marks together.'", "His offer acknowledges the lost work and supplies useful evidence.", "rebuild tallies together", "earlier sheet helps"),
        _fresh_case("found glasses", "'I can see the chart again now that my glasses are back,' said Imran with a relieved smile. Lopa found them beside the case.", "Write Imran's friendly message to Lopa.", "Imran can say, 'Thank you for finding my glasses beside the case.'", "The message names the exact help that caused his relief.", "thanks for finding glasses", "relief after return"),
        _fresh_case("too many dots", "'I feel confused when I count all the dots at once,' said Priti. The chart can be covered one row at a time.", "Which supportive reply is realistic?", "A partner can say, 'Let us uncover one row at a time and count each row together.'", "The smaller-row method directly answers Priti's confusion.", "count one row together", "smaller view reduces confusion"),
    ],
}

for _level_spec in SPEC["levels"]:
    _level_spec["fresh_cases"] = FRESH_CASES[_level_spec["level_id"]]


SPEC["assessment_pairs"] = [
    _assessment_pair("reading.event_sequence", _case("lamp count", "Ria counts ten lamps, two switch off, one turns on, and she counts nine.", "Which order matches?", "Count ten, lose two, gain one, then count nine.", "Count nine before any change.", "Turn on ten new lamps.", "The changes sit between the two counts.", "ten off on nine", "changes before recount"), _case("bead total", "Omi counts fifteen beads, removes three cracked ones, and labels twelve usable beads.", "What happens before twelve is written?", "Three cracked beads are removed.", "Twelve beads are added.", "The label is erased first.", "The usable total follows removal.", "remove three before twelve", "usable count after sort"), kind="choice"),
    _assessment_pair("reading.paragraph_main_idea", _fresh_case("changing sky count", "Clouds cover and uncover stars, so Mira writes three different totals during one hour.", "State the whole idea.", "Mira's visible star count changes as clouds move.", "The three totals and moving clouds support one idea.", "count changes with clouds", "three totals one hour"), _fresh_case("careful tally", "Dev marks one line for each bird, groups five lines, and checks the marks before writing the total.", "What is the paragraph mostly about?", "Dev uses a careful tally method to count birds.", "Every action supports accurate counting.", "careful bird tally", "marks checked before total"), kind="open"),
    _assessment_pair("reading.word_meaning_context", _case("estimate meaning", "Before opening the box, Ria guesses it holds about thirty blocks. This is an estimate.", "What does estimate mean?", "A sensible guess made before exact counting.", "A number copied after counting.", "A matching pair of blocks.", "About and before opening are clues.", "estimate sensible guess", "before exact count"), _case("remain meaning", "Nine birds leave, but four stay on the wire. Four remain.", "Which meaning fits remain?", "Remain means are left or stay behind.", "Remain means fly away first.", "Remain means become a dozen.", "The four staying give the meaning.", "remain stay behind", "four still there"), kind="choice"),
    _assessment_pair("vocab.chapter_word_usage", _case("total usage", "Six shells and seven shells are counted together.", "Which sentence uses total correctly?", "The total is thirteen shells.", "Total means only the first six.", "Total is a shell colour.", "Both groups combine to thirteen.", "total thirteen shells", "groups combined"), _case("fewer usage", "Tray A has five stars and Tray B has nine.", "Which sentence uses fewer?", "Tray A has fewer stars than Tray B.", "Tray A has fewer because five is greater.", "Fewer means both trays are equal.", "Five is the smaller count.", "five fewer than nine", "smaller count"), kind="choice"),
    _assessment_pair("grammar.adverbs", _case("here choice", "The speaker pats the chair beside her.", "Which sentence fits?", "Please sit here beside me.", "Please sit there across the field beside me.", "Here means far from the speaker.", "Beside me signals here.", "sit here beside me", "near speaker"), _case("there choice", "A boy points to a kite beyond the far wall.", "Which sentence fits?", "The kite is there beyond the wall.", "The kite is here in my hand.", "There means touching the speaker.", "Beyond the wall signals there.", "kite there beyond wall", "far from speaker"), kind="choice"),
    _assessment_pair("reading.sentence_comprehension", _case("location meaning", "Nila says, 'Bring the chart here to my desk.'", "Where should the chart go?", "It should go to Nila's desk.", "It should go to a distant gate.", "It should stay hidden.", "Here is fixed by the named desk.", "chart to Nila desk", "here names desk"), _case("pronoun meaning", "Ravi and Om count the dots. They write eleven.", "Who writes eleven?", "Ravi and Om write eleven.", "Only the dots write eleven.", "An unnamed girl writes it.", "They refers to both named boys.", "Ravi Om write eleven", "they means both"), kind="choice"),
    _assessment_pair("reading.dialogue_attribution", _case("speaker tally", "'I counted sixteen,' said Mira. Jo replied, 'I counted fourteen.'", "Who counted sixteen?", "Mira counted sixteen.", "Jo counted sixteen.", "The tally counted itself.", "Said Mira owns the first line.", "Mira counted sixteen", "speech tag Mira"), _case("speaker offer", "'Use my chart,' said Kavi to Leena.", "Who offers the chart?", "Kavi offers the chart.", "Leena offers it.", "The chart offers Kavi.", "The tag names Kavi.", "Kavi offers chart", "said Kavi"), kind="choice"),
    _assessment_pair("grammar.punctuation_capitalization", _fresh_case("question marks", "Words: rina asked / where is the moon now", "Write the dialogue with capitals and punctuation.", "Rina asked, 'Where is the moon now?'", "The speaker and question begin with capitals and the line ends correctly.", "Rina asks moon place", "capital question mark"), _fresh_case("reply marks", "Words: om replied / it is above the tower", "Punctuate the spoken reply.", "Om replied, 'It is above the tower.'", "The tag and quoted statement use capitals and a full stop.", "Om says above tower", "quoted full stop"), kind="open"),
    _assessment_pair("grammar.pronouns", _case("girls pronoun", "Mina and Tara check the chart.", "Which pronoun replaces both names?", "They check the chart.", "She check the chart.", "It checks the chart.", "Two people become they.", "they replaces girls", "two names plural"), _case("lamp pronoun", "The lamp glows near the map.", "Which pronoun replaces lamp?", "It glows near the map.", "They glows near the map.", "He glow near map.", "One object becomes it.", "it replaces lamp", "single object"), kind="choice"),
    _assessment_pair("grammar.subject_verb_agreement", _case("she counts", "Use she with count or counts.", "Which sentence agrees?", "She counts the stars.", "She count the stars.", "They counts the stars.", "She takes counts.", "she counts stars", "single subject"), _case("they shine", "Use they with shines or shine.", "Choose the agreeing sentence.", "They shine above the hill.", "They shines above the hill.", "It shine above hill.", "They takes shine.", "they shine hill", "plural subject"), kind="choice"),
    _assessment_pair("reading.inference_reason", _fresh_case("new count", "A cloud moves away, and Sia's second star count is larger than her first.", "Why is the second count larger?", "More stars became visible after the cloud moved.", "The clear patch reveals stars hidden during the first count.", "more stars visible", "cloud moved away"), _fresh_case("empty line", "The telescope line is empty at dawn after being crowded at midnight.", "Why is it probably empty?", "Viewing has likely ended because daylight is beginning.", "Dawn makes night objects harder to see.", "viewing ended at dawn", "daylight begins"), kind="open"),
    _assessment_pair("writing.friendly_message", _fresh_case("chart thanks", "Pia shares her tally chart after Sam loses his place.", "Write Sam's friendly reply.", "Thank you, Pia, for sharing your tally chart so I can check my count.", "The message names the helper, item, and useful reason.", "thank Pia for chart", "helps check count"), _fresh_case("torch thanks", "Nira lends Kavi a torch for the dark path to the viewing area.", "Write a relevant thank-you.", "Thank you, Nira, for lending me the torch for the dark path.", "The reply directly names the help and need.", "thank Nira for torch", "lights dark path"), kind="open", interaction_type="paragraph_text"),
    _assessment_pair("reading.inference_reason", _fresh_case("five groups", "Ravi circles four groups of five marks and then writes twenty.", "How did he get twenty?", "He counted four equal groups with five marks in each.", "The grouping shows repeated sets of five.", "four groups make twenty", "five in each"), _fresh_case("coat here", "A child says, 'Leave the coat here,' while touching the hook beside him.", "Where should the coat go?", "The coat should go on the nearby hook.", "Here and the touch point fix the place.", "coat on nearby hook", "speaker touches hook"), kind="open"),
    _assessment_pair("writing.friendly_message", _fresh_case("turn offer", "Mohan notices that Reva has not used the telescope and offers her the next turn.", "Write Reva's response.", "Thank you, Mohan, for making sure I get the next telescope turn.", "The reply names the fair offer.", "thank Mohan for turn", "fair telescope offer"), _fresh_case("count help", "Tara helps Jo match each shell with one tally mark after he counts twice.", "Write Jo's kind reply.", "Thank you, Tara, for helping me match each shell to one tally.", "The reply states the exact counting help.", "thank Tara for tally help", "matches shells marks"), kind="open", interaction_type="paragraph_text"),
]


_SEMANTIC_OPTION_REPLACEMENTS = {'Twelve is only a wild estimate despite complete checking.': 'Twelve is still an '
                                                              'estimate because the '
                                                              'crayons were not '
                                                              'grouped.'}
_SEMANTIC_ASSESSMENT_OVERRIDES = {}


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
