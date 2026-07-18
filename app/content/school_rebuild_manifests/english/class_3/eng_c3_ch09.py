"""Deep authored manifest for Class 3 English Chapter 9.

The source extract supplied only the chapter map and exercise forms. Every
runtime stimulus, question, option, and rubric below is original Zidd work.
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
    "chapter_id": "eng_c3_ch09",
    "chapter_no": 9,
    "title": "Madhu's Wish",
    "unit_title": "Good Food",
    "source_url": "https://ncert.nic.in/textbook/pdf/cesa109.pdf",
    "source_analysis_reference": (
        "/tmp/zidd-ncert-class2-3/eng_c3_ch09.txt structure review"
    ),
    "anchors": [
        {"label": "Let us read: Madhu's wish, missing water, and changed choice", "page_start": 1, "page_end": 5, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us think A: story comprehension and inference questions", "page_start": 6, "page_end": 6, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us learn B-C: kind, greedy, generous, and other quality words", "page_start": 7, "page_end": 8, "treatment": "zidd_equivalent", "required": True},
        {"label": "Let us learn D: joining with and and but; Zidd because extension for printed causes", "page_start": 8, "page_end": 9, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us write A: supported story continuation from the Vijaya opening", "page_start": 11, "page_end": 11, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us listen: tell what happened after two story moments", "page_start": 10, "page_end": 10, "treatment": "guided_only", "required": False},
        {"label": "Let us do: draw and assemble a table mat", "page_start": 13, "page_end": 14, "treatment": "offline_group_activity", "required": False},
        {"label": "Let us think B: speak about hiccups, water, and a personal wish", "page_start": 6, "page_end": 6, "treatment": "guided_only", "required": False},
    ],
    "levels": [
        {
            "level_id": "wish_story_chain",
            "title": "Follow a wish into a problem",
            "focus": "track event sequence and comprehend how one choice changes later events",
            "concept": "wish story result sequence",
            "outcome": "Order a wish, repeated choice, emerging need, and correction, then state what each event contributes to the visible chain.",
            "skill_ids": ["reading.event_sequence", "reading.sentence_comprehension"],
            "episode_kind": "comprehension_studio",
            "anchor_indexes": [1],
            "principle": "A later result follows an earlier choice. Time words and changing needs show how a pleasing start can turn into a problem and a repair.",
            "connect": _connect(
                "A wish story is more than a list of things received. Readers track what the character chooses, what the choice causes, and which later action repairs the difficulty.",
                "Rohan wished for endless paint but forgot to ask for paper. Jars filled his room until he exchanged most of them for a stack of drawing sheets.",
                "Trace the wish, missing need, crowded result, and corrective exchange.",
            ),
            "misconception": "The learner groups events by similar objects instead of time or misses that the later problem grows from the earlier narrow choice.",
            "remediation": "Number the visible events, draw a cause arrow from the wish to the problem, and explain each sentence's role before writing the complete chain.",
            "ordered_response": True,
            "cases": [
                _case("seed wish", "Kavi asks a magic pot for endless seeds. Bags soon block his doorway, so he keeps one garden packet and gives the rest to a seed library.", "Which event chain shows the choice, the problem, and the fix?", "Kavi asks for seeds, faces a blocked doorway, and shares the extra bags.", "Kavi shares seeds before making any wish.", "The doorway asks for a garden packet.", "The extra bags block the doorway, and sharing them fixes the problem.", "asks blocks shares", "extra bags cause problem"),
                _case("mango wish", "Tina wishes that every snack taste like mango. After several sweet meals she longs for something salty and changes the wish to a varied lunch box.", "How does the sequence develop?", "Tina chooses one flavour, tires of it, and changes to variety.", "Tina requests variety before tasting mango.", "The lunch box makes a wish for Tina.", "Repeated sweetness causes the desire for a balanced change.", "one flavour tires changes", "repetition causes change"),
                _case("toy wheel wish", "Biren asks for hundreds of toy wheels but no toy bodies. The wheels roll across the floor, and he finally asks for a small building set instead.", "What are the main events in order?", "Biren receives only wheels, finds them unhelpful, and changes his wish.", "Biren builds complete toys before receiving wheels.", "The floor requests hundreds of toys.", "The wish gives him parts he cannot use, so he asks for a better set.", "wheels unhelpful changes", "wish gives poor result"),
                _case("flower wish", "Leela wishes every pot would bloom at once. The balcony becomes too crowded for watering, so she moves some plants to the community garden.", "Which order explains the final move?", "All pots bloom, watering becomes difficult, and Leela moves some plants.", "Leela moves bare pots before any bloom.", "Watering creates a balcony from nothing.", "Crowding caused by the wish makes relocation necessary.", "bloom crowding moves", "crowding requires relocation"),
                _case("book wish", "Naman asks for every adventure book in town. Towers of books hide his desk, and he chooses ten favourites before donating the others.", "What result links the wish to the donation?", "The huge book collection blocks the desk, so Naman keeps a few and donates the rest.", "Naman donates books before receiving them.", "The desk reads every adventure.", "There are too many books to use, so Naman chooses some and shares the rest.", "collection blocks donates", "too many leads sharing"),
                _case("sweet fountain", "A fair visitor wishes for a fountain of syrup. The sticky flow covers the path, and she asks for clean water to wash the stones.", "How should the problem and fix be stated in order?", "Syrup covers the path, so the visitor asks for water to clean it.", "Water covers the path before the syrup appears.", "The stones ask for a fair ticket.", "The sticky path needs water before it can become clean again.", "syrup covers water cleans", "sticky result needs water"),
                _case("music wish", "A boy wishes that his drum never stop. The sound keeps the baby awake, so he changes the wish to one short song each evening.", "Which sequence shows learning from the result?", "The endless drumming disturbs the baby, and the boy chooses a limited song.", "The baby requests endless drumming.", "The boy chooses silence before making a wish.", "The unwanted effect causes a more thoughtful limit.", "drumming disturbs limits", "effect causes thoughtful limit"),
            ],
        },
        {
            "level_id": "wish_reasoning",
            "title": "Infer why a choice backfires",
            "focus": "infer a cause and construct a reason answer from linked clues",
            "concept": "choice and story result inference",
            "outcome": "Infer the unstated reason behind a character's change of mind and justify it with a because clause grounded in two visible clues.",
            "skill_ids": ["reading.inference_reason", "writing.reason_answer"],
            "episode_kind": "meaning_encounter",
            "anchor_indexes": [1, 2],
            "principle": "A good inference explains why a response follows earlier events. It must connect the need and the later problem instead of repeating the final action.",
            "connect": _connect(
                "When a character reverses a wish, the passage may not state every thought. Readers combine the growing problem with the final request to infer the reason.",
                "A magic shelf produced only salty crackers. After two plates, Pema reached for water and asked the shelf to offer fruit as well.",
                "Connect thirst and the changed request to infer why Pema no longer wants only crackers.",
            ),
            "misconception": "The learner calls the character foolish without evidence or answers with the final action alone instead of explaining the need that caused it.",
            "remediation": "Underline the problem clue and the changed action, join them with because, and remove any judgement word that the passage does not support.",
            "creative_transfer": True,
            "cases": [
                _case("cracker shelf", "Pema asks a shelf for only salty crackers. Her mouth becomes dry, and she changes the request to fruit and water.", "Why does Pema change her request?", "Pema changes it because the salty crackers make her thirsty.", "Pema changes it because she never sees a cracker.", "The shelf orders her to plant a tree.", "Dry mouth and the request for water reveal the unmet need.", "changes because thirsty", "dry mouth water clue"),
                _case("single colour", "A painter chooses only blue for a festival sign. The blue letters disappear against the blue wall, so she adds white borders.", "What reason explains the added borders?", "She adds white borders because the blue letters are hard to see.", "She adds borders because the wall is white.", "She wants every letter to disappear completely.", "Low contrast creates the visibility problem that white edges solve.", "borders improve visibility", "blue on blue contrast"),
                _case("endless wind", "A child wishes for wind all day to fly a kite. The wind later scatters the picnic plates, and the child asks for a calm hour.", "Why is a calm hour now important?", "A calm hour is needed because the endless wind is scattering the picnic.", "Calm is needed because the kite became a plate.", "The picnic happens before any wind.", "The scattered plates show why wind all day is causing trouble.", "calm because scattering", "disrupted picnic clue"),
                _case("only stories", "Zoya asks a talking box for stories all night. She yawns through breakfast and requests a quiet bedtime the next evening.", "Which inference supports the bedtime change?", "Zoya changes because staying awake for stories leaves her tired.", "Zoya changes because breakfast tells stories.", "She sleeps all night before the box begins.", "Yawning at breakfast links lost sleep to the later quiet request.", "changes because tired", "yawning lost sleep"),
                _case("giant garden", "Manu asks every seed to sprout in one day. The crowded shoots bend over one another, so he moves them into separate beds.", "Why does Manu separate the shoots?", "Manu separates them because the sudden crowding prevents healthy space.", "He separates them because no seed sprouts.", "The beds ask to become seeds.", "Bent crowded shoots show the need for more growing room.", "separates because crowded", "bent shoots need space"),
                _case("coin pocket", "Rita wishes her pocket always contain coins. It becomes too heavy to walk comfortably, so she keeps only enough for the bus.", "What reason justifies the smaller amount?", "Rita keeps fewer coins because the full pocket is too heavy.", "Rita keeps fewer because coins weigh nothing.", "The bus fills her pocket with stones.", "Walking difficulty reveals the cost of the unlimited amount.", "fewer because heavy", "walking difficulty"),
                _case("lamp wish", "A camper wishes for the brightest lamp possible. Moths crowd around it and block her view, so she turns it down.", "Why does the camper reduce the light?", "She reduces it because the bright lamp attracts too many moths.", "She reduces it because the lamp is already dark.", "The moths carry the lamp away.", "The crowd of moths is the unwanted result of the very bright light.", "reduces because moths", "brightness attracts crowd"),
            ],
        },
        {
            "level_id": "wish_character_quality",
            "title": "Prove a character quality",
            "focus": "infer vocabulary from action and classify quality words as adjectives",
            "concept": "character quality",
            "outcome": "Choose a quality word supported by a visible action, distinguish it from nouns and verbs, and explain the evidence without labelling the whole person forever.",
            "skill_ids": ["reading.word_meaning_context", "grammar.noun_verb_adjective"],
            "episode_kind": "language_lab",
            "anchor_indexes": [3],
            "principle": "A character quality adjective describes how someone acts in one stated moment. Use the shown action to choose a precise word.",
            "connect": _connect(
                "Words such as patient, generous, and careless are adjectives when they describe behaviour. Readers prove the quality with an action instead of choosing by mood alone.",
                "When only one umbrella remained, Farah held it over both herself and a younger child during the walk home.",
                "Use Farah's sharing action to test whether considerate is the supported quality adjective.",
            ),
            "misconception": "The learner chooses a quality based on whether the result was good, confuses an action verb with an adjective, or makes a permanent judgement from one scene.",
            "remediation": "Name the exact action, ask what it shows in this moment, select an adjective, and frame the answer as 'The action is ___ because...' rather than 'The person is always...'.",
            "cases": [
                _case("shared lunch", "Avi notices a new pupil without lunch and divides his own flatbread into two equal parts.", "Which adjective is supported by the action?", "Avi's action is generous because he shares his lunch.", "Avi's action is selfish because he shares equally.", "The quality word is divides, which is only the verb.", "Giving part of his own meal shows that this action is generous.", "generous shares lunch", "giving own meal"),
                _case("careful list", "Before using her wish token, Nira lists what she needs, checks each possible result, and asks one adult to review the plan.", "What character quality does the preparation show?", "Nira acts thoughtful because she checks her needs and possible results.", "Nira acts careless because she reviews the plan.", "The adjective is token, which is a noun.", "Planning and checking show thoughtful behaviour.", "thoughtful checks results", "planning evidence"),
                _case("returned purse", "Kush finds a purse near the gate and gives it to the office without taking anything from it.", "Which quality adjective fits this moment?", "Kush acts honest because he returns the untouched purse.", "Kush acts greedy because he returns it.", "The quality word is gives, which is a verb.", "Returning property intact supports honest.", "honest returns purse", "property intact"),
                _case("queue turn", "Mili waits while three younger children fill their bottles, even though she reached the tap first.", "What quality is shown by the waiting?", "Mili acts patient because she calmly waits for others.", "Mili acts impatient because she allows turns.", "The adjective is bottle, which names an object.", "Calm waiting despite delay is evidence of patience.", "patient calmly waits", "delay without complaint"),
                _case("broken branch", "Dev swings from a weak branch after a warning sign says not to climb it. The branch snaps, though he is not hurt.", "Which quality word describes the choice?", "Dev's choice is careless because he ignores the warning.", "Dev's choice is cautious because he ignores danger.", "The adjective is snaps, which is a verb.", "Ignoring a visible safety warning shows a careless choice.", "careless ignores warning", "visible safety risk"),
                _case("water share", "During a hot walk, Sana gives half her water to a tired teammate and then asks where both bottles can be refilled.", "Which quality and evidence belong together?", "Sana acts considerate because she shares water and plans a refill.", "Sana acts selfish because she helps a teammate.", "The quality word is refill, which is an action.", "She considers another person's need while protecting both walkers.", "considerate shares water", "plans refill for both"),
                _case("hasty wish", "Without reading the card, Hari uses his only wish on a noisy toy and regrets it when the toy has no off switch.", "Which adjective describes the decision in this scene?", "Hari's decision is hasty because he acts before reading the card.", "Hari's decision is patient because he skips the information.", "The adjective is toy, which is a noun.", "Acting before checking the terms supports hasty.", "hasty before reading", "skips checking terms"),
            ],
        },
        {
            "level_id": "wish_connectors",
            "title": "Join cause and contrast",
            "focus": "choose connectors and construct complete cause or contrast sentences",
            "concept": "connectors and but because",
            "outcome": "Use and to add a related idea, but to show a contrast, and because to give a reason in complete sentences.",
            "skill_ids": ["grammar.connectors_because_and_but", "writing.complete_sentence"],
            "episode_kind": "language_lab",
            "anchor_indexes": [4],
            "principle": "And adds a related idea, but shows a contrast, and because answers why. Both parts must make sense together.",
            "connect": _connect(
                "First ask whether the second idea adds, contrasts, or gives a reason. Then choose and, but, or because.",
                "Ria packed fruit and bread. She wanted another sweet, but she felt full. She chose water because she was thirsty.",
                "Notice the added foods, the surprising contrast, and the reason for choosing water.",
            ),
            "misconception": "The learner uses and for every join, swaps but and because, or joins fragments without a clear subject and action.",
            "remediation": "Label the link add, contrast, or reason, choose and, but, or because, then read both parts for a clear subject and action.",
            "cases": [
                _case("water choice", "Lena wanted juice. Her throat was dry, and only clean water was available, so she drank it.", "Which complete sentence uses because accurately?", "Lena drank water because her throat was dry.", "Lena drank water but her throat was dry as the reason.", "Because Lena water dry.", "Dryness answers why she chose the water.", "drank because dry", "reason answers why"),
                _case("sweet contrast", "Arun likes sesame sweets. Today he does not take one because he has already eaten a full meal.", "Which connector sentence preserves the contrast?", "Arun likes sesame sweets, but he does not take one today.", "Arun likes sweets because he refuses every sweet.", "But Arun sweets today.", "Liking the food contrasts with declining it now.", "likes but declines", "unexpected contrast"),
                _case("shared meal", "Maya has a small lunch. She divides it with her friend, who forgot a box.", "How can because join the action and reason?", "Maya shares her lunch because her friend has no box.", "Maya shares her lunch but her friend has no box as a reason.", "Because lunch friend.", "The missing lunch explains Maya's sharing action.", "shares because missing lunch", "cause for action"),
                _case("wish limit", "Nikhil could request ten games. He asks for one game so that he still has time for homework.", "Which sentence highlights the contrast with but?", "Nikhil could request ten games, but he asks for only one.", "Nikhil asks one because he could ask ten as the same fact.", "But ten game one.", "The smaller choice contrasts with the larger possibility.", "ten but one", "possibility contrasts choice"),
                _case("plant rescue", "The basil leaves droop. Sumi waters the pot after checking that the soil is dry.", "Which because sentence is supported?", "Sumi waters the basil because the soil is dry.", "Sumi waters the basil but the soil is dry as its cause.", "Because basil waters soil.", "Dry soil provides the direct reason for watering.", "waters because dry", "direct cause"),
                _case("rain plan", "The class planned an outdoor meal. Rain begins, and the class moves the meal inside without cancelling it.", "How should but express the change?", "Rain begins, but the class continues the meal indoors.", "Rain begins because the class continues indoors.", "But rain class meal.", "Bad weather contrasts with continuing the event in a new place.", "rain but continues", "weather contrast"),
                _case("careful request", "Pavi wants a giant box of paints. She chooses a small set after noticing the cupboard has little space.", "Which connector explains the final choice?", "Pavi chooses a small set because the cupboard has little space.", "Pavi chooses small but the cupboard is little as the reason.", "Because cupboard paint small.", "Limited storage answers why the request becomes smaller.", "chooses because space", "storage reason"),
            ],
        },
        {
            "level_id": "wish_main_idea_words",
            "title": "Summarise needs and choices",
            "focus": "identify a main idea and use need, plenty, replace, and enough in context",
            "concept": "need and plenty vocabulary",
            "outcome": "State a paragraph main idea about balanced needs and use key chapter vocabulary with precise quantity or replacement meanings.",
            "skill_ids": ["reading.paragraph_main_idea", "vocab.chapter_word_usage"],
            "episode_kind": "meaning_encounter",
            "anchor_indexes": [1, 2],
            "principle": "The main idea connects repeated details about wants and needs. Quantity words and replace must fit the relationship shown, not merely sound familiar.",
            "connect": _connect(
                "A paragraph may list many attractive things and one necessary thing. Readers ask which detail changes the outcome, then use vocabulary that distinguishes plenty from enough.",
                "The hikers carried plenty of snacks but little water. At the first refill point, everyone filled water bottles before opening another snack packet.",
                "Notice how the urgent need for water controls the paragraph's central idea.",
            ),
            "misconception": "The learner chooses the longest list as the main idea or uses plenty, enough, need, and replace as if they had the same meaning.",
            "remediation": "Sort details into want and need, identify which changes the action, define the target word, and test it in a new sentence with a visible quantity clue.",
            "cases": [
                _case("hiking bottles", "The group has plenty of biscuits but only one cup of water. They refill every bottle before continuing the walk.", "What main idea and quantity meaning fit?", "The group meets its need for water before using its plentiful snacks.", "The group needs more biscuits because it has plenty.", "Replace means throw away every bottle.", "The refill action shows water is necessary despite abundant food.", "need water plentiful snacks", "refill shows priority"),
                _case("art supplies", "Jia owns plenty of crayons but has no paper left. She replaces an empty notebook with a fresh pad before drawing.", "Which summary uses replace correctly?", "Jia has enough crayons but must replace her used paper supply.", "Jia replaces crayons by adding more crayons to plenty.", "Enough means having nothing useful.", "A new pad takes the place of the finished notebook.", "replace used paper", "new takes old place"),
                _case("garden water", "Rain fills two barrels, giving the garden enough water for the week. The gardener stores the extra bucket for dry days.", "What does enough mean in this paragraph?", "Enough means the garden has the amount of water it needs for the week.", "Enough means every barrel is empty.", "Plenty means less than any need.", "The weekly need is fully met and extra water remains.", "enough meets need", "extra remains"),
                _case("shoe repair", "Ivo has plenty of laces, but his torn shoe sole cannot be fixed with a lace. The cobbler replaces the sole.", "Which main idea separates plenty from the actual need?", "Having many laces does not meet Ivo's need for a sound shoe sole.", "The laces replace every part of the shoe.", "A torn sole means the shoe has plenty of soles.", "The required repair concerns the sole, not the abundant laces.", "need sound sole", "laces do not solve"),
                _case("festival lamps", "The hall has enough lamps for every table. Volunteers replace one cracked lamp before guests arrive.", "How do enough and replace work together?", "There are sufficient lamps, and one safe lamp takes the cracked lamp's place.", "Enough means the hall has no lamps.", "Replace means keep using the cracked lamp.", "Quantity is sufficient while safety requires one substitution.", "sufficient lamps replace cracked", "safe substitution"),
                _case("library shelf", "The shelf holds plenty of stories but no beginner dictionary. The librarian orders one because pupils need word meanings.", "What central idea covers the contrast?", "A library can have plenty of stories and still need a different kind of book.", "Plenty of stories removes every other need.", "A dictionary replaces all pupils.", "The missing reference book creates a need despite abundance elsewhere.", "plenty stories still need", "missing reference creates need"),
                _case("picnic fruit", "The picnic team brings enough fruit for each child and keeps two extra bananas for late arrivals.", "Which vocabulary statement is accurate?", "Enough fruit covers every expected child, with extra bananas kept in reserve.", "Enough means only one child receives fruit.", "Plenty means the bananas must be thrown away.", "The stated distribution meets the planned need and preserves a reserve.", "enough covers children", "extra reserve"),
            ],
        },
        {
            "level_id": "wish_story_continuation",
            "title": "Continue a wish story",
            "focus": "keep past tense and add a fitting next event to a visible story starter",
            "concept": "wish story continuation",
            "outcome": "Write two or three clear sentences that continue the shown story, keep the same characters and problem, and use past tense.",
            "skill_ids": ["grammar.tense_usage", "writing.short_answer"],
            "episode_kind": "expression_workshop",
            "anchor_indexes": [5],
            "principle": "A story continuation starts where the shown part stops. Keep the same people and problem, use past-tense verbs, and add a next event that could happen.",
            "connect": _connect(
                "Read the final shown event before adding anything. A useful next event answers the open problem without changing the people or place.",
                "Vijay found a seed box beside the village well. He opened it and saw a note asking the finder to plant only one seed.",
                "Think of what Vijay did next and keep found, opened, and saw in the past.",
            ),
            "misconception": "The learner changes the character or setting without a clue, repeats the starter, or switches between past and present tense.",
            "remediation": "Circle the last shown event, name the open problem, choose one possible next action, then write it with past-tense verbs.",
            "creative_transfer": True,
            "cases": [
                _case("one magic seed", "Vijay found a seed box beside the well. A note asked him to plant only one seed, but he wondered what the seed might grow.", "Which continuation keeps the same problem and past tense?", "Vijay planted one seed near the well and marked the spot with a stick. The next morning, a silver leaf appeared.", "Vijay plants every seed yesterday and moved to a city not named.", "A new girl cooked the box before Vijay found it.", "The next action follows the note, keeps Vijay at the well, and uses planted and appeared.", "Vijay planted one seed", "silver leaf appeared"),
                _case("endless mangoes", "Rina wished for mangoes, and baskets filled the courtyard. Soon there was no path to the gate.", "Continue the story with a sensible repair.", "Rina called her neighbours and shared the mangoes with them. By evening, the path was clear again.", "Rina calls yesterday and the courtyard became an ocean.", "A train arrived on the Moon without a clue.", "Sharing answers the blocked-path problem and the verbs stay in past tense.", "Rina shared mangoes", "path became clear"),
                _case("talking cup", "A clay cup promised Manu any drink. Manu asked for milk, but the cup poured far more than the jug could hold.", "What could happen next in this story?", "Manu placed a bucket under the cup and asked it to stop. He cleaned the table after the flow ended.", "Manu places a bucket tomorrow before the cup spoke.", "The cup turned into a bicycle and left school.", "The bucket and stop request answer the overflow shown in the starter.", "Manu used bucket", "asked cup to stop"),
                _case("sweet rain", "Pink sweets began falling in the park after Mira made a wish. Children cheered, but the path became sticky.", "Write a fitting two-sentence continuation.", "Mira asked everyone to gather the sweets in clean boxes. Then the park keeper washed the path with water.", "Mira gathers sweets tomorrow and the path never existed.", "A ship crossed the classroom ceiling.", "Gathering and washing solve the exact park problem in order.", "gathered sweets boxes", "keeper washed path"),
                _case("giant lunch box", "A magic lunch box grew until it covered Ravi's desk. He could not reach his books.", "How can the story continue without changing the setting?", "Ravi asked the box to shrink and moved it under the desk. He then picked up his books for class.", "Ravi asks yesterday and flew to a forest.", "His sister found a different box before Ravi appeared.", "Shrinking the box fixes the blocked-desk problem at school.", "box shrank under desk", "Ravi reached books"),
                _case("singing spoon", "A spoon sang whenever Bela stirred soup. At bedtime, it kept singing from the kitchen drawer.", "Add a next event that follows the noisy problem.", "Bela wrapped the spoon in a thick cloth and placed it in a closed tin. The song became quiet.", "Bela wraps it last night and the spoon built a house.", "A tiger entered without any earlier clue.", "The cloth and tin answer the unwanted sound while keeping Bela and the spoon.", "Bela wrapped spoon", "song became quiet"),
                _case("water wish", "Karan wished that the dry pond would fill. Water rose quickly and reached the edge of the footpath.", "Continue with a careful next action.", "Karan warned the walkers and opened the small side channel. The extra water flowed into the garden ditch.", "Karan warns yesterday after moving to another planet.", "The pond wrote a recipe for cake.", "Warning people and guiding water follow the rising-pond problem.", "Karan warned walkers", "water flowed to ditch"),
            ],
        },
    ],
}


FRESH_CASES = {
    "wish_story_chain": [
        _fresh_case("endless ribbons", "Asha wished for endless ribbons. They covered her chair, so she kept five rolls and gave the rest to the craft room.", "Put the wish, problem, and repair in order.", "Asha wished, the ribbons covered her chair, and she shared the extra rolls.", "The crowded chair appears before the choice to keep only a few.", "wish crowd share ribbons", "problem before repair"),
        _fresh_case("only bananas", "Tej asked for only bananas at every meal. By evening he wanted rice and lentils, so he changed the request.", "What is the story chain?", "Tej chose one food, tired of it, and asked for a varied meal.", "The repeated food leads to his later change.", "one food tired changed", "repetition before variety"),
        _fresh_case("bubble room", "Lina wished for bubbles indoors. They filled the room, hid the doorway, and made her ask for fresh air.", "Which event happens just before the fresh-air request?", "The bubbles hide the doorway before Lina asks for fresh air.", "The blocked view creates the need for a change.", "bubbles hide doorway", "request follows blockage"),
        _fresh_case("pencil pile", "A magic desk made a hundred pencils. The pile pushed off Mehul's notebook, so he kept six and packed the rest for school.", "Retell the events in a sensible order.", "The desk made pencils, the pile displaced the notebook, and Mehul packed the extras.", "The extra pencils must appear before they can cause and solve the problem.", "made pushed packed", "extras cause problem"),
        _fresh_case("never-ending bell", "Navi wished the bell would ring until everyone heard it. The sound hurt her ears, and she asked for one soft chime instead.", "What main change closes the chain?", "Navi replaces endless ringing with one soft chime.", "The painful sound explains the final smaller request.", "endless bell to chime", "loud sound prompts change"),
        _fresh_case("toy boats", "Omar wished for toy boats, but they poured from a box and blocked the stairs. He carried most to the playroom.", "Why does moving the boats come last?", "Omar moves the boats after they block the stairs.", "The obstacle must exist before he clears it.", "boats block then move", "obstacle before clearing"),
        _fresh_case("golden leaves", "Pia wished every leaf were gold. The shiny leaves became too hot in the sun, so she asked for green shade again.", "State the three main events.", "Pia changed the leaves, found the heat uncomfortable, and restored green shade.", "Heat from the changed leaves leads to the repair.", "gold heat green", "heat causes repair"),
        _fresh_case("soup tap", "A tap began pouring soup after Jai's wish. The pot filled, the floor flooded, and Jai turned the tap off.", "Which action ends the problem?", "Jai turns off the soup tap after the floor floods.", "Stopping the flow is the final repair.", "tap off after flood", "stop flow repairs"),
        _fresh_case("giant crayons", "Rumi asked for giant crayons. They would not fit her paper, so she wished them back to hand size.", "How does the size problem change the wish?", "Rumi changes from giant crayons to crayons she can use.", "The paper clue shows why the first size fails.", "giant to hand size", "paper does not fit"),
        _fresh_case("cookie cloud", "A cookie cloud dropped crumbs across the garden. Ants covered the path, so Zed swept and ended the wish.", "Put the clean-up in its place.", "The crumbs attract ants before Zed sweeps the path and ends the wish.", "Sweeping answers a problem created earlier.", "crumbs ants sweep", "clean after mess"),
        _fresh_case("bright shoes", "Mili wished for shoes that flashed all night. The light kept her awake, so she covered them and changed the wish.", "What happens between the wish and repair?", "The flashing shoes keep Mili awake.", "The lost sleep explains why she covers the shoes.", "shoes keep awake", "light before cover"),
        _fresh_case("fruit tower", "A fruit tower appeared after a wish. It leaned over the table, and Arav moved the baskets into low rows.", "Which order keeps the actions linked?", "The tower appears, begins to lean, and is rearranged into safe rows.", "The unsafe height leads to the lower layout.", "tower leans rearranged", "height prompts low rows"),
        _fresh_case("endless stickers", "Mira wished for endless star stickers. They covered her timetable, so she peeled off the extras and shared one sheet with each class table.", "Order Mira's wish, problem, correction, and sharing result.", "Mira wished, the stickers hid her timetable, she removed extras, and then shared the sheets.", "The hidden timetable creates the need to remove and divide the stickers.", "wish hide remove share", "problem leads correction"),
        _fresh_case("giant fan", "A hand fan grew as wide as the classroom. Its wind scattered every worksheet, so Rafi asked for a small fan and collected the papers.", "What chain connects the giant fan to Rafi's final actions?", "The fan grew, scattered papers, became small again, and Rafi collected the sheets.", "The scattered work explains both the changed wish and clean-up.", "grew scattered shrank collected", "mess causes repair"),
        _fresh_case("only music", "Nita wished that every sound became music. She could not hear the fire-drill bell, so she restored ordinary sounds and listened for the signal.", "Put the music wish, missed warning, and correction in order.", "Nita changed all sounds, missed the drill bell, restored normal sound, and listened again.", "The missed safety signal makes the correction necessary.", "music missed restored listened", "warning causes change"),
    ],
    "wish_reasoning": [
        _fresh_case("spicy snacks", "Reva wished for only spicy snacks. Her mouth burned, and she asked for curd and water.", "Why did Reva change the request?", "Reva changed it because the spicy food made her mouth burn.", "The later cooling foods answer the burning clue.", "changed because burning", "curd water cool"),
        _fresh_case("dark paint", "All of Kian's wish-paint was black. His night poster could not be read, so he added yellow letters.", "Why did yellow help?", "Yellow letters helped because they stood out on the dark paint.", "The unreadable poster shows a need for contrast.", "yellow stands out", "dark poster unreadable"),
        _fresh_case("huge pillow", "A pillow grew across Nia's bed and left no room to lie down. She asked it to shrink.", "What reason supports shrinking it?", "Nia shrank the pillow because it filled the whole bed.", "No sleeping space is the problem clue.", "shrank full pillow", "no room on bed"),
        _fresh_case("sweet tea", "The cup made tea sweeter after every sip. Daya stopped drinking when the taste became too strong.", "Why did Daya stop?", "Daya stopped because the tea became far too sweet.", "The changing taste directly explains her choice.", "stopped overly sweet tea", "taste grew stronger"),
        _fresh_case("many puppies", "A wish brought twelve puppies into one small yard. They had little space, so the family called an animal shelter.", "Why was help needed?", "Help was needed because the small yard could not safely hold twelve puppies.", "The number and space clues show the mismatch.", "yard too small", "twelve puppies need space"),
        _fresh_case("warm snow", "A child wished for snow at a summer picnic. It melted at once and soaked the blankets.", "Why did the blankets become wet?", "The blankets became wet because summer heat melted the snow.", "Melted snow provides the water named in the result.", "snow melted blankets wet", "summer heat clue"),
        _fresh_case("fast cart", "A toy cart moved faster each time Arun clapped. It nearly hit a vase, so he stopped clapping.", "Why did Arun become quiet?", "Arun stopped because more claps made the cart dangerously fast.", "The near collision shows the risk.", "stopped clapping for safety", "cart nearly hit vase"),
        _fresh_case("paper rain", "Sana wished for paper notes to rain from the ceiling. They covered the floor and made people slip.", "Why did Sana collect the notes?", "She collected them because the covered floor was unsafe.", "The slipping clue shows why clean-up matters.", "collected unsafe papers", "people slipped floor"),
        _fresh_case("endless story", "A book continued its tale past midnight. Kabir yawned and missed the morning alarm.", "Why did Kabir close it earlier the next night?", "He closed it earlier because the endless reading left him tired.", "Yawning and the missed alarm show lost sleep.", "closed book earlier", "tired missed alarm"),
        _fresh_case("giant soap", "One soap bar filled the wash basin. Water could not reach the drain, so Evi cut off a small piece.", "What explains using only a piece?", "Evi used a small piece because the giant bar blocked the drain.", "The blocked water path is the needed clue.", "small piece chosen", "bar blocked drain"),
        _fresh_case("singing plates", "Every plate sang during dinner. The baby cried, so the family asked for quiet plates.", "Why did the family change the wish?", "They changed it because the singing plates upset the baby.", "The baby's crying follows the loud dinnerware.", "quiet plates for baby", "singing caused crying"),
        _fresh_case("one long scarf", "A scarf stretched across the lane and stopped bicycles. Mira folded it into short pieces.", "Why did she shorten the scarf?", "Mira shortened it because the long cloth blocked the lane.", "Stopped bicycles reveal the problem.", "shortened blocking scarf", "bicycles could not pass"),
        _fresh_case("juice fountain", "A wish made juice pour without stopping. Cups overflowed across the counter, so Bela closed the magic tap and fetched a cloth.", "Why did Bela end the juice wish?", "Bela ended it because the nonstop juice overflowed the cups and counter.", "The spreading spill shows that the unlimited amount caused a problem.", "ended overflowing juice", "spill across counter"),
        _fresh_case("bright lamp", "A lamp wished brighter after every clap. The glare hurt Arjun's eyes, and he covered the switch before asking for gentle light.", "What two clues explain Arjun's smaller-light request?", "Arjun changed the wish because repeated claps made the glare hurt his eyes.", "The brighter lamp and eye pain directly support his decision.", "changed because glare hurt", "claps increased brightness"),
        _fresh_case("book mountain", "Tara wished for every adventure book at once. The pile bent her shelf and blocked the doorway, so she kept three and returned the rest.", "Why did Tara reduce the number of books?", "Tara kept only three because the huge pile bent the shelf and blocked the door.", "Both the damaged shelf and blocked doorway show there were too many.", "kept three books", "shelf bent door blocked"),
    ],
    "wish_character_quality": [
        _fresh_case("patient queue", "Rohit waited quietly while two younger pupils used the tap first.", "Which quality does his action show?", "Rohit acts patient because he waits without pushing.", "Quiet waiting supports the adjective patient.", "patient waits quietly", "does not push"),
        _fresh_case("selfish box", "Nila hid every crayon even after three classmates asked to share.", "What quality fits this one action?", "Nila's action is selfish because she keeps all the crayons.", "Refusing to share the whole supply supports selfish.", "selfish keeps all", "refuses classmates"),
        _fresh_case("brave call", "Aman saw smoke near a bin and quickly called an adult instead of touching it.", "Which adjective describes the safe action?", "Aman acts brave and careful by calling an adult.", "He faces the problem while choosing a safe response.", "brave careful call", "adult handles smoke"),
        _fresh_case("polite request", "Mira said please when asking for a book and thanked the librarian afterward.", "What quality word fits?", "Mira acts polite because she uses respectful words.", "Please and thanks are direct clues.", "polite respectful words", "please and thanks"),
        _fresh_case("careless spill", "Tej carried an open paint jar while running, and paint splashed on the floor.", "Which quality describes the choice?", "Tej's choice is careless because he runs with an open jar.", "The risky action causes the stated spill.", "careless open jar", "running causes spill"),
        _fresh_case("honest score", "Ria noticed that her score had one extra point and told the teacher.", "What does Ria's action show?", "Ria acts honest because she reports the extra point.", "She tells the truth even though it lowers her score.", "honest reports point", "truth about score"),
        _fresh_case("kind umbrella", "Dev moved his umbrella so a stranger could stand under it too.", "Choose and explain a quality.", "Dev acts kind because he shares shelter in the rain.", "His movement answers another person's need.", "kind shares shelter", "helps stranger in rain"),
        _fresh_case("hasty answer", "Before reading the whole question, Pavi chose the first option and got it wrong.", "Which quality fits the decision?", "Pavi's decision is hasty because she answers too soon.", "Skipping the rest of the question shows haste.", "hasty answers early", "did not finish reading"),
        _fresh_case("generous fruit", "Kamal gave three of his five oranges to children without snacks.", "What adjective is supported?", "Kamal acts generous because he gives most of his fruit away.", "The amount shared is clearly shown.", "generous shares oranges", "gives most fruit"),
        _fresh_case("lazy task", "The tools were ready, but Yash stayed on the mat and asked others to do his small job.", "Which quality fits this moment?", "Yash acts lazy because he avoids the work he can do.", "The card shows no barrier except his choice.", "lazy avoids work", "tools already ready"),
        _fresh_case("thoughtful bottle", "Before a walk, Lata packed water for herself and one extra bottle for her cousin.", "What quality does planning show?", "Lata acts thoughtful because she plans for another person's need.", "The extra bottle is a clear caring detail.", "thoughtful extra water", "plans for cousin"),
        _fresh_case("cautious wish", "Vik read every rule on the magic card before choosing one small wish.", "Which adjective fits?", "Vik acts cautious because he checks the rules first.", "Reading before acting shows care.", "cautious checks rules", "reads before choice"),
        _fresh_case("responsible tools", "After using the craft knife with an adult, Sami returns it to the locked drawer and counts every blade cover.", "Which quality is shown in this one action?", "Sami acts responsible because he stores the tool safely and checks its covers.", "The locked drawer and count show careful ownership of a risky item.", "responsible safe storage", "locked drawer covers counted"),
        _fresh_case("impatient line", "Kuhu leaves her place, pushes ahead of two pupils, and demands the first turn at the telescope.", "What quality fits Kuhu's behaviour at this moment?", "Kuhu acts impatient because she will not wait for her turn.", "Pushing ahead of the line is direct evidence of not waiting.", "impatient skips turn", "pushes ahead line"),
        _fresh_case("creative carton", "When the dollhouse roof breaks, Zain folds a clean cereal carton into a new roof and tests that it stays dry.", "Which quality word fits Zain's repair?", "Zain acts resourceful because he turns a spare carton into a useful roof.", "Reusing available material solves the exact dollhouse problem.", "resourceful carton repair", "reuses material for roof"),
    ],
    "wish_connectors": [
        _fresh_case("fruit list", "Nora packed an apple. She also packed a pear.", "Join the related ideas with and.", "Nora packed an apple and a pear.", "And adds two foods packed by the same person.", "apple and pear", "adds related foods"),
        _fresh_case("thirst reason", "Kavi drank water. His throat felt dry.", "Use because to join action and reason.", "Kavi drank water because his throat felt dry.", "Dryness answers why he drank.", "drank because dry", "reason for water"),
        _fresh_case("wanted cake", "Meera wanted cake. She chose fruit instead.", "Join the surprising change with but.", "Meera wanted cake, but she chose fruit instead.", "But shows a choice different from the first wish.", "wanted but chose fruit", "contrast in choice"),
        _fresh_case("three items", "The box holds chalk. It holds paper. It holds string.", "Make one sentence with and.", "The box holds chalk, paper, and string.", "And joins the final item in one related list.", "chalk paper and string", "items in same box"),
        _fresh_case("closed stall", "Ria went to buy juice. The stall was closed.", "Which connector shows the problem?", "Ria wanted juice, but the stall was closed.", "The closed stall contrasts with her plan.", "wanted but stall closed", "plan meets problem"),
        _fresh_case("shared snack", "Avi shared his snack. His friend had no lunch.", "Write the reason with because.", "Avi shared his snack because his friend had no lunch.", "The missing lunch explains the sharing.", "shared because no lunch", "reason answers why"),
        _fresh_case("washed fruit", "Pia washed the grapes. She placed them in a bowl.", "Use and to show two linked actions.", "Pia washed the grapes and placed them in a bowl.", "The same subject does both actions in order.", "washed and placed", "same person actions"),
        _fresh_case("full bag", "Omar liked the toy. His bag had no space.", "Join the contrast correctly.", "Omar liked the toy, but his bag had no space.", "Liking it conflicts with being unable to carry it.", "liked but no space", "clear contrast"),
        _fresh_case("umbrella reason", "Sana opened her umbrella. Rain began.", "Which because sentence fits?", "Sana opened her umbrella because rain began.", "Rain supplies the reason for opening it.", "opened because rain", "weather reason"),
        _fresh_case("wish and plan", "Tara made a small wish. She wrote a careful plan.", "Add both ideas with and.", "Tara made a small wish and wrote a careful plan.", "Both related actions belong to Tara.", "wished and planned", "related Tara actions"),
        _fresh_case("sweet but sour", "The fruit looked sweet. Its first bite tasted sour.", "Use but for the difference.", "The fruit looked sweet, but it tasted sour.", "Appearance and taste do not match.", "looked sweet but sour", "appearance taste contrast"),
        _fresh_case("rest reason", "Nitin sat under the tree. His legs were tired.", "Join the ideas with because.", "Nitin sat under the tree because his legs were tired.", "Tired legs explain why he rested.", "sat because tired", "rest reason"),
        _fresh_case("banner list", "The fair banner needs a date. It also needs a gate number.", "Join the two related banner needs with and.", "The fair banner needs a date and a gate number.", "And adds two useful details for the same banner.", "date and gate number", "related banner details"),
        _fresh_case("wanted swing", "Anil wanted the swing. A younger child was already using it.", "Use but to show the playground contrast.", "Anil wanted the swing, but a younger child was already using it.", "But connects his wish with the reason he cannot act immediately.", "wanted swing but occupied", "younger child using it"),
        _fresh_case("closed window", "Meera closed the window. Dust was blowing into the room.", "Write the complete because sentence.", "Meera closed the window because dust was blowing into the room.", "The blowing dust gives the reason for closing it.", "closed window because dust", "dust blowing inside"),
    ],
    "wish_main_idea_words": [
        _fresh_case("enough rice", "The pot contains one bowl of rice for each of six guests and one bowl extra.", "What does enough mean here?", "There is enough rice because every guest can receive a bowl.", "The number of bowls meets the stated need.", "enough for every guest", "bowls meet need"),
        _fresh_case("replace torch", "The old torch no longer lights. Mina puts a working torch in its place.", "Use replace in a summary.", "Mina replaces the broken torch with one that works.", "The working item takes the old item's place.", "replaces broken torch", "new takes old place"),
        _fresh_case("plenty pencils", "Twenty pencils sit in a box for four pupils, so several will remain unused.", "Which meaning fits plenty?", "The group has plenty of pencils for the task.", "The amount is more than the group needs.", "plenty of pencils", "more than needed"),
        _fresh_case("need water", "The walkers have many sweets but no drink on a hot path. They stop at a water point first.", "What is the main idea?", "Water is the walkers' urgent need even though they have lots of sweets.", "The first stop shows which item matters most.", "water is needed", "hot path no drink"),
        _fresh_case("enough chairs", "Eight chairs are set for eight readers. No one must stand.", "Explain enough with the card.", "Eight chairs are enough because each reader has a seat.", "The equal counts show the need is met.", "enough chairs for readers", "equal counts meet need"),
        _fresh_case("replace lid", "A cracked lid leaks. The cook removes it and uses a tight lid.", "What does replace mean in this action?", "The cook replaces the cracked lid with a tight one.", "One lid is removed and another takes its job.", "replace cracked lid", "tight lid takes place"),
        _fresh_case("plenty fruit", "The basket has thirty guavas for ten children, with three guavas planned for each child.", "Which quantity word fits?", "The basket has plenty of guavas for the children.", "The count exactly covers a generous share.", "plenty guavas", "three each available"),
        _fresh_case("shoe need", "Ritu owns many ribbons, but her shoe has no lace and keeps slipping.", "Which detail states the real need?", "Ritu needs a shoe lace, not more ribbons.", "The slipping shoe identifies the useful item.", "needs shoe lace", "slipping shows need"),
        _fresh_case("enough paint", "One small jar covers the entire sign, and some paint remains.", "How is enough used correctly?", "The jar holds enough paint for the sign.", "Finishing with paint left shows the amount was sufficient.", "enough paint for sign", "some remains after"),
        _fresh_case("replace page", "A worksheet page is soaked and unreadable. The teacher gives a clean copy.", "State the action with replace.", "The clean copy replaces the unreadable page.", "The new page serves the same task.", "copy replaces page", "new page same task"),
        _fresh_case("plenty time", "The work takes ten minutes, and the class has half an hour before lunch.", "What does plenty tell us?", "The class has plenty of time to finish the work.", "Thirty minutes is more than the ten needed.", "plenty of time", "thirty more than ten"),
        _fresh_case("main need", "A picnic list names cakes, games, cups, and clean drinking water. The weather note says the day will be very hot.", "Which need should guide the plan?", "Clean drinking water is the main need on the hot day.", "The weather clue makes water important for everyone.", "water main need", "hot weather clue"),
        _fresh_case("enough masks", "The drama group has twelve performers and twelve clean masks, one labelled for each person.", "Use enough in the main idea of the mask card.", "The group has enough masks because every performer has one labelled mask.", "Equal counts show the costume need is fully met.", "enough masks for performers", "twelve for twelve"),
        _fresh_case("replace marker", "The black marker is dry and leaves no line. Jaya puts it aside and uses a working marker for the sign.", "Use replace to summarise Jaya's action.", "Jaya replaces the dry marker with one that writes clearly.", "The working marker takes the failed marker's job.", "replaces dry marker", "working one takes place"),
        _fresh_case("plenty seedlings", "The garden club has eighteen seedlings for six pots and plans two plants in each pot.", "Which quantity word fits, and what is the card's main idea?", "The club has plenty of seedlings because twelve are needed and eighteen are available.", "The available count is greater than the planned amount.", "plenty of seedlings", "eighteen exceeds twelve"),
    ],
    "wish_story_continuation": [
        _fresh_case("silver key", "Navi found a silver key under the banyan tree. A tiny label said, 'Use me before sunset.'", "Continue the story in two past-tense sentences.", "Navi tried the key in the old garden gate. It opened a box holding seed packets.", "The gate and box give a possible next event before sunset.", "Navi tried silver key", "box held seeds"),
        _fresh_case("empty basket", "A magic basket gave fruit whenever Mina clapped. She clapped too often, and fruit rolled toward the stairs.", "Write what happened next.", "Mina stopped clapping and called her brother. They packed the fruit before anyone slipped.", "Stopping and packing solve the rolling-fruit problem.", "Mina stopped clapping", "packed fruit safely"),
        _fresh_case("paper bird story", "Story starter: A paper bird flew from Rohan's book and circled the room. It carried a note tied to one wing.", "Add a fitting next story event.", "Rohan caught the bird gently and untied the note. The message showed a map of the school garden.", "The continuation follows the bird and its visible note.", "Rohan caught bird", "note showed map"),
        _fresh_case("noisy jar", "A jar hummed louder each time Tara touched it. The baby in the next room woke up.", "Continue the problem and repair.", "Tara wrapped the jar in a towel and placed it on a shelf. The humming became soft.", "The towel answers the loud-sound problem without adding a new place.", "Tara wrapped jar", "humming became soft"),
        _fresh_case("moon seeds", "Ira planted three pale seeds at dusk. By midnight, thin silver stems reached the window.", "What could happen next?", "Ira tied the stems to short sticks so they did not bend. In the morning, white flowers opened.", "The support and flowers continue the shown plant growth.", "Ira tied stems", "white flowers opened"),
        _fresh_case("frozen fountain", "A wish froze the courtyard fountain on a warm day. Children could no longer fill their water cans.", "Write a useful next event.", "The wish-maker asked for the ice to melt slowly. Soon the tap flowed and the children filled their cans.", "Melting fixes the water problem already shown.", "ice melted slowly", "tap flowed again"),
        _fresh_case("walking shoes", "Jai's new shoes walked by themselves toward the market. Jai ran after them with one sock on.", "Continue with the same character and problem.", "Jai caught the laces at the corner and tied the shoes together. He carried them home under his arm.", "Catching and tying stop the moving shoes.", "Jai caught laces", "carried shoes home"),
        _fresh_case("giant pumpkin", "A pumpkin grew until it blocked the garden gate. Neighbours waited outside with empty baskets.", "Add two linked sentences.", "The gardener cut a safe opening with adult help. Then the neighbours carried pumpkin pieces home in their baskets.", "The opening clears the gate and the baskets gain a clear use.", "opened blocked gate", "neighbours carried pieces"),
        _fresh_case("whispering wall", "The kitchen wall whispered one recipe every morning. On Tuesday, it stopped after naming only the first ingredient.", "What happened next?", "Leena wrote down the first ingredient and waited quietly. At noon, the wall finished the recipe.", "The continuation keeps the wall and unfinished recipe.", "Leena wrote ingredient", "wall finished recipe"),
        _fresh_case("floating desk", "A classroom desk rose a handspan above the floor during a spelling lesson. Books began sliding from its top.", "Continue the event safely.", "The pupils caught the books and stepped back. Their teacher lowered the desk with the button underneath.", "The actions answer the sliding-book problem in the same room.", "pupils caught books", "teacher lowered desk"),
        _fresh_case("rainbow soup", "Vina stirred soup, and seven colours appeared on its surface. The soup smelled normal, but nobody knew if it was safe.", "Write a careful next part.", "Vina did not taste the soup. She called an adult, who checked the coloured spice packet.", "Waiting and asking an adult fit the safety doubt.", "Vina did not taste", "adult checked packet"),
        _fresh_case("clock wish", "A clock stopped time for one minute when Om pressed its blue button. He pressed it while a ball rolled toward a puddle.", "How could the story continue?", "Om moved the stopped ball away from the puddle. When time began again, it rolled safely onto the grass.", "The next action uses the one-minute pause and the shown ball.", "Om moved stopped ball", "rolled onto grass"),
        _fresh_case("glowing pebble", "A pebble in Siya's pocket began glowing whenever she walked toward the old well. At the gate, its light turned green.", "Continue the glowing-pebble story in past tense.", "Siya stopped at the gate and showed the green pebble to her grandmother. Together they followed the safe path around the well.", "The continuation keeps Siya, the pebble, and the well while choosing adult help.", "Siya showed green pebble", "followed safe path"),
        _fresh_case("tiny door", "A tiny door appeared behind Rohan's bookshelf. A paper note underneath said, 'Bring one seed.'", "Write two past-tense sentences that continue the same mystery.", "Rohan chose one bean seed and knocked on the tiny door. A small hand opened it and traded the seed for a silver button.", "The seed instruction leads directly to the knock and trade.", "Rohan chose seed", "door traded silver button"),
        _fresh_case("singing umbrella", "Maya's umbrella sang whenever rain touched it. On the quiet library steps, a shower began and the song grew loud.", "Continue the umbrella problem with the same setting and characters.", "Maya closed the umbrella under the covered steps. She waited there until the shower ended and the song stopped.", "Closing it under shelter solves the loud-song problem without leaving the library.", "Maya closed umbrella", "waited until song stopped"),
    ],
}

for _level_spec in SPEC["levels"]:
    _level_spec["fresh_cases"] = FRESH_CASES[_level_spec["level_id"]]


SPEC["assessment_pairs"] = [
    _assessment_pair("reading.event_sequence", _case("wish paint", "A pot made too much paint, the floor became crowded with jars, and Uma gave extras to the art room.", "Which order matches?", "Paint appeared, jars crowded the floor, and Uma shared extras.", "Uma shared before any paint appeared.", "The floor made a wish.", "The problem sits between the wish result and repair.", "appeared crowded shared", "problem before repair"), _case("wish bread", "Bread filled Ravi's table, blocked his books, and was packed for neighbours.", "What happened after the books were blocked?", "Ravi packed bread for neighbours.", "Ravi wished after packing.", "The books baked bread.", "Packing is the stated final repair.", "packed bread last", "after blocked books"), kind="choice"),
    _assessment_pair("reading.sentence_comprehension", _case("juice card", "Nila asked for juice, but the cup poured soup. Nila pushed the cup away.", "Who pushed the cup, and why?", "Nila pushed it because it gave soup instead of juice.", "The cup pushed Nila for asking.", "Soup asked for juice.", "The subject and contrast are printed clearly.", "Nila pushed cup", "soup instead of juice"), _case("seed card", "Dev planted one magic seed. His sister covered it with soil while Dev fetched water.", "Who covered the seed?", "Dev's sister covered the seed.", "Dev covered it while fetching water.", "The seed covered the sister.", "The subject before covered names his sister.", "sister covered seed", "subject before verb"), kind="choice"),
    _assessment_pair("reading.inference_reason", _fresh_case("salty wish", "A plate produced salty chips all afternoon. Lila's lips felt dry, and she asked for a water jug.", "Why did she ask for water?", "Lila asked for water because the salty chips made her thirsty.", "Dry lips and the new request support the reason.", "water because thirsty", "salty dry lips"), _fresh_case("bright room", "A magic lamp lit every corner at midnight. Arjun covered it when his eyes would not close.", "Why did Arjun cover the lamp?", "He covered it because the bright light stopped him from sleeping.", "Midnight and open eyes show the problem.", "covered light to sleep", "bright at midnight"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("crowded toys", "Thirty toy drums filled one small shelf and pushed the books off.", "Explain why keeping only three drums would help.", "Keeping three drums would help because the books need space on the shelf.", "The crowded shelf and fallen books give the reason.", "three drums leave space", "books pushed off"), _fresh_case("melting sweets", "Chocolate wishes melted on a sunny step and made the path slippery.", "Write why the sweets should be moved.", "The sweets should be moved because the melted chocolate makes the path slippery.", "The heat and unsafe path are stated clues.", "move melted sweets", "slippery path reason"), kind="open"),
    _assessment_pair("reading.word_meaning_context", _case("hasty choice", "Kira chose before reading any rule. The card calls her choice hasty.", "What does hasty mean?", "Hasty means done too quickly.", "Hasty means planned for weeks.", "Hasty means generous with food.", "Choosing before reading shows speed without care.", "hasty too quick", "before reading rules"), _case("considerate act", "Mo moved his bag so an older rider could sit. The note calls him considerate.", "Which meaning fits?", "Considerate means caring about another person's need.", "Considerate means hiding every seat.", "Considerate means unable to move.", "Making room is the context clue.", "considerate cares for others", "moves bag for rider"), kind="choice"),
    _assessment_pair("grammar.noun_verb_adjective", _case("kind word role", "In 'The kind child shared lunch,' the task asks about kind.", "What job does kind do?", "Kind is an adjective describing child.", "Kind is the action verb.", "Kind is the lunch noun.", "It tells what the child is like.", "kind is adjective", "describes child"), _case("wish word role", "In 'Tara wished for rain,' the task asks about wished.", "Which word job fits wished?", "Wished is the verb showing Tara's action.", "Wished is an adjective for rain.", "Wished is Tara's name.", "It tells what Tara did.", "wished is verb", "shows Tara action"), kind="choice"),
    _assessment_pair("grammar.connectors_because_and_but", _case("contrast join", "I like mangoes. I did not choose one today.", "Which joined sentence shows contrast?", "I like mangoes, but I did not choose one today.", "I like mangoes because I did not choose one.", "I like and but mangoes.", "But marks the surprising difference.", "like but did not choose", "clear contrast"), _case("reason join", "Nia carried water. The day was hot.", "Which sentence gives the reason?", "Nia carried water because the day was hot.", "Nia carried water but the day was hot as its reason.", "Because Nia hot water.", "Hot weather answers why.", "carried because hot", "reason for water"), kind="choice"),
    _assessment_pair("writing.complete_sentence", _fresh_case("and sentence", "Ideas: Reva packed bread. Reva packed fruit.", "Join both related ideas with and in one complete sentence.", "Reva packed bread and fruit for the walk.", "The subject and action stay clear while and adds an item.", "Reva packed bread fruit", "and adds food"), _fresh_case("because sentence", "Ideas: Om sat down. His feet hurt.", "Write one complete because sentence.", "Om sat down because his feet hurt after the walk.", "The second part explains the first action.", "sat because feet hurt", "reason completes sentence"), kind="open", interaction_type="paragraph_text"),
    _assessment_pair("reading.paragraph_main_idea", _fresh_case("need first", "The picnic basket held cakes, toys, and plates, but no water. Everyone walked to the tap before eating.", "What idea covers the paragraph?", "Clean water was the main need even though the picnic had many other things.", "The group's first action shows the most important missing item.", "water was main need", "tap before eating"), _fresh_case("small wish", "Pia checked her shelf, counted its free spaces, and chose two books instead of twenty.", "State the main idea.", "Pia made a careful wish that fitted the space she had.", "Checking and counting guide her smaller choice.", "careful wish fits space", "counted free places"), kind="open"),
    _assessment_pair("vocab.chapter_word_usage", _case("enough usage", "Six cups are ready for six guests.", "Which sentence uses enough correctly?", "There are enough cups for every guest.", "Enough means no guest gets a cup.", "Enough is a kind of cup handle.", "Equal counts meet the need.", "enough cups for all", "six for six"), _case("replace usage", "A torn bag is removed and a strong bag takes its place.", "Which sentence uses replace?", "They replace the torn bag with a strong one.", "Replace means keep both bags hidden.", "Replace names the colour of the bag.", "One item takes the old item's job.", "replace torn bag", "strong takes place"), kind="choice"),
    _assessment_pair("grammar.tense_usage", _fresh_case("past seed", "Time clue: yesterday. Mira plants one seed and waters it.", "Rewrite the action in past tense.", "Yesterday, Mira planted one seed and watered the soil.", "Planted and watered match the completed time.", "Mira planted watered", "yesterday past verbs"), _fresh_case("past jar", "Time clue: last night. The jar hums and wakes Ravi.", "Report both actions in past tense.", "Last night, the jar hummed and woke Ravi.", "Hummed and woke match last night.", "jar hummed woke", "last night past"), kind="open"),
    _assessment_pair("writing.short_answer", _fresh_case("continue basket", "A basket rolled fruit toward the doorway. Sumi saw a child entering.", "Continue the story in two past-tense sentences.", "Sumi stopped the basket and moved the fruit away. The child entered safely.", "The continuation answers the doorway danger and keeps Sumi.", "Sumi stopped basket", "child entered safely"), _fresh_case("continue kite", "A magic kite pulled Nikhil toward a muddy field. He held the string with both hands.", "Add a sensible next part.", "Nikhil called his sister, and she helped pull the kite down. They carried it home.", "The help solves the pulling problem with the same kite.", "sister helped pull", "carried kite home"), kind="open", interaction_type="creative_continuation"),
    _assessment_pair("reading.inference_reason", _fresh_case("empty jug", "The table has many sweet drinks, but Ritu reaches for an empty water jug and looks worried.", "What need can you infer?", "Ritu needs plain water even though other drinks are present.", "Her choice of jug over sweet drinks gives the clue.", "needs plain water", "reaches for water jug"), _fresh_case("few blocks", "After a tower fell twice, Sam chose four wide blocks instead of twelve narrow ones.", "Why did Sam change the blocks?", "Sam wanted a steadier tower after the narrow one fell.", "The repeated falls explain the wider smaller set.", "wanted steady tower", "narrow tower fell"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("share fruit", "One bowl has twelve guavas for four children, while another child has none.", "Write why sharing is a fair choice.", "Sharing is fair because there are plenty of guavas and one child has none.", "The counts and missing share support the answer.", "sharing guavas is fair", "plenty and none"), _fresh_case("stop music", "A music box played after midnight and woke two people.", "Explain why it should be stopped.", "The music box should be stopped because its late sound woke people.", "Midnight and waking are direct reasons.", "stop late music", "woke two people"), kind="open"),
]


_SEMANTIC_OPTION_REPLACEMENTS = {'The shelf orders her to plant a tree.': 'Pema changes her request because fruit is '
                                          'easier to carry.'}
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
