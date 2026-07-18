"""Deep authored manifest for Class 3 English Chapter 10.

The NCERT extract was consulted for section order and exercise types only.
All learner-facing content and grading authority are original Zidd material.
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
    "chapter_id": "eng_c3_ch10",
    "chapter_no": 10,
    "title": "Night",
    "unit_title": "The Sky",
    "source_url": "https://ncert.nic.in/textbook/pdf/cesa110.pdf",
    "source_analysis_reference": (
        "/tmp/zidd-ncert-class2-3/eng_c3_ch10.txt structure review"
    ),
    "anchors": [
        {"label": "Chapter poem text under the recitation heading: day and night sky images", "page_start": 2, "page_end": 3, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us think A-B: Sun, sky, day-night, and imagination questions", "page_start": 4, "page_end": 4, "treatment": "taught_and_assessed", "required": True},
        {"label": "Source opening-blend word list adapted to text-only word building", "page_start": 5, "page_end": 5, "treatment": "zidd_equivalent", "required": True},
        {"label": "Let us learn A-B: sky vocabulary and Sun compound words", "page_start": 6, "page_end": 6, "treatment": "taught_and_assessed", "required": True},
        {"label": "Unit picture-reading questions about a street scene", "page_start": 1, "page_end": 1, "treatment": "textbook_companion", "required": False},
        {"label": "Let us do: I Spy classroom game", "page_start": 5, "page_end": 5, "treatment": "offline_group_activity", "required": False},
        {"label": "Let us speak: say sp, st, and sk words aloud", "page_start": 5, "page_end": 5, "treatment": "guided_only", "required": False},
        {"label": "Recite the source poem", "page_start": 2, "page_end": 3, "treatment": "textbook_companion", "required": False},
    ],
    "levels": [
        {
            "level_id": "night_sky_images",
            "title": "Interpret a night image",
            "focus": "interpret sky imagery and identify a poem-like passage's central idea",
            "concept": "sky imagery",
            "outcome": "Explain a nonliteral sky picture through visible shape, light, or movement clues and connect it to the passage's whole night-time idea.",
            "skill_ids": ["reading.poetic_language", "reading.paragraph_main_idea"],
            "episode_kind": "meaning_encounter",
            "anchor_indexes": [1],
            "principle": "Sky imagery compares a sky detail with a familiar object. Name the shared feature, then tell what picture or change it helps you imagine.",
            "connect": _connect(
                "Poetic sky pictures are not literal reports. Readers identify the compared things, locate a shared feature such as curve or glow, and decide what the image adds to the whole scene.",
                "At dusk, a silver path appeared across the pond, as if the moon had laid a quiet ribbon on the water.",
                "Picture the reflected light and decide why ribbon is useful without claiming a real ribbon exists.",
            ),
            "misconception": "The learner treats an image as physical fact or explains one comparison word without connecting it to the passage's central night mood.",
            "remediation": "Name both compared things, circle the shared feature, mark the image nonliteral, and finish with one sentence stating how it shapes the whole scene.",
            "creative_transfer": True,
            "cases": [
                _case("moon ribbon", "Moonlight stretches over a still pond like a pale ribbon, and the garden grows quiet around it.", "What does the ribbon image show, and what central idea does it support?", "The ribbon image shows a long pale reflection in a calm night scene.", "A cloth ribbon was dropped into the pond.", "The passage is mainly about buying garden tools.", "The shared shape and gentle light reinforce the garden's quiet change.", "long pale reflection", "calm quiet night"),
                _case("star buttons", "Small stars shine above a dark field like bright buttons sewn across a black coat.", "Which interpretation uses the visible comparison?", "The stars resemble bright buttons because they are small points against darkness.", "The sky is a real coat made from cloth.", "The stars are large doors under the field.", "Scattered bright points and a dark background create the image.", "stars bright buttons", "points against darkness"),
                _case("cloud curtain", "A thick cloud slides across the moon like a curtain closing over a lamp, and the path briefly dims.", "How does the curtain image develop the event?", "The cloud is like a curtain because it covers the moon and reduces the light.", "A stage curtain is hanging from the moon.", "The path becomes brighter when covered.", "Covering and dimming are shared effects that explain the change.", "cloud covers moon", "light briefly dims"),
                _case("sunset ember", "The last orange patch near the hill glows like an ember before the sky turns deep blue.", "What shared feature supports ember, and what transition follows?", "The orange glow resembles an ember and marks the change from evening light to night.", "A real fire burns inside the hill.", "The sky changes from night to noon.", "Colour and fading brightness connect the image to the evening transition.", "orange ember glow", "evening becomes night"),
                _case("crescent boat", "A thin crescent rests above the rooftops like a little boat floating on a dark sea of sky.", "Why is boat an effective image here?", "The curved crescent resembles a small boat on the dark sky.", "People are sailing a real boat over roofs.", "The moon is square and hidden underground.", "The shared curve and apparent floating position build the picture.", "curved crescent boat", "floating dark sky"),
                _case("dawn doorway", "A narrow band of gold opens between two grey clouds like a doorway into morning.", "Which explanation connects image and main idea?", "The golden opening resembles a doorway and signals night giving way to morning.", "A wooden door is fixed to the clouds.", "The scene stays dark with no change.", "The opening light represents the transition into day.", "golden cloud doorway", "night gives morning"),
                _case("rain necklace", "After an evening shower, drops along the wire shine like a necklace under the streetlamp.", "What makes necklace a supported comparison?", "The lined-up shining drops resemble beads in a necklace.", "Someone hung jewellery inside every raindrop.", "The wire becomes a river at noon.", "Repeated bright drops along one line share the necklace pattern.", "shining drops necklace", "beads along line"),
            ],
        },
        {
            "level_id": "night_context_words",
            "title": "Use night words precisely",
            "focus": "infer word meaning and apply night vocabulary in a new context",
            "concept": "night vocabulary in context",
            "outcome": "Use surrounding clues to distinguish distant, dim, still, peep, and glow, then apply the selected word in a meaning-matched sentence.",
            "skill_ids": ["reading.word_meaning_context", "vocab.chapter_word_usage"],
            "episode_kind": "language_lab",
            "anchor_indexes": [1, 2],
            "principle": "Context reveals a word through distance, amount of light, movement, or partial appearance. The same word must keep that meaning when transferred to a new sentence.",
            "connect": _connect(
                "A nearby clue often demonstrates an unfamiliar word. Readers replace the word with a simple meaning, check the sentence, and then use it in a fresh but related context.",
                "The lighthouse looked distant; it was so far away that only a tiny blink of light could be seen.",
                "Use far away to infer distant, then imagine another object that could be distant.",
            ),
            "misconception": "The learner chooses a word because it belongs to the sky topic even when its precise meaning conflicts with the sentence clue.",
            "remediation": "Underline the defining clue, say a simple substitute, reread the sentence, and test the target word in one new context with the same meaning.",
            "cases": [
                _case("far tower", "The tower is distant; from the village it appears as a tiny line beyond three fields.", "What does distant mean, and which use preserves that meaning?", "Distant means far away, as the tower beyond the fields is far from the village.", "Distant means bright enough to touch.", "Distant means moving very quickly nearby.", "The fields and tiny appearance establish great separation.", "distant far away", "three fields separation"),
                _case("dim lamp", "The lamp is dim, giving only enough light to see the edge of the step.", "Which meaning and use fit dim?", "Dim means not very bright, like the weak light on the step.", "Dim means louder than thunder.", "Dim means completely transparent.", "The limited visibility shows low brightness.", "dim not bright", "weak limited light"),
                _case("still street", "After the shops close, the lane is still: no carts move and no footsteps pass.", "What meaning does still carry here?", "Still means quiet and without movement in this lane.", "Still means crowded with racing carts.", "Still means colourful at noon.", "The absence of movement and footsteps defines the word.", "still without movement", "no carts footsteps"),
                _case("sun peep", "At dawn, a narrow ray begins to peep between the curtains before the full sun is visible.", "How does the clue explain peep?", "Peep means appear partly or briefly through a small opening.", "Peep means vanish beneath the floor.", "Peep means shout across a field.", "Only a narrow ray appears before the whole source can be seen.", "peep partly appears", "narrow opening clue"),
                _case("firefly glow", "One firefly gives a soft glow under the leaf, making a small patch visible.", "Which meaning belongs to glow?", "Glow means give a steady soft light.", "Glow means make a harsh crashing sound.", "Glow means become colder than ice.", "The gentle light on the leaf supplies the meaning.", "glow soft light", "gentle visible patch"),
                _case("distant train", "A distant train can be heard, but its windows look like tiny dots beyond the dark fields.", "Which new sentence would use distant accurately?", "The distant train is far beyond the fields.", "The distant train is touching my shoe.", "Distant means the train has no wheels.", "Tiny windows beyond fields confirm separation from the viewer.", "distant train far", "beyond dark fields"),
                _case("still pond", "The night pond is still, so the moon's reflection stays smooth instead of breaking into ripples.", "How should still be explained in this setting?", "Still means the pond water is not moving.", "Still means the pond is running downhill.", "Still means the moon is making noise.", "A smooth unbroken reflection is evidence of unmoving water.", "still water unmoving", "smooth no ripples"),
            ],
        },
        {
            "level_id": "night_blend_spelling",
            "title": "Complete sky blends",
            "focus": "spell and form words beginning with sp, st, and sk",
            "concept": "opening blend",
            "outcome": "Use a sentence meaning clue to choose sp, st, or sk, preserve both consonants, and form a complete context-matched word.",
            "skill_ids": ["vocab.spelling", "vocab.word_formation"],
            "episode_kind": "language_lab",
            "anchor_indexes": [3],
            "principle": "An opening blend keeps both consonants. The sentence meaning decides among sp, st, and sk; a pronounceable result is not enough if the word does not fit.",
            "connect": _connect(
                "Blend spelling combines a letter pattern with meaning. Readers try the full blend, form a real word, and check that the word names the object or action described.",
                "A bright __ar appears above the roof. The clue names a point of light in the night sky.",
                "Test st to form star and keep both opening consonants.",
            ),
            "misconception": "The learner drops one consonant or forms a real blend word that does not match the printed meaning clue.",
            "remediation": "Circle the meaning clue, try each full blend, cross out completed words that do not fit, and copy the chosen word with every letter.",
            "cases": [
                _case("star clue", "One bright __ar appears after sunset. The missing noun names a point of light in the sky.", "Which full spelling fits?", "The word is star, beginning with st.", "The word is tar, missing the opening blend.", "The word is spar, which does not fit this clue.", "Star keeps st and matches the sky-light meaning.", "star begins st", "point of light"),
                _case("sky clue", "Clouds drift across the __y. The missing noun names the wide space above Earth.", "Which blend completes the noun?", "The word is sky, beginning with sk.", "The word is ky without a complete blend.", "The word is spy, which means secretly watch.", "Sky preserves sk and fits the space-above clue.", "sky begins sk", "space above clue"),
                _case("spoon clue", "Mira uses a __oon to stir warm milk. The missing object has a small bowl and handle.", "How should the word be formed?", "The word is spoon, beginning with sp.", "The word is poon without its blend.", "The word is stone, which is a rock.", "Spoon keeps sp and matches the utensil description.", "spoon begins sp", "stirring utensil"),
                _case("storm clue", "A dark __orm brings wind and heavy rain. The clue names rough weather.", "Which spelling completes the weather word?", "The word is storm, beginning with st.", "The word is torm without the full blend.", "The word is skorm, which is not the named word.", "Storm uses st and matches wind with heavy rain.", "storm begins st", "rough weather clue"),
                _case("skate clue", "Ravi will __ate on the smooth rink using boots with blades.", "Which blend forms the action word?", "The word is skate, beginning with sk.", "The word is kate without the blend.", "The word is state, which means a condition.", "Skate keeps sk and fits the rink-and-blades action.", "skate begins sk", "rink blades action"),
                _case("spin clue", "The round top will __in when Noor twists its stem. The missing verb means turn quickly.", "What complete word belongs here?", "The word is spin, beginning with sp.", "The word is pin, which fastens paper.", "The word is skin, which covers a body.", "Spin preserves sp and matches quick turning.", "spin begins sp", "turn quickly clue"),
                _case("step clue", "Use the lowest __ep to climb onto the platform. The missing noun names one level of a stair.", "Which blend and word are correct?", "The word is step, beginning with st.", "The word is tep without a blend.", "The word is skep, which does not match the stair clue.", "Step retains st and names a stair level.", "step begins st", "stair level clue"),
            ],
        },
        {
            "level_id": "night_compound_words",
            "title": "Build compound sky words",
            "focus": "recognise word classes and construct sentences with compound words",
            "concept": "compound word",
            "outcome": "Combine two meaningful base words into a supported compound, identify its noun role, and use it in a complete sentence that shows meaning.",
            "skill_ids": ["grammar.noun_verb_adjective", "writing.complete_sentence"],
            "episode_kind": "language_lab",
            "anchor_indexes": [4],
            "principle": "A compound word joins complete base words to create one meaning. Its job in the sentence can be checked by asking whether it names, acts, or describes.",
            "connect": _connect(
                "Not every pair of nearby words forms a compound. Both parts must contribute to a recognised combined meaning, and the finished word must fit its sentence role.",
                "Sun and light join as sunlight, a noun naming natural light from the sun: Sunlight warmed the steps.",
                "Notice both base words and the complete noun sentence before building another compound.",
            ),
            "misconception": "The learner joins any two sky words, drops a base word, or names the compound without using it as a meaningful noun in a complete sentence.",
            "remediation": "Separate the proposed word into two bases, explain the combined meaning, label its sentence job, and write a subject-plus-verb sentence using it.",
            "cases": [
                _case("sunlight noun", "Sun joins light to name the natural light entering the window. The complete sentence needs a noun subject.", "Which compound and sentence are correct?", "Sunlight is a noun in 'Sunlight filled the room.'", "Sunrun is the correct word for natural light.", "Light is a verb in 'Light sunlight room.'", "Both bases create the named light and the sentence gives it a verb.", "sunlight noun", "filled complete sentence"),
                _case("moonlight noun", "Moon joins light to name the pale light seen at night. It falls across the courtyard.", "How should the compound be used?", "Moonlight is a noun in 'Moonlight crossed the courtyard.'", "Moonchair names light from the moon.", "Moonlight crossed courtyard without a subject role.", "The compound names the light and works as the sentence subject.", "moonlight noun", "crossed courtyard"),
                _case("sunrise noun", "Sun joins rise to name the time when the sun appears in the morning.", "Which complete use shows the combined meaning?", "Sunrise is a noun in 'Sunrise coloured the clouds.'", "Sunset means the morning appearance here.", "Rise sun clouds coloured.", "The base meanings combine into a named morning event.", "sunrise noun", "morning appearance"),
                _case("sunset noun", "Sun joins set to name the evening event when the sun disappears below the horizon.", "What sentence uses the compound accurately?", "Sunset is a noun in 'Sunset turned the river orange.'", "Sunflower names the evening event.", "Sunset orange river without a verb.", "The word names the event and the complete sentence tells its effect.", "sunset noun", "evening event effect"),
                _case("daylight noun", "Day joins light to name the natural light available during daytime.", "Which formation and sentence fit?", "Daylight is a noun in 'Daylight entered through the curtains.'", "Daystorm means daytime light.", "Daylight through curtains with no action.", "The bases form a recognised light word used with a clear verb.", "daylight noun", "entered through curtains"),
                _case("rainbow noun", "Rain joins bow to name a curved band of colours that may appear when light meets water drops.", "How can the compound appear in a complete sentence?", "Rainbow is a noun in 'A rainbow arched above the field.'", "Rainshoe names the coloured arc.", "A rainbow above field without a verb.", "The word names the coloured arc and arched completes the idea.", "rainbow noun", "arched above field"),
                _case("starlight noun", "Star joins light to name light coming from stars, though it may look faint from Earth.", "Which sentence demonstrates the noun?", "Starlight is a noun in 'Faint starlight reached the path.'", "Starplate means light from stars.", "Starlight faint path without a verb.", "The compound names light and reached supplies the action.", "starlight noun", "reached path"),
            ],
        },
        {
            "level_id": "night_day_cycle",
            "title": "Sequence evening and morning",
            "focus": "track a day-night sequence and maintain tense across completed events",
            "concept": "day and night cycle",
            "outcome": "Order visible changes from evening through night to morning and report completed observations consistently in past tense.",
            "skill_ids": ["reading.event_sequence", "grammar.tense_usage"],
            "episode_kind": "application_mission",
            "anchor_indexes": [1, 2],
            "principle": "Time markers control event order and tense. Yesterday or last night calls for past forms, while sequence must follow the printed changes in light and activity.",
            "connect": _connect(
                "A cycle passage can begin at any point, so readers rely on dusk, midnight, dawn, and morning rather than assuming the first mentioned event happened first.",
                "Yesterday, the western sky faded at dusk, lamps glowed during the night, and birds called when dawn arrived.",
                "Place the light changes in time and notice the past forms faded, glowed, and called.",
            ),
            "misconception": "The learner orders events by sentence position while ignoring time markers or shifts between present and past in a report about one completed night.",
            "remediation": "Circle every time marker, place events on a dusk-to-dawn line, underline verbs, and convert all completed actions to matching past forms.",
            "ordered_response": True,
            "cases": [
                _case("rooftop evening", "Last evening, the sun slipped behind the flats, the sky darkened, and porch lamps switched on.", "Which ordered past-tense report fits?", "The sun slipped away, the sky darkened, and the lamps switched on.", "The lamps switch on before last evening began.", "The sky darkens yesterday while the sun will slip.", "The visible light loss precedes darkness and artificial light.", "slipped darkened switched", "evening order past"),
                _case("camp night", "At dusk, campers stored their games. After darkness fell, they lit one lantern. At dawn, they packed the lantern.", "How should the completed sequence be told?", "They stored the games, lit the lantern at night, and packed it at dawn.", "They packed the lantern before lighting it.", "They store yesterday and will lit at dawn.", "Time markers establish storage, use, and later packing.", "stored lit packed", "dusk night dawn"),
                _case("flower watch", "Yesterday at sunset, a night flower opened. It stayed open under the moon and closed after sunrise.", "Which sequence preserves time and tense?", "The flower opened at sunset, remained open at night, and closed after sunrise.", "The flower closed before it opened.", "The flower opens yesterday and closed tomorrow.", "Sunset, night, and sunrise form the printed cycle.", "opened remained closed", "sunset night sunrise"),
                _case("street sounds", "Last night, traffic became quiet, crickets began calling, and the milk cart arrived near dawn.", "What ordered report is accurate?", "Traffic quieted, crickets called, and the milk cart arrived near dawn.", "The dawn cart arrived before the night grew quiet.", "Crickets call last night and traffic will quiet.", "The changing sounds and dawn marker fix the order.", "quieted called arrived", "night to dawn"),
                _case("shadow change", "Yesterday, long shadows stretched at sunset. They disappeared in darkness and returned when morning light reached the wall.", "How should the shadow sequence be expressed?", "Shadows stretched, disappeared at night, and returned in morning light.", "Shadows returned before sunset stretched them.", "They disappear yesterday and will stretched.", "The printed light conditions explain each past event.", "stretched disappeared returned", "light conditions order"),
                _case("bakery morning", "Before dawn, the bakery windows were dark. The baker arrived, turned on the lights, and opened the door after sunrise.", "Which past-tense order follows the passage?", "The windows were dark, the baker arrived and lit them, and the door opened after sunrise.", "The door opened before the baker arrived.", "The baker arrive before dawn and opens yesterday.", "Arrival makes lighting possible before the later opening.", "were arrived opened", "before dawn after sunrise"),
                _case("moonset", "During the completed observation, the moon stood high at midnight, moved lower before dawn, and disappeared as the sky brightened.", "Which report keeps sequence and tense?", "The moon stood high, moved lower, and disappeared as morning brightened.", "The moon disappeared before standing high.", "The moon stands last night and will moved.", "Position and light clues show the ordered completed movement.", "stood moved disappeared", "midnight before dawn"),
            ],
        },
        {
            "level_id": "night_inference",
            "title": "Infer from changing light",
            "focus": "infer a reason from sky clues and construct an evidence-based answer",
            "concept": "night inference",
            "outcome": "Infer why a person changes an action as light changes and justify the answer with a precise clue from the visible scene.",
            "skill_ids": ["reading.inference_reason", "writing.reason_answer"],
            "episode_kind": "retrieval_challenge",
            "anchor_indexes": [2],
            "principle": "An inference joins an action with a relevant light, time, or visibility clue. The answer should not add unseen weather, danger, or conversation.",
            "connect": _connect(
                "Writers often show a changing need without naming it directly. Readers compare what a person could see before and after the sky changed.",
                "As the path grew dim, Sohan stopped reading the small map and switched on his torch.",
                "Use the dim path and small print to infer why the torch became necessary.",
            ),
            "misconception": "The learner repeats the action as its own reason or invents an unrelated threat instead of connecting visibility and time clues.",
            "remediation": "Underline the changed action, box the light clue, complete a because sentence, and delete any detail that cannot be traced to the reference.",
            "creative_transfer": True,
            "cases": [
                _case("map torch", "The path darkens, and Sohan can no longer read the small map. He switches on a torch.", "Why does Sohan use the torch?", "Sohan uses the torch because darkness makes the small map hard to read.", "Sohan uses it because the sun is brighter at noon.", "An unseen animal orders him to use it.", "Reduced visibility directly explains the new light source.", "torch because dark", "map hard to read"),
                _case("curtains closed", "Asha closes the curtains after the room lamp comes on because moths are gathering near the open window.", "What reason can be inferred for closing the curtains?", "Asha closes them to reduce the lamp light attracting moths at the window.", "Asha closes them to make the sun rise.", "The curtains are a kind of moth.", "The gathering insects and lit room establish the purpose.", "closes reduce light", "moths gather lamp"),
                _case("reflective strip", "The cyclist waits until dusk, checks that a reflective strip is visible on his bag, and then begins the ride.", "Why does he check the strip at dusk?", "He checks it because the reflective strip helps others notice the bag in lower light.", "He checks it because the bag is invisible at noon forever.", "The strip powers the bicycle wheels.", "Dusk lowers visibility, making a reflective marker useful.", "checks reflective strip", "lower light visibility"),
                _case("seedling cover", "The sky clears on a cold night, and the gardener covers tender seedlings before going inside.", "Which inference fits the timing?", "The gardener covers the seedlings to protect them during the cold night.", "The gardener covers them to create sunlight at midnight.", "The seedlings asked for a blanket in dialogue.", "The stated cold condition supports the protective action.", "covers protect seedlings", "cold night clue"),
                _case("morning curtains", "A pale glow enters the room, birds begin calling, and Reva opens the curtains before checking the clock.", "Why can Reva expect morning?", "Reva infers morning from the growing light and bird calls.", "Reva infers midnight because the room brightens.", "The clock speaks before she sees it.", "Two independent dawn clues support the time inference.", "infers morning", "light bird calls"),
                _case("shop sign", "At sunset, the fruit seller turns on a small lamp above the price sign while the stall remains open.", "What reason explains the lamp?", "The seller turns it on so customers can read the sign as daylight fades.", "The seller turns it on to make fruit grow instantly.", "The sign becomes the moon.", "Fading light and continued trading create a reading need.", "lamp read sign", "daylight fades"),
                _case("quiet dog", "The family dog stops barking when familiar footsteps reach the gate, though the lane is too dark to see the person.", "What inference explains the dog's change?", "The dog likely recognises the familiar footsteps and no longer treats them as unknown.", "The dog sees bright noon sunlight.", "The gate tells the dog a secret name.", "The sound clue changes while visual information remains unavailable.", "recognises familiar footsteps", "sound changes response"),
            ],
        },
    ],
}


FRESH_CASES = {
    "night_sky_images": [
        _fresh_case("silver boat", "A poem calls the thin moon a silver boat sailing above dark roofs.", "What shared feature makes the image work?", "The curved moon looks like a small silver boat.", "Both have a slim curved shape against a darker space.", "curved moon silver boat", "same slim shape"),
        _fresh_case("star buttons", "The verse says stars are bright buttons sewn onto a black coat.", "Explain the comparison.", "The small bright stars look like buttons on a dark sky.", "Their size, shine, and dark background support the picture.", "stars look like buttons", "bright on dark"),
        _fresh_case("cloud sheep", "At dusk, pale clouds drift together like a flock of slow sheep.", "Which detail joins clouds and sheep?", "The grouped clouds move slowly like a flock.", "Their soft shapes and shared movement create the image.", "clouds like sheep", "soft grouped movement"),
        _fresh_case("sun coin", "The setting sun is described as a red coin slipping behind the hill.", "How does coin help the reader picture sunset?", "The round red sun looks like a coin near the hill.", "Round shape and colour are the shared clues.", "sun like red coin", "round colour clue"),
        _fresh_case("night blanket", "A line says night pulled a dark blanket across the busy town.", "What change does blanket suggest?", "Darkness spread over the town like a covering blanket.", "A blanket covers, just as night hides daytime sights.", "night covers town", "blanket hides sights"),
        _fresh_case("moon lamp", "The full moon hangs like a quiet lamp above the empty road.", "Why is lamp a useful image?", "The moon seems like a lamp giving light to the road.", "Both shine above an otherwise dark place.", "moon like lamp", "lights dark road"),
        _fresh_case("cloud curtain", "Grey clouds close like curtains and hide the last orange light.", "What action is shared?", "The clouds hide light as curtains hide a view.", "Closing and covering connect both things.", "clouds like curtains", "close and hide"),
        _fresh_case("rain strings", "Under the streetlamp, rain looks like silver strings falling from the sky.", "Which feature supports strings?", "The thin bright rain lines look like silver strings.", "Light makes the long drops appear narrow and shining.", "rain like silver strings", "thin bright lines"),
        _fresh_case("dawn door", "A poem calls the first golden light a door opening into morning.", "What change does the door image show?", "The opening light shows night giving way to day.", "A door opening suggests entry into a new time.", "light opens morning", "night changes to day"),
        _fresh_case("star seeds", "Stars are called seeds scattered across a deep blue field.", "How should readers understand the seeds?", "The many small stars look scattered like seeds.", "Their number and spread create the comparison.", "stars like scattered seeds", "many small points"),
        _fresh_case("moon smile", "A crescent moon is a pale smile above the sleeping houses.", "Which shape makes the image clear?", "The curved crescent looks like a smiling mouth.", "The upward curve is shared by both.", "crescent like smile", "same upward curve"),
        _fresh_case("sunset fire", "The western clouds glow like a row of small fires before darkness arrives.", "What main change is pictured?", "Bright sunset colours fade as night approaches.", "The glow occurs just before the stated darkness.", "sunset glow then night", "fire colours fade"),
        _fresh_case("comet chalk", "A poem calls a comet a bright chalk line drawn quickly across the blackboard sky.", "How does the chalk-line image support the night-sky idea?", "The comet looks like a quick bright line across the dark sky.", "Its long shining trail resembles chalk on a black board.", "comet like chalk line", "bright trail dark sky"),
        _fresh_case("cloud island", "One low cloud floats in moonlight like a pale island in a deep blue sea.", "Which visible clues make the cloud-island picture work?", "The pale cloud looks like an island surrounded by blue night sky.", "Its separate shape and darker space create the comparison.", "cloud looks like island", "pale shape blue space"),
        _fresh_case("stars salt", "The verse says someone sprinkled silver salt across the night, leaving hundreds of tiny shining grains.", "Explain the silver-salt image and its whole sky idea.", "The many small stars look like silver salt scattered across darkness.", "Tiny bright points spread widely support the playful picture.", "stars like silver salt", "tiny points spread widely"),
    ],
    "night_context_words": [
        _fresh_case("dusk walk", "The sun has just gone below the roofs, but the sky is not fully dark. The card calls this dusk.", "What does dusk mean here?", "Dusk is the dim time just after sunset.", "The sun is down while some light remains.", "dusk after sunset", "dim light remains"),
        _fresh_case("faint star", "One star is hard to see because its light is weak. The note calls it faint.", "Explain faint from context.", "Faint means not bright or easy to see.", "Weak light gives the word's meaning.", "faint means weak light", "hard to see"),
        _fresh_case("glowing lamp", "The lamp gives a steady warm light without a flame. It glows beside the bed.", "How is glows used?", "Glows means gives a soft steady light.", "The warm light clue explains the verb.", "glows soft light", "steady warm shine"),
        _fresh_case("horizon line", "The sky seems to meet the far field at one low line. That line is the horizon.", "What is the horizon?", "The horizon is the far line where land and sky seem to meet.", "The card gives a direct place clue.", "horizon land sky line", "far meeting place"),
        _fresh_case("twinkle change", "The star seems to brighten and dim again and again. It appears to twinkle.", "Which meaning fits twinkle?", "Twinkle means appear to flash with changing light.", "Repeated bright and dim moments explain it.", "twinkle changing light", "bright then dim"),
        _fresh_case("shadow wall", "A dark shape copies the tree on the wall when the lamp shines. The shape is a shadow.", "What creates the shadow?", "The tree blocks light and makes a dark shape.", "The wall shape follows the object between lamp and wall.", "tree makes shadow", "blocks lamp light"),
        _fresh_case("silent lane", "No carts, voices, or footsteps can be heard on the lane. The lane is silent.", "What does silent tell us?", "Silent means making or holding no sound.", "The list of missing sounds gives the meaning.", "silent no sound", "no voices footsteps"),
        _fresh_case("dim room", "Only one weak bulb lights the room, so faces are difficult to see. The room is dim.", "Which meaning fits dim?", "Dim means having little light.", "The weak bulb and hard-to-see faces support it.", "dim little light", "weak bulb clue"),
        _fresh_case("gleam on water", "A narrow strip of moonlight shines briefly on the pond. The strip is a gleam.", "What is a gleam here?", "A gleam is a small or brief shine.", "The narrow shining strip gives the meaning.", "gleam brief shine", "narrow moonlight strip"),
        _fresh_case("nightfall", "Birds settle, lamps turn on, and the sky becomes dark. The card calls this nightfall.", "When does nightfall happen?", "Nightfall is the time when evening becomes night.", "Darkening sky and lamps show the change.", "nightfall evening to night", "sky becomes dark"),
        _fresh_case("dawn colour", "A pale pink band appears before the sun rises. The note calls this dawn.", "What does dawn mean?", "Dawn is the first light before sunrise.", "The early band appears before the sun.", "dawn first light", "before sunrise"),
        _fresh_case("sparkle frost", "Tiny frost points reflect the torch and look bright. They sparkle.", "How does sparkle fit?", "Sparkle means shine in many small bright flashes.", "The many reflected points support the word.", "sparkle small flashes", "frost reflects torch"),
        _fresh_case("distant tower", "A tower looks tiny beyond three fields even though it is tall up close. The card calls it distant.", "What does distant mean in the tower card, and how can it be used in a new sentence?", "Distant means far away. A distant train looked like a short silver line.", "Three fields and the tiny appearance show great distance.", "distant means far away", "three fields away"),
        _fresh_case("still pond", "The pond surface has no ripples, and the reflected moon does not shake. The water is still.", "Explain still from the pond clues and use it with the same meaning elsewhere.", "Still means not moving. The still flag hung without a breeze.", "No ripples and an unshaken reflection show no movement.", "still means not moving", "no ripples reflection steady"),
        _fresh_case("peeping moon", "The moon peeps between two clouds: only a thin bright edge is visible before the clouds meet again.", "What does peeps mean here, and how can peep fit another sentence?", "Peeps means appears briefly through a small gap. A kitten peeped from behind the curtain.", "Only one edge through the cloud gap gives the meaning.", "peeps appears briefly", "edge through cloud gap"),
    ],
    "night_blend_spelling": [
        _fresh_case("star word", "The night card shows __ar beside a bright point in the sky. The opening letters are st.", "Form the whole word.", "The word is star, beginning with st.", "The st blend and sky clue fit together.", "star begins st", "bright sky point"),
        _fresh_case("sky word", "Birds cross the __y before sunset. The missing noun names the space above us.", "Which blend completes the word?", "The word is sky, beginning with sk.", "Sky keeps sk and matches above us.", "sky begins sk", "space above clue"),
        _fresh_case("sleep word", "At night, the child will __eep for eight hours. The action means rest.", "Spell the rest word.", "The word is sleep, beginning with sl.", "Sleep uses sl and fits night rest.", "sleep begins sl", "night rest clue"),
        _fresh_case("snow word", "White __ow covers the cold hill. The noun names frozen flakes.", "What opening blend is needed?", "The word is snow, beginning with sn.", "Snow keeps sn and matches frozen flakes.", "snow begins sn", "frozen flakes clue"),
        _fresh_case("stone word", "A smooth __one lies beside the moonlit path. The noun names a hard rock piece.", "Complete the spelling.", "The word is stone, beginning with st.", "Stone uses st and fits the rock clue.", "stone begins st", "hard rock clue"),
        _fresh_case("skip word", "The child will __ip over two chalk lines. The verb names a light jump.", "Build the action word.", "The word is skip, beginning with sk.", "Skip has sk and matches the jumping action.", "skip begins sk", "light jump clue"),
        _fresh_case("slow word", "The moon seems to move __ow across the display. The word means not fast.", "Which blend finishes the word?", "The word is slow, beginning with sl.", "Slow uses sl and matches not fast.", "slow begins sl", "not fast meaning"),
        _fresh_case("snail word", "A __ail moves across the damp step after rain. The animal carries a shell.", "Spell the animal word.", "The word is snail, beginning with sn.", "Snail keeps sn and fits the shell clue.", "snail begins sn", "shell animal clue"),
        _fresh_case("stem word", "The flower's __em holds its head above the soil. The noun names the supporting plant part.", "What letters complete it?", "The word is stem, beginning with st.", "Stem uses st and matches the plant support.", "stem begins st", "supports flower head"),
        _fresh_case("skin word", "The orange has thick __in around its fruit. The missing noun names the outer covering.", "Which formed word fits?", "The word is skin, beginning with sk.", "Skin keeps sk and matches outer covering.", "skin begins sk", "outer fruit covering"),
        _fresh_case("slide word", "The bead will __ide down the tilted board. The verb means move smoothly.", "Write the full verb.", "The word is slide, beginning with sl.", "Slide has sl and fits smooth movement.", "slide begins sl", "smooth down movement"),
        _fresh_case("snug word", "The blanket feels __ug around the child. The adjective means warm and close-fitting.", "Complete the adjective.", "The word is snug, beginning with sn.", "Snug keeps sn and matches the warm close fit.", "snug begins sn", "warm close fitting"),
        _fresh_case("spoon word", "A metal __oon rests beside the night-time soup bowl. The missing noun names an eating tool.", "Which opening blend completes the eating-tool word?", "The word is spoon, beginning with sp.", "Spoon keeps sp and matches the bowl-side utensil clue.", "spoon begins sp", "eating tool clue"),
        _fresh_case("step word", "One stone __ep leads from the terrace to the garden. The missing noun names a place for a foot.", "Spell the complete terrace word.", "The word is step, beginning with st.", "Step preserves st and fits the foot-place clue.", "step begins st", "place for foot"),
        _fresh_case("sketch word", "Mira made a quick __etch of the crescent moon. The missing noun means a simple drawing.", "What opening blend forms the drawing word?", "The word is sketch, beginning with sk.", "Sketch uses sk and matches the quick drawing clue.", "sketch begins sk", "simple moon drawing"),
    ],
    "night_compound_words": [
        _fresh_case("moonlight", "Moon and light join to name light that comes from the moon.", "Form the compound and use it.", "Moonlight shone across the quiet path.", "Moon plus light forms one noun used as the sentence subject.", "moonlight shone path", "moon plus light"),
        _fresh_case("starlight", "Star and light join for the faint light seen from stars.", "Write a complete compound sentence.", "Starlight made tiny points on the water.", "The joined noun names the light and made gives its action.", "starlight made points", "star plus light"),
        _fresh_case("bedtime", "Bed and time join to name the usual time for going to bed.", "How can the compound be used?", "Bedtime came after Mira finished her story.", "The compound acts as a noun for a time.", "bedtime after story", "bed plus time"),
        _fresh_case("lamplight", "A reading lamp gives a warm glow. The compound lamplight names that glow.", "Use lamplight in one full sentence.", "Warm lamplight filled the reading corner.", "The compound is a noun, and filled gives it a clear action.", "warm lamplight corner", "lamp glow compound"),
        _fresh_case("sunrise", "Sun and rise form the word for the sun appearing in the morning.", "Write a sentence with sunrise.", "Sunrise coloured the eastern clouds pink.", "The compound is a noun and coloured is its verb.", "sunrise coloured clouds", "sun appears morning"),
        _fresh_case("nightfall", "Night and fall join for the time darkness begins.", "Which sentence uses the compound?", "The bats left their shelter at nightfall.", "Nightfall names when the action happened.", "bats at nightfall", "darkness begins"),
        _fresh_case("moonbeam", "Moon and beam join to name one line of moonlight.", "Form a clear sentence.", "A moonbeam crossed the bedroom wall.", "The compound names the subject and crossed gives an action.", "moonbeam crossed wall", "line of moonlight"),
        _fresh_case("raindrop", "Rain and drop join to name one drop of rain.", "Use raindrop as a noun.", "One raindrop landed on the window.", "One confirms the compound is a countable noun.", "raindrop landed window", "one drop rain"),
        _fresh_case("rooftop", "Roof and top join to name the upper surface of a roof.", "Write the compound in context.", "A cat rested on the warm rooftop.", "The word names a place after on.", "cat on rooftop", "top of roof"),
        _fresh_case("flashlight", "Flash and light form the noun for a small hand-held lamp.", "How can flashlight be used?", "Nikhil aimed the flashlight at the dark steps.", "The compound names the object receiving the action.", "aimed flashlight steps", "hand held light"),
        _fresh_case("classroom", "Class and room join to name a room used by a class.", "Write one complete sentence.", "The classroom became quiet after the bell.", "The joined noun is the subject and became is the verb.", "classroom became quiet", "class plus room"),
        _fresh_case("dreamland", "Dream and land join in a playful word for an imagined dream place.", "Use the compound without treating it as real geography.", "The sleepy child sailed to dreamland in her story.", "The story clue keeps the compound imaginative.", "sailed to dreamland", "imagined dream place"),
        _fresh_case("moonrise", "Moon and rise join for the moon appearing above the horizon.", "Build moonrise, then write a full sentence where the joined word names an event.", "Moonrise lit the hill after the evening clouds moved away.", "The compound names the event, and lit gives its effect.", "moonrise lit hill", "moon appears horizon"),
        _fresh_case("streetlight", "Street and light join to name a lamp beside a road.", "Write one sentence that shows the compound's meaning.", "The streetlight shone over the zebra crossing.", "The joined noun names the road lamp and acts as the subject.", "streetlight shone crossing", "road lamp compound"),
        _fresh_case("sunset", "Sun and set combine to name the evening time when the sun goes below the horizon.", "Use sunset clearly in one complete sentence.", "Sunset turned the river orange before nightfall.", "The compound is a time noun linked to the evening colour change.", "sunset turned river orange", "sun goes below horizon"),
    ],
    "night_day_cycle": [
        _fresh_case("evening lamps", "The sun lowers, the sky turns orange, street lamps switch on, and darkness covers the road.", "Order the change into night.", "First the sun lowers, next colours fade, then lamps turn on, and finally night arrives.", "The light changes lead from evening to darkness.", "sun colour lamps night", "evening before darkness"),
        _fresh_case("morning birds", "The eastern sky pales, one bird calls, the sun rises, and more birds leave their nests.", "Which event is third?", "The sun rises third in the shown order.", "Two clues occur before the rising sun.", "sun rises third", "after pale sky bird"),
        _fresh_case("shadow change", "At noon a pole has a short shadow. In late afternoon the shadow grows long, then disappears after sunset.", "Retell the shadow changes.", "The shadow is short, grows long, and disappears after sunset.", "The time words give the exact order.", "short long disappears", "noon afternoon sunset"),
        _fresh_case("owl routine", "At dusk an owl opens its eyes, leaves the tree after dark, hunts at night, and returns before sunrise.", "Write the routine in order.", "The owl wakes at dusk, leaves after dark, hunts, and returns before sunrise.", "Each time clue places one action.", "wakes leaves hunts returns", "dusk to sunrise"),
        _fresh_case("shop signs", "Yesterday the shop sign glowed at night, switched off at dawn, and stayed off through the bright morning.", "Report the completed sequence in past tense.", "The sign glowed, switched off at dawn, and stayed off in daylight.", "Yesterday calls for past forms in the shown order.", "glowed switched stayed", "yesterday past sequence"),
        _fresh_case("flower closing", "A flower faces the sun all afternoon, folds its petals at sunset, and opens them again after sunrise.", "What happens between facing and reopening?", "The flower folds its petals at sunset.", "The sunset action lies between the two stated events.", "folds petals at sunset", "between afternoon sunrise"),
        _fresh_case("home lights", "Before evening, the windows reflect sunlight. At dusk lamps appear, and at bedtime most rooms become dark.", "Which sequence describes the windows?", "They reflect sun, show lamp light, and become dark by bedtime.", "The three time markers guide the order.", "sun lamps dark", "before dusk bedtime"),
        _fresh_case("moon path", "The moon rises behind trees, moves higher by midnight, and sinks near the western roofs before dawn.", "Retell the visible path.", "The moon rises, climbs higher, and sinks before dawn.", "Position and time clues show the path.", "rises climbs sinks", "night position order"),
        _fresh_case("cloudy dawn", "At first the sky is dark. A pale band appears, clouds turn pink, and the sun finally clears the hill.", "What is the final event?", "The sun clears the hill after the clouds turn pink.", "Finally marks the last change.", "sun clears hill", "after pink clouds"),
        _fresh_case("night bus", "Last night the bus left at dusk, crossed the bridge after dark, and reached the depot before midnight.", "Write the trip using past verbs.", "The bus left, crossed the bridge, and reached the depot before midnight.", "Last night and ordered times support the completed verbs.", "bus left crossed reached", "last night trip"),
        _fresh_case("dew morning", "Before sunrise, dew covers the grass. Sunlight reaches it, drops shrink, and the grass dries.", "Why does drying come last?", "The grass dries after sunlight makes the dew shrink.", "Water must disappear before the grass becomes dry.", "dew shrinks then dries", "sunlight before dry"),
        _fresh_case("evening meal", "The family watched sunset, closed the curtains when darkness came, ate dinner, and turned off lights at bedtime.", "Place bedtime correctly.", "Turning off the lights happens last at bedtime.", "The earlier evening actions are printed before it.", "lights off last", "after sunset dinner"),
        _fresh_case("terrace lamp cycle", "Yesterday the terrace was bright at sunset, the lamp switched on after dark, moths gathered at night, and the lamp switched off at dawn.", "Report the terrace-lamp cycle in order with past-tense verbs.", "The terrace darkened, the lamp switched on, moths gathered, and the lamp switched off at dawn.", "Yesterday and the four time clues support the completed sequence.", "darkened switched gathered switched off", "sunset night dawn order"),
        _fresh_case("garden bud morning", "Before sunrise a flower bud stayed closed. First light reached the bed, the bud opened, and a bee landed after the sun rose.", "Order the garden-bud changes and explain why the bee event comes last.", "The bud stayed closed, received first light, opened, and then a bee landed.", "The card places the bee after sunrise and after the flower opens.", "closed light opened bee", "bee after sunrise opening"),
        _fresh_case("station clock night", "Last evening the station clock glowed at dusk, showed ten during the dark night, faded in early daylight, and looked plain by morning.", "Retell the station-clock changes consistently in past tense.", "The clock glowed at dusk, showed ten at night, faded at dawn, and looked plain in the morning.", "The printed time markers keep every completed change in order.", "glowed showed faded looked", "dusk night dawn morning"),
    ],
    "night_inference": [
        _fresh_case("wet bench", "The bench is wet at dawn, but no sprinkler ran. Dark clouds and puddles remain nearby.", "What probably happened overnight?", "Rain probably fell during the night.", "Clouds, puddles, and a wet bench support the idea.", "rain fell overnight", "clouds puddles wet"),
        _fresh_case("open flowers", "White flowers stay closed by day and open when the moon rises. Moths gather around them.", "Why might the flowers open at night?", "They may open at night to attract the visiting moths.", "The opening time and moth crowd appear together.", "flowers attract moths", "open when moths visit"),
        _fresh_case("quiet nest", "At dusk the parent birds return, tuck their heads under wings, and the nest becomes still.", "What can you infer?", "The birds are settling to sleep for the night.", "Returned birds, tucked heads, and stillness are sleep clues.", "birds settle to sleep", "tucked heads still"),
        _fresh_case("torch marks", "A torch lies beside muddy shoe marks leading from the gate to the shed.", "Why was the torch probably used?", "Someone likely used the torch to see the dark path to the shed.", "Night equipment and the route marks support this.", "torch lit shed path", "muddy route at night"),
        _fresh_case("early baker", "The bakery light is on before sunrise, and warm bread is ready when the first bus arrives.", "Why is the light on so early?", "The baker started work early to prepare bread for morning customers.", "Warm ready bread connects the early light with baking.", "baker prepares morning bread", "light before sunrise"),
        _fresh_case("covered telescope", "Thick clouds hide every star, so Rina puts the telescope back in its case.", "Why does she stop using it?", "Rina stops because clouds block the night sky she wants to see.", "No stars are visible through the stated cloud cover.", "clouds block telescope view", "stars hidden"),
        _fresh_case("sleepy guard", "The guard yawns near dawn after checking the gate through the whole night.", "What explains the yawn?", "The guard is tired after staying awake all night.", "The long night watch supplies the reason.", "guard tired from night", "awake whole night"),
        _fresh_case("fading stars", "Stars seem fewer as the eastern sky grows brighter, though they have not moved away.", "Why do they seem to vanish?", "The growing daylight makes the stars harder to see.", "Brightness, not movement, changes their visibility.", "daylight hides stars", "eastern sky brighter"),
        _fresh_case("closed curtains", "A room lamp is on, but thick curtains are closed before a night film begins.", "Why are the curtains probably closed?", "The curtains likely block outside light for a darker room.", "A film and closed covering suggest light control.", "curtains block outside light", "dark room for film"),
        _fresh_case("cat at door", "A cat waits by the door at dusk each day, and a food bowl is placed outside soon after.", "What has the cat probably learned?", "The cat has learned that food comes outside around dusk.", "Repeated timing links waiting with the bowl.", "cat expects dusk food", "daily bowl follows"),
        _fresh_case("cool roof", "The roof is hot at sunset but cool when Mira steps out before dawn.", "Why did the roof cool?", "It lost heat during the night without strong sunlight.", "The time change removes the daytime heat source.", "roof cooled overnight", "no strong sunlight"),
        _fresh_case("lamp insects", "Many insects circle the only bright lamp, while the unlit corner has almost none.", "What inference fits their movement?", "The insects are attracted to the bright lamp.", "Their different numbers follow the presence of light.", "insects attracted to lamp", "more near bright light"),
        _fresh_case("cycle lamp", "At dusk, Veer stops his bicycle and switches on the front lamp before entering a lane with no streetlights.", "Why does Veer change his bicycle before the dark lane?", "Veer switches on the lamp so he can see and be seen in the unlit lane.", "Dusk and the missing streetlights make extra visibility necessary.", "lamp helps see and be seen", "dusk unlit lane"),
        _fresh_case("covered bread", "A bakery stall covers its bread when the night air becomes damp, and the loaves remain dry until closing.", "Why did the seller cover the bread after dark?", "The seller covered the bread to protect it from the damp night air.", "The later dry loaves show that the cover blocked moisture.", "cover protects bread", "damp air loaves dry"),
        _fresh_case("moved telescope", "Clouds cover the eastern terrace, but the western side stays clear. Asha carries the telescope west and soon finds three stars.", "Why does Asha move the telescope across the terrace?", "Asha moves it west because the clear sky there gives a better star view.", "Clouds in the east and visible stars in the west support her choice.", "moves west for clear view", "east clouds west stars"),
    ],
}

for _level_spec in SPEC["levels"]:
    _level_spec["fresh_cases"] = FRESH_CASES[_level_spec["level_id"]]


SPEC["assessment_pairs"] = [
    _assessment_pair("reading.poetic_language", _fresh_case("moon bowl", "A poem calls the full moon a silver bowl resting on a dark shelf.", "Explain the image.", "The round moon looks like a silver bowl against the dark sky.", "Shape, colour, and background support the comparison.", "moon like silver bowl", "round bright on dark"), _fresh_case("cloud ships", "Long clouds are ships sailing across the evening sky.", "What feature makes the comparison work?", "The long drifting clouds seem like ships moving slowly.", "Their shape and motion create the picture.", "clouds like ships", "long drifting movement"), kind="open"),
    _assessment_pair("reading.paragraph_main_idea", _fresh_case("town darkens", "The sun slips away, lamps appear in windows, shops close, and stars become visible.", "State the whole idea.", "The town changes from evening light to nighttime darkness.", "Every detail shows one part of night arriving.", "town changes to night", "sun lamps shops stars"), _fresh_case("morning wakes", "A pale sky appears, birds call, doors open, and the first bus starts.", "What is the card mostly about?", "Morning light brings the neighbourhood back to activity.", "The light and waking actions support one idea.", "morning starts activity", "sky birds doors bus"), kind="open"),
    _assessment_pair("reading.word_meaning_context", _case("faint lamp", "The lamp is barely visible from the gate. Its light is faint.", "What does faint mean?", "Faint means weak and hard to see.", "Faint means very loud.", "Faint means close enough to touch.", "Barely visible gives the meaning.", "faint weak light", "hard to see"), _case("dawn card", "A pink line appears before sunrise. The card calls it dawn.", "Which meaning fits dawn?", "Dawn is the first light of morning.", "Dawn is the middle of a dark night.", "Dawn is a type of roof.", "Before sunrise is the direct clue.", "dawn first morning light", "before sunrise"), kind="choice"),
    _assessment_pair("vocab.chapter_word_usage", _case("horizon use", "The ship looks small where sea and sky seem to meet.", "Which sentence uses horizon correctly?", "The ship moved near the horizon.", "Horizon means a lamp beside the bed.", "The horizon slept under a blanket.", "The meeting line gives the word's place meaning.", "ship near horizon", "sea sky meeting line"), _case("twinkle use", "A star seems to flash as its light brightens and fades.", "Which sentence uses twinkle?", "The star appears to twinkle above the roof.", "Twinkle means remain completely dark.", "The roof twinkles by making noise.", "Changing light supports the word.", "star appears to twinkle", "brightens and fades"), kind="choice"),
    _assessment_pair("vocab.spelling", _case("sleep gap", "The child will __eep after the story.", "Which spelling completes the rest word?", "sleep", "seep", "skeep", "Sleep keeps sl and fits rest.", "sleep with sl", "rest clue"), _case("stone gap", "A grey __one lies on the path.", "Which spelling fits the rock word?", "stone", "tone", "snone", "Stone uses st and matches rock.", "stone with st", "rock clue"), kind="choice"),
    _assessment_pair("vocab.word_formation", _fresh_case("snail use", "The letters sn complete __ail, an animal with a shell.", "Form and use the word.", "The word is snail; a snail crossed the wet step slowly.", "The blend and shell-animal sentence fit.", "snail crossed step", "sn shell animal"), _fresh_case("slide use", "The letters sl complete __ide, meaning move smoothly.", "Build the word and write a sentence.", "The word is slide; the bead will slide down the board.", "The blend and movement context match.", "bead will slide", "sl smooth movement"), kind="open"),
    _assessment_pair("grammar.noun_verb_adjective", _case("moonlight role", "In 'Soft moonlight covered the yard,' the task asks about moonlight.", "What word job does moonlight have?", "Moonlight is a noun naming the light.", "Moonlight is the action verb.", "Moonlight is an adjective for soft.", "It names what covered the yard.", "moonlight is noun", "names the light"), _case("glowed role", "In 'The lamp glowed softly,' the task asks about glowed.", "Which role fits?", "Glowed is the verb showing the lamp's action.", "Glowed is the lamp noun.", "Glowed is an adjective for softly.", "It tells what the lamp did.", "glowed is verb", "lamp action"), kind="choice"),
    _assessment_pair("writing.complete_sentence", _fresh_case("sunset sentence", "Use sunset as a noun and orange as its describing word.", "Write one complete sentence.", "The orange sunset filled the western sky with colour.", "The noun has a describing word and a clear action.", "orange sunset filled sky", "noun adjective action"), _fresh_case("moonbeam sentence", "Use moonbeam as the subject and crossed as the action.", "Build a complete sentence.", "A pale moonbeam crossed the quiet bedroom wall.", "The sentence has a subject, action, and place.", "moonbeam crossed wall", "subject action place"), kind="open", interaction_type="paragraph_text"),
    _assessment_pair("reading.event_sequence", _case("dawn order", "The sky pales, birds call, the sun rises, and shadows appear.", "Which order matches?", "Pale sky, bird calls, sunrise, then shadows.", "Shadows, midnight, then pale sky.", "Sunrise before any pale light.", "The printed events guide the order.", "pale birds sun shadows", "shown time order"), _case("night order", "The sun sets, lamps turn on, stars appear, and the street grows quiet.", "What happens third?", "Stars appear third.", "The sun rises third.", "Lamps turn off third.", "Two events are named before stars.", "stars appear third", "after sunset lamps"), kind="choice"),
    _assessment_pair("grammar.tense_usage", _fresh_case("past moon", "Time clue: last night. The moon rises and lights the yard.", "Report the actions in past tense.", "Last night, the moon rose and lit the yard.", "Rose and lit match the completed time.", "moon rose lit", "last night past"), _fresh_case("past bus", "Time clue: yesterday evening. The bus leaves at dusk and reaches town after dark.", "Rewrite with past verbs.", "Yesterday evening, the bus left at dusk and reached town after dark.", "Left and reached fit the time clue.", "bus left reached", "yesterday past verbs"), kind="open"),
    _assessment_pair("reading.inference_reason", _fresh_case("puddle dawn", "At dawn, puddles cover the lane and every roof is wet, though taps are closed.", "What likely happened?", "Rain likely fell during the night.", "Wet roofs and many puddles support rain.", "rain fell at night", "wet roofs puddles"), _fresh_case("lamp moths", "Moths crowd one glowing bulb and ignore the dark wall beside it.", "What can you infer?", "The moths are drawn to the bulb's light.", "Their numbers change with brightness.", "moths drawn to light", "crowd glowing bulb"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("closed telescope", "Clouds cover the sky, and Renu closes her telescope case.", "Explain her choice.", "Renu closes the telescope because clouds hide the stars.", "The covered sky blocks what she planned to view.", "closes because clouds", "stars hidden"), _fresh_case("early curtain", "Sunlight enters the room before a sleeping child wakes, so an adult closes the curtain.", "Why is the curtain closed?", "The curtain is closed because bright sunlight may wake the child.", "The sleeping child and early light give the reason.", "curtain blocks sunlight", "protects sleeping child"), kind="open"),
    _assessment_pair("reading.inference_reason", _fresh_case("cool grass", "Grass is damp before sunrise even though no rain fell and no tap ran.", "What likely formed on it?", "Dew likely formed on the cool grass overnight.", "The early dampness without rain supports dew.", "dew formed overnight", "damp without rain"), _fresh_case("owl return", "An owl flies back to its tree as the eastern sky becomes pale.", "Why is it returning?", "The owl is likely ending its night activity as morning begins.", "Its return time matches dawn.", "owl ends night activity", "pale eastern sky"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("fading shadow", "A wall shadow disappears when the lamp is switched off.", "Explain why the shadow vanishes.", "The shadow vanishes because the lamp no longer provides light to block.", "No light means no projected dark shape.", "shadow vanishes without light", "lamp switched off"), _fresh_case("bright east", "Stars become hard to see while the eastern sky grows bright.", "Write a reason for the change.", "The stars look fainter because morning light brightens the sky.", "The stars remain, but stronger light hides them.", "stars fainter at dawn", "morning light hides"), kind="open"),
]


_SEMANTIC_OPTION_REPLACEMENTS = {}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch10:assessment:17': {'accepted_answers': ['Dawn is beginning.'],
                               'options': ['Midnight is beginning.',
                                           'Dawn is beginning.',
                                           'Noon is beginning.'],
                               'passage': 'The street lamps switch off as the eastern '
                                          'sky grows light, even though the sun is not '
                                          'fully up.',
                               'prompt': 'Which time of day is beginning?'}}


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
