"""Author the NCERT primary-English curriculum (Classes 2-5) as chapter modules.

This is the content-authoring source of truth. Each chapter's REAL content (its
Marigold unit name, grammar focus, vocabulary, comprehension, and writing tasks)
is hand-written in CURRICULUM below; this script expands each into the full
4-level chapter JSON + a gradable chapter test, and writes each class manifest
with milestone exams at 30% / 60% / 100% drawn from the chapters' own skills.

Re-run after editing CURRICULUM:  python scripts/build_school_curriculum.py
Chapter ids/levels are stable (c{N}_ch{NN}_...), so re-running is idempotent.
Class 2, Chapter 1 ("First Day at School") is kept hand-authored as the exemplar
and is NOT regenerated here; this script appends chapters 2..N and classes 3-5.
"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "content" / "data" / "school"

# Each chapter: real unit, genre, grammar focus, and authored items. The 4 levels
# (new words -> comprehension -> grammar -> writing) and a 5-item chapter test are
# expanded from these. Every item is deterministically gradable.
#   vocab_fill / comp_fill / grammar_fill / write_fill : (sentence_with___, answer, [accepts])
#   vocab_mc / comp_mc / grammar_mc                     : (question, answer, [options])
CURRICULUM: dict[int, dict] = {
    2: {
        "title": "Class 2 — English (Marigold)",
        "start_chapter": 2,   # ch01 is hand-authored; generate from ch02
        "chapters": [
            {
                "unit": "Haldi's Adventure", "genre": "story", "slug": "haldi",
                "grammar": "Action Words (Verbs)",
                "grammar_concept": "A doing word (verb) tells what someone does: run, jump, eat, fly.",
                "words": ["garden", "hen", "morning", "adventure"],
                "vocab_fill": ("A ___ gives us eggs.", "hen", []),
                "vocab_mc": ("Which word names a place with plants and flowers?", "garden", ["garden", "run", "happy"]),
                "comp_mc": ("In the story, Haldi the hen goes on an ___.", "adventure", ["adventure", "exam", "aeroplane"]),
                "grammar_mc": ("Which word is an action word?", "run", ["run", "table", "red"]),
                "grammar_fill": ("Birds ___ in the sky.", "fly", ["fly"]),
                "write_fill": ("In the garden, I can see a ___.", "flower", ["tree", "bird", "plant", "hen"]),
                "exemplars": ["The hen ran into the garden.", "I can run and jump in the park."],
            },
            {
                "unit": "I Am Lucky!", "genre": "poem", "slug": "lucky",
                "grammar": "Describing Words (Adjectives)",
                "grammar_concept": "A describing word (adjective) tells more about a thing: big, soft, green, happy.",
                "words": ["lucky", "wings", "tall", "soft"],
                "vocab_fill": ("A bird uses its ___ to fly.", "wings", ["wing"]),
                "vocab_mc": ("Which word means the opposite of 'short'?", "tall", ["tall", "small", "slow"]),
                "comp_mc": ("The poem says the child feels ___ to be who they are.", "lucky", ["lucky", "angry", "tired"]),
                "grammar_mc": ("Which word is a describing word?", "soft", ["soft", "run", "table"]),
                "grammar_fill": ("The rabbit has ___ fur.", "soft", ["white", "brown", "grey"]),
                "write_fill": ("I am lucky to have a ___ family.", "loving", ["kind", "big", "happy", "caring"]),
                "exemplars": ["I am lucky to have a kind teacher.", "The soft, white rabbit hopped away."],
            },
            {
                "unit": "A Smile", "genre": "poem", "slug": "smile",
                "grammar": "This, That, These, Those",
                "grammar_concept": "Use 'this/these' for things near you and 'that/those' for things far away.",
                "words": ["smile", "happy", "friend", "share"],
                "vocab_fill": ("When you are happy, you ___.", "smile", ["smiles"]),
                "vocab_mc": ("A person you like and play with is a ___.", "friend", ["friend", "stranger", "stone"]),
                "comp_mc": ("The poem says a smile grows when you ___ it.", "share", ["share", "hide", "throw"]),
                "grammar_mc": ("The book is far away. Which is correct?", "That is a book.", ["This is a book.", "That is a book.", "These is a book."]),
                "grammar_fill": ("___ is my pen, right here in my hand.", "This", ["this"]),
                "write_fill": ("I share my ___ with my friends.", "lunch", ["book", "toys", "pencil", "food"]),
                "exemplars": ["This is my new bag.", "Those are the tall trees near the gate."],
            },
            {
                "unit": "The Wind and the Sun", "genre": "story", "slug": "wind_sun",
                "grammar": "One and Many (Plurals)",
                "grammar_concept": "Add -s to make many: one cap, two caps; one box, two boxes.",
                "words": ["wind", "sun", "strong", "traveller"],
                "vocab_fill": ("The ___ blows the leaves off the trees.", "wind", []),
                "vocab_mc": ("Which one gives us light and heat?", "sun", ["sun", "wind", "cloud"]),
                "comp_mc": ("In the story, who finally made the traveller take off his coat?", "the sun", ["the sun", "the wind", "the rain"]),
                "grammar_mc": ("Which is the correct plural of 'box'?", "boxes", ["boxs", "boxes", "boxen"]),
                "grammar_fill": ("I see two ___ in the sky. (one bird, two ___)", "birds", []),
                "write_fill": ("On a windy day, I fly my ___.", "kite", ["kites"]),
                "exemplars": ["The sun is stronger than the wind.", "I have three books and two pens."],
            },
            {
                "unit": "Zoo Manners", "genre": "poem", "slug": "zoo",
                "grammar": "Asking Questions",
                "grammar_concept": "A question starts with a question word (what/where/who) and ends with '?'.",
                "words": ["zoo", "animal", "polite", "cage"],
                "vocab_fill": ("We see lions and tigers at the ___.", "zoo", []),
                "vocab_mc": ("A word that means well-behaved is ___.", "polite", ["polite", "rude", "lazy"]),
                "comp_mc": ("The poem teaches us to be ___ at the zoo.", "polite", ["polite", "noisy", "rough"]),
                "grammar_mc": ("Which one is a correct question?", "Where is the lion?", ["Where the lion is?", "Where is the lion?", "The lion where is?"]),
                "grammar_fill": ("___ is your favourite animal?", "What", ["what"]),
                "write_fill": ("At the zoo, I want to see a ___.", "tiger", ["lion", "monkey", "elephant", "bear"]),
                "exemplars": ["What time does the zoo open?", "Where do the monkeys live?"],
            },
        ],
    },
    3: {
        "title": "Class 3 — English (Marigold)",
        "start_chapter": 1,
        "chapters": [
            {
                "unit": "Good Morning", "genre": "poem", "slug": "good_morning",
                "grammar": "Naming Words (Nouns)",
                "grammar_concept": "A naming word names a person, place, animal, or thing: sun, tree, bird, school.",
                "words": ["morning", "sky", "breeze", "greet"],
                "vocab_fill": ("The sun rises in the ___.", "morning", []),
                "vocab_mc": ("A gentle wind is called a ___.", "breeze", ["breeze", "storm", "flood"]),
                "comp_mc": ("The poem greets the sun, the wind, and the ___.", "birds", ["birds", "cars", "shops"]),
                "grammar_mc": ("Which word is a naming word?", "tree", ["tree", "jump", "slowly"]),
                "grammar_fill": ("A ___ sings sweetly in the morning.", "bird", ["birds"]),
                "write_fill": ("Every morning I say good morning to my ___.", "mother", ["father", "teacher", "friend", "family"]),
                "exemplars": ["Good morning, dear sun and sky.", "The tree and the bird are naming words."],
            },
            {
                "unit": "The Magic Garden", "genre": "story", "slug": "magic_garden",
                "grammar": "Present Tense",
                "grammar_concept": "The present tense tells what happens now or every day. Add -s for he/she/it: she plants, they plant.",
                "words": ["garden", "seed", "bloom", "water"],
                "vocab_fill": ("We plant a ___ to grow a plant.", "seed", ["seeds"]),
                "vocab_mc": ("When a flower opens, we say it is in ___.", "bloom", ["bloom", "broom", "gloom"]),
                "comp_mc": ("In the story, the children look after the ___ together.", "garden", ["garden", "kitchen", "playground"]),
                "grammar_mc": ("Choose the correct present tense: 'She ___ the plants every day.'", "waters", ["water", "waters", "watered"]),
                "grammar_fill": ("Every day I ___ to school.", "walk", ["go", "run", "cycle"]),
                "write_fill": ("In my garden, I would grow a ___.", "rose", ["flower", "mango", "tomato", "tree"]),
                "exemplars": ["She waters the plants every morning.", "The seeds grow into bright flowers."],
            },
            {
                "unit": "Bird Talk", "genre": "poem", "slug": "bird_talk",
                "grammar": "Joining Words (and, but)",
                "grammar_concept": "Joining words link two ideas: 'and' adds, 'but' shows a difference.",
                "words": ["sparrow", "nest", "chirp", "feather"],
                "vocab_fill": ("A bird builds its ___ in a tree.", "nest", ["nests"]),
                "vocab_mc": ("The sound a small bird makes is a ___.", "chirp", ["chirp", "roar", "bark"]),
                "comp_mc": ("In the poem, the birds talk about ___.", "people", ["people", "rivers", "trains"]),
                "grammar_mc": ("Join with the right word: 'I like tea ___ not coffee.'", "but", ["and", "but", "because"]),
                "grammar_fill": ("I have a pen ___ a book.", "and", []),
                "write_fill": ("Birds are small ___ they can fly far.", "but", ["and"]),
                "exemplars": ["The sparrow chirps and builds its nest.", "It is small but very quick."],
            },
            {
                "unit": "Nina and the Baby Sparrows", "genre": "story", "slug": "nina",
                "grammar": "Was / Were",
                "grammar_concept": "Use 'was' for one (he/she/it was) and 'were' for many (they/you/we were).",
                "words": ["window", "kind", "worried", "safe"],
                "vocab_fill": ("Nina was ___ about the baby birds, so she helped them.", "worried", ["worry"]),
                "vocab_mc": ("A word that means out of danger is ___.", "safe", ["safe", "lost", "sad"]),
                "comp_mc": ("Nina helped the baby sparrows that lived near her ___.", "window", ["window", "school", "river"]),
                "grammar_mc": ("Choose the correct word: 'The birds ___ very small.'", "were", ["was", "were", "is"]),
                "grammar_fill": ("Yesterday I ___ very happy. (one person)", "was", []),
                "write_fill": ("I was ___ when I helped someone.", "glad", ["happy", "proud", "kind", "pleased"]),
                "exemplars": ["The baby birds were safe in the nest.", "Nina was kind to every animal."],
            },
            {
                "unit": "The Enormous Turnip", "genre": "story", "slug": "turnip",
                "grammar": "Opposites",
                "grammar_concept": "Opposite words have opposite meanings: big/small, pull/push, up/down.",
                "words": ["turnip", "enormous", "pull", "together"],
                "vocab_fill": ("Something very, very big is ___.", "enormous", []),
                "vocab_mc": ("To bring something towards you, you ___ it.", "pull", ["pull", "drop", "throw"]),
                "comp_mc": ("They could only move the turnip when they all worked ___.", "together", ["together", "alone", "slowly"]),
                "grammar_mc": ("What is the opposite of 'enormous'?", "tiny", ["tiny", "heavy", "round"]),
                "grammar_fill": ("The opposite of 'pull' is ___.", "push", []),
                "write_fill": ("When we work together, a hard job becomes ___.", "easy", ["simple", "quick", "fun"]),
                "exemplars": ["The enormous turnip was hard to pull.", "Together, the family pulled it out."],
            },
        ],
    },
    4: {
        "title": "Class 4 — English (Marigold)",
        "start_chapter": 1,
        "chapters": [
            {
                "unit": "Wake Up!", "genre": "poem", "slug": "wake_up",
                "grammar": "Present Continuous (-ing)",
                "grammar_concept": "Use 'is/are + verb-ing' for an action happening right now: the sun is rising, birds are singing.",
                "words": ["dawn", "stretch", "yawn", "fresh"],
                "vocab_fill": ("Early morning, when the sun comes up, is called ___.", "dawn", []),
                "vocab_mc": ("When you open your mouth wide because you are sleepy, you ___.", "yawn", ["yawn", "shout", "laugh"]),
                "comp_mc": ("The poem asks us to wake up and enjoy the ___ morning.", "fresh", ["fresh", "dark", "cold"]),
                "grammar_mc": ("Choose the present continuous: 'The birds ___ in the trees.'", "are singing", ["sing", "sang", "are singing"]),
                "grammar_fill": ("Right now, I ___ reading a book. (am + verb-ing)", "am", []),
                "write_fill": ("Early in the morning, I am ___.", "stretching", ["waking", "yawning", "smiling", "getting up"]),
                "exemplars": ["The sun is rising and the birds are singing.", "I am stretching my arms to wake up."],
            },
            {
                "unit": "Noses", "genre": "poem", "slug": "noses",
                "grammar": "Past Tense",
                "grammar_concept": "The past tense tells what already happened. Add -ed (jumped) or use special forms (go->went, eat->ate).",
                "words": ["nose", "sniff", "smell", "curious"],
                "vocab_fill": ("We use our nose to ___ a flower.", "smell", ["smells"]),
                "vocab_mc": ("A word that means wanting to know about things is ___.", "curious", ["curious", "tired", "afraid"]),
                "comp_mc": ("The funny poem wonders about all kinds of ___.", "noses", ["noses", "shoes", "hats"]),
                "grammar_mc": ("Choose the past tense: 'She ___ the rose.'", "smelled", ["smell", "smells", "smelled"]),
                "grammar_fill": ("Yesterday we ___ to the park. (go)", "went", []),
                "write_fill": ("Last Sunday, I ___ a beautiful garden.", "visited", ["saw", "found", "explored"]),
                "exemplars": ["Yesterday I smelled fresh bread in the kitchen.", "We went to the zoo and saw the lions."],
            },
            {
                "unit": "Run!", "genre": "poem", "slug": "run",
                "grammar": "Adverbs (How)",
                "grammar_concept": "An adverb tells HOW an action is done: quickly, slowly, loudly, carefully.",
                "words": ["race", "speed", "finish", "cheer"],
                "vocab_fill": ("The runners crossed the ___ line.", "finish", []),
                "vocab_mc": ("When a crowd shouts happily for you, they ___.", "cheer", ["cheer", "sleep", "frown"]),
                "comp_mc": ("The poem 'Run!' is full of energy and ___.", "speed", ["speed", "rain", "sleep"]),
                "grammar_mc": ("Which word tells HOW she ran?", "quickly", ["quickly", "garden", "happy"]),
                "grammar_fill": ("The tortoise walked ___. (in a slow way)", "slowly", []),
                "write_fill": ("In the race, I ran very ___.", "fast", ["quickly", "hard", "swiftly"]),
                "exemplars": ["She ran quickly to the finish line.", "He spoke loudly so everyone could hear."],
            },
            {
                "unit": "Why?", "genre": "poem", "slug": "why",
                "grammar": "Because / So",
                "grammar_concept": "'because' gives a reason; 'so' gives a result. I stayed home because it rained, so I read a book.",
                "words": ["question", "reason", "wonder", "answer"],
                "vocab_fill": ("When you ask 'why', you want a ___.", "reason", ["reasons"]),
                "vocab_mc": ("To think with curiosity about something is to ___.", "wonder", ["wonder", "sleep", "shout"]),
                "comp_mc": ("The child in the poem keeps asking lots of ___.", "questions", ["questions", "sweets", "songs"]),
                "grammar_mc": ("Join with a reason: 'I am happy ___ it is my birthday.'", "because", ["because", "but", "or"]),
                "grammar_fill": ("It was raining, ___ I took an umbrella.", "so", []),
                "write_fill": ("I like school because of my ___.", "friends", ["teacher", "books", "games"]),
                "exemplars": ["I stayed in because it was raining.", "The bell rang, so we went to class."],
            },
            {
                "unit": "The Giving Tree", "genre": "story", "slug": "giving_tree",
                "grammar": "Articles (a / an / the)",
                "grammar_concept": "Use 'a' before a consonant sound, 'an' before a vowel sound, and 'the' for a known thing.",
                "words": ["tree", "shade", "generous", "branch"],
                "vocab_fill": ("On a hot day, we sit in the cool ___ of a tree.", "shade", []),
                "vocab_mc": ("A person who loves to give is ___.", "generous", ["generous", "selfish", "lazy"]),
                "comp_mc": ("The story shows that the tree was very ___ to the boy.", "generous", ["generous", "angry", "scared"]),
                "grammar_mc": ("Choose the right word: '___ apple a day keeps illness away.'", "An", ["A", "An", "The"]),
                "grammar_fill": ("I sat under ___ big tree near my house.", "the", ["a"]),
                "write_fill": ("A tree gives us fruit, shade, and ___.", "oxygen", ["air", "wood", "shelter", "fruits"]),
                "exemplars": ["An old tree gave the boy sweet apples.", "The tree was a generous friend."],
            },
        ],
    },
    5: {
        "title": "Class 5 — English (Marigold)",
        "start_chapter": 1,
        "chapters": [
            {
                "unit": "Wonderful Waste!", "genre": "story", "slug": "waste",
                "grammar": "Mixed Tenses (Past, Present, Future)",
                "grammar_concept": "Match the tense to the time: yesterday (past), every day (present), tomorrow (future, use 'will').",
                "words": ["waste", "leftover", "useful", "recycle"],
                "vocab_fill": ("Food that is left after a meal is called ___.", "leftover", ["leftovers"]),
                "vocab_mc": ("To use waste again in a new way is to ___ it.", "recycle", ["recycle", "burn", "bury"]),
                "comp_mc": ("In the story, the cook turns leftover vegetables into a ___ dish.", "tasty", ["tasty", "burnt", "rotten"]),
                "grammar_mc": ("Which sentence is in the FUTURE tense?", "I will cook tomorrow.", ["I cooked yesterday.", "I cook daily.", "I will cook tomorrow."]),
                "grammar_fill": ("Tomorrow I ___ help my mother in the kitchen.", "will", []),
                "write_fill": ("We can reduce waste by learning to ___.", "recycle", ["reuse", "save", "compost"]),
                "exemplars": ["Yesterday we cooked, today we eat, and tomorrow we will share.", "Nothing is wasted if we use it wisely."],
            },
            {
                "unit": "Teamwork", "genre": "poem", "slug": "teamwork",
                "grammar": "Pronouns (he, she, it, they, we)",
                "grammar_concept": "A pronoun takes the place of a naming word: Ravi -> he; the girls -> they; the ball -> it.",
                "words": ["team", "together", "win", "support"],
                "vocab_fill": ("A group that plays or works together is a ___.", "team", ["teams"]),
                "vocab_mc": ("To help and encourage someone is to ___ them.", "support", ["support", "ignore", "blame"]),
                "comp_mc": ("The poem says a team can win only when members work ___.", "together", ["together", "alone", "quietly"]),
                "grammar_mc": ("Replace the names: 'Ravi and Sita played. ___ played well.'", "They", ["He", "She", "They"]),
                "grammar_fill": ("Meera is my friend. ___ is very kind. (she/he)", "She", ["she"]),
                "write_fill": ("My team wins because we ___ each other.", "support", ["help", "encourage", "trust"]),
                "exemplars": ["The players passed the ball, and they scored together.", "She is the captain, and we follow her."],
            },
            {
                "unit": "My Shadow", "genre": "poem", "slug": "shadow",
                "grammar": "Prepositions (Where)",
                "grammar_concept": "Prepositions tell where: in, on, under, behind, beside, between.",
                "words": ["shadow", "follow", "sunlight", "shape"],
                "vocab_fill": ("In bright sunlight, your ___ falls on the ground.", "shadow", ["shadows"]),
                "vocab_mc": ("To go after someone closely is to ___ them.", "follow", ["follow", "lead", "lose"]),
                "comp_mc": ("In the poem, the child's shadow always seems to ___ them.", "follow", ["follow", "vanish", "speak"]),
                "grammar_mc": ("The cat is hiding ___ the box (inside it).", "in", ["on", "in", "under"]),
                "grammar_fill": ("My shadow stands ___ me when the sun is behind. (in front of)", "before", ["beside", "near"]),
                "write_fill": ("On a sunny day, I see my shadow ___ the wall.", "on", []),
                "exemplars": ["My shadow walks beside me on the road.", "The book is on the table, under the lamp."],
            },
            {
                "unit": "The Lazy Frog", "genre": "poem", "slug": "lazy_frog",
                "grammar": "Reported Speech (basic)",
                "grammar_concept": "We can report what someone said: He said, 'I am tired' -> He said that he was tired.",
                "words": ["lazy", "pond", "complain", "effort"],
                "vocab_fill": ("A person who does not like to work is ___.", "lazy", []),
                "vocab_mc": ("To say you are unhappy about something is to ___.", "complain", ["complain", "praise", "thank"]),
                "comp_mc": ("The frog in the poem will not even try, because he is ___.", "lazy", ["lazy", "brave", "clever"]),
                "grammar_mc": ("Report it: He said, 'I am busy.' -> He said that he ___ busy.", "was", ["is", "was", "will be"]),
                "grammar_fill": ("She said, 'I am happy.' -> She said that she ___ happy.", "was", []),
                "write_fill": ("Instead of being lazy, we should make an ___.", "effort", ["attempt", "try"]),
                "exemplars": ["The lazy frog only sat by the pond and complained.", "He said that he would help us later."],
            },
            {
                "unit": "Class Discussion", "genre": "poem", "slug": "class_discussion",
                "grammar": "Conjunctions (although, while, or)",
                "grammar_concept": "Conjunctions link ideas: 'although' shows a contrast, 'while' shows two things at once, 'or' shows a choice.",
                "words": ["discuss", "opinion", "listen", "agree"],
                "vocab_fill": ("Your own idea or view about something is your ___.", "opinion", ["opinions"]),
                "vocab_mc": ("To talk about a topic with others is to ___ it.", "discuss", ["discuss", "ignore", "forget"]),
                "comp_mc": ("A good discussion needs us to speak AND to ___.", "listen", ["listen", "shout", "sleep"]),
                "grammar_mc": ("Choose the right word: 'I will read ___ you write.'", "while", ["while", "although", "or"]),
                "grammar_fill": ("You can have tea ___ coffee. (a choice)", "or", []),
                "write_fill": ("In a discussion, I always ___ to others first.", "listen", ["respond", "reply"]),
                "exemplars": ["Although I disagreed, I listened politely.", "We can meet today or tomorrow."],
            },
        ],
    },
}

# Per-chapter enrichment (keyed by slug) so every chapter carries a GENUINE second
# comprehension item (a cloze that tests understanding, not a recycled vocab fill)
# and grammar-APPLIED exemplars distinct from the chapter's general models. Merged
# onto each spec in main(); a chapter without an entry falls back gracefully.
#   comp_fill        : (sentence_with___, answer, [accepts])  — single-word answer
#   grammar_exemplars: [two short sentences showing the grammar point in use]
ENRICH: dict[str, dict] = {
    # ---- Class 2 ----
    "haldi": {
        "comp_fill": ("Haldi the hen sets off on a big ___ in the garden.", "adventure", []),
        "grammar_exemplars": ["The hen runs across the garden.", "Birds fly and sing in the morning."],
    },
    "lucky": {
        "comp_fill": ("In the poem, the child feels ___ for all that they have.", "lucky", ["thankful", "grateful"]),
        "grammar_exemplars": ["The soft, brown rabbit hops away.", "She has long, black hair."],
    },
    "smile": {
        "comp_fill": ("A smile grows bigger when you ___ it with others.", "share", []),
        "grammar_exemplars": ["This is my pen, right here.", "Those birds are flying far away."],
    },
    "wind_sun": {
        "comp_fill": ("The gentle ___ made the traveller take off his coat, not the wind.", "sun", []),
        "grammar_exemplars": ["I see two caps and three boxes.", "The girls play with their toys."],
    },
    "zoo": {
        "comp_fill": ("At the zoo, we must be gentle and ___ to the animals.", "polite", ["kind"]),
        "grammar_exemplars": ["Where do the tigers sleep?", "What does the elephant eat?"],
    },
    # ---- Class 3 ----
    "good_morning": {
        "comp_fill": ("The poem says good morning to the sun, the wind, and the ___.", "birds", ["bird"]),
        "grammar_exemplars": ["The sun, the tree, and the bird are naming words.", "My school is near the river."],
    },
    "magic_garden": {
        "comp_fill": ("In the story, the children grow a garden by planting a ___.", "seed", ["seeds"]),
        "grammar_exemplars": ["She waters the plants every day.", "They play in the garden after school."],
    },
    "bird_talk": {
        "comp_fill": ("In the poem, the birds chat about the ways of ___.", "people", []),
        "grammar_exemplars": ["I have a pen and a book.", "It is small but very fast."],
    },
    "nina": {
        "comp_fill": ("Nina felt ___, so she helped the baby sparrows.", "worried", ["kind"]),
        "grammar_exemplars": ["The baby birds were safe in the nest.", "Nina was very kind to them."],
    },
    "turnip": {
        "comp_fill": ("The huge turnip came out only when everyone pulled ___.", "together", []),
        "grammar_exemplars": ["Big is the opposite of small.", "We push the door, then pull it."],
    },
    # ---- Class 4 ----
    "wake_up": {
        "comp_fill": ("The poem tells us to wake up and enjoy the ___ morning.", "fresh", []),
        "grammar_exemplars": ["The birds are singing in the trees.", "I am stretching my arms."],
    },
    "noses": {
        "comp_fill": ("The funny poem wonders about all the different kinds of ___.", "noses", ["nose"]),
        "grammar_exemplars": ["Yesterday I smelled the roses.", "We went to the park and played."],
    },
    "run": {
        "comp_fill": ("The poem 'Run!' is full of energy and ___.", "speed", []),
        "grammar_exemplars": ["She ran quickly to the line.", "He spoke loudly and clearly."],
    },
    "why": {
        "comp_fill": ("The curious child in the poem keeps asking many ___.", "questions", ["question"]),
        "grammar_exemplars": ["I smiled because it was my birthday.", "It rained, so I stayed inside."],
    },
    "giving_tree": {
        "comp_fill": ("The story shows that the tree was very ___ to the boy.", "generous", ["kind", "giving"]),
        "grammar_exemplars": ["An apple fell from the tree.", "The tree gave the boy some shade."],
    },
    # ---- Class 5 ----
    "waste": {
        "comp_fill": ("The clever cook turns leftover vegetables into a ___ dish.", "tasty", ["delicious"]),
        "grammar_exemplars": ["Yesterday I cooked; today I eat; tomorrow I will share.", "She will visit us next week."],
    },
    "teamwork": {
        "comp_fill": ("The poem says a team wins only when its members work ___.", "together", []),
        "grammar_exemplars": ["Ravi and Sita played, and they won.", "Meera is kind; she helps everyone."],
    },
    "shadow": {
        "comp_fill": ("In the poem, the child's shadow seems to ___ them everywhere.", "follow", []),
        "grammar_exemplars": ["The cat hid under the box.", "The book is on the table."],
    },
    "lazy_frog": {
        "comp_fill": ("The frog will not even try, because he is so ___.", "lazy", []),
        "grammar_exemplars": ["He said that he was busy.", "She said that she would help."],
    },
    "class_discussion": {
        "comp_fill": ("A good discussion needs us to speak and also to ___.", "listen", []),
        "grammar_exemplars": ["Although I disagreed, I stayed calm.", "We can meet today or tomorrow."],
    },
}

_LEVELS = ["new_words", "understand", "grammar", "use"]


def _bx(bid, typ, sentence, hint, context, answer, accept=None, options=None, band="standard"):
    e = {"id": bid, "type": typ, "sentence": sentence, "hint": hint,
         "context": context, "answer_key": answer, "band": band}
    if accept is not None:
        e["accept"] = accept
    if options is not None:
        e["options"] = options
    return e


def _ti(tid, typ, prompt, answer, skill, accept=None, options=None):
    it = {"id": tid, "type": typ, "prompt": prompt, "answer_key": answer, "skill": skill}
    if accept is not None:
        it["accept"] = accept
    if options is not None:
        it["options"] = options
    return it


def build_chapter(class_no: int, chno: int, spec: dict) -> dict:
    cid = f"c{class_no}_ch{chno:02d}_{spec['slug']}"
    p = f"c{class_no}_ch{chno:02d}"
    words = ", ".join(spec["words"])
    unit = spec["unit"]
    vf, vmc = spec["vocab_fill"], spec["vocab_mc"]
    cmc = spec["comp_mc"]
    # A genuine SECOND comprehension item (fill_blank) so the comprehension level
    # and test actually probe understanding twice — not a recycled vocab fill.
    # Falls back to the comp MC's keyed phrase if a chapter hasn't authored one.
    cf = spec.get("comp_fill", (cmc[0].replace(cmc[1], "___"), cmc[1], []))
    gmc, gf = spec["grammar_mc"], spec["grammar_fill"]
    wf = spec["write_fill"]
    ex = spec["exemplars"]
    # Distinct models per level: the grammar level shows the grammar point applied;
    # other levels keep the chapter's general exemplars. Falls back to `ex`.
    gex = spec.get("grammar_exemplars", ex)
    nodes = [
        {
            "id": f"{p}_l1_new_words", "title": "New Words", "level": 1, "level_type": "text",
            "skill": f"Read and use the new words from '{unit}': {words}.",
            "teach_focus": f"What the new words from '{unit}' mean ({words}); use one correctly in a short phrase.",
            "success_criteria": "Uses two or more of the chapter's new words correctly.",
            "bridge_focus": "Name just one new word and what it means.",
            "prerequisites": [],
            "bridge_exercises": [
                _bx(f"{p}_l1_bx1", "fill_blank", vf[0], "a chapter word", "Uses a new word in context.", vf[1], vf[2], band="foundational"),
                _bx(f"{p}_l1_bx2", "multiple_choice", vmc[0], "think about the meaning", "Checks the meaning of a key word.", vmc[1], options=vmc[2]),
            ],
            "exemplars": ex,
        },
        {
            "id": f"{p}_l2_understand", "title": "Read and Understand", "level": 2, "level_type": "text",
            "skill": f"Understand the chapter '{unit}' and answer a simple question about it.",
            "teach_focus": f"The main idea and feeling of '{unit}'; answer a who/what/how question about it in one clear sentence.",
            "success_criteria": "Answers a simple question about the chapter in one clear sentence.",
            "bridge_focus": "Say in one sentence what the chapter is about.",
            "prerequisites": [f"{p}_l1_new_words"],
            "bridge_exercises": [
                _bx(f"{p}_l2_bx1", "multiple_choice", cmc[0], "remember the chapter", "Checks comprehension of the chapter.", cmc[1], options=cmc[2], band="foundational"),
                _bx(f"{p}_l2_bx2", "fill_blank", cf[0], "think about the chapter", "A second comprehension check.", cf[1], cf[2]),
            ],
            "exemplars": ex,
        },
        {
            "id": f"{p}_l3_grammar", "title": spec["grammar"], "level": 3, "level_type": "text",
            "skill": f"Use {spec['grammar'].lower()} correctly.",
            "teach_focus": spec["grammar_concept"],
            "success_criteria": f"Uses {spec['grammar'].lower()} correctly in a sentence.",
            "bridge_focus": f"Give one example of {spec['grammar'].lower()}.",
            "prerequisites": [f"{p}_l2_understand"],
            "bridge_exercises": [
                _bx(f"{p}_l3_bx1", "multiple_choice", gmc[0], spec["grammar"], "Identifies the grammar point.", gmc[1], options=gmc[2], band="foundational"),
                _bx(f"{p}_l3_bx2", "fill_blank", gf[0], spec["grammar"], "Produces the grammar point in a sentence.", gf[1], gf[2]),
            ],
            "exemplars": gex,
        },
        {
            "id": f"{p}_l4_use_it", "title": "Use It: Write a Sentence", "level": 4, "level_type": "text",
            "skill": f"Write one sentence of your own using ideas from '{unit}'.",
            "teach_focus": f"Write one clear sentence about '{unit}': who does what, with a capital letter and a full stop.",
            "success_criteria": "One complete sentence on the topic, with a capital and a full stop.",
            "bridge_focus": "Finish the sentence frame given.",
            "prerequisites": [f"{p}_l3_grammar"],
            "bridge_exercises": [
                _bx(f"{p}_l4_bx1", "fill_blank", wf[0], "your own idea", "Scaffolds writing with a frame to complete.", wf[1], wf[2], band="foundational"),
                _bx(f"{p}_l4_bx2", "fill_blank", gf[0], spec["grammar"], "A second frame to produce the chapter's grammar.", gf[1], gf[2]),
            ],
            "exemplars": ex,
        },
    ]
    test = {
        "id": f"{p}_test", "title": f"{unit}: Chapter Test", "kind": "chapter", "pass_mark": 0.6,
        "items": [
            _ti(f"{p}_t_i1", "multiple_choice", vmc[0], vmc[1], "new_words", options=vmc[2]),
            _ti(f"{p}_t_i2", "fill_blank", vf[0], vf[1], "new_words", accept=vf[2]),
            _ti(f"{p}_t_i3", "multiple_choice", cmc[0], cmc[1], "comprehension", options=cmc[2]),
            _ti(f"{p}_t_i4", "fill_blank", cf[0], cf[1], "comprehension", accept=cf[2]),
            _ti(f"{p}_t_i5", "multiple_choice", gmc[0], gmc[1], "grammar", options=gmc[2]),
            _ti(f"{p}_t_i6", "fill_blank", gf[0], gf[1], "grammar", accept=gf[2]),
        ],
    }
    return {
        "id": cid, "title": spec["unit"],
        "description": f"NCERT Class {class_no} English (Marigold): '{spec['unit']}'. New words, comprehension, {spec['grammar'].lower()}, and a writing task, closed by a chapter test.",
        "class_no": class_no, "chapter_no": chno, "ncert_unit": spec["unit"],
        "genre": spec["genre"], "nodes": nodes, "chapter_test": test,
    }, cid


def build_milestone(class_no, pct, chapter_specs_so_far, chapter_ids_so_far):
    """A cumulative milestone mixing GRAMMAR and COMPREHENSION across the chapters
    covered so far — not a grammar-only re-run of the chapter tests."""
    grammar_items, comp_items = [], []
    for chno, spec in chapter_specs_so_far:
        gmc = spec["grammar_mc"]
        gskill = spec["grammar"].split("(")[0].strip().lower().replace(" ", "_")
        grammar_items.append(("multiple_choice", gmc[0], gmc[1], gskill, gmc[2]))
        cmc = spec.get("comp_mc")   # the ch01 stand-in spec has no comp item
        if cmc:
            comp_items.append(("multiple_choice", cmc[0], cmc[1], "comprehension", cmc[2]))
    # Interleave grammar + comprehension so the exam samples both, newest chapters
    # last; cap to a reasonable length, keep at least 3.
    ordered = []
    for g, c in zip(grammar_items, comp_items):
        ordered.extend([g, c])
    leftover = grammar_items[len(comp_items):] + comp_items[len(grammar_items):]
    ordered.extend(leftover)
    ordered = ordered[:8]
    items = [
        _ti(f"c{class_no}_m{pct}_i{i+1}", typ, prompt, ans, skill, options=opts)
        for i, (typ, prompt, ans, skill, opts) in enumerate(ordered)
    ]
    return {
        "id": f"c{class_no}_milestone_{pct}", "title": f"Class {class_no} — {'Term Review' if pct == 100 else f'{pct}% Progress Check'}",
        "kind": "milestone", "at_percent": pct, "pass_mark": 0.6, "items": items,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for class_no, cdata in CURRICULUM.items():
        start = cdata["start_chapter"]
        chapter_ids: list[str] = []
        specs_indexed: list[tuple[int, dict]] = []
        # class 2 ch01 is hand-authored and kept; include its id + a stand-in spec
        if class_no == 2:
            chapter_ids.append("c2_ch01_first_day")
            specs_indexed.append((1, {"grammar_mc": ("Which word is a naming word?", "book", ["book", "run", "blue"]),
                                       "grammar": "Naming Words"}))
        for offset, spec in enumerate(cdata["chapters"]):
            chno = start + offset
            spec = {**spec, **ENRICH.get(spec["slug"], {})}   # merge per-chapter enrichment
            chapter, cid = build_chapter(class_no, chno, spec)
            # filename must start with 'class' to match the loader glob
            # (class*_ch*.json); the module id inside stays cN_chNN_slug.
            fname = f"class{class_no}_ch{chno:02d}_{spec['slug']}.json"
            (OUT / fname).write_text(json.dumps(chapter, indent=2, ensure_ascii=False))
            chapter_ids.append(cid)
            specs_indexed.append((chno, spec))
        total = len(chapter_ids)
        # milestones at 30/60/100% — cumulative over chapters reached by then
        milestones = []
        for pct in (30, 60, 100):
            done = max(1, round(total * pct / 100))
            milestones.append(build_milestone(class_no, pct, specs_indexed[:done], chapter_ids[:done]))
        manifest = {
            "class_no": class_no, "title": cdata["title"],
            "description": f"NCERT Class {class_no} English, organised by the Marigold chapters. Each chapter teaches new words, comprehension, a grammar focus, and writing, then a chapter test. Milestone reviews check cumulative learning at 30%, 60%, and 100% of the year.",
            "chapters": chapter_ids, "milestones": milestones,
        }
        (OUT / f"class{class_no}.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
        print(f"class {class_no}: {total} chapters, milestones at {[m['at_percent'] for m in milestones]}")


if __name__ == "__main__":
    main()
