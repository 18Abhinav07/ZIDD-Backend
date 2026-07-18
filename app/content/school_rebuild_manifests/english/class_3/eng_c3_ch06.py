"""Deep authored manifest for Class 3 English Chapter 6.

NCERT pages informed only the structural map and exercise forms. All runtime
passages, prompts, options, rubrics, and answers are original Zidd content.
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


CHAPTER_ID = "eng_c3_ch06"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/cesa106.pdf"


SOURCE_ANCHORS = [
    {"anchor_id": f"{CHAPTER_ID}:read:56-58", "section_label": "Let us Read: Water-Play Conflict and Cooperation", "page_start": 56, "page_end": 58, "source_url": f"{SOURCE_URL}#page=56", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:think:58-59", "section_label": "Let us Think: Causes, Help, and Preferred Games", "page_start": 58, "page_end": 59, "source_url": f"{SOURCE_URL}#page=58", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:speak:60", "section_label": "Let us Speak: Optional Story Retelling", "page_start": 60, "page_end": 60, "source_url": f"{SOURCE_URL}#page=60", "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:learn:61-62", "section_label": "Let us Learn: Pronouns and Position Words", "page_start": 61, "page_end": 62, "source_url": f"{SOURCE_URL}#page=61", "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:do:63", "section_label": "Let us Do: Optional Rangoli Sequence", "page_start": 63, "page_end": 63, "source_url": f"{SOURCE_URL}#page=63", "coverage_treatment": "optional_creative", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:write:64-65", "section_label": "Let us Write: Text-Guided Scene Description and Game Words", "page_start": 64, "page_end": 65, "source_url": f"{SOURCE_URL}#page=64", "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
    {"anchor_id": f"{CHAPTER_ID}:explore:66", "section_label": "Let us Explore: Optional Family Game Interview", "page_start": 66, "page_end": 66, "source_url": f"{SOURCE_URL}#page=66", "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
    {"anchor_id": f"{CHAPTER_ID}:self-assessment:67", "section_label": "Self Assessment: Optional Learner Reflection", "page_start": 67, "page_end": 67, "source_url": f"{SOURCE_URL}#page=67", "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
]


CRUNCH_BAR = {
    "raft_conflict_sequence": _crunch(
        [
            (
                "Meera marked a test lane for her foil boat. Ali placed stones in it, Meera explained that they blocked the route, and Ali moved the stones before timing the boat with her.",
                "Meera marked the lane first, Ali blocked it, Meera explained the problem, and Ali cleared it before joining the test. Listening changed the blockage into shared work.",
                ["marked then blocked then explained then cleared then tested", "Ali cleared the lane before joining"],
                ["listening changed blockage into shared work", "shared test followed"],
            ),
            (
                "Asha's paper fish was drying beside the tray. Nikhil dropped water on it, admitted the mistake, brought dry paper, and helped trace a replacement.",
                "The fish was drying first, water damaged it, Nikhil admitted the mistake, and replacement work followed. Honest action and repair rebuilt cooperation.",
                ["drying then damaged then admitted then replaced", "helped trace a replacement last"],
                ["honest action and repair", "rebuilt cooperation"],
            ),
            (
                "Two groups reached for one narrow channel. They paused, measured the tray, marked turns with a timer, and completed both current tests without bumping models.",
                "The channel conflict came first, measuring and timed turns followed, and both tests finished last. A fair turn plan protected each model.",
                ["conflict then paused then measured then timed then finished", "both tests finished last"],
                ["fair turn plan protected each model", "timed turns solved conflict"],
            ),
            (
                "Rehan laughed when a clay boat tipped. Its maker asked him to stop, Rehan noticed a cracked side, fetched clay, and helped seal it.",
                "The boat tipped first, laughter and a clear request followed, and Rehan fetched clay before helping. Respecting the request led to useful repair.",
                ["tipped then laughed then request then fetched then repaired", "clay was fetched before repair"],
                ["respecting the request led to repair", "help replaced laughter"],
            ),
            (
                "Kavya moved Priya's labelled waterwheel without asking. Priya showed the name tag, Kavya returned it, and they built a separate wheel together from spare cups.",
                "The labelled wheel was moved first, Priya showed ownership, Kavya returned it, and a separate shared wheel came last. Respect for ownership made cooperation possible.",
                ["moved then name tag then returned then built", "separate wheel came last"],
                ["respect for ownership", "made cooperation possible"],
            ),
        ],
        prompt="Order the conflict and repair events, then state how the response changed the result.",
        interaction_type="summary",
        ordered=True,
    ),
    "boundary_inference_and_reason": _crunch(
        [
            (
                "Lina covers her result card after a classmate begins copying its numbers. A blank record card is available.",
                "Ask the classmate to record a separate test on the blank card because Lina's covered card shows she wants her own results left unchanged.",
                ["use a separate blank card", "ask before using Lina's results"],
                ["Lina covers her result card", "wants results left unchanged"],
            ),
            (
                "One child keeps squeezing a dropper near another child's face. The other child steps back and says, 'Point it into the tray.'",
                "Point the dropper into the tray and stop squeezing near the child because the step back and spoken request show a clear safety boundary.",
                ["point the dropper into the tray", "stop squeezing near the child"],
                ["step back and spoken request", "clear safety boundary"],
            ),
            (
                "Farah frowns when her partner starts the timer before her boat reaches the line. She resets the boat at the marked start.",
                "Restart the timer when the boat reaches the marked line because Farah's reset shows that she wants the test to begin from the agreed start.",
                ["restart at the marked line", "wait until boat reaches start"],
                ["Farah resets the boat", "agreed start"],
            ),
            (
                "A younger pupil watches a waterwheel test but says the fast splashes hurt his eyes. A clear screen can stand between him and the tray.",
                "Place the clear screen between the pupil and tray because it lets him watch while blocking the fast splashes that bother his eyes.",
                ["place the clear screen", "between pupil and tray"],
                ["fast splashes hurt his eyes", "still lets him watch"],
            ),
            (
                "Two partners both want to pour the final cup. One measured all the water; the other built the channel, and they can hold the cup together.",
                "Let both partners hold and pour the final cup because each completed an important part and the shared action includes them fairly.",
                ["both partners hold and pour", "shared final action"],
                ["each completed an important part", "includes them fairly"],
            ),
        ],
        prompt="Choose a respectful next action and use the exact boundary or fairness clue as the reason.",
    ),
    "speakers_and_dialogue_marks": _crunch(
        [
            (
                "Draft: that is my test cup said sonal. may i use it after you asked arun",
                "'That is my test cup,' said Sonal. 'May I use it after you?' asked Arun.",
                ["Sonal names ownership", "Arun asks permission"],
                ["Sonal and Arun capitals", "comma, quotes, and question mark"],
            ),
            (
                "Amit says the floor is slippery. Bela replies that she will bring the warning cone.",
                "Amit said, 'The floor is slippery.' Bela replied, 'I will bring the warning cone.'",
                ["Amit states the danger", "Bela offers the cone"],
                ["quotation marks and capitals", "full stops close both lines"],
            ),
            (
                "Draft: please return my ruler said hina. sorry i picked up the wrong one answered jay",
                "'Please return my ruler,' said Hina. 'Sorry, I picked up the wrong one,' answered Jay.",
                ["Hina asks for her ruler", "Jay apologises"],
                ["Please, Hina, Sorry, and Jay capitals", "commas and quotation marks"],
            ),
            (
                "The teacher asks who moved the towel. Mahi admits that she moved it to dry the spill.",
                "The teacher asked, 'Who moved the towel?' Mahi replied, 'I moved it to dry the spill.'",
                ["teacher asks the question", "Mahi admits the action"],
                ["question mark and quotation marks", "capitals and full stop"],
            ),
            (
                "Draft: great our wheels turn together cheered veer. shall we time them asked numa",
                "'Great, our wheels turn together!' cheered Veer. 'Shall we time them?' asked Numa.",
                ["Veer cheers first", "Numa asks second"],
                ["exclamation mark then question mark", "names capitalised and lines quoted"],
            ),
        ],
        prompt="Name what each speaker contributes, then repair the capitals and dialogue punctuation.",
        interaction_type="dialogue",
    ),
    "pronouns_and_positions": _crunch(
        [
            (
                "Scene: Neha gives Iqbal a sponge. He places it inside the bucket, which stands beside the sink.",
                "He refers to Iqbal, and it refers to the sponge. The sponge is inside the bucket, and the bucket is beside the sink.",
                ["He refers to Iqbal", "it refers to the sponge"],
                ["sponge is inside the bucket", "bucket is beside the sink"],
            ),
            (
                "Scene: Two paper boats rest under a lamp. They cast shadows behind a blue screen, and Rupa moves them onto a shelf.",
                "They and them refer to the two paper boats. The boats begin under the lamp, cast shadows behind the screen, and end on the shelf.",
                ["They and them refer to the two paper boats"],
                ["boats begin under the lamp", "shadows behind the screen", "end on the shelf"],
            ),
            (
                "Scene: Mohan puts a funnel between two jars. He lays its handle on a cloth in front of the tray.",
                "He refers to Mohan, and its refers to the funnel. The funnel is between the jars, with its handle on the cloth in front of the tray.",
                ["He refers to Mohan", "its refers to the funnel"],
                ["funnel is between the jars", "handle on the cloth", "in front of the tray"],
            ),
            (
                "Scene: Sara and Uma carry a tub. They set it below the tap, while three cups stay on a rack above them.",
                "They and them refer to Sara and Uma, while it refers to the tub. The tub is below the tap, and the cups are on the rack above the pupils.",
                ["They and them refer to Sara and Uma", "it refers to the tub"],
                ["tub is below the tap", "cups are on the rack above the pupils"],
            ),
            (
                "Scene: A cork lies beside a ruler. Vikram picks it up and places it in a bowl behind his notebook.",
                "It refers to the cork in both places, and his refers to Vikram. The cork moves from beside the ruler to the bowl behind Vikram's notebook.",
                ["It refers to the cork", "his refers to Vikram"],
                ["cork lies beside the ruler", "bowl behind Vikram's notebook"],
            ),
        ],
        prompt="Say what each pronoun means and write every place shown on the text card.",
    ),
    "water_play_words": _crunch(
        [
            (
                "The water trickled, moving in a thin slow stream through the narrow gap.",
                "Trickled means flowed slowly in a thin stream. New sentence: Rainwater trickled down the window after the shower.",
                ["flowed slowly in a thin stream", "through narrow gap"],
                ["rainwater trickled down the window", "after the shower"],
            ),
            (
                "The floating lid bobbed, moving up and down as tiny waves passed.",
                "Bobbed means moved gently up and down. New sentence: The yellow float bobbed beside the fishing line.",
                ["moved gently up and down", "tiny waves passed"],
                ["yellow float bobbed", "beside fishing line"],
            ),
            (
                "Pavan objected, saying clearly that the shared cup should not be taken without a turn.",
                "Objected means spoke against an action. New sentence: Mira objected when the game began before every player was ready.",
                ["spoke against an action", "cup taken without a turn"],
                ["Mira objected", "game began too early"],
            ),
            (
                "The wet paper sagged, bending downward because it could no longer hold its shape.",
                "Sagged means bent or hung downward after losing support. New sentence: The old shelf sagged under the heavy books.",
                ["bent downward", "lost its shape"],
                ["old shelf sagged", "under heavy books"],
            ),
            (
                "The partners reconciled, ending their quarrel and agreeing to test the model together.",
                "Reconciled means became friendly again after a disagreement. New sentence: The teammates reconciled after making a fair turn plan.",
                ["became friendly again", "after a disagreement"],
                ["teammates reconciled", "fair turn plan"],
            ),
        ],
        prompt="Explain the word from its clue, then use the same meaning in a different situation.",
    ),
    "text_scene_short_answers": _crunch(
        [
            (
                "Parts: near the drain / placed / a warning cone / Ritu / after the spill. Question: Why was the cone useful?",
                "After the spill, Ritu placed a warning cone near the drain. The cone warned others about the wet area.",
                ["Ritu placed a warning cone", "after spill near drain"],
                ["warned others", "wet area"],
            ),
            (
                "Scene: one cup is full; a second cup is empty; a line on the jug marks one more cup. Question: How much water is still needed?",
                "One more cup of water is needed because the jug line marks that amount above the water already poured.",
                ["one more cup is needed", "amount still needed"],
                ["jug line marks one cup", "water already poured"],
            ),
            (
                "Parts: with a dry sponge / cleaned / the blue tray / Kabir / before storage. Question: What did Kabir use?",
                "Before storage, Kabir cleaned the blue tray with a dry sponge. He used the dry sponge for cleaning.",
                ["Kabir cleaned the blue tray", "before storage"],
                ["used the dry sponge", "for cleaning"],
            ),
            (
                "Scene: Tara holds the timer; Imran releases the boat at the start line; the timer reads twelve seconds at the finish. Question: Who performs each job?",
                "Tara times the test, while Imran releases the boat at the start line. The timer records twelve seconds at the finish.",
                ["Tara times and Imran releases", "jobs named correctly"],
                ["start line", "twelve seconds at finish"],
            ),
            (
                "Parts: during the second test / flowed / through the paper channel / the coloured water / slowly. Question: Where did it flow?",
                "During the second test, the coloured water flowed slowly through the paper channel. It flowed through the paper channel.",
                ["coloured water flowed slowly", "during second test"],
                ["through the paper channel", "place answers question"],
            ),
        ],
        prompt="Build the sentence from every card part, then answer only the stated question.",
        interaction_type="short_text",
    ),
}


LEVELS = [
    _make_level(
        level_id="raft_conflict_sequence",
        title="Track conflict, repair, and shared play",
        focus="sequence a conflict-resolution narrative and identify its main idea",
        outcome="Order the initial play, disruption, clear boundary, helpful response, and shared result, then state the story's cooperation message.",
        skill_ids=["reading.event_sequence", "reading.paragraph_main_idea"],
        choice_skill_ids=["reading.event_sequence"],
        episode_kind="comprehension_studio",
        source_anchor_ids=[f"{CHAPTER_ID}:read:56-58", f"{CHAPTER_ID}:think:58-59"],
        principle="Conflict stories turn when a character names the problem and another responds; the main idea connects that response to the changed relationship and result.",
        connect={"teaching_block": "A clear retell follows more than actions: it notices the moment a boundary is stated, the response to it, and the new way the characters act together.", "passage": "Navi tested cork rafts in a water tray. Sam blew one over, Navi asked him to stop, and Sam helped rebuild it before they raced separate rafts.", "prompt": "Trace play, disruption, boundary, repair, and shared result before naming the central idea."},
        choice_prompt="Which event comes first, second, or last as named in this conflict-resolution card?",
        response_prompt="order the turning points and state the main idea about respect and cooperation.",
        rubric_descriptions=["Orders the play, disruption, response, repair, and result accurately.", "States a main idea connecting respect for a boundary with later cooperation."],
        examples=[
            _q("Tara floated a cork raft, Veer splashed it, Tara asked for space, and Veer helped dry the sail.", "Veer helped dry the sail.", ["Tara floated the raft.", "Veer splashed it.", "Tara asked for space."], prompt="What did Veer do last?"),
            _q("First, Mina built a leaf bridge. Next, Jo stepped on it by mistake. Finally, Jo gathered fresh leaves for a stronger bridge.", "Jo stepped on the first bridge.", ["Mina built it first.", "Fresh leaves were gathered last.", "Jo gathered leaves before arriving."], prompt="Which event happened second?"),
            _r("Rafi arranged small boats in a tub. Anu pushed all of them into one corner, Rafi explained that he was testing distance, and Anu reset the boats before joining the test.", "Rafi arranged the boats first, Anu disrupted them, Rafi explained the test, and Anu reset them before joining. The main idea is that listening to a clear explanation turned disruption into helpful participation.", [["arranged", "disrupted", "explained", "reset", "joined"], ["listening to explanation", "helpful participation"]], ordered=True),
            _r("Leela made a channel from blocks. Karan removed one block for his own tower, so water leaked. After Leela pointed out the leak, Karan returned the block and built beside her.", "The channel was built, a block was removed, the leak was explained, and the block was returned before separate building continued. The passage shows that recognising the effect of an action can repair both a model and cooperation.", [["built", "removed", "leak", "returned", "continued"], ["recognising effect", "repair model and cooperation"]], ordered=True),
            _r("A paper cup boat belonged to Ina's experiment. Dev grabbed it without asking, bent the mast, apologised, and used a spare cup to make a replacement with Ina.", "The boat was taken, damaged, followed by an apology, and replaced together. The main idea is that taking responsibility and repairing harm can lead to respectful shared work.", [["taken", "damaged", "apology", "replaced"], ["responsibility", "repairing harm", "respectful work"]], ordered=True),
            _r("Two pupils wanted the same water lane. They marked two parallel lanes with string, tested both, and held a fair race without collisions.", "The lane conflict came first, two lanes were marked, both were tested, and a fair race followed. The central idea is that dividing shared space fairly allowed both pupils to play.", [["conflict", "marked", "tested", "race"], ["divide shared space", "both play"]], ordered=True),
            _r("A gust moved Sia's raft into Om's model. Om first blamed Sia, then noticed the open window, helped separate the models, and suggested closing it.", "The collision happened, Om blamed Sia, the wind clue was noticed, and both models were separated before the window was closed. The passage shows evidence correcting an unfair assumption and guiding a joint solution.", [["collision", "blame", "wind clue", "separated", "closed"], ["evidence corrected assumption", "joint solution"]], ordered=True),
            _r("Neer laughed when a beginner's raft sank. The beginner explained that the base leaked, Neer stopped laughing, and they tested three ways to seal it.", "The raft sank, laughter occurred, the leak was explained, and joint testing followed. The main idea is that listening and helping replaced an unkind response with useful cooperation.", [["sank", "laughed", "explained", "tested"], ["listening and helping", "replaced unkind response"]], ordered=True),
            _r("Pia blocked the whole tray for one large model. Her group explained that four small tests were waiting, so Pia moved the model to half the tray and shared the rest.", "The large model blocked the tray, the waiting tests were explained, and Pia moved it before sharing space. The central idea is that understanding others' needs led to a fair use of shared materials.", [["blocked", "tests explained", "moved", "shared"], ["others' needs", "fair shared materials"]], ordered=True),
            _q("A raft bumped a marker, the maker noticed a bent fin, and a partner offered tape.", "The maker noticed the bent fin.", ["The raft was repaired first.", "The marker disappeared.", "The partner used tape before the bump."], prompt="What happened immediately before the tape was offered?"),
            _r("Kabir kept blowing another child's sail after being asked to stop. A teacher restated the boundary, Kabir stopped, and he built a separate wind test with permission.", "The repeated blowing came first, the boundary was restated, Kabir stopped, and a separate permitted test followed. The passage shows that respecting a firm limit made a safer independent activity possible.", [["blew", "boundary restated", "stopped", "separate test"], ["respecting firm limit", "safe permitted activity"]], ordered=True),
            _q("First, the group found a leak. Next, it dried the base. Last, it added a patch.", "The group dried the base.", ["The patch was added first.", "The leak appeared after repair.", "The group filled the base with water."], prompt="Which action happened second?"),
            _r("A learner copied Mira's raft design and claimed it as his own. Mira showed her planning card, he acknowledged her idea, and they added both names to a revised design.", "The design was copied, Mira showed evidence, credit was acknowledged, and both names appeared on the revision. The main idea is that honest credit and collaboration repaired an ownership conflict.", [["copied", "planning card", "acknowledged", "both names"], ["honest credit", "repaired conflict"]], ordered=True),
            _r("A child spilled water while reaching across the tray. She warned others, fetched a cloth, dried the floor, and then moved tools closer before continuing.", "The spill occurred, a warning came next, the floor was dried, and tools were moved before play resumed. The passage shows responsible clean-up followed by a change that reduced another spill risk.", [["spill", "warning", "dried", "tools moved", "resumed"], ["responsible clean-up", "reduced risk"]], ordered=True),
        ],
        crunch_bar=CRUNCH_BAR["raft_conflict_sequence"],
        misconception="The learner omits the boundary or apology and reports only the final play, or claims cooperation happened simply because characters ended together without explaining the change in behaviour.",
        remediation="Place the events in play-disrupt-say-repair-result order, then write how the say or repair step changed the ending.",
    ),
    _make_level(
        level_id="boundary_inference_and_reason",
        title="Infer feelings and justify respectful action",
        focus="infer concerns from behaviour and write reasons for respectful conflict responses",
        outcome="Infer a likely feeling or motive from a specific clue and recommend an action that protects ownership, safety, and fair participation.",
        skill_ids=["reading.inference_reason", "writing.reason_answer"],
        choice_skill_ids=["reading.inference_reason"],
        episode_kind="application_mission",
        source_anchor_ids=[f"{CHAPTER_ID}:read:56-58", f"{CHAPTER_ID}:think:58-59"],
        principle="A supported idea explains behaviour without mind-reading; a respectful reason answer names an action and ties it to the person's stated boundary or shared safety need.",
        connect={"teaching_block": "Anger, worry, and disappointment may come from a damaged object, ignored request, unsafe action, or unfair turn. The exact cause determines the helpful response.", "passage": "Rina moves her model away after Dev reaches for it a second time. She says, 'Please ask before touching it.'", "prompt": "Use both the movement and direct request to infer the concern and choose a respectful next action."},
        choice_prompt="Which idea fits the action and stated clue?",
        response_prompt="recommend a respectful action and justify it from the boundary, need, or safety clue.",
        rubric_descriptions=["States a respectful and practical next action for the conflict.", "Uses the visible boundary, ownership, fairness, or safety clue as the reason."],
        examples=[
            _q("A child pulls her raft closer after someone changes its sail without asking.", "She likely wants control over changes to her own model.", ["She wants the sail changed again secretly.", "She has forgotten the raft exists.", "She wants every model destroyed."]),
            _q("Sam stops smiling when his careful test results are splashed away and points to the wet record card.", "Sam is upset because the splash damaged his recorded work.", ["Sam dislikes all water trays.", "Sam wants the card wetter.", "Sam has completed a dry test elsewhere."]),
            _r("One pupil keeps blowing another pupil's sail after hearing 'stop'. A separate fan station is empty.", "Stop blowing the other sail and use the empty fan station with permission because the owner stated a clear boundary and another testing space is available.", [["stop blowing", "use empty fan station"], ["clear boundary", "other space available"]]),
            _r("A shared tray has room for two models, but one learner spreads six unused tools across the second space.", "Move the unused tools to the supply mat because shared tray space should remain available for the second model.", [["move unused tools", "supply mat"], ["shared tray", "space for second model"]]),
            _r("A child accidentally bends a mast and immediately says what happened. Spare card and tape are available.", "Acknowledge the mistake and help replace the mast because honest reporting and available materials make a repair possible.", [["acknowledge and help replace", "repair mast"], ["honest reporting", "spare card and tape"]]),
            _r("Two learners both reach for the only dropper. Each needs it for one minute, and a timer is ready.", "Use one timed minute each because equal turns let both learners complete their tests with the single dropper.", [["timed minute each", "equal turns"], ["one dropper", "both tests"]]),
            _r("A learner laughs at a sinking model while its maker quietly gathers the pieces and looks down.", "Stop laughing and offer help gathering the pieces because the maker's quiet withdrawal suggests the response caused hurt rather than useful feedback.", [["stop laughing", "offer help"], ["quiet withdrawal", "caused hurt"]]),
            _r("One child copies another design without credit. The original planning card has a name and date.", "Credit the original planner and discuss how to build a joint version because the dated card shows whose idea came first.", [["credit original planner", "joint version"], ["name and date", "idea came first"]]),
            _r("Water spills beside an electrical extension board. An adult and a dry exit route are nearby.", "Step away and alert the adult because water beside electrical equipment creates a serious safety risk.", [["step away", "alert adult"], ["water beside electrical board", "safety risk"]]),
            _q("A partner suggests two lanes after both models keep colliding in one narrow channel.", "The partner wants each model to have a clear route.", ["The partner wants more collisions.", "The partner thinks lanes remove water.", "The partner wants to end every test."]),
            _r("A pupil blocks the tray while decorating and says she did not notice three waiting models.", "Show the waiting models and agree on a smaller decorating area because the shared tray must serve all four users.", [["show waiting models", "smaller area"], ["shared tray", "all four users"]]),
            _q("A child closes the window after noticing that gusts keep moving every model.", "The child wants the tests to use controlled conditions.", ["The child wants stronger random gusts.", "The window is part of a raft.", "The child wants no observations."]),
            _r("A beginner asks for help folding a sail, and an experienced learner has finished their own model.", "Demonstrate one fold and let the beginner try because the experienced learner is available and guided practice supports independent learning.", [["demonstrate one fold", "beginner tries"], ["learner available", "supports independence"]]),
            _r("A student angrily says a partner ruined the route, but the card shows a gust moved the raft before either child touched it.", "Pause the blame and review the gust evidence because the visible card shows the movement was not caused by the partner.", [["pause blame", "review evidence"], ["gust moved raft", "partner did not cause"]]),
        ],
        crunch_bar=CRUNCH_BAR["boundary_inference_and_reason"],
        misconception="The learner assumes anger means dislike, ignores a directly stated stop or ownership boundary, or recommends forced sharing when safety, permission, or personal work requires another response.",
        remediation="Compare what was observed with what was said, work out only what both clues support, then choose a response that protects safety, consent, credit, and fair access.",
    ),
    _make_level(
        level_id="speakers_and_dialogue_marks",
        title="Track conflict speakers and mark their lines",
        focus="identify dialogue speakers and use correct capitalization and punctuation",
        outcome="Identify who states a boundary, gives a reason, apologises, or proposes a repair, then punctuate the exchange so each contribution is clear.",
        skill_ids=["reading.dialogue_attribution", "grammar.punctuation_capitalization"],
        choice_skill_ids=["reading.dialogue_attribution"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:read:56-58", f"{CHAPTER_ID}:write:64-65"],
        principle="Speaker meaning and reporting clauses work together; punctuation must show questions, firm boundaries, apologies, and replies without changing who contributes what.",
        connect={"teaching_block": "In a repair exchange, one line may name the harm, another may acknowledge it, and a third may offer action. Correct punctuation keeps those roles distinct.", "passage": "'My sail is bent,' Noor said. 'I am sorry,' replied Jai. 'I will bring a spare card.'", "prompt": "Assign the problem, apology, and repair offer before checking quotation and end marks."},
        choice_prompt="Who says the named line, and what does it contribute?",
        response_prompt="identify each turn's speaker and rewrite the turns with correct capitals, quotation marks, commas, and end punctuation.",
        rubric_descriptions=["Identifies the correct speaker for each boundary, reason, apology, or repair line.", "Uses capitals, quotation marks, reporting punctuation, and suitable end marks correctly."],
        examples=[
            _q("'Please stop moving my raft,' Mira told Dev. 'I will leave it here,' he replied.", "Dev agrees to leave the raft in place.", ["Mira agrees to move it again.", "The raft speaks second.", "Dev asks Mira to stop."]),
            _q("'Why did the lane leak?' Arun asked. 'One block is missing,' Sia answered.", "Sia identifies the missing block.", ["Arun identifies it in the first line.", "The lane answers Arun.", "Sia asks the question."]),
            _r("Draft: that splash ruined my notes said tara. i am sorry replied om i will help rewrite them", "'That splash ruined my notes,' said Tara. 'I am sorry,' replied Om. 'I will help rewrite them.'", [["Tara names harm", "Om apologises and offers help"], ["Tara and Om capitals", "quotation marks", "commas and full stops"]], interaction_type="dialogue"),
            _r("Draft: may i use the dropper asked zoya. yes after my turn said neel", "'May I use the dropper?' asked Zoya. 'Yes, after my turn,' said Neel.", [["Zoya asks", "Neel answers with turn"], ["question mark", "Zoya and Neel capitals", "quotation marks"]], interaction_type="dialogue"),
            _r("Asha states that her model is still drying. Kabir asks where he should place his raft.", "Asha said, 'My model is still drying.' Kabir asked, 'Where should I place my raft?'", [["Asha states", "Kabir asks"], ["quotation marks", "question mark", "capitals"]], interaction_type="dialogue"),
            _r("Draft: stop blowing the sail said rina. i did not hear you replied ben", "'Stop blowing the sail,' said Rina. 'I did not hear you,' replied Ben.", [["Rina sets boundary", "Ben explains"], ["Rina and Ben capitals", "quotation marks", "commas"]], interaction_type="dialogue"),
            _r("Navi asks whether Sam can help repair the mast. Sam agrees and offers tape.", "Navi asked, 'Can you help repair the mast?' Sam replied, 'Yes, I can bring the tape.'", [["Navi asks", "Sam agrees"], ["question mark", "quotation marks", "capitals"]], interaction_type="dialogue"),
            _r("Draft: this is my planning card said leela. then i should credit your idea answered jo", "'This is my planning card,' said Leela. 'Then I should credit your idea,' answered Jo.", [["Leela presents evidence", "Jo acknowledges credit"], ["Leela and Jo capitals", "quotation marks", "commas"]], interaction_type="dialogue"),
            _r("A teacher asks why the floor is wet. Mina explains that the tray spilled and says she has fetched a cloth.", "The teacher asked, 'Why is the floor wet?' Mina replied, 'The tray spilled, and I have fetched a cloth.'", [["teacher asks", "Mina explains and acts"], ["question mark", "quotation marks", "comma"]], interaction_type="dialogue"),
            _q("'The fan is moving every raft,' said Veer. 'Then I will switch it off,' the adult replied.", "The adult proposes switching off the fan.", ["Veer proposes more wind.", "The fan speaks second.", "The adult denies the movement."]),
            _r("Draft: your model is in my lane said pia. lets mark two lanes suggested noor", "'Your model is in my lane,' said Pia. 'Let us mark two lanes,' suggested Noor.", [["Pia names overlap", "Noor proposes solution"], ["Pia and Noor capitals", "quotation marks", "commas"]], interaction_type="dialogue"),
            _q("'I bent the fin by accident,' Om admitted. 'Thank you for telling me,' Ria said.", "Ria acknowledges Om's honesty.", ["Om thanks himself.", "The fin admits the mistake.", "Ria denies hearing him."]),
            _r("A beginner says the fold is confusing. An experienced learner offers to show one step.", "The beginner said, 'This fold is confusing.' The experienced learner replied, 'I will show one step, and then you can try.'", [["beginner states difficulty", "learner offers guided help"], ["quotation marks", "capitals", "full stops"]], interaction_type="dialogue"),
            _r("Draft: are the boats ready asked jai. not yet the glue is wet answered sana", "'Are the boats ready?' asked Jai. 'Not yet; the glue is wet,' answered Sana.", [["Jai asks", "Sana explains delay"], ["question mark", "Jai and Sana capitals", "quotation marks"]], interaction_type="dialogue"),
        ],
        crunch_bar=CRUNCH_BAR["speakers_and_dialogue_marks"],
        misconception="The learner swaps the boundary-setter and responder, treats the nearest name as speaker without reading the reporting verb, or punctuates every line as a statement despite a question or exclamation.",
        remediation="Identify the purpose and speaker of each contribution, then apply the correct end mark before closing quotation marks.",
    ),
    _make_level(
        level_id="pronouns_and_positions",
        title="Track pronouns and locate every object",
        focus="resolve pronouns and use position prepositions from text-only scene cards",
        outcome="Connect he, she, it, they, and them to clear referents and describe object locations with accurate in, on, under, beside, between, or behind phrases.",
        skill_ids=["grammar.pronouns", "grammar.prepositions"],
        choice_skill_ids=["grammar.pronouns"],
        episode_kind="language_lab",
        source_anchor_ids=[f"{CHAPTER_ID}:learn:61-62", f"{CHAPTER_ID}:write:64-65"],
        principle="Pronouns depend on number and event logic; prepositions depend on the explicit spatial relation supplied in the text card, never an unseen picture.",
        connect={"teaching_block": "A scene can be fully described in words. Resolve who handles each object, then use the location phrase exactly as given.", "passage": "Mina placed the blue raft in the tray. She set its spare sail beside the towel, and both tools remained behind her notebook.", "prompt": "Link she and its to their nouns, then map in, beside, and behind from the printed scene."},
        choice_prompt="Which noun does the pronoun replace?",
        response_prompt="resolve the pronouns and write accurate location sentences from every supplied relation.",
        rubric_descriptions=["Links each pronoun to the correct person or object using number and event logic.", "Uses the supplied prepositions to state every required position correctly."],
        examples=[
            _q("Ria handed the cloth to Dev. He dried the table with it. Who does he refer to?", "Dev", ["Ria", "the cloth", "the table"]),
            _q("The two rafts touched the wall, so Mina moved them. What does them refer to?", "the two rafts", ["the wall", "Mina", "the movement"]),
            _r("Scene: Sia puts a cork in a bowl. She places it under a small cup. The bowl is beside a towel.", "She refers to Sia, and it refers to the cork. The cork is in the bowl under the cup, and the bowl is beside the towel.", [["She refers to Sia", "it refers to the cork"], ["cork is in the bowl under the cup", "bowl is beside the towel"]]),
            _r("Scene: Arun gives Leela a blue sail. She puts it between two dry books. Arun stands behind the chair.", "She refers to Leela, and it refers to the sail. The sail is between the books, while Arun is behind the chair.", [["She refers to Leela", "it refers to the sail"], ["sail is between the books", "Arun is behind the chair"]]),
            _r("Scene: Two droppers lie on a tray. They are beside a cup, and Mina places them inside a box afterward.", "They and them refer to the two droppers. The droppers begin on the tray beside the cup and end inside the box.", [["They and them refer to the two droppers"], ["droppers begin on the tray beside the cup and end inside the box"]]),
            _r("Scene: Jai puts the notebook under the shelf. He places its pencil on the notebook. A bag rests beside him.", "He and him refer to Jai, while its refers to the notebook. The notebook is under the shelf, the pencil is on it, and the bag is beside Jai.", [["He and him refer to Jai", "its refers to the notebook"], ["notebook is under the shelf", "pencil is on it", "bag is beside Jai"]]),
            _r("Scene: Nora and Ben carry two models. They place one between the cones and the other behind a screen.", "The pronoun they refers to Nora and Ben. One model is between the cones, and the other model is behind the screen.", [["pronoun they refers to Nora and Ben"], ["one model is between the cones", "other model is behind the screen"]]),
            _r("Scene: The red fin falls from the raft. It lands in the water near a marker. Sia lifts it onto a towel.", "Both uses of it refer to the red fin. The fin lands in the water near the marker and is moved onto the towel.", [["Both uses of it refer to the red fin"], ["fin lands in the water near the marker", "is moved onto the towel"]]),
            _r("Scene: Rafi shows Mira the patch. She stores it inside the repair box, which is under the table.", "She refers to Mira, and it refers to the patch. The patch is inside the repair box, and the box is under the table.", [["She refers to Mira", "it refers to the patch"], ["patch is inside the repair box", "box is under the table"]]),
            _q("The tray held two cups. They stood beside a folded cloth. What does they refer to?", "the two cups", ["the tray", "the cloth", "the folding"]),
            _r("Scene: Om moves the fan behind a screen. He places its cable along the wall and the switch beside the door.", "He refers to Om, and its refers to the fan. The fan is behind the screen, its cable is along the wall, and the switch is beside the door.", [["He refers to Om", "its refers to the fan"], ["fan is behind the screen", "cable is along the wall", "switch is beside the door"]]),
            _q("Tara set the mast on the raft before she painted it. Who does she refer to?", "Tara", ["the mast", "the raft", "the paint"]),
            _r("Scene: A ball is in a box. The box is on a bench, and two shoes are under the bench. They belong to Mehul.", "The pronoun they refers to the two shoes. The ball is in the box, the box is on the bench, and the shoes are under the bench.", [["pronoun they refers to the two shoes"], ["ball is in the box", "box is on the bench", "shoes are under the bench"]]),
            _r("Scene: Leena puts a marker between two jars. She places them beside the tray and stands in front of the shelf.", "She refers to Leena, and them refers to the two jars. The marker is between the jars, the jars are beside the tray, and Leena is in front of the shelf.", [["She refers to Leena", "them refers to the two jars"], ["marker is between the jars", "jars are beside the tray", "Leena is in front of the shelf"]]),
        ],
        crunch_bar=CRUNCH_BAR["pronouns_and_positions"],
        misconception="The learner links pronouns to the nearest noun without checking number or action, or guesses object positions from imagination instead of the printed relation.",
        remediation="Match each pronoun to a noun and decide whether it means one or more, then rewrite each location as object-preposition-reference while checking every relation against the scene card.",
    ),
    _make_level(
        level_id="water_play_words",
        title="Use movement and conflict words in context",
        focus="infer vocabulary meaning and transfer words to fresh situations",
        outcome="Explain a target movement, feeling, or cooperation word from context clues and use it accurately in a new complete sentence.",
        skill_ids=["reading.word_meaning_context", "vocab.chapter_word_usage"],
        choice_skill_ids=["reading.word_meaning_context"],
        episode_kind="meaning_encounter",
        source_anchor_ids=[f"{CHAPTER_ID}:read:56-58", f"{CHAPTER_ID}:think:58-59"],
        principle="Definition, contrast, and result clues set a word's meaning; transfer succeeds only when the fresh sentence preserves that meaning.",
        connect={"teaching_block": "A water-play story can reveal movement words through direction and speed, and conflict words through what changes before and after a response.", "passage": "The cork drifted, moving slowly with the water instead of following a steered path.", "prompt": "Use the slow uncontrolled movement clue to define drifted before changing the setting."},
        choice_prompt="Which meaning is supported by the context clue?",
        response_prompt="define the target word from context and use it accurately in a fresh sentence.",
        rubric_descriptions=["Defines the word using the supplied movement, contrast, or result clue.", "Uses the target word in a fresh complete sentence with the same meaning."],
        examples=[
            _q("The raft tilted, leaning to one side without fully turning over.", "leaned away from a level position", ["moved straight upward", "became perfectly balanced", "stopped existing"]),
            _q("Mina protested, clearly objecting when someone used her model without permission.", "objected or spoke against an action", ["agreed silently", "forgot the event", "celebrated the damage"]),
            _r("The leaf raft drifted, moving slowly wherever the gentle current carried it.", "Drifted means moved slowly without being steered. New sentence: A loose balloon drifted across the quiet hall.", [["moved slowly", "without being steered"], ["balloon drifted", "across hall"]]),
            _r("Jai nudged the boat, giving it one small gentle push away from the wall.", "Nudged means pushed gently a short distance. New sentence: I nudged the box closer with one finger.", [["small gentle push", "short distance"], ["nudged the box", "closer"]]),
            _r("The model remained steady, staying level even when small waves reached it.", "Steady means stable and not shaking or tipping. New sentence: The steady stool did not wobble on the floor.", [["stable", "not tipping"], ["steady stool", "did not wobble"]]),
            _r("Sia hesitated, pausing because she was unsure whether the glue had dried.", "Hesitated means paused because of uncertainty. New sentence: Arun hesitated before stepping onto the wet path.", [["paused", "uncertainty"], ["hesitated before", "wet path"]]),
            _r("The partners cooperated, sharing the tray and helping with each other's tests.", "Cooperated means worked together toward a shared result. New sentence: The neighbours cooperated to move the heavy table.", [["worked together", "shared result"], ["neighbours cooperated", "move table"]]),
            _r("The spilled water spread, covering a wider part of the floor over time.", "Spread means moved or extended over a larger area. New sentence: The blue paint spread across the damp paper.", [["extended over larger area", "wider floor"], ["paint spread", "across paper"]]),
            _r("Ravi acknowledged the mistake, openly accepting that he had moved the model without asking.", "Acknowledged means admitted or accepted that something was true. New sentence: Meera acknowledged that the first count was wrong.", [["admitted or accepted", "moved without asking"], ["acknowledged", "count was wrong"]]),
            _q("The current carried the cork along the channel without anyone pushing it.", "moving water that carries an object", ["a fixed wall", "a dry paper edge", "a kind of paint"]),
            _r("The child adjusted the fin, making a small change so the raft would travel straighter.", "Adjusted means changed slightly to improve fit or performance. New sentence: I adjusted the strap so the bag sat comfortably.", [["changed slightly", "improve travel"], ["adjusted the strap", "sat comfortably"]]),
            _q("The child handled the wet model gently, using soft careful movements.", "with soft and careful movement", ["with sudden force", "without touching it", "with loud speech only"]),
            _r("The two lanes were parallel, running beside each other without crossing.", "Parallel means side by side in the same direction without meeting. New sentence: Two parallel chalk lines marked the running lane.", [["side by side", "without crossing"], ["parallel chalk lines", "running lane"]]),
            _r("After the apology, the disagreement was resolved, meaning the problem was settled and both pupils accepted the plan.", "Resolved means settled so the conflict no longer continued. New sentence: A timer resolved the argument about whose turn came next.", [["problem settled", "conflict ended"], ["timer resolved", "turn argument"]]),
        ],
        crunch_bar=CRUNCH_BAR["water_play_words"],
        misconception="The learner chooses a water-related word without using the direction or result clue, or reuses the original sentence with only a changed name instead of transferring the meaning.",
        remediation="Find the defining movement or change, write a short synonym, then test a genuinely new sentence by replacing the target word with that synonym.",
    ),
    _make_level(
        level_id="text_scene_short_answers",
        title="Arrange scene facts and answer precisely",
        focus="order sentence parts and construct short scene responses supported by the card",
        outcome="Arrange a subject, action, object, place, and time naturally and answer a text-only scene question in one or two complete relevant sentences.",
        skill_ids=["grammar.sentence_order", "writing.short_answer"],
        choice_skill_ids=["grammar.sentence_order"],
        episode_kind="expression_workshop",
        source_anchor_ids=[f"{CHAPTER_ID}:write:64-65"],
        principle="Text cards supply every scene fact needed; natural sentence order makes the doer and action clear, while a short answer selects only details that answer the question.",
        connect={"teaching_block": "A learner does not need an unseen picture to describe a scene. A bounded card can name people, actions, objects, and positions explicitly.", "passage": "Scene card: two children test rafts at a table; a towel lies under the tray; both children smile after the rafts reach the marker.", "prompt": "Identify doers, action, place, support object, and result before constructing a focused response."},
        choice_prompt="Which sentence order is natural and complete?",
        response_prompt="arrange the supplied facts and answer the scene question in one or two precise sentences.",
        rubric_descriptions=["Uses a natural subject-action-object-place-time order with all required parts.", "Answers the stated scene question concisely using only relevant supplied facts."],
        examples=[
            _q("Parts: beside the tray / Mina / placed / a dry cloth.", "Mina placed a dry cloth beside the tray.", ["Beside placed Mina the dry tray.", "A cloth Mina beside placed.", "Placed beside tray dry Mina."]),
            _q("Parts: after the test / the children / returned / the droppers / to the box.", "After the test, the children returned the droppers to the box.", ["The droppers children after returned box.", "Returned after box the children.", "To the children the test returned."]),
            _r("Scene facts: Ravi holds a blue sail; Sia points to a loose corner; both stand beside the repair mat. Question: What problem are they addressing?", "Ravi and Sia are addressing the loose corner on the blue sail beside the repair mat.", [["Ravi and Sia addressing", "loose corner"], ["blue sail", "beside repair mat"]], interaction_type="short_text"),
            _r("Parts: carefully / Noor / moved / the wet model / onto a towel. Question: How did Noor protect the table?", "Noor carefully moved the wet model onto a towel. She protected the table by keeping the wet model on the absorbent surface.", [["Noor carefully moved", "wet model onto towel"], ["protected table", "absorbent surface"]], interaction_type="short_text"),
            _r("Scene facts: one raft follows lane A; another follows lane B; a string separates the lanes. Question: Why do they not collide?", "The rafts do not collide because each follows a separate lane and the string marks the boundary between them.", [["separate lanes", "one follows A and other B"], ["string boundary", "do not collide"]], interaction_type="short_text"),
            _r("Parts: before lunch / the group / tested / three cork shapes / in the water tray. Question: What was tested?", "Before lunch, the group tested three cork shapes in the water tray. They tested how the three shapes moved on water.", [["group tested three cork shapes", "before lunch"], ["how shapes moved", "on water"]], interaction_type="short_text"),
            _r("Scene facts: a spill is beside the table; Jai warns the group; Leena brings a cloth. Question: How does the group respond?", "Jai warns the group, and Leena brings a cloth to clean the spill beside the table.", [["Jai warns", "Leena brings cloth"], ["clean spill", "beside table"]], interaction_type="short_text"),
            _r("Parts: near the window / a gentle fan / moved / the paper sail / slowly. Question: What caused the movement?", "A gentle fan near the window moved the paper sail slowly. The fan's airflow caused the sail to move.", [["gentle fan moved sail", "near window"], ["airflow caused movement", "sail move"]], interaction_type="short_text"),
            _r("Scene facts: Om's model leans left; one weight is missing on the right; a spare weight lies in the box. Question: What repair is supported?", "Om should add the spare weight to the right side because the missing weight has made the model lean left.", [["add spare weight", "right side"], ["missing weight", "leans left"]], interaction_type="short_text"),
            _q("Parts: the marker / reached / at noon / the first raft.", "The first raft reached the marker at noon.", ["The marker first raft reached noon.", "At reached the raft marker.", "Noon the first reached marker."]),
            _r("Parts: after cleaning / Pia / stored / the tray / under the shelf. Question: Where is it now?", "After cleaning, Pia stored the tray under the shelf. The tray is now under the shelf.", [["Pia stored the tray", "after cleaning"], ["under the shelf", "tray now"]], interaction_type="short_text"),
            _q("Parts: with a pencil / Tara / marked / two parallel lanes / on the card.", "Tara marked two parallel lanes on the card with a pencil.", ["Two Tara pencil marked lanes.", "On marked the parallel card Tara.", "A pencil lanes Tara with marked."]),
            _r("Scene facts: two pupils share one dropper; a timer shows one minute each; both tests finish. Question: What made the sharing fair?", "The one-minute timer made sharing fair because each pupil received an equal turn with the dropper.", [["one-minute timer", "made fair"], ["equal turn", "each pupil"]], interaction_type="short_text"),
            _r("Parts: quietly / the class / watched / the final raft / from behind the line. Question: How and where did they watch?", "The class quietly watched the final raft from behind the line. They watched without noise and stayed behind the marked boundary.", [["class quietly watched", "final raft"], ["behind the line", "without noise"]], interaction_type="short_text"),
        ],
        crunch_bar=CRUNCH_BAR["text_scene_short_answers"],
        misconception="The learner guesses details from an imagined picture, starts with loose place phrases that hide the subject, or writes several scene facts without selecting the one that answers the question.",
        remediation="Find who, action, place, and time, build the sentence around who and action, then use only facts that directly answer the question in at most two sentences.",
    ),
]


ASSESSMENT_PAIRS = [
    _aq_pair("reading.event_sequence", "Which conflict-repair event came last?", ("A model was splashed, its owner set a boundary, the other child apologised, and both repaired it.", "Both children repaired the model.", ["The model was splashed.", "A boundary was stated.", "The other child apologised."]), ("A lane leaked, a missing block was found, the block was returned, and the route was tested again.", "The route was tested again.", ["The lane leaked.", "A block was found.", "The block was returned."])),
    _ar_pair("reading.paragraph_main_idea", "State the main idea in one sentence.", "Connects the conflict, respectful response, and cooperative result.", ("A child moved another raft without asking. After a clear request, he returned it and helped repair the sail.", "The child respected the owner's request, returned the raft, and helped repair it, turning the conflict into cooperation.", [["respected the owner's request", "honoured the owner's request"], ["returned the raft", "gave back the raft"], ["helped repair it", "helped fix it"], ["conflict into cooperation", "quarrel ended"]]), ("Two models collided in one lane. The pupils marked separate routes and completed both tests fairly.", "Creating separate routes solved the collision problem and gave both pupils fair testing space.", ["separate routes", "solved collision", "fair space"]), interaction_type="summary"),
    _ar_pair("reading.inference_reason", "State the supported feeling or motive and cite its clue.", "Infers a plausible concern or goal grounded in the visible action or statement.", ("Rina pulls her model closer after someone changes its sail without permission.", "Rina likely wants control over her own model because she pulls it closer after an unasked change.", ["wants control", "pulls it closer", "without permission"]), ("A partner suggests two lanes after repeated collisions in one channel.", "The partner wants each model to have a clear route because the shared channel causes repeated collisions.", ["clear route", "repeated collisions"])),
    _ar_pair("writing.reason_answer", "Recommend a respectful action and justify it from the card.", "States a practical response and a reason tied to boundary, fairness, ownership, or safety.", ("Leena keeps moving Omar's measuring cup after he says it holds his test water; an empty cup is available.", "Leave Omar's test cup in place and use the empty cup because his spoken request protects his own measured water.", ["leave Omar's test cup", "use the empty cup", "spoken request protects his measured water"]), ("Two learners need one dropper for one minute each; a timer is ready.", "Use one timed minute each because equal turns let both learners complete their tests.", ["timed minute each", "equal turns", "both tests"])),
    _aq_pair("reading.dialogue_attribution", "Who makes the named contribution?", ("'My notes are wet,' Tara said. 'I will help rewrite them,' Om replied.", "Om offers repair help.", ["Tara offers the help.", "The notes reply.", "Om denies the spill."]), ("'Why is the sail turning?' Neel asked. 'The knot is loose,' Tara replied.", "Tara identifies the cause.", ["Neel gives the answer.", "The sail asks the question.", "Tara asks why."])),
    _ar_pair("grammar.punctuation_capitalization", "Rewrite the exchange with correct capitals and punctuation.", "Uses capitals, quotation marks, reporting punctuation, and suitable end marks.", ("draft: is the spare sail dry asked imran. yes it is ready answered leela", "'Is the spare sail dry?' asked Imran. 'Yes, it is ready,' answered Leela.", ["Is capital", "question mark", "Imran and Leela capitals", "quotation marks"]), ("draft: stop moving my raft said mira. i will leave it replied dev", "'Stop moving my raft,' said Mira. 'I will leave it,' replied Dev.", ["Mira and Dev capitals", "quotation marks", "commas"]), interaction_type="dialogue", min_words=10),
    _aq_pair("grammar.pronouns", "What does the pronoun refer to?", ("Meena passed a towel to Arif. He dried the tray with it.", "He means Arif, and it means the towel.", ["He means Meena and it means the tray.", "Both mean the tray.", "He means the towel."]), ("Ravi placed two cups on the tray and carried them to the sink.", "them means the two cups", ["them means the tray", "them means Ravi", "them means the sink"])),
    _ar_pair("grammar.prepositions", "State all object locations from the text card.", "Uses every supplied position preposition with the correct object and reference.", ("A cork is in a bowl; the bowl is beside a towel; a cup is above the cork.", "The cork is in the bowl and below the cup, while the bowl is beside the towel.", ["cork in bowl", "below cup", "bowl beside towel"]), ("A tray is on a bench; two shoes are under the bench; a bag is beside it.", "The tray is on the bench, the shoes are under it, and the bag is beside the bench.", ["tray on bench", "shoes under", "bag beside"])),
    _aq_pair("reading.word_meaning_context", "What does the target word mean here?", ("The raft drifted, moving slowly without being steered.", "moved slowly without steering", ["rose straight upward", "stayed fixed", "was pulled quickly by hand"]), ("Asha hesitated, pausing before she poured water onto the model.", "paused because she was unsure", ["hurried without thinking", "finished the model at once", "spilled all the water"])),
    _ar_pair("vocab.chapter_word_usage", "Define the word and use it in a fresh sentence.", "Defines the word from context and transfers it accurately to a new complete sentence.", ("Nudged means pushed gently a short distance.", "Nudged means gave a small gentle push. I nudged the box closer with one finger.", ["small gentle push", "nudged the box"]), ("Resolved means settled so a conflict no longer continues.", "Resolved means settled. A timer resolved the argument about whose turn came next.", ["settled", "timer resolved", "turn argument"])),
    _aq_pair("grammar.sentence_order", "Which sentence uses the supplied parts naturally?", ("Parts: near the repair box / Sana / arranged / three dry sails.", "Sana arranged three dry sails near the repair box.", ["Near arranged Sana the dry repair.", "Three sails Sana box arranged.", "Arranged near repair three Sana."]), ("Parts: beside the window / Mira / dried / two paper sails / after lunch.", "After lunch, Mira dried two paper sails beside the window.", ["Beside dried Mira the paper lunch.", "Two sails Mira window after dried.", "Dried beside lunch two Mira sails."])),
    _ar_pair("writing.short_answer", "Answer the text-only scene question in one or two complete sentences.", "Selects the relevant visible facts and answers the exact question concisely.", ("Two rafts use separate lanes marked by string. Why do they not collide?", "They do not collide because each raft follows a separate lane and the string marks the boundary.", ["separate lane", "string boundary", "do not collide"]), ("A timer gives each pupil one minute with the dropper. What makes the sharing fair?", "The timer makes sharing fair because each pupil receives an equal one-minute turn.", ["timer", "equal one-minute turn", "fair"]), interaction_type="short_text"),
    _ar_pair("reading.paragraph_main_idea", "Summarise the whole response and result.", "Captures the problem, responsible action, and improved outcome.", ("A spill reached the floor. A pupil warned others, dried it, and moved tools closer before restarting.", "Responsible clean-up and a better tool position reduced the risk of another spill.", ["responsible clean-up", "tool position", "reduced risk"]), ("A copied design caused conflict. A dated card proved its source, credit was restored, and both pupils revised it together.", "Restoring honest credit allowed the pupils to turn a copied design into a joint revision.", ["restoring credit", "joint revision"]), interaction_type="summary"),
    _ar_pair("writing.short_answer", "Use the supplied scene facts to give a precise supported response.", "Answers the prompt with the relevant action and clue in one or two complete sentences.", ("A paper bridge sags because its middle support has slipped; an extra block is nearby. What repair is supported?", "Place the extra block under the middle because the slipped support has made the bridge sag.", ["extra block under the middle", "slipped support", "bridge sag"]), ("A wet model is beside a dry towel. How can the table be protected?", "Move the wet model onto the towel so the absorbent surface protects the table.", ["move onto towel", "absorbent surface", "protect table"]), interaction_type="short_text"),
]


LAUNCH_DEPTH_CASES = {
    "raft_conflict_sequence": [
        _launch_depth_case(
            "Two pairs launched paper boats in one rain channel. Asha's pair blocked the stream with stones, Dev asked them to clear one gap, and both pairs then timed boats through the open channel.",
            "Order the rain-channel play, blockage, boundary request, and shared result, then state the cooperation message.",
            "The pairs launched boats, stones blocked the stream, Dev asked for a gap, and both pairs timed boats afterward. The message is that a clear request and one shared channel let everyone continue the test.",
            "the pairs launched boats, stones blocked the stream, Dev asked for a gap, and both pairs timed boats afterward",
            "a clear request and one shared channel let everyone continue the test",
            ordered=True,
        ),
        _launch_depth_case(
            "At a tub station, Nila used every cork for her raft. Omar said he needed two corks for a bridge, Nila returned them, and they joined the raft and bridge into one floating course.",
            "Retell the cork conflict and helpful response, then give the whole idea about the floating course.",
            "Nila took the corks, Omar stated his need, Nila returned two, and they built one course. The main idea is that naming a need and sharing materials turned a conflict into joint play.",
            "Nila took the corks, Omar stated his need, Nila returned two, and they built one course",
            "naming a need and sharing materials turned a conflict into joint play",
            ordered=True,
        ),
        _launch_depth_case(
            "Ravi splashed near Meera's labelled water sample. Meera asked him to keep splashing behind the blue line, Ravi apologised, and he helped replace the wet label before both experiments continued.",
            "Sequence Ravi and Meera's water-sample conflict and state the cooperation lesson.",
            "Ravi splashed the sample, Meera set a boundary, Ravi apologised, and they replaced the label. The lesson is that respecting a clear boundary and repairing harm helps both activities continue.",
            "Ravi splashed the sample, Meera set a boundary, Ravi apologised, and they replaced the label",
            "respecting a clear boundary and repairing harm helps both activities continue",
            ordered=True,
        ),
    ],
    "boundary_inference_and_reason": [
        _launch_depth_case(
            "Kiran reaches for Rupa's watering can after she says it holds a measured amount for her seed test. Rupa pulls it closer and points to an empty can nearby.",
            "What feeling or motive does Rupa's action suggest, and what fair response protects the seed test?",
            "Rupa likely wants to protect her measured water. Kiran should use the empty can and ask before borrowing because changing the amount could spoil her seed test.",
            "Rupa likely wants to protect her measured water",
            "use the empty can and ask before borrowing",
        ),
        _launch_depth_case(
            "Aman writes his name under a model boat and asks friends not to repaint it before judging. Leela has a bright sticker but pauses when she reads the name.",
            "Why does Aman set the no-repainting boundary, and what should Leela do with the sticker?",
            "Aman wants his judged design to remain unchanged. Leela should ask permission or use the sticker on her own model because the named boat belongs to Aman's project.",
            "Aman wants his judged design to remain unchanged",
            "ask permission or use the sticker on her own model",
        ),
        _launch_depth_case(
            "The splash corner has a yellow line around it. Isha steps back when a younger child enters without boots and points to the dry waiting mat.",
            "What safety motive can be worked out from Isha's actions, and what fair next step fits the yellow line?",
            "Isha wants to keep the younger child away from a slippery wet area. The child should wait on the dry mat for boots because the yellow line marks the splash boundary.",
            "Isha wants to keep the younger child away from a slippery wet area",
            "wait on the dry mat for boots",
        ),
    ],
    "speakers_and_dialogue_marks": [
        _launch_depth_case(
            "Pia says the blue raft is hers and asks Veer to stop pulling its sail. Veer says he thought it was shared and offers to tie the sail back.",
            "Identify Pia's boundary and Veer's repair, then punctuate both blue-raft lines.",
            "Pia said, 'The blue raft is mine, so please stop pulling its sail.' Veer replied, 'I thought it was shared, and I will tie the sail back.' Veer's reply explains and repairs the problem.",
            "Pia said, 'The blue raft is mine, so please stop pulling its sail.' Veer replied, 'I thought it was shared, and I will tie the sail back.'",
            "Veer's reply explains and repairs the problem",
            interaction_type="dialogue",
            min_words=18,
        ),
        _launch_depth_case(
            "Sonal tells Kabir not to pour water over her chalk route. Kabir apologises and offers to move his bucket beside the drain.",
            "Write Sonal and Kabir's chalk-route exchange with clear speaker tags and punctuation.",
            "Sonal said, 'Please do not pour water over my chalk route.' Kabir replied, 'I am sorry, and I will move my bucket beside the drain.' Kabir respects the boundary with a new plan.",
            "Sonal said, 'Please do not pour water over my chalk route.' Kabir replied, 'I am sorry, and I will move my bucket beside the drain.'",
            "Kabir respects the boundary with a new plan",
            interaction_type="dialogue",
            min_words=17,
        ),
        _launch_depth_case(
            "At the pond model, Tariq says the gate must stay closed during his test. Esha asks why, and Tariq explains that an open gate would release all the stored water.",
            "Name Tariq and Esha as the speakers, then punctuate the pond-model question and reason.",
            "Tariq said, 'The gate must stay closed during my test.' Esha asked, 'Why must it stay closed?' Tariq replied, 'An open gate would release all the stored water.' The explanation supports his boundary.",
            "Esha asked, 'Why must it stay closed?' Tariq replied, 'An open gate would release all the stored water.'",
            "the explanation supports his boundary",
            interaction_type="dialogue",
            min_words=18,
        ),
    ],
    "pronouns_and_positions": [
        _launch_depth_case(
            "Nina places the red cup on the tray and the blue cup under the shelf. She asks Mohan to move it beside the jug, meaning the red cup.",
            "Who does she name, what does it refer to, and where should the red cup be moved?",
            "She refers to Nina, and it refers to the red cup. Mohan should move the red cup beside the jug.",
            "she refers to Nina, and it refers to the red cup",
            "move the red cup beside the jug",
        ),
        _launch_depth_case(
            "Arif and Bela leave two boats between the bucket and the drain. They put the paddles behind them, where them means the two boats.",
            "Identify they and them in the boat card, then state the boats' and paddles' positions.",
            "They means Arif and Bela, and them means the two boats. The boats are between the bucket and drain, and the paddles are behind the boats.",
            "they means Arif and Bela, and them means the two boats",
            "the boats are between the bucket and drain, and the paddles are behind the boats",
        ),
        _launch_depth_case(
            "The sponge is in the bowl, and the cork rests on the lid beside it. Here, it means the bowl, not the cork.",
            "What does it mean in the sponge-and-cork card, and where are the sponge, cork, and lid?",
            "It refers to the bowl. The sponge is in the bowl, the cork is on the lid, and the lid is beside the bowl.",
            "it refers to the bowl",
            "the sponge is in the bowl, the cork is on the lid, and the lid is beside the bowl",
        ),
    ],
    "water_play_words": [
        _launch_depth_case(
            "The leaf boat drifted across the tub, moving slowly with the current without anyone pushing it.",
            "Define drifted from the leaf-boat movement and use drifted in a fresh complete sentence.",
            "Drifted means moved slowly with air or water. New sentence: A feather drifted across the courtyard in the breeze.",
            "drifted means moved slowly with air or water",
            "a feather drifted across the courtyard",
        ),
        _launch_depth_case(
            "After both teams asked for the funnel, Jaya yielded her turn and let the younger team use it first. The card says she gave way willingly.",
            "What does yielded mean in the funnel card, and how can yielded be used in a new situation?",
            "Yielded means gave way or allowed another turn. New sentence: Omar yielded his seat to a passenger carrying a baby.",
            "yielded means gave way or allowed another turn",
            "Omar yielded his seat to a passenger carrying a baby",
        ),
        _launch_depth_case(
            "The paper sail tore at one corner, so Aditi mended it with a small tape patch until the two edges held together again.",
            "Use the sail and tape clues to explain mended, then use mended in another complete sentence.",
            "Mended means repaired something damaged. New sentence: Grandfather mended the loose strap on my schoolbag.",
            "mended means repaired something damaged",
            "grandfather mended the loose strap on my schoolbag",
        ),
    ],
    "text_scene_short_answers": [
        _launch_depth_case(
            "At four o'clock, Mira placed the folded blue sail inside the model-boat box on the art shelf. She did this before the room was cleaned.",
            "Arrange Mira, placed, sail, box, shelf, and four o'clock naturally, then answer where the sail ended.",
            "At four o'clock, Mira placed the folded blue sail inside the model-boat box on the art shelf. The sail ended inside the box on the shelf.",
            "at four o'clock, Mira placed the folded blue sail inside the model-boat box on the art shelf",
            "the sail ended inside the box on the shelf",
            ordered=True,
        ),
        _launch_depth_case(
            "Before lunch, the caretaker carried a full bucket from the tap to the garden tub. The children kept the path clear for him.",
            "Form a natural sentence with caretaker, carried, bucket, tap, garden tub, and before lunch, then answer why the path stayed clear.",
            "Before lunch, the caretaker carried a full bucket from the tap to the garden tub. The path stayed clear so he could carry the water safely.",
            "before lunch, the caretaker carried a full bucket from the tap to the garden tub",
            "the path stayed clear so he could carry the water safely",
            ordered=True,
        ),
        _launch_depth_case(
            "After the final test, Nikhil stored three dry corks in a labelled pouch beside the science tray. The wet cork remained on a cloth.",
            "Order Nikhil, stored, corks, pouch, science tray, and after the final test, then answer which cork was not stored.",
            "After the final test, Nikhil stored three dry corks in a labelled pouch beside the science tray. The wet cork was not stored because it remained on the cloth.",
            "after the final test, Nikhil stored three dry corks in a labelled pouch beside the science tray",
            "the wet cork was not stored because it remained on the cloth",
            ordered=True,
        ),
    ],
}

_add_launch_depth_variants(LEVELS, LAUNCH_DEPTH_CASES)


_SEMANTIC_OPTION_REPLACEMENTS = {'The child wants stronger random gusts.': 'The child wants to test the models with a '
                                           'stronger breeze.'}
_SEMANTIC_ASSESSMENT_OVERRIDES = {'eng_c3_ch06:assessment:03': {'model_answer': 'Asha wants to identify her own boat, '
                                               'so she writes her name after the boats '
                                               'were mixed together.',
                               'passage': 'Asha writes her name on a paper boat after '
                                          'another group mixes all the boats together.',
                               'prompt': 'State the supported feeling or motive and '
                                         'cite its clue.',
                               'relevance_terms': ['identify her own boat',
                                                   'writes her name',
                                                   'boats were mixed'],
                               'slot_aliases': [['identify her own boat'],
                                                ['writes her name'],
                                                ['boats were mixed']]},
 'eng_c3_ch06:assessment:05': {'accepted_answers': ['Kabir offers to press the fold '
                                                    'flat.'],
                               'options': ['Nila offers to fetch a ruler.',
                                           'Kabir offers to press the fold flat.',
                                           'Nila says the boat is finished.',
                                           'Kabir asks Nila to open the fold.'],
                               'passage': "'The fold has opened,' Nila said. 'I will "
                                          "press it flat with the ruler,' Kabir "
                                          'replied.',
                               'prompt': 'Who offers a repair, and what will that '
                                         'person do?'},
 'eng_c3_ch06:assessment:18': {'model_answer': 'Iqbal should use a clean board and '
                                               'leave the wide tray for the drying '
                                               'boat because two boards are free.',
                               'passage': "Neha's painted boat must dry on the only "
                                          'wide tray. Iqbal needs a flat surface for '
                                          'folding, and two clean boards are free.',
                               'prompt': 'Recommend a respectful plan and support it '
                                         'with the drying need and the free boards.',
                               'relevance_terms': ['Iqbal should use a clean board',
                                                   'leave the wide tray for the drying '
                                                   'boat',
                                                   'two boards are free'],
                               'slot_aliases': [['Iqbal should use a clean board'],
                                                ['leave the wide tray for the drying '
                                                 'boat'],
                                                ['two boards are free']]},
 'eng_c3_ch06:assessment:20': {'model_answer': "'May I borrow your blue paper?' asked "
                                               "Ria. 'Yes, take one sheet,' replied "
                                               'Aman. Key ideas: Ria and Aman '
                                               'capitals; quotation marks around both '
                                               'lines; commas before reporting words.',
                               'passage': 'draft: may i borrow your blue paper asked '
                                          'ria. yes take one sheet replied aman',
                               'prompt': 'Rewrite the exchange with correct capitals '
                                         'and punctuation.',
                               'relevance_terms': ['Ria and Aman capitals',
                                                   'quotation marks around both lines',
                                                   'commas before reporting words'],
                               'slot_aliases': [['Ria and Aman capitals'],
                                                ['quotation marks around both lines'],
                                                ['commas before reporting words']]}}


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
    chapter_no=6,
    title="Paper Boats",
    unit_title="Toys and Games",
    source_url=SOURCE_URL,
    page_extract="/tmp/zidd-ncert-class2-3/eng_c3_ch06.txt",
    source_anchors=SOURCE_ANCHORS,
    levels=LEVELS,
    assessment_pairs=ASSESSMENT_PAIRS,
)

_apply_semantic_copy_corrections(MANIFEST["levels"])
_apply_semantic_copy_corrections(
    MANIFEST["chapter_assessment"]["items"]
)
_apply_semantic_assessment_overrides(MANIFEST)
