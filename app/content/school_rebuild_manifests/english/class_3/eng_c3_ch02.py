"""Deep authored manifest for Class 3 English Chapter 2.

NCERT material informed only the chapter map and exercise modalities. All
runtime passages, questions, choices, rubrics, and answers are original.
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


CHAPTER_ID = "eng_c3_ch02"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/cesa102.pdf"


SOURCE_ANCHORS = [
    {"anchor_id": f"{CHAPTER_ID}:read:15-17", "section_label": "Let us Read: Care, Search, and Rescue Narrative", "page_start": 15, "page_end": 17, "source_url": f"{SOURCE_URL}#page=15", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:think:18", "section_label": "Let us Think: Recall, Inference, and Pet Responsibility", "page_start": 18, "page_end": 18, "source_url": f"{SOURCE_URL}#page=18", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:learn:19", "section_label": "Let us Learn: Past Actions and Word Pairing", "page_start": 19, "page_end": 19, "source_url": f"{SOURCE_URL}#page=19", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:listen:20", "section_label": "Let us Listen: Spoken Story Sequencing", "page_start": 20, "page_end": 20, "source_url": f"{SOURCE_URL}#page=20", "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:speak:21", "section_label": "Let us Speak: Daily Routine Exchange", "page_start": 21, "page_end": 21, "source_url": f"{SOURCE_URL}#page=21", "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:write:21-23", "section_label": "Let us Write: Ordered Story, Punctuation, and Conversation", "page_start": 21, "page_end": 23, "source_url": f"{SOURCE_URL}#page=21", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:do:24", "section_label": "Let us Do: Optional Picture Extension", "page_start": 24, "page_end": 24, "source_url": f"{SOURCE_URL}#page=24", "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
]


CRUNCH_BAR = {
    "rescue_sequence_and_main_idea": _crunch(
        [
            (
                "A hamster pushed open its travel-box flap, hid behind seed sacks, squeaked when the shop became quiet, and was returned after the owner showed its card.",
                "The hamster escaped first, hid next, squeaked in the quiet shop, and returned after its card was checked. A sound clue and identity card led to a safe return.",
                ["escaped first", "hid next", "squeaked then returned"],
                ["sound clue and identity card", "led to a safe return"],
            ),
            (
                "A library pouch fell beside a stair. A cleaner noticed its stitched initials, called the class teacher, and placed it in the office cupboard.",
                "The pouch fell first, the cleaner noticed the initials, called the teacher, and stored it last. The initials helped return lost class property responsibly.",
                ["fell first", "noticed initials", "stored last"],
                ["initials helped return property", "responsible lost-property return"],
            ),
            (
                "Wind blew a pet-care chart from a balcony. It caught on a neem branch, a gardener read the flat number, and the family collected it.",
                "Wind carried the chart first, the branch caught it next, and the gardener used the flat number before the family collected it. Written details solved the loss.",
                ["wind carried first", "branch caught next", "family collected last"],
                ["flat number solved the loss", "written details helped return it"],
            ),
            (
                "A lamb slipped through a hedge, left wool on a thorn, and bleated near a dry pond. The shepherd followed both clues and mended the gap.",
                "The lamb slipped out first, wool marked the path, and its bleat revealed the pond before the hedge was mended. Two clues helped recover it and stop another escape.",
                ["slipped out first", "wool marked path", "hedge mended last"],
                ["two clues helped recover it", "stopped another escape"],
            ),
            (
                "A violin case was left on a train seat. The conductor found a concert ticket inside, phoned the music school, and locked the case in the station office.",
                "The case was left first, the ticket identified the music school, and the conductor phoned before storing it securely. The ticket supported a safe return.",
                ["left first", "ticket identified school", "stored securely last"],
                ["ticket supported a safe return", "conductor used the concert clue"],
            ),
        ],
        prompt="Put the events in order and tell the main idea.",
        interaction_type="summary",
        ordered=True,
    ),
    "care_inference_and_reason": _crunch(
        [
            (
                "A tortoise stays under its shelter at noon and stretches its neck toward a fresh water dish without leaving the shade.",
                "Place the water dish within the shaded area because the tortoise is avoiding the hot ground but is reaching toward water.",
                ["place water in the shade", "move the dish within reach"],
                ["avoiding hot ground", "reaching toward water"],
            ),
            (
                "A young bird is tangled in loose garden netting. It is still breathing, and a wildlife rescue number is posted on the gate.",
                "Keep people back and call the wildlife rescue number because pulling the net without training could hurt the breathing bird.",
                ["keep people back and call rescue", "contact the wildlife helper"],
                ["pulling could hurt the bird", "bird is tangled but breathing"],
            ),
            (
                "A cat enters an open carrier for treats but backs away when the door is pushed quickly. An adult can close it slowly.",
                "Let the adult close the carrier slowly after the cat enters because the quick door movement makes the cat back away.",
                ["adult closes the carrier slowly", "wait until the cat enters"],
                ["quick movement makes it back away", "cat enters for treats"],
            ),
            (
                "Fish gather near the filter outlet, but only a few bubbles appear. The care card says an adult must check the air tube.",
                "Tell an adult to check the air tube because the weak bubbles and gathered fish may show that the water needs more air.",
                ["tell an adult to check the tube", "ask for an air-tube check"],
                ["weak bubbles and gathered fish", "water may need more air"],
            ),
            (
                "A pony lifts one front hoof after crossing a stony lane. The handler is beside it, and the stable helper has hoof tools.",
                "The handler should stop and call the stable helper because the lifted hoof after the stony lane may need a safe check.",
                ["stop and call the stable helper", "ask for a hoof check"],
                ["lifted hoof after stones", "safe check is needed"],
            ),
        ],
        prompt="Choose the safest action and give the card clue as your reason.",
    ),
    "rescue_words_in_context": _crunch(
        [
            (
                "The sudden clang startled the puppy, making it jump and look around at once.",
                "Startled means suddenly surprised or frightened. New sentence: A falling tray startled the sleeping cat.",
                ["suddenly surprised or frightened", "jumped at the clang"],
                ["tray startled the cat", "startled the sleeping cat"],
            ),
            (
                "After the long search, the weary volunteer sat down because her legs felt heavy.",
                "Weary means very tired. New sentence: The weary pony rested after the steep path.",
                ["very tired", "heavy legs after search"],
                ["weary pony rested", "tired after the path"],
            ),
            (
                "The guard made the carrier secure by fastening both clips so the door could not swing open.",
                "Secure means safely fastened. New sentence: We kept the medicine box secure on a high shelf.",
                ["safely fastened", "clips stopped the door opening"],
                ["medicine box secure", "secure on a high shelf"],
            ),
            (
                "Nora waited patiently, without rushing or complaining, while the shy rabbit came closer.",
                "Patiently means waiting calmly. New sentence: Arjun patiently held the gate while the goats passed.",
                ["waiting calmly", "without rushing"],
                ["patiently held the gate", "calmly waited for goats"],
            ),
            (
                "The sturdy crate did not bend when two heavy food bags were placed inside it.",
                "Sturdy means strong and not easy to bend. New sentence: A sturdy fence kept the calves inside the field.",
                ["strong and not easy to bend", "held heavy bags"],
                ["sturdy fence", "strong fence kept calves in"],
            ),
        ],
        prompt="Explain the bold word from the clue, then use it in a new sentence.",
    ),
    "past_actions_in_order": _crunch(
        [
            (
                "Yesterday / the helper / wrap / the injured wing box / in a towel / carefully.",
                "Yesterday, the helper carefully wrapped the injured wing box in a towel. Wrapped shows a finished action.",
                ["carefully wrapped", "finished action wrapped"],
                ["helper wrapped the box", "in a towel yesterday"],
            ),
            (
                "Last evening / Mira / bring / clean bowls / to the shelter / quietly.",
                "Last evening, Mira quietly brought clean bowls to the shelter. Brought is the past form of bring.",
                ["quietly brought", "past form brought"],
                ["Mira brought clean bowls", "to the shelter last evening"],
            ),
            (
                "Two hours ago / the vet / check / the puppy's paw / at the clinic.",
                "Two hours ago, the vet checked the puppy's paw at the clinic. Checked matches the completed time clue.",
                ["vet checked", "completed form checked"],
                ["puppy's paw at the clinic", "two hours ago"],
            ),
            (
                "On Sunday / our group / find / three empty water trays / behind the shed.",
                "On Sunday, our group found three empty water trays behind the shed. Found is the past form of find.",
                ["group found", "past form found"],
                ["three empty water trays", "behind the shed on Sunday"],
            ),
            (
                "Before sunrise / the farmer / lead / the lost calf / back through the gate.",
                "Before sunrise, the farmer led the lost calf back through the gate. Led is the past form of lead.",
                ["farmer led", "past form led"],
                ["lost calf through the gate", "before sunrise"],
            ),
        ],
        prompt="Use the past-tense verb and put every detail in a clear sentence.",
        interaction_type="short_text",
    ),
    "questions_and_punctuation": _crunch(
        [
            (
                "Draft: when did aman feed the rabbit. Answer fact: Aman fed it at seven.",
                "When did Aman feed the rabbit? Aman fed it at seven. Both sentences begin with capitals and use the right end marks.",
                ["When did Aman feed", "capital letter for Aman"],
                ["question mark and full stop", "right end marks"],
            ),
            (
                "Draft: where is the blue carrier. Answer fact: The carrier is beside Neha.",
                "Where is the blue carrier? The carrier is beside Neha. The question and name use capitals and correct end marks.",
                ["Where is the blue carrier", "capital letter for Where"],
                ["question mark", "Neha and full stop"],
            ),
            (
                "Draft: did salim close the gate. Answer fact: Yes, Salim closed it.",
                "Did Salim close the gate? Yes, Salim closed it. Salim has a capital letter, and each sentence has the right end mark.",
                ["Did Salim close", "capital letter for Salim"],
                ["question mark", "full stop after the answer"],
            ),
            (
                "Draft: why is moti under the bench. Answer fact: The sun is hot.",
                "Why is Moti under the bench? Moti is there because the sun is hot. Moti begins with a capital, and both end marks are correct.",
                ["Why is Moti", "capital letter for Moti"],
                ["question mark and full stop", "correct end marks"],
            ),
            (
                "Draft: who called lake road clinic. Answer fact: Rina called it.",
                "Who called Lake Road Clinic? Rina called it. The place name and Rina use capitals, with a question mark and full stop.",
                ["Who called Lake Road Clinic", "capital letters for the place name"],
                ["question mark and full stop", "Rina called it"],
            ),
        ],
        prompt="Rewrite the question and answer with the right capitals and end marks.",
        interaction_type="short_text",
    ),
    "responsive_rescue_dialogue": _crunch(
        [
            (
                "Sana says the bird bath is empty. Reply as Mohit, who will fetch clean water.",
                "Sana said, 'The bird bath is empty.' Mohit replied, 'I will fetch clean water for it.'",
                ["Sana said", "bird bath is empty"],
                ["Mohit replied", "fetch clean water"],
            ),
            (
                "A guard asks Leela for the number on a red tag. Leela reads 4127.",
                "The guard asked, 'What number is on the red tag?' Leela replied, 'The number is 4127.'",
                ["guard asked", "number on the red tag"],
                ["Leela replied", "number is 4127"],
            ),
            (
                "Rafi warns that a kitten is near the bicycle wheel. Tara agrees to hold the bicycle still.",
                "Rafi warned, 'A kitten is near the bicycle wheel.' Tara replied, 'I will hold the bicycle still.'",
                ["Rafi warned", "kitten near the wheel"],
                ["Tara replied", "hold the bicycle still"],
            ),
            (
                "The shelter worker asks why the dog is wet. Neer explains that it crossed a flooded lane.",
                "The worker asked, 'Why is the dog wet?' Neer replied, 'It crossed a flooded lane.'",
                ["worker asked", "Why is the dog wet"],
                ["Neer replied", "crossed a flooded lane"],
            ),
            (
                "Ira says the medicine card is missing. Dev suggests checking the labelled folder with an adult.",
                "Ira said, 'The medicine card is missing.' Dev replied, 'Let us ask an adult to check the labelled folder.'",
                ["Ira said", "medicine card is missing"],
                ["Dev replied", "adult checks the labelled folder"],
            ),
        ],
        prompt="Write both speakers' lines with clear reporting words and punctuation.",
        interaction_type="dialogue",
        min_words=12,
    ),
}


LEVELS = [
    _make_level(
        level_id="rescue_sequence_and_main_idea",
        title="Track a rescue from clue to result",
        focus="sequence a short rescue narrative and state its central idea",
        outcome="Order the problem, search clue, action, and safe result, then compress them into an accurate one-sentence main idea.",
        skill_ids=["reading.event_sequence", "reading.paragraph_main_idea"],
        choice_skill_ids=["reading.event_sequence"],
        episode_kind="comprehension_studio",
        source_anchor_ids=[f"{CHAPTER_ID}:read:15-17", f"{CHAPTER_ID}:think:18"],
        principle="Time and cause clues establish what happened first, while a main idea joins the problem, useful response, and result without retelling every detail.",
        connect={"teaching_block": "A rescue account becomes clear when the reader tracks the missing subject, the clue that changes the search, the helpful action, and the ending.", "passage": "A rainstorm loosened a rabbit hutch latch. The family noticed paw marks under the awning, followed them to a shed, and carried the dry rabbit home.", "prompt": "Trace the escape, clue, search, and return before naming the story's whole idea."},
        choice_prompt="Which event comes first, second, or last as named in the card?",
        response_prompt="order the key events and state the main idea in one concise sentence.",
        rubric_descriptions=["Orders the problem, clue, action, and result accurately.", "States a main idea that includes both the response and outcome."],
        crunch_bar=CRUNCH_BAR["rescue_sequence_and_main_idea"],
        examples=[
            _q("A kitten slipped into a storeroom, knocked a tin, and mewed until the guard opened the door.", "The guard opened the storeroom door.", ["The kitten entered the storeroom.", "A tin made a sound.", "The guard locked the kitten outside."], prompt="Which rescue action came last?"),
            _q("First, Pema noticed an empty bird cage. Next, she found feathers near the balcony plant. Finally, she saw the bird perched on a curtain rod.", "She found feathers near the balcony plant.", ["She noticed the empty cage.", "She saw the bird last.", "She carried the cage downstairs."]),
            _r("A puppy ran after a cart. Its blue collar caught on a low branch. A fruit seller heard the collar bell, freed it, and called the number on its tag.", "The puppy chased a cart first, became caught next, and was freed before its owner was called. The main idea is that a seller used sound and tag clues to rescue and return a trapped puppy.", [["chased first", "caught next", "freed before call"], ["sound and tag clues", "rescue and return"]], ordered=True),
            _r("A tortoise left an open garden pen. Wet tracks crossed the path toward cabbages. The gardener followed them, found the tortoise, and repaired the gate.", "The tortoise escaped first, the gardener followed wet tracks, and the gate was repaired after the animal returned. The passage shows a gardener using tracks to recover a pet and prevent another escape.", [["escaped first", "followed tracks", "repaired after return"], ["recover a pet", "prevent another escape"]], ordered=True),
            _r("During a fair, a child lost a small drum. A stall owner heard a soft beat under a bench, retrieved the drum, and checked the name written inside it.", "The drum was lost, heard under a bench, retrieved, and identified in that order. The central idea is that careful listening and a written name helped return a lost object.", [["lost", "heard", "retrieved", "identified"], ["listening and written name", "return a lost object"]], ordered=True),
            _r("A school dog wandered beyond the playground. Pupils told the caretaker, who found fresh paw prints beside the water tap and followed them to the bicycle stand.", "The dog wandered away first, pupils reported it, and the caretaker followed prints to find it. The main idea is that prompt reporting and track clues led to the dog's safe recovery.", [["wandered", "reported", "followed prints"], ["prompt reporting", "safe recovery"]], ordered=True),
            _r("A parakeet flew from a window during cleaning. The family placed its familiar food on the sill and waited quietly. It returned at sunset, and they closed the screen.", "The bird flew out, the family set food and waited, and it returned before the screen was secured. The passage shows a calm familiar lure bringing a pet home safely.", [["flew out", "food and waited", "returned", "secured screen"], ["calm familiar lure", "home safely"]], ordered=True),
            _r("A calf strayed through a field gate. Its owner heard the bell near tall grass, led it back with fodder, and tied the loose gate rope.", "The calf strayed first, its bell revealed the location, and fodder helped lead it back before the gate was fixed. The main idea is that sound and a familiar food supported a safe return.", [["strayed", "bell revealed", "led back", "gate fixed"], ["sound and food", "safe return"]], ordered=True),
            _r("Nuru could not find her library pouch. She retraced her route, saw a purple strap beneath the bus seat, and gave the pouch number to the driver before collecting it.", "Nuru retraced her route, spotted the strap, verified the number, and collected the pouch. The passage is mainly about using visible and identity clues to recover a lost item responsibly.", [["retraced", "spotted", "verified", "collected"], ["visible and identity clues", "recover responsibly"]], ordered=True),
            _q("A hen left the yard, scattered grain showed its direction, and the keeper found it beside the compost bin. What happened immediately before the hen was found?", "The keeper followed the scattered grain.", ["The hen returned by itself.", "The bin was moved into the yard.", "The keeper closed the gate first."]),
            _r("A goat's rope came loose near dusk. A neighbour saw chewed leaves along a lane, followed the trail, and found the goat at an empty plot.", "The rope loosened first, the neighbour noticed chewed leaves, and the trail led to the goat. The main idea is that a neighbour used a feeding trail to locate a wandering animal.", [["rope loosened", "noticed leaves", "trail led"], ["feeding trail", "locate wandering animal"]], ordered=True),
            _q("A child heard scratching, checked behind stacked boxes, and then lifted out a trapped puppy. Which action happened second?", "The child checked behind the boxes.", ["The puppy was lifted first.", "The child left without checking.", "The boxes scratched the child."]),
            _r("A fish tank filter stopped, the water became cloudy, and the fish stayed near the surface. An adult moved them to clean water before repairing the filter.", "The filter stopped first, the water clouded, and the fish showed distress before the adult moved them. The card shows quick observation leading to a safer temporary home during a repair.", [["filter stopped", "water clouded", "fish distress", "moved"], ["quick observation", "safer temporary home"]], ordered=True),
            _r("A delivery rider found a pet carrier on a bench. The contact card was dry inside a pocket, so the station office called the owner and stored the carrier securely.", "The rider found the carrier, the office read the contact card, called the owner, and stored it safely. The main idea is that contact information enabled responsible return of lost property.", [["found", "read card", "called", "stored"], ["contact information", "responsible return"]], ordered=True),
        ],
        misconception="The learner orders events by sentence length or memory instead of time clues, or gives a main idea that mentions only the missing animal without the useful response and result.",
        remediation="Find the problem, clue, action, and result in order, then combine the clue, action, and result in one main-idea sentence.",
    ),
    _make_level(
        level_id="care_inference_and_reason",
        title="Infer care and justify responsibility",
        focus="infer feelings or motives and write care decisions supported by clues",
        outcome="Infer a likely motive from behaviour and recommend a responsible action with a reason tied to safety, routine, or animal need.",
        skill_ids=["reading.inference_reason", "writing.reason_answer"],
        choice_skill_ids=["reading.inference_reason"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:think:18"],
        principle="A sound idea from clues connects behaviour to a likely need, and a responsible answer states an action plus a because-clause grounded in the card.",
        connect={"teaching_block": "Animals and people do not always state what they need. Readers can use posture, repeated actions, weather, and routine to infer a reason before choosing a safe response.", "passage": "The dog remained beside its empty bowl, looked toward the tap, and licked its lips after a long walk.", "prompt": "Use all three behaviours to infer the likely need before deciding what a caretaker should do."},
        choice_prompt="Which idea fits the behaviour and setting?",
        response_prompt="state the responsible action and justify it with the strongest visible clue.",
        rubric_descriptions=["States a safe and responsible response suited to the need.", "Cites a visible behaviour, condition, or routine as the reason."],
        crunch_bar=CRUNCH_BAR["care_inference_and_reason"],
        examples=[
            _q("A cat circles the closed kitchen door at its usual feeding time and taps the empty dish.", "The cat is likely expecting its meal.", ["The cat wants the dish hidden.", "The cat has forgotten the kitchen.", "The cat is asking for a bath."]),
            _q("A puppy crouches under a chair when thunder sounds and stops shaking when the room becomes quiet.", "The loud thunder frightened the puppy.", ["The chair made the puppy hungry.", "The puppy wanted more thunder.", "The quiet room was too bright."]),
            _r("A rabbit's water bottle is empty on a hot afternoon, and the rabbit repeatedly touches the metal spout.", "Refill the clean water bottle because the empty bottle, hot weather, and repeated touching show that the rabbit may be thirsty.", [["refill the clean water", "provide fresh water"], ["empty bottle", "hot weather", "touches the spout"]]),
            _r("A rescued bird stays still in an open box while a crowd leans close and speaks loudly. A wildlife helper is on the way.", "Move the crowd back and keep the area quiet because the bird is already still and loud close attention may add stress while help arrives.", [["move crowd back", "keep area quiet"], ["bird stays still", "crowd loud", "helper coming"]]),
            _r("A neighbour's dog is alone behind a locked gate, limping and wearing an address tag. The neighbour's phone number is displayed.", "Call the displayed number and wait outside the gate because the dog is limping but entering locked property without permission is unsafe.", [["call the number", "wait outside"], ["dog is limping", "locked gate", "permission"]]),
            _r("A kitten sleeps inside a parked car's wheel area. The driver is nearby at a tea stall, and the car has not started.", "Tell the driver and keep people away from the car because the hidden kitten could be hurt if the vehicle moves.", [["tell the driver", "keep people away"], ["kitten near wheel", "hurt if vehicle moves"]]),
            _r("A class fish is fed by three pupils who each think no one else has fed it. The feeding chart is blank.", "Pause feeding and ask the teacher to update the chart because repeated unrecorded feeding could give the fish too much food.", [["pause feeding", "update the chart"], ["three pupils unsure", "too much food"]]),
            _r("A goat keeps pulling toward a shaded trough after walking in strong sun. The path is clear and its handler holds the rope.", "The handler should guide the goat to the shaded trough because its repeated pulling after sun exposure suggests it needs rest or water.", [["guide to shaded trough", "allow rest or water"], ["pulling repeatedly", "strong sun"]]),
            _r("A dog returns a dropped glove to a child and waits with a wagging tail instead of running away.", "The child should thank the handler or gently accept the glove because the dog's return and waiting behaviour show a helpful trained action.", [["thank or gently accept", "respond calmly"], ["returns glove", "waits", "helpful action"]]),
            _q("A parrot moves to the far side of its perch whenever a hand enters the cage.", "The parrot may want more distance from the hand.", ["The parrot wants the hand to move closer.", "The perch has disappeared.", "The parrot is asking for loud music."]),
            _r("A street dog sleeps near a shop entrance during heavy rain. The shopkeeper can place a dry mat under the awning without blocking customers.", "Place the dry mat under the awning because the dog is sheltering from rain and the mat can help without blocking the entrance.", [["place a dry mat", "under the awning"], ["sheltering from rain", "not block entrance"]]),
            _q("A pony slows, breathes quickly, and turns toward a water tub after a long route.", "The pony likely needs a rest and water.", ["The pony wants a longer route immediately.", "The water tub made it run.", "The pony is searching for a book."]),
            _r("A child's pet-care alarm rings, but the child is busy painting. The pet's medicine card says the dose is due now and an adult is present.", "Tell the adult immediately and follow the medicine card because the scheduled dose should not be delayed or guessed during another activity.", [["tell the adult", "follow the medicine card"], ["dose due now", "not delay or guess"]]),
            _r("A puppy has chewed a loose electrical cable and remains near it. The switch is across the room and an adult is nearby.", "Keep away, warn the adult, and have the power switched off because the damaged cable can be dangerous to both the puppy and people.", [["keep away", "warn adult", "switch power off"], ["damaged cable dangerous", "puppy and people"]]),
        ],
        misconception="The learner assigns a human emotion without behavioural evidence, or recommends touching, entering, feeding, or treating an animal without considering safety and adult help.",
        remediation="Name one observed behaviour and one setting clue, write 'This may mean...', then choose an action that protects the animal, the learner, and ownership boundaries.",
    ),
    _make_level(
        level_id="rescue_words_in_context",
        title="Use rescue words from context",
        focus="infer chapter vocabulary and use it accurately in a new sentence",
        outcome="Explain a target word from contrast, definition, or result clues and produce a fresh sentence that preserves the same meaning.",
        skill_ids=["reading.word_meaning_context", "vocab.chapter_word_usage"],
        choice_skill_ids=["reading.word_meaning_context"],
        episode_kind="meaning_encounter",
        source_anchor_ids=[f"{CHAPTER_ID}:read:15-17", f"{CHAPTER_ID}:learn:19"],
        principle="Context shows a word's meaning; a new sentence proves understanding only when the target word keeps that meaning.",
        connect={"teaching_block": "A definition may appear after a comma, while a cause or contrast may reveal meaning indirectly. After inferring the word, test it in a different rescue scene.", "passage": "The hikers were relieved, no longer worried, when the missing dog returned with the guide.", "prompt": "Use 'no longer worried' to define relieved, then imagine another safe ending where the word would fit."},
        choice_prompt="Which meaning matches the context clue?",
        response_prompt="explain the target word from the clue and use it accurately in a fresh sentence.",
        rubric_descriptions=["Defines the target word using the specific context clue.", "Uses the word in a new sentence with the same meaning and correct situation."],
        crunch_bar=CRUNCH_BAR["rescue_words_in_context"],
        examples=[
            _q("The soaked puppy dripped water across the mat after walking through heavy rain.", "completely wet", ["very noisy", "fully rested", "brightly coloured"]),
            _q("The guard stayed alert, watching the gate closely for the missing animal.", "watchful and ready to notice", ["asleep and unaware", "angry without reason", "lost in another town"]),
            _r("The child sheltered the kitten under a dry basket until the shower passed. Sheltered means protected from the weather.", "Sheltered means kept protected from rain, as the dry basket covered the kitten. New sentence: We sheltered the bird box under the porch during the storm.", [["protected from rain", "dry basket covered"], ["sheltered the bird box", "under the porch"]]),
            _r("A faint bell sound was weak but still just loud enough to guide the searchers.", "Faint means weak or hard to hear, shown by the bell being only just audible. New sentence: A faint mew came from behind the closed cupboard.", [["weak or hard to hear", "just audible"], ["faint mew", "behind the cupboard"]]),
            _r("The careful neighbour approached the frightened dog cautiously, moving slowly and keeping a safe distance.", "Cautiously means with care to avoid danger, shown by slow movement and distance. New sentence: The child cautiously carried the injured butterfly box to an adult.", [["with care", "slow movement and distance"], ["cautiously carried", "to an adult"]]),
            _r("The goat wandered beyond the field, moving without a planned direction until its owner found it.", "Wandered means moved around without a clear route, as the goat went beyond the field. New sentence: The puppy wandered from the picnic blanket toward the trees.", [["without a clear route", "beyond the field"], ["puppy wandered", "toward the trees"]]),
            _r("The tag was secure, firmly attached to the collar even after the puppy pushed through bushes.", "Secure means firmly fixed and unlikely to come loose. New sentence: The keeper checked that the cage latch was secure before leaving.", [["firmly fixed", "unlikely to come loose"], ["latch was secure", "before leaving"]]),
            _r("The searchers retraced their route, going back along the same path to check every stop again.", "Retraced means went back over the same route. New sentence: I retraced my walk and found the lead beside the fountain.", [["back over same route", "check every stop"], ["retraced my walk", "found beside fountain"]]),
            _r("The puppy whimpered, making a soft unhappy sound while its paw was caught.", "Whimpered means made a quiet distressed sound, as the trapped puppy did. New sentence: The cold pup whimpered until the blanket warmed it.", [["quiet distressed sound", "paw was caught"], ["pup whimpered", "blanket warmed"]]),
            _q("The owner was relieved after the clinic said the paw would heal fully.", "no longer worried", ["more confused", "still searching", "ready to leave the pet"]),
            _r("The bright collar was distinctive, noticeably different from all the plain black collars nearby.", "Distinctive means easy to recognise because it is different. New sentence: The dog's distinctive star-shaped tag helped the office identify it.", [["easy to recognise", "different from others"], ["distinctive tag", "helped identify"]]),
            _q("The horse remained calm, standing quietly while the noisy gate was repaired.", "peaceful and not upset", ["running wildly", "hidden from view", "covered in mud"]),
            _r("The children alerted the caretaker, making him aware that a kitten was inside the shed.", "Alerted means warned or made someone aware. New sentence: A bell alerted the family when the gate opened.", [["warned or made aware", "told caretaker"], ["bell alerted", "gate opened"]]),
            _r("The volunteer inspected the carrier, checking its door, handle, and air holes carefully before use.", "Inspected means examined carefully, shown by checking several parts. New sentence: The adult inspected the leash for a damaged clip.", [["examined carefully", "checking several parts"], ["inspected the leash", "damaged clip"]]),
        ],
        misconception="The learner substitutes a related feeling or action without checking the defining clue, or copies the original sentence instead of transferring the word to a genuinely new context.",
        remediation="Find the definition or result clue, state a short synonym, then write a new who-did-what sentence and replace the target word with the synonym to test the meaning.",
    ),
    _make_level(
        level_id="past_actions_in_order",
        title="Keep completed actions in past tense",
        focus="use consistent past-tense verbs and natural sentence order",
        outcome="Use time clues to choose past forms and arrange a doer, action, object, place, and time into clear rescue-account sentences.",
        skill_ids=["grammar.tense_usage", "grammar.sentence_order"],
        choice_skill_ids=["grammar.tense_usage"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:learn:19", f"{CHAPTER_ID}:write:21-23"],
        principle="A completed-time clue controls every linked action; after choosing verb forms, place the doer and action before the supporting details.",
        connect={"teaching_block": "Words such as yesterday and last evening signal completed events. A clear account keeps those actions in past tense and orders sentence parts around the doer.", "passage": "Yesterday, Tara checked the gate, fastened the latch, and recorded the repair in a notebook.", "prompt": "Notice how one time clue controls all three verbs and how Tara appears before the actions."},
        choice_prompt="Which verb form matches the completed-time clue?",
        response_prompt="repair all verb forms and arrange the supplied details into a natural past-tense sentence.",
        rubric_descriptions=["Uses consistent and accurate past-tense forms for completed actions.", "Orders the doer, action, object, place, and time naturally."],
        crunch_bar=CRUNCH_BAR["past_actions_in_order"],
        examples=[
            _q("Last night, the guard ___ the open kennel door.", "closed", ["close", "closes", "closing"]),
            _q("Yesterday, the puppy ___ its red ball behind the sofa.", "pushed", ["push", "pushes", "pushing"]),
            _r("Draft: This morning, Mira check the collar and record the phone number. Parts: at the clinic / Mira / the number / recorded.", "This morning, Mira checked the collar and recorded the phone number. Mira recorded the number at the clinic.", [["checked", "recorded"], ["Mira recorded the number", "at the clinic"]]),
            _r("Draft: Last Saturday, we follow the paw prints and find the dog near a shed. Parts: near the shed / found / we / the tired dog.", "Last Saturday, we followed the paw prints and found the dog near a shed. We found the tired dog near the shed.", [["followed", "found"], ["We found the tired dog", "near the shed"]]),
            _r("Draft: Yesterday, Ali carry the bird box and place it on a quiet table. Parts: carefully / Ali / placed / the box / on a table.", "Yesterday, Ali carried the bird box and placed it on a quiet table. Ali carefully placed the box on a table.", [["carried", "placed"], ["Ali carefully placed", "on a table"]]),
            _r("Draft: Last evening, the volunteer wash the bowls, dry them, and filled them again. Parts: after cleaning / the volunteer / filled / the bowls.", "Last evening, the volunteer washed the bowls, dried them, and filled them again. The volunteer filled the bowls after cleaning.", [["washed", "dried", "filled"], ["volunteer filled the bowls", "after cleaning"]]),
            _r("Draft: Two days ago, Neha notice a torn lead and tells an adult. Parts: immediately / Neha / told / an adult / about the lead.", "Two days ago, Neha noticed a torn lead and told an adult. Neha immediately told an adult about the lead.", [["noticed", "told"], ["Neha immediately told", "about the lead"]]),
            _r("Draft: Yesterday morning, the cat jump onto the sill and waited there. Parts: before breakfast / the cat / jumped / onto the sill.", "Yesterday morning, the cat jumped onto the sill and waited there. The cat jumped onto the sill before breakfast.", [["jumped", "waited"], ["cat jumped onto the sill", "before breakfast"]]),
            _r("Draft: Last week, the class collect blankets and delivers them to the shelter. Parts: the class / delivered / clean blankets / on Friday.", "Last week, the class collected blankets and delivered them to the shelter. The class delivered clean blankets on Friday.", [["collected", "delivered"], ["class delivered clean blankets", "on Friday"]]),
            _q("An hour ago, the caretaker ___ the water bowl.", "refilled", ["refill", "refills", "refilling"]),
            _r("Draft: On Monday, the office call the tag number and returns the collar. Parts: at noon / the office / returned / the collar / to its owner.", "On Monday, the office called the tag number and returned the collar. At noon, the office returned the collar to its owner.", [["called", "returned"], ["office returned the collar", "to its owner"]]),
            _q("Last month, our group ___ a pet-care chart.", "created", ["create", "creates", "creating"]),
            _r("Draft: Yesterday, the child hear a mew, looks under the bench, and lifted the kitten. Parts: from under the bench / the child / lifted / the kitten.", "Yesterday, the child heard a mew, looked under the bench, and lifted the kitten. The child lifted the kitten from under the bench.", [["heard", "looked", "lifted"], ["child lifted the kitten", "from under the bench"]]),
            _r("Draft: Last night, rain soak the bedding, so the keeper moves the dog indoors. Parts: indoors / the keeper / moved / the wet bedding / later.", "Last night, rain soaked the bedding, so the keeper moved the dog indoors. Later, the keeper moved the wet bedding indoors.", [["soaked", "moved"], ["keeper moved the wet bedding", "indoors"]]),
        ],
        misconception="The learner adds -ed to every verb without checking irregular forms, shifts back to present after one past verb, or begins with loose details that hide the doer and action.",
        remediation="Use the completed-time clue to choose each verb form, check irregular forms separately, then rebuild each sentence as doer-action-object-place-time.",
    ),
    _make_level(
        level_id="questions_and_punctuation",
        title="Form clear questions and statements",
        focus="use capitalization and end punctuation while forming information questions",
        outcome="Distinguish statements from questions, capitalize openings and names, and build a complete who-what-where question with the correct question mark.",
        skill_ids=["grammar.punctuation_capitalization", "grammar.question_formation"],
        choice_skill_ids=["grammar.punctuation_capitalization"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:write:21-23"],
        principle="The purpose of a sentence controls its end mark; a question also needs a clear question word and clear word order.",
        connect={"teaching_block": "A statement gives information and ends with a full stop. A question asks for information, begins with a capital letter, and ends with a question mark.", "passage": "Statement: The puppy waits near the gate. Question: Why does the puppy wait near the gate?", "prompt": "Compare the purpose, opening capital, helper word, and end mark in the two sentences."},
        choice_prompt="Which version has correct capitalization and punctuation?",
        response_prompt="repair the sentence and form the requested complete question with a question mark.",
        rubric_descriptions=["Uses opening capitals, name capitals, and the correct end punctuation.", "Forms a natural complete question that asks for the requested information."],
        crunch_bar=CRUNCH_BAR["questions_and_punctuation"],
        examples=[
            _q("Sentence card: The animal clinic opens at nine.", "It tells a fact.", ["It asks for a place.", "It asks for a person.", "It gives an excited warning."], prompt="What job does this sentence do?", skills=["grammar.question_formation"]),
            _q("Question card: Where is the animal clinic?", "It asks for a place.", ["It tells that the clinic is closed.", "It asks who owns an animal.", "It gives a command."], prompt="What information does this question ask for?", skills=["grammar.question_formation"]),
            _r("Draft statement: the guard found a collar near lake road. Ask for the time of the finding.", "The guard found a collar near Lake Road. When did the guard find the collar?", [["The guard", "Lake Road", "full stop"], ["When did the guard find", "question mark"]]),
            _r("Draft: why the kitten is hiding under the chair. Repair it as a question and add the answer fact: thunder is loud.", "Why is the kitten hiding under the chair? The kitten is hiding because the thunder is loud.", [["Why is the kitten", "question mark"], ["The kitten is hiding", "thunder is loud", "full stop"]]),
            _r("Fact: Arjun filled the bowl at six o'clock. Ask who performed the action, then write the fact correctly.", "Who filled the bowl at six o'clock? Arjun filled the bowl at six o'clock.", [["Who filled", "question mark"], ["Arjun filled", "full stop"]]),
            _r("Draft question: where did sara place the medicine card. Correct it and answer: on the top shelf.", "Where did Sara place the medicine card? Sara placed it on the top shelf.", [["Where did Sara", "question mark"], ["Sara placed it", "top shelf"]]),
            _r("Fact: The blue tag belongs to Kunal's dog. Form a question asking whose dog has the tag.", "Whose dog has the blue tag? Kunal's dog has the blue tag.", [["Whose dog has", "question mark"], ["Kunal's dog", "full stop"]]),
            _r("Draft: did leena call the shelter yesterday. Correct the question and add a yes answer.", "Did Leena call the shelter yesterday? Yes, Leena called the shelter yesterday.", [["Did Leena call", "question mark"], ["Yes, Leena called", "full stop"]]),
            _r("Fact: The rabbit moved because the floor was wet. Ask for the reason and answer it.", "Why did the rabbit move? It moved because the floor was wet.", [["Why did the rabbit move", "question mark"], ["because the floor was wet", "full stop"]]),
            _r("Draft: the clinic opens on monday", "The clinic opens on Monday. The begins with a capital letter, Monday is a name with a capital, and the statement ends with a full stop.", [["capital letter for Monday", "Monday is a name with a capital"], ["full stop", "statement ends with a full stop"]], prompt="Rewrite the statement with the right capitals and end mark.", interaction_type="short_text"),
            _r("Draft statement: on friday, nasim repaired the gate. Ask when the repair happened.", "On Friday, Nasim repaired the gate. When did Nasim repair the gate?", [["On Friday", "Nasim", "full stop"], ["When did Nasim repair", "question mark"]]),
            _r("Draft: who owns this red lead", "Who owns this red lead? Who begins with a capital letter, owns stays lowercase, and the question ends with a question mark.", [["capital letter for Who", "Who begins with a capital"], ["question mark", "question ends with a question mark"]], prompt="Rewrite the question with the right capital and end mark.", interaction_type="short_text"),
            _r("Fact: The caretaker put the carrier beside the office door. Ask where it was placed and answer.", "Where did the caretaker put the carrier? The caretaker put it beside the office door.", [["Where did the caretaker put", "question mark"], ["beside the office door", "full stop"]]),
            _r("Draft: can the puppy stay with us. Correct it and add the condition: an adult must agree.", "Can the puppy stay with us? It can stay only if an adult agrees.", [["Can the puppy stay", "question mark"], ["only if an adult agrees", "full stop"]]),
        ],
        misconception="The learner chooses an end mark by sentence length, leaves names uncapitalized, or places question words into statement order such as 'Why the dog is...'.",
        remediation="Decide whether each sentence asks or tells, capitalize its first word and names, build questions with question-word plus helper plus subject, and add the matching end mark last.",
    ),
    _make_level(
        level_id="responsive_rescue_dialogue",
        title="Track speakers and write responsive dialogue",
        focus="identify dialogue speakers and construct a relevant two-turn exchange",
        outcome="Identify each speaker from reporting clauses and the meaning of each reply, then write punctuated dialogue in which the second turn directly answers or advances the first.",
        skill_ids=["reading.dialogue_attribution", "writing.complete_sentence"],
        choice_skill_ids=["reading.dialogue_attribution"],
        episode_kind="expression_workshop",
        source_anchor_ids=[f"{CHAPTER_ID}:read:15-17", f"{CHAPTER_ID}:write:21-23"],
        principle="Reporting clauses identify voices, response meaning confirms them, and strong dialogue uses clear punctuation while making every turn relevant to the previous one.",
        connect={"teaching_block": "A dialogue reader tracks who speaks, what the line responds to, and whether the reply changes the plan. A dialogue writer makes those links visible.", "passage": "'I found the tag,' Jiya told Om. 'Then I will call the number on it,' he replied.", "prompt": "Use the reporting clauses and the logic of 'then' to assign both voices and their contributions."},
        choice_prompt="Who speaks the named line, and which clue proves it?",
        response_prompt="identify the speaker of the supplied turn and write a punctuated reply that responds directly to it.",
        rubric_descriptions=["Identifies the correct speaker using a reporting or meaning clue.", "Writes a clearly punctuated reply that answers or advances the situation."],
        crunch_bar=CRUNCH_BAR["responsive_rescue_dialogue"],
        examples=[
            _q("'The paw prints turn left,' Asha told Vikram. 'I will check that lane,' he answered.", "Vikram will check the lane.", ["Asha will erase the prints.", "The lane speaks second.", "Vikram found no clue."]),
            _q("'Please hold the gate,' Rehan asked Mili. 'I have it,' she replied.", "Mili says, 'I have it.'", ["Rehan says both lines.", "The gate replies.", "Mili asks for the gate."]),
            _r("Kavya says, 'The water bowl is empty.' The second speaker is Dev, who agrees to fill it.", "Kavya reported, 'The water bowl is empty.' Dev replied, 'I will fill it with clean water now.'", [["Kavya reported", "water bowl is empty"], ["Dev replied", "fill it with clean water"]], interaction_type="dialogue"),
            _r("Imran asks where the red collar was found. Noor found it beside the bus stop and answers.", "Imran asked, 'Where did you find the red collar?' Noor replied, 'I found it beside the bus stop.'", [["Imran asked", "Where did you find"], ["Noor replied", "beside the bus stop"]], interaction_type="dialogue"),
            _r("A clinic worker says the puppy needs quiet. The owner thanks the worker and agrees.", "The worker said, 'The puppy needs a quiet place to rest.' The owner replied, 'Thank you; I will keep the room calm.'", [["worker said", "quiet place"], ["owner replied", "keep the room calm"]], interaction_type="dialogue"),
            _r("A neighbour asks whether the kitten belongs to Salma. Salma recognises its blue patch and answers yes.", "The neighbour asked, 'Does this kitten belong to you, Salma?' Salma replied, 'Yes, I recognise the blue patch on its paw.'", [["neighbour asked", "belong to you"], ["Salma replied", "blue patch"]], interaction_type="dialogue"),
            _r("Ritu warns that the cage latch is loose. Ben proposes asking an adult to repair it.", "Ritu warned, 'The cage latch is loose.' Ben replied, 'Let us ask an adult to repair it before we use the cage.'", [["Ritu warned", "latch is loose"], ["Ben replied", "ask an adult to repair"]], interaction_type="dialogue"),
            _r("The guard asks for the contact number on a tag. Pia reads the number and provides it.", "The guard asked, 'What contact number is printed on the tag?' Pia replied, 'The number is 9840 112 300.'", [["guard asked", "contact number"], ["Pia replied", "9840 112 300"]], interaction_type="dialogue"),
            _r("A child says a bird is trapped behind a grille. An adult tells the child to step back while help is called.", "The child said, 'A bird is trapped behind the grille.' The adult replied, 'Step back, please, while I call a trained helper.'", [["child said", "bird is trapped"], ["adult replied", "step back", "call a trained helper"]], interaction_type="dialogue"),
            _q("'I can carry the clean blanket,' Farah told Nikhil. 'I will open the shelter door,' he answered.", "Nikhil will open the door.", ["Farah will open the door.", "The blanket answers Farah.", "Nikhil carries every blanket."]),
            _r("Mehul asks why the dog is waiting. Tia points to the closed clinic door as her answer.", "Mehul asked, 'Why is the dog waiting here?' Tia replied, 'The clinic door is still closed.'", [["Mehul asked", "Why is the dog waiting"], ["Tia replied", "clinic door is closed"]], interaction_type="dialogue"),
            _q("'The medicine card says eight o'clock,' Tara reminded Jo. 'Then I will set an alarm,' he said.", "Jo will set an alarm.", ["Tara will hide the card.", "The card speaks to Jo.", "Jo changes the time to noon."]),
            _r("The owner thanks a shopkeeper for protecting a lost puppy. The shopkeeper explains that the tag made contact possible.", "The owner said, 'Thank you for keeping my puppy safe.' The shopkeeper replied, 'The phone number on the tag helped me contact you.'", [["owner said", "Thank you", "puppy safe"], ["shopkeeper replied", "number on the tag"]], interaction_type="dialogue"),
            _r("Lina reports that the rabbit pen is open. Her brother says he will check the garden while she closes the gate.", "Lina said, 'The rabbit pen is open.' Her brother replied, 'I will check the garden while you secure the gate.'", [["Lina said", "pen is open"], ["brother replied", "check the garden", "secure the gate"]], interaction_type="dialogue"),
        ],
        misconception="The learner assigns a pronoun to the nearest name without checking the reporting clause, or writes two unrelated quotations that do not answer, clarify, or advance one another.",
        remediation="Identify each reporting verb and speaker, explain how the second turn answers the first turn's need, then check quotation marks, capitals, commas, and end punctuation.",
    ),
]


ASSESSMENT_PAIRS = [
    _aq_pair("reading.event_sequence", "What happened last in this rescue chain?", ("A collar slipped off, a walker found it, and the office called its owner.", "The office called the owner.", ["The collar slipped off.", "A walker found it.", "The owner hid the office."]), ("The bird flew indoors, perched on a shelf, and entered its cage when food was placed inside.", "The bird entered its cage.", ["The bird flew indoors.", "It perched on a shelf.", "The shelf entered the cage."])),
    _ar_pair("reading.paragraph_main_idea", "State the main idea in one concise sentence.", "Combines the problem, useful clue or response, and safe result.", ("A puppy wandered from a park. A bright tag helped a guard call the family, who collected it safely.", "A visible tag enabled a guard to return a wandering puppy safely to its family.", [["visible tag enabled a guard", "guard used the bright name tag"], ["return a wandering puppy safely to its family", "bring the lost puppy back to its family"]]), ("A rabbit escaped through a loose panel. Tracks led the keeper to a vegetable patch, and the panel was repaired.", "Tracks helped recover an escaped rabbit, and repairing the panel prevented another escape.", ["tracks helped recover", "panel repaired"]), interaction_type="summary"),
    _ar_pair("reading.inference_reason", "State the best idea and cite its clue.", "States a plausible need or motive grounded in visible behaviour.", ("The dog waits by an empty bowl and licks its lips after exercise.", "The dog is likely thirsty because it waits at the empty bowl and licks its lips after exercise.", ["likely thirsty", "empty bowl", "licks its lips"]), ("The cat hides under a bed only while fireworks sound outside.", "The loud fireworks likely frighten the cat because it hides only when those sounds occur.", ["fireworks frighten", "hides only when"])),
    _ar_pair("writing.reason_answer", "Recommend a responsible action and support it with a because-clause.", "Names a safe action and ties the reason to the supplied need or boundary.", ("A limping dog stands behind a locked gate, and a contact number is visible.", "Call the contact number and wait outside because the dog needs help but the locked gate marks a property boundary.", ["call the contact number", "wait outside", "locked gate"]), ("A kitten is beneath a parked car, and the driver is nearby.", "Tell the driver not to move the car because the hidden kitten could be injured near the wheel.", ["tell the driver", "not move the car", "kitten could be injured"])),
    _aq_pair("reading.word_meaning_context", "What does the target word mean here?", ("The soaked dog left drops on every step.", "completely wet", ["very sleepy", "brightly coloured", "ready to run"]), ("The distinctive star tag was easy to recognise among plain circles.", "noticeably different", ["hard to see", "made of paper", "without a shape"])),
    _ar_pair("vocab.chapter_word_usage", "Explain the word from context and use it in a new sentence.", "Defines the word from the clue and transfers it accurately to a fresh context.", ("The searchers retraced the lane, walking back along the same route.", "Retraced means went back over the same route. New sentence: We retraced our path and found the lead near the gate.", ["back over same route", "retraced our path"]), ("The owner felt relieved, no longer anxious, when the cat returned.", "Relieved means no longer worried. New sentence: I felt relieved after the clinic said the bird was safe.", ["no longer worried", "felt relieved"])),
    _aq_pair("grammar.tense_usage", "Which verb fits the completed-time clue?", ("Yesterday, the guard ___ the loose gate.", "fixed", ["fix", "fixes", "fixing"]), ("Last night, the puppy ___ beneath the chair.", "slept", ["sleep", "sleeps", "sleeping"])),
    _ar_pair("grammar.sentence_order", "Arrange every part into one natural sentence.", "Uses all parts in a clear doer-action-object-place-time order.", ("Parts: yesterday / the caretaker / found / the collar / near the tap.", "Yesterday, the caretaker found the collar near the tap.", ["caretaker found", "the collar", "near the tap"]), ("Parts: carefully / Mina / carried / the bird box / into the clinic.", "Mina carefully carried the bird box into the clinic.", ["Mina carefully carried", "bird box", "into the clinic"]), interaction_type="short_text"),
    _ar_pair("grammar.punctuation_capitalization", "Rewrite the sentence with the right capital letters and end mark.", "Uses capital letters for sentence openings and names, then adds the correct full stop or question mark.", ("Draft: on monday, rafi called the shelter", "On Monday, Rafi called the shelter. Monday and Rafi begin with capital letters, and the statement ends with a full stop.", ["Monday and Rafi begin with capital letters", "statement ends with a full stop"]), ("Draft: where is lake road", "Where is Lake Road? Where and Lake Road use capital letters, and the question ends with a question mark.", ["Where and Lake Road use capital letters", "question ends with a question mark"]), interaction_type="short_text"),
    _ar_pair("grammar.question_formation", "Form the requested complete question.", "Uses a suitable question word, natural order, capitalization, and a question mark.", ("Ask for the place where Rina found the lead.", "Where did Rina find the lead? This complete question asks for the finding place.", ["Where did Rina find", "question mark"]), ("Ask for the reason the dog barked.", "Why did the dog bark? This complete question asks for the barking reason.", ["Why did the dog bark", "question mark"]), interaction_type="short_text"),
    _aq_pair("reading.dialogue_attribution", "Who speaks the second line?", ("'The tag has a number,' Sara told Om. 'I will call it,' he replied.", "Om", ["Sara", "the tag", "the owner"]), ("'Please close the pen,' Vik asked Nila. 'I will do it now,' she answered.", "Nila", ["Vik", "the pen", "the rabbit"])),
    _ar_pair("writing.complete_sentence", "Write the supplied two-turn exchange with clear speakers and punctuation.", "Creates two responsive, correctly punctuated complete sentences with clear speakers.", ("A child reports an empty bowl. An adult agrees to refill it.", "The child said, 'The water bowl is empty.' The adult replied, 'I will refill it with clean water.'", ["child said", "bowl is empty", "adult replied", "refill"]), ("A guard asks where a collar was found. A walker answers: beside the bus stand.", "The guard asked, 'Where did you find the collar?' The walker replied, 'I found it beside the bus stand.'", ["guard asked", "Where did you find", "walker replied", "bus stand"]), interaction_type="dialogue", min_words=12),
    _ar_pair("reading.event_sequence", "Retell the three actions in order.", "Preserves all supplied events in the correct sequence.", ("A child heard a mew, checked a cupboard, and called an adult.", "The child heard a mew first, checked the cupboard next, and called an adult last.", ["heard first", "checked next", "called last"]), ("The office read a tag, phoned the owner, and stored the carrier safely.", "The office read the tag first, phoned the owner next, and stored the carrier safely last.", ["read first", "phoned next", "stored last"]), interaction_type="summary"),
    _ar_pair("writing.complete_sentence", "Add a relevant complete reply to the supplied first turn.", "Writes a complete reply with a clear speaker that directly addresses the first speaker's need.", ("Mira said, 'The cage latch is loose.' Reply as Dev with a safe plan.", "Mira said, 'The cage latch is loose.' Dev replied, 'I will ask an adult to repair it before we use the cage.'", ["Dev replied", "ask an adult", "repair it"]), ("Ali asked, 'Why is the puppy waiting?' Reply as Noor using the closed-door clue.", "Ali asked, 'Why is the puppy waiting?' Noor replied, 'The clinic door is still closed.'", ["Noor replied", "clinic door", "closed"]), interaction_type="dialogue", min_words=12),
]


LAUNCH_DEPTH_CASES = {
    "rescue_sequence_and_main_idea": [
        _launch_depth_case(
            "A field-trip name badge fell near the museum gate. A guard saw the school emblem, called the teacher, and kept the badge at the desk until the class returned.",
            "Order the museum name-badge events and state the main idea of the guard's rescue action.",
            "The badge fell, the guard noticed the emblem, called the teacher, and kept it safely. The main idea is that a school clue helped the guard return a lost badge responsibly.",
            "the badge fell, the guard noticed the emblem, called the teacher, and kept it safely",
            "a school clue helped the guard return a lost badge responsibly",
            ordered=True,
        ),
        _launch_depth_case(
            "The aquarium pump stopped during lunch. Fish gathered near the surface, so the caretaker moved them to a clean tub and repaired the loose plug before returning them.",
            "Retell the aquarium pump problem and safe response, then give the card's main idea.",
            "The pump stopped, the fish showed distress, the caretaker moved them, repaired the plug, and returned them. The card is mainly about noticing a danger sign and protecting the fish during a repair.",
            "the pump stopped, the fish showed distress, the caretaker moved them, repaired the plug, and returned them",
            "noticing a danger sign and protecting the fish during a repair",
            ordered=True,
        ),
        _launch_depth_case(
            "A cricket kit was left beside the community pitch. Rohan read the team initials on the bat cover, asked the coach, and locked the kit in the equipment room until its owner arrived.",
            "Put Rohan's cricket-kit actions in order and state the whole rescue idea.",
            "Rohan found the kit, read the initials, asked the coach, and stored it until the owner came. The main idea is that identity clues and secure storage helped return sports equipment.",
            "Rohan found the kit, read the initials, asked the coach, and stored it until the owner came",
            "identity clues and secure storage helped return sports equipment",
            ordered=True,
        ),
    ],
    "care_inference_and_reason": [
        _launch_depth_case(
            "A puppy keeps lifting its paws from the hot courtyard and settles only on the shaded mat beside the door. Its water bowl is still in the sun.",
            "What does the puppy's hot-courtyard behaviour suggest, and what caring action should happen?",
            "The puppy is trying to avoid the hot ground. Move its water bowl to the shaded mat because it needs a cool place to rest and drink.",
            "the puppy is trying to avoid the hot ground",
            "move its water bowl to the shaded mat",
        ),
        _launch_depth_case(
            "A rescued myna hops toward a shallow dish but backs away when the dish wobbles on a box. It drinks when an adult holds the dish steady.",
            "Why does the rescued myna back away, and what responsible change fits the dish clue?",
            "The myna is cautious because the dish feels unstable. Place the shallow dish on a firm floor because a steady surface lets the bird drink safely.",
            "the myna is cautious because the dish feels unstable",
            "place the shallow dish on a firm floor",
        ),
        _launch_depth_case(
            "An older cat waits by a low step instead of jumping onto its usual high cushion. It purrs after Meera places a folded towel on the floor.",
            "What need can Meera work out from the older cat's actions, and why is the folded towel suitable?",
            "The older cat likely needs an easier resting place. The folded towel is suitable because it gives a soft bed without a high jump.",
            "the older cat likely needs an easier resting place",
            "a soft bed without a high jump",
        ),
    ],
    "rescue_words_in_context": [
        _launch_depth_case(
            "The frightened calf stopped pulling when Iqbal spoke softly and stroked its neck. The note says his calm voice soothed the calf.",
            "What does soothed mean in the frightened-calf card, and how can soothed be used in a new sentence?",
            "Soothed means made calmer. New sentence: A quiet song soothed the baby during the noisy storm.",
            "soothed means made calmer",
            "a quiet song soothed the baby",
        ),
        _launch_depth_case(
            "Before carrying the rabbit box, Anu fastened both clips so the lid could not open. The helper wrote that she secured the box.",
            "Explain secured from the rabbit-box clue and use secured in a fresh complete sentence.",
            "Secured means made safe or firmly closed. New sentence: We secured the loose garden gate with a strong latch.",
            "secured means made safe or firmly closed",
            "we secured the loose garden gate",
        ),
        _launch_depth_case(
            "Vikram hesitated at the flooded lane: he paused at the edge, checked the water depth, and chose the dry bridge instead.",
            "Use the flooded-lane actions to define hesitated, then use hesitated in another situation.",
            "Hesitated means paused before deciding. New sentence: Lila hesitated before stepping onto the moving escalator.",
            "hesitated means paused before deciding",
            "Lila hesitated before stepping onto the moving escalator",
        ),
    ],
    "past_actions_in_order": [
        _launch_depth_case(
            "Yesterday a cyclist noticed a fledgling on the path, stopped the bicycle, called a wildlife helper, and waited beside the marked spot.",
            "Put the cyclist and fledgling actions in order and report them with past-tense verbs.",
            "Yesterday the cyclist noticed the fledgling, stopped the bicycle, called a helper, and waited beside the spot. Each action happened in that order.",
            "the cyclist noticed the fledgling, stopped the bicycle, called a helper, and waited",
            "yesterday shows that each action happened in the past",
            ordered=True,
        ),
        _launch_depth_case(
            "Last evening, children saw a tortoise near the road. They placed a cone nearby, asked the park keeper for help, and watched the keeper carry it toward the pond.",
            "Arrange the tortoise rescue and write one natural past-tense sentence about the park keeper.",
            "The children saw the tortoise, placed a cone, and asked for help before the keeper moved it. The park keeper carried the tortoise toward the pond last evening.",
            "the children saw the tortoise, placed a cone, and asked for help before the keeper moved it",
            "the park keeper carried the tortoise toward the pond last evening",
            ordered=True,
        ),
        _launch_depth_case(
            "On Monday, a gardener heard a kitten inside the tool shed, opened the side window, set down a basket, and lifted the kitten out after it climbed in.",
            "Retell the gardener and kitten events, then form a clear sentence with doer, action, object, place, and time.",
            "The gardener heard the kitten, opened the window, set down a basket, and lifted it out. On Monday, the gardener lifted the kitten from the tool shed in a basket.",
            "the gardener heard the kitten, opened the window, set down a basket, and lifted it out",
            "on Monday, the gardener lifted the kitten from the tool shed in a basket",
            ordered=True,
        ),
    ],
    "questions_and_punctuation": [
        _launch_depth_case(
            "The office notice says Mira returned a blue notebook from the playground at 2 p.m. The class wants to ask about the person who returned it.",
            "Build and punctuate the complete question about Mira and the blue notebook.",
            "Who returned the blue notebook from the playground? The capital W and question mark show a complete question.",
            "who returned the blue notebook from the playground?",
            "capital W and question mark",
            answer_description="Uses a capital letter and the correct punctuation mark.",
        ),
        _launch_depth_case(
            "A shelter card says the vet will examine the puppy in Room Three on Friday. Ritu needs to ask about the place.",
            "Write Ritu's complete question about the puppy, Room Three, and Friday with correct punctuation.",
            "Where will the vet examine the puppy on Friday? The question begins with a capital and ends with a question mark.",
            "where will the vet examine the puppy on Friday?",
            "begins with a capital and ends with a question mark",
            answer_description="Uses a capital letter and the correct punctuation mark.",
        ),
        _launch_depth_case(
            "The bus helper found a red scarf after the final stop. Dev wants to ask why the scarf was taken to the depot desk.",
            "Form Dev's why-question about the red scarf and depot desk, using capitals and the right end mark.",
            "Why was the red scarf taken to the depot desk? Why starts with a capital, and the sentence ends with a question mark.",
            "why was the red scarf taken to the depot desk?",
            "starts with a capital, and the sentence ends with a question mark",
            answer_description="Uses a capital letter and the correct punctuation mark.",
        ),
    ],
    "responsive_rescue_dialogue": [
        _launch_depth_case(
            "At the clinic gate, Noor says the puppy's lead has snapped. Kavi answers that he will close the gate while Noor calls an adult.",
            "Identify Noor and Kavi in the clinic-gate exchange, then write their two responsive lines with punctuation.",
            "Noor said, 'The puppy's lead has snapped.' Kavi replied, 'I will close the gate while you call an adult.' Kavi's reply answers the safety problem.",
            "Noor said, 'The puppy's lead has snapped.' Kavi replied, 'I will close the gate while you call an adult.'",
            "Kavi's reply answers the safety problem",
            interaction_type="dialogue",
            min_words=15,
            answer_description="Uses capital letters, speaker punctuation, and end marks correctly.",
        ),
        _launch_depth_case(
            "On the school bus, Jia reports that a lunch bag is under Seat Six. The driver replies that he will place it at the school office after the route.",
            "Write Jia and the driver's school-bus dialogue so the second line responds to the lost bag.",
            "Jia said, 'A lunch bag is under Seat Six.' The driver replied, 'I will take it to the school office after the route.' The driver gives a clear next step.",
            "Jia said, 'A lunch bag is under Seat Six.' The driver replied, 'I will take it to the school office after the route.'",
            "the driver gives a clear next step",
            interaction_type="dialogue",
            min_words=15,
            answer_description="Uses capital letters, speaker punctuation, and end marks correctly.",
        ),
        _launch_depth_case(
            "Near the garden shed, Esha says a hedgehog is trapped inside a loose net. Om replies that he will keep everyone back while the caretaker removes it.",
            "Name Esha and Om as the speakers, then punctuate a reply that advances the garden-shed rescue.",
            "Esha said, 'A hedgehog is trapped in the loose net.' Om replied, 'I will keep everyone back while the caretaker removes it.' Om's reply makes space for a safe rescue.",
            "Esha said, 'A hedgehog is trapped in the loose net.' Om replied, 'I will keep everyone back while the caretaker removes it.'",
            "Om's reply makes space for a safe rescue",
            interaction_type="dialogue",
            min_words=15,
            answer_description="Uses capital letters, speaker punctuation, and end marks correctly.",
        ),
    ],
}

_add_launch_depth_variants(LEVELS, LAUNCH_DEPTH_CASES)


_SEMANTIC_OPTION_REPLACEMENTS = {}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch02:assessment:11': {'accepted_answers': ['Aman'],
                               'options': ['Rupa', 'Aman', 'Moti', 'the cupboard'],
                               'passage': "'Moti needs a dry blanket,' Rupa said. Aman "
                                          "answered, 'I will bring one from the "
                                          "cupboard.'",
                               'prompt': 'Who offers to bring the blanket?'}}


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
    chapter_no=2,
    title="Badal and Moti",
    unit_title="Fun with Friends",
    source_url=SOURCE_URL,
    page_extract="/tmp/zidd-ncert-class2-3/eng_c3_ch02.txt",
    source_anchors=SOURCE_ANCHORS,
    levels=LEVELS,
    assessment_pairs=ASSESSMENT_PAIRS,
)

_apply_semantic_copy_corrections(MANIFEST["levels"])
_apply_semantic_copy_corrections(
    MANIFEST["chapter_assessment"]["items"]
)
_apply_semantic_assessment_overrides(MANIFEST)
