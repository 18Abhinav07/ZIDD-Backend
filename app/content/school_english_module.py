"""School English module — 16 graded nodes for Indian primary grades 2-5.

A foundational written-English ladder aligned to the NCERT primary-English
arc (Marigold, classes 2-5): letter-sounds and naming words in grade 2, simple
tenses and describing words in grade 3, past tense / plurals / conjunctions and
the first paragraph in grade 4, and mixed tenses, prepositions, story- and
letter-writing in grade 5.

Content is DERIVED / PARAPHRASED from the prescribed syllabus, never copied
verbatim — IP-safe in a paid product. CEFR runs A1 -> B1 across the ladder.

Same CommNode shape and (MODULE_ID, MODULE_TITLE, MODULE_DESCRIPTION, *_NODES)
exports as comm_module, so the registry wires it in with a single MODULES entry
and the engine loop is unchanged.
"""
from app.content.comm_module import CommNode

SCHOOL_NODES: list[CommNode] = [
    # ---------- Grade 2 (A1): sounds, words, the first sentence ----------
    CommNode(
        id="c2_alphabet_sounds",
        title="Letters and Their Sounds",
        level=1,
        level_type="text",
        skill="Match a letter to its beginning sound and write a word that starts with it.",
        teach_focus="Letter-sound mapping; one clear example word per letter.",
        success_criteria="Writes a correct word starting with the given letter's sound.",
        bridge_focus="Just say one word that starts with the letter (e.g. b -> ball).",
        cefr="A1",
    ),
    CommNode(
        id="c2_naming_words",
        title="Naming Words (Nouns)",
        level=2,
        level_type="text",
        skill="Name people, animals, places, and things with the correct naming word.",
        teach_focus="Nouns as names; sort words into person/animal/place/thing.",
        success_criteria="Gives 3+ correct naming words for a picture or category.",
        bridge_focus="Name just one thing you can see around you.",
        cefr="A1",
        prerequisites=["c2_alphabet_sounds"],
    ),
    CommNode(
        id="c2_simple_sentence",
        title="Make a Simple Sentence",
        level=3,
        level_type="text",
        skill="Join a naming word and a doing word into one complete sentence.",
        teach_focus="A sentence needs who + what they do; capital letter and full stop.",
        success_criteria="One complete sentence with a capital letter and a full stop.",
        bridge_focus="Finish the sentence: 'The cat ___.'",
        cefr="A1",
        prerequisites=["c2_naming_words"],
    ),
    CommNode(
        id="c2_this_that",
        title="This, That, These, Those",
        level=4,
        level_type="text",
        skill="Point to near and far things using this/that/these/those correctly.",
        teach_focus="This/these for near, that/those for far; singular vs plural.",
        success_criteria="Uses this/that/these/those correctly in 2+ sentences.",
        bridge_focus="Say 'This is a ___' about something next to you.",
        cefr="A1",
        prerequisites=["c2_simple_sentence"],
    ),
    # ---------- Grade 3 (A1->A2): verbs, adjectives, tense, questions ----------
    CommNode(
        id="c3_action_words",
        title="Action Words (Verbs)",
        level=5,
        level_type="text",
        skill="Pick the action word that tells what someone is doing.",
        teach_focus="Verbs as doing words; choose the right verb for an action.",
        success_criteria="Writes a sentence using a correct, fitting action word.",
        bridge_focus="Tell me one thing you can DO (run, eat, jump).",
        cefr="A1",
        prerequisites=["c2_this_that"],
    ),
    CommNode(
        id="c3_describing_words",
        title="Describing Words (Adjectives)",
        level=6,
        level_type="text",
        skill="Add a describing word to tell more about a naming word.",
        teach_focus="Adjectives describe size/colour/feeling; place before the noun.",
        success_criteria="Uses a fitting adjective in a sentence ('a big red ball').",
        bridge_focus="Add one describing word to 'a ___ dog'.",
        cefr="A2",
        prerequisites=["c3_action_words"],
    ),
    CommNode(
        id="c3_present_tense",
        title="What Is Happening Now",
        level=7,
        level_type="text",
        skill="Use the present tense to say what is happening now or every day.",
        teach_focus="Present simple; add -s for he/she/it (she runs, they run).",
        success_criteria="A correct present-tense sentence with right verb form.",
        bridge_focus="Finish: 'Every day I ___.'",
        cefr="A2",
        prerequisites=["c3_describing_words"],
    ),
    CommNode(
        id="c3_questions",
        title="Asking Questions",
        level=8,
        level_type="text",
        skill="Form a simple question using what/where/who/when and a question mark.",
        teach_focus="Question words; word order; end with a question mark.",
        success_criteria="A correct question with a question word and a '?'.",
        bridge_focus="Turn 'It is a dog' into a question: 'Is it a dog?'",
        cefr="A2",
        prerequisites=["c3_present_tense"],
    ),
    # ---------- Grade 4 (A2->B1): past, plurals, joining, paragraph ----------
    CommNode(
        id="c4_past_tense",
        title="What Happened Before",
        level=9,
        level_type="text",
        skill="Use the past tense to tell about something that already happened.",
        teach_focus="Regular -ed and common irregulars (go->went, eat->ate).",
        success_criteria="A correct past-tense sentence about a finished action.",
        bridge_focus="Finish: 'Yesterday I ___.'",
        cefr="A2",
        prerequisites=["c3_questions"],
    ),
    CommNode(
        id="c4_plural_articles",
        title="One and Many; a / an / the",
        level=10,
        level_type="text",
        skill="Make plurals correctly and choose a, an, or the.",
        teach_focus="Plural -s/-es; 'an' before vowel sounds; 'the' for a known thing.",
        success_criteria="Correct plural and correct article in a sentence.",
        bridge_focus="Add a or an: '___ apple', '___ book'.",
        cefr="A2",
        prerequisites=["c4_past_tense"],
    ),
    CommNode(
        id="c4_conjunctions",
        title="Joining Words (and, but, because)",
        level=11,
        level_type="text",
        skill="Join two ideas into one sentence using and, but, or because.",
        teach_focus="and to add, but to contrast, because to give a reason.",
        success_criteria="One joined sentence using a fitting joining word.",
        bridge_focus="Join with 'and': 'I have a pen. I have a book.'",
        cefr="B1",
        prerequisites=["c4_plural_articles"],
    ),
    CommNode(
        id="c4_paragraph",
        title="Write a Short Paragraph",
        level=12,
        level_type="text",
        skill="Write 3-4 connected sentences on one topic.",
        teach_focus="One topic; sentences in order; each starts capital, ends full stop.",
        success_criteria="3+ sentences that stay on one topic and connect.",
        bridge_focus="Write just two sentences about your favourite animal.",
        cefr="B1",
        prerequisites=["c4_conjunctions"],
    ),
    # ---------- Grade 5 (B1): mixed tense, prepositions, story, letter ----------
    CommNode(
        id="c5_tenses_mix",
        title="Past, Present, and Future",
        level=13,
        level_type="text",
        skill="Choose the right tense for past, present, or future in a sentence.",
        teach_focus="Match time words to tense; 'will' for the future.",
        success_criteria="Three sentences, one each for past, present, future, all correct.",
        bridge_focus="Say what you WILL do tomorrow: 'Tomorrow I will ___.'",
        cefr="B1",
        prerequisites=["c4_paragraph"],
    ),
    CommNode(
        id="c5_prepositions",
        title="Where Things Are (Prepositions)",
        level=14,
        level_type="text",
        skill="Use in/on/under/between to say where something is.",
        teach_focus="Position words; match the preposition to the actual place.",
        success_criteria="A sentence with a correct preposition of place.",
        bridge_focus="Finish: 'The book is ___ the table.'",
        cefr="B1",
        prerequisites=["c5_tenses_mix"],
    ),
    CommNode(
        id="c5_story_writing",
        title="Write a Short Story",
        level=15,
        level_type="text",
        skill="Write a tiny story with a beginning, middle, and end.",
        teach_focus="A character, what happened, how it ended; events in order.",
        success_criteria="A short story with a clear start, middle, and ending.",
        bridge_focus="Tell just the beginning: who is the story about?",
        cefr="B1",
        prerequisites=["c5_prepositions"],
    ),
    CommNode(
        id="c5_letter_writing",
        title="Write a Friendly Letter",
        level=16,
        level_type="text",
        skill="Write a short informal letter with a greeting, message, and sign-off.",
        teach_focus="Dear ___, a short message, and 'Your friend, ___'.",
        success_criteria="A letter with a greeting, a clear message, and a sign-off.",
        bridge_focus="Just write the greeting line: 'Dear ___,'.",
        cefr="B1",
        prerequisites=["c5_story_writing"],
    ),
]

MODULE_ID = "school_english"
MODULE_TITLE = "School English (Grades 2-5)"
MODULE_DESCRIPTION = (
    "Foundational written English for young learners, aligned to the NCERT "
    "primary-English arc: letter sounds and naming words up through tenses, "
    "paragraphs, story- and letter-writing. A1 to B1."
)
MODULE_ORDER: list[str] = [n.id for n in SCHOOL_NODES]
_BY_ID: dict[str, CommNode] = {n.id: n for n in SCHOOL_NODES}


def get_node(node_id: str) -> CommNode:
    return _BY_ID[node_id]


def next_node(node_id: str) -> str | None:
    """Next node id in module order, or None if this was the last level."""
    idx = MODULE_ORDER.index(node_id)
    return MODULE_ORDER[idx + 1] if idx + 1 < len(MODULE_ORDER) else None
