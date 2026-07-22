"""Original deep manifest for Class 2 English Chapter 9, My Name."""

from __future__ import annotations

from typing import Any

from app.content.school_rebuild_manifests.english.class_2.eng_c2_ch08 import (
    CLASS2_SKILLS,
    _open_set,
    build_manifest,
    choice_task,
    evidence,
    open_task,
)


S = CLASS2_SKILLS
CHAPTER_ID = "eng_c2_ch09"
SOURCE_URL = "https://ncert.nic.in/textbook/pdf/bemr109.pdf"


LEVELS: list[dict[str, Any]] = [
    {
        "level_id": f"{CHAPTER_ID}:search_and_memory_chain",
        "title": "Follow a name search",
        "focus": "track each helper, clue, and memory trigger in a search sequence",
        "outcome": "Retell a search in order and explain which visible event helps the seeker remember without inventing a missing step.",
        "skill_ids": [S["comprehension"], S["sequence"]],
        "episode_kind": "comprehension_studio",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-2", f"{CHAPTER_ID}:write:5"],
        "principle": "A search chain follows the same question from one helper to the next; a memory trigger must be linked to a stated sight or action.",
        "connect": {
            "teaching_block": "When a character visits several helpers, names and route words keep the search clear. The final clue may also explain a memory.",
            "passage": "Nilo forgets his garden tool's name. He asks the guard, then the gardener, and remembers spade when he sees one digging soil.",
            "prompt": "Notice the two helpers and the final memory clue before continuing.",
        },
        "co": choice_task(
            "Tara cannot recall the name of a fruit. She asks her brother, who sends her to the cook. The cook cuts a guava, and Tara remembers.",
            "Whom does Tara ask immediately before she remembers?",
            "the cook",
            ["her brother", "the fruit seller"],
        ),
        "guided": [
            choice_task(
                "A child searches for a puppy's name. First she asks the neighbour, next the postman, and last the puppy runs to a tag marked Moti.",
                "Which event ends the search?",
                "The puppy runs to the marked tag.",
                ["The child asks the neighbour.", "The postman loses a tag."],
            ),
            open_task(
                "Ira forgets the word lantern. Her aunt points to the storeroom; there Ira sees a glowing lamp hanging from a hook and remembers.",
                "Give the helper, visible trigger, and remembered word in order.",
                "Ira's aunt guides her, the glowing hanging lamp triggers her memory, and Ira remembers lantern.",
                [
                    evidence("Names the aunt as helper.", "aunt guides her", "her aunt points"),
                    evidence("Links the glowing lamp to lantern.", "glowing hanging lamp", "remembers lantern"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set(
            [
                (
                    "Kabir forgets his team's colour name. He asks the coach, then checks the equipment shelf, where a violet ribbon makes him remember.",
                    "Retell the search and explain what wakes Kabir's memory.",
                    "Kabir asks the coach and checks the shelf; seeing the violet ribbon helps him remember violet.",
                    [
                        evidence("Keeps coach before shelf.", "asks the coach", "checks the shelf"),
                        evidence("Connects ribbon to the remembered colour.", "violet ribbon", "remember violet"),
                    ],
                ),
                (
                    "Mina cannot recall a bird's name. The librarian sends her to the courtyard, and a bird tapping a tree trunk reminds her of woodpecker.",
                    "Write the route and the cause of Mina's remembering.",
                    "The librarian sends Mina to the courtyard, where the tapping bird makes her remember woodpecker.",
                    [
                        evidence("States the route to the courtyard.", "librarian sends", "to the courtyard"),
                        evidence("Uses tapping as the memory cause.", "tapping bird", "remember woodpecker"),
                    ],
                ),
            ],
            ordered=True,
        ),
        "transfer": _open_set(
            [
                (
                    "Ravi forgets the word compass during a hike. A guide opens a map case, and the round direction tool inside restores the word.",
                    "Transfer the memory-chain skill: state the problem, trigger, and result.",
                    "Ravi forgets compass, sees the round direction tool in the map case, and then remembers the word.",
                    [
                        evidence("States the forgotten word problem.", "forgets compass", "cannot remember compass"),
                        evidence("Links the round tool to remembering.", "round direction tool", "remembers the word"),
                    ],
                ),
                (
                    "At a clinic, Zoya forgets the word thermometer. The nurse shows a slim tool with numbers, and the familiar sight brings the word back.",
                    "Explain how the nurse's action solves Zoya's search.",
                    "The nurse shows the numbered tool, and that familiar sight helps Zoya remember thermometer.",
                    [
                        evidence("Includes the nurse's shown clue.", "nurse shows", "numbered tool"),
                        evidence("Connects the clue to thermometer.", "remember thermometer", "word thermometer"),
                    ],
                ),
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "Dev forgets the name of a tune. He asks his cousin, visits the music room, and remembers lullaby when he reads a labelled song card.",
                    "Sequence all three search steps and identify the memory trigger.",
                    "Dev asks his cousin, visits the music room, reads the labelled card, and remembers lullaby.",
                    [
                        evidence("Orders cousin and music room.", "asks his cousin", "visits the music room"),
                        evidence("Names the labelled card trigger.", "labelled card", "remembers lullaby"),
                    ],
                ),
                (
                    "Sana seeks the word marigold. Her grandfather suggests the balcony, where an orange flower beside its label helps her recall it.",
                    "Tell how the search moves and why it ends.",
                    "Sana follows her grandfather's balcony clue, sees the orange flower and label, and remembers marigold.",
                    [
                        evidence("Uses the balcony route clue.", "balcony clue", "suggests the balcony"),
                        evidence("Explains the flower-label trigger.", "orange flower", "remembers marigold"),
                    ],
                ),
            ],
            ordered=True,
        ),
        "cluster_id": f"{CHAPTER_ID}:search_order_trigger_gap",
        "misconception": "The learner lists characters without preserving the search route or says the answer appeared without linking it to the visible memory trigger.",
        "remediation": "Build a who-next path, circle the final sight or action, and connect that clue to remembering with one because statement.",
        "support": _open_set(
            [
                ("Omi asks his sister, then the baker, before a loaf label reminds him of rye.", "Name the two helpers and final clue in order.", "Omi asks his sister, then the baker, and remembers rye from the loaf label.", [evidence("Keeps both helpers and label in order.", "sister", "baker", "loaf label")]),
                ("Lata forgets the word jasmine. A neighbour points to a scented white flower with a name card.", "Explain which clue restores Lata's word.", "The scented white flower and its name card help Lata remember jasmine.", [evidence("Links the flower card to jasmine.", "white flower", "name card", "remember jasmine")]),
                ("First Noor asks the driver. Next she checks the lost-property desk. There she sees her badge marked Falcon.", "Retell the route to the remembered team name.", "Noor asks the driver, checks the desk, and remembers Falcon from the marked badge.", [evidence("Orders driver, desk, and badge.", "asks the driver", "checks the desk", "marked badge")]),
                ("Aman sees a spinning wheel and suddenly recalls the word pinwheel.", "State the visible cause and memory result.", "Seeing the spinning wheel causes Aman to remember pinwheel.", [evidence("Connects the wheel sight to remembering.", "spinning wheel", "remember pinwheel")]),
                ("Reva asks a teacher where to look, opens the science box, and recognises a magnet by its red-blue ends.", "Give the search action and recognition clue.", "Reva opens the science box, sees the red and blue ends, and recognises the magnet.", [evidence("Includes the box action and colour clue.", "science box", "red and blue ends", "recognises the magnet")]),
            ],
            ordered=True,
        ),
    },
    {
        "level_id": f"{CHAPTER_ID}:name_and_polite_words",
        "title": "Use memory and polite words",
        "focus": "infer identity and request vocabulary from context and use it respectfully",
        "outcome": "Explain a chapter word through context and use name, memory, ask, please, or thank accurately in a fresh situation.",
        "skill_ids": [S["word_context"], S["word_use"]],
        "episode_kind": "meaning_encounter",
        "source_anchor_ids": [f"{CHAPTER_ID}:read:1-2", f"{CHAPTER_ID}:do-project:6"],
        "principle": "Nearby actions explain a word, while polite words show how a request or response respects another person.",
        "connect": {
            "teaching_block": "A context clue may show remembering, forgetting, asking, or responding. Read what happens around the target word.",
            "passage": "Pia recalls her locker code; the number returns to her memory after she sees a note.",
            "prompt": "Notice how returns to her memory explains recalls before continuing.",
        },
        "co": choice_task("Rohan hesitates because he is unsure which notebook belongs to him.", "Which meaning fits hesitates?", "pauses because he is unsure", ["runs because he is late", "writes with confidence"]),
        "guided": [
            choice_task("Maya recognises the labelled cup; she knows it is hers as soon as she sees her name.", "Which phrase explains recognises?", "knows it from a clue", ["forgets it completely", "borrows it secretly"]),
            open_task("Ishaan says, 'Please lend me the blue pencil.' After Neha gives it, he says, 'Thank you.'", "Explain the job of please and thank you, then create a new polite request.", "Please makes the request respectful, thank you shows gratitude, and a new request is: Please pass the ruler.", [evidence("Explains both polite words.", "request respectful", "shows gratitude"), evidence("Creates a request with please.", "Please pass", "Please lend")]),
        ],
        "independent": _open_set([
            ("A label identifies a lunchbox by showing the owner's name and class.", "Define identifies from context and use it in a new name sentence.", "Identifies means shows exactly who or what something is. The tag identifies Mira's bag.", [evidence("Explains exact identity.", "shows exactly who", "shows what something is"), evidence("Uses identifies with a label or tag.", "tag identifies", "label identifies")]),
            ("Arif requests a library card by asking calmly and including the word please.", "Explain requests and write a different polite request.", "Requests means asks for something politely. Arif could say, 'Please give me a library form.'", [evidence("Defines a polite ask.", "asks for something politely", "polite ask"), evidence("Writes a please request.", "Please give", "Please may I")]),
        ]),
        "transfer": _open_set([
            ("A shop token has a unique number that belongs to only one order.", "Explain unique and use it for a person's name card.", "Unique means different from every other one. Each learner has a unique name card.", [evidence("Explains one-of-a-kind difference.", "different from every other", "only one"), evidence("Uses unique with a name card.", "unique name card")]),
            ("Meera is grateful when a neighbour returns her book, so she thanks him warmly.", "Infer grateful and use it in a fresh response.", "Grateful means thankful. I felt grateful when my friend found my badge.", [evidence("Defines thankful.", "means thankful", "feels thankful"), evidence("Uses grateful after helpful action.", "felt grateful", "am grateful")]),
        ]),
        "review": _open_set([
            ("A child introduces herself by stating her name and one detail about her hobby.", "Explain introduces and write a short example.", "Introduces means tells others who she is. 'My name is Kavya, and I enjoy chess.'", [evidence("Explains telling identity.", "tells others who", "says who she is"), evidence("Includes a name and detail.", "My name is", "I enjoy")]),
            ("The clue reminds Yusuf of a word he knew earlier but could not recall.", "Distinguish reminds from teaches and use reminds correctly.", "Reminds means helps someone remember. The seed packet reminds Yusuf of the word sunflower.", [evidence("Defines help with remembering.", "helps someone remember"), evidence("Uses reminds with a clue.", "packet reminds", "label reminds")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:context_or_politeness_mismatch",
        "misconception": "The learner repeats a word without its context meaning or writes a command while claiming it is a polite request.",
        "remediation": "Match the word to the nearby action, replace it with a plain meaning, and test polite requests for please plus a clear requested item.",
        "support": _open_set([
            ("The familiar song is one Jaya already knows.", "Explain familiar and use it with a name.", "Familiar means already known. The familiar name helped Jaya remember her cousin.", [evidence("Defines and uses already known.", "already known", "familiar name")]),
            ("Kunal forgets the code, so it is no longer in his memory.", "State the context meaning of forgets.", "Forgets means cannot remember something that was known before.", [evidence("Explains loss of a known memory.", "cannot remember", "known before")]),
            ("Nia wants a book from a friend.", "Turn the want into one respectful request.", "Nia can ask, 'Please may I borrow your book?'", [evidence("Uses please and names the book.", "Please", "borrow your book")]),
            ("A classmate returns Om's pencil.", "Write a fitting polite response and explain its purpose.", "Om says, 'Thank you for returning my pencil,' to show gratitude.", [evidence("Includes thanks and gratitude.", "Thank you", "show gratitude")]),
            ("The card states: Name: Ritu; Class: 2B.", "Explain how the card identifies Ritu.", "The card identifies Ritu with the name Ritu and class 2B.", [evidence("States the written name.", "name Ritu", "Ritu is the name"), evidence("States the written class.", "class 2B", "2B is the class")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:visible_name_spellings",
        "title": "Build search-word spellings",
        "focus": "use printed chunks and letter patterns to spell identity and search words",
        "outcome": "Produce a standard spelling from visible letters and use the word in a meaningful name-search sentence.",
        "skill_ids": [S["spelling"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:speak-blends:7", f"{CHAPTER_ID}:write:5"],
        "principle": "This text-only spelling lab uses visible letters and chunks; it never claims to assess pronunciation or listening.",
        "connect": {
            "teaching_block": "Check every printed chunk before joining a word, then confirm that the completed spelling fits the sentence meaning.",
            "passage": "Printed chunks: re + mem + ber = remember; name + tag = nametag.",
            "prompt": "Notice the visible chunks and complete forms before continuing.",
        },
        "co": choice_task("Candidates: blanket, blankit, blancket. The sentence names a warm cover.", "Which candidate has the standard spelling?", "blanket", ["blankit", "blancket"]),
        "guided": [
            choice_task("Candidates: plant, plaant, plunt. The clue names a living green thing.", "Which printed word is standard?", "plant", ["plaant", "plunt"]),
            open_task("Chunks: re + call. Meaning clue: remember something.", "Join the chunks and use the word in a search sentence.", "The word is recall. Mina can recall her street name.", [evidence("Spells recall correctly.", "recall"), evidence("Uses recall as remembering.", "recall her street name", "recall the name")]),
        ],
        "independent": _open_set([
            ("Missing letters: m e m _ r y. The clue holds remembered information.", "Complete the word and use it in a sentence.", "The word is memory. The flower picture brought back a memory.", [evidence("Spells memory correctly.", "memory"), evidence("Uses memory meaningfully.", "brought back a memory", "my memory")]),
            ("Scrambled letters: e n a m. The clue identifies a person or thing.", "Unscramble the word and write a complete identity sentence.", "The word is name. My name is Asha.", [evidence("Spells name correctly.", "name"), evidence("Uses name in an identity sentence.", "My name is")]),
        ]),
        "transfer": _open_set([
            ("Base word: help. Add ful to describe a useful clue.", "Build the new spelling and use it for a person.", "The word is helpful. The helpful guard showed us the desk.", [evidence("Builds helpful correctly.", "helpful"), evidence("Uses helpful for assistance.", "helpful guard", "helpful friend")]),
            ("Chunks: po + lite. The word describes respectful manners.", "Join the chunks and write one complete sentence.", "The word is polite. A polite request includes please.", [evidence("Spells polite correctly.", "polite"), evidence("Uses polite for respectful language.", "polite request", "polite reply")]),
        ]),
        "review": _open_set([
            ("Correct the printed word remembar in a sentence about a lost name.", "Write the corrected word and a complete sentence.", "The corrected word is remember. I remember the name after seeing the card.", [evidence("Corrects remember.", "remember"), evidence("Uses it with a memory clue.", "remember the name", "seeing the card")]),
            ("Missing letters: p l e _ s e. The clue makes a request respectful.", "Complete the word and write a polite request.", "The word is please. Please pass the green notebook.", [evidence("Spells please correctly.", "please"), evidence("Uses please in a request.", "Please pass", "Please lend")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:blend_and_chunk_spelling",
        "misconception": "The learner drops a visible blend, swaps letters after guessing from memory, or writes a correct-looking word that does not fit the printed clue.",
        "remediation": "Trace each shown chunk, join without deleting letters, compare with the meaning clue, and finish by using the spelling in a short sentence.",
        "support": _open_set([
            ("Chunks: bl + ue. The clue names a colour.", "Join and use the colour word.", "The word is blue. The blue label shows my group.", [evidence("Spells and uses blue.", "blue", "blue label")]),
            ("Chunks: pl + ate. The clue names a dish.", "Build the word and write a sentence.", "The word is plate. My name card rests beside the plate.", [evidence("Spells and uses plate.", "plate", "beside the plate")]),
            ("Candidates: grass, gras, grasse. The clue names a green ground plant.", "Write the standard word in a sentence.", "The word is grass. A label stood in the grass.", [evidence("Spells and uses grass.", "grass", "in the grass")]),
            ("Scrambled letters: e d a r. The clue is a warm greeting word.", "Unscramble and use the word before a name.", "The word is dear. Dear Ravi, thank you for the note.", [evidence("Spells and uses dear.", "dear", "Dear Ravi")]),
            ("Correct this word: thnak. The intended response shows gratitude.", "Repair the spelling and use it politely.", "The corrected word is thank. I thank you for helping me.", [evidence("Corrects and uses thank.", "thank", "thank you")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:identity_word_jobs",
        "title": "Find jobs in identity sentences",
        "focus": "classify names, actions, and describing words in short profiles",
        "outcome": "Identify nouns, verbs, and adjectives in visible identity or search sentences and explain each selected word's job.",
        "skill_ids": [S["word_jobs"]],
        "episode_kind": "language_lab",
        "source_anchor_ids": [f"{CHAPTER_ID}:write:5", f"{CHAPTER_ID}:do-project:6"],
        "principle": "A profile sentence names a person or thing, shows an action, and may add a describing word; the sentence decides each job.",
        "connect": {
            "teaching_block": "Read a complete profile before labelling words. A capitalised personal name is a noun, while actions and descriptions do different work.",
            "passage": "Cheerful Zain carries a red folder. Zain and folder name, carries acts, and cheerful and red describe.",
            "prompt": "Notice how each word job is proved by the visible sentence.",
        },
        "co": choice_task("Quiet Leela searches the garden.", "Which word shows Leela's action?", "searches", ["quiet", "garden"]),
        "guided": [
            choice_task("The helpful cook reads the label.", "Which word describes the cook?", "helpful", ["cook", "reads"]),
            open_task("Young Rafi carries a heavy basket.", "Label Rafi, carries, and heavy by word job.", "Rafi is a noun, carries is a verb, and heavy is an adjective.", [evidence("Labels the name and action.", "Rafi is a noun", "carries is a verb"), evidence("Labels heavy as describing.", "heavy is an adjective")]),
        ],
        "independent": _open_set([
            ("Curious Mira opens the old notebook.", "Identify a naming word, the action, and both describing words.", "Mira or notebook is a noun, opens is the verb, and curious and old are adjectives.", [evidence("Names a noun and verb.", "Mira", "notebook", "opens"), evidence("Finds curious and old.", "curious", "old")]),
            ("The brown leaf reminds Sameer.", "Explain the jobs of brown, leaf, and reminds.", "Brown is an adjective, leaf is a noun, and reminds is a verb.", [evidence("Classifies all three words.", "brown is an adjective", "leaf is a noun", "reminds is a verb")]),
        ]),
        "transfer": _open_set([
            ("Polite Nita thanks the driver.", "Transfer the word-job check and label polite, Nita, and thanks.", "Polite is an adjective, Nita is a noun, and thanks is a verb.", [evidence("Classifies all requested words.", "polite is an adjective", "Nita is a noun", "thanks is a verb")]),
            ("A bright sign identifies the correct lane.", "Name the noun, action, and describing word tied to sign.", "Sign is the noun, identifies is the action, and bright describes the sign.", [evidence("Connects all jobs to sign.", "sign is the noun", "identifies is the action", "bright describes")]),
        ]),
        "review": _open_set([
            ("The small card shows Arun's full name.", "Classify small, card, and shows.", "Small is an adjective, card is a noun, and shows is a verb.", [evidence("Classifies adjective, noun, and verb.", "small is an adjective", "card is a noun", "shows is a verb")]),
            ("Kind Salma returns the lost badge.", "Identify the action and the words that name and describe the person.", "Returns is the action, Salma names the person, and kind describes her.", [evidence("Finds returns and Salma.", "returns is the action", "Salma names"), evidence("Links kind to Salma.", "kind describes")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:profile_word_job_guess",
        "misconception": "The learner calls every capitalised or important word an action, or labels by memorised position instead of testing the word inside the sentence.",
        "remediation": "Ask who or what, what happens, and which word tells more; then attach each answer to the exact word before assigning a label.",
        "support": _open_set([
            ("Brave Om asks a question.", "Label brave, Om, and asks.", "Brave is an adjective, Om is a noun, and asks is a verb.", [evidence("Labels all three jobs.", "brave is an adjective", "Om is a noun", "asks is a verb")]),
            ("The silver tag hangs nearby.", "Find the naming, action, and describing words.", "Tag is a noun, hangs is a verb, and silver is an adjective.", [evidence("Finds tag, hangs, and silver.", "tag is a noun", "hangs is a verb", "silver is an adjective")]),
            ("A gentle breeze moves the leaf.", "Explain why breeze is not the action.", "Breeze names a thing, while moves is the action verb.", [evidence("Contrasts breeze and moves.", "breeze names", "moves is the action")]),
            ("Happy Rina remembers the word.", "Classify happy, Rina, and remembers.", "Happy describes, Rina names, and remembers shows action.", [evidence("Classifies all requested words.", "happy describes", "Rina names", "remembers shows action")]),
            ("The green label identifies Kabir.", "Name the adjective and both naming words.", "Green is the adjective, while label and Kabir are nouns.", [evidence("Finds green, label, and Kabir.", "green is the adjective", "label", "Kabir")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:polite_question_builder",
        "title": "Build polite questions and replies",
        "focus": "arrange request words and use capitals, question marks, and full stops",
        "outcome": "Build a complete polite question or reply from visible words and finish it with the correct sentence boundaries.",
        "skill_ids": [S["sentence_order"], S["punctuation"]],
        "episode_kind": "expression_workshop",
        "source_anchor_ids": [f"{CHAPTER_ID}:speak:3", f"{CHAPTER_ID}:do-project:6"],
        "principle": "A polite request keeps please near the action, follows question order when needed, and uses a capital plus the correct end mark.",
        "connect": {
            "teaching_block": "First identify whether the words form a question or statement. Then arrange the request and complete its written boundaries.",
            "passage": "Word set: may / please / I / borrow / the card. Finished question: May I please borrow the card?",
            "prompt": "Notice the request order, capital M, and question mark.",
        },
        "co": choice_task("Word set: name / your / what / is", "Which option forms a complete question?", "What is your name?", ["Your what name is.", "what is Name your?"]),
        "guided": [
            choice_task("Word set: please / me / label / give / the", "Which option is a finished polite request?", "Please give me the label.", ["Give label please the me.", "please Me the label give"]),
            open_task("Word set: do / remember / name / you / the", "Arrange the words and punctuate the memory question.", "Do you remember the name?", [evidence("Uses correct question order.", "do you remember the name"), evidence("Uses capital and question mark.", "Do", "?")]),
        ],
        "independent": _open_set([
            ("Word set: could / please / repeat / you / that", "Build the respectful question with every word.", "Could you please repeat that?", [evidence("Uses the complete polite order.", "could you please repeat that"), evidence("Adds capital and question mark.", "Could", "?")]),
            ("Unfinished reply: thank you for finding my card", "Repair the reply as a complete sentence.", "Thank you for finding my card.", [evidence("Keeps the gratitude message.", "thank you for finding my card"), evidence("Adds capital and full stop.", "Thank", ".")]),
        ]),
        "transfer": _open_set([
            ("Word set: where / desk / is / help / the / please", "Create a polite request for location help.", "Please help: where is the desk?", [evidence("Uses please and asks the location.", "please help", "where is the desk"), evidence("Uses capital and question mark.", "Please", "?")]),
            ("Word set: your / may / pencil / borrow / I / please", "Arrange the borrowing question and finish it.", "May I please borrow your pencil?", [evidence("Uses all words in request order.", "may I please borrow your pencil"), evidence("Uses capital and question mark.", "May", "?")]),
        ]),
        "review": _open_set([
            ("Jumbled line: name / spell / please / your", "Write the polite command as a complete sentence.", "Please spell your name.", [evidence("Uses polite command order.", "please spell your name"), evidence("Uses capital and full stop.", "Please", ".")]),
            ("Unfinished question: who helped you remember", "Add the missing sentence boundaries.", "Who helped you remember?", [evidence("Keeps the complete question.", "who helped you remember"), evidence("Adds capital and question mark.", "Who", "?")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:request_order_boundary",
        "misconception": "The learner keeps jumbled order, drops please, or ends every request with the same mark without checking whether it is a question or statement.",
        "remediation": "Choose question or statement first, arrange person and action, restore please, and finish with a capital plus the matching end mark.",
        "support": _open_set([
            ("Word set: name / is / my / Veer", "Build the identity statement.", "The finished statement is: My name is Veer.", [evidence("Builds and punctuates the statement.", "my name is Veer", "My", ".")]),
            ("Word set: what / mean / does / recall", "Build the meaning question.", "What does recall mean?", [evidence("Builds and punctuates the question.", "what does recall mean", "What", "?")]),
            ("Line needing repair: please show me the tag", "Add correct sentence boundaries.", "Please show me the tag.", [evidence("Adds capital and full stop.", "Please show me the tag", ".")]),
            ("Word set: do / where / study / you", "Arrange the location question.", "The finished question is: Where do you study?", [evidence("Uses correct question order and mark.", "where do you study", "Where", "?")]),
            ("Line needing repair: thank you for your help", "Finish the gratitude statement.", "Thank you for your help.", [evidence("Adds complete statement boundaries.", "Thank you for your help", ".")]),
        ]),
    },
    {
        "level_id": f"{CHAPTER_ID}:identity_sentence_writer",
        "title": "Write a clear identity introduction",
        "focus": "construct complete name, interest, and polite response sentences from visible facts",
        "outcome": "Write a complete identity introduction or respectful response that uses every supplied fact and does not invent private information.",
        "skill_ids": [S["comprehension"], S["sentence"]],
        "episode_kind": "application_mission",
        "source_anchor_ids": [f"{CHAPTER_ID}:speak:3", f"{CHAPTER_ID}:do-project:6"],
        "principle": "An identity sentence uses only volunteered facts, begins clearly, and joins a name with one relevant detail in respectful language.",
        "connect": {
            "teaching_block": "A short introduction can be complete without sharing private details. A name and one chosen interest are enough.",
            "passage": "Visible profile: Name: Ayan. Chosen interest: growing mint plants.",
            "prompt": "Notice that the profile supplies both safe facts needed for one sentence.",
        },
        "co": choice_task("Visible profile: Name: Ria. Chosen interest: paper folding.", "Which sentence uses both supplied facts respectfully?", "My name is Ria, and I enjoy paper folding.", ["Ria must share her home address.", "Paper folding has no name."], skills=[S["comprehension"]]),
        "guided": _open_set([
            ("Visible profile: Name: Danish. Favourite school activity: reading comics.", "Write a two-part introduction using both facts.", "My name is Danish, and my favourite school activity is reading comics.", [evidence("States the name Danish.", "name is Danish"), evidence("Includes reading comics as the chosen activity.", "reading comics")]),
            ("Situation: Tara lends you a ruler after you ask. Visible goal: respond with gratitude and name the helpful act.", "Write one complete respectful response.", "Thank you, Tara, for lending me the ruler.", [evidence("Includes gratitude to Tara.", "Thank you, Tara", "thank you Tara"), evidence("Names lending the ruler.", "lending me the ruler", "for the ruler")]),
        ]),
        "independent": _open_set([
            ("Visible profile: Name: Mehul. Language learned at home: Marathi. Hobby: making paper boats.", "Create two complete sentences using all three volunteered facts.", "My name is Mehul. I learn Marathi at home and enjoy making paper boats.", [evidence("States Mehul's name and Marathi.", "name is Mehul", "Marathi"), evidence("Includes making paper boats.", "making paper boats")]),
            ("Situation: A classmate forgets your name and asks politely. Visible facts: your chosen name is Naina; you carry a green badge.", "Write a friendly complete reply using both facts.", "My name is Naina, and you can remember me by my green badge.", [evidence("States the name Naina.", "name is Naina"), evidence("Uses the green badge as a memory clue.", "green badge", "remember me")]),
        ]),
        "transfer": _open_set([
            ("Club card facts: Member: Iqbal. Club: Garden Team. Task: watering seedlings.", "Turn the card into a complete introduction for a new teammate.", "My name is Iqbal. I am on the Garden Team, and I water the seedlings.", [evidence("Includes Iqbal and Garden Team.", "name is Iqbal", "Garden Team"), evidence("Includes watering seedlings.", "water the seedlings", "watering seedlings")]),
            ("Event badge facts: Name: Lila. Role: welcome helper. Chosen greeting: Good morning.", "Write what Lila can say to introduce herself and welcome a visitor.", "Good morning. My name is Lila, and I am a welcome helper.", [evidence("Uses the greeting and name.", "Good morning", "name is Lila"), evidence("States the welcome-helper role.", "welcome helper")]),
        ]),
        "review": _open_set([
            ("Visible profile: Name: Omkar. Favourite tree: neem. Reason: it gives cool shade.", "Write a complete introduction plus one reason sentence.", "My name is Omkar. My favourite tree is neem because it gives cool shade.", [evidence("States Omkar and neem.", "name is Omkar", "tree is neem"), evidence("Includes the shade reason.", "gives cool shade", "because")]),
            ("Situation: A friend returns your labelled notebook. Visible goal: thank the friend and mention why the label helped.", "Compose one or two complete response sentences.", "Thank you for returning my notebook. The name label helped you identify it.", [evidence("Thanks the friend for returning it.", "Thank you", "returning my notebook"), evidence("Explains the label clue.", "name label", "identify it")]),
        ]),
        "cluster_id": f"{CHAPTER_ID}:identity_fragment_or_invention",
        "misconception": "The learner writes a fragment, omits a supplied identity detail, or invents private information that the visible profile never provides.",
        "remediation": "Highlight only volunteered facts, select name plus one safe detail, build a subject-and-action sentence, and check that no new private fact was added.",
        "support": _open_set([
            ("Profile: Name: Bina. Interest: puzzles.", "Write one complete introduction.", "My name is Bina, and I enjoy puzzles.", [evidence("Uses both visible profile facts.", "name is Bina", "enjoy puzzles")]),
            ("Profile: Name: Ali. Favourite colour: yellow.", "Create a clear two-fact sentence.", "My name is Ali, and my favourite colour is yellow.", [evidence("Includes Ali and yellow.", "name is Ali", "colour is yellow")]),
            ("Situation: Nikhil gives you a pencil.", "Write a complete gratitude response naming the act.", "Thank you, Nikhil, for giving me a pencil.", [evidence("Thanks Nikhil and names the pencil.", "Thank you, Nikhil", "giving me a pencil")]),
            ("Profile: Name: Juhi. School group: Blue House.", "Use only the supplied facts in one sentence.", "My name is Juhi, and I belong to Blue House.", [evidence("Includes Juhi and Blue House only.", "name is Juhi", "Blue House")]),
            ("Situation: A visitor asks your role. Card: Name: Rehan; Role: library helper.", "Write the complete safe reply.", "My name is Rehan, and I am a library helper.", [evidence("Uses the name and role.", "name is Rehan", "library helper")]),
        ]),
    },
]


EXTRA_DEPTH = {
    f"{CHAPTER_ID}:search_and_memory_chain": {
        "guided": [
            choice_task(
                "Mili forgets the word apron. The shopkeeper points to a hook, where a striped apron is hanging.",
                "Which sight helps Mili remember the word?",
                "the striped apron on the hook",
                ["the shopkeeper's shoes", "an empty shelf"],
            ),
            open_task(
                "Arun cannot recall the word paddle. His coach sends him to the boat shed, where he sees a flat blade beside an oar.",
                "Name the helper, the place, and the sight that ends Arun's search.",
                "The coach sends Arun to the boat shed, and the flat blade helps him remember paddle.",
                [
                    evidence("Names the helper.", "the coach sends Arun", "Arun's coach helps"),
                    evidence("Names the search place.", "to the boat shed", "the boat shed is the place"),
                    evidence("Names the memory sight.", "the flat blade helps", "seeing the flat blade"),
                ],
                ordered=True,
            ),
        ],
        "independent": _open_set([
            (
                "Pema forgets the word helmet. She asks the games teacher, opens the safety cupboard, and recognises it from a hard round cap.",
                "Retell Pema's search in order and explain why it ends.",
                "Pema asks the games teacher, opens the safety cupboard, sees the hard round cap, and remembers helmet.",
                [
                    evidence("States the first helper.", "asks the games teacher", "games teacher is asked first"),
                    evidence("States the next place.", "opens the safety cupboard", "checks the safety cupboard"),
                    evidence("Links the cap to remembering.", "hard round cap", "remembers helmet"),
                ],
            ),
            (
                "Jatin seeks the word ladle. His father suggests the kitchen drawer; a long-handled serving spoon inside brings the word back.",
                "Explain the route clue and the memory clue as two clear parts.",
                "Jatin follows his father's kitchen-drawer clue, and the long-handled spoon helps him remember ladle.",
                [
                    evidence("States the route clue.", "father's kitchen-drawer clue", "father suggests the kitchen drawer"),
                    evidence("States the memory clue.", "long-handled spoon helps", "long serving spoon brings the word back"),
                ],
            ),
        ], ordered=True),
        "transfer": _open_set([
            (
                "At a museum, Saba forgets the word fossil. A guide opens a case, and the stone shape of an old leaf helps her recall it.",
                "Use search-chain thinking to state the problem, helpful action, and result.",
                "Saba forgets fossil, the guide opens the case, and the old leaf shape in stone helps her remember the word.",
                [
                    evidence("States the forgotten word.", "forgets fossil", "cannot recall fossil"),
                    evidence("States the guide's action.", "guide opens the case", "the case is opened by the guide"),
                    evidence("Links the stone leaf to recall.", "old leaf shape in stone", "helps her remember"),
                ],
            )
        ], ordered=True),
    },
    f"{CHAPTER_ID}:name_and_polite_words": {
        "guided": [
            choice_task(
                "Rohan says, 'Could you repeat your name, please?' He asks in a gentle and respectful way.",
                "Which meaning fits respectful?",
                "showing care for another person",
                ["speaking without listening", "hiding a name card"],
            ),
            open_task(
                "A label identifies a lunch box because the printed name shows exactly whose box it is.",
                "Explain identifies and use the word in a different school sentence.",
                "Identifies means shows exactly which one. A red badge identifies the class monitor.",
                [
                    evidence("Explains the meaning.", "shows exactly which one", "tells which person or thing"),
                    evidence("Uses identifies freshly.", "red badge identifies the class monitor", "badge shows who the monitor is"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "When Neha recalls a tune, she brings the tune back into her mind after forgetting it for a while.",
                "Infer recalls and use it with a different remembered detail.",
                "Recalls means remembers again. Neha recalls the title after seeing the music card.",
                [
                    evidence("Explains recalls.", "means remembers again", "brings a memory back"),
                    evidence("Uses recalls in context.", "recalls the title", "remembers the title again"),
                ],
            ),
            (
                "The visitor introduces herself by saying her name and why she has come.",
                "Explain introduces and create a polite new example.",
                "Introduces means tells others who someone is. Kabir introduces his new teammate to the group.",
                [
                    evidence("Explains introduces.", "tells others who someone is", "helps people know a person"),
                    evidence("Creates a polite use.", "Kabir introduces his new teammate", "introduces a teammate to the group"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "A library card is personal because it belongs to one member and carries that member's chosen details.",
                "Explain personal, then use it without asking for a private detail.",
                "Personal means belonging to one person. My personal bookmark has my chosen initials on it.",
                [
                    evidence("Explains personal.", "belonging to one person", "made for one person"),
                    evidence("Uses a safe chosen detail.", "personal bookmark has my chosen initials", "chosen initials on my bookmark"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:visible_name_spellings": {
        "guided": [
            choice_task(
                "Candidates: address, adress, addres. The form needs the word for where a letter is sent.",
                "Which candidate is the standard spelling?",
                "address",
                ["adress", "addres"],
            ),
            open_task(
                "Printed chunks: po + lite. The clue describes a respectful request.",
                "Join the chunks and use the word in one complete sentence.",
                "The word is polite. Zoya makes a polite request for the ruler.",
                [
                    evidence("Builds the spelling.", "word is polite", "spell it polite"),
                    evidence("Uses the meaning.", "polite request for the ruler", "Zoya asks in a respectful way"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Missing letters: r e m e m b _ r. The clue means keep or bring back in the mind.",
                "Complete the word and write a sentence showing its meaning.",
                "The word is remember. I remember my partner's name from the badge.",
                [
                    evidence("Completes the spelling.", "word is remember", "spell it remember"),
                    evidence("Uses remember accurately.", "remember my partner's name", "name stays in my mind"),
                ],
            ),
            (
                "Scrambled letters: l a b e l. The clue names a small tag that gives information.",
                "Unscramble the word and use it with a named object.",
                "The word is label. The label shows that this bottle belongs to Aman.",
                [
                    evidence("Unscrambles the word.", "word is label", "spell it label"),
                    evidence("Uses label accurately.", "label shows that this bottle belongs", "bottle label names Aman"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Base word: friend. Add ly to describe a warm and kind manner.",
                "Build the new word and use it in a greeting sentence.",
                "The new word is friendly. The helper gives the visitor a friendly greeting.",
                [
                    evidence("Builds the new spelling.", "new word is friendly", "spell it friendly"),
                    evidence("Uses friendly in context.", "friendly greeting", "helper greets the visitor warmly"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:identity_word_jobs": {
        "guided": [
            choice_task(
                "The careful pupil prints her name clearly.",
                "Which word tells what the pupil does?",
                "prints",
                ["careful", "name"],
            ),
            open_task(
                "A blue badge marks the new helper.",
                "Give the jobs of badge, marks, blue, and new.",
                "Badge is a noun, marks is a verb, and blue and new are adjectives.",
                [
                    evidence("Labels badge.", "badge is a noun", "badge names a thing"),
                    evidence("Labels marks.", "marks is a verb", "marks shows the action"),
                    evidence("Labels blue.", "blue is an adjective", "blue tells what kind"),
                    evidence("Labels new.", "new is an adjective", "new describes the helper"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "The friendly guide welcomes quiet visitors.",
                "Classify guide, welcomes, friendly, and quiet.",
                "Guide is a noun, welcomes is a verb, and friendly and quiet are adjectives.",
                [
                    evidence("Labels guide.", "guide is a noun", "guide names a person"),
                    evidence("Labels welcomes.", "welcomes is a verb", "welcomes shows action"),
                    evidence("Labels friendly.", "friendly is an adjective", "friendly describes the guide"),
                    evidence("Labels quiet.", "quiet is an adjective", "quiet describes visitors"),
                ],
            ),
            (
                "An old photograph reminds Mira of her cheerful cousin.",
                "State the jobs of photograph, reminds, old, and cheerful.",
                "Photograph is a noun, reminds is a verb, and old and cheerful are adjectives.",
                [
                    evidence("Labels photograph.", "photograph is a noun", "photograph names a thing"),
                    evidence("Labels reminds.", "reminds is a verb", "reminds shows action"),
                    evidence("Labels old.", "old is an adjective", "old describes the photograph"),
                    evidence("Labels cheerful.", "cheerful is an adjective", "cheerful describes the cousin"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "The round token admits one eager player.",
                "Transfer the word-job check to token, admits, round, and eager.",
                "Token is a noun, admits is a verb, and round and eager are adjectives.",
                [
                    evidence("Labels token.", "token is a noun", "token names a thing"),
                    evidence("Labels admits.", "admits is a verb", "admits shows action"),
                    evidence("Labels round.", "round is an adjective", "round describes the token"),
                    evidence("Labels eager.", "eager is an adjective", "eager describes the player"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:polite_question_builder": {
        "guided": [
            choice_task(
                "Word set: may / your / I / borrow / pencil / please",
                "Which option forms the complete polite question?",
                "May I borrow your pencil, please?",
                ["Your pencil may please I borrow.", "may I your pencil borrow please."],
            ),
            open_task(
                "Word set: spell / could / surname / you / the / please",
                "Arrange every word as a polite question.",
                "Could you spell the surname, please?",
                [
                    evidence("Uses the question order.", "could you spell the surname please", "ask you to spell the surname"),
                    evidence("Uses a natural question ending.", "surname please?", "the surname please?"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Word set: card / this / whose / is / name",
                "Build the complete ownership question.",
                "Whose name card is this?",
                [
                    evidence("Uses the question order.", "whose name card is this", "ask whose card this is"),
                    evidence("Uses a natural question ending.", "card is this?", "is this?"),
                ],
            ),
            (
                "Line needing repair: please tell me how to say your name",
                "Add the correct sentence boundaries to the polite request.",
                "Please tell me how to say your name.",
                [
                    evidence("Keeps the polite request.", "please tell me how to say your name", "tell me how to say your name"),
                    evidence("Uses a natural statement ending.", "your name.", "say your name."),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Word set: may / map / the / see / we / please",
                "Use the same polite ordering pattern for a museum request.",
                "May we see the map, please?",
                [
                    evidence("Uses the polite question order.", "may we see the map please", "ask to see the map please"),
                    evidence("Uses a natural question ending.", "map please?", "the map please?"),
                ],
            )
        ]),
    },
    f"{CHAPTER_ID}:identity_sentence_writer": {
        "guided": [
            choice_task(
                "Profile card: Name: Sana. Chosen activity: caring for the class plant.",
                "Which introduction uses only the two visible facts?",
                "My name is Sana, and I care for the class plant.",
                ["Sana lives beside the school gate.", "The plant chose Sana's private address."],
                skills=[S["comprehension"]],
            ),
            open_task(
                "Profile card: Name: Joel. Team: Red House. Chosen task: keeping score.",
                "Write a clear introduction using all three volunteered facts.",
                "My name is Joel. I belong to Red House, and my chosen task is keeping score.",
                [
                    evidence("States the name.", "name is Joel", "I am Joel"),
                    evidence("States the team.", "belong to Red House", "Red House is my team"),
                    evidence("States the chosen task.", "task is keeping score", "I keep score"),
                ],
            ),
        ],
        "independent": _open_set([
            (
                "Profile card: Name: Farah. Favourite book type: riddles. Reason: they make her think carefully.",
                "Create an introduction and a reason sentence from the card.",
                "My name is Farah. I enjoy riddle books because they make me think carefully.",
                [
                    evidence("States Farah's name.", "name is Farah", "I am Farah"),
                    evidence("Names the book choice.", "enjoy riddle books", "favourite books are riddles"),
                    evidence("Gives the stated reason.", "make me think carefully", "riddles help careful thinking"),
                ],
            ),
            (
                "Situation card: Mohan finds your named water bottle. Your chosen reply must thank him and say how the label helped.",
                "Write the complete two-part reply.",
                "Thank you, Mohan, for finding my bottle. The name label showed that it was mine.",
                [
                    evidence("Thanks Mohan.", "thank you Mohan", "Mohan is thanked"),
                    evidence("Names the helpful act.", "finding my bottle", "found the bottle"),
                    evidence("Explains the label clue.", "name label showed it was mine", "label identified my bottle"),
                ],
            ),
        ]),
        "transfer": _open_set([
            (
                "Workshop card: Name: Esha. Role: clay-table helper. Job: share tools fairly. Greeting: Hello, everyone.",
                "Turn the card into a safe welcome introduction.",
                "Hello, everyone. My name is Esha, and I am the clay-table helper who shares tools fairly.",
                [
                    evidence("Uses the greeting.", "hello everyone", "greets everyone with hello"),
                    evidence("States Esha's role.", "name is Esha", "Esha is the clay-table helper"),
                    evidence("States the fair-sharing job.", "shares tools fairly", "job is to share the tools fairly"),
                ],
            )
        ]),
    },
}

LAUNCH_DEPTH = {
    f"{CHAPTER_ID}:search_and_memory_chain": {
        "transfer": _open_set(
            [
                (
                    "Farah forgets the word ladle while helping at lunch. The cook opens a drawer, and seeing the deep spoon with a long handle brings the word back.",
                    "State Farah's problem, the visible trigger, and the remembered word.",
                    "Farah forgets ladle, sees the deep long-handled spoon in the drawer, and then remembers the word ladle.",
                    [
                        evidence("States the forgotten word.", "forgets ladle", "cannot remember ladle"),
                        evidence("States the visible trigger.", "deep long-handled spoon in the drawer", "sees the deep spoon"),
                        evidence("States the result.", "remembers the word ladle", "then remembers ladle"),
                    ],
                )
            ],
            ordered=True,
        ),
        "review": _open_set(
            [
                (
                    "During art, Vihaan cannot recall palette. His friend points to a flat tray holding six paint colours, and the sight helps him remember.",
                    "Explain the helper, clue, and memory result in order.",
                    "Vihaan's friend points to the colour tray, and seeing it helps Vihaan remember palette.",
                    [
                        evidence("Names the helper action.", "friend points to the colour tray", "friend points"),
                        evidence("Names the visual clue.", "seeing the colour tray", "six paint colours"),
                        evidence("Names the remembered word.", "remember palette", "word palette"),
                    ],
                ),
                (
                    "Leena forgets sprout in the garden. The gardener shows a tiny green shoot pushing through soil, and Leena recalls the word.",
                    "Retell how Leena's word search ends.",
                    "The gardener shows Leena the tiny green shoot; that soil clue helps her remember sprout.",
                    [
                        evidence("Names the gardener action.", "gardener shows Leena"),
                        evidence("States the shown clue.", "tiny green shoot"),
                        evidence("Links the soil detail.", "that soil clue", "pushing through soil"),
                        evidence("States the result.", "remember sprout", "recalls the word sprout"),
                    ],
                ),
            ],
            ordered=True,
        ),
    },
    f"{CHAPTER_ID}:name_and_polite_words": {
        "transfer": _open_set(
            [
                (
                    "On a library card, A. Sen uses A as the initial for Asha. An initial is the first letter of a name.",
                    "Explain initial and use it for another fictional name.",
                    "An initial is the first letter of a name. R is the initial for the name Rohan.",
                    [
                        evidence("Explains initial.", "first letter of a name", "initial is the first letter"),
                        evidence("Uses initial accurately.", "R is the initial for the name Rohan", "initial for the name Rohan"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Naman says, 'Hello, I am Naman,' to a new classmate. To introduce yourself means to tell someone who you are politely.",
                    "State what introduce means and use it in a fresh school sentence.",
                    "Introduce means tell someone who you are. I introduce myself to the new art teacher.",
                    [
                        evidence("Explains introduce.", "tell someone who you are", "Introduce means"),
                        evidence("Uses introduce freshly.", "introduce myself to the new art teacher", "I introduce myself"),
                    ],
                ),
                (
                    "Ishita's family calls her Ishi at home. Ishi is a nickname, a friendly shorter name used with her permission.",
                    "Explain nickname and write one respectful fictional example.",
                    "A nickname is a friendly shorter name. Kabir agrees that his friends may call him Kabi.",
                    [
                        evidence("Explains nickname.", "nickname is a friendly shorter name", "friendly shorter name"),
                        evidence("Includes permission.", "Kabir agrees", "agrees that his friends may call him"),
                        evidence("Gives the example.", "call him Kabi", "Kabi"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:visible_name_spellings": {
        "transfer": _open_set(
            [
                (
                    "Visible chunks: wel + come. The notice uses the word that warmly receives a new visitor.",
                    "Join the chunks and use the completed word in a greeting.",
                    "The word is welcome. We welcome our new classmate to the reading club.",
                    [
                        evidence("Spells the target word.", "word is welcome", "spell it welcome"),
                        evidence("Uses welcome accurately.", "welcome our new classmate to the reading club", "We welcome"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Candidates: family, famly, familey. The profile sentence needs the word for people related at home.",
                    "Choose the standard spelling and use it in a complete sentence.",
                    "The standard spelling is family. My fictional profile says my family enjoys board games.",
                    [
                        evidence("Gives the standard spelling.", "standard spelling is family", "spell it family"),
                        evidence("Uses family in context.", "family enjoys board games", "my family"),
                    ],
                ),
                (
                    "Visible parts: class + mate. The clue means a person who learns in the same class.",
                    "Build the word and write a kind school sentence.",
                    "The word is classmate. I share the picture book with my classmate.",
                    [
                        evidence("Builds the joined spelling.", "word is classmate", "spell it classmate"),
                        evidence("Uses classmate kindly.", "share the picture book with my classmate", "my classmate"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:identity_word_jobs": {
        "transfer": _open_set(
            [
                (
                    "The friendly guide greets a nervous visitor.",
                    "Classify guide, greets, friendly, and nervous.",
                    "Guide is a noun, greets is a verb, and friendly and nervous are adjectives.",
                    [
                        evidence("Labels guide.", "Guide is a noun", "guide names a person"),
                        evidence("Labels greets.", "greets is a verb", "greets shows action"),
                        evidence("Labels friendly.", "friendly is an adjective", "friendly describes the guide"),
                        evidence("Labels nervous.", "nervous is an adjective", "nervous describes the visitor"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "A cheerful neighbour carries a heavy parcel.",
                    "Give the jobs of neighbour, carries, cheerful, and heavy.",
                    "Neighbour is a noun, carries is a verb, and cheerful and heavy are adjectives.",
                    [
                        evidence("Labels neighbour.", "Neighbour is a noun", "neighbour names a person"),
                        evidence("Labels carries.", "carries is a verb", "carries shows action"),
                        evidence("Labels cheerful.", "cheerful is an adjective", "cheerful describes the neighbour"),
                        evidence("Labels heavy.", "heavy is an adjective", "heavy describes the parcel"),
                    ],
                ),
                (
                    "The patient teacher reads a colourful card.",
                    "Classify teacher, reads, patient, and colourful in the card-reading sentence.",
                    "Teacher is a noun, reads is a verb, and patient and colourful are adjectives.",
                    [
                        evidence("Labels teacher.", "Teacher is a noun", "teacher names a person"),
                        evidence("Labels reads.", "reads is a verb", "reads shows action"),
                        evidence("Labels patient.", "patient is an adjective", "patient describes the teacher"),
                        evidence("Labels colourful.", "colourful is an adjective", "colourful describes the card"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:polite_question_builder": {
        "transfer": _open_set(
            [
                (
                    "Word set: may / I / know / your preferred name / please",
                    "Arrange the words as one polite question.",
                    "May I know your preferred name, please?",
                    [
                        evidence("Uses polite question order.", "May I know your preferred name", "May I know"),
                        evidence("Keeps the polite word.", "name, please?", "please?"),
                    ],
                )
            ]
        ),
        "review": _open_set(
            [
                (
                    "Unfinished question: could you repeat your name please",
                    "Add the capital, polite pause, and question ending.",
                    "Could you repeat your name, please?",
                    [
                        evidence("Uses the capital opening.", "Could you", "Could"),
                        evidence("Uses the complete polite question ending.", "repeat your name, please?", "name, please?"),
                    ],
                ),
                (
                    "Word set: how / do / you / spell / Mira",
                    "Build a complete respectful question from every word.",
                    "How do you spell Mira?",
                    [
                        evidence("Uses natural question order.", "How do you spell Mira", "How do you spell"),
                        evidence("Capitalizes the name.", "Mira?", "spell Mira"),
                        evidence("Uses the question mark.", "spell Mira?", "Mira?"),
                    ],
                ),
            ]
        ),
    },
    f"{CHAPTER_ID}:identity_sentence_writer": {
        "transfer": _open_set(
            [
                (
                    "Fictional profile: Name - Tara; favourite activity - making paper puppets; language used with grandparents - Marathi.",
                    "Write two complete sentences using all three profile facts.",
                    "Tara enjoys making paper puppets. She uses Marathi when speaking with her grandparents.",
                    [
                        evidence("Uses the name and activity.", "Tara enjoys making paper puppets", "Tara"),
                        evidence("Uses the language fact.", "uses Marathi", "Marathi"),
                        evidence("Uses the family context.", "speaking with her grandparents", "grandparents"),
                    ],
                )
            ],
            interaction="paragraph_text",
        ),
        "review": _open_set(
            [
                (
                    "Fictional welcome card: Arjun is new to the class, likes growing mint, and wants to join the garden team.",
                    "Write a welcoming response that uses two facts from the card.",
                    "Welcome, Arjun! You can grow mint with us when you join the garden team.",
                    [
                        evidence("Uses the person's name.", "Welcome, Arjun", "Arjun"),
                        evidence("Uses the mint interest.", "grow mint with us", "likes growing mint"),
                        evidence("Uses the team wish.", "join the garden team", "garden team"),
                    ],
                ),
                (
                    "Fictional profile: Zeba reads animal stories, celebrates her birthday in August, and prefers the nickname Zee.",
                    "Create two respectful sentences from all three facts.",
                    "Zeba, who prefers the nickname Zee, reads animal stories. Her birthday is in August.",
                    [
                        evidence("Uses the chosen nickname.", "prefers the nickname Zee", "nickname Zee"),
                        evidence("Uses the reading interest.", "reads animal stories", "animal stories"),
                        evidence("Uses the birthday month.", "birthday is in August", "August"),
                    ],
                ),
            ],
            interaction="paragraph_text",
        ),
    },
}

for _level in LEVELS:
    _existing_depth = EXTRA_DEPTH[_level["level_id"]]
    _launch_depth = LAUNCH_DEPTH[_level["level_id"]]
    _level["depth"] = {
        **_existing_depth,
        "transfer": [
            *_existing_depth.get("transfer", []),
            *_launch_depth["transfer"],
        ],
        "review": list(_launch_depth["review"]),
    }


def _assessment_form(label: str) -> list[dict[str, Any]]:
    if label == "a":
        return [
            choice_task("A clue revives Anu's memory, bringing back a word she had forgotten.", "Which meaning fits revives here?", "brings back", ["hides forever", "writes incorrectly"], skills=[S["word_context"]]),
            choice_task("Ravi asks the cook, while Mina asks the gardener. Only Mina sees the labelled herb.", "Who sees the labelled herb?", "Mina", ["Ravi", "the cook"], skills=[S["comprehension"]]),
            choice_task("First Pihu checks the desk, next she visits the office, and last she finds her tag.", "Which event happens second?", "She visits the office.", ["She checks the desk.", "She finds the tag."], skills=[S["sequence"]]),
            choice_task("Sentence frame: ___ may I borrow your eraser?", "Which polite word completes the request?", "Please", ["Never", "Suddenly"], skills=[S["word_use"]]),
            choice_task("Candidates: remember, remembar, rmember. The sentence needs the memory word.", "Which candidate is standard?", "remember", ["remembar", "rmember"], skills=[S["spelling"]]),
            choice_task("Helpful Sita returns the card.", "Which word shows the action?", "returns", ["helpful", "Sita"], skills=[S["word_jobs"]]),
            open_task("Word set: name / your / spell / please", "Arrange the polite statement.", "Please spell your name.", [evidence("Uses complete correct order.", "please spell your name"), evidence("Uses every word.", "spell", "name")], skills=[S["sentence_order"]]),
            open_task("Unfinished question: where is my name card", "Add the correct beginning and end mark.", "Where is my name card?", [evidence("Uses a capital beginning.", "Where"), evidence("Uses a question mark.", "?")], skills=[S["punctuation"]]),
            open_task("Profile facts: Name: Amol. Hobby: collecting smooth stones.", "Write one complete introduction with both facts.", "My name is Amol, and I enjoy collecting smooth stones.", [evidence("States Amol's name.", "name is Amol"), evidence("Includes collecting smooth stones.", "collecting smooth stones")], skills=[S["sentence"]]),
            open_task("Uma asks the guard, checks the shelf, and remembers atlas when she sees a book of maps.", "Retell the search and name the memory trigger.", "Uma asks the guard, checks the shelf, finds the book of maps, and remembers atlas.", [evidence("Orders guard before shelf.", "asks the guard", "checks the shelf"), evidence("Links maps to atlas.", "book of maps", "remembers atlas")], skills=[S["comprehension"], S["sequence"]], ordered=True),
            open_task("A polite reply is courteous, showing respect to the listener.", "Explain courteous and use a chapter word with the same idea.", "Courteous means respectful. A courteous child says please when asking for help.", [evidence("Explains respectful.", "means respectful"), evidence("Uses polite language accurately.", "says please", "asking for help")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
            open_task("Word set: where / did / Rina / keep / her / red ribbon", "Build and punctuate the complete question.", "Where did Rina keep her red ribbon?", [evidence("Uses correct question order.", "where did Rina keep her red ribbon", "Rina keep her red ribbon"), evidence("Uses capital and question mark.", "Where did Rina", "red ribbon?")], skills=[S["sentence_order"], S["punctuation"]]),
        ]
    return [
        choice_task("The badge is recognisable because its striped border makes it easy to know again.", "Which meaning fits recognisable?", "easy to know again", ["impossible to see", "ready to throw away"], skills=[S["word_context"]]),
        choice_task("Kavi asks the coach; Renu asks the librarian. The librarian shows Renu a marked folder.", "Who receives the marked-folder clue?", "Renu", ["Kavi", "the coach"], skills=[S["comprehension"]]),
        choice_task("Asha sees a clue, opens her notebook, and then recalls the forgotten word.", "What happens immediately before she recalls it?", "She opens her notebook.", ["She sees a clue.", "She closes the school."], skills=[S["sequence"]]),
        choice_task("Sentence frame: ___ you for returning my book.", "Which chapter phrase completes the response?", "Thank", ["Ask", "Forget"], skills=[S["word_use"]]),
        choice_task("Candidates: polite, polight, politee. The sentence describes a respectful request.", "Which spelling is standard?", "polite", ["polight", "politee"], skills=[S["spelling"]]),
        choice_task("The bright label identifies Noor's bag.", "Which word describes the label?", "bright", ["identifies", "bag"], skills=[S["word_jobs"]]),
        open_task("Word set: could / you / please / lend / me / the / blue crayon", "Arrange the polite request.", "Could you please lend me the blue crayon?", [evidence("Uses correct request order.", "could you please lend me", "please lend me"), evidence("Uses all supplied words.", "blue crayon", "lend me the blue crayon")], skills=[S["sentence_order"]]),
        open_task("Unfinished line: thank you for the helpful clue", "Repair the statement boundaries.", "Thank you for the helpful clue.", [evidence("Uses a capital beginning.", "Thank"), evidence("Uses a full stop.", ".")], skills=[S["punctuation"]]),
        open_task("Profile facts: Name: Simran. Favourite game: kho-kho.", "Write one complete introduction using both facts.", "My name is Simran, and my favourite game is kho-kho.", [evidence("States Simran's name.", "name is Simran"), evidence("Includes kho-kho as favourite game.", "favourite game is kho-kho")], skills=[S["sentence"]]),
        open_task("Veer asks his aunt, visits the balcony, and remembers basil after reading a plant label.", "Give the ordered route and final trigger.", "Veer asks his aunt, visits the balcony, reads the plant label, and remembers basil.", [evidence("Orders aunt before balcony.", "asks his aunt", "visits the balcony"), evidence("Links label to basil.", "plant label", "remembers basil")], skills=[S["comprehension"], S["sequence"]], ordered=True),
        open_task("The clue is familiar, meaning it was known before. Use familiar with a correctly spelled chapter word.", "State the meaning and write the new use.", "Familiar means known before. The familiar name helped Jatin remember his team.", [evidence("Explains known before.", "known before"), evidence("Uses familiar and remember accurately.", "familiar name", "remember his team")], skills=[S["word_context"], S["word_use"], S["spelling"]]),
        open_task("Word set: where / did / find / label / the / you", "Build the finished question with correct punctuation.", "Where did you find the label?", [evidence("Uses correct question order.", "where did you find the label"), evidence("Uses capital and question mark.", "Where", "?")], skills=[S["sentence_order"], S["punctuation"]]),
    ]


CONFIG = {
    "chapter_id": CHAPTER_ID,
    "chapter_no": 9,
    "title": "My Name",
    "unit_title": "Life Around Us",
    "source_url": SOURCE_URL,
    "extract_path": "/tmp/zidd-ncert-class2-3/eng_c2_ch09.txt",
    "source_anchors": [
        {"anchor_id": f"{CHAPTER_ID}:read:1-2", "section_label": "Let us read: search chain and memory trigger", "page_start": 1, "page_end": 2, "source_url": SOURCE_URL, "coverage_treatment": "zidd_equivalent", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:speak:3", "section_label": "Let us speak: name, identity, and remembering", "page_start": 3, "page_end": 3, "source_url": SOURCE_URL, "coverage_treatment": "guided_only", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:listen:4", "section_label": "Let us listen: outdoor and animal sound activity", "page_start": 4, "page_end": 4, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:write:5", "section_label": "Let us write: search recall and sentence completion", "page_start": 5, "page_end": 5, "source_url": SOURCE_URL, "coverage_treatment": "taught_and_assessed", "required_for_chapter_certification": True},
        {"anchor_id": f"{CHAPTER_ID}:do-project:6", "section_label": "Let us do and project: polite requests and name meaning", "page_start": 6, "page_end": 6, "source_url": SOURCE_URL, "coverage_treatment": "offline_group_activity", "required_for_chapter_certification": False},
        {"anchor_id": f"{CHAPTER_ID}:speak-blends:7", "section_label": "Let us speak: printed bl and pl blend words", "page_start": 7, "page_end": 7, "source_url": SOURCE_URL, "coverage_treatment": "textbook_companion", "required_for_chapter_certification": False},
    ],
    "levels": LEVELS,
    "assessment_forms": [_assessment_form("a"), _assessment_form("b")],
}


MANIFEST = build_manifest(CONFIG)
