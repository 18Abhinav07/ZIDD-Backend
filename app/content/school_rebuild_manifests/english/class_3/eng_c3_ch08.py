"""Deep authored manifest for Class 3 English Chapter 8.

The official extract informed only the story and exercise sequence. Runtime
passages, prompts, options, and grading authority are original Zidd content.
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
    "chapter_id": "eng_c3_ch08",
    "chapter_no": 8,
    "title": "Thank God!",
    "unit_title": "Good Food",
    "source_url": "https://ncert.nic.in/textbook/pdf/cesa108.pdf",
    "source_analysis_reference": (
        "/tmp/zidd-ncert-class2-3/eng_c3_ch08.txt structure review"
    ),
    "anchors": [
        {"label": "Let us read: fruit-gift choice, palace surprise, and thankful reason", "page_start": 1, "page_end": 4, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us think A: story comprehension and reason questions", "page_start": 5, "page_end": 5, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us learn A: opposite words in context", "page_start": 6, "page_end": 6, "treatment": "zidd_equivalent", "required": True},
        {"label": "Let us learn B-C: singular and plural agreement with is and are", "page_start": 6, "page_end": 7, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us write: Chandu's Fruit Salad step order", "page_start": 9, "page_end": 9, "treatment": "taught_and_assessed", "required": True},
        {"label": "Let us listen: humorous elephant-size verse", "page_start": 8, "page_end": 8, "treatment": "guided_only", "required": False},
        {"label": "Let us speak: food for a helpful elephant visit", "page_start": 9, "page_end": 9, "treatment": "guided_only", "required": False},
        {"label": "Let us explore: picture fruit-word grid", "page_start": 10, "page_end": 10, "treatment": "textbook_companion", "required": False},
    ],
    "levels": [
        {
            "level_id": "thankful_story_sequence",
            "title": "Track the gift journey",
            "focus": "reconstruct an event sequence and state the story's central movement",
            "concept": "event sequence",
            "outcome": "Order a character's plan, journey, surprise, and response, then state a main idea that covers the whole visible mini-story.",
            "skill_ids": ["reading.event_sequence", "reading.paragraph_main_idea"],
            "episode_kind": "comprehension_studio",
            "anchor_indexes": [1],
            "principle": "An event sequence follows causes and time clues. A main idea then compresses the linked events without becoming a list of every small action.",
            "connect": _connect(
                "Story events form a chain: a plan leads to an action, the action creates a result, and the result changes what a character understands or does next.",
                "Ketan packed guavas for the town nurse. Rain blocked the short road, so he used the bridge path and arrived just before the clinic closed.",
                "Trace the plan, obstacle, changed route, and arrival before deciding what the whole episode shows.",
            ),
            "misconception": "The learner orders events by sentence length instead of story logic or selects one colourful detail as the paragraph's complete main idea.",
            "remediation": "Label each event plan, obstacle, action, or result; connect them with arrows; then write one sentence that includes the chain's beginning and outcome.",
            "ordered_response": True,
            "cases": [
                _case("orchard delivery", "Mina chose ripe oranges for the shelter. She packed them in a light crate, crossed the footbridge, and handed the crate to the cook before lunch.", "Which order and main idea match the complete episode?", "Mina selects, packs, carries, and delivers fruit to help the shelter.", "Mina eats lunch before growing an orchard.", "The footbridge is the only important idea.", "The linked actions show a planned helpful delivery from orchard to shelter.", "selects packs carries delivers", "helpful planned delivery"),
                _case("garden basket", "Omar notices tomatoes bending a plant. He fetches a basket, picks the ripe ones, and takes them to his grandmother for soup.", "What event chain drives the short story?", "Omar notices a need, collects ripe tomatoes, and brings them for soup.", "Grandmother makes soup before Omar sees any plant.", "The story is mainly about an empty basket colour.", "The need in the garden leads directly to collecting and sharing food.", "notices collects brings", "need leads to sharing"),
                _case("market choice", "Sia first planned to carry a heavy melon to her uncle. She saw the long uphill path, chose a small bag of plums instead, and reached his shop easily.", "How should the change of plan be sequenced?", "Sia plans the melon, considers the path, chooses plums, and reaches the shop.", "Sia reaches the shop before choosing any fruit.", "The uncle carries the hill to the market.", "The path difficulty explains why the lighter choice comes before arrival.", "plan path choice arrival", "difficulty changes choice"),
                _case("school harvest", "The class watered bean plants for weeks. On Friday they picked the pods, counted them, and gave equal bundles to the kitchen team.", "Which summary keeps the full progression?", "The class cares for beans, harvests them, and shares the crop with the kitchen.", "Friday is a day with no connection to beans.", "Counting is the only event that matters.", "Long-term care leads to harvest and useful sharing.", "cares harvests shares", "care leads to harvest"),
                _case("fruit stall rain", "A sudden shower soaked Ravi's fruit-stall sign. He moved the baskets under a roof, dried the sign, and reopened when the rain stopped.", "What main event sequence is supported?", "Ravi protects the stall, repairs the wet sign, and reopens after the shower.", "Ravi opens before the baskets exist.", "The story mainly explains cloud shapes.", "The rain causes protective actions followed by reopening.", "protects dries reopens", "rain causes action"),
                _case("picnic packet", "Neha checks the picnic list, washes pears, packs them with napkins, and places the packet near the door for morning.", "Which ordered idea covers all four actions?", "Neha follows a list to prepare and stage the fruit packet for the picnic.", "Neha returns from the picnic before packing.", "Napkins grow on pear trees.", "Checking guides preparation, packing, and readiness for the next morning.", "checks washes packs places", "guided picnic preparation"),
                _case("seed exchange", "Kabir dries pumpkin seeds, labels two envelopes, walks to the garden club, and swaps one envelope for spinach seeds.", "What sequence and central purpose fit the passage?", "Kabir prepares labelled seeds and exchanges them at the garden club.", "Kabir swaps spinach before preparing any envelope.", "The passage mainly describes pumpkin soup.", "Preparation makes the later seed exchange possible.", "dries labels walks swaps", "preparation enables exchange"),
            ],
        },
        {
            "level_id": "thankful_reasoning_turn",
            "title": "Infer the reason behind thanks",
            "focus": "infer a hidden reason and construct a because-supported answer",
            "concept": "cause and thankful inference",
            "outcome": "Use two printed clues to infer why a character feels relieved or thankful and express the reasoning in a complete because sentence.",
            "skill_ids": ["reading.inference_reason", "writing.reason_answer"],
            "episode_kind": "meaning_encounter",
            "anchor_indexes": [1, 2],
            "principle": "An inference joins a visible event with a likely thought. The reason must fit every clue and avoid inventing feelings or facts that the passage never supports.",
            "connect": _connect(
                "A character may say thanks after a surprising event. Readers look backward for the danger, difficulty, or worse possibility that the character has just avoided.",
                "A branch fell behind Jaya seconds after she stepped into the library doorway. She looked back at the empty path and whispered, 'That was close.'",
                "Use the timing and the fallen branch to infer why Jaya feels relieved.",
            ),
            "misconception": "The learner copies the word thankful as its own explanation or invents an unrelated reward instead of connecting the response to the avoided outcome.",
            "remediation": "Circle the character's response, underline the before-and-after clues, complete 'The character is thankful because...', and reject any reason not printed or implied.",
            "creative_transfer": True,
            "cases": [
                _case("soft parcel", "A courier almost placed a glass jar under a heavy sack, but Mira moved the jar to the top first. When the sack dropped, she sighed with relief.", "Why does Mira feel relieved?", "Mira is relieved because she moved the glass jar away from the falling sack.", "Mira wanted the jar to break under the sack.", "The courier gave her an unseen prize.", "Her earlier action prevented the heavy sack from crushing the jar.", "moved glass jar", "prevented crushing"),
                _case("small fruit choice", "Arun carried berries instead of a large pumpkin on a crowded bus. When the bus stopped sharply, he held the berry box safely and said, 'Good choice.'", "What reason supports Arun's response?", "Arun is thankful for choosing a small box that he could hold safely.", "Arun believes pumpkins can drive buses.", "The driver asked him to throw the berries.", "The sharp stop shows why an easier-to-hold package mattered.", "small box safely", "sharp stop mattered"),
                _case("covered seedlings", "Lata covered young plants before the cold night. In the morning, frost lay on the path but the covered leaves were unharmed.", "Why is Lata pleased with her earlier decision?", "Lata is pleased because the cover protected the seedlings from frost.", "Lata wanted frost inside every leaf.", "The plants moved indoors by themselves.", "The contrast between frosty path and safe leaves shows the protection worked.", "cover protected seedlings", "frost contrast"),
                _case("spare bottle", "Before a long walk, Zubin filled a spare water bottle. His first bottle leaked halfway, so he used the spare and thanked his sister for the reminder.", "Which inference explains the thanks?", "Zubin is thankful because the spare bottle replaced the water he lost.", "Zubin thanked her for making the first bottle leak.", "The walk ended before he needed water.", "The leak created a need that the prepared spare solved.", "spare replaced water", "leak created need"),
                _case("light umbrella", "Pari selected a folding umbrella instead of a wide sunshade for the train. It began raining as she left the station, and the umbrella opened easily in the narrow crowd.", "Why does Pari value her choice?", "Pari values the folding umbrella because it works in rain and fits the narrow crowd.", "Pari chose it because the station had no people.", "The sunshade became a train ticket.", "Rain and limited space both support the practical choice.", "umbrella works fits", "rain narrow space"),
                _case("saved receipt", "Dev kept the seed-shop receipt in his pocket. At home he found one packet missing, and the shop replaced it after checking the receipt.", "Why is Dev glad he kept the paper?", "Dev is glad because the receipt proved his purchase and helped replace the missing packet.", "Dev used the receipt to grow seeds overnight.", "The shop refused to check any proof.", "The replacement depends on the saved purchase record.", "receipt proved purchase", "enabled replacement"),
                _case("quiet path", "Asha avoided the muddy shortcut and used the paved lane with her fruit cart. The shortcut flooded minutes later, while her wheels stayed clean.", "What good result explains Asha's satisfaction?", "Asha is satisfied because the paved lane kept her cart out of the flooded mud.", "Asha wanted the fruit cart to sink.", "The paved lane became a river.", "Her route choice kept the wheels clean and moving.", "paved lane avoided mud", "route kept wheels clean"),
            ],
        },
        {
            "level_id": "thankful_opposite_context",
            "title": "Choose precise opposites",
            "focus": "derive a word meaning from context and select its true opposite",
            "concept": "opposite word in context",
            "outcome": "Explain the target word using its sentence clue and choose an opposite that reverses the same property rather than naming an unrelated word.",
            "skill_ids": ["reading.word_meaning_context", "vocab.antonyms"],
            "episode_kind": "language_lab",
            "anchor_indexes": [3],
            "principle": "True opposites reverse one shared property: heavy and light compare weight, while long and short compare length. Context identifies which property matters.",
            "connect": _connect(
                "Two words are not opposites merely because they differ. A reader names the property in the sentence, places both words on that scale, and checks that they point in reverse directions.",
                "The full grain sack needed two people to lift it, but the empty cloth bag could be raised with one finger.",
                "Use the lifting clues to place heavy and light at opposite ends of the weight scale.",
            ),
            "misconception": "The learner selects a related noun or a different adjective instead of reversing the same property shown by the context.",
            "remediation": "Name the comparison property, quote the clue for the target word, state the reverse end of that property, and test the opposite in the sentence.",
            "cases": [
                _case("weight baskets", "The melon basket needs two carriers because it is heavy; the empty reed basket is easy for one child to lift.", "Which opposite pair is proved by the lifting clues?", "Heavy is opposite to light in this context.", "Heavy is opposite to basket.", "Heavy is opposite to green.", "Both words describe reverse ends of the weight property.", "heavy opposite light", "weight property"),
                _case("path length", "The river route takes an hour and is long. The bridge route takes ten minutes and is short.", "What true opposite reverses long on the same scale?", "Long is opposite to short here.", "Long is opposite to river.", "Long is opposite to quickness only.", "The travel clues compare route length using reverse terms.", "long opposite short", "route length scale"),
                _case("fabric touch", "The cotton scarf feels soft against the skin, while the dry jute rope feels rough.", "Which antonym is supported by touch?", "Soft is opposite to rough in the passage.", "Soft is opposite to scarf.", "Soft is opposite to brown.", "The two adjectives reverse the texture property.", "soft opposite rough", "texture property"),
                _case("movement speed", "The snail crosses the leaf slowly, but the squirrel reaches the branch quickly.", "Which words form the speed contrast?", "Slow is opposite to fast or quick here.", "Slow is opposite to leaf.", "Slow is opposite to branch colour.", "The time taken by each animal establishes reverse movement speed.", "slow opposite fast", "movement speed contrast"),
                _case("box fullness", "One lunch box is full to the lid. The second box has nothing inside and is empty.", "Which opposite reverses full accurately?", "Full is opposite to empty.", "Full is opposite to lunch.", "Full is opposite to square.", "The amount inside the boxes changes from maximum to none.", "full opposite empty", "amount inside"),
                _case("door position", "The shop door stands open during the fair, but the store-room door is shut and cannot be entered.", "What context-matched antonym belongs with open?", "Open is opposite to closed or shut.", "Open is opposite to shopkeeper.", "Open is opposite to wooden.", "Entry is possible in one case and blocked in the other.", "open opposite closed", "entry possible blocked"),
                _case("fruit freshness", "The crisp guavas were picked this morning and are fresh. The forgotten berries smell bad and are stale.", "Which reverse quality is shown?", "Fresh is opposite to stale in this food context.", "Fresh is opposite to guava.", "Fresh is opposite to purple.", "Recent crisp food contrasts with old spoiled food.", "fresh opposite stale", "recent versus old"),
            ],
        },
        {
            "level_id": "thankful_agreement",
            "title": "Match subjects with is or are",
            "focus": "apply subject-verb agreement and construct a complete sentence",
            "concept": "subject-verb agreement",
            "outcome": "Locate the sentence subject, decide whether it is one or more than one, and use is or are in a complete context-matched sentence.",
            "skill_ids": ["grammar.subject_verb_agreement", "writing.complete_sentence"],
            "episode_kind": "language_lab",
            "anchor_indexes": [4],
            "principle": "A singular subject takes is and a plural subject takes are. Nearby plural nouns do not control the verb when they are not the sentence subject.",
            "connect": _connect(
                "Agreement begins by finding who or what the sentence is about. Count that subject, then choose the verb; do not simply copy the noun closest to the blank.",
                "The basket of red apples is beside the gate. The apples are ready for the stall.",
                "Compare the singular subject basket with the plural subject apples before choosing each verb.",
            ),
            "misconception": "The learner chooses are whenever any plural noun appears nearby or writes only is or are without completing the sentence meaning.",
            "remediation": "Underline the full subject, circle its head noun, mark one or many, choose is or are, and read the complete sentence aloud silently for sense.",
            "cases": [
                _case("mango crate", "The wooden crate of mangoes __ beside the cart. The subject is the one crate, not the many mangoes inside it.", "Which complete sentence has correct agreement?", "The wooden crate of mangoes is beside the cart.", "The wooden crate of mangoes are beside the cart.", "The wooden crate mangoes be beside.", "The singular head noun crate requires is.", "crate is beside", "singular head noun"),
                _case("market stalls", "The two fruit stalls __ open after sunrise. The subject names more than one stall.", "How should the sentence be completed?", "The two fruit stalls are open after sunrise.", "The two fruit stalls is open after sunrise.", "The fruit stalls am opening yesterday.", "The plural subject stalls requires are.", "stalls are open", "plural subject"),
                _case("bowl of grapes", "A bowl of green grapes __ on the counter. The sentence is about one bowl.", "Which verb completes the idea correctly?", "A bowl of green grapes is on the counter.", "A bowl of green grapes are on the counter.", "A bowl grapes were counter.", "One bowl controls agreement despite the nearby plural grapes.", "bowl is on counter", "one bowl controls"),
                _case("children in garden", "Three children __ watering the herb bed. The subject refers to a group of three.", "Which full sentence agrees with the subject?", "Three children are watering the herb bed.", "Three children is watering the herb bed.", "Three children am water herb.", "Children is plural and therefore pairs with are.", "children are watering", "plural children"),
                _case("guard at gate", "The guard near the baskets __ checking each visitor's pass. Only one guard is named.", "What agreement completes the sentence?", "The guard near the baskets is checking each pass.", "The guard near the baskets are checking each pass.", "The guard checking baskets are pass.", "The singular subject guard takes is.", "guard is checking", "singular guard"),
                _case("grapes in box", "The grapes in the blue box __ sweet and firm. Grapes is the plural subject.", "Which sentence is both complete and correct?", "The grapes in the blue box are sweet and firm.", "The grapes in the blue box is sweet and firm.", "The grapes blue box sweet.", "The plural subject grapes agrees with are.", "grapes are sweet", "plural agrees are"),
                _case("farmer with tools", "The farmer with two clean tools __ ready to work. The sentence names one farmer.", "How does the head noun control the blank?", "The farmer with two clean tools is ready to work.", "The farmer with two clean tools are ready to work.", "The farmer tools be ready.", "One farmer remains the subject even though tools is plural.", "farmer is ready", "one farmer subject"),
            ],
        },
        {
            "level_id": "thankful_procedure",
            "title": "Order a fruit procedure",
            "focus": "arrange a procedure and explain it in a concise response",
            "concept": "procedure sequence",
            "outcome": "Use sequence words to organise a visible no-cook food procedure, then explain why one step must come before another.",
            "skill_ids": ["grammar.sentence_order", "writing.short_answer"],
            "episode_kind": "application_mission",
            "anchor_indexes": [5],
            "principle": "In a procedure, preparation makes later actions possible. First, next, then, and finally should show the true order rather than decorate a random list.",
            "connect": _connect(
                "A procedure can be checked by asking whether each object is ready for the next action. Serving cannot happen before ingredients are combined, and a container must be ready before it is filled.",
                "The card says to wash a cup, place sliced fruit inside, add curd, stir gently, and serve.",
                "Trace how each step leads from a clean cup to a finished fruit cup.",
            ),
            "misconception": "The learner follows the printed order of loose slips without asking what must happen first, or gives a one-word answer that does not explain the order.",
            "remediation": "Name the object produced by each step, match it to the next step's need, order the chain, and justify one link with before or because.",
            "ordered_response": True,
            "creative_transfer": True,
            "cases": [
                _case("pear bowl", "The steps are: place pear pieces in a bowl, add pomegranate seeds, spoon in curd, mix gently, and serve.", "Which procedure order is logical?", "First place pear, next add seeds, then add curd, mix, and finally serve.", "First serve an empty bowl, then search for pear.", "First mix the table, then remove every ingredient.", "Ingredients must enter the bowl before mixing and serving.", "pear seeds curd mix serve", "ingredients before serving"),
                _case("orange cooler", "A drink card lists: fill a jug with cool water, add orange slices, stir in mint leaves, wait five minutes, and pour.", "How should the time-linked steps be ordered?", "First fill, next add orange, then stir in mint, wait, and finally pour.", "First pour, then fill the empty jug afterward.", "First wait without a drink, then remove the jug.", "The flavours need to be in water before waiting and pouring.", "fill add stir wait pour", "flavour before waiting"),
                _case("apple plate", "An adult supplies cut apple pieces. Mira lines a plate with leaves, arranges the apple, sprinkles cinnamon, and carries the plate to the table.", "Which response keeps the steps safe and in order?", "First use the prepared apple, next line the plate, then arrange and sprinkle, and finally carry it.", "First use a knife alone, then throw away the plate.", "First carry an empty table, then find leaves.", "Prepared fruit and a lined plate come before arranging and carrying.", "prepared line arrange carry", "safe steps in order"),
                _case("banana oats", "The visible recipe says: pour oats into a cup, add banana pieces, add milk, stir, and eat with a spoon.", "Why must pouring and adding come before stirring?", "First put oats and banana in the cup, then add milk and stir before eating.", "Stir an empty cup and eat before adding food.", "Place the spoon outside and skip every ingredient.", "Stirring combines ingredients only after they are present.", "oats banana milk stir", "ingredients present first"),
                _case("melon sticks", "Prepared melon cubes, blunt sticks, a tray, and a cover are provided. The steps are thread cubes, place sticks on tray, cover, and chill.", "What is the correct stated order?", "First thread the cubes, next tray the sticks, then cover, and finally chill.", "First chill empty sticks, then cut fruit alone.", "First cover the cubes before obtaining a tray.", "The assembled sticks are placed and covered before chilling.", "thread tray cover chill", "assembled before chilling"),
                _case("berry yoghurt", "A card directs: spoon yoghurt into a bowl, add washed berries, fold them in gently, divide into cups, and serve.", "Which sequence follows the card without adding actions?", "First spoon yoghurt, next add berries, then fold, divide, and finally serve.", "First serve empty cups, then remove yoghurt.", "First cook berries over an unseen fire.", "The mixture must be made before it can be divided and served.", "yoghurt berries fold divide", "mixture before divide"),
                _case("cucumber snack", "The no-cook steps state: place prepared cucumber rounds on a plate, add curd to each, sprinkle herbs, cover, and carry to the table.", "How should the steps be reported?", "First plate cucumber, next add curd, then sprinkle herbs, cover, and finally carry.", "First carry an empty plate, then uncover nothing.", "First chop cucumber without the prepared pieces.", "Topping and covering occur only after the cucumber is plated.", "plate curd herbs cover", "plating before topping"),
            ],
        },
        {
            "level_id": "thankful_dialogue_response",
            "title": "Follow speakers and respond kindly",
            "focus": "attribute dialogue and write a relevant friendly message",
            "concept": "dialogue response",
            "outcome": "Use speaker tags and message content to identify who said what, then write a brief friendly reply that answers the stated need.",
            "skill_ids": ["reading.dialogue_attribution", "writing.friendly_message"],
            "episode_kind": "expression_workshop",
            "anchor_indexes": [1, 2],
            "principle": "Speaker tags establish ownership of words. A friendly response names the person or need, answers it directly, and avoids promises the dialogue cannot support.",
            "connect": _connect(
                "Dialogue becomes clear when each quotation is tied to a speaker and purpose. A response should continue that exchange rather than introduce an unrelated topic.",
                "'I cannot lift this seed tray alone,' said Noor. 'I can hold the other side,' replied Tej.",
                "Match each line to its speaker and notice how Tej's reply addresses Noor's exact need.",
            ),
            "misconception": "The learner swaps the speakers because both names are nearby or writes a cheerful message that ignores the request in the printed dialogue.",
            "remediation": "Draw an arrow from each speech tag to its line, name the request in three words, and build a greeting plus one relevant offer or answer.",
            "creative_transfer": True,
            "cases": [
                _case("seed tray offer", "'The seed tray is too wide for me,' said Noor. Tej answered, 'I will carry the other side with you.'", "Who offers help, and what friendly reply could Noor write?", "Tej offers help, and Noor can thank him for sharing the load.", "Noor offers to leave Tej alone with every tray.", "The seed tray speaks to both children.", "The reply follows Tej's line and addresses the carrying need.", "Tej offers help", "thanks for carrying"),
                _case("missing label", "Ira asked, 'Did you see the label for the pear basket?' Sam replied, 'It is beside the weighing scale.'", "Who gives the location, and how can Ira respond?", "Sam gives the location, and Ira can thank him for the clear direction.", "Ira gives Sam an unrelated weather report.", "The weighing scale asks the question.", "Sam's quoted answer supplies the needed location.", "Sam gives location", "thanks for direction"),
                _case("water break", "'You have worked in the sun for an hour,' Meena told Ali. 'Please take this water bottle.' Ali smiled.", "Who makes the caring offer, and what message fits Ali?", "Meena offers water, and Ali can thank her for noticing he needs a break.", "Ali orders Meena to work without water.", "The sun hands over the bottle.", "The offer responds to Ali's long work in heat.", "Meena offers water", "thanks for caring"),
                _case("recipe question", "Pia said, 'I forgot whether mint comes before mixing.' Her aunt replied, 'Add the mint, and then mix gently.'", "Who answers the procedure question, and what reply is relevant?", "Pia's aunt answers, and Pia can thank her for clarifying the order.", "Pia answers a question about train tickets.", "Mint gives the instruction by itself.", "The aunt directly resolves Pia's uncertainty about sequence.", "aunt answers order", "thanks for clarifying"),
                _case("shared umbrella", "'The rain is getting heavier,' said Vik. Renu answered, 'Stand under my umbrella until the gate opens.'", "Whose line contains the offer, and how might Vik reply?", "Renu offers shelter, and Vik can thank her for sharing the umbrella.", "Vik offers Renu a fruit basket not mentioned.", "The gate holds the umbrella.", "Renu's instruction directly responds to the heavier rain.", "Renu offers shelter", "thanks for sharing"),
                _case("garden directions", "Aman asked, 'Which path reaches the herb garden?' Lila said, 'Follow the stone markers beyond the pump.'", "Who provides directions, and what friendly message belongs next?", "Lila provides directions, and Aman can thank her before following the markers.", "Aman tells Lila that no garden exists.", "The pump asks for a path.", "Lila's line names the route Aman requested.", "Lila provides directions", "thanks before following"),
                _case("fruit donation", "'We still need two boxes for the food drive,' said Mridul. Sana replied, 'My family can bring both boxes tomorrow.'", "Who promises the boxes, and how can Mridul acknowledge it?", "Sana promises the boxes, and Mridul can thank her family for helping the drive.", "Mridul promises to cancel the food drive.", "Tomorrow speaks for Sana's family.", "Sana's reply meets the exact need for two boxes.", "Sana promises boxes", "thanks for helping"),
            ],
        },
    ],
}


FRESH_CASES = {
    "thankful_story_sequence": [
        _fresh_case("lost scarf", "Navi finds a scarf, reads the name tag, returns it to Mira, and receives a warm thank-you note.", "Retell the events in the order they happen.", "First Navi finds the scarf, next reads the tag, then returns it, and finally gets thanks.", "The name tag must be read before the owner can receive the scarf.", "find read return thank", "tag before return"),
        _fresh_case("rain shelter", "Rain begins at dismissal. Kabir opens his umbrella for Jo, they walk to the gate, and Jo thanks him there.", "What order and main idea fit this short story?", "Kabir shares shelter before Jo thanks him at the gate.", "The walk and thanks both grow from Kabir's helpful choice.", "shares umbrella then thanks", "help links events"),
        _fresh_case("library book", "A book falls behind a shelf. Sia spots it, calls the librarian, helps lift it out, and later receives a bookmark.", "Which action begins the helpful chain?", "Sia first spots the fallen book behind the shelf.", "Finding the problem allows her to ask for help and recover the book.", "spots fallen book first", "finding starts help"),
        _fresh_case("garden seed", "Omi has no bean seeds. Lata gives him three, he plants them, and a week later he gives her a thank-you card.", "How do the gift and card connect?", "Lata gives seeds before Omi plants them and thanks her.", "The later card responds to the earlier gift.", "gives plants thanks", "card follows gift"),
        _fresh_case("heavy parcel", "A courier struggles with a parcel. Two pupils hold the door, the courier enters safely, and he thanks them.", "What is the story mostly about?", "Small acts of help make a difficult job easier.", "Holding the door solves the stated problem and leads to thanks.", "help makes work easier", "door solves problem"),
        _fresh_case("missed stop", "Tara misses her bus stop. The conductor explains the return route, Tara follows it, and she later sends praise to the depot.", "Place the route help and praise correctly.", "The conductor explains first, Tara travels next, and praise comes last.", "The praise is a response to useful directions already given.", "explain travel praise", "praise after directions"),
        _fresh_case("spilled pencils", "A pencil box opens in the hall. Dev gathers the pencils, sorts them by colour, hands them to Ria, and Ria smiles her thanks.", "Which sequence keeps every step sensible?", "Dev gathers, sorts, returns, and then receives thanks.", "Pencils must be collected before they can be sorted and returned.", "gather sort return thank", "collect before sort"),
        _fresh_case("quiet seat", "An elderly visitor enters a full room. Meena offers her chair, the visitor sits, and the teacher thanks Meena after class.", "State the main idea without listing only the chair.", "Meena shows care by giving her seat to someone who needs it.", "The visitor's need and Meena's response carry the whole story.", "Meena gives needed seat", "care answers need"),
        _fresh_case("broken strap", "Arun's bag strap breaks. Zoya lends him a cord, he ties the bag, and he returns the cord with a note.", "What happens just before the note is given?", "Arun returns the borrowed cord before giving the note.", "The note belongs at the end after the bag problem is solved.", "returns cord before note", "thanks ends story"),
        _fresh_case("canteen token", "A child drops a lunch token. The cook notices it, keeps it safe, returns it at noon, and receives a thank-you drawing.", "Which sentence gives the whole story idea?", "Keeping a lost token safe leads to a grateful response.", "The cook's care and the later drawing are the linked parts.", "safe token brings thanks", "care linked drawing"),
        _fresh_case("math card", "Pavan cannot read one number card. Esha turns it upright, Pavan finishes the sum, and he thanks her after checking.", "Why must turning the card come before finishing?", "The card must face correctly before Pavan can read it and finish.", "The first helpful action removes the reading problem.", "turn card then finish", "upright makes readable"),
        _fresh_case("water bowl", "A stray dog finds an empty bowl. Noor fills it, the dog drinks, and the watchman thanks Noor for noticing.", "What idea joins the actions?", "Noor notices a need and helps by filling the water bowl.", "The drink and thanks follow the useful action.", "notices need fills bowl", "help leads drink"),
        _fresh_case("clinic folder", "A clinic folder slips from a trolley. Naman sees the room number, gives it to the nurse, and later receives a thank-you sticker.", "Retell the clinic-folder chain and state its main idea.", "Naman finds the folder, checks the room number, returns it, and then receives thanks.", "The room clue helps him return important property responsibly.", "find check return thank", "room clue guides return"),
        _fresh_case("garden basket", "Tia plans to take spinach to her neighbour, washes the leaves, packs a basket, walks around roadwork, and delivers it before dinner.", "Which order and main idea fit the garden-basket story?", "Tia prepares, reroutes, and delivers garden food to help her neighbour.", "Every event supports a thoughtful delivery despite the blocked road.", "prepare reroute deliver", "help despite roadwork"),
        _fresh_case("bus pass", "A bus pass falls near the ticket window. Salim reads the school name, calls the office, stores the pass, and returns it when the pupil arrives.", "Put the bus-pass events in order and give the whole story idea.", "Salim reads, calls, stores, and returns the lost pass in that order.", "A printed school clue and safe storage make the return possible.", "read call store return", "school clue safe storage"),
    ],
    "thankful_reasoning_turn": [
        _fresh_case("dry paints", "Ila's paints are dry. Venu shares a water cup, and Ila can finish her poster.", "Why does Ila thank Venu?", "Ila thanks Venu because the shared water lets her finish painting.", "The water solves the exact problem named on the card.", "thanks for shared water", "water fixes dry paint"),
        _fresh_case("gate latch", "A small child cannot reach the gate latch. Rohan opens it, and the child joins the group.", "What reason supports a thankful reply?", "The child can thank Rohan for opening the high latch.", "Rohan's action removes the height problem.", "thanks for opening gate", "latch was too high"),
        _fresh_case("missing ruler", "Pia needs a ruler for one line. Aman lends his spare, so her chart is completed on time.", "Why is Aman's help useful?", "His spare ruler allows Pia to complete the chart.", "The borrowed tool directly meets the stated need.", "ruler completes chart", "tool meets need"),
        _fresh_case("muddy step", "The school step is muddy. Jatin places a mat over it, and people enter without slipping.", "What can readers infer about the mat?", "The mat makes the muddy entrance safer.", "It covers the slippery surface named in the card.", "mat makes entrance safer", "covers muddy step"),
        _fresh_case("faded label", "A jar label is too pale to read. Sana rewrites it in dark ink, and everyone can sort the jar.", "Why would the group thank Sana?", "They can thank Sana because her dark label is easy to read.", "Readable words solve the sorting problem.", "thanks for clear label", "dark ink readable"),
        _fresh_case("cold lunch", "Ravi forgets his lunch cloth. Neha shares a clean one, so he can cover the food.", "Which clue explains Ravi's thanks?", "Neha provides the clean cloth Ravi forgot.", "Her gift fills the missing-item need.", "shares forgotten cloth", "fills missing item"),
        _fresh_case("torn page", "A worksheet tears at the corner. The teacher gives tape, and Kim can keep all the questions together.", "What result follows from the tape?", "The tape holds the torn worksheet together.", "The repair matches the damaged-page clue.", "tape holds page", "repairs torn corner"),
        _fresh_case("late message", "The practice time changes. Farah tells Nitin before he leaves home, so he arrives at the new time.", "Why is Farah's message helpful?", "Her early message prevents Nitin from arriving at the old time.", "The timing clue shows that he can change his plan.", "message prevents wrong time", "told before leaving"),
        _fresh_case("heavy watering can", "Uma cannot lift a full can. Sid pours half into a second can, and they carry one each.", "What thoughtful idea does Sid use?", "Sid shares the load by dividing the water between two cans.", "Two lighter cans solve the weight problem.", "divides water load", "two cans lighter"),
        _fresh_case("dark path", "The corridor light fails. A guard uses a torch and walks the children to the exit.", "Why are the children likely grateful?", "The guard helps them see and reach the exit safely.", "The torch answers the dark-path problem.", "grateful for safe guide", "torch lights path"),
        _fresh_case("wrong room", "Leela enters the music room by mistake. A monitor points to the art-room sign, and she reaches class.", "Which reason fits a thank-you?", "Leela can thank the monitor for showing the correct room.", "The direction fixes her stated mistake.", "thanks for correct direction", "fixes wrong room"),
        _fresh_case("plant shade", "A seedling bends in hot sun. Arif moves it under a light cloth, and its leaves lift later.", "What can be inferred from the later leaves?", "The light shade probably helped the seedling recover.", "The leaves improve after protection from the hot sun.", "shade helped seedling", "leaves lift later"),
        _fresh_case("spare umbrella", "Megha reaches the gate as heavy rain begins. Her umbrella will not open, so Yash shares his large umbrella and both arrive dry.", "Why is Megha likely relieved and thankful?", "Megha is relieved because Yash's umbrella keeps her dry on the walk.", "The broken umbrella and heavy rain show exactly why his help matters.", "relieved by shared umbrella", "broken umbrella heavy rain"),
        _fresh_case("paint apron", "Blue paint spills near Aman's uniform. Tara quickly lends him a spare apron before he starts the mural, and his clothes stay clean.", "What two clues explain Aman's thankful response?", "Aman can thank Tara because her spare apron protects his uniform from the blue paint.", "The spill risk and clean clothes both show the apron solved his problem.", "thanks for spare apron", "spill risk clothes clean"),
        _fresh_case("route sign", "Roadwork hides the usual clinic turn. A shopkeeper points Nisha to a temporary green sign, and she reaches her appointment on time.", "Why would Nisha feel thankful to the shopkeeper?", "Nisha is thankful because the shopkeeper shows the temporary route that gets her to the clinic on time.", "The hidden turn and on-time arrival connect the direction to her relief.", "thankful for temporary route", "hidden turn on time"),
    ],
    "thankful_opposite_context": [
        _fresh_case("empty basket", "The first basket has no oranges; the second is packed to the rim.", "Which opposite word describes the second basket?", "The second basket is full.", "Full is the opposite of empty in this setting.", "basket is full", "opposite of empty"),
        _fresh_case("narrow gate", "The old gate lets one person pass. The new entrance lets four walk side by side.", "What opposite of narrow fits the new entrance?", "The new entrance is wide.", "Four people side by side show greater width.", "entrance is wide", "four side by side"),
        _fresh_case("quiet hall", "The hall is silent before the band arrives. Drums and horns then fill it with sound.", "Which opposite describes the hall after the band starts?", "The hall becomes noisy.", "Drums and horns change quiet to noisy.", "hall becomes noisy", "band fills sound"),
        _fresh_case("rough stone", "One stone scratches the cloth. Another has an even surface that slides easily.", "What opposite of rough describes the second stone?", "The second stone is smooth.", "The easy-sliding surface gives the opposite meaning.", "stone is smooth", "slides without scratch"),
        _fresh_case("early train", "Mina arrives before the bell. Her brother comes after the lesson has begun.", "Which opposite of early fits her brother?", "Her brother is late.", "Arriving after the start explains late.", "brother is late", "after lesson begins"),
        _fresh_case("heavy box", "A wooden box needs two carriers. A paper packet can be lifted with one finger.", "Which opposite describes the packet?", "The paper packet is light.", "One-finger lifting contrasts with the heavy box.", "packet is light", "one finger lift"),
        _fresh_case("open window", "The first window lets air in. The second has both panels pulled together and latched.", "What opposite of open fits the second window?", "The second window is closed.", "Latched panels block the opening.", "window is closed", "panels latched together"),
        _fresh_case("wet towel", "The blue towel drips after washing. The yellow towel stayed indoors and has no water in it.", "Which opposite word fits the yellow towel?", "The yellow towel is dry.", "No water contrasts with the dripping towel.", "towel is dry", "has no water"),
        _fresh_case("bright lamp", "One corner glows under a lamp. The cupboard interior receives no light.", "What opposite of bright describes the cupboard?", "The cupboard is dark.", "No light gives the opposite meaning.", "cupboard is dark", "receives no light"),
        _fresh_case("soft pillow", "The pillow bends under a hand. The wooden bench does not bend at all.", "Which opposite of soft describes the bench?", "The bench is hard.", "Its unbending wood supports hard.", "bench is hard", "wood does not bend"),
        _fresh_case("near shop", "A kiosk stands beside the gate. The market requires a forty-minute bus ride.", "Which opposite of near fits the market?", "The market is far.", "The long bus ride shows distance.", "market is far", "long bus ride"),
        _fresh_case("kind reply", "One message offers help. Another mocks the person who asked.", "Which opposite of kind fits the mocking message?", "The mocking message is unkind.", "Mocking contrasts with offering help.", "message is unkind", "mocks instead of helps"),
        _fresh_case("crowded platform", "The first platform is packed with passengers. After the train leaves, no one remains on the second platform.", "Which opposite of crowded fits the second platform?", "The second platform is empty.", "No remaining passengers reverse the packed-platform condition.", "platform is empty", "no passengers remain"),
        _fresh_case("shallow tray", "Water barely covers the base of one tray. In the tank, the water reaches above a child's knee.", "What opposite of shallow describes the tank water?", "The tank water is deep.", "The knee-high level contrasts with the thin layer in the tray.", "tank water is deep", "knee high level"),
        _fresh_case("straight ribbon", "One ribbon lies in one even line. The other bends left and right around three pegs.", "Which opposite of straight describes the ribbon around the pegs?", "The ribbon around the pegs is crooked.", "Its repeated bends reverse the even straight line.", "ribbon is crooked", "bends around pegs"),
    ],
    "thankful_agreement": [
        _fresh_case("single gardener", "The gardener ___ the young trees every morning. The verb choices are water and waters.", "Which verb agrees with gardener?", "The gardener waters the young trees.", "One gardener takes waters in the present tense.", "gardener waters trees", "one subject waters"),
        _fresh_case("many cooks", "The cooks ___ the clean pots after lunch. Choose stacks or stack.", "Complete the sentence with agreement.", "The cooks stack the clean pots.", "A plural subject uses the base verb stack.", "cooks stack pots", "plural uses stack"),
        _fresh_case("helpful child", "Renu ___ her neighbour with the bags. The choices are help and helps.", "Which complete sentence is correct?", "Renu helps her neighbour with the bags.", "The one named person agrees with helps.", "Renu helps neighbour", "one person helps"),
        _fresh_case("two monitors", "The two monitors ___ the windows before rain. Choose closes or close.", "What verb fits the plural subject?", "The two monitors close the windows.", "Two monitors need the base verb close.", "monitors close windows", "two subjects close"),
        _fresh_case("bus arrives", "The morning bus ___ at eight. The choices are arrive and arrives.", "Finish the sentence.", "The morning bus arrives at eight.", "Bus is one thing, so arrives agrees.", "bus arrives eight", "single bus arrives"),
        _fresh_case("birds gather", "Small birds ___ near the water bowl. Choose gathers or gather.", "Which form matches birds?", "Small birds gather near the water bowl.", "Birds is plural and takes gather.", "birds gather water", "plural birds gather"),
        _fresh_case("friend carries", "My friend ___ the second box. Choose carry or carries.", "Write the correct full sentence.", "My friend carries the second box.", "Friend names one person and takes carries.", "friend carries box", "one friend carries"),
        _fresh_case("teams share", "Both teams ___ the field after practice. Choose shares or share.", "Which verb completes the idea?", "Both teams share the field after practice.", "Both teams is plural, so share fits.", "teams share field", "both means plural"),
        _fresh_case("cat waits", "The grey cat ___ beside the door. Choose wait or waits.", "How should the sentence read?", "The grey cat waits beside the door.", "One cat agrees with waits.", "cat waits door", "single cat waits"),
        _fresh_case("pupils thank", "The pupils ___ the driver after the trip. Choose thanks or thank.", "Select the agreeing verb.", "The pupils thank the driver after the trip.", "Pupils is plural and needs thank.", "pupils thank driver", "plural pupils thank"),
        _fresh_case("aunt teaches", "My aunt ___ me a card game. Choose teach or teaches.", "Complete the present-tense sentence.", "My aunt teaches me a card game.", "Aunt is one person and takes teaches.", "aunt teaches game", "one aunt teaches"),
        _fresh_case("workers repair", "The workers ___ the loose gate. Choose repairs or repair.", "Which full sentence has agreement?", "The workers repair the loose gate.", "More than one worker takes repair.", "workers repair gate", "plural workers repair"),
        _fresh_case("one kite", "The red kite ___ above the terrace. Choose fly or flies.", "Complete the kite sentence with the agreeing verb.", "The red kite flies above the terrace.", "One kite takes flies in the present tense.", "kite flies terrace", "one kite flies"),
        _fresh_case("many dancers", "The dancers ___ in two rows near the stage. Choose moves or move.", "Which complete sentence matches the plural subject?", "The dancers move in two rows near the stage.", "More than one dancer uses the base verb move.", "dancers move rows", "plural uses move"),
        _fresh_case("vendor packs", "The fruit vendor ___ six guavas in a paper bag. Choose pack or packs.", "Write the full agreeing sentence about the fruit vendor.", "The fruit vendor packs six guavas in a paper bag.", "Vendor names one person, so packs agrees.", "vendor packs guavas", "one vendor packs"),
    ],
    "thankful_procedure": [
        _fresh_case("thank-you card", "The card gives these steps: fold paper, write a message, check the name, and place it in an envelope.", "Give the steps in a usable order.", "First fold, next write, then check the name, and finally use the envelope.", "The message belongs on folded paper before the card is packed.", "fold write check pack", "message before envelope"),
        _fresh_case("water station", "A note says: wash the jug, fill it, set out cups, and place the jug on the table.", "What should happen before the cups are used?", "Wash and fill the jug before placing it with the cups.", "A clean filled jug is needed for the station.", "wash fill before serve", "clean jug needed"),
        _fresh_case("book return", "The library strip says: find the shelf code, carry the book there, match the label, and slide it into place.", "Retell the four actions.", "First find the code, next carry the book, then match, and finally shelve it.", "The code guides where the later matching happens.", "find carry match shelve", "code guides shelf"),
        _fresh_case("seed gift", "The packet directions say: write the seed name, add three dry seeds, close the flap, and give it to a friend.", "Which order keeps the label useful?", "Write the name before adding, closing, and giving the seeds.", "The recipient needs the label on the finished packet.", "label add close give", "name before gift"),
        _fresh_case("clean brush", "After painting, rinse the brush, press out water, shape the bristles, and leave it flat to dry.", "Write a short answer with all actions in order.", "First rinse, next press, then shape, and finally dry the brush flat.", "Cleaning comes before shaping and drying.", "rinse press shape dry", "clean before dry"),
        _fresh_case("lost item note", "The notice plan is: name the object, tell where it was found, add the date, and give the note to the office.", "What makes the notice complete?", "It needs the object, place, date, and office delivery in that order.", "Each detail helps the office identify the lost item.", "object place date office", "details identify item"),
        _fresh_case("shared snack", "The safe plan says: wash hands, open the sealed box, place pieces on plates, and pass one plate to each table.", "Which step must be first?", "Washing hands must happen before the food is handled.", "The hygiene step comes before opening and serving.", "wash hands first", "before handling food"),
        _fresh_case("plant support", "The garden card says: place a stick beside the stem, tie a loose cloth strip, check the knot, and water the soil.", "How should the support be added?", "First place the stick, next tie loosely, then check, and finally water.", "The stick must be present before the stem can be tied.", "place tie check water", "stick before tie"),
        _fresh_case("class shelf", "To tidy the shelf, remove loose papers, sort books by label, stand them upright, and return the papers to a folder.", "Give a clear four-step response.", "First remove papers, next sort books, then stand them, and finally file the papers.", "Clearing space allows sorting before final filing.", "remove sort stand file", "clear space before sort"),
        _fresh_case("visitor badge", "The desk guide says: ask the visitor's name, write it, clip the badge on, and point out the waiting area.", "What is the correct welcome order?", "Ask, write, clip the badge, and then show the waiting area.", "A name must be known before it can be written on the badge.", "ask write clip guide", "name before badge"),
        _fresh_case("umbrella return", "The tag steps are: dry the umbrella, close it, tie the strap, and return it to its owner.", "Which action comes just before return?", "Tying the strap comes just before returning the umbrella.", "The item is dried and secured before handover.", "tie before return", "dry secure handover"),
        _fresh_case("team thanks", "The group plan says: list each helper, write one specific thanks, read the note for errors, and sign every member's name.", "Summarise the plan in sequence.", "First list helpers, next write thanks, then check, and finally add the names.", "The message is drafted before checking and signing.", "list write check sign", "draft before signing"),
        _fresh_case("yoghurt fruit bowl", "The no-cook card says: rinse berries, put yoghurt in a cup, place the fruit over it, and finish with a seed topping.", "Retell the fruit-cup steps and explain why rinsing comes first.", "First rinse berries, next add yoghurt, then place fruit, and finally top with seeds.", "Rinsing happens first because the fruit must be clean before it touches the ready-to-eat cup.", "rinse yoghurt fruit seeds", "clean fruit before cup"),
        _fresh_case("cucumber sandwich", "The lunch card says: wash cucumber, spread soft cheese on bread, add thin cucumber slices, and close the sandwich.", "Put the cucumber-sandwich steps in order and name the step before closing.", "First wash cucumber, next spread cheese, then add slices, and finally close the sandwich.", "Adding the cucumber slices comes just before the bread is closed.", "wash spread add close", "slices before closing"),
        _fresh_case("trail mix cup", "The snack plan says: check the ingredient labels, measure puffed rice, add raisins, and stir both in a clean cup.", "Give the trail-mix order and explain why label checking must happen before mixing.", "First check labels, next measure rice, then add raisins, and finally stir.", "Labels are checked first so the ingredients are suitable before they are combined.", "check measure add stir", "labels before mixing"),
    ],
    "thankful_dialogue_response": [
        _fresh_case("door offer", "'I can hold the door while you carry the box,' said Neel. Asha nodded.", "Who offers help, and what can Asha say?", "Neel offers help, and Asha can thank him for holding the door.", "The speech tag names Neel and his offer answers the box problem.", "Neel offers door help", "thanks for holding"),
        _fresh_case("pencil loan", "Maya asked, 'May I use your green pencil?' 'Yes, here it is,' replied Om.", "Who lends the pencil, and what reply fits?", "Om lends the pencil, and Maya can thank him for sharing it.", "Om's quoted answer gives the requested object.", "Om lends pencil", "thanks for sharing"),
        _fresh_case("seat direction", "'Where is my seat?' asked Hari. Lopa said, 'It is beside the window.'", "Who gives the answer?", "Lopa gives the seat location, and Hari can thank her for the direction.", "Her line directly names the requested place.", "Lopa gives location", "thanks for direction"),
        _fresh_case("water offer", "Zed said, 'My bottle is empty.' Rina replied, 'You may fill it from my jug.'", "What friendly response belongs next?", "Zed can thank Rina for offering water from her jug.", "Rina's offer matches the empty-bottle need.", "Zed thanks Rina", "water meets need"),
        _fresh_case("page number", "'Which page has the map?' asked Tanu. 'Page eighteen,' answered her partner.", "How can Tanu continue the exchange?", "Tanu can thank her partner for naming page eighteen.", "The answer supplies exactly the missing page number.", "thanks for page number", "answer matches question"),
        _fresh_case("bag repair", "'Your strap is loose,' said Vivek. 'I have a safe clip you can use.'", "Who notices the problem and offers an item?", "Vivek notices the strap and offers a clip, so the owner can thank him.", "Both helpful ideas belong to Vivek's quoted lines.", "Vivek offers clip", "notices loose strap"),
        _fresh_case("raincoat share", "Sonal said, 'You can wear my spare raincoat.' Jai replied, 'That will keep me dry.'", "What could Jai add?", "Jai can thank Sonal for sharing her spare raincoat.", "The thanks follows Sonal's clear offer.", "Jai thanks Sonal", "shares spare raincoat"),
        _fresh_case("quiet reminder", "'The baby is sleeping,' whispered Dipa. Arun answered, 'I will close the door softly.'", "Whose reply solves the need?", "Arun responds by promising to close the door softly.", "His action answers Dipa's need for quiet.", "Arun closes softly", "quiet for sleeping baby"),
        _fresh_case("route help", "Kavi asked, 'How do I reach the hall?' Nira replied, 'Turn left after the office.'", "Write Kavi's friendly next line.", "Kavi can thank Nira for the clear left-turn direction.", "Nira gives the route Kavi requested.", "Kavi thanks Nira", "clear left turn"),
        _fresh_case("shared notes", "'I missed the first instruction,' said Ritu. Mehul answered, 'You can read my notes.'", "Why would Ritu thank Mehul?", "Ritu can thank Mehul because his notes contain the missed instruction.", "The offered notes fill the exact information gap.", "thanks for notes", "notes replace missed instruction"),
        _fresh_case("fallen books", "'These books fell from my arms,' said Salma. 'I will pick up the two near me,' replied Gopal.", "Who will pick up books?", "Gopal will pick up two books, and Salma can thank him for helping.", "The reply and speech tag clearly belong to Gopal.", "Gopal picks books", "thanks for helping"),
        _fresh_case("clock check", "'Is it time to leave?' asked Bina. The coach said, 'We have five more minutes.'", "What polite response can Bina make?", "Bina can thank the coach and wait for five more minutes.", "The coach answers the time question with a clear amount.", "Bina thanks coach", "waits five minutes"),
        _fresh_case("library renewal", "'My library book is due today,' said Eira. The librarian replied, 'I can renew it until Monday.'", "Who offers the solution, and what friendly reply can Eira write?", "The librarian offers a renewal, and Eira can thank her for extending the book until Monday.", "The reply directly solves Eira's due-date concern.", "librarian offers renewal", "thanks for Monday extension"),
        _fresh_case("shared desk", "Manu asked, 'May I sit here while my desk dries?' Roshni answered, 'Yes, move your notebook beside mine.'", "Identify Roshni's answer and write Manu's friendly next message.", "Roshni offers a shared desk, and Manu can thank her for making room beside her notebook.", "Her quoted instruction answers Manu's request for a dry place.", "Roshni shares desk", "thanks for making room"),
        _fresh_case("garden directions", "'Where is the compost box?' asked Ali. Sumi replied, 'Walk past the tap and turn right at the neem tree.'", "Who gives the route, and how can Ali respond politely?", "Sumi gives the route, and Ali can thank her for the tap-and-neem directions.", "Her line supplies the exact path Ali requested.", "Sumi gives route", "thanks for clear directions"),
    ],
}

for _level_spec in SPEC["levels"]:
    _level_spec["fresh_cases"] = FRESH_CASES[_level_spec["level_id"]]


SPEC["assessment_pairs"] = [
    _assessment_pair("reading.event_sequence", _case("parcel chain", "A parcel drops, Ina picks it up, checks its label, returns it, and receives thanks.", "Which order matches the card?", "Pick up, check, return, then receive thanks.", "Return, drop, and then check.", "Receive thanks before finding the parcel.", "The label check comes before the safe return.", "pick check return thank", "label before return"), _case("chair chain", "A visitor needs a seat. Raj notices, brings a chair, the visitor sits, and Raj is thanked.", "Which event comes just before thanks?", "The visitor sits in the chair.", "Raj hides the chair.", "The visitor leaves before arriving.", "Sitting follows the helpful action and comes before thanks.", "visitor sits before thanks", "help then response"), kind="choice"),
    _assessment_pair("reading.paragraph_main_idea", _fresh_case("shared tools", "Three pupils lend one another a ruler, eraser, and sharpener so every poster is finished.", "What idea covers the whole card?", "Sharing tools helps the group finish its work.", "Every listed item supports the larger idea of cooperation.", "sharing helps group", "tools finish posters"), _fresh_case("bus kindness", "A child gives up a front seat, carries one bag, and opens the exit for an older rider.", "State the main idea.", "Several small kind acts make the rider's trip easier.", "The seat, bag, and door all help the same person.", "kind acts ease trip", "three helpful actions"), kind="open"),
    _assessment_pair("reading.inference_reason", _fresh_case("dry floor", "Mop marks lead away from a spill, and a yellow sign stands nearby.", "Why was the sign probably placed there?", "The sign warns people about the wet area while it dries.", "The spill and mop marks show a slipping risk.", "sign warns wet floor", "spill creates risk"), _fresh_case("labelled lunch", "A lunch bag has Reva's name and room number. A monitor carries it toward Room 3.", "Why is the monitor going to Room 3?", "The monitor is probably returning Reva's named lunch bag.", "The room number gives a clear delivery clue.", "returning Reva lunch", "room number clue"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("shared torch", "The stair light fails, and Mali lends Dev a torch for the dark steps.", "Write why Dev should thank Mali.", "Dev should thank Mali because the torch helps him see the dark steps.", "The offered light solves the danger shown on the card.", "thanks for torch", "light solves dark steps"), _fresh_case("spare lace", "Niko's shoe lace snaps before a race. Fara gives him a spare lace.", "Explain why Fara's help matters.", "Fara's spare lace lets Niko tie his shoe before the race.", "The new lace fixes the exact problem in time.", "spare lace helps", "fixes shoe before race"), kind="open"),
    _assessment_pair("reading.word_meaning_context", _case("scarce cups", "Only two cups remain for ten people, so the card calls cups scarce.", "What does scarce mean?", "Scarce means not enough are available.", "Scarce means shining brightly.", "Scarce means easy to carry.", "Two for ten shows a shortage.", "scarce means not enough", "two for ten"), _case("generous share", "Pema gives half her fruit to a hungry visitor. The note calls her generous.", "Which meaning fits generous?", "Generous means willing to give and share.", "Generous means refusing every request.", "Generous means arriving late.", "Giving half the fruit is the context clue.", "generous willing to share", "gives half fruit"), kind="choice"),
    _assessment_pair("vocab.antonyms", _case("deep tray", "One tray is shallow; the other holds water far below its rim.", "Which opposite describes the second tray?", "deep", "soft", "early", "Far below the rim contrasts with shallow.", "tray is deep", "opposite of shallow"), _case("slow cart", "The first cart moves quickly; the second takes ten minutes to cross the yard.", "What opposite of quick fits the second cart?", "slow", "bright", "full", "The long crossing time gives the meaning.", "cart is slow", "takes long time"), kind="choice"),
    _assessment_pair("grammar.subject_verb_agreement", _case("child carries", "One child ___ the folded mat. Choose carry or carries.", "Which full sentence agrees?", "One child carries the folded mat.", "One child carry the folded mat.", "One children carries the mat.", "A single child takes carries.", "child carries mat", "single subject carries"), _case("helpers wash", "The helpers ___ the paint cups. Choose washes or wash.", "Select the correct sentence.", "The helpers wash the paint cups.", "The helpers washes the cups.", "The helper wash the cups.", "A plural subject takes wash.", "helpers wash cups", "plural takes wash"), kind="choice"),
    _assessment_pair("writing.complete_sentence", _fresh_case("neighbour helps", "Words on the card: our neighbour / carries / the heavy basket.", "Turn the words into one complete sentence.", "Our neighbour carries the heavy basket to the gate.", "The sentence has a named subject and a clear action.", "neighbour carries basket", "subject and action"), _fresh_case("pupils return", "Words on the card: the pupils / return / the library books.", "Write a complete sentence with the parts.", "The pupils return the library books after lunch.", "The plural subject and action form a whole idea.", "pupils return books", "whole subject action"), kind="open", interaction_type="paragraph_text"),
    _assessment_pair("grammar.sentence_order", _case("badge order", "Words: first / write / the name / on the badge.", "Which order makes sense?", "First, write the name on the badge.", "The badge first on write name.", "Name the on first badge write.", "The sequence word leads a complete command.", "first write name", "complete command order"), _case("brush order", "Words: finally / leave / the brush / flat to dry.", "Choose the correct sentence.", "Finally, leave the brush flat to dry.", "The dry finally brush to leave.", "Flat finally the leave dry.", "The action follows the sequence word in clear order.", "finally leave brush", "clear action order"), kind="choice"),
    _assessment_pair("writing.short_answer", _fresh_case("return plan", "A borrowed game must be checked, packed in its box, and returned before Friday.", "What should the borrower do?", "The borrower should check and pack the game, then return it before Friday.", "The answer includes the needed actions and the deadline.", "check pack return game", "before Friday deadline"), _fresh_case("watering plan", "The class must fill one can, water the dry pots, and put the empty can by the tap.", "Give a short usable answer.", "Fill the can, water the dry pots, and return the empty can to the tap.", "The answer keeps all three stated jobs.", "fill water return can", "all jobs included"), kind="open"),
    _assessment_pair("reading.dialogue_attribution", _case("map speaker", "'The map is in the blue drawer,' said Kiran to Mo.", "Who gives the location?", "Kiran gives the location.", "Mo gives the location.", "The drawer speaks.", "The speech tag names Kiran.", "Kiran gives location", "speech tag names Kiran"), _case("water speaker", "Tia asked for water. 'Use my spare bottle,' replied Ash.", "Who offers the bottle?", "Ash offers the bottle.", "Tia offers the bottle.", "Water offers itself.", "Replied Ash assigns the quoted offer.", "Ash offers bottle", "reply tag Ash"), kind="choice"),
    _assessment_pair("writing.friendly_message", _fresh_case("coat thanks", "Mira lends Jo a dry coat after rain so Jo can travel home warmly.", "Write Jo's friendly reply.", "Thank you, Mira, for lending me a dry coat for the trip home.", "The message names the helper and the exact useful act.", "thank Mira for coat", "keeps Jo warm"), _fresh_case("notes thanks", "Aman shares clear class notes with Zoya after she misses one lesson.", "Write a relevant thank-you message.", "Thank you, Aman, for sharing the notes from the lesson I missed.", "The reply directly names the notes and missed class.", "thank Aman for notes", "notes cover missed lesson"), kind="open", interaction_type="paragraph_text"),
    _assessment_pair("reading.inference_reason", _fresh_case("extra plate", "A host sets one extra plate after reading a message that Nia's cousin is coming.", "Why is there an extra plate?", "The host expects Nia's cousin to join the meal.", "The new visitor message explains the added place.", "cousin joins meal", "message explains plate"), _fresh_case("covered plants", "Dark clouds gather, and the gardener moves young plants under a roof.", "Why does the gardener move them?", "The gardener expects rain and wants to protect the young plants.", "The clouds and shelter action support that idea.", "protect plants from rain", "dark clouds clue"), kind="open"),
    _assessment_pair("writing.reason_answer", _fresh_case("clear sign", "Ria writes larger letters on a safety sign so people at the far gate can read it.", "Explain why the larger letters help.", "Larger letters help because distant readers can see the warning more easily.", "The far-gate clue makes size useful.", "large letters easier read", "far gate needs visibility"), _fresh_case("two baskets", "A heavy load is split into two baskets so two children can carry it.", "Write why splitting the load works.", "Splitting the load works because each basket becomes lighter to carry.", "Two carriers share weight that was in one place.", "two lighter baskets", "shared weight easier"), kind="open"),
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
