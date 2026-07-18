"""Deep authored manifest for Class 3 English Chapter 3.

The official chapter supplied structural and exercise-form guidance only.
Every runtime stimulus, question, rubric, option, and answer is Zidd-authored.
"""

from __future__ import annotations

from app.content.school_rebuild_manifests.english.class_3.eng_c3_ch01 import (
    _add_launch_depth_variants,
    _aq_pair,
    _ar_pair,
    _build_manifest,
    _crunch,
    _launch_depth_case,
    _make_level,
    _q,
    _r,
)


CHAPTER_ID = "eng_c3_ch03"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/cesa103.pdf"


SOURCE_ANCHORS = [
    {"anchor_id": f"{CHAPTER_ID}:read:25-28", "section_label": "Let us Read: Shapes, Disagreement, and Cooperation", "page_start": 25, "page_end": 28, "source_url": f"{SOURCE_URL}#page=25", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:think:29", "section_label": "Let us Think: Facts, Lesson, and Shared Strengths", "page_start": 29, "page_end": 29, "source_url": f"{SOURCE_URL}#page=29", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:speak:30", "section_label": "Let us Speak: Optional Character Reading", "page_start": 30, "page_end": 30, "source_url": f"{SOURCE_URL}#page=30", "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:learn:30-31", "section_label": "Let us Learn: Nouns, Articles, and Complete Sentences", "page_start": 30, "page_end": 31, "source_url": f"{SOURCE_URL}#page=30", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:write:31-32", "section_label": "Let us Write: Clear Friend Profile", "page_start": 31, "page_end": 32, "source_url": f"{SOURCE_URL}#page=31", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:do:32", "section_label": "Let us Do: Optional Shape Drawing", "page_start": 32, "page_end": 32, "source_url": f"{SOURCE_URL}#page=32", "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:explore:33", "section_label": "Let us Explore: Optional Shape Design", "page_start": 33, "page_end": 33, "source_url": f"{SOURCE_URL}#page=33", "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:fun-words:34-35", "section_label": "Fun with Words: Animal Actions and Verse Patterns", "page_start": 34, "page_end": 35, "source_url": f"{SOURCE_URL}#page=34", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
]


CRUNCH_BAR = {
    "mural_sequence_and_idea": _crunch(
        [
            (
                "The badge team disagreed about a moon or tree. They compared both sketches, put the moon above the tree, and produced one night-garden badge.",
                "The disagreement came first, comparison followed, both ideas were joined, and a night-garden badge was finished. Combining the sketches improved the result.",
                ["disagreement came first", "comparison followed", "ideas were joined"],
                ["combining sketches improved the result", "one badge used both ideas"],
            ),
            (
                "One pupil drew a wide path while another drew tiny shops. The pair measured the page, narrowed the path, and placed shops along both sides.",
                "The clashing sizes came first, measuring guided the change, and the new layout kept the path and shops. Measurement helped both ideas fit.",
                ["clashing sizes came first", "measuring guided the change", "kept path and shops"],
                ["measurement helped both ideas fit", "shared layout solved the problem"],
            ),
            (
                "A poster had separate sun and rain panels. The group added a curved bridge between them and made one weather-cycle picture.",
                "Separate panels came first, the curved bridge was added next, and one cycle picture followed. Linking the panels made the weather idea clearer.",
                ["separate panels first", "bridge added next", "cycle picture followed"],
                ["linking panels made the idea clearer", "one weather cycle joined both"],
            ),
            (
                "Two teams brought different border stamps. They tested a repeating leaf-star order, corrected one gap, and stamped the final frame together.",
                "Different stamps came first, the pattern test came next, the gap was fixed, and the frame was completed. Testing let both teams share one border.",
                ["different stamps first", "pattern test next", "gap fixed before frame"],
                ["both teams shared one border", "testing joined the designs"],
            ),
            (
                "The map group had a river but no crossing and a road that ended early. It added a bridge, extended the road, and checked that both routes met.",
                "The broken routes came first, the bridge and road extension followed, and a route check came last. Shared checking made the map usable.",
                ["broken routes came first", "bridge and extension followed", "route check last"],
                ["shared checking made the map usable", "routes met after teamwork"],
            ),
        ],
        prompt="Put the teamwork events in order and tell how cooperation improved the result.",
        interaction_type="summary",
        ordered=True,
    ),
    "conflict_inference_and_reason": _crunch(
        [
            (
                "Asha wants large title letters, but Dev says they cover the picture. A blank strip remains above the picture.",
                "Place medium title letters in the blank strip because this keeps the picture clear and still gives the title its own space.",
                ["medium title in the blank strip", "use the free strip for the title"],
                ["keeps the picture clear", "title still has space"],
            ),
            (
                "Two pupils want the only gold pen. One needs it for four stars; the other needs it for one heading, and a timer is ready.",
                "Give the heading writer a short timed turn, then pass the pen for the four stars because both jobs can finish in planned turns.",
                ["short timed turn then pass the pen", "plan two pen turns"],
                ["both jobs can finish", "timer makes the turns fair"],
            ),
            (
                "Mina wants to erase a crooked tree. Jo says the tree is her idea and offers to redraw its trunk on tracing paper first.",
                "Test Jo's new trunk on tracing paper before erasing because it respects her idea and checks whether the change works.",
                ["test the trunk on tracing paper", "try the change before erasing"],
                ["respects her idea", "checks whether the change works"],
            ),
            (
                "A group has room for six labels but has written eight. Two labels repeat facts already shown by symbols.",
                "Remove the two repeated labels because the six new facts fit the space and the symbols already show the repeated information.",
                ["remove the two repeated labels", "keep six new labels"],
                ["symbols already show the facts", "six labels fit the space"],
            ),
            (
                "Ravi wants a blue border and Pema wants green. Their trial card shows alternating colours without hiding the words.",
                "Use the alternating blue-green border because the test keeps the words readable and includes both colour choices.",
                ["use the alternating border", "keep blue and green turns"],
                ["words stay readable", "includes both choices"],
            ),
        ],
        prompt="Choose a fair next step and use the shared goal or concern as your reason.",
    ),
    "shape_attribute_order": _crunch(
        [
            (
                "Mosaic piece counts: circle panel 21, leaf panel 13, wave panel 17. Order them from fewest to most pieces.",
                "The leaf panel comes first with 13 pieces, the wave panel follows with 17, and the circle panel comes last with 21.",
                ["leaf panel then wave panel then circle panel", "fewest to most pieces"],
                ["13 then 17 then 21", "uses all three piece counts"],
            ),
            (
                "Tower heights: square tower 9 blocks, triangle tower 14 blocks, circle tower 6 blocks. Order tallest to shortest.",
                "The triangle tower is tallest with 14 blocks, the square tower follows with 9, and the circle tower is shortest with 6.",
                ["triangle square circle", "tallest to shortest"],
                ["14 then 9 then 6", "compares block heights"],
            ),
            (
                "Shape widths: oval 12 cm, rectangle 20 cm, diamond 16 cm. Order left to right from narrowest to widest.",
                "Place the oval left at 12 cm, the diamond in the middle at 16 cm, and the rectangle right at 20 cm because their widths increase.",
                ["oval diamond rectangle", "narrowest to widest"],
                ["12 then 16 then 20", "widths increase left to right"],
            ),
            (
                "Bag weights: star bag 4 kg, moon bag 7 kg, sun bag 5 kg. Order lightest to heaviest.",
                "The star bag comes first at 4 kg, the sun bag next at 5 kg, and the moon bag last at 7 kg.",
                ["star sun moon", "lightest to heaviest"],
                ["4 then 5 then 7", "compares all weights"],
            ),
            (
                "Flagpole distances from the gate: yellow 3 m, white 8 m, red 6 m. Order nearest to farthest.",
                "Yellow is nearest at 3 m, red is next at 6 m, and white is farthest at 8 m because the distances rise from 3 to 8.",
                ["yellow red white", "nearest to farthest"],
                ["3 then 6 then 8", "distances rise"],
            ),
        ],
        prompt="Write the full order and use the numbers to explain it.",
        interaction_type="short_text",
        ordered=True,
    ),
    "shape_words_and_sentences": _crunch(
        [
            (
                "Card: a narrow rectangle / frames / the school name / above the door.",
                "A narrow rectangle frames the school name above the door. Rectangle and name are nouns, frames is the verb, and narrow describes the rectangle.",
                ["rectangle and name are nouns", "frames is the verb"],
                ["narrow rectangle frames the name", "above the door"],
            ),
            (
                "Card: three round buttons / fill / the empty corner / neatly.",
                "Three round buttons neatly fill the empty corner. Buttons and corner are nouns, fill is the verb, and round and empty are describing words.",
                ["buttons and corner are nouns", "fill is the verb"],
                ["round buttons fill the corner", "neatly fill the empty corner"],
            ),
            (
                "Card: the pointed arrow / shows / the library route / on the map.",
                "The pointed arrow shows the library route on the map. Arrow, route, and map are nouns, shows is the verb, and pointed describes the arrow.",
                ["Arrow, route, and map are nouns", "shows is the verb"],
                ["The pointed arrow shows the library route", "on the map"],
            ),
            (
                "Card: a curved line / joins / two square panels / at the centre.",
                "A curved line joins two square panels at the centre. Line and panels are nouns, joins is the verb, and curved and square describe shapes.",
                ["line and panels are nouns", "joins is the verb"],
                ["curved line joins panels", "at the centre"],
            ),
            (
                "Card: the tall triangle / covers / a small circle / near the edge.",
                "The tall triangle covers a small circle near the edge. Triangle and circle are nouns, covers is the verb, and tall and small are describing words.",
                ["triangle and circle are nouns", "covers is the verb"],
                ["tall triangle covers a circle", "near the edge"],
            ),
        ],
        prompt="Build the sentence, then name the nouns, verb, and shape words.",
    ),
    "clear_pronouns_and_traits": _crunch(
        [
            (
                "Lata held the ruler steady while Simran drew the line. She checked the measurement before Simran moved the ruler. Trait: careful.",
                "She means Lata because Lata was holding and checking the ruler. Lata was careful because she checked the measurement before it moved.",
                ["She means Lata", "Lata checked the ruler"],
                ["Lata was careful", "checked before it moved"],
            ),
            (
                "Arun offered a new paper after Bilal tore his sketch. He also helped copy the labels. Trait: helpful.",
                "He means Arun because Arun offered the paper and copied labels. Arun was helpful because both actions supported Bilal's work.",
                ["He means Arun", "Arun offered paper"],
                ["Arun was helpful", "supported Bilal's work"],
            ),
            (
                "The border strips lay beside the glue pots. They were moved to a dry shelf before painting began. Trait: organised.",
                "They means the border strips because the strips were moved. The group was organised because it protected the strips before painting.",
                ["They means the border strips", "strips were moved"],
                ["group was organised", "protected strips before painting"],
            ),
            (
                "Nora listened while Keshav explained his symbol, then she asked one clear question instead of erasing it. Trait: respectful.",
                "She means Nora because Nora listened and asked the question. Nora was respectful because she discussed the symbol before changing it.",
                ["She means Nora", "Nora asked the question"],
                ["Nora was respectful", "discussed before changing"],
            ),
            (
                "Two younger pupils carried the paper rolls. They stopped when the doorway became crowded and waited. Trait: sensible.",
                "They means the two younger pupils because both carried the rolls. The pupils were sensible because they waited at the crowded doorway.",
                ["They means the two pupils", "both carried the rolls"],
                ["pupils were sensible", "waited at the crowded doorway"],
            ),
        ],
        prompt="Say what each pronoun means and use the trait with the action that proves it.",
    ),
    "animal_actions_and_agreement": _crunch(
        [
            (
                "One rabbit hops past the pot; two rabbits hop past the gate. The lines repeat past the.",
                "Rabbit takes hops, while rabbits takes hop. Repeating past the gives both movements the same beat and links their routes.",
                ["rabbit hops and rabbits hop", "singular hops plural hop"],
                ["repeating past the gives a beat", "links the routes"],
            ),
            (
                "The parrot calls from the tree; the parrots call from the rail. The phrase calls from is repeated.",
                "Parrot uses calls, and parrots use call. The repeated sentence shape makes the two sounds feel like an answering pattern.",
                ["parrot calls and parrots call", "verb agrees with each subject"],
                ["repeated shape feels like an answer", "two sounds form a pattern"],
            ),
            (
                "A squirrel races over the wall; three squirrels race under the bench. Over and under mark a changing path.",
                "Squirrel takes races, while squirrels takes race. The changing place words make the movement quick and playful.",
                ["squirrel races and squirrels race", "singular and plural agree"],
                ["place words show changing movement", "quick playful path"],
            ),
            (
                "The duck splashes once; the ducks splash twice. The repeated splash sound grows from one beat to two.",
                "Duck uses splashes, and ducks use splash. Repeating the splash action makes the second line feel busier than the first.",
                ["duck splashes and ducks splash", "correct agreement"],
                ["repeated splash feels busier", "one beat grows to two"],
            ),
            (
                "One calf turns toward the bell; four calves turn toward the barn. Toward begins both movement parts.",
                "Calf takes turns, while calves take turn. Repeating toward connects the movements and points both lines to a goal.",
                ["calf turns and calves turn", "verbs match number"],
                ["repeating toward connects movement", "both lines point to a goal"],
            ),
        ],
        prompt="Fix the verb for one or more animals, then explain the repeated action pattern.",
        interaction_type="short_text",
    ),
}


LEVELS = [
    _make_level(
        level_id="mural_sequence_and_idea",
        title="Follow the cooperative mural plan",
        focus="sequence a problem-solving narrative and identify its main idea",
        outcome="Order disagreement, experiment, joint action, and result, then state how combined contributions solved the mural problem.",
        skill_ids=["reading.event_sequence", "reading.paragraph_main_idea"],
        choice_skill_ids=["reading.event_sequence"],
        episode_kind="comprehension_studio",
        source_anchor_ids=[f"{CHAPTER_ID}:read:25-28", f"{CHAPTER_ID}:think:29"],
        principle="Track what changes the plan, not merely which detail appears first on the page; the main idea connects the shared problem, cooperation, and result.",
        connect={"teaching_block": "A teamwork story often moves from separate claims to a test, a revised plan, and a result that no one contribution could produce alone.", "passage": "Four pupils argued about one mural design. They tested separate sketches, combined the strongest parts, and completed a clear neighbourhood map together.", "prompt": "Notice the disagreement, test, combination, and successful result before naming the story's message."},
        choice_prompt="Which event comes first, second, or last as named in the card?",
        response_prompt="order the turning points and state the central idea about cooperation.",
        rubric_descriptions=["Orders the disagreement, response, combined action, and outcome correctly.", "States a central idea explaining how cooperation improved the result."],
        examples=[
            _q("Nila proposed circles, Kabir proposed rectangles, and then both tested a design using each shape.", "They tested a design using both shapes.", ["Nila proposed circles.", "Kabir proposed rectangles.", "They erased every design before talking."], prompt="Which action happened last?"),
            _q("First the sign pieces looked confusing. Next, the team grouped matching edges. Finally, they assembled one clear arrow.", "The team grouped matching edges.", ["The pieces looked confusing.", "They assembled the arrow last.", "They painted the arrow before grouping."], prompt="Which action happened second?"),
            _r("Three builders each made a weak paper tower. They compared the bases, joined a wide square base to triangular braces, and produced one stable tower.", "The builders made separate weak towers first, compared them next, and combined a square base with braces last. The main idea is that sharing useful features created a stronger design.", [["weak towers first", "compared next", "combined last"], ["sharing useful features", "stronger design"]], ordered=True),
            _r("A puzzle group disagreed about the border. They laid out two samples, measured each gap, and chose a repeating circle-square pattern that fit exactly.", "The group disagreed, tested two borders, measured the gaps, and then chose the fitting pattern. The passage shows evidence helping a group turn disagreement into a shared decision.", [["disagreed", "tested", "measured", "chose"], ["evidence", "shared decision"]], ordered=True),
            _r("A class map had roads but no landmarks. One pair added house symbols, another added labels, and a third checked the key before the class displayed it.", "Roads came first, symbols and labels were added next, and the key was checked before display. The main idea is that different tasks combined to make the map useful.", [["roads first", "symbols and labels next", "key checked"], ["different tasks combined", "map useful"]], ordered=True),
            _r("Two children wanted the same tile space. They traced both ideas on scrap paper, noticed the shapes could overlap, and made a flower from the combined outlines.", "The children wanted one space, tested both ideas, discovered overlap, and created a shared flower. The central idea is that experimentation revealed a way to include both contributions.", [["wanted one space", "tested", "discovered overlap", "created"], ["include both contributions", "experimentation revealed"]], ordered=True),
            _r("A model bridge bent under blocks. The team added triangular side supports, tested again, and recorded that the revised bridge held twice as many blocks.", "The bridge bent first, supports were added next, and a stronger result appeared in the second test. The passage shows testing and revision improving a shared model.", [["bent first", "supports next", "second test"], ["testing and revision", "improving model"]], ordered=True),
            _r("The notice board looked crowded. Pupils sorted cards by topic, assigned one shape to each topic, and left clear spaces between groups.", "The board was crowded, cards were sorted, shape labels were assigned, and spacing completed the organisation. The main idea is that a shared system made information easier to scan.", [["crowded", "sorted", "assigned", "spacing"], ["shared system", "easier to scan"]], ordered=True),
            _r("A pattern stopped halfway because one colour ran out. The group counted the remaining pieces, changed to an alternating two-colour plan, and completed the border.", "The colour shortage stopped the pattern, counting guided a new plan, and the revised border was completed. The central idea is that flexible teamwork solved a material problem.", [["shortage", "counted", "new plan", "completed"], ["flexible teamwork", "material problem"]], ordered=True),
            _q("The group sketched four ideas, selected one feature from each, and made a final badge.", "They selected one feature from each idea.", ["They made the badge first.", "They threw away every sketch.", "They selected features after finishing."], prompt="What happened immediately before the badge was made?"),
            _r("A route poster lacked a clear starting point. Jatin suggested a star, Mahi suggested a bold outline, and they combined both so visitors found the start quickly.", "The missing start caused confusion, two features were proposed, and both were combined before visitors used the poster. The main idea is that two ideas together made the route clearer.", [["confusion", "features proposed", "combined", "visitors used"], ["two ideas together", "route clearer"]], ordered=True),
            _q("First, the team measured the wall. Then it scaled the sketch. Last, it marked the mural grid.", "The team scaled the sketch.", ["It measured after marking.", "It marked the grid first.", "It painted without a sketch."], prompt="Which action happened second?"),
            _r("A mobile hung unevenly because all shapes were on one side. The makers moved two pieces, checked the balance, and tied the centre string again.", "The mobile hung unevenly, pieces were moved, balance was checked, and the centre was retied. The passage shows observation and joint adjustment restoring balance.", [["uneven", "moved", "checked", "retied"], ["joint adjustment", "restoring balance"]], ordered=True),
            _r("Four clue cards seemed unrelated. Learners arranged them by matching corners, discovered a larger park plan, and added one title for the finished display.", "The cards seemed separate, matching corners revealed their order, and a title completed the display. The main idea is that careful collaboration revealed a whole plan from separate parts.", [["separate", "matching corners", "revealed order", "title"], ["collaboration", "whole from parts"]], ordered=True),
        ],
        crunch_bar=CRUNCH_BAR["mural_sequence_and_idea"],
        misconception="The learner treats every contribution as a separate ending, or states that one person was best instead of explaining how comparison and combination changed the shared result.",
        remediation="Place the events in problem-test-combine-result order, then complete the main-idea frame 'Together, the group improved... by...'.",
    ),
    _make_level(
        level_id="conflict_inference_and_reason",
        title="Infer a fair way through disagreement",
        focus="infer motives in a disagreement and justify a fair resolution",
        outcome="Use words and actions to infer why a character resists a plan, then propose a fair response supported by the group's shared goal.",
        skill_ids=["reading.inference_reason", "writing.reason_answer"],
        choice_skill_ids=["reading.inference_reason"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:read:25-28", f"{CHAPTER_ID}:think:29"],
        principle="An idea about a disagreement must fit the speaker's clues; a fair resolution protects the shared goal and gives each relevant idea a test or turn.",
        connect={"teaching_block": "Saying 'no' can signal worry about time, fairness, fit, or safety. Readers should identify the specific concern before recommending a response.", "passage": "Esha rejected a large circle for the narrow banner and pointed to the measured width. She suggested testing a smaller circle instead.", "prompt": "Use the width measurement and alternative suggestion to infer Esha's concern rather than calling her unhelpful."},
        choice_prompt="Which motive is supported by the speaker's words and actions?",
        response_prompt="propose a fair resolution and justify it with the shared goal and visible concern.",
        rubric_descriptions=["Proposes a fair action that addresses the actual disagreement.", "Uses a stated concern, measurement, need, or shared goal as the reason."],
        examples=[
            _q("Ravi asks to test both borders before choosing because neither has been measured.", "Ravi wants evidence before the group decides.", ["Ravi wants no border at all.", "Ravi has already measured both borders.", "Ravi wants to hide the materials."]),
            _q("Sona moves her tile aside after hearing that it covers the route label and asks where else it could fit.", "Sona wants her tile included without hiding important information.", ["Sona wants the route label removed.", "Sona refuses every new position.", "Sona believes the tile is invisible."]),
            _r("Two pupils want to place their symbols at the map centre. The centre must show the school gate, but both symbols can fit beside it.", "Keep the school gate at the centre and place one symbol on each side because the shared map needs a clear gate while both contributions can still appear.", [["gate at centre", "symbols on each side"], ["map needs clear gate", "both can appear"]]),
            _r("One group wants a quick freehand border; another worries the repeated spaces will become uneven. A ruler and five extra minutes are available.", "Use the ruler for a short measured test because it addresses the spacing concern and still fits within the available five minutes.", [["measured test with ruler", "use five minutes"], ["addresses spacing", "time available"]]),
            _r("Mira speaks twice while Dev has not presented his sketch. The group promised equal turns before beginning.", "Pause and invite Dev to present next because the group agreed to equal turns and Mira has already spoken twice.", [["invite Dev next", "pause Mira"], ["equal-turn agreement", "Mira spoke twice"]]),
            _r("Two badge colours both meet the theme. The group cannot agree by discussion, and a visibility test can be done against the uniform cloth.", "Test both colours on the uniform cloth because visibility evidence can decide fairly when both choices fit the theme.", [["test both colours", "against uniform cloth"], ["visibility evidence", "both fit theme"]]),
            _r("A square label fits the box but covers a drawing. A narrow rectangle keeps the words readable and leaves the drawing clear.", "Choose the narrow rectangle because it preserves both the readable label and the visible drawing, which are the group's two goals.", [["choose narrow rectangle", "preserve both"], ["words readable", "drawing visible"]]),
            _r("Leena rejects a glue plan after noticing that the paper is thin and may wrinkle. Tape dots are available.", "Try tape dots on one sample because Leena's wrinkle concern comes from the thin paper and a sample protects the final work.", [["test tape dots", "one sample"], ["thin paper may wrinkle", "protect final work"]]),
            _r("A team member wants every shape the same size, but the title must be visible from the door while small legend symbols only need close reading.", "Use a large title shape and smaller legend shapes because the two parts have different viewing purposes.", [["large title", "smaller legend shapes"], ["visible from door", "close reading"]]),
            _q("Nikhil asks to rotate the triangle after its point blocks a word, rather than remove it.", "He wants to keep the triangle while making the word readable.", ["He wants to cover the whole word.", "He believes rotation changes the word.", "He wants no shapes on the page."]),
            _r("Two pupils each claim their pattern is easier. Ten classmates can follow one sample of each pattern and report confusion.", "Run both samples with the ten classmates because user evidence can show which pattern is easier to follow.", [["run both samples", "ask ten classmates"], ["user evidence", "easier to follow"]]),
            _q("Asha asks for a pause after three rushed mistakes appear in the grid.", "Asha likely wants time to check accuracy.", ["Asha wants more mistakes.", "Asha has finished a perfect grid.", "Asha wants to erase the wall."]),
            _r("One learner's design uses all available stars, leaving none for the legend that explains the map symbols.", "Reserve enough stars for the legend and reduce the decoration because the map needs its key to remain understandable.", [["reserve stars for legend", "reduce decoration"], ["map needs key", "remain understandable"]]),
            _r("A partner erases a shape without asking because it extends beyond the border. The shape can be resized instead.", "Restore the idea and ask the partner to resize it because the border concern is valid but erasing another person's work without discussion is unfair.", [["restore and resize", "ask the partner"], ["border concern valid", "erasing without discussion unfair"]]),
        ],
        crunch_bar=CRUNCH_BAR["conflict_inference_and_reason"],
        misconception="The learner labels the disagreeing person as selfish without using the stated concern, or chooses a majority vote when a quick evidence test could protect both fairness and quality.",
        remediation="Quote or paraphrase the exact concern, name the shared goal, and choose among turn-taking, combining, measuring, or testing based on which action addresses both.",
    ),
    _make_level(
        level_id="shape_attribute_order",
        title="Order shapes by one stated feature",
        focus="order objects by measurable features and explain the rule concisely",
        outcome="Use supplied side, corner, or length facts to create a complete order and justify neighbouring positions in a short answer.",
        skill_ids=["vocab.attribute_ordering", "writing.short_answer"],
        choice_skill_ids=["vocab.attribute_ordering"],
        episode_kind="retrieval_challenge",
        source_anchor_ids=[f"{CHAPTER_ID}:think:29"],
        principle="A feature order must use one named measure consistently; a short explanation should cite values for at least two neighbouring positions.",
        connect={"teaching_block": "Shape names alone do not create an order. A reference card must give the chosen feature, such as number of sides or measured length.", "passage": "Side-count card: triangle 3, square 4, pentagon 5. From fewest to most sides, the order follows the numbers 3, 4, 5.", "prompt": "Identify the single ordering rule and compare each neighbouring value."},
        choice_prompt="Which order follows the stated feature and direction?",
        response_prompt="write the full order and justify it with the supplied measurements.",
        rubric_descriptions=["Orders every named object in the required direction using one feature.", "Uses the relevant values or comparisons in a concise explanation."],
        examples=[
            _q("Corner card: circle 0, triangle 3, rectangle 4. Order from fewest to most corners.", "circle, triangle, rectangle", ["rectangle, triangle, circle", "triangle, circle, rectangle", "circle, rectangle, triangle"]),
            _q("Ribbon lengths: red 12 cm, blue 18 cm, green 15 cm. Order shortest to longest.", "red, green, blue", ["blue, green, red", "green, red, blue", "red, blue, green"]),
            _r("Side counts: hexagon 6, triangle 3, square 4, pentagon 5. Order from fewest to most sides.", "The order is triangle, square, pentagon, hexagon because their side counts increase from 3 to 4 to 5 to 6.", [["triangle, square, pentagon, hexagon", "complete order"], ["3 to 4 to 5 to 6", "side counts increase"]]),
            _r("Tile widths: star 9 cm, circle 6 cm, rectangle 12 cm, triangle 8 cm. Order narrowest to widest.", "The order is circle, triangle, star, rectangle because the widths are 6, 8, 9, and 12 centimetres.", [["circle, triangle, star, rectangle", "complete order"], ["6, 8, 9, 12", "widths"]]),
            _r("Perimeter card: shape A 16 cm, B 12 cm, C 20 cm. Order from greatest to least perimeter.", "The order is C, A, B because 20 centimetres is greatest, 16 is next, and 12 is least.", [["C, A, B", "complete order"], ["20", "16", "12"]]),
            _r("Corner counts: oval 0, arrow 7, rectangle 4, triangle 3. Order from most to fewest corners.", "The order is arrow, rectangle, triangle, oval because their corner counts decrease from 7 to 4 to 3 to 0.", [["arrow, rectangle, triangle, oval", "complete order"], ["7 to 4 to 3 to 0", "decrease"]]),
            _r("Paper areas: yellow 24 squares, red 18 squares, blue 30 squares, green 20 squares. Order smallest to largest area.", "The order is red, green, yellow, blue because the areas rise from 18 to 20 to 24 to 30 squares.", [["red, green, yellow, blue", "complete order"], ["18, 20, 24, 30", "areas rise"]]),
            _r("Pattern intensity card: pale 1, soft 2, bright 4, vivid 5. Order weakest to strongest colour intensity.", "The order is pale, soft, bright, vivid because the intensity values increase from 1 through 5.", [["pale, soft, bright, vivid", "complete order"], ["values increase", "1", "2", "4", "5"]]),
            _r("Stick lengths: P 7 cm, Q 11 cm, R 5 cm, S 9 cm. Order longest to shortest.", "The order is Q, S, P, R because 11 is longer than 9, which is longer than 7 and 5.", [["Q, S, P, R", "complete order"], ["11", "9", "7", "5"]]),
            _q("Side counts: triangle 3, pentagon 5, octagon 8. Order most to fewest sides.", "octagon, pentagon, triangle", ["triangle, pentagon, octagon", "pentagon, triangle, octagon", "octagon, triangle, pentagon"]),
            _r("Frame heights: A 14 cm, B 10 cm, C 17 cm, D 12 cm. Order shortest to tallest.", "The order is B, D, A, C because the heights increase from 10 to 12 to 14 to 17 centimetres.", [["B, D, A, C", "complete order"], ["10, 12, 14, 17", "heights increase"]]),
            _q("Measured diagonals: tile X 5 cm, Y 9 cm, Z 7 cm. Order shortest to longest.", "X, Z, Y", ["Y, Z, X", "Z, X, Y", "X, Y, Z"]),
            _r("Dot counts: circle card 8, square card 12, star card 10, triangle card 6. Order most to fewest dots.", "The order is square, star, circle, triangle because the counts fall from 12 to 10 to 8 to 6.", [["square, star, circle, triangle", "complete order"], ["12, 10, 8, 6", "counts fall"]]),
            _r("Border lengths: wave 22 cm, zigzag 19 cm, straight 25 cm, curve 21 cm. Order shortest to longest.", "The order is zigzag, curve, wave, straight because their lengths are 19, 21, 22, and 25 centimetres.", [["zigzag, curve, wave, straight", "complete order"], ["19, 21, 22, 25", "lengths"]]),
        ],
        crunch_bar=CRUNCH_BAR["shape_attribute_order"],
        misconception="The learner switches from sides to size midway, reverses the requested direction, or gives an order without citing the numbers that justify it.",
        remediation="Name the feature and direction, compare each value with its neighbours, then write the complete order and explain one neighbouring pair.",
    ),
    _make_level(
        level_id="shape_words_and_sentences",
        title="Use shape words in complete sentences",
        focus="classify nouns, verbs, and adjectives and construct complete object descriptions",
        outcome="Identify each word's job and write a complete sentence that names an object, gives its action or state, and adds an accurate shape description.",
        skill_ids=["grammar.noun_verb_adjective", "writing.complete_sentence"],
        choice_skill_ids=["grammar.noun_verb_adjective"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:learn:30-31", f"{CHAPTER_ID}:write:31-32"],
        principle="A noun names the object, a verb gives its action or state, and an adjective describes it; all three can support a complete visual description without an image.",
        connect={"teaching_block": "A text card can supply every visual fact needed for a shape sentence. The sentence must name the object and say what it does or is.", "passage": "The narrow rectangular sign hangs above the gate. Sign is a noun, hangs is a verb, and narrow and rectangular are adjectives.", "prompt": "Classify the four highlighted jobs before using the same pattern on a fresh card."},
        choice_prompt="Which word performs the named grammar job?",
        response_prompt="classify the target words and write one complete sentence from all supplied facts.",
        rubric_descriptions=["Correctly identifies or uses the noun, verb, and shape adjective.", "Writes a complete sentence containing the supplied object, action or state, and detail."],
        examples=[
            _q("The round clock hangs above the shelf. Which word is the shape adjective?", "round", ["clock", "hangs", "shelf"]),
            _q("A triangular flag waves beside the door. Which word is the verb?", "waves", ["triangular", "flag", "door"]),
            _r("Facts: object - window; shape - square; action - reflects morning light.", "The square window reflects the morning light. Window is the noun, reflects is the verb, and square is the adjective.", [["window noun", "reflects verb", "square adjective"], ["The square window reflects", "morning light"]]),
            _r("Facts: object - table; shape - oval; state - stands in the centre of the room.", "The oval table stands in the centre of the room. Table is the noun, stands is the verb, and oval is the adjective.", [["table noun", "stands verb", "oval adjective"], ["oval table stands", "centre of the room"]]),
            _r("Fragment: The blue triangular. Add noun 'kite' and action 'rises above the field'.", "The blue triangular kite rises above the field. Kite is the noun, rises is the verb, and blue and triangular are adjectives.", [["kite noun", "rises verb", "triangular adjective"], ["kite rises", "above the field"]]),
            _r("Facts: object - tiles; description - small hexagonal; action - cover the path.", "Small hexagonal tiles cover the path. Tiles is the noun, cover is the verb, and small and hexagonal are adjectives.", [["tiles noun", "cover verb", "hexagonal adjective"], ["tiles cover the path", "small hexagonal"]]),
            _r("Facts: object - mirror; shape - circular; action - catches the afternoon light.", "The circular mirror catches the afternoon light. Mirror is the noun, catches is the verb, and circular is the adjective.", [["mirror noun", "catches verb", "circular adjective"], ["circular mirror catches", "afternoon light"]]),
            _r("Fragment: A long rectangular board. Add action and place: displays the timetable near the office.", "A long rectangular board displays the timetable near the office. Board is the noun, displays is the verb, and long and rectangular are adjectives.", [["board noun", "displays verb", "rectangular adjective"], ["board displays timetable", "near the office"]]),
            _r("Sentence card: The sharp metal triangle rings when tapped. Classify triangle, rings, sharp, and metal.", "Triangle is a noun, rings is a verb, and sharp and metal describe the triangle. The sharp metal triangle rings when tapped.", [["triangle noun", "rings verb", "sharp and metal adjectives"], ["triangle rings", "when tapped"]]),
            _q("The bright star sticker marks the first box. Which word names the object doing the marking?", "sticker", ["bright", "star", "marks"]),
            _r("Facts: object - badge; shape - star-shaped; action - identifies the team leader.", "The star-shaped badge identifies the team leader. Badge is the noun, identifies is the verb, and star-shaped is the adjective.", [["badge noun", "identifies verb", "star-shaped adjective"], ["badge identifies", "team leader"]]),
            _q("A curved arrow points toward the exit. Which word is the action verb?", "points", ["curved", "arrow", "exit"]),
            _r("Facts: object - boxes; shape - cube-shaped; state - sit under the counter.", "The cube-shaped boxes sit under the counter. Boxes is the noun, sit is the verb, and cube-shaped is the adjective.", [["boxes noun", "sit verb", "cube-shaped adjective"], ["boxes sit", "under the counter"]]),
            _r("Fragment: The patterned circle. Add action and place: frames the number on the poster.", "The patterned circle frames the number on the poster. Circle is the noun, frames is the verb, and patterned is the adjective.", [["circle noun", "frames verb", "patterned adjective"], ["circle frames the number", "on the poster"]]),
        ],
        crunch_bar=CRUNCH_BAR["shape_words_and_sentences"],
        misconception="The learner treats every shape word as a noun, or writes a descriptive fragment with no verb because the object and its qualities seem sufficient.",
        remediation="Find the named object, what it does or is, and its shape descriptions, then reject any draft that cannot answer both 'what?' and 'does what?'.",
    ),
    _make_level(
        level_id="clear_pronouns_and_traits",
        title="Track pronouns in a friend profile",
        focus="resolve pronouns and use chapter trait words accurately",
        outcome="Connect each pronoun to one clear person or object and use a supplied cooperation trait in a fresh profile sentence supported by the card.",
        skill_ids=["grammar.pronouns", "vocab.chapter_word_usage"],
        choice_skill_ids=["grammar.pronouns"],
        episode_kind="meaning_encounter",
        source_anchor_ids=[f"{CHAPTER_ID}:write:31-32", f"{CHAPTER_ID}:think:29"],
        principle="A pronoun must agree with and clearly point to its referent; a trait word needs an action example rather than unsupported praise.",
        connect={"teaching_block": "Profiles become confusing when two people are named and a pronoun could point to either. Repeating a name once can protect clarity, while an action can prove a trait.", "passage": "Mina gave Tara the ruler because Tara needed it. She thanked Mina and measured the border. Here she clearly points to Tara because Tara receives and then responds.", "prompt": "Trace giver, receiver, and response before identifying the pronoun and the helpful trait."},
        choice_prompt="Which noun does the pronoun clearly replace?",
        response_prompt="resolve every pronoun and use the target trait in a new profile sentence supported by the card.",
        rubric_descriptions=["Links each pronoun to the correct named referent using sentence logic.", "Uses the target chapter trait in a fresh sentence supported by a specific action."],
        examples=[
            _q("Asha showed the pattern to Leena. She checked every repeated pair. Who does she refer to?", "Leena", ["Asha", "the pattern", "every pair"]),
            _q("The square card covered the label, so Nikhil moved it. What does it refer to?", "the square card", ["the label", "Nikhil", "the movement"]),
            _r("Ravi lent Om a compass. He used it to draw a circle, then returned it. Trait word: responsible.", "He refers to Om, and it refers to the compass. Om was responsible because he returned the borrowed compass after using it.", [["He refers to Om", "it refers to compass"], ["responsible", "returned borrowed compass"]]),
            _r("Mira asked Zoya to hold the ruler while she marked the line. Zoya held it steady. Trait word: cooperative.", "The first she refers to Mira, and it refers to the ruler. Zoya was cooperative because she held the ruler steady while Mira worked.", [["she refers to Mira", "it refers to ruler"], ["cooperative", "held ruler steady"]]),
            _r("The triangle touched the circle, so Ben shifted it to the left. Trait word for Ben: attentive.", "It refers to the triangle. Ben was attentive because he noticed the overlap and shifted the triangle.", [["it refers to triangle", "triangle shifted"], ["attentive", "noticed overlap"]]),
            _r("Kavya gave Naman her sketch after he asked to compare ideas. Trait word: generous.", "Her refers to Kavya, and he refers to Naman. Kavya was generous because she shared her sketch for comparison.", [["her Kavya", "he Naman"], ["generous", "shared her sketch"]]),
            _r("Aarav and Jui tested the frame. They repaired it after one corner opened. Trait word: persistent.", "They refers to Aarav and Jui, and it refers to the frame. They were persistent because they repaired the frame after the first test failed.", [["They Aarav and Jui", "it frame"], ["persistent", "repaired after failure"]]),
            _r("The label was beside the arrow, but it was too small to read. Sia enlarged it. Trait word: practical.", "Both uses of it refer to the label. Sia was practical because she enlarged an unreadable label.", [["it refers to label", "both uses"], ["practical", "enlarged unreadable label"]]),
            _r("Nora thanked Ishan because he had saved her tile space. Trait word for Ishan: considerate.", "He refers to Ishan, and her refers to Nora. Ishan was considerate because he protected Nora's place in the design.", [["he Ishan", "her Nora"], ["considerate", "protected Nora's place"]]),
            _q("The circles surrounded the title. They were evenly spaced. What does they refer to?", "the circles", ["the title", "the spacing", "the page"]),
            _r("Pia reminded Dev about his turn, and he invited her to speak first. Trait word for Dev: courteous.", "His and he refer to Dev, while her refers to Pia. Dev was courteous because he invited Pia to speak first.", [["his and he Dev", "her Pia"], ["courteous", "invited Pia first"]]),
            _q("The rectangle held two photographs. It had a thick blue border. What does it refer to?", "the rectangle", ["the photographs", "the colour blue", "two borders"]),
            _r("Tara and Mehul checked their pieces before they joined them. Trait word: careful.", "Their and they refer to Tara and Mehul, while them refers to the pieces. They were careful because they checked the pieces before joining them.", [["their and they Tara and Mehul", "them pieces"], ["careful", "checked before joining"]]),
            _r("Anil offered his marker to Reva because hers had dried. Trait word for Anil: helpful.", "His refers to Anil's marker, and hers refers to Reva's marker. Anil was helpful because he offered a working marker when Reva's dried.", [["his Anil", "hers Reva"], ["helpful", "offered working marker"]]),
        ],
        crunch_bar=CRUNCH_BAR["clear_pronouns_and_traits"],
        misconception="The learner links a pronoun to the nearest noun even when the action becomes impossible, or calls someone helpful or responsible without naming an action that proves the trait.",
        remediation="Test each pronoun against the possible nouns, reject links that break number or event logic, then complete the trait frame 'was ___ because...'.",
    ),
    _make_level(
        level_id="animal_actions_and_agreement",
        title="Read action verse and match subjects",
        focus="interpret repetition in short verse and use subject-verb agreement",
        outcome="Explain what an animal-action pattern emphasises and choose or write a verb form that matches one or more subjects.",
        skill_ids=["reading.poetic_language", "grammar.subject_verb_agreement"],
        choice_skill_ids=["grammar.subject_verb_agreement"],
        episode_kind="expression_workshop",
        source_anchor_ids=[f"{CHAPTER_ID}:fun-words:34-35"],
        principle="Repeated action lines create rhythm and character, while the verb must still agree with whether the subject names one animal or more than one.",
        connect={"teaching_block": "A short action verse can repeat a sentence shape to compare animals. Singular subjects often take a verb ending in s, while plural subjects use the base form.", "passage": "The sparrow hops; the horses run. Each action fits its subject while the repeated pattern makes the list lively.", "prompt": "Compare one sparrow with several horses and notice how the verb forms change inside the repeated shape."},
        choice_prompt="Which verb form agrees with the subject in this patterned line?",
        response_prompt="repair subject-verb agreement and explain how the repeated action pattern shapes the verse.",
        rubric_descriptions=["Uses a verb form that agrees with each singular or plural subject.", "Identifies the repeated action pattern and explains its rhythmic or meaning effect."],
        examples=[
            _q("One monkey ___ from branch to branch.", "swings", ["swing", "swinging", "are swing"]),
            _q("Two parrots ___ above the mango tree.", "fly", ["flies", "flying", "is fly"]),
            _r("Draft: The dog run and the puppies barks. Pattern: one animal, then a group.", "The dog runs and the puppies bark. The repeated animal-plus-action pattern contrasts one dog with several puppies and creates a quick rhythm.", [["dog runs", "puppies bark"], ["animal-plus-action pattern", "quick rhythm"]]),
            _r("Lines: The frog leap; the ducks swims; the fish glide. Repair them and explain the list pattern.", "The frog leaps; the ducks swim; the fish glide. Repeating subject plus action presents three movements in a steady sequence.", [["frog leaps", "ducks swim", "fish glide"], ["subject plus action", "steady sequence"]]),
            _r("Verse: A bee hum; many crickets chirps; the quiet moth rests. Correct agreement and describe the sound contrast.", "A bee hums; many crickets chirp; the quiet moth rests. The repeated action lines move from one soft sound to many sounds and then to silence.", [["bee hums", "crickets chirp", "moth rests"], ["soft to many sounds", "then silence"]]),
            _r("Verse: The elephant lift its trunk; the deer raise their heads. Correct the verbs and explain the parallel actions.", "The elephant lifts its trunk; the deer raise their heads. The matching sentence pattern compares one large movement with a group's alert movement.", [["elephant lifts", "deer raise"], ["matching pattern", "compares movements"]]),
            _r("Draft: One owl watch; three bats circles; both lines begin with a number clue.", "One owl watches; three bats circle. The repeated number-subject-action pattern highlights the contrast between one watcher and several moving bats.", [["owl watches", "bats circle"], ["number-subject-action", "one versus several"]]),
            _r("Lines: The horse trots, the riders wave, the crowd cheer. Repair the last verb and explain the growing scene.", "The horse trots, the riders wave, and the crowd cheers. The repeated actions widen attention from the horse to riders and then the whole crowd.", [["horse trots", "riders wave", "crowd cheers"], ["widens attention", "horse to crowd"]]),
            _r("Verse: A squirrel gathers; two mynas call; the garden wake. Correct the final verb and explain the morning pattern.", "A squirrel gathers, two mynas call, and the garden wakes. The repeated present actions build a picture of the garden coming alive.", [["squirrel gathers", "mynas call", "garden wakes"], ["repeated present actions", "coming alive"]]),
            _q("The striped zebras ___ across the plain.", "graze", ["grazes", "is graze", "grazing"]),
            _r("Lines: The kitten stretch; the older cats yawn. Correct and explain the shared sleepy mood.", "The kitten stretches, and the older cats yawn. The parallel actions connect one kitten and several cats in the same sleepy mood.", [["kitten stretches", "cats yawn"], ["parallel actions", "sleepy mood"]]),
            _q("A lion ___ while the lionesses watch.", "roars", ["roar", "roaring", "are roar"]),
            _r("Verse: One ant carry a crumb; many ants builds a path. Correct both and explain the contrast.", "One ant carries a crumb; many ants build a path. The repeated structure contrasts an individual action with group work.", [["ant carries", "ants build"], ["individual action", "group work"]]),
            _r("Lines: The peacock dances; the feathers shines; visitors smile. Repair and explain the visual progression.", "The peacock dances, the feathers shine, and visitors smile. The repeated actions move from display to visible detail to human response.", [["peacock dances", "feathers shine", "visitors smile"], ["display to detail to response", "repeated actions"]]),
        ],
        crunch_bar=CRUNCH_BAR["animal_actions_and_agreement"],
        misconception="The learner chooses a verb by the nearest noun instead of the sentence subject, or identifies repetition without explaining how it compares actions, builds rhythm, or changes focus.",
        remediation="Decide whether each complete subject means one or more, choose the matching verb, then find the repeated sentence shape and finish 'This pattern shows...'.",
    ),
]


ASSESSMENT_PAIRS = [
    _aq_pair("reading.event_sequence", "Which teamwork result came last?", ("The team compared two plans, combined their best parts, and displayed one finished map.", "They displayed the finished map.", ["They compared plans.", "They combined parts.", "They hid the map first."]), ("The bridge bent, pupils added braces, and a second test held more blocks.", "The second test held more blocks.", ["The bridge bent.", "Pupils added braces.", "The blocks removed the bridge."])),
    _ar_pair("reading.paragraph_main_idea", "State the main idea in one sentence.", "Explains how combined effort or evidence improved the shared result.", ("Four separate border ideas did not fit. The group measured the space and joined two patterns into one border that fit exactly.", "Measuring and combining ideas helped the group create a border that fit the available space.", [["measuring and combining ideas", "measuring and mixing two designs"], ["border that fit the available space", "border that matched the open space"]]), ("A map lacked labels, symbols, and a key. Three pairs completed one missing part each, then checked the map together.", "Dividing useful tasks and checking together turned an incomplete map into a usable one.", ["dividing tasks", "checking together", "usable map"]), interaction_type="summary"),
    _ar_pair("reading.inference_reason", "State the supported motive and cite its clue.", "Infers a motive that matches the character's words, action, or concern.", ("Nina asks to measure both banners before choosing because neither has been tested on the wall.", "Nina wants evidence before choosing, shown by her request to measure both untested banners.", ["wants evidence", "measure both"]), ("Omar rotates his tile after noticing that its point covers a label.", "Omar wants to keep the tile while making the label readable, shown by rotating instead of removing it.", ["keep the tile", "label readable", "rotating"])),
    _ar_pair("writing.reason_answer", "Propose a fair action and justify it from the card.", "States a fair resolution and a reason tied to the shared goal or evidence.", ("Two colours fit the theme, and both can be tested against the uniform cloth.", "Test both colours on the cloth because visibility evidence can decide fairly between two suitable choices.", ["test both colours", "visibility evidence"]), ("Mira has spoken twice, Dev has not spoken, and the group promised equal turns.", "Invite Dev to speak next because the group agreed to equal turns and Mira has already had two turns.", ["invite Dev", "equal turns"])),
    _aq_pair("vocab.attribute_ordering", "Which order follows the stated measure?", ("Plant heights: fern 22 cm, mint 14 cm, basil 18 cm. Shortest to tallest.", "mint, basil, fern", ["fern, basil, mint", "basil, mint, fern", "mint, fern, basil"]), ("Widths: A 8 cm, B 13 cm, C 10 cm. Widest to narrowest.", "B, C, A", ["A, C, B", "C, B, A", "B, A, C"])),
    _ar_pair("writing.short_answer", "Write the full order and justify it with values.", "Gives a complete order and cites the measurements that support it.", ("Corner counts: circle 0, triangle 3, rectangle 4, star 5. Least to greatest.", "The order is circle, triangle, rectangle, star because the corner counts rise from 0 to 3 to 4 to 5.", ["circle, triangle, rectangle, star", "0 to 3 to 4 to 5"]), ("Jar capacities: blue 250 ml, amber 400 ml, clear 300 ml. Least to greatest.", "The order is blue, clear, amber because the capacities rise from 250 to 300 to 400 millilitres.", ["blue, clear, amber", "250 to 300 to 400"]), interaction_type="short_text"),
    _aq_pair("grammar.noun_verb_adjective", "Which word is the shape adjective?", ("The circular mirror reflects the lamp.", "circular", ["mirror", "reflects", "lamp"]), ("A narrow rectangular board hangs nearby.", "rectangular", ["board", "hangs", "nearby"])),
    _ar_pair("writing.complete_sentence", "Use every supplied fact in one complete sentence.", "Writes a complete sentence with the object, action or state, and shape detail.", ("Object: window; shape: square; action: catches morning light; place: above the reading table.", "The square window catches the morning light above the reading table.", ["square window catches", "morning light", "above the reading table"]), ("Object: tiles; size: small; shape: hexagonal; action: cover the path; place: outside the library.", "Small hexagonal tiles cover the path outside the library.", ["hexagonal tiles cover", "the path", "outside the library"]), interaction_type="short_text"),
    _aq_pair("grammar.pronouns", "What does the pronoun refer to?", ("The star card covered the title, so Ria moved it.", "the star card", ["the title", "Ria", "the movement"]), ("Mina gave Tara the ruler. She thanked Mina.", "Tara", ["Mina", "the ruler", "the thanks"])),
    _ar_pair("vocab.chapter_word_usage", "Use the trait word in a supported profile sentence.", "Uses the supplied trait accurately and proves it with a specific action.", ("Trait: cooperative. Action: Zoya held the ruler steady while Mira drew.", "Zoya was cooperative because she held the ruler steady while Mira completed the line.", ["cooperative", "held the ruler steady"]), ("Trait: persistent. Action: Aman repaired the model after its first test failed.", "Aman was persistent because he repaired the model after the first test failed.", ["persistent", "repaired after failure"])),
    _aq_pair("grammar.subject_verb_agreement", "Which verb agrees with the subject?", ("A squirrel ___ along the fence.", "runs", ["run", "are run", "running"]), ("Three parrots ___ above the field.", "fly", ["flies", "is fly", "flying"])),
    _ar_pair("reading.poetic_language", "Explain the repeated action pattern and its effect.", "Identifies the pattern and explains its rhythm, comparison, or movement of focus.", ("The frog leaps, the ducks swim, the fish glide.", "Repeating animal plus action creates a steady rhythm while comparing three kinds of movement.", ["animal plus action", "steady rhythm", "three movements"]), ("One ant carries; many ants build; together the busy pathways grow.", "The repeated ant actions contrast individual effort with group work and lead toward a shared result.", ["individual effort", "group work", "shared result"])),
    _ar_pair("reading.paragraph_main_idea", "Summarise the teamwork result without listing every detail.", "Captures the shared problem, combined response, and improved result.", ("The mobile leaned left. Two pupils shifted pieces while another checked the centre string. The mobile then hung evenly.", "Joint adjustments to the pieces and centre string restored the mobile's balance.", ["joint adjustments", "restored balance"]), ("Four clue cards seemed separate. Matching their corners revealed one park plan, which the group labelled together.", "Matching and labelling separate clue cards revealed a complete park plan.", ["matching and labelling", "complete park plan"]), interaction_type="summary"),
    _ar_pair("writing.complete_sentence", "Repair the fragment as a complete shape sentence.", "Adds a named object and meaningful verb while preserving the supplied detail.", ("Fragment: The bright round. Add lantern and hangs above the doorway.", "The bright round lantern hangs above the doorway.", ["round lantern hangs", "above the doorway"]), ("Fragment: A narrow oval mirror. Add reflects the lamp beside the stairs.", "A narrow oval mirror reflects the lamp beside the stairs.", ["oval mirror reflects", "lamp beside the stairs"]), interaction_type="short_text"),
]


LAUNCH_DEPTH_CASES = {
    "mural_sequence_and_idea": [
        _launch_depth_case(
            "Two groups wanted the centre of a science wall. They measured the space, placed the solar-system panel above the plant panel, and added one shared title across both displays.",
            "Order the science-wall disagreement, measuring, placement, and shared-title result, then state the main idea.",
            "The groups disagreed, measured the wall, placed both panels, and added a shared title. The main idea is that measuring and one joint heading gave both science topics a fair place.",
            "the groups disagreed, measured the wall, placed both panels, and added a shared title",
            "measuring and one joint heading gave both science topics a fair place",
            ordered=True,
        ),
        _launch_depth_case(
            "For a neighbourhood map, one child drew roads while another drew trees over the same corner. They used tracing paper, shifted the trees beside the roads, and coloured the finished map together.",
            "Retell the neighbourhood-map problem and solution, then give the whole idea of the joint map.",
            "The drawings overlapped, the children tested tracing paper, moved the trees, and finished the map together. The card shows that checking both plans helped combine roads and trees clearly.",
            "the drawings overlapped, the children tested tracing paper, moved the trees, and finished the map together",
            "checking both plans helped combine roads and trees clearly",
            ordered=True,
        ),
        _launch_depth_case(
            "Mona painted festival lamps on a banner, but Ali needed room for the date. They tried a small date, widened the lower border, and chose a layout where both details were easy to read.",
            "Sequence Mona and Ali's festival-banner choices and state how their combined work solved the problem.",
            "Mona painted lamps, Ali raised the date problem, they tested sizes, and then widened the border. The main idea is that trying layouts helped them keep the artwork and make the date readable.",
            "Mona painted lamps, Ali raised the date problem, they tested sizes, and then widened the border",
            "trying layouts helped them keep the artwork and make the date readable",
            ordered=True,
        ),
    ],
    "conflict_inference_and_reason": [
        _launch_depth_case(
            "Ravi holds the only wide paintbrush and says the background must be finished first. Pihu needs the same brush for a river, and the group wants the poster ready by lunch.",
            "Why is Ravi resisting Pihu's request for the wide paintbrush, and what fair response supports the poster goal?",
            "Ravi resists because he thinks the large background is urgent. They should set a short timer and share the brush because both sections must be ready by lunch.",
            "Ravi resists because he thinks the large background is urgent",
            "set a short timer and share the brush",
        ),
        _launch_depth_case(
            "Anaya refuses to move her garden label because she worries visitors will miss the herb name. The label covers Kabir's watering note, and both facts are needed on the display.",
            "What concern explains Anaya's garden-label choice, and how can the pair meet their shared display goal?",
            "Anaya worries that the herb name will become hard to see. They should place the name above the watering note because visitors need both pieces of information.",
            "Anaya worries that the herb name will become hard to see",
            "place the name above the watering note",
        ),
        _launch_depth_case(
            "During rhythm practice, Zoya repeats her drum part and will not try Neel's softer ending. She says the class may lose the beat, while the group wants a calm finish.",
            "Why does Zoya resist the softer drum ending, and what fair test can protect the group's calm finish?",
            "Zoya resists because she fears the beat will break. The group should rehearse Neel's ending once with a count because a trial can check the beat before they decide.",
            "Zoya resists because she fears the beat will break",
            "rehearse Neel's ending once with a count",
        ),
    ],
    "shape_attribute_order": [
        _launch_depth_case(
            "A tile row shows a small circle first, a tall rectangle second, a blue triangle third, and a long oval fourth. The rectangle must stay beside the circle and triangle.",
            "Write the full tile-row order and explain why the tall rectangle belongs between the circle and triangle.",
            "The order is small circle, tall rectangle, blue triangle, long oval. The rectangle belongs second because the card places it after the circle and before the triangle.",
            "small circle, tall rectangle, blue triangle, long oval",
            "after the circle and before the triangle",
            ordered=True,
        ),
        _launch_depth_case(
            "Four flags hang from left to right: red square, green triangle, yellow rectangle, and white circle. The yellow flag touches the green and white flags.",
            "State the left-to-right flag order and give the position reason for the yellow rectangle.",
            "The order is red square, green triangle, yellow rectangle, white circle. The yellow rectangle is third because it is between the green triangle and white circle.",
            "red square, green triangle, yellow rectangle, white circle",
            "between the green triangle and white circle",
            ordered=True,
        ),
        _launch_depth_case(
            "A craft shelf holds a short blue tube, a wide orange box, a thin silver ring, and a tall purple cone in that order. The ring follows the box.",
            "List the craft-shelf objects in order and explain the thin silver ring's neighbouring positions.",
            "The order is short blue tube, wide orange box, thin silver ring, tall purple cone. The ring is after the box and before the cone.",
            "short blue tube, wide orange box, thin silver ring, tall purple cone",
            "after the box and before the cone",
            ordered=True,
        ),
    ],
    "shape_words_and_sentences": [
        _launch_depth_case(
            "The triangular flag flutters above the gate. Flag is the object, triangular describes its shape, and flutters tells its action.",
            "Identify the jobs of triangular, flag, and flutters, then write the complete gate sentence.",
            "Flag is a noun, triangular is an adjective, and flutters is a verb. The triangular flag flutters above the gate.",
            "flag is a noun, triangular is an adjective, and flutters is a verb",
            "the triangular flag flutters above the gate",
        ),
        _launch_depth_case(
            "A narrow ribbon curls around the round parcel. Ribbon names the object, narrow describes it, and curls gives the action.",
            "Explain narrow, ribbon, and curls, then write one complete sentence about the round parcel.",
            "Ribbon is a noun, narrow is an adjective, and curls is a verb. A narrow ribbon curls around the round parcel.",
            "ribbon is a noun, narrow is an adjective, and curls is a verb",
            "a narrow ribbon curls around the round parcel",
        ),
        _launch_depth_case(
            "The square window gleams beside the dark door. Window is a noun, square tells its shape, and gleams shows what it does.",
            "Name the word jobs in square window gleams and write the full dark-door sentence.",
            "Window is a noun, square is an adjective, and gleams is a verb. The square window gleams beside the dark door.",
            "window is a noun, square is an adjective, and gleams is a verb",
            "the square window gleams beside the dark door",
        ),
    ],
    "clear_pronouns_and_traits": [
        _launch_depth_case(
            "Meena waited while Farah tested two border colours. Then Meena praised Farah for checking both choices before deciding. This patient behaviour kept the pair calm.",
            "Who does she mean if the next line says, 'She praised Farah,' and how can patient be used in a fresh profile sentence?",
            "She means Meena because Meena gives the praise. New profile: Meena is patient because she waits while her partner checks both choices.",
            "she means Meena",
            "Meena is patient because she waits",
        ),
        _launch_depth_case(
            "Arun brought the ruler, and Dev marked the poster edge. They checked every line together before cutting the paper. The card calls their work cooperative.",
            "Who does they refer to in the ruler-and-poster card, and use cooperative in a fresh sentence about the pair.",
            "They refers to Arun and Dev. New sentence: The cooperative partners checked the measurements together before they cut the poster.",
            "they refers to Arun and Dev",
            "the cooperative partners checked the measurements together",
        ),
        _launch_depth_case(
            "The tape roll ended, so Lata folded paper tabs to hold the display until more tape arrived. Her group called the solution resourceful.",
            "What does her refer to in the paper-tab card, and use resourceful in a fresh profile sentence grounded in Lata's action.",
            "Her refers to Lata. New profile: Lata is resourceful because she makes paper tabs when the tape runs out.",
            "her refers to Lata",
            "Lata is resourceful because she makes paper tabs",
        ),
    ],
    "animal_actions_and_agreement": [
        _launch_depth_case(
            "Bees hum by the basil, bees hum by the bean, bees hum wherever yellow flowers are seen. One bee hovers near a leaf, but many bees hover near the bed.",
            "Explain the repeated bees hum pattern and choose the matching hover forms for one bee and many bees.",
            "Repeating bees hum stresses their busy movement across the garden. One bee hovers, while many bees hover.",
            "repeating bees hum stresses their busy movement",
            "one bee hovers, while many bees hover",
        ),
        _launch_depth_case(
            "The crane steps through silver water; the cranes step when morning grows bright. Repeating step makes the birds' slow movement stand out.",
            "What does repeated step emphasise, and how does the verb change for the crane and the cranes?",
            "Repeated step emphasises the cranes' slow walking. The crane steps, and the cranes step.",
            "repeated step emphasises the cranes' slow walking",
            "the crane steps, and the cranes step",
        ),
        _launch_depth_case(
            "Monkeys leap over roots, monkeys leap past vines, monkeys leap as the forest path winds. A single monkey leaps onto a rock.",
            "Describe the effect of repeated monkeys leap and give the correct verb for one monkey.",
            "Repeating monkeys leap creates a lively action pattern through the forest. One monkey leaps onto a rock, while several monkeys leap together.",
            "repeating monkeys leap creates a lively action pattern",
            "one monkey leaps onto a rock, while several monkeys leap together",
        ),
    ],
}

_add_launch_depth_variants(LEVELS, LAUNCH_DEPTH_CASES)


_SEMANTIC_OPTION_REPLACEMENTS = {'are roar': 'roared',
 'are run': 'ran',
 'are swing': 'swung',
 'is fly': 'flew',
 'is graze': 'grazed'}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch03:assessment:18': {'model_answer': "Let Lata's pair use the easel now "
                                               'because the timer signalled the agreed '
                                               'swap.',
                               'passage': "Ravi's pair has used the display easel for "
                                          "ten minutes. Lata's pair is still waiting, "
                                          'and the class agreed to swap pairs when the '
                                          'timer rings.',
                               'prompt': 'What should happen now? Give a fair action '
                                         'and support it with the timer and agreement.',
                               'relevance_terms': ["let Lata's pair use the easel",
                                                   'timer signalled the agreed swap'],
                               'slot_aliases': [["let Lata's pair use the easel"],
                                                ['timer signalled the agreed swap']]}}


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

MANIFEST = _build_manifest(
    chapter_id=CHAPTER_ID,
    chapter_no=3,
    title="Best Friends",
    unit_title="Fun with Friends",
    source_url=SOURCE_URL,
    page_extract="/tmp/zidd-ncert-class2-3/eng_c3_ch03.txt",
    source_anchors=SOURCE_ANCHORS,
    levels=LEVELS,
    assessment_pairs=ASSESSMENT_PAIRS,
)

_apply_semantic_copy_corrections(MANIFEST["levels"])
_apply_semantic_copy_corrections(
    MANIFEST["chapter_assessment"]["items"]
)
_apply_semantic_assessment_overrides(MANIFEST)
