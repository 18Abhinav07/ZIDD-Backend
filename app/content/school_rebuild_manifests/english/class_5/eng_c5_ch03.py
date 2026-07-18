"""Deep authored manifest for Class 5 English Chapter 3.

The NCERT chapter was used only to map sections, modalities, and exercise
progression. Every learner-facing stimulus, prompt, option, rubric, and hidden
reference answer below is original Zidd content.
"""

from __future__ import annotations

from typing import Any

from app.content.school_rebuild_manifests.english.class_5.eng_c5_ch02 import (
    _choice,
    _evidence,
    _level,
    _open_direction,
    _task,
    _terms,
)


CHAPTER_ID = "eng_c5_ch03"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/eesa103.pdf"

POETIC_SKILLS = ["reading.poetic_language", "reading.paragraph_main_idea"]
REFERENCE_SKILLS = ["grammar.pronouns", "reading.word_meaning_context"]
SOUND_SKILLS = ["reading.poetic_language", "vocab.antonyms"]
WORDCRAFT_SKILLS = ["vocab.word_formation", "grammar.noun_verb_adjective"]
COLOUR_SKILLS = ["reading.event_sequence", "writing.short_answer"]
JOURNEY_SKILLS = ["grammar.tense_usage", "writing.paragraph"]
JOURNEY_PREFLIGHT = "journey_paragraph_80_100"
COMPARE_SKILLS = ["writing.compare_contrast", "research.information_selection"]


LEVEL_SPECS: list[dict[str, Any]] = [
    {
        "level_id": "rainbow_image_and_idea",
        "title": "Read the sky picture",
        "focus": "interpret a poetic comparison and identify its central idea",
        "outcome": "Explain how shape, position, and colour create a bridge-like sky image, then state the poem's central idea in own words.",
        "skill_ids": POETIC_SKILLS,
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:recite:1",
            f"{CHAPTER_ID}:think:2-3",
        ],
        "principle": "Treat a poetic comparison as a picture made from clues: name the two things, identify the shared feature, and connect it to the whole idea.",
        "connect": {
            "teaching_block": "Poems can make one thing help us imagine another. The comparison is not a science claim; it directs attention to shape, position, colour, or mood.",
            "passage": "After a shower, sunlight crossed the mist above a garden. A curved band of colour appeared to rest between two distant trees.",
            "prompt": "Picture the curve and its two apparent ends before examining what the image suggests.",
        },
        "co_construct": _choice(
            "A silver arc of cloud stretched above the valley like a doorway in the sky.",
            "Which shared feature makes doorway an effective comparison?",
            "Both shapes seem to arch over an opening.",
            ["Both objects are made of wood.", "Both objects stand on a classroom floor.", "Both objects can be locked with a key."],
            skills=["reading.poetic_language"],
        ),
        "guided": [
            _choice(
                "At sunset, a thin orange curve rested above the dark hills like a glowing handle.",
                "Which detail supports the handle comparison?",
                "the thin curved shape above the hills",
                ["the darkness inside the hills", "the sound of evening traffic", "the weight of a metal handle"],
                skills=["reading.poetic_language"],
            ),
            _task(
                "Rain ended, the clouds opened, and bands of colour brightened the quiet field. Children paused to watch the brief sky display.",
                "State the central idea in one sentence and include the change from rain to wonder.",
                "The passage shows a rainy field becoming a moment of shared wonder when colour appears in the clearing sky.",
                [
                    _evidence("change", "Connects the clearing rain to the appearance of colour.", "rainy field becoming", "rain ended and colour appeared"),
                    _evidence("idea", "States shared wonder as the central idea.", "shared wonder", "children paused to watch"),
                ],
                interaction_type="summary",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
        "independent": [
            _task(
                "A many-coloured curve rose above the river. From the bank, it looked as though it joined the reeds on one side to the old fort on the other.",
                "Explain why a poet might call the curve a bridge, using two clues from the passage.",
                "The curve resembles a bridge because it arches over the river and appears to connect the reeds with the distant fort.",
                [
                    _evidence("shape", "Uses the arching shape as one clue.", "arches over the river", "curved above the river"),
                    _evidence("connection", "Uses the apparent connection between two places.", "connect the reeds", "joined the reeds and fort"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "A storm left puddles across the playground. When the sun returned, a bright arc appeared, and even the impatient players became still for a minute.",
                "Write the main idea without listing every detail.",
                "A bright arc after the storm briefly united the players in quiet attention.",
                [_evidence("main", "Captures the post-storm sight and the players' shared response.", "after the storm", "players in quiet attention")],
                interaction_type="summary",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
        "transfer": [
            _task(
                "Festival lights curved from one rooftop to another, forming a shining necklace above the lane.",
                "Interpret the necklace image: what two things are compared, and which feature connects them?",
                "The curved festival lights are compared with a necklace because both form a bright linked line that hangs in a curve.",
                [
                    _evidence("pair", "Names lights and necklace as the compared things.", "lights are compared with a necklace", "festival lights and necklace"),
                    _evidence("feature", "Explains the shared bright curved line.", "bright linked line", "hangs in a curve"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "Mist covered the lake until a shaft of morning light opened a clear path across the water. Walkers stopped and pointed toward it.",
                "State the central idea and exclude background details that do not develop it.",
                "Morning light transformed the misty lake and drew the walkers' attention to a sudden clear path.",
                [_evidence("idea", "Combines transformation and attention into one central idea.", "light transformed", "walkers' attention")],
                interaction_type="summary",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
        "review": [
            _task(
                "A pale curve above the sea looked like a ribbon pinned to two clouds.",
                "Explain the ribbon comparison without treating the image as literal fact.",
                "The curve is compared with a ribbon because it is narrow, colourful, and seems to stretch between two points; it is not actually pinned to clouds.",
                [
                    _evidence("feature", "Explains at least two shared visual features.", "narrow", "colourful", "stretch between"),
                    _evidence("nonliteral", "States that the pinning is an image rather than fact.", "not actually pinned", "poetic image"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "Dark clouds moved away, sunlight reached the wet roofs, and neighbours stepped outside to admire the coloured sky.",
                "Summarise the main movement from weather change to human response.",
                "As the storm cleared, sunlight created a colourful sight that brought neighbours outside to admire it.",
                [_evidence("summary", "Links clearing weather, colourful sight, and neighbour response.", "storm cleared", "colourful sight", "neighbours outside")],
                interaction_type="summary",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
        "cluster_id": "rainbow-literal-or-detail-only-reading",
        "misconception": "The learner treats the comparison as a physical claim or repeats one colour detail without explaining the shared feature or central idea.",
        "remediation": "Use a two-column image map for the compared things, circle their shared visual feature, then compress the supporting details into one central-idea sentence.",
        "support": [
            _task(
                "A curved beam of light appeared above two buildings like a coloured gate.",
                "Name the compared things and one shared feature.",
                "The light beam is compared with a gate because both have a curved shape over an opening.",
                [_evidence("comparison", "Names both things and the shared curve.", "light beam", "gate", "curved shape")],
                skills=["reading.poetic_language"],
            ),
            _task(
                "A wet morning changed when a bright arc appeared over the school and pupils gathered near the windows.",
                "Build the idea in two steps: first the sky change, then its effect on the pupils.",
                "A bright arc changed the wet morning, and its appearance drew pupils together at the windows.",
                [
                    _evidence("change", "States the bright-arc change.", "bright arc changed", "arc appeared"),
                    _evidence("effect", "Connects the sight to pupils gathering.", "drew pupils together", "pupils gathered"),
                ],
                skills=["reading.paragraph_main_idea"],
            ),
            _task(
                "The moon lay on the pond like a coin, although no coin was in the water.",
                "Explain the image and its nonliteral boundary.",
                "The reflected moon resembles a round bright coin, but the comparison does not mean a real coin lies in the pond.",
                [
                    _evidence("feature", "Uses roundness or brightness as the shared feature.", "round bright coin", "resembles a coin"),
                    _evidence("boundary", "Rejects the literal interpretation.", "not mean a real coin", "comparison is not literal"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "Wind pushed the clouds apart. Colour brightened the sky, and a noisy queue became silent as everyone looked up.",
                "Remove minor details and state the central idea.",
                "A sudden display of colour after the clouds parted captured everyone's attention.",
                [_evidence("idea", "Keeps the weather change and shared attention.", "clouds parted", "colour", "everyone's attention")],
                skills=["reading.paragraph_main_idea"],
            ),
            _task(
                "A rainbow-like arc seemed to touch two fields beyond the road.",
                "Write one sentence explaining what seems true and what is only visual appearance.",
                "The arc appears to touch the two fields from the viewer's position, but it does not form a solid crossing between them.",
                [
                    _evidence("appearance", "States the apparent connection from the viewer's position.", "appears to touch", "viewer"),
                    _evidence("reality", "States that no solid crossing exists.", "does not form a solid crossing", "not a real bridge"),
                ],
                skills=["reading.poetic_language", "reading.paragraph_main_idea"],
            ),
        ],
    },
    {
        "level_id": "rainbow_natural_and_built",
        "title": "Compare nature and design",
        "focus": "compare natural and human-made crossings using bounded evidence",
        "outcome": "Report supplied facts accurately, then write a balanced comparison with one supported similarity, one difference, and no invented claims.",
        "skill_ids": COMPARE_SKILLS,
        "episode_kind": "application_mission",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:think:2-3",
        ],
        "principle": "Separate observation from sourced fact, compare the same feature on both sides, and state only what the bounded information packet can support.",
        "connect": {
            "teaching_block": "A natural arc may look bridge-like, but appearance and function are different questions. Research packets help us compare shape, purpose, material, and duration honestly.",
            "passage": "Sky arc packet: formed by light and water droplets; visible briefly; cannot carry travellers. Footbridge packet: built from wood and rope; spans a stream; carries walkers.",
            "prompt": "Notice the shared arching appearance and the different material, purpose, and duration.",
        },
        "co_construct": _choice(
            "Packet A: a natural light arc appears after rain. Packet B: a stone bridge carries people across a canal.",
            "Which claim is fully supported?",
            "Both can appear arched, but only the stone bridge carries people.",
            ["Both are built from stone.", "Both remain in place throughout the year.", "The natural arc carries people across rain."],
            skills=["research.information_selection"],
        ),
        "guided": [
            _choice(
                "Boat packet: coracle, round woven frame, used on calm rivers, guided with a paddle. No speed record is supplied.",
                "Which profile sentence stays within the packet?",
                "A coracle is a round woven boat guided with a paddle on calm rivers.",
                ["A coracle is the world's fastest racing boat.", "Every coracle is made of steel.", "Coracles can only travel on the sea."],
                skills=["research.information_selection"],
            ),
            _task(
                "Natural arch: made visible by light through mist; temporary; viewed from the ground. Garden arch: built from metal; permanent until removed; supports climbing plants.",
                "Write one similarity and one difference using the same comparison feature.",
                "Both form a curved shape above the viewer, but the light arch is temporary while the metal garden arch is built to remain.",
                [
                    _evidence("similarity", "States the shared curved shape.", "Both form a curved shape", "both arch above"),
                    _evidence("difference", "Contrasts temporary and built-to-remain duration.", "temporary", "built to remain"),
                ],
                skills=["writing.compare_contrast"],
            ),
        ],
        "independent": [
            _task(
                "Source card: bamboo footbridge; built by village craftspeople; crosses a narrow stream; inspected after monsoon. A second card shows a rainbow after rain but gives no construction facts.",
                "Write two sourced sentences that name the footbridge builders, crossing, inspection time, and the limit on what the cards say about the rainbow.",
                "The source card says village craftspeople built the bamboo footbridge across a narrow stream and inspect it after monsoon. The cards do not identify anyone as building the rainbow.",
                [
                    _evidence("builder", "Names the supplied builders and bamboo footbridge.", "village craftspeople built the bamboo footbridge"),
                    _evidence("crossing", "States what the footbridge crosses.", "across a narrow stream"),
                    _evidence("inspection", "States when the footbridge is inspected.", "inspect it after monsoon"),
                    _evidence("limit", "States the missing rainbow-construction evidence.", "do not identify anyone as building the rainbow"),
                ],
                skills=["research.information_selection"],
            ),
            _task(
                "Rainbow: an optical sight that may appear curved and fades as conditions change. Suspension bridge: a physical structure with cables that supports traffic across a gap.",
                "Compare appearance and function in a three-sentence response.",
                "Both may form a curve across a wide view. The rainbow is an optical sight that fades, whereas the suspension bridge is a physical structure. Only the bridge supports traffic across a gap.",
                [
                    _evidence("appearance", "States a supported visual similarity.", "Both may form a curve", "curve across"),
                    _evidence("function", "Contrasts optical sight with traffic-supporting structure.", "optical sight", "supports traffic"),
                ],
                skills=["writing.compare_contrast"],
            ),
        ],
        "transfer": [
            _task(
                "Research notes: shikara; long narrow wooden boat; used on lakes; propelled with a paddle; often carries people and goods. Source: regional transport card.",
                "Write a brief attributed profile that reports its form, setting, and movement, then protect the missing superlative claim.",
                "According to the regional transport card, a shikara is a long narrow wooden boat used on lakes. It is moved with a paddle and can carry people and goods. The card gives no basis for calling it the fastest or best boat.",
                [
                    _evidence("source", "Attributes the profile to the supplied card.", "According to the regional transport card"),
                    _evidence("form", "Reports the boat's supplied form.", "long narrow wooden boat"),
                    _evidence("setting", "Reports where the boat is used.", "used on lakes"),
                    _evidence("movement", "Reports how the boat moves.", "moved with a paddle"),
                    _evidence("restraint", "Protects the missing superlative claim.", "no basis for calling it the fastest or best boat"),
                ],
                skills=["research.information_selection"],
            ),
            _task(
                "Cloud shadow: natural, moves with clouds, cools an area briefly. Cloth canopy: human-made, fixed to posts, provides planned shade until removed.",
                "Compare origin, movement, and purpose without claiming one is better.",
                "Both can shade an area, but the cloud shadow forms naturally and moves, while the cloth canopy is built and fixed in place for planned shade.",
                [
                    _evidence("similarity", "States the shared shade effect.", "Both can shade", "shade an area"),
                    _evidence("differences", "Contrasts natural moving and built fixed origins.", "forms naturally and moves", "built and fixed"),
                ],
                skills=["writing.compare_contrast"],
            ),
        ],
        "review": [
            _task(
                "Packet: reed boat; bundled reeds; river use; local fishing; source is a museum label. It does not state who invented the design.",
                "Write a two-sentence profile and explicitly protect the missing fact.",
                "The museum label describes a river boat made from bundled reeds and used for local fishing. It does not identify an inventor of the design.",
                [
                    _evidence("profile", "Reports material, setting, and use.", "bundled reeds", "river", "local fishing"),
                    _evidence("boundary", "States the inventor is unknown from the packet.", "does not identify an inventor", "inventor is not supplied"),
                ],
                skills=["research.information_selection"],
            ),
            _task(
                "Natural waterfall: water drops over rock and changes with river flow. Fountain: pumped water follows a designed path and can be switched off.",
                "Write one similarity and two matched differences.",
                "Both display moving water. The waterfall follows natural rock and river flow, whereas the fountain follows a designed pumped path. River conditions change the waterfall, but people can switch the fountain off.",
                [
                    _evidence("similarity", "States moving water as the shared feature.", "Both display moving water", "moving water"),
                    _evidence("origin", "Contrasts the natural and designed water paths.", "waterfall follows natural rock and river flow, whereas the fountain follows a designed pumped path"),
                    _evidence("control", "Contrasts changing river conditions with human control.", "River conditions change the waterfall, but people can switch the fountain off"),
                ],
                skills=["writing.compare_contrast"],
            ),
        ],
        "cluster_id": "rainbow-comparison-with-invented-facts",
        "misconception": "The learner compares different features on each side, treats visual resemblance as identical function, or adds famous, fastest, safest, or inventor claims absent from the source packet.",
        "remediation": "Build a matched-feature table for origin, material, duration, and function; mark each statement as observed, supplied, or unknown before writing the comparison.",
        "support": [
            _task(
                "Arc A is light after rain and lasts minutes. Arc B is painted steel and remains over a gate.",
                "Compare the same shape and duration features.",
                "Both have an arched shape, but Arc A is temporary light while Arc B is a lasting steel structure.",
                [
                    _evidence("shape", "States the shared arched shape.", "Both have an arched shape", "both are curved"),
                    _evidence("duration", "Contrasts temporary light and lasting steel.", "temporary light", "lasting steel"),
                ],
                skills=["writing.compare_contrast"],
            ),
            _task(
                "Fact labels: rope bridge; handwoven ropes; spans ravine; walkers cross one at a time. No age or builder is listed.",
                "Select supported facts and name one unknown.",
                "The labels describe a handwoven rope bridge across a ravine that walkers cross one at a time. Its age and builder are unknown from the labels.",
                [
                    _evidence("facts", "Reports material, place, and use.", "handwoven rope bridge", "ravine", "one at a time"),
                    _evidence("unknown", "Protects age or builder as unknown.", "age and builder are unknown", "not listed"),
                ],
                skills=["research.information_selection"],
            ),
            _task(
                "A learner writes: 'Both rainbows and bridges carry cars because both curve over land.' The packet says only built road bridges carry traffic.",
                "Repair the comparison using appearance and function separately.",
                "Rainbows and some bridges can both look curved, but only the built road bridge in the packet carries traffic.",
                [
                    _evidence("appearance", "Keeps only the supported curved similarity.", "both look curved", "appearance"),
                    _evidence("function", "Limits traffic function to the built bridge.", "only the built road bridge", "carries traffic"),
                ],
                skills=["writing.compare_contrast"],
            ),
            _task(
                "Boat card: dugout canoe, carved from one log, moved with paddles, used on sheltered water. Photograph shows two passengers but gives no capacity limit.",
                "Write a factual description without turning the photograph into a universal capacity claim.",
                "The card describes a dugout canoe carved from one log and moved with paddles on sheltered water. The photograph shows two passengers, but it does not establish the canoe's maximum capacity.",
                [
                    _evidence("facts", "Reports construction, movement, and setting.", "carved from one log", "moved with paddles", "sheltered water"),
                    _evidence("limit", "Separates visible passengers from capacity evidence.", "does not establish", "maximum capacity"),
                ],
                skills=["research.information_selection"],
            ),
            _task(
                "Natural stepping stones: rocks in a shallow stream, positions change after floods. Built walkway: fixed boards on supports, inspected and repaired by people.",
                "Write a sourced comparison of crossing purpose, stability, and maintenance.",
                "Both may help people cross shallow water. Floods can move the natural stones, while the supported boards are designed to stay fixed. People inspect and repair the walkway, but no maintenance fact is supplied for the natural rocks.",
                [
                    _evidence("purpose", "States the shared crossing purpose.", "Both may help people cross", "shallow water"),
                    _evidence("contrast", "Contrasts stability and supplied maintenance facts.", "Floods can move", "designed to stay fixed", "inspect and repair"),
                ],
                skills=COMPARE_SKILLS,
            ),
        ],
    },
]


def _assessment_choice(
    item_no: int,
    skill_id: str,
    passage: str,
    prompt: str,
    correct: str,
    distractors: list[str],
) -> dict[str, Any]:
    item_id = f"{CHAPTER_ID}:assessment:{item_no:02d}"
    raw = [correct, *distractors]
    shift = item_no % len(raw)
    options = raw[shift:] + raw[:shift]
    return {
        "kind": "selected_option",
        "activity_id": item_id,
        "teaching_block": "Apply the named chapter strategy to the fresh stimulus and verify the exact clue before selecting an answer.",
        "passage": passage,
        "prompt": prompt,
        "skill_ids": [skill_id],
        "options": options,
        "accepted_answers": [correct],
    }


def _assessment_open(
    item_no: int,
    skill_id: str,
    passage: str,
    prompt: str,
    model_answer: str,
    evidence: list[tuple[str, str, list[str]]],
    *,
    interaction_type: str = "evidence_text",
    min_words: int = 8,
    preflight_rule: str = "relevant_english_response",
) -> dict[str, Any]:
    activity_id = f"{CHAPTER_ID}:assessment:{item_no:02d}"
    criteria = []
    slots = []
    for suffix, description, phrases in evidence:
        criterion_id = f"{activity_id}:{suffix}"
        criteria.append(
            {
                "id": criterion_id,
                "description": description,
                "required": True,
                "min_quality": 0.65,
            }
        )
        slots.append(
            {
                "id": criterion_id,
                "description": description,
                "any_of": phrases,
            }
        )
    direction = _open_direction(
        phase="assessment",
        skill_ids=[skill_id],
        criterion_count=len(criteria),
    )
    return {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": (
            "Answer independently from the supplied evidence and use original "
            f"English wording. {direction}"
        ),
        "passage": passage,
        "prompt": prompt,
        "skill_ids": [skill_id],
        "interaction_type": interaction_type,
        "rubric_criteria": criteria,
        "concept_slots": slots,
        "forbidden_phrases": [
            "The supplied details do not matter",
            "I copied the sample answer",
        ],
        "min_response_words": min_words,
        "relevance_terms": _terms(model_answer),
        "model_answer": model_answer,
        "pass_score": 0.8,
        "preflight_rule": preflight_rule,
    }


ASSESSMENT_ITEMS = [
    _assessment_choice(1, "reading.poetic_language", "After rain, streetlights reflected across the road like a necklace of gold beads.", "Which shared feature supports the necklace image?", "separate bright points forming a line", ["the metal weight of a necklace", "beads hanging from the clouds", "the depth of the roadside drain"]),
    _assessment_open(
        2,
        "reading.poetic_language",
        "Sunlight formed an arch in the spray above a fountain, and visitors called it a doorway of light.",
        "Explain the doorway image using shape and nonliteral meaning.",
        "The spray and light form an arch like a doorway, but the image does not mean visitors can physically walk through it.",
        [
            _evidence("shape", "Explains the shared arch shape.", "form an arch like a doorway"),
            _evidence("boundary", "Protects the nonliteral boundary.", "does not mean visitors can physically walk through it"),
        ],
    ),
    _assessment_choice(3, "reading.poetic_language", "Glow over the snow, gleam in the stream.", "Which pair creates the clearest matching end sound?", "gleam and stream", ["glow and snowing", "over and in", "snow and stream"]),
    _assessment_open(
        4,
        "reading.poetic_language",
        "Still went the lane, still went the tree, still for a moment stood you and me.",
        "Explain what repeating still emphasises and name the rhyme pair.",
        "Repeating still emphasises the shared pause, while tree and me form the rhyme pair.",
        [
            _evidence("emphasis", "Explains what the repetition emphasises.", "emphasises the shared pause"),
            _evidence("rhyme", "Identifies the rhyme pair.", "tree and me form the rhyme pair"),
        ],
    ),
    _assessment_choice(5, "reading.paragraph_main_idea", "Clouds cleared after a storm. A coloured arc appeared, and people across the market stopped to look up together.", "Which sentence best states the main idea?", "A post-storm sky display briefly captured the whole market's attention.", ["The market sold many goods.", "Clouds always remain after storms.", "People looked only at the road."]),
    _assessment_open(
        6,
        "reading.paragraph_main_idea",
        "Morning mist hid the hills until sunlight opened a bright path across the valley. Hikers paused and photographed the change.",
        "State the central idea in one concise sentence that includes both the change and the hikers' response.",
        "Sunlight transformed the misty valley and drew the hikers' attention to the sudden change.",
        [
            _evidence("change", "States the change in the valley.", "Sunlight transformed the misty valley"),
            _evidence("response", "Includes the hikers' response.", "drew the hikers' attention"),
        ],
        interaction_type="summary",
    ),
    _assessment_choice(7, "grammar.pronouns", "The bands brightened above the field. They faded before sunset.", "What does They refer to?", "the bands", ["the field", "sunset", "the spectators"]),
    _assessment_open(
        8,
        "grammar.pronouns",
        "Anika showed the colour cards to Rehan. He arranged them before she labelled the chart.",
        "Identify the referent of He, them, and she.",
        "He refers to Rehan, them refers to the colour cards, and she refers to Anika.",
        [
            _evidence("he", "Links He to Rehan.", "He refers to Rehan"),
            _evidence("them", "Links them to the colour cards.", "them refers to the colour cards"),
            _evidence("she", "Links she to Anika.", "she refers to Anika"),
        ],
    ),
    _assessment_choice(9, "reading.word_meaning_context", "The colours were vivid, remaining bright even against the sunlit cloud.", "What does vivid mean here?", "bright and clear", ["brief and hidden", "silent and smooth", "heavy and solid"]),
    _assessment_open(
        10,
        "reading.word_meaning_context",
        "As shopkeepers lowered their shutters, the market noise dwindled from a loud rumble to a few distant voices.",
        "Explain dwindled using the before-and-after clue.",
        "Dwindled means gradually became less, shown by the market changing from a loud rumble to only a few distant voices.",
        [
            _evidence("meaning", "Defines dwindled in context.", "gradually became less"),
            _evidence("contrast", "Uses the complete before-and-after sound contrast.", "loud rumble to only a few distant voices"),
        ],
    ),
    _assessment_choice(11, "vocab.antonyms", "The first band was faint, but the second was ___.", "Which word gives the clearest opposite contrast?", "vivid", ["curved", "distant", "striped"]),
    _assessment_open(
        12,
        "vocab.antonyms",
        "The platform was crowded before the train and empty afterward.",
        "Name the opposite pair and explain the change.",
        "Crowded and empty are opposites showing that many people were present before the train but none remained afterward.",
        [
            _evidence("pair", "Names the opposite pair.", "Crowded and empty are opposites"),
            _evidence("change", "Explains the contextual change.", "many people were present before the train but none remained afterward"),
        ],
    ),
    _assessment_choice(13, "vocab.word_formation", "A thin strip placed in a book marks the page where a reader stopped.", "Which compound names this object?", "bookmark", ["bookcase", "notebook", "bookshelf"]),
    _assessment_open(
        14,
        "vocab.word_formation",
        "The bases tooth and brush name a tool used to clean teeth.",
        "Form, split, and define the compound.",
        "Toothbrush combines tooth and brush and means a brush used to clean teeth.",
        [
            _evidence("compound", "Forms the compound.", "Toothbrush"),
            _evidence("bases", "Splits the compound into both bases.", "combines tooth and brush"),
            _evidence("definition", "Defines the compound from the bases.", "brush used to clean teeth"),
        ],
    ),
    _assessment_choice(15, "grammar.noun_verb_adjective", "The bright band crossed the quiet valley.", "Which word is an adjective describing band?", "bright", ["band", "crossed", "valley"]),
    _assessment_open(
        16,
        "grammar.noun_verb_adjective",
        "Sentence A: We colour the final stripe. Sentence B: The colour remained vivid.",
        "Classify colour in each sentence and explain its job.",
        "Colour is a verb naming the action in sentence A and a noun naming the visual quality in sentence B.",
        [
            _evidence("action_use", "Classifies and explains colour in sentence A.", "verb naming the action in sentence A"),
            _evidence("naming_use", "Classifies and explains colour in sentence B.", "noun naming the visual quality in sentence B"),
        ],
    ),
    _assessment_choice(17, "reading.event_sequence", "A verified colour strip ends with the five-position fragment blue, green, yellow, orange, red.", "Which colour comes immediately before orange?", "yellow", ["green", "red", "blue"]),
    _assessment_open(
        18,
        "reading.event_sequence",
        "A planting card lists these mixed steps: label the pot; fill it with soil; sow two seeds; water gently.",
        "Rewrite the four steps in a workable order and explain why the label comes last.",
        "First fill the pot with soil, then sow two seeds and water gently. Label the pot last so the planted pot can be identified afterward.",
        [
            _evidence("soil", "Places filling the pot first.", "fill the pot with soil"),
            _evidence("seeds", "Places sowing after the soil.", "then sow two seeds"),
            _evidence("water", "Places watering after sowing.", "water gently"),
            _evidence("label", "Places labelling last.", "Label the pot last"),
            _evidence("reason", "Explains the purpose of the final label.", "planted pot can be identified afterward"),
        ],
    ),
    _assessment_open(
        19,
        "writing.short_answer",
        "A learner leaves a gap between blue and yellow in the seven-colour order.",
        "Write a complete one-sentence correction with both neighbour clues.",
        "Green fills the gap because it comes after blue and before yellow.",
        [
            _evidence("correction", "Names the missing colour.", "Green fills the gap"),
            _evidence("after", "Uses the blue neighbour clue.", "after blue"),
            _evidence("before", "Uses the yellow neighbour clue.", "before yellow"),
        ],
        interaction_type="short_text",
    ),
    _assessment_open(
        20,
        "writing.short_answer",
        "A card row begins indigo, violet, blue and then continues correctly.",
        "Explain the one swap needed to repair the beginning.",
        "Swap indigo and violet so the sequence begins violet, indigo, blue.",
        [
            _evidence("swap", "States the exact swap.", "Swap indigo and violet"),
            _evidence("corrected_order", "Gives the corrected beginning.", "sequence begins violet, indigo, blue"),
        ],
        interaction_type="short_text",
    ),
    _assessment_choice(21, "grammar.tense_usage", "Yesterday, the volunteers ___ three saplings before lunch.", "Which verb matches the completed action?", "planted", ["plant", "plants", "planting"]),
    _assessment_open(
        22,
        "grammar.tense_usage",
        "Draft: Yesterday I board the ferry, see two islands, and reached the far bank.",
        "Rewrite every completed action in consistent past tense.",
        "Yesterday I boarded the ferry, saw two islands, and reached the far bank.",
        [
            _evidence("boarded", "Changes board to past tense.", "boarded the ferry"),
            _evidence("saw", "Changes see to past tense.", "saw two islands"),
            _evidence("reached", "Keeps reached in past tense.", "reached the far bank"),
        ],
    ),
    _assessment_open(
        23,
        "writing.paragraph",
        "Journey packet: dawn bus; winding hill road; misty orchards; cold window; roadside waterfall; arrival at camp before breakfast; reflection on the changing landscape.",
        "Write an 80- to 100-word first-person journey paragraph with a focused opening, ordered movement, sensory detail, consistent past tense, arrival, and closing reflection.",
        "We left by bus at dawn and climbed a winding hill road while the town lights faded behind us. Mist covered the orchards beside the road, and cold air entered through the open window. After one sharp turn, a narrow waterfall flashed between the trees and made everyone lean toward the glass. We reached the camp before breakfast and carried our bags into the quiet courtyard. Watching the landscape change from streets to misty hills made the early journey feel surprising and worthwhile.",
        [
            _evidence("opening", "Opens with the dawn departure.", "left by bus at dawn"),
            _evidence("movement", "Orders the movement along the hill road.", "climbed a winding hill road"),
            _evidence("sensory", "Includes a specific sensory detail.", "cold air entered through the open window"),
            _evidence("tense", "Keeps completed journey actions in past tense.", "waterfall flashed between the trees"),
            _evidence("arrival", "Reaches the stated destination.", "reached the camp before breakfast"),
            _evidence("reflection", "Closes with the supplied reflection.", "made the early journey feel surprising and worthwhile"),
        ],
        interaction_type="paragraph_text",
        min_words=80,
        preflight_rule=JOURNEY_PREFLIGHT,
    ),
    _assessment_open(
        24,
        "writing.paragraph",
        "Journey packet: train toward city museum; platform changed suddenly; announcement echoed; station helper showed new route; boarded before doors closed; reached museum on time; lesson about checking display boards.",
        "Write an 80- to 100-word first-person journey paragraph that orders the problem and resolution, uses sensory detail and consistent past tense, reaches the destination, and closes with the lesson.",
        "I travelled by train toward the city museum when a sudden platform change interrupted my journey. The announcement echoed through the crowded station, and I first walked toward the wrong stairs. A station helper noticed my ticket and showed me the shorter route to the new platform. I hurried across the bridge and boarded just before the doors closed. The train reached the museum stop on time. The experience taught me to check display boards carefully whenever an announcement changes a journey plan.",
        [
            _evidence("problem", "States the platform-change problem.", "sudden platform change interrupted my journey"),
            _evidence("resolution", "Explains how the helper resolved it.", "showed me the shorter route"),
            _evidence("sensory", "Includes a specific sensory detail.", "announcement echoed through the crowded station"),
            _evidence("tense", "Keeps completed journey actions in past tense.", "I travelled by train"),
            _evidence("arrival", "Reaches the museum stop.", "reached the museum stop on time"),
            _evidence("lesson", "Closes with the supplied lesson.", "check display boards carefully"),
        ],
        interaction_type="paragraph_text",
        min_words=80,
        preflight_rule=JOURNEY_PREFLIGHT,
    ),
    _assessment_open(
        25,
        "writing.compare_contrast",
        "Natural arc: light through mist, temporary, cannot carry travellers. Garden arch: metal structure, lasting, supports plants.",
        "Write one matched similarity and two differences.",
        "Both appear curved above a space. The natural arc is temporary light, while the garden arch is lasting metal. Only the garden arch physically supports plants.",
        [
            _evidence("similarity", "States the shared curved appearance.", "Both appear curved above a space"),
            _evidence("duration", "Contrasts temporary and lasting form.", "natural arc is temporary light, while the garden arch is lasting metal"),
            _evidence("function", "Contrasts physical support.", "Only the garden arch physically supports plants"),
        ],
    ),
    _assessment_open(
        26,
        "writing.compare_contrast",
        "Cloud shadow: natural and moving. Cloth canopy: human-made and fixed. Both cool a small area.",
        "Compare origin, movement, and shared effect without ranking them.",
        "Both cool a small area. The cloud shadow forms naturally, whereas the cloth canopy is human-made. The shadow moves, while the canopy remains fixed.",
        [
            _evidence("shared_effect", "States the shared cooling effect.", "Both cool a small area"),
            _evidence("origin", "Contrasts natural and human-made origin.", "cloud shadow forms naturally, whereas the cloth canopy is human-made"),
            _evidence("movement", "Contrasts moving and fixed positions.", "shadow moves, while the canopy remains fixed"),
        ],
    ),
    _assessment_choice(27, "research.information_selection", "Boat packet: long narrow wooden shikara; lake use; moved with a paddle; carries people and goods. No speed record supplied.", "Which claim is fully supported?", "A shikara is a narrow wooden lake boat moved with a paddle.", ["A shikara is the world's fastest boat.", "Every shikara crosses the open sea.", "A shikara is always built from steel."]),
    _assessment_open(
        28,
        "research.information_selection",
        "Museum card: reed boat; bundled reeds; river use; local fishing. The card names no inventor.",
        "Write a sourced profile and protect the missing inventor fact.",
        "The museum card describes a river boat made from bundled reeds and used for local fishing. It does not identify an inventor.",
        [
            _evidence("source", "Attributes the profile to the card.", "museum card describes"),
            _evidence("facts", "Reports the supplied construction and use facts.", "river boat made from bundled reeds and used for local fishing"),
            _evidence("limit", "Protects the missing inventor fact.", "does not identify an inventor"),
        ],
    ),
    _assessment_open(
        29,
        "reading.poetic_language",
        "A line calls moonlight 'a silver road across the pond.'",
        "Interpret the road image and state why it is not literal.",
        "The reflected light forms a long bright path like a road, but it is not a solid surface anyone can walk on.",
        [
            _evidence("image", "Explains the shared path-like feature.", "reflected light forms a long bright path like a road"),
            _evidence("boundary", "States the nonliteral limit.", "not a solid surface anyone can walk on"),
        ],
    ),
    _assessment_choice(30, "vocab.word_formation", "Moon plus light names light seen from the moon at night.", "Which compound preserves both base meanings?", "moonlight", ["sunlight", "moonstone", "starlight"]),
    _assessment_choice(31, "grammar.tense_usage", "Last evening, the train ___ the bridge and ___ at the station.", "Which pair keeps both actions in past tense?", "crossed, stopped", ["cross, stop", "crosses, stopped", "crossing, stops"]),
    _assessment_choice(32, "research.information_selection", "Source label: clay water pot; shaped by a local potter; porous walls help cool the water; holds eight litres.", "Which statement stays within the source?", "The locally made clay pot holds eight litres and helps cool water through its porous walls.", ["The pot won an international design prize.", "The pot is the oldest vessel in the district.", "The pot keeps water frozen for several days."]),
]


STRANDS = [
    {
        "strand_id": "rainbow-poetic-meaning",
        "skill_ids": POETIC_SKILLS,
        "minimum_items": 7,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["rainbow_image_and_idea", "rainbow_sound_and_contrast"],
    },
    {
        "strand_id": "rainbow-reference-and-contrast",
        "skill_ids": ["grammar.pronouns", "reading.word_meaning_context", "vocab.antonyms"],
        "minimum_items": 6,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["rainbow_reference_and_context", "rainbow_sound_and_contrast"],
    },
    {
        "strand_id": "rainbow-wordcraft",
        "skill_ids": WORDCRAFT_SKILLS,
        "minimum_items": 5,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["rainbow_compounds_and_word_jobs"],
    },
    {
        "strand_id": "rainbow-colour-expression",
        "skill_ids": COLOUR_SKILLS,
        "minimum_items": 4,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["rainbow_colour_sequence"],
    },
    {
        "strand_id": "rainbow-journey-writing",
        "skill_ids": JOURNEY_SKILLS,
        "minimum_items": 5,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["rainbow_journey_paragraph"],
    },
    {
        "strand_id": "rainbow-comparison-research",
        "skill_ids": COMPARE_SKILLS,
        "minimum_items": 5,
        "evidence_forms": ["selected_option", "constructed_response"],
        "remediation_level_ids": ["rainbow_natural_and_built"],
    },
]


LEVEL_ORDER = (
    "rainbow_image_and_idea",
    "rainbow_reference_and_context",
    "rainbow_sound_and_contrast",
    "rainbow_compounds_and_word_jobs",
    "rainbow_colour_sequence",
    "rainbow_journey_paragraph",
    "rainbow_natural_and_built",
)
def _build_manifest() -> dict[str, Any]:
    level_by_id = {spec["level_id"]: spec for spec in LEVEL_SPECS}
    return {
        "schema_version": "school-class5-deep-manifest-v1",
        "chapter": {
            "chapter_id": CHAPTER_ID,
            "chapter_no": 3,
            "title": "The Rainbow",
            "book_title": "Santoor",
            "unit_title": "My Colourful World",
            "source_url": SOURCE_URL,
            "source_note": "NCERT structural alignment only. All teaching passages, prompts, examples, choices, rubrics, and answers are original Zidd content.",
            "content_version": "2026-07-15.5",
            "certification_version": "2026-07-15.5",
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": "/tmp/eesa103.txt structural exercise and modality matrix; no textbook body retained",
            },
        },
        "source_anchors": SOURCE_ANCHORS,
        "levels": [_level(level_by_id[level_id]) for level_id in LEVEL_ORDER],
        "chapter_assessment": {
            "items_per_attempt": 16,
            "pass_score": 0.8,
            "max_attempts": 2,
            "bank_item_count": 32,
            "items": ASSESSMENT_ITEMS,
            "strands": STRANDS,
        },
    }


SOURCE_ANCHORS = [
    {
        "anchor_id": f"{CHAPTER_ID}:recite:1",
        "section_label": "Let us Recite: Poem Image and Rhythm",
        "page_start": 1,
        "page_end": 1,
        "source_url": f"{SOURCE_URL}#page=1",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:new-words:2",
        "section_label": "New Words",
        "page_start": 2,
        "page_end": 2,
        "source_url": f"{SOURCE_URL}#page=2",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:think:2-3",
        "section_label": "Let us Think: Poetic Meaning, Reference, and Imagination",
        "page_start": 2,
        "page_end": 3,
        "source_url": f"{SOURCE_URL}#page=2",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:learn:3",
        "section_label": "Let us Learn: Word Order and Poem Vocabulary",
        "page_start": 3,
        "page_end": 3,
        "source_url": f"{SOURCE_URL}#page=3",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:listen:4",
        "section_label": "Let us Listen: Sound and Rhyme Companion",
        "page_start": 4,
        "page_end": 4,
        "source_url": f"{SOURCE_URL}#page=4",
        "coverage_treatment": "guided_only",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:speak:5-6",
        "section_label": "Let us Speak: Expressive Recitation and Discussion",
        "page_start": 5,
        "page_end": 6,
        "source_url": f"{SOURCE_URL}#page=5",
        "coverage_treatment": "offline_group_activity",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:write-poem:7-8",
        "section_label": "Let us Write: Poetic Title, Rhyme, Image, and Journey",
        "page_start": 7,
        "page_end": 8,
        "source_url": f"{SOURCE_URL}#page=7",
        "coverage_treatment": "zidd_equivalent",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:write-words:9-12",
        "section_label": "Let us Write: Compounds, Word Jobs, Opposites, and Colour Order",
        "page_start": 9,
        "page_end": 12,
        "source_url": f"{SOURCE_URL}#page=9",
        "coverage_treatment": "taught_and_assessed",
        "required_for_chapter_certification": True,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:do:13",
        "section_label": "Let us Do: Visual Colour Activities",
        "page_start": 13,
        "page_end": 13,
        "source_url": f"{SOURCE_URL}#page=13",
        "coverage_treatment": "optional_creative",
        "required_for_chapter_certification": False,
    },
    {
        "anchor_id": f"{CHAPTER_ID}:explore:14-15",
        "section_label": "Let us Explore: Boats and Natural versus Human-made Features",
        "page_start": 14,
        "page_end": 15,
        "source_url": f"{SOURCE_URL}#page=14",
        "coverage_treatment": "textbook_companion",
        "required_for_chapter_certification": False,
    },
]


LEVEL_SPECS += [
    {
        "level_id": "rainbow_sound_and_contrast",
        "title": "Hear pattern and contrast",
        "focus": "interpret rhyme, repetition, and opposite meanings",
        "outcome": "Explain how a sound or repetition pattern shapes a short poem and choose or use an opposite that preserves the sentence meaning.",
        "skill_ids": SOUND_SKILLS,
        "episode_kind": "language_lab",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:recite:1",
            f"{CHAPTER_ID}:write-poem:7-8",
        ],
        "principle": "Read end sounds aloud in your head rather than matching spelling alone, notice purposeful repetition, and test an opposite inside the full sentence.",
        "connect": {
            "teaching_block": "Poetic music can come from rhyme, repeated words, and repeated sentence shapes. Contrast words sharpen the picture by showing what changed.",
            "passage": "Light crossed the night; rain left the lane. The paired sounds make the two short lines easier to remember.",
            "prompt": "Notice the matching sound pairs and the change between darkness and brightness.",
        },
        "co_construct": _choice(
            "The glow moved slow above the silent town.",
            "Which two words create the clearest end-sound pattern?",
            "glow and slow",
            ["moved and town", "silent and above", "the and town"],
            skills=["reading.poetic_language"],
        ),
        "guided": [
            _choice(
                "The band was faint at first but became vivid after the cloud moved.",
                "Which word is the best opposite of faint in this sentence?",
                "vivid",
                ["cloudy", "curved", "distant"],
                skills=["vocab.antonyms"],
            ),
            _task(
                "Bright over the field, bright over the stream, bright for a moment in everyone's dream.",
                "Explain what the repeated word bright emphasises and identify the end-sound pair.",
                "Repeating bright emphasises the spreading light, while stream and dream create the end-sound pair.",
                [
                    _evidence("repetition", "Explains the emphasis created by bright.", "emphasises the spreading light", "repeating bright"),
                    _evidence("rhyme", "Identifies stream and dream as the sound pair.", "stream and dream", "end-sound pair"),
                ],
                skills=["reading.poetic_language"],
            ),
        ],
        "independent": [
            _task(
                "Across the bay, the colours stay; above the foam, they lead us home.",
                "Identify both rhyme pairs and explain how the repeated sentence shape creates rhythm.",
                "Bay rhymes with stay, and foam rhymes with home. The repeated place-then-action pattern gives both lines a balanced rhythm.",
                [
                    _evidence("rhymes", "Identifies both sound pairs.", "bay rhymes with stay", "foam rhymes with home"),
                    _evidence("rhythm", "Explains the balanced repeated structure.", "repeated place-then-action", "balanced rhythm"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "Before sunrise the lane was dim; after sunrise the wet stones looked bright.",
                "Name the opposite pair and explain the change it marks.",
                "Dim and bright are opposites that mark the lane's change from low morning light to a sunlit surface.",
                [
                    _evidence("pair", "Names dim and bright as opposites.", "Dim and bright", "dim versus bright"),
                    _evidence("change", "Explains the light transition.", "low morning light", "sunlit surface"),
                ],
                skills=["vocab.antonyms"],
            ),
        ],
        "transfer": [
            _task(
                "Tap of the rain, tap on the pane; hush of the breeze, hush in the trees.",
                "Explain how repetition and rhyme work together in these lines.",
                "Repeating tap and hush imitates two soft sounds, while rain and pane and breeze and trees link the lines through rhyme.",
                [
                    _evidence("repetition", "Connects repeated words with imitated sounds.", "Repeating tap and hush", "imitates two soft sounds"),
                    _evidence("rhyme", "Identifies both rhyme pairs.", "rain and pane", "breeze and trees"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "The crowded platform became empty after the final train departed.",
                "Use the opposite pair to explain the before-and-after change.",
                "Crowded and empty are opposites: many people filled the platform before the train, but none remained afterward.",
                [
                    _evidence("pair", "Names crowded and empty.", "Crowded and empty", "opposites"),
                    _evidence("contrast", "Explains the change in number of people.", "many people", "none remained"),
                ],
                skills=["vocab.antonyms"],
            ),
        ],
        "review": [
            _task(
                "Colour in the air, colour everywhere; light beside the stream, light inside the dream.",
                "Identify the repeated words and rhyme pairs, then state their combined effect.",
                "Colour and light are repeated for emphasis; air rhymes with everywhere and stream with dream, creating a musical celebration of the scene.",
                [
                    _evidence("patterns", "Identifies repetition and both rhyme pairs.", "Colour and light", "air rhymes with everywhere", "stream with dream"),
                    _evidence("effect", "Explains the musical celebratory effect.", "musical celebration", "celebrates the scene"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "The first sketch was rough, but the revised colour band looked smooth and even.",
                "Identify the opposite pair and use it in a sentence about the revision.",
                "Rough and smooth are opposites. Revision changed the rough first band into a smooth, even one.",
                [
                    _evidence("pair", "Names rough and smooth.", "Rough and smooth", "opposites"),
                    _evidence("use", "Uses both words to explain revision.", "rough first band", "smooth"),
                ],
                skills=["vocab.antonyms"],
            ),
        ],
        "cluster_id": "rainbow-spelling-rhyme-or-random-opposite",
        "misconception": "The learner matches rhyme by similar spelling instead of sound, names repetition without its effect, or chooses an antonym that breaks the sentence context.",
        "remediation": "Separate final sounds from spellings, mark repeated words and their emphasis, then substitute each candidate opposite into the complete sentence before choosing.",
        "support": [
            _task(
                "High in the sky, light drifting by.",
                "Name the rhyme pair and describe the shared final sound.",
                "Sky and by rhyme because both end with the long eye sound.",
                [_evidence("rhyme", "Names sky and by with their shared sound.", "Sky and by", "long eye sound")],
                skills=["reading.poetic_language"],
            ),
            _task(
                "Clear, clear, clear grew the opening above the trees.",
                "Explain why clear is repeated rather than written once.",
                "Repeating clear emphasises the opening becoming more noticeable and gives the line a steady beat.",
                [
                    _evidence("emphasis", "Explains increasing noticeability.", "more noticeable", "emphasises the opening"),
                    _evidence("sound", "Mentions the steady beat.", "steady beat", "rhythm"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "The path was broad near the gate but narrow beside the pond.",
                "Identify and explain the opposite pair.",
                "Broad and narrow are opposites describing how the path's width changes between the gate and pond.",
                [_evidence("contrast", "Names the pair and width change.", "Broad and narrow", "width changes")],
                skills=["vocab.antonyms"],
            ),
            _task(
                "The colours appeared briefly but the memory remained permanent.",
                "Use the contrast to explain permanent.",
                "Permanent means lasting rather than brief; the colours vanished, but the memory continued.",
                [
                    _evidence("meaning", "Defines permanent through the opposite brief.", "lasting rather than brief", "continued"),
                    _evidence("contrast", "Connects vanished colours with lasting memory.", "colours vanished", "memory continued"),
                ],
                skills=["vocab.antonyms"],
            ),
            _task(
                "Near and clear, far and star: the line repeats two contrasts and two matching sounds.",
                "Separate the opposite relationship from the rhyme relationship.",
                "Near contrasts with far, while near rhymes with clear and far rhymes with star.",
                [
                    _evidence("opposites", "Names near and far as the contrast.", "Near contrasts with far", "near and far"),
                    _evidence("rhymes", "Names both sound pairs.", "near rhymes with clear", "far rhymes with star"),
                ],
                skills=SOUND_SKILLS,
            ),
        ],
    },
    {
        "level_id": "rainbow_compounds_and_word_jobs",
        "title": "Build words and test their jobs",
        "focus": "form meaningful compounds and distinguish noun, verb, and adjective uses",
        "outcome": "Explain how two base words create a compound meaning and classify a familiar word from the job it performs in a sentence.",
        "skill_ids": WORDCRAFT_SKILLS,
        "episode_kind": "language_lab",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:write-words:9-12",
        ],
        "principle": "A compound must preserve meaning from both base words, while a word's part of speech comes from its sentence job rather than its spelling.",
        "connect": {
            "teaching_block": "English can join two useful words into one new idea. The same familiar word can also name something in one sentence and express an action in another.",
            "passage": "Rain plus coat forms raincoat, a coat made for rain. In 'We colour the poster,' colour performs an action rather than naming a shade.",
            "prompt": "Check both the word parts and the sentence job before moving to the examples.",
        },
        "co_construct": _choice(
            "Sun plus light names the light that comes from the sun.",
            "Which compound is correctly formed?",
            "sunlight",
            ["lightsun", "sunlitely", "sunninglight"],
            skills=["vocab.word_formation"],
        ),
        "guided": [
            _choice(
                "The bright colours filled the poster.",
                "What job does bright perform?",
                "adjective describing colours",
                ["noun naming a person", "verb showing an action", "pronoun replacing poster"],
                skills=["grammar.noun_verb_adjective"],
            ),
            _task(
                "The bases rain and drop form a word for one small drop of rain.",
                "Form the compound, split it into its bases, and explain the meaning.",
                "Raindrop combines rain and drop and means a single drop of rain.",
                [
                    _evidence("form", "Forms raindrop and names both bases.", "Raindrop", "rain and drop"),
                    _evidence("meaning", "Explains the combined meaning.", "single drop of rain", "drop of rain"),
                ],
                skills=["vocab.word_formation"],
            ),
        ],
        "independent": [
            _task(
                "The bases bow and tie name a tie shaped like a bow.",
                "Form the compound and explain why both bases matter.",
                "Bowtie combines bow and tie: tie names the object, while bow describes its shape.",
                [
                    _evidence("form", "Forms bowtie from both bases.", "Bowtie", "bow and tie"),
                    _evidence("roles", "Explains what each base contributes.", "tie names the object", "bow describes its shape"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "Sentence A: We painted a blue arc. Sentence B: Please colour the final band blue.",
                "Classify blue in A and colour in B, explaining each sentence job.",
                "Blue is an adjective describing arc in sentence A, while colour is a verb telling the reader what action to perform in sentence B.",
                [
                    _evidence("adjective", "Classifies blue as describing arc.", "Blue is an adjective", "describing arc"),
                    _evidence("verb", "Classifies colour as the action.", "colour is a verb", "action to perform"),
                ],
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
        "transfer": [
            _task(
                "A notebook used to record weather combines the bases weather and book.",
                "Create the compound and write a definition that uses both base meanings.",
                "Weatherbook combines weather and book and means a book used to record or study weather.",
                [
                    _evidence("form", "Forms weatherbook from the supplied bases.", "Weatherbook", "weather and book"),
                    _evidence("definition", "Uses both ideas in the definition.", "book used to record", "weather"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "Sentence A: The bridge spans the canal. Sentence B: The narrow bridge needs repair.",
                "Classify bridge in each sentence and identify the verb in sentence A.",
                "Bridge is a noun in both sentences because it names a structure, while spans is the verb in sentence A.",
                [
                    _evidence("noun", "Classifies bridge as a noun in both uses.", "Bridge is a noun", "names a structure"),
                    _evidence("verb", "Identifies spans as the action.", "spans is the verb", "verb in sentence A"),
                ],
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
        "review": [
            _task(
                "The bases moon and light form a word for light that appears to come from the moon.",
                "Form, split, and define the compound.",
                "Moonlight combines moon and light and means light seen from the moon at night.",
                [
                    _evidence("form", "Forms moonlight and splits both bases.", "Moonlight", "moon and light"),
                    _evidence("meaning", "Defines the combined idea.", "light seen from the moon", "at night"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "The calm lake reflected a bright band. Later, the wind calmed the ripples.",
                "Classify calm in the first sentence and calmed in the second, using their jobs as evidence.",
                "Calm is an adjective describing lake, while calmed is a verb naming what the wind did to the ripples.",
                [
                    _evidence("adjective", "Explains calm as a description.", "Calm is an adjective", "describing lake"),
                    _evidence("verb", "Explains calmed as an action.", "calmed is a verb", "wind did"),
                ],
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
        "cluster_id": "rainbow-word-form-or-job-confusion",
        "misconception": "The learner reverses or alters compound bases without preserving meaning, or classifies a word from memory instead of checking its sentence function.",
        "remediation": "Write each compound as base plus base plus combined definition, then underline the word and ask whether it names, acts, or describes in that exact sentence.",
        "support": [
            _task(
                "Rain plus bow creates a word for a coloured arc often seen after rain.",
                "Form the word and explain each base contribution.",
                "Rainbow combines rain and bow: rain names the weather condition, and bow describes the curved shape.",
                [
                    _evidence("form", "Forms rainbow from both bases.", "Rainbow", "rain and bow"),
                    _evidence("meaning", "Explains weather and shape contributions.", "weather condition", "curved shape"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "The display shows three colour cards. We display them near the window.",
                "Explain the different jobs of display in the two sentences.",
                "Display is a noun naming an arrangement in the first sentence and a verb meaning show in the second.",
                [
                    _evidence("noun", "Identifies the naming use.", "Display is a noun", "naming an arrangement"),
                    _evidence("verb", "Identifies the action use.", "verb meaning show", "display them"),
                ],
                skills=["grammar.noun_verb_adjective"],
            ),
            _task(
                "Sun plus rise names the event when the sun appears in the morning.",
                "Build and define the compound without reversing the bases.",
                "Sunrise combines sun and rise and names the morning appearance of the sun.",
                [
                    _evidence("form", "Forms sunrise in the correct order.", "Sunrise", "sun and rise"),
                    _evidence("definition", "Defines the morning event.", "morning appearance", "sun appears"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "A light band crossed the sky. Please light the small lamp.",
                "Classify light in each sentence.",
                "Light is an adjective describing band in the first sentence and a verb meaning ignite in the second.",
                [
                    _evidence("description", "Identifies the adjective use.", "adjective describing band", "Light is an adjective"),
                    _evidence("action", "Identifies the verb use.", "verb meaning ignite", "light the lamp"),
                ],
                skills=["grammar.noun_verb_adjective"],
            ),
            _task(
                "Cloud plus burst forms cloudburst. The sudden cloudburst flooded the lane.",
                "Explain the compound's bases, meaning, and sentence job.",
                "Cloudburst combines cloud and burst and means sudden heavy rain; in the sentence it is a noun naming the event.",
                [
                    _evidence("compound", "Explains bases and combined meaning.", "cloud and burst", "sudden heavy rain"),
                    _evidence("job", "Classifies cloudburst as a noun.", "noun naming the event", "it is a noun"),
                ],
                skills=WORDCRAFT_SKILLS,
            ),
        ],
    },
    {
        "level_id": "rainbow_reference_and_context",
        "title": "Track words and references",
        "focus": "resolve pronouns and infer unfamiliar meaning from context",
        "outcome": "Identify what a reference word points to and explain an unfamiliar word using nearby action, contrast, or description clues.",
        "skill_ids": REFERENCE_SKILLS,
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:new-words:2",
            f"{CHAPTER_ID}:think:2-3",
            f"{CHAPTER_ID}:learn:3",
            f"{CHAPTER_ID}:write-poem:7-8",
        ],
        "principle": "For a reference word, test the nearby nouns for number and meaning; for an unfamiliar word, replace it with a meaning that preserves the whole sentence.",
        "connect": {
            "teaching_block": "A poem often avoids repeating the same noun. Pronouns keep the lines flowing, while surrounding details reveal what unusual words mean.",
            "passage": "The bright bands appeared after rain. They faded as the afternoon grew warmer, but the children remembered them.",
            "prompt": "Track what each they or them points to before deciding what happened.",
        },
        "co_construct": _choice(
            "The coloured arc crossed the cloud. It became faint within minutes.",
            "What does It refer to?",
            "the coloured arc",
            ["the cloud", "the minutes", "the colour blue"],
            skills=["grammar.pronouns"],
        ),
        "guided": [
            _choice(
                "Seven bands appeared above the field. They seemed brightest near the centre.",
                "What does They refer to?",
                "the seven bands",
                ["the field", "the centre", "the spectators"],
                skills=["grammar.pronouns"],
            ),
            _task(
                "The arc was vivid; its colours remained strong even beside the bright afternoon sky.",
                "Explain vivid and use the nearby clue in your answer.",
                "Vivid means very bright and clear, shown by the colours remaining strong beside the bright sky.",
                [
                    _evidence("meaning", "Defines vivid as bright and clear.", "bright and clear", "strong colour"),
                    _evidence("clue", "Uses the strong-colour clue.", "colours remained strong", "beside the bright sky"),
                ],
                skills=["reading.word_meaning_context"],
            ),
        ],
        "independent": [
            _task(
                "Mira noticed two pale bands near the horizon. She photographed them before they disappeared.",
                "Identify what She, them, and they each refer to.",
                "She refers to Mira, while them and they both refer to the two pale bands.",
                [
                    _evidence("person", "Links She to Mira.", "She refers to Mira", "She means Mira"),
                    _evidence("bands", "Links both plural references to the bands.", "them and they", "two pale bands"),
                ],
                skills=["grammar.pronouns"],
            ),
            _task(
                "The colours dissolved into the grey sky until no clear edge remained.",
                "Infer dissolved in this sentence and cite the result clue.",
                "Dissolved means gradually blended or disappeared, supported by the fact that no clear edge remained.",
                [
                    _evidence("meaning", "Explains gradual blending or disappearance.", "gradually blended", "disappeared"),
                    _evidence("clue", "Uses the missing-edge clue.", "no clear edge remained", "edge disappeared"),
                ],
                skills=["reading.word_meaning_context"],
            ),
        ],
        "transfer": [
            _task(
                "The lanterns hung from the balcony. When the wind moved them, they tapped softly against the rail.",
                "Resolve both plural pronouns and explain why the rail cannot be their referent.",
                "Them and they refer to the lanterns because both pronouns are plural and describe objects moved by wind; the singular rail stays fixed.",
                [
                    _evidence("referent", "Links both pronouns to lanterns.", "refer to the lanterns", "them and they"),
                    _evidence("reason", "Uses number and action to reject rail.", "pronouns are plural", "rail stays fixed"),
                ],
                skills=["grammar.pronouns"],
            ),
            _task(
                "The lake looked tranquil: its surface was smooth, and even the ducks drifted without splashing.",
                "Infer tranquil and explain how two clues support the meaning.",
                "Tranquil means calm and peaceful; the smooth surface and quietly drifting ducks both support that meaning.",
                [
                    _evidence("meaning", "Defines tranquil as calm or peaceful.", "calm and peaceful", "quiet"),
                    _evidence("clues", "Uses the smooth water and quiet ducks.", "smooth surface", "ducks drifted without splashing"),
                ],
                skills=["reading.word_meaning_context"],
            ),
        ],
        "review": [
            _task(
                "A shower crossed the farms. It cooled them, and they looked greener afterward.",
                "Identify the referent of It, them, and they.",
                "It refers to the shower, while them and they refer to the farms.",
                [
                    _evidence("singular", "Links It to the shower.", "It refers to the shower", "It means the shower"),
                    _evidence("plural", "Links them and they to farms.", "them and they refer to the farms", "farms"),
                ],
                skills=["grammar.pronouns"],
            ),
            _task(
                "The colours were fleeting: they shone for a short while and vanished before the bus arrived.",
                "Explain fleeting using both time clues.",
                "Fleeting means lasting only briefly, shown by the short while of brightness before the colours vanished before the bus arrived.",
                [
                    _evidence("meaning", "Defines fleeting as brief.", "lasting only briefly", "short-lived"),
                    _evidence("clues", "Uses both short duration clues.", "short while", "vanished before"),
                ],
                skills=["reading.word_meaning_context"],
            ),
        ],
        "cluster_id": "rainbow-nearest-noun-or-guessing",
        "misconception": "The learner attaches every pronoun to the nearest noun or guesses an unfamiliar word without checking sentence number, action, and context clues.",
        "remediation": "Draw reference arrows from each pronoun to a noun that matches number and action, then test a plain-language replacement for the unfamiliar word in the complete sentence.",
        "support": [
            _task(
                "The clouds opened above the hills. They revealed a strip of blue sky.",
                "What does They mean, and which grammar clue helps?",
                "They refers to the clouds, and the plural pronoun matches the plural noun.",
                [_evidence("reference", "Links They to clouds using plurality.", "They refers to the clouds", "plural pronoun")],
                skills=["grammar.pronouns"],
            ),
            _task(
                "The arc was radiant, glowing so brightly that it stood out against the dark cloud.",
                "Infer radiant through a clue-replacement check.",
                "Radiant means shining brightly because the arc was glowing and stood out against the dark cloud.",
                [
                    _evidence("meaning", "Defines radiant as shining brightly.", "shining brightly", "glowing"),
                    _evidence("clue", "Uses contrast with the dark cloud.", "dark cloud", "stood out"),
                ],
                skills=["reading.word_meaning_context"],
            ),
            _task(
                "Ravi placed the colour cards beside the chart. He arranged them before it was displayed.",
                "Resolve He, them, and it using number and meaning.",
                "He refers to Ravi, them refers to the colour cards, and it refers to the chart.",
                [
                    _evidence("person", "Links He to Ravi.", "He refers to Ravi", "He means Ravi"),
                    _evidence("objects", "Links them to cards and it to chart.", "them refers to the colour cards", "it refers to the chart"),
                ],
                skills=["grammar.pronouns"],
            ),
            _task(
                "The breeze subsided; leaves that had shaken constantly became still.",
                "Explain subsided with the before-and-after clue.",
                "Subsided means became weaker or stopped, shown because the leaves had shaken constantly and then became still.",
                [
                    _evidence("meaning", "Defines weakening or stopping.", "became weaker", "stopped"),
                    _evidence("change", "Uses movement-to-stillness evidence.", "became still", "had shaken constantly"),
                ],
                skills=["reading.word_meaning_context"],
            ),
            _task(
                "A bright band crossed the valley. It faded slowly, but the walkers kept describing it after they reached camp.",
                "Resolve both uses of it and they, then explain faded from context.",
                "Both uses of it refer to the bright band, they refers to the walkers, and faded means became less visible over time.",
                [
                    _evidence("references", "Resolves band and walker references.", "it refer to the bright band", "they refers to the walkers"),
                    _evidence("meaning", "Defines faded as becoming less visible.", "became less visible", "slowly disappeared"),
                ],
                skills=REFERENCE_SKILLS,
            ),
        ],
    },
    {
        "level_id": "rainbow_colour_sequence",
        "title": "Reason through the colour order",
        "focus": "use sequence evidence to locate, correct, and explain colour positions",
        "outcome": "Reconstruct the seven-colour order from clues and write a concise answer that explains where a missing or misplaced colour belongs.",
        "skill_ids": COLOUR_SKILLS,
        "episode_kind": "application_mission",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:write-words:9-12",
        ],
        "principle": "Treat the colour mnemonic as an ordered map, not a bag of names: compare neighbours, count positions, then explain one correction in a complete short answer.",
        "connect": {
            "teaching_block": "A sequence question needs position evidence. The seven-colour mnemonic helps recall the order, but a strong answer also names the neighbours that prove a position.",
            "passage": "The sequence is violet, indigo, blue, green, yellow, orange, red. Each colour has a fixed neighbour except the two ends.",
            "prompt": "Trace the order from violet to red and notice which colours sit around green.",
        },
        "co_construct": _choice(
            "violet, indigo, blue, green, yellow, orange, red",
            "Which colour comes immediately after blue?",
            "green",
            ["indigo", "yellow", "red"],
            skills=["reading.event_sequence"],
        ),
        "guided": [
            _choice(
                "violet, indigo, __, green, yellow, orange, red",
                "Which colour completes the third position?",
                "blue",
                ["orange", "red", "violet"],
                skills=["reading.event_sequence"],
            ),
            _task(
                "A chart places yellow directly after blue and leaves out green.",
                "Write one sentence correcting the chart and name both neighbours of green.",
                "Green belongs between blue and yellow, so the chart must insert green after blue and before yellow.",
                [
                    _evidence("position", "Places green between blue and yellow.", "Green belongs between blue and yellow", "after blue and before yellow"),
                    _evidence("correction", "States the required insertion.", "insert green", "chart must add green"),
                ],
                skills=["writing.short_answer"],
            ),
        ],
        "independent": [
            _task(
                "A card row reads violet, indigo, blue, yellow, green, orange, red.",
                "Identify the misplaced pair and give the corrected seven-colour order.",
                "Yellow and green are reversed. The correct order is violet, indigo, blue, green, yellow, orange, red.",
                [
                    _evidence("error", "Identifies yellow and green as reversed.", "Yellow and green are reversed", "green and yellow swapped"),
                    _evidence("order", "Gives the complete corrected order.", "violet, indigo, blue, green, yellow, orange, red"),
                ],
                ordered=True,
                skills=["reading.event_sequence"],
            ),
            _task(
                "Clues: orange is between yellow and red; yellow follows green; red is the final colour.",
                "Write a short answer placing yellow, orange, and red in order and explain one clue.",
                "The order is yellow, orange, red. Orange must be in the middle because it is between yellow and the final colour, red.",
                [
                    _evidence("order", "Places yellow, orange, and red correctly.", "yellow, orange, red", "yellow then orange then red"),
                    _evidence("reason", "Uses the between clue or final-position clue.", "orange must be in the middle", "red is final"),
                ],
                skills=["writing.short_answer"],
            ),
        ],
        "transfer": [
            _task(
                "Race stations are marked A, B, C, D, E, F, G. A runner skips from C to E.",
                "Use sequence reasoning to identify the skipped station and its neighbours.",
                "The runner skipped D, which belongs after C and before E.",
                [
                    _evidence("missing", "Identifies D as missing.", "skipped D", "missing station is D"),
                    _evidence("neighbours", "Places D between C and E.", "after C and before E", "between C and E"),
                ],
                skills=["reading.event_sequence"],
            ),
            _task(
                "A learner says, 'Red should come before orange because R appears earlier in the mnemonic word.' The taught colour sequence ends with orange, red.",
                "Correct the claim in two sentences using sequence evidence rather than alphabet order.",
                "The mnemonic records colour order, not alphabet order. Orange comes before red, and red is the final colour in the sequence.",
                [
                    _evidence("rule", "Rejects alphabet order as the rule.", "not alphabet order", "mnemonic records colour order"),
                    _evidence("correction", "Places orange before final red.", "Orange comes before red", "red is the final colour"),
                ],
                skills=["writing.short_answer"],
            ),
        ],
        "review": [
            _task(
                "Cards show indigo, blue, green, yellow. One violet card and one orange card must be placed; red stays last.",
                "Explain where both new cards belong in the full sequence.",
                "Violet goes before indigo at the beginning, while orange goes after yellow and before the final red card.",
                [
                    _evidence("violet", "Places violet before indigo.", "Violet goes before indigo", "at the beginning"),
                    _evidence("orange", "Places orange between yellow and red.", "orange goes after yellow", "before the final red"),
                ],
                skills=["reading.event_sequence"],
            ),
            _task(
                "A sequence has the correct first three colours and final two colours, but green and yellow are missing from the middle.",
                "Write the full seven-colour order and explain the middle pair.",
                "The order is violet, indigo, blue, green, yellow, orange, red. Green precedes yellow between blue and orange.",
                [
                    _evidence("full", "Writes all seven colours in order.", "violet, indigo, blue, green, yellow, orange, red"),
                    _evidence("middle", "Explains green before yellow in the middle.", "Green precedes yellow", "between blue and orange"),
                ],
                ordered=True,
                skills=["writing.short_answer"],
            ),
        ],
        "cluster_id": "rainbow-colour-list-without-position-proof",
        "misconception": "The learner remembers some colour names but swaps neighbours, follows alphabet order, or gives a correction without explaining position evidence.",
        "remediation": "Build a seven-slot strip, anchor violet and red at the ends, place each middle colour by both neighbours, then explain one move using before, after, or between.",
        "support": [
            _task(
                "Sequence fragment: blue, __, yellow.",
                "Fill the gap and state the two neighbour clues.",
                "Green fills the gap because it comes after blue and before yellow.",
                [_evidence("gap", "Places green and names both neighbours.", "Green fills the gap", "after blue and before yellow")],
                skills=COLOUR_SKILLS,
            ),
            _task(
                "Mixed cards: red, green, violet, orange, blue, yellow, indigo.",
                "Describe how to rebuild the order from the two ends inward.",
                "Place violet first and red last, then arrange indigo, blue, green, yellow, and orange between them in that order.",
                [
                    _evidence("ends", "Anchors violet first and red last.", "violet first", "red last"),
                    _evidence("middle", "Orders all five middle colours.", "indigo, blue, green, yellow, and orange"),
                ],
                ordered=True,
                skills=COLOUR_SKILLS,
            ),
            _task(
                "The row reads violet, blue, indigo, green, yellow, orange, red.",
                "Name the one swap that repairs the row.",
                "Swap blue and indigo so the beginning becomes violet, indigo, blue.",
                [_evidence("repair", "Names the swap and corrected beginning.", "Swap blue and indigo", "violet, indigo, blue")],
                skills=["reading.event_sequence"],
            ),
            _task(
                "A child remembers only that green is fourth and red is seventh.",
                "Write a short explanation of what those position numbers mean.",
                "Green has three colours before it, while red comes after all six other colours at the end.",
                [
                    _evidence("green", "Explains fourth position.", "three colours before it", "Green is fourth"),
                    _evidence("red", "Explains seventh or final position.", "after all six", "at the end"),
                ],
                skills=["writing.short_answer"],
            ),
            _task(
                "A corrected chart now reads violet, indigo, blue, green, yellow, orange, red.",
                "Verify the chart by naming the third, fourth, and sixth colours with one sentence of evidence.",
                "Blue is third, green is fourth, and orange is sixth; their neighbours match the complete taught sequence.",
                [
                    _evidence("positions", "Names all three requested positions.", "Blue is third", "green is fourth", "orange is sixth"),
                    _evidence("evidence", "Connects verification to neighbouring order.", "neighbours match", "complete taught sequence"),
                ],
                skills=COLOUR_SKILLS,
            ),
        ],
    },
    {
        "level_id": "rainbow_journey_paragraph",
        "title": "Shape a journey paragraph",
        "focus": "organise a first-person journey using consistent past tense",
        "outcome": "Plan and write a focused journey paragraph with a clear opening, ordered events, sensory detail, and a closing reflection in consistent past tense.",
        "skill_ids": JOURNEY_SKILLS,
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [
            f"{CHAPTER_ID}:write-poem:7-8",
            f"{CHAPTER_ID}:write-words:9-12",
        ],
        "principle": "Choose one journey focus, order events with time signals, keep completed actions in past tense, and close with what the traveller noticed or learned.",
        "connect": {
            "teaching_block": "A journey paragraph is more than a list of vehicles. It leads a reader from departure through one or two meaningful moments to an arrival or reflection.",
            "passage": "Yesterday, I boarded a ferry before sunrise, watched fishing boats cross the pink water, and reached the island as the market opened.",
            "prompt": "Notice the past-tense actions, chronological movement, sensory image, and arrival point.",
        },
        "co_construct": _choice(
            "Last Sunday, we ___ across the lake before the rain began.",
            "Which verb form matches the completed journey?",
            "sailed",
            ["sail", "sails", "sailing"],
            skills=["grammar.tense_usage"],
        ),
        "guided": [
            _choice(
                "Yesterday, I ___ the early bus and ___ the hill town by noon.",
                "Which pair keeps both completed actions in past tense?",
                "caught, reached",
                ["catch, reach", "catches, reached", "catching, reaches"],
                skills=["grammar.tense_usage"],
            ),
            _task(
                "Notes: school gate at dawn; bus climbed a winding road; mist covered tea gardens; arrival before breakfast.",
                "Write a three-sentence journey paragraph with opening, ordered middle detail, and arrival.",
                "We left the school gate at dawn and climbed a winding road by bus. Mist covered the tea gardens beside us. We reached the hostel before breakfast.",
                [
                    _evidence("structure", "Includes departure, middle observation, and arrival.", "left the school gate", "mist covered", "reached the hostel"),
                    _evidence("tense", "Keeps completed actions in past tense.", "left", "covered", "reached"),
                ],
                interaction_type="paragraph_text",
                skills=["writing.paragraph"],
            ),
        ],
        "independent": [
            _task(
                "Journey packet: last evening; village square; river jetty; wooden ferry; baskets under a bench; lamps on the far bank; cool breeze; arrival across the river.",
                "Write an 80- to 100-word first-person journey paragraph using last evening, then, and finally, with consistent past tense, ordered movement, sensory detail, and a closing response.",
                "Last evening, I walked from our village square to the river jetty, where a wooden ferry waited beside the steps. First, I helped the boatman place two baskets safely under a bench. Then we crossed the dark water while lamps flickered along the opposite bank. A cool breeze carried the smell of wet mud across the deck. Finally, I reached the far bank, thanked the boatman, and felt proud that I had travelled calmly during my first evening ferry journey.",
                [
                    _evidence("journey", "Orders departure, crossing details, and arrival.", "walked from our village square", "crossed the dark water", "reached the far bank"),
                    _evidence("craft", "Uses all time signals, sensory detail, and a closing response in past tense.", "Last evening", "Then", "Finally", "smell of wet mud", "felt proud"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
            _task(
                "Journey packet: overnight train; window seat; sunrise over farms; shared breakfast; station arrival at eight; platform sounds; reflection on changing scenes.",
                "Write an 80- to 100-word first-person journey paragraph with a focused opening, ordered movement, two sensory details, consistent past tense, and a closing response.",
                "I travelled overnight by train and woke beside the window just before sunrise. Golden light spread across the farms, and drops of mist shone on the glass while my family shared breakfast from a steel box. At eight, the train entered the busy station, where our quiet view changed into whistles, voices, and hurried footsteps. I carried our bag onto the platform and looked back at the long line of coaches. The changing scenes made me feel rested, alert, and grateful for the journey.",
                [
                    _evidence("organisation", "Builds an opening, connected journey details, arrival, and closing response.", "travelled overnight", "Golden light", "At eight", "onto the platform", "grateful for the journey"),
                    _evidence("craft", "Keeps the paragraph centred on the train journey with sensory detail and past-tense actions.", "mist shone", "whistles, voices", "carried our bag", "looked back"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
        ],
        "transfer": [
            _task(
                "Journey draft: 'Last Friday we cycle to the wetland and see cranes. Our guide explained the nesting area.' Notes add a muddy track, reed shadows, a quiet observation stop, the return before rain, and a reflection about protecting habitats.",
                "Rewrite and expand the draft into an 80- to 100-word first-person journey paragraph with consistent past tense, ordered events, sensory detail, arrival, and reflection.",
                "Last Friday, we cycled along a muddy track to the wetland and saw cranes standing beyond the reeds. Their long shadows moved across the shallow water while our guide explained the nesting area. We stopped quietly near a wooden screen and watched one bird lift into the grey sky. Dark clouds gathered, so we rode back to school before the rain began. The careful visit showed me that people can enjoy a journey through nature while still giving wild birds the space and safety they need.",
                [
                    _evidence("events", "Orders travel, observation, explanation, and return in past tense.", "cycled along a muddy track", "saw cranes", "guide explained", "rode back to school"),
                    _evidence("craft", "Adds sensory detail and closes with a habitat reflection.", "shadows moved", "grey sky", "space and safety"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
            _task(
                "Journey packet: bicycle trip to aunt's village; warm afternoon; tyre puncture beside a canal; worried pause; shopkeeper helps; ride resumes; arrival before sunset; lesson about a repair kit.",
                "Write an 80- to 100-word focused journey paragraph that orders every stage, uses consistent past tense and sensory detail, and turns the problem into a meaningful ending.",
                "I cycled toward my aunt's village on a warm afternoon, but my rear tyre punctured beside the canal. For a moment, I felt worried as trucks passed and dry grass rustled near the water. A shopkeeper from a nearby stall brought a pump, showed me the small tear, and helped me repair it. I thanked him and resumed the ride, reaching the village before sunset. The delay taught me to check my bicycle carefully and carry a repair kit whenever I planned another long journey.",
                [
                    _evidence("events", "Orders trip, puncture, help, resumed travel, and arrival.", "cycled toward", "tyre punctured", "shopkeeper", "resumed the ride", "reaching the village"),
                    _evidence("ending", "Closes with the practical lesson from the problem.", "taught me", "check my bicycle", "carry a repair kit"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
        ],
        "review": [
            _task(
                "Draft: 'Last month, I travel by metro, change lines twice, and reached the museum before ten.' Notes add a crowded first platform, a quiet underground tunnel, a helpful sign, arrival before ten, and confidence about travelling independently.",
                "Revise the draft into an 80- to 100-word first-person journey paragraph with corrected past tense, ordered movement, sensory contrast, arrival, and reflection.",
                "Last month, I travelled by metro to the city museum and changed lines twice along the way. The first platform was crowded and noisy, but the underground tunnel became cool and quiet after the train doors closed. At the interchange, a clear blue sign helped me find the correct staircase without rushing. I reached the museum before ten and joined my class near the entrance. Completing each change calmly made me feel more confident about reading signs and travelling independently in a busy city.",
                [
                    _evidence("events", "Uses consistent past tense for travel, changes, and arrival.", "travelled by metro", "changed lines twice", "reached the museum"),
                    _evidence("craft", "Adds sensory contrast and closes with a personal reflection.", "crowded and noisy", "cool and quiet", "more confident"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
            _task(
                "Draft: We went somewhere. It was nice. We came back. Notes add a morning hill walk, cold wind through grass, a steep rocky turn, a rainbow over the valley, shared silence, return before lunch, and a lasting memory.",
                "Revise the draft into an 80- to 100-word vivid journey paragraph with ordered past-tense movement, sensory detail, a focused key moment, return, and closing reflection.",
                "We climbed the hill path early in the morning while cold wind moved through the silver grass. After a steep rocky turn, we reached a ledge above the valley and stopped to catch our breath. A rainbow curved across the clearing sky, and everyone became quiet as the colours brightened over the fields. We watched until the arc faded, then walked home before lunch along the same narrow path. That shared moment of silence became the part of the journey I remembered most clearly.",
                [
                    _evidence("detail", "Orders the climb, ledge, rainbow, and return with sensory detail.", "hill path", "cold wind", "rocky turn", "rainbow", "walked home before lunch"),
                    _evidence("ending", "Closes with a focused reflection on the shared key moment.", "shared moment of silence", "remembered most clearly"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
        ],
        "cluster_id": "rainbow-journey-list-or-tense-shift",
        "misconception": "The learner lists disconnected transport details, shifts between present and past for completed actions, or omits an arrival or reflection that closes the journey.",
        "remediation": "Plan four boxes for departure, movement, key moment, and arrival or lesson; circle past-tense verbs in each box before combining them into one focused paragraph.",
        "support": [
            _task(
                "Time clue: yesterday. Actions: board bus; cross bridge; arrive market.",
                "Change all three actions to past tense in one ordered sentence.",
                "Yesterday, I boarded the bus, crossed the bridge, and arrived at the market.",
                [_evidence("sentence", "Uses all three past forms in order.", "boarded", "crossed", "arrived")],
                skills=["grammar.tense_usage"],
            ),
            _task(
                "Journey frame: departure from home, one surprising sight, arrival at grandmother's house, closing feeling.",
                "Fill the four-part frame with a connected paragraph.",
                "I left home after breakfast and travelled by bus. On the way, I saw hundreds of white birds beside a flooded field. I reached my grandmother's house before noon and felt eager to tell her about the sight.",
                [
                    _evidence("frame", "Includes all four planned parts.", "left home", "white birds", "reached", "felt eager"),
                    _evidence("connection", "Links details as one journey.", "On the way", "before noon"),
                ],
                interaction_type="paragraph_text",
                skills=["writing.paragraph"],
            ),
            _task(
                "Draft verbs: leave, rode, see, stopped, return. Time: last Saturday.",
                "Repair the tense pattern and use every action in two sentences.",
                "Last Saturday, we left home, rode toward the lake, and saw a rainbow. We stopped to watch it and returned before dark.",
                [
                    _evidence("forms", "Uses left, rode, saw, stopped, and returned.", "left", "rode", "saw", "stopped", "returned"),
                    _evidence("time", "Connects actions to last Saturday.", "Last Saturday", "completed actions"),
                ],
                skills=["grammar.tense_usage"],
            ),
            _task(
                "Notes contain six details, but the paragraph focus is a boat ride during rain. Relevant facts: covered boat, drops on river, safe landing. Unrelated facts: lunch menu, shoe colour, classroom timetable.",
                "Select the relevant facts and write a focused mini-paragraph.",
                "We crossed the river in a covered boat while rain patterned the water. The boat kept us dry and reached the landing safely.",
                [
                    _evidence("selection", "Uses covered boat, rainy river, and safe landing.", "covered boat", "rain", "landing safely"),
                    _evidence("focus", "Omits unrelated menu, shoe, and timetable details.", "crossed the river", "kept us dry"),
                ],
                interaction_type="paragraph_text",
                skills=["writing.paragraph"],
            ),
            _task(
                "A trip account has a clear departure and middle but ends with 'Then more things happened.' The supplied outcome is arrival at camp and relief after the steep climb.",
                "Replace the weak ending with two specific past-tense sentences.",
                "We reached the camp as the sun disappeared behind the ridge. I felt relieved that the steep climb was complete.",
                [
                    _evidence("arrival", "States arrival at camp.", "reached the camp", "sun disappeared"),
                    _evidence("reflection", "Closes with relief about the climb.", "felt relieved", "climb was complete"),
                ],
                interaction_type="paragraph_text",
                skills=JOURNEY_SKILLS,
            ),
        ],
    },
]


_DEPTH_EXPANSIONS: dict[str, dict[str, list[dict[str, Any]]]] = {
    "rainbow_image_and_idea": {
        "guided": [
            _choice(
                "A crescent moon floated above the harbour like a white sail.",
                "Which visual feature supports the sail comparison?",
                "its pale curved shape above the water",
                [
                    "the cloth rope tied to a real mast",
                    "the harbour wall below the boats",
                    "the sound made by the evening tide",
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "A dusty afternoon ended with a short shower. When a clear golden opening appeared between the clouds, shoppers at the bus stand lifted their faces and smiled.",
                "State the central idea by connecting the weather change with the people's response.",
                "A clearing in the clouds transformed the dusty afternoon and gave the waiting shoppers a shared moment of delight.",
                [
                    _evidence("change", "Names the change in the sky.", "clearing in the clouds", "transformed the dusty afternoon"),
                    _evidence("response", "Connects the sight to the shoppers' response.", "waiting shoppers", "shared moment of delight"),
                ],
                interaction_type="summary",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
        "independent": [
            _task(
                "Sunset laid a copper road across the reservoir, running from the far bank toward Leela's feet.",
                "Explain the road image and protect its nonliteral boundary.",
                "The sunlit streak is compared with a road because both form a long bright line, but the water is not a solid path.",
                [
                    _evidence("feature", "Explains the shared long-line feature.", "streak is compared with a road", "long bright line"),
                    _evidence("boundary", "States why the image is not literal.", "water is not a solid path", "not a solid path"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "The warning siren stopped as the storm moved east. A double arc emerged over the cycle track, and riders who had sheltered separately called one another out to see it.",
                "Write one sentence expressing the central idea rather than a list of events.",
                "The storm's departure revealed a striking sky scene that turned separate waiting riders into an excited group.",
                [
                    _evidence("idea", "Combines the changed weather and shared response.", "storm's departure", "separate waiting riders into an excited group"),
                ],
                interaction_type="summary",
                skills=["reading.paragraph_main_idea"],
            ),
        ],
        "transfer": [
            _task(
                "A librarian called the rising row of books on a display table 'a staircase of stories.'",
                "Interpret the staircase image by naming the compared things, their shared feature, and the literal limit.",
                "The rising books are compared with a staircase because both climb in steps, although the books are not actual stairs for people.",
                [
                    _evidence("comparison", "Names the books and staircase with their stepped shape.", "books are compared with a staircase", "both climb in steps"),
                    _evidence("limit", "Rejects the literal use of the books as stairs.", "not actual stairs for people", "books are not actual stairs"),
                ],
                skills=["reading.poetic_language", "reading.paragraph_main_idea"],
            ),
        ],
    },
    "rainbow_natural_and_built": {
        "guided": [
            _choice(
                "Information card: rope footbridge; woven fibre deck; crosses a mountain stream; checked before the rainy season. The card gives no age for the bridge.",
                "Which statement stays fully inside the card?",
                "The rope footbridge crosses a mountain stream and is checked before the rains.",
                [
                    "The bridge is exactly one hundred years old.",
                    "The bridge carries heavy trucks every day.",
                    "The bridge won an international prize.",
                ],
                skills=["research.information_selection"],
            ),
            _task(
                "Dew web: droplets reveal a spider's threads at sunrise and disappear as the air warms. Fishing net: people knot fibre into a lasting tool used to catch fish.",
                "Compare appearance and duration using one matched similarity and one difference.",
                "Both show a mesh of crossing lines, but the dew web is briefly visible at sunrise while the knotted fishing net lasts as a tool.",
                [
                    _evidence("similarity", "States the shared mesh appearance.", "mesh of crossing lines", "Both show a mesh"),
                    _evidence("difference", "Contrasts brief visibility with lasting use.", "briefly visible at sunrise", "fishing net lasts as a tool"),
                ],
                skills=["writing.compare_contrast"],
            ),
        ],
        "independent": [
            _task(
                "Archive note: a catamaran has two parallel hulls, moves with sails or an engine, and is used on coastal water. The note does not list a maximum passenger number.",
                "Write an attributed two-sentence profile with three facts and the missing capacity boundary.",
                "The archive note describes a catamaran with two parallel hulls that travels on coastal water using sails or an engine. It does not state a maximum passenger capacity.",
                [
                    _evidence("source", "Attributes the profile to the archive note.", "archive note describes"),
                    _evidence("form", "Reports the two-hull form.", "catamaran with two parallel hulls"),
                    _evidence("setting", "Reports the coastal setting.", "travels on coastal water"),
                    _evidence("movement", "Reports the supplied movement methods.", "using sails or an engine"),
                    _evidence("capacity", "Protects the missing capacity fact.", "does not state a maximum passenger capacity"),
                ],
                skills=["research.information_selection"],
            ),
            _task(
                "Lightning fork: a natural flash that branches for a moment and cannot guide traffic. Road junction: a built split in the road that remains in place and directs vehicles.",
                "Compare shape, duration, and function without claiming the two are identical.",
                "Both can show branching lines, but the lightning fork vanishes in a moment while the road junction remains. Only the built junction directs vehicles.",
                [
                    _evidence("shape_duration", "Gives the shared shape and duration contrast.", "branching lines", "lightning fork vanishes in a moment"),
                    _evidence("function", "Contrasts their traffic function.", "built junction directs vehicles", "Only the built junction"),
                ],
                skills=["writing.compare_contrast"],
            ),
        ],
        "transfer": [
            _task(
                "Field notes: baya nest, woven by a bird from grass, hangs from a branch, shelters eggs. Market basket, woven by a craftsperson from cane, carried by a handle, holds goods.",
                "Write a sourced comparison of maker, material action, and purpose.",
                "Both objects are woven from plant material, but a bird makes the hanging nest to shelter eggs while a craftsperson makes the handled basket to carry goods.",
                [
                    _evidence("similarity", "States the shared weaving and plant material.", "woven from plant material", "Both objects are woven"),
                    _evidence("differences", "Contrasts maker and purpose on both sides.", "bird makes the hanging nest", "craftsperson makes the handled basket"),
                ],
                skills=COMPARE_SKILLS,
            ),
        ],
    },
    "rainbow_sound_and_contrast": {
        "guided": [
            _choice(
                "A lone bird flew over stone, then settled quietly on its own.",
                "Which words make the strongest end-sound pair?",
                "stone and own",
                ["bird and quietly", "flew and settled", "over and its"],
                skills=["reading.poetic_language"],
            ),
            _choice(
                "Near the bank the water was shallow, but beside the old pier it became ___.",
                "Which word completes the opposite contrast?",
                "deep",
                ["silver", "moving", "narrow"],
                skills=["vocab.antonyms"],
            ),
        ],
        "independent": [
            _task(
                "Drip on the roof, drip by the door; sweep of the broom, sweep on the floor.",
                "Identify the repeated words and both rhyme pairs, then explain the rhythm they create.",
                "Drip and sweep are repeated, while roof rhymes with broom and door rhymes with floor, creating a steady work-like beat.",
                [
                    _evidence("patterns", "Names the repetitions and rhyme pairs.", "Drip and sweep are repeated", "roof rhymes with broom", "door rhymes with floor"),
                    _evidence("effect", "Explains the resulting rhythm.", "steady work-like beat", "creating a steady"),
                ],
                skills=["reading.poetic_language"],
            ),
            _task(
                "The corridor was noisy during lunch, yet it became silent when the principal began the announcement.",
                "Name the antonyms and explain what event caused the contrast.",
                "Noisy and silent are opposites, and the principal's announcement changed the corridor from lunch chatter to quiet attention.",
                [
                    _evidence("pair", "Names the opposite words.", "Noisy and silent are opposites", "Noisy and silent"),
                    _evidence("cause", "Connects the change to the announcement.", "principal's announcement", "quiet attention"),
                ],
                skills=["vocab.antonyms"],
            ),
        ],
        "transfer": [
            _task(
                "Rise with the sun, run for the fun; strong in our stride, long is the ride.",
                "Explain how the rhyme pairs and repeated sentence pattern make this chant energetic.",
                "Sun and fun rhyme, as do stride and ride, while the repeated action phrases create a quick, energetic marching rhythm.",
                [
                    _evidence("rhymes", "Identifies both rhyme pairs.", "Sun and fun rhyme", "stride and ride"),
                    _evidence("rhythm", "Explains the energetic repeated pattern.", "repeated action phrases", "energetic marching rhythm"),
                ],
                skills=["reading.poetic_language"],
            ),
        ],
    },
    "rainbow_compounds_and_word_jobs": {
        "guided": [
            _choice(
                "Tooth plus brush names a brush used for cleaning teeth.",
                "Which compound preserves both base meanings?",
                "toothbrush",
                ["toothpaste", "hairbrush", "paintbrush"],
                skills=["vocab.word_formation"],
            ),
            _choice(
                "We paint the scenery after lunch.",
                "What job does paint perform in this sentence?",
                "verb naming the action",
                ["noun naming the scenery", "adjective describing lunch", "pronoun replacing we"],
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
        "independent": [
            _task(
                "Star plus fish names a sea animal whose body often has radiating arms.",
                "Form the compound and explain the contribution of each base.",
                "Starfish combines star and fish: fish names the animal, while star describes its radiating body shape.",
                [
                    _evidence("form", "Forms the compound from both bases.", "Starfish combines star and fish", "star and fish"),
                    _evidence("roles", "Explains what each base contributes.", "fish names the animal", "star describes its radiating body shape"),
                ],
                skills=["vocab.word_formation"],
            ),
            _task(
                "Sentence A: The clean window reflected the clouds. Sentence B: Please clean the paintbrushes.",
                "Classify clean in each sentence and justify both decisions from its job.",
                "Clean is an adjective describing the window in sentence A, but it is a verb directing an action in sentence B.",
                [
                    _evidence("adjective", "Classifies the describing use.", "adjective describing the window", "sentence A"),
                    _evidence("verb", "Classifies the action use.", "verb directing an action", "sentence B"),
                ],
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
        "transfer": [
            _task(
                "Green plus house forms greenhouse. In 'The greenhouse protects young plants,' the joined word names a structure.",
                "Explain the compound meaning and classify its sentence job.",
                "Greenhouse combines green and house to name a plant-growing structure, and it works as a noun because it names that structure in the sentence.",
                [
                    _evidence("meaning", "Explains the combined word meaning.", "plant-growing structure", "combines green and house"),
                    _evidence("job", "Classifies the word as a naming noun.", "works as a noun", "names that structure"),
                ],
                skills=WORDCRAFT_SKILLS,
            ),
        ],
    },
    "rainbow_reference_and_context": {
        "guided": [
            _choice(
                "Nisha handed the sketch to Tara because she had finished colouring it.",
                "In the clearest reading, what does it refer to?",
                "the sketch",
                ["Nisha", "Tara", "the colouring time"],
                skills=["grammar.pronouns"],
            ),
            _choice(
                "After the long walk, Kabir felt drowsy and could barely keep his eyes open.",
                "What does drowsy mean here?",
                "sleepy",
                ["angry", "hungry", "lost"],
                skills=["reading.word_meaning_context"],
            ),
        ],
        "independent": [
            _task(
                "Arun placed three jars beside the seedlings. He filled them before they were carried into the greenhouse.",
                "Identify the referent of He, them, and they, using number and action.",
                "He refers to Arun, while them and they refer to the three jars that Arun filled and someone later carried.",
                [
                    _evidence("person", "Links the singular person reference.", "He refers to Arun", "Arun filled"),
                    _evidence("objects", "Links both plural pronouns to the jars.", "them and they refer to the three jars", "someone later carried"),
                ],
                skills=["grammar.pronouns"],
            ),
            _task(
                "The marbles scattered when the pouch tore, rolling under desks and into corners across the room.",
                "Infer scattered and cite two action clues.",
                "Scattered means spread in different directions, shown by the marbles rolling under desks and into corners.",
                [
                    _evidence("meaning", "Defines movement in different directions.", "spread in different directions", "Scattered means spread"),
                    _evidence("clues", "Uses both location clues from the sentence.", "rolling under desks", "into corners"),
                ],
                skills=["reading.word_meaning_context"],
            ),
        ],
        "transfer": [
            _task(
                "The paper lanterns glowed above the courtyard. Meera photographed them before they vanished when the power failed.",
                "Resolve both plural pronouns and explain vanished from the event clue.",
                "Them and they refer to the paper lanterns, and vanished means disappeared from sight when the power failed.",
                [
                    _evidence("referents", "Links both pronouns to the lanterns.", "refer to the paper lanterns", "Them and they"),
                    _evidence("meaning", "Defines vanished using the power-failure clue.", "disappeared from sight", "power failed"),
                ],
                skills=REFERENCE_SKILLS,
            ),
        ],
    },
    "rainbow_colour_sequence": {
        "guided": [
            _choice(
                "On a numbered colour chart, green occupies box 4 and orange occupies box 6.",
                "According to the taught order, which colour belongs between them in box 5?",
                "yellow",
                ["green", "orange", "indigo"],
                skills=["reading.event_sequence"],
            ),
            _choice(
                "The row begins violet, indigo and ends orange, red.",
                "Which ordered group completes the three middle positions?",
                "blue, green, yellow",
                ["green, blue, yellow", "yellow, green, blue", "blue, yellow, green"],
                skills=["reading.event_sequence"],
            ),
        ],
        "independent": [
            _task(
                "A display starts indigo, violet, blue, green, yellow, orange, red.",
                "Identify the opening error and write the corrected sequence.",
                "Indigo and violet are reversed. The corrected sequence is violet, indigo, blue, green, yellow, orange, red.",
                [
                    _evidence("error", "Names the reversed opening pair.", "Indigo and violet are reversed", "opening error"),
                    _evidence("correction", "Writes the complete corrected order.", "violet, indigo, blue, green, yellow, orange, red"),
                ],
                ordered=True,
                skills=["reading.event_sequence"],
            ),
            _task(
                "Position clues: indigo is second, green is fourth, orange is sixth, and red closes the row.",
                "Reconstruct the full sequence and explain how the four anchors support it.",
                "The sequence is violet, indigo, blue, green, yellow, orange, red; the second, fourth, sixth, and final positions match every supplied anchor.",
                [
                    _evidence("sequence", "Writes all seven colours in order.", "violet, indigo, blue, green, yellow, orange, red"),
                    _evidence("anchors", "Checks the named positions against the clues.", "second, fourth, sixth, and final positions", "match every supplied anchor"),
                ],
                ordered=True,
                skills=["writing.short_answer"],
            ),
        ],
        "transfer": [
            _task(
                "A recipe order is wash the mangoes, peel them, slice them, then blend them. A learner puts blending before slicing.",
                "Use neighbour evidence to correct the misplaced step.",
                "Slicing must come before blending because it follows peeling and directly prepares the mango pieces for the blender.",
                [
                    _evidence("correction", "Places slicing before blending.", "Slicing must come before blending", "follows peeling"),
                    _evidence("reason", "Explains the functional neighbour link.", "prepares the mango pieces for the blender", "directly prepares"),
                ],
                skills=["reading.event_sequence", "writing.short_answer"],
            ),
        ],
    },
    "rainbow_journey_paragraph": {
        "guided": [
            _choice(
                "Yesterday, the hikers ___ the ridge and ___ beside the spring.",
                "Which pair keeps both completed actions in past tense?",
                "crossed, rested",
                ["cross, rest", "crosses, rested", "crossing, rests"],
                skills=["grammar.tense_usage"],
            ),
            _task(
                "Plan: leave the village after sunrise; follow a forest path; hear langurs in the trees; reach the watchtower before noon.",
                "Turn the plan into three ordered past-tense sentences with a clear arrival.",
                "We left the village after sunrise and followed a forest path. Langurs called from the trees as we climbed. We reached the watchtower before noon.",
                [
                    _evidence("order", "Includes departure, middle detail, and arrival.", "left the village", "Langurs called", "reached the watchtower"),
                    _evidence("tense", "Uses consistent completed-action verbs.", "followed a forest path", "before noon"),
                ],
                interaction_type="paragraph_text",
                skills=["writing.paragraph"],
            ),
        ],
        "independent": [
            _task(
                "Journey packet: early this morning; quiet bus stop; town bus; crowded market; bakery smell; bridge traffic; sports ground; teammates waiting; relief at arriving on time.",
                "Write an 80- to 100-word first-person journey paragraph using early this morning, next, and at last, with consistent past tense, ordered movement, sensory detail, and a closing response.",
                "Early this morning, I waited at a quiet bus stop while the sky slowly brightened above the shops. I boarded the town bus and found a seat beside the window. Next, we crossed the crowded market, where the smell of fresh bread drifted from a bakery, and moved slowly through bridge traffic. At last, I reached the sports ground and saw my teammates warming up near the track. I felt relieved that the careful early start had helped me arrive on time for practice.",
                [
                    _evidence("events", "Orders waiting, boarding, market travel, and arrival.", "waited at a quiet bus stop", "boarded the town bus", "crossed the crowded market", "reached the sports ground"),
                    _evidence("craft", "Uses all time signals, sensory detail, and a closing response in past tense.", "Early this morning", "Next", "At last", "smell of fresh bread", "felt relieved"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
            _task(
                "Journey packet: paddle from the jetty at dawn; narrow mangrove creek; dark roots; blue kingfisher; soft paddle sounds; tide rises over muddy banks; safe return; curiosity about the wetland.",
                "Write an 80- to 100-word focused first-person journey paragraph with ordered movement, at least two sensory details, consistent past tense, safe return, and a closing reflection.",
                "We paddled from the jetty at dawn and entered a narrow mangrove creek as pale light spread across the water. Dark roots twisted above the mud, and each paddle stroke made a soft splash beside the boat. A blue kingfisher flashed over us before settling on a low branch. When the rising tide covered the muddy banks, our guide turned the boat toward the open river. We returned safely to the jetty, and the quiet trip made me curious to learn how mangroves protect the wetland.",
                [
                    _evidence("journey", "Orders departure, creek movement, key sight, tide change, and return.", "paddled from the jetty", "kingfisher flashed", "rising tide", "returned safely"),
                    _evidence("craft", "Uses sensory details and closes with a relevant reflection.", "soft splash", "pale light", "made me curious", "protect the wetland"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
        ],
        "transfer": [
            _task(
                "Journey draft: 'Last Friday we climb the fort steps, pause at the gate, and see the city below.' Notes add rough stone, hot sunlight, a shaded arch, water break, the wide city view, descent before evening, and the reflection that effort made the view feel earned.",
                "Correct and expand the draft into an 80- to 100-word first-person journey paragraph with consistent past tense, ordered movement, sensory detail, return, and the supplied reflection.",
                "Last Friday, we climbed the fort steps while hot sunlight warmed the rough stone beneath our shoes. We paused under a shaded arch, drank water, and listened to pigeons moving above the gate. At the highest wall, we saw the whole city spreading toward the river, with buses appearing like tiny coloured boxes. We rested there for several minutes before descending the same steps before evening. The steep walk tired my legs, but the effort made the wide view feel earned and the journey worth remembering.",
                [
                    _evidence("events", "Orders climb, pause, view, and descent using past tense.", "climbed the fort steps", "paused under", "saw the whole city", "descending"),
                    _evidence("craft", "Adds sensory details and the supplied reflective close.", "hot sunlight", "rough stone", "steep walk", "view feel earned"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                skills=JOURNEY_SKILLS,
            ),
        ],
    },
}


_LAUNCH_VARIANTS = {
    "rainbow_image_and_idea": {
        "transfer": [
            _task(
                "At dawn, five kites climbed above the beach, and a reporter called them 'a ladder of colour rising into the wind.' Families stopped near the shore to watch.",
                "Explain the ladder image and state the central idea of the whole scene.",
                "The rising kites resemble a ladder because they form colourful steps up the sky. The central idea is that the unusual kite display drew families together at dawn.",
                [
                    _evidence("image", "Explains the ladder comparison through the rising stepped shape.", "rising kites resemble a ladder", "colourful steps up the sky"),
                    _evidence("idea", "States how the display affected the families.", "drew families together", "at dawn"),
                ],
            ),
        ],
        "review": [
            _task(
                "Evening lamps reflected across a canal like a golden road. Cyclists slowed beside the railing to admire the bright line on the water.",
                "Interpret the golden-road image and summarise why the cyclists slowed.",
                "The lamp reflections look like a golden road because they form a long bright line across the canal, but no solid road is there. The striking reflection made the cyclists slow and look.",
                [
                    _evidence("image", "Explains the shared long bright shape and its nonliteral limit.", "long bright line across the canal", "no solid road is there"),
                    _evidence("idea", "Connects the reflection with the cyclists' response.", "reflection made the cyclists slow", "and look"),
                ],
            ),
            _task(
                "A gap opened in the clouds, and sunlight spread down a hillside like a curtain being lifted. Workers in the orchard paused as the grey slope brightened.",
                "Explain the lifted-curtain comparison and give the scene's main idea in one sentence.",
                "The clearing clouds resemble a lifted curtain because they reveal the bright hillside. The main idea is that sudden sunlight transformed the grey orchard and caught the workers' attention.",
                [
                    _evidence("comparison", "Connects the opening clouds with a curtain revealing a view.", "resemble a lifted curtain", "reveal the bright hillside"),
                    _evidence("main", "Combines the light change and the workers' response.", "sunlight transformed the grey orchard", "workers' attention"),
                ],
            ),
        ],
    },
    "rainbow_reference_and_context": {
        "transfer": [
            _task(
                "Riya placed three seed packets beside a clay pot filled with damp soil. She labelled them before they were moved into a sheltered room, where the soil smelled earthy.",
                "Identify what She, them, and they refer to, then infer earthy from the final clue.",
                "She refers to Riya, while them and they both refer to the seed packets. Earthy means smelling like damp soil, as the final clue explains.",
                [
                    _evidence(
                        "references",
                        "Identifies Riya as She and the seed packets as both plural antecedents.",
                        "She refers to Riya, while them and they both refer to the seed packets",
                        "She means Riya, and both them and they mean the seed packets",
                    ),
                    _evidence("meaning", "Defines earthy from the damp-soil clue.", "smelling like damp soil", "final clue"),
                ],
            ),
        ],
        "review": [
            _task(
                "The musicians carried their drums beneath the awning. It sheltered them when a sudden shower became torrential, drumming loudly on the roof.",
                "Resolve It and them, then explain torrential using the sound and weather clues.",
                "It refers to the awning, and them refers to the musicians. Torrential means extremely heavy because the sudden rain drummed loudly on the roof.",
                [
                    _evidence("references", "Links both pronouns to the correct nouns.", "It refers to the awning", "them refers to the musicians"),
                    _evidence("context", "Infers very heavy rain from the surrounding clues.", "means extremely heavy", "rain drummed loudly"),
                ],
            ),
            _task(
                "Asha and Neel watched the fireflies near a hedge. They followed them until the tiny lights became sparse, with only one or two visible at a time.",
                "Name both referents of They and them, and infer sparse from the number clue.",
                "They refers to Asha and Neel, while them refers to the fireflies. Sparse means few and far apart, shown by only one or two lights remaining visible.",
                [
                    _evidence("pronouns", "Resolves the people and firefly references.", "They refers to Asha and Neel", "them refers to the fireflies"),
                    _evidence("word", "Defines sparse from the one-or-two clue.", "few and far apart", "only one or two lights"),
                ],
            ),
        ],
    },
    "rainbow_sound_and_contrast": {
        "transfer": [
            _task(
                "Bright was the square when drums filled the air; dull grew the street when no beat met our feet.",
                "Identify the sound pattern and opposite pair, then explain how both mark the change.",
                "Square and air rhyme, as do street and feet, while bright and dull are opposites. The lively rhymes support the busy opening, and the contrast marks the quiet ending.",
                [
                    _evidence("sound", "Identifies both end-sound pairs.", "Square and air rhyme", "street and feet"),
                    _evidence("contrast", "Names the opposites and explains the scene change.", "bright and dull are opposites", "quiet ending"),
                ],
            ),
        ],
        "review": [
            _task(
                "Soft fell the snow, slow did we go; loud rang the bell, proud was its swell.",
                "Name the rhyme pairs and explain the contrast between the two sound moods.",
                "Snow and go rhyme, while bell and swell rhyme. Soft and loud create a contrast between the quiet walk and the strong ringing sound.",
                [
                    _evidence("rhyme", "Identifies both rhyme pairs.", "Snow and go rhyme", "bell and swell rhyme"),
                    _evidence("opposites", "Explains how soft and loud shape different moods.", "Soft and loud create a contrast", "quiet walk"),
                ],
            ),
            _task(
                "Near was the light, bright in our sight; far was the star, small from afar.",
                "Explain the repeated sentence pattern, the rhymes, and the opposite distance words.",
                "The repeated word order balances the two lines. Light and sight rhyme, as do star and afar, while near and far show the change in distance.",
                [
                    _evidence("pattern", "Explains the repeated structure and rhyme pairs.", "repeated word order balances", "Light and sight rhyme", "star and afar"),
                    _evidence("distance", "Identifies the opposite distance words.", "near and far", "change in distance"),
                ],
            ),
        ],
    },
    "rainbow_compounds_and_word_jobs": {
        "transfer": [
            _task(
                "Rain plus coat forms raincoat. In the sentence 'My raincoat kept my uniform dry,' the joined word names an object.",
                "Explain how both bases build the meaning and classify raincoat by its sentence job.",
                "Raincoat combines rain and coat to name a coat worn for protection from rain. It is a noun because it names the object that kept the uniform dry.",
                [
                    _evidence("compound", "Uses both base meanings to define the joined word.", "combines rain and coat", "protection from rain"),
                    _evidence("job", "Classifies the word as a naming noun.", "It is a noun", "names the object"),
                ],
            ),
        ],
        "review": [
            _task(
                "Sun plus flower forms sunflower. In 'The tall sunflower faced the morning light,' the compound names a plant and tall describes it.",
                "Split and define the compound, then classify sunflower and tall by their jobs.",
                "Sunflower combines sun and flower to name a flower with a sun-like head. Sunflower is a noun naming the plant, while tall is an adjective describing it.",
                [
                    _evidence("formation", "Explains the compound using both bases.", "combines sun and flower", "sun-like head"),
                    _evidence("jobs", "Classifies the naming and describing words.", "Sunflower is a noun", "tall is an adjective"),
                ],
            ),
            _task(
                "Book plus case forms bookcase. In 'We book the hall, then place the atlas in the bookcase,' book performs two different jobs.",
                "Explain the compound and classify book in both places.",
                "Bookcase combines book and case to name furniture that holds books. Book is a verb in 'book the hall' because it names an action, but it contributes a noun meaning inside bookcase.",
                [
                    _evidence("meaning", "Defines bookcase from both bases.", "combines book and case", "furniture that holds books"),
                    _evidence("classification", "Explains the action and naming uses of book.", "Book is a verb", "contributes a noun meaning"),
                ],
            ),
        ],
    },
    "rainbow_colour_sequence": {
        "transfer": [
            _task(
                "A bus route lists Market, Library, Clinic, Lake, and Stadium. A passenger's note places Lake before Clinic.",
                "Correct the middle order in one complete sentence and use both neighbouring stops as evidence.",
                "Clinic must come after Library and before Lake, so the note should place Lake fourth rather than third.",
                [
                    _evidence("order", "Places Clinic and Lake in the correct middle positions.", "Clinic must come after Library", "before Lake"),
                    _evidence("answer", "States the exact correction concisely.", "Lake fourth rather than third", "the note should place"),
                ],
                interaction_type="short_text",
                ordered=True,
            ),
        ],
        "review": [
            _task(
                "A seed diary should show soak the beans, wrap them in damp cloth, check for roots, and plant the sprouted beans. The diary puts planting second.",
                "Write a concise correction and explain which two steps must happen before planting.",
                "Planting belongs last because the beans must first be wrapped in damp cloth and checked for roots after soaking.",
                [
                    _evidence("correction", "Moves planting to the final position.", "Planting belongs last", "after soaking"),
                    _evidence("neighbours", "Names the preparation and root-check steps.", "wrapped in damp cloth", "checked for roots"),
                ],
                interaction_type="short_text",
                ordered=True,
            ),
            _task(
                "A relay plan lists warm up, take starting positions, run each leg, exchange the baton, and cool down. One card places cool down before the baton exchange.",
                "Correct the final part in one or two sentences using event purpose.",
                "The runners must exchange the baton during the relay before they cool down, because cooling down belongs after all running legs are complete.",
                [
                    _evidence("sequence", "Places baton exchange before cooling down.", "exchange the baton", "before they cool down"),
                    _evidence("reason", "Uses the end-of-running purpose as evidence.", "after all running legs", "are complete"),
                ],
                interaction_type="short_text",
                ordered=True,
            ),
        ],
    },
    "rainbow_journey_paragraph": {
        "transfer": [
            _task(
                "Journey packet: ferry from the riverside at sunrise; cool spray; gulls above the deck; engine slows near a sandbar; crew follows a marked channel; island library appears; arrival before opening; reflection on patient navigation.",
                "Write an 80- to 100-word first-person journey paragraph with ordered movement, consistent past tense, sensory detail, arrival, and the supplied reflection.",
                "I boarded the ferry at sunrise while cool spray drifted across the riverside. Gulls circled above the deck as the engine carried us toward the island. Near a pale sandbar, the boat slowed, and the crew carefully followed a marked channel through the shallow water. Soon the island library appeared beyond a row of palms. We reached its jetty before the doors opened and waited on the quiet steps. The careful crossing taught me that patient navigation can be more useful than rushing toward a destination.",
                [
                    _evidence("departure", "Begins with the sunrise departure.", "boarded the ferry at sunrise"),
                    _evidence("obstacle", "Includes the response to the sandbar.", "boat slowed"),
                    _evidence("route", "Explains the crew's navigation choice.", "crew carefully followed a marked channel"),
                    _evidence("arrival", "Reaches the island destination.", "reached its jetty before the doors opened"),
                    _evidence("tense", "Keeps completed movement in past tense.", "engine carried us toward the island"),
                    _evidence("sensory", "Includes a specific sensory detail.", "cool spray drifted across the riverside"),
                    _evidence("reflection", "Closes with the supplied navigation reflection.", "patient navigation can be more useful than rushing"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                preflight_rule=JOURNEY_PREFLIGHT,
            ),
        ],
        "review": [
            _task(
                "Draft: 'Yesterday our bus stop near the science fair because a tyre bursts. We wait and reach late.' Notes add a dusty roadside, driver's repair, shared water, fair gates still open, arrival before the first demonstration, and relief.",
                "Revise the draft into an 80- to 100-word first-person journey paragraph with corrected past tense, ordered events, sensory detail, arrival, and reflection.",
                "Yesterday, our bus stopped on a dusty roadside when one tyre burst on the way to the science fair. The driver opened the tool box and repaired it while we shared water in the warm shade. After a short wait, the wheel was ready and we continued through slow morning traffic. The fair gates were still open when we arrived, just before the first demonstration began. I felt relieved and learned that a calm repair and a little patience could rescue an important journey.",
                [
                    _evidence("problem", "States the tyre problem first.", "bus stopped on a dusty roadside when one tyre burst"),
                    _evidence("repair", "Explains the driver's repair.", "driver opened the tool box and repaired it"),
                    _evidence("resumed", "Shows the journey resuming after repair.", "we continued through slow morning traffic"),
                    _evidence("arrival", "Reaches the fair before the demonstration.", "fair gates were still open when we arrived"),
                    _evidence("sensory", "Includes a specific sensory detail.", "shared water in the warm shade"),
                    _evidence("tense", "Keeps completed actions in past tense.", "wheel was ready"),
                    _evidence("reflection", "Closes with a lesson from the delay.", "calm repair and a little patience could rescue an important journey"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                preflight_rule=JOURNEY_PREFLIGHT,
            ),
            _task(
                "Journey packet: overnight train to grandparents' town; dim platform lamps; whistle at departure; rain against the window; tea seller at dawn; river bridge; grandparents waiting; reflection on night changing into morning.",
                "Create an 80- to 100-word first-person journey paragraph that follows the packet in past tense and ends with the supplied reflection.",
                "I boarded the overnight train beneath dim platform lamps and heard its whistle echo as we left the city. Rain tapped the window while dark fields slipped past my seat, and I soon fell asleep. At dawn, a tea seller's call woke me before the train crossed a wide river bridge. Golden light spread across the water as our town came into view. My grandparents waited near the exit when I arrived. Watching the dark journey turn into morning made the familiar visit feel completely new.",
                [
                    _evidence("route", "Orders departure, night travel, dawn, bridge, and arrival.", "boarded the overnight train", "At dawn", "crossed a wide river bridge", "when I arrived"),
                    _evidence("reflection", "Uses sensory details and the night-to-morning idea.", "whistle echo", "Rain tapped", "dark journey turn into morning"),
                ],
                interaction_type="paragraph_text",
                min_words=80,
                preflight_rule=JOURNEY_PREFLIGHT,
            ),
        ],
    },
    "rainbow_natural_and_built": {
        "transfer": [
            _task(
                "Observation card: a flat rock warms naturally in sunlight and cools when shade returns. Design card: a solar cooker uses reflective panels to direct sunlight toward a covered pot. Neither card gives a cooking-time claim.",
                "Write a sourced comparison of heat source and control, then protect the missing timing fact.",
                "Both objects receive heat from sunlight, but the rock warms without a designed purpose while the solar cooker uses reflective panels to direct heat toward a pot. The cards do not state how long cooking takes.",
                [
                    _evidence("comparison", "Compares the shared sunlight and different control.", "Both objects receive heat from sunlight", "reflective panels to direct heat"),
                    _evidence("boundary", "States that cooking time is not supplied.", "do not state how long cooking takes", "cards do not state"),
                ],
            ),
        ],
        "review": [
            _task(
                "Nature card: a termite mound has internal passages that let air move. Building card: a brick ventilation tower is designed with openings that move air through a room. The cards give no temperature measurements.",
                "Compare the airflow feature and mark the missing measurement honestly.",
                "Both structures use openings or passages for airflow, but termites build the mound while people design the brick tower for a room. The cards provide no temperature measurements.",
                [
                    _evidence("features", "States the shared airflow and different makers or settings.", "Both structures use openings", "termites build the mound", "people design the brick tower"),
                    _evidence("limit", "Protects the missing measurement.", "no temperature measurements", "cards provide no"),
                ],
            ),
            _task(
                "Leaf cup card: folded from one large leaf, biodegradable, used once for a snack. Steel bowl card: factory-made, washable, used repeatedly. No cost information is supplied.",
                "Write one similarity, two matched differences, and one source limit.",
                "Both can hold a snack. The leaf cup is made from a biodegradable leaf, whereas the steel bowl is factory-made. The leaf cup is used once, while the washable steel bowl is reusable. The packet does not compare their cost.",
                [
                    _evidence("similarity", "States the shared use.", "Both can hold a snack"),
                    _evidence("material", "Contrasts natural-leaf and factory-made materials.", "leaf cup is made from a biodegradable leaf, whereas the steel bowl is factory-made"),
                    _evidence("reuse", "Contrasts single use and reuse.", "leaf cup is used once, while the washable steel bowl is reusable"),
                    _evidence("limit", "States that cost is unsupported.", "packet does not compare their cost"),
                ],
            ),
        ],
    },
}

for _level_spec in LEVEL_SPECS:
    _expansion = _DEPTH_EXPANSIONS[_level_spec["level_id"]]
    for _phase_name in ("guided", "independent", "transfer"):
        _level_spec[_phase_name].extend(_expansion[_phase_name])
    _launch = _LAUNCH_VARIANTS[_level_spec["level_id"]]
    for _phase_name in ("transfer", "review"):
        _level_spec[_phase_name].extend(_launch[_phase_name])

_journey_gate_count = 0
for _level_spec in LEVEL_SPECS:
    if _level_spec["level_id"] != "rainbow_journey_paragraph":
        continue
    for _phase_name in ("independent", "transfer", "review"):
        for _task_spec in _level_spec[_phase_name]:
            if _task_spec.get("min_words", 0) < 80:
                continue
            _task_spec["preflight_rule"] = JOURNEY_PREFLIGHT
            _journey_gate_count += 1
if _journey_gate_count != 12:
    raise ValueError(f"unexpected_journey_gate_count:{_journey_gate_count}")


MANIFEST = _build_manifest()
