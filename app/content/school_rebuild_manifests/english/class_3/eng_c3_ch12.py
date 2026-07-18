"""Deep authored manifest for Class 3 English Chapter 12.

The source extract supplied chapter themes and exercise forms only. All Zidd
runtime passages, questions, options, reference answers, and rubrics are new.
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
    "chapter_id": "eng_c3_ch12",
    "chapter_no": 12,
    "title": "Chandrayaan",
    "unit_title": "The Sky",
    "source_url": "https://ncert.nic.in/textbook/pdf/cesa112.pdf",
    "source_analysis_reference": (
        "/tmp/zidd-ncert-class2-3/eng_c3_ch12.txt structure review"
    ),
    "anchors": [
        {"label": "Let us read: Rani's question, India Moon news, rocket vehicle, name meanings, launch, and landing dates", "page_start": 1, "page_end": 4, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us think A: mission comprehension and inference questions", "page_start": 5, "page_end": 5, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us learn A-C: a and an with singular noun phrases", "page_start": 6, "page_end": 7, "treatment": "textbook_companion", "required": False},
        {"label": "Let us write A: sk, sw, sp, and st blend word completion", "page_start": 8, "page_end": 8, "treatment": "taught_and_assessed", "required": True},
        {"label": "Fun with Words A-B: ordinal positions of weekdays", "page_start": 9, "page_end": 9, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us speak: ask about and share a far journey", "page_start": 5, "page_end": 5, "treatment": "guided_only", "required": False},
        {"label": "Let us write B: draw and describe the Moon", "page_start": 8, "page_end": 8, "treatment": "optional_creative", "required": False},
        {"label": "Let us do A: group project with mission news clippings", "page_start": 10, "page_end": 10, "treatment": "offline_group_activity", "required": False},
    ],
    "levels": [
        {
            "level_id": "mission_curiosity",
            "title": "Follow a curious question",
            "focus": "identify a curiosity-driven main idea and infer why questions lead to investigation",
            "concept": "curiosity and inquiry",
            "outcome": "Show how noticing leads to a question and an investigation, then use visible clues to explain the next step.",
            "skill_ids": ["reading.paragraph_main_idea", "reading.inference_reason"],
            "episode_kind": "meaning_encounter",
            "anchor_indexes": [1, 2],
            "principle": "Curiosity begins with a noticed gap in understanding. A main idea links the question to the investigation, while an inference explains why the chosen source can help.",
            "connect": _connect(
                "A curious reader asks a clear question and then uses the facts on a card. Keep the answer tied to what the card actually says.",
                "Mission fact card: Chandrayaan-3 was India's Moon mission. A rocket carried it away from Earth. It landed on the Moon on 23 August 2023.",
                "Find the mission, vehicle, country, and landing date before stating the main idea.",
            ),
            "misconception": "The learner treats any sentence ending in a question mark as useful curiosity or invents a reason for visiting a source that the reference does not support.",
            "remediation": "Box the knowledge gap, underline the exact question, identify what the chosen source contains, and write one sentence linking inquiry to evidence.",
            "creative_transfer": True,
            "cases": [
                _case("India Moon mission", "A fact card says Chandrayaan-3 was India's mission to the Moon and reached the lunar surface in August 2023.", "What main idea does the card give?", "India sent Chandrayaan-3 on a Moon mission.", "The card is mainly about a sea voyage.", "The mission belonged to another country not named.", "The country, mission name, and Moon destination support the answer.", "India Moon mission", "Chandrayaan three destination"),
                _case("rocket vehicle", "The mission card says a rocket carried Chandrayaan-3 away from Earth on its journey.", "Why is rocket an important fact?", "The rocket was the vehicle that began the Moon journey.", "The rocket was a food carried by the mission.", "The rocket landed in a classroom tray.", "The card gives the rocket's carrying job directly.", "rocket began journey", "carried mission from Earth"),
                _case("name meaning", "A word card explains: Chandra means Moon, and Yaan means vehicle.", "What does Chandrayaan tell us through its two parts?", "Chandrayaan joins the ideas of Moon and vehicle.", "Chandra means river and Yaan means fruit.", "Both parts mean the same colour.", "The two printed meanings combine in the mission name.", "Moon and vehicle", "two word meanings join"),
                _case("landing date", "The dated card says Chandrayaan-3 landed on the Moon on 23 August 2023.", "Which landing fact is supported?", "Chandrayaan-3 landed on the Moon on 23 August 2023.", "It landed on Earth on 14 July 2023.", "The card gives no landing date.", "The mission, action, place, and date are all printed.", "landed Moon 23 August 2023", "dated landing fact"),
                _case("launch and landing", "The timeline begins with launch on 14 July 2023 and ends with the Moon landing on 23 August 2023.", "What can readers infer about the two dates?", "The launch happened before the Moon landing.", "The landing happened before launch.", "Both events happened on the same day.", "The timeline order places July before August.", "launch before landing", "July before August"),
                _case("curious question", "Rani reads that India landed a mission on the Moon and asks which vehicle began the journey. The next card names a rocket.", "How is her question answered?", "The rocket is the vehicle named for the start of the journey.", "A bicycle is named as the Moon vehicle.", "Her question asks about the landing date only.", "The second card supplies the exact vehicle she asks about.", "rocket answers vehicle question", "next card names it"),
                _case("fact summary", "The card lists India, Chandrayaan-3, a rocket, the Moon, and 23 August 2023.", "Write the one idea that joins all five details.", "India's Chandrayaan-3 travelled by rocket and landed on the Moon on 23 August 2023.", "The details describe a festival meal in August.", "The Moon launched a country called India.", "Every listed detail belongs to one mission fact summary.", "India mission landed Moon", "rocket and date details"),
            ],
        },
        {
            "level_id": "mission_questions",
            "title": "Build answerable questions",
            "focus": "form precise questions and punctuate them correctly",
            "concept": "question formation",
            "outcome": "Reorder question words, helper verbs, subjects, and actions into a focused question with a capital letter and final question mark.",
            "skill_ids": ["grammar.question_formation", "grammar.punctuation_capitalization"],
            "episode_kind": "language_lab",
            "anchor_indexes": [1, 2],
            "principle": "An answerable question names the missing information and uses a clear word order. It begins with a capital and ends with a question mark, not a full stop.",
            "connect": _connect(
                "A useful question asks for one clear detail. Readers choose who, what, where, when, why, or how, place the helper before the subject when needed, and check the end mark.",
                "The class wants to know the model rover's destination. The focused question is: Where will the model rover stop?",
                "Notice how where names the missing place and the question mark completes the sentence.",
            ),
            "misconception": "The learner adds a question mark to statement word order, leaves the opening word lowercase, or combines several unrelated questions into one sentence.",
            "remediation": "Name the missing information, select one question word, arrange helper-subject-action, capitalise the first word, and add one question mark.",
            "ordered_response": True,
            "cases": [
                _case("rover place", "The class knows the model rover will stop, but it does not know the place. The words are: where / will / the rover / stop.", "Which focused question is formed correctly?", "Where will the rover stop?", "The rover will stop where.", "where the rover stop.", "Where requests the missing place and the order plus question mark is correct.", "Where will rover stop", "place question order"),
                _case("launch time", "The team knows a balloon probe will rise today but needs the exact time. The words are: when / will / it / rise.", "How should the question be written?", "When will it rise?", "It will rise when.", "when will it rise.", "When asks for time and the sentence uses capital and question mark.", "When will it rise", "time question punctuation"),
                _case("wheel reason", "Tara sees one wheel turn slowly and wants the cause. The words are: why / is / this wheel / slow.", "Which question asks for the reason?", "Why is this wheel slow?", "This wheel is slow why.", "why this wheel slow.", "Why targets a reason with correct helper-subject order.", "Why is wheel slow", "reason word order"),
                _case("camera action", "The manual names a camera but not its job. The words are: what / does / the camera / record.", "Which complete question requests the action?", "What does the camera record?", "The camera does record what.", "what camera record.", "What asks for the missing information and does supports the verb.", "What does camera record", "action question form"),
                _case("designer person", "The card describes a model but omits the maker's name. The words are: who / designed / the model.", "How should the identity question appear?", "Who designed the model?", "The model designed who.", "who designed the model.", "Who asks for a person and the capital plus question mark complete it.", "Who designed model", "person question mark"),
                _case("travel method", "The route is known, but the class wants to know the method of movement. The words are: how / does / the rover / move.", "Which question asks for method?", "How does the rover move?", "The rover does move how.", "how the rover move.", "How requests method and the helper precedes the subject.", "How does rover move", "method helper order"),
                _case("sample location", "A report says a sample was stored but not where. The words are: where / was / the sample / stored.", "Which punctuated question is correct?", "Where was the sample stored?", "The sample was stored where.", "where was sample stored.", "Where requests location with correct past helper order.", "Where was sample stored", "location past question"),
            ],
        },
        {
            "level_id": "mission_event_chain",
            "title": "Sequence a model mission",
            "focus": "track mission events and comprehend each step's purpose",
            "concept": "mission event sequence",
            "outcome": "Order preparation, launch, travel, task, and return from a fully visible model mission, explaining why each stage must follow the one before it.",
            "skill_ids": ["reading.event_sequence", "reading.sentence_comprehension"],
            "episode_kind": "application_mission",
            "anchor_indexes": [1],
            "principle": "A mission follows a needed order, not the most exciting action. Equipment checks come before launch, travel comes before the target task, and results are recorded after the task.",
            "connect": _connect(
                "Mission reports include many actions, but their logic is stable: prepare, begin travel, reach the target, complete a task, and report or return the result.",
                "The club checks the model rover's battery, starts it at the ramp, guides it to the sand tray, records wheel marks, and brings the record sheet back.",
                "Trace why the battery check and travel must happen before the wheel-mark record.",
            ),
            "misconception": "The learner places the most dramatic action first or treats preparation and evidence return as optional details outside the mission chain.",
            "remediation": "Label each action prepare, travel, arrive, task, or report; connect dependencies with arrows; and state what would fail if one stage moved earlier.",
            "ordered_response": True,
            "cases": [
                _case("sand rover", "The team charges a model rover, places it at the ramp, drives it to a sand tray, photographs its tracks, and saves the observation note.", "Which mission order is correct?", "First charge, then start and travel, next record tracks, and finally save the note.", "First record tracks before the rover reaches sand.", "First save an observation that has not happened.", "The rover must be ready and travel before the team can record its tracks.", "charge travel record save", "travel before track record"),
                _case("balloon probe", "Pupils attach a temperature card to a balloon, check the string, release it to the ceiling, read the card after lowering it, and log the result.", "How should the model mission be sequenced?", "Attach and check first, release and lower next, then read and log the card.", "Log the result before attaching the card.", "Read the card while it is absent.", "Equipment must be prepared and recovered before its result can be read.", "attach release lower log", "prepare recover read"),
                _case("crater drop", "The class labels three clay balls, drops them one at a time into flour, measures each mark, and compares the table.", "Which chain preserves the investigation?", "Label first, drop each ball, measure the marks, and finally compare the table.", "Compare the table before making any mark.", "Measure balls that were never dropped.", "Labels connect each drop to the later measurement and comparison.", "label drop measure compare", "labels connect evidence"),
                _case("signal route", "A coder writes three movement commands, checks them, sends them to the rover, watches the route, and corrects the second command afterward.", "What sequence explains the correction?", "Write and check, send, observe the route, and then correct the faulty command.", "Correct the route before sending any command.", "Observe a movement before writing instructions.", "The visible route supplies evidence for the later correction.", "write send observe correct", "observation guides correction"),
                _case("sample carrier", "A small carrier is cleaned, moved to a marked tray, loaded with one stone, returned to base, and opened over a mat.", "Which ordered report is safe and complete?", "Clean, travel, load, return, and finally open over the mat.", "Open at base before collecting the stone.", "Load the stone before the carrier reaches the tray.", "Travel to the sample precedes loading, and return precedes opening.", "clean travel load return", "collection before opening"),
                _case("camera tower", "Students test a model camera, raise it on a cardboard tower, capture a view of the grid, lower it, and inspect the saved image.", "How does the evidence move through the mission?", "Test and raise the camera, capture the grid, lower it, and inspect the saved result.", "Inspect an image before capturing it.", "Lower the camera before raising it.", "Capture creates the evidence that can be inspected after recovery.", "test raise capture inspect", "capture before inspection"),
                _case("night sensor", "The club checks a light sensor indoors, carries it to a dark box, records the reading, returns it to the desk, and compares both readings.", "Which mission sequence supports comparison?", "Check indoors, move to darkness, record, return, and compare the two readings.", "Compare before recording the dark reading.", "Return from the box before entering it.", "Two readings from ordered settings are required for comparison.", "check move record compare", "two settings evidence"),
            ],
        },
        {
            "level_id": "mission_words_nouns",
            "title": "Use mission words and blends",
            "focus": "use mission vocabulary in context and spell words beginning with sk, sw, sp, and st",
            "concept": "mission word meaning and opening blends",
            "outcome": "Use mission words such as launch, land, rocket, and vehicle correctly, then complete written words with sk, sw, sp, or st.",
            "skill_ids": ["vocab.chapter_word_usage", "vocab.spelling"],
            "episode_kind": "language_lab",
            "anchor_indexes": [1, 4],
            "principle": "A mission word must fit the action or object on the card. In an opening blend, keep both starting letters and check the whole word's meaning.",
            "connect": _connect(
                "Use the sentence clue to choose a mission word. For a word gap, test sk, sw, sp, and st, then keep the blend that makes a real word with the right meaning.",
                "A rocket can launch from Earth. In the word __ace, the blend sp makes space.",
                "Check the mission meaning first, then keep both letters in the written blend.",
            ),
            "misconception": "The learner swaps launch and land, calls every machine a rocket, or writes only one letter from the opening blend.",
            "remediation": "Underline the action clue, choose the mission word that fits, then test sk, sw, sp, and st and copy both letters of the useful blend.",
            "cases": [
                _case("model vehicle", "The wheeled machine carries a card across the tray. The sentence calls it ___ model vehicle, and the noun begins with the consonant sound v.", "Which vocabulary phrase is correct?", "It is a model vehicle used to carry the card.", "It is an model vehicle because m is written first.", "Vehicle means the place where a trip ends.", "Vehicle names the carrier, and its opening sound takes a.", "a model vehicle", "carrier consonant sound"),
                _case("engineer check", "The person tests the wheel design and records changes. Engineer begins with a vowel sound.", "Which phrase and meaning fit?", "An engineer checks and improves the model design.", "A engineer is the place where a model lands.", "Engineer means a radio message.", "The noun names a technical problem-solver and begins with a vowel sound.", "an engineer", "checks design vowel"),
                _case("space blend", "The sentence says, 'A rocket travels through __ace.' The missing noun names the vast area beyond Earth.", "Which opening blend completes the word?", "The word is space, beginning with sp.", "The word is sace with one opening letter.", "The word is stake, which does not fit the meaning.", "Space keeps both sp letters and matches the beyond-Earth clue.", "space begins sp", "beyond Earth clue"),
                _case("land action", "After a short glide, the paper craft touches the target mat and stops. The report needs the verb land.", "Which sentence uses land accurately?", "The paper craft will land on the target mat.", "The craft will launch when it touches down.", "Land means a message sent by radio.", "Touching down at the destination matches land.", "land target mat", "touch down action"),
                _case("star blend", "The card says, 'The Moon and Earth are in a sky with each __ar.' The missing noun names a bright object seen at night.", "Which blend forms the word?", "The word is star, beginning with st.", "The word is tar, missing the full blend.", "The word is scar, which names a mark.", "Star keeps st and fits the bright-sky clue.", "star begins st", "bright night object"),
                _case("signal word", "A lamp flashes twice to tell the rover to stop. The flash carries information rather than moving the rover itself.", "Which sentence uses signal precisely?", "The two flashes are a signal telling the rover to stop.", "The flashes are an vehicle carrying stones.", "Signal means the final landing place.", "A signal conveys information through the stated flashes.", "a signal flashes", "carries information"),
                _case("sky blend", "The sentence says, 'The rocket rose into the __y.' The missing noun names the space seen above the ground.", "How should the word be completed?", "The word is sky, beginning with sk.", "The word is sy with one blend letter.", "The word is spy, which names a secret watcher.", "Sky keeps sk and matches the above-ground clue.", "sky begins sk", "above ground clue"),
            ],
        },
        {
            "level_id": "mission_ordinal_order",
            "title": "Report ordinal positions",
            "focus": "interpret ordinal position and arrange a sentence in sequence order",
            "concept": "ordinal mission order",
            "outcome": "Distinguish position from quantity, assign first through seventh to a visible line, and construct an ordered sentence with the correct ordinal adjective.",
            "skill_ids": ["vocab.attribute_ordering", "grammar.sentence_order"],
            "episode_kind": "language_lab",
            "anchor_indexes": [5],
            "principle": "Cardinal numbers tell how many; ordinal words tell position. A position sentence identifies the ordered line and the item occupying that place.",
            "connect": _connect(
                "An ordinal depends on a visible order. Readers locate the start point, count positions once, and attach first, second, third, or another ordinal to the correct item.",
                "The model mission line reads: check battery, close hatch, start timer, move rover. Start timer is the third action.",
                "Locate the first action before confirming the third position.",
            ),
            "misconception": "The learner reports how many items instead of an item's position, starts from the wrong end, or scrambles the subject and ordinal phrase.",
            "remediation": "Mark the line's start, number each position, circle the target, state its ordinal, and rebuild the sentence as item plus is plus ordinal position.",
            "ordered_response": True,
            "cases": [
                _case("four-step line", "The printed order is check battery, close hatch, start timer, move rover. The question targets start timer.", "Which ordinal sentence is correct?", "Start timer is the third action in the line.", "Start timer is three actions in total.", "Third the action timer start is.", "Counting from the stated beginning places it after two actions.", "third action timer", "after two positions"),
                _case("tool queue", "The tool order is brush, ruler, torch, scoop, camera. The target is the torch.", "What position does the torch occupy?", "The torch is third in the tool order.", "There are third torches in the line.", "Torch the order in third is.", "Brush and ruler occupy the first two positions.", "torch is third", "two items before"),
                _case("seven cards", "The weekday cards begin Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday. The target is Friday.", "Which ordinal describes Friday here?", "Friday is the sixth card in the stated order.", "Friday means there are sixth cards.", "Sixth Friday order the is.", "Five named cards appear before Friday.", "Friday sixth card", "five before position"),
                _case("landing tasks", "The task strip says unfold legs, test balance, mark target, release model. The target task is mark target.", "How should its position be reported?", "Mark target is the third task.", "Mark target means three tasks exist only.", "Third is mark the target task.", "Two actions are printed before the target action.", "mark target third", "two actions before"),
                _case("sample row", "The labelled samples are red, blue, green, white, black from left to right. The target is white.", "Which sentence states position rather than quantity?", "The white sample is fourth from the left.", "There are fourth white samples.", "White from fourth left sample.", "Three samples occur before white from the stated start.", "white fourth left", "three before"),
                _case("speaker turns", "The discussion order is Nia, Dev, Kavi, Uma. The target speaker is Kavi.", "What ordinal belongs to Kavi's turn?", "Kavi has the third speaking turn.", "Kavi has three speaking turns.", "Third turn Kavi has the.", "Nia and Dev speak before Kavi.", "Kavi third turn", "two speakers before"),
                _case("route stops", "The rover route visits gate, ramp, sand tray, flag, base. The target location is flag.", "Which ordered sentence is accurate?", "The flag is the fourth stop on the route.", "The route has fourth flags.", "Fourth the flag stop route.", "Gate, ramp, and sand tray are the first three stops.", "flag fourth stop", "three stops before"),
            ],
        },
        {
            "level_id": "mission_report_reason",
            "title": "Report a completed test",
            "focus": "use past tense and justify a mission decision from evidence",
            "concept": "mission evidence report",
            "outcome": "Report a completed model mission consistently in past tense and explain one design or route decision with a because clause tied to recorded evidence.",
            "skill_ids": ["grammar.tense_usage", "writing.reason_answer"],
            "episode_kind": "expression_workshop",
            "anchor_indexes": [1, 2],
            "principle": "A completed mission report uses past forms for actions and evidence. A reason sentence names the observed problem and the decision it supports.",
            "connect": _connect(
                "Reports separate what happened from what the team will do next. Past-tense evidence should appear before the because-based design conclusion.",
                "Yesterday, the rover crossed the smooth board but stopped in loose sand. The team chose wider wheels because the narrow wheels spun without moving forward.",
                "Check crossed, stopped, and spun as completed evidence supporting the wheel decision.",
            ),
            "misconception": "The learner mixes present and past in one completed report or gives a preferred design without citing the recorded result that justifies it.",
            "remediation": "Circle the completed-time marker, convert action verbs to past, underline the observed problem, and join the decision to that evidence with because.",
            "creative_transfer": True,
            "cases": [
                _case("wide wheels", "Yesterday, the narrow wheels spun in sand and the rover stopped. The team fitted wider covers for the next test.", "Which report uses tense and reason correctly?", "The rover stopped because its narrow wheels spun, so the team fitted wider covers.", "The rover stops yesterday because it will spun.", "The team fitted covers before observing any wheel.", "Past evidence directly supports the completed design change.", "stopped spun fitted", "because narrow wheels"),
                _case("stronger leg", "During the test, one thin landing leg bent and the model tipped. The team replaced it with a thicker leg.", "Why was the leg replaced, and how should the event be reported?", "The team replaced the leg because the thin one bent and tipped the model.", "The team replaces it yesterday because it never bent.", "The model tipped after a future replacement.", "Bent and tipped are completed observations that justify replacement.", "replaced because bent", "tipped model evidence"),
                _case("shorter route", "The rover followed a long route, used most of its battery, and stopped before base. The team selected a shorter return route.", "Which evidence-based past report fits?", "The team chose a shorter route because the long route used too much battery.", "The team chooses yesterday because the battery is full forever.", "The short route caused the earlier long route.", "The recorded battery loss explains the later route choice.", "chose shorter route", "long route battery loss"),
                _case("camera cover", "Powder covered the model camera lens, and the saved view looked cloudy. Pupils added a clear shield.", "How should the design reason be stated?", "Pupils added a clear shield because powder made the camera view cloudy.", "Pupils add a shield yesterday because the view was clear.", "The shield created the earlier powder.", "The visible image problem supports protecting the lens.", "added clear shield", "powder cloudy view"),
                _case("signal pause", "The first command arrived late, and the rover turned after passing the marker. The coder added a pause before the turn command.", "Which report connects evidence and correction?", "The coder added a pause because the delayed command made the rover pass the marker.", "The coder adds a pause yesterday before any delay occurred.", "The marker sent the command itself.", "The late turn supplies the reason for changed timing.", "added pause delayed", "passed marker evidence"),
                _case("lighter carrier", "The heavy sample carrier moved slowly and drained the model battery. The class removed two unused blocks.", "Why did the class reduce the load?", "The class removed blocks because the heavy carrier drained the battery.", "The class removes blocks yesterday because the battery gained power.", "Unused blocks made the carrier lighter before removal.", "Slow movement and battery drain justify a lower mass.", "removed blocks heavy", "battery drain reason"),
                _case("raised sensor", "A low sensor struck every ridge and missed readings. The team raised it by two centimetres and repeated the route.", "Which completed report supports the adjustment?", "The team raised the sensor because it struck the ridges and missed readings.", "The team raises it yesterday because it cleared every ridge before.", "The repeated route happened before the first problem.", "The contact and missing data are recorded reasons for more clearance.", "raised sensor struck", "missed readings reason"),
            ],
        },
    ],
}


FRESH_CASES = {
    "mission_curiosity": [
        _fresh_case("country fact", "The card names India as the country that sent Chandrayaan-3 to the Moon.", "What fact answers the country question?", "India sent the Chandrayaan-3 Moon mission.", "The country and mission are stated together on the card.", "India sent Moon mission", "country named directly"),
        _fresh_case("journey vehicle", "Rani asks what carried the mission away from Earth. The fact card says it was a rocket.", "How is Rani's question answered?", "A rocket carried the mission away from Earth.", "The card directly names the vehicle and its job.", "rocket carried mission", "vehicle away from Earth"),
        _fresh_case("rover wheel question", "A model rover leaves one deep wheel line and one light line in sand. Mira asks why the lines differ and checks whether one wheel carries extra clay.", "What main idea links Mira's question and check?", "Mira investigates whether extra clay makes one rover wheel press deeper into sand.", "The unequal tracks lead her to test the weight on one wheel.", "checks deeper rover track", "extra clay changes pressure"),
        _fresh_case("battery table clue", "A club rover stops after two minutes with an old battery but runs for nine minutes with a charged battery. Dev checks the table before choosing one.", "Why does Dev choose the charged battery?", "Dev chooses it because the table shows a longer running time.", "Nine minutes is longer than the old battery's two-minute result.", "charged battery runs longer", "nine versus two minutes"),
        _fresh_case("crater test plan", "Three clay balls have different widths. The team drops each from the same height into flour and measures every mark.", "State the investigation idea and why the height stays the same.", "The team compares how ball width changes a crater, and one height keeps the test fair.", "Only the ball width should change while the drop height remains equal.", "width changes crater size", "same height fair test"),
        _fresh_case("camera focus report", "The first rover photo is blurry. The team cleans the lens, takes a second photo, and finds the grid lines clear.", "What main idea covers the whole report?", "Cleaning the model rover lens made the next grid photo clearer.", "The first and second photos show the result of one repair.", "clean lens clear photo", "repair improves image"),
        _fresh_case("route map choice", "A rover map shows Route A crossing three rough patches and Route B crossing one. The team wants fewer bumps for a glass sample.", "Why will the team probably choose Route B?", "Route B is safer for the glass sample because it has fewer rough patches.", "The map shows one rough patch on B compared with three on A.", "choose route B", "fewer rough patches"),
        _fresh_case("mission summary", "The card gives four ideas: India, a rocket, Chandrayaan-3, and a Moon landing.", "Write the main idea joining them.", "India used a rocket for Chandrayaan-3, which later landed on the Moon.", "All four details describe one Moon mission.", "India rocket Moon landing", "one mission details"),
        _fresh_case("curious reader", "A child knows the landing date but not the mission name. She checks the heading Chandrayaan-3.", "Why does she check the heading?", "She checks it to find the name of the Moon mission.", "The heading supplies the missing information she wants.", "find mission name", "heading answers question"),
        _fresh_case("meaning question", "Rani sees Chandrayaan and asks why Moon and vehicle belong together. A note explains both word parts.", "What main idea fits the note?", "The mission name combines a Moon word and a vehicle word.", "Chandra and Yaan are each explained on the card.", "Moon vehicle name", "two parts explained"),
        _fresh_case("rocket question", "The story card shows models of rockets and then states that a rocket is used to reach the Moon.", "Why do the rocket models help Rani?", "They help Rani connect the vehicle word with a Moon journey.", "The later fact explains what the models represent.", "models show rocket vehicle", "fact links Moon journey"),
        _fresh_case("fact checking", "One note says the landing was in July, but the dated fact card says 23 August 2023.", "Which date should Rani keep?", "Rani should keep 23 August 2023 as the landing date.", "The dated fact card is the supplied source for this task.", "landing 23 August 2023", "dated card corrects note"),
        _fresh_case("bridge crack check", "A model bridge bends only when the rover carries three blocks. Kavi notices a small crack near the middle and tests the empty rover next.", "What main idea links Kavi's bridge question and next check?", "Kavi investigates whether the three-block load causes the bridge to bend and crack.", "Comparing the loaded and empty rover can separate weight from other causes.", "checks load causes crack", "loaded versus empty test"),
        _fresh_case("plant lamp question", "One seedling under the rover lamp leans left while the others stand straight. Rina asks why and moves the lamp to the centre for one day.", "How does Rina's observation lead to a careful next step?", "Rina investigates whether the side lamp made one seedling lean toward its light.", "Moving the lamp to the centre tests the light-direction clue.", "tests light caused leaning", "lamp moved to centre"),
        _fresh_case("magnet wheel clue", "A rover wheel stops beside a hidden magnet but rolls past the same spot after the magnet is removed. Dev writes both results in a table.", "What question and evidence form the main idea of Dev's check?", "Dev checks whether the hidden magnet stopped the rover wheel.", "The wheel stops with the magnet and passes after its removal.", "checks magnet stopped wheel", "with magnet versus removed"),
    ],
    "mission_questions": [
        _fresh_case("country question", "The answer is India. The words are: which country / sent / the mission.", "Form the full question.", "Which country sent the mission?", "Which country asks for the missing nation and ends correctly.", "Which country sent mission", "country question mark"),
        _fresh_case("rocket question", "The class wants the vehicle name. Words: what / carried / Chandrayaan-3 / from Earth.", "Write the answerable question.", "What carried Chandrayaan-3 from Earth?", "What asks for the missing vehicle in clear order.", "What carried mission", "vehicle question order"),
        _fresh_case("launch date question", "The launch date is missing. Words: when / was / Chandrayaan-3 / launched.", "How should the question read?", "When was Chandrayaan-3 launched?", "When asks for a date and the helper precedes the subject.", "When was launched", "date helper order"),
        _fresh_case("landing place question", "Rani knows the mission landed but not where. Words: where / did / it / land.", "Build the place question.", "Where did it land?", "Where asks for place and did supports land.", "Where did it land", "place question form"),
        _fresh_case("word meaning question", "Rani wants the meaning of Yaan. Words: what / does / Yaan / mean.", "Write the question with punctuation.", "What does Yaan mean?", "What asks for meaning and the question mark closes it.", "What does Yaan mean", "meaning question mark"),
        _fresh_case("mission person", "The card names a scientist, but the name is hidden. Words: who / explained / the mission.", "Form the identity question.", "Who explained the mission?", "Who asks for a person in direct order.", "Who explained mission", "person question"),
        _fresh_case("travel method", "The child asks about how the mission travelled. Words: how / did / the mission / begin its journey.", "Which complete question fits?", "How did the mission begin its journey?", "How asks for method and did comes before the subject.", "How did mission begin", "method helper order"),
        _fresh_case("Moon reason", "Rani wants to know why the Moon mission mattered to the class. Words: why / were / they / excited.", "Write the reason question.", "Why were they excited?", "Why asks for a reason and the sentence ends with a question mark.", "Why were they excited", "reason question form"),
        _fresh_case("photo place", "A photo is shown but its location is missing. Words: where / was / this photo / taken.", "How should it be asked?", "Where was this photo taken?", "Where and was create a clear past place question.", "Where was photo taken", "past place order"),
        _fresh_case("date detail", "Rani wants the day and month of landing. Words: on what date / did / it / land.", "Build one focused question.", "On what date did it land?", "The opening phrase asks for one date and did supports land.", "What date did land", "focused date question"),
        _fresh_case("name parts", "Rani wants both word-part meanings. Words: what / do / Chandra and Yaan / mean.", "Write the complete question.", "What do Chandra and Yaan mean?", "The plural subject takes do and the question mark is present.", "What do words mean", "plural question helper"),
        _fresh_case("rocket model", "A child points to one model and wants its purpose. Words: what / is / this rocket model / for.", "Which question is correct?", "What is this rocket model for?", "What asks for purpose and keeps the full noun phrase together.", "What is model for", "purpose question order"),
        _fresh_case("slipping wheel", "The class wants the reason one rover wheel slips. Words: why / does / the left wheel / slip / in sand.", "Form the complete capitalised question.", "Why does the left wheel slip in sand?", "Why asks for a reason, does precedes the subject, and the question mark closes it.", "Why does wheel slip", "reason helper question"),
        _fresh_case("sensor place", "The temperature sensor is missing from the model. Words: where / is / the temperature sensor / stored.", "Write the focused place question.", "Where is the temperature sensor stored?", "Where asks for the missing place and the full subject stays together.", "Where is sensor stored", "place question order"),
        _fresh_case("fair test method", "Ravi wants the method for comparing two ramps. Words: how / will / we / test / both ramps fairly.", "Build and punctuate Ravi's method question.", "How will we test both ramps fairly?", "How asks for a method, will comes before we, and the line ends with a question mark.", "How will we test ramps", "method helper punctuation"),
    ],
    "mission_event_chain": [
        _fresh_case("mission timeline", "The card says: rocket launch on 14 July, travel from Earth, Moon landing on 23 August, and a report of success.", "Retell the order.", "First launch, next travel, then Moon landing, and finally the success report.", "The dated events and journey words fix the order.", "launch travel land report", "dates guide order"),
        _fresh_case("rover test", "A team charges a rover, places it at a start mark, drives to a crater model, and records the wheel marks.", "Which action is last?", "Recording the wheel marks comes after the rover reaches the model crater.", "The tracks must exist before they can be recorded.", "record wheel marks last", "tracks after travel"),
        _fresh_case("rocket model", "Pupils build a paper rocket, check its fins, place it on a launcher, release it, and measure the flight line.", "Give the safe sequence.", "Build, check, place, release, and then measure the flight.", "Measurement follows the completed model flight.", "build check launch measure", "flight before measure"),
        _fresh_case("signal trial", "The coder writes a stop command, sends it, watches the rover stop, and notes the stopping point.", "What happens between sending and noting?", "The coder watches the rover stop.", "The observed stop supplies the later note.", "watch rover stop", "between send and note"),
        _fresh_case("lander legs", "The class opens the model legs, checks balance, lowers the lander onto a mat, and looks for tipping.", "Why is balance checked before lowering?", "The check prepares the lander before it touches the mat.", "The order prevents testing an unopened or unsteady model.", "check before lower", "prepare before landing"),
        _fresh_case("sample route", "A carrier leaves base, reaches the marked tray, picks up one stone, returns, and places it in a cup.", "Write the route order.", "Leave base, reach the tray, collect the stone, return, and place it in the cup.", "Collection needs arrival, and cup placement follows return.", "leave reach collect return", "arrival before collection"),
        _fresh_case("camera mission", "The camera is tested indoors, raised above a grid, takes one photo, is lowered, and the photo is checked.", "Which event creates the item checked at the end?", "Taking the photo creates the image checked later.", "The image must exist before inspection.", "photo taken before checked", "capture creates image"),
        _fresh_case("balloon card", "A card is attached to a balloon, the knot is checked, the balloon rises, it is pulled down, and the card is read.", "What must happen before reading?", "The balloon must be brought down before the attached card can be read.", "The card remains with the raised balloon until return.", "lower before read", "card attached balloon"),
        _fresh_case("wheel change", "The rover crosses a board, slips in sand, returns to base, receives wider wheels, and repeats the route.", "Place the wheel change correctly.", "The wider wheels are fitted after the first slipping test and before the repeat.", "The problem is seen before the design is changed.", "slip change repeat", "problem before repair"),
        _fresh_case("light sensor", "A sensor is checked in light, moved into a box, records darkness, returns to the desk, and both readings are compared.", "Why is comparison last?", "Both light and dark readings must exist before comparison.", "The final task needs the two earlier records.", "two readings before compare", "light and dark records"),
        _fresh_case("countdown model", "The leader checks the area, counts down from five, releases the model, waits for it to stop, and marks the landing place.", "What follows the countdown?", "The model is released after the countdown.", "The numbered signal prepares the stated launch.", "release after countdown", "signal before launch"),
        _fresh_case("mission note", "Ria reads the task, gathers the materials, tests the model, writes the result, and stores the note in a folder.", "Retell all stages in order.", "Read, gather, test, write the result, and finally store the note.", "The result can be written only after the test.", "read gather test write store", "test before result"),
        _fresh_case("weather balloon model", "The team checks the string, attaches a temperature card, releases the model balloon, pulls it back, and reads the card.", "Retell the weather-balloon mission and explain why reading comes after return.", "First check, next attach, then release, pull back, and finally read the card.", "The attached card must return within reach before the team can read its result.", "check attach release return read", "card returns before reading"),
        _fresh_case("seed rover route", "A rover leaves base, follows the blue line, places one seed cup at the garden mark, photographs it, and returns for charging.", "Order the seed-rover stages and name the task completed before return.", "The rover leaves, follows the line, places the cup, takes a photo, and returns.", "Photographing the placed seed cup completes the field task before charging.", "leave follow place photograph return", "photo before charging"),
        _fresh_case("rescue beacon trial", "Pupils charge a beacon, carry it to the far mat, switch it on, record the visible flash, and bring it back to the desk.", "Write the rescue-beacon chain and explain why recording follows switching on.", "First charge, next carry, then switch on, record the flash, and finally return.", "The flash must appear before pupils can record its visible signal.", "charge carry switch record return", "flash before record"),
    ],
    "mission_words_nouns": [
        _fresh_case("rocket meaning", "A tall vehicle carries the model upward from the launch point. The card names it a rocket.", "Use rocket in a complete meaning sentence.", "A rocket is a vehicle used to begin a journey away from Earth.", "The carrying and upward-start clues explain the word.", "rocket carries from Earth", "upward launch vehicle"),
        _fresh_case("swing blend", "The sentence says, 'Children __ing in the park.' The missing action begins with sw.", "Spell the word.", "The word is swing, beginning with sw.", "Swing keeps both letters and matches the park action.", "swing begins sw", "park action clue"),
        _fresh_case("launch meaning", "The team sends the rocket model upward from the marked pad. The needed word is launch.", "How should launch be used?", "The team will launch the rocket model from the pad.", "The upward starting action gives the meaning.", "launch rocket from pad", "begin upward journey"),
        _fresh_case("stone blend", "The rover passes one __one on the model path. The missing noun names a hard rock piece.", "Which opening blend completes it?", "The word is stone, beginning with st.", "Stone keeps st and fits the hard object.", "stone begins st", "hard rock clue"),
        _fresh_case("space word", "A rocket can travel through space. Complete __ace with the correct blend.", "Give the mission word and spelling clue.", "Space names the area beyond Earth and begins with sp.", "The meaning and both opening letters fit together.", "space beyond Earth", "sp opening blend"),
        _fresh_case("sample meaning", "The rover tray holds one spoonful of sand taken from a larger test bed. The small part will be studied at the desk.", "Which sentence uses sample correctly?", "The rover collected a sand sample for the class to study.", "A sample is a small part taken from a larger amount for checking.", "collected sand sample", "small part for study"),
        _fresh_case("sky spelling", "The mission model rises into the __y above the school field.", "Complete the sky word.", "The word is sky, beginning with sk.", "Sky keeps sk and names the area above.", "sky begins sk", "area above clue"),
        _fresh_case("vehicle and star", "A mission vehicle moves under a card showing one bright __ar. The missing word starts with st.", "Use vehicle and finish the blend word.", "The vehicle moved under a bright star, and star begins with st.", "Vehicle fits the carrier while st completes the night object.", "vehicle under star", "st bright object"),
        _fresh_case("signal and switch", "A light signal tells the rover to stop. The command is sent with a __itch beginning sw.", "Explain signal and complete the gap.", "The signal carries a stop message, and switch begins with sw.", "The flash gives information and both blend letters form switch.", "signal stop message", "switch begins sw"),
        _fresh_case("launch and space", "The class will launch a model toward a card labelled __ace. The missing noun begins sp.", "Write the full idea.", "The class will launch the model toward space, and space begins with sp.", "Launch names the start action and the blend forms the destination word.", "launch toward space", "sp destination word"),
        _fresh_case("land and stone", "The model will land beside a __one on the tray. The rock word begins st.", "Complete the sentence and explain land.", "The model will land beside a stone, and stone begins with st.", "Land means touch down while st forms the rock noun.", "land beside stone", "touch down st word"),
        _fresh_case("rocket and sky", "A rocket rises into the __y. The above-ground word begins with sk.", "Use both mission and blend knowledge.", "The rocket rises into the sky, and sky begins with sk.", "Rocket names the vehicle and sk completes the place word.", "rocket rises sky", "sk above ground"),
        _fresh_case("spark signal", "A tiny __ark appears when the model wire touches the wrong clip. The missing noun begins with sp.", "Complete the blend word and use it in the mission warning.", "The word is spark, beginning with sp; the spark warns the team to disconnect the wire.", "Spark names the tiny flash and the sp blend completes it.", "spark begins sp", "tiny warning flash"),
        _fresh_case("switch control", "The rover stops when Mina presses the __itch on the control box. The missing noun begins with sw.", "Spell the control word and explain its job.", "The word is switch, beginning with sw; the switch sends the stop command.", "Both blend letters and the control action support the word.", "switch begins sw", "sends stop command"),
        _fresh_case("station noun", "The model returns to a charging __ation after the route. The place word begins with st.", "Form the complete mission noun and use it in a sentence.", "The word is station, beginning with st; the rover waited at the charging station.", "Station names the return place and preserves the st opening.", "station begins st", "rover charging place"),
    ],
    "mission_ordinal_order": [
        _fresh_case("five tasks", "The order is check map, close lid, start timer, move rover, record stop. The target is move rover.", "What position is move rover?", "Move rover is the fourth task.", "Three actions appear before it.", "move rover fourth", "three tasks before"),
        _fresh_case("tool row", "From left: brush, scoop, ruler, torch, camera. The target is ruler.", "State its ordinal place.", "The ruler is third from the left.", "Brush and scoop occupy the first two places.", "ruler third left", "two tools before"),
        _fresh_case("mission cards", "The cards read Earth, launch, travel, Moon, landing, report. The target is Moon.", "Which ordinal fits Moon?", "Moon is the fourth card in the row.", "Three cards are listed before Moon.", "Moon fourth card", "three before Moon"),
        _fresh_case("seven buttons", "Buttons are labelled red, blue, green, yellow, white, black, silver. The target is white.", "What is white's position?", "White is the fifth button.", "Four colours occur before white.", "white fifth button", "four colours before"),
        _fresh_case("speaker order", "The speakers are Ana, Bilal, Charu, Deep, and Esha. The target is Deep.", "Write a position sentence.", "Deep is the fourth speaker.", "Three names come first.", "Deep fourth speaker", "three names before"),
        _fresh_case("route stops", "The route visits gate, ramp, flag, sand tray, base. The target is flag.", "Which ordinal names flag?", "The flag is the third stop.", "Gate and ramp are first and second.", "flag third stop", "two stops before"),
        _fresh_case("day row", "The printed row begins Monday, Tuesday, Wednesday, Thursday, Friday. The target is Thursday.", "State the ordinal.", "Thursday is fourth in the row.", "Three named days precede Thursday.", "Thursday fourth", "three days before"),
        _fresh_case("model pieces", "The pieces are body, left wheel, right wheel, camera, flag. The target is camera.", "What position does camera have?", "The camera is the fourth piece listed.", "Body and two wheels come before it.", "camera fourth piece", "three pieces before"),
        _fresh_case("countdown words", "The line reads fifth, fourth, third, second, first. The target is third.", "Where is third in this printed line?", "Third is the third word in the line.", "Fifth and fourth stand before it.", "third word third", "two words before"),
        _fresh_case("sample cups", "From right to left: blue, red, green, white. The target is red.", "Count from the stated side.", "Red is second from the right.", "Blue is first from the right.", "red second right", "blue before red"),
        _fresh_case("launch jobs", "The jobs are clear area, set model, count down, release, measure. The target is release.", "Which ordinal describes release?", "Release is the fourth job.", "Three preparation jobs occur first.", "release fourth job", "three jobs before"),
        _fresh_case("photo set", "Photos A, B, C, D, E, F are in order. The target is E.", "Write E's position.", "Photo E is fifth in the set.", "Four labelled photos stand before E.", "photo E fifth", "four photos before"),
        _fresh_case("seven mission bins", "From left, the bins are maps, wheels, wires, tools, cameras, flags, and notes. The target is cameras.", "State the cameras bin's position in a complete ordered sentence.", "The cameras bin is fifth from the left.", "Maps, wheels, wires, and tools occupy the first four places.", "cameras fifth left", "four bins before"),
        _fresh_case("rover checkpoint line", "The checkpoints are start, bridge, sand, crater, flag, sample tray, and base. The target is flag.", "Which ordinal position belongs to the flag checkpoint?", "The flag is the fifth checkpoint.", "Four named checkpoints appear before the flag.", "flag fifth checkpoint", "four checkpoints before"),
        _fresh_case("launch team row", "The team stands in this order: Asha, Bilal, Chen, Diya, Emon, Farah, and Gita. The target is Farah.", "Write Farah's position without confusing it with the number of team members.", "Farah is sixth in the launch-team row.", "Five people stand before Farah, while seven names give the total quantity.", "Farah sixth row", "five people before"),
    ],
    "mission_report_reason": [
        _fresh_case("loose wheel", "Yesterday a loose wheel shook and the rover left the line. The team tightened it before a second test.", "Write the past report and reason.", "The team tightened the wheel because it shook and moved the rover off line.", "The completed problem directly explains the repair.", "tightened loose wheel", "shook off line"),
        _fresh_case("dim signal", "The first signal was too dim to see across the room. Pupils used a brighter lamp next.", "Why did they change lamps?", "They changed lamps because the first signal was hard to see.", "The visibility problem supports the completed choice.", "changed to brighter lamp", "dim signal hard see"),
        _fresh_case("high ramp", "The model rolled too fast from a high ramp and passed the target. The class lowered the ramp.", "Report the design change.", "The class lowered the ramp because the model passed the target too quickly.", "The earlier fast roll is the reason for lowering.", "lowered ramp", "model passed target"),
        _fresh_case("dusty lens", "Powder covered the lens, and every photo looked cloudy. The team added a clear cover.", "Write why the cover was added.", "The team added a clear cover because powder made the photos cloudy.", "The image problem supports protecting the lens.", "added clear cover", "powder clouded photos"),
        _fresh_case("weak legs", "Two thin legs bent when the lander touched down. Pupils replaced them with thicker legs.", "Use past tense and because.", "Pupils replaced the legs because the thin ones bent during landing.", "Bent shows a completed failure that explains the change.", "replaced bent legs", "thin legs failed"),
        _fresh_case("long route", "The rover used most of its battery on a long path. The coder chose a shorter return route.", "Why was the route changed?", "The coder chose a shorter route because the long path used too much battery.", "The recorded battery use explains the later choice.", "chose shorter route", "long path used battery"),
        _fresh_case("late turn", "A command reached the rover after it passed the flag. The coder moved the turn command earlier.", "Report the reason.", "The coder moved the command earlier because the rover passed the flag before turning.", "The timing error supports the correction.", "moved command earlier", "passed flag first"),
        _fresh_case("heavy carrier", "The carrier moved slowly with six blocks. The class removed two unused blocks.", "Why did the class remove blocks?", "The class removed blocks because the heavy carrier moved too slowly.", "The slow test gives the reason for reducing the load.", "removed two blocks", "heavy carrier slow"),
        _fresh_case("low camera", "The camera pointed too low and missed the top of the grid. The team raised its stand.", "Write the completed report.", "The team raised the stand because the low camera missed part of the grid.", "The missing view supports the height change.", "raised camera stand", "missed grid top"),
        _fresh_case("rough wheel", "A rough wheel caught on every ridge. Pupils fitted a smoother cover before repeating the route.", "What reason supports the cover?", "Pupils fitted a smooth cover because the rough wheel caught on ridges.", "The repeated stopping problem explains the repair.", "fitted smooth cover", "rough wheel caught"),
        _fresh_case("open hatch", "The sample fell out when the hatch stayed open. The team added a simple latch.", "Why was a latch added?", "The team added a latch because the open hatch dropped the sample.", "The lost sample is the shown reason.", "added hatch latch", "sample fell out"),
        _fresh_case("faint mark", "The soft wheel left marks too faint to measure. The class pressed the model with one extra block.", "Report the change and clue.", "The class added one block because the first wheel marks were too faint.", "The hard-to-measure marks explain the extra pressure.", "added one block", "marks too faint"),
        _fresh_case("crooked antenna", "The antenna leaned after the first run and the signal failed at the far mat. The team straightened it before the second run.", "Report the completed antenna change and its reason.", "The team straightened the antenna because the crooked position lost the signal at the far mat.", "The failed distant signal is the recorded evidence for the repair.", "straightened antenna", "crooked signal failed"),
        _fresh_case("slippery ramp", "The rover slid sideways on a smooth ramp and missed the landing box. Pupils taped a rough strip down the centre.", "Use past tense and because to explain the ramp decision.", "Pupils added the rough strip because the rover slid sideways and missed the box.", "The first route result ties the texture change to better control.", "added rough strip", "rover slid missed box"),
        _fresh_case("warm battery", "The battery felt warm after a ten-minute route, and the table showed the rover slowed during the last two minutes. The class shortened the next route.", "Write the past mission report and grounded route reason.", "The class shortened the route because the warm battery and slower final minutes showed strain.", "Both the temperature and timing records support the decision.", "shortened the route", "warm battery slower minutes"),
    ],
}

for _level_spec in SPEC["levels"]:
    _level_spec["fresh_cases"] = FRESH_CASES[_level_spec["level_id"]]


SPEC["assessment_pairs"] = [
    _assessment_pair("reading.paragraph_main_idea", _fresh_case("fact card A", "India sent Chandrayaan-3 toward the Moon. A rocket began the journey, and the mission later landed there.", "State the main idea.", "India's Chandrayaan-3 travelled by rocket and reached the Moon.", "Country, vehicle, mission, and place support one fact summary.", "India mission reached Moon", "rocket began journey"), _fresh_case("fact card B", "Chandra means Moon, Yaan means vehicle, and both parts appear in the name Chandrayaan.", "What idea joins the word facts?", "The name Chandrayaan combines the meanings Moon and vehicle.", "The two meanings are printed as parts of one name.", "Chandrayaan Moon vehicle", "two word parts"), kind="open"),
    _assessment_pair("reading.inference_reason", _fresh_case("rover log", "A model rover log records a battery check at 9:00 and its first movement at 9:05.", "What can you infer about the two events?", "The team checked the battery before the rover began moving.", "The earlier time belongs to preparation and the later time to movement.", "battery check before moving", "nine before nine oh five"), _fresh_case("model room", "Rani sees several rocket models before an adult explains how a mission begins its Moon journey.", "Why are the models useful?", "The models help Rani picture the rocket named in the explanation.", "The objects and later vehicle fact refer to the same idea.", "models show rocket", "help picture vehicle"), kind="open"),
    _assessment_pair("grammar.question_formation", _case("country form", "Words: which country / sent / Chandrayaan-3.", "Which question is correct?", "Which country sent Chandrayaan-3?", "Chandrayaan-3 sent which country.", "which country sent Chandrayaan-3.", "The order and question mark are complete.", "Which country sent", "correct question order"), _case("date form", "Words: when / did / the mission / land.", "Choose the complete question.", "When did the mission land?", "The mission did land when.", "when mission land.", "When, helper, subject, and verb are ordered.", "When did mission land", "date question order"), kind="choice"),
    _assessment_pair("grammar.punctuation_capitalization", _case("Moon capital", "The words form a question: where did chandrayaan-3 land", "Which version is punctuated?", "Where did Chandrayaan-3 land?", "where did chandrayaan-3 land.", "Where did Chandrayaan-3 land.", "The first word and name are capitalised and the question mark closes it.", "Where Chandrayaan land", "capital question mark"), _case("Rani statement", "Words: rani watched the rocket rise", "Which sentence is correct?", "Rani watched the rocket rise.", "rani watched the rocket rise", "Rani watched the rocket rise?", "Rani begins with a capital and the statement ends with a full stop.", "Rani watched rocket", "capital full stop"), kind="choice"),
    _assessment_pair("reading.event_sequence", _case("dated chain", "The card lists launch, travel, Moon landing, and a success report.", "Which order fits?", "Launch, travel, landing, then report.", "Report, landing, launch, then travel.", "Landing before any journey.", "The mission must begin and travel before landing.", "launch travel land report", "journey before landing"), _case("model chain", "The team checks the rocket model, sets it on the launcher, releases it, and measures the flight.", "What happens third?", "The model is released third.", "The flight is measured third.", "The model is checked after release.", "Two preparation steps come before release.", "release third", "after check and set"), kind="choice"),
    _assessment_pair("reading.sentence_comprehension", _case("probe subject", "A red balloon probe carried the temperature card above the classroom floor.", "What carried the temperature card?", "The red balloon probe carried it.", "The classroom floor carried the probe.", "The temperature card carried the balloon.", "The subject before carried names the balloon probe.", "balloon probe carried card", "subject before verb"), _case("lander subject", "The cardboard lander touched the sand tray at noon.", "What touched the sand tray?", "The cardboard lander touched it.", "Noon touched the cardboard.", "The sand tray landed on the craft.", "The named lander is the sentence subject.", "cardboard lander touched tray", "lander is subject"), kind="choice"),
    _assessment_pair("vocab.chapter_word_usage", _case("launch use", "The action is the upward start of a rocket model.", "Which sentence uses launch?", "The class will launch the model from the pad.", "The model will land when it starts upward.", "Launch means the final resting place.", "Upward start gives the meaning.", "launch model from pad", "begin journey"), _case("land use", "The craft touches the target and stops.", "Which sentence uses land?", "The craft will land on the target.", "The craft will launch when it touches down.", "Land means a radio message.", "Touching down supports land.", "land on target", "touch down meaning"), kind="choice"),
    _assessment_pair("vocab.spelling", _case("space gap", "The rocket enters __ace beyond Earth.", "Which spelling completes the word?", "space", "sace", "stace", "Space uses sp and fits beyond Earth.", "space with sp", "beyond Earth"), _case("swing gap", "Children __ing on the playground.", "Which spelling fits?", "swing", "sing", "sping", "Swing uses sw and fits the action.", "swing with sw", "playground action"), kind="choice"),
    _assessment_pair("vocab.attribute_ordering", _case("kit position", "Order: map, battery, camera, sample bag, radio. Target: sample bag.", "Which position sentence is right?", "The sample bag is fourth in the kit order.", "There are fourth sample bags.", "Sample bag fourth order the.", "Three items appear before the sample bag.", "sample bag fourth", "three items before"), _case("task position", "Order: check, count, release, measure, store. Target: measure.", "Choose the ordinal sentence.", "Measure is the fourth task.", "Measure means four tasks total.", "Fourth measure task the.", "Three actions precede measure.", "measure fourth", "three before"), kind="choice"),
    _assessment_pair("grammar.sentence_order", _case("ordinal words", "Words: the flag / is / the third / stop.", "Which sentence is ordered?", "The flag is the third stop.", "Third the flag stop is.", "Is stop flag third.", "Subject, verb, and ordinal phrase are clear.", "flag is third stop", "clear sentence order"), _case("mission words", "Words: a rocket / carried / the mission / from Earth.", "Choose the correct order.", "A rocket carried the mission from Earth.", "The mission from carried rocket Earth.", "Carried Earth a mission rocket.", "The subject comes before action and object.", "rocket carried mission", "subject action object"), kind="choice"),
    _assessment_pair("grammar.tense_usage", _fresh_case("past launch", "Time clue: on 14 July 2023. India launches the mission.", "Report the event in past tense.", "India launched Chandrayaan-3 on 14 July 2023.", "Launched matches the completed dated event.", "India launched mission", "dated past event"), _fresh_case("past landing", "Time clue: on 23 August 2023. The mission lands on the Moon.", "Rewrite with past tense.", "The mission landed on the Moon on 23 August 2023.", "Landed matches the completed date.", "mission landed Moon", "past landing date"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("wide wheel", "A narrow rover wheel spun in sand, so the team fitted a wider cover.", "Explain the change.", "The team fitted a wider cover because the narrow wheel spun in sand.", "The first test problem gives the repair reason.", "fitted wider cover", "narrow wheel spun"), _fresh_case("clear shield", "Dust made every camera image cloudy, and pupils added a clear shield.", "Write why the shield was added.", "Pupils added the shield because dust made the images cloudy.", "The poor image quality supports protecting the lens.", "added clear shield", "dust clouded images"), kind="open"),
    _assessment_pair("reading.paragraph_main_idea", _fresh_case("timeline summary", "One box names India's launch date, another shows travel, and the last gives the Moon landing date.", "What is the whole card about?", "The card summarises Chandrayaan-3 from launch to Moon landing.", "All boxes belong to stages of one mission.", "mission launch to landing", "timeline stages"), _fresh_case("star cart summary", "A club names its small model Starcart. It carries a star card across a Moon map and returns the card to a marked base.", "State the main idea.", "The club uses Starcart to carry a card across a Moon map and back to base.", "The model name, carried card, route, and return all belong to one model mission.", "Starcart carries card", "route returns to base"), kind="open"),
    _assessment_pair("reading.inference_reason", _fresh_case("rocket display", "A classroom display puts a rocket model beside an Earth card and an arrow pointing upward.", "What job does the model probably show?", "It shows the vehicle beginning a journey away from Earth.", "The Earth card and upward arrow support the idea.", "vehicle leaves Earth", "upward arrow rocket"), _fresh_case("landing cheer", "The class cheers when a dated card says the mission reached the Moon.", "Why are they cheering?", "They are pleased that the Moon mission completed its landing.", "The cheer follows the success fact on the card.", "cheer for Moon landing", "success fact before cheer"), kind="open"),
]


_SEMANTIC_OPTION_REPLACEMENTS = {}
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
