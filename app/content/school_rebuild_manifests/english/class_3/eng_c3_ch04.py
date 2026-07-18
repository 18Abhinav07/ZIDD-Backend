"""Deep authored manifest for Class 3 English Chapter 4.

Official pages were consulted only for structure, themes, and activity forms.
All learner-facing runtime content below is original Zidd text.
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


CHAPTER_ID = "eng_c3_ch04"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/cesa104.pdf"


SOURCE_ANCHORS = [
    {"anchor_id": f"{CHAPTER_ID}:picture:36-38", "section_label": "Picture Reading: Outdoor Games and Shared Space", "page_start": 36, "page_end": 38, "source_url": f"{SOURCE_URL}#page=36", "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:recite:39-40", "section_label": "Let us Recite text used for poetry reading: Garden Play and Action Patterns", "page_start": 39, "page_end": 40, "source_url": f"{SOURCE_URL}#page=39", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:think:41", "section_label": "Let us Think: Game Meaning and Outdoor Safety", "page_start": 41, "page_end": 41, "source_url": f"{SOURCE_URL}#page=41", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:speak:41", "section_label": "Let us Speak: Optional Game Sharing", "page_start": 41, "page_end": 41, "source_url": f"{SOURCE_URL}#page=41", "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:learn:42", "section_label": "Let us Learn: Actions Joined with And", "page_start": 42, "page_end": 42, "source_url": f"{SOURCE_URL}#page=42", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:do:43", "section_label": "Let us Do: Optional Paper Bag Puppet Craft", "page_start": 43, "page_end": 43, "source_url": f"{SOURCE_URL}#page=43", "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
]


CRUNCH_BAR = {
    "garden_verse_and_idea": _crunch(
        [
            (
                "Over the chalk line the beanbag flies, over the chalk line our happy shout rises.",
                "Repeating over the chalk line gives both actions one lively direction. The main idea is that a shared target joins throwing and cheering.",
                ["repeating over the chalk line", "one lively direction"],
                ["shared target joins throwing and cheering", "throwing and cheering"],
            ),
            (
                "Quiet feet wait by the gate; quick feet race when partners call. Quiet, then quick, keeps the whole relay ready.",
                "The change from quiet feet to quick feet builds excitement. The main idea is that patient waiting helps a relay begin smoothly.",
                ["quiet feet to quick feet", "builds excitement"],
                ["patient waiting helps a relay", "begin smoothly"],
            ),
            (
                "Turn with the ribbon, turn with the breeze; pause when your neighbour needs room by the trees.",
                "Repeating turn creates a circling rhythm, while the pause adds care. The main idea is that lively play must leave space for others.",
                ["repeating turn", "circling rhythm"],
                ["play must leave space for others", "pause adds care"],
            ),
            (
                "One tap starts the pass, two claps welcome it back, and three smiles carry the pattern down the track.",
                "The growing count makes the rhythm feel busier. The main idea is that signals and friendly responses help a passing game continue.",
                ["growing count", "rhythm feel busier"],
                ["signals and friendly responses", "passing game continue"],
            ),
            (
                "After the race we gather each flag, after the race we fold every mat, after the race we leave a clear patch.",
                "Repeating after the race stresses the clean-up actions. The main idea is that players share responsibility for the space when play ends.",
                ["repeating after the race", "stresses clean-up"],
                ["players share responsibility", "when play ends"],
            ),
        ],
        prompt="Explain the verse pattern and state one main idea about the play scene.",
        interaction_type="summary",
    ),
    "play_actions_in_sentences": _crunch(
        [
            (
                "Card: the calm referee / lifts / a yellow flag / beside the track.",
                "The calm referee lifts a yellow flag beside the track. Referee and flag are nouns, lifts is the verb, and calm and yellow are describing words.",
                ["referee and flag are nouns", "lifts is the verb"],
                ["calm referee lifts a yellow flag", "beside the track"],
            ),
            (
                "Card: a silver whistle / hangs / from the short cord / near the bench.",
                "A silver whistle hangs from the short cord near the bench. Whistle and cord are nouns, hangs is the verb, and silver and short are describing words.",
                ["whistle and cord are nouns", "hangs is the verb"],
                ["silver whistle hangs", "near the bench"],
            ),
            (
                "Card: the strong thrower / sends / the light disc / across the field.",
                "The strong thrower sends the light disc across the field. Thrower and disc are nouns, sends is the verb, and strong and light are describing words.",
                ["thrower and disc are nouns", "sends is the verb"],
                ["strong thrower sends the light disc", "across the field"],
            ),
            (
                "Card: two careful pupils / stack / the orange cones / inside the shed.",
                "Two careful pupils stack the orange cones inside the shed. Pupils and cones are nouns, stack is the verb, and careful and orange are describing words.",
                ["pupils and cones are nouns", "stack is the verb"],
                ["careful pupils stack the orange cones", "inside the shed"],
            ),
            (
                "Card: the smooth marble / rolls / down a wooden ramp / slowly.",
                "The smooth marble rolls slowly down a wooden ramp. Marble and ramp are nouns, rolls is the verb, and smooth and wooden are describing words.",
                ["marble and ramp are nouns", "rolls is the verb"],
                ["smooth marble rolls slowly", "down a wooden ramp"],
            ),
        ],
        prompt="Write the full sentence, then name its nouns, verb, and describing words.",
    ),
    "outdoor_safety_reasoning": _crunch(
        [
            (
                "A loose shoelace trails under a runner's foot. The runner is still beside the start line.",
                "Ask the runner to tie the loose lace before starting because it could catch under a foot and cause a fall.",
                ["tie the loose lace before starting", "stop beside the start line"],
                ["catch under a foot", "cause a fall"],
            ),
            (
                "A football has rolled into a thorny hedge. A long-handled rake and an adult helper are nearby.",
                "Ask the adult to use the long-handled rake because reaching into the thorny hedge could scratch a player's hands.",
                ["ask the adult to use the rake", "use the long handle"],
                ["thorny hedge could scratch hands", "avoid reaching into thorns"],
            ),
            (
                "The painted goal line is wet, but a dry grass strip can hold a new line of cones.",
                "Move the goal to the dry grass strip and mark it with cones because players could slip on the wet painted line.",
                ["move the goal to dry grass", "mark it with cones"],
                ["wet painted line", "players could slip"],
            ),
            (
                "A paper glider contest points toward an open classroom door where pupils are carrying books.",
                "Turn the throwing line away from the doorway because gliders could strike or distract pupils who are carrying books.",
                ["turn the throwing line away", "move away from the doorway"],
                ["pupils are carrying books", "gliders could strike or distract"],
            ),
            (
                "A badminton net peg is sticking out beyond the sideline. A bright cover fits over the peg.",
                "Place the bright cover over the peg before play because someone near the sideline could trip on the uncovered peg.",
                ["cover the peg before play", "use the bright cover"],
                ["peg sticks beyond sideline", "someone could trip"],
            ),
        ],
        prompt="Choose a safe action and use the exact danger clue to explain why.",
    ),
    "connect_actions_clearly": _crunch(
        [
            (
                "Facts: Noor placed the wickets. Noor measured the gap. Join the two actions with and.",
                "Noor placed the wickets and measured the gap. And joins two actions done by Noor in a clear sentence.",
                ["and joins two actions", "placed and measured"],
                ["Noor placed the wickets", "measured the gap"],
            ),
            (
                "Facts: The hoop looked heavy. It rolled easily. Join the contrast with but.",
                "The hoop looked heavy, but it rolled easily. But shows the contrast between its heavy look and easy movement.",
                ["but shows contrast", "heavy but rolled easily"],
                ["hoop looked heavy", "it rolled easily"],
            ),
            (
                "Facts: We covered the chalk marks. Rain was beginning. Join the action and reason with because.",
                "We covered the chalk marks because rain was beginning. Because links the action to its weather reason.",
                ["because links the reason", "rain was beginning"],
                ["we covered the chalk marks", "action and reason"],
            ),
            (
                "Facts: I wanted the red bat. I used the blue bat. The red bat had a crack. Use but and because.",
                "I wanted the red bat, but I used the blue bat because the red bat had a crack.",
                ["but shows the changed choice", "because gives the reason"],
                ["used the blue bat", "red bat had a crack"],
            ),
            (
                "Parts: after the match / swept the court / and / the two teams / returned the rackets.",
                "After the match, the two teams swept the court and returned the rackets. And joins both clean-up actions in a clear order.",
                ["and joins clean-up actions", "swept and returned"],
                ["after the match", "two teams swept the court"],
            ),
        ],
        prompt="Join every idea with the right connector and explain what the connector shows.",
        interaction_type="short_text",
    ),
    "game_setup_sequence": _crunch(
        [
            (
                "Ring route: set one basket by the wall; mark a standing spot; carry three rings to the spot; toss them one at a time; return the rings to the basket.",
                "First set the basket and mark the spot, then carry and toss the rings, and last return all rings to the basket. Returning them resets the route.",
                ["set the basket and mark the spot, then carry and toss the rings, and last return all rings"],
                ["Returning them resets the route"],
            ),
            (
                "Balance path: lay two ropes; check that each rope is flat; walk between them; ring a bell at the end; coil both ropes.",
                "Lay and flatten the ropes first, walk the path next, ring the bell, and coil both ropes last. The flat-rope check prevents a raised loop from catching a foot.",
                ["lay then check then walk then ring then coil", "complete balance path order"],
                ["flat rope prevents catching a foot", "check before walking"],
            ),
            (
                "Target tower: stack four tins; draw a throw line; stand behind it; roll a soft ball; rebuild the tins for the next player.",
                "Stack the tins and draw the line, stand behind it, roll the ball, and rebuild the tower last. Rebuilding prepares the same target for the next player.",
                ["stack then draw then stand then roll then rebuild", "complete tower order"],
                ["rebuilding prepares the next turn", "same target for next player"],
            ),
            (
                "Shadow tag: choose a sunny open patch; mark its edge; explain that feet stay inside; play for two minutes; remove the edge markers.",
                "Choose and mark the patch, explain the boundary, play for two minutes, and remove the markers last. The boundary talk shows players where their feet may move.",
                ["choose then mark then explain then play then remove", "complete shadow tag order"],
                ["boundary shows where feet may move", "explain before play"],
            ),
            (
                "Beanbag count: place five numbered bowls; give each pair one beanbag; take five turns; record each landing; collect the bowls.",
                "Place the bowls and give out beanbags first, take and record five turns, and collect the bowls last. Recording each landing keeps the score complete.",
                ["place then give then take then record then collect", "complete beanbag order"],
                ["recording keeps score complete", "record each landing"],
            ),
        ],
        prompt="Write the printed steps in order and explain the purpose of the named check or reset.",
        interaction_type="summary",
        ordered=True,
    ),
    "outdoor_words_in_context": _crunch(
        [
            (
                "The toy boat drifted, moving slowly across the pond without being pushed.",
                "Drifted means moved slowly without a push. New sentence: A dry leaf drifted across the puddle after the rain.",
                ["moved slowly without a push", "across the pond"],
                ["leaf drifted across the puddle", "new use of drifted"],
            ),
            (
                "The goalkeeper crouched, bending low with knees ready before the shot.",
                "Crouched means bent low in a ready position. New sentence: The gardener crouched beside the small seedling.",
                ["bent low in a ready position", "knees ready"],
                ["gardener crouched beside the seedling", "new use of crouched"],
            ),
            (
                "The spinning coin toppled, lost its balance, and fell flat on the table.",
                "Toppled means lost balance and fell over. New sentence: The tall block tower toppled when the desk shook.",
                ["lost balance and fell over", "coin fell flat"],
                ["block tower toppled", "desk shook"],
            ),
            (
                "The child scooped the marbles, lifting several at once with both curved hands.",
                "Scooped means lifted or gathered with a curved hand. New sentence: Rani scooped wet sand into the bucket.",
                ["lifted with a curved hand", "gathered several at once"],
                ["Rani scooped wet sand", "into the bucket"],
            ),
            (
                "The kite dipped, moving downward for a moment before rising again.",
                "Dipped means moved down briefly. New sentence: The swallows dipped toward the lake and flew upward again.",
                ["moved down briefly", "before rising again"],
                ["swallows dipped toward the lake", "flew upward again"],
            ),
        ],
        prompt="Use the clue to explain the movement word, then use that word in a truly new sentence.",
    ),
}


LEVELS = [
    _make_level(
        level_id="garden_verse_and_idea",
        title="Read movement patterns in play verse",
        focus="interpret repetition and action imagery and identify a poem's main idea",
        outcome="Explain how repeated action lines create rhythm and combine their details into one central idea about active, shared outdoor play.",
        skill_ids=["reading.poetic_language", "reading.paragraph_main_idea"],
        choice_skill_ids=["reading.poetic_language"],
        episode_kind="comprehension_studio",
        source_anchor_ids=[f"{CHAPTER_ID}:recite:39-40"],
        principle="Repeated words and sentence shapes link separate movements; the main idea describes what those linked movements show about the whole play scene.",
        connect={"teaching_block": "Action verse often repeats a place, time, or sentence frame. Readers should explain the effect of the pattern before summarising the larger scene.", "passage": "Across the court we hop, across the court we glide, across the court our careful teammates move side by side.", "prompt": "Notice the repeated place phrase, changing actions, and teamwork image."},
        choice_prompt="Which explanation best matches the repeated action pattern?",
        response_prompt="identify the pattern, explain its effect, and state the verse's central idea.",
        rubric_descriptions=["Identifies the repeated phrase, action pattern, or movement image and explains its effect.", "States a central idea that connects the important actions and mood."],
        examples=[
            _q("Round goes the hoop, round goes the wheel, round goes the marker in our passing drill.", "Repeating round links three circular movements.", ["Round proves every object is a wheel.", "The lines describe only still objects.", "Repeating round removes movement."]),
            _q("We jump at the line, we turn at the cone, we cheer for each runner until everyone is home.", "Repeating we emphasises group participation.", ["We means one runner acts alone.", "The line says the cone is a house.", "The runners never move."]),
            _r("Skip past the marker, skip into place; wait for your partner and match their pace.", "Repeating skip gives the opening a lively rhythm, while waiting and matching pace show considerate teamwork. The main idea is that energetic play works best when partners move with care for one another.", [["repeating skip", "lively rhythm", "matching pace"], ["energetic play", "care for partners"]]),
            _r("Blue kite rising, red ribbon streaming; quiet field waking, bright faces beaming.", "The paired colour and movement images make the field feel lively. The central idea is that a kite's movement changes a quiet outdoor space into a cheerful shared scene.", [["colour and movement images", "kite rising", "ribbon streaming"], ["quiet to cheerful", "shared scene"]]),
            _r("Catch and return, catch and return; careful hands help every new player learn.", "Repeating catch and return creates a practice rhythm and stresses taking turns. The main idea is that patient repetition helps beginners join a game.", [["catch and return repeated", "practice rhythm"], ["patient repetition", "beginners join"]]),
            _r("Under the tree we stretch and sway; out in the sun we race away.", "The contrasting place phrases move the verse from calm stretching to fast racing. The central idea is that outdoor play can include both gentle and energetic movement.", [["under tree versus sun", "stretch to race"], ["gentle and energetic movement", "outdoor play"]]),
            _r("Tap goes the ball, clap goes the team; one steady rhythm holds the passing stream.", "The repeated sound-action pattern links the ball tap with team claps. The main idea is that a shared rhythm helps the passing game feel coordinated.", [["tap and clap pattern", "sound-action"], ["shared rhythm", "coordinated passing"]]),
            _r("First feet waiting, then feet flying; last runner crosses with every friend replying.", "The movement from waiting to flying creates speed and excitement, while the friends' response adds support. The central idea is that a relay builds energy and shared encouragement.", [["waiting to flying", "speed and excitement"], ["relay energy", "shared encouragement"]]),
            _r("Swing to the left, swing to the right; hold the rope steady and keep the turn light.", "The mirrored left-right actions create balance and rhythm. The central idea is that controlled movement and steady help make play safer.", [["left-right pattern", "balance and rhythm"], ["controlled movement", "safer play"]]),
            _q("Step with the beat, step with the line, step so your partner can follow the sign.", "Repeating step stresses coordinated movement.", ["Step means the partner should leave.", "The sign makes the beat silent.", "The line describes sleeping."]),
            _r("High sails the shuttle, low bends the knee; quick comes the return across players three.", "High and low create a movement contrast, and quick return adds pace. The main idea is that three players coordinate changing movements in a fast rally.", [["high-low contrast", "quick return"], ["three players coordinate", "fast rally"]]),
            _q("Run to the post, run back to the start, run at a pace that is steady and smart.", "Repeating run creates urgency while the last line adds control.", ["Run means no one should move.", "The post becomes a runner.", "The last line demands unsafe speed."]),
            _r("Soft on the grass, loud at the goal; changing sounds follow the ball's rolling role.", "Soft and loud create a sound contrast as play moves toward the goal. The central idea is that changing sound helps show the game's movement and excitement.", [["soft-loud contrast", "toward goal"], ["sound shows movement", "excitement"]]),
            _r("Together we mark, together we play, together we clear all the cones away.", "Repeating together emphasises shared responsibility before, during, and after play. The main idea is that teamwork includes preparing and cleaning the space as well as playing.", [["repeating together", "before during after"], ["shared responsibility", "prepare and clean"]]),
        ],
        crunch_bar=CRUNCH_BAR["garden_verse_and_idea"],
        misconception="The learner identifies a repeated word but gives no effect, or lists sports equipment instead of explaining the whole verse's movement, mood, or teamwork idea.",
        remediation="Find the repeated frame and movement changes, complete 'The pattern makes...', and combine the important actions in one main-idea sentence.",
    ),
    _make_level(
        level_id="play_actions_in_sentences",
        title="Name actions and build play sentences",
        focus="classify nouns, verbs, and adjectives and write complete action sentences",
        outcome="Identify word jobs in a game card and construct a complete subject-action-object sentence with one useful place or manner detail.",
        skill_ids=["grammar.noun_verb_adjective", "writing.complete_sentence"],
        choice_skill_ids=["grammar.noun_verb_adjective"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:learn:42"],
        principle="The player or object is the noun, movement is the verb, and a quality word adds detail; a complete sentence must tell who or what performs the action.",
        connect={"teaching_block": "Game instructions become clearer when action words are precise. Classifying each word's job helps turn fragments into complete descriptions.", "passage": "The alert goalkeeper catches the rolling ball near the post. Goalkeeper and ball are nouns, catches is the verb, and alert and rolling describe nouns.", "prompt": "Find the doer, action, object, descriptions, and place detail."},
        choice_prompt="Which word performs the named grammar job?",
        response_prompt="classify the target words and write a complete action sentence from the card.",
        rubric_descriptions=["Correctly identifies or uses the required noun, verb, or adjective.", "Writes a complete sentence with a named doer, meaningful action, and supplied detail."],
        examples=[
            _q("The quick runner crosses the white line. Which word is the action?", "crosses", ["quick", "runner", "white"]),
            _q("A heavy ball rests beside the cone. Which word describes ball?", "heavy", ["ball", "rests", "cone"]),
            _r("Facts: player - Nita; action - bounces; object - a red ball; place - beside the wall.", "Nita bounces a red ball beside the wall. Nita and ball are nouns, bounces is the verb, and red describes the ball.", [["Nita and ball nouns", "bounces verb", "red adjective"], ["Nita bounces", "beside the wall"]]),
            _r("Fragment: The careful catcher. Add action and detail: receives the high throw with both hands.", "The careful catcher receives the high throw with both hands. Catcher is the noun, receives is the verb, and careful and high are adjectives.", [["catcher noun", "receives verb", "careful adjective"], ["catcher receives", "with both hands"]]),
            _r("Facts: two children; action - pull; object - a long rope; manner - steadily.", "Two children pull a long rope steadily. Children and rope are nouns, pull is the verb, and long describes the rope.", [["children and rope nouns", "pull verb", "long adjective"], ["children pull", "steadily"]]),
            _r("Facts: a bright kite; action - circles; place - above the open field.", "A bright kite circles above the open field. Kite and field are nouns, circles is the verb, and bright and open are adjectives.", [["kite and field nouns", "circles verb", "bright adjective"], ["kite circles", "above the field"]]),
            _r("Fragment: The small top. Add action and place: spins quickly on the flat board.", "The small top spins quickly on the flat board. Top and board are nouns, spins is the verb, and small and flat are adjectives.", [["top and board nouns", "spins verb", "small adjective"], ["top spins quickly", "flat board"]]),
            _r("Facts: the patient coach; action - explains; object - a new rule; time - before play.", "The patient coach explains a new rule before play. Coach and rule are nouns, explains is the verb, and patient and new are adjectives.", [["coach and rule nouns", "explains verb", "patient adjective"], ["coach explains", "before play"]]),
            _r("Sentence card: The blue marker shows the safe boundary. Classify marker, shows, blue, and safe.", "Marker is a noun, shows is a verb, and blue and safe are adjectives. The blue marker shows the safe boundary.", [["marker noun", "shows verb", "blue and safe adjectives"], ["marker shows", "safe boundary"]]),
            _q("In 'The tall player throws gently,' which word names the doer?", "player", ["tall", "throws", "gently"]),
            _r("Facts: a soft shuttle; action - lands; place - inside the square court.", "A soft shuttle lands inside the square court. Shuttle and court are nouns, lands is the verb, and soft and square are adjectives.", [["shuttle and court nouns", "lands verb", "soft adjective"], ["shuttle lands", "inside the court"]]),
            _q("The narrow path curves around the garden. Which word is the verb?", "curves", ["narrow", "path", "garden"]),
            _r("Fragment: The excited team. Add action and detail: cheers for the final runner at the finish line.", "The excited team cheers for the final runner at the finish line. Team and runner are nouns, cheers is the verb, and excited and final are adjectives.", [["team and runner nouns", "cheers verb", "excited adjective"], ["team cheers", "finish line"]]),
            _r("Facts: the striped hoop; action - rolls; direction - toward the waiting child.", "The striped hoop rolls toward the waiting child. Hoop and child are nouns, rolls is the verb, and striped and waiting are adjectives.", [["hoop and child nouns", "rolls verb", "striped adjective"], ["hoop rolls", "toward the child"]]),
        ],
        crunch_bar=CRUNCH_BAR["play_actions_in_sentences"],
        misconception="The learner labels every movement-related word as a verb, or writes an equipment fragment without naming a doer and meaningful action.",
        remediation="Find the doer, action, object, and useful descriptions, then read the draft to confirm it answers 'who does what?'.",
    ),
    _make_level(
        level_id="outdoor_safety_reasoning",
        title="Infer risks and explain safe choices",
        focus="infer outdoor-play risks and write supported safety reasons",
        outcome="Use position, speed, equipment, and weather clues to infer a likely risk and recommend a proportionate safe action with a clear reason.",
        skill_ids=["reading.inference_reason", "writing.reason_answer"],
        choice_skill_ids=["reading.inference_reason"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:think:41"],
        principle="A safety answer names what could happen from the visible clue; a sound recommendation reduces that risk without inventing danger.",
        connect={"teaching_block": "Outdoor play changes with surface, space, weather, and nearby people. A safety answer should identify the specific hazard and the smallest useful response.", "passage": "Rain has left one corner of the court slippery. The dry half remains open and the cones can be moved.", "prompt": "Infer the slipping risk and use the available dry space in a proportionate plan."},
        choice_prompt="Which risk is directly supported by the scene?",
        response_prompt="recommend a safe action and justify it with the exact hazard clue.",
        rubric_descriptions=["States a practical action that reduces the specific play risk.", "Uses the supplied surface, space, speed, weather, or equipment clue as the reason."],
        examples=[
            _q("A ball game is set beside an open road, and missed balls already roll toward traffic.", "Players or balls could enter the traffic area.", ["The road will become a garden.", "Every ball will stay still.", "Traffic makes the ball softer."]),
            _q("A kite string crosses a walking path at neck height.", "A walker could collide with the hard-to-see string.", ["The string will paint the path.", "Walkers can see through every object.", "The kite will turn into a ball."]),
            _r("A relay lane ends beside a bench where families are seated. An empty lane farther away is available.", "Move the finish line to the empty lane because fast runners could collide with people seated beside the current ending.", [["move finish line", "use empty lane"], ["fast runners", "collide with seated people"]]),
            _r("A skipping rope has a frayed middle section, and an undamaged spare rope is in the equipment box.", "Stop using the frayed rope and choose the spare because the damaged section could break during movement.", [["stop using frayed rope", "choose spare"], ["damaged section", "could break"]]),
            _r("Children are throwing a hard ball near glass windows. A soft ball and a window-free wall are available.", "Move to the window-free wall and use the soft ball because a hard missed throw could break glass and cause injury.", [["window-free wall", "soft ball"], ["hard ball", "break glass"]]),
            _r("The sun is very strong at noon, and players have no water. A shaded break area and filled bottles are nearby.", "Pause in the shade and drink water because strong midday heat and no water can make players unwell.", [["pause in shade", "drink water"], ["strong noon sun", "no water"]]),
            _r("A younger child stands inside the path of a swinging bat while watching. A marked waiting box is behind the batter.", "Guide the child to the waiting box because the swinging bat can reach the current standing place.", [["guide to waiting box", "move behind batter"], ["swinging bat", "can reach current place"]]),
            _r("A top-spinning area is covered with loose stones. A smooth paved circle beside it is empty.", "Use the smooth paved circle because loose stones can make the top jump unpredictably or trip players.", [["use smooth circle", "leave loose stones"], ["top jump unpredictably", "trip players"]]),
            _r("Dark clouds and thunder begin during field play. The school hall is open nearby.", "End the field game and move into the hall because thunder signals unsafe storm conditions outdoors.", [["end field game", "move into hall"], ["thunder", "storm unsafe outdoors"]]),
            _q("A seesaw seat has a visible crack that widens when pressed.", "The seat may fail under a rider's weight.", ["The crack makes the seat stronger.", "The seesaw can become a kite.", "Pressing removes all weight."]),
            _r("Two groups are running through the same narrow lane in opposite directions. A second lane can be marked with cones.", "Mark separate one-way lanes because runners moving toward each other in a narrow space could collide.", [["separate one-way lanes", "mark second lane"], ["opposite directions", "could collide"]]),
            _q("A swing chain makes a rough scraping sound and one link looks bent.", "The damaged link may not hold safely.", ["The chain is singing a game song.", "A bent link is always stronger.", "The swing needs faster use."]),
            _r("A marble game blocks the only doorway, and people keep stepping over the play area. A clear corner is available.", "Move the marble game to the clear corner because blocking a doorway creates a trip risk and interrupts people entering.", [["move to clear corner", "clear doorway"], ["trip risk", "people entering"]]),
            _r("Players continue a chase game after dusk, but the far boundary markers are no longer visible. A lit smaller court is open.", "Shift the game to the lit smaller court because hidden boundary markers make running routes unclear after dusk.", [["shift to lit court", "smaller court"], ["markers not visible", "routes unclear"]]),
        ],
        crunch_bar=CRUNCH_BAR["outdoor_safety_reasoning"],
        misconception="The learner gives a generic 'be careful' answer, exaggerates unsupported danger, or recommends continuing despite a clear equipment, traffic, weather, or collision clue.",
        remediation="Name the hazard, possible result, and available safer option, then write 'Do ___ because clue ___ could lead to ___'.",
    ),
    _make_level(
        level_id="connect_actions_clearly",
        title="Join actions with and, but, and because",
        focus="use connectors accurately and arrange connected sentence parts",
        outcome="Choose a connector that shows addition, contrast, or reason and arrange all supplied clauses into one natural sentence without changing their relationship.",
        skill_ids=["grammar.connectors_because_and_but", "grammar.sentence_order"],
        choice_skill_ids=["grammar.connectors_because_and_but"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:learn:42"],
        principle="And adds related actions, but marks a contrast, and because introduces a reason; sentence order must keep each connector beside the relationship it expresses.",
        connect={"teaching_block": "Two actions can be joined without losing their order or logic. The connector should tell the reader whether the second idea adds, contrasts, or explains.", "passage": "Mira catches the ball and returns it. She runs quickly but stops at the line because the boundary matters.", "prompt": "Separate addition, contrast, and reason before rebuilding connected sentences."},
        choice_prompt="Which connector expresses the relationship in the card?",
        response_prompt="choose the correct connector and arrange every clause into one natural sentence.",
        rubric_descriptions=["Uses and, but, or because to express the stated addition, contrast, or reason.", "Orders all supplied clauses into a complete natural sentence."],
        examples=[
            _q("Ria bends her knees ___ catches the low ball.", "and", ["because", "but", "although"]),
            _q("The court was small, ___ both teams found room to practise.", "but", ["because", "and then because", "so that why"]),
            _r("Parts: the players / stopped / because / thunder began / the outdoor game.", "The players stopped the outdoor game because thunder began.", [["because gives reason", "thunder began"], ["players stopped the outdoor game", "natural order"]]),
            _r("Parts: Tara / marked the lane / and / placed the cones / before the relay.", "Tara marked the lane and placed the cones before the relay.", [["and joins actions", "marked and placed"], ["Tara marked the lane", "before the relay"]]),
            _r("Parts: the kite rose / but / the wind remained gentle / it did not pull hard.", "The kite rose above the field, but the gentle wind did not pull the string hard.", [["but shows contrast", "rose versus did not pull"], ["kite rose", "wind did not pull"]]),
            _r("Facts: Neel wanted to run; he waited; another runner was crossing. Use but and because.", "Neel wanted to run, but he waited because another runner was crossing.", [["but and because", "want contrast and reason"], ["Neel wanted to run", "another runner was crossing"]]),
            _r("Facts: The team collected the balls; the team counted them; none remained on the field. Use and.", "The team collected and counted the balls, and none remained on the field.", [["and joins actions and result", "collected and counted"], ["team collected", "none remained"]]),
            _r("Parts: the rope was long / but / the play area was narrow / so the group shortened it.", "The rope was long, but the play area was narrow, so the group shortened it.", [["but marks contrast", "long versus narrow"], ["group shortened it", "natural clause order"]]),
            _r("Facts: We moved indoors; rain covered the court. Join with because.", "We moved indoors because rain covered the court.", [["because gives reason", "rain covered court"], ["We moved indoors", "natural order"]]),
            _q("The player slowed down ___ a younger child entered the lane.", "because", ["but", "and without reason", "or else and"]),
            _r("Parts: Mira / skipped / and / clapped / to the steady beat.", "Mira skipped and clapped to the steady beat.", [["and joins two actions", "skipped and clapped"], ["Mira skipped", "steady beat"]]),
            _q("The hoop was bent, ___ the spare hoop was ready.", "but", ["because", "and because why", "unless so"]),
            _r("Facts: The children wanted to continue; the light was fading; they moved to the lit court. Use but and because.", "The children wanted to continue, but they moved to the lit court because the light was fading.", [["but and because", "want contrast and reason"], ["moved to lit court", "light fading"]]),
            _r("Parts: the coach / explained the rule / and / demonstrated one safe turn / before play.", "The coach explained the rule and demonstrated one safe turn before play.", [["and joins explained and demonstrated", "two actions"], ["coach explained", "before play"]]),
        ],
        crunch_bar=CRUNCH_BAR["connect_actions_clearly"],
        misconception="The learner treats all connectors as interchangeable, places because before the result it should explain, or drops one supplied clause while rearranging parts.",
        remediation="Decide whether the relationship adds, contrasts, or gives a reason, select and, but, or because, then make sure every supplied clause appears in the rebuilt sentence.",
    ),
    _make_level(
        level_id="game_setup_sequence",
        title="Explain a visible game setup sequence",
        focus="sequence a text-only process and answer process questions precisely",
        outcome="Order preparation, action, check, and reset steps from visible instructions and write concise answers that cite the relevant step.",
        skill_ids=["reading.event_sequence", "writing.short_answer"],
        choice_skill_ids=["reading.event_sequence"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:think:41"],
        principle="A process answer must use the printed step order and explain purpose from the supplied instruction, not from an unseen demonstration.",
        connect={"teaching_block": "Text instructions can make a process fully visible. Identify what must be prepared, what action follows, how success is checked, and how the space is reset.", "passage": "Cone-pass setup: mark two lines, place one cone at each line, pass the ball between partners, then return both cones to the box.", "prompt": "Separate setup, play action, and reset without assuming any picture or live demonstration."},
        choice_prompt="Which step comes first, second, or last as named in the process?",
        response_prompt="state the correct order and answer the process question with the relevant step clue.",
        rubric_descriptions=["Preserves the complete printed step order without adding an unseen action.", "Answers the process question concisely and cites the relevant step or purpose."],
        examples=[
            _q("Setup card: draw a start line; place three markers; stand behind the line; begin on the signal.", "stand behind the line", ["begin before placing markers", "erase the start line", "place markers after the signal"], prompt="Which step happens third?"),
            _q("Packing card: count six balls; wipe each ball; place them in the net; tie the net.", "tie the net", ["count six balls", "wipe each ball", "place them in the net"], prompt="Which step happens last?"),
            _r("Steps: mark a square; put one beanbag inside; stand two metres away; toss three rings; collect all rings.", "First mark the square and put the beanbag inside. Next stand two metres away and toss three rings. Finally collect every ring so the area is ready again.", [["mark", "put beanbag", "stand", "toss", "collect"], ["collect for reset", "area ready again"]], ordered=True),
            _r("Steps: check the rope for damage; lay it straight; place players on opposite sides; pull only after the signal; coil the rope afterward. Why is checking first important?", "Check the rope before laying it out, place teams, wait for the signal, pull, and coil it afterward. The first check matters because a damaged rope should not be used.", [["check", "lay", "place", "wait", "pull", "coil"], ["damaged rope", "should not be used"]], ordered=True),
            _r("Steps: choose a clear wall; mark a target with tape; stand behind a line; throw a soft ball; retrieve it after it stops. When should a player retrieve the ball?", "Choose and mark the wall, stand behind the line, throw the soft ball, and retrieve it only after it stops. Waiting prevents a player from entering while the ball is moving.", [["choose", "mark", "stand", "throw", "retrieve after stop"], ["after it stops", "not while moving"]], ordered=True),
            _r("Steps: place four number cards face down; turn one card; perform that many jumps; replace the card; give the next player a turn.", "Place the cards first, turn one, perform the matching jumps, replace it, and then pass the turn. Replacing the card keeps the same set available for the next player.", [["place", "turn", "jump", "replace", "next turn"], ["same set available", "next player"]], ordered=True),
            _r("Steps: spread a mat; put the spinning top at its centre; wind the string; release the top; wait until it stops before collecting it.", "Spread the mat, centre the top, wind the string, release it, and collect it after it stops. Waiting protects hands from the moving top.", [["spread", "centre", "wind", "release", "collect"], ["after it stops", "protects hands"]], ordered=True),
            _r("Steps: mark two safe zones; choose one caller; players move on the call; freeze on 'stop'; check that the path is clear before restarting.", "Mark zones and choose the caller first, move on the call, freeze on stop, check the path, and restart only when clear. The check prevents restarting into an obstacle.", [["mark", "choose", "move", "freeze", "check", "restart"], ["path clear", "prevents obstacle"]], ordered=True),
            _r("Steps: place score cards in order; write team names; record each completed round; total the marks; store the cards. Why are names written before scores?", "Place cards, write team names, record rounds, total marks, and store the cards. Names come first so every later score is linked to the correct team.", [["place", "write names", "record", "total", "store"], ["scores linked", "correct team"]], ordered=True),
            _q("Route card: place arrows; walk the route once; fix unclear arrows; invite players.", "fix unclear arrows", ["place arrows after inviting", "walk after the game", "remove every arrow"], prompt="What happens immediately before players are invited?"),
            _r("Steps: inflate the ball with an adult; press it gently to check firmness; close the valve; use it on the court; return it to the shelf.", "An adult inflates the ball, firmness is checked, the valve is closed, the ball is used, and it is returned. Checking before play confirms that the ball is ready.", [["inflate", "check", "close", "use", "return"], ["check before play", "ball ready"]], ordered=True),
            _q("Clean-up card: collect cones; count them; report one missing cone; search the marked area.", "count the cones", ["search before collecting", "report before counting", "leave all cones outside"], prompt="Which action happens second?"),
            _r("Steps: draw two chalk circles; place one flag in each; divide into teams; explain the boundary; start after questions are answered.", "Draw the circles, place the flags, divide teams, explain the boundary, and start after questions. Answering questions first helps players understand where they may move.", [["draw", "place", "divide", "explain", "start"], ["questions answered", "understand boundary"]], ordered=True),
            _r("Steps: choose a dry patch; remove loose stones; mark a square; test one slow roll; begin the full rolling game. Why is the slow test before full play?", "Choose and clear the patch, mark the square, test one slow roll, and then begin. The slow test checks whether the surface and boundary work safely.", [["choose", "clear", "mark", "test", "begin"], ["checks surface and boundary", "before full play"]], ordered=True),
        ],
        crunch_bar=CRUNCH_BAR["game_setup_sequence"],
        misconception="The learner relies on a familiar game routine instead of the printed card, omits setup or reset, or answers why with a generic safety phrase unrelated to the named step.",
        remediation="Place the printed verbs in setup-action-check-reset order, then answer process questions by quoting or paraphrasing the exact step that gives the reason.",
    ),
    _make_level(
        level_id="outdoor_words_in_context",
        title="Use movement words from context",
        focus="infer outdoor-play vocabulary and transfer it to fresh sentences",
        outcome="Define a movement or equipment word from a visible clue and use it accurately in a new game or everyday context.",
        skill_ids=["reading.word_meaning_context", "vocab.chapter_word_usage"],
        choice_skill_ids=["reading.word_meaning_context"],
        episode_kind="meaning_encounter",
        source_anchor_ids=[f"{CHAPTER_ID}:think:41"],
        principle="Movement meaning comes from direction, speed, or result clues; a fresh sentence proves the word still carries that meaning in a different scene.",
        connect={"teaching_block": "A nearby description can define an action word. After finding the meaning, change the subject or setting while preserving the same movement.", "passage": "The branch swayed, moving gently from side to side in the breeze.", "prompt": "Use the side-to-side clue to define swayed before transferring it to another object."},
        choice_prompt="Which meaning matches the movement clue?",
        response_prompt="define the target word from context and use it accurately in a new sentence.",
        rubric_descriptions=["Defines the target word using the supplied direction, speed, or result clue.", "Uses the target word in a fresh sentence with the same meaning."],
        examples=[
            _q("The ball bounced, striking the ground and rising again.", "hit a surface and moved upward again", ["rolled without leaving the ground", "stayed completely still", "changed into a square"]),
            _q("Mira tugged the kite string with one short, firm pull.", "pulled briefly and firmly", ["released it forever", "painted it blue", "folded it gently"]),
            _r("The child glided across the smooth floor, moving without heavy steps.", "Glided means moved smoothly and lightly. New sentence: The paper plane glided across the quiet room.", [["moved smoothly and lightly", "without heavy steps"], ["plane glided", "across room"]]),
            _r("The runner darted between two cones, moving suddenly and quickly.", "Darted means moved quickly in a sudden direction. New sentence: A lizard darted beneath the garden bench.", [["quick sudden movement", "between cones"], ["lizard darted", "beneath bench"]]),
            _r("The hoop wobbled, tipping from side to side without falling.", "Wobbled means moved unsteadily from side to side. New sentence: The loose table wobbled when the bag touched it.", [["unsteadily side to side", "without falling"], ["table wobbled", "bag touched"]]),
            _r("The team huddled, standing close together to discuss the next move.", "Huddled means gathered closely in a small group. New sentence: We huddled under the awning during the shower.", [["gathered closely", "small group"], ["huddled under awning", "during shower"]]),
            _r("The shuttle soared, rising high above the players before descending.", "Soared means rose or moved high through the air. New sentence: The kite soared above the trees in the steady wind.", [["rose high through air", "above players"], ["kite soared", "above trees"]]),
            _r("The goalkeeper lunged, making a sudden long step toward the rolling ball.", "Lunged means moved forward with a sudden long step. New sentence: Rafi lunged to catch the falling book.", [["sudden long step", "toward ball"], ["Rafi lunged", "catch book"]]),
            _r("The players scattered, moving quickly in different directions when their zones were called.", "Scattered means spread out in different directions. New sentence: Dry leaves scattered when the gate opened.", [["spread in different directions", "zones called"], ["leaves scattered", "gate opened"]]),
            _q("The marble rolled, turning over and over along the ground.", "moved by turning along a surface", ["jumped straight upward", "floated in water", "remained in one spot"]),
            _r("The rope slackened, becoming loose after both teams stopped pulling.", "Slackened means became less tight. New sentence: The kite string slackened when the wind dropped.", [["became less tight", "teams stopped pulling"], ["string slackened", "wind dropped"]]),
            _q("The child dodged the ball by moving quickly to one side.", "avoided it with a quick movement", ["caught it while still", "painted it", "threw it upward"]),
            _r("The flag fluttered, making small quick movements in the breeze.", "Fluttered means moved with small light motions. New sentence: The paper ribbon fluttered beside the open window.", [["small light motions", "in breeze"], ["ribbon fluttered", "open window"]]),
            _r("The tired runner slowed, reducing speed near the final marker.", "Slowed means moved at a lower speed. New sentence: The bicycle slowed before the crowded crossing.", [["reduced speed", "near marker"], ["bicycle slowed", "before crossing"]]),
        ],
        crunch_bar=CRUNCH_BAR["outdoor_words_in_context"],
        misconception="The learner chooses any action associated with games, or copies the original sentence with only a changed name instead of transferring the exact movement to a new setting.",
        remediation="Find the direction-speed-result clue, write a short meaning, and test a fresh sentence by replacing the target word with that meaning.",
    ),
]


ASSESSMENT_PAIRS = [
    _aq_pair("reading.poetic_language", "Which explanation best matches the repeated pattern?", ("Pass and turn, pass and turn; steady hands help every partner learn.", "Repeating pass and turn creates practice rhythm and stresses teamwork.", ["The pattern means partners work alone.", "Turn describes a broken road.", "The lines remove all movement."]), ("Step with care, step in time; step together down the line.", "Repeating step creates a steady rhythm and links the players' movement.", ["Step means everyone stays still.", "The line describes a broken clock.", "Repeating step separates the players."])),
    _ar_pair("reading.paragraph_main_idea", "State the verse's central idea.", "Connects the important actions and mood in one accurate idea.", ("Players wait at the line, race on the signal, and cheer as each teammate finishes.", "A relay combines patient starts, energetic running, and support for every teammate.", [["patient starts", "waiting for the start"], ["energetic running", "running hard"], ["support for every teammate", "cheering every teammate"]]), ("Children mark a court, practise careful passes, and return the equipment afterward.", "Responsible play includes preparing the space, practising together, and cleaning up afterward.", ["preparing", "practising together", "cleaning up"]), interaction_type="summary"),
    _aq_pair("grammar.noun_verb_adjective", "Which word is the action verb?", ("The alert goalkeeper catches the low ball.", "catches", ["alert", "goalkeeper", "low"]), ("A striped hoop rolls toward the child.", "rolls", ["striped", "hoop", "child"])),
    _ar_pair("writing.complete_sentence", "Use all supplied details in one complete sentence.", "Includes a named doer, meaningful action, object, and relevant detail.", ("Doer: Kabir; action: rolls; object: yellow hoop; place: across the court.", "Kabir rolls a yellow hoop across the court.", ["Kabir rolls", "yellow hoop", "across the court"]), ("Doers: two children; action: pull; object: long rope; manner: steadily; place: across the marked line.", "Two children steadily pull a long rope across the marked line.", ["children steadily pull", "long rope", "across the marked line"]), interaction_type="short_text"),
    _ar_pair("reading.inference_reason", "State the supported risk and cite its clue.", "Infers a proportionate risk directly from the supplied condition.", ("A loose stone lies in the middle of the running lane.", "A runner could trip because the loose stone blocks the running lane.", ["runner could trip", "loose stone", "running lane"]), ("Rain has made the painted court shiny and slippery.", "Players could slip because rain has made the painted court slippery.", ["players could slip", "rain", "painted court slippery"])),
    _ar_pair("writing.reason_answer", "Recommend a safe action and support it with the hazard clue.", "Names a practical risk-reducing action and its specific reason.", ("The court is wet in one corner, and a dry half is open.", "Move the cones to the dry half because players could slip on the wet corner.", ["move to dry half", "slip on wet corner"]), ("Thunder begins, and an open hall is nearby.", "End outdoor play and move into the hall because thunder signals unsafe storm conditions.", ["move into hall", "thunder", "unsafe storm"])),
    _aq_pair("grammar.connectors_because_and_but", "Which connector shows the stated relationship?", ("The player waited ___ another runner was crossing.", "because", ["but", "and without reason", "although why"]), ("The rope was long, ___ the play space was narrow.", "but", ["because", "and because why", "so that reason"])),
    _ar_pair("grammar.sentence_order", "Arrange every part into one clear joined sentence.", "Uses all clauses in a grammatical order with the connector in the correct place.", ("Parts: tightened the loose knots / Isha / before practice / checked the boundary rope / and", "Before practice, Isha checked the boundary rope and tightened the loose knots.", ["Isha checked the boundary rope", "tightened the loose knots", "before practice"]), ("Parts: rain covered the court / because / the team / moved indoors", "The team moved indoors because rain covered the court.", ["team moved indoors", "because rain covered"]), interaction_type="short_text"),
    _aq_pair("reading.event_sequence", "Which step happens last?", ("Mark the square; place the beanbag; toss three rings; collect the rings.", "collect the rings", ["mark the square", "place the beanbag", "toss three rings"]), ("Count the balls; wipe them; place them in the net; tie the net.", "tie the net", ["count the balls", "wipe them", "place them in net"])),
    _ar_pair("writing.short_answer", "State the step order and explain the named check or reset.", "Preserves the printed order and gives a concise purpose tied to one step.", ("Check the rope; lay it straight; wait for the signal; pull; coil it afterward. Why check first?", "Check, lay, wait, pull, and coil in that order. Checking first prevents use of a damaged rope.", ["check, lay, wait, pull, coil", "damaged rope"]), ("Set a basket target; draw a rolling line; wait behind it; roll a foam ball; collect the ball only when it is still. When collect?", "Set, draw, wait, roll, and collect in that order. Collect the ball only when it is still.", ["set, draw, wait, roll, and collect", "only when it is still"]), interaction_type="short_text"),
    _aq_pair("reading.word_meaning_context", "What does the movement word mean here?", ("The paper spinner twirled, turning quickly around its centre.", "turned quickly around its centre", ["stayed flat without moving", "slid slowly in one direction", "folded into a smaller shape"]), ("The puppy scampered, moving with quick light steps across the grass.", "moved with quick light steps", ["slept without moving", "crawled heavily under a chair", "jumped straight into the air"])),
    _ar_pair("vocab.chapter_word_usage", "Define the word from context and use it in a fresh sentence.", "Defines the movement from its clue and transfers it accurately.", ("The tall cone wobbled, rocking unevenly after the ball brushed it.", "Wobbled means rocked unsteadily from side to side. New sentence: The loose stool wobbled when I touched it.", ["rocked unsteadily from side to side", "stool wobbled"]), ("The pinwheel spun, turning fast around its centre in the wind.", "Spun means turned quickly around a centre. New sentence: The bicycle wheel spun as Meera rode downhill.", ["turned quickly around a centre", "bicycle wheel spun"])),
    _ar_pair("reading.paragraph_main_idea", "Summarise the whole play card in one sentence.", "Combines preparation, coordinated action, and responsible result.", ("The team checked the court, practised slow passes, then completed a safe fast round.", "Careful preparation and practice helped the team complete a faster round safely.", ["preparation and practice", "faster round safely"]), ("Children shifted a game from a wet field to a dry hall and continued with softer equipment.", "Adapting the place and equipment allowed the children to continue playing safely.", ["adapting place and equipment", "continue safely"]), interaction_type="summary"),
    _ar_pair("writing.complete_sentence", "Repair the fragment with the supplied action detail.", "Produces a complete sentence with a doer, action, and supplied detail.", ("Fragment: The striped kite. Add climbs high above the busy playground.", "The striped kite climbs high above the busy playground.", ["kite climbs high", "above the busy playground"]), ("Fragment: The excited team. Add cheers for the final runner.", "The excited team cheers for the final runner.", ["team cheers", "final runner"]), interaction_type="short_text"),
]


LAUNCH_DEPTH_CASES = {
    "garden_verse_and_idea": [
        _launch_depth_case(
            "Skip past the chalk, skip round the tree, skip to the line and wait for me. The repeated action carries every player along the same garden path.",
            "How does repeated skip shape the garden-path verse, and what main idea joins all three lines?",
            "Repeating skip creates a quick, playful rhythm. The main idea is that players follow one shared route and finish by waiting for one another.",
            "repeating skip creates a quick, playful rhythm",
            "players follow one shared route and finish by waiting for one another",
        ),
        _launch_depth_case(
            "Roll the hoop softly, roll it past the chair, roll it to your teammate waiting over there. Each repeated line moves the same game forward.",
            "Explain the effect of repeated roll in the hoop game and state the whole verse idea.",
            "Repeated roll gives the lines a steady game rhythm. The verse is mainly about controlling a hoop and passing it safely to a teammate.",
            "repeated roll gives the lines a steady game rhythm",
            "controlling a hoop and passing it safely to a teammate",
        ),
        _launch_depth_case(
            "Splash with the boots, splash by the drain, splash through the puddles left by the rain. The repeated word links three careful rainy-day actions.",
            "What rhythm does repeated splash create, and what is the rainy-day verse mainly showing?",
            "Repeating splash creates a lively sound-and-action rhythm. The main idea is that children in boots enjoy moving through rain puddles together.",
            "repeating splash creates a lively sound-and-action rhythm",
            "children in boots enjoy moving through rain puddles together",
        ),
    ],
    "play_actions_in_sentences": [
        _launch_depth_case(
            "The sturdy bat strikes the soft ball near the boundary. Bat is the object, sturdy describes it, and strikes gives the action.",
            "Identify sturdy, bat, and strikes, then write the complete soft-ball sentence.",
            "Bat is a noun, sturdy is an adjective, and strikes is a verb. The sturdy bat strikes the soft ball near the boundary.",
            "bat is a noun, sturdy is an adjective, and strikes is a verb",
            "the sturdy bat strikes the soft ball near the boundary",
        ),
        _launch_depth_case(
            "A striped hoop rolls smoothly across the courtyard. Hoop names the object, striped describes it, and rolls tells its movement.",
            "Name the jobs of striped, hoop, and rolls, then form the full courtyard sentence.",
            "Hoop is a noun, striped is an adjective, and rolls is a verb. A striped hoop rolls smoothly across the courtyard.",
            "hoop is a noun, striped is an adjective, and rolls is a verb",
            "a striped hoop rolls smoothly across the courtyard",
        ),
        _launch_depth_case(
            "The quick goalkeeper catches the bouncing ball beside the cone. Goalkeeper is a noun, quick describes the player, and catches is the action.",
            "Explain quick goalkeeper catches and write one complete sentence with the ball and cone details.",
            "Goalkeeper is a noun, quick is an adjective, and catches is a verb. The quick goalkeeper catches the bouncing ball beside the cone.",
            "goalkeeper is a noun, quick is an adjective, and catches is a verb",
            "the quick goalkeeper catches the bouncing ball beside the cone",
        ),
    ],
    "outdoor_safety_reasoning": [
        _launch_depth_case(
            "Rain has made the stone steps shiny. A runner approaches quickly while holding a skipping rope and cannot see the small puddle on the second step.",
            "What risk do the shiny stone steps create, and what safe action fits the runner and rope clues?",
            "The runner could slip on the wet second step. The runner should slow down and carry the rope beside the steps because the shiny surface hides the puddle.",
            "the runner could slip on the wet second step",
            "slow down and carry the rope beside the steps",
        ),
        _launch_depth_case(
            "Mihir's cycling helmet rocks from side to side before he starts. The chin strap hangs loose, and the path has two steep turns.",
            "What safety problem do the loose helmet and steep turns suggest, and what should Mihir do?",
            "The loose helmet may not protect Mihir on the turns. He should stop and tighten the chin strap before riding because the helmet must stay in place.",
            "the loose helmet may not protect Mihir on the turns",
            "tighten the chin strap before riding",
        ),
        _launch_depth_case(
            "Strong wind pushes a badminton shuttle toward the parking lane. Players keep chasing it beyond the painted play area while a scooter is approaching slowly.",
            "Work out the parking-lane risk and recommend a proportionate safe response for the windy game.",
            "Chasing the shuttle into the parking lane could put players near the scooter. They should pause the game and move the net because the wind keeps carrying play outside the safe area.",
            "chasing the shuttle into the parking lane could put players near the scooter",
            "pause the game and move the net",
        ),
    ],
    "connect_actions_clearly": [
        _launch_depth_case(
            "The relay team marked the turning line. The chalk was faint. They redrew it because every runner needed to see where to turn.",
            "Join the relay turning-line facts with but and because, keeping the team, faint chalk, and reason in natural order.",
            "The team marked the turning line, but the chalk was faint, so they redrew it because every runner needed a clear place to turn.",
            "the team marked the turning line, but the chalk was faint",
            "they redrew it because every runner needed a clear place to turn",
            ordered=True,
        ),
        _launch_depth_case(
            "Ria packed a cap and a water bottle. She left the heavy jacket at home because the morning was warm. A light breeze arrived later.",
            "Arrange the cap, water bottle, jacket, and warm-morning facts using and and because.",
            "Ria packed a cap and a water bottle, but she left the heavy jacket at home because the morning was warm.",
            "Ria packed a cap and a water bottle, but she left the heavy jacket at home",
            "because the morning was warm",
            ordered=True,
        ),
        _launch_depth_case(
            "The ball crossed the side line. Arjun wanted to continue, but the referee stopped play because a bicycle was passing behind the goal.",
            "Build one natural sentence from the ball, referee, bicycle, but, and because details.",
            "Arjun wanted to continue after the ball crossed the side line, but the referee stopped play because a bicycle was passing behind the goal.",
            "Arjun wanted to continue after the ball crossed the side line, but the referee stopped play",
            "because a bicycle was passing behind the goal",
            ordered=True,
        ),
    ],
    "game_setup_sequence": [
        _launch_depth_case(
            "For a kite test, first tie the string, next check the tail knots, then walk to the open field, and finally wind the string after the flight.",
            "Retell the kite-test setup and reset in order, then explain why the tail knots are checked before the field walk.",
            "First tie the string, next check the tail, then walk to the field, and finally wind the string. The knots are checked early because a loose tail could spoil the flight.",
            "first tie the string, next check the tail, then walk to the field, and finally wind the string",
            "a loose tail could spoil the flight",
            ordered=True,
        ),
        _launch_depth_case(
            "A cone relay card says: place four cones, give each runner a band, start at the whistle card, check every cone, and stack the cones after the finish.",
            "Order the cone-relay preparation, action, check, and reset, then name the step that follows the finish.",
            "First place cones, next hand out bands, then start and check the course, and finally stack the cones. Stacking the cones is the reset step after the finish.",
            "first place cones, next hand out bands, then start and check the course, and finally stack the cones",
            "stacking the cones is the reset step after the finish",
            ordered=True,
        ),
        _launch_depth_case(
            "The beanbag game instructions say to mark a square, count six beanbags, throw one at a time, record where each lands, and return all six to the basket.",
            "Put the beanbag-game instructions in order and explain why recording happens before the basket reset.",
            "Mark the square, count the bags, throw them, record each landing, and return all six. Recording comes before reset because the landing evidence would be lost after the bags move.",
            "mark the square, count the bags, throw them, record each landing, and return all six",
            "landing evidence would be lost after the bags move",
            ordered=True,
        ),
    ],
    "outdoor_words_in_context": [
        _launch_depth_case(
            "Navi dodged the rolling tyre by stepping quickly to one side before it reached his feet. The side-step clue explains the action word.",
            "Define dodged from the rolling-tyre card and use dodged in a fresh everyday sentence.",
            "Dodged means moved quickly aside to avoid something. New sentence: The cyclist dodged a branch lying near the curb.",
            "dodged means moved quickly aside to avoid something",
            "the cyclist dodged a branch",
        ),
        _launch_depth_case(
            "Pema balanced the beanbag on her head by keeping it steady while she walked along the chalk line.",
            "Use the beanbag and chalk-line clues to explain balanced, then write balanced in a new context.",
            "Balanced means kept steady without letting it fall. New sentence: I balanced the lunch tray with both hands.",
            "balanced means kept steady without letting it fall",
            "I balanced the lunch tray with both hands",
        ),
        _launch_depth_case(
            "When the final bell sounded, the runner sprinted the last short distance, moving much faster than before to reach the ribbon.",
            "What does sprinted mean in the final-bell card, and how can sprinted fit another situation?",
            "Sprinted means ran very fast for a short distance. New sentence: Aarav sprinted to the shelter when the rain began.",
            "sprinted means ran very fast for a short distance",
            "Aarav sprinted to the shelter",
        ),
    ],
}

_add_launch_depth_variants(LEVELS, LAUNCH_DEPTH_CASES)


_SEMANTIC_OPTION_REPLACEMENTS = {'A bent link is always stronger.': 'The bent link shows that the chain is ready for '
                                    'one more test.',
 'The chain is singing a game song.': "The scraping sound is part of the swing's "
                                      'normal movement.',
 'The line says the cone is a house.': 'The repeated actions describe where the '
                                       'runners wait.',
 'The runners never move.': 'The repeated actions show that the race has already '
                            'ended.',
 'The swing needs faster use.': 'One faster turn will show whether the noise stops.',
 'Traffic makes the ball softer.': 'The ball becomes safer because the traffic is '
                                   'moving slowly.',
 'and then because': 'so',
 'or else and': 'so',
 'so that reason': 'so',
 'are run': 'ran'}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch04:assessment:07': {'accepted_answers': ['because'],
                               'options': ['and', 'because', 'but', 'so'],
                               'passage': 'Meena moved the cones ___ the path needed '
                                          'to stay clear.',
                               'prompt': 'Which connector shows the stated '
                                         'relationship?'},
 'eng_c3_ch04:assessment:17': {'accepted_answers': ['balances'],
                               'options': ['careful', 'child', 'beanbag', 'balances'],
                               'passage': 'A careful child balances the beanbag.',
                               'prompt': 'Which word is the action verb?'},
 'eng_c3_ch04:assessment:18': {'model_answer': 'Kavya carefully carries two seed trays '
                                               'into the greenhouse.',
                               'passage': 'Doer: Kavya; action: carries; object: two '
                                          'seed trays; manner: carefully; place: into '
                                          'the greenhouse.',
                               'prompt': 'Use all given details in one complete '
                                         'sentence.',
                               'relevance_terms': ['Kavya carefully carries',
                                                   'two seed trays',
                                                   'into the greenhouse'],
                               'slot_aliases': [['Kavya carefully carries'],
                                                ['two seed trays'],
                                                ['into the greenhouse']]},
 'eng_c3_ch04:assessment:22': {'model_answer': 'Rohan filled the watering can because '
                                               'the seedlings needed water.',
                               'passage': 'Parts: the seedlings needed water / because '
                                          '/ Rohan / filled the watering can',
                               'prompt': 'Arrange every part into one clear joined '
                                         'sentence.',
                               'relevance_terms': ['Rohan filled the watering can',
                                                   'because the seedlings needed '
                                                   'water'],
                               'slot_aliases': [['Rohan filled the watering can'],
                                                ['because the seedlings needed '
                                                 'water']]},
 'eng_c3_ch04:assessment:23': {'accepted_answers': ['fasten the folder'],
                               'options': ['arrange the cards by team',
                                           'fasten the folder',
                                           'take down the score cards',
                                           'slide the cards into the folder'],
                               'passage': 'Take down the score cards; arrange them by '
                                          'team; slide them into the folder; fasten '
                                          'the folder.',
                               'prompt': 'Which step happens last?'},
 'eng_c3_ch04:assessment:28': {'model_answer': 'The patient gardener waters the new '
                                               'seedlings before lunch.',
                               'passage': 'Fragment: The patient gardener. Add waters '
                                          'the new seedlings before lunch.',
                               'prompt': 'Repair the fragment with the given action '
                                         'detail.',
                               'relevance_terms': ['gardener waters',
                                                   'new seedlings before lunch'],
                               'slot_aliases': [['gardener waters'],
                                                ['new seedlings before lunch']]}}


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
    chapter_no=4,
    title="Out in the Garden",
    unit_title="Toys and Games",
    source_url=SOURCE_URL,
    page_extract="/tmp/zidd-ncert-class2-3/eng_c3_ch04.txt",
    source_anchors=SOURCE_ANCHORS,
    levels=LEVELS,
    assessment_pairs=ASSESSMENT_PAIRS,
)

_apply_semantic_copy_corrections(MANIFEST["levels"])
_apply_semantic_copy_corrections(
    MANIFEST["chapter_assessment"]["items"]
)
_apply_semantic_assessment_overrides(MANIFEST)
