"""Deep authored manifest for Class 3 English Chapter 5.

The official chapter was used only to understand structure and exercise
modalities. Runtime passages, prompts, rubrics, and answers are original.
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


CHAPTER_ID = "eng_c3_ch05"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/cesa105.pdf"


SOURCE_ANCHORS = [
    {"anchor_id": f"{CHAPTER_ID}:read:44-48", "section_label": "Let us Read: Toy Counter Voices and Choices", "page_start": 44, "page_end": 48, "source_url": f"{SOURCE_URL}#page=44", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:think:49", "section_label": "Let us Think: Recall, Preference, and Feeling", "page_start": 49, "page_end": 49, "source_url": f"{SOURCE_URL}#page=49", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:learn:49-51", "section_label": "Let us Learn: Describing Words and Plural Forms", "page_start": 49, "page_end": 51, "source_url": f"{SOURCE_URL}#page=49", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:listen:51-52", "section_label": "Let us Listen: Optional Top Poem Recitation", "page_start": 51, "page_end": 52, "source_url": f"{SOURCE_URL}#page=51", "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:write:52-54", "section_label": "Let us Write: Ordered Kite Instructions and Letter Forms", "page_start": 52, "page_end": 54, "source_url": f"{SOURCE_URL}#page=52", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:do:55", "section_label": "Let us Do: Optional Puppet Craft", "page_start": 55, "page_end": 55, "source_url": f"{SOURCE_URL}#page=55", "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
]


CRUNCH_BAR = {
    "toy_workshop_sequence": _crunch(
        [
            (
                "A music box arrived with a stiff handle. The worker brushed dust from the joint, added one drop of oil, turned the handle twice, and heard a clear tune.",
                "The stiff handle was noticed first, cleaning and oiling followed, and two turns tested the repair. The main idea is that careful cleaning restored the music box.",
                ["stiff handle then brushed then oiled then tested", "clear tune came last"],
                ["careful cleaning restored the music box", "repair brought back the tune"],
            ),
            (
                "A puppet kept falling from its stand. The maker measured the base, added a wider cardboard foot, tested three poses, and placed it in the display.",
                "The falling problem came first, the base was measured and widened, and three pose tests came before display. A wider base made the puppet steady.",
                ["falling then measured then widened then tested then displayed", "three pose tests before display"],
                ["wider base made the puppet steady", "measurement guided the repair"],
            ),
            (
                "A block set had a faded age label. The clerk checked the maker's guide, printed a clear label, counted every block, and returned the set to the shelf.",
                "The faded label was checked first, a new label was printed, the blocks were counted, and the set returned last. Clear information made the set ready for a suitable shopper.",
                ["faded label then guide then new label then count then shelf", "returned to shelf last"],
                ["clear information made the set ready", "suitable shopper can use the label"],
            ),
            (
                "A toy crane lifted unevenly because one cord was longer. The repairer matched both cord lengths, tied new knots, lifted a wooden cube, and marked the crane ready.",
                "The uneven lift revealed the long cord, both cords were matched and tied, and a cube lift tested the change. Equal cords made the crane work evenly.",
                ["uneven lift then matched then tied then tested then ready", "cube lift tested the change"],
                ["equal cords made the crane work evenly", "repair fixed uneven lifting"],
            ),
            (
                "A domino case opened when carried. The maker examined its latch, bent the metal tab gently, shook the closed case, and found every tile still inside.",
                "The opening case came first, the latch was examined and adjusted, and a shake test came last. Testing showed that the repaired latch could hold the tiles.",
                ["case opened then latch checked then bent then shake tested", "tiles stayed inside last"],
                ["repaired latch held the tiles", "testing confirmed the repair"],
            ),
        ],
        prompt="Put the workshop events in order and state how the careful action improved the toy.",
        interaction_type="summary",
        ordered=True,
    ),
    "toy_speakers_and_punctuation": _crunch(
        [
            (
                "Draft: will my drum sound softer asked the bear. yes replied ila i tightened the skin gently",
                "The bear asked, 'Will my drum sound softer?' Ila replied, 'Yes, I tightened the skin gently.'",
                ["bear asks first", "Ila replies second"],
                ["Will capital and question mark", "quotes around both lines"],
            ),
            (
                "The wooden horse says that its red wheel is missing. The helper promises to search the parts tray.",
                "The wooden horse said, 'My red wheel is missing.' The helper replied, 'I will search the parts tray.'",
                ["wooden horse speaks first", "helper promises second"],
                ["quotation marks and capitals", "full stops close both lines"],
            ),
            (
                "Draft: please place me upright whispered the doll. the child answered i will use the stand",
                "'Please place me upright,' whispered the doll. The child answered, 'I will use the stand.'",
                ["doll whispers first", "child answers second"],
                ["Please and The capitals", "commas and quotation marks"],
            ),
            (
                "The robot thinks, I hope the new switch fits. The mechanic says, It matches the open space.",
                "The robot thought, 'I hope the new switch fits.' The mechanic said, 'It matches the open space.'",
                ["robot has the first thought", "mechanic speaks second"],
                ["quotes and capitals", "full stops mark both statements"],
            ),
            (
                "Draft: hooray my sail is straight cheered the boat. shall we test it asked the maker",
                "'Hooray, my sail is straight!' cheered the boat. 'Shall we test it?' asked the maker.",
                ["boat cheers first", "maker asks second"],
                ["exclamation mark then question mark", "capitals and quotation marks"],
            ),
        ],
        prompt="Say who owns each line, then rewrite both lines with capitals and dialogue marks.",
        interaction_type="dialogue",
    ),
    "toy_preference_inference": _crunch(
        [
            (
                "Options: picture dominoes, a battery siren, a giant floor train. Need: a quiet matching activity for a small library table and two players.",
                "Choose picture dominoes because two players can match them quietly and the pieces fit on a small library table.",
                ["choose picture dominoes", "two players can match"],
                ["quiet activity", "small library table"],
            ),
            (
                "Options: a washable bath boat, a paper puppet, a cloth puzzle. Need: a toy that can float and be dried after water play.",
                "Choose the washable bath boat because it can float during water play and can be dried afterward.",
                ["choose washable bath boat", "toy can float"],
                ["water play", "can be dried afterward"],
            ),
            (
                "Options: six-piece animal puzzle, one hundred-piece map, metal model kit. Need: a beginner who enjoys animals and completes short tasks.",
                "Choose the six-piece animal puzzle because its animal theme fits the interest and its short puzzle suits a beginner.",
                ["choose six-piece animal puzzle", "animal theme fits"],
                ["short puzzle", "suits a beginner"],
            ),
            (
                "Options: two hand drums, one marble maze, a reading lamp. Need: two cousins who want to make rhythms together without sharing one object.",
                "Choose the two hand drums because each cousin can play an instrument and they can make rhythms together.",
                ["choose two hand drums", "each cousin can play"],
                ["make rhythms together", "two separate instruments"],
            ),
            (
                "Options: a folding chess set, a tall dollhouse, an electric track. Need: a thinking game for a bus trip with no power socket.",
                "Choose the folding chess set because it supports a thinking game, travels in little space, and needs no power socket.",
                ["choose folding chess set", "supports a thinking game"],
                ["bus trip", "needs no power"],
            ),
        ],
        prompt="Choose the best toy and give two card facts that make it suitable.",
    ),
    "describing_toys_in_context": _crunch(
        [
            (
                "Card word: springy means able to bend and return to shape. Facts: a toy snake bends around a peg and straightens again.",
                "Springy is a describing word for the snake. The springy toy snake bent around the peg and returned to its straight shape.",
                ["springy is a describing word", "bends and returns to shape"],
                ["springy toy snake bent", "returned to straight shape"],
            ),
            (
                "Card word: faded means having lost some colour. Facts: an old red wagon now looks pale near its handle.",
                "Faded describes the wagon's colour. The faded red wagon looked pale near its well-used handle.",
                ["faded describes colour", "lost some colour"],
                ["faded red wagon looked pale", "near its handle"],
            ),
            (
                "Card word: miniature means much smaller than the usual size. Facts: a tiny kitchen fits inside a toy case.",
                "Miniature is a describing word meaning very small. The miniature kitchen fitted neatly inside the toy case.",
                ["miniature is a describing word", "much smaller than usual"],
                ["miniature kitchen fitted", "inside the toy case"],
            ),
            (
                "Card word: rattled means made a series of short hard sounds. Facts: loose beads moved inside a wooden cube.",
                "Rattled is the action word for the short sounds. The loose beads rattled inside the wooden cube when it moved.",
                ["rattled is the action word", "short hard sounds"],
                ["loose beads rattled", "inside the wooden cube"],
            ),
            (
                "Card word: spotless means completely clean. Facts: the repaired tea set has no dust or marks before display.",
                "Spotless is a describing word meaning completely clean. The spotless toy tea set had no dust or marks when it reached the display.",
                ["spotless is a describing word", "completely clean"],
                ["spotless toy tea set", "no dust or marks"],
            ),
        ],
        prompt="Explain the word's job and meaning, then use it in one complete new sentence.",
    ),
    "plural_and_compound_building": _crunch(
        [
            (
                "Base noun: watch. Needed meaning: three toy watches.",
                "The plural is watches. Watch ends in ch, so the plural adds es while keeping the whole base word.",
                ["watches", "three toy watches"],
                ["ends in ch", "adds es"],
            ),
            (
                "Bases: wheel + barrow. Meaning clue: a small cart with one wheel and handles.",
                "Wheelbarrow joins wheel and barrow. It names a barrow moved on a wheel by holding its handles.",
                ["wheelbarrow", "wheel and barrow"],
                ["barrow moved on a wheel", "handles are used"],
            ),
            (
                "Base noun: shelf. Needed meaning: several shelves holding games.",
                "The plural is shelves. Shelf changes f to v and adds es when it names more than one shelf.",
                ["shelves", "several shelves"],
                ["f changes to v", "adds es"],
            ),
            (
                "Bases: rain + coat. Meaning clue: clothing worn to keep rain off the body.",
                "Raincoat joins rain and coat. It means a coat worn to keep rain off the person wearing it.",
                ["raincoat", "rain and coat"],
                ["coat keeps rain off", "both bases explain the clothing"],
            ),
            (
                "Base noun: key. Needed meaning: four keys for wind-up toys.",
                "The plural is keys. Key keeps its y after a vowel and adds s to show more than one.",
                ["keys", "four keys"],
                ["keeps the y", "adds s"],
            ),
        ],
        prompt="Write the correct plural or compound and explain the spelling or the two word meanings.",
        interaction_type="short_text",
    ),
    "toy_process_explanations": _crunch(
        [
            (
                "Facts: wipe the wheel axle; add fresh oil; both actions reduce rough movement. Use and.",
                "Wipe the wheel axle and add fresh oil. The two actions reduce rough movement before the wheel is tested.",
                ["and joins wipe and add", "wipe axle and add oil"],
                ["reduce rough movement", "before wheel test"],
            ),
            (
                "Facts: the new cloth matches the doll; its edge is still loose; another seam is needed. Use but.",
                "The new cloth matches the doll, but its edge is still loose. Add another seam before returning the doll.",
                ["but shows contrast", "matches but edge is loose"],
                ["add another seam", "before returning doll"],
            ),
            (
                "Facts: test the toy torch in a dim corner; weak light is easier to notice there. Use because.",
                "Test the toy torch in a dim corner because weak light is easier to notice there.",
                ["because gives the reason", "weak light is easier to notice"],
                ["test the toy torch", "in a dim corner"],
            ),
            (
                "Facts: number the puzzle bags; place matching pieces inside; numbering helps owners find the right set. Use and and because.",
                "Number the puzzle bags and place matching pieces inside because the numbers help owners find the right set.",
                ["and joins number and place", "because gives the purpose"],
                ["owners find the right set", "matching pieces inside"],
            ),
            (
                "Facts: a new spring fits the robot; the arm still stops halfway; inspect the joint. Use but.",
                "The new spring fits the robot, but the arm still stops halfway. Inspect the joint before another full test.",
                ["but shows the remaining problem", "spring fits but arm stops"],
                ["inspect the joint", "before another test"],
            ),
        ],
        prompt="Join the facts with the right connector and give the short purpose shown on the card.",
        interaction_type="short_text",
    ),
}


LEVELS = [
    _make_level(
        level_id="toy_workshop_sequence",
        title="Track a toy from problem to new home",
        focus="sequence a toy-workshop narrative and state its main idea",
        outcome="Order arrival, inspection, repair or choice, and result, then state how careful attention matched a toy with a real need.",
        skill_ids=["reading.event_sequence", "reading.paragraph_main_idea"],
        choice_skill_ids=["reading.event_sequence"],
        episode_kind="comprehension_studio",
        source_anchor_ids=[f"{CHAPTER_ID}:read:44-48", f"{CHAPTER_ID}:think:49"],
        principle="Follow the toy's condition, the clue that guides a decision, the action taken, and the final use; the main idea connects care or choice to the result.",
        connect={"teaching_block": "A workshop story can follow an object rather than a person. Track where the toy arrives, what is noticed, what changes, and who eventually uses it.", "passage": "A wooden cart arrived with one loose wheel. The maker inspected the axle, fitted a new peg, tested the cart, and placed it in the ready basket.", "prompt": "Trace the cart's condition, repair, test, and result before stating the central idea."},
        choice_prompt="Which event comes first, second, or last as named in the card?",
        response_prompt="order the key events and state the main idea about careful repair or choice.",
        rubric_descriptions=["Orders the arrival, clue or inspection, action, and result correctly.", "States a main idea connecting careful attention with the useful outcome."],
        examples=[
            _q("A cloth doll arrived with a torn pocket, the tailor stitched it, and a child collected it after school.", "A child collected the repaired doll.", ["The doll arrived with a tear.", "The tailor stitched the pocket.", "The child tore the pocket after collection."], prompt="What happened last in the toy story?"),
            _q("First, a customer asked for a quiet travel toy. Next, the helper compared two choices. Finally, the customer chose a magnetic puzzle.", "The helper compared two choices.", ["The customer asked first.", "The puzzle was chosen last.", "The helper closed the shop before listening."], prompt="Which event happened second?"),
            _r("A spinning top wobbled during a test. The maker shortened its uneven peg, tested it again, and placed the steady top in a gift box.", "The top wobbled first, its peg was shortened next, and a successful second test came before boxing. The main idea is that testing and a precise repair made the toy ready to give.", [["wobbled", "peg shortened", "tested again", "boxed"], ["testing and precise repair", "ready to give"]], ordered=True),
            _r("A parent needed a toy for a toddler who likes stacking. The clerk read age labels, found large smooth blocks, and checked that no small parts were included.", "The need was identified, labels were read, safe blocks were selected, and parts were checked. The passage shows careful information helping match a suitable toy to a young child.", [["need", "labels", "blocks selected", "parts checked"], ["careful information", "suitable toy"]], ordered=True),
            _r("A toy bus reached the repair table without a door. A craft worker measured the opening, cut a light wooden piece, attached it, and tested the hinge.", "The missing door was noticed, measured, replaced, and tested in that order. The central idea is that measured steps restored a toy bus to working condition.", [["noticed", "measured", "replaced", "tested"], ["measured steps", "restored bus"]], ordered=True),
            _r("Two children wanted a shared rainy-day activity. They compared a noisy racing toy with a four-player board game and chose the game everyone could join.", "The children named a shared need, compared two toys, and chose the inclusive game. The main idea is that considering all players led to a better group choice.", [["shared need", "compared", "chose"], ["all players", "better group choice"]], ordered=True),
            _r("A stuffed bear had a loose button. The repairer removed the button, embroidered a soft eye, checked every seam, and returned the bear safely.", "The loose button was removed, a soft eye was added, seams were checked, and the bear was returned. The passage shows a repair changing a risky part into a safer feature.", [["button removed", "soft eye added", "seams checked", "returned"], ["risky to safer", "careful repair"]], ordered=True),
            _r("A puzzle box lacked three pieces. The shop checked its spare tray, matched colours and edges, added the pieces, and completed one test picture.", "The missing pieces were identified, matched, added, and tested. The main idea is that systematic matching made an incomplete puzzle useful again.", [["identified", "matched", "added", "tested"], ["systematic matching", "useful again"]], ordered=True),
            _r("A wind-up bird moved in circles instead of straight ahead. The maker cleaned one wheel, aligned both wheels, and confirmed a straight test path.", "The faulty path came first, cleaning and alignment followed, and the straight test confirmed the repair. The central idea is that observing movement helped locate and correct the problem.", [["faulty path", "cleaned", "aligned", "straight test"], ["observing movement", "correct problem"]], ordered=True),
            _q("A helper read the age card, checked the parts, and wrapped the chosen toy.", "The helper checked the parts.", ["The age card was read after wrapping.", "The toy was hidden before checking.", "The customer repaired the shelf."], prompt="What happened immediately before wrapping?"),
            _r("A fabric kite returned with a split tail. The maker compared both sides, sewed a matching strip, tested the balance in a fan breeze, and folded it neatly.", "The split was examined, a matching strip was sewn, balance was tested, and the kite was folded. The main idea is that balanced repair returned the kite to a usable condition.", [["examined", "sewn", "balance tested", "folded"], ["balanced repair", "usable condition"]], ordered=True),
            _q("First, the clerk listened to the child's interests. Then she showed three choices. Last, the child selected a construction set.", "The clerk showed three choices.", ["The child selected first.", "The clerk ignored the interests.", "The set was returned before viewing."], prompt="Which action happened second?"),
            _r("A train set stopped at one track joint. The worker found a raised connector, pressed it flat, ran the train twice, and labelled the set ready.", "The stop revealed the problem, the connector was flattened, two tests followed, and the set was labelled ready. The passage shows repeated testing confirming a simple track repair.", [["stop", "flattened", "tested twice", "ready"], ["repeated testing", "confirming repair"]], ordered=True),
            _r("A family wanted one toy for a long journey. The assistant asked about space, showed a compact card game, explained its rules, and packed it in a small pouch.", "Space needs were discussed, a compact game was shown, rules were explained, and it was packed. The main idea is that asking about use helped select a practical travel toy.", [["space need", "game shown", "rules explained", "packed"], ["asking about use", "practical travel toy"]], ordered=True),
        ],
        crunch_bar=CRUNCH_BAR["toy_workshop_sequence"],
        misconception="The learner lists shoppers or toy names without following one problem-to-result chain, or states that buying is the main idea when the card focuses on repair, safety, or matching a need.",
        remediation="Follow one toy through arrive-check-act-result order, then complete 'Careful ___ helped ___ so that ___'.",
    ),
    _make_level(
        level_id="toy_speakers_and_punctuation",
        title="Track toy voices and mark dialogue",
        focus="identify speakers of spoken or thought lines and use capitals and dialogue punctuation",
        outcome="Use reporting clauses and the meaning of each reply to identify speakers, then repair quotation marks, capitals, commas, and end marks in a short exchange.",
        skill_ids=["reading.dialogue_attribution", "grammar.punctuation_capitalization"],
        choice_skill_ids=["reading.dialogue_attribution"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:read:44-48"],
        principle="A reporting clause names the voice, while punctuation separates that voice from narration and shows whether the line asks, tells, or exclaims.",
        connect={"teaching_block": "Toy stories may include speech and private thoughts. Readers must not assign an unspoken thought to another character, and writers must mark each line clearly.", "passage": "'My wheel is steady now,' said the cart. The top thought, I hope my peg is checked next. Only the first line is spoken aloud.", "prompt": "Separate the cart's speech, the top's private thought, and the punctuation signals."},
        choice_prompt="Who says or thinks the named line?",
        response_prompt="identify the speaker of every line and rewrite the exchange with correct capitals and punctuation.",
        rubric_descriptions=["Identifies the correct speaker for each line or thought using reporting and response clues.", "Uses capitals, quotation marks, reporting punctuation, and end marks correctly."],
        examples=[
            _q("'Please test my bell,' the toy bicycle asked. 'I will check it now,' the mechanic replied.", "the mechanic says the second line", ["the bicycle says both lines", "the bell replies", "a customer says the first line"]),
            _q("The puzzle thought, I hope someone enjoys solving me. The clerk said, 'This one has forty pieces.'", "the puzzle has the private thought", ["the clerk thinks both lines", "forty pieces speak", "a customer says the thought"]),
            _r("Draft: my door opens smoothly said the toy bus. the worker replied shall i test the wheels too", "'My door opens smoothly,' said the toy bus. The worker replied, 'Shall I test the wheels too?'", [["bus says first", "worker replies second"], ["quotation marks", "My and The capitals", "question mark"]], interaction_type="dialogue"),
            _r("Draft: where is my red scarf asked the doll. it is in the repair basket answered the bear", "'Where is my red scarf?' asked the doll. 'It is in the repair basket,' answered the bear.", [["doll asks", "bear answers"], ["Where capital", "question mark", "quotation marks"]], interaction_type="dialogue"),
            _r("Line 1 belongs to the top: I can spin steadily now. Line 2 belongs to the maker: Let us pack you carefully.", "The top said, 'I can spin steadily now.' The maker replied, 'Let us pack you carefully.'", [["top said first", "maker replied"], ["quotation marks", "capitals", "full stops"]], interaction_type="dialogue"),
            _r("Draft: the train asked is the track flat. yes answered the worker i checked every joint", "The train asked, 'Is the track flat?' 'Yes,' answered the worker, 'I checked every joint.'", [["train asks", "worker answers"], ["Is capital", "question mark", "commas and quotes"]], interaction_type="dialogue"),
            _r("The toy rabbit whispers that its ear is loose. The tailor promises a soft repair.", "The rabbit whispered, 'My ear is loose.' The tailor replied, 'I will stitch it with soft thread.'", [["rabbit whispers", "tailor replies"], ["quotation marks", "capitals", "full stops"]], interaction_type="dialogue"),
            _r("Draft: wow my lights work exclaimed the bus. the helper said please switch them off before packing", "'Wow, my lights work!' exclaimed the bus. The helper said, 'Please switch them off before packing.'", [["bus exclaims", "helper instructs"], ["exclamation mark", "comma", "quotation marks"]], interaction_type="dialogue"),
            _r("The board game asks whether all its counters are present. The clerk answers that there are sixteen.", "The board game asked, 'Are all my counters present?' The clerk replied, 'Yes, there are sixteen.'", [["game asks", "clerk replies"], ["question mark", "sixteen", "quotation marks"]], interaction_type="dialogue"),
            _q("'I need a new string,' said the kite. 'The blue string will fit,' thought the maker.", "the maker has the second thought", ["the kite says both lines", "the string thinks", "a shopper says the first line"]),
            _r("Draft: can you mend my pocket asked the doll. of course said the tailor", "'Can you mend my pocket?' asked the doll. 'Of course,' said the tailor.", [["doll asks", "tailor answers"], ["Can capital", "question mark", "quotes"]], interaction_type="dialogue"),
            _q("The robot thought, I hope my battery lasts. A child said, 'I will switch you off after play.'", "the child speaks the quoted line", ["the robot speaks both lines", "the battery answers", "the child has the first thought"]),
            _r("The ball says it is ready to roll. The cart asks it to wait for the clear path.", "The ball said, 'I am ready to roll.' The cart replied, 'Please wait until the path is clear.'", [["ball says", "cart replies"], ["quotation marks", "Please capital", "full stops"]], interaction_type="dialogue"),
            _r("Draft: thank you for fixing me said the bear. you are welcome replied nora", "'Thank you for fixing me,' said the bear. 'You are welcome,' replied Nora.", [["bear thanks", "Nora replies"], ["quotation marks", "Nora capital", "commas"]], interaction_type="dialogue"),
        ],
        crunch_bar=CRUNCH_BAR["toy_speakers_and_punctuation"],
        misconception="The learner treats thoughts as spoken dialogue, links a reply to the nearest noun instead of the reporting verb, or adds quotation marks without capitals and meaningful end punctuation.",
        remediation="Decide whether each line is said or thought and identify its speaker, then rebuild spoken lines with opening quote, capital, content, end mark, closing quote, and reporting clause.",
    ),
    _make_level(
        level_id="toy_preference_inference",
        title="Infer preferences and explain fair choices",
        focus="infer interests from evidence and write reasons for suitable toy choices",
        outcome="Infer what a person values from actions or constraints and justify a suitable, inclusive, or safe choice using the supplied facts.",
        skill_ids=["reading.inference_reason", "writing.reason_answer"],
        choice_skill_ids=["reading.inference_reason"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:think:49", f"{CHAPTER_ID}:read:44-48"],
        principle="Preference evidence comes from repeated interests, age, space, players, and purpose; the best reason links the choice to those facts rather than calling a toy simply fun.",
        connect={"teaching_block": "A shopper may not name a toy directly. A helper can infer a suitable category from what the toy must allow and what limits the setting creates.", "passage": "The child enjoys building, has a small travel bag, and wants an activity that can be used without batteries.", "prompt": "Combine the building interest, size limit, and no-battery need before recommending a toy type."},
        choice_prompt="Which preference or need is best supported?",
        response_prompt="choose a suitable option and justify it with at least two supplied facts.",
        rubric_descriptions=["Chooses a suitable, inclusive, or safe toy or response.", "Uses at least two relevant preference, age, space, player, or safety facts as the reason."],
        examples=[
            _q("A child repeatedly builds bridges from blocks and asks how wheels turn.", "The child likely enjoys construction and moving parts.", ["The child dislikes making objects.", "The child wants only a silent book.", "The child is afraid of every wheel."]),
            _q("Two cousins ask for one activity they can play together during a train ride.", "They need a compact game for at least two players.", ["They need two large outdoor swings.", "They want an activity for one person only.", "They need a game that cannot travel."]),
            _r("Options: a noisy battery drum, a compact magnetic puzzle, a large outdoor hoop. Need: quiet solo activity for a waiting room.", "Choose the compact magnetic puzzle because it is quiet, suits one player, and fits a waiting-room space.", [["choose magnetic puzzle", "compact puzzle"], ["quiet", "one player", "waiting room"]]),
            _r("Options: small marbles, large soft blocks, a complex card deck. Need: toy for a two-year-old who likes stacking; avoid tiny parts.", "Choose the large soft blocks because they support stacking and avoid the tiny parts that make marbles unsuitable for the young child.", [["choose large soft blocks", "stacking"], ["two-year-old", "avoid tiny parts"]]),
            _r("Options: four-player board game, single remote car, one-person puzzle. Need: shared activity for four siblings.", "Choose the four-player board game because all four siblings can take part in the same activity.", [["choose four-player game", "board game"], ["all four siblings", "shared activity"]]),
            _r("Options: paint kit, washable stamp set, permanent marker set. Need: colour activity at a rented table where marks must clean easily.", "Choose the washable stamp set because it provides colour play and can be cleaned from the rented table more safely than permanent markers.", [["choose washable stamps", "colour play"], ["clean easily", "rented table"]]),
            _r("Options: delicate shelf model, sturdy pull cart, glass decoration. Need: active toy for a child who enjoys moving objects outdoors.", "Choose the sturdy pull cart because it is made for active movement outdoors and is less delicate than the shelf model or glass item.", [["choose sturdy pull cart", "active movement"], ["outdoors", "less delicate"]]),
            _r("Options: word cards, picture matching game, advanced rulebook. Need: a beginner who recognises pictures but reads only a few words.", "Choose the picture matching game because the learner can use recognised images without depending on long written rules.", [["choose picture matching", "recognised images"], ["beginner", "few words"]]),
            _r("Options: one large kite, two small hand puzzles, a loud horn. Need: two children sharing a small indoor room.", "Choose the two hand puzzles because each child can participate and the toys fit a small indoor room without a loud horn.", [["choose two hand puzzles", "each child"], ["small indoor room", "not loud"]]),
            _q("A child checks every instruction card and enjoys solving clues before touching the pieces.", "The child likely enjoys puzzles with clear rules.", ["The child dislikes all instructions.", "The child wants only running games.", "The child cannot look at clues."]),
            _r("Options: solar model kit, battery race car, plush pillow. Need: a curious child who asks about sunlight and wants to assemble parts.", "Choose the solar model kit because it connects the child's sunlight questions with hands-on assembly.", [["choose solar model kit", "assemble parts"], ["asks about sunlight", "curious child"]]),
            _q("A family asks whether a game can include a grandparent and two children at the same table.", "They value an accessible three-person table activity.", ["They need a one-player outdoor race.", "They want no one at the table.", "They require a game with tiny unreadable cards."]),
            _r("Options: soft hand puppet, sharp-edged metal model, tiny bead kit. Need: safe pretend play for a young child with adult supervision.", "Choose the soft hand puppet because it supports pretend play and avoids the sharp edges and tiny pieces in the other options.", [["choose soft puppet", "pretend play"], ["avoids sharp edges", "avoids tiny pieces"]]),
            _r("Options: reusable construction set, single-use paper surprise, electronic toy with no charger. Need: durable toy that can create many designs.", "Choose the reusable construction set because its pieces can be rearranged into many designs and used repeatedly.", [["choose construction set", "many designs"], ["reusable", "used repeatedly"]]),
        ],
        crunch_bar=CRUNCH_BAR["toy_preference_inference"],
        misconception="The learner recommends a favourite toy without using the user's age, interests, space, number of players, or safety constraints, or infers a preference from one unrelated detail.",
        remediation="Find the want, user, place, and limit facts, remove options that break a limit, and justify the remaining choice with two card facts.",
    ),
    _make_level(
        level_id="describing_toys_in_context",
        title="Choose precise toy descriptions",
        focus="classify nouns, verbs, and adjectives and use chapter vocabulary accurately",
        outcome="Identify how a describing word changes a toy noun and use a supplied texture, movement, condition, or feeling word in a fresh complete sentence.",
        skill_ids=["grammar.noun_verb_adjective", "vocab.chapter_word_usage"],
        choice_skill_ids=["grammar.noun_verb_adjective"],
        episode_kind="meaning_encounter",
        source_anchor_ids=[f"{CHAPTER_ID}:learn:49-51", f"{CHAPTER_ID}:read:44-48"],
        principle="An adjective should name a useful quality, while accurate vocabulary use preserves the word's context meaning in a new toy or everyday sentence.",
        connect={"teaching_block": "A precise description can identify material, size, condition, colour, or feeling. The noun tells what; the adjective narrows which kind; the verb tells what happens.", "passage": "The sturdy wooden cart rolls smoothly. Cart is a noun, sturdy and wooden describe it, and rolls is the action.", "prompt": "Separate object, useful qualities, and movement before transferring one word."},
        choice_prompt="Which word performs the named grammar or description job?",
        response_prompt="classify the target words and use the supplied chapter word accurately in a fresh complete sentence.",
        rubric_descriptions=["Correctly identifies or uses the toy noun, action verb, and precise adjective.", "Uses the target chapter word in a fresh complete sentence with the same meaning."],
        examples=[
            _q("The colourful puppet waves from the shelf. Which word describes puppet?", "colourful", ["puppet", "waves", "shelf"]),
            _q("A tiny bell rings inside the toy cart. Which word is the verb?", "rings", ["tiny", "bell", "cart"]),
            _r("Card word: sturdy means strong enough for regular use. Sentence facts: a block tower remains standing after three tests.", "Sturdy is an adjective describing strength. The sturdy block tower remained standing after three tests.", [["sturdy adjective", "describes strength"], ["sturdy block tower", "remained standing"]]),
            _r("Card word: delicate means easily damaged. Sentence facts: a thin paper model needs a safe shelf.", "Delicate is an adjective describing the model. The delicate paper model needs a safe shelf because it is easily damaged.", [["delicate adjective", "easily damaged"], ["delicate paper model", "safe shelf"]]),
            _r("Card word: eager means strongly interested and ready. Facts: the children wait at the counter for the repaired train.", "Eager describes the children's feeling. The eager children waited at the counter for the repaired train.", [["eager describes feeling", "interested and ready"], ["eager children waited", "repaired train"]]),
            _r("Card word: polished means made smooth and shiny. Facts: the maker rubs a wooden top before display.", "Polished describes the top's finished condition. The maker displayed the polished wooden top after rubbing it smooth.", [["polished describes condition", "smooth and shiny"], ["polished wooden top", "displayed"]]),
            _r("Card word: flexible means able to bend without breaking. Facts: a soft toy arm bends during play.", "Flexible is an adjective describing the arm. The flexible toy arm bent during play without breaking.", [["flexible adjective", "bend without breaking"], ["flexible toy arm", "bent during play"]]),
            _r("Card word: compact means small enough to fit limited space. Facts: a card game fits one travel pouch.", "Compact describes the game's small practical size. The compact card game fitted inside one travel pouch.", [["compact describes size", "limited space"], ["compact card game", "travel pouch"]]),
            _r("Card word: displayed means placed where people can see it. Facts: the repaired kite hangs near the counter.", "Displayed is the action verb meaning placed for viewing. The shop displayed the repaired kite near the counter.", [["displayed action verb", "placed for viewing"], ["displayed repaired kite", "near counter"]]),
            _q("The smooth marble rolls across the tray. Which word is the noun naming the moving object?", "marble", ["smooth", "rolls", "tray"]),
            _r("Card word: cheerful means noticeably happy. Facts: Nira smiles while opening a gifted puzzle.", "Cheerful is an adjective for Nira's happy mood. Cheerful Nira smiled as she opened the gifted puzzle.", [["cheerful adjective", "happy mood"], ["Cheerful Nira smiled", "opened puzzle"]]),
            _q("A repaired robot marches steadily. Which word is the action verb?", "marches", ["repaired", "robot", "steadily"]),
            _r("Card word: balanced means steady because weight is even. Facts: a mobile hangs level after two pieces move.", "Balanced describes the mobile's steady condition. The balanced mobile hung level after the pieces were adjusted.", [["balanced describes condition", "weight even"], ["balanced mobile", "hung level"]]),
            _r("Card word: suitable means right for a need. Facts: large blocks are chosen for a young stacker.", "Suitable is an adjective meaning right for the user's need. The large blocks were suitable for the young child who enjoyed stacking.", [["suitable adjective", "right for need"], ["blocks were suitable", "young child stacking"]]),
        ],
        crunch_bar=CRUNCH_BAR["describing_toys_in_context"],
        misconception="The learner calls every toy word a naming word, chooses a vague adjective such as nice, or uses a new vocabulary word in a sentence that contradicts its supplied meaning.",
        remediation="Find the noun, verb, and description, replace vague words with the card word, and substitute the definition into the new sentence to test meaning.",
    ),
    _make_level(
        level_id="plural_and_compound_building",
        title="Spell plurals and build toy compounds",
        focus="produce standard plural spellings and explain compound words",
        outcome="Choose or write plural forms using s or es and form a compound whose meaning reflects both supplied base words.",
        skill_ids=["vocab.spelling", "vocab.word_formation"],
        choice_skill_ids=["vocab.spelling"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:learn:49-51"],
        principle="Plural spelling depends on the word ending, while compound formation keeps two complete bases and a meaning contribution from each.",
        connect={"teaching_block": "Many nouns add s, while endings such as s, sh, ch, or x often take es. Compounds follow a different process by joining complete base words.", "passage": "One cart becomes two carts; one brush becomes two brushes. Toybox joins toy and box to name a box for toys.", "prompt": "Compare the plural endings, then split the compound and explain both bases."},
        choice_prompt="Which spelling or compound is correctly formed?",
        response_prompt="write the correct form and explain the ending rule or both compound bases.",
        rubric_descriptions=["Produces the standard plural or compound spelling from the supplied word parts.", "Explains the ending choice or meaning contribution of both bases."],
        examples=[
            _q("Word card: Write the plural form of the noun train.", "trains", ["traines", "trainss", "trainies"]),
            _q("Word card: One brush becomes several of these objects.", "brushes", ["brushs", "brushies", "brushess"]),
            _r("Base noun: box. Needed meaning: more than one box.", "The plural is boxes. Box ends in x, so es is added for the plural.", [["boxes", "standard plural"], ["ends in x", "add es"]]),
            _r("Bases: toy + shop. Meaning clue: a shop that sells toys.", "Toyshop combines toy and shop and means a shop where toys are sold.", [["toyshop", "toy + shop"], ["shop where toys are sold", "both bases"]]),
            _r("Base noun: doll. Needed meaning: four of them.", "The plural is dolls. Doll takes s because it does not need the es ending used after sounds such as sh or x.", [["dolls", "standard plural"], ["add s", "not es ending"]]),
            _r("Bases: board + game. Meaning clue: a game played with pieces or cards on a board.", "Board game combines board and game and names a game organised around a playing board.", [["board game", "board + game"], ["game with playing board", "both bases"]]),
            _r("The travel shelf has one cloth pouch. Four teams each need a pouch for their counters.", "The plural is pouches. Pouch ends in ch, so es is added for the four team pouches.", [["pouches", "standard plural"], ["ends in ch", "add es"]]),
            _r("Bases: hand + puppet. Meaning clue: a puppet moved by a hand inside it.", "Hand puppet combines hand and puppet and means a puppet controlled by a hand.", [["Hand puppet combines hand and puppet"], ["means a puppet controlled by a hand"]]),
            _r("One glass marble rests in the game tray. Ria adds five more glass pieces for the next round.", "The plural is marbles. Marble takes s to show more than one glass marble in the tray.", [["marbles", "standard plural"], ["add s", "more than one"]]),
            _q("Word card: Change the singular noun bus to its plural form.", "buses", ["buss", "bussies", "buseses"]),
            _r("Bases: wind + up. Meaning clue: a toy mechanism prepared by turning a key or knob.", "Wind-up joins wind and up to describe a toy prepared by winding its mechanism.", [["wind-up", "wind + up"], ["toy prepared by winding", "mechanism"]]),
            _q("Word card: More than one spinning top needs a plural noun.", "tops", ["topes", "topps", "topies"]),
            _r("Base noun: class. Needed meaning: several classes.", "The plural is classes. Class ends in s, so es is added.", [["classes", "standard plural"], ["ends in s", "add es"]]),
            _r("Bases: puzzle + box. Meaning clue: a box containing or forming a puzzle.", "Puzzle box combines puzzle and box and means a box used for a puzzle or designed as one.", [["puzzle box", "puzzle + box"], ["box used for puzzle", "both bases"]]),
        ],
        crunch_bar=CRUNCH_BAR["plural_and_compound_building"],
        misconception="The learner adds es to every plural, drops letters from the base, or joins compound words while explaining only the first word's meaning.",
        remediation="Check the final sound or letters, choose s or es, and recheck the full base spelling; for compounds, separate the base words and state what each adds.",
    ),
    _make_level(
        level_id="toy_process_explanations",
        title="Connect process steps in short answers",
        focus="use because, and, and but while writing concise process explanations",
        outcome="Join visible process facts with the connector that shows addition, contrast, or reason and answer a transfer question in one or two complete sentences.",
        skill_ids=["grammar.connectors_because_and_but", "writing.short_answer"],
        choice_skill_ids=["grammar.connectors_because_and_but"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:write:52-54"],
        principle="And links steps, but marks a problem or limit, and because explains why a step matters; a short answer should name the action and its supplied purpose.",
        connect={"teaching_block": "Visible text instructions can support language learning without requiring the learner to make an object. Focus on how one step relates to the next and why checks matter.", "passage": "Fold the card and press the edge, but do not attach the string yet because the balance must be checked first.", "prompt": "Separate the added action, timing contrast, and reason from the printed instruction."},
        choice_prompt="Which connector expresses the relationship in the process card?",
        response_prompt="join the steps correctly and give a concise reason using only the visible process facts.",
        rubric_descriptions=["Uses and, but, or because to express the supplied relationship accurately.", "Writes a concise complete answer naming the action and its relevant purpose or result."],
        examples=[
            _q("The maker tested the wheels ___ one wheel still wobbled.", "but", ["because", "and without contrast", "so why"]),
            _q("The clerk counted the pieces ___ closed the box.", "and", ["but", "because without reason", "although why"]),
            _r("Facts: press the sticker firmly; loose edges collect dust. Use because and explain the purpose.", "Press the sticker firmly because loose edges can collect dust. This keeps the label flat and readable.", [["because", "loose edges collect dust"], ["keeps label flat", "readable"]]),
            _r("Facts: fold the cloth; place it in the box; both actions prepare safe packing. Use and.", "Fold the cloth and place it in the box. These two steps prepare the toy for safe packing.", [["fold and place", "and connector"], ["safe packing", "prepare toy"]]),
            _r("Facts: the first wheel turns; the second wheel sticks; testing must continue. Use but.", "The first wheel turns, but the second wheel sticks. The maker should continue testing before the toy is packed.", [["but contrast", "turns versus sticks"], ["continue testing", "before packing"]]),
            _r("Facts: write the owner's number; attach the tag; the item can be returned if lost. Use and and because.", "Write the owner's number and attach the tag because contact information can help return the item if it is lost.", [["and", "because", "write and attach"], ["contact information", "return if lost"]]),
            _r("Facts: align both sides; the kite must balance in a breeze. Explain why alignment comes before testing.", "Align both sides before testing because even sides help the kite balance in a breeze.", [["because", "align before testing"], ["even sides", "kite balance"]]),
            _r("Facts: the toy looks clean; its loose button remains; it is not ready. Use but.", "The toy looks clean, but its button is still loose. It is not ready until that part is repaired.", [["but contrast", "clean versus loose"], ["not ready", "button repaired"]]),
            _r("Facts: sort the pieces; count them; close the lid only after both checks. Use and.", "Sort and count the pieces, and close the lid only after both checks. This prevents an incomplete set from being packed.", [["sort and count", "and connector"], ["prevents incomplete set", "close after checks"]]),
            _q("The toy is small ___ it contains parts unsuitable for toddlers.", "but", ["because it is small therefore", "and with no contrast", "or why"]),
            _r("Facts: smooth the rough edge; hands will hold the toy there. Explain the reason.", "Smooth the rough edge because hands will hold the toy there. This reduces the chance of a scratch during play.", [["because", "hands hold there"], ["reduce scratch", "during play"]]),
            _q("The maker stitched the seam ___ checked it with a gentle pull.", "and", ["but", "because without cause", "unless why"]),
            _r("Facts: a magnetic piece fits; it does not match the picture colour; compare another spare. Use but.", "The magnetic piece fits, but its colour does not match the picture. Compare another spare before completing the puzzle.", [["but contrast", "fits versus colour mismatch"], ["compare another spare", "before completing"]]),
            _r("Facts: read the age label; choose a toy; label protects younger users from unsuitable parts. Use because.", "Read the age label before choosing because it warns when parts are unsuitable for younger users.", [["because", "read age label"], ["warns unsuitable parts", "younger users"]]),
        ],
        crunch_bar=CRUNCH_BAR["toy_process_explanations"],
        misconception="The learner uses because to join two steps even when no reason is given, writes a general reason not shown on the card, or writes a long procedure instead of the asked short explanation.",
        remediation="Decide whether each relation adds, contrasts, or gives a reason, choose the connector, and limit the answer to action plus visible purpose in one or two sentences.",
    ),
]


ASSESSMENT_PAIRS = [
    _aq_pair("reading.event_sequence", "Which workshop action came last?", ("The maker found a loose wheel, replaced its peg, tested the cart, and boxed it.", "The maker boxed the cart.", ["A loose wheel was found.", "The peg was replaced.", "The cart was tested."]), ("The clerk heard the travel need, compared two games, explained one, and packed it.", "The clerk packed the game.", ["The need was heard.", "Games were compared.", "One game was explained."])),
    _ar_pair("reading.paragraph_main_idea", "State the main idea in one concise sentence.", "Connects careful inspection or need matching with the useful result.", ("A top wobbled, its uneven peg was shortened, and a second test showed steady spinning.", "The worker spotted the uneven peg, shortened it, and tested the top again until it spun steadily.", [["spotted the uneven peg"], ["shortened it, and tested the top again", "fixed it, and tested it again"], ["spun steadily", "toy spun well"]]), ("A family needed a compact shared game. The assistant asked about space and players before choosing one.", "Asking about the family's space and players helped select a suitable shared travel game.", ["asking about space and players", "suitable shared game"]), interaction_type="summary"),
    _aq_pair("reading.dialogue_attribution", "Who speaks or thinks the named line?", ("'Is my wheel straight?' asked the cart. 'I will test it,' the maker replied.", "the maker speaks the second line", ["the cart speaks both lines", "the wheel replies", "a shopper speaks first"]), ("The puzzle thought, I hope all pieces are here. The clerk said, 'I counted forty.'", "the puzzle has the private thought", ["the clerk thinks both lines", "forty speaks", "a customer thinks first"])),
    _ar_pair("grammar.punctuation_capitalization", "Rewrite the exchange with correct capitals and punctuation.", "Uses quotation marks, capitals, reporting punctuation, and fitting end marks.", ("draft: can you fix my bell asked the bicycle. yes replied nora", "'Can you fix my bell?' asked the bicycle. 'Yes,' replied Nora.", ["Can capital", "question mark", "Nora capital", "quotation marks"]), ("draft: this wheel is stuck cried the robot. i can oil it said ria", "'This wheel is stuck!' cried the robot. 'I can oil it,' said Ria.", ["exclamation mark", "I capital", "Ria capital", "quotation marks"]), interaction_type="dialogue", min_words=10),
    _ar_pair("reading.inference_reason", "State the supported preference and cite its clue.", "Infers a need or interest from at least two supplied facts.", ("A child likes building, asks how wheels move, and wants to assemble parts.", "The child likely enjoys construction toys with moving parts, shown by building and asking about wheels.", ["construction toys", "building", "asking about wheels"]), ("Two cousins need one quiet activity for a small train table.", "They likely need a compact two-player quiet game because the table is small and both cousins must join.", ["compact two-player", "quiet", "small table"])),
    _ar_pair("writing.reason_answer", "Choose the suitable toy and justify it with the constraints.", "Names a suitable choice and uses at least two supplied need or safety facts.", ("Options: tiny beads, large soft blocks, long rulebook. User: two-year-old who likes stacking.", "Choose the large soft blocks because they support stacking and avoid the tiny parts in the bead set.", ["large soft blocks", "stacking", "avoid tiny parts"]), ("Options: loud horn, compact magnetic puzzle, outdoor hoop. Need: quiet waiting-room activity.", "Choose the compact magnetic puzzle because it is quiet and fits the waiting-room space.", ["compact magnetic puzzle", "quiet", "waiting room"])),
    _aq_pair("grammar.noun_verb_adjective", "Which word is the adjective?", ("The sturdy wooden cart rolls smoothly.", "sturdy", ["cart", "rolls", "smoothly"]), ("A flexible track bends around the chair.", "flexible", ["track", "bends", "chair"])),
    _ar_pair("vocab.chapter_word_usage", "Explain the word and use it in a fresh sentence.", "Defines the supplied word and transfers it accurately to a new complete sentence.", ("Compact means small enough for limited space.", "Compact means practical in a small space. The compact card game fitted inside one travel pouch.", ["small space", "compact card game", "travel pouch"]), ("Sturdy means strong enough for regular use.", "Sturdy means strong and dependable. The sturdy block tower remained standing after three tests.", ["strong and dependable", "sturdy block tower"])),
    _aq_pair("vocab.spelling", "Which plural spelling is standard?", ("Assessment word card: Write the noun brush for more than one object.", "brushes", ["brushs", "brushies", "brushess"]), ("Assessment word card: Write the noun train for more than one vehicle.", "trains", ["traines", "trainss", "trainies"])),
    _ar_pair("vocab.word_formation", "Form the word and explain the parts or ending.", "Produces the correct form and explains the relevant base parts or spelling rule.", ("Bases: toy + shop. Meaning: a shop selling toys.", "Toyshop combines toy and shop and means a shop where toys are sold.", ["toyshop", "toy and shop", "toys are sold"]), ("One dish is on the table. Write the word for three of them.", "The plural is dishes. Dish ends in sh, so es is added.", ["dishes", "ends in sh", "add es"])),
    _aq_pair("grammar.connectors_because_and_but", "Which connector expresses the relationship?", ("The first wheel turns, ___ the second wheel sticks.", "but", ["because", "and without contrast", "so why"]), ("Read the age label ___ it warns about unsuitable parts.", "because", ["but", "and without reason", "or why"])),
    _ar_pair("writing.short_answer", "Join the facts and give the visible reason in one or two sentences.", "Uses the correct connector and gives a concise action-purpose explanation.", ("Facts: press the label firmly; loose edges collect dust.", "Press the label firmly because loose edges collect dust. This keeps the label flat and readable.", ["because", "loose edges collect dust", "flat and readable"]), ("Facts: the puzzle picture is complete; two pieces are bent; it cannot be packed yet.", "The puzzle picture is complete, but two pieces are bent. It cannot be packed until those pieces are replaced.", ["but", "two pieces are bent", "cannot be packed"]), interaction_type="short_text"),
    _ar_pair("reading.paragraph_main_idea", "Summarise the whole repair or choice card.", "Captures the need, careful response, and useful result without listing minor details.", ("A puzzle lacked pieces. The worker matched spare edges and colours, then completed one test picture.", "Matching spare pieces by edge and colour made the incomplete puzzle usable again.", ["matching spare pieces", "usable again"]), ("A child needed a four-person activity. The clerk compared player counts and chose a game everyone could join.", "Checking player counts helped choose an inclusive game for all four children.", ["checking player counts", "inclusive game"]), interaction_type="summary"),
    _ar_pair("writing.short_answer", "Explain why the named check happens before packing.", "Names the check and its specific purpose in a concise complete answer.", ("The worker tests a repaired wheel before boxing the cart.", "The worker tests the wheel before packing because the test confirms that the cart rolls steadily.", ["tests before packing", "confirms rolls steadily"]), ("The clerk counts puzzle pieces before closing the lid.", "The clerk counts the pieces before closing the lid because this prevents an incomplete set from being packed.", ["counts before closing", "prevents incomplete set"]), interaction_type="short_text"),
]


LAUNCH_DEPTH_CASES = {
    "toy_workshop_sequence": [
        _launch_depth_case(
            "A wooden cart arrived with one wheel rubbing the side. The class compared the axles, added a thin washer, spun the wheel again, and gave the smooth cart to the reading corner.",
            "Order the wooden-cart inspection and repair, then state the main idea of matching the fix to the problem.",
            "The class noticed the rubbing wheel, compared axles, added a washer, tested it, and placed the cart in the reading corner. The main idea is that careful checking found a small fix that made the cart roll smoothly.",
            "noticed the rubbing wheel, compared axles, added a washer, tested it, and placed the cart",
            "careful checking found a small fix that made the cart roll smoothly",
            ordered=True,
        ),
        _launch_depth_case(
            "A cloth puppet reached the workshop with a loose hand loop. Neha measured the user's wrist, shortened the loop, stitched it twice, and watched the child move the puppet comfortably.",
            "Retell Neha's cloth-puppet work and give the whole idea about the user's need.",
            "Neha found the loose loop, measured the wrist, shortened and stitched it, and then checked the puppet. The card is mainly about changing a toy part so it fits the user safely and comfortably.",
            "found the loose loop, measured the wrist, shortened and stitched it, and then checked the puppet",
            "changing a toy part so it fits the user safely and comfortably",
            ordered=True,
        ),
        _launch_depth_case(
            "A board game had tiny direction cards that two players could not read. The makers rewrote them in larger print, tested one round, and stored the clear cards in a labelled pouch.",
            "Sequence the board-game problem, change, test, and result, then state the main idea.",
            "The makers noticed the tiny print, rewrote the cards, tested a round, and stored the clearer set. The main idea is that listening to players helped make the game easier to use.",
            "noticed the tiny print, rewrote the cards, tested a round, and stored the clearer set",
            "listening to players helped make the game easier to use",
            ordered=True,
        ),
    ],
    "toy_speakers_and_punctuation": [
        _launch_depth_case(
            "At the repair table, Asha says the toy train stops at every curve. The maker replies that he will check the front wheels before changing the track.",
            "Identify Asha and the maker, then punctuate their toy-train exchange with capitals, commas, quotation marks, and end marks.",
            "Asha said, 'The toy train stops at every curve.' The maker replied, 'I will check the front wheels before changing the track.' The reply addresses Asha's report.",
            "Asha said, 'The toy train stops at every curve.' The maker replied, 'I will check the front wheels before changing the track.'",
            "the reply addresses Asha's report",
            interaction_type="dialogue",
            min_words=15,
        ),
        _launch_depth_case(
            "Milan asks whether the paper kite can use a shorter tail. Reva answers that they should test both tails in the same breeze.",
            "Name Milan and Reva as the speakers, then write the correctly punctuated kite question and reply.",
            "Milan asked, 'Can the paper kite use a shorter tail?' Reva replied, 'Let us test both tails in the same breeze.' Reva proposes a fair comparison.",
            "Milan asked, 'Can the paper kite use a shorter tail?' Reva replied, 'Let us test both tails in the same breeze.'",
            "Reva proposes a fair comparison",
            interaction_type="dialogue",
            min_words=14,
        ),
        _launch_depth_case(
            "The toy librarian says a puzzle piece is missing. Dinu replies that he saw one under the blue shelf and will bring it back.",
            "Write the toy librarian and Dinu's puzzle exchange with clear speaker tags and punctuation.",
            "The toy librarian said, 'A puzzle piece is missing.' Dinu replied, 'I saw one under the blue shelf, and I will bring it back.' Dinu answers with a useful clue and action.",
            "the toy librarian said, 'A puzzle piece is missing.' Dinu replied, 'I saw one under the blue shelf, and I will bring it back.'",
            "Dinu answers with a useful clue and action",
            interaction_type="dialogue",
            min_words=16,
        ),
    ],
    "toy_preference_inference": [
        _launch_depth_case(
            "Leena feels each game piece before choosing it and keeps losing the flat pieces on the smooth board. She finds the raised star and ridged circle quickly.",
            "What toy feature does Leena likely value, and why is a raised-shape game a suitable choice?",
            "Leena likely values pieces she can identify by touch. A raised-shape game suits her because the star and ridged circle are easy to feel and find.",
            "Leena likely values pieces she can identify by touch",
            "the star and ridged circle are easy to feel and find",
        ),
        _launch_depth_case(
            "Rohit leaves a noisy battery robot on the shelf and spends ten minutes arranging quiet wooden animals into a farm. He smiles when no sound interrupts the story.",
            "What does Rohit's toy choice suggest, and why would the wooden farm be a suitable recommendation?",
            "Rohit likely values quiet pretend play. The wooden farm suits him because he can build a long story without the robot's sound interrupting.",
            "Rohit likely values quiet pretend play",
            "build a long story without the robot's sound interrupting",
        ),
        _launch_depth_case(
            "Maya takes toys to the courtyard and tests them on rough paving. A thin plastic wheel cracks, but the thick rubber-wheeled truck keeps moving.",
            "What constraint matters in Maya's courtyard play, and why is the rubber-wheeled truck the safer choice?",
            "Maya needs a toy that can handle a rough surface. The rubber-wheeled truck is safer because its thick wheels survive the paving without cracking.",
            "Maya needs a toy that can handle a rough surface",
            "thick wheels survive the paving without cracking",
        ),
    ],
    "describing_toys_in_context": [
        _launch_depth_case(
            "The flexible figure bends at its knees and elbows without breaking. Flexible describes how the toy moves, while figure names the object.",
            "Explain the jobs of flexible and figure, then use flexible in a fresh complete toy sentence.",
            "Figure is a noun, and flexible is an adjective. New sentence: The flexible track curved around the table leg without snapping.",
            "figure is a noun, and flexible is an adjective",
            "the flexible track curved around the table leg without snapping",
        ),
        _launch_depth_case(
            "A sturdy block bridge stays upright after three toy buses cross it. Sturdy describes the bridge as strong enough for repeated use.",
            "Identify sturdy and bridge, then use sturdy in a new sentence about another toy.",
            "Bridge is a noun, and sturdy is an adjective meaning strong and dependable. New sentence: The sturdy drum kept its shape after many turns.",
            "bridge is a noun, and sturdy is an adjective",
            "the sturdy drum kept its shape after many turns",
        ),
        _launch_depth_case(
            "The polished spinning top has a smooth shiny surface that reflects the lamp. Polished tells the top's condition, and spins names its action.",
            "Name the word jobs of polished, top, and spins, then use polished in a fresh toy sentence.",
            "Top is a noun, polished is an adjective, and spins is a verb. New sentence: A polished wooden horse shone on the display shelf.",
            "top is a noun, polished is an adjective, and spins is a verb",
            "a polished wooden horse shone on the display shelf",
        ),
    ],
    "plural_and_compound_building": [
        _launch_depth_case(
            "The art set has one brush, three brushes, and a box that holds paint. The base words paint and box name the container together.",
            "Write the plural of brush and form the compound from paint and box, explaining both forms from the art set.",
            "The plural of brush is brushes because it adds es. Paint and box join as paintbox, the box that holds paint.",
            "the plural of brush is brushes",
            "paint and box join as paintbox",
        ),
        _launch_depth_case(
            "One toy bus stands beside four toy buses. A stop made for buses is labelled with the base words bus and stop.",
            "Give the plural of bus and build the bus-stop compound shown on the toy-town card.",
            "The plural of bus is buses. Bus and stop combine as bus stop, a place where buses stop in the toy town.",
            "the plural of bus is buses",
            "bus and stop combine as bus stop",
        ),
        _launch_depth_case(
            "The play kitchen has one dish, five dishes, and a cloth for drying dishes. The base words dish and cloth form the cloth's name.",
            "Spell the plural of dish and form the compound from dish and cloth with its meaning.",
            "The plural of dish is dishes because it takes es. Dish and cloth join as dishcloth, a cloth used for dishes.",
            "the plural of dish is dishes",
            "dish and cloth join as dishcloth",
        ),
    ],
    "toy_process_explanations": [
        _launch_depth_case(
            "The wind-up mouse moved after Suri turned its key, but it leaned left because one wheel was loose. She tightened the wheel and tested it again.",
            "Use but and because to explain the wind-up mouse result and answer what Suri should check first.",
            "The mouse moved, but it leaned left because one wheel was loose. Suri should check the wheel first because tightening it changed the test.",
            "the mouse moved, but it leaned left because one wheel was loose",
            "check the wheel first because tightening it changed the test",
        ),
        _launch_depth_case(
            "A cardboard van had a roof and doors, but its thin axle bent because the load was too heavy. The builders removed two blocks before the next trial.",
            "Join the cardboard-van facts with but and because, then give a short reason for removing two blocks.",
            "The van had a roof and doors, but its axle bent because the load was too heavy. The builders removed two blocks to make the next load lighter.",
            "the van had a roof and doors, but its axle bent because the load was too heavy",
            "removed two blocks to make the next load lighter",
        ),
        _launch_depth_case(
            "A hanging mobile looked level at first, but the star side dropped because two extra beads were added. Noor moved one bead to the moon side.",
            "Explain the hanging-mobile change with but and because, then answer why Noor moved one bead.",
            "The mobile looked level, but the star side dropped because it held extra beads. Noor moved one bead to the moon side to balance the two sides.",
            "the mobile looked level, but the star side dropped because it held extra beads",
            "moved one bead to the moon side to balance the two sides",
        ),
    ],
}

_add_launch_depth_variants(LEVELS, LAUNCH_DEPTH_CASES)


_SEMANTIC_OPTION_REPLACEMENTS = {'The child selected first.': 'The child chose a set before hearing the three choices.',
 'The clerk ignored the interests.': 'The clerk chose a set only by its box colour.',
 'The set was returned before viewing.': 'The child returned the set before comparing '
                                         'the choices.',
 'and with no contrast': 'so'}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch05:assessment:07': {'accepted_answers': ['flexible'],
                               'options': ['easily', 'flexible', 'puppet', 'bends'],
                               'passage': 'The flexible puppet bends easily.',
                               'prompt': 'Which word is the adjective?'},
 'eng_c3_ch05:assessment:10': {'model_answer': 'Playroom combines play and room and '
                                               'means a room used for play.',
                               'passage': 'Bases: play + room. Meaning: a room used '
                                          'for play.',
                               'prompt': 'Form the word and explain the parts or '
                                         'ending.',
                               'relevance_terms': ['playroom',
                                                   'play and room',
                                                   'room used for play'],
                               'slot_aliases': [['playroom'],
                                                ['play and room'],
                                                ['room used for play']]},
 'eng_c3_ch05:assessment:11': {'accepted_answers': ['but'],
                               'options': ['and', 'but', 'because', 'so'],
                               'passage': "The doll's arm moves, ___ its wheel base is "
                                          'stuck.',
                               'prompt': 'Which connector expresses the relationship?'},
 'eng_c3_ch05:assessment:12': {'model_answer': 'Close the paint pots because open '
                                               'paint can dry out. This keeps the '
                                               'paint ready for later.',
                               'passage': 'Facts: close the paint pots; open paint can '
                                          'dry out.',
                               'prompt': 'Join the facts and give the visible reason '
                                         'in one or two sentences.',
                               'relevance_terms': ['because',
                                                   'open paint can dry out',
                                                   'paint ready for later'],
                               'slot_aliases': [['because'],
                                                ['open paint can dry out'],
                                                ['paint ready for later']]},
 'eng_c3_ch05:assessment:13': {'model_answer': 'The maker tightened the side cords, '
                                               'and a clear beat returned to the toy '
                                               'drum.',
                               'passage': 'A toy drum sounded dull because its top was '
                                          'loose. The maker tightened the side cords '
                                          'evenly, tested it, and heard a clear beat.',
                               'prompt': 'Summarise the whole repair or choice card.',
                               'relevance_terms': ['tightened the side cords',
                                                   'clear beat returned'],
                               'slot_aliases': [['tightened the side cords'],
                                                ['clear beat returned']]},
 'eng_c3_ch05:assessment:20': {'model_answer': 'Choose the folding card puzzle because '
                                               'it is quiet and fits in a small train '
                                               'bag.',
                               'passage': 'Options: large marble run, folding card '
                                          'puzzle, noisy electronic drum. Need: a '
                                          'quiet toy that fits in a small train bag '
                                          'for one child.',
                               'prompt': 'Choose the suitable toy and give a reason '
                                         'for it with the constraints.',
                               'relevance_terms': ['folding card puzzle',
                                                   'quiet',
                                                   'fits in a small train bag'],
                               'slot_aliases': [['folding card puzzle'],
                                                ['quiet'],
                                                ['fits in a small train bag']]}}


_SEMANTIC_CONNECTOR_OPTIONS = ("and", "but", "because", "so", "although")
_SEMANTIC_MALFORMED_CONNECTORS = (
    "and then because",
    "or else and",
    "so that reason",
    "with no contrast",
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
    chapter_no=5,
    title="Talking Toys",
    unit_title="Toys and Games",
    source_url=SOURCE_URL,
    page_extract="/tmp/zidd-ncert-class2-3/eng_c3_ch05.txt",
    source_anchors=SOURCE_ANCHORS,
    levels=LEVELS,
    assessment_pairs=ASSESSMENT_PAIRS,
)

_apply_semantic_copy_corrections(MANIFEST["levels"])
_apply_semantic_copy_corrections(
    MANIFEST["chapter_assessment"]["items"]
)
_apply_semantic_assessment_overrides(MANIFEST)
