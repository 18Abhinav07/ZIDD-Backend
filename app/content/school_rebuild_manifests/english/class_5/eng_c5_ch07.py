"""Authored deep manifest for Class 5 English Chapter 7.

The embedded baseline preserves the original Zidd-authored chapter manifest.
The expansion below supplies fresh deep-loop and misconception-remediation
cases before compilation.
"""

from __future__ import annotations

import json

from app.content.school_rebuild_manifests.english.class_5.eng_c5_ch02 import (
    _evidence,
    _open_activity,
    _task,
    _terms,
)


MANIFEST = json.loads(r'''{
  "schema_version": "school-class5-deep-manifest-v1",
  "chapter": {
    "chapter_id": "eng_c5_ch07",
    "chapter_no": 7,
    "title": "Gilli Danda",
    "book_title": "Santoor",
    "unit_title": "Ups and Downs",
    "source_url": "https://ncert.nic.in/textbook/pdf/eesa107.pdf",
    "source_note": "NCERT structural alignment only. All learner-facing passages, examples, questions, feedback authorities, and assessments are Zidd-authored originals.",
    "content_version": "2026-07-15.1",
    "certification_version": "2026-07-15.1",
    "authorship": {
      "zidd_authored_original": true,
      "textbook_body_or_questions_copied": false,
      "source_analysis_reference": "official NCERT structural exercise matrix reviewed 2026-07-15"
    }
  },
  "source_anchors": [
    {
      "anchor_id": "eng_c5_ch07:poem:1-3",
      "section_label": "Poem comprehension, mood, and imaginative response",
      "page_start": 1,
      "page_end": 3,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa107.pdf#page=1",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch07:morphology:4-5",
      "section_label": "Prefixes, nouns, and possessive pronouns",
      "page_start": 4,
      "page_end": 5,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa107.pdf#page=4",
      "coverage_treatment": "taught_and_assessed",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch07:game:6-8",
      "section_label": "Game explanation, rules, sequence, and safety",
      "page_start": 6,
      "page_end": 8,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa107.pdf#page=6",
      "coverage_treatment": "zidd_equivalent",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch07:wordwork:9-12",
      "section_label": "Dictionary, questions, spelling, opposites, and procedural application",
      "page_start": 9,
      "page_end": 12,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa107.pdf#page=9",
      "coverage_treatment": "textbook_companion",
      "required_for_chapter_certification": true
    },
    {
      "anchor_id": "eng_c5_ch07:facilitated:1-12",
      "section_label": "Facilitated recitation, listen-and-act, making, and group-play extensions",
      "page_start": 1,
      "page_end": 12,
      "source_url": "https://ncert.nic.in/textbook/pdf/eesa107.pdf#page=1",
      "coverage_treatment": "offline_group_activity",
      "required_for_chapter_certification": false
    }
  ],
  "levels": [
    {
      "level_id": "gilli-poetic-meaning",
      "title": "See the Game Through a Poem",
      "focus": "interpret imagery, comparison, mood, and nonliteral lines",
      "outcome": "Explain how poetic words create an image, mood, contrast, or value without treating imaginative language as a literal fact.",
      "skill_ids": [
        "reading.poetic_language",
        "reading.sentence_comprehension"
      ],
      "episode_kind": "comprehension_studio",
      "source_anchor_ids": [
        "eng_c5_ch07:poem:1-3"
      ],
      "connect": {
        "teaching_block": "Poems compress action and feeling into images, comparisons, repetition, and sound. You can practise recitation with a facilitator; here, use the visible lines to explain the poem's meaning.",
        "passage": "The small stick rose like a spark. The comparison makes its quick upward movement vivid; it does not say the stick became fire.",
        "prompt": "Separate the literal action from the image, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "gilli-poetic-meaning-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
        "passage": "At dusk the players mark a ring / A short stick waits beside the line / One tap sends the smaller piece / Up like a spark in fading shine.",
        "prompt": "Which image makes the action feel sudden and lively?",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "options": [
          "the ring is marked before play",
          "dusk is a time of day",
          "the piece rises like a spark",
          "the line remains on the ground"
        ],
        "accepted_answers": [
          "the piece rises like a spark"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "gilli-poetic-meaning-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "Dust lifts, feet race, voices call; / A measured turn belongs to all. / The longest hit may win a cheer, / But fair play keeps the game sincere.",
          "prompt": "What central idea connects the final two lines?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "dust is the only part of play",
            "the longest player always wins",
            "rules make cheering impossible",
            "fairness matters more than applause"
          ],
          "accepted_answers": [
            "fairness matters more than applause"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "gilli-poetic-meaning-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "The gilli spins above the lane, / Then drops beside the neem again. / We count the lengths from mark to fall, / And argue softly, one and all.",
          "prompt": "What does 'mark to fall' help the reader picture?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the height of the neem tree",
            "the distance from start to landing",
            "the number of players arguing",
            "the time until evening"
          ],
          "accepted_answers": [
            "the distance from start to landing"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-poetic-meaning-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "No screen records the dusty flight, / No whistle shines beneath a light; / Yet every child can tell the score / From careful eyes and rules agreed before.",
          "prompt": "What contrast is the speaker making?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "modern equipment",
                "simple game",
                "agreed rules"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "modern equipment",
            "simple game",
            "agreed rules"
          ],
          "model_answer": "The speaker contrasts modern equipment with a simple game governed by observation and agreed rules.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-poetic-meaning-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "A crooked twig becomes our bat, / A level patch becomes the ground. / We need no gate or painted stand / To make a joyful game be found.",
          "prompt": "How does the poem develop the idea of resourcefulness?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "ordinary materials",
                "used creatively",
                "joyful game"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "ordinary materials",
            "used creatively",
            "joyful game"
          ],
          "model_answer": "It shows ordinary materials and an open patch being used creatively to make a joyful game.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-poetic-meaning-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "The losing side collects the sticks, / The winners smooth the dusty place; / Tomorrow teams may change again, / So neither side should boast or chase.",
          "prompt": "Infer the attitude toward winning and losing.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "temporary results",
                "shared responsibility",
                "humility"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "temporary results",
            "shared responsibility",
            "humility"
          ],
          "model_answer": "The poem treats results as temporary and values shared responsibility and humility.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-poetic-meaning-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "Tap once, leap twice, the small stick flies; / A brown bird startles to the skies. / The players freeze, then laugh with care, / And wait until the path is clear.",
          "prompt": "Which event changes the mood, and how?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "startled bird",
                "cautious pause",
                "path clear"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "startled bird",
            "cautious pause",
            "path clear"
          ],
          "model_answer": "The startled bird changes excitement into cautious pause before the players laugh and resume safely.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-poetic-meaning-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "Grandmother draws a smaller ring / And shows the grip she knew at ten. / The children copy, miss, and try; / An old game starts its life again.",
          "prompt": "Explain the final line without treating it literally.",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "new generation",
                "learns",
                "old game continues"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "new generation",
            "learns",
            "old game continues"
          ],
          "model_answer": "The old game 'starts its life again' because a new generation learns and plays it.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-poetic-meaning-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "A rule remembered after loss / Is worth far more than winning wrong; / The shortest turn played honestly / Can keep the whole day's friendship strong.",
          "prompt": "What value does the speaker emphasise?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "honest play",
                "friendship",
                "unfair victory"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "honest play",
            "friendship",
            "unfair victory"
          ],
          "model_answer": "The speaker emphasises honest play and friendship over an unfair victory.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "gilli-poetic-meaning-misconception",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "misconception": "The learner retells only literal events or treats comparison and exaggeration as scientific fact.",
          "remediation": "Use two columns: what physically happens and what picture or feeling the poet creates; connect them with 'this suggests'.",
          "support_check_ids": [
            "gilli-poetic-meaning-bridge",
            "gilli-poetic-meaning-masterclass",
            "gilli-poetic-meaning-revision1",
            "gilli-poetic-meaning-revision2",
            "gilli-poetic-meaning-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "gilli-poetic-meaning-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "At dusk the players mark a ring / A short stick waits beside the line / One tap sends the smaller piece / Up like a spark in fading shine.",
          "prompt": "Which image makes the action feel sudden and lively?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the piece rises like a spark",
            "the ring is marked before play",
            "dusk is a time of day",
            "the line remains on the ground"
          ],
          "accepted_answers": [
            "the piece rises like a spark"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "gilli-poetic-meaning-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "Dust lifts, feet race, voices call; / A measured turn belongs to all. / The longest hit may win a cheer, / But fair play keeps the game sincere.",
          "prompt": "What central idea connects the final two lines?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "dust is the only part of play",
            "the longest player always wins",
            "fairness matters more than applause",
            "rules make cheering impossible"
          ],
          "accepted_answers": [
            "fairness matters more than applause"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "gilli-poetic-meaning-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "The gilli spins above the lane, / Then drops beside the neem again. / We count the lengths from mark to fall, / And argue softly, one and all.",
          "prompt": "What does 'mark to fall' help the reader picture?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "the height of the neem tree",
            "the distance from start to landing",
            "the number of players arguing",
            "the time until evening"
          ],
          "accepted_answers": [
            "the distance from start to landing"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "gilli-poetic-meaning-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "No screen records the dusty flight, / No whistle shines beneath a light; / Yet every child can tell the score / From careful eyes and rules agreed before.",
          "prompt": "What contrast is the speaker making?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "technology versus careful shared rules",
            "daylight versus complete darkness",
            "children versus all adults",
            "scores versus having no rules"
          ],
          "accepted_answers": [
            "technology versus careful shared rules"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "gilli-poetic-meaning-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Read the surrounding lines, identify the image or contrast, and state what it adds to the poem's meaning.",
          "passage": "A crooked twig becomes our bat, / A level patch becomes the ground. / We need no gate or painted stand / To make a joyful game be found.",
          "prompt": "How does the poem develop the idea of resourcefulness?",
          "skill_ids": [
            "reading.poetic_language",
            "reading.sentence_comprehension"
          ],
          "options": [
            "games require expensive equipment",
            "simple things can create a game",
            "crooked objects cannot be useful",
            "painted stands create joy by themselves"
          ],
          "accepted_answers": [
            "simple things can create a game"
          ]
        }
      }
    },
    {
      "level_id": "gilli-prefix-formation",
      "title": "Build Meaning with un- and re-",
      "focus": "form and explain prefixed words in context",
      "outcome": "Add un- or re- to a suitable base word, explain the changed meaning, and verify the new word in a complete context.",
      "skill_ids": [
        "vocab.word_formation",
        "vocab.chapter_word_usage"
      ],
      "episode_kind": "meaning_encounter",
      "source_anchor_ids": [
        "eng_c5_ch07:morphology:4-5"
      ],
      "connect": {
        "teaching_block": "A prefix changes meaning, not merely spelling. In this chapter, un- often means 'not' or reversal, while re- usually means 'again'. The resulting word must still be a real word that fits the context.",
        "passage": "Tie means fasten. Untie means reverse that action. Play means take part in a game. Replay means play again.",
        "prompt": "Say the base and changed meaning for both examples, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "gilli-prefix-formation-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
        "passage": "Base word: tie. New sentence: After the match, Kabir will untie the boundary rope.",
        "prompt": "Which explanation shows how the added letters change 'tie' into 'untie'?",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "to tie twice",
          "to tie again",
          "untie: to remove or loosen a tie or knot",
          "a person who owns rope"
        ],
        "accepted_answers": [
          "untie: to remove or loosen a tie or knot"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "gilli-prefix-formation-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: pack. New sentence: The team had to repack the kit after checking the bats.",
          "prompt": "Which explanation shows how the added letters change 'pack' into 'repack'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "to remove every item",
            "to refuse to pack",
            "repack: to pack again",
            "to pack without checking"
          ],
          "accepted_answers": [
            "repack: to pack again"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "gilli-prefix-formation-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: fair. New sentence: Changing the score secretly would be unfair.",
          "prompt": "Which explanation shows how the added letters change 'fair' into 'unfair'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "fair again",
            "more colourful",
            "unfair: not fair",
            "easy to measure"
          ],
          "accepted_answers": [
            "unfair: not fair"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-prefix-formation-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: play. New sentence: The class chose to replay the final round after a scoring mistake.",
          "prompt": "Which explanation shows how the added letters change 'play' into 'replay'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "replay",
                "to play again",
                "play"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "replay",
            "to play again",
            "play"
          ],
          "model_answer": "'replay' means to play again; the sentence uses that changed meaning accurately.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-prefix-formation-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: lock. New sentence: The monitor will unlock the games cupboard after lunch.",
          "prompt": "Which explanation shows how the added letters change 'lock' into 'unlock'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "unlock",
                "to open something that was locked",
                "lock"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "unlock",
            "to open something that was locked",
            "lock"
          ],
          "model_answer": "'unlock' means to open something that was locked; the sentence uses that changed meaning accurately.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-prefix-formation-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: write. New sentence: Mina will rewrite the game rules more clearly.",
          "prompt": "Which explanation shows how the added letters change 'write' into 'rewrite'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "rewrite",
                "to write again in an improved or corrected form",
                "write"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "rewrite",
            "to write again in an improved or corrected form",
            "write"
          ],
          "model_answer": "'rewrite' means to write again in an improved or corrected form; the sentence uses that changed meaning accurately.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-prefix-formation-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: safe. New sentence: A cracked stick is unsafe for play.",
          "prompt": "Which explanation shows how the added letters change 'safe' into 'unsafe'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "unsafe",
                "not safe",
                "safe"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "unsafe",
            "not safe",
            "safe"
          ],
          "model_answer": "'unsafe' means not safe; the sentence uses that changed meaning accurately.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-prefix-formation-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: build. New sentence: The players will rebuild the marker after the rain.",
          "prompt": "Which explanation shows how the added letters change 'build' into 'rebuild'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "rebuild",
                "to build again",
                "build"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "rebuild",
            "to build again",
            "build"
          ],
          "model_answer": "'rebuild' means to build again; the sentence uses that changed meaning accurately.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-prefix-formation-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: known. New sentence: The owner of the unmarked bag was unknown.",
          "prompt": "Which explanation shows how the added letters change 'known' into 'unknown'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "unknown",
                "not known",
                "known"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "unknown",
            "not known",
            "known"
          ],
          "model_answer": "'unknown' means not known; the sentence uses that changed meaning accurately.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "gilli-prefix-formation-misconception",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "misconception": "The learner attaches a prefix to any word or confuses 'not/reverse' with 'again'.",
          "remediation": "Run a three-step test: define the base, apply the prefix meaning, and use the new word in a sentence that proves the change.",
          "support_check_ids": [
            "gilli-prefix-formation-bridge",
            "gilli-prefix-formation-masterclass",
            "gilli-prefix-formation-revision1",
            "gilli-prefix-formation-revision2",
            "gilli-prefix-formation-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "gilli-prefix-formation-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: tie. New sentence: After the match, Kabir will untie the boundary rope.",
          "prompt": "Which explanation shows how the added letters change 'tie' into 'untie'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "untie: to remove or loosen a tie or knot",
            "to tie twice",
            "to tie again",
            "a person who owns rope"
          ],
          "accepted_answers": [
            "untie: to remove or loosen a tie or knot"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "gilli-prefix-formation-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: pack. New sentence: The team had to repack the kit after checking the bats.",
          "prompt": "Which explanation shows how the added letters change 'pack' into 'repack'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "to remove every item",
            "to refuse to pack",
            "to pack without checking",
            "repack: to pack again"
          ],
          "accepted_answers": [
            "repack: to pack again"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "gilli-prefix-formation-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: fair. New sentence: Changing the score secretly would be unfair.",
          "prompt": "Which explanation shows how the added letters change 'fair' into 'unfair'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "fair again",
            "unfair: not fair",
            "more colourful",
            "easy to measure"
          ],
          "accepted_answers": [
            "unfair: not fair"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "gilli-prefix-formation-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: play. New sentence: The class chose to replay the final round after a scoring mistake.",
          "prompt": "Which explanation shows how the added letters change 'play' into 'replay'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "replay: to play again",
            "not to play",
            "to watch only once",
            "to remove the rules"
          ],
          "accepted_answers": [
            "replay: to play again"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "gilli-prefix-formation-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Read the base meaning first, apply 'not' for un- or 'again' for re-, and then test the built word in the sentence.",
          "passage": "Base word: lock. New sentence: The monitor will unlock the games cupboard after lunch.",
          "prompt": "Which explanation shows how the added letters change 'lock' into 'unlock'?",
          "skill_ids": [
            "vocab.word_formation",
            "vocab.chapter_word_usage"
          ],
          "options": [
            "to lock again",
            "to paint the lock",
            "to count keys",
            "unlock: to open something that was locked"
          ],
          "accepted_answers": [
            "unlock: to open something that was locked"
          ]
        }
      }
    },
    {
      "level_id": "gilli-concrete-abstract",
      "title": "Objects, Feelings, and Ideas",
      "focus": "distinguish concrete and abstract nouns with evidence",
      "outcome": "Classify a noun as concrete or abstract by deciding whether it names a physical object or an idea, feeling, relationship, or quality.",
      "skill_ids": [
        "grammar.noun_verb_adjective"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch07:morphology:4-5"
      ],
      "connect": {
        "teaching_block": "Concrete nouns name physical people, places, animals, or things. Abstract nouns name ideas, qualities, feelings, and relationships that we recognise through thought or behaviour.",
        "passage": "A rope is concrete because it can be seen and touched. Fairness is abstract because it names an idea shown through decisions.",
        "prompt": "Apply the sensory test to both nouns, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "gilli-concrete-abstract-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
        "passage": "The smooth gilli rolled across the dust.",
        "prompt": "Classify 'gilli' and justify the classification with the sensory test.",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "options": [
          "abstract: it names a feeling",
          "verb: it shows rolling",
          "adjective: it describes dust",
          "a concrete noun: it names an object that can be seen and touched"
        ],
        "accepted_answers": [
          "a concrete noun: it names an object that can be seen and touched"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "gilli-concrete-abstract-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "Courage helped Leela take another turn after two misses.",
          "prompt": "Classify 'courage' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "options": [
            "concrete: it is the stick",
            "verb: it means take",
            "adjective: it describes the turn",
            "an abstract noun: it names a quality that cannot be touched or seen as an object"
          ],
          "accepted_answers": [
            "an abstract noun: it names a quality that cannot be touched or seen as an object"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "gilli-concrete-abstract-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "The players valued honesty when they counted the distance.",
          "prompt": "Classify 'honesty' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "options": [
            "concrete: it is a measuring rope",
            "verb: it means counted",
            "an abstract noun: it names a moral quality rather than a physical object",
            "adjective: it describes distance"
          ],
          "accepted_answers": [
            "an abstract noun: it names a moral quality rather than a physical object"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-concrete-abstract-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "A chalk line marked the edge of the field.",
          "prompt": "Classify 'line' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "line",
                "a concrete noun",
                "it names a visible mark on the ground"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "line",
            "a concrete noun",
            "it names a visible mark on the ground"
          ],
          "model_answer": "'line' is a concrete noun because it names a visible mark on the ground.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-concrete-abstract-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "Their friendship survived a disputed score.",
          "prompt": "Classify 'friendship' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "friendship",
                "an abstract noun",
                "it names a relationship, not something detected as a separate object"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "friendship",
            "an abstract noun",
            "it names a relationship, not something detected as a separate object"
          ],
          "model_answer": "'friendship' is an abstract noun because it names a relationship, not something detected as a separate object.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-concrete-abstract-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "The umpire held a measuring cord.",
          "prompt": "Classify 'cord' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "cord",
                "a concrete noun",
                "it can be seen and touched"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "cord",
            "a concrete noun",
            "it can be seen and touched"
          ],
          "model_answer": "'cord' is a concrete noun because it can be seen and touched.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-concrete-abstract-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "Patience kept Arun calm while he waited.",
          "prompt": "Classify 'patience' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "patience",
                "an abstract noun",
                "it names a quality shown through behaviour"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "patience",
            "an abstract noun",
            "it names a quality shown through behaviour"
          ],
          "model_answer": "'patience' is an abstract noun because it names a quality shown through behaviour.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-concrete-abstract-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "The wooden stick lay beside the ring.",
          "prompt": "Classify 'stick' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "stick",
                "a concrete noun",
                "it names a physical object"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "stick",
            "a concrete noun",
            "it names a physical object"
          ],
          "model_answer": "'stick' is a concrete noun because it names a physical object.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-concrete-abstract-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "Excitement spread when the final hit crossed the mark.",
          "prompt": "Classify 'excitement' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "excitement",
                "an abstract noun",
                "it names a feeling inferred from people, not a touchable object"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "excitement",
            "an abstract noun",
            "it names a feeling inferred from people, not a touchable object"
          ],
          "model_answer": "'excitement' is an abstract noun because it names a feeling inferred from people, not a touchable object.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "gilli-concrete-abstract-misconception",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "misconception": "The learner calls every difficult word abstract or confuses an adjective or action with the noun being classified.",
          "remediation": "Underline the target noun, ask what it names, and use the sensory test only after confirming its job in the sentence.",
          "support_check_ids": [
            "gilli-concrete-abstract-bridge",
            "gilli-concrete-abstract-masterclass",
            "gilli-concrete-abstract-revision1",
            "gilli-concrete-abstract-revision2",
            "gilli-concrete-abstract-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "gilli-concrete-abstract-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "The smooth gilli rolled across the dust.",
          "prompt": "Classify 'gilli' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "options": [
            "abstract: it names a feeling",
            "verb: it shows rolling",
            "a concrete noun: it names an object that can be seen and touched",
            "adjective: it describes dust"
          ],
          "accepted_answers": [
            "a concrete noun: it names an object that can be seen and touched"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "gilli-concrete-abstract-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "Courage helped Leela take another turn after two misses.",
          "prompt": "Classify 'courage' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "options": [
            "concrete: it is the stick",
            "verb: it means take",
            "adjective: it describes the turn",
            "an abstract noun: it names a quality that cannot be touched or seen as an object"
          ],
          "accepted_answers": [
            "an abstract noun: it names a quality that cannot be touched or seen as an object"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "gilli-concrete-abstract-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "The players valued honesty when they counted the distance.",
          "prompt": "Classify 'honesty' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "options": [
            "concrete: it is a measuring rope",
            "verb: it means counted",
            "adjective: it describes distance",
            "an abstract noun: it names a moral quality rather than a physical object"
          ],
          "accepted_answers": [
            "an abstract noun: it names a moral quality rather than a physical object"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "gilli-concrete-abstract-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "A chalk line marked the edge of the field.",
          "prompt": "Classify 'line' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "options": [
            "abstract: it names fairness",
            "verb: it means marked",
            "a concrete noun: it names a visible mark on the ground",
            "adjective: it describes chalk"
          ],
          "accepted_answers": [
            "a concrete noun: it names a visible mark on the ground"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "gilli-concrete-abstract-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Apply the sensory test, then check whether the target word is functioning as a noun in the sentence.",
          "passage": "Their friendship survived a disputed score.",
          "prompt": "Classify 'friendship' and justify the classification with the sensory test.",
          "skill_ids": [
            "grammar.noun_verb_adjective"
          ],
          "options": [
            "concrete: it is a scoreboard",
            "verb: it means survived",
            "an abstract noun: it names a relationship, not something detected as a separate object",
            "adjective: it describes score"
          ],
          "accepted_answers": [
            "an abstract noun: it names a relationship, not something detected as a separate object"
          ]
        }
      }
    },
    {
      "level_id": "gilli-possessive-pronouns",
      "title": "Make the Owner Clear",
      "focus": "replace owner-plus-noun phrases with possessive pronouns",
      "outcome": "Choose a possessive pronoun that agrees with the owner and replaces the owned noun without leaving an unclear reference.",
      "skill_ids": [
        "grammar.pronouns",
        "grammar.sentence_order"
      ],
      "episode_kind": "language_lab",
      "source_anchor_ids": [
        "eng_c5_ch07:morphology:4-5"
      ],
      "connect": {
        "teaching_block": "Possessive adjectives such as my, your, and their still need a noun. Possessive pronouns such as mine, yours, and theirs replace the whole owner-plus-noun phrase.",
        "passage": "This is our playing field becomes: This playing field is ours. 'Ours' replaces 'our playing field'.",
        "prompt": "Identify the owner and the replaced noun, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "gilli-possessive-pronouns-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
        "passage": "Ritu's gilli is red. The red one is ____.",
        "prompt": "Choose the possessive pronoun that refers clearly to Ritu, then explain the match.",
        "skill_ids": [
          "grammar.pronouns",
          "grammar.sentence_order"
        ],
        "options": [
          "hers",
          "her",
          "theirs",
          "his"
        ],
        "accepted_answers": [
          "hers"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "gilli-possessive-pronouns-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "Aman and Zoya brought the rope. The rope is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to Aman and Zoya, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "options": [
            "their",
            "ours",
            "his",
            "theirs"
          ],
          "accepted_answers": [
            "theirs"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "gilli-possessive-pronouns-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "I marked this turn in my notebook. The notebook is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to the speaker, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "options": [
            "my",
            "yours",
            "mine",
            "hers"
          ],
          "accepted_answers": [
            "mine"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-possessive-pronouns-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "You carried that bat. The bat is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to the listener, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "yours",
                "the listener",
                "the listener owns the bat"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "yours",
            "the listener",
            "the listener owns the bat"
          ],
          "model_answer": "The correct form is 'yours' because the listener owns the bat.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-possessive-pronouns-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "Our team chose this corner. The corner is ____ for the round.",
          "prompt": "Choose the possessive pronoun that refers clearly to our team, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "ours",
                "our team",
                "the speaker's group owns or claims it"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "ours",
            "our team",
            "the speaker's group owns or claims it"
          ],
          "model_answer": "The correct form is 'ours' because the speaker's group owns or claims it.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-possessive-pronouns-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "Vikram left his cap near the line. The cap is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to Vikram, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "his",
                "Vikram",
                "one male owner is named"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "his",
            "Vikram",
            "one male owner is named"
          ],
          "model_answer": "The correct form is 'his' because one male owner is named.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-possessive-pronouns-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "The girls made these scorecards. The cards are ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to the girls, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "theirs",
                "the girls",
                "the plural group owns the cards"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "theirs",
            "the girls",
            "the plural group owns the cards"
          ],
          "model_answer": "The correct form is 'theirs' because the plural group owns the cards.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-possessive-pronouns-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "Maya and I packed the kit. The kit is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to Maya and the speaker, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "ours",
                "Maya and the speaker",
                "the speaker belongs to the owning group"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "ours",
            "Maya and the speaker",
            "the speaker belongs to the owning group"
          ],
          "model_answer": "The correct form is 'ours' because the speaker belongs to the owning group.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-possessive-pronouns-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "That water bottle belongs to Neha. It is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to Neha, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "hers",
                "Neha",
                "the noun is replaced after naming one female owner"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "hers",
            "Neha",
            "the noun is replaced after naming one female owner"
          ],
          "model_answer": "The correct form is 'hers' because the noun is replaced after naming one female owner.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "gilli-possessive-pronouns-misconception",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "misconception": "The learner chooses a form by the owned object rather than the owner, or uses my/your/their without a following noun.",
          "remediation": "Draw an arrow from owner to object, select the owner form, and run the replacement test: the pronoun must stand without the noun.",
          "support_check_ids": [
            "gilli-possessive-pronouns-bridge",
            "gilli-possessive-pronouns-masterclass",
            "gilli-possessive-pronouns-revision1",
            "gilli-possessive-pronouns-revision2",
            "gilli-possessive-pronouns-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "gilli-possessive-pronouns-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "Ritu's gilli is red. The red one is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to Ritu, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "options": [
            "her",
            "theirs",
            "his",
            "hers"
          ],
          "accepted_answers": [
            "hers"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "gilli-possessive-pronouns-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "Aman and Zoya brought the rope. The rope is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to Aman and Zoya, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "options": [
            "their",
            "ours",
            "theirs",
            "his"
          ],
          "accepted_answers": [
            "theirs"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "gilli-possessive-pronouns-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "I marked this turn in my notebook. The notebook is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to the speaker, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "options": [
            "mine",
            "my",
            "yours",
            "hers"
          ],
          "accepted_answers": [
            "mine"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "gilli-possessive-pronouns-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "You carried that bat. The bat is ____.",
          "prompt": "Choose the possessive pronoun that refers clearly to the listener, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "options": [
            "your",
            "mine",
            "theirs",
            "yours"
          ],
          "accepted_answers": [
            "yours"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "gilli-possessive-pronouns-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Name the owner, decide whether the owner is speaker, listener, one person, or a group, and check whether the noun is being replaced.",
          "passage": "Our team chose this corner. The corner is ____ for the round.",
          "prompt": "Choose the possessive pronoun that refers clearly to our team, then explain the match.",
          "skill_ids": [
            "grammar.pronouns",
            "grammar.sentence_order"
          ],
          "options": [
            "our",
            "theirs",
            "his",
            "ours"
          ],
          "accepted_answers": [
            "ours"
          ]
        }
      }
    },
    {
      "level_id": "gilli-game-procedure",
      "title": "Explain a Game People Can Actually Play",
      "focus": "present setup, turns, goal, fairness, and safety in order",
      "outcome": "Write a usable game or activity procedure with supplied equipment, ordered turns, goal or completion condition, and necessary safety rules.",
      "skill_ids": [
        "reading.event_sequence",
        "writing.procedure"
      ],
      "episode_kind": "application_mission",
      "source_anchor_ids": [
        "eng_c5_ch07:game:6-8"
      ],
      "connect": {
        "teaching_block": "A game explanation is a procedure, not a loose description. It lets a new player set up, take a legal turn, know when play ends, and avoid preventable harm.",
        "passage": "Set two markers ten steps apart. One player rolls the ball; the partner stops it behind the far marker. Waiting players remain beside the start line.",
        "prompt": "Locate setup, turn, and safety, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "gilli-game-procedure-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
        "passage": "Game packet: four players, one soft ball, six floor markers. Players throw from behind a line and collect only after every throw.",
        "prompt": "Write a safe setup and turn procedure.",
        "skill_ids": [
          "reading.event_sequence"
        ],
        "options": [
          "collect while others throw",
          "set markers, throw once each, collect after all throws",
          "use a hard ball near the group",
          "omit the starting line"
        ],
        "accepted_answers": [
          "set markers, throw once each, collect after all throws"
        ]
      },
      "guided_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Gilli-danda practice uses pre-smoothed equipment prepared by an adult. The striking zone is clear, and waiting players stand behind a marked boundary.",
          "prompt": "Explain the safety procedure before the first turn.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "equipment",
              "description": "Includes adult-checked equipment.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "space",
              "description": "Clears the striking area.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "waiting",
              "description": "Positions waiting players safely.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "equipment",
              "description": "Includes adult-checked equipment.",
              "any_of": [
                "adult checks",
                "pre-smoothed"
              ]
            },
            {
              "id": "space",
              "description": "Clears the striking area.",
              "any_of": [
                "clear striking zone",
                "area empty"
              ]
            },
            {
              "id": "waiting",
              "description": "Positions waiting players safely.",
              "any_of": [
                "behind boundary"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "adult checks",
            "pre-smoothed",
            "clear striking zone",
            "area empty",
            "behind boundary"
          ],
          "model_answer": "An adult checks the pre-smoothed equipment, players clear the striking zone, and everyone waiting stays behind the boundary. Play begins only after the striker confirms the area is empty.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "equipment",
            "space",
            "waiting"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Scoring rule: measure from the start mark to the landing point with the same cord each time. If players disagree, repeat the measurement with both captains watching.",
          "prompt": "Write the scoring procedure and dispute step.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "measure",
              "description": "Keeps measurement consistent.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "record",
              "description": "Includes score recording.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "dispute",
              "description": "Gives the fair review step.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "measure",
              "description": "Keeps measurement consistent.",
              "any_of": [
                "same start mark",
                "same cord"
              ]
            },
            {
              "id": "record",
              "description": "Includes score recording.",
              "any_of": [
                "record result"
              ]
            },
            {
              "id": "dispute",
              "description": "Gives the fair review step.",
              "any_of": [
                "both captains",
                "repeat measurement",
                "confirm"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "same start mark",
            "same cord",
            "record result",
            "both captains",
            "repeat measurement",
            "confirm"
          ],
          "model_answer": "Measure every landing from the same start mark with the same cord. Record the result. If there is a disagreement, both captains watch a repeated measurement before the score is confirmed.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "measure",
            "record",
            "dispute"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Relay setup: two equal teams, one baton per team, a turning cone, and a no-pushing rule. The next runner starts only after receiving the baton.",
          "prompt": "Present the relay rules in a logical order.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "setup",
              "description": "Includes teams, baton, and cone.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "sequence",
              "description": "Orders running and handover.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety",
              "description": "States the no-pushing rule.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setup",
              "description": "Includes teams, baton, and cone.",
              "any_of": [
                "two equal teams",
                "baton",
                "turning cone"
              ]
            },
            {
              "id": "sequence",
              "description": "Orders running and handover.",
              "any_of": [
                "around cone",
                "hand over",
                "next starts"
              ]
            },
            {
              "id": "safety",
              "description": "States the no-pushing rule.",
              "any_of": [
                "no pushing"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "two equal teams",
            "baton",
            "turning cone",
            "around cone",
            "hand over",
            "next starts",
            "no pushing"
          ],
          "model_answer": "Make two equal teams and place a turning cone. Give each first runner a baton. Runners go around the cone and hand over the baton before the next runner starts. No one may push.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setup",
            "sequence",
            "safety"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Circle pass: six players form a wide circle. They pass a beanbag clockwise. A dropped bag is picked up by the same player while others pause.",
          "prompt": "Write the complete play procedure without inventing a winner.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "setup",
              "description": "Uses the supplied formation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "play",
              "description": "Explains direction and drop rule.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Does not invent missing rules.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setup",
              "description": "Uses the supplied formation.",
              "any_of": [
                "six players",
                "wide circle"
              ]
            },
            {
              "id": "play",
              "description": "Explains direction and drop rule.",
              "any_of": [
                "clockwise",
                "same player",
                "others pause"
              ]
            },
            {
              "id": "limit",
              "description": "Does not invent missing rules.",
              "any_of": [
                "no winning condition",
                "not invented"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "six players",
            "wide circle",
            "clockwise",
            "same player",
            "others pause",
            "no winning condition",
            "not invented"
          ],
          "model_answer": "Six players form a wide circle and pass the beanbag clockwise. If it drops, everyone pauses while the same player picks it up, then passing resumes. The packet gives no winning condition, so none should be invented.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setup",
            "play",
            "limit"
          ]
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "A board path has twenty squares. Each player rolls once per turn, moves that number, and follows any instruction on the landing square. The first exact roll to square twenty wins.",
          "prompt": "Explain setup, turn, and win condition.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "setup",
              "description": "Places counters correctly.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "turn",
              "description": "Explains roll, move, and instruction.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "win",
              "description": "States the exact-roll condition.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setup",
              "description": "Places counters correctly.",
              "any_of": [
                "before square one",
                "counter"
              ]
            },
            {
              "id": "turn",
              "description": "Explains roll, move, and instruction.",
              "any_of": [
                "roll once",
                "move",
                "landing instruction"
              ]
            },
            {
              "id": "win",
              "description": "States the exact-roll condition.",
              "any_of": [
                "square twenty",
                "exact roll"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "before square one",
            "counter",
            "roll once",
            "move",
            "landing instruction",
            "square twenty",
            "exact roll"
          ],
          "model_answer": "Place each counter before square one. On a turn, roll once, move that many squares, and follow the landing instruction. A player wins only by reaching square twenty with an exact roll.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setup",
            "turn",
            "win"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "A quiet classroom game uses word cards. One player describes a word without saying it; teammates have thirty seconds to guess. No mocking is allowed.",
          "prompt": "Write a fair turn procedure and behaviour rule.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "turn",
              "description": "Orders card, timer, description, and guessing.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "constraint",
              "description": "Keeps the target word unspoken.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "respect",
              "description": "Includes the behaviour rule.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "turn",
              "description": "Orders card, timer, description, and guessing.",
              "any_of": [
                "word card",
                "thirty-second timer",
                "describe",
                "guess"
              ]
            },
            {
              "id": "constraint",
              "description": "Keeps the target word unspoken.",
              "any_of": [
                "without saying word"
              ]
            },
            {
              "id": "respect",
              "description": "Includes the behaviour rule.",
              "any_of": [
                "no mocking",
                "incorrect guess"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "word card",
            "thirty-second timer",
            "describe",
            "guess",
            "without saying word",
            "no mocking",
            "incorrect guess"
          ],
          "model_answer": "Choose one describer, show that player a word card, and start the thirty-second timer. Teammates may guess while the describer avoids saying the word. End the turn when time finishes, and never mock an incorrect guess.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "turn",
            "constraint",
            "respect"
          ]
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Skipping challenge: one rope, one clear lane, and pairs taking turns. The rope turner stops immediately if anyone enters the lane.",
          "prompt": "Explain the safety-first procedure.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "check",
              "description": "Checks the lane first.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "turn",
              "description": "Keeps one pair active and others outside.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "stop",
              "description": "States the interruption response.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "check",
              "description": "Checks the lane first.",
              "any_of": [
                "lane clear"
              ]
            },
            {
              "id": "turn",
              "description": "Keeps one pair active and others outside.",
              "any_of": [
                "one pair",
                "wait outside"
              ]
            },
            {
              "id": "stop",
              "description": "States the interruption response.",
              "any_of": [
                "stop immediately",
                "clear again"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "lane clear",
            "one pair",
            "wait outside",
            "stop immediately",
            "clear again"
          ],
          "model_answer": "Check that the lane is clear, then one pair begins while others wait outside it. If anyone enters, the rope turner stops immediately. The next pair starts only after the lane is clear again.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "check",
            "turn",
            "stop"
          ]
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "A fair game explanation names equipment, player count, setup, one turn, scoring or goal, and safety. Missing rules are marked as missing rather than invented.",
          "prompt": "State the six-part explanation checklist in order.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "start",
              "description": "Names equipment, players, and setup.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "play",
              "description": "Explains turn and goal.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety",
              "description": "Includes safety.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Marks missing rules.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "start",
              "description": "Names equipment, players, and setup.",
              "any_of": [
                "equipment",
                "players",
                "setup"
              ]
            },
            {
              "id": "play",
              "description": "Explains turn and goal.",
              "any_of": [
                "turn",
                "scoring",
                "goal"
              ]
            },
            {
              "id": "safety",
              "description": "Includes safety.",
              "any_of": [
                "safety"
              ]
            },
            {
              "id": "limit",
              "description": "Marks missing rules.",
              "any_of": [
                "missing",
                "not invent"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 24,
          "relevance_terms": [
            "equipment",
            "players",
            "setup",
            "turn",
            "scoring",
            "goal",
            "safety",
            "missing"
          ],
          "model_answer": "Name equipment and players, describe the setup, explain a turn, state the supplied scoring or goal, include safety, and identify any rule the source does not provide.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "start",
            "play",
            "safety",
            "limit"
          ]
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "gilli-game-procedure-misconception",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "misconception": "The learner lists equipment or excitement but omits starting positions, turn order, end condition, fairness, or safety.",
          "remediation": "Rebuild the explanation in fixed boxes and test it by asking whether a new player could begin and finish without asking another question.",
          "support_check_ids": [
            "gilli-game-procedure-bridge",
            "gilli-game-procedure-masterclass",
            "gilli-game-procedure-revision1",
            "gilli-game-procedure-revision2",
            "gilli-game-procedure-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Game packet: four players, one soft ball, six floor markers. Players throw from behind a line and collect only after every throw.",
          "prompt": "Write a safe setup and turn procedure.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "setup",
              "description": "Names players, equipment, and starting boundary.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "turn",
              "description": "Explains the turn action.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety",
              "description": "States when collection is safe.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setup",
              "description": "Names players, equipment, and starting boundary.",
              "any_of": [
                "four players",
                "soft ball",
                "six markers",
                "behind line"
              ]
            },
            {
              "id": "turn",
              "description": "Explains the turn action.",
              "any_of": [
                "one throw",
                "each player"
              ]
            },
            {
              "id": "safety",
              "description": "States when collection is safe.",
              "any_of": [
                "after all throws",
                "collect together"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "four players",
            "soft ball",
            "six markers",
            "behind line",
            "one throw",
            "each player",
            "after all throws",
            "collect together"
          ],
          "model_answer": "Place six markers beyond the line and give each of four players one throw with the soft ball. Everyone stays behind the line until all throws finish; then the group collects the markers together.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setup",
            "turn",
            "safety"
          ]
        },
        "masterclass": {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Gilli-danda practice uses pre-smoothed equipment prepared by an adult. The striking zone is clear, and waiting players stand behind a marked boundary.",
          "prompt": "Explain the safety procedure before the first turn.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "equipment",
              "description": "Includes adult-checked equipment.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "space",
              "description": "Clears the striking area.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "waiting",
              "description": "Positions waiting players safely.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "equipment",
              "description": "Includes adult-checked equipment.",
              "any_of": [
                "adult checks",
                "pre-smoothed"
              ]
            },
            {
              "id": "space",
              "description": "Clears the striking area.",
              "any_of": [
                "clear striking zone",
                "area empty"
              ]
            },
            {
              "id": "waiting",
              "description": "Positions waiting players safely.",
              "any_of": [
                "behind boundary"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "adult checks",
            "pre-smoothed",
            "clear striking zone",
            "area empty",
            "behind boundary"
          ],
          "model_answer": "An adult checks the pre-smoothed equipment, players clear the striking zone, and everyone waiting stays behind the boundary. Play begins only after the striker confirms the area is empty.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "equipment",
            "space",
            "waiting"
          ]
        },
        "revision_level_1": {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Scoring rule: measure from the start mark to the landing point with the same cord each time. If players disagree, repeat the measurement with both captains watching.",
          "prompt": "Write the scoring procedure and dispute step.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "measure",
              "description": "Keeps measurement consistent.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "record",
              "description": "Includes score recording.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "dispute",
              "description": "Gives the fair review step.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "measure",
              "description": "Keeps measurement consistent.",
              "any_of": [
                "same start mark",
                "same cord"
              ]
            },
            {
              "id": "record",
              "description": "Includes score recording.",
              "any_of": [
                "record result"
              ]
            },
            {
              "id": "dispute",
              "description": "Gives the fair review step.",
              "any_of": [
                "both captains",
                "repeat measurement",
                "confirm"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "same start mark",
            "same cord",
            "record result",
            "both captains",
            "repeat measurement",
            "confirm"
          ],
          "model_answer": "Measure every landing from the same start mark with the same cord. Record the result. If there is a disagreement, both captains watch a repeated measurement before the score is confirmed.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "measure",
            "record",
            "dispute"
          ]
        },
        "revision_level_2": {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Relay setup: two equal teams, one baton per team, a turning cone, and a no-pushing rule. The next runner starts only after receiving the baton.",
          "prompt": "Present the relay rules in a logical order.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "setup",
              "description": "Includes teams, baton, and cone.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "sequence",
              "description": "Orders running and handover.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "safety",
              "description": "States the no-pushing rule.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setup",
              "description": "Includes teams, baton, and cone.",
              "any_of": [
                "two equal teams",
                "baton",
                "turning cone"
              ]
            },
            {
              "id": "sequence",
              "description": "Orders running and handover.",
              "any_of": [
                "around cone",
                "hand over",
                "next starts"
              ]
            },
            {
              "id": "safety",
              "description": "States the no-pushing rule.",
              "any_of": [
                "no pushing"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "two equal teams",
            "baton",
            "turning cone",
            "around cone",
            "hand over",
            "next starts",
            "no pushing"
          ],
          "model_answer": "Make two equal teams and place a turning cone. Give each first runner a baton. Runners go around the cone and hand over the baton before the next runner starts. No one may push.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setup",
            "sequence",
            "safety"
          ]
        },
        "revision_level_3": {
          "kind": "open_response",
          "activity_id": "gilli-game-procedure-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Use setup-turn-goal-safety boxes and mark any missing rule instead of inventing it.",
          "passage": "Circle pass: six players form a wide circle. They pass a beanbag clockwise. A dropped bag is picked up by the same player while others pause.",
          "prompt": "Write the complete play procedure without inventing a winner.",
          "skill_ids": [
            "reading.event_sequence",
            "writing.procedure"
          ],
          "interaction_type": "paragraph_text",
          "rubric_criteria": [
            {
              "id": "setup",
              "description": "Uses the supplied formation.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "play",
              "description": "Explains direction and drop rule.",
              "required": true,
              "min_quality": 0.7
            },
            {
              "id": "limit",
              "description": "Does not invent missing rules.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "setup",
              "description": "Uses the supplied formation.",
              "any_of": [
                "six players",
                "wide circle"
              ]
            },
            {
              "id": "play",
              "description": "Explains direction and drop rule.",
              "any_of": [
                "clockwise",
                "same player",
                "others pause"
              ]
            },
            {
              "id": "limit",
              "description": "Does not invent missing rules.",
              "any_of": [
                "no winning condition",
                "not invented"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 18,
          "relevance_terms": [
            "six players",
            "wide circle",
            "clockwise",
            "same player",
            "others pause",
            "no winning condition",
            "not invented"
          ],
          "model_answer": "Six players form a wide circle and pass the beanbag clockwise. If it drops, everyone pauses while the same player picks it up, then passing resumes. The packet gives no winning condition, so none should be invented.",
          "pass_score": 0.8,
          "ordered_concept_slot_ids": [
            "setup",
            "play",
            "limit"
          ]
        }
      }
    },
    {
      "level_id": "gilli-source-questions",
      "title": "Ask Questions the Source Can Answer",
      "focus": "form complete WH-questions from bounded facts",
      "outcome": "Choose an appropriate question word, arrange a grammatical question, use a question mark, and verify that the supplied fact packet contains the answer.",
      "skill_ids": [
        "grammar.question_formation",
        "research.information_selection"
      ],
      "episode_kind": "application_mission",
      "source_anchor_ids": [
        "eng_c5_ch07:wordwork:9-12"
      ],
      "connect": {
        "teaching_block": "A strong question is complete, relevant, and answerable. It does not smuggle in a claim that the source never supplied. Dictionary and fact-card work use the same evidence boundary.",
        "passage": "Fact: The match begins at 4 p.m. Answer type: time. Question: When does the match begin?",
        "prompt": "Match the answer type to the question word, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "gilli-source-questions-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
        "passage": "Fact card: The community court opens at 4 p.m. and closes at 6 p.m.",
        "prompt": "Which complete WH-question is answered by the opening time?",
        "skill_ids": [
          "grammar.question_formation",
          "research.information_selection"
        ],
        "options": [
          "Where the court opens?",
          "When community court open.",
          "When does the community court open?",
          "Why does 4 p.m. close?"
        ],
        "accepted_answers": [
          "When does the community court open?"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "gilli-source-questions-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: Five players form each team.",
          "prompt": "Choose the question that can be answered exactly from the card.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "options": [
            "Who invented every team?",
            "Why are five players happy?",
            "How many players form each team?",
            "How many form each team"
          ],
          "accepted_answers": [
            "How many players form each team?"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "gilli-source-questions-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: The measuring cord is kept in the blue equipment box.",
          "prompt": "Which question correctly asks for the location?",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "options": [
            "When the cord kept?",
            "Where does kept the cord?",
            "Where is the measuring cord kept?",
            "Why is blue a cord?"
          ],
          "accepted_answers": [
            "Where is the measuring cord kept?"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-source-questions-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: The umpire repeats a measurement because the first mark was unclear.",
          "prompt": "Which question asks for the reason without adding a new fact?",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "why",
                "repeat measurement",
                "unclear mark"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "why",
            "repeat measurement",
            "unclear mark"
          ],
          "model_answer": "'Why does the umpire repeat the measurement?' is answered by the unclear first mark.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-source-questions-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Dictionary entry: boundary, noun: a line that marks the edge of an area.",
          "prompt": "Form one answerable question about the supplied meaning and give its answer.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "what does boundary mean",
                "line",
                "edge of area"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "what does boundary mean",
            "line",
            "edge of area"
          ],
          "model_answer": "Question: 'What does boundary mean?' Answer: It is a line that marks the edge of an area.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-source-questions-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Mini source: The village sports club began in 1998 and first met beside the old library.",
          "prompt": "Write a valid question about the year and state the source answer.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "when did club begin",
                "1998",
                "source answer"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "when did club begin",
            "1998",
            "source answer"
          ],
          "model_answer": "'When did the village sports club begin?' It began in 1998.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-source-questions-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Mini source: Coach Salma introduced a no-pushing rule after two players collided.",
          "prompt": "Write a reason question that is fully answered by the source.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "why",
                "no-pushing rule",
                "players collided"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "why",
            "no-pushing rule",
            "players collided"
          ],
          "model_answer": "'Why did Coach Salma introduce a no-pushing rule?' She introduced it after two players collided.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-source-questions-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Mini source: A gilli is shorter than the danda and is struck at one end to lift it.",
          "prompt": "Create a comparison question and answer it from the source.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "how different",
                "gilli shorter",
                "lifted"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "how different",
            "gilli shorter",
            "lifted"
          ],
          "model_answer": "'How is the gilli different from the danda?' The gilli is shorter and is the piece that is lifted for striking.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-source-questions-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: The equipment inspection happens before teams enter the field.",
          "prompt": "Write a question whose answer is 'before teams enter the field'.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "when",
                "inspection",
                "before teams enter"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "when",
            "inspection",
            "before teams enter"
          ],
          "model_answer": "'When does the equipment inspection happen?' It happens before teams enter the field.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "gilli-source-questions-misconception",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "misconception": "The learner rearranges words without auxiliary order or asks an interesting question whose answer is absent from the supplied source.",
          "remediation": "Start from the known answer, label its type, build the matching WH-question, and finish by underlining the source words that answer it.",
          "support_check_ids": [
            "gilli-source-questions-bridge",
            "gilli-source-questions-masterclass",
            "gilli-source-questions-revision1",
            "gilli-source-questions-revision2",
            "gilli-source-questions-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "gilli-source-questions-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: The community court opens at 4 p.m. and closes at 6 p.m.",
          "prompt": "Which complete WH-question is answered by the opening time?",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "options": [
            "Where the court opens?",
            "When does the community court open?",
            "When community court open.",
            "Why does 4 p.m. close?"
          ],
          "accepted_answers": [
            "When does the community court open?"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "gilli-source-questions-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: Five players form each team.",
          "prompt": "Choose the question that can be answered exactly from the card.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "options": [
            "Who invented every team?",
            "How many players form each team?",
            "Why are five players happy?",
            "How many form each team"
          ],
          "accepted_answers": [
            "How many players form each team?"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "gilli-source-questions-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: The measuring cord is kept in the blue equipment box.",
          "prompt": "Which question correctly asks for the location?",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "options": [
            "When the cord kept?",
            "Where does kept the cord?",
            "Where is the measuring cord kept?",
            "Why is blue a cord?"
          ],
          "accepted_answers": [
            "Where is the measuring cord kept?"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "gilli-source-questions-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Fact card: The umpire repeats a measurement because the first mark was unclear.",
          "prompt": "Which question asks for the reason without adding a new fact?",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "options": [
            "How many umpires own marks?",
            "Why the umpire repeated?",
            "Where is the invented second cord?",
            "Why does the umpire repeat the measurement?"
          ],
          "accepted_answers": [
            "Why does the umpire repeat the measurement?"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "gilli-source-questions-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Decide the answer type first, choose the WH-word, build the question, and point to the exact source fact that answers it.",
          "passage": "Dictionary entry: boundary, noun: a line that marks the edge of an area.",
          "prompt": "Form one answerable question about the supplied meaning and give its answer.",
          "skill_ids": [
            "grammar.question_formation",
            "research.information_selection"
          ],
          "options": [
            "Who boundary the field?",
            "When is boundary a player?",
            "Why does the entry mention an invented wall?",
            "What does boundary mean?"
          ],
          "accepted_answers": [
            "What does boundary mean?"
          ]
        }
      }
    },
    {
      "level_id": "gilli-spelling-opposites",
      "title": "Check the Word, Then Check the Meaning",
      "focus": "verify standard spelling and contextual antonyms",
      "outcome": "Recognise standard spellings, including taught double-letter patterns, and select an antonym that fits both meaning and grammar in a sentence.",
      "skill_ids": [
        "vocab.spelling",
        "vocab.antonyms"
      ],
      "episode_kind": "retrieval_challenge",
      "source_anchor_ids": [
        "eng_c5_ch07:wordwork:9-12"
      ],
      "connect": {
        "teaching_block": "Sound alone cannot guarantee spelling, and a related word is not always an opposite. Accurate word work checks the letter pattern and the sentence meaning separately.",
        "passage": "Rabbit has double b. Quiet is an antonym of noisy in 'The room became quiet', but silence is a noun and cannot fill every adjective slot.",
        "prompt": "Check spelling and word form separately, then continue."
      },
      "co_construct": {
        "kind": "selected_option",
        "activity_id": "gilli-spelling-opposites-co",
        "teaching_block": "Work through the clue with the coach, then choose the claim that the clue actually supports. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
        "passage": "The standard spelling has a doubled consonant: ba__on.",
        "prompt": "Complete the game word and explain the double letter.",
        "skill_ids": [
          "vocab.spelling",
          "vocab.antonyms"
        ],
        "options": [
          "batton",
          "battan",
          "baton",
          "battone"
        ],
        "accepted_answers": [
          "baton"
        ]
      },
      "guided_variants": [
        {
          "kind": "selected_option",
          "activity_id": "gilli-spelling-opposites-guided-1",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "Choose the standard spelling for a person who controls a match: referee.",
          "prompt": "Which option is spelled correctly?",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "options": [
            "refferee",
            "referee",
            "refere",
            "refereee"
          ],
          "accepted_answers": [
            "referee"
          ]
        },
        {
          "kind": "selected_option",
          "activity_id": "gilli-spelling-opposites-guided-2",
          "teaching_block": "Name the exact relation being tested before you compare the choices. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "The opposite of 'victory' in this sentence is needed: The team accepted defeat calmly.",
          "prompt": "Which word is the contextual antonym of victory?",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "options": [
            "cheer",
            "defeat",
            "practice",
            "score"
          ],
          "accepted_answers": [
            "defeat"
          ]
        }
      ],
      "independent_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-spelling-opposites-independent-1",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "The marker is visible, but after dust covers it the marker becomes ____.",
          "prompt": "Form the contextual opposite of visible.",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "visible",
                "invisible",
                "covered"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "visible",
            "invisible",
            "covered"
          ],
          "model_answer": "The marker becomes invisible; the prefix 'in-' creates the opposite meaning.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-spelling-opposites-independent-2",
          "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "Complete the double-letter word: The players carried a ra__le to make a sound.",
          "prompt": "Which spelling completes the sentence?",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "rattle",
                "double t",
                "sound"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "rattle",
            "double t",
            "sound"
          ],
          "model_answer": "'Rattle' is spelled with double t and fits the object that makes a sound.",
          "pass_score": 0.8
        }
      ],
      "transfer_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-spelling-opposites-transfer-1",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "The rules were clear, but the faded score was ____.",
          "prompt": "Choose an antonym of clear that fits meaning and grammar.",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "clear",
                "unclear",
                "faded"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "clear",
            "unclear",
            "faded"
          ],
          "model_answer": "'Unclear' fits because the faded score was difficult to understand.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-spelling-opposites-transfer-2",
          "teaching_block": "The setting has changed. Transfer the same reasoning process instead of copying earlier wording. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "A 'winner' succeeds in the contest; the direct opposite role is the loser.",
          "prompt": "Use both opposites in one respectful sentence.",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "winner",
                "loser",
                "fairly"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "winner",
            "loser",
            "fairly"
          ],
          "model_answer": "The winner thanked the loser after both had played fairly.",
          "pass_score": 0.8
        }
      ],
      "review_variants": [
        {
          "kind": "open_response",
          "activity_id": "gilli-spelling-opposites-review-1",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "Choose the standard double-letter spelling for a small white animal often kept as a pet.",
          "prompt": "Which spelling is correct?",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "rabbit",
                "double b",
                "animal"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "rabbit",
            "double b",
            "animal"
          ],
          "model_answer": "'Rabbit' is the standard spelling and contains double b.",
          "pass_score": 0.8
        },
        {
          "kind": "open_response",
          "activity_id": "gilli-spelling-opposites-review-2",
          "teaching_block": "Retrieve the strategy from memory, then show both the decision and the clue that justifies it. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "The path was narrow, whereas the field was ____.",
          "prompt": "Supply the most suitable antonym and keep the adjective form.",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "interaction_type": "evidence_text",
          "rubric_criteria": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "required": true,
              "min_quality": 0.7
            }
          ],
          "concept_slots": [
            {
              "id": "core",
              "description": "Gives the accurate idea supported by the stimulus.",
              "any_of": [
                "narrow",
                "wide",
                "adjective"
              ]
            }
          ],
          "forbidden_phrases": [
            "I do not know",
            "copy the sample"
          ],
          "min_response_words": 8,
          "relevance_terms": [
            "narrow",
            "wide",
            "adjective"
          ],
          "model_answer": "The field was wide; 'wide' is an adjective opposite to 'narrow'.",
          "pass_score": 0.8
        }
      ],
      "misconception_clusters": [
        {
          "cluster_id": "gilli-spelling-opposites-misconception",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "misconception": "The learner guesses double letters from sound or chooses a related word without testing whether it is an opposite in the sentence.",
          "remediation": "Use a look-cover-write-check spelling cycle, then replace the target with the proposed antonym and read the full sentence for opposite meaning and matching form.",
          "support_check_ids": [
            "gilli-spelling-opposites-bridge",
            "gilli-spelling-opposites-masterclass",
            "gilli-spelling-opposites-revision1",
            "gilli-spelling-opposites-revision2",
            "gilli-spelling-opposites-revision3"
          ]
        }
      ],
      "support_checks": {
        "bridge": {
          "kind": "selected_option",
          "activity_id": "gilli-spelling-opposites-bridge",
          "teaching_block": "Reduce the task to one clue and one decision. Check that the two match before answering. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "The standard spelling has a doubled consonant: ba__on.",
          "prompt": "Complete the game word and explain the double letter.",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "options": [
            "batton",
            "battan",
            "baton",
            "battone"
          ],
          "accepted_answers": [
            "baton"
          ]
        },
        "masterclass": {
          "kind": "selected_option",
          "activity_id": "gilli-spelling-opposites-masterclass",
          "teaching_block": "Rebuild the skill in three moves: locate the signal, name its job, and use it in the answer. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "Choose the standard spelling for a person who controls a match: referee.",
          "prompt": "Which option is spelled correctly?",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "options": [
            "refferee",
            "refere",
            "referee",
            "refereee"
          ],
          "accepted_answers": [
            "referee"
          ]
        },
        "revision_level_1": {
          "kind": "selected_option",
          "activity_id": "gilli-spelling-opposites-revision1",
          "teaching_block": "First revision: mark the signal word or event, then state only what it proves. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "The opposite of 'victory' in this sentence is needed: The team accepted defeat calmly.",
          "prompt": "Which word is the contextual antonym of victory?",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "options": [
            "cheer",
            "defeat",
            "practice",
            "score"
          ],
          "accepted_answers": [
            "defeat"
          ]
        },
        "revision_level_2": {
          "kind": "selected_option",
          "activity_id": "gilli-spelling-opposites-revision2",
          "teaching_block": "Second revision: compare the tempting error with the evidence and explain the mismatch. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "The marker is visible, but after dust covers it the marker becomes ____.",
          "prompt": "Form the contextual opposite of visible.",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "options": [
            "unvisible",
            "revisible",
            "visibility",
            "invisible"
          ],
          "accepted_answers": [
            "invisible"
          ]
        },
        "revision_level_3": {
          "kind": "selected_option",
          "activity_id": "gilli-spelling-opposites-revision3",
          "teaching_block": "Final supported revision: use the short checklist, then produce a complete answer independently. Verify spelling through a known pattern or reliable entry, then substitute each proposed opposite into the whole sentence.",
          "passage": "Complete the double-letter word: The players carried a ra__le to make a sound.",
          "prompt": "Which spelling completes the sentence?",
          "skill_ids": [
            "vocab.spelling",
            "vocab.antonyms"
          ],
          "options": [
            "ratle",
            "rattel",
            "rattle",
            "rrattle"
          ],
          "accepted_answers": [
            "rattle"
          ]
        }
      }
    }
  ],
  "chapter_assessment": {
    "items_per_attempt": 16,
    "pass_score": 0.8,
    "max_attempts": 2,
    "bank_item_count": 32,
    "items": [
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-poetic-meaning-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The kite pulls hard against the reel, / Then bows when evening winds grow still. / The child who held it high all day / Now winds the thread with patient skill.",
        "prompt": "Transfer the poetic-language strategy: what does 'bows' suggest here?",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "options": [
          "the kite speaks politely",
          "the reel bends into a weapon",
          "the child leaves before evening",
          "the kite dips as the wind weakens"
        ],
        "accepted_answers": [
          "the kite dips as the wind weakens"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-poetic-meaning-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Rain drums lightly on the roof; / The class grows quiet, page by page. / Outside, the restless puddles dance; / Inside, a story fills the stage.",
        "prompt": "Identify one sound image and one movement image.",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "options": [
          "pages are the only sound",
          "the story literally builds a stage",
          "rain drums; puddles dance",
          "quiet is a kind of puddle"
        ],
        "accepted_answers": [
          "rain drums; puddles dance"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-poetic-meaning-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The old bridge groans beneath the cart, / The new road hums with wheels nearby. / One carries memory through the fields; / One sends tomorrow racing by.",
        "prompt": "What comparison is created between bridge and road?",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "bridge memory",
              "road future",
              "speed"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "bridge memory",
          "road future",
          "speed"
        ],
        "model_answer": "The bridge is linked with memory and age, while the road represents speed and the future.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-poetic-meaning-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Repetition can echo an action, comparison can sharpen an image, and exaggeration can express feeling without reporting a literal fact.",
        "prompt": "State the safest way to interpret poetic language.",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "surrounding lines",
              "image or feeling",
              "not literal fact"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "surrounding lines",
          "image or feeling",
          "not literal fact"
        ],
        "model_answer": "Use the surrounding lines to decide what image or feeling the device creates, and do not treat imaginative exaggeration as factual reporting.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-poetic-meaning-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "We missed the gilli three times straight, / Then changed our stance and watched the line. / The fourth small tap rose clean and high; / The cheer belonged to patient time.",
        "prompt": "What does 'the cheer belonged to patient time' mean?",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "patient practice",
              "adjustment",
              "success"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "patient practice",
          "adjustment",
          "success"
        ],
        "model_answer": "It means patient practice and adjustment led to the successful fourth attempt.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-prefix-formation-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Base word: arrange. New sentence: Rearrange the teams so each side has five players.",
        "prompt": "Which explanation shows how the added letters change 'arrange' into 'rearrange'?",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "to leave the arrangement unchanged",
          "to remove all players",
          "to count one team",
          "rearrange: to arrange again in a different or improved order"
        ],
        "accepted_answers": [
          "rearrange: to arrange again in a different or improved order"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-prefix-formation-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Base word: certain. New sentence: The umpire was uncertain because the landing mark had faded.",
        "prompt": "Which explanation shows how the added letters change 'certain' into 'uncertain'?",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "options": [
          "certain again",
          "uncertain: not certain",
          "completely correct",
          "louder than before"
        ],
        "accepted_answers": [
          "uncertain: not certain"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-prefix-formation-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Base word: read. New sentence: Reread the safety rule before shaping the stick.",
        "prompt": "Which explanation shows how the added letters change 'read' into 'reread'?",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "reread",
              "to read again",
              "read"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "reread",
          "to read again",
          "read"
        ],
        "model_answer": "'reread' means to read again; the sentence uses that changed meaning accurately.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-prefix-formation-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Base word: kind. New sentence: Mocking a new player would be unkind.",
        "prompt": "Which explanation shows how the added letters change 'kind' into 'unkind'?",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "unkind",
              "not kind",
              "kind"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "unkind",
          "not kind",
          "kind"
        ],
        "model_answer": "'unkind' means not kind; the sentence uses that changed meaning accurately.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-prefix-formation-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Base word: start. New sentence: Restart the timer after the interruption.",
        "prompt": "Which explanation shows how the added letters change 'start' into 'restart'?",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "restart",
              "to start again",
              "start"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "restart",
          "to start again",
          "start"
        ],
        "model_answer": "'restart' means to start again; the sentence uses that changed meaning accurately.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-concrete-abstract-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "A bright lantern hung above the gate.",
        "prompt": "Classify 'lantern' and justify the classification with the sensory test.",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "options": [
          "a concrete noun: it can be seen and touched",
          "abstract: it names brightness",
          "verb: it means hung",
          "adjective: it describes gate"
        ],
        "accepted_answers": [
          "a concrete noun: it can be seen and touched"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-concrete-abstract-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Justice requires the same rule for both teams.",
        "prompt": "Classify 'justice' and justify the classification with the sensory test.",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "options": [
          "an abstract noun: it names an idea about fairness",
          "concrete: it is a team",
          "verb: it means requires",
          "adjective: it describes rule"
        ],
        "accepted_answers": [
          "an abstract noun: it names an idea about fairness"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-concrete-abstract-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The referee placed the whistle on the bench.",
        "prompt": "Classify 'whistle' and justify the classification with the sensory test.",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "whistle",
              "a concrete noun",
              "it names an object that can be held and heard"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "whistle",
          "a concrete noun",
          "it names an object that can be held and heard"
        ],
        "model_answer": "'whistle' is a concrete noun because it names an object that can be held and heard.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-concrete-abstract-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Respect appeared when the winners thanked the other team.",
        "prompt": "Classify 'respect' and justify the classification with the sensory test.",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "respect",
              "an abstract noun",
              "it names an attitude shown through actions"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "respect",
          "an abstract noun",
          "it names an attitude shown through actions"
        ],
        "model_answer": "'respect' is an abstract noun because it names an attitude shown through actions.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-concrete-abstract-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The notebook contained every score.",
        "prompt": "Classify 'notebook' and justify the classification with the sensory test.",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "notebook",
              "a concrete noun",
              "it is a physical item that can be handled"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "notebook",
          "a concrete noun",
          "it is a physical item that can be handled"
        ],
        "model_answer": "'notebook' is a concrete noun because it is a physical item that can be handled.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-possessive-pronouns-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "These gloves belong to you and Ravi. They are ____.",
        "prompt": "Choose the possessive pronoun that refers clearly to you and Ravi, then explain the match.",
        "skill_ids": [
          "grammar.pronouns",
          "grammar.sentence_order"
        ],
        "options": [
          "your",
          "theirs",
          "yours",
          "mine"
        ],
        "accepted_answers": [
          "yours"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-possessive-pronouns-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The club owns the field. During practice, the field is ____.",
        "prompt": "Choose the possessive pronoun that refers clearly to the club, then explain the match.",
        "skill_ids": [
          "grammar.pronouns",
          "grammar.sentence_order"
        ],
        "options": [
          "their",
          "ours",
          "hers",
          "theirs"
        ],
        "accepted_answers": [
          "theirs"
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-possessive-pronouns-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "I borrowed Sara's ruler; the ruler remains ____.",
        "prompt": "Choose the possessive pronoun that refers clearly to Sara, then explain the match.",
        "skill_ids": [
          "grammar.pronouns",
          "grammar.sentence_order"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "hers",
              "Sara",
              "borrowing does not change ownership"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "hers",
          "Sara",
          "borrowing does not change ownership"
        ],
        "model_answer": "The correct form is 'hers' because borrowing does not change ownership.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-possessive-pronouns-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Possessive pronouns replace an owner plus a noun: 'my bat' becomes 'mine', while 'my' alone still needs a noun.",
        "prompt": "Choose the possessive pronoun that refers clearly to the speaker in 'my bat', then explain the match.",
        "skill_ids": [
          "grammar.pronouns",
          "grammar.sentence_order"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "mine",
              "the speaker in 'my bat'",
              "the noun has been replaced"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "mine",
          "the speaker in 'my bat'",
          "the noun has been replaced"
        ],
        "model_answer": "The correct form is 'mine' because the noun has been replaced.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-possessive-pronouns-5",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The blue sticks belong to our opponents. The blue sticks are ____.",
        "prompt": "Choose the possessive pronoun that refers clearly to the opposing team, then explain the match.",
        "skill_ids": [
          "grammar.pronouns",
          "grammar.sentence_order"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "theirs",
              "the opposing team",
              "a plural group owns them"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "theirs",
          "the opposing team",
          "a plural group owns them"
        ],
        "model_answer": "The correct form is 'theirs' because a plural group owns them.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-game-procedure-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Library hunt: pairs receive a call-number card, walk to the correct shelf, record one title, and return without running. The task ends after three cards.",
        "prompt": "Transfer the game-procedure structure to this learning activity.",
        "skill_ids": [
          "reading.event_sequence",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "turn",
            "description": "Orders card, search, record, and return.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "safety",
            "description": "Includes no running.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "end",
            "description": "States the completion condition.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "turn",
            "description": "Orders card, search, record, and return.",
            "any_of": [
              "card",
              "walk",
              "record title",
              "return"
            ]
          },
          {
            "id": "safety",
            "description": "Includes no running.",
            "any_of": [
              "no running"
            ]
          },
          {
            "id": "end",
            "description": "States the completion condition.",
            "any_of": [
              "three cards"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "card",
          "walk",
          "record title",
          "return",
          "no running",
          "three cards"
        ],
        "model_answer": "Give each pair one call-number card. They walk to the shelf, record one matching title, and return before receiving another card. No running is allowed, and the hunt ends after three completed cards.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-game-procedure-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Science sort: teams receive twelve picture cards and three labelled hoops: solid, liquid, gas. One card is discussed at a time; a reason is required before placement.",
        "prompt": "Write the collaborative procedure.",
        "skill_ids": [
          "reading.event_sequence",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "setup",
            "description": "Includes hoops and cards.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "turn",
            "description": "Requires discussion, reason, and placement.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "check",
            "description": "Handles disagreement responsibly.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "setup",
            "description": "Includes hoops and cards.",
            "any_of": [
              "three hoops",
              "twelve cards"
            ]
          },
          {
            "id": "turn",
            "description": "Requires discussion, reason, and placement.",
            "any_of": [
              "one card",
              "reason",
              "place"
            ]
          },
          {
            "id": "check",
            "description": "Handles disagreement responsibly.",
            "any_of": [
              "lesson source",
              "disagreement"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "three hoops",
          "twelve cards",
          "one card",
          "reason",
          "place",
          "lesson source",
          "disagreement"
        ],
        "model_answer": "Place the three labelled hoops first. A team discusses one card, states a reason, and then places it in the chosen hoop. Repeat until all twelve cards are classified; disagreements are checked against the lesson source.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-game-procedure-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Treasure-grid directions: start at B2, move two squares east, one north, then stop. Players must keep tokens on the grid and read one direction at a time.",
        "prompt": "Explain the move procedure and error check.",
        "skill_ids": [
          "reading.event_sequence",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "sequence",
            "description": "Uses start and moves in order.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "control",
            "description": "Uses one direction at a time.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "repair",
            "description": "Gives an error-recovery step.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "sequence",
            "description": "Uses start and moves in order.",
            "any_of": [
              "B2",
              "two east",
              "one north",
              "stop"
            ]
          },
          {
            "id": "control",
            "description": "Uses one direction at a time.",
            "any_of": [
              "read one",
              "then move"
            ]
          },
          {
            "id": "repair",
            "description": "Gives an error-recovery step.",
            "any_of": [
              "last correct square",
              "re-read"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "B2",
          "two east",
          "one north",
          "stop",
          "read one",
          "then move",
          "last correct square",
          "re-read"
        ],
        "model_answer": "Place the token at B2, read the first direction, move two squares east, then read and move one square north. Stop there. If the token leaves the grid, return to the last correct square and re-read the step.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-game-procedure-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Community game day has two zones: striking games and running games. Each zone has an adult facilitator, marked waiting area, water break every twenty minutes, and equipment check before play.",
        "prompt": "Write the event safety procedure.",
        "skill_ids": [
          "reading.event_sequence",
          "writing.procedure"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "zones",
            "description": "Uses zone and facilitator facts.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "safety",
            "description": "Separates waiting and active players and checks equipment.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "break",
            "description": "Includes timed water breaks.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "zones",
            "description": "Uses zone and facilitator facts.",
            "any_of": [
              "two zones",
              "adult facilitator"
            ]
          },
          {
            "id": "safety",
            "description": "Separates waiting and active players and checks equipment.",
            "any_of": [
              "waiting area",
              "equipment check",
              "separated"
            ]
          },
          {
            "id": "break",
            "description": "Includes timed water breaks.",
            "any_of": [
              "twenty minutes",
              "water break"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 18,
        "relevance_terms": [
          "two zones",
          "adult facilitator",
          "waiting area",
          "equipment check",
          "separated",
          "twenty minutes",
          "water break"
        ],
        "model_answer": "Players enter the marked waiting area for their chosen zone. The adult facilitator checks equipment before play, keeps active and waiting players separated, and pauses each zone for water every twenty minutes.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-source-questions-1",
        "teaching_block": "Read the museum label closely. Form a complete place question, then answer with only the location the label gives.",
        "passage": "Museum label: This wooden spinning top was made in Rajasthan in 1975.",
        "prompt": "Write the place question and its source-supported answer.",
        "skill_ids": [
          "grammar.question_formation",
          "research.information_selection"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "question",
            "description": "Forms a complete where-question about the spinning top's place of manufacture.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "answer",
            "description": "Answers Rajasthan and adds no unsupported place.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "question",
            "description": "Forms a complete where-question about the spinning top's place of manufacture.",
            "any_of": ["where was the wooden spinning top made", "where was this spinning top made"]
          },
          {
            "id": "answer",
            "description": "Answers Rajasthan and adds no unsupported place.",
            "any_of": ["Rajasthan", "made in Rajasthan"]
          }
        ],
        "forbidden_phrases": ["I do not know", "copy the sample"],
        "min_response_words": 10,
        "relevance_terms": ["where", "spinning", "top", "made", "Rajasthan"],
        "model_answer": "Where was the wooden spinning top made? It was made in Rajasthan.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-source-questions-2",
        "teaching_block": "Use the because-clause in the weather note. Form a complete reason question and answer only with the stated cause.",
        "passage": "Weather note: Practice moved indoors because lightning was seen nearby.",
        "prompt": "Write the reason question and its source-supported answer.",
        "skill_ids": [
          "grammar.question_formation",
          "research.information_selection"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "question",
            "description": "Forms a complete why-question about practice moving indoors.",
            "required": true,
            "min_quality": 0.7
          },
          {
            "id": "answer",
            "description": "Answers that nearby lightning was seen without inventing a strike.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "question",
            "description": "Forms a complete why-question about practice moving indoors.",
            "any_of": ["why did practice move indoors", "why was practice moved indoors"]
          },
          {
            "id": "answer",
            "description": "Answers that nearby lightning was seen without inventing a strike.",
            "any_of": ["lightning was seen nearby", "because lightning was nearby"]
          }
        ],
        "forbidden_phrases": ["I do not know", "lightning hit the field"],
        "min_response_words": 11,
        "relevance_terms": ["why", "practice", "indoors", "lightning", "nearby"],
        "model_answer": "Why did practice move indoors? It moved indoors because lightning was seen nearby.",
        "pass_score": 0.8
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-source-questions-3",
        "teaching_block": "Choose the complete number question that the library record can answer directly without subtraction.",
        "passage": "Library record: Twelve books about traditional games were borrowed this month; seven were returned by Friday.",
        "prompt": "Which question fits the source and does not require subtraction?",
        "skill_ids": [
          "grammar.question_formation",
          "research.information_selection"
        ],
        "options": [
          "How many books about traditional games were borrowed this month?",
          "How many borrowed books were still missing on Friday?",
          "Why were the seven books returned by Friday?",
          "How many books were borrowed next month?"
        ],
        "accepted_answers": [
          "How many books about traditional games were borrowed this month?"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-source-questions-4",
        "teaching_block": "Check each proposed checklist for question word, complete order, punctuation, and an answer available in the source.",
        "passage": "A trustworthy source question names what it asks, uses an appropriate question word, follows English order, ends with a question mark, and can be answered from the packet.",
        "prompt": "Which checklist includes every requirement?",
        "skill_ids": [
          "grammar.question_formation",
          "research.information_selection"
        ],
        "options": [
          "Use a fitting question word, complete English order, a question mark, and a source-supported answer.",
          "Use any opening word and add an answer from memory.",
          "Copy one source sentence and remove its full stop.",
          "Write a question mark and guess any missing fact."
        ],
        "accepted_answers": [
          "Use a fitting question word, complete English order, a question mark, and a source-supported answer."
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-spelling-opposites-1",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The bag felt heavy before equipment was removed and ____ afterward.",
        "prompt": "Choose the contextual opposite.",
        "skill_ids": [
          "vocab.spelling",
          "vocab.antonyms"
        ],
        "options": [
          "dark",
          "slow",
          "light",
          "emptying"
        ],
        "accepted_answers": [
          "light"
        ]
      },
      {
        "kind": "selected_option",
        "activity_id": "eng_c5_ch07-assessment-gilli-spelling-opposites-2",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The word 'beginning' contains doubled n in the middle.",
        "prompt": "Choose the standard spelling in a new sentence.",
        "skill_ids": [
          "vocab.spelling",
          "vocab.antonyms"
        ],
        "options": [
          "The begining of the match was delayed.",
          "The beggining of match delayed.",
          "The begininng was delay.",
          "The beginning of the match was delayed."
        ],
        "accepted_answers": [
          "The beginning of the match was delayed."
        ]
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-spelling-opposites-3",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "The antonym of 'ancient' may be 'modern' when comparing objects or practices.",
        "prompt": "Use the pair in a meaningful comparison.",
        "skill_ids": [
          "vocab.spelling",
          "vocab.antonyms"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "ancient",
              "modern",
              "comparison"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "ancient",
          "modern",
          "comparison"
        ],
        "model_answer": "Gilli danda is an ancient game, while the electronic scoreboard is modern.",
        "pass_score": 0.8
      },
      {
        "kind": "open_response",
        "activity_id": "eng_c5_ch07-assessment-gilli-spelling-opposites-4",
        "teaching_block": "Answer without a model. Build the response from the visible evidence in this new example. Use the visible card and check each requested detail against it.",
        "passage": "Spelling should be checked by a reliable word source, while antonyms must be tested inside the sentence for meaning and word form.",
        "prompt": "State the two-part verification rule.",
        "skill_ids": [
          "vocab.spelling",
          "vocab.antonyms"
        ],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "required": true,
            "min_quality": 0.7
          }
        ],
        "concept_slots": [
          {
            "id": "core",
            "description": "Gives the accurate idea supported by the stimulus.",
            "any_of": [
              "dictionary",
              "substitute antonym",
              "meaning and grammar"
            ]
          }
        ],
        "forbidden_phrases": [
          "I do not know",
          "copy the sample"
        ],
        "min_response_words": 8,
        "relevance_terms": [
          "dictionary",
          "substitute antonym",
          "meaning and grammar"
        ],
        "model_answer": "Verify spelling in a reliable dictionary, and substitute an antonym into the sentence to confirm both meaning and grammar.",
        "pass_score": 0.8
      }
    ],
    "strands": [
      {
        "strand_id": "gilli-poetic-meaning",
        "skill_ids": [
          "reading.poetic_language",
          "reading.sentence_comprehension"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "gilli-poetic-meaning"
        ]
      },
      {
        "strand_id": "gilli-prefix-formation",
        "skill_ids": [
          "vocab.word_formation",
          "vocab.chapter_word_usage"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "gilli-prefix-formation"
        ]
      },
      {
        "strand_id": "gilli-concrete-abstract",
        "skill_ids": [
          "grammar.noun_verb_adjective"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "gilli-concrete-abstract"
        ]
      },
      {
        "strand_id": "gilli-possessive-pronouns",
        "skill_ids": [
          "grammar.pronouns",
          "grammar.sentence_order"
        ],
        "minimum_items": 5,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "gilli-possessive-pronouns"
        ]
      },
      {
        "strand_id": "gilli-game-procedure",
        "skill_ids": [
          "reading.event_sequence",
          "writing.procedure"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "constructed_response"
        ],
        "remediation_level_ids": [
          "gilli-game-procedure"
        ]
      },
      {
        "strand_id": "gilli-source-questions",
        "skill_ids": [
          "grammar.question_formation",
          "research.information_selection"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "gilli-source-questions"
        ]
      },
      {
        "strand_id": "gilli-spelling-opposites",
        "skill_ids": [
          "vocab.spelling",
          "vocab.antonyms"
        ],
        "minimum_items": 4,
        "evidence_forms": [
          "selected_option",
          "constructed_response"
        ],
        "remediation_level_ids": [
          "gilli-spelling-opposites"
        ]
      }
    ]
  }
}''')


def _one(
    passage: str,
    prompt: str,
    answer: str,
    alias: str,
    *,
    description: str,
    skills: list[str],
    interaction: str = "evidence_text",
    min_words: int = 10,
) -> dict:
    try:
        _terms(answer)
    except ValueError:
        answer = f"{answer} This response {description.lower()}"
    return _task(
        passage,
        prompt,
        answer,
        [_evidence("core", description, alias)],
        interaction_type=interaction,
        min_words=min_words,
        skills=skills,
    )


def _two(
    passage: str,
    prompt: str,
    answer: str,
    first: tuple[str, str, str],
    second: tuple[str, str, str],
    *,
    skills: list[str],
    interaction: str = "evidence_text",
    min_words: int = 14,
    ordered: bool = False,
) -> dict:
    return _task(
        passage,
        prompt,
        answer,
        [
            _evidence(first[0], first[1], first[2]),
            _evidence(second[0], second[1], second[2]),
        ],
        interaction_type=interaction,
        min_words=min_words,
        skills=skills,
        ordered=ordered,
    )


_PRINCIPLES = {
    "gilli-poetic-meaning": "Read the image as a comparison or movement clue, then explain the idea in ordinary language without making it literal.",
    "gilli-prefix-formation": "Test the base word first, add un- or re-, and confirm that the new word fits the sentence's intended meaning.",
    "gilli-concrete-abstract": "Ask whether the noun names something sensed directly or an idea, feeling, or quality understood through actions.",
    "gilli-possessive-pronouns": "Match the owner and number before replacing the noun phrase with a possessive pronoun.",
    "gilli-game-procedure": "Write playable steps in order, including space, turn, scoring, and safety boundaries.",
    "gilli-source-questions": "Ask only questions the supplied source can answer, and separate missing information from evidence.",
    "gilli-spelling-opposites": "Verify the spelling of each word, then check that the pair expresses opposite meanings in the given context.",
}


_DEPTH = {
    "gilli-poetic-meaning": {
        "guided": [
            _one(
                "A spinning top hums on the courtyard floor, drawing a tiny circle of dust before it leans and sleeps.",
                "Explain what sleeps suggests about the top without taking the word literally.",
                "Sleeps suggests that the spinning top has slowed, fallen still, and ended its lively movement.",
                "spinning top has slowed, fallen still, and ended its lively movement",
                description="Explains the nonliteral image through movement clues.",
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
            ),
            _one(
                "The kite tugged at its string like an impatient puppy while the child held the reel firmly.",
                "What shared action makes the puppy comparison effective?",
                "The kite and an impatient puppy both pull repeatedly against something that holds them back.",
                "both pull repeatedly against something that holds them back",
                description="Identifies the shared action behind the comparison.",
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
            ),
        ],
        "independent": [
            _two(
                "Across the field, the small wooden striker leapt from the soil, flashed once in the sun, and raced away like a startled bird. The waiting players shouted and ran.",
                "Interpret the startled-bird image and explain how it shapes the scene's energy.",
                "The striker is compared with a startled bird because both rise suddenly and move quickly away. That image makes the game feel fast, surprising, and full of pursuit.",
                ("image", "Explains the shared sudden movement.", "both rise suddenly and move quickly away"),
                ("effect", "Explains the energetic effect on the scene.", "makes the game feel fast, surprising, and full of pursuit"),
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
                min_words=25,
            ),
            _two(
                "The last throw curved through evening light. For one breath the whole lane became quiet, then cheers burst from every doorway.",
                "Explain the contrast between quiet and cheers and state the moment's central idea.",
                "The brief quiet shows everyone waiting to see the throw's result, while the sudden cheers release their excitement. The scene centres on a shared moment of suspense becoming celebration.",
                ("contrast", "Explains waiting silence and released excitement.", "quiet shows everyone waiting to see the throw's result, while the sudden cheers release their excitement"),
                ("idea", "States the central movement from suspense to celebration.", "shared moment of suspense becoming celebration"),
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
                min_words=27,
            ),
        ],
        "transfer": [
            _two(
                "A marble rolled down the step, paused at the edge, and then dived into the drain's shadow.",
                "Interpret dived and explain why the verb is more vivid than went.",
                "Dived means the marble dropped quickly into the dark drain opening. The verb is vivid because it suggests a sudden, directed plunge rather than ordinary movement.",
                ("meaning", "Explains dived from the action.", "marble dropped quickly into the dark drain opening"),
                ("effect", "Compares the vivid verb with ordinary movement.", "suggests a sudden, directed plunge rather than ordinary movement"),
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
                min_words=23,
            ),
        ],
        "support": [
            _one(
                "The ball skipped over three stones before resting in the grass.",
                "What movement does skipped create in your mind?",
                "Skipped shows the ball making several quick, light bounces over the stones.",
                "several quick, light bounces over the stones",
                description="Explains the movement image.",
                skills=["reading.poetic_language"],
            ),
            _one(
                "The bat sang when it struck the rubber ball cleanly.",
                "Explain sang as a sound image, not a literal action.",
                "Sang describes the clear ringing sound made by the clean strike; the bat did not use a voice.",
                "clear ringing sound made by the clean strike",
                description="Explains the sound image and its nonliteral boundary.",
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
            ),
            _one(
                "Dust rose behind the runners like a pale curtain.",
                "Name the compared things and the shared feature.",
                "The rising dust is compared with a curtain because both form a broad sheet that partly hides what is behind.",
                "both form a broad sheet that partly hides what is behind",
                description="Explains the visual comparison.",
                skills=["reading.poetic_language"],
            ),
            _one(
                "The whistle cut through the noisy playground.",
                "What does cut through mean in this sentence?",
                "Cut through means the whistle was sharp and loud enough to be heard above the playground noise.",
                "sharp and loud enough to be heard above the playground noise",
                description="Infers the phrase from the sound context.",
                skills=["reading.sentence_comprehension"],
            ),
            _two(
                "The final catch froze every player, then sent the winning team jumping into the air.",
                "Explain froze and the change that follows it.",
                "Froze means the players stopped in suspense for an instant. The confirmed catch then changed stillness into celebration.",
                ("image", "Explains the nonliteral stopping.", "players stopped in suspense for an instant"),
                ("change", "Explains the movement into celebration.", "changed stillness into celebration"),
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
            ),
        ],
    },
    "gilli-prefix-formation": {
        "guided": [
            _one(
                "The chalk score was wrong, so the captain had to ___ it before the next round. Base word: write.",
                "Form the word that means write again and use it in the completed sentence.",
                "The captain had to rewrite the score before the next round.",
                "had to rewrite the score before the next round",
                description="Forms rewrite and uses it with the intended meaning.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
            _one(
                "A knot came loose during play, making the boundary rope ___ until it was tied again. Base word: secure.",
                "Add the prefix that gives the opposite meaning.",
                "The boundary rope became unsecure until it was tied again.",
                "boundary rope became unsecure until it was tied again",
                description="Forms the opposite with un- and fits the context.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
        ],
        "independent": [
            _two(
                "The first diagram was unclear, so Mira drew it again. Later, she noticed that one label could not be read at all.",
                "Use one re- word and one un- word to describe the two problems accurately.",
                "Mira redrew the unclear diagram, and the damaged label was unreadable.",
                ("again", "Uses a re- form for doing the action again.", "Mira redrew the unclear diagram"),
                ("not", "Uses an un- form for the missing ability.", "damaged label was unreadable"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=10,
            ),
            _two(
                "A player tied the marker wrongly, untied it, and tied it once more in the correct place. The old position could no longer be used.",
                "Choose two prefixed words that capture the correction and explain their meanings.",
                "The player untied the marker and then retied it correctly. Untied means released from the knot, while retied means tied again.",
                ("words", "Uses untied and retied in sequence.", "untied the marker and then retied it correctly"),
                ("meanings", "Explains the contrast between undoing and repeating.", "Untied means released from the knot, while retied means tied again"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=20,
                ordered=True,
            ),
        ],
        "transfer": [
            _two(
                "A digital form did not save, so the volunteer entered the details again. One phone number had no reliable owner and could not be confirmed.",
                "Use a re- word for the repeated action and an un- word for the doubtful number.",
                "The volunteer re-entered the details, but the phone number remained unverified.",
                ("repeat", "Forms the repeated-action word.", "re-entered the details"),
                ("negative", "Forms the not-confirmed word.", "phone number remained unverified"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=12,
            ),
        ],
        "support": [
            _one(
                "The bell did not work, so the match had to begin again.",
                "Replace begin again with one re- word.",
                "The match had to restart because the bell did not work.",
                "match had to restart because the bell did not work",
                description="Uses restart for begin again.",
                skills=["vocab.word_formation"],
            ),
            _one(
                "The surface was not even, so the wooden piece rolled sideways.",
                "Build one un- word from even.",
                "The wooden piece rolled sideways because the surface was uneven.",
                "surface was uneven",
                description="Forms uneven and uses it correctly.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
            _one(
                "The coach asked the team to arrange the markers again after the wind moved them.",
                "Replace arrange again with a prefixed verb.",
                "The coach asked the team to rearrange the markers after the wind moved them.",
                "rearrange the markers after the wind moved them",
                description="Uses rearrange for arranging again.",
                skills=["vocab.word_formation"],
            ),
            _one(
                "The rule was not fair because only one team could choose the playing side.",
                "Form an un- word that describes the rule.",
                "The rule was unfair because only one team could choose the playing side.",
                "rule was unfair",
                description="Forms unfair from the meaning clue.",
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
            ),
            _two(
                "The scorer counted the points again after noticing an error, but one faded mark was impossible to read.",
                "Use a re- word and an un- word in one sentence.",
                "The scorer recounted the points, but the faded mark remained unreadable.",
                ("repeat", "Uses recounted for counting again.", "scorer recounted the points"),
                ("negative", "Uses unreadable for impossible to read.", "mark remained unreadable"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=10,
            ),
        ],
    },
    "gilli-concrete-abstract": {
        "guided": [
            _one(
                "The wooden peg lay beside the chalk line, while patience helped the new player wait for her turn.",
                "Classify peg and patience and justify both choices.",
                "Peg is a concrete noun because it can be seen and touched, while patience is an abstract noun shown through calm waiting.",
                "Peg is a concrete noun because it can be seen and touched, while patience is an abstract noun",
                description="Classifies one sensed object and one quality.",
                skills=["grammar.noun_verb_adjective"],
            ),
            _one(
                "The crowd admired Rohan's honesty when he admitted that the ball touched the line.",
                "Which noun is abstract, and which action reveals it?",
                "Honesty is the abstract noun, and Rohan admitting the line touch reveals that quality.",
                "Honesty is the abstract noun, and Rohan admitting the line touch reveals that quality",
                description="Links an abstract quality to observable evidence.",
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
        "independent": [
            _two(
                "A cracked bat rested near the bench. Despite the loss, the captain showed courage by congratulating the other team and organising a rematch.",
                "Identify one concrete noun and one abstract noun, then cite the evidence for the abstract idea.",
                "Bat is a concrete noun because it is a physical object. Courage is abstract, and the captain shows it by congratulating the winners and organising a rematch after losing.",
                ("classes", "Correctly classifies bat and courage.", "Bat is a concrete noun because it is a physical object. Courage is abstract"),
                ("evidence", "Uses the captain's actions as evidence.", "shows it by congratulating the winners and organising a rematch after losing"),
                skills=["grammar.noun_verb_adjective"],
                min_words=26,
            ),
            _two(
                "The trophy stood on the table, but fairness mattered more when both teams agreed to replay a disputed point.",
                "Explain why trophy and fairness belong to different noun groups.",
                "Trophy is concrete because it can be seen and held. Fairness is abstract because it names a principle demonstrated when both teams replay the disputed point.",
                ("trophy", "Explains the concrete noun.", "Trophy is concrete because it can be seen and held"),
                ("fairness", "Explains the abstract noun through the action.", "Fairness is abstract because it names a principle demonstrated when both teams replay the disputed point"),
                skills=["grammar.noun_verb_adjective"],
                min_words=23,
            ),
        ],
        "transfer": [
            _two(
                "A medal hung inside the clinic, honouring a nurse whose kindness comforted frightened children.",
                "Transfer the concrete-abstract distinction and use the action clue.",
                "Medal is concrete because it is a physical object. Kindness is abstract, and the nurse's comforting actions show that quality.",
                ("object", "Classifies medal as concrete.", "Medal is concrete because it is a physical object"),
                ("quality", "Classifies kindness and cites evidence.", "Kindness is abstract, and the nurse's comforting actions show that quality"),
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
        "support": [
            _one(
                "A red cone marks the boundary.",
                "Is cone concrete or abstract, and why?",
                "Cone is concrete because it can be seen and touched.",
                "Cone is concrete because it can be seen and touched",
                description="Classifies a physical object.",
                skills=["grammar.noun_verb_adjective"],
            ),
            _one(
                "The players' joy grew when the missing child returned safely.",
                "Classify joy and use the scene as evidence.",
                "Joy is abstract because it names a feeling revealed by the safe return.",
                "Joy is abstract because it names a feeling",
                description="Classifies a feeling as abstract.",
                skills=["grammar.noun_verb_adjective"],
            ),
            _two(
                "A whistle lay in the teacher's hand, and silence spread when everyone listened.",
                "Classify whistle and silence.",
                "Whistle is concrete because it is a held object. Silence is abstract because it names the absence of sound.",
                ("object", "Classifies whistle.", "Whistle is concrete because it is a held object"),
                ("idea", "Classifies silence.", "Silence is abstract because it names the absence of sound"),
                skills=["grammar.noun_verb_adjective"],
            ),
            _one(
                "Meena showed generosity by lending her only spare bat.",
                "Which word names the abstract quality and what proves it?",
                "Generosity is the abstract quality, proved by Meena lending her only spare bat.",
                "Generosity is the abstract quality, proved by Meena lending her only spare bat",
                description="Links the quality to an observed action.",
                skills=["grammar.noun_verb_adjective"],
            ),
            _two(
                "The rope formed a circle, while teamwork helped the group measure it correctly.",
                "Explain the two noun types.",
                "Rope is concrete because it is a physical material. Teamwork is abstract because it names cooperative effort.",
                ("concrete", "Classifies rope.", "Rope is concrete because it is a physical material"),
                ("abstract", "Classifies teamwork.", "Teamwork is abstract because it names cooperative effort"),
                skills=["grammar.noun_verb_adjective"],
            ),
        ],
    },
    "gilli-possessive-pronouns": {
        "guided": [
            _one(
                "Asha's marker is blue. My marker is red. The blue marker is ___.",
                "Complete the sentence with the possessive pronoun that matches Asha.",
                "The blue marker is hers.",
                "blue marker is hers",
                description="Uses hers for Asha's marker.",
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=6,
            ),
            _one(
                "The twins brought two bats. Those bats belong to them.",
                "Replace belong to them with a possessive pronoun sentence.",
                "Those bats are theirs. The possessive pronoun matches the plural owners.",
                "Those bats are theirs",
                description="Uses theirs for plural owners.",
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=6,
            ),
        ],
        "independent": [
            _two(
                "Ritu placed her cap beside Mohan's cap. His had a white stripe, while hers had a green badge.",
                "Identify both pronoun owners and rewrite the comparison without ambiguity.",
                "His refers to Mohan's cap, and hers refers to Ritu's cap. Mohan's cap had the white stripe, while Ritu's cap had the green badge.",
                ("owners", "Links his and hers to the correct people.", "His refers to Mohan's cap, and hers refers to Ritu's cap"),
                ("rewrite", "Restates the comparison clearly.", "Mohan's cap had the white stripe, while Ritu's cap had the green badge"),
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=22,
            ),
            _two(
                "Our team uses the near field; their team uses the far field. The near field is ours and the far field is theirs.",
                "Explain how number and viewpoint determine ours and theirs.",
                "Ours refers to the field belonging to the speaker's whole team, while theirs refers to the field belonging to the other team. Both pronouns replace plural-owner noun phrases.",
                ("viewpoint", "Explains speaker group versus other group.", "Ours refers to the field belonging to the speaker's whole team, while theirs refers to the field belonging to the other team"),
                ("number", "Notes the plural owners.", "Both pronouns replace plural-owner noun phrases"),
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=25,
            ),
        ],
        "transfer": [
            _two(
                "In the art room, my brush is thin and your brush is broad. The thin brush is mine; the broad one is yours.",
                "Resolve mine and yours, then write the full noun phrases.",
                "Mine means my thin brush, and yours means your broad brush. The full comparison is: my brush is thin, while your brush is broad.",
                ("pronouns", "Resolves both possessive pronouns.", "Mine means my thin brush, and yours means your broad brush"),
                ("sentence", "Restores both noun phrases in order.", "my brush is thin, while your brush is broad"),
                skills=["grammar.pronouns", "grammar.sentence_order"],
            ),
        ],
        "support": [
            _one(
                "This bottle belongs to me.",
                "Rewrite the ownership using mine.",
                "This bottle is mine.",
                "This bottle is mine",
                description="Uses mine for the speaker's possession.",
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=6,
            ),
            _one(
                "That scorecard belongs to you.",
                "Rewrite the sentence using yours.",
                "That scorecard is yours. The pronoun matches the listener who owns it.",
                "That scorecard is yours",
                description="Uses yours for the listener's possession.",
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=6,
            ),
            _one(
                "The green scarf belongs to Neha.",
                "Replace Neha's scarf with a possessive pronoun.",
                "The green scarf is hers. The pronoun matches Neha as the owner.",
                "green scarf is hers",
                description="Uses hers for a female singular owner.",
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=6,
            ),
            _one(
                "The wooden striker belongs to Arjun.",
                "Use the matching possessive pronoun.",
                "The wooden striker is his. The pronoun matches Arjun as the owner.",
                "wooden striker is his",
                description="Uses his for a male singular owner.",
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=6,
            ),
            _two(
                "Our cones are orange; their cones are yellow.",
                "Rewrite both ownership phrases with pronouns.",
                "The orange cones are ours, and the yellow cones are theirs.",
                ("ours", "Uses ours for the speaker's group.", "orange cones are ours"),
                ("theirs", "Uses theirs for the other group.", "yellow cones are theirs"),
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=10,
            ),
        ],
    },
    "gilli-game-procedure": {
        "guided": [
            _two(
                "Game card: mark a throwing line; place three hoops two metres away; each player gets two beanbags; one point is earned for each bag inside a hoop.",
                "Write the setup and one complete turn.",
                "Mark the throwing line and place the hoops two metres away. A player stands behind the line, throws two beanbags, and earns one point for each bag inside a hoop.",
                ("setup", "Includes line and hoop placement.", "Mark the throwing line and place the hoops two metres away"),
                ("turn", "Includes position, two throws, and scoring.", "stands behind the line, throws two beanbags, and earns one point for each bag inside a hoop"),
                skills=["reading.event_sequence", "writing.procedure"],
                min_words=27,
                ordered=True,
            ),
            _two(
                "Safety note: only the current thrower enters the lane; everyone else waits behind the rope; all beanbags are collected after both throws.",
                "Turn the note into a waiting rule and a collection rule.",
                "Only the current thrower may enter the lane while the others wait behind the rope. Beanbags are collected only after both throws are complete.",
                ("waiting", "Keeps non-throwers behind the rope.", "others wait behind the rope"),
                ("collection", "Delays collection until the turn ends.", "collected only after both throws are complete"),
                skills=["reading.event_sequence", "writing.procedure"],
            ),
        ],
        "independent": [
            _two(
                "Design brief: four players, one chalk circle, six bottle caps, and a soft ball. Each player rolls once per round. A cap knocked outside the circle earns one point. Nobody retrieves caps until all four rolls finish.",
                "Write playable rules covering setup, turn order, scoring, and safety.",
                "Place six caps inside the chalk circle and line up four players. Each player rolls the soft ball once, earning one point for every cap knocked outside. Complete all four rolls before anyone retrieves the caps, then reset them for the next round.",
                ("play", "Includes setup, turn order, and score.", "Each player rolls the soft ball once, earning one point for every cap knocked outside"),
                ("safety", "Keeps retrieval after all rolls.", "Complete all four rolls before anyone retrieves the caps"),
                skills=["reading.event_sequence", "writing.procedure"],
                interaction="paragraph_text",
                min_words=37,
                ordered=True,
            ),
            _two(
                "School-yard adaptation: a narrow lane cannot safely allow long hits. Use a foam striker, keep hits below knee height, and award distance points at one, two, and three marked zones. A miss scores zero.",
                "Write the adapted procedure and explain how it controls risk.",
                "Players use the foam striker and keep every hit below knee height. The landing zone gives one, two, or three points, while a miss scores zero. Short, low hits fit the narrow lane and reduce the chance of striking bystanders.",
                ("rules", "Includes equipment, height, zones, and misses.", "foam striker and keep every hit below knee height. The landing zone gives one, two, or three points, while a miss scores zero"),
                ("risk", "Explains why the adaptation is safer.", "Short, low hits fit the narrow lane and reduce the chance of striking bystanders"),
                skills=["reading.event_sequence", "writing.procedure"],
                interaction="paragraph_text",
                min_words=34,
                ordered=True,
            ),
        ],
        "transfer": [
            _two(
                "A classroom review game uses question cards, a timer, and team tokens. One learner draws a card, the team has thirty seconds to answer, and a correct answer moves its token one space. Teams rotate after every card.",
                "Convert the information into an ordered procedure with a fair-turn rule.",
                "Place each team's token at the start. One learner draws a card and the team answers within thirty seconds; a correct answer moves its token one space. Rotate to the next team after every card so turns remain fair.",
                ("steps", "Orders draw, timed answer, score, and movement.", "draws a card and the team answers within thirty seconds; a correct answer moves its token one space"),
                ("fairness", "States rotation after every card.", "Rotate to the next team after every card so turns remain fair"),
                skills=["reading.event_sequence", "writing.procedure"],
                min_words=30,
                ordered=True,
            ),
        ],
        "support": [
            _two(
                "Setup card: draw one circle, place the target in its centre, and mark a standing line three steps away.",
                "Write the three setup actions in order.",
                "First draw the circle, next place the target at its centre, and finally mark the standing line three steps away.",
                ("first", "Starts with the circle.", "First draw the circle"),
                ("rest", "Places target before marking the line.", "next place the target at its centre, and finally mark the standing line"),
                skills=["reading.event_sequence", "writing.procedure"],
                ordered=True,
            ),
            _two(
                "Turn card: Player A strikes once, waits outside the lane, and records the landing zone after the piece stops.",
                "Write the complete turn and the waiting boundary.",
                "Player A strikes once and waits outside the lane until the piece stops. Then the landing zone is recorded.",
                ("turn", "Orders strike, stop, and record.", "strikes once and waits outside the lane until the piece stops. Then the landing zone is recorded"),
                ("boundary", "Keeps the player outside while the piece moves.", "waits outside the lane"),
                skills=["reading.event_sequence", "writing.procedure"],
                ordered=True,
            ),
            _two(
                "Score card: near zone equals one point, middle zone equals two, far zone equals three, and outside all zones equals zero.",
                "Explain how to record one throw without inventing bonus points.",
                "Record the single zone where the piece stops: one, two, or three points. Record zero if it stops outside every zone, and add no bonus.",
                ("score", "Uses only the supplied zones.", "one, two, or three points. Record zero if it stops outside every zone"),
                ("limit", "Rejects invented bonuses.", "add no bonus"),
                skills=["reading.event_sequence", "writing.procedure"],
            ),
            _two(
                "Safety card: use a foam piece; keep spectators behind the chalk line; stop play if anyone enters the lane.",
                "Turn all three directions into a safety procedure.",
                "Use the foam piece and keep spectators behind the chalk line. Stop play immediately if anyone enters the lane.",
                ("prevention", "Includes foam equipment and spectator position.", "Use the foam piece and keep spectators behind the chalk line"),
                ("stop", "States when play stops.", "Stop play immediately if anyone enters the lane"),
                skills=["reading.event_sequence", "writing.procedure"],
            ),
            _two(
                "Round card: three players take one turn each, the scorer totals points, and the next round begins only after the pieces are returned.",
                "Write the round-ending check and restart condition.",
                "After all three players finish one turn, the scorer totals the points. The next round begins only after every piece has been returned.",
                ("check", "Totals after all turns.", "After all three players finish one turn, the scorer totals the points"),
                ("restart", "Requires pieces returned before restart.", "next round begins only after every piece has been returned"),
                skills=["reading.event_sequence", "writing.procedure"],
                ordered=True,
            ),
        ],
    },
    "gilli-source-questions": {
        "guided": [
            _one(
                "Source card: The school sports club began in 2018. It meets on Wednesdays and stores equipment in Room 4.",
                "Write one question whose answer is the meeting day.",
                "On which day does the school sports club meet?",
                "On which day does the school sports club meet?",
                description="Forms a grammatical question answerable from the source.",
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=8,
            ),
            _one(
                "Fact note: The wooden pieces are cut from fallen branches by an adult craft group. The note gives no price.",
                "Ask one answerable question about who makes the pieces.",
                "Who cuts the wooden pieces from fallen branches?",
                "Who cuts the wooden pieces from fallen branches?",
                description="Asks for a supplied person or group.",
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=8,
            ),
        ],
        "independent": [
            _two(
                "Museum label: This painted clay game piece was found near a river settlement. It is about two hundred years old. The maker's name is unknown.",
                "Write one answerable question and one question the label cannot answer, then classify them.",
                "Where was the painted clay piece found? is answerable: near a river settlement. Who made it? is not answerable because the maker's name is unknown.",
                ("answerable", "Forms and answers a source-grounded question.", "Where was the painted clay piece found? is answerable: near a river settlement"),
                ("unknown", "Identifies a question blocked by missing information.", "Who made it? is not answerable because the maker's name is unknown"),
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=24,
            ),
            _two(
                "Interview note: Salma learned the game from her grandmother when she was nine. She now teaches it at the community centre each Saturday. The note does not state her favourite rule.",
                "Create two different question types supported by the note and flag the unavailable topic.",
                "When did Salma learn the game? She learned it at age nine. Where does she teach it? At the community centre. Her favourite rule cannot be reported from this note.",
                ("questions", "Forms when and where questions with supplied answers.", "When did Salma learn the game? She learned it at age nine. Where does she teach it? At the community centre"),
                ("limit", "Flags the unsupported favourite-rule topic.", "favourite rule cannot be reported from this note"),
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=27,
            ),
        ],
        "transfer": [
            _two(
                "Weather chart: Monday 12 mm rain, Tuesday 0 mm, Wednesday 7 mm. The chart contains no wind information.",
                "Write a comparison question the chart can answer and a wind question it cannot.",
                "Which day had more rain, Monday or Wednesday? Monday had more. How strong was Tuesday's wind? cannot be answered because the chart gives no wind data.",
                ("supported", "Forms and answers a rainfall comparison.", "Which day had more rain, Monday or Wednesday? Monday had more"),
                ("unsupported", "Forms and rejects the wind question.", "How strong was Tuesday's wind? cannot be answered because the chart gives no wind data"),
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=24,
            ),
        ],
        "support": [
            _one(
                "Card: The match starts at four o'clock.",
                "Write the question answered by four o'clock.",
                "What time does the match start?",
                "What time does the match start?",
                description="Forms a correct what-time question.",
                skills=["grammar.question_formation"],
                min_words=6,
            ),
            _one(
                "Card: The players meet beside the banyan tree.",
                "Ask for the meeting place.",
                "Where do the players meet? This question asks for the supplied meeting place.",
                "Where do the players meet?",
                description="Forms a correct where question.",
                skills=["grammar.question_formation"],
                min_words=6,
            ),
            _one(
                "Card: Anita keeps the score because she knows the rules well.",
                "Ask for the reason Anita keeps score.",
                "Why does Anita keep the score?",
                "Why does Anita keep the score?",
                description="Forms a correct why question.",
                skills=["grammar.question_formation"],
                min_words=6,
            ),
            _two(
                "Note: The lane is fifteen metres long. Its builder is not named.",
                "Ask one measurable question and one unavailable-person question.",
                "How long is the lane? It is fifteen metres long. Who built it? cannot be answered because no builder is named.",
                ("measure", "Asks and answers length.", "How long is the lane? It is fifteen metres long"),
                ("limit", "Rejects the builder question.", "Who built it? cannot be answered because no builder is named"),
                skills=["grammar.question_formation", "research.information_selection"],
            ),
            _two(
                "Poster: Registration closes on 18 August. Forms go to the sports office. The poster gives no fee.",
                "Write two supported questions and name the missing information.",
                "When does registration close? On 18 August. Where do forms go? To the sports office. The fee is not provided.",
                ("supported", "Asks when and where from the poster.", "When does registration close? On 18 August. Where do forms go? To the sports office"),
                ("missing", "States the unavailable fee.", "fee is not provided"),
                skills=["grammar.question_formation", "research.information_selection"],
            ),
        ],
    },
    "gilli-spelling-opposites": {
        "guided": [
            _one(
                "The first lane is narrow, but the second has enough room for four players abreast.",
                "Write the correctly spelled opposite of narrow for the second lane.",
                "The second lane is wide.",
                "second lane is wide",
                description="Uses the correctly spelled opposite in context.",
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=6,
            ),
            _one(
                "The crowd was noisy during the game and became ___ when the announcer read the result.",
                "Complete the sentence with the correctly spelled opposite.",
                "The crowd became quiet when the announcer read the result.",
                "crowd became quiet",
                description="Uses quiet as the correctly spelled opposite of noisy.",
                skills=["vocab.spelling", "vocab.antonyms"],
            ),
        ],
        "independent": [
            _two(
                "Draft pairs: heavy/light, early/late, scarce/plentifull. Only one word is misspelled.",
                "Correct the spelling and explain which pair expresses opposite quantity.",
                "The correct spelling is plentiful. Scarce and plentiful express opposite quantities: one means not enough, while the other means more than enough.",
                ("spelling", "Corrects plentifull.", "correct spelling is plentiful"),
                ("meaning", "Explains the quantity opposition.", "Scarce and plentiful express opposite quantities"),
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=21,
            ),
            _two(
                "A report calls the first surface rough and the polished surface smoothe. It also labels the empty box full.",
                "Correct the spelling error and the meaning error separately.",
                "Smooth is spelled without a final e. The empty box should be called empty, not full, because full is its opposite.",
                ("spelling", "Corrects smoothe to smooth.", "Smooth is spelled without a final e"),
                ("meaning", "Corrects full using the context.", "empty box should be called empty, not full"),
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=19,
            ),
        ],
        "transfer": [
            _two(
                "The path was safe in daylight but became dangerus after the lamps failed. A sign should state the contrast clearly.",
                "Correct the misspelling and write the opposite pair in a complete sentence.",
                "The correct spelling is dangerous. The path was safe in daylight but dangerous after the lamps failed.",
                ("spelling", "Corrects dangerus.", "correct spelling is dangerous"),
                ("pair", "Uses safe and dangerous as contextual opposites.", "path was safe in daylight but dangerous after the lamps failed"),
                skills=["vocab.spelling", "vocab.antonyms"],
            ),
        ],
        "support": [
            _one(
                "The gate is open now; after play it must be ___.",
                "Supply the correctly spelled opposite.",
                "After play, the gate must be closed.",
                "gate must be closed",
                description="Uses closed as the opposite of open.",
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=7,
            ),
            _one(
                "One rope is long, while the practice rope is ___.",
                "Write the opposite of long.",
                "The practice rope is short. Short is the correctly spelled opposite of long.",
                "practice rope is short",
                description="Uses short as the opposite of long.",
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=6,
            ),
            _one(
                "Correct the misspelling in this pair: strong / week.",
                "Write the correctly spelled opposite of strong.",
                "The correctly spelled opposite is weak.",
                "correctly spelled opposite is weak",
                description="Distinguishes weak from the time word week.",
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=6,
            ),
            _two(
                "The dry cloth absorbed water and became wett.",
                "Correct the spelling and state the opposite pair.",
                "The correct spelling is wet. Dry and wet are opposites describing the cloth before and after absorbing water.",
                ("spelling", "Corrects wett.", "correct spelling is wet"),
                ("meaning", "Explains the dry-wet contrast.", "Dry and wet are opposites"),
                skills=["vocab.spelling", "vocab.antonyms"],
            ),
            _two(
                "The rule seemed simple at first, but the final version was complicatted.",
                "Correct the word and give a clear opposite pair.",
                "The correct spelling is complicated. Simple and complicated form the intended opposite pair in this sentence.",
                ("spelling", "Corrects complicatted.", "correct spelling is complicated"),
                ("pair", "Identifies the intended opposition.", "Simple and complicated form the intended opposite pair"),
                skills=["vocab.spelling", "vocab.antonyms"],
            ),
        ],
    },
}


_LAUNCH_VARIANTS = {
    "gilli-poetic-meaning": {
        "transfer": [
            _two(
                "A paper boat danced between the ripples, then bowed beneath the footbridge before appearing on the other side.",
                "Interpret danced and bowed, then explain how the two images shape the boat's journey.",
                "Danced suggests the paper boat bobbed and turned lightly between the ripples, while bowed suggests it dipped under the bridge. Together the images make a small journey feel lively and graceful.",
                ("images", "Explains both movement images without taking them literally.", "bobbed and turned lightly between the ripples, while bowed suggests it dipped under the bridge"),
                ("effect", "States the effect of the images on the scene.", "make a small journey feel lively and graceful"),
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
                min_words=29,
            ),
        ],
        "review": [
            _two(
                "The first school bell scattered the sleepy silence, and doors opened all along the corridor.",
                "Explain scattered as a sound image and identify the change it creates in the sentence.",
                "Scattered means the ringing bell broke the quiet across the corridor. The image changes the setting from still and sleepy to active as the school day begins.",
                ("meaning", "Interprets the nonliteral verb from the sound clue.", "ringing bell broke the quiet across the corridor"),
                ("change", "Explains the movement from stillness to activity.", "changes the setting from still and sleepy to active"),
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
                min_words=25,
            ),
            _two(
                "After the shower, the evening sun stitched a gold line along the wet edge of the playing field.",
                "What does stitched mean here, and what picture does the phrase create?",
                "Stitched means the sunlight formed a thin connected line on the wet ground. The phrase helps the reader picture a bright gold border joining the field's edge.",
                ("meaning", "Explains stitched as a visual comparison.", "sunlight formed a thin connected line on the wet ground"),
                ("picture", "Describes the image created for the reader.", "bright gold border joining the field's edge"),
                skills=["reading.poetic_language", "reading.sentence_comprehension"],
                min_words=25,
            ),
        ],
    },
    "gilli-prefix-formation": {
        "transfer": [
            _two(
                "A storage box was packed for the match, but rain soaked its label. The team packed the dry equipment again and replaced the label that could not be read.",
                "Use one re- word and one un- word to describe the two actions precisely.",
                "The team repacked the dry equipment and replaced the unreadable label. Repacked means packed again, while unreadable means not able to be read.",
                ("words", "Forms and uses both prefixed words correctly.", "repacked the dry equipment and replaced the unreadable label"),
                ("meanings", "Explains the again and not meanings.", "Repacked means packed again, while unreadable means not able to be read"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=22,
            ),
        ],
        "review": [
            _two(
                "The goal rope was tied across the wrong posts. A player loosened it and tied it again across the correct posts.",
                "Replace the repeated actions with accurate un- and re- words, then explain each prefix.",
                "The player untied the rope and retied it across the correct posts. Un- reverses the tying, and re- shows that the rope was tied again.",
                ("sentence", "Uses untied and retied in context.", "untied the rope and retied it across the correct posts"),
                ("prefixes", "Explains what each prefix contributes.", "Un- reverses the tying, and re- shows that the rope was tied again"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=23,
            ),
            _two(
                "The boundary line had no clear mark after the dust storm, so the class painted the line again before play began.",
                "Describe the line before and after the work using an un- word and a re- word.",
                "The boundary was unmarked after the storm, so the class repainted it before the game. Unmarked means without a clear mark, and repainted means painted again.",
                ("use", "Uses both formed words in a meaningful sentence.", "boundary was unmarked after the storm, so the class repainted it"),
                ("meaning", "Explains the meanings created by both prefixes.", "Unmarked means without a clear mark, and repainted means painted again"),
                skills=["vocab.word_formation", "vocab.chapter_word_usage"],
                min_words=25,
            ),
        ],
    },
    "gilli-concrete-abstract": {
        "transfer": [
            _two(
                "Patience kept Arjun beside the practice line while a whistle rested on the bench.",
                "Classify patience and whistle as abstract or concrete nouns and justify both choices.",
                "Patience is an abstract noun because it names a quality understood through Arjun's waiting. Whistle is a concrete noun because it names an object that can be seen and touched.",
                ("abstract", "Classifies and explains the quality noun.", "Patience is an abstract noun because it names a quality"),
                ("concrete", "Classifies and explains the object noun.", "Whistle is a concrete noun because it names an object that can be seen and touched"),
                skills=["grammar.noun_verb_adjective"],
                min_words=28,
            ),
        ],
        "review": [
            _two(
                "Courage helped Leena take the final turn, and her helmet shone in the morning light.",
                "Identify the abstract and concrete nouns and explain the evidence for each.",
                "Courage is abstract because it names an inner quality shown by Leena's action. Helmet is concrete because it is a physical object visible in the scene.",
                ("abstract", "Identifies the inner quality noun.", "Courage is abstract because it names an inner quality"),
                ("concrete", "Identifies the physical object noun.", "Helmet is concrete because it is a physical object visible in the scene"),
                skills=["grammar.noun_verb_adjective"],
                min_words=24,
            ),
            _two(
                "Joy spread through the team when the metal medal was placed in their captain's hand.",
                "Classify joy and medal, then support each classification from the sentence.",
                "Joy is an abstract noun because it names a feeling shared by the team. Medal is a concrete noun because it is a metal object placed in the captain's hand.",
                ("feeling", "Classifies joy as an abstract feeling.", "Joy is an abstract noun because it names a feeling shared by the team"),
                ("object", "Classifies medal as a concrete object.", "Medal is a concrete noun because it is a metal object placed in the captain's hand"),
                skills=["grammar.noun_verb_adjective"],
                min_words=28,
            ),
        ],
    },
    "gilli-possessive-pronouns": {
        "transfer": [
            _two(
                "Anaya and Farah brought the two blue rackets. The red rackets belong to our group.",
                "Replace both owner phrases with possessive pronouns in two clear, ordered sentences.",
                "The blue rackets are theirs. The red rackets are ours.",
                ("owners", "Matches plural owners to theirs and ours.", "blue rackets are theirs", "red rackets are ours"),
                ("order", "Keeps each item beside its correct owner.", "The blue rackets are theirs. The red rackets are ours"),
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=10,
                ordered=True,
            ),
        ],
        "review": [
            _two(
                "I repaired the yellow kite. You repaired the green kite.",
                "Rewrite the ownership without repeating either person's name or the word repaired.",
                "The yellow kite is mine, and the green kite is yours.",
                ("pronouns", "Uses mine and yours for the correct owners.", "yellow kite is mine", "green kite is yours"),
                ("sentence", "Keeps both ownership statements in clear order.", "The yellow kite is mine, and the green kite is yours"),
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=11,
                ordered=True,
            ),
            _two(
                "Our class marked the near court. Their class marked the court beyond the trees.",
                "Use possessive pronouns to compare the courts without an unclear owner.",
                "The near court is ours, while the court beyond the trees is theirs.",
                ("pronouns", "Matches ours and theirs to the two classes.", "near court is ours", "court beyond the trees is theirs"),
                ("order", "Preserves the near-then-far comparison.", "The near court is ours, while the court beyond the trees is theirs"),
                skills=["grammar.pronouns", "grammar.sentence_order"],
                min_words=13,
                ordered=True,
            ),
        ],
    },
    "gilli-game-procedure": {
        "transfer": [
            _two(
                "For Coin Slide, draw three scoring bands on a smooth table and give each player three large counters. Players slide one counter per turn from behind a line. A counter touching a band edge earns the lower score, and hands stay off the table until every counter stops.",
                "Write playable setup and turn rules in order, including scoring and the safety boundary.",
                "Draw and number the three bands, place three counters per player behind the line, and choose a turn order. Each player slides one counter per turn; record the lower score for an edge touch, and wait until all counters stop before collecting them.",
                ("setup", "Orders the space, equipment, and turn setup.", "Draw and number the three bands, place three counters per player behind the line, and choose a turn order"),
                ("play", "States the turn, scoring, and safety rules.", "slides one counter per turn; record the lower score for an edge touch, and wait until all counters stop before collecting them"),
                skills=["reading.event_sequence", "writing.procedure"],
                interaction="paragraph_text",
                min_words=39,
                ordered=True,
            ),
        ],
        "review": [
            _two(
                "For Beanbag Squares, tape four numbered squares on the floor, mark a throwing line two metres away, and give each player two throws. A bag scores only when it rests fully inside a square. Players retrieve bags after both throws.",
                "Turn the description into an ordered procedure another class could follow.",
                "Tape and number four floor squares, mark the throwing line, give each player two beanbags, and set the turn order. Players throw from behind the line, score only bags fully inside a square, and collect both bags after the turn.",
                ("setup", "Orders the court and equipment setup.", "Tape and number four floor squares, mark the throwing line, give each player two beanbags, and set the turn order"),
                ("rules", "States throwing, scoring, and retrieval rules.", "throw from behind the line, score only bags fully inside a square, and collect both bags after the turn"),
                skills=["reading.event_sequence", "writing.procedure"],
                interaction="paragraph_text",
                min_words=36,
                ordered=True,
            ),
            _two(
                "In Chalk Trail Relay, teams copy a six-shape path from a card, then one player at a time steps through the shapes in order. A missed shape sends that player back to the start. The waiting team stays outside the marked lane.",
                "Write the setup and complete round procedure with the boundary rule.",
                "Copy the six shapes onto one lane for each team and place the model card at the start. One player follows the shapes in order; after a miss the player restarts, while waiting teammates remain outside the lane.",
                ("setup", "Creates lanes and positions the model card.", "Copy the six shapes onto one lane for each team and place the model card at the start"),
                ("round", "Orders play, restart, and waiting boundary.", "player follows the shapes in order; after a miss the player restarts, while waiting teammates remain outside the lane"),
                skills=["reading.event_sequence", "writing.procedure"],
                interaction="paragraph_text",
                min_words=35,
                ordered=True,
            ),
        ],
    },
    "gilli-source-questions": {
        "transfer": [
            _two(
                "Source card: The community court opened in 2018. Its surface is packed earth, and volunteers repaint the boundary every June. The card does not name the original designer.",
                "Write one well-formed question the card can answer and give its answer, then state one question it cannot answer.",
                "When do volunteers repaint the court boundary? They repaint it every June. The card cannot answer, 'Who designed the original court?' because no designer is named.",
                ("answerable", "Forms and answers a question supported by the card.", "When do volunteers repaint the court boundary? They repaint it every June"),
                ("limit", "Identifies a well-formed question beyond the source.", "Who designed the original court?"),
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=24,
            ),
        ],
        "review": [
            _two(
                "Practice timetable: Monday - balance drills; Wednesday - short matches; Friday - team review. Every session begins at 4 p.m. The timetable gives no coach names.",
                "Ask and answer one question about Wednesday, then write a question the timetable cannot settle.",
                "What happens at Wednesday's practice? Short matches happen at 4 p.m. The timetable cannot answer, 'Which coach leads the session?' because it lists no coach.",
                ("supported", "Forms and answers the Wednesday question from the timetable.", "What happens at Wednesday's practice? Short matches happen at 4 p.m"),
                ("unknown", "States a grammatical question with missing evidence.", "Which coach leads the session?"),
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=24,
            ),
            _two(
                "Map key: a blue circle marks a water point, a green triangle marks a first-aid desk, and a black line marks the walking route. The map has no distance scale.",
                "Form one question about a green triangle and answer it, then identify a question blocked by the missing scale.",
                "What does a green triangle show? It marks a first-aid desk. The map cannot answer, 'How many metres long is the walking route?' because it has no distance scale.",
                ("map", "Forms and answers a symbol question from the key.", "What does a green triangle show? It marks a first-aid desk"),
                ("boundary", "Forms the distance question the source cannot answer.", "How many metres long is the walking route?"),
                skills=["grammar.question_formation", "research.information_selection"],
                min_words=28,
            ),
        ],
    },
    "gilli-spelling-opposites": {
        "transfer": [
            _two(
                "One practice lane is rough and narrow; the repaired lane is smooth and wide.",
                "Write both opposite pairs correctly and explain how each pair contrasts the lanes.",
                "Rough is the opposite of smooth, and narrow is the opposite of wide. The first pair contrasts surface texture, while the second contrasts the space across each lane.",
                ("pairs", "Spells and pairs all four words correctly.", "Rough is the opposite of smooth, and narrow is the opposite of wide"),
                ("use", "Explains both contrasts in context.", "first pair contrasts surface texture, while the second contrasts the space across each lane"),
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=27,
            ),
        ],
        "review": [
            _two(
                "The notice describes an ancient stone game beside a modern sports hall. Teams arrive before play and depart after the final whistle.",
                "Copy the two opposite pairs with correct spelling and explain their meanings in this setting.",
                "Ancient and modern are opposites describing old and present-day places. Arrive and depart are opposites describing movement to and away from the game.",
                ("spelling", "Writes both antonym pairs accurately.", "Ancient and modern are opposites", "Arrive and depart are opposites"),
                ("meaning", "Explains both contrasts in the given setting.", "old and present-day places", "movement to and away from the game"),
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=23,
            ),
            _two(
                "At the start, the score board is empty and the equipment box is full. At the end, the board is full of scores and the box is empty.",
                "Spell the opposite pair and explain how its meaning switches between the two objects.",
                "Empty is the opposite of full. At the start the board is empty and the box is full, but at the end their conditions are reversed.",
                ("pair", "Spells the antonym pair correctly.", "Empty is the opposite of full"),
                ("context", "Explains the switched conditions.", "start the board is empty and the box is full, but at the end their conditions are reversed"),
                skills=["vocab.spelling", "vocab.antonyms"],
                min_words=25,
            ),
        ],
    },
}


def _iter_open_activities() -> list[dict]:
    activities: list[dict] = []
    for level in MANIFEST["levels"]:
        activities.extend(level["guided_variants"])
        activities.extend(level["independent_variants"])
        activities.extend(level["transfer_variants"])
        activities.extend(level["review_variants"])
        activities.extend(level["support_checks"].values())
    activities.extend(MANIFEST["chapter_assessment"]["items"])
    return [activity for activity in activities if activity["kind"] == "open_response"]


def _apply_depth() -> None:
    MANIFEST["chapter"]["content_version"] = "2026-07-15.3"
    MANIFEST["chapter"]["certification_version"] = "2026-07-15.3"
    anchors = {
        anchor["anchor_id"]: anchor for anchor in MANIFEST["source_anchors"]
    }
    anchors["eng_c5_ch07:wordwork:9-12"]["coverage_treatment"] = (
        "taught_and_assessed"
    )
    levels = {level["level_id"]: level for level in MANIFEST["levels"]}
    support_names = (
        "bridge",
        "masterclass",
        "revision_level_1",
        "revision_level_2",
        "revision_level_3",
    )
    for level_id, additions in _DEPTH.items():
        level = levels[level_id]
        principle = _PRINCIPLES[level_id]
        for target_key, phase_name in (
            ("guided_variants", "guided"),
            ("independent_variants", "independent"),
            ("transfer_variants", "transfer"),
        ):
            start = len(level[target_key]) + 1
            for offset, task in enumerate(additions[phase_name]):
                try:
                    activity = _open_activity(
                        level_id=level_id,
                        phase=phase_name,
                        index=start + offset,
                        principle=principle,
                        level_skills=level["skill_ids"],
                        task=task,
                    )
                except ValueError as exc:
                    raise ValueError(
                        f"{level_id}:{phase_name}:{task['model_answer']}"
                    ) from exc
                level[target_key].append(activity)
        support = {}
        for name, task in zip(support_names, additions["support"], strict=True):
            try:
                support[name] = _open_activity(
                    level_id=level_id,
                    phase=name,
                    index=1,
                    principle=principle,
                    level_skills=level["skill_ids"],
                    task=task,
                )
            except ValueError as exc:
                raise ValueError(
                    f"{level_id}:{name}:{task['model_answer']}"
                ) from exc
        level["support_checks"] = support
        support_ids = [support[name]["activity_id"] for name in support_names]
        for cluster in level["misconception_clusters"]:
            cluster["support_check_ids"] = support_ids


def _apply_launch_variants() -> None:
    MANIFEST["chapter"]["content_version"] = "2026-07-15.4"
    MANIFEST["chapter"]["certification_version"] = "2026-07-15.4"
    levels = {level["level_id"]: level for level in MANIFEST["levels"]}
    for level_id, additions in _LAUNCH_VARIANTS.items():
        level = levels[level_id]
        principle = _PRINCIPLES[level_id]
        for target_key, phase_name in (
            ("transfer_variants", "transfer"),
            ("review_variants", "review"),
        ):
            start = len(level[target_key]) + 1
            for offset, task in enumerate(additions[phase_name]):
                level[target_key].append(
                    _open_activity(
                        level_id=level_id,
                        phase=phase_name,
                        index=start + offset,
                        principle=principle,
                        level_skills=level["skill_ids"],
                        task=task,
                    )
                )


_MULTI_SLOT_ALIAS_REPAIRS = {
    "gilli-game-procedure-guided-1": {
        "space": "players clear the striking zone",
        "waiting": "everyone waiting stays behind the boundary",
    },
    "gilli-game-procedure-guided-2": {
        "record": "Record the result",
    },
    "gilli-game-procedure-independent-1": {
        "safety": "No one may push",
    },
    "gilli-game-procedure-transfer-2": {
        "constraint": "describer avoids saying the word",
    },
    "gilli-game-procedure-review-1": {
        "check": "Check that the lane is clear",
    },
    "gilli-game-procedure-review-2": {
        "limit": "identify any rule the source does not provide",
    },
    "eng_c5_ch07-assessment-gilli-game-procedure-1": {
        "end": "hunt ends after three completed cards",
    },
    "eng_c5_ch07-assessment-gilli-game-procedure-3": {
        "control": "read the first direction, move two squares east, then read and move one square north",
    },
}


def _repair_open_authority() -> None:
    for activity in _iter_open_activities():
        slots = activity["concept_slots"]
        if len(slots) == 1:
            slots[0]["any_of"] = [activity["model_answer"]]
        for slot in slots:
            replacement = _MULTI_SLOT_ALIAS_REPAIRS.get(
                activity["activity_id"], {}
            ).get(slot["id"])
            if replacement is not None:
                slot["any_of"] = [replacement]


_CONTENT_REPAIRS = {
    "gilli-prefix-formation:guided:3": {
        "model_answer": (
            "The word is rewrite, meaning write again. The completed sentence "
            "is: The captain had to rewrite the score before the next round."
        ),
        "relevance_terms": ["rewrite", "score", "round"],
    },
    "gilli-prefix-formation-independent-1": {
        "prompt": (
            "Explain what re- adds to play and use the scoring mistake to show "
            "why replay fits."
        ),
        "model_answer": (
            "Replay means to play again. The scoring mistake caused the class to "
            "play the final round again."
        ),
        "relevance_terms": ["replay", "play again", "scoring mistake"],
        "min_response_words": 15,
    },
    "gilli-prefix-formation-independent-2": {
        "prompt": (
            "Explain what un- changes in unlock and connect that meaning to the "
            "games cupboard."
        ),
        "model_answer": (
            "Unlock means to remove the locked state. The monitor will open the "
            "games cupboard after lunch."
        ),
        "relevance_terms": ["unlock", "locked state", "cupboard"],
        "min_response_words": 14,
    },
    "gilli-prefix-formation-transfer-1": {
        "passage": (
            "The first draft of the game rules is unclear. Mina will rewrite it "
            "so the steps are easier to follow."
        ),
        "prompt": (
            "Explain what re- adds to write and use the first-draft clue to show "
            "why rewrite fits."
        ),
        "model_answer": (
            "The prefix re- changes write to mean write again. The first draft is "
            "unclear, so Mina writes the rules again more clearly."
        ),
        "relevance_terms": ["prefix", "write again", "first draft"],
        "min_response_words": 18,
    },
    "gilli-prefix-formation-transfer-2": {
        "passage": "A cracked stick is unsafe for play.",
        "prompt": (
            "Complete the meaning equation unsafe = not safe, then name the crack "
            "as evidence for that meaning."
        ),
        "model_answer": (
            "Unsafe means not safe. The crack is evidence that the stick should "
            "not be used for play."
        ),
        "relevance_terms": ["unsafe", "not safe", "crack"],
        "min_response_words": 15,
    },
    "gilli-prefix-formation-review-1": {
        "passage": (
            "Rain knocked down the boundary marker. The players will rebuild it "
            "before the next match."
        ),
        "prompt": (
            "Correct the claim 'rebuild means build before rain': state what re- "
            "means and connect it to the damaged marker."
        ),
        "model_answer": (
            "The prefix re- means again. The rain knocked the marker down, so the "
            "players build it again."
        ),
        "relevance_terms": ["prefix", "again", "marker"],
        "min_response_words": 16,
    },
    "gilli-prefix-formation-review-2": {
        "passage": "The owner of the unmarked bag was unknown.",
        "prompt": (
            "Break unknown into its base word and prefix, then use the unmarked "
            "bag to confirm the meaning."
        ),
        "model_answer": (
            "The base word is known, and un- changes it to not known. The bag has "
            "no identifying mark, so its owner is unknown."
        ),
        "relevance_terms": ["known", "not known", "unmarked"],
        "min_response_words": 20,
    },
    "gilli-concrete-abstract-independent-1": {
        "prompt": (
            "Apply the sensory test to line: state its noun type and the visible "
            "feature that proves it."
        ),
    },
    "gilli-concrete-abstract-independent-2": {
        "prompt": (
            "Explain why friendship is abstract even though friendly actions can "
            "be seen."
        ),
    },
    "gilli-concrete-abstract-transfer-1": {
        "passage": (
            "The umpire held a measuring cord and waited patiently while the teams "
            "checked the score."
        ),
        "prompt": (
            "Classify cord and patience, giving one sensory or behaviour clue for "
            "each."
        ),
        "model_answer": (
            "Cord is concrete because it can be seen and touched. Patience is "
            "abstract because it is a quality shown by waiting calmly."
        ),
        "relevance_terms": ["cord", "concrete", "patience"],
        "min_response_words": 20,
    },
    "gilli-concrete-abstract-transfer-2": {
        "passage": (
            "Arun waited calmly after his turn was delayed. A learner says, "
            "'Patience is concrete because I can see Arun waiting.'"
        ),
        "prompt": (
            "Correct the classification and explain why visible behaviour does not "
            "make the quality a physical object."
        ),
        "model_answer": (
            "Patience is an abstract noun. Arun's waiting is visible evidence of "
            "the quality, but patience itself is not an object that can be touched."
        ),
        "relevance_terms": ["patience", "abstract noun", "visible evidence"],
        "min_response_words": 22,
    },
    "gilli-concrete-abstract-review-1": {
        "passage": (
            "A wooden stick lay beside the ring, and fairness guided the next turn."
        ),
        "prompt": (
            "Sort stick and fairness into concrete and abstract nouns, then justify "
            "each choice with a different test."
        ),
        "model_answer": (
            "Stick is concrete because it is a physical object that can be seen and "
            "touched. Fairness is abstract because it names an idea shown in how "
            "turns are shared."
        ),
        "relevance_terms": ["stick", "concrete", "fairness"],
        "min_response_words": 25,
    },
    "gilli-concrete-abstract-review-2": {
        "passage": (
            "A drum sounded when the final hit crossed the mark, and excitement "
            "spread through the team."
        ),
        "prompt": (
            "Compare drum with excitement: classify each noun and explain what "
            "evidence reveals it."
        ),
        "model_answer": (
            "Drum is concrete because it names a sound-making object. Excitement "
            "is abstract because it names a feeling revealed by the team's reaction."
        ),
        "relevance_terms": ["drum", "concrete", "excitement"],
        "min_response_words": 21,
    },
    "gilli-possessive-pronouns-independent-1": {
        "prompt": (
            "Complete 'The bat is ___' for the listener, then explain why your "
            "cannot stand alone."
        ),
    },
    "gilli-possessive-pronouns-independent-2": {
        "prompt": (
            "Rewrite the second sentence with the standalone ownership form for "
            "our team, then explain how the speaker is included."
        ),
    },
    "gilli-possessive-pronouns-transfer-1": {
        "passage": (
            "Vikram left his cap near the line. A learner completes the next "
            "sentence as: The cap is him."
        ),
        "prompt": (
            "Correct him and explain why the sentence needs a possessive pronoun."
        ),
        "model_answer": (
            "The cap is his. His replaces the owned noun phrase, while him is an "
            "object pronoun and cannot show ownership here."
        ),
        "relevance_terms": ["cap", "his", "ownership"],
        "min_response_words": 19,
    },
    "gilli-possessive-pronouns-transfer-2": {
        "passage": (
            "The girls made these scorecards. A label reads: The cards are their."
        ),
        "prompt": (
            "Replace their with the form that can stand alone, then explain why no "
            "noun follows it."
        ),
        "model_answer": (
            "The cards are theirs. Theirs stands alone as a possessive pronoun, "
            "while their must come before a noun."
        ),
        "relevance_terms": ["cards", "theirs", "possessive pronoun"],
        "min_response_words": 17,
    },
    "gilli-possessive-pronouns-review-1": {
        "passage": (
            "Maya and I packed our kit. Later I said, 'The kit is ours.'"
        ),
        "prompt": (
            "Explain why our changes to ours when the noun kit is no longer "
            "repeated."
        ),
        "model_answer": (
            "Our comes before the noun kit, while ours stands alone when the noun "
            "is not repeated. Both forms show that Maya and the speaker own it."
        ),
        "relevance_terms": ["our", "ours", "kit"],
        "min_response_words": 22,
    },
    "gilli-possessive-pronouns-review-2": {
        "passage": (
            "That water bottle belongs to Neha. Compare 'It is her' with 'It is "
            "hers.'"
        ),
        "prompt": (
            "Choose the ownership form and explain why the other form does not fit "
            "after is."
        ),
        "model_answer": (
            "It is hers. Hers shows ownership after the verb, while her cannot "
            "stand alone there as the possessive form."
        ),
        "relevance_terms": ["bottle", "hers", "ownership"],
        "min_response_words": 17,
    },
}


_ATOMIC_REQUIREMENT_REPAIRS = {
    "gilli-poetic-meaning-transfer-2": [
        ("event", "Names the event that changes the mood.", "The startled bird"),
        (
            "mood_change",
            "Explains how the mood changes after that event.",
            "changes excitement into cautious pause",
        ),
    ],
    "gilli-prefix-formation:guided:3": [
        (
            "formed_word",
            "Forms rewrite and explains that it means write again.",
            "The word is rewrite, meaning write again",
        ),
        (
            "sentence_use",
            "Uses rewrite correctly in the supplied sentence.",
            "The captain had to rewrite the score before the next round",
        ),
    ],
    "gilli-prefix-formation-independent-1": [
        ("prefix_meaning", "Explains replay as play again.", "Replay means to play again"),
        ("context_use", "Uses the scoring mistake to justify replay.", "The scoring mistake caused the class to play the final round again"),
    ],
    "gilli-prefix-formation-independent-2": [
        ("prefix_meaning", "Explains unlock as removing a locked state.", "Unlock means to remove the locked state"),
        ("context_use", "Connects unlock to opening the cupboard.", "The monitor will open the games cupboard after lunch"),
    ],
    "gilli-prefix-formation-transfer-1": [
        (
            "prefix_meaning",
            "Explains what re- adds to write.",
            "The prefix re- changes write to mean write again",
        ),
        (
            "context_clue",
            "Uses the unclear first draft to justify rewrite.",
            "The first draft is unclear, so Mina writes the rules again more clearly",
        ),
    ],
    "gilli-prefix-formation-transfer-2": [
        ("meaning", "Explains unsafe as not safe.", "Unsafe means not safe"),
        (
            "evidence",
            "Uses the crack as evidence for that meaning.",
            "The crack is evidence that the stick should not be used for play",
        ),
    ],
    "gilli-prefix-formation-review-1": [
        ("prefix_meaning", "Explains re- as again.", "The prefix re- means again"),
        (
            "context_clue",
            "Connects rebuilding to the rain-damaged marker.",
            "The rain knocked the marker down, so the players build it again",
        ),
    ],
    "gilli-prefix-formation-review-2": [
        (
            "word_parts",
            "Uses the base word and prefix to explain unknown.",
            "The base word is known, and un- changes it to not known",
        ),
        (
            "context_clue",
            "Uses the unmarked bag to confirm the meaning.",
            "The bag has no identifying mark, so its owner is unknown",
        ),
    ],
    "gilli-concrete-abstract-transfer-1": [
        (
            "concrete",
            "Classifies cord with a sensory reason.",
            "Cord is concrete because it can be seen and touched",
        ),
        (
            "abstract",
            "Classifies patience with a behaviour clue.",
            "Patience is abstract because it is a quality shown by waiting calmly",
        ),
    ],
    "gilli-concrete-abstract:guided:3": [
        ("concrete", "Classifies peg with a sensory reason.", "Peg is a concrete noun because it can be seen and touched"),
        ("abstract", "Classifies patience with a behaviour clue.", "patience is an abstract noun shown through calm waiting"),
    ],
    "gilli-concrete-abstract:guided:4": [
        ("quality", "Identifies the abstract quality.", "Honesty is the abstract noun"),
        ("evidence", "Names the action that reveals the quality.", "Rohan admitting the line touch reveals that quality"),
    ],
    "gilli-concrete-abstract-independent-1": [
        ("classification", "Classifies line as concrete.", "'line' is a concrete noun"),
        ("reason", "Uses the visible-mark sensory reason.", "it names a visible mark on the ground"),
    ],
    "gilli-concrete-abstract-independent-2": [
        ("classification", "Classifies friendship as abstract.", "'friendship' is an abstract noun"),
        ("reason", "Explains that a relationship is not a separate physical object.", "it names a relationship, not something detected as a separate object"),
    ],
    "gilli-concrete-abstract-transfer-2": [
        (
            "correction",
            "Corrects patience to an abstract noun.",
            "Patience is an abstract noun",
        ),
        (
            "reason",
            "Explains why visible behaviour does not make patience an object.",
            "Arun's waiting is visible evidence of the quality, but patience itself is not an object that can be touched",
        ),
    ],
    "gilli-concrete-abstract-review-1": [
        (
            "concrete",
            "Classifies stick with a sensory reason.",
            "Stick is concrete because it is a physical object that can be seen and touched",
        ),
        (
            "abstract",
            "Classifies fairness with an idea-and-behaviour reason.",
            "Fairness is abstract because it names an idea shown in how turns are shared",
        ),
    ],
    "gilli-concrete-abstract-review-2": [
        (
            "concrete",
            "Classifies drum as a physical object.",
            "Drum is concrete because it names a sound-making object",
        ),
        (
            "abstract",
            "Classifies excitement as a feeling revealed by a reaction.",
            "Excitement is abstract because it names a feeling revealed by the team's reaction",
        ),
    ],
    "gilli-concrete-abstract:bridge:1": [
        ("classification", "Classifies cone as concrete.", "Cone is concrete"),
        ("reason", "Uses the sensory test.", "it can be seen and touched"),
    ],
    "gilli-concrete-abstract:masterclass:1": [
        ("classification", "Classifies joy as abstract.", "Joy is abstract"),
        ("evidence", "Uses the safe return as evidence of the feeling.", "a feeling revealed by the safe return"),
    ],
    "gilli-concrete-abstract:revision_level_2:1": [
        ("quality", "Identifies generosity as the abstract quality.", "Generosity is the abstract quality"),
        ("evidence", "Uses Meena's lending action as evidence.", "Meena lending her only spare bat"),
    ],
    "gilli-possessive-pronouns-independent-1": [
        ("pronoun", "Chooses yours for the listener.", "The correct form is 'yours'"),
        ("reason", "Explains that the listener owns the bat.", "the listener owns the bat"),
    ],
    "gilli-possessive-pronouns-independent-2": [
        ("pronoun", "Chooses ours for the speaker's team.", "The correct form is 'ours'"),
        ("reason", "Explains that the speaker's group owns it.", "the speaker's group owns or claims it"),
    ],
    "gilli-possessive-pronouns-transfer-1": [
        ("pronoun", "Corrects the sentence with his.", "The cap is his"),
        (
            "reason",
            "Explains why his, not him, marks ownership.",
            "His replaces the owned noun phrase, while him is an object pronoun",
        ),
    ],
    "gilli-possessive-pronouns-transfer-2": [
        ("pronoun", "Corrects the sentence with theirs.", "The cards are theirs"),
        (
            "reason",
            "Explains the standalone-pronoun rule.",
            "Theirs stands alone as a possessive pronoun, while their must come before a noun",
        ),
    ],
    "gilli-possessive-pronouns-review-1": [
        (
            "determiner",
            "Explains that our comes before kit.",
            "Our comes before the noun kit",
        ),
        (
            "pronoun",
            "Explains that ours stands alone.",
            "ours stands alone when the noun is not repeated",
        ),
    ],
    "gilli-possessive-pronouns-review-2": [
        ("pronoun", "Chooses hers as the ownership form.", "It is hers"),
        (
            "reason",
            "Explains why her cannot stand alone as the possessive form.",
            "her cannot stand alone there as the possessive form",
        ),
    ],
    "gilli-source-questions-independent-2": [
        (
            "question",
            "Writes a question answered by the supplied meaning.",
            "What does boundary mean?",
        ),
        (
            "answer",
            "Answers the question from the supplied meaning.",
            "It is a line that marks the edge of an area",
        ),
    ],
    "gilli-source-questions-transfer-1": [
        (
            "question",
            "Writes a valid question about the year.",
            "When did the village sports club begin?",
        ),
        ("answer", "Answers with the source year.", "It began in 1998"),
    ],
    "gilli-source-questions-review-1": [
        (
            "question",
            "Writes a comparison question answered by the source.",
            "How is the gilli different from the danda?",
        ),
        (
            "answer",
            "Answers with the source comparison.",
            "The gilli is shorter and is the piece that is lifted for striking",
        ),
    ],
    "gilli-spelling-opposites-transfer-2": [
        ("winner", "Uses winner as one member of the opposite pair.", "The winner thanked"),
        ("loser", "Uses loser as the other member of the opposite pair.", "the loser after both had played fairly"),
    ],
    "eng_c5_ch07-assessment-gilli-possessive-pronouns-3": [
        ("pronoun", "Chooses hers for Sara's item.", "The correct form is 'hers'"),
        ("reason", "Explains why borrowing does not change ownership.", "borrowing does not change ownership"),
    ],
    "eng_c5_ch07-assessment-gilli-possessive-pronouns-5": [
        ("pronoun", "Chooses theirs for the opposing team.", "The correct form is 'theirs'"),
        ("reason", "Explains ownership by a plural group.", "a plural group owns them"),
    ],
    "eng_c5_ch07-assessment-gilli-spelling-opposites-4": [
        (
            "spelling_check",
            "States how to verify spelling.",
            "Verify spelling in a reliable dictionary",
        ),
        (
            "antonym_check",
            "States how to verify an antonym in context.",
            "substitute an antonym into the sentence to confirm both meaning and grammar",
        ),
    ],
}


_SELECTED_OPTION_REPAIRS = {
    "gilli-possessive-pronouns-co": {
        "prompt": "Which possessive pronoun completes the sentence for Ritu?",
    },
    "gilli-possessive-pronouns-guided-1": {
        "prompt": (
            "Which possessive pronoun completes the sentence for Aman and Zoya?"
        ),
    },
    "gilli-possessive-pronouns-guided-2": {
        "prompt": "Which possessive pronoun completes the sentence for the speaker?",
    },
    "gilli-game-procedure-co": {
        "prompt": "Which option gives a safe setup and turn procedure?",
    },
    "gilli-spelling-opposites-co": {
        "passage": (
            "The game word for the player who wins has a doubled consonant: "
            "wi__er."
        ),
        "prompt": "Which option completes the word with standard spelling?",
        "options": ["winer", "winnar", "winner", "winnner"],
        "accepted_answers": ["winner"],
    },
    "eng_c5_ch07-assessment-gilli-possessive-pronouns-1": {
        "prompt": (
            "Which possessive pronoun completes the sentence for you and Ravi?"
        ),
    },
    "eng_c5_ch07-assessment-gilli-possessive-pronouns-2": {
        "passage": (
            "The club members own the field. During practice, the field is ____."
        ),
        "prompt": (
            "Which possessive pronoun completes the sentence for the club members?"
        ),
    },
    "eng_c5_ch07-assessment-gilli-source-questions-4": {
        "accepted_answer": (
            "Name the requested fact, use a fitting question word and complete "
            "English order, add a question mark, and ask only what the packet can "
            "answer."
        ),
    },
}


def _all_manifest_activities() -> list[dict]:
    activities: list[dict] = []
    for level in MANIFEST["levels"]:
        activities.append(level["co_construct"])
        activities.extend(level["guided_variants"])
        activities.extend(level["independent_variants"])
        activities.extend(level["transfer_variants"])
        activities.extend(level["review_variants"])
        activities.extend(level["support_checks"].values())
    activities.extend(MANIFEST["chapter_assessment"]["items"])
    return activities


def _detail_guidance(count: int) -> str:
    if count == 1:
        return "include the detail the question asks for"
    if count == 2:
        return "include both details"
    return f"include all {count} details"


def _set_detail_guidance(activity: dict, count: int) -> None:
    guidance = _detail_guidance(count)
    teaching_block = activity["teaching_block"]
    known_guidance = [
        "include the detail the question asks for",
        "include both details",
        *(f"include all {value} details" for value in range(3, 9)),
    ]
    for old_guidance in known_guidance:
        if old_guidance in teaching_block:
            activity["teaching_block"] = teaching_block.replace(
                old_guidance,
                guidance,
            )
            return
    activity["teaching_block"] = (
        f"{teaching_block.rstrip()} {guidance.capitalize()}."
    )


def _set_atomic_requirements(
    activity: dict,
    requirements: list[tuple[str, str, str]],
) -> None:
    activity_id = activity["activity_id"]
    model_answer = " ".join(activity["model_answer"].casefold().split())
    min_quality = activity["rubric_criteria"][0].get("min_quality", 0.7)
    criteria = []
    slots = []
    for suffix, description, alias in requirements:
        if " ".join(alias.casefold().split()) not in model_answer:
            raise ValueError(f"{activity_id}:{suffix}:alias_not_in_model_answer")
        slot_id = f"{activity_id}:{suffix}"
        criteria.append(
            {
                "id": slot_id,
                "description": description,
                "required": True,
                "min_quality": min_quality,
            }
        )
        slots.append(
            {
                "id": slot_id,
                "description": description,
                "any_of": [alias],
            }
        )
    activity["rubric_criteria"] = criteria
    activity["concept_slots"] = slots
    if activity.get("ordered_concept_slot_ids") is not None:
        activity["ordered_concept_slot_ids"] = [item["id"] for item in slots]
    _set_detail_guidance(activity, len(requirements))


def _assessment_focus(activity: dict) -> str:
    activity_skills = set(activity["skill_ids"])
    return next(
        level["focus"]
        for level in MANIFEST["levels"]
        if activity_skills <= set(level["skill_ids"])
    )


def _apply_semantic_quality() -> None:
    MANIFEST["chapter"]["content_version"] = "2026-07-16.1"
    MANIFEST["chapter"]["certification_version"] = "2026-07-16.1"
    activities = {
        activity["activity_id"]: activity for activity in _all_manifest_activities()
    }
    for activity_id, repair in _CONTENT_REPAIRS.items():
        activities[activity_id].update(repair)

    for activity_id, repair in _SELECTED_OPTION_REPAIRS.items():
        activity = activities[activity_id]
        old_answer = activity["accepted_answers"][0]
        activity.update(
            {
                key: value
                for key, value in repair.items()
                if key not in {"accepted_answer", "accepted_answers", "options"}
            }
        )
        if "options" in repair:
            activity["options"] = repair["options"]
            activity["accepted_answers"] = repair["accepted_answers"]
        elif "accepted_answer" in repair:
            accepted_answer = repair["accepted_answer"]
            answer_index = activity["options"].index(old_answer)
            activity["options"][answer_index] = accepted_answer
            activity["accepted_answers"] = [accepted_answer]

    for activity_id, requirements in _ATOMIC_REQUIREMENT_REPAIRS.items():
        _set_atomic_requirements(activities[activity_id], requirements)

    for activity in MANIFEST["chapter_assessment"]["items"]:
        focus = _assessment_focus(activity)
        if activity["kind"] == "selected_option":
            activity["teaching_block"] = (
                f"Use the new card to {focus}. Compare every option with the "
                "visible details before choosing."
            )
            continue
        activity["teaching_block"] = (
            f"Use the new card to {focus}; "
            f"{_detail_guidance(len(activity['rubric_criteria']))}. "
            "Write only what the card supports."
        )


_apply_depth()
_apply_launch_variants()
_repair_open_authority()
_apply_semantic_quality()
