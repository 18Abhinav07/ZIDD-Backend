"""Deep authored manifest for Class 4 English Chapter 7.

The official NCERT extract was used only to map chapter themes, section order,
and exercise forms. All runtime passages, prompts, options, rubrics, and model
answers in this manifest are original Zidd content.

This owned chapter manifest also exposes the small authoring helpers used by
the other Class 4 chapter manifests in the same assigned batch.
"""

from __future__ import annotations

from collections import Counter
import re
from typing import Any

from app.content.school_rebuild_manifests.english.class_5.eng_c5_ch02 import (
    _choice,
    _evidence,
    _level,
    _task,
    _terms,
)
from app.services.school.semantic_evidence import (
    authored_evidence_can_prove_criterion,
)


MANIFEST_SCHEMA_VERSION = "school-class5-deep-manifest-v1"
CORE_ACTORS = ("Zoya", "Milan", "Tara", "Nakul", "Ira")
TRANSFER_ACTORS = ("Farah", "Ketan", "Leela", "Ojas", "Rumi")
PRODUCTIVE_PREFIXES = ("writing.", "speaking.", "oral.")
SEMANTIC_OPEN_SKILLS = {"reading.inference_reason"}
SKILL_DIRECTIONS = {
    "reading.word_meaning_context": "uses nearby clues to explain the key word",
    "vocab.chapter_word_usage": "uses the chapter word with its precise meaning",
    "reading.paragraph_main_idea": "states the central idea rather than one detail",
    "reading.event_sequence": "places the linked events in their supported order",
    "reading.inference_reason": "draws a conclusion from a visible clue",
    "writing.reason_answer": "gives a relevant claim and a because-style reason",
    "grammar.noun_verb_adjective": "identifies or uses the requested word role",
    "writing.complete_sentence": "forms a complete sentence with a clear subject and action",
    "reading.sentence_comprehension": "explains who did what in the sentence",
    "writing.summary_own_words": "summarises only the essential ideas in fresh wording",
    "reading.poetic_language": "interprets the poetic image without making it literal",
    "writing.paragraph": "organises a focused paragraph with linked supporting details",
    "reading.dialogue_attribution": "tracks the speaker and purpose of a dialogue turn",
    "grammar.question_formation": "forms an answerable question with a question mark",
    "grammar.connectors_because_and_but": "uses a connector that matches reason or contrast",
    "writing.procedure": "presents materials and actions in a usable order",
    "grammar.tense_usage": "uses a verb tense that matches the time clue",
    "writing.compare_contrast": "states a matched similarity and difference",
    "grammar.prepositions": "uses a position or direction word accurately",
    "vocab.spelling": "recognises and produces the intended spelling pattern",
    "grammar.pronouns": "links each pronoun to a clear noun",
    "writing.dialogue": "writes connected turns with clear speakers and punctuation",
    "research.information_selection": "reports only facts stated in the fact card",
    "grammar.sentence_order": "orders words and articles into a meaningful sentence",
    "grammar.punctuation_capitalization": "uses capitals and punctuation to preserve meaning",
    "vocab.word_formation": "builds a related word and checks its meaning in context",
}

SKILL_DIRECTIONS_B = {
    "reading.word_meaning_context": "explain the target word using nearby clues",
    "vocab.chapter_word_usage": "use the chapter word in a situation that fits",
    "reading.paragraph_main_idea": "tell the main idea of the whole story",
    "reading.event_sequence": "put the events in the correct order",
    "reading.inference_reason": "explain a conclusion using the result in the story",
    "writing.reason_answer": "join a clear answer to a story-based reason",
    "grammar.noun_verb_adjective": "use the requested word type accurately",
    "writing.complete_sentence": "write a complete thought with a subject and action",
    "reading.sentence_comprehension": "name the actor, action, and result",
    "writing.summary_own_words": "retell the important facts in fresh wording",
    "reading.poetic_language": "explain what the comparison means",
    "writing.paragraph": "develop one idea in a linked paragraph",
    "reading.dialogue_attribution": "track who asks and who gives the fact",
    "grammar.question_formation": "write a clear question that can be answered",
    "grammar.connectors_because_and_but": "choose a connector for a reason or contrast",
    "writing.procedure": "write usable steps with a safety rule",
    "grammar.tense_usage": "match the verb form to the time clue",
    "writing.compare_contrast": "state one fair likeness and one difference",
    "grammar.prepositions": "place the object with an exact position word",
    "vocab.spelling": "write the intended letter pattern",
    "grammar.pronouns": "connect each pronoun to a clear noun",
    "writing.dialogue": "write linked speaker turns with punctuation",
    "research.information_selection": "keep the stated facts and leave out guesses",
    "grammar.sentence_order": "arrange the words and articles clearly",
    "grammar.punctuation_capitalization": "mark sentence boundaries and names correctly",
    "vocab.word_formation": "build a related word that keeps the intended meaning",
}

FRESH_PHASE_RANGES = {
    "independent": (0, 4),
    "transfer": (4, 8),
    "review": (8, 12),
    "support": (12, 17),
}

# Each tuple contains a unique label, setting, preparation, action, result,
# useful word, and context meaning. Assessment stories use a separate bank.
FRESH_TEACHING_SCENES = {
    "eng_c4_ch07": (
        ("orchard stretch chart", "school orchard", "marked three gentle stretches", "led a slow warm-up under the trees", "the group began its walk without stiff legs", "steady", "controlled and even"),
        ("canal path walk", "canal-side path", "filled two water bottles", "kept a comfortable pace between shade stops", "every walker returned with energy left", "moderate", "neither too hard nor too easy"),
        ("courtyard balance circuit", "brick courtyard", "placed chalk lines and soft rings", "mixed balancing steps with short rests", "each child finished the circuit safely", "balanced", "including different needs in fair amounts"),
        ("breakfast energy plan", "morning activity room", "chose fruit and warm porridge", "waited before joining a skipping game", "the first round felt active but comfortable", "nourishing", "helpful for healthy growth and energy"),
        ("hill picnic pace", "low picnic hill", "checked the shaded turns", "shortened each climb and paused at benches", "younger cousins reached the top smiling", "gradual", "changing in small steps"),
        ("rain hall movement", "covered community hall", "cleared bags from the floor", "changed an outdoor race into calm movement stations", "the wet day still included safe exercise", "adaptable", "able to change for new conditions"),
        ("family chore rhythm", "shared apartment landing", "divided sweeping and watering jobs", "worked in ten-minute turns with breathing breaks", "the chores ended without anyone becoming exhausted", "rhythm", "a regular pattern of action and pause"),
        ("bus-stop movement plan", "covered bus terminal", "checked that the walking lane was clear", "used calf raises and shoulder rolls beside the bench", "the wait included safe movement without blocking travellers", "practical", "suited to a real need or situation"),
        ("seated ribbon routine", "inclusive activity room", "set chairs in a wide circle and handed out soft ribbons", "completed arm patterns with seated and standing choices", "every participant followed a suitable movement sequence", "accessible", "easy for people with different needs to use"),
        ("homework stretch timer", "quiet study corner", "set a twenty-minute reading timer", "stood and stretched between two study sections", "the next page began with renewed attention", "refresh", "restore energy or attention after effort"),
        ("sunrise breathing pause", "quiet terrace", "watched the sky brighten", "counted four slow breaths after each movement", "her heartbeat settled before the next set", "recover", "return to a comfortable state"),
        ("inclusive beanbag station", "neighbourhood play court", "set seated and standing targets", "offered each child a suitable throwing line", "everyone completed a fair challenge", "inclusive", "welcoming people with different needs"),
        ("garden hose warm-up", "kitchen garden", "coiled the hose away from the path", "reached and bent before carrying watering cans", "no one stumbled over the work area", "careful", "acting with attention to safety"),
        ("ferry queue posture", "river ferry shelter", "placed a light bag on both shoulders", "stood upright instead of leaning on one rail", "the wait ended without an aching back", "upright", "straight rather than bent"),
        ("library stair break", "public library stairs", "noticed a younger child breathing quickly", "stopped at the landing and shared water", "both climbed the final steps calmly", "considerate", "noticing and helping another person's needs"),
        ("rooftop kite recovery", "safe rooftop court", "checked the boundary rope", "rested after several turns of pulling the kite line", "his hands relaxed before the next flight", "pause", "a short stop before continuing"),
        ("market basket carry", "weekly vegetable market", "split vegetables between two small baskets", "changed hands at each lane corner", "the load stayed comfortable all the way home", "manageable", "easy enough to handle safely"),
    ),
    "eng_c4_ch08": (
        ("courtyard cone builders", "community courtyard", "sorted cones by colour", "rebuilt a low target while teammates guarded the lane", "the round ended after the last cone stood", "coordinate", "arrange connected jobs"),
        ("beanbag boundary round", "school play square", "drew a wide throwing line", "used gentle underarm throws toward cloth targets", "no throw crossed into the waiting area", "boundary", "a marked limit around a space"),
        ("captain signal practice", "youth-club court", "agreed on three short calls", "used one call each for pass, rebuild, and stop", "players changed roles without confusion", "signal", "a sign or sound that gives a message"),
        ("fair turn ladder", "festival game stall", "wrote every player's name once", "followed the list before allowing repeat turns", "all teammates tried the challenge", "rotation", "an order in which turns come around"),
        ("indoor tower transfer", "rainy recreation room", "replaced stones with foam blocks", "rolled a soft ball instead of throwing it", "the changed game kept its teamwork goal", "adapt", "change something to fit new conditions"),
        ("beach marker rescue", "clean sandy beach", "placed shells outside the play lane", "restacked driftwood pieces after a rolling-ball hit", "the team completed the goal without sharp objects", "retrieve", "bring something back"),
        ("park score tokens", "public park circle", "set two bowls beside the scorer", "moved one wooden token after each completed rebuild", "both teams could see the correct total", "transparent", "easy for everyone to see and understand"),
        ("terrace chalk-stack game", "apartment terrace court", "replaced hard stones with chalk-marked foam cups", "rolled a cloth ball toward the low stack", "the adapted round kept its rebuilding goal without hard equipment", "modify", "change part of something for a new need"),
        ("captain handover round", "school courtyard", "placed three coloured role bands beside the teams", "passed the captain band to a new player after each turn", "every teammate practised giving one clear direction", "rotate", "move turns through a repeating order"),
        ("rain-score replay", "covered veranda", "kept the score card from an interrupted round", "replayed one disputed point under a single agreed rule", "both teams accepted the corrected total", "resolve", "settle a disagreement with a clear solution"),
        ("quiet referee question", "sports-day practice", "noticed two stop calls at once", "asked which signal should end the turn", "the referee explained one clear restart rule", "clarify", "make an idea easier to understand"),
        ("teamwork recap board", "class notice corner", "selected only the decisive match moments", "linked the thrower's aim with the builder's quick work", "the short recap explained the shared success", "cooperation", "people working toward one result"),
        ("rope lane repair", "playground side court", "found one loose corner marker", "retied the rope before the next throw", "players could judge the safe lane clearly", "secure", "fixed firmly in place"),
        ("soft disc sorting", "after-school equipment room", "counted discs and cloth bands", "placed each set in a labelled basket", "the next group found every item quickly", "organise", "put things into a useful order"),
        ("waiting zone lesson", "apartment play area", "saw children crowd behind the thrower", "marked a separate line for the next pair", "the active lane remained clear", "distance", "space between people or things"),
        ("shared strategy cards", "library activity table", "gave each role one small card", "combined the defender and builder suggestions", "the new plan used both useful ideas", "consensus", "agreement reached by a group"),
        ("sunset equipment check", "village open ground", "counted all markers before dusk", "matched each object with a chalk outline", "nothing was left on the field", "complete", "having every needed part"),
    ),
    "eng_c4_ch09": (
        ("linked ribbon circle", "school lawn", "tied coloured bands loosely at each wrist", "held a wide shape while challengers tested openings", "the circle stayed connected without pulling", "formation", "an arranged shape made by a group"),
        ("safe surrender round", "community game court", "reviewed the stop word", "used it as soon as three defenders closed the space", "the next challenger entered without argument", "surrender", "yield and stop resisting"),
        ("boundary guard drill", "marked grass square", "checked the corner lines", "moved sideways to close an open gap", "the challenger turned away before crossing", "defend", "protect a place from an opponent"),
        ("recovery token rule", "club practice yard", "placed two rest tokens by each team", "spent one token after a tiring round", "later turns showed controlled movement", "recover", "regain strength after effort"),
        ("museum floor challenge", "wide museum classroom", "used fabric loops instead of linked arms", "guided the group around a marked display zone", "the adapted contest protected the exhibits", "restraint", "control that prevents excessive force"),
        ("snow camp ring game", "winter camp hall", "laid a circle with bright tape", "used walking steps on the slippery floor", "players kept the strategy without unsafe speed", "cautious", "careful to avoid danger"),
        ("family picnic contest", "shaded picnic ground", "mixed adults and children across teams", "shortened each round to one minute", "the score remained close and fair", "balanced", "fairly shared between sides"),
        ("foam-link circle", "recreation hall", "gave each player one short foam link", "formed a wide ring without gripping another person's arm", "the group practised the same defence with safer spacing", "adapt", "change a rule or tool to fit new conditions"),
        ("tag-count evidence", "school court notebook", "marked every legal touch in a numbered table", "compared the referee's call with the written marks", "the captain accepted the corrected point total", "verify", "check a claim against reliable evidence"),
        ("captain-turn rotation", "community lawn", "listed three callers before the match", "changed the caller after each completed round", "quieter players also guided the formation", "leadership", "helping a group move toward a shared goal"),
        ("inside outside recap", "classroom floor grid", "placed blue cards inside and yellow cards outside", "moved each role only when its rule allowed", "the final diagram showed both jobs correctly", "role", "the job a person has in an activity"),
        ("captain choice review", "sports journal table", "compared two completed rounds", "linked a patient caller with fewer broken chains", "the written reason matched the observed change", "evidence", "a detail that supports an idea"),
        ("chalk gap repair", "neighbourhood court", "noticed rain had erased one line", "redrew the gap before arranging teams", "no player disputed the boundary", "restore", "bring something back to its proper condition"),
        ("whistle meaning check", "youth-centre yard", "heard one long signal", "stopped movement and waited for instructions", "the round restarted only after the all-clear", "signal", "a sound that gives a message"),
        ("equal entry list", "school games board", "listed all challengers in order", "crossed off each name after one turn", "every player entered before anyone repeated", "rotate", "take turns in a repeating order"),
        ("water break redesign", "summer practice ground", "noticed shade shrinking near noon", "added a drink pause after each pair of rounds", "players stayed alert through the final game", "revise", "change a plan to improve it"),
        ("quiet strength station", "indoor activity room", "placed thick mats around the circle", "practised firm stances without pushing", "the class learned control before competition", "stability", "the quality of staying firm and balanced"),
    ),
    "eng_c4_ch10": (
        ("terrace hammock view", "garden terrace", "checked both cloth loops", "moved gently above rows of herbs", "new rooftops appeared beyond the wall", "sway", "move smoothly from side to side"),
        ("train window motion", "slow hill train", "chose a seat facing the valley", "watched nearby poles seem to hurry backward", "distant fields appeared almost still", "perspective", "the way a view changes from one position"),
        ("kite platform pause", "low observation platform", "held the rail before looking up", "followed a kite from trees to open sky", "the wider view made its path easy to trace", "distant", "far away from the viewer"),
        ("porch chair rhythm", "grandparent's porch", "set both feet on the footrest", "rocked in small even arcs", "the quiet motion felt calm and safe", "rhythmic", "following a repeated beat or pattern"),
        ("boat deck viewpoint", "lake ferry deck", "stood behind the yellow line", "compared reeds nearby with hills across the water", "the far hills seemed smaller", "horizon", "the line where land or water appears to meet the sky"),
        ("forest rope seat", "nature camp clearing", "tested a low rope seat", "swung only between two marked posts", "leaves above changed shape with each arc", "arc", "a curved path"),
        ("wheelchair garden route", "sensory garden", "chose a level viewing place", "rolled from the fountain toward taller flowers", "the changing height of plants altered the view", "glide", "move smoothly without sudden stops"),
        ("hill-bus window view", "seated hill shuttle", "chose a window seat behind the safety line", "compared nearby guardrails with farms across the valley", "the near rails seemed to pass faster than the distant fields", "relative", "judged by comparison with something else"),
        ("camera-step viewpoint", "school courtyard photo walk", "marked two safe standing spots", "photographed the same tree from a low step and the far gate", "the tree filled different amounts of each picture", "viewpoint", "the position from which something is seen"),
        ("roundabout dismount", "accessible playground roundabout", "held the centre rail as the platform slowed", "waited until the platform stopped before releasing the rail", "both feet reached stable ground without a jump", "stationary", "not moving"),
        ("moonlit balcony recap", "apartment balcony", "noticed a still moon above moving clouds", "compared what moved with what stayed fixed", "the explanation separated real and apparent motion", "contrast", "a clear difference between things"),
        ("safe dismount review", "playground swing bay", "waited through three smaller arcs", "placed both feet down before releasing the ropes", "the seat stopped without a jump", "gradual", "happening in small stages"),
        ("breeze ribbon check", "school garden gate", "tied a ribbon below the sign", "watched it bend toward the east", "the cloth showed the wind's direction", "direction", "the way something points or travels"),
        ("bench position map", "riverside park", "marked the gate and fountain", "placed the bench between a tree and the path", "a visitor followed the map without help", "beside", "at the side of something"),
        ("cloud boat comparison", "open reading yard", "watched one long cloud cross the sun", "compared its slow travel with a quiet boat", "the image created a peaceful mood", "drift", "move slowly without a fixed path"),
        ("rope wear decision", "community play corner", "found a rough strand near the hook", "closed the seat and told the caretaker", "no one used it before repair", "frayed", "worn into loose threads"),
        ("pendulum count", "science activity table", "pulled a small weight to one side", "counted each return through the centre", "the repeated motion made an even pattern", "interval", "the space or time between repeated events"),
    ),
    "eng_c4_ch11": (
        ("pine trail shelter", "lower pine trail", "packed a rain layer and route card", "followed blue markers to a roofed rest place", "the group arrived before the shower", "shelter", "a place that gives protection"),
        ("ridge water plan", "sunny ridge path", "counted bottles before climbing", "shared small drink stops at marked bends", "enough water remained for the descent", "ration", "a carefully limited share"),
        ("stream bridge choice", "forest stream", "noticed wet stones below fast water", "used the railed footbridge upstream", "everyone crossed with dry shoes", "cautious", "careful to avoid a risk"),
        ("valley echo note", "open valley ledge", "stood inside the safety line", "called once and timed the returning sound", "the echo arrived from the opposite slope", "echo", "a sound heard again after reflection"),
        ("desert hill transfer", "dry sandstone hill", "covered water and checked the map", "chose the gentler shaded route", "the walkers reached camp without overheating", "terrain", "the natural shape and surface of land"),
        ("coastal cliff walk", "marked sea-cliff path", "read the wind warning", "stayed behind the low barrier", "the group viewed nesting birds from a safe distance", "exposed", "open to strong weather or danger"),
        ("city stair trek", "historic tower stairs", "divided a heavy bag", "paused at every second landing", "all visitors reached the lookout together", "endurance", "ability to continue through effort"),
        ("mangrove boardwalk route", "coastal nature reserve", "checked the tide notice and boardwalk arrows", "followed the raised path around the wet roots", "the group reached the bird hide without entering the mud", "habitat", "the natural home of plants or animals"),
        ("rockfall detour record", "foothill trail junction", "read a fresh closure sign beside the upper path", "followed the mapped lower detour", "the walkers reached camp without entering the closed slope", "detour", "a different route around a blocked way"),
        ("erosion step choice", "hill path repair day", "noticed a shortcut cutting through loose soil", "placed guide stones along the existing steps", "walkers stayed on the firm route and new plants remained undisturbed", "erosion", "the gradual wearing away of soil or rock"),
        ("turnaround time review", "mountain checkpoint", "compared the clock with the route card", "started down instead of chasing the summit", "the party reached the gate before dark", "wise", "showing careful judgement"),
        ("wildflower path recap", "alpine meadow edge", "saw a shortcut through blooms", "kept to the stone-marked trail", "the plants remained untouched", "preserve", "keep something safe from harm"),
        ("fog marker search", "misty woodland slope", "lost sight of the next post", "returned to the last clear arrow", "the guide found the route without guessing", "bearing", "a direction used for travel"),
        ("shared pack lesson", "rocky camp approach", "noticed one walker slowing", "moved light items into two other bags", "the group regained an even pace", "load", "weight carried by a person"),
        ("litter carryback", "hilltop lunch place", "counted wrappers before leaving", "sealed every scrap in a reusable pouch", "the ground looked as clean as before", "responsible", "taking care of duties and effects"),
        ("goat crossing wait", "narrow mountain bend", "spotted goats above the path", "stood quietly at a wider point", "the animals crossed without being chased", "patient", "able to wait calmly"),
        ("contour route choice", "map-reading room", "compared close and wide contour lines", "traced a longer route around the steep face", "the plan reduced the climb's sharpness", "gradient", "the steepness of a slope"),
    ),
    "eng_c4_ch12": (
        ("stepwell inscription visit", "old stepwell court", "read a translated stone note", "kept hands away from the carved letters", "the worn message stayed protected", "inscription", "words cut into a hard surface"),
        ("weaving hall border", "craft learning hall", "compared cotton and silk threads", "traced the same pattern on both cloth faces", "the border looked complete from either side", "reversible", "usable or visible on both sides"),
        ("river gate route", "historic riverside gate", "checked the visitor map", "walked from the arch to the landing in order", "the group found the exit without crossing a closed court", "heritage", "valued places and traditions passed through time"),
        ("granary airflow clue", "stone storage room", "noticed narrow openings near the roof", "linked them with the cool moving air", "the grain area stayed dry", "ventilation", "movement of fresh air through a place"),
        ("village kiln transfer", "pottery workshop", "shaped a small clay bowl", "watched it harden inside a heated chamber", "the finished bowl held water", "kiln", "an oven used for firing clay"),
        ("canal bridge survey", "old canal crossing", "counted three curved supports", "matched each arch with the stones above it", "the sketch explained how the bridge carried weight", "arch", "a curved structure spanning an opening"),
        ("indigo dye register", "weaving cooperative", "read two dated plant-dye recipes", "matched a blue cloth sample with the recorded mixture", "the sample card preserved the method for future weavers", "record", "a written account kept for later use"),
        ("audio guide fact check", "heritage museum", "compared a guide script with the object's label", "removed an unsupported royal-owner claim", "the revised guide kept only verified information", "authentic", "genuine and supported by reliable evidence"),
        ("rain-spout route", "fort courtyard", "marked a carved stone spout on the plan", "followed its channel from the roof to a garden tank", "the notes explained how rainwater moved through the building", "channel", "a passage that carries water in a direction"),
        ("market clock timeline", "town clock square", "ordered three repair dates", "connected the newest date with a replaced hand", "the timeline showed the latest change", "chronology", "events arranged by time"),
        ("museum label review", "local history room", "compared an object with its card", "removed an invented owner's name", "the corrected label kept only known facts", "accurate", "correct and supported by facts"),
        ("courtyard article recap", "fort courtyard", "introduced an iron bell and a stone seat", "used the for each known object later", "the paragraph kept every reference clear", "specific", "clearly identified rather than general"),
        ("mural distance rule", "painted temple passage", "noticed colour flakes below one wall", "stood behind the viewing line", "the fragile surface remained untouched", "conserve", "protect something from loss or damage"),
        ("archive page order", "district archive room", "cleared a padded table", "numbered each page before closing the folder", "no sheet was returned out of order", "sequence", "an arrangement from first to last"),
        ("ferry fare ledger", "river museum desk", "read one dated list of fares", "separated written amounts from a visitor's guess", "the summary reported only documented travel costs", "source", "a place where information comes from"),
        ("carved lintel cleaning", "heritage doorway", "read the caretaker's soft-brush rule", "lifted loose dust without scraping", "the shallow design remained visible", "delicate", "easily damaged and needing care"),
        ("memorial garden route", "public memorial garden", "started beside the stone map", "visited the plaque and tree circle before the arch", "the written route ended at the correct exit", "landmark", "a noticeable place used for finding a route"),
    ),
}

CHAPTER_ASSESSMENT_SCENES = {
    "eng_c4_ch07": {
        "a": (
            ("community walking log", "Anaya", "checked the route markers", "kept an even pace through every lane", "the group finished together without rushing"),
            ("school activity timetable", "Kabir", "listed movement and rest periods", "balanced games with quiet recovery", "the plan supported both energy and concentration"),
            ("table-tennis practice", "Mehul", "warmed his shoulders and wrists", "repeated a controlled return drill", "his final returns landed inside the marked zone"),
            ("playground shade break", "Raina", "noticed two tired teammates", "moved the next round into a cooler area", "both players completed the session comfortably"),
            ("cycling safety card", "Tanu", "examined a bright fitted helmet", "described the careful rider beside it", "the sentence matched each adjective to the correct noun"),
            ("balanced school-day diary", "Dev", "walked before lessons", "combined an evening game with a short rest", "homework began with calm attention"),
            ("movement-rhyme planner", "Lina", "marked the beat in a short verse", "linked lively movement with water pauses", "the final plan joined activity and recovery"),
            ("campus hydration board", "Asha", "counted empty bottles after lunch", "added two refill pauses to the activity chart", "the afternoon group returned with enough water"),
            ("posture warm-up clinic", "Ritesh", "noticed stiff shoulders before badminton", "demonstrated slow circles and an upright stance", "the class began play with freer movement"),
            ("weekend recovery chart", "Mira", "compared two busy family plans", "moved one long game away from the hottest hour", "the revised day included effort, shade, and rest"),
            ("playground pulse note", "Zoya", "measured her heartbeat after skipping", "waited until her breathing became steady", "the next round started only after recovery"),
            ("fruit-snack record", "Arun", "read the labels on two snack boxes", "chose fruit and water before practice", "he completed the drill without an early energy drop"),
            ("stair-climb pacing trial", "Sana", "marked three pause points on the route", "climbed at a talkable pace instead of racing", "every participant reached the top comfortably"),
            ("sleep-readiness log", "Farah", "recorded five late bedtimes", "shifted homework and screens earlier", "morning stretching began with better attention"),
            ("inclusive station circuit", "Nikhil", "checked what each classmate could do safely", "offered seated throws beside standing jumps", "everyone completed a suitable movement station"),
        ),
        "b": (
            ("garden-work record", "Bina", "set tools in a steady row", "worked at the same controlled speed", "every bed was ready before the heat increased"),
            ("family weekend chart", "Rohit", "grouped errands and free time", "placed cycling between study and rest", "the day included effort, enjoyment, and recovery"),
            ("dance-rehearsal sheet", "Hema", "cleared the floor and stretched", "practised turns before the full pattern", "the group cooled down after the final run"),
            ("morning-focus note", "Ishan", "ended screen time early", "slept before the next day's practice", "he followed every instruction attentively"),
            ("park-poster sentence", "Noor", "selected the noun runner", "added the adjective patient and the verb waited", "the completed line described the scene precisely"),
            ("rainy-day routine", "Gopal", "moved chairs from the centre", "completed a gentle indoor circuit", "slow breathing ended the active session"),
            ("river-motion paragraph", "Jaya", "interpreted a smooth-flowing comparison", "connected it with warm-up and teamwork", "the closing sentence explained the benefit of rest"),
            ("shaded-break schedule", "Leela", "found that the court stayed hot after noon", "placed shorter rounds between shaded pauses", "the team maintained a comfortable pace"),
            ("breathing-recovery card", "Sameer", "finished a fast shuttle run", "counted slow breaths before drinking water", "his pulse settled before the next task"),
            ("helmet-fit checklist", "Pooja", "tested a loose cycling strap", "adjusted it until two fingers fit beneath", "the helmet stayed level during the practice ride"),
            ("screen-balance diary", "Imran", "noticed tired eyes before evening play", "replaced one video period with a short walk", "he arrived at practice alert and ready"),
            ("morning-stretch sequence", "Kavya", "cleared a quiet floor space", "reached, bent, rotated, and relaxed in order", "the routine ended without hurried movement"),
            ("team-encouragement note", "Manav", "heard a player worry about missing a catch", "praised the effort and suggested one calm retry", "the player rejoined with confidence"),
            ("neighbourhood walking map", "Diya", "compared a steep lane with a level path", "selected the safer route and marked a water stop", "the family completed the walk before dusk"),
            ("weekly habit reflection", "Omar", "reviewed movement, meals, sleep, and study", "changed one crowded day instead of every routine", "the new plan remained practical for a full week"),
        ),
    },
    "eng_c4_ch08": {
        "a": (
            ("foam-target practice", "Anaya", "read the role cards", "helped rebuild a low target", "the team understood the builder's responsibility"),
            ("captains' planning talk", "Kabir", "asked how both sides could improve", "recorded each captain's reply", "the exchange showed that teamwork guided the match"),
            ("marker-stack round", "Mehul", "chalked a safe throwing line", "knocked down and rebuilt three soft markers", "the referee ended the round after the rebuild"),
            ("defence-change record", "Raina", "noticed an unguarded target", "asked one player to protect the stack", "the next gentle throw was stopped"),
            ("referee-question card", "Tanu", "studied a delayed stop signal", "formed a question about the restart", "the capital letter and question mark made the request clear"),
            ("neighbourhood match report", "Dev", "tracked a close final round", "kept only the decisive actions", "the summary explained how cooperation secured the finish"),
            ("soft-disc challenge", "Lina", "counted foam discs and cones", "ordered setup, play, and scoring steps", "the procedure included a clear stop rule"),
            ("beanbag-accuracy lane", "Asha", "placed three low targets at different distances", "tested underarm throws from the nearest line first", "the group chose a fair starting distance"),
            ("court-boundary repair", "Ritesh", "found a broken chalk corner", "remeasured the side and redrew the missing angle", "both teams could judge in-bounds throws clearly"),
            ("turn-rotation chart", "Mira", "noticed two players taking repeated turns", "numbered the order and added a waiting zone", "every teammate received one attempt before repeats"),
            ("score-dispute record", "Zoya", "collected the referee and scorer notes", "matched the signal time with the written total", "the corrected score used agreed evidence"),
            ("safe-throw workshop", "Arun", "saw a hard throw pass near a face", "lowered the target and required gentle underarm action", "practice continued without risky contact"),
            ("team-signal rehearsal", "Sana", "listed three confusing calls", "assigned one short word to pass, rebuild, and stop", "players responded to each instruction consistently"),
            ("equipment-return check", "Farah", "counted cones before dismissal", "matched each item with its storage outline", "nothing remained on the playing surface"),
            ("rain-adapted game plan", "Nikhil", "lost access to the outdoor court", "replaced long throws with floor rolls indoors", "the changed rules preserved teamwork and safety"),
        ),
        "b": (
            ("community game desk", "Bina", "compared attacker and defender cards", "identified the referee's duty", "every role was used correctly in a new round"),
            ("strategy-timeout dialogue", "Rohit", "asked why the stack stayed open", "linked two teammates' answers", "the conversation developed a shared defence plan"),
            ("beanbag-tower contest", "Hema", "placed a boundary rope", "tossed, retrieved, and restacked in sequence", "the score was recorded only after play stopped"),
            ("wide-pass decision", "Ishan", "saw defenders crowd one lane", "sent the soft ball toward an open teammate", "the target became reachable without unsafe contact"),
            ("scorekeeper interview", "Noor", "reviewed a disputed point", "wrote an answerable question for the official", "the final sentence used correct capitals and punctuation"),
            ("festival game recap", "Gopal", "noted two fair-play moments", "removed minor crowd details", "the short report preserved the match result and message"),
            ("ring-and-cone relay", "Jaya", "gathered rings, cones, and a signal card", "wrote ordered turns and a walking limit", "another group could follow the safe procedure"),
            ("captain-handover note", "Leela", "read the first captain's unfinished plan", "added the missing defender role before taking charge", "the team changed leaders without losing its strategy"),
            ("spectator-zone layout", "Sameer", "saw viewers standing beside the throwing line", "moved the rope behind a marked waiting strip", "players gained a clear and protected lane"),
            ("restart-after-foul card", "Pooja", "recorded where play stopped", "returned the marker stack before signalling a restart", "both sides resumed from the same agreed condition"),
            ("paired-aiming drill", "Imran", "compared one rushed throw with one planned throw", "asked partners to point, pause, and release", "accuracy improved without increasing force"),
            ("fair-team selection", "Kavya", "listed each player's experience", "distributed skilled builders and throwers across both groups", "the opening round began with balanced teams"),
            ("timeout-planning board", "Manav", "noticed teammates speaking over one another", "gave each role ten seconds to report", "the revised plan included every useful observation"),
            ("damaged-ball replacement", "Diya", "found a foam ball split along one edge", "removed it and checked a softer spare", "the match continued with usable equipment"),
            ("newcomer instruction card", "Omar", "watched a learner miss the rebuild rule", "wrote one setup example and one scoring example", "the newcomer completed the next turn independently"),
        ),
    },
    "eng_c4_ch09": {
        "a": (
            ("circle-role briefing", "Anaya", "read the inside and outside cards", "matched each role with its objective", "the new players entered with clear responsibilities"),
            ("fair-strength meeting", "Kabir", "listed stop and surrender rules", "connected each limit to controlled play", "the central message favoured skill with restraint"),
            ("boundary-round record", "Mehul", "marked one entry point", "tracked entry, surround, surrender, and exit", "a replacement entered only after the captured player left"),
            ("space-making strategy", "Raina", "noticed crowding near the line", "delayed one challenger for five seconds", "the next entry happened through a clear lane"),
            ("yesterday's match note", "Tanu", "underlined the time clue", "changed enter and surround into past forms", "the completed sentences matched the finished match"),
            ("safe-contest summary", "Dev", "selected boundary and point facts", "combined them without copying the record", "the recap explained how the result was decided"),
            ("entry-rule redesign", "Lina", "gathered bands, rope, and a whistle", "placed a one-player limit at the opening", "the procedure used because to explain reduced contact"),
            ("centre-entry timing", "Asha", "watched two challengers approach together", "held the second player behind a count line", "only one person entered the circle at a time"),
            ("touch-verification note", "Ritesh", "heard opposite claims about one tag", "compared the boundary judge and scorer records", "the accepted point followed matching evidence"),
            ("chalk-circle inspection", "Mira", "found one side narrowed by footsteps", "measured and restored the full curve", "defenders began with equal space around the centre"),
            ("defender-rotation plan", "Zoya", "noticed the same learner guarding every round", "moved roles clockwise after each stop", "all team members practised defence and recovery"),
            ("surrender-signal trial", "Arun", "saw a tired player wave without being noticed", "introduced a raised-band signal and immediate pause", "the player left safely before a replacement entered"),
            ("scorekeeper token record", "Sana", "separated valid entries from practice attempts", "placed one dated token for each counted point", "the final total could be checked by both teams"),
            ("controlled-restart drill", "Farah", "marked where contact had stopped play", "returned everyone to a spaced starting position", "the next entry began after the whistle"),
            ("alternate-rule pilot", "Nikhil", "identified crowding near the centre", "tested a wider gate for three rounds", "recorded observations showed fewer collisions"),
        ),
        "b": (
            ("team-role station", "Bina", "examined challenger and defender badges", "used surrender in a new explanation", "the role vocabulary remained precise"),
            ("rules-and-purpose board", "Rohit", "grouped scoring and safety facts", "compared strong play with agreed limits", "the whole display explained fair competition"),
            ("token-scoring trial", "Hema", "set the boundary before play", "added one token after each valid objective", "the final total was checked after the stop signal"),
            ("recovery-zone test", "Ishan", "saw a tired player surrender", "directed that player to a marked rest space", "the replacement entered while recovery stayed protected"),
            ("completed-game report", "Noor", "circled yesterday and last", "wrote past-tense actions beside them", "the timeline stayed consistently in the past"),
            ("community demonstration recap", "Gopal", "watched safe entries and clear exits", "kept only result-changing actions", "the summary described controlled strength and scoring"),
            ("visible-score procedure", "Jaya", "prepared tokens and a result board", "added an ordered recording step", "players accepted the total because every point was visible"),
            ("narrow-court adaptation", "Leela", "measured a smaller indoor floor", "reduced team size and shortened the entry lane", "the game kept its objective without unsafe crowding"),
            ("mixed-age turn chart", "Sameer", "compared the reach of younger and older players", "alternated challengers and adjusted the waiting line", "each age group received a workable turn"),
            ("disputed-tag review", "Pooja", "paused after two judges disagreed", "replayed the written sequence from entry to exit", "the round was reset instead of awarding a guessed point"),
            ("balance-challenge station", "Imran", "noticed fast entries causing slips", "required a controlled stop on a floor marker", "players demonstrated balance before scoring"),
            ("timeout-signal card", "Kavya", "heard several informal calls for rest", "selected one visible hand sign and one whistle pattern", "every participant recognised the pause immediately"),
            ("fairness-redesign meeting", "Manav", "found that one role earned every point", "added a defender objective and rotated starts", "both roles could now influence the result"),
            ("final-round chronology", "Diya", "received six shuffled event notes", "ordered entry, surround, signal, exit, and replacement", "the score line appeared only after the completed sequence"),
            ("equipment-free practice", "Omar", "lost the coloured team bands", "used numbered role cards at the waiting area", "players still identified responsibilities before entering"),
        ),
    },
    "eng_c4_ch10": {
        "a": (
            ("garden-swing word card", "Anaya", "watched a seat move gently", "linked sway with side-to-side motion", "the word fit the visible movement"),
            ("high-view poem note", "Kabir", "marked a bird-like comparison", "connected height with a wider view", "the image expressed freedom rather than literal flight"),
            ("playground motion log", "Mehul", "checked the ropes and cleared the path", "pushed, rose, returned, and slowed", "the rider stepped off only after the seat stopped"),
            ("nervous-rider record", "Raina", "held the ropes before the first arc", "began with smaller movements", "confidence increased as each return stayed controlled"),
            ("noun-and-verb display", "Tanu", "labelled child and swing as nouns", "used climbed and moved as verbs", "the final sentence communicated one complete event"),
            ("viewpoint journal", "Dev", "noticed roofs above the hedge", "combined the changing view with the rider's feeling", "the summary kept both motion and perspective"),
            ("park-layout paragraph", "Lina", "placed a bench beside the path", "located the swing between two trees", "linked position details supported one clear description"),
            ("platform-view journal", "Asha", "climbed a low observation deck", "compared the near garden with the distant road", "the entry explained how height changed perspective"),
            ("breeze-direction flag", "Ritesh", "watched a ribbon point east", "linked the steady pull with the moving air", "the note distinguished wind direction from object colour"),
            ("rope-inspection card", "Mira", "found one strand rough near the hook", "closed that seat and reported the wear", "no rider used the swing before repair"),
            ("pendulum-timing trial", "Zoya", "marked the seat at its centre point", "counted equal returns during ten seconds", "the chart represented repeated motion accurately"),
            ("cloud-comparison line", "Arun", "saw a white cloud drift beyond the frame", "compared it with a slow boat crossing open water", "the image communicated calm movement"),
            ("quiet-park description", "Sana", "listed a still bench, moving leaves, and empty path", "selected details that shared one evening mood", "the paragraph stayed focused on peaceful change"),
            ("motion-sentence expansion", "Farah", "began with the words The seat moved", "added direction, speed, and a visible cause", "the expanded sentence remained complete and clear"),
            ("safe-dismount sequence", "Nikhil", "noticed the seat still travelling forward", "waited through smaller arcs and planted both feet", "he released the ropes only after stopping"),
        ),
        "b": (
            ("hammock-motion record", "Bina", "observed a gentle backward move", "used glide for smooth travel", "the context clue fixed the movement word"),
            ("cloud-window verse", "Rohit", "underlined a floating-road image", "explained the changing sky view", "the poetic line suggested wonder and height"),
            ("rope-seat safety sequence", "Hema", "inspected the knot and landing space", "sat, moved, slowed, and waited", "she left the seat after both ropes were still"),
            ("first-try reflection", "Ishan", "asked for a low starting push", "watched each safe return", "his worried expression changed into a smile"),
            ("action-sentence workshop", "Noor", "chose breeze as a noun", "used lifted as the verb", "a complete sentence described the moving scarf"),
            ("courtyard-view recap", "Gopal", "saw a wall disappear below", "linked the higher view with excitement", "the concise summary avoided minor colour details"),
            ("station-position paragraph", "Jaya", "located a seat under a canopy", "placed steps behind the rail", "the linked paragraph used exact prepositions throughout"),
            ("terrace-hammock view", "Leela", "lay below a line of potted plants", "watched their tops appear and vanish during each sway", "the account connected motion with a changing view"),
            ("branch-movement record", "Sameer", "observed one branch bend after a gust", "separated the moving branch from the wind as cause", "the completed sentence assigned noun and verb correctly"),
            ("playground-seat map", "Pooja", "stood beside the sandbox entrance", "placed the swing beyond the slide and near the fence", "a visitor could locate the seat from the directions"),
            ("kite-viewpoint note", "Imran", "followed a kite above nearby roofs", "described how streets looked narrow from that height", "the comparison explained a distant perspective"),
            ("train-window motion card", "Kavya", "watched poles seem to move backward", "contrasted apparent motion with the travelling carriage", "the explanation kept observer and object distinct"),
            ("hill-path lookout", "Manav", "paused where the path crossed a ridge", "identified the village below and clouds overhead", "the description used position words precisely"),
            ("preposition-route grid", "Diya", "placed a marker at the gate", "moved it across the bridge and under the arch", "each location phrase matched the drawn route"),
            ("noun-verb word study", "Omar", "compared the phrases a swing and birds swing", "labelled the naming use and action use", "two original sentences preserved both meanings"),
        ),
    },
    "eng_c4_ch11": {
        "a": (
            ("ridge-route word log", "Anaya", "studied the highest marked point", "used summit for the final high place", "the route clue fixed the mountain word"),
            ("trek preparation account", "Kabir", "packed water and a weather layer", "checked the route before climbing", "the central idea joined planning with safe travel"),
            ("hill-trail sequence", "Mehul", "tightened his pack straps", "followed markers, rested, and reached the shelter", "the register was signed after arrival"),
            ("stream-crossing decision", "Raina", "noticed loose stones near the water", "chose the marked bridge instead", "the group crossed without disturbing the bank"),
            ("conjunction trail card", "Tanu", "wrote a steep-path sentence", "joined caution and progress with but", "the complete line showed a sensible contrast"),
            ("mountain-day summary", "Dev", "selected route and weather facts", "compressed the changing conditions", "the recap kept both challenge and preparation"),
            ("body-part metaphor plan", "Lina", "interpreted the shoulder of a hill", "linked the image with a litter-free rest point", "the closing paragraph proposed care for the route"),
            ("trail-marker repair", "Asha", "found an arrow turned toward a closed path", "reset it using the route map and ranger note", "later walkers followed the open trail"),
            ("weather-shelter choice", "Ritesh", "saw dark clouds reach the western ridge", "stopped at a roofed checkpoint instead of climbing", "the group remained dry during the short storm"),
            ("shared-load plan", "Mira", "noticed one walker carrying all cooking gear", "divided light items among three packs", "the team maintained an even pace"),
            ("water-ration log", "Zoya", "counted bottles before a long dry section", "set equal drink pauses on the map", "enough water remained for the return"),
            ("valley-echo observation", "Arun", "called once from an open ledge", "timed the returning sound without leaving the marked area", "the note linked echo with surrounding slopes"),
            ("summit-turnaround decision", "Sana", "reached the final checkpoint later than planned", "followed the turnaround time rather than the summit arrow", "the group descended before darkness"),
            ("wildlife-distance card", "Farah", "spotted goats beside a narrow bend", "waited quietly and used a wider viewing point", "the animals crossed without being chased"),
            ("litter-return plan", "Nikhil", "counted wrappers after the rest stop", "sealed them in a reusable carry bag", "the shelter area matched its clean arrival condition"),
        ),
        "b": (
            ("valley-map vocabulary", "Bina", "traced the low land between slopes", "used valley for that landform", "the surrounding heights supplied the clue"),
            ("weather-wise journey note", "Rohit", "read the cloud warning", "changed the departure time and packed a cover", "the whole account stressed thoughtful preparation"),
            ("forest-lookout route", "Hema", "registered at the lower gate", "climbed, paused, checked bearings, and returned", "the final note came after safe descent"),
            ("wildflower-path choice", "Ishan", "saw walkers leave the marked trail", "kept his group on the firm route", "the flowers remained undamaged"),
            ("cause-and-contrast sentence", "Noor", "identified two related ideas", "used because for the reason and but for the change", "both clauses formed one complete response"),
            ("highland-visit recap", "Gopal", "removed snack and colour details", "kept the route, shelter, and weather change", "the summary stayed accurate and concise"),
            ("river-arm care paragraph", "Jaya", "explained the arm as a branching channel", "connected the image with keeping waste away", "the linked ending stated a community benefit"),
            ("fog-navigation record", "Leela", "lost sight of the next ridge marker", "stopped, checked the compass, and returned to the last post", "the group regained the route without guessing"),
            ("footwear-check station", "Sameer", "found a smooth sole before departure", "changed into shoes with firm tread", "he crossed damp stones with better grip"),
            ("river-crossing decision", "Pooja", "saw water cover the usual stepping stones", "used the upstream footbridge shown on the map", "the walkers avoided the swollen channel"),
            ("rest-pace journal", "Imran", "recorded two walkers falling behind", "shortened the next section and added a seated pause", "the full group reached camp together"),
            ("contour-map lesson", "Kavya", "compared tightly packed and widely spaced lines", "chose the gentler route around the hill", "the planned climb avoided the steep face"),
            ("emergency-whistle drill", "Manav", "separated three signal patterns", "used the agreed distress call during practice", "the guide identified the location quickly"),
            ("wildflower-protection note", "Diya", "found a shortcut crossing a bloom patch", "blocked it with a route marker and direction card", "walkers stayed on the durable path"),
            ("community-trail report", "Omar", "gathered bridge, shelter, and erosion facts", "recommended one repair supported by those notes", "the final paragraph linked evidence with public care"),
        ),
    },
    "eng_c4_ch12": {
        "a": (
            ("riverside-arch word clue", "Anaya", "studied a tall carved entrance", "used majestic for its grand appearance", "the surrounding description fixed the heritage word"),
            ("fort-guide dialogue", "Kabir", "asked why steps reached the water", "recorded the guide's transport explanation", "the exchange developed a river-access message"),
            ("weaving-sample sequence", "Mehul", "selected cotton and silk threads", "set, wove, checked, and trimmed the sample", "the cloth was folded after both faces were examined"),
            ("courtyard-plaque reason", "Raina", "noticed visitors reading the worn inscription", "protected the plaque from scratching", "future visitors could still study its letters"),
            ("silent-letter label", "Tanu", "compared written and spoken forms", "kept the silent letter in the museum label", "the complete sentence used the intended spelling"),
            ("heritage fact summary", "Dev", "selected fort and public-work facts", "removed an unsupported date", "the recap remained accurate to the fact card"),
            ("riverside-granary paragraph", "Lina", "introduced a stone granary and an arched doorway", "referred later to the doorway and loading court", "the linked paragraph used articles in meaningful order"),
            ("pottery-kiln label", "Asha", "compared raw clay with a fired vessel", "used kiln for the heated chamber", "the object note connected place and function"),
            ("river-ferry archive", "Ritesh", "read fare and route entries from one dated sheet", "separated recorded facts from a visitor's guess", "the summary described transport without inventing an owner"),
            ("carved-lintel care", "Mira", "noticed dust packed into shallow letters", "used a soft brush under the curator's written method", "the inscription remained visible and undamaged"),
            ("market-clock timeline", "Zoya", "found repair dates beside the clock drawing", "ordered the entries before stating the latest change", "the summary preserved the documented sequence"),
            ("textile-dye process", "Arun", "prepared a small thread sample and measured dye", "soaked, rinsed, dried, and compared the colour", "the final card reported the checked shade"),
            ("oral-history transcript check", "Sana", "received two written interview transcripts", "marked the detail confirmed in both records", "the heritage note labelled one unmatched claim uncertain"),
            ("memorial-garden route", "Farah", "entered beside a stone map", "visited the plaque, tree circle, and exit arch in order", "the route paragraph ended at the recorded final stop"),
            ("visitor-code paragraph", "Nikhil", "listed quiet movement and no-touch rules", "connected each rule with protecting the shared site", "the conclusion explained respectful heritage care"),
        ),
        "b": (
            ("woven-border vocabulary card", "Bina", "compared several cloth edges", "used unique for the unmatched pattern", "the contrast showed the exact meaning"),
            ("archive-room exchange", "Rohit", "asked how wells served residents", "separated the archivist's fact from a visitor's reaction", "the dialogue centred on public works"),
            ("fort-visit route", "Hema", "entered through the lower gate", "crossed the court, read a plaque, and reached the landing", "the return began only after the final stop"),
            ("stone-step protection note", "Ishan", "observed a cracked edge", "guided visitors around the marked repair", "the old surface stayed protected"),
            ("heritage-word spelling check", "Noor", "heard a word with one quiet letter", "kept every written letter on the object card", "the sentence preserved correct spelling and meaning"),
            ("craft-fact recap", "Gopal", "retained cotton, silk, and two-sided border facts", "rejected a guessed inventor", "the summary reported only the stated facts"),
            ("craft-hall description paragraph", "Jaya", "introduced a weaving hall and an open veranda", "used the for the known veranda later", "the closing sentence stayed within the given place facts"),
            ("old-bridge word card", "Leela", "studied stone supports spanning a narrow channel", "used arch for the curved load-bearing shape", "the structural clue fixed the meaning"),
            ("coin-display dialogue", "Sameer", "asked why two dates appeared on one label", "connected the curator's minting and discovery facts", "the exchange distinguished production from recovery"),
            ("archive-folio sequence", "Pooja", "cleared a padded table", "opened, numbered, photographed, and closed the folio", "storage began after every page was checked"),
            ("stone-drain reason", "Imran", "saw a channel carry rain away from a courtyard", "linked the slope with protecting the floor", "the explanation linked function with protection"),
            ("quiet-letter object tag", "Kavya", "compared the written words sign and design", "kept each silent letter in a new museum sentence", "both labels preserved standard spelling"),
            ("temple fact summary", "Manav", "selected location and carving facts", "left an unknown building date unstated", "the recap remained true to the archive card"),
            ("museum-article description", "Diya", "introduced an iron key and a storage chest", "used the for each known object later", "the paragraph maintained clear reference"),
            ("conservation-notice paragraph", "Omar", "listed a faded mural and a low barrier", "linked viewing distance with colour protection", "the closing sentence proposed one supported visitor action"),
        ),
    },
}


ASSESSMENT_WORD_GLOSSES = {
    "steady": "evenly controlled movement",
    "swift": "unusually fast movement",
    "cheerful": "a warm and hopeful feeling",
    "rhythmic": "following a regular pulse",
    "proud": "satisfied with worthwhile work",
    "boundary": "a line enclosing the play area",
    "referee": "an official who enforces rules",
    "dodge": "shift aside to escape contact",
    "opponent": "a player competing against you",
    "teamwork": "people coordinating one shared effort",
    "defender": "a player guarding an area",
    "challenger": "a competitor testing another side",
    "surrender": "ending resistance and yielding",
    "declared": "stated publicly as official",
    "superiority": "greater ability in comparison",
    "wide": "stretching across much space",
    "sway": "move smoothly back and forth",
    "distant": "located far from here",
    "pleasant": "comfortable and enjoyable",
    "descending": "travelling from high to low",
    "valley": "low ground amid hills",
    "summit": "the uppermost point of a height",
    "journey": "travel between places over time",
    "load": "an object or weight being carried",
    "memory": "a past event kept in mind",
    "majestic": "impressively grand in appearance",
    "overhanging": "projecting above something lower",
    "unique": "unlike every compared example",
    "wise": "showing careful good judgement",
    "fortress": "a strongly defended building or place",
    "design": "a planned arrangement or pattern",
    "sign": "a notice giving information",
    "high": "far above lower ground",
    "light": "easy to lift or carry",
    "bright": "strong and easy to see",
}


ASSESSMENT_WORD_GLOSSES_B = {
    "steady": "controlled at a consistent pace",
    "swift": "moving with notable speed",
    "cheerful": "showing an encouraging happy mood",
    "rhythmic": "moving to a repeated pattern",
    "proud": "pleased with a worthy achievement",
    "boundary": "the game's marked limit",
    "referee": "a rule official during a match",
    "dodge": "sidestep to avoid contact",
    "opponent": "a person competing on another side",
    "teamwork": "shared effort through coordination",
    "defender": "a player protecting a position",
    "challenger": "a competitor testing the other side",
    "surrender": "yield and stop competing",
    "declared": "announced in an official way",
    "superiority": "being stronger by comparison",
    "wide": "covering plenty of space",
    "sway": "move gently to and fro",
    "distant": "far from the current place",
    "pleasant": "enjoyable without discomfort",
    "descending": "moving from higher to lower",
    "valley": "lower land between slopes",
    "summit": "highest place on a mountain",
    "journey": "travel from one place onward",
    "load": "weight that someone carries",
    "memory": "past experience held in thought",
    "majestic": "grand enough to inspire admiration",
    "overhanging": "extending beyond and above",
    "unique": "different from every comparison",
    "wise": "guided by careful judgement",
    "fortress": "a place strongly built for defence",
    "design": "a planned pattern or arrangement",
    "sign": "a posted notice carrying a message",
    "high": "well above the surrounding ground",
    "light": "not heavy to carry",
    "bright": "vivid and clearly visible",
}


def _case(label: str, passage: str, answer: str) -> dict[str, str]:
    if "{actor}" not in passage or "{actor}" not in answer:
        raise ValueError("class4_case_requires_actor_token")
    if len(answer.format(actor="Learner").split()) < 8:
        raise ValueError("class4_case_answer_too_short")
    return {"label": label, "passage": passage, "answer": answer}


def _render(case: dict[str, str], actor: str) -> tuple[str, str]:
    return case["passage"].format(actor=actor), case["answer"].format(actor=actor)


DOUBLE_LETTER_WORDS = (
    ("fitness", "ss"),
    ("running", "nn"),
    ("swimming", "mm"),
    ("skipping", "pp"),
    ("tennis", "nn"),
    ("happy", "pp"),
    ("little", "tt"),
    ("hopping", "pp"),
    ("wellness", "ll"),
    ("football", "ll"),
    ("yellow", "ll"),
    ("carrot", "rr"),
    ("bottle", "tt"),
    ("rabbit", "bb"),
    ("summer", "mm"),
    ("correct", "rr"),
    ("paddle", "dd"),
)
RHYME_PAIRS = (
    ("play", "day"),
    ("rest", "best"),
    ("light", "bright"),
    ("pace", "race"),
    ("slow", "go"),
    ("ground", "round"),
    ("team", "stream"),
    ("move", "prove"),
    ("pause", "cause"),
    ("more", "shore"),
    ("care", "share"),
    ("feet", "beat"),
    ("bend", "friend"),
    ("strong", "long"),
    ("track", "back"),
    ("glide", "side"),
    ("cheer", "near"),
)
UNSCRAMBLE_LINES = (
    ("tower / the / {actor} / rebuilt", "{actor} rebuilt the tower."),
    ("softly / ball / rolled / the / {actor}", "{actor} rolled the ball softly."),
    ("line / behind / waited / the / team / the", "The team waited behind the line."),
    ("signal / clear / gave / referee / the / a", "The referee gave a clear signal."),
    ("markers / counted / all / {actor} / the", "{actor} counted all the markers."),
    ("turn / each / took / player / one", "Each player took one turn."),
    ("target / guarded / carefully / defenders / the / the", "The defenders guarded the target carefully."),
    ("steps / counted / four / {actor}", "{actor} counted four steps."),
    ("rest / short / group / took / a / the", "The group took a short rest."),
    ("water / shared / players / the", "The players shared water."),
    ("question / captain / asked / the / a", "The captain asked a question."),
    ("match / teamwork / won / the", "Teamwork won the match."),
    ("rope / fixed / loose / {actor} / the", "{actor} fixed the loose rope."),
    ("basket / discs / placed / the / in / {actor}", "{actor} placed the discs in the basket."),
    ("zone / players / waiting / the / stood / in / the", "The players stood in the waiting zone."),
    ("ideas / two / group / joined / the", "The group joined two ideas."),
    ("field / left / clean / team / the / the", "The team left the field clean."),
)
HOMOPHONE_PAIRS = (
    ("there", "their"),
    ("right", "write"),
    ("one", "won"),
    ("hear", "here"),
    ("pair", "pear"),
    ("blue", "blew"),
    ("week", "weak"),
    ("fair", "fare"),
    ("see", "sea"),
    ("wait", "weight"),
    ("peace", "piece"),
    ("sun", "son"),
    ("meet", "meat"),
    ("hole", "whole"),
    ("tail", "tale"),
    ("flower", "flour"),
    ("road", "rode"),
)
ANIMAL_SOUND_CLUSTERS = (
    ("growl", "gr", "dog"),
    ("bleat", "bl", "goat"),
    ("snort", "sn", "pig"),
    ("croak", "cr", "frog"),
    ("trumpet", "tr", "elephant"),
    ("squawk", "squ", "parrot"),
    ("bray", "br", "donkey"),
    ("twitter", "tw", "sparrow"),
    ("whinny", "wh", "horse"),
    ("squeak", "squ", "mouse"),
    ("cluck", "cl", "hen"),
    ("grunt", "gr", "boar"),
    ("screech", "scr", "owl"),
    ("whine", "wh", "puppy"),
    ("chirrup", "chr", "cricket"),
    ("drone", "dr", "bee"),
    ("trill", "tr", "songbird"),
)


def _fresh_scene(
    chapter_id: str,
    phase: str,
    index: int,
) -> tuple[tuple[str, ...], int]:
    start, end = FRESH_PHASE_RANGES[phase]
    position = start + index - 1
    if not start <= position < end:
        raise ValueError(f"class4_fresh_scene_index:{phase}:{index}")
    return FRESH_TEACHING_SCENES[chapter_id][position], position


def _special_language_feature(
    *,
    level_id: str,
    actor: str,
    position: int,
    phase: str,
) -> tuple[str, str] | None:
    if level_id == "fit_double_letter_spelling":
        word, doubled = DOUBLE_LETTER_WORDS[position]
        detail = (
            f"A word card shows {word}. Its spelling keeps the double letter "
            f"{doubled} in the middle, and {actor} checks both letters before "
            "using the word in a sentence."
        )
        answer = {
            "independent": (
                f"{actor} writes {word} and circles the double letter {doubled}. "
                f"Both repeated letters remain in the complete spelling."
            ),
            "transfer": (
                f"In the new word {word}, {actor} keeps the middle pair {doubled}. "
                "The finished sentence uses that spelling accurately."
            ),
            "review": (
                f"Checking from left to right, {actor} finds {doubled} repeated in {word}. "
                "The word is correct only when neither matching letter is dropped."
            ),
            "support": (
                f"{actor} repairs the spelling of {word} by restoring the pair {doubled}. "
                "A second check confirms every letter in its proper place."
            ),
        }[phase]
        return detail, answer
    if level_id == "fit_poetic_balanced_plan":
        first, second = RHYME_PAIRS[position]
        detail = (
            f"Two short lines end with {first} and {second}. The ending sounds "
            "match, so the rhyme gives the movement plan a clear beat."
        )
        answer = (
            f"The words {first} and {second} rhyme because their ending sounds "
            f"match. {actor} links that rhyme with a plan that balances movement, rest, and care."
        )
        return detail, answer
    if level_id == "lagori_word_unscrambling":
        scrambled, ordered = UNSCRAMBLE_LINES[position]
        sentence = ordered.format(actor=actor)
        detail = (
            f"A card says, 'Scrambled words: {scrambled.format(actor=actor)}.' "
            "To unscramble it, the naming words must come before the action and "
            "the sentence must end with a full stop."
        )
        answer = {
            "independent": (
                f"{actor} writes the complete sentence '{sentence}' The naming words come first, "
                "the action follows, and a full stop closes the thought."
            ),
            "transfer": (
                f"After sorting every word by its job, {actor} produces '{sentence}' "
                "The subject leads, the verb follows, and the final mark completes the new sentence."
            ),
            "review": (
                f"The checked order is '{sentence}' {actor} confirms the capital opening, "
                "the doer before the action, and the full stop at the end."
            ),
            "support": (
                f"{actor} repairs the mixed word card as '{sentence}' Reading from the doer "
                "to the action and then the end mark confirms a complete thought."
            ),
        }[phase]
        return detail, answer
    if level_id == "hekko_homophones":
        first, second = HOMOPHONE_PAIRS[position]
        detail = (
            f"The words {first} and {second} are a homophone pair: they sound "
            "alike but have different spellings and meanings. One fits the game sentence; the other does not."
        )
        answer = {
            "independent": (
                f"{actor} identifies {first} and {second} as homophones: their sounds match, "
                "but the two spellings carry separate meanings."
            ),
            "transfer": (
                f"Although {first} sounds like {second}, {actor} uses the sentence clue "
                "to choose between their different meanings and spellings."
            ),
            "review": (
                f"{actor} checks the pair {first} and {second}. Equal sounds make them "
                "homophones, while context keeps their meanings apart."
            ),
            "support": (
                f"{actor} corrects a sound-only guess by comparing {first} with {second}. "
                "The sentence meaning decides which homophone spelling fits."
            ),
        }[phase]
        return detail, answer
    if level_id == "hekko_clusters_and_animal_sounds":
        sound, cluster, animal = ANIMAL_SOUND_CLUSTERS[position]
        detail = (
            f"The animal sound word {sound} names the sound of a {animal}. It "
            f"begins with the consonant cluster {cluster}, whose consonant sounds can be heard together."
        )
        answer = {
            "independent": (
                f"{actor} matches {sound} with a {animal} and marks {cluster} at the start. "
                "Both opening consonants can be heard in the animal-sound word."
            ),
            "transfer": (
                f"In this unfamiliar example, {actor} links the {animal} to {sound}. "
                f"The beginning {cluster} blends two or more consonant sounds."
            ),
            "review": (
                f"{actor} checks that {sound} names a {animal}'s sound rather than the animal. "
                f"The letters {cluster} form its opening consonant cluster."
            ),
            "support": (
                f"{actor} repairs the match by pairing {animal} with {sound}, then rebuilds "
                f"the beginning from the consonant cluster {cluster}."
            ),
        }[phase]
        return detail, answer
    return None


def _fresh_case(
    *,
    spec: dict[str, Any],
    phase: str,
    index: int,
    actor: str,
) -> dict[str, Any]:
    chapter_id = spec["_chapter_id"]
    raw_scene, position = _fresh_scene(chapter_id, phase, index)
    label, setting, preparation, action, result, word, definition = raw_scene
    if phase == "independent":
        opening = (
            f"At the {setting}, {{actor}} {preparation}. Two friends checked "
            "that the space was ready and agreed on the goal before anyone began."
        )
        bridge = f"Then {{actor}} {action}. Soon, {result}."
    elif phase == "transfer":
        opening = (
            f"The {setting} brought a different challenge. Before starting, "
            f"{{actor}} {preparation} and explained the safe plan to the group."
        )
        bridge = f"During the activity, {{actor}} {action}. In the end, {result}."
    elif phase == "review":
        opening = (
            f"On a return visit to the {setting}, {{actor}} {preparation}. A "
            "friend asked what mattered most, so the group watched the next change closely."
        )
        bridge = f"{{actor}} then {action}. Afterward, {result}."
    else:
        opening = (
            f"During a short practice at the {setting}, {{actor}} {preparation}. "
            "The first idea did not fit every detail, so the group slowed down and checked the new example."
        )
        bridge = f"Next, {{actor}} {action}. The change meant that {result}."

    special = _special_language_feature(
        level_id=spec["level_id"],
        actor="{actor}",
        position=position,
        phase=phase,
    )
    if special is not None:
        feature, answer = special
    else:
        skills = set(spec["skill_ids"])
        if "grammar.noun_verb_adjective" in skills:
            feature = (
                f"A language card says, 'The careful helper moved the bright "
                f"{word} marker near the {setting}.' The sentence has naming, action, and describing words."
            )
            answer = {
                "independent": (
                    f"In the {label} line, helper and marker are nouns, moved is the verb, "
                    f"and careful and bright are adjectives. {{actor}} explains every word's job."
                ),
                "transfer": (
                    f"{{actor}} sorts the new sentence by role: helper names a person, moved "
                    f"shows action, and bright describes the {word} marker near the {setting}."
                ),
                "review": (
                    f"Looking again at the {label} sentence, {{actor}} labels marker as a noun, "
                    "moved as a verb, and careful as an adjective before writing a complete thought."
                ),
                "support": (
                    f"{{actor}} corrects the word-role mix-up in the {label} line. Helper is a noun, "
                    "moved is a verb, and bright is an adjective describing the marker."
                ),
            }[phase]
        elif "grammar.question_formation" in skills:
            feature = (
                f"A teammate wants to know how the {label} result happened. The "
                "question needs a capital letter, a clear asking word, and a question mark."
            )
            answer = (
                f"How did {{actor}} help the {label} activity succeed? This is a "
                "complete question with a capital letter and a question mark."
            )
        elif "grammar.prepositions" in skills:
            feature = (
                f"The {word} marker stood beside the path and below the sign at "
                f"the {setting}. Those position words show exactly where it was."
            )
            answer = (
                f"The marker stood beside the path and below the sign. {{actor}} "
                f"uses both prepositions to place it clearly in the {label} paragraph."
            )
        elif "reading.dialogue_attribution" in skills:
            feature = (
                f"'What changed the result?' asked the captain. '{{actor}} "
                f"{action},' replied the scorer."
            )
            answer = (
                f"The captain asks what changed the result, and the scorer answers "
                f"that {{actor}} {action}. Their exchange links the action to the ending."
            )
        elif "reading.poetic_language" in skills:
            feature = (
                f"A short line calls the {word} plan a bridge to the result. This "
                "comparison describes how one helpful choice leads to a better ending; it is not a real bridge."
            )
            answer = (
                f"The bridge image shows that {{actor}}'s {word} choice connects "
                f"the opening problem with this ending: {result}. The comparison is figurative."
            )
        elif "grammar.tense_usage" in skills:
            feature = (
                "The words yesterday and later show that every action is already finished. "
                "The verbs must therefore use clear past-tense forms."
            )
            answer = (
                f"Yesterday, {{actor}} {preparation} and later {action}. The "
                "past-tense verbs form a complete sentence about finished actions."
            )
        elif "grammar.connectors_because_and_but" in skills:
            feature = (
                f"The group improved the plan because a clear need appeared, but "
                "the new rule still kept the activity enjoyable. Each connector has a different job."
            )
            answer = (
                f"{{actor}} changed the plan because the earlier arrangement needed help, "
                f"but the new version stayed enjoyable. As a result, {result}."
            )
        elif "grammar.sentence_order" in skills:
            feature = (
                f"The words '{{actor}} / {action}' must keep the actor before the "
                "action. A capital letter and full stop make the ordered words a complete sentence."
            )
            answer = (
                f"{{actor}} {action}. The ordered sentence begins with the actor, "
                "places the action next, and ends with a full stop."
            )
        elif "vocab.spelling" in skills:
            feature = (
                f"A label uses the word {word}, meaning {definition}. {{actor}} "
                "checks every written letter before putting the label beside the object."
            )
            answer = (
                f"{{actor}} spells {word} correctly and uses it to mean {definition}. "
                "The complete sentence matches the word to the visible situation."
            )
        else:
            feature = {
                "independent": (
                    f"In the {label} scene, {word} means {definition}. The warm-up, "
                    "main choice, and comfortable ending make that meaning clear."
                ),
                "transfer": (
                    f"A sign at the {setting} calls the new plan {word}, meaning "
                    f"{definition}. The group tests that description against what changed."
                ),
                "review": (
                    f"Looking back, a friend chooses {word} for the action. The word "
                    f"means {definition}, which fits the later condition."
                ),
                "support": (
                    f"One child first guesses the wrong meaning for {word}. The {label} "
                    f"details instead show that it means {definition}."
                ),
            }[phase]
            if "reading.word_meaning_context" in skills:
                answer = (
                    f"In this story, {word} means {definition}. {{actor}} uses the "
                    f"word accurately because the action leads to this ending: {result}."
                )
            elif "reading.paragraph_main_idea" in skills:
                answer = (
                    f"The main idea is that {{actor}} prepared carefully and made a "
                    f"useful choice, so {result}. The idea covers the whole {label} story."
                )
            elif "reading.event_sequence" in skills:
                answer = (
                    f"First, {{actor}} {preparation}. Next, {{actor}} {action}. "
                    f"Finally, {result}."
                )
            elif "reading.inference_reason" in skills:
                answer = (
                    f"{{actor}} made a sensible choice because {{actor}} {action}. "
                    f"That decision led to this clear result: {result}."
                )
            elif "reading.sentence_comprehension" in skills:
                answer = (
                    f"{{actor}} is the person who acts, and the key action is that "
                    f"{{actor}} {action}. The important result is that {result}."
                )
            else:
                answer = (
                    f"{{actor}} {preparation}, then {action}. The useful change was "
                    f"clear because {result}."
                )
    if "writing.procedure" in spec["skill_ids"]:
        materials = (
            "boundary rope, two team bands, a whistle, and score tokens"
            if chapter_id == "eng_c4_ch09"
            else "six foam discs, a soft ball, chalk, and a whistle"
        )
        feature = f"{{actor}} receives {materials}. {feature}"
    phase_tail = {
        "independent": (
            f"Rereading the beginning confirms how {word} fits this story. "
            f"A classmate retells the {setting} event and explains why that word belongs."
        ),
        "transfer": (
            f"The unfamiliar setting makes {word} clear through its outcome. "
            f"The group compares this {setting} result with its opening challenge."
        ),
        "review": (
            f"A final check connects {word} with the decisive change. "
            f"One partner retells the {setting} change without adding a new event."
        ),
        "support": (
            f"This new example repairs the earlier mistake about {word}. "
            f"The group then explains why the corrected idea fits the {setting}."
        ),
    }[phase]
    passage = f"{opening} {bridge} {feature} {phase_tail}"
    rendered = _case(label, passage, answer)
    rendered.update(
        {
            "setting": setting,
            "preparation": preparation,
            "action": action,
            "result": result,
            "word": word,
            "definition": definition,
        }
    )
    return rendered


def _clean_claim(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" ,.;:")
    return re.sub(r"^(?:and|so|while|which)\s+", "", cleaned, flags=re.IGNORECASE)


def _paraphrase_claim(value: str) -> str:
    replacements = (
        ("The main idea is", "The central message is"),
        ("the main idea is", "the central message is"),
        ("means", "refers to"),
        ("first", "at the beginning"),
        ("next", "after that"),
        ("finally", "at the end"),
        ("shows", "demonstrates"),
        ("showing", "demonstrating"),
        ("uses", "applies"),
        ("writes", "states"),
        ("helps", "supports"),
        ("helped", "supported"),
        ("together", "as a group"),
        ("safe", "low-risk"),
        ("result", "outcome"),
    )
    paraphrase = value
    for source, replacement in replacements:
        paraphrase = re.sub(
            rf"(?<!\w){re.escape(source)}(?!\w)",
            replacement,
            paraphrase,
        )
    paraphrase = _clean_claim(paraphrase)
    if paraphrase.casefold() == _clean_claim(value).casefold():
        paraphrase = f"According to the record, {value[0].lower()}{value[1:]}"
    return paraphrase


def _claim_parts(answer: str, *, ordered: bool) -> list[str]:
    cleaned = _clean_claim(answer)
    sentence_parts = [
        _clean_claim(part)
        for part in re.split(r"(?<=[.!?])\s+", answer.strip())
        if len(_clean_claim(part).split()) >= 3
    ]
    if len(sentence_parts) >= 2 and not ordered:
        return [sentence_parts[0], " ".join(sentence_parts[1:])]
    parts = [
        _clean_claim(part)
        for part in re.split(
            r"\s+because\s+|,\s+(?:and|so|while|which)\s+|;\s*",
            cleaned,
            maxsplit=1,
        )
        if len(_clean_claim(part).split()) >= 3
    ]
    if ordered:
        sequence_parts = [
            _clean_claim(part)
            for part in re.split(r"(?<=[.!?])\s+", answer.strip())
            if re.match(
                r"^(?:first|next|then|finally|afterward|in the end)\b",
                _clean_claim(part),
                re.IGNORECASE,
            )
        ]
        if len(sequence_parts) < 3:
            sequence_parts = [
                _clean_claim(part)
                for part in re.split(
                    r"(?=(?:First|Next|Then|Finally|Afterward),\s)",
                    cleaned,
                )
                if len(_clean_claim(part).split()) >= 3
            ]
        if len(sequence_parts) >= 3:
            return [
                sequence_parts[0],
                sequence_parts[len(sequence_parts) // 2],
                sequence_parts[-1],
            ]
        if len(sentence_parts) >= 2:
            return sentence_parts
    if len(parts) >= 2:
        return [parts[0], parts[1]]
    words = cleaned.split()
    split_at = max(3, len(words) // 2)
    return [" ".join(words[:split_at]), " ".join(words[split_at:])]


def _evidence_for_claims(
    *,
    case_label: str,
    claims: list[str],
    descriptions: list[str] | None = None,
) -> list[tuple[str, str, list[str]]]:
    evidence: list[tuple[str, str, list[str]]] = []
    used_aliases: set[str] = set()
    for index, claim in enumerate(claims, start=1):
        exact = _clean_claim(claim)
        alternate = _paraphrase_claim(exact)
        aliases = []
        for alias in (exact, alternate):
            normalized = alias.casefold()
            if normalized not in used_aliases:
                aliases.append(alias)
                used_aliases.add(normalized)
        if len(aliases) < 2:
            fallback = f"The {case_label} record confirms that {exact[0].lower()}{exact[1:]}"
            aliases.append(fallback)
            used_aliases.add(fallback.casefold())
        if descriptions is not None:
            description = descriptions[index - 1]
        else:
            protected = {
                "and",
                "both",
                "final",
                "first",
                "last",
                "order",
                "ordered",
                "sequence",
                "three",
                "two",
            }
            anchors = [
                word
                for word in re.findall(r"[A-Za-z0-9']+", exact)
                if word.casefold() not in protected
            ][:5]
            label_anchors = [
                word
                for word in re.findall(r"[A-Za-z0-9']+", case_label)
                if word.casefold() not in protected
            ][:4]
            exact_description = (
                f"Checks this {' '.join(label_anchors) or 'story'} claim: {exact}."
            )
            if all(
                authored_evidence_can_prove_criterion(exact_description, alias)
                for alias in aliases
            ):
                description = exact_description
            else:
                description = (
                    f"Checks the {' '.join(label_anchors) or 'story'} idea about "
                    f"{' '.join(anchors)}."
                )
        evidence.append((f"claim-{index}", description, aliases))
    return evidence


def _teaching_passage(
    *,
    spec: dict[str, Any],
    case: dict[str, str],
    actor: str,
    phase: str,
    index: int,
) -> str:
    base_passage, _ = _render(case, actor)
    return _strip_template_sentences(base_passage)


def _paragraph_authority(
    *,
    spec: dict[str, Any],
    case: dict[str, str],
    actor: str,
) -> tuple[str, list[tuple[str, str, list[str]]]]:
    base_passage, base_answer = _render(case, actor)
    base_passage = base_passage.rstrip(" .")
    base_answer = base_answer.rstrip(" .")
    label = case["label"].replace("-", " ").replace(" packet", " fact card")
    if case.get("setting"):
        opening = (
            f"The {label} story shows a thoughtful way to practise "
            f"{spec['title'].casefold()}"
        )
        support = f"First, {actor} {case['preparation']} before the activity began"
        link = (
            f"In addition, {actor} {case['action']}, so {case['result']}"
        )
        closing = (
            f"Overall, the {case['word']} choice helped the group reach a useful "
            f"ending at the {case['setting']}"
        )
    else:
        opening = (
            f"The {label} story develops one clear idea from its action and result"
        )
        support = f"One supporting detail is that {base_answer[0].lower()}{base_answer[1:]}"
        link = f"In addition, {base_passage}"
        closing = f"Overall, these linked details explain the {label} message clearly"
    model_answer = ". ".join((opening, support, link, closing)) + "."
    descriptions = [
        f"Uses an opening sentence that states the {label} paragraph focus.",
        "Adds a relevant support sentence grounded in the supplied account.",
        "Uses a linking expression to connect a second supporting detail.",
        "Ends with a punctuated closing sentence that returns to the focus.",
    ]
    return model_answer, _evidence_for_claims(
        case_label=case["label"],
        claims=[opening, support, link, closing],
        descriptions=descriptions,
    )


def _procedure_materials(spec: dict[str, Any], passage: str) -> str:
    received = re.search(r"receives? (.+?)(?:\.| The | Players )", passage)
    if received:
        return received.group(1).strip()
    if "hekko" in spec["level_id"]:
        return "boundary rope, two team bands, a whistle, and one rule card"
    return "six foam discs, a soft ball, chalk, and a whistle"


def _procedure_authority(
    *,
    spec: dict[str, Any],
    case: dict[str, str],
    actor: str,
) -> tuple[str, list[tuple[str, str, list[str]]]]:
    base_passage, base_answer = _render(case, actor)
    label = case["label"].replace("-", " ")
    materials = _procedure_materials(spec, base_passage)
    material_claim = f"Materials: {materials}"
    if case.get("setting"):
        order_claim = (
            f"First, mark a clear area for the {label} activity. Next, place the "
            f"materials where every player can reach them. Then, have {actor} "
            f"complete the story's key action: {case['action']}"
        )
        result_text = case["result"]
    else:
        order_claim = (
            f"First, mark the play area and explain the {label} goal. Next, place "
            "all equipment before anyone begins. Then, complete each action in the story's order"
        )
        result_text = _clean_claim(base_answer)
    safety_claim = (
        "For safety, leave two arm lengths between players, use controlled "
        "movement, and stop when the whistle sounds"
    )
    result_claim = (
        f"Finally, put away the materials and check this result: {result_text}"
    )
    model_answer = ". ".join(
        (material_claim, order_claim, safety_claim, result_claim)
    ) + "."
    descriptions = [
        "Names the materials needed for the procedure before any action begins.",
        "Presents setup and play as ordered steps with transition words and clear punctuation.",
        "States a usable safety condition and stop rule for the activity.",
        "Finishes with a punctuated result step that completes the procedure.",
    ]
    return model_answer, _evidence_for_claims(
        case_label=case["label"],
        claims=[material_claim, order_claim, safety_claim, result_claim],
        descriptions=descriptions,
    )


def _extend_answer(
    answer: str,
    *,
    minimum: int,
    case_label: str,
    spec: dict[str, Any],
) -> str:
    additions = (
        f"The {case_label.replace('-', ' ')} story gives the action that supports this answer.",
        "The ending also supports the same idea.",
    )
    expanded = answer
    index = 0
    while len(expanded.split()) < minimum:
        expanded += " " + additions[index % len(additions)]
        index += 1
    return expanded


def _open_case(
    *,
    spec: dict[str, Any],
    case: dict[str, str],
    actor: str,
    prompt: str,
    skills: list[str],
    phase: str,
    index: int,
    minimum_words: int | None = None,
) -> dict[str, Any]:
    _, answer = _render(case, actor)
    passage = _teaching_passage(
        spec=spec,
        case=case,
        actor=actor,
        phase=phase,
        index=index,
    )
    ordered = bool(spec.get("ordered", False))
    if "writing.paragraph" in skills:
        answer, evidence = _paragraph_authority(spec=spec, case=case, actor=actor)
        min_words = max(45, minimum_words or 0)
        ordered = False
        lead = "Try" if phase == "transfer" else "Read"
        prompt = (
            f"{lead} the {case['label'].replace('-', ' ')} story. Write one "
            "paragraph with an opening, two linked details, and a closing."
        )
    elif "writing.procedure" in skills:
        answer, evidence = _procedure_authority(spec=spec, case=case, actor=actor)
        min_words = max(50, minimum_words or 0)
        ordered = True
        lead = "Try" if phase == "transfer" else "Read"
        prompt = (
            f"{lead} the {case['label'].replace('-', ' ')} story. Write a usable "
            "procedure with materials, ordered steps, one safety rule, and a final check."
        )
    else:
        min_words = minimum_words or min(12, len(answer.split()))
        min_words = max(8, min_words)
        answer = _extend_answer(
            answer,
            minimum=min_words,
            case_label=case["label"],
            spec=spec,
        )
        claims = _claim_parts(answer, ordered=ordered)
        evidence = _evidence_for_claims(
            case_label=case["label"],
            claims=claims,
        )
    return _task(
        passage,
        prompt,
        answer,
        evidence,
        interaction_type=spec["interaction_type"],
        min_words=min_words,
        skills=skills,
        ordered=ordered,
    )


def _choice_case(
    *,
    spec: dict[str, Any],
    cases: list[dict[str, str]],
    case_index: int,
    actor: str,
    prompt: str,
    skills: list[str],
) -> dict[str, Any]:
    passage, answer = _render(cases[case_index], actor)
    distractors = [
        _render(cases[(case_index + offset) % len(cases)], actor)[1]
        for offset in (1, 2, 3)
    ]
    return _choice(passage, prompt, answer, distractors, skills=skills)


def _support_task(
    *,
    spec: dict[str, Any],
    case: dict[str, str],
    actor: str,
    index: int,
    skills: list[str],
) -> dict[str, Any]:
    passage, base_answer = _render(case, actor)
    if "writing.paragraph" in skills:
        model_answer, evidence = _paragraph_authority(
            spec=spec,
            case=case,
            actor=actor,
        )
        minimum = 24 + index * 4
        ordered = False
    elif "writing.procedure" in skills:
        model_answer, evidence = _procedure_authority(
            spec=spec,
            case=case,
            actor=actor,
        )
        minimum = 26 + index * 4
        ordered = True
    else:
        minimum = 10 + index * 2
        model_answer = _extend_answer(
            base_answer,
            minimum=minimum,
            case_label=case["label"],
            spec=spec,
        )
        ordered = bool(spec.get("ordered", False))
        evidence = _evidence_for_claims(
            case_label=case["label"],
            claims=_claim_parts(model_answer, ordered=ordered),
        )
    prompt = (
        f"Try the {case['label'].replace('-', ' ')} story. "
        f"{spec['support_action'].capitalize()}. Explain the action and the change it caused."
    )
    if "writing.paragraph" in skills:
        prompt += " Present the response as one linked, punctuated paragraph."
    elif "writing.procedure" in skills:
        prompt += (
            " Present a usable procedure with materials, ordered steps, "
            "punctuation, safety, and a result."
        )
    return _task(
        passage,
        prompt,
        model_answer,
        evidence,
        interaction_type=spec["interaction_type"],
        min_words=minimum,
        skills=skills,
        ordered=ordered,
    )


def _raise_rubric_quality(activity: dict[str, Any]) -> None:
    for criterion in activity.get("rubric_criteria") or ():
        criterion["min_quality"] = 0.75


def build_authored_level(
    spec: dict[str, Any],
    level_index: int,
    chapter_id: str,
) -> dict[str, Any]:
    spec = {**spec, "_chapter_id": chapter_id}
    cases = spec["cases"]
    if len(cases) != 5:
        raise ValueError("class4_level_requires_five_authored_case_patterns")
    skills = list(spec["skill_ids"])
    first_skill = skills[0]
    if first_skill.startswith(PRODUCTIVE_PREFIXES):
        raise ValueError("class4_level_first_skill_must_support_selected_evidence")

    core_actors = tuple(
        CORE_ACTORS[(level_index + offset) % len(CORE_ACTORS)]
        for offset in range(5)
    )
    transfer_actors = tuple(
        TRANSFER_ACTORS[(level_index + offset) % len(TRANSFER_ACTORS)]
        for offset in range(5)
    )
    co_prompt = (
        f"Which answer {SKILL_DIRECTIONS[first_skill]} in the "
        f"{cases[0]['label'].replace('-', ' ')} story?"
    )
    guided_choice_prompt = (
        f"Which conclusion matches the details in the "
        f"{cases[1]['label'].replace('-', ' ')} story?"
    )
    guided: list[dict[str, Any]] = []
    for variant_index in range(1, 5):
        case_index = (variant_index - 1) % len(cases)
        case = cases[case_index]
        actor = core_actors[case_index]
        prompt = (
            f"Read the {case['label'].replace('-', ' ')} story. "
            f"{spec['guided_prompt']} Point to the detail that helped you decide."
        )
        if variant_index <= 2:
            guided.append(
                _choice_case(
                    spec=spec,
                    cases=cases,
                    case_index=case_index,
                    actor=actor,
                    prompt=prompt,
                    skills=[first_skill],
                )
            )
        else:
            guided.append(
                _open_case(
                    spec=spec,
                    case=case,
                    actor=actor,
                    prompt=prompt,
                    skills=skills,
                    phase="guided",
                    index=variant_index,
                )
            )

    independent = []
    for variant_index in range(1, 5):
        actor = core_actors[(level_index + variant_index) % len(core_actors)]
        case = _fresh_case(
            spec=spec,
            phase="independent",
            index=variant_index,
            actor=actor,
        )
        independent.append(
            _open_case(
                spec=spec,
                case=case,
                actor=actor,
                prompt=(
                    f"Read the {case['label']} story. {spec['independent_prompt']} "
                    "Use two details from this story."
                ),
                skills=skills,
                phase="independent",
                index=variant_index,
            )
        )

    transfer = []
    for variant_index in range(1, 5):
        actor = transfer_actors[(level_index + variant_index) % len(transfer_actors)]
        case = _fresh_case(
            spec=spec,
            phase="transfer",
            index=variant_index,
            actor=actor,
        )
        transfer.append(
            _open_case(
                spec=spec,
                case=case,
                actor=actor,
                prompt=(
                    f"Try the {case['label']} story. {spec['transfer_prompt']} "
                    "Explain how the details support your answer."
                ),
                skills=skills,
                phase="transfer",
                index=variant_index,
            )
        )

    review = []
    for variant_index in range(1, 5):
        actor = transfer_actors[(level_index + variant_index + 2) % len(transfer_actors)]
        case = _fresh_case(
            spec=spec,
            phase="review",
            index=variant_index,
            actor=actor,
        )
        review.append(
            _open_case(
                spec=spec,
                case=case,
                actor=actor,
                prompt=(
                    f"Read the {case['label']} story. {spec['review_prompt']} "
                    "Check the meaning and the detail that proves it."
                ),
                skills=skills,
                phase="review",
                index=variant_index,
            )
        )

    support = []
    for index in range(1, 6):
        actor = core_actors[(level_index + index + 1) % len(core_actors)]
        case = _fresh_case(
            spec=spec,
            phase="support",
            index=index,
            actor=actor,
        )
        support.append(
            _support_task(
                spec=spec,
                case=case,
                actor=actor,
                index=index,
                skills=skills,
            )
        )
    authored = {
        **spec,
        "co_construct": _choice_case(
            spec=spec,
            cases=cases,
            case_index=0,
            actor=core_actors[0],
            prompt=co_prompt,
            skills=[first_skill],
        ),
        "guided": guided,
        "independent": independent,
        "transfer": transfer,
        "review": review,
        "support": support,
    }
    level_payload = _level(authored)
    level_payload["misconception_clusters"][0]["remediation"] = (
        f"First, identify the exact error described here: {spec['misconception']} "
        f"Then, work through a different example by applying this repair: "
        f"{spec['remediation']} Finally, remove the scaffold and answer a new "
        "case independently, checking both parts of the response."
    )
    support_names = (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    progression = (
        "name the first useful detail",
        "compare the action with the ending",
        "explain the two linked ideas",
        "solve the new example with one short hint",
        "complete the response without a hint",
    )
    coaching = {
        "reading.word_meaning_context": "A topic guess is not enough; the nearby action and result must fit the meaning.",
        "reading.paragraph_main_idea": "One small detail cannot cover the whole story; include the action and its purpose.",
        "reading.event_sequence": "The result cannot happen before the action that causes it.",
        "reading.inference_reason": "A reason must name the visible choice and the change that followed.",
        "grammar.noun_verb_adjective": "Check each word's job in the complete sentence before naming its type.",
        "reading.sentence_comprehension": "Keep the actor, action, and result together when shortening the story.",
        "reading.poetic_language": "Use the sound or comparison in the line; do not treat an image as a real event.",
        "reading.dialogue_attribution": "Follow the speech marks so each idea stays with the correct speaker.",
        "grammar.question_formation": "A question needs an asking word, a complete thought, and a question mark.",
        "grammar.punctuation_capitalization": "Mark the beginning, pauses, and ending so the order stays clear.",
        "grammar.tense_usage": "A finished-time clue needs a past verb, including irregular forms.",
        "grammar.connectors_because_and_but": "Use because for a reason and but for a contrast.",
        "grammar.prepositions": "Choose the position word that matches the exact place in the story.",
        "vocab.spelling": "Say the word slowly, then check every written letter and its position.",
        "grammar.sentence_order": "Place the actor before the action and finish the complete thought with punctuation.",
        "vocab.word_formation": "Keep the opening consonants and the word's meaning together.",
    }
    coaching_text = coaching.get(
        first_skill,
        "Match each part of the answer with a detail in the new story.",
    )
    for support_index, name in enumerate(support_names, start=1):
        activity = level_payload["support_checks"][name]
        activity["teaching_block"] = (
            f"Start with: find the action and what changed in this story. Think: "
            f"{coaching_text} Next: {progression[support_index - 1]}."
        )
    phase_activities = {
        "co_construct": [level_payload["co_construct"]],
        "guided": level_payload["guided_variants"],
        "independent": level_payload["independent_variants"],
        "transfer": level_payload["transfer_variants"],
        "review": level_payload["review_variants"],
    }
    phase_directions = {
        "co_construct": "Compare the choices with one exact clue before selecting.",
        "guided": "Follow one clue, then check the answer against the result.",
        "independent": "Use two story details and complete the answer on your own.",
        "transfer": "Use the same skill in this new setting without copying an earlier answer.",
        "review": "Recheck the meaning, evidence, and final response before finishing.",
    }
    for phase_name, phase_items in phase_activities.items():
        for activity in phase_items:
            story = _semantic_story_label(activity)
            coaching_clause = coaching_text[0].lower() + coaching_text[1:]
            activity["teaching_block"] = (
                f"In the {story} story, {coaching_clause} "
                f"{phase_directions[phase_name]}"
            )
    lesson_activities = [
        activity
        for phase_items in phase_activities.values()
        for activity in phase_items
    ]
    activities = [
        *lesson_activities,
        *level_payload["support_checks"].values(),
    ]
    for activity in activities:
        _raise_rubric_quality(activity)
    return level_payload


def _assessment_scene(
    chapter_id: str,
    form: str,
    form_slot: int,
) -> dict[str, str]:
    scenes = CHAPTER_ASSESSMENT_SCENES[chapter_id][form]
    if len(scenes) != 15:
        raise ValueError(f"assessment_form_requires_fifteen_scenes:{chapter_id}:{form}")
    raw = scenes[form_slot - 1]
    setting, subject, preparation, action, result = raw
    return {
        "setting": setting,
        "subject": subject,
        "preparation": preparation,
        "action": action,
        "result": result,
    }


def _assessment_word_target(case: dict[str, str]) -> str:
    _, answer = _render(case, "The learner")
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", answer)
    if not words:
        raise ValueError("assessment_word_target_missing")
    if [word.casefold() for word in words[:2]] == ["the", "learner"]:
        return case["label"].split()[0].replace("-", " ").casefold()
    word_index = 1 if words[0].casefold() in {"a", "an", "the"} else 0
    return words[word_index].casefold()


def _assessment_definition(
    target: str,
    *,
    form: str,
    required: bool,
) -> str:
    glosses = (
        ASSESSMENT_WORD_GLOSSES if form == "a" else ASSESSMENT_WORD_GLOSSES_B
    )
    if target in glosses:
        return glosses[target]
    if required:
        raise ValueError(f"missing_assessment_word_gloss:{target}")
    return "the story's key idea"


def _assessment_language_feature(
    *,
    level_id: str,
    form: str,
    form_slot: int,
    subject: str,
) -> dict[str, str] | None:
    if level_id == "fit_double_letter_spelling":
        word, doubled = (
            ("balloon", "ll") if form == "a" else ("coffee", "ff")
        )
        return {
            "target": word,
            "definition": f"a correctly written word containing double {doubled}",
            "detail": (
                (
                    f"The activity card uses the word {word} and circles its double "
                    f"letter {doubled}. {subject} checks the spelling before writing a new sentence."
                )
                if form == "a"
                else (
                    f"On a word strip, {subject} finds {doubled} repeated inside {word}. "
                    "A left-to-right check keeps both matching letters in place."
                )
            ),
            "answer": (
                (
                    f"{subject} spells {word} with the double letter {doubled}. The "
                    f"spelling is correct because both repeated letters appear in {word}."
                )
                if form == "a"
                else (
                    f"After checking each position, {subject} keeps the pair {doubled} in {word}. "
                    "Dropping either matching letter would make the spelling incorrect."
                )
            ),
            "kind": "double_letter",
        }
    if level_id == "fit_poetic_balanced_plan":
        first, second = ("hill", "still") if form == "a" else ("moon", "tune")
        return {
            "target": first,
            "definition": f"a word that rhymes with {second}",
            "detail": (
                (
                    f"A two-line plan ends with {first} and {second}. The matching "
                    "ending sounds create a rhyme and make the healthy plan easy to remember."
                )
                if form == "a"
                else (
                    f"The last words in a short verse are {first} and {second}. "
                    "Their shared sound pattern adds rhythm to advice about active and quiet time."
                )
            ),
            "answer": (
                (
                    f"The words {first} and {second} rhyme because their ending sounds "
                    "match. The rhyme gives the movement-and-rest plan a memorable beat."
                )
                if form == "a"
                else (
                    f"The matching final sounds in {first} and {second} form a rhyme. "
                    "That sound link makes the balanced advice flow smoothly."
                )
            ),
            "kind": "rhyme",
        }
    if level_id == "lagori_word_unscrambling":
        scrambled, sentence = (
            ("cones / counted / Mira / the", "Mira counted the cones.")
            if form == "a"
            else ("signal / heard / Ravi / the", "Ravi heard the signal.")
        )
        return {
            "target": "unscramble",
            "definition": "put mixed words into a meaningful sentence",
            "detail": (
                (
                    f"A word strip says, 'Scrambled words: {scrambled}.' "
                    "To unscramble the line, the first word needs a capital letter and the finished sentence needs a full stop."
                )
                if form == "a"
                else (
                    f"Mixed tiles show '{scrambled}.' To unscramble them, "
                    "the naming part must lead into the action before the ending mark is added."
                )
            ),
            "answer": (
                (
                    f"The unscrambled sentence is '{sentence}' The words now form a "
                    "complete idea with the actor before the action and correct punctuation."
                )
                if form == "a"
                else (
                    f"Reordering every tile gives '{sentence}' The arrangement now "
                    "states who acts, what happens, and where the sentence finishes."
                )
            ),
            "kind": "unscramble",
        }
    if level_id == "hekko_homophones":
        first, second = ("sea", "see") if form == "a" else ("brake", "break")
        return {
            "target": first,
            "definition": f"a word sounding like {second} but carrying another meaning",
            "detail": (
                (
                    f"The language board pairs {first} with {second}. They are "
                    "homophones: they sound alike, but their spellings and meanings are different."
                )
                if form == "a"
                else (
                    f"A sentence test compares {first} and {second}. Their sound matches, "
                    "yet only one spelling carries the meaning needed by its sentence."
                )
            ),
            "answer": (
                (
                    f"{first} and {second} are homophones because they sound alike. "
                    "Their different spellings show that the two words have different meanings."
                )
                if form == "a"
                else (
                    f"The pair {first} and {second} shares a pronunciation, so it is a "
                    "homophone pair. Context separates the meaning attached to each spelling."
                )
            ),
            "kind": "homophone",
        }
    if level_id == "hekko_clusters_and_animal_sounds":
        sound, cluster, animal = (
            ("bellow", "bl", "cow")
            if form == "a"
            else ("squeal", "squ", "pig")
        )
        return {
            "target": sound,
            "definition": f"the sound made by a {animal}",
            "detail": (
                (
                    f"A {animal} can make the animal sound {sound}. At the start of {sound}, "
                    f"the letters {cluster} form a cluster and both consonants can be heard."
                )
                if form == "a"
                else (
                    f"Beside a {animal}, an animal sound card shows {sound}. The opening letters "
                    f"{cluster} blend while each consonant can still be noticed."
                )
            ),
            "answer": (
                (
                    f"The animal sound {sound} belongs to a {animal}. Its opening "
                    f"consonant cluster is {cluster}, with the consonant sounds joined at the start."
                )
                if form == "a"
                else (
                    f"A {animal} can make the sound {sound}. At the word's beginning, "
                    f"{cluster} forms a consonant cluster whose sounds blend together."
                )
            ),
            "kind": "animal_cluster",
        }
    return None


def _assessment_skill_evidence(
    *,
    form: str,
    skill_id: str,
    scene: dict[str, str],
) -> str:
    if form == "b":
        if skill_id in {
            "reading.word_meaning_context",
            "vocab.chapter_word_usage",
            "vocab.word_formation",
            "vocab.spelling",
        }:
            return (
                f"Near the ending, a label defines {scene['target']} as "
                f"'{scene['definition']}'. The situation shows why that definition belongs."
            )
        if skill_id == "reading.poetic_language":
            return (
                f"The closing caption compares {scene['subject']}'s solution to a path "
                "linking a difficulty with an improved situation. It describes an idea rather than a real path."
            )
        if skill_id in {"reading.dialogue_attribution", "writing.dialogue"}:
            return (
                f"'What helped the group most?' asked the coach. The captain replied, "
                f"'{scene['subject']} {scene['action']}.'"
            )
        if skill_id == "grammar.prepositions":
            return (
                f"The activity sign stood above the result card, which rested near "
                f"{scene['subject']}'s bag."
            )
        if skill_id == "grammar.question_formation":
            return (
                f"A classmate plans to ask why the ending changed after {scene['subject']}'s action. "
                "The written line needs an asking word and the correct end mark."
            )
        if skill_id == "grammar.noun_verb_adjective":
            return (
                f"Another sentence reads, 'A patient {scene['subject']} moved the light cone.' "
                "It includes words that name, show action, and describe."
            )
        if skill_id == "grammar.sentence_order":
            return (
                f"The mixed strip reads 'the / idea / {scene['subject']} / clearly / explained.' "
                "Its words need to form one complete actor-action thought."
            )
        if skill_id == "grammar.punctuation_capitalization":
            return (
                f"The line '{scene['subject']} finished the check everyone smiled' "
                "needs a capital and a clear break between its thoughts."
            )
        if skill_id == "grammar.pronouns":
            return (
                f"The sentence '{scene['subject']} finished the plan before sharing it' "
                f"uses it to refer to the plan."
            )
        return (
            f"One closing line connects the choice made by {scene['subject']} with the later condition. "
            "Readers can trace the aim, the change, and the finish."
        )
    if skill_id in {
        "reading.word_meaning_context",
        "vocab.chapter_word_usage",
        "vocab.word_formation",
        "vocab.spelling",
    }:
        return (
            f"A small sign uses {scene['target']} and explains it through the "
            f"nearby clue '{scene['definition']}'."
        )
    if skill_id == "reading.poetic_language":
        return (
            f"A short line calls {scene['subject']}'s plan a bridge from the "
            "first problem to the improved ending. The line describes a connection, not a real bridge."
        )
    if skill_id in {"reading.dialogue_attribution", "writing.dialogue"}:
        question = (
            "Which choice changed the ending?"
            if form == "a"
            else "What helped the group most?"
        )
        return (
            f"'{question}' asked the captain. '{scene['subject']} "
            f"{scene['action']},' replied the scorer."
        )
    if skill_id == "grammar.prepositions":
        return (
            f"At the end, the result card lay beside {scene['subject']}'s bag "
            "and below the activity sign."
        )
    if skill_id == "grammar.question_formation":
        return (
            f"A teammate wants to ask how {scene['subject']}'s action led to the ending. "
            "The question must begin with a capital letter and end with a question mark."
        )
    if skill_id == "grammar.noun_verb_adjective":
        return (
            f"A language line says, 'The careful {scene['subject']} checked the bright marker.' "
            "The line contains naming, action, and describing words."
        )
    if skill_id == "grammar.sentence_order":
        return (
            f"A word strip shows 'carefully / {scene['subject']} / the / plan / checked.' "
            "The words need an actor-first order and a full stop."
        )
    if skill_id == "grammar.punctuation_capitalization":
        return (
            f"One unmarked line reads '{scene['subject']} checked the plan then the team began'. "
            "Its name and sentence boundary need clear marks."
        )
    if skill_id == "grammar.pronouns":
        return (
            f"A later sentence says, '{scene['subject']} checked the plan before they shared it.' "
            f"The pronoun they refers to {scene['subject']}."
        )
    return (
        f"A final sentence joins {scene['subject']}'s action with the change that followed. "
        "The beginning, choice, and ending all appear in the story."
    )


def _assessment_passage(
    *,
    chapter_id: str,
    form: str,
    form_slot: int,
    level_index: int,
    skill_id: str,
    level: dict[str, Any],
    case: dict[str, str],
) -> tuple[str, dict[str, str]]:
    scene = _assessment_scene(chapter_id, form, form_slot)
    special = _assessment_language_feature(
        level_id=level["level_id"],
        form=form,
        form_slot=form_slot,
        subject=scene["subject"],
    )
    requires_gloss = skill_id in {
        "reading.word_meaning_context",
        "vocab.chapter_word_usage",
        "vocab.word_formation",
        "vocab.spelling",
    }
    target = (
        special["target"]
        if special is not None
        else (
            _assessment_word_target(case)
            if requires_gloss
            else case["label"].split()[0].replace("-", " ")
        )
    )
    scene = {
        **scene,
        "target": target,
        "definition": (
            special["definition"]
            if special is not None
            else _assessment_definition(
                target,
                form=form,
                required=requires_gloss,
            )
        ),
        "special_answer": special["answer"] if special is not None else "",
        "special_kind": special["kind"] if special is not None else "",
        "materials": (
            (
                "a boundary rope, two cloth bands, chalk, and a whistle"
                if form == "a"
                else "four cones, two cloth bands, a soft ball, and a whistle"
            )
            if chapter_id == "eng_c4_ch09"
            else (
                "five cones, two beanbags, a boundary rope, and a whistle"
                if form == "a"
                else "four cones, a beanbag, a boundary rope, and a whistle"
            )
        ),
    }
    skill_evidence = (
        special["detail"]
        if special is not None
        else _assessment_skill_evidence(
            form=form,
            skill_id=skill_id,
            scene=scene,
        )
    )
    if skill_id == "writing.procedure":
        skill_evidence = (
            f"The materials laid out are {scene['materials']}. {skill_evidence}"
        )
    if form == "a":
        passage = (
            f"On a busy morning at the {scene['setting']}, {scene['subject']} "
            f"{scene['preparation']}. Two classmates walked around the area, "
            f"named the aim in one sentence, and nodded when ready. Next, {scene['subject']} "
            f"{scene['action']}. The group watched what changed instead of guessing. "
            f"As a result, {scene['result']}. {skill_evidence} Before leaving, "
            "the classmates retold the event from its opening moment to its final change. "
            "Their short retelling included no invented action."
        )
    else:
        passage = (
            f"One afternoon at the {scene['setting']}, {scene['subject']} "
            f"{scene['preparation']}. A partner described the starting condition "
            "and asked what could improve by the finish. Later, "
            f"{scene['subject']} {scene['action']}. Everyone compared the later "
            f"condition with the beginning. Consequently, {scene['result']}. "
            f"{skill_evidence} At the end, the partner explained which choice "
            "mattered and why the ending made sense. No extra event was added to the story."
        )
    return passage, scene


def _assessment_prompt(
    *,
    form: str,
    form_slot: int,
    skill_id: str,
) -> str:
    if form == "a":
        return (
            f"Read Story A{form_slot}. Write an answer that "
            f"{SKILL_DIRECTIONS[skill_id]}. Use the story details."
        )
    return (
        f"Read Story B{form_slot}. {SKILL_DIRECTIONS_B[skill_id].capitalize()}. "
        "Show how the story supports your answer."
    )


def _assessment_normal_answer(
    *,
    skill_id: str,
    scene: dict[str, str],
) -> str:
    subject = scene["subject"]
    target = scene["target"]
    if scene.get("special_answer"):
        return scene["special_answer"]
    if skill_id == "reading.event_sequence":
        return (
            f"First, {subject} {scene['preparation']}. Next, {subject} "
            f"{scene['action']}. Finally, {scene['result']}."
        )
    if skill_id == "reading.paragraph_main_idea":
        return (
            f"The main idea is that {subject} prepared carefully and made a "
            f"useful choice, so {scene['result']}. This idea covers the whole story."
        )
    if skill_id in {"reading.inference_reason", "writing.reason_answer"}:
        return (
            f"{subject} made an effective choice because {subject} "
            f"{scene['action']}. That choice led to this result: {scene['result']}."
        )
    if skill_id == "reading.word_meaning_context":
        return (
            f"In this story, {target} means {scene['definition']}. That meaning "
            "fits because the nearby action supports it while the explanation "
            "confirms it."
        )
    if skill_id in {"vocab.chapter_word_usage", "vocab.word_formation", "vocab.spelling"}:
        return (
            f"The word {target} fits because it means {scene['definition']}. "
            f"{subject} uses it in a complete sentence that keeps the same meaning."
        )
    if skill_id == "grammar.question_formation":
        return f"How did {subject}'s action help the group reach the ending?"
    if skill_id == "grammar.tense_usage":
        return (
            f"Earlier, {subject} {scene['preparation']}. Later, {subject} "
            f"{scene['action']}. Both verbs describe finished actions."
        )
    if skill_id == "grammar.prepositions":
        return (
            f"The result card lay beside {subject}'s bag and below the activity "
            "sign. Both prepositions show its exact position."
        )
    if skill_id == "grammar.connectors_because_and_but":
        return (
            f"{subject} changed the plan because {subject} noticed the starting "
            f"problem, but the activity still stayed enjoyable. As a result, {scene['result']}."
        )
    if skill_id == "grammar.noun_verb_adjective":
        return (
            f"In 'The careful {subject} checked the bright marker,' {subject} "
            "and marker are nouns, checked is the verb, and careful and bright are adjectives."
        )
    if skill_id == "grammar.sentence_order":
        return f"{subject} checked the plan carefully. The ordered words form a complete sentence."
    if skill_id == "grammar.punctuation_capitalization":
        return (
            f"{subject} checked the plan. Then the team began. Both sentences "
            "start with capitals and end with full stops."
        )
    if skill_id == "reading.dialogue_attribution":
        return (
            f"The captain asks which choice mattered. The scorer answers that "
            f"{subject} {scene['action']}, linking the speaker to the important action."
        )
    if skill_id == "reading.poetic_language":
        return (
            f"The bridge image is figurative because {subject}'s plan is not a "
            f"real bridge. It shows how the action leads to this ending: {scene['result']}."
        )
    if skill_id == "reading.sentence_comprehension":
        return (
            f"{subject} is the actor. The key action is that {subject} "
            f"{scene['action']}. The result is that {scene['result']}."
        )
    if skill_id in {"writing.summary_own_words", "research.information_selection"}:
        return (
            f"After preparing carefully, {subject} {scene['action']}. This led "
            f"to the stated ending: {scene['result']}. The summary adds no new event."
        )
    if skill_id == "writing.complete_sentence":
        return f"{subject} {scene['action']}, so {scene['result']}."
    if skill_id == "writing.compare_contrast":
        return (
            f"Both the preparation and the later action helped {subject}, but "
            "only the later action directly produced the ending."
        )
    if skill_id == "grammar.pronouns":
        return f"{subject} checked the plan before they shared it with the group."
    if skill_id == "writing.dialogue":
        return (
            f"\"Which choice mattered most?\" asked the captain. The scorer replied, "
            f"\"{subject} {scene['action']}, so {scene['result']}.\""
        )
    return (
        f"{subject} began by preparing carefully and then {scene['action']}. "
        f"The story ends when {scene['result']}."
    )


def _assessment_paragraph_authority(
    *,
    level: dict[str, Any],
    scene: dict[str, str],
) -> tuple[str, list[tuple[str, str, list[str]]], int, bool]:
    opening = (
        f"The {scene['setting']} story shows how one thoughtful choice can improve an activity"
    )
    support = (
        f"First, {scene['subject']} {scene['preparation']} before the group began"
    )
    link = (
        f"In addition, {scene['subject']} {scene['action']}, so {scene['result']}"
    )
    closing = (
        "Overall, the linked details explain why careful preparation and action led to a useful ending"
    )
    descriptions = [
        "Uses an opening sentence that establishes one paragraph focus.",
        "Adds a relevant support sentence from the visible story.",
        "Uses a linking expression before a second story detail.",
        "Ends with a punctuated closing sentence tied to the opening.",
    ]
    model_answer = ". ".join((opening, support, link, closing)) + "."
    return (
        model_answer,
        _evidence_for_claims(
            case_label=scene["target"],
            claims=[opening, support, link, closing],
            descriptions=descriptions,
        ),
        45,
        False,
    )


def _assessment_procedure_authority(
    *,
    level: dict[str, Any],
    scene: dict[str, str],
) -> tuple[str, list[tuple[str, str, list[str]]], int, bool]:
    materials = f"Materials: {scene['materials']}"
    ordered = (
        f"First, {scene['subject']} {scene['preparation']}. Next, place the listed "
        f"equipment in the prepared area. Then, {scene['subject']} {scene['action']}"
    )
    safety = (
        "For safety, leave two arm lengths between players, use controlled "
        "movement, and stop as soon as the whistle sounds"
    )
    result = (
        f"Finally, put away the equipment and confirm the observed ending: {scene['result']}"
    )
    descriptions = [
        "Names all materials required before the procedure starts.",
        "Presents preparation and action as ordered steps with explicit punctuation.",
        "Includes a specific safety distance and stop condition.",
        "Uses punctuation in a final result step that completes the procedure.",
    ]
    model_answer = ". ".join((materials, ordered, safety, result)) + "."
    return (
        model_answer,
        _evidence_for_claims(
            case_label=scene["target"],
            claims=[materials, ordered, safety, result],
            descriptions=descriptions,
        ),
        50,
        True,
    )


def _assessment_authority(
    *,
    skill_id: str,
    level: dict[str, Any],
    scene: dict[str, str],
) -> tuple[str, list[tuple[str, str, list[str]]], int, bool]:
    if skill_id == "writing.paragraph":
        return _assessment_paragraph_authority(level=level, scene=scene)
    if skill_id == "writing.procedure":
        return _assessment_procedure_authority(level=level, scene=scene)
    answer = _assessment_normal_answer(skill_id=skill_id, scene=scene)
    minimum = max(8, min(14, len(answer.split())))
    ordered = skill_id == "reading.event_sequence"
    evidence = _evidence_for_claims(
        case_label=scene["target"],
        claims=_claim_parts(answer, ordered=ordered),
    )
    return answer, evidence, minimum, ordered


def _assessment_open(
    *,
    chapter_id: str,
    item_no: int,
    form: str,
    form_slot: int,
    level_index: int,
    skill_id: str,
    level: dict[str, Any],
    case: dict[str, str],
) -> dict[str, Any]:
    passage, scene = _assessment_passage(
        chapter_id=chapter_id,
        form=form,
        form_slot=form_slot,
        level_index=level_index,
        skill_id=skill_id,
        level=level,
        case=case,
    )
    answer, evidence, minimum, ordered = _assessment_authority(
        skill_id=skill_id,
        level=level,
        scene=scene,
    )
    terms = _terms(answer)
    criterion_prefix = f"{chapter_id}:assessment:{item_no:02d}"
    criteria = []
    slots = []
    for index, (_, description, aliases) in enumerate(evidence, start=1):
        slot_id = f"{criterion_prefix}:claim-{index}"
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": 0.75,
            }
        )
        slots.append(
            {
                "id": slot_id,
                "description": description,
                "any_of": aliases,
            }
        )
    interaction_type = {
        "writing.paragraph": "paragraph_text",
        "writing.summary_own_words": "summary",
        "writing.dialogue": "dialogue",
        "writing.procedure": "paragraph_text",
        "writing.reason_answer": "evidence_text",
        "writing.complete_sentence": "short_text",
    }.get(skill_id, "evidence_text")
    payload: dict[str, Any] = {
        "kind": "open_response",
        "activity_id": f"{chapter_id}:assessment:{item_no:02d}",
        "teaching_block": "Read the new story carefully and answer in your own words.",
        "passage": passage,
        "prompt": _assessment_prompt(
            form=form,
            form_slot=form_slot,
            skill_id=skill_id,
        ),
        "skill_ids": [skill_id],
        "interaction_type": interaction_type,
        "rubric_criteria": criteria,
        "concept_slots": slots,
        "forbidden_phrases": [
            "The passage does not matter",
            "I copied the model answer",
        ],
        "min_response_words": minimum,
        "relevance_terms": terms,
        "model_answer": answer,
        "pass_score": 0.8,
    }
    if ordered:
        payload["ordered_concept_slot_ids"] = [slot["id"] for slot in slots]
    return payload


def _assessment_distractors(
    *,
    skill_id: str,
    scene: dict[str, str],
    form: str,
) -> list[str]:
    subject = scene["subject"]
    preparation = scene["preparation"]
    action = scene["action"]
    result = scene["result"]
    target = scene["target"]
    special_kind = scene.get("special_kind")
    if special_kind == "double_letter":
        return [
            f"{subject} removes one repeated letter from {target}, even though the activity card circles both letters.",
            f"{subject} keeps the sound of {target} but changes its double-letter spelling on the activity card.",
            f"{subject} copies the {scene['setting']} name instead of spelling the double-letter word {target}.",
        ]
    if special_kind == "rhyme":
        return [
            f"The two line-ending words at the {scene['setting']} have unrelated sounds, so the plan has no rhyme.",
            f"The words rhyme only because {subject} writes them on the same activity card.",
            f"The rhyme describes the colour of the {scene['setting']} instead of the movement-and-rest plan.",
        ]
    if special_kind == "unscramble":
        return [
            f"The scrambled words should begin with the action and place {subject} after the full stop.",
            f"The word strip at the {scene['setting']} is complete without arranging an actor before the action.",
            f"At the {scene['setting']}, {subject} should keep the scrambled order because punctuation alone gives the words clear meaning.",
        ]
    if special_kind == "homophone":
        return [
            f"The paired words on the {scene['setting']} board are identical in spelling as well as sound.",
            f"The two homophones have the same meaning because {subject} hears the same sound.",
            f"At the {scene['setting']}, the homophone pair changes meaning only when {subject} says the words more loudly.",
        ]
    if special_kind == "animal_cluster":
        return [
            f"The animal-sound word {target} ends with the consonant cluster shown at the {scene['setting']}.",
            f"{target} names the animal itself, not the sound heard by {subject} in the activity.",
            f"The opening letters in {target} make one vowel sound instead of a consonant cluster.",
        ]
    if skill_id == "reading.event_sequence":
        return [
            f"First, {subject} {action}. Next, {subject} {preparation}. Finally, {result}.",
            f"First, {result}. Next, {subject} {preparation}. Finally, {subject} {action}.",
            f"First, {subject} {preparation}. Next, {result}. Finally, {subject} {action}.",
        ]
    if skill_id == "reading.paragraph_main_idea":
        return [
            f"The story mainly describes the {scene['setting']} and treats the later result, '{result}', as an unimportant detail.",
            f"The main idea is only that {subject} {preparation}; it leaves out how {subject} {action}.",
            f"The story is only about how {subject} {action}, so the changed result, '{result}', does not belong in its main idea.",
        ]
    if skill_id in {
        "reading.word_meaning_context",
        "vocab.chapter_word_usage",
        "vocab.word_formation",
        "vocab.spelling",
    }:
        return [
            f"In this story, {target} means the name of the {scene['setting']}, not {scene['definition']}.",
            f"At the {scene['setting']}, {target} describes only how {subject} {preparation}, not its stated meaning.",
            f"{subject} uses {target} to mean the opposite of the clue '{scene['definition']}'.",
        ]
    if skill_id == "grammar.noun_verb_adjective":
        return [
            f"In the {scene['setting']} language line, careful names the action and checked describes the bright marker.",
            f"In {subject}'s {scene['setting']} sentence, marker shows the action and bright names the careful helper.",
            f"The {scene['setting']} language line treats helper and marker as describing words, with checked as a naming word.",
        ]
    if skill_id == "grammar.question_formation":
        return [
            f"How {subject}'s action changed the ending.",
            f"{subject} changed the ending at the {scene['setting']}?",
            f"Why did the ending change at the {scene['setting']}.",
        ]
    if skill_id == "grammar.prepositions":
        return [
            f"The result card floated through {subject}'s bag and the activity sign.",
            f"The result card stood during the {scene['setting']} and became the sign.",
            f"The activity sign lay inside {subject}, while the result card became a bag.",
        ]
    if skill_id == "grammar.sentence_order":
        return [
            f"Carefully the plan {subject} checked.",
            f"The plan carefully checked {subject}.",
            f"Checked carefully {subject} the plan.",
        ]
    if skill_id == "grammar.punctuation_capitalization":
        return [
            f"{subject.lower()} checked the plan then the team began",
            f"{subject} checked the plan, then the team began?",
            f"{subject} checked the plan then, The team began.",
        ]
    if skill_id == "reading.dialogue_attribution":
        return [
            f"{subject} asks the question, while the captain answers by naming the action at the {scene['setting']}.",
            f"The scorer asks about the {scene['setting']}, but nobody names {subject}'s important action.",
            f"At the {scene['setting']}, the captain and scorer both say that {subject}'s preparation happened after the result.",
        ]
    if skill_id == "reading.poetic_language":
        return [
            f"{subject} built a real bridge inside the {scene['setting']} before the activity could end.",
            f"The bridge image describes only the colour of the {scene['setting']} and not {subject}'s plan.",
            f"The story says {subject}'s action blocked every path to the ending instead of connecting the two ideas.",
        ]
    if skill_id == "reading.sentence_comprehension":
        return [
            f"The {scene['setting']} is the actor, while the words '{subject} {action}' describe only a result.",
            f"The preparation '{preparation}' is the ending, while the actual result '{result}' is the person who acts.",
            f"The sentence says nobody acted at the {scene['setting']}, although the story states that {subject} {action}.",
        ]
    variant = (
        f"{subject}'s preparation alone caused the ending before the later action at the {scene['setting']}."
        if form == "a"
        else f"The ending at the {scene['setting']} happened before {subject} made the important choice."
    )
    return [
        variant,
        f"{subject} {action}, but the story ends with the opposite of this result: {result}.",
        f"The {scene['setting']} matters more than {subject}'s preparation, action, and stated ending.",
    ]


def _assessment_choice(
    *,
    chapter_id: str,
    item_no: int,
    form: str,
    form_slot: int,
    level_index: int,
    skill_id: str,
    level: dict[str, Any],
    case_index: int,
) -> dict[str, Any]:
    cases = level["cases"]
    passage, scene = _assessment_passage(
        chapter_id=chapter_id,
        form=form,
        form_slot=form_slot,
        level_index=level_index,
        skill_id=skill_id,
        level=level,
        case=cases[case_index],
    )
    answer = _assessment_normal_answer(skill_id=skill_id, scene=scene)
    distractors = _assessment_distractors(
        skill_id=skill_id,
        scene=scene,
        form=form,
    )
    raw_options = [answer, *distractors]
    shift = item_no % len(raw_options)
    options = raw_options[shift:] + raw_options[:shift]
    return {
        "kind": "selected_option",
        "activity_id": f"{chapter_id}:assessment:{item_no:02d}",
        "teaching_block": "Read the new story, then compare every option with its details.",
        "passage": passage,
        "prompt": _assessment_prompt(
            form=form,
            form_slot=form_slot,
            skill_id=skill_id,
        ),
        "skill_ids": [skill_id],
        "options": options,
        "accepted_answers": [answer],
    }


def build_assessment(
    chapter_id: str,
    level_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    skill_to_level: dict[str, dict[str, Any]] = {}
    level_positions = {
        level["level_id"]: index for index, level in enumerate(level_specs)
    }
    ordered_skills: list[str] = []
    for level in level_specs:
        for skill_id in level["skill_ids"]:
            if skill_id in skill_to_level:
                raise ValueError(f"class4_skill_repeated_across_levels:{skill_id}")
            if skill_id not in SKILL_DIRECTIONS:
                raise ValueError(f"class4_skill_direction_missing:{skill_id}")
            skill_to_level[skill_id] = level
            ordered_skills.append(skill_id)
    if not 8 <= len(ordered_skills) <= 15:
        raise ValueError("class4_assessed_skill_count_out_of_range")

    items: list[dict[str, Any]] = []
    item_no = 0
    receptive_skills = [
        skill_id
        for skill_id in ordered_skills
        if not skill_id.startswith(PRODUCTIVE_PREFIXES)
        and skill_id not in SEMANTIC_OPEN_SKILLS
    ]
    for form_index in range(2):
        form = "a" if form_index == 0 else "b"
        form_items: list[dict[str, Any]] = []
        for skill_index, skill_id in enumerate(ordered_skills):
            level = skill_to_level[skill_id]
            case_index = (skill_index + form_index * 2) % len(level["cases"])
            item_no += 1
            form_slot = len(form_items) + 1
            must_open = (
                skill_id.startswith(PRODUCTIVE_PREFIXES)
                or skill_id in SEMANTIC_OPEN_SKILLS
            )
            sampled_open = (skill_index + form_index) % 3 == 0
            item = (
                _assessment_open(
                    chapter_id=chapter_id,
                    item_no=item_no,
                    form=form,
                    form_slot=form_slot,
                    level_index=level_positions[level["level_id"]],
                    skill_id=skill_id,
                    level=level,
                    case=level["cases"][case_index],
                )
                if must_open or sampled_open
                else _assessment_choice(
                    chapter_id=chapter_id,
                    item_no=item_no,
                    form=form,
                    form_slot=form_slot,
                    level_index=level_positions[level["level_id"]],
                    skill_id=skill_id,
                    level=level,
                    case_index=case_index,
                )
            )
            form_items.append(item)

        extras_needed = 15 - len(form_items)
        for extra_index in range(extras_needed):
            skill_id = receptive_skills[(form_index * extras_needed + extra_index) % len(receptive_skills)]
            level = skill_to_level[skill_id]
            case_index = (
                len(ordered_skills) + extra_index + form_index * 2
            ) % len(level["cases"])
            item_no += 1
            form_slot = len(form_items) + 1
            form_items.append(
                _assessment_choice(
                    chapter_id=chapter_id,
                    item_no=item_no,
                    form=form,
                    form_slot=form_slot,
                    level_index=level_positions[level["level_id"]],
                    skill_id=skill_id,
                    level=level,
                    case_index=case_index,
                )
            )
        if len(form_items) != 15:
            raise RuntimeError("class4_assessment_form_size_internal_error")
        items.extend(form_items)

    strand_counts = Counter(
        level["level_id"]
        for item in items
        for level in [skill_to_level[item["skill_ids"][0]]]
    )
    strands = []
    for level in level_specs:
        level_items = [
            item
            for item in items
            if item["skill_ids"][0] in set(level["skill_ids"])
        ]
        evidence_forms = []
        if any(item["kind"] == "selected_option" for item in level_items):
            evidence_forms.append("selected_option")
        if any(item["kind"] == "open_response" for item in level_items):
            evidence_forms.append("constructed_response")
        strands.append(
            {
                "strand_id": f"{level['level_id']}:assessment-strand",
                "skill_ids": list(level["skill_ids"]),
                "minimum_items": strand_counts[level["level_id"]],
                "evidence_forms": evidence_forms,
                "remediation_level_ids": [level["level_id"]],
            }
        )
    return {
        "items_per_attempt": 15,
        "pass_score": 0.8,
        "max_attempts": 2,
        "bank_item_count": 30,
        "items": items,
        "strands": strands,
    }


def build_manifest(
    *,
    chapter: dict[str, Any],
    source_anchors: list[dict[str, Any]],
    level_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "chapter": chapter,
        "source_anchors": source_anchors,
        "levels": [
            build_authored_level(spec, index, chapter["chapter_id"])
            for index, spec in enumerate(level_specs)
        ],
        "chapter_assessment": build_assessment(chapter["chapter_id"], level_specs),
    }


# These corrections live in the authoring layer so every generated runtime keeps
# the same explicit teaching, evidence, and grading contract.
_SEMANTIC_SUPPORT_NAMES = (
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
)
_SEMANTIC_SKILL_TEACHING = {
    "reading.word_meaning_context": "Infer the word from a nearby action, description, or result instead of guessing from the topic.",
    "vocab.chapter_word_usage": "Use the target word in a new sentence that keeps the meaning shown by the passage.",
    "reading.paragraph_main_idea": "State one main idea broad enough to cover the opening, key action, and result.",
    "reading.dialogue_attribution": "Track who speaks, what that speaker says, and why the turn matters.",
    "reading.event_sequence": "Use time and cause clues to place every event in supported order.",
    "reading.inference_reason": "Make a claim that follows from the visible action and result.",
    "writing.reason_answer": "Write the claim, a relevant because reason, and the story evidence that supports it.",
    "grammar.noun_verb_adjective": "Identify each word by its job in this sentence, then use the requested word role accurately.",
    "grammar.question_formation": "Choose an answerable question word, put the words in clear order, and use a question mark.",
    "grammar.punctuation_capitalization": "Use capitals and punctuation to make each instruction or sentence unambiguous.",
    "grammar.sentence_order": "Arrange the words and details so the actor, action, and complete thought are clear.",
    "grammar.tense_usage": "Match the verb form to the stated time and keep the sentence complete.",
    "grammar.connectors_because_and_but": "Choose the connector by meaning: because gives a reason, but contrasts, and adds, and or offers a choice.",
    "grammar.prepositions": "Choose each position word from the exact spatial relationship in the passage.",
    "reading.sentence_comprehension": "Resolve who did what before combining the important sentences.",
    "writing.summary_own_words": "Keep the essential actor, action, and result while removing minor details and copying no sentence.",
    "reading.poetic_language": "Explain the sound or comparison, its nonliteral meaning, and the detail that supports it.",
    "writing.paragraph": "Write one focused paragraph with an opening, linked support, and a closing sentence.",
    "writing.procedure": "Write usable materials, ordered steps, a safety rule, and the intended result.",
    "writing.complete_sentence": "Write a complete actor-action thought with accurate grammar and punctuation.",
    "vocab.spelling": "Preserve the requested letter pattern and use the correctly spelled word in context.",
    "vocab.word_formation": "Build or analyse the word one letter group at a time, then check that its meaning still fits.",
}
_SEMANTIC_SKILL_RUBRIC = {
    "reading.word_meaning_context": "Grades a precise context-based meaning supported by a nearby clue.",
    "vocab.chapter_word_usage": "Grades accurate use of the target word in a new complete sentence.",
    "reading.paragraph_main_idea": "Grades one central idea that covers the whole passage rather than one detail.",
    "reading.dialogue_attribution": "Grades correct speaker attribution, spoken fact, and purpose of the turn.",
    "reading.event_sequence": "Grades the complete event order using the passage's time and cause clues.",
    "reading.inference_reason": "Grades a supported inference that follows from the visible action and result.",
    "writing.reason_answer": "Grades a clear claim, relevant reason, and cited story evidence.",
    "grammar.noun_verb_adjective": "Grades each requested word role by its job in the learner's sentence.",
    "grammar.question_formation": "Grades question-word choice, meaningful order, and final question mark.",
    "grammar.punctuation_capitalization": "Grades capitals and punctuation that make the response clear.",
    "grammar.sentence_order": "Grades meaningful actor-action order and a complete thought.",
    "grammar.tense_usage": "Grades a verb form that agrees with the stated time clue.",
    "grammar.connectors_because_and_but": "Grades a connector whose meaning accurately joins the two ideas.",
    "grammar.prepositions": "Grades position words against the exact spatial details.",
    "reading.sentence_comprehension": "Grades accurate resolution of the actor, action, and result.",
    "writing.summary_own_words": "Grades an accurate own-words summary containing only essential events.",
    "reading.poetic_language": "Grades the sound or comparison, its nonliteral meaning, and supporting detail.",
    "writing.paragraph": "Grades a focused paragraph with an opening, linked support, and closing.",
    "writing.procedure": "Grades materials, ordered steps, safety, punctuation, and intended result.",
    "writing.complete_sentence": "Grades a complete grammatical sentence with clear punctuation.",
    "vocab.spelling": "Grades the requested spelling pattern and accurate contextual use.",
    "vocab.word_formation": "Grades the stated letter group and the resulting word's intended meaning.",
}
_SEMANTIC_SUPPORT_STAGE = {
    "bridge": "work through the first corrected example",
    "masterclass": "contrast the tempting mistake with the decisive clue",
    "revision_level_1": "mark the first missing idea",
    "revision_level_2": "join the corrected ideas with one short hint",
    "revision_level_3": "complete the repair independently",
}
_SEMANTIC_IGNORED_WORDS = {
    "about", "after", "answer", "before", "because", "details", "explain",
    "from", "passage", "response", "their", "there", "these", "they", "this",
    "through", "using", "visible", "which", "while", "with", "write",
}
_SEMANTIC_WORD_DISTRACTORS = {
    "swift": ("careful but slow movement", "a repeated beat", "a proud feeling after success"),
    "rhythmic": ("moving without any pattern", "finishing unusually fast", "remaining completely still"),
    "proud": ("worried about an unfinished task", "tired after repeated movement", "unwilling to share credit"),
    "cheerful": ("silent and serious", "careless about the rules", "too tired to encourage anyone"),
    "referee": ("the player who begins every attack", "the captain who chooses team strategy", "the scorer who only records points"),
    "teamwork": ("one player completing every role", "two sides ignoring a shared rule", "players competing without coordination"),
    "dodge": ("stand still and accept contact", "throw directly at another player", "leave the marked area permanently"),
    "opponent": ("a teammate on the same side", "the official enforcing the rules", "a spectator recording the score"),
    "challenger": ("the defender already holding the centre", "the official who ends the round", "a spectator waiting outside the game"),
    "surrender": ("continue after the stop signal", "score without entering the circle", "replace another player before capture"),
    "declared": ("whispered as a private guess", "left unstated until later", "changed without telling either team"),
    "sway": ("remain fixed in one position", "drop suddenly to the ground", "move only in a straight line"),
    "pleasant": ("painful and difficult to continue", "dangerous because control is lost", "confusing because nothing is visible"),
    "descending": ("travelling from low ground upward", "remaining at the highest point", "moving sideways at one height"),
    "distant": ("close enough to touch", "hidden directly underneath", "located inside the current object"),
    "summit": ("the lowest base of a hill", "a sheltered gap between ridges", "a path circling the middle slope"),
    "journey": ("a pause without changing place", "one object carried in a bag", "a view remembered after travel"),
    "load": ("the route chosen between places", "a memory from an earlier trip", "the highest point of a hill"),
    "overhanging": ("resting entirely below another object", "standing far away with no projection", "lying flat at ground level"),
    "high": ("close to the lowest ground", "hidden beneath the floor", "level with the river bank"),
    "wise": ("chosen without checking any evidence", "likely to create avoidable harm", "based only on a hurried guess"),
    "fortress": ("an open market without defences", "a temporary cloth shelter", "a narrow path between fields"),
    "unique": ("identical to every comparison", "ordinary because it is repeated", "copied without any difference"),
    "bright": ("dim and difficult to see", "colourless under weak light", "hidden behind an opaque cover"),
}


def _iter_manifest_activities(level: dict[str, Any]):
    yield "phase:co_construct", level["co_construct"], "formative"
    for pool_name, evidence_role in (
        ("guided_variants", "supported"),
        ("independent_variants", "certifying"),
        ("transfer_variants", "certifying"),
        ("review_variants", "certifying"),
    ):
        for activity in level[pool_name]:
            yield activity["activity_id"], activity, evidence_role
    for name in _SEMANTIC_SUPPORT_NAMES:
        yield f"check:{name}", level["support_checks"][name], "supported"


def _semantic_words(value: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", value.casefold())


def _semantic_content_words(value: str) -> list[str]:
    return [
        word
        for word in _semantic_words(value)
        if len(word) >= 4 and word not in _SEMANTIC_IGNORED_WORDS
    ]


def _semantic_actor_name(passage: str) -> str:
    ignored = {
        "At", "The", "First", "Next", "Then", "Finally", "On", "In", "As",
        "During", "Before", "Later", "Consequently", "One",
    }
    return next(
        (
            name
            for name in re.findall(r"\b[A-Z][a-z]+\b", passage)
            if name not in ignored
        ),
        "the reader",
    )


def _semantic_story_label(activity: dict[str, Any]) -> str:
    match = re.search(
        r"\b(?:read|try) the (.+?) story\b",
        activity.get("prompt", ""),
        re.I,
    )
    if match:
        return match.group(1)
    match = re.search(
        r"\bin the (.+?) story(?:\?|\.|$)",
        activity.get("prompt", ""),
        re.I,
    )
    if match:
        return match.group(1)
    tokens = _semantic_content_words(activity.get("passage", ""))
    return " ".join(tokens[:3]) or "current example"


def _clean_semantic_string(value: str) -> str:
    replacements = {
        "before the activity began": "at the start",
        "reach a useful ending": "produce the stated result",
        "used the for each known object later": "used the article the after introducing each object",
        "a owl": "an owl",
        "a elephant": "an elephant",
        "before the after that": "before the later",
        "the after that": "the later",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def _clean_semantic_tree(value: Any) -> Any:
    if isinstance(value, str):
        return _clean_semantic_string(value)
    if isinstance(value, list):
        return [_clean_semantic_tree(item) for item in value]
    if isinstance(value, dict):
        return {key: _clean_semantic_tree(item) for key, item in value.items()}
    return value


def _strip_template_sentences(value: str) -> str:
    banned_fragments = (
        "the first idea did not fit every detail",
        "this new example repairs the earlier mistake",
        "the group then explains why the corrected idea fits",
        "two friends checked that the space was ready",
        "rereading the beginning confirms how",
        "a classmate retells the",
        "the unfamiliar setting makes",
        "the group compares this",
        "a friend asked what mattered most",
        "a final check connects",
        "one partner retells the",
        "two classmates walked around the area",
        "the group watched what changed instead of guessing",
        "before leaving, the classmates retold the event",
        "their short retelling included no invented action",
        "a partner described the starting condition",
        "everyone compared the later condition with the beginning",
        "at the end, the partner explained which choice mattered",
        "no extra event was added to the story",
    )
    sentences = re.split(r"(?<=[.!?])\s+", value.strip())
    return " ".join(
        sentence
        for sentence in sentences
        if not any(fragment in sentence.casefold() for fragment in banned_fragments)
    ).strip()


def _strengthen_open_activity(activity: dict[str, Any]) -> None:
    if activity.get("kind") != "open_response":
        return
    criteria = activity["rubric_criteria"]
    slots = activity["concept_slots"]
    for criterion, slot in zip(criteria, slots, strict=True):
        if criterion["id"] != slot["id"]:
            raise ValueError("class4_rubric_slot_id_mismatch")
        criterion["description"] = slot["description"]


def _learner_task(level: dict[str, Any]) -> str:
    if level["level_id"] == "hekko_clusters_and_animal_sounds":
        return "match the animal sound and explain its opening cluster"
    task_by_skill = {
        "writing.paragraph": "write a linked paragraph",
        "writing.procedure": "write a safe procedure in order",
        "writing.reason_answer": "write a claim with a story-based reason",
        "writing.summary_own_words": "summarise the actor, action, and result",
        "writing.dialogue": "write clear, connected speaker turns",
        "writing.complete_sentence": "write one complete sentence",
        "writing.compare_contrast": "state one likeness and one difference",
        "grammar.question_formation": "write one answerable question",
        "grammar.sentence_order": "arrange the words into a complete sentence",
    }
    for skill, task in task_by_skill.items():
        if skill in level["skill_ids"]:
            return task
    first_skill = level["skill_ids"][0]
    return SKILL_DIRECTIONS_B.get(first_skill, "answer from the story clues")


def _child_detail_guidance(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


def _set_support_teaching(
    level: dict[str, Any], name: str, activity: dict[str, Any]
) -> None:
    story = _semantic_story_label(activity)
    task = _learner_task(level)
    detail_guidance = _child_detail_guidance(len(activity["rubric_criteria"]))
    teaching = {
        "bridge": (
            f"Worked example: In the {story} story, find the strongest clue first. "
            f"Use that clue to {task}."
        ),
        "masterclass": (
            f"Why it works: In the {story} story, the answer must match the exact words and result. "
            f"Compare the tempting choice with the strongest clue before you {task}."
        ),
        "revision_level_1": (
            f"Guided repair: In the {story} story, use two clues, the key action "
            f"and its result, to {task}. "
            "Check both before answering."
        ),
        "revision_level_2": (
            f"Short hint: Use one clue from the {story} story to {task}. "
            "Check the ending once."
        ),
        "revision_level_3": (
            f"Independent retry: For the {story} story, {task} without a hint. "
            f"Use the visible story to practise {level['focus']}; "
            f"{detail_guidance}."
        ),
    }
    prompts = {
        "bridge": f"Try the {story} story. Find one clue, then {task}.",
        "masterclass": (
            f"Try the {story} story. {task.capitalize()}, then explain why the clue fits."
        ),
        "revision_level_1": (
            f"Try the {story} story. Use two clues to {task}."
        ),
        "revision_level_2": (
            f"Try the {story} story. Use one clue to {task}."
        ),
        "revision_level_3": (
            f"Try the {story} story. {task.capitalize()} without a hint."
        ),
    }
    activity["teaching_block"] = teaching[name]
    activity["prompt"] = prompts[name]


def _repair_word_distractors(activity: dict[str, Any]) -> None:
    if not activity.get("options"):
        return
    correct = activity["accepted_answers"][0]
    match = re.search(
        r"(?:the word|in this story,)\s+([a-z]+)\s+(?:fits|means)",
        correct.casefold(),
    )
    if not match or match.group(1) not in _SEMANTIC_WORD_DISTRACTORS:
        return
    word = match.group(1)
    actor_match = re.search(r"\b([A-Z][a-z]+)\b", correct)
    actor = actor_match.group(1) if actor_match else "The reader"
    scene_match = re.search(r"\bat the ([^,]+)", activity["passage"].casefold())
    scene = scene_match.group(1) if scene_match else "story scene"
    wrongs = [
        f"In the {scene}, {actor} reads {word} as meaning {meaning}, which conflicts with the decisive clue."
        for meaning in _SEMANTIC_WORD_DISTRACTORS[word]
    ]
    wrong_index = 0
    repaired = []
    for option in activity["options"]:
        if option == correct:
            repaired.append(option)
        else:
            repaired.append(wrongs[wrong_index])
            wrong_index += 1
    activity["options"] = repaired


def _repair_role_distractors(activity: dict[str, Any]) -> None:
    if not activity.get("options"):
        return
    correct = activity["accepted_answers"][0]
    scene_match = re.search(r"\bat the ([^,]+)", activity["passage"].casefold())
    scene = scene_match.group(1) if scene_match else "story"
    if "The captain asks which choice mattered. The scorer answers that " in correct:
        actor_match = re.search(r"answers that ([A-Z][a-z]+)", correct)
        actor = actor_match.group(1) if actor_match else "the player"
        wrongs = [
            f"At the {scene}, the scorer asks the question and the captain answers, reversing the two dialogue roles.",
            f"The captain asks which choice mattered, but the scorer names only {actor}'s opening setup and omits the decisive action.",
            f"The captain asks about the {scene}, but the scorer credits the classmates instead of {actor} for the important action.",
        ]
    elif " is the actor. The key action is that " in correct:
        actor = correct.split(" is the actor.", 1)[0]
        wrongs = [
            f"At the {scene}, the classmates are treated as the main actors even though {actor} performs the decisive action.",
            f"{actor} is the actor, but this answer treats the opening preparation as the result and omits the final change.",
            f"{actor} is the actor and the result is mentioned, but the key middle action at the {scene} is missing.",
        ]
    else:
        return
    repaired = []
    wrong_index = 0
    for option in activity["options"]:
        if option == correct:
            repaired.append(option)
        else:
            repaired.append(wrongs[wrong_index])
            wrong_index += 1
    activity["options"] = repaired


def _set_two_claim_rubric(
    activity: dict[str, Any],
    first: str,
    second: str,
    first_aliases: list[str],
    second_aliases: list[str],
) -> None:
    criteria = activity["rubric_criteria"]
    slots = activity["concept_slots"]
    criteria[0]["description"] = first
    criteria[1]["description"] = second
    slots[0]["description"] = first
    slots[1]["description"] = second
    slots[0]["any_of"] = first_aliases
    slots[1]["any_of"] = second_aliases


def _repair_chapter_nine(manifest: dict[str, Any]) -> None:
    level = next(
        level
        for level in manifest["levels"]
        if level["level_id"] == "hekko_clusters_and_animal_sounds"
    )
    for _, activity, _ in _iter_manifest_activities(level):
        if activity.get("kind") != "open_response":
            continue
        activity["teaching_block"] = activity["teaching_block"].rstrip() + (
            " Keep the animal-sound match separate from the opening-cluster check."
        )
        story = _semantic_story_label(activity)
        lead = "Try" if activity["activity_id"].split(":")[-2] == "transfer" else "Read"
        activity["prompt"] = (
            f"{lead} the {story} story. Match the animal to its sound, then "
            "name and explain the opening cluster."
        )
        haystack = " ".join(
            str(activity.get(field, ""))
            for field in ("passage", "prompt", "model_answer")
        ).casefold()
        matches = [
            (sound, cluster, animal)
            for sound, cluster, animal in ANIMAL_SOUND_CLUSTERS
            if re.search(rf"\b{re.escape(sound)}\b", haystack)
            and re.search(rf"\b{re.escape(animal)}\b", haystack)
        ]
        if len(matches) != 1:
            raise ValueError(
                f"class4_animal_cluster_authority_ambiguous:{activity['activity_id']}"
            )
        sound, cluster, animal = matches[0]
        phase = activity["activity_id"].split(":")[-2]
        if phase == "guided":
            claims = (
                f"A {animal} makes the animal sound {sound}",
                f"{sound.capitalize()} opens with {cluster}, a consonant cluster whose individual sounds remain audible",
            )
        elif phase == "independent":
            claims = (
                f"The sound word {sound} belongs to a {animal}",
                f"At the start of {sound}, the consonants in {cluster} can each be heard",
            )
        elif phase == "transfer":
            claims = (
                f"In this new setting, the {animal}'s sound is {sound}",
                f"The opening {cluster} blends consonants without hiding any sound",
            )
        elif phase == "review":
            claims = (
                f"The checked match pairs {animal} with {sound}",
                f"The word {sound} starts with {cluster}, and every consonant sound stays clear",
            )
        else:
            claims = (
                f"The corrected match links the {animal} to {sound}",
                f"In {sound}, {cluster} is the opening cluster because its consonant sounds stay audible",
            )
        activity["model_answer"] = ". ".join(claims) + "."
        first = (
            f"Animal-sound match links {sound} to the {animal}."
        )
        second = (
            f"Cluster analysis explains the opening {cluster} in {sound} through "
            "audible consonant sounds."
        )
        _set_two_claim_rubric(
            activity,
            first,
            second,
            [
                claims[0],
                f"A {animal} can make the animal sound {sound}",
            ],
            [
                claims[1],
                f"The opening consonant cluster in {sound} is {cluster}, and each consonant sound can be heard",
            ],
        )

    revision = level["support_checks"]["revision_level_1"]
    revision["passage"] = (
        "Zoya first matches a cricket with the sound word chirrup. For a separate cluster check, "
        "she studies the game word crisp and hears both consonants in cr. She also notes that ch in "
        "chirrup spells one opening sound, so chr is not a consonant cluster."
    )
    revision["prompt"] = (
        "Try the cricket sound and crisp cluster story. First match cricket with chirrup. Separately "
        "identify the true cluster in crisp and explain why chirrup does not begin with a chr cluster."
    )
    revision["model_answer"] = (
        "Chirrup is a sound made by a cricket. For the separate cluster task, crisp begins with cr, "
        "where both consonant sounds are heard; chirrup begins with the ch digraph, not a chr cluster."
    )
    _set_two_claim_rubric(
        revision,
        "Animal-sound match: states that chirrup is a sound made by a cricket.",
        "Cluster analysis: states that crisp begins with the true cr cluster and distinguishes it from the ch digraph in chirrup.",
        [
            "Chirrup is a sound made by a cricket",
            "A cricket can make the sound chirrup",
        ],
        [
            "Crisp begins with the cr consonant cluster, while chirrup begins with the ch digraph rather than chr",
            "The true cluster is cr in crisp; chirrup starts with the ch digraph and has no chr cluster",
        ],
    )

    items = {
        item["activity_id"]: item
        for item in manifest["chapter_assessment"]["items"]
    }
    item = items["eng_c4_ch09:assessment:14"]
    item["passage"] = (
        "Farah labels a grass court before a controlled restart. She circles gr in grass and checks "
        "that both the g and r sounds are heard at the beginning. The marked word helps the team read "
        "the boundary note accurately before play resumes."
    )
    item["prompt"] = (
        "Read Story A14. Which answer correctly identifies and explains the opening consonant cluster in grass?"
    )
    correct = (
        "Grass begins with the consonant cluster gr because both the g and r sounds remain audible."
    )
    item["accepted_answers"] = [correct]
    item["options"] = [
        correct,
        "Grass begins with the single consonant sound g, so r belongs to the next syllable.",
        "Grass begins with the cluster gs because the first and last consonants are joined.",
        "Grass has no opening cluster because two consonant letters can never begin one word.",
    ]

    item = items["eng_c4_ch09:assessment:15"]
    item["passage"] = (
        "Nikhil pauses beside a farm fence when a crow gives a sharp caw. The sudden sound cuts through "
        "the quiet field and warns the group that the bird is nearby. He matches crow with caw before "
        "explaining how the brief sound changes the mood of the scene."
    )
    item["prompt"] = (
        "Read Story A15. Which answer correctly matches the animal sound and explains its effect in the scene?"
    )
    correct = (
        "Caw is the crow's sound, and its sudden sharp note breaks the quiet and creates an alert mood."
    )
    item["accepted_answers"] = [correct]
    item["options"] = [
        correct,
        "Caw names the fence, and the crow remains silent throughout the field scene.",
        "Crow is the sound word, while caw names the animal standing near the group.",
        "Caw is a soft water sound that makes the field feel sleepy rather than alert.",
    ]

    item = items["eng_c4_ch09:assessment:29"]
    item["passage"] = (
        "Diya writes a restart rule on the ground card. She underlines st in stop and listens for both "
        "consonant sounds before the vowel. The cluster check helps her keep the command short and clear "
        "for every player entering the marked circle."
    )
    item["prompt"] = (
        "Read Story B14. Identify the opening cluster in stop and explain how you know it is a cluster."
    )
    correct = (
        "Stop begins with the consonant cluster st because both the s and t sounds are heard before the vowel."
    )
    item["accepted_answers"] = [correct]
    item["options"] = [
        correct,
        "Stop begins with the cluster sp because p is the final consonant in the word.",
        "Stop begins with one consonant sound, so t cannot be part of its beginning.",
        "Stop has the opening cluster so because the first two letters must always form a cluster.",
    ]

    item = items["eng_c4_ch09:assessment:30"]
    item["passage"] = (
        "Omar hears a bee buzz beside the equipment table. He matches bee with buzz, then describes how "
        "the repeated low sound makes the quiet waiting area feel busy. No letter-cluster decision is "
        "needed for this animal-sound interpretation."
    )
    item["prompt"] = (
        "Read Story B15. Match the animal to its sound word and explain the sound image without doing a cluster task."
    )
    item["model_answer"] = (
        "Buzz is the sound linked to the bee. Its repeated low note makes the waiting area seem active "
        "even before the next round begins."
    )
    _set_two_claim_rubric(
        item,
        "Animal-sound match: identifies buzz as the sound linked to the bee.",
        "Poetic sound effect: explains that the repeated low buzz makes the quiet area feel active.",
        ["Buzz is the sound linked to the bee", "The bee's sound word is buzz"],
        [
            "The repeated low buzz makes the quiet waiting area feel active",
            "The low repeated sound changes the quiet area into a busy-feeling scene",
        ],
    )


_METAPHOR_CASES = {
    "check:bridge": ("Ira", "foot of the slope", "lowest base", "returning to the last marked post", "keep the fog-route entrance clear", "the guide found the route without guessing"),
    "check:masterclass": ("Zoya", "shoulder of the hill", "upper side below the peak", "sharing weight from one heavy pack", "protect the narrow upper trail from crowding", "the group regained an even pace"),
    "check:revision_level_1": ("Milan", "heart of the meadow", "central living area", "sealing every wrapper in a reusable pouch", "leave the meadow centre clean", "the ground remained free of litter"),
    "check:revision_level_2": ("Tara", "mouth of the pass", "narrow entrance", "waiting quietly for goats to cross", "keep the pass entrance calm for wildlife", "the animals crossed without being chased"),
    "check:revision_level_3": ("Nakul", "shoulder of the mountain", "sloping upper side", "choosing the longer contour route", "stay on the durable mapped path", "the plan avoided the steep face"),
    "mountain_metaphor_care_paragraph:guided:3": ("Nakul", "arm of the river", "branching water section", "keeping reeds and litter out of the channel", "leave the water branch unblocked", "water continued to the nesting meadow"),
    "mountain_metaphor_care_paragraph:guided:4": ("Ira", "heart of the forest", "central living area", "remaining on the marked edge", "protect the old central grove", "visitors avoided trampling new plants"),
    "mountain_metaphor_care_paragraph:independent:1": ("Nakul", "foot of the pine ridge", "lowest base", "following blue markers to the shelter", "keep the route entrance clear", "the group arrived before the shower"),
    "mountain_metaphor_care_paragraph:independent:2": ("Ira", "shoulder of the ridge", "upper side below the crest", "sharing water at marked bends", "use only durable rest points", "enough water remained for the descent"),
    "mountain_metaphor_care_paragraph:independent:3": ("Zoya", "mouth of the ravine", "narrow entrance", "using the railed bridge upstream", "avoid disturbing the wet stones below", "everyone crossed with dry shoes"),
    "mountain_metaphor_care_paragraph:independent:4": ("Milan", "heart of the valley", "central area", "calling once from behind the safety line", "limit noise at the valley centre", "the echo returned without repeated shouting"),
    "mountain_metaphor_care_paragraph:transfer:1": ("Ojas", "foot of the sandstone hill", "lowest base", "choosing the gentler shaded route", "protect the fragile base trail", "the walkers reached camp without overheating"),
    "mountain_metaphor_care_paragraph:transfer:2": ("Rumi", "shoulder of the cliff", "upper ledge below the top", "staying behind the low barrier", "give nesting birds space", "the group watched without approaching nests"),
    "mountain_metaphor_care_paragraph:transfer:3": ("Farah", "heart of the old tower", "central stairwell", "pausing at every second landing", "keep the shared centre uncrowded", "all visitors reached the lookout together"),
    "mountain_metaphor_care_paragraph:transfer:4": ("Leela", "arm of the mangrove creek", "branching water section", "following the raised boardwalk around wet roots", "protect the mangrove habitat from trampling", "the group reached the bird hide without entering the mud"),
    "mountain_metaphor_care_paragraph:review:1": ("Farah", "foot of the mountain", "lowest base", "turning back at the checkpoint", "leave the return path clear before dark", "the party reached the gate safely"),
    "mountain_metaphor_care_paragraph:review:2": ("Ketan", "heart of the meadow", "central living area", "staying on the stone-marked trail", "protect the central wildflowers", "the blooms remained untouched"),
    "mountain_metaphor_care_paragraph:review:3": ("Ojas", "mouth of the lower path", "narrow entrance", "using the mapped detour around a closed slope", "keep walkers away from the rockfall area", "the group reached camp without entering the closure"),
    "mountain_metaphor_care_paragraph:review:4": ("Rumi", "shoulder of the hill", "sloping upper side", "placing guide stones along the existing steps", "protect loose soil and new plants from shortcuts", "walkers remained on the firm route"),
}


def _repair_chapter_eleven(manifest: dict[str, Any]) -> None:
    level = next(
        level
        for level in manifest["levels"]
        if level["level_id"] == "mountain_metaphor_care_paragraph"
    )
    for key, activity, _ in _iter_manifest_activities(level):
        if key not in _METAPHOR_CASES:
            continue
        actor, expression, meaning, action, care, result = _METAPHOR_CASES[key]
        story_match = re.search(
            r"\b(?:read|try) the (.+?) story\b", activity["prompt"], re.I
        )
        story = story_match.group(1) if story_match else expression
        activity["teaching_block"] = activity["teaching_block"].rstrip() + (
            " Treat the body-part image as a comparison, then connect its shared "
            "feature to one nature-care action."
        )
        activity["passage"] = (
            f"At the {expression}, meaning the {meaning}, {actor} considers how the place should be cared for. "
            f"{actor} acts by {action}. This choice helps {care}, and {result}."
        )
        lead = "Try" if ":transfer:" in activity["activity_id"] else "Read"
        activity["prompt"] = (
            f"{lead} the {story} story. Explain {expression} as the {meaning}, then "
            "link the care action to its result in one paragraph."
        )
        activity["model_answer"] = (
            f"The phrase {expression} is a body-part metaphor for the {meaning}, not a literal body part. "
            f"{actor} responds by {action}, which is a relevant care choice for this place. "
            f"Because the action helps {care}, {result}. "
            "Overall, the paragraph connects the metaphor's shared feature with a practical way to care for the site."
        )
        first = (
            f"Opening sentence interprets the body-part metaphor {expression} "
            f"through its shared feature, the {meaning}, rather than a literal body part."
        )
        second = (
            "Support sentence names the relevant nature-care choice at the site."
        )
        _set_two_claim_rubric(
            activity,
            first,
            second,
            [
                f"{expression} is a body-part metaphor for the {meaning}, not a literal body part",
                f"The {expression} is a body-part metaphor for the {meaning}; it is not a literal body part",
            ],
            [
                f"{actor} cares for the place by {action}, and {result}",
                f"By {action}, {actor} cares for the place so {result}",
            ],
        )

    items = {
        item["activity_id"]: item
        for item in manifest["chapter_assessment"]["items"]
    }
    item = items["eng_c4_ch11:assessment:11"]
    item["passage"] = (
        "Zoya reaches the foot of a ridge, the lowest base where the marked trail begins. She keeps bags "
        "away from the entrance so other walkers can start safely. The word foot compares the ridge's "
        "base with the position of a body part; the ridge has no literal foot."
    )
    item["prompt"] = (
        "Read Story A11. Which answer correctly explains the body-part metaphor and the linked care action?"
    )
    correct = (
        "Foot is a body-part metaphor for the ridge's lowest base, and keeping that entrance clear is the linked care action."
    )
    item["accepted_answers"] = [correct]
    item["options"] = [
        correct,
        "Foot is literal because the ridge walks on the trail, so the bags do not affect its meaning.",
        "Foot means the highest point of the ridge, and the care action is to block the entrance with bags.",
        "Foot names the whole mountain journey, while the lowest base is only an unrelated detail.",
    ]

    item = items["eng_c4_ch11:assessment:26"]
    item["passage"] = (
        "Imran pauses on the shoulder of a hill, a sloping upper side below the summit. He keeps the group "
        "on the marked path so loose soil beside the shortcut is not worn away. Shoulder is a body-part "
        "metaphor for position, not a literal part of the hill."
    )
    item["prompt"] = (
        "Read Story B11. Which answer explains the body-part metaphor and uses it to support nature care?"
    )
    correct = (
        "Shoulder is a body-part metaphor for the hill's upper side, and staying on the marked path helps protect that slope from erosion."
    )
    item["accepted_answers"] = [correct]
    item["options"] = [
        correct,
        "Shoulder literally carries the summit, so walkers should use the loose-soil shortcut.",
        "Shoulder means the valley floor, and leaving the marked path prevents all erosion.",
        "Shoulder names Imran's backpack, so the condition of the hill path is unrelated.",
    ]


_ARTICLE_CASES = {
    "check:bridge": ("Ira", "painted passage", "engraved arch", "the passage contains a fragile mural", "standing behind the viewing line kept the mural untouched"),
    "check:masterclass": ("Zoya", "district archive", "old folio", "the archive stores numbered pages", "returning the folio in order protected every page"),
    "check:revision_level_1": ("Milan", "river museum", "inked ledger", "the museum displays a dated fare list", "checking the ledger kept the summary factual"),
    "check:revision_level_2": ("Tara", "heritage doorway", "ornate lintel", "the doorway has a shallow carved design", "using a soft brush protected the lintel"),
    "check:revision_level_3": ("Nakul", "memorial garden", "engraved plaque", "the garden route ends at a stone arch", "following the plaque kept the route in order"),
    "maheshwar_article_place_paragraph:guided:3": ("Nakul", "weaving house", "open workroom", "the house contains several looms", "the workroom kept the looms together"),
    "maheshwar_article_place_paragraph:guided:4": ("Ira", "memorial garden", "engraved plaque", "the garden has a central path", "the plaque stands beside the path"),
    "maheshwar_article_place_paragraph:independent:1": ("Nakul", "old stepwell", "inscribed stone", "the stepwell court contains a translated note", "keeping hands away protected the inscription"),
    "maheshwar_article_place_paragraph:independent:2": ("Ira", "weaving hall", "artisan's border", "the hall displays reversible cloth", "the border looked complete on both sides"),
    "maheshwar_article_place_paragraph:independent:3": ("Zoya", "riverside gate", "arched entrance", "the gate connects the court and landing", "the entrance led the group to the exit"),
    "maheshwar_article_place_paragraph:independent:4": ("Milan", "stone granary", "airflow opening", "the granary stores grain below the roof", "the opening helped the grain remain dry"),
    "maheshwar_article_place_paragraph:transfer:1": ("Ojas", "village kiln", "earthen bowl", "the kiln hardens shaped clay", "the bowl held water after firing"),
    "maheshwar_article_place_paragraph:transfer:2": ("Rumi", "canal bridge", "arched support", "the bridge crosses a narrow channel", "the support carried the stones above it"),
    "maheshwar_article_place_paragraph:transfer:3": ("Farah", "market clock", "iron hand", "the clock has three repair dates", "the hand marked the newest repair"),
    "maheshwar_article_place_paragraph:transfer:4": ("Leela", "weaving register", "indigo sample", "the register preserves two dated dye recipes", "the sample matched the recorded plant mixture"),
    "maheshwar_article_place_paragraph:review:1": ("Farah", "local museum", "ancient tool", "the museum pairs each object with a label", "the tool's label kept only verified facts"),
    "maheshwar_article_place_paragraph:review:2": ("Ketan", "fort courtyard", "iron bell", "the courtyard also contains a stone seat", "the bell and the seat remained clear on later mention"),
    "maheshwar_article_place_paragraph:review:3": ("Ojas", "museum guide", "object label", "the guide and label describe the same carved vessel", "removing an unsupported owner kept the account factual"),
    "maheshwar_article_place_paragraph:review:4": ("Rumi", "stone channel", "upper spout", "the channel carries roof water toward a garden tank", "the spout and channel made the rain route clear"),
}


def _repair_chapter_twelve(manifest: dict[str, Any]) -> None:
    level = next(
        level
        for level in manifest["levels"]
        if level["level_id"] == "maheshwar_article_place_paragraph"
    )
    for key, activity, _ in _iter_manifest_activities(level):
        if key not in _ARTICLE_CASES:
            continue
        actor, a_noun, an_noun, fact, result = _ARTICLE_CASES[key]
        story_match = re.search(
            r"\b(?:read|try) the (.+?) story\b", activity["prompt"], re.I
        )
        story = story_match.group(1) if story_match else a_noun
        activity["teaching_block"] = activity["teaching_block"].rstrip() + (
            " Use a or an for each first mention, then use the for both known "
            "subjects in the linked place paragraph."
        )
        activity["passage"] = (
            f"{actor} studies a fact card about a {a_noun} and an {an_noun}. The card explains that {fact}. "
            f"On later mention, it calls them the {a_noun} and the {an_noun}. As a result, {result}."
        )
        lead = "Try" if ":transfer:" in activity["activity_id"] else "Read"
        activity["prompt"] = (
            f"{lead} the {story} story. Write one place paragraph using a and an "
            "for first mentions, then the for both known subjects."
        )
        activity["model_answer"] = (
            f"{actor} introduces a {a_noun} and an {an_noun} in the opening sentence. "
            f"The next sentence uses the {a_noun} and the {an_noun} because both subjects are now known. "
            f"In addition, {fact}, so {result}. "
            "Overall, the accurate article choices keep the historical-place paragraph clear from its opening to its conclusion."
        )
        first = (
            f"Opening article decision: uses a for the first mention of {a_noun} and an for the first mention of {an_noun}."
        )
        second = (
            f"Later mention article decision: uses the for the known {a_noun} and the known {an_noun}."
        )
        _set_two_claim_rubric(
            activity,
            first,
            second,
            [
                f"A {a_noun} and an {an_noun} correctly introduce both subjects on first mention",
                f"The first mention correctly uses a {a_noun} and an {an_noun}",
            ],
            [
                f"The {a_noun} and the {an_noun} correctly refer to both known subjects on later mention",
                f"The later mention correctly uses the {a_noun} and the {an_noun}",
            ],
        )

    items = {
        item["activity_id"]: item
        for item in manifest["chapter_assessment"]["items"]
    }
    item = items["eng_c4_ch12:assessment:12"]
    item["passage"] = (
        "Arun drafts a fort label. A gallery contains an arch above the river steps. On later mention, "
        "the gallery guides visitors toward the water, and the arch frames the view. He must keep the "
        "article choices and sentence order clear."
    )
    item["prompt"] = (
        "Read Story A12. Which answer correctly uses a, an, and the for first and later mentions?"
    )
    correct = (
        "A gallery contains an arch. The gallery overlooks the river, and the arch frames the view."
    )
    item["accepted_answers"] = [correct]
    item["options"] = [
        correct,
        "An gallery contains a arch. The gallery overlooks the river, and the arch frames the view.",
        "A gallery contains an arch. A gallery overlooks the river, and an arch frames the view.",
        "The gallery contains the arch before either object has been introduced. A gallery then frames a view.",
    ]

    item = items["eng_c4_ch12:assessment:27"]
    item["passage"] = (
        "Kavya prepares a museum note about a courtyard and an iron bell. The courtyard also contains a "
        "stone seat. Later, the bell and the seat are named again while the courtyard is described as a "
        "meeting place."
    )
    item["prompt"] = (
        "Read Story B12. Write two sentences using the articles a and an for new "
        "subjects and the for known subjects; explain each choice."
    )
    item["model_answer"] = (
        "A courtyard contains an iron bell and a stone seat; the articles a and an introduce the new subjects. "
        "The bell and the seat stand inside the courtyard; the article the marks all three subjects as known."
    )
    _set_two_claim_rubric(
        item,
        "New-subject article decision: uses a with courtyard plus an with iron bell.",
        "Later-mention article decision: uses the with bell, seat, and courtyard as known subjects.",
        [
            "A courtyard contains an iron bell and a stone seat; the articles a and an introduce the new subjects",
            "The new subjects are a courtyard and an iron bell, introduced with the articles a and an",
        ],
        [
            "The bell and the seat stand inside the courtyard; the article the marks all three subjects as known",
            "The known bell, seat, and courtyard use the article the on later mention",
        ],
    )


def _extend_reading_passage(activity: dict[str, Any]) -> None:
    activity["passage"] = _strip_template_sentences(activity["passage"])


def _repair_aliases(activity: dict[str, Any]) -> None:
    if activity.get("kind") != "open_response":
        return
    model = activity["model_answer"]
    sentences = [
        sentence.strip().rstrip(".")
        for sentence in re.split(r"(?<=[.!?])\s+", model)
        if sentence.strip()
    ]
    slots = activity["concept_slots"]
    if (
        any(slot["any_of"][0] not in model for slot in slots)
        and len(sentences) >= len(slots)
    ):
        for index, slot in enumerate(slots):
            slot["any_of"][0] = sentences[index]
    for slot in slots:
        canonical = slot["any_of"][0]
        slot["any_of"][1] = (
            f"The passage shows that {canonical[0].lower() + canonical[1:]}"
        )


def _remove_repeated_assessment_instruction(item: dict[str, Any]) -> None:
    prompt = item["prompt"]
    for method in _SEMANTIC_SKILL_TEACHING.values():
        prompt = prompt.replace(" " + method, "").replace(method, "")
    item["prompt"] = " ".join(prompt.split())


def _compact_prompt(activity: dict[str, Any], *, max_words: int = 30) -> None:
    if len(_semantic_words(activity["prompt"])) <= max_words:
        return
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", activity["prompt"].strip())
        if sentence.strip()
    ]
    while len(sentences) > 1 and len(
        _semantic_words(" ".join(sentences))
    ) > max_words:
        sentences.pop()
    compact = " ".join(sentences)
    if len(_semantic_words(compact)) > max_words or len(sentences) < 2:
        raise ValueError(
            f"class4_prompt_needs_authored_compaction:{activity.get('activity_id')}"
        )
    activity["prompt"] = compact


def _make_distractors_story_specific(item: dict[str, Any]) -> None:
    if not item.get("options"):
        return
    passage_words = set(_semantic_content_words(item["passage"]))
    anchors = _semantic_content_words(item["passage"])
    if len(anchors) < 2:
        return
    correct = item["accepted_answers"][0]
    repaired = []
    for option in item["options"]:
        if (
            option != correct
            and len(set(_semantic_content_words(option)) & passage_words) < 2
        ):
            option = option.rstrip(".") + f" in the {anchors[0]} {anchors[1]} account."
        repaired.append(option)
    item["options"] = repaired


def _normalize_special_aliases(manifest: dict[str, Any], chapter_id: str) -> None:
    level_ids = {
        "eng_c4_ch09": "hekko_clusters_and_animal_sounds",
        "eng_c4_ch11": "mountain_metaphor_care_paragraph",
        "eng_c4_ch12": "maheshwar_article_place_paragraph",
    }
    if chapter_id not in level_ids:
        return
    level = next(
        level
        for level in manifest["levels"]
        if level["level_id"] == level_ids[chapter_id]
    )
    targets = [
        activity for _, activity, _ in _iter_manifest_activities(level)
    ] + manifest["chapter_assessment"]["items"]
    for activity in targets:
        for slot in activity.get("concept_slots") or ():
            if len(slot.get("any_of") or ()) >= 2:
                canonical = slot["any_of"][0]
                slot["any_of"][1] = (
                    f"The passage shows that {canonical[0].lower() + canonical[1:]}"
                )


def _shorten_assessment_extension(item: dict[str, Any]) -> None:
    passage = item["passage"]
    if "opening condition beside the exact middle choice" not in passage:
        return
    suffix_start = passage.rfind(" In the ")
    base = passage[:suffix_start].rstrip() if suffix_start >= 0 else passage
    anchors = _semantic_content_words(base)[:3]
    label = " ".join(anchors) or "assessment scene"
    actor = _semantic_actor_name(base)
    item["passage"] = (
        f"{base} {actor} uses the {label} facts to identify the opening, the named action, and its consequence. "
        f"Within the {label} account, {actor} compares that action with the {label} ending before answering. "
        f"Only {actor}'s {label} evidence supports this response; no outside event is needed."
    )


def _rewrite_form_b_extension(item: dict[str, Any]) -> None:
    passage = item["passage"]
    marker = " facts to identify the opening, the named action, and its consequence."
    marker_index = passage.rfind(marker)
    if marker_index < 0:
        return
    extension_start = passage.rfind(". ", 0, marker_index) + 2
    base = passage[:extension_start].rstrip()
    actor = _semantic_actor_name(base)
    label = " ".join(_semantic_content_words(base)[:3]) or "second form"
    item["passage"] = (
        f"{base} To solve the {label} check, {actor} traces the later condition back to the precise decision. "
        f"Next, {actor} tests whether the {label} conclusion follows from that decision. "
        f"A valid {label} answer preserves the stated sequence, keeps {actor}'s role clear, and adds no event beyond the text."
    )


def _repair_chapter_twelve_dialogue(manifest: dict[str, Any]) -> None:
    item = next(
        item
        for item in manifest["chapter_assessment"]["items"]
        if item["activity_id"] == "eng_c4_ch12:assessment:29"
    )
    item["passage"] = (
        "One afternoon at the museum-article desk, Diya introduced an iron key and a storage chest in a label. "
        "Later, she referred to them as the key and the chest, so every reference remained clear. "
        "The captain asked, 'Which article choice helped the label?' The scorer answered, 'Diya used a and an "
        "for the first mentions, then the for the known objects.' To solve this dialogue check, Diya traces "
        "the scorer's fact back to the label. The exchange keeps the captain's question, the scorer's answer, "
        "and Diya's article decisions distinct."
    )
    item["prompt"] = (
        "Read Story B14. Track the captain's question, the scorer's answer, and the fact the scorer gives about Diya's article choices."
    )
    correct = (
        "The captain asks which article choice helped the label. The scorer answers that Diya used a and an first, "
        "then the for the known key and chest."
    )
    item["options"] = [
        "At the museum-article desk, the scorer asks about the key and chest while the captain gives the article explanation, reversing the dialogue roles.",
        "The captain asks about the museum label, but the scorer says Diya repeated a key and a chest on later mention instead of using the.",
        "The captain asks which article choice helped, but the scorer credits another visitor rather than Diya for the key-and-chest label.",
        correct,
    ]
    item["accepted_answers"] = [correct]


def synchronize_manifest_semantics(manifest: dict[str, Any]) -> dict[str, Any]:
    """Apply the reviewed Class 4 corrections before manifest validation/build."""

    chapter_id = manifest["chapter"]["chapter_id"]
    for level in manifest["levels"]:
        level["connect"]["passage"] = _strip_template_sentences(
            level["connect"]["passage"]
        )
        for _, activity, _ in _iter_manifest_activities(level):
            activity["passage"] = _strip_template_sentences(activity["passage"])
            _strengthen_open_activity(activity)

    for item in manifest["chapter_assessment"]["items"]:
        item["passage"] = _strip_template_sentences(item["passage"])
        _strengthen_open_activity(item)
        _repair_word_distractors(item)
        _repair_role_distractors(item)

    if chapter_id == "eng_c4_ch09":
        _repair_chapter_nine(manifest)
    elif chapter_id == "eng_c4_ch11":
        _repair_chapter_eleven(manifest)
    elif chapter_id == "eng_c4_ch12":
        _repair_chapter_twelve(manifest)

    manifest = _clean_semantic_tree(manifest)
    _normalize_special_aliases(manifest, chapter_id)

    for level in manifest["levels"]:
        for name in _SEMANTIC_SUPPORT_NAMES:
            _set_support_teaching(level, name, level["support_checks"][name])
        for _, activity, evidence_role in _iter_manifest_activities(level):
            if evidence_role == "certifying":
                _extend_reading_passage(activity)
            _repair_aliases(activity)

    for item in manifest["chapter_assessment"]["items"]:
        _remove_repeated_assessment_instruction(item)
        _extend_reading_passage(item)
        _repair_aliases(item)
        _make_distractors_story_specific(item)

    if chapter_id in {"eng_c4_ch11", "eng_c4_ch12"}:
        level_id = (
            "mountain_metaphor_care_paragraph"
            if chapter_id == "eng_c4_ch11"
            else "maheshwar_article_place_paragraph"
        )
        level = next(
            level for level in manifest["levels"] if level["level_id"] == level_id
        )
        for name in _SEMANTIC_SUPPORT_NAMES:
            prompt = level["support_checks"][name]["prompt"]
            if prompt.startswith("Read the "):
                level["support_checks"][name]["prompt"] = (
                    "Try the " + prompt[len("Read the ") :]
                )

    if chapter_id == "eng_c4_ch09":
        level = next(
            level
            for level in manifest["levels"]
            if level["level_id"] == "hekko_clusters_and_animal_sounds"
        )
        for _, activity, _ in _iter_manifest_activities(level):
            if (
                activity.get("kind") == "open_response"
                and "animal" not in activity["teaching_block"].casefold()
            ):
                activity["teaching_block"] += (
                    " Treat the first decision as an animal-sound match and the second as separate cluster analysis."
                )

    assessment_items = manifest["chapter_assessment"]["items"]
    for item in assessment_items:
        _shorten_assessment_extension(item)
    for item in assessment_items[15:]:
        _rewrite_form_b_extension(item)

    if chapter_id == "eng_c4_ch12":
        _repair_chapter_twelve_dialogue(manifest)

    for level in manifest["levels"]:
        for _, activity, _ in _iter_manifest_activities(level):
            _compact_prompt(activity)
    for item in manifest["chapter_assessment"]["items"]:
        _compact_prompt(item)

    return manifest


CHAPTER_ID = "eng_c4_ch07"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/desa107.pdf"


def _anchor(
    suffix: str,
    label: str,
    start: int,
    end: int,
    treatment: str,
    required: bool,
) -> dict[str, Any]:
    return {
        "anchor_id": f"{CHAPTER_ID}:{suffix}",
        "section_label": label,
        "page_start": start,
        "page_end": end,
        "source_url": f"{SOURCE_URL}#page={start}",
        "coverage_treatment": treatment,
        "required_for_chapter_certification": required,
    }


SOURCE_ANCHORS = [
    _anchor("read:1-2", "Let us Read: active children and poetic pattern", 1, 2, "zidd_equivalent", True),
    _anchor("think:3", "Let us Think: comprehension and personal response", 3, 3, "taught_and_assessed", True),
    _anchor("adjectives:4", "Let us Learn: adjectives and naming words", 4, 4, "taught_and_assessed", True),
    _anchor("picture-do:5", "Picture and no-fire classroom do companion", 5, 5, "optional_creative", False),
    _anchor("wordwork:5-6", "Let us Write: spelling, rhyme, and word meaning", 5, 6, "taught_and_assessed", True),
    _anchor("explore:6", "Let us Explore: inclusive sport project companion", 6, 6, "textbook_companion", False),
]


LEVEL_SPECS: list[dict[str, Any]] = [
    {
        "level_id": "fit_context_vocabulary",
        "title": "Read active words through context",
        "focus": "infer and use active-routine vocabulary in context",
        "outcome": "Infer a movement or mood word from nearby clues and use that word accurately in a new complete response.",
        "skill_ids": ["reading.word_meaning_context", "vocab.chapter_word_usage"],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-2", f"{CHAPTER_ID}:wordwork:5-6"],
        "principle": "Use the action, result, and mood around a word to infer its precise meaning before reusing it.",
        "connect": {
            "teaching_block": "Context clues explain unfamiliar active words through what someone does, how the action looks, and what changes afterward.",
            "passage": "Mira kept an even speed through every lap, and her breathing stayed calm from start to finish.",
            "prompt": "Notice how even speed and calm breathing reveal the meaning of steady before continuing.",
        },
        "guided_prompt": "Explain the key word and use it accurately in one new sentence.",
        "independent_prompt": "State the word meaning from context and demonstrate that meaning in a complete sentence.",
        "transfer_prompt": "Infer the active word in this unfamiliar setting and use it without changing its meaning.",
        "review_prompt": "Recover the precise word meaning and support it with one nearby clue.",
        "support_action": "state the word meaning and use it accurately",
        "interaction_type": "evidence_text",
        "cluster_id": "fit-context-word-guessing",
        "misconception": "The learner chooses a familiar but vague meaning, ignores the action-result clue, or repeats the target word without showing its meaning.",
        "remediation": "Underline the action and result, replace the target with a plain meaning phrase, and test that phrase in a new sentence.",
        "cases": [
            _case("steady shuttle run", "{actor} kept the same pace through six shuttle runs. The final run was as controlled as the first.", "Steady means controlled and even, so {actor} maintained a steady pace without rushing."),
            _case("swift court return", "{actor} crossed the court before the ball bounced twice. The quick return surprised the waiting team.", "Swift means very quick, and {actor} made a swift return across the court."),
            _case("cheerful practice circle", "{actor} smiled, encouraged two beginners, and kept the group hopeful after a missed turn.", "Cheerful describes a happy encouraging mood, which {actor} brought to the practice circle."),
            _case("rhythmic skipping set", "{actor} repeated three light jumps and one high jump to the same beat each time.", "Rhythmic means following a repeated beat or pattern, as {actor} did while skipping."),
            _case("proud relay finish", "{actor} completed a difficult relay change and stood taller while thanking the team.", "Proud means pleased by a worthy effort, and {actor} felt proud of the relay finish."),
        ],
    },
    {
        "level_id": "fit_active_main_idea",
        "title": "Find the active routine message",
        "focus": "identify the main idea of an active routine",
        "outcome": "Separate examples from the central message and state how varied movement, rest, or music supports a healthy routine.",
        "skill_ids": ["reading.paragraph_main_idea"],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-2", f"{CHAPTER_ID}:think:3"],
        "principle": "Group related details, ask what they show together, and state one central idea broader than any single example.",
        "connect": {
            "teaching_block": "A main idea gathers several related details under one message. It does not simply repeat the first sport, person, or object mentioned.",
            "passage": "One child cycled, another stretched, and a third played a drum pattern. Each chose an active routine that required regular practice.",
            "prompt": "Group the three examples under the shared idea of regular active practice.",
        },
        "guided_prompt": "State the central idea and leave out minor names or numbers.",
        "independent_prompt": "Write one main-idea sentence that covers every important detail.",
        "transfer_prompt": "Find the shared message across this new set of healthy choices.",
        "review_prompt": "Distinguish the broad message from one memorable supporting detail.",
        "support_action": "state one central message that covers all details",
        "interaction_type": "summary",
        "cluster_id": "fit-main-idea-detail-only",
        "misconception": "The learner copies one activity detail as the main idea or gives a broad slogan that ignores the supplied routine.",
        "remediation": "Sort details into movement, practice, and recovery, then write one sentence that truthfully covers all three groups.",
        "cases": [
            _case("morning movement club", "{actor} walked briskly, stretched carefully, and drank water afterward. The three habits made the morning routine safe and active.", "The main idea is that {actor} combines movement, careful stretching, and water in a safe active routine."),
            _case("music and motion break", "{actor} tapped a drum pattern while classmates stepped to the beat. Everyone moved and concentrated for ten lively minutes.", "The main idea is that {actor} uses music and movement together for an active focused break."),
            _case("practice and recovery plan", "{actor} practised throws, paused when tired, and slept on time. Improvement came from effort as well as recovery.", "The main idea is that {actor} balances practice with rest to improve safely."),
            _case("inclusive playground hour", "{actor} marked a shorter route and offered lighter equipment. More children could then join the playground challenge.", "The main idea is that {actor} adapts an activity so more children can participate."),
            _case("weekend activity mix", "{actor} gardened in the morning, cycled in the evening, and read quietly before bed. The day included effort and calm.", "The main idea is that {actor} creates a balanced day with active and restful choices."),
        ],
    },
    {
        "level_id": "fit_routine_sequence",
        "title": "Order a safe practice routine",
        "focus": "sequence movement and recovery steps",
        "outcome": "Use time and result clues to put preparation, practice, and recovery into a coherent supported order.",
        "skill_ids": ["reading.event_sequence"],
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:think:3", f"{CHAPTER_ID}:wordwork:5-6"],
        "principle": "Track what prepares the body, what performs the skill, and what helps recovery; time clues confirm the order.",
        "connect": {
            "teaching_block": "An active routine has a usable order. Preparation comes before effort, and recovery follows the effort rather than replacing it.",
            "passage": "First the group rotated ankles. Next they practised short races. Finally they walked slowly and drank water.",
            "prompt": "Trace preparation, practice, and recovery in that order before continuing.",
        },
        "guided_prompt": "Retell the preparation, practice, and recovery events in order.",
        "independent_prompt": "Explain the full event sequence using clear transition words.",
        "transfer_prompt": "Apply the three-stage sequence to this unfamiliar active routine.",
        "review_prompt": "Restore the correct order and explain which clue fixes each step.",
        "support_action": "rebuild the preparation-to-recovery sequence",
        "interaction_type": "summary",
        "ordered": True,
        "cluster_id": "fit-sequence-middle-step-loss",
        "misconception": "The learner starts with the hardest action, omits recovery, or lists events without using the time and purpose clues.",
        "remediation": "Place each event on a prepare-practise-recover strip and justify its position with one transition or purpose clue.",
        "cases": [
            _case("relay preparation line", "{actor} checked the track, warmed up, completed two relay rounds, and then cooled down with a slow walk.", "{actor} first checked and warmed up, next ran the relay rounds, and finally cooled down."),
            _case("dance rehearsal order", "{actor} cleared the floor, rehearsed the steps slowly, performed the full pattern, and stretched afterward.", "{actor} prepared the floor, rehearsed slowly, performed the pattern, and ended with a stretch."),
            _case("cycle safety sequence", "{actor} tested the brakes, fastened a helmet, rode the marked loop, and parked before drinking water.", "{actor} checked safety first, rode the loop next, and parked before beginning recovery."),
            _case("skating correction cycle", "{actor} noticed a shaky turn, practised the foot position, tried the turn again, and recorded the improvement.", "{actor} noticed the problem, practised a correction, retried the turn, and recorded the result."),
            _case("rainy indoor circuit", "{actor} moved benches aside, set three stations, completed each station, and returned the room to order.", "{actor} prepared the space, arranged the circuit, completed it, and restored the room afterward."),
        ],
    },
    {
        "level_id": "fit_wellbeing_reason",
        "title": "Explain an active choice with evidence",
        "focus": "infer a wellbeing reason and write supported reasoning",
        "outcome": "Draw a reasonable conclusion from an action-result clue and express the claim with a relevant evidence-based reason.",
        "skill_ids": ["reading.inference_reason", "writing.reason_answer"],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-2", f"{CHAPTER_ID}:think:3"],
        "principle": "An inference joins a visible action to a visible result; a reason answer names both instead of relying on a general opinion.",
        "connect": {
            "teaching_block": "A strong reason answer states what is likely true and points to the exact action or result that supports it.",
            "passage": "After regular balance practice, Nisha stopped reaching for the wall during turns. She also smiled when the next drill began.",
            "prompt": "Connect repeated balance practice with steadier and more confident movement.",
        },
        "guided_prompt": "Infer why the choice helped and support the inference with one visible result.",
        "independent_prompt": "Write a claim-and-reason answer grounded in the action and its outcome.",
        "transfer_prompt": "Use cause and result clues to explain this new wellbeing decision.",
        "review_prompt": "State the inference, add because, and cite the decisive passage detail.",
        "support_action": "write a supported claim-and-reason response",
        "interaction_type": "evidence_text",
        "cluster_id": "fit-reason-without-evidence",
        "misconception": "The learner gives a generic health slogan, reverses cause and result, or states an opinion without a passage clue.",
        "remediation": "Mark the chosen action and observed result in different colours, then join them with a because sentence.",
        "cases": [
            _case("careful skating retry", "{actor} slowed down to practise one difficult turn. The next attempt stayed inside the marked lane.", "{actor} improved because slower focused practice led to a controlled turn inside the lane."),
            _case("water break decision", "{actor} paused for water after several fast rounds. The final round was completed without dizziness.", "{actor} made a sensible choice because the water break supported a safer final round."),
            _case("team encouragement moment", "{actor} praised a beginner after a missed catch. The beginner tried again instead of leaving the game.", "{actor} helped the team because encouragement gave the beginner confidence to try again."),
            _case("sleep before competition", "{actor} ended practice on time and slept early. The next morning, attention remained sharp through every instruction.", "{actor} benefited from early rest because it supported sharp attention during the competition."),
            _case("mistake review habit", "{actor} wrote down why two passes failed and changed hand position. Three later passes reached the target.", "{actor} learned from mistakes because reviewing the failed passes led to a useful correction."),
        ],
    },
    {
        "level_id": "fit_adjective_sentences",
        "title": "Build precise activity descriptions",
        "focus": "use adjectives in complete activity sentences",
        "outcome": "Select an adjective that fits a visible noun and action, then write a complete sentence that communicates the description.",
        "skill_ids": ["grammar.noun_verb_adjective", "writing.complete_sentence"],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:adjectives:4", f"{CHAPTER_ID}:wordwork:5-6"],
        "principle": "A useful adjective adds a precise quality to a noun, while the complete sentence still needs a clear subject and action or state.",
        "connect": {
            "teaching_block": "Describing words should match visible qualities rather than decorate a sentence randomly. The noun and action keep the sentence complete.",
            "passage": "A narrow track curved around the garden, and a patient runner waited for a safe gap.",
            "prompt": "Notice how narrow describes the track and patient describes the runner.",
        },
        "guided_prompt": "Identify the useful adjective and write a complete sentence showing what it describes.",
        "independent_prompt": "Construct one precise sentence with the correct noun, adjective, and action.",
        "transfer_prompt": "Choose a fitting describing word for this new activity scene and use it in a complete sentence.",
        "review_prompt": "Check the adjective-noun link and confirm that the sentence has a subject and meaningful action.",
        "support_action": "repair the adjective-noun link and complete the sentence",
        "interaction_type": "short_text",
        "cluster_id": "fit-adjective-fragment-confusion",
        "misconception": "The learner labels every vivid word an adjective, attaches a quality to the wrong noun, or writes only a noun phrase instead of a sentence.",
        "remediation": "Box the noun, ask what kind, underline the answering adjective, and add a subject-action frame to complete the thought.",
        "cases": [
            _case("agile goalkeeper", "{actor} watched an agile goalkeeper change direction quickly and block a low ball.", "Agile describes the goalkeeper, and {actor} writes: The agile goalkeeper blocked the low ball."),
            _case("rocky practice path", "{actor} crossed a rocky path where uneven stones made each careful step important.", "Rocky describes the path, and {actor} writes: The careful walker crossed the rocky path safely."),
            _case("cheerful music group", "{actor} joined a cheerful music group that welcomed every new player with a bright tune.", "Cheerful describes the group, and {actor} writes: The cheerful group welcomed a new player."),
            _case("swift bicycle rider", "{actor} noticed a swift rider pass the marker quickly while keeping both hands steady.", "Swift describes the rider, and {actor} writes: The swift rider passed the marker with steady hands."),
            _case("balanced activity plan", "{actor} followed a balanced plan with movement, water, study, and enough rest.", "Balanced describes the plan, and {actor} writes: The balanced plan included movement, water, study, and rest."),
        ],
    },
    {
        "level_id": "fit_summary_response",
        "title": "Summarise a balanced routine",
        "focus": "understand key sentences and summarise a balanced plan",
        "outcome": "Track the actor and essential actions across a short routine, then compress them into an accurate own-words summary.",
        "skill_ids": ["reading.sentence_comprehension", "writing.summary_own_words"],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:think:3", f"{CHAPTER_ID}:wordwork:5-6"],
        "principle": "Resolve who does each action, keep only details that shape the routine, and combine them without copying the passage order word for word.",
        "connect": {
            "teaching_block": "A clear summary keeps the person, main choices, and overall result. Names of minor objects and repeated examples can usually be removed.",
            "passage": "Rohan walks to school, plays after class, and rests before homework. His plan gives time to movement, learning, and recovery.",
            "prompt": "Track Rohan's three main choices and compress them into one balanced-plan message.",
        },
        "guided_prompt": "Name who makes the choices and summarise the essential routine in fresh wording.",
        "independent_prompt": "Write a concise own-words summary that keeps the actor, key actions, and result.",
        "transfer_prompt": "Compress this unfamiliar routine into a clear balanced-plan summary.",
        "review_prompt": "Remove minor details, resolve every subject, and state the whole routine accurately.",
        "support_action": "identify the actor and write an own-words summary",
        "interaction_type": "summary",
        "cluster_id": "fit-summary-copy-or-actor-loss",
        "misconception": "The learner copies several sentences, loses who performed an action, or replaces the routine with unsupported advice.",
        "remediation": "Write who, key actions, and result in three boxes, cover the original wording, and combine the boxes into one or two fresh sentences.",
        "cases": [
            _case("school-day balance", "{actor} walks to school, plays table tennis after class, and rests before evening study. The routine makes space for movement and focus.", "{actor} balances the school day by combining walking, active play, rest, and focused study."),
            _case("weekend family routine", "{actor} helps in the garden, cycles with family, and reads quietly after lunch. No single activity fills the whole day.", "{actor} follows a varied weekend routine that combines helpful movement, family activity, and quiet reading."),
            _case("practice with recovery", "{actor} rehearses dance steps for twenty minutes, drinks water, and pauses before another round. The breaks keep practice controlled.", "{actor} practises dance in short controlled rounds with water and recovery breaks."),
            _case("indoor rainy-day plan", "{actor} stretches, follows a safe indoor circuit, and ends with slow breathing. Rain changes the location but not the healthy routine.", "{actor} maintains an active rainy-day routine indoors through stretching, a safe circuit, and calm recovery."),
            _case("inclusive sports morning", "{actor} offers seated throws, standing throws, and adjustable targets. Each learner chooses a suitable challenge.", "{actor} creates an inclusive sports morning by offering adjustable ways for every learner to participate."),
        ],
    },
    {
        "level_id": "fit_poetic_balanced_plan",
        "title": "Move from rhyme to a balanced plan",
        "focus": "interpret active poetic language and develop a balanced plan paragraph",
        "outcome": "Explain how sound or imagery presents joyful movement, then transfer the message into a supported organised paragraph about a balanced plan.",
        "skill_ids": ["reading.poetic_language", "writing.paragraph"],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-2", f"{CHAPTER_ID}:wordwork:5-6"],
        "principle": "Interpret rhyme and imagery through visible language clues, then organise a paragraph with an opening idea, connected plan details, and a closing benefit.",
        "connect": {
            "teaching_block": "Poetic sound can make movement feel lively, while a paragraph turns that lively idea into a practical and connected plan.",
            "passage": "Shoes tap the track; hands clap back. The short rhyme makes the practice sound energetic and shared.",
            "prompt": "Notice the track-back rhyme and the shared rhythm before building a practical paragraph.",
        },
        "guided_prompt": "Explain the sound image and connect it to one practical balanced-plan choice.",
        "independent_prompt": "Interpret the poetic clue, then write a focused paragraph with activity, recovery, and a closing benefit.",
        "transfer_prompt": "Carry the movement image into a new organised plan without treating the image as literal fact.",
        "review_prompt": "Explain the rhyme or image and check that the paragraph has an opening, support, and closing.",
        "support_action": "interpret the poetic clue and organise the balanced-plan paragraph",
        "interaction_type": "paragraph_text",
        "cluster_id": "fit-poetry-literal-or-list-paragraph",
        "misconception": "The learner treats imagery as fact, names a rhyme without explaining its effect, or writes an unconnected activity list instead of a paragraph.",
        "remediation": "Name the image and its effect in one sentence, then use an opening-support-closing frame to turn the idea into a balanced plan.",
        "cases": [
            _case("track-back rhyme", "{actor} reads: Feet meet the track, then spring lightly back. The rhyme gives the line a quick returning beat.", "The track-back rhyme suggests lively repeated movement, and {actor} plans practice followed by water and rest."),
            _case("bright-flight image", "{actor} reads: The shuttle takes bright flight above the net. The image makes an ordinary hit seem joyful.", "Bright flight is a playful image for the shuttle, and {actor} builds a paragraph about practice, teamwork, and recovery."),
            _case("drum-step rhythm", "{actor} reads: Drum, step, turn; pause, breathe, learn. The repeated pattern links music, movement, and reflection.", "The repeated rhythm joins movement with reflection, so {actor} proposes short practice rounds with pauses to learn."),
            _case("river-run comparison", "{actor} reads that runners flowed around the bend like a careful river. The comparison describes smooth group motion.", "The river comparison suggests smooth coordinated running, and {actor} writes a balanced plan with warm-up, teamwork, and cooldown."),
            _case("joyful activity chorus", "{actor} reads: Roll and stroll, play and sway; choose one active joy each day. The paired sounds create an encouraging chorus.", "The rhyme encourages varied joyful movement, and {actor} organises a paragraph with daily activity, safe limits, and rest."),
        ],
    },
    {
        "level_id": "fit_double_letter_spelling",
        "title": "Keep double letters in active words",
        "focus": "recognise and write double-letter spelling patterns",
        "outcome": "Identify the repeated letters in familiar activity words and spell each word accurately in a complete sentence.",
        "skill_ids": ["vocab.spelling"],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:wordwork:5-6"],
        "principle": "A double letter belongs to the standard spelling even when the two letters are heard as one sound; look, cover, write, and check both letters.",
        "connect": {
            "teaching_block": "Double-letter spelling needs a visual check. Mark the repeated pair, cover the word, write it from memory, and compare every letter.",
            "passage": "The activity chart shows running with double n and skipping with double p. Mira circles each repeated pair before copying the words.",
            "prompt": "Notice each double letter and check the complete spelling before continuing.",
        },
        "guided_prompt": "Name the double letter, spell the activity word, and use it in a sentence.",
        "independent_prompt": "Write the double-letter spelling accurately and explain which letters repeat.",
        "transfer_prompt": "Apply the same spelling check to this new activity word.",
        "review_prompt": "Check the word from first letter to last and confirm the repeated pair.",
        "support_action": "restore the double letter and spell the whole word accurately",
        "interaction_type": "short_text",
        "cluster_id": "fit-double-letter-loss",
        "misconception": "The learner writes only one of the repeated letters or identifies a repeated sound without checking the standard spelling.",
        "remediation": "Box the repeated pair, cover the model, write the complete word, and compare each position before using it in a sentence.",
        "cases": [
            _case("running double n", "{actor} checks the word running and marks the double letter n before writing the fitness note.", "{actor} spells running with double n and uses the complete spelling in a sentence about exercise."),
            _case("skipping double p", "{actor} studies skipping on the activity chart and circles the double letter p.", "{actor} keeps double p in skipping and writes the spelling accurately in a complete sentence."),
            _case("fitness double s", "{actor} compares fit with fitness and notices the double letter s at the end.", "{actor} spells fitness with double s and explains that both repeated letters remain in the word."),
            _case("jogging double g", "{actor} writes jogging after checking the double letter g in the middle.", "{actor} preserves double g in jogging and uses the correct spelling for a morning routine."),
            _case("swimming double m", "{actor} reads swimming slowly and underlines the double letter m before copying it.", "{actor} writes swimming with double m and checks the full spelling from beginning to end."),
        ],
    },
]


MANIFEST = synchronize_manifest_semantics(build_manifest(
    chapter={
        "chapter_id": CHAPTER_ID,
        "chapter_no": 7,
        "title": "Fit Body, Fit Mind, Fit Nation",
        "book_title": "Santoor",
        "unit_title": "Fun with Games",
        "source_url": SOURCE_URL,
        "source_note": "NCERT structural alignment only. Every learner-facing passage, prompt, option, rubric, and answer is original Zidd content.",
        "content_version": "2026-07-16.1",
        "certification_version": "2026-07-16.1",
        "authorship": {
            "zidd_authored_original": True,
            "textbook_body_or_questions_copied": False,
            "source_analysis_reference": "/tmp/zidd-ncert-class4/eng_c4_ch07.txt structural exercise review",
        },
    },
    source_anchors=SOURCE_ANCHORS,
    level_specs=LEVEL_SPECS,
))
